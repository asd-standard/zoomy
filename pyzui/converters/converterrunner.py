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

"""Process-based converter execution for parallel media conversion.

This module provides functions to run converters in separate processes,
avoiding threading conflicts between pyvips and TileManager threads.

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
import atexit
import os


def _get_safe_context():
    """
    Get a multiprocessing context that's safe for the current thread state.

    Returns 'fork' if only the main thread is running (fast, clean shutdown).
    Returns 'spawn' if other threads exist (avoids fork-after-threads issues).
    """
    env_context = os.environ.get('PYZUI_MP_CONTEXT')
    if env_context:
        return multiprocessing.get_context(env_context)

    # Check if other threads are running (fork is unsafe with multiple threads)
    if threading.active_count() > 1:
        return multiprocessing.get_context('spawn')
    else:
        return multiprocessing.get_context('fork')


def _run_vips_conversion(infile: str, outfile: str,
                         rotation: int = 0,
                         invert_colors: bool = False,
                         black_and_white: bool = False) -> Optional[str]:
    """
    Run VipsConverter in a separate process.

    Parameters:
        infile: Path to the source image file
        outfile: Path where the converted PPM will be written
        rotation: Rotation angle in degrees (0, 90, 180, or 270)
        invert_colors: Enable color inversion when True
        black_and_white: Enable grayscale conversion when True

    Returns:
        None on success, error message string on failure
    """
    # Import here to avoid issues with multiprocessing
    from pyzui.converters.vipsconverter import VipsConverter

    converter = VipsConverter(infile, outfile, rotation, invert_colors, black_and_white)
    converter.run()
    return converter.error


def _run_pdf_conversion(infile: str, outfile: str) -> Optional[str]:
    """
    Run PDFConverter in a separate process.

    Parameters:
        infile: Path to the source PDF file
        outfile: Path where the rasterized PPM will be written

    Returns:
        None on success, error message string on failure
    """
    # Import here to avoid issues with multiprocessing
    from pyzui.converters.pdfconverter import PDFConverter

    converter = PDFConverter(infile, outfile)
    converter.run()
    return converter.error


# Global executor for process-based conversion
_executor: Optional[ProcessPoolExecutor] = None
_executor_context_name: Optional[str] = None
_max_workers: int = 8
_atexit_registered: bool = False


def init(max_workers: int = 8) -> None:
    """
    Initialize the converter runner with a process pool.

    Parameters:
        max_workers: Maximum number of parallel conversion processes
    """
    global _executor, _executor_context_name, _max_workers, _atexit_registered
    _max_workers = max_workers

    # Get context appropriate for current thread state
    context = _get_safe_context()
    context_name = context.get_start_method()

    # If executor exists but with different context, shut it down first
    if _executor is not None and _executor_context_name != context_name:
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
    Shutdown the process pool executor and terminate any lingering processes.
    """
    global _executor, _executor_context_name
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
    """Get or create the process pool executor."""
    global _executor, _executor_context_name

    # Check if we need to recreate executor due to context change
    context = _get_safe_context()
    context_name = context.get_start_method()

    if _executor is not None and _executor_context_name != context_name:
        # Context changed (e.g., threads were created), need new executor
        shutdown()

    if _executor is None:
        init(_max_workers)

    return _executor


def submit_vips_conversion(infile: str, outfile: str,
                           rotation: int = 0,
                           invert_colors: bool = False,
                           black_and_white: bool = False) -> Future:
    """
    Submit a VipsConverter job to run in a separate process.

    Parameters:
        infile: Path to the source image file
        outfile: Path where the converted PPM will be written
        rotation: Rotation angle in degrees (0, 90, 180, or 270)
        invert_colors: Enable color inversion when True
        black_and_white: Enable grayscale conversion when True

    Returns:
        A Future object that will contain the conversion result
    """
    executor = _get_executor()
    return executor.submit(_run_vips_conversion, infile, outfile,
                          rotation, invert_colors, black_and_white)


def submit_pdf_conversion(infile: str, outfile: str) -> Future:
    """
    Submit a PDFConverter job to run in a separate process.

    Parameters:
        infile: Path to the source PDF file
        outfile: Path where the rasterized PPM will be written

    Returns:
        A Future object that will contain the conversion result
    """
    executor = _get_executor()
    return executor.submit(_run_pdf_conversion, infile, outfile)


class ConversionHandle:
    """
    A handle to a running or completed conversion process.

    This class wraps a Future and provides a similar interface to the
    thread-based Converter class, with progress and error properties.
    """

    def __init__(self, future: Future, infile: str, outfile: str):
        """
        Create a new ConversionHandle.

        Parameters:
            future: The Future object from the process pool
            infile: Path to the source file
            outfile: Path to the output file
        """
        self._future = future
        self._infile = infile
        self._outfile = outfile
        self._error: Optional[str] = None
        self._checked = False

    @property
    def progress(self) -> float:
        """
        Return the conversion progress.

        Since process-based conversion doesn't support incremental progress,
        this returns 0.0 while running and 1.0 when done.
        """
        if self._future.done():
            self._check_result()
            return 1.0
        return 0.0

    @property
    def error(self) -> Optional[str]:
        """Return the error message if conversion failed, None otherwise."""
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
            self._error = f"conversion process error: {str(e)}"

    def is_alive(self) -> bool:
        """Return True if the conversion is still running."""
        return not self._future.done()

    def join(self, timeout: Optional[float] = None) -> None:
        """Wait for the conversion to complete."""
        try:
            self._future.result(timeout=timeout)
        except Exception:
            pass
        self._check_result()
