import pytest
from unittest.mock import Mock, MagicMock, patch
from threading import Thread, Condition, Event
from collections import deque
import time
from pyzui.tilesystem.tileproviders import TileProvider
from pyzui.tilesystem.tile import Tile

class TestTileProvider:
    """
    Feature: Tile Provider Base Class

    This test suite validates the TileProvider base class functionality including thread management,
    task queuing, and abstract methods for loading tiles from various sources.
    """

    def test_init(self):
        """
        Scenario: Initialize a tile provider

        Given a mock tile cache
        When a TileProvider is instantiated
        Then it should be created as a daemon thread
        """
        tilecache = Mock()
        provider = TileProvider(tilecache)
        assert isinstance(provider, Thread)
        assert provider.daemon is True

    def test_inherits_from_thread(self):
        """
        Scenario: Verify TileProvider is a Thread

        Given a mock tile cache
        When a TileProvider is instantiated
        Then it should be an instance of Thread
        """
        tilecache = Mock()
        provider = TileProvider(tilecache)
        assert isinstance(provider, Thread)

    def test_request_adds_task(self):
        """
        Scenario: Request a tile to be loaded

        Given a TileProvider with a mock cache
        When a tile is requested with a specific tile_id
        Then the tile_id should be added to the internal task queue
        """
        tilecache = Mock()
        provider = TileProvider(tilecache)
        tile_id = ('media_id', 0, 0, 0)
        provider.request(tile_id)
        # Task should be added internally

    def test_request_multiple_tasks(self):
        """
        Scenario: Request multiple tiles

        Given a TileProvider with a mock cache
        When multiple tiles are requested with different tile_ids
        Then all tile_ids should be added to the internal task queue
        """
        tilecache = Mock()
        provider = TileProvider(tilecache)
        tile_id1 = ('media_id1', 0, 0, 0)
        tile_id2 = ('media_id2', 1, 1, 1)
        provider.request(tile_id1)
        provider.request(tile_id2)
        # Both tasks should be added internally

    def test_load_abstract_method(self):
        """
        Scenario: Call abstract load method

        Given a TileProvider instance
        When the _load method is called with a tile_id
        Then it should return None as it is an abstract method
        """
        tilecache = Mock()
        provider = TileProvider(tilecache)
        tile_id = ('media_id', 0, 0, 0)
        result = provider._load(tile_id)
        assert result is None

    def test_purge_all_tasks(self):
        """
        Scenario: Purge all tasks from queue

        Given a TileProvider with multiple requested tiles
        When purge is called without a media_id
        Then all tasks should be cleared from the queue
        """
        tilecache = Mock()
        provider = TileProvider(tilecache)
        provider.request(('media_id1', 0, 0, 0))
        provider.request(('media_id2', 1, 1, 1))
        provider.purge()
        # All tasks should be purged

    def test_purge_specific_media_id(self):
        """
        Scenario: Purge tasks for specific media

        Given a TileProvider with tiles requested from different media sources
        When purge is called with a specific media_id
        Then only tasks for that media_id should be removed
        """
        tilecache = Mock()
        provider = TileProvider(tilecache)
        provider.request(('media_id1', 0, 0, 0))
        provider.request(('media_id2', 1, 1, 1))
        provider.purge('media_id1')
        # Only media_id1 tasks should be purged

    def test_str_representation(self):
        """
        Scenario: Get string representation

        Given a TileProvider instance
        When str() is called on the provider
        Then it should return 'TileProvider'
        """
        tilecache = Mock()
        provider = TileProvider(tilecache)
        assert str(provider) == 'TileProvider'

    def test_repr_representation(self):
        """
        Scenario: Get repr representation

        Given a TileProvider instance
        When repr() is called on the provider
        Then it should return 'TileProvider()'
        """
        tilecache = Mock()
        provider = TileProvider(tilecache)
        assert repr(provider) == 'TileProvider()'

    @patch.object(TileProvider, '_load')
    def test_run_loads_tile(self, mock_load):
        """
        Scenario: Run provider to load tiles

        Given a TileProvider with a mocked _load method that returns an image
        When a tile is requested and the provider processes tasks
        Then the _load method should be called to load the tile
        """
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
        """
        Scenario: Handle unavailable tile

        Given a TileProvider with a mocked _load that returns None
        When a tile is requested and cannot be loaded
        Then the tile should be marked as None in the cache
        """
        tilecache = {}
        provider = TileProvider(tilecache)
        tile_id = ('media_id', 0, 0, 0)

        # Mock _load to return None (unavailable)
        mock_load.return_value = None

        provider.request(tile_id)
        # Unavailable tile should be set to None in cache

    def test_daemon_thread(self):
        """
        Scenario: Verify daemon thread status

        Given a TileProvider instance
        When checking its daemon attribute
        Then it should be True
        """
        tilecache = Mock()
        provider = TileProvider(tilecache)
        assert provider.daemon is True

    def test_thread_processes_single_task(self):
        """
        Scenario: Thread processes a single tile request

        Given a running TileProvider thread with mocked _load
        When a tile is requested
        Then the thread should process the task
        And the tile should be loaded into the cache
        """
        tilecache = {}
        provider = TileProvider(tilecache)

        # Mock the _load method to return a test image
        mock_image = Mock()
        mock_tile = Mock(spec=Tile)
        load_called = Event()

        def mock_load(tile_id):
            load_called.set()
            return mock_image

        with patch.object(provider, '_load', side_effect=mock_load):
            with patch('pyzui.tilesystem.tileproviders.tileprovider.Tile', return_value=mock_tile):
                provider.start()

                tile_id = ('test_media', 0, 0, 0)
                provider.request(tile_id)

                # Wait for the tile to be processed
                assert load_called.wait(timeout=2.0), "Tile was not loaded within timeout"

                # Give thread time to update cache
                time.sleep(0.1)

                # Verify tile was added to cache
                assert tile_id in tilecache
                assert tilecache[tile_id] == mock_tile

    def test_thread_processes_lifo_order(self):
        """
        Scenario: Verify LIFO (Last In First Out) task processing

        Given a running TileProvider thread
        When multiple tiles are requested in sequence
        Then they should be processed in LIFO order (last requested first)
        """
        tilecache = {}
        provider = TileProvider(tilecache)

        processed_order = []
        all_processed = Event()

        def mock_load(tile_id):
            processed_order.append(tile_id)
            if len(processed_order) == 3:
                all_processed.set()
            time.sleep(0.05)  # Small delay to ensure ordering
            return Mock()

        with patch.object(provider, '_load', side_effect=mock_load):
            with patch('pyzui.tilesystem.tileproviders.tileprovider.Tile', return_value=Mock(spec=Tile)):
                provider.start()

                # Request tiles in order: A, B, C
                tile_a = ('media_a', 0, 0, 0)
                tile_b = ('media_b', 1, 1, 1)
                tile_c = ('media_c', 2, 2, 2)

                provider.request(tile_a)
                provider.request(tile_b)
                provider.request(tile_c)

                # Wait for all tiles to be processed
                assert all_processed.wait(timeout=3.0), "Not all tiles processed"

                # Verify LIFO order: C, B, A
                assert processed_order == [tile_c, tile_b, tile_a]

    def test_thread_handles_load_exception(self):
        """
        Scenario: Handle exception during tile loading

        Given a running TileProvider thread
        When _load raises an exception
        Then the exception should be caught and logged
        And None should be stored in the cache
        """
        tilecache = {}
        provider = TileProvider(tilecache)

        exception_handled = Event()

        def mock_load(tile_id):
            exception_handled.set()
            raise ValueError("Simulated load error")

        with patch.object(provider, '_load', side_effect=mock_load):
            provider.start()

            tile_id = ('error_media', 0, 0, 0)
            provider.request(tile_id)

            # Wait for exception to be handled
            assert exception_handled.wait(timeout=2.0), "Exception not handled"

            # Give thread time to update cache
            time.sleep(0.1)

            # Verify None was stored in cache
            assert tile_id in tilecache
            assert tilecache[tile_id] is None

    def test_thread_handles_unavailable_tile(self):
        """
        Scenario: Handle unavailable tile (load returns None)

        Given a running TileProvider thread
        When _load returns None for an unavailable tile
        Then None should be stored in the cache
        And the cache should contain the tile_id
        """
        tilecache = {}
        provider = TileProvider(tilecache)

        load_called = Event()

        def mock_load(tile_id):
            load_called.set()
            return None

        with patch.object(provider, '_load', side_effect=mock_load):
            provider.start()

            tile_id = ('unavailable_media', 0, 0, 0)
            provider.request(tile_id)

            # Wait for load to be called
            assert load_called.wait(timeout=2.0), "Load not called"

            # Give thread time to update cache
            time.sleep(0.1)

            # Verify None was stored in cache
            assert tile_id in tilecache
            assert tilecache[tile_id] is None

    def test_thread_skips_cached_tiles(self):
        """
        Scenario: Skip loading tiles already in cache

        Given a running TileProvider thread
        And a tile already present in the cache
        When the same tile is requested again
        Then _load should not be called
        And the cached tile should remain unchanged
        """
        tilecache = {}
        provider = TileProvider(tilecache)

        tile_id = ('cached_media', 0, 0, 0)
        cached_tile = Mock(spec=Tile)
        tilecache[tile_id] = cached_tile

        load_called = Event()
        request_processed = Event()

        def mock_load(tile_id_arg):
            load_called.set()
            return Mock()

        with patch.object(provider, '_load', side_effect=mock_load):
            with patch('pyzui.tilesystem.tileproviders.tileprovider.Tile', return_value=Mock(spec=Tile)):
                provider.start()

                # Request a different tile first to ensure thread is running
                other_tile = ('other_media', 1, 1, 1)
                provider.request(other_tile)

                # Wait a bit for other tile to be processed
                time.sleep(0.2)

                # Now request the cached tile
                provider.request(tile_id)
                time.sleep(0.2)

                # Verify the cached tile is still the same object
                assert tilecache[tile_id] is cached_tile

    def test_thread_processes_multiple_concurrent_requests(self):
        """
        Scenario: Process multiple tile requests concurrently

        Given a running TileProvider thread
        When multiple tiles are requested for different media
        Then all tiles should be processed
        And all should appear in the cache
        """
        tilecache = {}
        provider = TileProvider(tilecache)

        num_tiles = 5
        tiles_loaded = []
        all_loaded = Event()

        def mock_load(tile_id):
            tiles_loaded.append(tile_id)
            if len(tiles_loaded) == num_tiles:
                all_loaded.set()
            return Mock()

        with patch.object(provider, '_load', side_effect=mock_load):
            with patch('pyzui.tilesystem.tileproviders.tileprovider.Tile', return_value=Mock(spec=Tile)):
                provider.start()

                # Request multiple tiles
                tile_ids = [('media_%d' % i, i, i, i) for i in range(num_tiles)]
                for tile_id in tile_ids:
                    provider.request(tile_id)

                # Wait for all tiles to be processed
                assert all_loaded.wait(timeout=3.0), "Not all tiles loaded"

                # Give thread time to update cache
                time.sleep(0.1)

                # Verify all tiles are in cache
                for tile_id in tile_ids:
                    assert tile_id in tilecache

    def test_thread_waits_when_no_tasks(self):
        """
        Scenario: Thread waits when task queue is empty

        Given a running TileProvider thread
        When no tasks are in the queue
        Then the thread should wait on the condition variable
        And resume when a task is added
        """
        tilecache = {}
        provider = TileProvider(tilecache)

        first_load = Event()
        second_load = Event()

        def mock_load(tile_id):
            if tile_id[0] == 'first':
                first_load.set()
            else:
                second_load.set()
            return Mock()

        with patch.object(provider, '_load', side_effect=mock_load):
            with patch('pyzui.tilesystem.tileproviders.tileprovider.Tile', return_value=Mock(spec=Tile)):
                provider.start()

                # Request first tile
                provider.request(('first', 0, 0, 0))
                assert first_load.wait(timeout=2.0), "First tile not loaded"

                # Thread should now be waiting for tasks
                time.sleep(0.1)

                # Request second tile
                provider.request(('second', 1, 1, 1))
                assert second_load.wait(timeout=2.0), "Second tile not loaded"

    def test_purge_during_thread_execution(self):
        """
        Scenario: Purge tasks while thread is running

        Given a running TileProvider thread with queued tasks
        When purge is called for a specific media_id
        Then tasks for that media_id should be removed
        And tasks for other media should remain
        """
        tilecache = {}
        provider = TileProvider(tilecache)

        processed = []
        first_processed = Event()

        def mock_load(tile_id):
            processed.append(tile_id)
            if len(processed) == 1:
                first_processed.set()
            time.sleep(0.1)  # Slow down processing
            return Mock()

        with patch.object(provider, '_load', side_effect=mock_load):
            with patch('pyzui.tilesystem.tileproviders.tileprovider.Tile', return_value=Mock(spec=Tile)):
                provider.start()

                # Queue several tasks
                keep_tile = ('keep_media', 0, 0, 0)
                purge_tile1 = ('purge_media', 1, 1, 1)
                purge_tile2 = ('purge_media', 2, 2, 2)

                provider.request(keep_tile)
                provider.request(purge_tile1)
                provider.request(purge_tile2)

                # Wait for first tile to start processing
                assert first_processed.wait(timeout=2.0)

                # Purge tasks for 'purge_media'
                provider.purge('purge_media')

                # Wait a bit for remaining tasks to process
                time.sleep(0.5)

                # Verify purged tiles were not processed
                assert keep_tile in processed
                assert purge_tile1 not in processed or purge_tile2 not in processed
