.. PyZui converter benchmark instruction file,

Converter Benchmark Documentation
==================================

Overview
--------

The Converter Benchmark is a performance testing tool for PyZUI's image
conversion and tiling pipeline. It measures the complete workflow from
source image to tiled representation, including:

- Image conversion from various formats to PPM
- Tiling operation with memory tracking
- Interactive zoom performance testing

The benchmark provides detailed metrics for conversion time, tiling
performance, memory consumption, and rendering framerates under
zoom operations.

Table of Contents
-----------------

-  :ref:`Quick Start <quick-start-converter>`
-  :ref:`Usage Documentation <usage-documentation-converter>`
   -  :ref:`Basic Usage <basic-usage-converter>`
   -  :ref:`Output Interpretation <output-interpretation-converter>`
-  :ref:`Technical Documentation <technical-documentation-converter>`
   -  :ref:`Benchmark Phases <benchmark-phases-converter>`
   -  :ref:`Functions <functions-converter>`
-  :ref:`Troubleshooting <troubleshooting-converter>`

------------------------------

.. _quick-start-converter:

Quick Start
-----------

Run a benchmark on a single image:

.. code-block:: bash

   cd /path/to/pyzui
   python test/benchmarks/converterbenchmark.py data/sample.jpg

Benchmark multiple images:

.. code-block:: bash

   for file in data/*.jpg; do
       python test/benchmarks/converterbenchmark.py "$file"
   done

------------------------------

.. _usage-documentation-converter:

Usage Documentation
-------------------

.. _basic-usage-converter:

Basic Usage
~~~~~~~~~~~

The Converter Benchmark requires a single image file as input:

.. code-block:: bash

   python test/benchmarks/converterbenchmark.py <image_file>

The benchmark will:

1. Convert the image to PPM format using libvips
2. Extract image dimensions and metadata
3. Tile the image into a pyramidal structure
4. Launch a PyZUI window (800x600)
5. Perform cold cache zoom test (100 frames)
6. Perform warm cache zoom test (100 frames)
7. Display comprehensive performance metrics

Supported Formats
~~~~~~~~~~~~~~~~~

The converter supports all formats supported by libvips, including:

- JPEG (.jpg, .jpeg)
- PNG (.png)
- TIFF (.tif, .tiff)
- GIF (.gif)
- BMP (.bmp)
- WebP (.webp)
- And many more

For a complete list, see https://www.libvips.org/API/current/file-format.html

.. _output-interpretation-converter:

Output Interpretation
~~~~~~~~~~~~~~~~~~~~~

The benchmark produces output in multiple stages:

**1. Conversion Phase**

.. code-block:: text

   Benchmarking sample.jpg ...
   Converting to PPM...
   Done: took 2.45s

**2. Metadata Extraction**

.. code-block:: text

   Dimensions: 4096x3072, 12.58 megapixels

**3. Tiling Phase**

.. code-block:: text

   Tiling...
   Done: took 8.23s consuming 145.32MB RAM

**4. Zoom Testing**

.. code-block:: text

   Viewport: 800x600
   Zoom amount: 5.0
   Zooming (cold)...
   Done: 100 frames took 3.42s, mean framerate 29.24 FPS
   Zooming (warm)...
   Done: 100 frames took 2.15s, mean framerate 46.51 FPS

Metric Explanations
~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 50 25

   * - Metric
     - Description
     - Interpretation
   * - Conversion time
     - Time to convert image to PPM
     - Depends on format/size
   * - Tiling time
     - Time to create tile pyramid
     - Depends on megapixels
   * - Memory consumption
     - Peak RAM during tiling
     - Should scale with image size
   * - Cold cache FPS
     - Initial zoom framerate
     - Lower due to tile loading
   * - Warm cache FPS
     - Repeat zoom framerate
     - Higher due to caching

------------------------------

.. _technical-documentation-converter:

Technical Documentation
-----------------------

.. _benchmark-phases-converter:

Benchmark Phases
~~~~~~~~~~~~~~~~

**Phase 1: Initialization**

::

   1. Initialize TileManager
   2. Create temporary tile storage directory
   3. Create Qt application instance
   4. Parse command-line arguments
   5. Validate input file exists

**Phase 2: Conversion**

::

   1. Create VipsConverter instance
   2. Load image with libvips
   3. Convert to 8-bit RGB/grayscale
   4. Write to temporary PPM file
   5. Measure conversion time

**Phase 3: Metadata Extraction**

::

   1. Open PPM file in binary mode
   2. Read PPM header (P6 format)
   3. Extract width and height
   4. Calculate megapixels
   5. Close file

**Phase 4: Tiling**

::

   1. Record baseline memory usage
   2. Create PPMTiler instance
   3. Execute tiling operation
   4. Generate pyramidal tile structure
   5. Record peak memory usage
   6. Measure tiling time

**Phase 5: Zoom Performance - Cold Cache**

::

   1. Create QZUI widget (800x600)
   2. Create new Scene
   3. Add TiledMediaObject
   4. Fit object to viewport
   5. Execute 100 zoom frames
   6. Record time and calculate FPS

**Phase 6: Zoom Performance - Warm Cache**

::

   1. Zoom back to original position
   2. Execute same 100 zoom frames
   3. Record time and calculate FPS
   4. Tiles now cached in memory

**Phase 7: Cleanup**

::

   1. Remove temporary tile directory
   2. Remove temporary PPM file
   3. Clean up Qt resources

.. _functions-converter:

Functions
~~~~~~~~~

mem(size: str = 'rss') -> int
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get the current process memory usage in kilobytes.

**Parameters:**

- ``size``: Memory type to measure

  - ``'rss'``: Resident Set Size (default)
  - ``'rsz'``: Resident + text memory
  - ``'vsz'``: Virtual memory size

**Returns:** Memory usage in KB

**Implementation:** Uses ``ps`` command via ``os.popen``

benchmark(filename: str, ppmfile: str) -> None
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Execute the complete benchmark pipeline.

**Parameters:**

- ``filename``: Absolute path to source image
- ``ppmfile``: Path to temporary PPM file

**Process:**

1. Measures baseline memory
2. Converts image to PPM
3. Extracts metadata
4. Tiles the image
5. Performs zoom tests
6. Reports all metrics

main() -> None
^^^^^^^^^^^^^^

Entry point for the benchmark utility.

**Responsibilities:**

- Initialize PyZUI systems
- Parse command-line arguments
- Validate input file
- Create temporary files
- Execute benchmark
- Ensure cleanup on exit

**Exit codes:**

- ``0``: Success
- ``1``: Error (missing file, invalid arguments)

Benchmark Constants
~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Constant
     - Value
     - Purpose
   * - Viewport width
     - 800
     - Display window width
   * - Viewport height
     - 600
     - Display window height
   * - Zoom amount
     - 5.0
     - Total zoom level change
   * - Frame count
     - 100
     - Frames per zoom test
   * - Tile size
     - 256
     - Default tile dimensions (via PPMTiler)
   * - PPM format
     - P6
     - Binary PPM with maxval=255

------------------------------

.. _troubleshooting-converter:

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**"Error: No image file specified"**

Provide image path:

.. code-block:: bash

   python test/benchmarks/converterbenchmark.py path/to/image.jpg

**"Error: File not found"**

Check file path is correct and accessible.

**Conversion fails**

- Verify libvips is installed: ``conda install -c conda-forge libvips``
- Check image format is supported by libvips
- Ensure image file is not corrupted

**Low framerate during zoom**

Normal for:

- Very large images (>50 megapixels)
- First run (cold cache)
- Systems with limited RAM

**Memory consumption too high**

Expected behavior:

- Memory scales with image size
- PPM format is uncompressed
- Tiling requires temporary storage

Performance Tips
~~~~~~~~~~~~~~~~

1. Use smaller images for quick tests
2. Warm cache performance represents typical usage
3. Compare different image formats
4. Monitor memory for memory leak detection

Interpreting Results
~~~~~~~~~~~~~~~~~~~~

**Good performance indicators:**

- Conversion time < 1s per megapixel
- Tiling time < 3s per megapixel
- Cold cache FPS > 20
- Warm cache FPS > 30
- Memory usage < 200MB for typical images

**Performance bottlenecks:**

- Slow conversion: I/O or libvips issue
- Slow tiling: CPU or I/O bound
- Low cold FPS: Tile loading overhead
- Low warm FPS: Rendering/GPU issue
- High memory: Image size or leak

Batch Testing
~~~~~~~~~~~~~

Test multiple images:

.. code-block:: bash

   #!/bin/bash
   for img in data/*.jpg; do
       echo "===== Testing $img ====="
       python test/benchmarks/converterbenchmark.py "$img"
       echo ""
   done > benchmark_results.txt

Analyze results:

.. code-block:: bash

   grep "megapixels" benchmark_results.txt
   grep "FPS" benchmark_results.txt
   grep "consuming" benchmark_results.txt

------------------------------

Implementation Details
----------------------

Memory Tracking
~~~~~~~~~~~~~~~

Memory is measured at two points:

1. **Baseline**: Before tiling starts
2. **Peak**: After tiling completes

The difference approximates peak tiling memory consumption.

**Note:** Python doesn't always return memory to the OS immediately,
so the peak measurement represents approximate maximum usage during
the tiling phase.

Zoom Test Methodology
~~~~~~~~~~~~~~~~~~~~~

**Cold cache test:**

- First zoom operation after tiling
- Tiles loaded from disk on demand
- Measures I/O and rendering performance

**Warm cache test:**

- Zoom after returning to original position
- Tiles already in memory (TileCache)
- Measures pure rendering performance

The performance difference between cold and warm cache tests indicates
the effectiveness of the tile caching system.

PPM Format
~~~~~~~~~~

The benchmark uses PPM (Portable Pixmap) as an intermediate format:

**Advantages:**

- Simple uncompressed format
- Fast to read during tiling
- No codec overhead
- Consistent format across tests

**Disadvantages:**

- Large file size
- Temporary storage required
- Extra conversion step

Alternative formats may be added in future versions.

------------------------------

Related Documentation
---------------------

- :doc:`QZUI Benchmark <qzuibenchmark>` - Stress testing and performance
- :doc:`Tiling System <../technicaldocumentation/tilingsystem>` - Tile generation details
- :doc:`Converter System <../technicaldocumentation/convertersystem>` - Image conversion pipeline

------------------------------

License
-------

This benchmark is part of PyZUI and licensed under GNU GPLv2.

Copyright (C) 2009
David Roberts <d@vidr.cc>
