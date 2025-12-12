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
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pyzui.converters.vipsconverter import VipsConverter

class TestVipsConverter:
    """
    Feature: Vips Converter

    This test suite validates the VipsConverter class which converts various image formats
    to PPM using the pyvips library, handling different color depths and band configurations.
    """

    def test_init(self):
        """
        Scenario: Initialize Vips converter

        Given input and output file paths
        When a VipsConverter is instantiated
        Then it should store the file paths
        And bitdepth should be set to 8
        """
        converter = VipsConverter("input.jpg", "output.ppm")
        assert converter._infile == "input.jpg"
        assert converter._outfile == "output.ppm"
        assert converter.bitdepth == 8

    def test_inherits_from_converter(self):
        """
        Scenario: Verify inheritance from Converter

        Given a VipsConverter instance
        When checking its type
        Then it should be an instance of Converter
        """
        from pyzui.converters.converter import Converter
        converter = VipsConverter("input.jpg", "output.ppm")
        assert isinstance(converter, Converter)

    def test_bitdepth_attribute(self):
        """
        Scenario: Verify bitdepth setting

        Given a newly created VipsConverter
        When checking the bitdepth attribute
        Then it should be 8
        """
        converter = VipsConverter("input.jpg", "output.ppm")
        assert converter.bitdepth == 8

    @patch('pyvips.Image.new_from_file')
    def test_run_success(self, mock_new_from_file):
        """
        Scenario: Successfully convert image to PPM

        Given a VipsConverter with mocked pyvips
        When run is called with a valid 8-bit RGB image
        Then the image should be converted and written
        And progress should be 1.0
        And error should be None
        """
        # Create a mock image
        mock_image = Mock()
        mock_image.width = 100
        mock_image.height = 100
        mock_image.bands = 3
        mock_image.format = 'uchar'
        mock_image.write_to_file = Mock()
        mock_new_from_file.return_value = mock_image

        converter = VipsConverter("input.jpg", "output.ppm")
        converter.run()

        assert converter._progress == 1.0
        assert converter.error is None
        mock_new_from_file.assert_called_once_with("input.jpg", access='sequential')
        mock_image.write_to_file.assert_called_once_with("output.ppm")

    @patch('pyvips.Image.new_from_file')
    def test_run_converts_16bit_to_8bit(self, mock_new_from_file):
        """
        Scenario: Convert 16-bit image to 8-bit

        Given a VipsConverter with mocked 16-bit image
        When run is called
        Then the image should be cast to uchar (8-bit)
        And progress should be 1.0
        And error should be None
        """
        # Create a mock 16-bit image
        mock_image = Mock()
        mock_image.width = 100
        mock_image.height = 100
        mock_image.bands = 3
        mock_image.format = 'ushort'  # 16-bit
        mock_image.cast = Mock(return_value=mock_image)
        mock_image.write_to_file = Mock()
        mock_new_from_file.return_value = mock_image

        converter = VipsConverter("input.tif", "output.ppm")
        converter.run()

        assert converter._progress == 1.0
        assert converter.error is None
        mock_image.cast.assert_called_once_with('uchar')

    @patch('pyvips.Image.new_from_file')
    def test_run_handles_rgba_images(self, mock_new_from_file):
        """
        Scenario: Handle RGBA image by flattening

        Given a VipsConverter with mocked RGBA image
        When run is called
        Then the image should be flattened to remove alpha channel
        And progress should be 1.0
        And error should be None
        """
        # Create a mock RGBA image
        mock_image = Mock()
        mock_image.width = 100
        mock_image.height = 100
        mock_image.bands = 4  # RGBA
        mock_image.format = 'uchar'
        mock_flattened = Mock()
        mock_flattened.write_to_file = Mock()
        mock_image.flatten = Mock(return_value=mock_flattened)
        mock_new_from_file.return_value = mock_image

        converter = VipsConverter("input.png", "output.ppm")
        converter.run()

        assert converter._progress == 1.0
        assert converter.error is None
        mock_image.flatten.assert_called_once()
        mock_flattened.write_to_file.assert_called_once_with("output.ppm")

    @patch('pyvips.Image.new_from_file')
    def test_run_handles_multiband_images(self, mock_new_from_file):
        """
        Scenario: Handle multiband image by extracting RGB bands

        Given a VipsConverter with mocked multiband image (>3 bands)
        When run is called
        Then the first 3 bands should be extracted
        And progress should be 1.0
        And error should be None
        """
        # Create a mock multiband image
        mock_image = Mock()
        mock_image.width = 100
        mock_image.height = 100
        mock_image.bands = 5  # e.g., multispectral image
        mock_image.format = 'uchar'
        mock_extracted = Mock()
        mock_extracted.write_to_file = Mock()
        mock_image.extract_band = Mock(return_value=mock_extracted)
        mock_new_from_file.return_value = mock_image

        converter = VipsConverter("input.tif", "output.ppm")
        converter.run()

        assert converter._progress == 1.0
        assert converter.error is None
        mock_image.extract_band.assert_called_once_with(0, n=3)
        mock_extracted.write_to_file.assert_called_once_with("output.ppm")

    @patch('pyvips.Image.new_from_file')
    @patch('os.path.exists')
    @patch('os.unlink')
    def test_run_handles_errors(self, mock_unlink, mock_exists, mock_new_from_file):
        """
        Scenario: Handle conversion errors gracefully

        Given a VipsConverter with mocked pyvips that raises exception
        When run is called
        Then error should be set with exception message
        And progress should be 1.0
        And partial output file should be deleted
        """
        mock_new_from_file.side_effect = Exception("Failed to load image")
        mock_exists.return_value = True

        converter = VipsConverter("invalid.jpg", "output.ppm")
        converter.run()

        assert converter.error is not None
        assert "conversion failed" in converter.error
        assert "Failed to load image" in converter.error
        assert converter._progress == 1.0
        mock_unlink.assert_called_once_with("output.ppm")

    def test_str_representation(self):
        """
        Scenario: Get string representation

        Given a VipsConverter instance
        When str() is called
        Then it should return the expected format
        """
        converter = VipsConverter("input.jpg", "output.ppm")
        assert str(converter) == "VipsConverter(input.jpg, output.ppm)"

    def test_repr_representation(self):
        """
        Scenario: Get repr representation

        Given a VipsConverter instance
        When repr() is called
        Then it should return the expected format
        """
        converter = VipsConverter("input.jpg", "output.ppm")
        assert repr(converter) == "VipsConverter('input.jpg', 'output.ppm')"

    def test_small_image_conversion(self):
        """
        Scenario: Integration test for small PNG conversion

        Given a small PNG test file
        When VipsConverter converts it to PPM
        Then the conversion should succeed
        And progress should be 1.0
        And output file should exist with valid PPM format
        """
        infile = "data/black_white_split_5x5.png"

        # Skip test if file doesn't exist
        if not os.path.exists(infile):
            pytest.skip(f"Test file not found: {infile}")

        # Create temporary output file
        with tempfile.NamedTemporaryFile(suffix='.ppm', delete=False) as tmp:
            outfile = tmp.name

        try:
            # Create and run converter
            converter = VipsConverter(infile, outfile)
            converter.start()
            converter.join()

            # Verify conversion succeeded
            assert converter.error is None, f"Conversion failed: {converter.error}"
            assert converter._progress == 1.0
            assert os.path.exists(outfile), "Output file not created"
            assert os.path.getsize(outfile) > 0, "Output file is empty"

            # Verify it's a valid PPM file (P6 binary format)
            with open(outfile, 'rb') as f:
                magic = f.read(2)
                assert magic == b'P6', f"Invalid PPM format, magic number: {magic}"

        finally:
            # Cleanup
            if os.path.exists(outfile):
                os.unlink(outfile)

    def test_large_tiff_conversion(self):
        """
        Scenario: Integration test for large TIFF conversion

        Given a large TIFF test file
        When VipsConverter converts it to PPM
        Then the conversion should succeed
        And progress should be 1.0
        And output file should exist with valid PPM format
        """
        infile = "data/eso1031b.tif"

        # Skip test if file doesn't exist
        if not os.path.exists(infile):
            pytest.skip(f"Test file not found: {infile}")

        # Create temporary output file
        with tempfile.NamedTemporaryFile(suffix='.ppm', delete=False) as tmp:
            outfile = tmp.name

        try:
            # Create and run converter
            converter = VipsConverter(infile, outfile)
            converter.start()
            converter.join()

            # Verify conversion succeeded
            assert converter.error is None, f"Conversion failed: {converter.error}"
            assert converter._progress == 1.0
            assert os.path.exists(outfile), "Output file not created"
            assert os.path.getsize(outfile) > 0, "Output file is empty"

            # Verify it's a valid PPM file (P6 binary format)
            with open(outfile, 'rb') as f:
                magic = f.read(2)
                assert magic == b'P6', f"Invalid PPM format, magic number: {magic}"

        finally:
            # Cleanup
            if os.path.exists(outfile):
                os.unlink(outfile)

    def test_jpeg_conversion(self):
        """
        Scenario: Integration test for JPEG conversion

        Given a JPEG test file
        When VipsConverter converts it to PPM
        Then the conversion should succeed
        And progress should be 1.0
        And output file should exist with valid PPM format
        """
        infile = "data/eso1031b.jpg"

        # Skip test if file doesn't exist
        if not os.path.exists(infile):
            pytest.skip(f"Test file not found: {infile}")

        # Create temporary output file
        with tempfile.NamedTemporaryFile(suffix='.ppm', delete=False) as tmp:
            outfile = tmp.name

        try:
            # Create and run converter
            converter = VipsConverter(infile, outfile)
            converter.start()
            converter.join()

            # Verify conversion succeeded
            assert converter.error is None, f"Conversion failed: {converter.error}"
            assert converter._progress == 1.0
            assert os.path.exists(outfile), "Output file not created"
            assert os.path.getsize(outfile) > 0, "Output file is empty"

            # Verify it's a valid PPM file (P6 binary format)
            with open(outfile, 'rb') as f:
                magic = f.read(2)
                assert magic == b'P6', f"Invalid PPM format, magic number: {magic}"

        finally:
            # Cleanup
            if os.path.exists(outfile):
                os.unlink(outfile)
