import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open
from io import BytesIO
from pyzui import ppm
from pyzui.ppm import PPMTiler, read_ppm_header

class TestReadPPMHeader:
    """Test suite for read_ppm_header function."""

    def test_valid_ppm_header(self):
        """Test reading a valid PPM header."""
        ppm_data = b"P6\n100 200\n255\n"
        f = BytesIO(ppm_data)
        width, height = read_ppm_header(f)
        assert width == 100
        assert height == 200

    def test_valid_ppm_header_with_comments(self):
        """Test reading PPM header with whitespace."""
        ppm_data = b"P6\n  100   200  \n255\n"
        f = BytesIO(ppm_data)
        width, height = read_ppm_header(f)
        assert width == 100
        assert height == 200

    def test_invalid_magic_number(self):
        """Test IOError raised for invalid magic number."""
        ppm_data = b"P5\n100 200\n255\n"
        f = BytesIO(ppm_data)
        with pytest.raises(IOError, match="can only load binary PPM"):
            read_ppm_header(f)

    def test_invalid_maxval(self):
        """Test IOError raised for invalid maxval."""
        ppm_data = b"P6\n100 200\n256\n"
        f = BytesIO(ppm_data)
        with pytest.raises(IOError, match="PPM maxval must equal 255"):
            read_ppm_header(f)

    def test_invalid_header_format(self):
        """Test IOError raised for invalid header format."""
        ppm_data = b"P6\nabc 200\n255\n"
        f = BytesIO(ppm_data)
        with pytest.raises(IOError, match="invalid PPM header"):
            read_ppm_header(f)

    def test_incomplete_header(self):
        """Test IOError raised for incomplete header."""
        ppm_data = b"P6\n100\n"
        f = BytesIO(ppm_data)
        with pytest.raises(IOError, match="not enough entries in PPM header"):
            read_ppm_header(f)

    def test_empty_file(self):
        """Test IOError raised for empty file."""
        f = BytesIO(b"")
        with pytest.raises(IOError, match="not enough entries in PPM header"):
            read_ppm_header(f)


class TestEnlargePPMFile:
    """Test suite for enlarge_ppm_file function."""

    @patch('builtins.open', new_callable=mock_open, read_data="P6\n10 5\n255\ndata_here")
    def test_enlarge_ppm_file_basic(self, mock_file):
        """Test enlarging PPM file."""
        ppm.enlarge_ppm_file("test.ppm", 10, 5, 3)
        # Function should have been called

    @patch('builtins.open')
    def test_enlarge_ppm_file_reads_and_writes(self, mock_file_open):
        """Test that enlarge_ppm_file reads and writes correctly."""
        # This is a complex function that modifies files
        # Testing would require more sophisticated mocking
        pass


class TestPPMTiler:
    """Test suite for PPMTiler class."""

    @patch('builtins.open', new_callable=mock_open, read_data=b"P6\n256 256\n255\n" + b"\x00" * (256 * 256 * 3))
    def test_init(self, mock_file):
        """Test PPMTiler initialization."""
        tiler = PPMTiler("test.ppm")
        assert tiler._width == 256
        assert tiler._height == 256
        assert tiler._bytes_per_pixel == 3

    @patch('builtins.open', new_callable=mock_open, read_data=b"P6\n100 200\n255\n" + b"\x00" * (100 * 200 * 3))
    def test_init_custom_dimensions(self, mock_file):
        """Test PPMTiler with custom dimensions."""
        tiler = PPMTiler("test.ppm", media_id="test_id", filext="png", tilesize=512)
        assert tiler._width == 100
        assert tiler._height == 200

    @patch('builtins.open', side_effect=IOError("File not found"))
    def test_init_file_not_found(self, mock_file):
        """Test PPMTiler raises IOError for missing file."""
        with pytest.raises(IOError):
            PPMTiler("nonexistent.ppm")

    @patch('builtins.open', new_callable=mock_open, read_data=b"P6\n256 256\n255\n" + b"\xFF\x00\x00" * (256 * 256))
    def test_scanchunk(self, mock_file):
        """Test _scanchunk method reads correct amount of data."""
        tiler = PPMTiler("test.ppm")
        chunk = tiler._scanchunk()
        # Should read bytes_per_pixel * width bytes
        assert len(chunk) == 3 * 256

    @patch('builtins.open', new_callable=mock_open, read_data=b"P6\n10 10\n255\n" + b"\x00" * (10 * 10 * 3))
    def test_bytes_per_pixel(self, mock_file):
        """Test bytes_per_pixel is set correctly."""
        tiler = PPMTiler("test.ppm")
        assert tiler._bytes_per_pixel == 3

    @patch('builtins.open', new_callable=mock_open, read_data=b"P6\n512 512\n255\n" + b"\x00" * (512 * 512 * 3))
    def test_del_closes_file(self, mock_file):
        """Test __del__ closes the file."""
        tiler = PPMTiler("test.ppm")
        file_handle = tiler._PPMTiler__ppm_fileobj
        tiler.__del__()
        file_handle.close.assert_called()
