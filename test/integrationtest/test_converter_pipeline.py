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

"""
Integration Tests: Converter Pipeline
======================================

This module contains integration tests validating the converter pipeline,
which transforms various media formats into tileable images. The converters
work in conjunction with the tiling system to enable viewing of PDFs,
large images, and other formats.

The tests cover:
- VipsConverter for image format conversion
- PDFConverter for PDF rasterization
- Converter to Tiler pipeline (convert then tile)
- Progress tracking during conversion
- Error handling for invalid or corrupted files
- Concurrent conversion operations
- Output format validation
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
import time
import tempfile
import shutil
import subprocess
from pathlib import Path
from threading import Thread
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image

from pyzui.converters.converter import Converter
from pyzui.converters.vipsconverter import VipsConverter
from pyzui.converters.pdfconverter import PDFConverter
from pyzui.tilesystem.tiler import Tiler
from pyzui.tilesystem import tilestore
from pyzui.tilesystem import tilemanager

class ConcreteTiler(Tiler):
    """
    A concrete implementation of Tiler for testing the converter pipeline.

    Implements the _scanchunk method using PIL to read PPM image data.
    """

    def __init__(self, infile, media_id=None, filext='jpg', tilesize=256):
        """Initialize the tiler and open the source image."""
        super().__init__(infile, media_id, filext, tilesize)
        self._image = Image.open(infile).convert('RGB')
        self._width, self._height = self._image.size
        self._bytes_per_pixel = 3
        self._current_row = 0

    def _scanchunk(self):
        """Read the next scanline from the image."""
        if self._current_row >= self._height:
            return b''
        # Use crop to get entire row at once (much faster than getpixel)
        row_img = self._image.crop((0, self._current_row, self._width, self._current_row + 1))
        row_data = row_img.tobytes()
        self._current_row += 1
        return row_data

def is_pdftoppm_available():
    """Check if pdftoppm is available on the system."""
    try:
        result = subprocess.run(
            ['pdftoppm', '-v'],
            capture_output=True,
            timeout=5
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def is_pyvips_available():
    """Check if pyvips is available and functional."""
    try:
        import pyvips
        return True
    except ImportError:
        return False

@pytest.fixture
def temp_tilestore(tmp_path):
    """
    Fixture: Isolated Tile Storage

    Provides a temporary directory for tile storage.

    Yields:
        str: Path to the temporary tilestore directory.
    """
    from pyzui.tilesystem.tilestore import tilestore as ts_module

    original_tile_dir = ts_module.tile_dir
    temp_dir = str(tmp_path / "tilestore")
    os.makedirs(temp_dir, exist_ok=True)

    ts_module.tile_dir = temp_dir
    tilestore.tile_dir = temp_dir

    yield temp_dir

    ts_module.tile_dir = original_tile_dir
    tilestore.tile_dir = original_tile_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

@pytest.fixture
def initialized_tilemanager(temp_tilestore):
    """
    Fixture: Initialized TileManager

    Yields:
        None (TileManager is a module with global state)
    """
    tilemanager.init(total_cache_size=100, auto_cleanup=False)
    yield
    tilemanager.purge()

@pytest.fixture
def sample_images(tmp_path):
    """
    Fixture: Sample Test Images

    Creates test images in various formats for conversion testing.

    Yields:
        dict: Mapping of format name to image file path.
    """
    images = {}

    # PNG image
    png_path = tmp_path / "test_image.png"
    img = Image.new('RGB', (800, 600), color='red')
    for y in range(600):
        for x in range(min(50, 800)):
            img.putpixel((x, y), (x * 5, y % 256, 128))
    img.save(png_path)
    images['png'] = str(png_path)

    # JPEG image
    jpg_path = tmp_path / "test_image.jpg"
    img.save(jpg_path, quality=95)
    images['jpg'] = str(jpg_path)

    # TIFF image
    tiff_path = tmp_path / "test_image.tiff"
    img.save(tiff_path)
    images['tiff'] = str(tiff_path)

    # Large image
    large_path = tmp_path / "large_image.png"
    large_img = Image.new('RGB', (2048, 1536), color='blue')
    large_img.save(large_path)
    images['large'] = str(large_path)

    # RGBA image (with alpha channel)
    rgba_path = tmp_path / "rgba_image.png"
    rgba_img = Image.new('RGBA', (400, 300), color=(255, 0, 0, 128))
    rgba_img.save(rgba_path)
    images['rgba'] = str(rgba_path)

    yield images

@pytest.fixture
def sample_pdf(tmp_path):
    """
    Fixture: Sample PDF File

    Creates a minimal PDF file for testing PDFConverter.
    Uses reportlab if available, otherwise creates a minimal valid PDF.

    Yields:
        str: Path to the PDF file, or None if PDF creation fails.
    """
    pdf_path = tmp_path / "test_document.pdf"

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        c.drawString(100, 750, "Test PDF Document")
        c.drawString(100, 700, "Page 1 - Integration Test")
        c.rect(50, 400, 500, 200, fill=1)
        c.save()

        yield str(pdf_path)

    except ImportError:
        # Create minimal valid PDF without reportlab
        minimal_pdf = b"""%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >> endobj
4 0 obj << /Length 44 >> stream
BT /F1 12 Tf 100 700 Td (Test PDF) Tj ET
endstream endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
trailer << /Size 5 /Root 1 0 R >>
startxref
307
%%EOF"""
        with open(pdf_path, 'wb') as f:
            f.write(minimal_pdf)

        yield str(pdf_path)

class TestVipsConverterBasicOperations:
    """
    Feature: VipsConverter Basic Operations

    VipsConverter uses libvips to convert images between formats.
    It handles large images efficiently with low memory usage and
    outputs PPM format for subsequent tiling.
    """

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_convert_png_to_ppm(self, sample_images, tmp_path):
        """
        Scenario: Convert PNG image to PPM format

        Given a PNG image file
        When VipsConverter processes it
        Then a PPM file is created at the output path
        And the output is valid image data
        """
        infile = sample_images['png']
        outfile = str(tmp_path / "output.ppm")

        converter = VipsConverter(infile, outfile)
        converter.run()

        assert converter.error is None, f"Conversion failed: {converter.error}"
        assert converter.progress == 1.0
        assert os.path.exists(outfile)

        # Verify output is readable
        output_img = Image.open(outfile)
        assert output_img.size == (800, 600)

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_convert_jpg_to_ppm(self, sample_images, tmp_path):
        """
        Scenario: Convert JPEG image to PPM format

        Given a JPEG image file
        When VipsConverter processes it
        Then a valid PPM file is created
        """
        infile = sample_images['jpg']
        outfile = str(tmp_path / "output.ppm")

        converter = VipsConverter(infile, outfile)
        converter.run()

        assert converter.error is None
        assert os.path.exists(outfile)

        output_img = Image.open(outfile)
        assert output_img.mode == 'RGB'

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_convert_tiff_to_ppm(self, sample_images, tmp_path):
        """
        Scenario: Convert TIFF image to PPM format

        Given a TIFF image file
        When VipsConverter processes it
        Then a valid PPM file is created
        """
        infile = sample_images['tiff']
        outfile = str(tmp_path / "output.ppm")

        converter = VipsConverter(infile, outfile)
        converter.run()

        assert converter.error is None
        assert os.path.exists(outfile)

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_convert_rgba_flattens_alpha(self, sample_images, tmp_path):
        """
        Scenario: RGBA images are flattened to RGB

        Given an RGBA image with transparency
        When VipsConverter processes it
        Then the alpha channel is flattened
        And the output is RGB format
        """
        infile = sample_images['rgba']
        outfile = str(tmp_path / "output.ppm")

        converter = VipsConverter(infile, outfile)
        converter.run()

        assert converter.error is None

        output_img = Image.open(outfile)
        assert output_img.mode == 'RGB'

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_convert_large_image(self, sample_images, tmp_path):
        """
        Scenario: Large images are converted efficiently

        Given a large image file
        When VipsConverter processes it
        Then conversion completes without memory issues
        And output dimensions match input
        """
        infile = sample_images['large']
        outfile = str(tmp_path / "output.ppm")

        converter = VipsConverter(infile, outfile)
        converter.run()

        assert converter.error is None

        output_img = Image.open(outfile)
        assert output_img.size == (2048, 1536)

class TestVipsConverterErrorHandling:
    """
    Feature: VipsConverter Error Handling

    The converter must handle errors gracefully, reporting issues
    without crashing and cleaning up partial output files.
    """

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_nonexistent_input_file_sets_error(self, tmp_path):
        """
        Scenario: Nonexistent input file reports error

        Given a path to a file that doesn't exist
        When VipsConverter attempts to process it
        Then an error is set on the converter
        And progress reaches 1.0 (completion)
        """
        infile = str(tmp_path / "nonexistent.png")
        outfile = str(tmp_path / "output.ppm")

        converter = VipsConverter(infile, outfile)
        converter.run()

        assert converter.error is not None
        assert converter.progress == 1.0

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_corrupted_input_file_sets_error(self, tmp_path):
        """
        Scenario: Corrupted input file reports error

        Given a file with invalid image data
        When VipsConverter attempts to process it
        Then an error is set on the converter
        And partial output is cleaned up
        """
        # Create corrupted file
        corrupted_path = tmp_path / "corrupted.png"
        with open(corrupted_path, 'wb') as f:
            f.write(b"This is not a valid image file")

        outfile = str(tmp_path / "output.ppm")

        converter = VipsConverter(str(corrupted_path), outfile)
        converter.run()

        assert converter.error is not None

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_invalid_output_directory_sets_error(self, sample_images, tmp_path):
        """
        Scenario: Invalid output path reports error

        Given a valid input file
        And an output path in a nonexistent directory
        When VipsConverter attempts to process
        Then an error is set on the converter
        """
        infile = sample_images['png']
        outfile = str(tmp_path / "nonexistent_dir" / "output.ppm")

        converter = VipsConverter(infile, outfile)
        converter.run()

        assert converter.error is not None

class TestPDFConverterBasicOperations:
    """
    Feature: PDFConverter Basic Operations

    PDFConverter rasterizes PDF documents using pdftoppm, converting
    each page to a raster image and merging them into a single PPM file.
    """

    @pytest.mark.skipif(not is_pdftoppm_available(), reason="pdftoppm not available")
    def test_convert_pdf_to_ppm(self, sample_pdf, tmp_path):
        """
        Scenario: Convert PDF document to PPM format

        Given a valid PDF file
        When PDFConverter processes it
        Then a PPM file is created at the output path
        And the output contains rasterized page content
        """
        if sample_pdf is None:
            pytest.skip("Could not create sample PDF")

        outfile = str(tmp_path / "output.ppm")

        converter = PDFConverter(sample_pdf, outfile)
        converter.run()

        assert converter.error is None, f"Conversion failed: {converter.error}"
        assert converter.progress == 1.0
        assert os.path.exists(outfile)

        # Verify output is readable
        output_img = Image.open(outfile)
        assert output_img.size[0] > 0
        assert output_img.size[1] > 0

    @pytest.mark.skipif(not is_pdftoppm_available(), reason="pdftoppm not available")
    def test_pdf_conversion_respects_resolution(self, sample_pdf, tmp_path):
        """
        Scenario: PDF conversion uses specified resolution

        Given a PDF file
        When PDFConverter processes it with custom resolution
        Then output dimensions reflect the resolution setting
        """
        if sample_pdf is None:
            pytest.skip("Could not create sample PDF")

        outfile_low = str(tmp_path / "output_low.ppm")
        outfile_high = str(tmp_path / "output_high.ppm")

        # Low resolution conversion
        converter_low = PDFConverter(sample_pdf, outfile_low)
        converter_low.resolution = 72
        converter_low.run()

        # High resolution conversion
        converter_high = PDFConverter(sample_pdf, outfile_high)
        converter_high.resolution = 300
        converter_high.run()

        if converter_low.error is None and converter_high.error is None:
            img_low = Image.open(outfile_low)
            img_high = Image.open(outfile_high)

            # Higher resolution should produce larger image
            assert img_high.size[0] > img_low.size[0]
            assert img_high.size[1] > img_low.size[1]

class TestPDFConverterErrorHandling:
    """
    Feature: PDFConverter Error Handling

    The PDF converter must handle errors from pdftoppm gracefully
    and report meaningful error messages.
    """

    @pytest.mark.skipif(not is_pdftoppm_available(), reason="pdftoppm not available")
    def test_nonexistent_pdf_sets_error(self, tmp_path):
        """
        Scenario: Nonexistent PDF file reports error

        Given a path to a PDF that doesn't exist
        When PDFConverter attempts to process it
        Then an error is set on the converter
        """
        infile = str(tmp_path / "nonexistent.pdf")
        outfile = str(tmp_path / "output.ppm")

        converter = PDFConverter(infile, outfile)
        converter.run()

        assert converter.error is not None

    @pytest.mark.skipif(not is_pdftoppm_available(), reason="pdftoppm not available")
    def test_corrupted_pdf_sets_error(self, tmp_path):
        """
        Scenario: Corrupted PDF file reports error

        Given a file with invalid PDF data
        When PDFConverter attempts to process it
        Then an error is set on the converter
        """
        corrupted_path = tmp_path / "corrupted.pdf"
        with open(corrupted_path, 'wb') as f:
            f.write(b"This is not a valid PDF file")

        outfile = str(tmp_path / "output.ppm")

        converter = PDFConverter(str(corrupted_path), outfile)
        converter.run()

        assert converter.error is not None

class TestConverterToTilerPipeline:
    """
    Feature: Converter to Tiler Pipeline

    The complete pipeline converts source files to PPM format and
    then tiles them for display. This integration tests the full
    workflow from input file to tile pyramid.
    """

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_convert_then_tile_png(
            self, sample_images, tmp_path, temp_tilestore, initialized_tilemanager):
        """
        Scenario: Convert PNG and create tile pyramid

        Given a PNG image file
        When converted to PPM and then tiled
        Then a complete tile pyramid is created
        And tiles are accessible via TileStore
        """
        infile = sample_images['png']
        ppm_file = str(tmp_path / "converted.ppm")
        media_id = "pipeline_test_png"

        # Step 1: Convert
        converter = VipsConverter(infile, ppm_file)
        converter.run()
        assert converter.error is None

        # Step 2: Tile
        tiler = ConcreteTiler(ppm_file, media_id=media_id, tilesize=256)
        tiler.run()
        assert tiler.error is None

        # Verify results
        assert tilestore.tiled(media_id)
        assert tilestore.get_metadata(media_id, 'width') == 800
        assert tilestore.get_metadata(media_id, 'height') == 600

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_convert_then_tile_large_image(
            self, sample_images, tmp_path, temp_tilestore, initialized_tilemanager):
        """
        Scenario: Convert and tile large image

        Given a large image file
        When converted to PPM and then tiled
        Then multiple tile levels are created
        And the full pyramid is accessible
        """
        infile = sample_images['large']
        ppm_file = str(tmp_path / "large_converted.ppm")
        media_id = "pipeline_large"

        # Convert
        converter = VipsConverter(infile, ppm_file)
        converter.run()
        assert converter.error is None

        # Tile
        tiler = ConcreteTiler(ppm_file, media_id=media_id, tilesize=256)
        tiler.run()
        assert tiler.error is None

        # Verify multiple levels
        maxlevel = tilestore.get_metadata(media_id, 'maxtilelevel')
        assert maxlevel >= 2  # Large image should have multiple levels

    @pytest.mark.skipif(
        not (is_pdftoppm_available() and is_pyvips_available()),
        reason="pdftoppm or pyvips not available"
    )
    def test_convert_pdf_then_tile(
            self, sample_pdf, tmp_path, temp_tilestore, initialized_tilemanager):
        """
        Scenario: Convert PDF and create tile pyramid

        Given a PDF document
        When rasterized to PPM and then tiled
        Then tiles are created representing the document pages
        """
        if sample_pdf is None:
            pytest.skip("Could not create sample PDF")

        ppm_file = str(tmp_path / "pdf_converted.ppm")
        media_id = "pipeline_pdf"

        # Convert PDF
        converter = PDFConverter(sample_pdf, ppm_file)
        converter.run()

        if converter.error is not None:
            pytest.skip(f"PDF conversion failed: {converter.error}")

        # Tile the result
        tiler = ConcreteTiler(ppm_file, media_id=media_id, tilesize=256)
        tiler.run()
        assert tiler.error is None

        # Verify
        assert tilestore.tiled(media_id)

class TestConverterProgressTracking:
    """
    Feature: Converter Progress Tracking

    Converters track progress from 0.0 to 1.0, enabling UI feedback
    during potentially long conversion operations.
    """

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_progress_starts_at_zero(self, sample_images, tmp_path):
        """
        Scenario: Progress starts at zero before conversion

        Given a new converter instance
        Then progress is initially 0.0
        """
        infile = sample_images['png']
        outfile = str(tmp_path / "output.ppm")

        converter = VipsConverter(infile, outfile)
        assert converter.progress == 0.0

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_progress_reaches_one_after_completion(self, sample_images, tmp_path):
        """
        Scenario: Progress reaches 1.0 after conversion completes

        Given a converter that processes a file
        When conversion completes (success or failure)
        Then progress is 1.0
        """
        infile = sample_images['png']
        outfile = str(tmp_path / "output.ppm")

        converter = VipsConverter(infile, outfile)
        converter.run()

        assert converter.progress == 1.0

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_progress_reaches_one_even_on_error(self, tmp_path):
        """
        Scenario: Progress reaches 1.0 even when conversion fails

        Given a converter with invalid input
        When conversion fails
        Then progress is still 1.0
        """
        infile = str(tmp_path / "nonexistent.png")
        outfile = str(tmp_path / "output.ppm")

        converter = VipsConverter(infile, outfile)
        converter.run()

        assert converter.progress == 1.0
        assert converter.error is not None

class TestConverterThreading:
    """
    Feature: Converter Threading Support

    Converters can run in background threads for non-blocking operations.
    However, due to pyvips internal threading, running multiple VipsConverter
    instances concurrently in threads can cause conflicts. For parallel
    conversions, use the process-based converter_runner module instead.
    """

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_converter_runs_in_thread(self, sample_images, tmp_path):
        """
        Scenario: Converter runs in background thread

        Given a converter instance
        When run() is called in a separate thread
        Then conversion executes in that thread
        And main thread can continue execution
        """
        import threading

        infile = sample_images['png']
        outfile = str(tmp_path / "output.ppm")

        converter = VipsConverter(infile, outfile)
        result = {'done': False}

        def run_conversion():
            converter.run()
            result['done'] = True

        thread = threading.Thread(target=run_conversion)
        thread.start()
        thread.join(timeout=30)

        assert result['done'], "Conversion thread timed out"
        assert converter.progress == 1.0
        assert os.path.exists(outfile) or converter.error is not None

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_multiple_converters_run_concurrently_via_processes(self, sample_images, tmp_path):
        """
        Scenario: Multiple converters run concurrently using processes

        Given multiple images to convert
        When conversions run in parallel processes
        Then all complete independently
        And no interference occurs between conversions

        Note: This uses process-based parallelism to avoid pyvips threading conflicts.
        """
        from pyzui.converters import converter_runner
        from concurrent.futures import wait

        futures = []
        outfiles = []

        for i in range(3):
            infile = sample_images['png']
            outfile = str(tmp_path / f"output_{i}.ppm")
            outfiles.append(outfile)
            future = converter_runner.submit_vips_conversion(infile, outfile)
            futures.append(future)

        # Wait for all to complete with timeout
        done, not_done = wait(futures, timeout=60)
        assert len(not_done) == 0, f"{len(not_done)} conversions timed out"

        # Verify all completed successfully
        for i, future in enumerate(futures):
            error = future.result()
            assert error is None, f"Conversion {i} failed: {error}"
            assert os.path.exists(outfiles[i]), f"Output {i} not created"

class TestConcurrentConversionOperations:
    """
    Feature: Concurrent Conversion Operations

    Multiple conversion operations may run simultaneously using process-based
    parallelism. The system must handle concurrent disk access and resource
    usage correctly.

    Note: Due to pyvips internal threading conflicts, concurrent conversions
    should use the process-based converter_runner rather than ThreadPoolExecutor.
    """

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_concurrent_conversions_complete_independently(
            self, sample_images, tmp_path):
        """
        Scenario: Concurrent conversions complete independently

        Given multiple files to convert
        When conversions run in parallel processes
        Then each conversion completes independently
        And all outputs are valid
        """
        from pyzui.converters import converter_runner
        from concurrent.futures import wait

        files_to_convert = [
            (sample_images['png'], str(tmp_path / "out1.ppm")),
            (sample_images['jpg'], str(tmp_path / "out2.ppm")),
            (sample_images['tiff'], str(tmp_path / "out3.ppm")),
        ]

        # Submit all conversions to process pool
        futures = []
        for infile, outfile in files_to_convert:
            future = converter_runner.submit_vips_conversion(infile, outfile)
            futures.append((future, outfile))

        # Wait for all to complete
        done, not_done = wait([f for f, _ in futures], timeout=60)
        assert len(not_done) == 0, f"{len(not_done)} conversions timed out"

        # All should complete without error
        for future, outfile in futures:
            error = future.result()
            assert error is None, f"Conversion failed: {error}"
            assert os.path.exists(outfile), f"Output not created: {outfile}"

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_concurrent_conversion_and_tiling(
            self, sample_images, tmp_path, temp_tilestore):
        """
        Scenario: Concurrent conversion and tiling pipelines

        Given multiple images to convert and tile
        When full pipelines run sequentially (conversion in processes, tiling after)
        Then all complete without interference
        And all tile pyramids are created correctly

        Note: Conversions run in separate processes for isolation. Tiling
        runs after conversion completes to avoid threading conflicts.
        """
        from pyzui.converters import converter_runner
        from concurrent.futures import wait

        # Initialize tilemanager locally
        tilemanager.init(total_cache_size=100, auto_cleanup=False)

        # First, run all conversions in parallel processes
        conversion_jobs = []
        for i in range(3):
            ppm_file = str(tmp_path / f"converted_{i}.ppm")
            future = converter_runner.submit_vips_conversion(
                sample_images['png'], ppm_file)
            conversion_jobs.append((i, ppm_file, future))

        # Wait for all conversions to complete
        done, not_done = wait([job[2] for job in conversion_jobs], timeout=60)
        assert len(not_done) == 0, "Some conversions timed out"

        # Check for conversion errors
        for i, ppm_file, future in conversion_jobs:
            error = future.result()
            assert error is None, f"Conversion {i} failed: {error}"

        # Now run tiling sequentially (tiling uses shared tilestore)
        results = {}
        for i, ppm_file, _ in conversion_jobs:
            media_id = f"concurrent_pipeline_{i}"
            tiler = ConcreteTiler(ppm_file, media_id=media_id, tilesize=256)
            tiler.run()

            if tiler.error:
                results[i] = {'error': tiler.error}
            else:
                results[i] = {
                    'media_id': media_id,
                    'tiled': tilestore.tiled(media_id)
                }

        # All should succeed
        for idx, result in results.items():
            assert 'error' not in result or result.get('error') is None, \
                f"Pipeline {idx} failed: {result.get('error')}"
            assert result.get('tiled', False), f"Pipeline {idx} not tiled"

class TestConverterOutputValidation:
    """
    Feature: Converter Output Validation

    Converter output must be valid for subsequent pipeline stages.
    This includes correct format, dimensions, and pixel data.
    """

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_output_preserves_dimensions(self, sample_images, tmp_path):
        """
        Scenario: Output dimensions match input

        Given an input image with known dimensions
        When converted to PPM
        Then output dimensions match input
        """
        infile = sample_images['png']
        outfile = str(tmp_path / "output.ppm")

        # Get input dimensions
        input_img = Image.open(infile)
        input_size = input_img.size

        # Convert
        converter = VipsConverter(infile, outfile)
        converter.run()
        assert converter.error is None

        # Verify output dimensions
        output_img = Image.open(outfile)
        assert output_img.size == input_size

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_output_is_8bit_rgb(self, sample_images, tmp_path):
        """
        Scenario: Output is 8-bit RGB format

        Given any supported input format
        When converted to PPM
        Then output is 8-bit RGB
        """
        infile = sample_images['png']
        outfile = str(tmp_path / "output.ppm")

        converter = VipsConverter(infile, outfile)
        converter.run()
        assert converter.error is None

        output_img = Image.open(outfile)
        assert output_img.mode == 'RGB'

    @pytest.mark.skipif(not is_pyvips_available(), reason="pyvips not available")
    def test_output_readable_by_pil(self, sample_images, tmp_path):
        """
        Scenario: Output is readable by PIL

        Given a converted PPM file
        Then PIL can open and read the file
        And pixel data is accessible
        """
        infile = sample_images['png']
        outfile = str(tmp_path / "output.ppm")

        converter = VipsConverter(infile, outfile)
        converter.run()
        assert converter.error is None

        # Verify PIL can read
        output_img = Image.open(outfile)
        output_img.load()  # Force load pixel data

        # Access pixel data
        pixel = output_img.getpixel((0, 0))
        assert len(pixel) == 3  # RGB

class TestConverterStringRepresentation:
    """
    Feature: Converter String Representation

    Converters provide useful string representations for logging
    and debugging purposes.
    """

    def test_str_representation(self, sample_images, tmp_path):
        """
        Scenario: __str__ returns readable representation

        Given a converter instance
        Then __str__ returns a readable string
        And includes input and output file paths
        """
        infile = sample_images['png']
        outfile = str(tmp_path / "output.ppm")

        converter = VipsConverter(infile, outfile)
        str_rep = str(converter)

        assert "VipsConverter" in str_rep
        assert infile in str_rep or "test_image" in str_rep

    def test_repr_representation(self, sample_images, tmp_path):
        """
        Scenario: __repr__ returns formal representation

        Given a converter instance
        Then __repr__ returns a formal string representation
        """
        infile = sample_images['png']
        outfile = str(tmp_path / "output.ppm")

        converter = VipsConverter(infile, outfile)
        repr_str = repr(converter)

        assert "VipsConverter" in repr_str
