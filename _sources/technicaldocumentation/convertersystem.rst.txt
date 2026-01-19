.. Converter System Documentation

Converter System
================

This document provides a comprehensive overview of the converter system architecture in PyZUI,
explaining how various media formats (PDF, images) are converted to PPM format for tiling and
display in the Zooming User Interface. The converter system is a crucial preprocessing step
that normalizes different input formats into a common format suitable for tile generation.

Overview
--------

The converter system is responsible for:

1. Converting various media formats to PPM (Portable Pixmap) format
2. Running conversions in background processes to avoid blocking the UI
3. Tracking conversion progress for user feedback
4. Handling errors gracefully during conversion
5. Managing temporary files and enabling true parallel conversion

The system uses a **process-based architecture** where each conversion runs in a separate
process via ``ProcessPoolExecutor``. This design was chosen to avoid threading conflicts
between pyvips (which has its own internal thread pool) and TileManager's background threads.
All converters output to PPM format, which is then processed by the tiling system.

**Why Process-Based?**

The original thread-based design encountered issues when multiple ``VipsConverter``
instances ran concurrently alongside TileManager threads:

- pyvips uses its own internal threading for image operations
- TileManager starts TileProvider threads for loading tiles
- When these run together in the same process, threading conflicts can occur
- The conflicts manifest as hangs or deadlocks during concurrent conversions

By running conversions in separate processes (using Python's ``multiprocessing`` with
the 'spawn' start method), each converter gets its own isolated memory space and pyvips
instance, eliminating these conflicts while enabling true parallel conversion.

Architecture
------------

The converter system consists of the following components:

.. code-block:: text

    converterrunner (Process Pool Manager)
    │   • ProcessPoolExecutor with 'spawn' context
    │   • submit_vips_conversion() - submit image conversion job
    │   • submit_pdf_conversion() - submit PDF conversion job
    │   • ConversionHandle - tracks running/completed conversions
    │   • init() / shutdown() - pool lifecycle management
    │
    Converter (Abstract Base, extends Thread)
    │   • Can still run as thread for direct use
    │   • Progress tracking (0.0 to 1.0)
    │   • Error handling
    │   • Logger integration
    │   • Abstract run() method
    │
    ├── PDFConverter
    │       • PDF to PPM conversion
    │       • Uses pdftoppm (Poppler/Xpdf)
    │       • Multi-page support
    │       • Configurable resolution (default: 300 DPI)
    │       • Page merging into single PPM
    │
    └── VipsConverter
            • Multi-format image conversion
            • Uses libvips (via pyvips)
            • Supports: JPG, PNG, GIF, TIFF, WebP, etc.
            • Automatic format detection
            • Bit-depth conversion (8-bit)
            • RGBA to RGB flattening
            • Image transformations (rotation, invert, B&W)

**Conversion Pipeline:**

.. code-block:: text

    ┌─────────────────────────────────────────────────────────────┐
    │                    TiledMediaObject                         │
    │              (Detects format, submits to converterrunner)  │
    └──────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                    converterrunner                         │
    │              (ProcessPoolExecutor with 'spawn')             │
    └──────────────────────┬──────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┬──────────┐
           │               │               │          │
           ▼               ▼               ▼          ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
    │   .pdf   │   │   .jpg   │   │   .png   │   │   .ppm   │
    │          │   │   .tiff  │   │   .gif   │   │ (direct) │
    └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘
         │              │              │              │
         ▼              ▼              │              │
    ┌──────────┐   ┌──────────┐        │              │
    │   PDF    │   │  Vips    │        │              │
    │Converter │   │Converter │◀───────┘              │
    │(process) │   │(process) │                       │
    └────┬─────┘   └────┬─────┘                       │
         │              │                             │
         │     Creates  │                             │
         │   temp file  │                             │
         ▼              ▼                             ▼
    ┌──────────────────────────────────────────────────────────┐
    │                    PPM File                              │
    │           (Portable Pixmap Format)                       │
    └────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
    ┌──────────────────────────────────────────────────────────┐
    │                    PPMTiler                              │
    │           (Creates tile pyramid)                         │
    └──────────────────────────────────────────────────────────┘

**Process Isolation:**

.. code-block:: text

    ┌─────────────────────────────────────┐    ┌────────────────────┐
    │          Main Process               │    │  Worker Processes  │
    │  ┌───────────────────────────────┐  │    │  ┌──────────────┐  │
    │  │ TileManager Threads           │  │    │  │VipsConverter │  │
    │  │  - StaticTileProvider         │  │    │  │  (isolated)  │  │
    │  │  - DynamicTileProvider        │  │    │  └──────────────┘  │
    │  └───────────────────────────────┘  │    │  ┌──────────────┐  │
    │  ┌───────────────────────────────┐  │    │  │PDFConverter  │  │
    │  │ ProcessPoolExecutor           │  │◄──►│  │  (isolated)  │  │
    │  │  - submits conversion jobs    │  │    │  └──────────────┘  │
    │  │  - tracks via Future          │  │    │                    │
    │  └───────────────────────────────┘  │    │  Each process has  │
    │  ┌───────────────────────────────┐  │    │  own pyvips, own   │
    │  │ ConversionHandle              │  │    │  memory space      │
    │  │  - wraps Future               │  │    │                    │
    │  │  - provides progress/error    │  │    └────────────────────┘
    │  └───────────────────────────────┘  │
    └─────────────────────────────────────┘

Why PPM Format?
~~~~~~~~~~~~~~~

PPM (Portable Pixmap) is chosen as the intermediate format because:

1. **Simplicity**: Extremely simple format - just header + raw pixel data
2. **Uncompressed**: No decompression overhead during tiling
3. **Sequential Access**: Can be read and processed line-by-line
4. **No Dependencies**: Can be parsed without external libraries
5. **Lossless**: No quality degradation from conversion
6. **Universal Support**: All image libraries support PPM output

Core Components
---------------

Converter (Abstract Base Class)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :class:`Converter` class provides the foundation for all converters, implementing
the threading mechanism and progress tracking.

**Class Definition:**

.. code-block:: python

    class Converter(Thread):
        def __init__(self, infile: str, outfile: str) -> None:
            Thread.__init__(self)
            self._infile = infile
            self._outfile = outfile
            self._progress = 0.0
            self._logger = get_logger(f'Converter.{infile}')
            self.error = None

**Key Attributes:**

- ``_infile``: Path to input file to be converted
- ``_outfile``: Path to output file (PPM format)
- ``_progress``: Conversion progress (0.0 to 1.0)
- ``_logger``: Logger instance for debugging and error reporting
- ``error``: Error message string if conversion fails (None on success)

**Key Methods:**

- ``run()``: Abstract method implemented by subclasses to perform conversion
- ``progress``: Property returning current conversion progress (0.0 to 1.0)
- ``start()``: Inherited from Thread - starts conversion in background

**Threading Model:**

Converters inherit from :class:`threading.Thread`, which means:

1. Conversion happens in a separate thread
2. Main thread continues executing (non-blocking)
3. Progress can be monitored via the ``progress`` property
4. Errors are stored in the ``error`` attribute

**Usage Pattern:**

.. code-block:: python

    # Create converter
    converter = SomeConverter('input.pdf', 'output.ppm')

    # Start conversion in background thread
    converter.start()

    # Check progress (in main thread or render loop)
    while converter.progress < 1.0:
        print(f"Progress: {converter.progress * 100:.1f}%")
        time.sleep(0.1)

    # Check for errors
    if converter.error:
        print(f"Conversion failed: {converter.error}")

PDFConverter
~~~~~~~~~~~~

The :class:`PDFConverter` class converts PDF documents to PPM format using the
``pdftoppm`` command-line tool from Poppler or Xpdf.

**Class Definition:**

.. code-block:: python

    class PDFConverter(Converter):
        def __init__(self, infile: str, outfile: str) -> None:
            Converter.__init__(self, infile, outfile)
            self.resolution = 300

**Key Attributes:**

- ``resolution``: DPI resolution for rasterization (default: 300)

**Conversion Process:**

The PDF conversion follows these steps:

.. code-block:: text

    1. Create temporary directory
       ├─ Used to store individual page PPM files
       └─ Cleaned up after conversion

    2. Call pdftoppm
       ├─ Command: pdftoppm -r <resolution> <infile> <tmpdir>/page
       ├─ Generates: page-0001.ppm, page-0002.ppm, ...
       └─ Each file contains one page of the PDF

    3. Read page headers
       ├─ Parse PPM header from each page file
       ├─ Extract width and height
       └─ Calculate total height (sum of all pages)

    4. Merge pages
       ├─ Create output PPM header (width, total_height)
       ├─ Concatenate pixel data from all pages vertically
       └─ Result: Single PPM with all pages stacked

    5. Clean up
       ├─ Close all file handles
       ├─ Delete temporary directory
       └─ Set progress to 1.0

**Multi-Page Handling:**

PDF documents can have multiple pages. PDFConverter handles this by:

1. Rasterizing each page separately with ``pdftoppm``
2. Determining page order from filenames (e.g., ``page-0001.ppm``)
3. Reading each page's dimensions from PPM headers
4. Creating a single tall PPM by vertically concatenating all pages
5. Preserving page order in the output

**PPM Page Merging Algorithm:**

.. code-block:: python

    # Simplified merge logic
    total_height = sum(page_heights)

    # Write combined header
    output.write(f"P6\n{width} {total_height}\n255\n")

    # Concatenate pixel data
    for page_file in page_files_in_order:
        shutil.copyfileobj(page_file, output)

**Progress Tracking:**

- ``0.0``: Conversion not started
- ``0.5``: ``pdftoppm`` finished, starting page merge
- ``1.0``: Conversion complete

**Error Handling:**

Errors can occur at several stages:

- **pdftoppm failure**: Invalid PDF, missing tool, insufficient memory
- **Page header parsing**: Corrupted PPM output
- **File I/O errors**: Disk full, permission denied

When errors occur:

1. Error message stored in ``self.error``
2. Logged via ``self._logger.error()``
3. Temporary files cleaned up
4. Output file deleted (if partially written)
5. Progress set to 1.0 (indicates completion, check error)

**Dependencies:**

Requires ``pdftoppm`` command-line tool:

- **Linux**: Install ``poppler-utils`` package
- **macOS**: Install via Homebrew: ``brew install poppler``
- **Windows**: Download Poppler for Windows

**Example PDF Conversion:**

.. code-block:: python

    converter = PDFConverter('document.pdf', 'output.ppm')
    converter.resolution = 150  # Lower resolution for faster conversion
    converter.start()

    # Wait for completion
    converter.join()

    if converter.error:
        print(f"Conversion failed: {converter.error}")
    else:
        print(f"Converted PDF to PPM: {converter._outfile}")

VipsConverter
~~~~~~~~~~~~~

The :class:`VipsConverter` class converts various image formats to PPM using
libvips, a fast image processing library.

**Class Definition:**

.. code-block:: python

    class VipsConverter(Converter):
        def __init__(self, infile: str, outfile: str) -> None:
            Converter.__init__(self, infile, outfile)
            self.bitdepth = 8

**Key Attributes:**

- ``bitdepth``: Output bit depth (default: 8-bit, required for PPMTiler)

**Supported Formats:**

VipsConverter supports a wide range of image formats:

- **Common**: JPEG, PNG, GIF, BMP, TIFF
- **Advanced**: WebP, HEIF/HEIC, FITS, OpenEXR
- **Scientific**: Analyze, NIfTI, DICOM (with plugins)
- **Raw**: Various camera RAW formats

For a complete list, see: https://www.libvips.org/API/current/file-format.html

**Conversion Process:**

.. code-block:: text

    1. Load image
       ├─ Use pyvips.Image.new_from_file()
       ├─ Automatic format detection
       └─ Sequential access for memory efficiency

    2. Bit-depth conversion (if needed)
       ├─ Check current format
       ├─ If not 8-bit unsigned char (uchar)
       └─ Cast to 8-bit: image.cast('uchar')

    3. Color space handling
       ├─ RGBA (4 bands) → RGB via flatten()
       │   └─ Composites alpha channel with white background
       ├─ Multi-band (>3 bands, not grayscale) → RGB
       │   └─ Extract first 3 bands
       └─ RGB and grayscale → pass through unchanged

    4. Write to PPM
       ├─ Use image.write_to_file()
       ├─ Format automatically determined from extension
       └─ libvips handles PPM format generation

    5. Error handling
       ├─ Catch exceptions
       ├─ Store error message
       ├─ Clean up partial output
       └─ Set progress to 1.0

**Why libvips?**

libvips offers several advantages:

1. **Performance**: Much faster than PIL/Pillow for large images
2. **Memory Efficiency**: Processes images in chunks (streaming)
3. **Format Support**: Extensive format support via plugins
4. **Large Images**: Can handle images larger than RAM
5. **Quality**: High-quality image processing algorithms

**Format-Specific Handling:**

**RGBA Images:**

.. code-block:: python

    # RGBA has 4 bands (Red, Green, Blue, Alpha)
    if image.bands == 4:
        # Flatten alpha channel (composite over white background)
        image = image.flatten()
        # Result: 3-band RGB image

**Multi-band Images:**

.. code-block:: python

    # Some formats (e.g., satellite imagery) have >3 bands
    if image.bands > 3 and image.bands != 1:
        # Extract first 3 bands as RGB
        image = image.extract_band(0, n=3)

**16-bit Images:**

.. code-block:: python

    # Check bit depth
    if self.bitdepth == 8 and image.format != 'uchar':
        # Scale from 16-bit to 8-bit range
        image = image.cast('uchar')

**Progress Tracking:**

Unlike PDFConverter, VipsConverter doesn't track intermediate progress:

- ``0.0``: Conversion not started
- ``1.0``: Conversion complete (success or failure)

This is because libvips processing is typically fast and difficult to
monitor incrementally.

**Error Handling:**

Common errors include:

- **Unsupported format**: File format not supported by libvips
- **Corrupted file**: Invalid or corrupted image data
- **Memory errors**: Insufficient memory for very large images
- **Dependency errors**: Missing libvips plugins for specific formats

**Dependencies:**

Requires both:

1. **libvips**: C library (system package)

   - **Linux**: ``apt install libvips-dev`` or ``yum install vips-devel``
   - **macOS**: ``brew install vips``
   - **Windows**: Download from libvips website

2. **pyvips**: Python bindings

   - ``pip install pyvips``

**Example Image Conversion:**

.. code-block:: python

    converter = VipsConverter('photo.jpg', 'output.ppm')
    converter.bitdepth = 8  # Ensure 8-bit output
    converter.start()

    # Wait for completion
    converter.join()

    if converter.error:
        print(f"Conversion failed: {converter.error}")
    else:
        print(f"Converted image to PPM: {converter._outfile}")

converterrunner Module
~~~~~~~~~~~~~~~~~~~~~~~

The ``converterrunner`` module provides process-based conversion execution,
enabling parallel conversions without threading conflicts.

**Module Functions:**

.. code-block:: python

    from pyzui.converters import converterrunner

    # Initialize process pool (optional, auto-initialized on first use)
    converterrunner.init(max_workers=4)

    # Submit image conversion
    future = converterrunner.submit_vips_conversion(
        infile='image.jpg',
        outfile='output.ppm',
        rotation=0,           # 0, 90, 180, or 270 degrees
        invert_colors=False,
        black_and_white=False
    )

    # Submit PDF conversion
    future = converterrunner.submit_pdf_conversion(
        infile='document.pdf',
        outfile='output.ppm'
    )

    # Shutdown pool when done
    converterrunner.shutdown()

**ConversionHandle Class:**

The ``ConversionHandle`` wraps a ``Future`` and provides a compatible interface
with the thread-based ``Converter`` class:

.. code-block:: python

    from pyzui.converters.converterrunner import ConversionHandle

    # Create handle from future
    handle = ConversionHandle(future, infile, outfile)

    # Check if still running
    if handle.is_alive():
        print("Still converting...")

    # Get progress (0.0 or 1.0 for process-based)
    print(f"Progress: {handle.progress * 100}%")

    # Wait for completion
    handle.join(timeout=30)

    # Check for errors
    if handle.error:
        print(f"Failed: {handle.error}")

Integration with TiledMediaObject
----------------------------------

The converter system is tightly integrated with :class:`TiledMediaObject`,
which automatically selects and uses the appropriate converter via ``converterrunner``.

Format Detection and Converter Selection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`TiledMediaObject` submits conversions to the process pool based on file extension:

.. code-block:: python

    # In TiledMediaObject.__init__()
    from pyzui.converters import converterrunner

    if self._media_id.lower().endswith('.pdf'):
        # Use process-based PDF conversion
        future = converterrunner.submit_pdf_conversion(
            self._media_id, self.__tmpfile)
        self.__converter = converterrunner.ConversionHandle(
            future, self._media_id, self.__tmpfile)
        self.__ppmfile = self.__tmpfile

    elif self._media_id.lower().endswith('.ppm'):
        # PPM files need no conversion
        self.__logger.info("assuming media is a local PPM file")
        self.__ppmfile = self._media_id

    else:
        # Use process-based Vips conversion
        future = converterrunner.submit_vips_conversion(
            self._media_id, self.__tmpfile)
        self.__converter = converterrunner.ConversionHandle(
            future, self._media_id, self.__tmpfile)
        self.__ppmfile = self.__tmpfile

Conversion Workflow
~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    TiledMediaObject Creation        |     │              │
            │                        |     │              ▼
            ▼                        |     │     ┌────────────────┐
    ┌─────────────────┐              |     │     │ Show loading   │
    │  Check if       │              |     │     │ placeholder    │
    │  already tiled  │              |     │     └────────┬───────┘
    └────────┬────────┘              |     │              │
             │                       |     │              ▼
        ┌────┴────┐                  |     │     ┌────────────────┐
        │         │                  |     │     │ Converter      │
      YES        NO                  |     │     │ completes      │
        │         │                  |     │     └────────┬───────┘
        │         ▼                  |     │              │
        │  ┌────────────────┐        |     │              ▼
        │  │ Create temp    │        |     │     ┌────────────────┐
        │  │ file for PPM   │        |     │     │ Start PPMTiler │
        │  └────────┬───────┘        |     │     └────────┬───────┘
        │           │                |     │              │
        │           ▼                |     └──────────────│  
        │  ┌────────────────┐        |                    │
        │  │ Select and     │        |                    ▼
        │  │ start converter│        |      ┌─────────────────────┐
        │  └────────┬───────┘        |      │ Load and display    │
        │           │                |      │ tiles               │
        │           ▼                |      └─────────────────────┘
        │  ┌────────────────┐        |
        │  │ Converter runs │        |
        │  │ in background  │        |
        │  └────────────────┘        |

Progress Reporting
~~~~~~~~~~~~~~~~~~

TiledMediaObject combines converter and tiler progress for user feedback:

.. code-block:: python

    @property
    def __progress(self) -> float:
        if self.__converter is None and self.__tiler is None:
            return 0.0
        elif self.__converter is None:
            # Only tiling remaining
            return self.__tiler.progress
        elif self.__tiler is None:
            # Only conversion (weighted as 50% of total)
            return 0.5 * self.__converter.progress
        else:
            # Both conversion and tiling active
            return 0.5 * (self.__converter.progress + self.__tiler.progress)

This creates smooth progress indication:

- ``0.0 - 0.5``: Conversion phase
- ``0.5 - 1.0``: Tiling phase

Temporary File Management
~~~~~~~~~~~~~~~~~~~~~~~~~~

Converters create temporary PPM files that are cleaned up after tiling:

.. code-block:: python

    # Create temporary file
    fd, self.__tmpfile = tempfile.mkstemp('.ppm')
    os.close(fd)

    # Use as converter output
    converter = PDFConverter(media_id, self.__tmpfile)
    converter.start()

    # After tiling completes, clean up
    if self.__tmpfile:
        try:
            os.unlink(self.__tmpfile)
        except:
            self._logger.exception(
                f"unable to unlink temporary file '{self.__tmpfile}'")

Thread Safety and Process Isolation
------------------------------------

Process-Based Isolation
~~~~~~~~~~~~~~~~~~~~~~~

Converters run in separate processes via ``ProcessPoolExecutor``, providing complete isolation:

.. code-block:: python

    from pyzui.converters import converterrunner

    # Submit conversion to process pool
    future = converterrunner.submit_vips_conversion(infile, outfile)

    # Track via ConversionHandle
    handle = converterrunner.ConversionHandle(future, infile, outfile)

    # Check progress/completion
    if handle.progress == 1.0:
        if handle.error:
            print(f"Failed: {handle.error}")

This ensures:

1. No threading conflicts with TileManager threads
2. Each pyvips instance runs in its own memory space
3. True parallel conversion (multiple conversions run simultaneously)
4. No deadlocks from pyvips internal threading

**Why Process-Based?**

The process-based approach was adopted because:

- pyvips uses its own internal thread pool for image operations
- TileManager starts TileProvider threads for tile loading
- When these run in the same process, threading conflicts can occur
- Process isolation eliminates these conflicts completely

**Spawn Context:**

The ``converterrunner`` uses Python's 'spawn' multiprocessing context:

.. code-block:: python

    import multiprocessing
    _mp_context = multiprocessing.get_context('spawn')
    _executor = ProcessPoolExecutor(max_workers=4, mp_context=_mp_context)

The 'spawn' method creates a fresh Python interpreter for each subprocess,
avoiding issues that occur when forking a process that already has pyvips initialized.

TileManager Pause/Resume (Optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TileManager includes pause/resume functionality that can be used if needed:

.. code-block:: python

    from pyzui.tilesystem import tilemanager

    # Pause all tile provider threads
    tilemanager.pause()

    # Perform operations...

    # Resume tile provider threads
    tilemanager.resume()

This mechanism pauses the ``StaticTileProvider`` and ``DynamicTileProvider`` threads,
which may be useful in certain scenarios. However, with process-based conversion,
this is typically not needed since converters run in separate processes.

Logging and Debugging
---------------------

All converters integrate with PyZUI's logging system:

.. code-block:: python

    # Logger is created per-converter with unique name
    self._logger = get_logger(f'Converter.{infile}')

    # Usage throughout conversion
    self._logger.debug("loading image with libvips")
    self._logger.info("calling pdftoppm")
    self._logger.error(self.error)

**Log Levels:**

- **DEBUG**: Detailed conversion steps, dimensions, format info
- **INFO**: Major milestones (starting conversion, merging pages)
- **ERROR**: Conversion failures, with full error details

**Example Log Output:**

.. code-block:: text

    INFO: Converter.image.jpg - loading image with libvips
    DEBUG: Converter.image.jpg - loaded 4096x3072 image with 3 bands
    DEBUG: Converter.image.jpg - writing to /tmp/tmp1234.ppm
    INFO: Converter.document.pdf - calling pdftoppm
    INFO: Converter.document.pdf - merging pages

Error Handling Best Practices
------------------------------

Checking for Errors
~~~~~~~~~~~~~~~~~~~

Always check the ``error`` attribute after conversion:

.. code-block:: python

    converter.start()
    converter.join()  # Wait for completion

    if converter.error:
        # Handle error
        print(f"Conversion failed: {converter.error}")
        # Don't proceed to tiling
    else:
        # Success - proceed to tiling
        run_tiler(converter._outfile)

Error Recovery
~~~~~~~~~~~~~~

When converters fail, they:

1. Set ``self.error`` to a descriptive message
2. Log the error for debugging
3. Clean up partial output files
4. Set progress to 1.0 (indicates completion)

**TiledMediaObject Error Handling:**

.. code-block:: python

    if self.__converter and self.__converter.error:
        raise LoadError(self.__converter.error)

This propagates errors up to the Scene, which removes problematic objects.

Common Error Scenarios
~~~~~~~~~~~~~~~~~~~~~~

**Missing Dependencies:**

.. code-block:: python

    # PDFConverter
    "conversion failed with return code 127"
    # Solution: Install poppler-utils

    # VipsConverter
    "conversion failed: libvips library not found"
    # Solution: Install libvips and pyvips

**Unsupported Format:**

.. code-block:: python

    "unable to parse SVG file"
    # Wrong converter selected - use SVGMediaObject instead

**Corrupted Input:**

.. code-block:: python

    "conversion failed: VipsJpeg: Corrupt JPEG data"
    # Input file is corrupted or incomplete

**Insufficient Memory:**

.. code-block:: python

    "unable to allocate memory"
    # Image too large for available RAM
    # Solution: Use libvips (VipsConverter) which streams

Performance Considerations
--------------------------

Conversion Speed
~~~~~~~~~~~~~~~~

Typical conversion times vary by format and file size:

**PDFConverter:**

- **Factor**: Pages, resolution, complexity
- **Speed**: ~1-5 seconds per page at 300 DPI
- **Bottleneck**: CPU (rasterization)

**VipsConverter:**

- **Factor**: Format, size, compression
- **Speed**: 0.1-2 seconds for most images
- **Bottleneck**: Disk I/O (reading/writing)

Memory Usage
~~~~~~~~~~~~

**PDFConverter:**

- Memory usage scales with resolution and page dimensions
- Each page loaded entirely into memory
- Peak usage during page merging

**VipsConverter:**

- Memory usage relatively constant (streaming)
- Can process images larger than RAM
- Minimal peak memory usage

Optimization Strategies
~~~~~~~~~~~~~~~~~~~~~~~

**For PDFs:**

.. code-block:: python

    # Lower resolution for faster conversion (if acceptable)
    converter = PDFConverter('large.pdf', 'output.ppm')
    converter.resolution = 150  # Instead of default 300

**For Images:**

.. code-block:: python

    # VipsConverter is already optimized
    # Ensure libvips is installed (faster than PIL/Pillow)
    converter = VipsConverter('huge.tiff', 'output.ppm')

**Concurrent Conversions:**

Since converters are threaded, multiple can run simultaneously:

.. code-block:: python

    # Start multiple conversions
    conv1 = PDFConverter('doc1.pdf', 'out1.ppm')
    conv2 = VipsConverter('img1.jpg', 'out2.ppm')
    conv3 = VipsConverter('img2.png', 'out3.ppm')

    conv1.start()
    conv2.start()
    conv3.start()

    # All run concurrently

However, disk lock serializes disk access, so actual speedup depends on
CPU vs I/O balance.

Usage Examples
--------------

Basic Conversion
~~~~~~~~~~~~~~~~

.. code-block:: python

    from pyzui.converters import PDFConverter, VipsConverter

    # Convert PDF
    pdf_conv = PDFConverter('document.pdf', 'output_pdf.ppm')
    pdf_conv.start()
    pdf_conv.join()

    if not pdf_conv.error:
        print("PDF converted successfully!")

    # Convert image
    img_conv = VipsConverter('photo.jpg', 'output_img.ppm')
    img_conv.start()
    img_conv.join()

    if not img_conv.error:
        print("Image converted successfully!")

Progress Monitoring
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import time

    converter = PDFConverter('large_document.pdf', 'output.ppm')
    converter.start()

    # Monitor progress
    while converter.progress < 1.0:
        print(f"\rProgress: {converter.progress * 100:.1f}%", end='')
        time.sleep(0.1)

    print()  # New line

    if converter.error:
        print(f"Error: {converter.error}")
    else:
        print("Conversion complete!")

Custom Resolution PDF Conversion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # High-resolution conversion for printing
    converter = PDFConverter('document.pdf', 'high_res.ppm')
    converter.resolution = 600  # 600 DPI
    converter.start()
    converter.join()

    # Low-resolution conversion for preview
    converter = PDFConverter('document.pdf', 'low_res.ppm')
    converter.resolution = 72  # 72 DPI (screen resolution)
    converter.start()
    converter.join()

Handling Multiple Formats
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import os

    def convert_to_ppm(input_file, output_file):
        """Convert any supported format to PPM."""

        ext = os.path.splitext(input_file)[1].lower()

        if ext == '.pdf':
            converter = PDFConverter(input_file, output_file)
        elif ext == '.ppm':
            # Already PPM, just copy
            import shutil
            shutil.copy(input_file, output_file)
            return True
        else:
            # Try VipsConverter for everything else
            converter = VipsConverter(input_file, output_file)

        converter.start()
        converter.join()

        if converter.error:
            print(f"Conversion failed: {converter.error}")
            return False

        return True

    # Usage
    success = convert_to_ppm('document.pdf', 'output1.ppm')
    success = convert_to_ppm('photo.jpg', 'output2.ppm')
    success = convert_to_ppm('diagram.png', 'output3.ppm')

API Reference
-------------

converterrunner Module
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Module functions
    def init(max_workers: int = 4) -> None
    def shutdown() -> None
    def submit_vips_conversion(infile, outfile, rotation=0,
                               invert_colors=False, black_and_white=False) -> Future
    def submit_pdf_conversion(infile, outfile) -> Future

    # ConversionHandle class
    class ConversionHandle:
        def __init__(self, future: Future, infile: str, outfile: str) -> None

        @property
        def progress(self) -> float  # 0.0 or 1.0
        @property
        def error(self) -> Optional[str]

        def is_alive(self) -> bool
        def join(self, timeout: Optional[float] = None) -> None

Converter (Abstract Base)
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    class Converter(Thread):
        def __init__(self, infile: str, outfile: str) -> None
        def run(self) -> None  # Abstract

        @property
        def progress(self) -> float  # 0.0 to 1.0

        # Attributes
        self._infile: str
        self._outfile: str
        self._progress: float
        self._logger: Logger
        self.error: Optional[str]

PDFConverter
~~~~~~~~~~~~

.. code-block:: python

    class PDFConverter(Converter):
        def __init__(self, infile: str, outfile: str) -> None

        # Attributes
        self.resolution: int  # DPI (default: 300)

VipsConverter
~~~~~~~~~~~~~

.. code-block:: python

    class VipsConverter(Converter):
        def __init__(self, infile: str, outfile: str,
                     rotation: Literal[0, 90, 180, 270] = 0,
                     invert_colors: bool = False,
                     black_and_white: bool = False) -> None

        # Attributes
        self.bitdepth: int  # Bit depth (default: 8)
        self.rotation: int  # Rotation angle
        self.invert_colors: bool  # Color inversion flag
        self.black_and_white: bool  # Grayscale conversion flag

Key Classes
~~~~~~~~~~~

- :class:`pyzui.converters.converterrunner` - Process-based conversion execution
- :class:`pyzui.converters.converter.Converter` - Abstract base class
- :class:`pyzui.converters.pdfconverter.PDFConverter` - PDF converter
- :class:`pyzui.converters.vipsconverter.VipsConverter` - Image converter

See Also
--------

- :doc:`tilingsystem` - Tile generation from PPM files
- :doc:`tiledmediaobject` - Integration with TiledMediaObject
- :doc:`objectsystem` - Overall object system architecture
- :doc:`projectstructure` - Project organization
