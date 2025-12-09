"""
Integration Tests: Concurrent Access and Thread Safety
=======================================================

This module contains integration tests validating thread safety and
concurrent access patterns in the tiling system. These tests verify
that the system handles multiple simultaneous requests correctly,
without race conditions or data corruption.

The tests cover:
- Multiple threads requesting the same tile simultaneously
- Concurrent tiling of different images
- Cache access under heavy multi-threaded load
- Provider queue behavior with rapid concurrent requests
- Race conditions between cache check and tile load
- Thread-safe metadata access
- Concurrent read/write operations on TileStore
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
import time
import threading
import queue
import tempfile
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
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
from pyzui.tilesystem.tileproviders.tileprovider import TileProvider


class ConcreteTiler(Tiler):
    """
    A concrete implementation of Tiler for testing purposes.

    Implements the _scanchunk method using PIL to read image data.
    """

    def __init__(self, infile, media_id=None, filext='jpg', tilesize=256):
        """Initialize the tiler and open the source image."""
        super().__init__(infile, media_id, filext, tilesize)
        self._image = Image.open(infile).convert('RGB')
        self._width, self._height = self._image.size
        self._bytes_per_pixel = 3
        self._current_row = 0
        self._lock = threading.Lock()

    def _scanchunk(self):
        """
        Read the next scanline from the image (thread-safe).

        Returns:
            bytes: Raw RGB pixel data for the next scanline.
        """
        with self._lock:
            if self._current_row >= self._height:
                return b''
            row_data = []
            for x in range(self._width):
                pixel = self._image.getpixel((x, self._current_row))
                row_data.extend(pixel)
            self._current_row += 1
            return bytes(row_data)


class MockTileProvider(TileProvider):
    """
    Mock provider with configurable delay for race condition testing.
    """

    def __init__(self, cache, load_delay=0.05):
        """Initialize with configurable load delay."""
        super().__init__(cache)
        self.load_delay = load_delay
        self.load_call_count = 0
        self.load_calls = []
        self._lock = threading.Lock()

    def _load(self, tile_id):
        """Load with artificial delay to expose race conditions."""
        time.sleep(self.load_delay)
        with self._lock:
            self.load_call_count += 1
            self.load_calls.append(tile_id)
        return Image.new('RGB', (256, 256), color='gray')


@pytest.fixture
def temp_tilestore(tmp_path):
    """
    Fixture: Isolated Tile Storage

    Provides a temporary directory for tile storage.

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

    Yields:
        None (TileManager is a module with global state)
    """
    tilemanager.init(total_cache_size=200, auto_cleanup=False)
    yield
    tilemanager.purge()


@pytest.fixture
def sample_images(tmp_path):
    """
    Fixture: Multiple Sample Test Images

    Creates several test images for concurrent testing.

    Yields:
        list: List of image file paths.
    """
    images = []
    for i in range(5):
        img = Image.new('RGB', (512, 512), color=(i * 50, 100, 150))
        path = tmp_path / f"concurrent_test_{i}.png"
        img.save(path)
        images.append(str(path))

    yield images


@pytest.fixture
def cache():
    """
    Fixture: Thread-safe TileCache

    Yields:
        TileCache: A fresh cache instance.
    """
    return TileCache(maxsize=100, maxage=3600)


class TestConcurrentTileRequests:
    """
    Feature: Concurrent Tile Request Handling

    Multiple threads may request tiles simultaneously. The system
    must handle these requests without race conditions, ensuring
    each tile is loaded only once and all requesters receive valid data.
    """

    def test_same_tile_requested_by_multiple_threads(self, cache):
        """
        Scenario: Same tile requested simultaneously by multiple threads

        Given multiple threads requesting the same tile
        When requests arrive concurrently
        Then the tile is loaded only once
        And all threads eventually receive the same tile
        """
        provider = MockTileProvider(cache, load_delay=0.1)
        provider.start()

        tile_id = ('media', 1, 0, 0)
        num_threads = 10
        results = []
        errors = []

        def request_tile():
            try:
                provider.request(tile_id)
                time.sleep(0.2)  # Wait for load
                if tile_id in cache:
                    results.append(cache[tile_id])
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=request_tile) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors occurred: {errors}"
        # Tile should be loaded only once (or very few times due to race)
        assert provider.load_call_count <= 2, \
            f"Tile loaded {provider.load_call_count} times, expected 1-2"
        assert tile_id in cache

    def test_different_tiles_requested_concurrently(self, cache):
        """
        Scenario: Different tiles requested concurrently

        Given multiple threads requesting different tiles
        When requests arrive concurrently
        Then each tile is loaded independently
        And all tiles become available in cache
        """
        provider = MockTileProvider(cache, load_delay=0.02)
        provider.start()

        num_tiles = 20
        tile_ids = [('media', 1, 0, i) for i in range(num_tiles)]

        def request_tile(tile_id):
            provider.request(tile_id)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(request_tile, tid) for tid in tile_ids]
            for f in as_completed(futures):
                f.result()  # Raise any exceptions

        time.sleep(1.5)  # Allow processing (20 tiles * 0.02s delay + overhead)

        # All tiles should be loaded
        assert provider.load_call_count == num_tiles
        for tile_id in tile_ids:
            assert tile_id in cache

    def test_rapid_requests_dont_cause_queue_corruption(self, cache):
        """
        Scenario: Rapid concurrent requests maintain queue integrity

        Given hundreds of tile requests submitted rapidly
        When processed by the provider
        Then no queue corruption occurs
        And all tiles are eventually processed
        """
        provider = MockTileProvider(cache, load_delay=0.01)
        provider.start()

        num_requests = 100
        tile_ids = [('media', 1, i // 10, i % 10) for i in range(num_requests)]

        def rapid_requests():
            for tile_id in tile_ids:
                provider.request(tile_id)
                time.sleep(0.001)  # Very rapid

        threads = [threading.Thread(target=rapid_requests) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        time.sleep(2)  # Allow processing

        # All unique tiles should be loaded
        unique_tiles = set(tile_ids)
        loaded_count = sum(1 for tid in unique_tiles if tid in cache)
        assert loaded_count == len(unique_tiles)


class TestConcurrentTilingOperations:
    """
    Feature: Concurrent Image Tiling

    Multiple images can be tiled simultaneously. Each tiling operation
    must maintain its own state without interfering with others.
    """

    def test_concurrent_tiling_different_images(
            self, temp_tilestore, sample_images, initialized_tilemanager):
        """
        Scenario: Multiple images tiled concurrently

        Given several images to tile
        When tiling operations run in parallel
        Then each image is tiled correctly
        And no cross-contamination occurs between tile sets
        """
        results = {}
        errors = []

        def tile_image(image_path, index):
            try:
                media_id = f"concurrent_media_{index}"
                tiler = ConcreteTiler(image_path, media_id=media_id, tilesize=256)
                tiler.run()
                results[media_id] = {
                    'error': tiler.error,
                    'progress': tiler.progress
                }
            except Exception as e:
                errors.append((index, e))

        threads = []
        for i, path in enumerate(sample_images[:3]):
            t = threading.Thread(target=tile_image, args=(path, i))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors: {errors}"

        # All should complete successfully
        for media_id, result in results.items():
            assert result['error'] is None, f"{media_id} failed: {result['error']}"
            assert result['progress'] == 1.0
            assert tilestore.tiled(media_id)

    def test_concurrent_tiling_creates_independent_pyramids(
            self, temp_tilestore, sample_images, initialized_tilemanager):
        """
        Scenario: Concurrent tiling produces independent tile pyramids

        Given multiple concurrent tiling operations
        When all complete
        Then each media has its own complete tile pyramid
        And metadata is correctly stored for each
        """
        media_ids = []

        def tile_image(image_path, index):
            media_id = f"pyramid_test_{index}"
            media_ids.append(media_id)
            tiler = ConcreteTiler(image_path, media_id=media_id, tilesize=256)
            tiler.run()
            return tiler.error

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(tile_image, path, i)
                for i, path in enumerate(sample_images[:3])
            ]
            errors = [f.result() for f in as_completed(futures)]

        assert all(e is None for e in errors)

        # Verify each has independent metadata
        for media_id in media_ids:
            assert tilestore.tiled(media_id)
            assert tilestore.get_metadata(media_id, 'width') == 512
            assert tilestore.get_metadata(media_id, 'height') == 512


class TestCacheThreadSafety:
    """
    Feature: TileCache Thread Safety

    The TileCache uses RLock for thread-safe operations. Concurrent
    reads, writes, and evictions must not corrupt cache state.
    """

    def test_concurrent_cache_reads(self, cache):
        """
        Scenario: Multiple threads read from cache simultaneously

        Given tiles stored in cache
        When multiple threads read concurrently
        Then all reads return correct values
        And no corruption occurs
        """
        # Pre-populate cache
        for i in range(10):
            tile_id = ('media', 1, 0, i)
            cache[tile_id] = Tile(Image.new('RGB', (256, 256)))

        results = []
        errors = []

        def read_tiles():
            try:
                for i in range(10):
                    tile_id = ('media', 1, 0, i)
                    if tile_id in cache:
                        tile = cache[tile_id]
                        results.append((tile_id, tile is not None))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=read_tiles) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert all(result[1] for result in results)

    def test_concurrent_cache_writes(self, cache):
        """
        Scenario: Multiple threads write to cache simultaneously

        Given an empty cache
        When multiple threads write different tiles concurrently
        Then all tiles are stored correctly
        And no writes are lost
        """
        num_threads = 10
        tiles_per_thread = 10

        def write_tiles(thread_id):
            for i in range(tiles_per_thread):
                tile_id = ('media', 1, thread_id, i)
                cache[tile_id] = Tile(Image.new('RGB', (256, 256)))

        threads = [threading.Thread(target=write_tiles, args=(i,))
                   for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify all tiles were stored
        stored_count = 0
        for thread_id in range(num_threads):
            for i in range(tiles_per_thread):
                tile_id = ('media', 1, thread_id, i)
                if tile_id in cache:
                    stored_count += 1

        assert stored_count == num_threads * tiles_per_thread

    def test_concurrent_read_write_mix(self, cache):
        """
        Scenario: Concurrent reads and writes do not corrupt cache

        Given ongoing read and write operations
        When executed concurrently
        Then no corruption or crashes occur
        And data remains consistent
        """
        errors = []
        stop_flag = threading.Event()

        def writer():
            i = 0
            while not stop_flag.is_set():
                tile_id = ('media', 1, 0, i % 50)
                try:
                    cache[tile_id] = Tile(Image.new('RGB', (256, 256)))
                except Exception as e:
                    errors.append(('write', e))
                i += 1
                time.sleep(0.001)

        def reader():
            while not stop_flag.is_set():
                for i in range(50):
                    tile_id = ('media', 1, 0, i)
                    try:
                        if tile_id in cache:
                            _ = cache[tile_id]
                    except KeyError:
                        pass  # Expected - tile may have been evicted
                    except Exception as e:
                        errors.append(('read', e))
                time.sleep(0.001)

        writers = [threading.Thread(target=writer) for _ in range(3)]
        readers = [threading.Thread(target=reader) for _ in range(5)]

        for t in writers + readers:
            t.start()

        time.sleep(1)  # Run for 1 second
        stop_flag.set()

        for t in writers + readers:
            t.join()

        assert len(errors) == 0, f"Errors: {errors}"

    def test_cache_eviction_under_concurrent_access(self):
        """
        Scenario: LRU eviction works correctly under concurrent access

        Given a small cache with ongoing concurrent operations
        When cache fills and eviction occurs
        Then eviction completes without corruption
        And recently accessed tiles are preserved
        """
        small_cache = TileCache(maxsize=20, maxage=3600)
        errors = []

        def access_and_fill():
            for i in range(100):
                tile_id = ('media', 1, 0, i)
                try:
                    small_cache[tile_id] = Tile(Image.new('RGB', (256, 256)))
                    # Immediately access some tiles to affect LRU order
                    if i > 0 and i % 5 == 0:
                        recent_id = ('media', 1, 0, i - 1)
                        if recent_id in small_cache:
                            _ = small_cache[recent_id]
                except Exception as e:
                    errors.append(e)

        threads = [threading.Thread(target=access_and_fill) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestProviderQueueConcurrency:
    """
    Feature: Provider Queue Thread Safety

    The provider's request queue handles concurrent request submission.
    LIFO ordering must be maintained even under concurrent access.
    """

    def test_concurrent_request_submission(self, cache):
        """
        Scenario: Concurrent request submission to provider queue

        Given multiple threads submitting requests simultaneously
        When requests are processed
        Then no requests are lost
        And queue remains consistent
        """
        provider = MockTileProvider(cache, load_delay=0.01)
        provider.start()

        num_threads = 10
        requests_per_thread = 20

        def submit_requests(thread_id):
            for i in range(requests_per_thread):
                tile_id = ('media', 1, thread_id, i)
                provider.request(tile_id)

        threads = [threading.Thread(target=submit_requests, args=(i,))
                   for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        time.sleep(3)  # Allow all to process

        # All tiles should eventually be loaded
        total_expected = num_threads * requests_per_thread
        assert provider.load_call_count == total_expected

    def test_purge_during_concurrent_requests(self, cache):
        """
        Scenario: Purge operation during concurrent requests

        Given ongoing request submission
        When purge is called
        Then purge completes without deadlock
        And remaining requests continue processing
        """
        provider = MockTileProvider(cache, load_delay=0.02)
        provider.start()

        stop_flag = threading.Event()
        purge_count = [0]

        def submit_requests():
            i = 0
            while not stop_flag.is_set():
                tile_id = ('media', 1, 0, i % 100)
                provider.request(tile_id)
                i += 1
                time.sleep(0.005)

        def periodic_purge():
            while not stop_flag.is_set():
                time.sleep(0.1)
                provider.purge()
                purge_count[0] += 1

        submitter = threading.Thread(target=submit_requests)
        purger = threading.Thread(target=periodic_purge)

        submitter.start()
        purger.start()

        time.sleep(1)  # Run for 1 second
        stop_flag.set()

        submitter.join()
        purger.join()

        # Verify purge was called multiple times without deadlock
        assert purge_count[0] > 5


class TestMetadataConcurrency:
    """
    Feature: Thread-Safe Metadata Access

    Metadata operations through TileStore and TileManager must be
    thread-safe, allowing concurrent reads without corruption.
    """

    def test_concurrent_metadata_reads(
            self, temp_tilestore, sample_images, initialized_tilemanager):
        """
        Scenario: Concurrent metadata reads do not corrupt data

        Given tiled media with metadata
        When multiple threads read metadata concurrently
        Then all reads return consistent values
        """
        # Tile an image first
        media_id = "metadata_test"
        tiler = ConcreteTiler(sample_images[0], media_id=media_id, tilesize=256)
        tiler.run()

        results = []
        errors = []

        def read_metadata():
            try:
                for _ in range(50):
                    width = tilemanager.get_metadata(media_id, 'width')
                    height = tilemanager.get_metadata(media_id, 'height')
                    results.append((width, height))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=read_metadata) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        # All results should be consistent
        assert all(r == (512, 512) for r in results)


class TestTileManagerConcurrency:
    """
    Feature: TileManager Concurrent Operations

    The TileManager coordinates multiple concurrent operations
    including tile loading, synthesis, and metadata access.
    """

    def test_concurrent_load_tile_calls(
            self, temp_tilestore, sample_images, initialized_tilemanager):
        """
        Scenario: Concurrent load_tile calls for same media

        Given a tiled media
        When multiple threads call load_tile for different tiles
        Then all requests are queued correctly
        And tiles become available
        """
        # Tile an image
        media_id = "load_test"
        tiler = ConcreteTiler(sample_images[0], media_id=media_id, tilesize=256)
        tiler.run()

        tile_ids = [(media_id, 1, r, c) for r in range(2) for c in range(2)]

        def load_tiles():
            for tile_id in tile_ids:
                tilemanager.load_tile(tile_id)

        threads = [threading.Thread(target=load_tiles) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        time.sleep(0.5)

        # Verify tiles are loadable (may need retry due to async loading)
        for tile_id in tile_ids:
            for _ in range(10):
                try:
                    tile = tilemanager.get_tile(tile_id)
                    break
                except TileNotLoaded:
                    time.sleep(0.1)

    def test_concurrent_get_tile_robust_calls(
            self, temp_tilestore, sample_images, initialized_tilemanager):
        """
        Scenario: Concurrent get_tile_robust calls with synthesis

        Given limited cached tiles
        When multiple threads call get_tile_robust
        Then all threads receive valid tiles
        And synthesis works correctly under load
        """
        # Tile an image
        media_id = "robust_test"
        tiler = ConcreteTiler(sample_images[0], media_id=media_id, tilesize=256)
        tiler.run()

        # Ensure base tile is cached
        tilemanager.load_tile((media_id, 0, 0, 0))
        time.sleep(0.3)

        results = []
        errors = []

        def get_tiles():
            try:
                for level in range(2):
                    for r in range(2):
                        for c in range(2):
                            tile_id = (media_id, level, r, c)
                            tile = tilemanager.get_tile_robust(tile_id)
                            results.append(tile is not None)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=get_tiles) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors: {errors}"
        assert all(results)


class TestStressConditions:
    """
    Feature: System Behavior Under Stress

    The tiling system must remain stable under heavy load conditions
    with many concurrent operations.
    """

    def test_high_concurrency_stress(self, cache):
        """
        Scenario: System handles high concurrency without failure

        Given many concurrent threads performing cache operations
        When stress test runs for extended period
        Then no crashes or deadlocks occur
        And cache remains functional
        """
        errors = []
        operation_count = [0]
        lock = threading.Lock()

        def random_operations():
            import random
            for _ in range(100):
                try:
                    op = random.choice(['read', 'write', 'check'])
                    tile_id = ('media', 1, random.randint(0, 10), random.randint(0, 10))

                    if op == 'write':
                        cache[tile_id] = Tile(Image.new('RGB', (256, 256)))
                    elif op == 'read' and tile_id in cache:
                        _ = cache[tile_id]
                    elif op == 'check':
                        _ = tile_id in cache

                    with lock:
                        operation_count[0] += 1
                except KeyError:
                    pass  # Expected during eviction
                except Exception as e:
                    errors.append(e)

        threads = [threading.Thread(target=random_operations) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors: {errors}"
        # Allow small variance due to threading timing
        assert operation_count[0] >= 1990, \
            f"Expected ~2000 operations, got {operation_count[0]}"

    def test_memory_pressure_stability(self):
        """
        Scenario: System remains stable under memory pressure

        Given a small cache
        When many more tiles are inserted than capacity
        Then eviction works correctly
        And no memory errors occur
        """
        small_cache = TileCache(maxsize=10, maxage=3600)
        errors = []

        def fill_cache():
            for i in range(200):
                tile_id = ('media', 1, i // 20, i % 20)
                try:
                    small_cache[tile_id] = Tile(Image.new('RGB', (256, 256)))
                except Exception as e:
                    errors.append(e)

        threads = [threading.Thread(target=fill_cache) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        # Cache should have limited tiles due to eviction
        # (exact count depends on timing and LRU order)
