import pytest
from unittest.mock import Mock, patch, mock_open, MagicMock
from pyzui.pdfconverter import PDFConverter

class TestPDFConverter:
    """Test suite for the PDFConverter class."""

    def test_init(self):
        """Test PDFConverter initialization."""
        converter = PDFConverter("input.pdf", "output.ppm")
        assert converter._infile == "input.pdf"
        assert converter._outfile == "output.ppm"
        assert converter.resolution == 300

    def test_inherits_from_converter(self):
        """Test that PDFConverter inherits from Converter."""
        from pyzui.converter import Converter
        converter = PDFConverter("input.pdf", "output.ppm")
        assert isinstance(converter, Converter)

    def test_resolution_attribute(self):
        """Test resolution attribute defaults to 300."""
        converter = PDFConverter("input.pdf", "output.ppm")
        assert converter.resolution == 300

    def test_resolution_can_be_changed(self):
        """Test resolution attribute can be modified."""
        converter = PDFConverter("input.pdf", "output.ppm")
        converter.resolution = 150
        assert converter.resolution == 150

    @patch('subprocess.Popen')
    @patch('tempfile.mkdtemp')
    @patch('shutil.rmtree')
    def test_run_success(self, mock_rmtree, mock_mkdtemp, mock_popen):
        """Test run method with successful conversion."""
        mock_mkdtemp.return_value = '/tmp/test'
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b'', b'')
        mock_popen.return_value = mock_process

        converter = PDFConverter("input.pdf", "output.ppm")

        # Mock the merge method to avoid file operations
        with patch.object(converter, '_PDFConverter__merge'):
            converter.run()
            assert converter._progress == 1.0

    @patch('subprocess.Popen')
    @patch('tempfile.mkdtemp')
    @patch('shutil.rmtree')
    def test_run_pdftoppm_failure(self, mock_rmtree, mock_mkdtemp, mock_popen):
        """Test run method handles pdftoppm failure."""
        mock_mkdtemp.return_value = '/tmp/test'
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (b'Error', b'')
        mock_popen.return_value = mock_process

        converter = PDFConverter("input.pdf", "output.ppm")
        converter.run()

        assert converter.error is not None
        assert "conversion failed" in converter.error
        assert converter._progress == 1.0

    @patch('subprocess.Popen')
    @patch('tempfile.mkdtemp')
    @patch('shutil.rmtree')
    def test_run_cleans_tmpdir(self, mock_rmtree, mock_mkdtemp, mock_popen):
        """Test run method cleans up temporary directory."""
        mock_mkdtemp.return_value = '/tmp/test'
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.communicate.return_value = (b'', b'')
        mock_popen.return_value = mock_process

        converter = PDFConverter("input.pdf", "output.ppm")

        with patch.object(converter, '_PDFConverter__merge'):
            converter.run()
            mock_rmtree.assert_called_once_with('/tmp/test', ignore_errors=True)

    def test_str_representation(self):
        """Test string representation."""
        converter = PDFConverter("input.pdf", "output.ppm")
        assert str(converter) == "PDFConverter(input.pdf, output.ppm)"

    def test_repr_representation(self):
        """Test repr representation."""
        converter = PDFConverter("input.pdf", "output.ppm")
        assert repr(converter) == "PDFConverter('input.pdf', 'output.ppm')"

    @patch('subprocess.Popen')
    def test_run_calls_pdftoppm_with_resolution(self, mock_popen):
        """Test run method calls pdftoppm with correct resolution."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.communicate.return_value = (b'', b'')
        mock_popen.return_value = mock_process

        converter = PDFConverter("input.pdf", "output.ppm")
        converter.resolution = 200

        with patch('tempfile.mkdtemp', return_value='/tmp/test'):
            with patch('shutil.rmtree'):
                converter.run()

        # Check that pdftoppm was called with resolution
        call_args = mock_popen.call_args[0][0]
        assert '-r' in call_args
        assert '200' in call_args
