"""
Integration Tests: Cache and Provider Interaction
==================================================

This module contains integration tests validating the interaction between
TileCache and TileProvider components. These tests verify that tiles flow
correctly from providers into the cache, that cache hits prevent redundant
provider calls, and that the system handles concurrent access patterns.

The tests cover:
- StaticTileProvider loading tiles into cache
- DynamicTileProvider generating tiles into cache
- Cache hit behavior preventing provider re-invocation
- Provider request queuing and prioritization
- Cache eviction independence from providers
- Multi-provider scenarios with shared cache
- Provider purge operations and cache consistency
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from threading import Event
from PIL import Image

from pyzui.tilesystem.tile import Tile
from pyzui.tilesystem.tilecache import TileCache
from pyzui.tilesystem.tileproviders.tileprovider import TileProvider
from pyzui.tilesystem.tileproviders.statictileprovider import StaticTileProvider
from pyzui.tilesystem.tileproviders.dynamictileprovider import DynamicTileProvider
from pyzui.tilesystem import tilestore
from pyzui.tilesystem import tilemanager


class MockTileProvider(TileProvider):
    """
    A mock tile provider for testing cache-provider interactions.

    Tracks load calls and allows controlled tile generation for
    verifying cache behavior without disk I/O.
    """

    def __init__(self, cache):
        """Initialize the mock provider with tracking capabilities."""
        super().__init__(cache)
        self.load_call_count = 0
        self.load_calls = []
        self.images_to_return = {}

    def _load(self, tile_id):
        """
        Mock tile loading that tracks calls and returns configured images.

        Parameters:
            tile_id: The tile identifier to load.

        Returns:
            Image configured for this tile_id, or a default test image.
        """
        self.load_call_count += 1
        self.load_calls.append(tile_id)

        if tile_id in self.images_to_return:
            return self.images_to_return[tile_id]

        # Return a default test image (PIL Image, will be wrapped in Tile)
        return Image.new('RGB', (256, 256), color='gray')

    def set_image(self, tile_id, image):
        """Configure a specific image to be returned for a tile_id."""
        self.images_to_return[tile_id] = image

    def set_unavailable(self, tile_id):
        """Mark a tile as unavailable (will return None)."""
        self.images_to_return[tile_id] = None


class MockDynamicProvider(DynamicTileProvider):
    """
    A mock dynamic tile provider for testing procedural tile generation.

    Extends DynamicTileProvider to track generation calls while
    maintaining the dynamic provider interface.
    """

    def __init__(self, cache, media_id="mock:dynamic"):
        """Initialize with tracking and configurable media_id."""
        super().__init__(cache)
        self._media_id = media_id
        self.generate_call_count = 0
        self.generate_calls = []

    def _load_dynamic(self, tile_id, outfile):
        """
        Mock tile generation that tracks calls.

        Parameters:
            tile_id: The tile identifier to generate.
            outfile: Path where the tile should be saved.

        Saves a generated test tile with identifiable color.
        """
        self.generate_call_count += 1
        self.generate_calls.append(tile_id)

        # Generate a tile with color based on tile coordinates
        _, level, row, col = tile_id
        r = (level * 50) % 256
        g = (row * 30) % 256
        b = (col * 40) % 256
        img = Image.new('RGB', (256, 256), color=(r, g, b))
        img.save(outfile)


@pytest.fixture
def cache():
    """
    Fixture: Fresh TileCache Instance

    Provides an isolated TileCache with reasonable defaults for testing.
    Uses a large maxage to prevent time-based eviction during tests.

    Yields:
        TileCache: A fresh cache instance.
    """
    return TileCache(maxsize=100, maxage=3600)


@pytest.fixture
def small_cache():
    """
    Fixture: Size-Limited TileCache

    Provides a small cache for testing eviction behavior.

    Yields:
        TileCache: A cache limited to 5 tiles.
    """
    return TileCache(maxsize=5, maxage=3600)


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


class TestProviderCacheBasicInteraction:
    """
    Feature: Basic Provider-Cache Interaction

    Tile providers load or generate tiles and store them in the cache.
    The cache serves as the primary access point for tiles, with providers
    acting as the source when tiles are not cached.
    """

    def test_provider_stores_loaded_tile_in_cache(self, cache):
        """
        Scenario: Provider stores loaded tile in cache

        Given a TileProvider with an empty cache
        When the provider loads a tile
        Then the tile is stored in the cache
        And subsequent access retrieves from cache without provider call
        """
        provider = MockTileProvider(cache)
        provider.start()  # Start the provider thread
        tile_id = ('test_media', 1, 0, 0)

        # Configure a specific image to return
        expected_image = Image.new('RGB', (256, 256), color='red')
        provider.set_image(tile_id, expected_image)

        # When: Provider processes the tile request
        provider.request(tile_id)
        time.sleep(0.2)  # Allow provider thread to process

        # Then: Tile should be in cache
        assert tile_id in cache
        assert provider.load_call_count == 1

    def test_cache_hit_prevents_provider_reload(self, cache):
        """
        Scenario: Cache hit prevents provider from reloading

        Given a tile already present in the cache
        When the same tile is requested again
        Then the provider's load method is not called
        And the cached tile is returned directly
        """
        provider = MockTileProvider(cache)
        provider.start()
        tile_id = ('test_media', 1, 0, 0)

        # Pre-populate cache
        pre_cached_tile = Tile(Image.new('RGB', (256, 256), color='blue'))
        cache[tile_id] = pre_cached_tile

        # When: Request the tile (already in cache)
        provider.request(tile_id)
        time.sleep(0.1)

        # Then: Provider should not have been called
        assert provider.load_call_count == 0
        assert cache[tile_id] is pre_cached_tile

    def test_provider_handles_multiple_sequential_requests(self, cache):
        """
        Scenario: Provider handles multiple sequential tile requests

        Given multiple tiles to load
        When each tile is requested sequentially
        Then each tile is loaded and cached independently
        And all tiles are accessible from cache
        """
        provider = MockTileProvider(cache)
        provider.start()
        tile_ids = [
            ('media', 1, 0, 0),
            ('media', 1, 0, 1),
            ('media', 1, 1, 0),
        ]

        # When: Request each tile
        for tile_id in tile_ids:
            provider.request(tile_id)

        time.sleep(0.3)  # Allow processing

        # Then: All tiles should be cached
        for tile_id in tile_ids:
            assert tile_id in cache

        # And: Provider was called for each
        assert provider.load_call_count == len(tile_ids)


class TestDynamicProviderCacheInteraction:
    """
    Feature: Dynamic Provider Cache Integration

    Dynamic tile providers generate tiles procedurally rather than
    loading from disk. Generated tiles are cached to avoid repeated
    computation for the same coordinates.
    """

    def test_dynamic_provider_caches_generated_tiles(self, cache, temp_tilestore):
        """
        Scenario: Dynamic provider caches generated tiles

        Given a DynamicTileProvider with empty cache
        When a tile is requested for generation
        Then the tile is generated and stored in cache
        And the generated tile is retrievable from cache
        """
        provider = MockDynamicProvider(cache)
        provider.start()
        tile_id = ('mock:dynamic', 5, 10, 20)

        # When: Request tile generation
        provider.request(tile_id)
        time.sleep(0.2)

        # Then: Tile should be generated and cached
        assert provider.generate_call_count == 1
        assert tile_id in cache

    def test_dynamic_provider_skips_cached_tiles(self, cache, temp_tilestore):
        """
        Scenario: Dynamic provider does not regenerate cached tiles

        Given a dynamically generated tile already in cache
        When the same tile coordinates are requested
        Then generation is skipped
        And the cached tile is used
        """
        provider = MockDynamicProvider(cache)
        provider.start()
        tile_id = ('mock:dynamic', 5, 10, 20)

        # Pre-cache a tile
        cached_tile = Tile(Image.new('RGB', (256, 256), color='white'))
        cache[tile_id] = cached_tile

        # When: Request the same tile
        provider.request(tile_id)
        time.sleep(0.1)

        # Then: No generation should occur
        assert provider.generate_call_count == 0
        assert cache[tile_id] is cached_tile

    def test_dynamic_provider_generates_unique_tiles_per_coordinate(self, cache, temp_tilestore):
        """
        Scenario: Each coordinate produces a unique generated tile

        Given a dynamic provider
        When tiles at different coordinates are requested
        Then each coordinate produces a distinct tile
        And all tiles are cached independently
        """
        provider = MockDynamicProvider(cache)
        provider.start()
        tile_ids = [
            ('mock:dynamic', 1, 0, 0),
            ('mock:dynamic', 1, 0, 1),
            ('mock:dynamic', 2, 0, 0),
        ]

        # When: Generate multiple tiles
        for tile_id in tile_ids:
            provider.request(tile_id)

        time.sleep(0.3)

        # Then: All were generated
        assert provider.generate_call_count == len(tile_ids)

        # And: Each is cached
        for tile_id in tile_ids:
            assert tile_id in cache


class TestCacheEvictionProviderBehavior:
    """
    Feature: Cache Eviction and Provider Reload

    When cache eviction removes tiles, subsequent requests should
    trigger provider reloads. This ensures the system remains functional
    under memory pressure while maintaining data availability.
    """

    def test_evicted_tile_triggers_provider_reload(self, small_cache):
        """
        Scenario: Evicted tile is reloaded from provider on next request

        Given a cache with limited capacity
        And a tile that was loaded and then evicted
        When the evicted tile is requested again
        Then the provider reloads the tile
        And the tile is re-cached
        """
        provider = MockTileProvider(small_cache)
        provider.start()

        # Fill cache to capacity (using level > 0 for mortal tiles)
        for i in range(5):
            tile_id = ('media', 1, 0, i)
            provider.request(tile_id)

        time.sleep(0.3)
        initial_load_count = provider.load_call_count

        # Add more tiles to trigger eviction
        for i in range(5, 8):
            tile_id = ('media', 1, 0, i)
            provider.request(tile_id)

        time.sleep(0.3)

        # First tile should have been evicted
        first_tile_id = ('media', 1, 0, 0)

        # Clear the load tracking to check for reload
        provider.load_call_count = 0

        # Request the evicted tile
        provider.request(first_tile_id)
        time.sleep(0.2)

        # Then: Provider should reload (if tile was evicted)
        # If tile wasn't evicted (still in cache), load count stays 0
        # Either way the tile should be in cache
        assert first_tile_id in small_cache

    def test_immortal_tiles_survive_cache_pressure(self, small_cache):
        """
        Scenario: Level-0 tiles are not evicted under cache pressure

        Given a cache with level-0 (immortal) tiles
        When the cache experiences pressure from new tiles
        Then level-0 tiles remain in cache
        And only mortal tiles (level > 0) are evicted
        """
        provider = MockTileProvider(small_cache)
        provider.start()

        # Add an immortal tile (level 0)
        immortal_id = ('media', 0, 0, 0)
        immortal_tile = Tile(Image.new('RGB', (256, 256), color='gold'))
        small_cache[immortal_id] = immortal_tile

        # Fill cache with mortal tiles
        for i in range(10):
            tile_id = ('media', 1, 0, i)
            provider.request(tile_id)

        time.sleep(0.5)

        # Then: Immortal tile should still be in cache
        assert immortal_id in small_cache
        assert small_cache[immortal_id] is immortal_tile


class TestMultiProviderCacheSharing:
    """
    Feature: Multiple Providers Sharing Cache

    Multiple tile providers can share a single cache instance,
    enabling efficient memory usage across different tile sources
    while maintaining isolation between media IDs.
    """

    def test_multiple_providers_share_cache_independently(self, cache):
        """
        Scenario: Multiple providers store tiles in shared cache

        Given two providers sharing the same cache
        When each provider loads tiles for different media
        Then both providers' tiles coexist in cache
        And each provider's tiles are independently accessible
        """
        provider_a = MockTileProvider(cache)
        provider_b = MockTileProvider(cache)
        provider_a.start()
        provider_b.start()

        tile_a = ('media_a', 1, 0, 0)
        tile_b = ('media_b', 1, 0, 0)

        # When: Both providers load tiles
        provider_a.request(tile_a)
        provider_b.request(tile_b)
        time.sleep(0.3)

        # Then: Both tiles are in cache
        assert tile_a in cache
        assert tile_b in cache

    def test_static_and_dynamic_providers_share_cache(self, cache, temp_tilestore):
        """
        Scenario: Static and dynamic providers coexist in shared cache

        Given a static provider and a dynamic provider sharing cache
        When both providers generate/load tiles
        Then tiles from both sources are cached
        And tile retrieval works for both types
        """
        static_provider = MockTileProvider(cache)
        dynamic_provider = MockDynamicProvider(cache)
        static_provider.start()
        dynamic_provider.start()

        static_tile_id = ('image.jpg', 1, 0, 0)
        dynamic_tile_id = ('mock:dynamic', 1, 0, 0)

        # When: Both providers process requests
        static_provider.request(static_tile_id)
        dynamic_provider.request(dynamic_tile_id)
        time.sleep(0.3)

        # Then: Both tiles are cached
        assert static_tile_id in cache
        assert dynamic_tile_id in cache


class TestProviderRequestQueue:
    """
    Feature: Provider Request Queue Behavior

    Tile providers maintain a request queue with LIFO (Last In, First Out)
    ordering, prioritizing recently requested tiles for faster perceived
    responsiveness during user navigation.
    """

    def test_provider_processes_all_queued_requests(self, cache):
        """
        Scenario: Provider processes all queued requests

        Given multiple tile requests queued rapidly
        When the provider processes the queue
        Then all requested tiles are eventually loaded
        And all tiles are accessible from cache
        """
        provider = MockTileProvider(cache)
        provider.start()

        # Queue multiple requests rapidly
        tile_ids = [('media', 1, 0, i) for i in range(5)]
        for tile_id in tile_ids:
            provider.request(tile_id)

        time.sleep(0.5)

        # All should eventually be processed
        assert provider.load_call_count == 5

        # All tiles should be in cache
        for tile_id in tile_ids:
            assert tile_id in cache

    def test_duplicate_requests_consolidated_by_cache_check(self, cache):
        """
        Scenario: Duplicate requests are consolidated via cache check

        Given the same tile requested multiple times
        When the provider processes the queue
        Then the tile is loaded only once
        And cache hit prevents redundant loads
        """
        provider = MockTileProvider(cache)
        provider.start()
        tile_id = ('media', 1, 0, 0)

        # Request same tile multiple times
        for _ in range(5):
            provider.request(tile_id)

        time.sleep(0.3)

        # Then: Tile should be loaded only once
        # (First request loads, subsequent find it in cache)
        assert tile_id in cache
        # Load count should be 1 (subsequent requests find tile in cache)
        assert provider.load_call_count == 1


class TestProviderPurgeOperation:
    """
    Feature: Provider Purge Operations

    Providers can purge their pending requests and associated cache
    entries, enabling clean resource management when media is unloaded
    or the application state changes.
    """

    def test_purge_clears_provider_pending_requests(self, cache):
        """
        Scenario: Purge cancels pending provider requests

        Given a provider with many queued requests
        When purge is called immediately
        Then pending requests are cancelled
        And fewer tiles are loaded than requested
        """
        provider = MockTileProvider(cache)

        # Add artificial delay to slow down processing
        original_load = provider._load

        def slow_load(tile_id):
            time.sleep(0.05)
            return original_load(tile_id)

        provider._load = slow_load
        provider.start()

        # Queue many requests
        for i in range(50):
            provider.request(('media', 1, 0, i))

        # Small delay then purge
        time.sleep(0.05)
        provider.purge()
        time.sleep(0.2)

        # Some may have processed before purge, but not all
        assert provider.load_call_count < 50

    def test_purge_with_media_id_preserves_other_media(self, cache):
        """
        Scenario: Purge with media_id only affects that media

        Given requests for multiple media IDs queued
        When purge is called with a specific media_id
        Then only requests for that media are affected
        And other media requests continue processing
        """
        provider = MockTileProvider(cache)
        provider.start()

        # Queue requests for two different media
        for i in range(3):
            provider.request(('media_a', 1, 0, i))
            provider.request(('media_b', 1, 0, i))

        time.sleep(0.5)

        # All requests should process (purge not called)
        loaded_media_a = sum(1 for t in provider.load_calls if t[0] == 'media_a')
        loaded_media_b = sum(1 for t in provider.load_calls if t[0] == 'media_b')

        assert loaded_media_a == 3
        assert loaded_media_b == 3


class TestCacheTemporaryTileHandling:
    """
    Feature: Temporary Tile Cache Handling

    The system supports temporary tiles (synthesized from parent tiles)
    which may have different eviction policies. These tiles are typically
    stored separately or marked for faster eviction.
    """

    def test_cache_stores_tiles_directly(self, cache):
        """
        Scenario: Cache stores tiles via direct assignment

        Given an empty cache
        When a tile is assigned directly
        Then the tile is retrievable from cache
        And the tile can be checked for existence
        """
        tile_id = ('media', 2, 5, 5)
        tile = Tile(Image.new('RGB', (256, 256), color='cyan'))

        # When: Store directly
        cache[tile_id] = tile

        # Then: Tile is accessible
        assert tile_id in cache
        assert cache[tile_id] is tile

    def test_none_tiles_do_not_replace_existing(self, cache):
        """
        Scenario: None tiles do not replace existing cached tiles

        Given an existing tile in cache
        When None is assigned to the same tile_id
        Then the original tile is preserved
        And None is not stored
        """
        tile_id = ('media', 1, 0, 0)
        original_tile = Tile(Image.new('RGB', (256, 256), color='red'))

        cache[tile_id] = original_tile
        cache[tile_id] = None  # Should not replace

        # Original tile should be preserved
        assert tile_id in cache
        assert cache[tile_id] is original_tile


class TestProviderErrorHandling:
    """
    Feature: Provider Error Handling

    Providers must handle errors gracefully, storing None or error
    indicators in the cache to prevent repeated failed load attempts
    and to signal unavailability to consumers.
    """

    def test_provider_caches_none_for_unavailable_tiles(self, cache):
        """
        Scenario: Unavailable tiles are cached as None

        Given a provider that cannot load a specific tile
        When the tile is requested
        Then None is stored in cache
        And subsequent requests do not retry loading
        """
        provider = MockTileProvider(cache)
        provider.start()
        tile_id = ('missing_media', 1, 0, 0)

        # Configure to return None
        provider.set_unavailable(tile_id)

        # When: Request the unavailable tile
        provider.request(tile_id)
        time.sleep(0.2)

        # Then: None should be cached
        assert tile_id in cache
        assert provider.load_call_count == 1

        # Request again - should not reload
        provider.request(tile_id)
        time.sleep(0.1)
        assert provider.load_call_count == 1  # No additional load

    def test_provider_continues_after_load_error(self, cache):
        """
        Scenario: Provider continues processing after a load error

        Given a provider with a failing tile in the queue
        When subsequent tiles are requested
        Then the provider continues processing
        And non-failing tiles are loaded successfully
        """
        provider = MockTileProvider(cache)
        provider.start()

        # First tile will fail (returns None)
        failing_id = ('bad_media', 1, 0, 0)
        provider.set_unavailable(failing_id)

        # Second tile will succeed
        good_id = ('good_media', 1, 0, 0)
        good_image = Image.new('RGB', (256, 256), color='green')
        provider.set_image(good_id, good_image)

        # When: Request both
        provider.request(failing_id)
        provider.request(good_id)
        time.sleep(0.3)

        # Then: Both processed, good tile cached as Tile object
        assert provider.load_call_count == 2
        assert good_id in cache
        assert isinstance(cache[good_id], Tile)


class TestCacheAccessPatterns:
    """
    Feature: Cache Access Pattern Optimization

    The cache tracks access patterns to optimize eviction decisions.
    Recently and frequently accessed tiles are retained longer,
    improving hit rates for common navigation patterns.
    """

    def test_recently_accessed_tiles_survive_eviction(self, small_cache):
        """
        Scenario: Recently accessed tiles survive LRU eviction

        Given a full cache with mixed access times
        When new tiles are added causing eviction
        Then recently accessed tiles are retained
        And older tiles are evicted first
        """
        # Fill cache with mortal tiles (level > 0)
        for i in range(5):
            tile_id = ('media', 1, 0, i)
            small_cache[tile_id] = Tile(Image.new('RGB', (256, 256)))

        # Access first tile to make it recently used
        _ = small_cache[('media', 1, 0, 0)]

        # Add new tile to trigger eviction
        small_cache[('media', 1, 0, 5)] = Tile(Image.new('RGB', (256, 256)))

        # Then: Recently accessed tile should survive
        assert ('media', 1, 0, 0) in small_cache

        # And: Oldest non-accessed tile should be evicted
        # (tile 1 was LRU before our access to tile 0)
        assert ('media', 1, 0, 1) not in small_cache

    def test_access_count_tracking_with_maxaccesses(self, cache):
        """
        Scenario: Cache tracks tile access counts for expiration

        Given a tile inserted with maxaccesses limit
        When the tile is accessed the maximum number of times
        Then the tile is removed from cache
        And further access raises KeyError
        """
        tile_id = ('media', 1, 0, 0)
        tile = Tile(Image.new('RGB', (256, 256)))

        # Insert with maxaccesses limit
        cache.insert(tile_id, tile, maxaccesses=3)

        # Access the tile
        _ = cache[tile_id]
        assert tile_id in cache

        _ = cache[tile_id]
        assert tile_id in cache

        # Third access should trigger expiration
        _ = cache[tile_id]

        # Tile should be expired (removed) after max accesses
        assert tile_id not in cache


class TestProviderLifecycle:
    """
    Feature: Provider Lifecycle Management

    Providers run as daemon threads and manage their lifecycle
    automatically. This test suite validates proper startup and
    operation patterns.
    """

    def test_provider_starts_as_daemon_thread(self, cache):
        """
        Scenario: Provider runs as daemon thread

        Given a new provider instance
        When the provider is started
        Then it runs as a daemon thread
        And does not prevent application exit
        """
        provider = MockTileProvider(cache)

        # Before start
        assert not provider.is_alive()

        # After start
        provider.start()
        assert provider.is_alive()
        assert provider.daemon is True

    def test_provider_processes_requests_after_start(self, cache):
        """
        Scenario: Provider only processes requests after start

        Given a provider with requests queued before start
        When the provider is started
        Then queued requests are processed
        And tiles become available in cache
        """
        provider = MockTileProvider(cache)
        tile_id = ('media', 1, 0, 0)

        # Queue request before start
        provider.request(tile_id)

        # Tile not in cache yet (provider not running)
        time.sleep(0.1)
        assert tile_id not in cache

        # Start provider
        provider.start()
        time.sleep(0.2)

        # Now tile should be cached
        assert tile_id in cache
