import pytest
import time
from unittest.mock import Mock, patch
from pyzui.tilesystem.tilestore.tilecache import TileCache

class TestTileCache:
    """
    Feature: Tile Cache Management

    The TileCache class maintains a two-tier cache system for tiles, managing
    memory usage through size limits and age-based eviction. It provides LRU
    (Least Recently Used) eviction, access counting, and special handling for
    immortal tiles (None tiles and level-0 tiles).
    """

    def test_init_default(self):
        """
        Scenario: Initialize cache with default parameters

        Given no custom parameters are provided
        When a TileCache is created
        Then maxsize should be 256 tiles
        And maxage should be 60 seconds
        """
        cache = TileCache()
        assert cache._TileCache__maxsize == 256
        assert cache._TileCache__maxage == 60

    def test_init_custom_params(self):
        """
        Scenario: Initialize cache with custom parameters

        Given custom maxsize of 128 and maxage of 30
        When a TileCache is created
        Then maxsize should be 128 tiles
        And maxage should be 30 seconds
        """
        cache = TileCache(maxsize=128, maxage=30)
        assert cache._TileCache__maxsize == 128
        assert cache._TileCache__maxage == 30

    def test_init_no_size_limit(self):
        """
        Scenario: Initialize cache with unlimited size

        Given maxsize of 0
        When a TileCache is created
        Then maxsize should be 0 (unlimited)
        """
        cache = TileCache(maxsize=0)
        assert cache._TileCache__maxsize == 0

    def test_init_no_age_limit(self):
        """
        Scenario: Initialize cache with no age expiration

        Given maxage of 0
        When a TileCache is created
        Then maxage should be 0 (no expiration)
        """
        cache = TileCache(maxage=0)
        assert cache._TileCache__maxage == 0

    def test_setitem_getitem(self):
        """
        Scenario: Store and retrieve a tile

        Given an empty tile cache
        And a tile with ID ('media1', 1, 0, 0)
        When the tile is stored using dict-style assignment
        Then the tile should be retrievable using the same ID
        And the retrieved tile should be the same object
        """
        cache = TileCache()
        tile_id = ('media1', 1, 0, 0)
        tile = Mock()
        cache[tile_id] = tile
        assert cache[tile_id] == tile

    def test_getitem_nonexistent(self):
        """
        Scenario: Attempt to retrieve non-existent tile

        Given an empty tile cache
        When retrieving a tile ID that doesn't exist
        Then a KeyError should be raised
        """
        cache = TileCache()
        with pytest.raises(KeyError):
            _ = cache[('nonexistent', 1, 0, 0)]

    def test_contains(self):
        """
        Scenario: Check tile existence in cache

        Given an empty tile cache
        When checking if a tile ID is in the cache
        Then it should return False
        When a tile is stored with that ID
        Then checking should return True
        """
        cache = TileCache()
        tile_id = ('media1', 1, 0, 0)
        tile = Mock()

        assert tile_id not in cache
        cache[tile_id] = tile
        assert tile_id in cache

    def test_delitem(self):
        """
        Scenario: Delete a tile from cache

        Given a cache containing a tile
        When the tile is deleted using del operator
        Then the tile should no longer be in the cache
        """
        cache = TileCache()
        tile_id = ('media1', 1, 0, 0)
        tile = Mock()

        cache[tile_id] = tile
        assert tile_id in cache

        del cache[tile_id]
        assert tile_id not in cache

    def test_insert_basic(self):
        """
        Scenario: Insert tile using insert method

        Given an empty cache
        When insert is called with a tile ID and tile
        Then the tile should be stored and retrievable
        """
        cache = TileCache()
        tile_id = ('media1', 1, 0, 0)
        tile = Mock()
        cache.insert(tile_id, tile)
        assert cache[tile_id] == tile

    def test_insert_with_maxaccesses(self):
        """
        Scenario: Insert tile with access limit

        Given an empty cache
        When insert is called with maxaccesses=3
        Then the tile should be stored with an access limit
        """
        cache = TileCache()
        tile_id = ('media1', 1, 0, 0)
        tile = Mock()
        cache.insert(tile_id, tile, maxaccesses=3)
        assert cache[tile_id] == tile

    def test_maxaccesses_expiration(self):
        """
        Scenario: Tile expires after maxaccesses

        Given a cache with a tile having maxaccesses=2
        When the tile is accessed once
        Then the tile should still be in cache
        When the tile is accessed a second time
        Then the tile should be automatically removed
        """
        cache = TileCache()
        tile_id = ('media1', 1, 0, 0)
        tile = Mock()
        cache.insert(tile_id, tile, maxaccesses=2)

        # Access once
        _ = cache[tile_id]
        assert tile_id in cache

        # Access twice - should expire
        _ = cache[tile_id]
        assert tile_id not in cache

    def test_none_tile_immortal(self):
        """
        Scenario: None tiles are protected from eviction

        Given a cache with maxsize=1
        And a None tile stored in the cache
        When multiple other tiles are added exceeding maxsize
        Then the None tile should remain in cache
        """
        cache = TileCache(maxsize=1)
        none_tile_id = ('media1', 1, 0, 0)
        cache[none_tile_id] = None

        # Add more tiles to exceed maxsize
        cache[('media2', 1, 0, 0)] = Mock()
        cache[('media3', 1, 0, 0)] = Mock()

        # None tile should still be there
        assert none_tile_id in cache

    def test_zero_level_tile_immortal(self):
        """
        Scenario: Level-0 tiles are protected from eviction

        Given a cache with maxsize=1
        And a tile at level 0 (0, 0, 0)
        When multiple other tiles are added exceeding maxsize
        Then the level-0 tile should remain in cache
        """
        cache = TileCache(maxsize=1)
        zero_tile_id = ('media1', 0, 0, 0)
        cache[zero_tile_id] = Mock()

        # Add more tiles to exceed maxsize
        cache[('media2', 1, 0, 0)] = Mock()
        cache[('media3', 1, 0, 0)] = Mock()

        # Zero-level tile should still be there
        assert zero_tile_id in cache

    def test_lru_eviction(self):
        """
        Scenario: Least recently used tiles are evicted

        Given a cache with maxsize=2
        And two tiles already stored
        When a third tile is added
        Then the oldest tile should be evicted
        And the two most recent tiles should remain
        """
        cache = TileCache(maxsize=2)
        tile1_id = ('media1', 1, 0, 0)
        tile2_id = ('media2', 1, 0, 0)
        tile3_id = ('media3', 1, 0, 0)

        cache[tile1_id] = Mock()
        cache[tile2_id] = Mock()
        cache[tile3_id] = Mock()

        # tile1 should have been evicted
        assert tile1_id not in cache
        assert tile2_id in cache
        assert tile3_id in cache

    def test_purge(self):
        """
        Scenario: Purge all tiles from cache

        Given a cache containing multiple tiles
        When purge is called
        Then all tiles should be removed from cache
        """
        cache = TileCache()
        cache[('media1', 1, 0, 0)] = Mock()
        cache[('media2', 1, 0, 0)] = Mock()
        cache[('media3', 1, 0, 0)] = Mock()

        cache.purge()

        assert ('media1', 1, 0, 0) not in cache
        assert ('media2', 1, 0, 0) not in cache
        assert ('media3', 1, 0, 0) not in cache

    def test_dont_replace_existing_with_none(self):
        """
        Scenario: Existing tiles are not replaced with None

        Given a cache containing a real tile
        When attempting to store None with the same ID
        Then the original tile should remain
        And not be replaced with None
        """
        cache = TileCache()
        tile_id = ('media1', 1, 0, 0)
        tile = Mock()

        cache[tile_id] = tile
        cache[tile_id] = None

        # Original tile should still be there
        assert cache[tile_id] == tile

    def test_access_updates_lru(self):
        """
        Scenario: Accessing a tile updates LRU ordering

        Given a cache with maxsize=2 containing two tiles
        When the first tile is accessed
        Then it becomes recently used
        When a third tile is added
        Then the second tile should be evicted (not the first)
        """
        cache = TileCache(maxsize=2)
        tile1_id = ('media1', 1, 0, 0)
        tile2_id = ('media2', 1, 0, 0)
        tile3_id = ('media3', 1, 0, 0)

        cache[tile1_id] = Mock()
        cache[tile2_id] = Mock()

        # Access tile1 to make it recently used
        _ = cache[tile1_id]

        # Add tile3, should evict tile2 instead of tile1
        cache[tile3_id] = Mock()

        assert tile1_id in cache
        assert tile2_id not in cache
        assert tile3_id in cache

    def test_thread_safety(self):
        """
        Scenario: Cache operations are thread-safe

        Given a tile cache
        When basic operations are performed
        Then they should complete without errors

        Note: This is a basic smoke test. Full threading tests
        would require concurrent access simulation.
        """
        cache = TileCache()
        tile_id = ('media1', 1, 0, 0)
        tile = Mock()

        # Basic test - actual threading tests would be more complex
        cache[tile_id] = tile
        assert cache[tile_id] == tile
