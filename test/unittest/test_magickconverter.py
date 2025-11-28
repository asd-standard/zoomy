import pytest
from unittest.mock import Mock, patch, MagicMock
from pyzui.magickconverter import MagickConverter

class TestMagickConverter:
    """Test suite for the MagickConverter class."""

    def test_init(self):
        """Test MagickConverter initialization."""
        converter = MagickConverter("input.jpg", "output.png")
        assert converter._infile == "input.jpg"
        assert converter._outfile == "output.png"
        assert converter.bitdepth == 8

    def test_inherits_from_converter(self):
        """Test that MagickConverter inherits from Converter."""
        from pyzui.converter import Converter
        converter = MagickConverter("input.jpg", "output.png")
        assert isinstance(converter, Converter)

    def test_bitdepth_attribute(self):
        """Test bitdepth attribute is set to 8."""
        converter = MagickConverter("input.jpg", "output.png")
        assert converter.bitdepth == 8

    @patch('subprocess.Popen')
    @patch('os.name', 'posix')
    def test_run_success_unix(self, mock_popen):
        """Test run method on Unix systems."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b'', b'')
        mock_popen.return_value = mock_process

        converter = MagickConverter("input.jpg", "output.png")
        converter.run()

        assert converter._progress == 1.0
        assert converter.error is None

    @patch('subprocess.Popen')
    @patch('os.name', 'nt')
    def test_run_uses_imconvert_on_windows(self, mock_popen):
        """Test run method uses 'imconvert' on Windows."""
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b'', b'')
        mock_popen.return_value = mock_process

        converter = MagickConverter("input.jpg", "output.png")
        converter.run()

        # Should use imconvert on Windows
        args = mock_popen.call_args[0][0]
        assert args[0] == 'imconvert'

    @patch('subprocess.Popen')
    @patch('os.unlink')
    def test_run_failure(self, mock_unlink, mock_popen):
        """Test run method handles conversion failure."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (b'Error message', b'')
        mock_popen.return_value = mock_process

        converter = MagickConverter("input.jpg", "output.png")
        converter.run()

        assert converter.error is not None
        assert "conversion failed" in converter.error
        assert converter._progress == 1.0

    def test_str_representation(self):
        """Test string representation."""
        converter = MagickConverter("input.jpg", "output.png")
        assert str(converter) == "MagickConverter(input.jpg, output.png)"

    def test_repr_representation(self):
        """Test repr representation."""
        converter = MagickConverter("input.jpg", "output.png")
        assert repr(converter) == "MagickConverter('input.jpg', 'output.png')"

    def test_tiff_to_ppm_conversion(self):
        """Integration test: Convert TIFF file to PPM format."""
        import os
        import tempfile

        infile = "data/eso1031b.tif"

        # Skip test if file doesn't exist
        if not os.path.exists(infile):
            pytest.skip(f"Test file not found: {infile}")

        # Create temporary output file
        with tempfile.NamedTemporaryFile(suffix='.ppm', delete=False) as tmp:
            outfile = tmp.name

        try:
            # Create and run converter
            converter = MagickConverter(infile, outfile)
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
