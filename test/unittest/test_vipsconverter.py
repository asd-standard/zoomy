import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pyzui.vipsconverter import VipsConverter

class TestVipsConverter:
    """Test suite for the VipsConverter class."""

    def test_init(self):
        """Test VipsConverter initialization."""
        converter = VipsConverter("input.jpg", "output.ppm")
        assert converter._infile == "input.jpg"
        assert converter._outfile == "output.ppm"
        assert converter.bitdepth == 8

    def test_inherits_from_converter(self):
        """Test that VipsConverter inherits from Converter."""
        from pyzui.converter import Converter
        converter = VipsConverter("input.jpg", "output.ppm")
        assert isinstance(converter, Converter)

    def test_bitdepth_attribute(self):
        """Test bitdepth attribute is set to 8."""
        converter = VipsConverter("input.jpg", "output.ppm")
        assert converter.bitdepth == 8

    @patch('pyvips.Image.new_from_file')
    def test_run_success(self, mock_new_from_file):
        """Test run method with successful conversion."""
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
        """Test that 16-bit images are converted to 8-bit."""
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
        """Test that RGBA images are flattened to RGB."""
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
        """Test that multiband images (>3 bands) are handled correctly."""
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
        """Test run method handles conversion errors."""
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
        """Test string representation."""
        converter = VipsConverter("input.jpg", "output.ppm")
        assert str(converter) == "VipsConverter(input.jpg, output.ppm)"

    def test_repr_representation(self):
        """Test repr representation."""
        converter = VipsConverter("input.jpg", "output.ppm")
        assert repr(converter) == "VipsConverter('input.jpg', 'output.ppm')"

    def test_small_image_conversion(self):
        """Integration test: Convert a small PNG to PPM format."""
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
        """Integration test: Convert large TIFF file to PPM format."""
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
        """Integration test: Convert JPEG file to PPM format."""
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
