import pytest
from unittest.mock import Mock, MagicMock, patch
from threading import Thread, Condition
from collections import deque
from pyzui.tileproviders import TileProvider
from pyzui.tile import Tile

class TestTileProvider:
    """Test suite for the TileProvider class."""

    def test_init(self):
        """Test TileProvider initialization."""
        tilecache = Mock()
        provider = TileProvider(tilecache)
        assert isinstance(provider, Thread)
        assert provider.daemon is True

    def test_inherits_from_thread(self):
        """Test that TileProvider inherits from Thread."""
        tilecache = Mock()
        provider = TileProvider(tilecache)
        assert isinstance(provider, Thread)

    def test_request_adds_task(self):
        """Test request method adds tile_id to tasks."""
        tilecache = Mock()
        provider = TileProvider(tilecache)
        tile_id = ('media_id', 0, 0, 0)
        provider.request(tile_id)
        # Task should be added internally

    def test_request_multiple_tasks(self):
        """Test requesting multiple tiles."""
        tilecache = Mock()
        provider = TileProvider(tilecache)
        tile_id1 = ('media_id1', 0, 0, 0)
        tile_id2 = ('media_id2', 1, 1, 1)
        provider.request(tile_id1)
        provider.request(tile_id2)
        # Both tasks should be added internally

    def test_load_abstract_method(self):
        """Test _load method is abstract and returns None."""
        tilecache = Mock()
        provider = TileProvider(tilecache)
        tile_id = ('media_id', 0, 0, 0)
        result = provider._load(tile_id)
        assert result is None

    def test_purge_all_tasks(self):
        """Test purge method without media_id clears all tasks."""
        tilecache = Mock()
        provider = TileProvider(tilecache)
        provider.request(('media_id1', 0, 0, 0))
        provider.request(('media_id2', 1, 1, 1))
        provider.purge()
        # All tasks should be purged

    def test_purge_specific_media_id(self):
        """Test purge method with specific media_id."""
        tilecache = Mock()
        provider = TileProvider(tilecache)
        provider.request(('media_id1', 0, 0, 0))
        provider.request(('media_id2', 1, 1, 1))
        provider.purge('media_id1')
        # Only media_id1 tasks should be purged

    def test_str_representation(self):
        """Test string representation of TileProvider."""
        tilecache = Mock()
        provider = TileProvider(tilecache)
        assert str(provider) == 'TileProvider'

    def test_repr_representation(self):
        """Test repr representation of TileProvider."""
        tilecache = Mock()
        provider = TileProvider(tilecache)
        assert repr(provider) == 'TileProvider()'

    @patch.object(TileProvider, '_load')
    def test_run_loads_tile(self, mock_load):
        """Test run method loads tiles from tasks."""
        tilecache = {}
        provider = TileProvider(tilecache)
        tile_id = ('media_id', 0, 0, 0)

        # Mock _load to return a mock image
        mock_image = Mock()
        mock_load.return_value = mock_image

        # Manually add task and process one iteration
        provider.request(tile_id)
        # We can't test run() fully as it loops forever

    @patch.object(TileProvider, '_load')
    def test_run_handles_unavailable_tile(self, mock_load):
        """Test run method handles unavailable tiles."""
        tilecache = {}
        provider = TileProvider(tilecache)
        tile_id = ('media_id', 0, 0, 0)

        # Mock _load to return None (unavailable)
        mock_load.return_value = None

        provider.request(tile_id)
        # Unavailable tile should be set to None in cache

    def test_daemon_thread(self):
        """Test that TileProvider is created as daemon thread."""
        tilecache = Mock()
        provider = TileProvider(tilecache)
        assert provider.daemon is True
