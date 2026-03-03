## PyZUI - Python Zooming User Interface
## Copyright (C) 2009 David Roberts <d@vidr.cc>
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

"""Process-based tiling execution for parallel image tiling.

This module provides functions to run tilers in separate processes,
avoiding threading conflicts between pyvips, TileManager threads, and Qt.

The multiprocessing context is chosen automatically:

- 'fork': Used when no other threads are running. Fast and clean shutdown.
- 'spawn': Used when other threads exist (fork-after-threads is unsafe).
  This creates a fresh Python interpreter per worker.

The context can be overridden via PYZUI_MP_CONTEXT environment variable.
"""

from concurrent.futures import ProcessPoolExecutor, Future
from typing import Optional, Literal, Dict, Any
import multiprocessing
import threading
import warnings
import atexit
import os


def _get_safe_context():
    """
    Get a multiprocessing context that's safe for the current thread state.

    Returns 'fork' if only the main thread is running (fast, clean shutdown).
    Returns 'spawn' if other threads exist (avoids fork-after-threads issues).

    Python 3.12+ DeprecationWarning about fork() in multi-threaded processes:
    -------------------------------------------------------------------------
    Python 3.12 emits a DeprecationWarning when os.fork() is called while
    multiple threads are active, because forking duplicates the process but
    only the calling thread — leaving any mutex locks held by other threads
    in a permanently locked state, which can cause deadlocks in the child.

    This warning does NOT apply to our use case for the following reasons:

    1. We select 'fork' only when threading.active_count() == 1 (main thread
       only). However, ProcessPoolExecutor spawns workers lazily on the first
       submit() call, and by that time pytest or Qt may have started internal
       threads (e.g., Qt event loop, pytest-xdist workers).

    2. The forked worker processes are safe because they perform fresh imports
       of PPMTiler/Tiler (see _run_tiling) and do not inherit or interact with
       any shared thread state, locks, or Qt objects from the parent process.

    3. The alternative contexts ('spawn', 'forkserver') cause the process pool
       to hang during interpreter shutdown / pytest teardown, making them
       unsuitable. 'fork' provides clean and fast shutdown via the atexit
       handler registered in init().

    We therefore catch this specific DeprecationWarning and log it at debug
    level rather than letting it propagate to the user.
    """
    
    env_context = os.environ.get('PYZUI_MP_CONTEXT')
    if env_context:
        return multiprocessing.get_context(env_context)

    # Check if other threads are running (fork is unsafe with multiple threads)
    if threading.active_count() > 1:
        return multiprocessing.get_context('spawn')
    else:
        return multiprocessing.get_context('fork')


def _run_tiling(infile: str, media_id: Optional[str] = None, 
                filext: str = 'jpg', tilesize: int = 256) -> Optional[str]:
    """
    Run Tiler in a separate process.

    Parameters:
        infile: Path to the source PPM file
        media_id: Media identifier for tile storage (defaults to infile)
        filext: Tile file extension ('jpg' or 'png')
        tilesize: Tile size in pixels

    Returns:
        None on success, error message string on failure
    """
    # Import here to avoid issues with multiprocessing
    from .ppm import PPMTiler
    
    tiler = PPMTiler(infile, media_id, filext, tilesize)
    tiler.run()
    return tiler.error


# Global executor for process-based tiling
_executor: Optional[ProcessPoolExecutor] = None
_executor_context_name: Optional[str] = None
_max_workers: int = 4
_atexit_registered: bool = False

# Thread safety lock for executor management
# Using RLock to allow reentrancy (e.g., _get_executor() -> init() chain)
_executor_lock = threading.RLock()


def init(max_workers: int = 4) -> None:
    """
    Function :
        init(max_workers)
    Parameters :
        max_workers : int
            - Maximum number of parallel tiling processes (default: 4)

    init(max_workers) --> None

    Initialize the tiler runner with a process pool.
    
    Thread-safe: This function uses a reentrant lock to ensure safe concurrent
    initialization and shutdown operations.
    """
    global _executor, _executor_context_name, _max_workers, _atexit_registered
    
    with _executor_lock:
        _max_workers = max_workers

        # Get context appropriate for current thread state
        context = _get_safe_context()
        context_name = context.get_start_method()

        # If executor exists but with different context, shut it down first
        if _executor is not None and _executor_context_name != context_name:
            # Note: shutdown() will acquire the same lock (reentrant)
            shutdown()

        if _executor is None:
            _executor = ProcessPoolExecutor(max_workers=max_workers, mp_context=context)
            _executor_context_name = context_name
            # Register atexit handler to ensure clean shutdown during interpreter finalization
            if not _atexit_registered:
                atexit.register(shutdown)
                _atexit_registered = True


def shutdown() -> None:
    """
    Function :
        shutdown()
    Parameters :
        None

    shutdown() --> None

    Shutdown the process pool executor and terminate any lingering processes.
    
    Thread-safe: This function uses a reentrant lock to ensure safe concurrent
    initialization and shutdown operations.
    """
    global _executor, _executor_context_name
    
    with _executor_lock:
        if _executor is not None:
            # Shutdown the executor - don't wait to avoid blocking
            _executor.shutdown(wait=False, cancel_futures=True)
            _executor = None
            _executor_context_name = None

        # Forcefully terminate any remaining child processes from multiprocessing
        # This prevents hangs during interpreter finalization
        for child in multiprocessing.active_children():
            child.terminate()
            child.join(timeout=1)


def _get_executor() -> ProcessPoolExecutor:
    """
    Function :
        _get_executor()
    Parameters :
        None

    _get_executor() --> ProcessPoolExecutor

    Get or create the process pool executor.
    
    Thread-safe: This function uses a reentrant lock to ensure safe concurrent
    access to the global executor. The lock allows reentrancy for the
    init() -> shutdown() -> init() chain that may occur during context changes.
    
    Returns:
        ProcessPoolExecutor: The global process pool executor instance
    """
    global _executor, _executor_context_name
    
    with _executor_lock:
        # Check if we need to recreate executor due to context change
        context = _get_safe_context()
        context_name = context.get_start_method()

        if _executor is not None and _executor_context_name != context_name:
            # Context changed (e.g., threads were created), need new executor
            # Note: shutdown() will acquire the same lock (reentrant)
            shutdown()

        if _executor is None:
            # Note: init() will acquire the same lock (reentrant)
            init(_max_workers)

        # After init() call, _executor should not be None
        # The type checker doesn't understand our locking guarantees
        assert _executor is not None, "Executor should be initialized after init()"
        return _executor


def submit_tiling(infile: str, media_id: Optional[str] = None,
                  filext: str = 'jpg', tilesize: int = 256) -> Future:
    """
    Submit a tiling job to run in a separate process.

    Parameters:
        infile: Path to the source PPM file
        media_id: Media identifier for tile storage (defaults to infile)
        filext: Tile file extension ('jpg' or 'png')
        tilesize: Tile size in pixels

    Returns:
        A Future object that will contain the tiling result
    """
    executor = _get_executor()
    # Catch the Python 3.12+ DeprecationWarning about fork() in multi-threaded
    # processes. The warning is emitted here because ProcessPoolExecutor spawns
    # workers lazily on the first submit() call, which is when os.fork() runs.
    # See _get_safe_context() docstring for why this is safe in our case.
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=".*multi-threaded.*use of fork\\(\\).*",
            category=DeprecationWarning)
        return executor.submit(_run_tiling, infile, media_id, filext, tilesize)


class TilingHandle:
    """
    A handle to a running or completed tiling process.

    This class wraps a Future and provides a similar interface to the
    thread-based Tiler class, with progress and error properties.
    """

    def __init__(self, future: Future, infile: str, media_id: Optional[str] = None):
        """
        Create a new TilingHandle.

        Parameters:
            future: The Future object from the process pool
            infile: Path to the source file
            media_id: Media identifier for tile storage
        """
        self._future = future
        self._infile = infile
        self._media_id = media_id
        self._error: Optional[str] = None
        self._checked = False

    @property
    def progress(self) -> float:
        """
        Return the tiling progress.

        Since process-based tiling doesn't support incremental progress,
        this returns 0.0 while running and 1.0 when done.
        """
        if self._future.done():
            self._check_result()
            return 1.0
        return 0.0

    @property
    def error(self) -> Optional[str]:
        """Return the error message if tiling failed, None otherwise."""
        if self._future.done():
            self._check_result()
        return self._error

    def _check_result(self) -> None:
        """Check the future result and update error status."""
        if self._checked:
            return
        self._checked = True
        try:
            result = self._future.result()
            if result is not None:
                self._error = result
        except Exception as e:
            self._error = f"tiling process error: {str(e)}"

    def is_alive(self) -> bool:
        """Return True if the tiling is still running."""
        return not self._future.done()

    def join(self, timeout: Optional[float] = None) -> None:
        """Wait for the tiling to complete."""
        try:
            self._future.result(timeout=timeout)
        except Exception:
            pass
        self._check_result()