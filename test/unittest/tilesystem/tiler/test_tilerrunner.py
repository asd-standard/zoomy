## PyZUI - Python Zooming User Interface
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 3
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <https://www.gnu.org/licenses/>.

import pytest
import threading
import os
from unittest.mock import Mock, patch, MagicMock, call
from concurrent.futures import Future, ProcessPoolExecutor
import multiprocessing

from pyzui.tilesystem.tiler import tilerrunner


@pytest.fixture(autouse=True)
def reset_tilerrunner_state():
    """
    Fixture: Reset Tiler Runner State
    
    Reset the global state of the tilerrunner module before each test
    to ensure test isolation.
    """
    # Save original state
    original_executor = tilerrunner._executor
    original_context_name = tilerrunner._executor_context_name
    original_max_workers = tilerrunner._max_workers
    original_atexit_registered = tilerrunner._atexit_registered
    
    # Reset to initial state
    tilerrunner._executor = None
    tilerrunner._executor_context_name = None
    tilerrunner._max_workers = 4
    tilerrunner._atexit_registered = False
    
    yield
    
    # Restore original state (though tests should clean up)
    tilerrunner._executor = original_executor
    tilerrunner._executor_context_name = original_context_name
    tilerrunner._max_workers = original_max_workers
    tilerrunner._atexit_registered = original_atexit_registered


class TestTilerRunnerContextSelection:
    """
    Feature: Tiler Runner Context Selection

    The tiler runner automatically selects the appropriate multiprocessing
    context based on thread count and environment variables to ensure safe
    process creation for parallel tiling operations.
    """

    @patch('pyzui.tilesystem.tiler.tilerrunner.threading.active_count')
    @patch('pyzui.tilesystem.tiler.tilerrunner.multiprocessing.get_context')
    def test_get_safe_context_single_thread(self, mock_get_context, mock_active_count):
        """
        Scenario: Select fork context when only main thread is running

        Given a single-threaded environment (only main thread)
        When _get_safe_context is called
        Then it should return 'fork' context
        And multiprocessing.get_context should be called with 'fork'
        """
        mock_active_count.return_value = 1
        mock_context = Mock()
        mock_get_context.return_value = mock_context
        mock_context.get_start_method.return_value = 'fork'

        # Clear environment variable to test default behavior
        with patch.dict(os.environ, {}, clear=True):
            result = tilerrunner._get_safe_context()

        mock_get_context.assert_called_once_with('fork')
        assert result == mock_context

    @patch('pyzui.tilesystem.tiler.tilerrunner.threading.active_count')
    @patch('pyzui.tilesystem.tiler.tilerrunner.multiprocessing.get_context')
    def test_get_safe_context_multiple_threads(self, mock_get_context, mock_active_count):
        """
        Scenario: Select spawn context when multiple threads are running

        Given a multi-threaded environment (more than one thread)
        When _get_safe_context is called
        Then it should return 'spawn' context
        And multiprocessing.get_context should be called with 'spawn'
        """
        mock_active_count.return_value = 3
        mock_context = Mock()
        mock_get_context.return_value = mock_context
        mock_context.get_start_method.return_value = 'spawn'

        with patch.dict(os.environ, {}, clear=True):
            result = tilerrunner._get_safe_context()

        mock_get_context.assert_called_once_with('spawn')
        assert result == mock_context

    @patch('pyzui.tilesystem.tiler.tilerrunner.threading.active_count')
    @patch('pyzui.tilesystem.tiler.tilerrunner.multiprocessing.get_context')
    def test_get_safe_context_env_override(self, mock_get_context, mock_active_count):
        """
        Scenario: Environment variable overrides context selection

        Given PYZUI_MP_CONTEXT environment variable is set to 'forkserver'
        When _get_safe_context is called
        Then it should return the context specified by environment variable
        And thread count should not be checked
        """
        mock_context = Mock()
        mock_get_context.return_value = mock_context
        mock_context.get_start_method.return_value = 'forkserver'

        with patch.dict(os.environ, {'PYZUI_MP_CONTEXT': 'forkserver'}):
            result = tilerrunner._get_safe_context()

        mock_get_context.assert_called_once_with('forkserver')
        mock_active_count.assert_not_called()
        assert result == mock_context


class TestTilerRunnerLifecycle:
    """
    Feature: Tiler Runner Lifecycle Management

    The tiler runner manages the lifecycle of the process pool executor,
    including initialization, shutdown, and context-aware reinitialization
    for parallel tiling operations.
    """

    @patch('pyzui.tilesystem.tiler.tilerrunner.ProcessPoolExecutor')
    @patch('pyzui.tilesystem.tiler.tilerrunner._get_safe_context')
    @patch('pyzui.tilesystem.tiler.tilerrunner.atexit.register')
    def test_init_creates_executor(self, mock_atexit, mock_get_context, mock_executor_class):
        """
        Scenario: Initialize creates process pool executor

        Given no existing executor
        When init is called with max_workers parameter
        Then a ProcessPoolExecutor should be created with correct parameters
        And atexit handler should be registered
        """
        mock_context = Mock()
        mock_context.get_start_method.return_value = 'fork'
        mock_get_context.return_value = mock_context
        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor

        # Ensure clean state
        tilerrunner.shutdown()

        tilerrunner.init(max_workers=6)

        mock_get_context.assert_called_once()
        mock_executor_class.assert_called_once_with(max_workers=6, mp_context=mock_context)
        mock_atexit.assert_called_once_with(tilerrunner.shutdown)

    @patch('pyzui.tilesystem.tiler.tilerrunner.ProcessPoolExecutor')
    @patch('pyzui.tilesystem.tiler.tilerrunner._get_safe_context')
    def test_shutdown_cleans_up(self, mock_get_context, mock_executor_class):
        """
        Scenario: Shutdown terminates executor and child processes

        Given an initialized executor
        When shutdown is called
        Then executor should be shut down with wait=False
        And child processes should be terminated
        """
        mock_context = Mock()
        mock_context.get_start_method.return_value = 'fork'
        mock_get_context.return_value = mock_context
        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor

        # Initialize first
        tilerrunner.init(max_workers=4)

        # Mock active_children
        mock_child1 = Mock()
        mock_child2 = Mock()
        with patch('pyzui.tilesystem.tiler.tilerrunner.multiprocessing.active_children') as mock_active:
            mock_active.return_value = [mock_child1, mock_child2]
            tilerrunner.shutdown()

        # Verify executor shutdown
        mock_executor.shutdown.assert_called_once_with(wait=False, cancel_futures=True)
        
        # Verify child process termination
        mock_child1.terminate.assert_called_once()
        mock_child1.join.assert_called_once_with(timeout=1)
        mock_child2.terminate.assert_called_once()
        mock_child2.join.assert_called_once_with(timeout=1)

    @patch('pyzui.tilesystem.tiler.tilerrunner.ProcessPoolExecutor')
    @patch('pyzui.tilesystem.tiler.tilerrunner._get_safe_context')
    def test_get_executor_lazy_initialization(self, mock_get_context, mock_executor_class):
        """
        Scenario: Executor is lazily initialized on first use

        Given no initialized executor
        When _get_executor is called
        Then init should be called to create executor
        And executor should be returned
        """
        mock_context = Mock()
        mock_context.get_start_method.return_value = 'fork'
        mock_get_context.return_value = mock_context
        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor

        # Mock init to set our mock executor
        with patch.object(tilerrunner, 'init') as mock_init:
            # When init is called, it should set _executor
            def set_executor(*args, **kwargs):
                tilerrunner._executor = mock_executor
                tilerrunner._executor_context_name = 'fork'
            mock_init.side_effect = set_executor
            
            result = tilerrunner._get_executor()

        mock_init.assert_called_once()
        assert result == mock_executor

    @patch('pyzui.tilesystem.tiler.tilerrunner.ProcessPoolExecutor')
    @patch('pyzui.tilesystem.tiler.tilerrunner._get_safe_context')
    def test_context_change_recreates_executor(self, mock_get_context, mock_executor_class):
        """
        Scenario: Executor is recreated when context changes

        Given an initialized executor with 'fork' context
        When context changes to 'spawn' (simulated by different get_start_method)
        Then shutdown should be called
        And new executor should be created with new context
        """
        # First call: fork context
        mock_context_fork = Mock()
        mock_context_fork.get_start_method.return_value = 'fork'
        
        # Second call: spawn context (simulating thread creation)
        mock_context_spawn = Mock()
        mock_context_spawn.get_start_method.return_value = 'spawn'
        
        mock_get_context.side_effect = [mock_context_fork, mock_context_spawn]
        
        mock_executor1 = Mock()
        mock_executor2 = Mock()
        mock_executor_class.side_effect = [mock_executor1, mock_executor2]

        # Initialize with fork context
        tilerrunner.init(max_workers=4)
        
        # Simulate context change by calling _get_executor which will detect change
        with patch.object(tilerrunner, 'shutdown') as mock_shutdown:
            tilerrunner._get_executor()
            
            # shutdown should be called due to context change
            mock_shutdown.assert_called_once()


class TestTilerRunnerThreadSafety:
    """
    Feature: Tiler Runner Thread Safety

    The tiler runner uses reentrant locks to ensure thread-safe access
    to the global executor, preventing race conditions during concurrent
    tiling submission operations.
    """

    @patch('pyzui.tilesystem.tiler.tilerrunner.ProcessPoolExecutor')
    @patch('pyzui.tilesystem.tiler.tilerrunner._get_safe_context')
    def test_concurrent_submit_operations(self, mock_get_context, mock_executor_class):
        """
        Scenario: Multiple threads can submit tiling jobs concurrently

        Given an initialized executor
        When multiple threads call submit_tiling simultaneously
        Then all submissions should complete without race conditions
        And executor.submit should be called for each submission
        """
        mock_context = Mock()
        mock_context.get_start_method.return_value = 'fork'
        mock_get_context.return_value = mock_context
        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor
        
        # Mock Future objects
        mock_future1 = Mock(spec=Future)
        mock_future2 = Mock(spec=Future)
        mock_future3 = Mock(spec=Future)
        mock_executor.submit.side_effect = [mock_future1, mock_future2, mock_future3]

        # Initialize executor
        tilerrunner.init(max_workers=4)

        results = []
        errors = []
        
        def submit_tiling_job(index):
            try:
                future = tilerrunner.submit_tiling(
                    f"input_{index}.ppm", 
                    media_id=f"media_{index}",
                    filext='jpg',
                    tilesize=256
                )
                results.append((index, future))
            except Exception as e:
                errors.append((index, str(e)))

        # Create and start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=submit_tiling_job, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5)
            assert not thread.is_alive(), f"Thread {thread} timed out"

        # Verify no errors occurred
        assert len(errors) == 0, f"Errors occurred during concurrent submission: {errors}"
        
        # Verify all submissions completed
        assert len(results) == 3
        assert mock_executor.submit.call_count == 3

    @patch('pyzui.tilesystem.tiler.tilerrunner.ProcessPoolExecutor')
    @patch('pyzui.tilesystem.tiler.tilerrunner._get_safe_context')
    def test_init_shutdown_race_condition(self, mock_get_context, mock_executor_class):
        """
        Scenario: Concurrent init and shutdown operations are thread-safe

        Given multiple threads calling init and shutdown simultaneously
        When operations execute concurrently
        Then no race conditions should occur
        And executor state should remain consistent
        """
        mock_context = Mock()
        mock_context.get_start_method.return_value = 'fork'
        mock_get_context.return_value = mock_context
        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor

        init_called = 0
        shutdown_called = 0
        
        def call_init():
            nonlocal init_called
            tilerrunner.init(max_workers=4)
            init_called += 1
        
        def call_shutdown():
            nonlocal shutdown_called
            tilerrunner.shutdown()
            shutdown_called += 1

        # Start multiple threads calling init and shutdown
        threads = []
        for i in range(5):
            if i % 2 == 0:
                thread = threading.Thread(target=call_init)
            else:
                thread = threading.Thread(target=call_shutdown)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=5)
            assert not thread.is_alive(), f"Thread {thread} timed out"

        # Verify operations completed (exact counts may vary due to timing)
        assert init_called > 0 or shutdown_called > 0, "No operations completed"

    @patch('pyzui.tilesystem.tiler.tilerrunner.ProcessPoolExecutor')
    @patch('pyzui.tilesystem.tiler.tilerrunner._get_safe_context')
    def test_multiple_threads_get_executor(self, mock_get_context, mock_executor_class):
        """
        Scenario: Multiple threads can safely get executor instance

        Given multiple threads calling _get_executor simultaneously
        When executor needs to be initialized
        Then initialization should happen only once
        And all threads should receive same executor instance
        """
        mock_context = Mock()
        mock_context.get_start_method.return_value = 'fork'
        mock_get_context.return_value = mock_context
        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor

        # Ensure clean state
        tilerrunner.shutdown()

        executors = []
        lock = threading.Lock()
        
        def get_executor_and_store():
            executor = tilerrunner._get_executor()
            with lock:
                executors.append(executor)

        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=get_executor_and_store)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=5)
            assert not thread.is_alive(), f"Thread {thread} timed out"

        # Verify all threads got the same executor instance
        assert len(executors) == 5
        first_executor = executors[0]
        for executor in executors[1:]:
            assert executor is first_executor, "All threads should get same executor instance"
        
        # Verify executor was created only once
        assert mock_executor_class.call_count == 1


class TestTilingHandle:
    """
    Feature: Tiling Handle

    The TilingHandle class wraps Future objects from process pool submissions,
    providing a consistent interface for monitoring tiling progress and errors.
    """

    def test_progress_property(self):
        """
        Scenario: Progress property reflects Future state

        Given a TilingHandle with a Future
        When Future is not done
        Then progress should be 0.0
        When Future is done
        Then progress should be 1.0
        """
        mock_future = Mock(spec=Future)
        mock_future.done.return_value = False
        
        handle = tilerrunner.TilingHandle(mock_future, "input.ppm", "media_123")
        
        # Not done -> progress 0.0
        assert handle.progress == 0.0
        
        # Done -> progress 1.0
        mock_future.done.return_value = True
        mock_future.result.return_value = None  # No error
        
        assert handle.progress == 1.0

    def test_error_property(self):
        """
        Scenario: Error property captures tiling failures

        Given a TilingHandle with a Future
        When Future completes with error result
        Then error property should contain error message
        When Future completes successfully
        Then error property should be None
        """
        mock_future = Mock(spec=Future)
        mock_future.done.return_value = True
        
        # Test with error
        error_message = "Tiling failed: invalid PPM format"
        mock_future.result.return_value = error_message
        
        handle = tilerrunner.TilingHandle(mock_future, "input.ppm", "media_123")
        
        assert handle.error == error_message
        
        # Test without error
        mock_future.result.return_value = None
        
        handle2 = tilerrunner.TilingHandle(mock_future, "input2.ppm", "media_456")
        
        assert handle2.error is None

    def test_error_property_future_exception(self):
        """
        Scenario: Error property captures Future exceptions

        Given a TilingHandle with a Future
        When Future.result() raises an exception
        Then error property should contain exception message
        """
        mock_future = Mock(spec=Future)
        mock_future.done.return_value = True
        mock_future.result.side_effect = RuntimeError("Process crashed during tiling")
        
        handle = tilerrunner.TilingHandle(mock_future, "input.ppm", "media_123")
        
        assert "tiling process error" in handle.error
        assert "Process crashed" in handle.error

    def test_join_timeout(self):
        """
        Scenario: Join method waits for completion with timeout

        Given a TilingHandle with a Future
        When join is called with timeout
        Then Future.result should be called with timeout parameter
        """
        mock_future = Mock(spec=Future)
        # Mock result to avoid exception
        mock_future.result.return_value = None

        handle = tilerrunner.TilingHandle(mock_future, "input.ppm", "media_123")
        handle.join(timeout=5.0)

        # join() calls result() with timeout, and _check_result() also calls result()
        # So we expect 2 calls: one with timeout, one without
        assert mock_future.result.call_count == 2
        # First call should be with timeout
        mock_future.result.assert_any_call(timeout=5.0)

    def test_join_no_timeout(self):
        """
        Scenario: Join method waits indefinitely without timeout

        Given a TilingHandle with a Future
        When join is called without timeout
        Then Future.result should be called without timeout parameter
        """
        mock_future = Mock(spec=Future)
        # Mock result to avoid exception
        mock_future.result.return_value = None

        handle = tilerrunner.TilingHandle(mock_future, "input.ppm", "media_123")
        handle.join()

        # join() calls result() without timeout, and _check_result() also calls result()
        # So we expect 2 calls: one without timeout, one without timeout
        assert mock_future.result.call_count == 2
        # First call should be without timeout (default)
        mock_future.result.assert_any_call(timeout=None)

    def test_is_alive(self):
        """
        Scenario: is_alive reflects Future completion state

        Given a TilingHandle with a Future
        When Future is not done
        Then is_alive should return True
        When Future is done
        Then is_alive should return False
        """
        mock_future = Mock(spec=Future)
        mock_future.done.return_value = False
        
        handle = tilerrunner.TilingHandle(mock_future, "input.ppm", "media_123")
        
        assert handle.is_alive() is True
        
        mock_future.done.return_value = True
        
        assert handle.is_alive() is False