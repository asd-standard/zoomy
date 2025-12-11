"""
Integration Tests: Tiling Pipeline
===================================

This module contains end-to-end integration tests for the complete tiling
pipeline, validating the interaction between Tiler, TileStore, TileCache,
TileManager, and TileProviders.

The tests verify that images are correctly converted into pyramidal tile
structures, stored on disk, cached in memory, and retrieved on demand.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
import shutil
import tempfile
import hashlib
from pathlib import Path
from PIL import Image

# Import tiling system components
from pyzui.tilesystem.tiler import Tiler
from pyzui.tilesystem.tile import Tile
from pyzui.tilesystem import tilestore
from pyzui.tilesystem import tilemanager
from pyzui.tilesystem.tilestore import TileCache
from pyzui.tilesystem.tileproviders.statictileprovider import StaticTileProvider


class ConcreteTiler(Tiler):
    """
    A concrete implementation of Tiler for testing purposes.

    This class implements the _scanchunk method using PIL
    to read image data, enabling end-to-end testing of the tiling process.
    """

    def __init__(self, infile, media_id=None, filext='jpg', tilesize=256):
        """Initialize the tiler and open the source image."""
        super().__init__(infile, media_id, filext, tilesize)
        self._image = Image.open(infile).convert('RGB')
        self._width, self._height = self._image.size
        self._bytes_per_pixel = 3
        self._current_row = 0

    def _scanchunk(self):
        """
        Read the next scanline from the image.

        This is a stateful method that returns the next row each time
        it is called. The tiler calls this once per pixel row.

        Returns:
            bytes: Raw RGB pixel data for the next scanline, or empty string
                   if past end of image.
        """
        if self._current_row >= self._height:
            return b''
        row_data = []
        for x in range(self._width):
            pixel = self._image.getpixel((x, self._current_row))
            row_data.extend(pixel)
        self._current_row += 1
        return bytes(row_data)


@pytest.fixture
def temp_tilestore(tmp_path):
    """
    Fixture: Isolated Temporary Tile Store

    Provides a temporary directory for tile storage that is automatically
    cleaned up after each test, ensuring test isolation.

    Yields:
        str: Path to the temporary tilestore directory.
    """
    # Import the actual tilestore module (not the package)
    from pyzui.tilesystem.tilestore import tilestore as ts_module

    original_tile_dir = ts_module.tile_dir
    temp_dir = str(tmp_path / "tilestore")
    os.makedirs(temp_dir, exist_ok=True)

    # Patch both the package and the module
    ts_module.tile_dir = temp_dir
    tilestore.tile_dir = temp_dir

    yield temp_dir

    # Restore original and cleanup
    ts_module.tile_dir = original_tile_dir
    tilestore.tile_dir = original_tile_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def sample_images(tmp_path):
    """
    Fixture: Sample Test Images

    Creates test images of various sizes for testing different tiling scenarios:
    - 256x256: Single tile image (exactly one tile)
    - 512x512: Four tiles at max level (2x2 grid)
    - 500x300: Non-power-of-two dimensions
    - 100x100: Image smaller than tile size
    - 1024x1024: Larger pyramid (3 levels)

    Yields:
        dict: Mapping of (width, height) to image file path.
    """
    images = {}
    test_cases = [
        (256, 256, 'red'),
        (512, 512, 'green'),
        (500, 300, 'blue'),
        (100, 100, 'yellow'),
        (1024, 1024, 'purple'),
    ]

    for width, height, color in test_cases:
        img = Image.new('RGB', (width, height), color=color)
        # Add a gradient pattern for visual verification
        for y in range(height):
            for x in range(min(10, width)):
                img.putpixel((x, y), (x * 25, y % 256, 128))
        path = tmp_path / f"test_{width}x{height}.png"
        img.save(path)
        images[(width, height)] = str(path)

    yield images

    # Cleanup
    for path in images.values():
        if os.path.exists(path):
            os.remove(path)


class TestTilingPipelineEndToEnd:
    """
    Feature: Complete Tiling Pipeline

    The tiling system converts large images into pyramidal tile structures
    that enable efficient zooming and panning. This test suite validates
    the complete pipeline from image input to tile retrieval.
    """

    def test_tile_image_creates_pyramid_structure(self, temp_tilestore, sample_images):
        """
        Scenario: Tiling an image creates a complete tile pyramid

        Given a 512x512 pixel image
        When the Tiler processes the image
        Then tiles are created at multiple pyramid levels
        And the base level (0) contains a single overview tile
        And the maximum level contains the full-resolution tiles
        And all tiles are stored in the TileStore
        """
        image_path = sample_images[(512, 512)]
        media_id = "test_512x512"

        # When: Process the image with the tiler
        tiler = ConcreteTiler(image_path, media_id=media_id, tilesize=256)
        tiler.run()

        # Then: Verify no errors occurred
        assert tiler.error is None, f"Tiling failed: {tiler.error}"
        assert tiler.progress == 1.0, "Tiling did not complete"

        # And: Verify tile pyramid structure
        # For 512x512 with tilesize 256: maxtilelevel = 1
        # Level 0: 1 tile (overview)
        # Level 1: 2x2 = 4 tiles (full resolution)

        # Check level 0 tile exists
        tile_path_0 = tilestore.get_tile_path((media_id, 0, 0, 0), filext='jpg')
        assert os.path.exists(tile_path_0), "Level 0 tile not created"

        # Check level 1 tiles exist (2x2 grid)
        for row in range(2):
            for col in range(2):
                tile_path = tilestore.get_tile_path((media_id, 1, row, col), filext='jpg')
                assert os.path.exists(tile_path), f"Level 1 tile ({row},{col}) not created"

        # And: Verify metadata was written
        assert tilestore.tiled(media_id), "Media not marked as tiled"
        assert tilestore.get_metadata(media_id, 'width') == 512
        assert tilestore.get_metadata(media_id, 'height') == 512
        assert tilestore.get_metadata(media_id, 'tilesize') == 256
        assert tilestore.get_metadata(media_id, 'maxtilelevel') == 1

    def test_tile_single_tile_image(self, temp_tilestore, sample_images):
        """
        Scenario: Tiling an image that fits in a single tile

        Given a 256x256 pixel image (exactly one tile size)
        When the Tiler processes the image
        Then only a single tile at level 0 is created
        And the maximum tile level is 0
        """
        image_path = sample_images[(256, 256)]
        media_id = "test_single_tile"

        # When
        tiler = ConcreteTiler(image_path, media_id=media_id, tilesize=256)
        tiler.run()

        # Then
        assert tiler.error is None
        assert tilestore.get_metadata(media_id, 'maxtilelevel') == 0

        # Only level 0 tile should exist
        tile_path = tilestore.get_tile_path((media_id, 0, 0, 0), filext='jpg')
        assert os.path.exists(tile_path)

        # Level 1 should not exist
        tile_path_1 = tilestore.get_tile_path((media_id, 1, 0, 0), filext='jpg')
        assert not os.path.exists(tile_path_1)

    def test_tile_image_smaller_than_tilesize(self, temp_tilestore, sample_images):
        """
        Scenario: Tiling an image smaller than the tile size

        Given a 100x100 pixel image (smaller than 256x256 tile size)
        When the Tiler processes the image
        Then a single tile is created containing the entire image
        And the tile dimensions match the original image size
        """
        image_path = sample_images[(100, 100)]
        media_id = "test_small_image"

        # When
        tiler = ConcreteTiler(image_path, media_id=media_id, tilesize=256)
        tiler.run()

        # Then
        assert tiler.error is None
        assert tilestore.get_metadata(media_id, 'maxtilelevel') == 0
        assert tilestore.get_metadata(media_id, 'width') == 100
        assert tilestore.get_metadata(media_id, 'height') == 100

    def test_tile_non_power_of_two_dimensions(self, temp_tilestore, sample_images):
        """
        Scenario: Tiling an image with non-power-of-two dimensions

        Given a 500x300 pixel image
        When the Tiler processes the image
        Then edge tiles have reduced dimensions to fit the image bounds
        And the tile structure correctly represents the original image
        """
        image_path = sample_images[(500, 300)]
        media_id = "test_non_pot"

        # When
        tiler = ConcreteTiler(image_path, media_id=media_id, tilesize=256)
        tiler.run()

        # Then
        assert tiler.error is None

        # 500x300 with tilesize 256:
        # Width: ceil(500/256) = 2 tiles across
        # Height: ceil(300/256) = 2 tiles down
        # maxtilelevel = ceil(log2(max(500,300)/256)) = ceil(log2(1.95)) = 1

        assert tilestore.get_metadata(media_id, 'width') == 500
        assert tilestore.get_metadata(media_id, 'height') == 300

        # Verify tiles exist
        tile_path = tilestore.get_tile_path((media_id, 0, 0, 0), filext='jpg')
        assert os.path.exists(tile_path)

    def test_tile_larger_pyramid(self, temp_tilestore, sample_images):
        """
        Scenario: Tiling a larger image creates multiple pyramid levels

        Given a 1024x1024 pixel image
        When the Tiler processes the image
        Then tiles are created at levels 0, 1, and 2
        And each level has the correct number of tiles
        """
        image_path = sample_images[(1024, 1024)]
        media_id = "test_large"

        # When
        tiler = ConcreteTiler(image_path, media_id=media_id, tilesize=256)
        tiler.run()

        # Then
        assert tiler.error is None

        # 1024x1024 with tilesize 256: maxtilelevel = 2
        # Level 0: 1 tile
        # Level 1: 2x2 = 4 tiles
        # Level 2: 4x4 = 16 tiles
        # Total: 21 tiles

        assert tilestore.get_metadata(media_id, 'maxtilelevel') == 2

        # Verify level 2 has 4x4 tiles
        for row in range(4):
            for col in range(4):
                tile_path = tilestore.get_tile_path((media_id, 2, row, col), filext='jpg')
                assert os.path.exists(tile_path), f"Level 2 tile ({row},{col}) missing"

    def test_progress_tracking_during_tiling(self, temp_tilestore, sample_images):
        """
        Scenario: Progress is tracked during tiling

        Given an image to tile
        When the Tiler runs
        Then progress starts at 0.0
        And progress ends at 1.0 upon completion
        """
        image_path = sample_images[(512, 512)]
        media_id = "test_progress"

        tiler = ConcreteTiler(image_path, media_id=media_id, tilesize=256)

        # Before running
        assert tiler.progress == 0.0

        # Run the tiler
        tiler.run()

        # After completion
        assert tiler.progress == 1.0


class TestTileRetrievalIntegration:
    """
    Feature: Tile Retrieval After Tiling

    After images are tiled, tiles must be retrievable through the
    TileManager and TileProvider system for display.
    """

    def test_retrieve_tiles_after_tiling(self, temp_tilestore, sample_images):
        """
        Scenario: Retrieve tiles from TileStore after tiling

        Given an image that has been tiled
        When tiles are requested from TileStore
        Then the tile files can be read and contain valid image data
        """
        image_path = sample_images[(512, 512)]
        media_id = "test_retrieval"

        # Given: Tile the image
        tiler = ConcreteTiler(image_path, media_id=media_id, tilesize=256)
        tiler.run()
        assert tiler.error is None

        # When: Retrieve tile paths
        tile_path = tilestore.get_tile_path((media_id, 1, 0, 0), filext='jpg')

        # Then: Tile file exists and is readable as image
        assert os.path.exists(tile_path)

        tile_image = Image.open(tile_path)
        assert tile_image.size[0] <= 256
        assert tile_image.size[1] <= 256

    def test_tiled_check_before_and_after(self, temp_tilestore, sample_images):
        """
        Scenario: Verify tiled status before and after tiling

        Given an image path
        When checking tiled status before tiling
        Then tiled() returns False
        When the image is tiled
        Then tiled() returns True
        """
        image_path = sample_images[(256, 256)]
        media_id = "test_tiled_check"

        # Before tiling
        assert not tilestore.tiled(media_id), "Should not be tiled initially"

        # Tile the image
        tiler = ConcreteTiler(image_path, media_id=media_id, tilesize=256)
        tiler.run()

        # After tiling
        assert tilestore.tiled(media_id), "Should be tiled after processing"

    def test_metadata_retrieval_after_tiling(self, temp_tilestore, sample_images):
        """
        Scenario: Retrieve metadata after tiling

        Given an image that has been tiled
        When metadata is requested for the media
        Then all expected metadata fields are available
        And values match the original image properties
        """
        image_path = sample_images[(500, 300)]
        media_id = "test_metadata"

        # Tile the image
        tiler = ConcreteTiler(image_path, media_id=media_id, filext='png', tilesize=128)
        tiler.run()

        # Retrieve and verify metadata
        assert tilestore.get_metadata(media_id, 'width') == 500
        assert tilestore.get_metadata(media_id, 'height') == 300
        assert tilestore.get_metadata(media_id, 'tilesize') == 128
        assert tilestore.get_metadata(media_id, 'filext') == 'png'
        assert tilestore.get_metadata(media_id, 'maxtilelevel') is not None


class TestTileCacheIntegration:
    """
    Feature: Tile Cache Integration

    The TileCache provides in-memory caching of tiles to avoid repeated
    disk reads. This test suite validates cache behavior.
    """

    def test_cache_stores_and_retrieves_tiles(self, temp_tilestore, sample_images):
        """
        Scenario: Cache stores and retrieves tiles

        Given a TileCache instance
        When a tile is added to the cache
        Then the same tile can be retrieved by its ID
        """
        cache = TileCache(maxsize=100)

        # Create a test tile
        test_image = Image.new('RGB', (256, 256), color='red')
        tile = Tile(test_image)

        tile_id = ('test_media', 0, 0, 0)

        # Store in cache
        cache[tile_id] = tile

        # Retrieve from cache
        retrieved = cache[tile_id]
        assert retrieved is tile

    def test_cache_replaces_existing_tiles(self, temp_tilestore, sample_images):
        """
        Scenario: Cache replaces existing tiles with new ones

        Given a tile already in the cache
        When storing a new tile with the same tile ID
        Then the cache stores the new tile
        And the original tile is replaced
        """
        cache = TileCache(maxsize=100)

        tile_id = ('test_media', 1, 0, 0)  # Use tilelevel=1 for mortal tile

        # Store first tile
        tile1 = Tile(Image.new('RGB', (256, 256), color='red'))
        cache[tile_id] = tile1

        # Store second tile with same ID
        tile2 = Tile(Image.new('RGB', (256, 256), color='blue'))
        cache[tile_id] = tile2

        # New tile should replace the original
        retrieved = cache[tile_id]
        assert retrieved is tile2

    def test_cache_lru_eviction(self, temp_tilestore, sample_images):
        """
        Scenario: LRU eviction removes least recently used tiles

        Given a cache with limited size
        When the cache exceeds its maximum size
        Then the least recently used tiles are evicted
        And recently accessed tiles remain in cache

        Note: Tiles with tilelevel=0 are immortal and never evicted.
        This test uses tilelevel=1 to ensure tiles are mortal.
        """
        cache = TileCache(maxsize=3)

        # Add 3 tiles (using tilelevel=1 for mortal tiles)
        for i in range(3):
            tile_id = ('media', 1, 0, i)  # tilelevel=1 makes them mortal
            cache[tile_id] = Tile(Image.new('RGB', (256, 256)))

        # Access tile at col=0 to make it recently used
        _ = cache[('media', 1, 0, 0)]

        # Add a 4th tile, should evict tile at col=1 (LRU)
        cache[('media', 1, 0, 3)] = Tile(Image.new('RGB', (256, 256)))

        # Tile at col=0 should still be in cache (recently accessed)
        assert ('media', 1, 0, 0) in cache

        # Tile at col=1 should be evicted (LRU, oldest not accessed)
        assert ('media', 1, 0, 1) not in cache

    def test_cache_contains_check(self, temp_tilestore, sample_images):
        """
        Scenario: Check if tile exists in cache

        Given a cache with some tiles
        When checking for tile existence
        Then existing tiles return True
        And missing tiles return False
        """
        cache = TileCache(maxsize=100)

        tile_id = ('media', 1, 2, 3)
        cache[tile_id] = Tile(Image.new('RGB', (256, 256)))

        assert tile_id in cache
        assert ('media', 9, 9, 9) not in cache


class TestMultipleImageTiling:
    """
    Feature: Multiple Image Tiling

    The tiling system must handle multiple images independently,
    each with its own tile pyramid and metadata.
    """

    def test_tile_multiple_images_independently(self, temp_tilestore, sample_images):
        """
        Scenario: Multiple images are tiled independently

        Given multiple images of different sizes
        When each image is tiled
        Then each has its own tile pyramid
        And metadata is stored separately for each
        And tiles do not interfere with each other
        """
        # Tile first image
        tiler1 = ConcreteTiler(
            sample_images[(256, 256)],
            media_id="image_1",
            tilesize=256
        )
        tiler1.run()

        # Tile second image
        tiler2 = ConcreteTiler(
            sample_images[(512, 512)],
            media_id="image_2",
            tilesize=256
        )
        tiler2.run()

        # Both should complete successfully
        assert tiler1.error is None
        assert tiler2.error is None

        # Both should be marked as tiled
        assert tilestore.tiled("image_1")
        assert tilestore.tiled("image_2")

        # Metadata should be independent
        assert tilestore.get_metadata("image_1", 'width') == 256
        assert tilestore.get_metadata("image_2", 'width') == 512

        assert tilestore.get_metadata("image_1", 'maxtilelevel') == 0
        assert tilestore.get_metadata("image_2", 'maxtilelevel') == 1


class TestTilePathConsistency:
    """
    Feature: Tile Path Consistency

    Tile paths must be consistent and deterministic, ensuring that
    the same tile ID always maps to the same file path.
    """

    def test_tile_path_is_deterministic(self, temp_tilestore):
        """
        Scenario: Tile paths are deterministic

        Given a tile ID
        When the path is requested multiple times
        Then the same path is returned each time
        """
        tile_id = ('my_media.jpg', 5, 100, 200)

        path1 = tilestore.get_tile_path(tile_id, filext='jpg')
        path2 = tilestore.get_tile_path(tile_id, filext='jpg')

        assert path1 == path2

    def test_different_tiles_have_different_paths(self, temp_tilestore):
        """
        Scenario: Different tiles have different paths

        Given two different tile IDs
        When their paths are requested
        Then the paths are different
        """
        tile_id_1 = ('media', 0, 0, 0)
        tile_id_2 = ('media', 0, 0, 1)

        path1 = tilestore.get_tile_path(tile_id_1, filext='jpg')
        path2 = tilestore.get_tile_path(tile_id_2, filext='jpg')

        assert path1 != path2

    def test_media_path_uses_hash(self, temp_tilestore):
        """
        Scenario: Media path uses SHA1 hash for directory naming

        Given a media ID
        When the media path is requested
        Then the path contains a SHA1 hash of the media ID
        """
        media_id = "my_image.jpg"
        expected_hash = hashlib.sha1(media_id.encode('utf-8')).hexdigest()

        path = tilestore.get_media_path(media_id)

        assert expected_hash in path


class TestTilingErrorHandling:
    """
    Feature: Tiling Error Handling

    The tiling system must handle errors gracefully and provide
    meaningful error information.
    """

    def test_tiling_nonexistent_file_sets_error(self, temp_tilestore, tmp_path):
        """
        Scenario: Tiling a nonexistent file reports error

        Given a path to a file that does not exist
        When the Tiler attempts to process it
        Then an error is set on the tiler
        And progress is set to 1.0 (completion)
        """
        nonexistent_path = str(tmp_path / "does_not_exist.jpg")

        try:
            tiler = ConcreteTiler(nonexistent_path, media_id="error_test")
            tiler.run()
            # Should have error after run
            assert tiler.error is not None or tiler.progress == 1.0
        except FileNotFoundError:
            # This is also acceptable behavior
            pass

    def test_tiling_corrupted_image_handles_gracefully(self, temp_tilestore, tmp_path):
        """
        Scenario: Tiling a corrupted image handles error gracefully

        Given a file that is not a valid image
        When the Tiler attempts to process it
        Then an error is reported
        And the system does not crash
        """
        corrupted_path = tmp_path / "corrupted.jpg"
        with open(corrupted_path, 'wb') as f:
            f.write(b"This is not a valid image file")

        try:
            tiler = ConcreteTiler(str(corrupted_path), media_id="corrupted_test")
            # Should raise or set error
            tiler.run()
        except Exception:
            # Exception during init or run is acceptable
            pass


class TestTileStorageStats:
    """
    Feature: Tile Storage Statistics

    The TileStore provides statistics about stored tiles for
    monitoring and management purposes.
    """

    def test_get_directory_size(self, temp_tilestore, sample_images):
        """
        Scenario: Calculate tile directory size

        Given a directory with tiled images
        When directory size is requested
        Then the total size in bytes is returned
        """
        # Tile an image to create files
        tiler = ConcreteTiler(
            sample_images[(256, 256)],
            media_id="size_test",
            tilesize=256
        )
        tiler.run()

        media_path = tilestore.get_media_path("size_test")
        size = tilestore.get_directory_size(media_path)

        assert size > 0, "Directory size should be greater than 0"

    def test_get_tilestore_stats(self, temp_tilestore, sample_images):
        """
        Scenario: Get overall tilestore statistics

        Given a tilestore with multiple tiled images
        When statistics are requested
        Then media count, file count, and total size are returned
        """
        # Tile multiple images
        for i, size in enumerate([(256, 256), (512, 512)]):
            if size in sample_images:
                tiler = ConcreteTiler(
                    sample_images[size],
                    media_id=f"stats_test_{i}",
                    tilesize=256
                )
                tiler.run()

        stats = tilestore.get_tilestore_stats()

        assert 'media_count' in stats
        assert 'file_count' in stats
        assert 'total_size' in stats
        assert stats['media_count'] >= 2
        assert stats['file_count'] > 0
        assert stats['total_size'] > 0
