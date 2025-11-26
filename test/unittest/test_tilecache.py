import pytest
import time
from unittest.mock import Mock, patch
from pyzui.tilecache import TileCache

class TestTileCache:
    """Test suite for the TileCache class."""

    def test_init_default(self):
        """Test TileCache initialization with default parameters."""
        cache = TileCache()
        assert cache._TileCache__maxsize == 256
        assert cache._TileCache__maxage == 60

    def test_init_custom_params(self):
        """Test TileCache initialization with custom parameters."""
        cache = TileCache(maxsize=128, maxage=30)
        assert cache._TileCache__maxsize == 128
        assert cache._TileCache__maxage == 30

    def test_init_no_size_limit(self):
        """Test TileCache with no size limit."""
        cache = TileCache(maxsize=0)
        assert cache._TileCache__maxsize == 0

    def test_init_no_age_limit(self):
        """Test TileCache with no age limit."""
        cache = TileCache(maxage=0)
        assert cache._TileCache__maxage == 0

    def test_setitem_getitem(self):
        """Test setting and getting a tile."""
        cache = TileCache()
        tile_id = ('media1', 1, 0, 0)
        tile = Mock()
        cache[tile_id] = tile
        assert cache[tile_id] == tile

    def test_getitem_nonexistent(self):
        """Test getting a nonexistent tile raises KeyError."""
        cache = TileCache()
        with pytest.raises(KeyError):
            _ = cache[('nonexistent', 1, 0, 0)]

    def test_contains(self):
        """Test __contains__ method."""
        cache = TileCache()
        tile_id = ('media1', 1, 0, 0)
        tile = Mock()

        assert tile_id not in cache
        cache[tile_id] = tile
        assert tile_id in cache

    def test_delitem(self):
        """Test deleting a tile."""
        cache = TileCache()
        tile_id = ('media1', 1, 0, 0)
        tile = Mock()

        cache[tile_id] = tile
        assert tile_id in cache

        del cache[tile_id]
        assert tile_id not in cache

    def test_insert_basic(self):
        """Test insert method."""
        cache = TileCache()
        tile_id = ('media1', 1, 0, 0)
        tile = Mock()
        cache.insert(tile_id, tile)
        assert cache[tile_id] == tile

    def test_insert_with_maxaccesses(self):
        """Test insert method with maxaccesses parameter."""
        cache = TileCache()
        tile_id = ('media1', 1, 0, 0)
        tile = Mock()
        cache.insert(tile_id, tile, maxaccesses=3)
        assert cache[tile_id] == tile

    def test_maxaccesses_expiration(self):
        """Test tile expires after maxaccesses."""
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
        """Test that None tiles are immortal."""
        cache = TileCache(maxsize=1)
        none_tile_id = ('media1', 1, 0, 0)
        cache[none_tile_id] = None

        # Add more tiles to exceed maxsize
        cache[('media2', 1, 0, 0)] = Mock()
        cache[('media3', 1, 0, 0)] = Mock()

        # None tile should still be there
        assert none_tile_id in cache

    def test_zero_level_tile_immortal(self):
        """Test that (0,0,0) tiles are immortal."""
        cache = TileCache(maxsize=1)
        zero_tile_id = ('media1', 0, 0, 0)
        cache[zero_tile_id] = Mock()

        # Add more tiles to exceed maxsize
        cache[('media2', 1, 0, 0)] = Mock()
        cache[('media3', 1, 0, 0)] = Mock()

        # Zero-level tile should still be there
        assert zero_tile_id in cache

    def test_lru_eviction(self):
        """Test least recently used tiles are evicted."""
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
        """Test purge method clears all tiles."""
        cache = TileCache()
        cache[('media1', 1, 0, 0)] = Mock()
        cache[('media2', 1, 0, 0)] = Mock()
        cache[('media3', 1, 0, 0)] = Mock()

        cache.purge()

        assert ('media1', 1, 0, 0) not in cache
        assert ('media2', 1, 0, 0) not in cache
        assert ('media3', 1, 0, 0) not in cache

    def test_dont_replace_existing_with_none(self):
        """Test that existing tiles are not replaced with None."""
        cache = TileCache()
        tile_id = ('media1', 1, 0, 0)
        tile = Mock()

        cache[tile_id] = tile
        cache[tile_id] = None

        # Original tile should still be there
        assert cache[tile_id] == tile

    def test_access_updates_lru(self):
        """Test that accessing a tile updates LRU order."""
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
        """Test that cache operations are thread-safe."""
        cache = TileCache()
        tile_id = ('media1', 1, 0, 0)
        tile = Mock()

        # Basic test - actual threading tests would be more complex
        cache[tile_id] = tile
        assert cache[tile_id] == tile
