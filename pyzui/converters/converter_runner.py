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

Uses 'spawn' start method to ensure fresh Python interpreter in each
subprocess, avoiding issues with forked pyvips state.
"""

from concurrent.futures import ProcessPoolExecutor, Future
from typing import Optional, Literal, Dict, Any
import multiprocessing
import os

# Use 'spawn' context to avoid forking issues with pyvips
# 'spawn' creates a fresh Python interpreter, avoiding inherited state
_mp_context = multiprocessing.get_context('spawn')


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
_max_workers: int = 8


def init(max_workers: int = 8) -> None:
    """
    Initialize the converter runner with a process pool.

    Parameters:
        max_workers: Maximum number of parallel conversion processes
    """
    global _executor, _max_workers
    _max_workers = max_workers
    if _executor is None:
        # Use spawn context to create fresh Python interpreters
        _executor = ProcessPoolExecutor(max_workers=max_workers, mp_context=_mp_context)


def shutdown() -> None:
    """
    Shutdown the process pool executor.
    """
    global _executor
    if _executor is not None:
        _executor.shutdown(wait=True)
        _executor = None


def _get_executor() -> ProcessPoolExecutor:
    """Get or create the process pool executor."""
    global _executor
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
