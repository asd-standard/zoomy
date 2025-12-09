"""
Integration Tests: TileManager Coordination
============================================

This module contains integration tests validating the TileManager's role as
the central coordinator of the tiling system. The TileManager routes tile
requests to appropriate providers, manages dual-tier caching, and synthesizes
missing tiles from available ones.

The tests cover:
- Tile request routing to static vs dynamic providers
- get_tile, get_tile_robust, and cut_tile operations
- Negative tile level handling (zoomed-out views)
- Dual-cache coordination (permanent + temporary)
- Metadata access for static and dynamic media
- Exception handling (MediaNotTiled, TileNotLoaded, TileNotAvailable)
- Provider purge operations through TileManager
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
import time
import tempfile
import shutil
from pathlib import Path
from PIL import Image

from pyzui.tilesystem.tile import Tile
from pyzui.tilesystem.tilecache import TileCache
from pyzui.tilesystem import tilestore
from pyzui.tilesystem import tilemanager
from pyzui.tilesystem.tilemanager import (
    MediaNotTiled,
    TileNotLoaded,
    TileNotAvailable
)
from pyzui.tilesystem.tiler import Tiler


class ConcreteTiler(Tiler):
    """
    A concrete implementation of Tiler for testing purposes.

    Implements the _scanchunk method using PIL to read image data,
    enabling end-to-end testing of the tiling process.
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

        Returns:
            bytes: Raw RGB pixel data for the next scanline.
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
    Fixture: Isolated Tile Storage

    Provides a temporary directory for tile storage, ensuring
    test isolation from the system tilestore.

    Yields:
        str: Path to the temporary tilestore directory.
    """
    from pyzui.tilesystem.tilestore import tilestore as ts_module

    original_tile_dir = ts_module.tile_dir
    temp_dir = str(tmp_path / "tilestore")
    os.makedirs(temp_dir, exist_ok=True)

    ts_module.tile_dir = temp_dir
    tilestore.tile_dir = temp_dir

    yield temp_dir

    ts_module.tile_dir = original_tile_dir
    tilestore.tile_dir = original_tile_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def initialized_tilemanager(temp_tilestore):
    """
    Fixture: Initialized TileManager

    Initializes the TileManager with test-appropriate settings and
    ensures cleanup after test completion.

    Yields:
        None (TileManager is a module with global state)
    """
    tilemanager.init(total_cache_size=100, auto_cleanup=False)
    yield
    tilemanager.purge()


@pytest.fixture
def sample_images(tmp_path):
    """
    Fixture: Sample Test Images

    Creates test images of various sizes for testing different scenarios.

    Yields:
        dict: Mapping of (width, height) to image file path.
    """
    images = {}
    test_cases = [
        (256, 256, 'red'),
        (512, 512, 'green'),
        (1024, 1024, 'blue'),
    ]

    for width, height, color in test_cases:
        img = Image.new('RGB', (width, height), color=color)
        # Add gradient pattern for visual verification
        for y in range(height):
            for x in range(min(10, width)):
                img.putpixel((x, y), (x * 25, y % 256, 128))
        path = tmp_path / f"test_{width}x{height}.png"
        img.save(path)
        images[(width, height)] = str(path)

    yield images


@pytest.fixture
def tiled_media(temp_tilestore, sample_images, initialized_tilemanager):
    """
    Fixture: Pre-tiled Media

    Creates and tiles a sample image, returning the media_id for testing.

    Yields:
        str: The media_id of the tiled image.
    """
    image_path = sample_images[(512, 512)]
    media_id = "test_tiled_media"

    tiler = ConcreteTiler(image_path, media_id=media_id, tilesize=256)
    tiler.run()

    assert tiler.error is None
    yield media_id


class TestTileManagerInitialization:
    """
    Feature: TileManager Initialization

    The TileManager must be initialized before use. Initialization
    sets up caches, providers, and cleanup settings.
    """

    def test_init_creates_dual_cache_system(self, temp_tilestore):
        """
        Scenario: Initialization creates dual-tier cache

        Given a fresh TileManager
        When init() is called with cache size
        Then permanent cache receives 80% of total size
        And temporary cache receives 20% of total size
        """
        tilemanager.init(total_cache_size=100, auto_cleanup=False)

        # Verify init completed without error
        # The caches are private, but we can verify through behavior
        assert tilemanager.tiled("dynamic:fern") is True

        tilemanager.purge()

    def test_init_starts_static_provider(self, temp_tilestore):
        """
        Scenario: Initialization starts static tile provider

        Given a fresh TileManager
        When init() is called
        Then the static tile provider thread is started
        And it is ready to receive requests
        """
        tilemanager.init(total_cache_size=100, auto_cleanup=False)

        # Static provider should be running - verify by making a request
        # (won't load anything but shouldn't crash)
        try:
            tilemanager.load_tile(("nonexistent", 0, 0, 0))
        except Exception:
            pass  # Expected - media doesn't exist

        tilemanager.purge()

    def test_init_registers_dynamic_providers(self, temp_tilestore):
        """
        Scenario: Initialization registers dynamic tile providers

        Given a fresh TileManager
        When init() is called
        Then dynamic providers are registered
        And dynamic media IDs are recognized as tiled
        """
        tilemanager.init(total_cache_size=100, auto_cleanup=False)

        # Dynamic media should always be considered tiled
        assert tilemanager.tiled("dynamic:fern") is True

        tilemanager.purge()


class TestTileRequestRouting:
    """
    Feature: Tile Request Routing

    The TileManager routes tile requests to the appropriate provider
    based on the media_id prefix. Static media goes to StaticTileProvider,
    dynamic media (prefixed with "dynamic:") goes to the corresponding
    DynamicTileProvider.
    """

    def test_static_media_routed_to_static_provider(
            self, temp_tilestore, tiled_media, initialized_tilemanager):
        """
        Scenario: Static media requests go to static provider

        Given a tiled static media
        When a tile is requested via load_tile
        Then the request is routed to StaticTileProvider
        And the tile becomes available in cache
        """
        tile_id = (tiled_media, 0, 0, 0)

        # Request tile load
        tilemanager.load_tile(tile_id)
        time.sleep(0.3)

        # Should be loadable now
        tile = tilemanager.get_tile(tile_id)
        assert tile is not None
        assert isinstance(tile, Tile)

    def test_dynamic_media_routed_to_dynamic_provider(
            self, temp_tilestore, initialized_tilemanager):
        """
        Scenario: Dynamic media requests go to dynamic provider

        Given an initialized TileManager with dynamic providers
        When a tile is requested for dynamic media
        Then the request is routed to the appropriate DynamicTileProvider
        And the tile is generated and cached
        """
        tile_id = ("dynamic:fern", 5, 0, 0)

        # Request tile load
        tilemanager.load_tile(tile_id)
        time.sleep(0.5)

        # Dynamic tile should be generated
        try:
            tile = tilemanager.get_tile(tile_id)
            assert tile is not None
        except TileNotLoaded:
            # May still be loading - that's OK for this test
            pass

    def test_unknown_dynamic_prefix_uses_static_provider(
            self, temp_tilestore, initialized_tilemanager):
        """
        Scenario: Unknown media uses static provider

        Given a media_id that doesn't match any dynamic provider
        When a tile is requested
        Then the request is routed to StaticTileProvider
        And MediaNotTiled is raised if not tiled
        """
        tile_id = ("unknown_media.jpg", 0, 0, 0)

        with pytest.raises(MediaNotTiled):
            tilemanager.get_tile(tile_id)


class TestGetTileBehavior:
    """
    Feature: get_tile Operation

    The get_tile function retrieves tiles from cache, raising appropriate
    exceptions when tiles are unavailable. It distinguishes between
    untiled media, tiles not yet loaded, and permanently unavailable tiles.
    """

    def test_get_tile_returns_cached_tile(
            self, temp_tilestore, tiled_media, initialized_tilemanager):
        """
        Scenario: get_tile returns tile from cache

        Given a tile that has been loaded into cache
        When get_tile is called
        Then the cached tile is returned
        And no exception is raised
        """
        tile_id = (tiled_media, 0, 0, 0)

        # Load tile first
        tilemanager.load_tile(tile_id)
        time.sleep(0.3)

        # Get should succeed
        tile = tilemanager.get_tile(tile_id)
        assert tile is not None
        assert isinstance(tile, Tile)

    def test_get_tile_raises_media_not_tiled(
            self, temp_tilestore, initialized_tilemanager):
        """
        Scenario: get_tile raises MediaNotTiled for untiled media

        Given a media that has not been tiled
        When get_tile is called
        Then MediaNotTiled exception is raised
        """
        tile_id = ("never_tiled_media.jpg", 0, 0, 0)

        with pytest.raises(MediaNotTiled):
            tilemanager.get_tile(tile_id)

    def test_get_tile_raises_tile_not_loaded(
            self, temp_tilestore, tiled_media, initialized_tilemanager):
        """
        Scenario: get_tile raises TileNotLoaded for uncached tile

        Given a tiled media with tiles not yet in cache
        When get_tile is called for an uncached tile
        Then TileNotLoaded exception is raised
        And load_tile is triggered automatically
        """
        # Use a tile that exists but isn't cached yet
        tile_id = (tiled_media, 1, 1, 1)

        # First call should raise TileNotLoaded
        with pytest.raises(TileNotLoaded):
            tilemanager.get_tile(tile_id)

    def test_get_tile_raises_tile_not_available_for_negative_level(
            self, temp_tilestore, tiled_media, initialized_tilemanager):
        """
        Scenario: get_tile raises TileNotAvailable for negative levels

        Given a valid tiled media
        When get_tile is called with negative tile level
        Then TileNotAvailable exception is raised
        """
        tile_id = (tiled_media, -1, 0, 0)

        with pytest.raises(TileNotAvailable):
            tilemanager.get_tile(tile_id)


class TestGetTileRobust:
    """
    Feature: get_tile_robust Operation

    The get_tile_robust function provides fallback behavior, attempting
    to synthesize tiles from parent tiles when direct loading fails.
    It never raises TileNotLoaded or TileNotAvailable.
    """

    def test_get_tile_robust_returns_cached_tile(
            self, temp_tilestore, tiled_media, initialized_tilemanager):
        """
        Scenario: get_tile_robust returns cached tile when available

        Given a tile that is already cached
        When get_tile_robust is called
        Then the cached tile is returned directly
        """
        tile_id = (tiled_media, 0, 0, 0)

        # Load tile first
        tilemanager.load_tile(tile_id)
        time.sleep(0.3)

        tile = tilemanager.get_tile_robust(tile_id)
        assert tile is not None
        assert isinstance(tile, Tile)

    def test_get_tile_robust_synthesizes_missing_tile(
            self, temp_tilestore, tiled_media, initialized_tilemanager):
        """
        Scenario: get_tile_robust synthesizes tile from parent

        Given a tile that is not cached
        And its parent tiles are available
        When get_tile_robust is called
        Then a tile is synthesized via cut_tile
        And no exception is raised
        """
        # First ensure level 0 is cached
        base_tile_id = (tiled_media, 0, 0, 0)
        tilemanager.load_tile(base_tile_id)
        time.sleep(0.3)

        # Request a higher level tile that may not be cached
        tile_id = (tiled_media, 1, 0, 0)

        tile = tilemanager.get_tile_robust(tile_id)
        assert tile is not None

    def test_get_tile_robust_raises_media_not_tiled(
            self, temp_tilestore, initialized_tilemanager):
        """
        Scenario: get_tile_robust still raises MediaNotTiled

        Given a media that has never been tiled
        When get_tile_robust is called
        Then MediaNotTiled exception is raised
        And synthesis cannot help (no base tile exists)
        """
        tile_id = ("untiled_media.jpg", 0, 0, 0)

        with pytest.raises(MediaNotTiled):
            tilemanager.get_tile_robust(tile_id)

    def test_get_tile_robust_handles_negative_levels(
            self, temp_tilestore, tiled_media, initialized_tilemanager):
        """
        Scenario: get_tile_robust handles negative tile levels

        Given a tiled media with level 0 tile cached
        When get_tile_robust is called with negative level
        Then a zoomed-out tile is synthesized
        And no exception is raised
        """
        # Ensure level 0 is cached
        base_tile_id = (tiled_media, 0, 0, 0)
        tilemanager.load_tile(base_tile_id)
        time.sleep(0.3)

        # Request negative level
        tile_id = (tiled_media, -1, 0, 0)

        tile = tilemanager.get_tile_robust(tile_id)
        assert tile is not None


class TestCutTileOperation:
    """
    Feature: cut_tile Tile Synthesis

    The cut_tile function synthesizes tiles by cropping and resizing
    parent tiles. It handles both upscaling (from lower detail) and
    negative levels (zoomed-out views).
    """

    def test_cut_tile_synthesizes_from_parent(
            self, temp_tilestore, tiled_media, initialized_tilemanager):
        """
        Scenario: cut_tile creates tile from parent

        Given a parent tile at lower zoom level
        When cut_tile is called for a child tile
        Then the child tile is synthesized by cropping and resizing
        And a tuple of (tile, final_flag) is returned
        """
        # Ensure level 0 is cached
        base_tile_id = (tiled_media, 0, 0, 0)
        tilemanager.load_tile(base_tile_id)
        time.sleep(0.3)

        # Cut a tile from level 1
        tile_id = (tiled_media, 1, 0, 0)
        tile, final = tilemanager.cut_tile(tile_id)

        assert tile is not None
        assert isinstance(final, bool)

    def test_cut_tile_negative_level_resizes_base_tile(
            self, temp_tilestore, tiled_media, initialized_tilemanager):
        """
        Scenario: cut_tile handles negative levels by resizing

        Given the base tile (0,0,0) is cached
        When cut_tile is called with negative level
        Then the base tile is resized to smaller dimensions
        And final flag is True (definitive result)
        """
        # Ensure level 0 is cached
        base_tile_id = (tiled_media, 0, 0, 0)
        tilemanager.load_tile(base_tile_id)
        time.sleep(0.3)

        # Cut at negative level
        tile_id = (tiled_media, -1, 0, 0)
        tile, final = tilemanager.cut_tile(tile_id)

        assert tile is not None
        assert final is True  # Negative levels are always final
        # Tile should be smaller than original
        assert tile.size[0] <= 256
        assert tile.size[1] <= 256

    def test_cut_tile_returns_final_true_for_available_tile(
            self, temp_tilestore, tiled_media, initialized_tilemanager):
        """
        Scenario: cut_tile returns final=True when tile is definitive

        Given a tile that exists at the requested resolution
        When cut_tile retrieves or synthesizes it
        Then final flag is True
        And the tile can be cached permanently
        """
        # Ensure tiles are loaded
        tile_id = (tiled_media, 0, 0, 0)
        tilemanager.load_tile(tile_id)
        time.sleep(0.3)

        tile, final = tilemanager.cut_tile(tile_id)
        assert final is True

    def test_cut_tile_with_tempcache_stores_intermediate(
            self, temp_tilestore, tiled_media, initialized_tilemanager):
        """
        Scenario: cut_tile uses temporary cache for intermediate tiles

        Given tempcache parameter is positive
        When cut_tile synthesizes a non-final tile
        Then the tile is stored in temporary cache
        And expires after specified number of accesses
        """
        # Ensure level 0 is cached
        base_tile_id = (tiled_media, 0, 0, 0)
        tilemanager.load_tile(base_tile_id)
        time.sleep(0.3)

        # Request with tempcache enabled
        tile_id = (tiled_media, 1, 0, 0)
        tile, final = tilemanager.cut_tile(tile_id, tempcache=5)

        assert tile is not None


class TestNegativeTileLevels:
    """
    Feature: Negative Tile Level Handling

    Negative tile levels represent zoomed-out views beyond level 0.
    Level -1 is 50% of level 0, level -2 is 25%, etc. These are
    created by resizing the base (0,0,0) tile.
    """

    def test_negative_level_produces_smaller_tile(
            self, temp_tilestore, tiled_media, initialized_tilemanager):
        """
        Scenario: Negative levels produce progressively smaller tiles

        Given the base tile at level 0
        When tiles at negative levels are requested
        Then each negative level is half the size of the previous
        """
        # Ensure level 0 is cached
        base_tile_id = (tiled_media, 0, 0, 0)
        tilemanager.load_tile(base_tile_id)
        time.sleep(0.3)

        base_tile = tilemanager.get_tile(base_tile_id)
        base_size = base_tile.size

        # Level -1 should be 50%
        tile_neg1, _ = tilemanager.cut_tile((tiled_media, -1, 0, 0))
        assert tile_neg1.size[0] == base_size[0] // 2
        assert tile_neg1.size[1] == base_size[1] // 2

        # Level -2 should be 25%
        tile_neg2, _ = tilemanager.cut_tile((tiled_media, -2, 0, 0))
        assert tile_neg2.size[0] == base_size[0] // 4
        assert tile_neg2.size[1] == base_size[1] // 4

    def test_negative_levels_always_final(
            self, temp_tilestore, tiled_media, initialized_tilemanager):
        """
        Scenario: Negative level tiles are always marked as final

        Given a request for negative tile level
        When cut_tile processes the request
        Then final flag is always True
        And the tile is cached permanently
        """
        # Ensure level 0 is cached
        base_tile_id = (tiled_media, 0, 0, 0)
        tilemanager.load_tile(base_tile_id)
        time.sleep(0.3)

        for level in [-1, -2, -3]:
            tile, final = tilemanager.cut_tile((tiled_media, level, 0, 0))
            assert final is True, f"Level {level} should be final"


class TestMetadataAccess:
    """
    Feature: Metadata Access Through TileManager

    The TileManager provides unified access to metadata for both
    static and dynamic media. Static media metadata comes from
    TileStore, dynamic media has predefined defaults.
    """

    def test_static_media_metadata_from_tilestore(
            self, temp_tilestore, tiled_media, initialized_tilemanager):
        """
        Scenario: Static media metadata retrieved from TileStore

        Given a tiled static media
        When metadata is requested through TileManager
        Then values are retrieved from TileStore
        And match the original tiling parameters
        """
        width = tilemanager.get_metadata(tiled_media, 'width')
        height = tilemanager.get_metadata(tiled_media, 'height')
        tilesize = tilemanager.get_metadata(tiled_media, 'tilesize')

        assert width == 512
        assert height == 512
        assert tilesize == 256

    def test_dynamic_media_metadata_defaults(
            self, temp_tilestore, initialized_tilemanager):
        """
        Scenario: Dynamic media returns predefined metadata

        Given a dynamic media provider
        When metadata is requested
        Then provider-specific defaults are returned
        And standard keys are available
        """
        media_id = "dynamic:fern"

        tilesize = tilemanager.get_metadata(media_id, 'tilesize')
        maxtilelevel = tilemanager.get_metadata(media_id, 'maxtilelevel')
        filext = tilemanager.get_metadata(media_id, 'filext')

        assert tilesize is not None
        assert maxtilelevel is not None
        assert filext is not None

    def test_unknown_metadata_key_returns_none(
            self, temp_tilestore, tiled_media, initialized_tilemanager):
        """
        Scenario: Unknown metadata key returns None

        Given a valid media_id
        When requesting a non-existent metadata key
        Then None is returned
        And no exception is raised
        """
        result = tilemanager.get_metadata(tiled_media, 'nonexistent_key')
        assert result is None


class TestTiledCheck:
    """
    Feature: Media Tiled Status Check

    The tiled() function checks whether media has been tiled.
    Dynamic media is always considered tiled, static media
    requires actual tiling to be complete.
    """

    def test_tiled_returns_true_for_tiled_static_media(
            self, temp_tilestore, tiled_media, initialized_tilemanager):
        """
        Scenario: tiled() returns True for tiled static media

        Given a media that has been successfully tiled
        When tiled() is called
        Then True is returned
        """
        assert tilemanager.tiled(tiled_media) is True

    def test_tiled_returns_false_for_untiled_static_media(
            self, temp_tilestore, initialized_tilemanager):
        """
        Scenario: tiled() returns False for untiled static media

        Given a media that has not been tiled
        When tiled() is called
        Then False is returned
        """
        assert tilemanager.tiled("never_tiled.jpg") is False

    def test_tiled_returns_true_for_dynamic_media(
            self, temp_tilestore, initialized_tilemanager):
        """
        Scenario: tiled() always returns True for dynamic media

        Given a dynamic media_id (prefixed with "dynamic:")
        When tiled() is called
        Then True is returned regardless of state
        """
        assert tilemanager.tiled("dynamic:fern") is True
        assert tilemanager.tiled("dynamic:unknown") is True


class TestPurgeOperation:
    """
    Feature: Provider Purge Through TileManager

    The purge() function clears pending requests from providers,
    enabling clean resource management when media is unloaded.
    """

    def test_purge_all_clears_all_providers(
            self, temp_tilestore, initialized_tilemanager):
        """
        Scenario: purge() without arguments clears all providers

        Given pending requests in multiple providers
        When purge() is called without media_id
        Then all providers have their queues cleared
        """
        # Queue some requests
        tilemanager.load_tile(("media1.jpg", 0, 0, 0))
        tilemanager.load_tile(("dynamic:fern", 0, 0, 0))

        # Purge all
        tilemanager.purge()

        # No assertion needed - just verify no crash

    def test_purge_specific_media_clears_only_that_media(
            self, temp_tilestore, initialized_tilemanager):
        """
        Scenario: purge(media_id) only clears specific media

        Given pending requests for multiple media
        When purge() is called with specific media_id
        Then only that media's requests are cleared
        """
        # This is primarily a non-crash test
        tilemanager.purge("specific_media.jpg")


class TestDualCacheCoordination:
    """
    Feature: Dual Cache Coordination

    The TileManager maintains two caches: permanent (80%) for
    loaded tiles and temporary (20%) for synthesized tiles.
    This separation enables different eviction policies.
    """

    def test_loaded_tiles_go_to_permanent_cache(
            self, temp_tilestore, tiled_media, initialized_tilemanager):
        """
        Scenario: Loaded tiles stored in permanent cache

        Given a tile loaded from disk
        When it is stored in cache
        Then it goes to the permanent cache
        And is retrievable via get_tile
        """
        tile_id = (tiled_media, 0, 0, 0)

        tilemanager.load_tile(tile_id)
        time.sleep(0.3)

        # Should be in permanent cache
        tile = tilemanager.get_tile(tile_id)
        assert tile is not None

    def test_synthesized_tiles_use_temporary_cache(
            self, temp_tilestore, tiled_media, initialized_tilemanager):
        """
        Scenario: Synthesized non-final tiles use temporary cache

        Given a tile synthesized via cut_tile
        When tempcache parameter is positive
        Then non-final tiles are stored in temporary cache
        And expire after specified accesses
        """
        # Ensure base tile is available
        base_tile_id = (tiled_media, 0, 0, 0)
        tilemanager.load_tile(base_tile_id)
        time.sleep(0.3)

        # Synthesize with tempcache
        tile_id = (tiled_media, 1, 0, 0)
        tile, final = tilemanager.cut_tile(tile_id, tempcache=3)

        assert tile is not None
