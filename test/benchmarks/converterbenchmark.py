## PyZUI 0.1 - Python Zooming User Interface
## Copyright (C) 2009  David Roberts <d@vidr.cc>
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
## 02110-1301, USA.

"""
Converter Benchmark Module

This module provides benchmarking utilities for measuring the performance
of PyZUI's image conversion, tiling, and zooming operations. It measures:
- Image conversion to PPM format
- Tiling performance and memory consumption
- Zooming performance (cold and warm cache)

Usage:
    python converterbenchmark.py <image_file>

Example:
    python converterbenchmark.py data/sample.jpg
    for file in images/*; do python converterbenchmark.py $file; done
"""

import os
import sys
import tempfile
import time
import shutil
from typing import Tuple

sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))

from PySide6 import QtCore, QtGui, QtWidgets

import pyzui.tilesystem.tilemanager as TileManager
import pyzui.tilesystem.tilestore as TileStore
from pyzui.converters.vipsconverter import VipsConverter
from pyzui.tilesystem.tiler.ppm import PPMTiler, read_ppm_header
from pyzui.objects.scene.qzui import QZUI
import pyzui.objects.scene.scene as Scene
from pyzui.objects.mediaobjects.tiledmediaobject import TiledMediaObject


def mem(size: str = 'rss') -> int:
    """
    Function :
        mem(size)
    Parameters :
        size : str
            - Memory type to measure: 'rss' (resident), 'rsz' (resident+text),
              or 'vsz' (virtual)

    mem(size) --> int

    Get the memory usage of the current process in kilobytes.

    Returns the memory consumption based on the specified memory type:
    - rss: resident memory (default)
    - rsz: resident plus text memory
    - vsz: virtual memory

    Adapted from <http://snipplr.com/view/6460/> by Florian Leitner.
    """
    return int(os.popen("ps -p %d -o %s | tail -1" %
        (os.getpid(), size)).read())


def benchmark(filename: str, ppmfile: str) -> None:
    """
    Function :
        benchmark(filename, ppmfile)
    Parameters :
        filename : str
            - Absolute path to the image file to benchmark
        ppmfile : str
            - Path to temporary PPM file for conversion output

    benchmark(filename, ppmfile) --> None

    Execute comprehensive performance benchmarks on image processing pipeline.

    Measures and reports performance metrics for:
    1. Image conversion from source format to PPM format
    2. Tiling operation with memory consumption tracking
    3. Cold cache zoom performance (first zoom operation)
    4. Warm cache zoom performance (subsequent zoom operation)

    The function prints detailed timing and performance statistics to stdout,
    including conversion time, tiling time with memory consumption, image
    dimensions, and framerate statistics for zoom operations.
    """
    print("Benchmarking %s ..." % os.path.basename(filename))

    base_mem = mem()

    ## Conversion
    converter = VipsConverter(filename, ppmfile)
    start_time = time.time()
    print("Converting to PPM...")
    sys.stdout.flush()
    converter.run()
    end_time = time.time()
    print("Done: took %.2fs" % (end_time - start_time))
    del converter

    ## Metadata extraction
    f = open(ppmfile, 'rb')
    width, height = read_ppm_header(f)
    f.close()
    print("Dimensions: %dx%d, %.2f megapixels" %
          (width, height, width * height * 1e-6))
    del f, width, height

    ## Tiling
    tiler = PPMTiler(ppmfile)
    start_time = time.time()
    print("Tiling...")
    sys.stdout.flush()
    tiler.run()
    end_time = time.time()

    ## Memory usage tracking
    ## Note: Python doesn't necessarily return allocated memory to the OS
    ## (see <http://effbot.org/pyfaq/
    ## why-doesnt-python-release-the-memory-when-i-delete-a-large-object.htm>)
    ## The current memory usage approximates peak memory usage during tiling
    ## It would be better to periodically check memory usage while the tiler
    ## is running and maintain a max value
    end_mem = mem()

    print("Done: took %.2fs consuming %.2fMB RAM" %
          ((end_time - start_time), (end_mem - base_mem) * 1e-3))
    del tiler

    ## Zooming benchmark
    viewport_w = 800
    viewport_h = 600
    print("Viewport: %dx%d" % (viewport_w, viewport_h))

    zoom_amount = 5.0
    print("Zoom amount: %.1f" % zoom_amount)

    qzui = QZUI()
    qzui.framerate = None
    qzui.resize(viewport_w, viewport_h)
    qzui.show()

    scene = Scene.new()
    qzui.scene = scene
    obj = TiledMediaObject(ppmfile, scene, True)
    scene.add(obj)
    obj.fit((0, 0, viewport_w, viewport_h))

    ## Cold cache zoom test
    num_frames = 100
    start_time = time.time()
    print("Zooming (cold)...")
    sys.stdout.flush()

    for i in range(num_frames):
        qzui.repaint()
        scene.centre = (viewport_w/2, viewport_h/2)
        scene.zoom(zoom_amount/num_frames)

    end_time = time.time()
    elapsed = end_time - start_time
    fps = num_frames / elapsed
    print("Done: %d frames took %.2fs, mean framerate %.2f FPS" %
          (num_frames, elapsed, fps))

    ## Warm cache zoom test
    scene.zoom(-zoom_amount)
    num_frames = 100
    start_time = time.time()
    print("Zooming (warm)...")
    sys.stdout.flush()

    for i in range(num_frames):
        qzui.repaint()
        scene.centre = (viewport_w/2, viewport_h/2)
        scene.zoom(zoom_amount/num_frames)

    end_time = time.time()
    elapsed = end_time - start_time
    fps = num_frames / elapsed
    print("Done: %d frames took %.2fs, mean framerate %.2f FPS" %
          (num_frames, elapsed, fps))


def main() -> None:
    """
    Function :
        main()
    Parameters :
        None

    main() --> None

    Entry point for the converter benchmark utility.

    Initializes the tile management system, creates temporary directories
    for tile storage, processes command-line arguments, and executes the
    benchmark suite. Ensures proper cleanup of temporary files and
    directories regardless of success or failure.

    Command-line usage:
        python converterbenchmark.py <image_file>

    The image file path should be provided as the first command-line argument.
    """
    TileManager.init()
    TileStore.tile_dir = tempfile.mkdtemp()
    app = QtWidgets.QApplication(sys.argv)

    if len(sys.argv) < 2:
        print("Error: No image file specified")
        print("Usage: python converterbenchmark.py <image_file>")
        sys.exit(1)

    filename = os.path.abspath(sys.argv[1])

    if not os.path.exists(filename):
        print("Error: File not found: %s" % filename)
        sys.exit(1)

    ppmfile = tempfile.mkstemp('.ppm')[1]

    try:
        benchmark(filename, ppmfile)
    finally:
        ## Cleanup temporary directories and files
        shutil.rmtree(TileStore.tile_dir, ignore_errors=True)
        os.unlink(ppmfile)


if __name__ == '__main__':
    main()
