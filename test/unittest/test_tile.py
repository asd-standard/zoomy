import pytest
from unittest.mock import Mock, MagicMock, patch
from PIL import Image
from PySide6 import QtGui
from pyzui import tile
from pyzui.tile import Tile

class TestTile:
    """Test suite for the Tile class."""

    def test_init_with_pil_image(self):
        """Test Tile initialization with PIL Image."""
        pil_image = Image.new('RGB', (100, 100))
        t = Tile(pil_image)
        assert t.size == (100, 100)

    def test_init_with_qimage(self):
        """Test Tile initialization with QImage."""
        qimage = QtGui.QImage(100, 100, QtGui.QImage.Format_RGB32)
        t = Tile(qimage)
        assert t.size == (100, 100)

    def test_size_property(self):
        """Test size property returns correct dimensions."""
        qimage = QtGui.QImage(200, 150, QtGui.QImage.Format_RGB32)
        t = Tile(qimage)
        assert t.size == (200, 150)

    def test_crop(self):
        """Test crop method returns cropped tile."""
        qimage = QtGui.QImage(100, 100, QtGui.QImage.Format_RGB32)
        t = Tile(qimage)
        cropped = t.crop((10, 10, 50, 50))
        assert isinstance(cropped, Tile)
        assert cropped.size == (40, 40)

    def test_resize(self):
        """Test resize method returns resized tile."""
        qimage = QtGui.QImage(100, 100, QtGui.QImage.Format_RGB32)
        t = Tile(qimage)
        resized = t.resize(200, 200)
        assert isinstance(resized, Tile)
        assert resized.size == (200, 200)

    def test_resize_to_smaller_size(self):
        """Test resize method with smaller dimensions."""
        qimage = QtGui.QImage(100, 100, QtGui.QImage.Format_RGB32)
        t = Tile(qimage)
        resized = t.resize(50, 50)
        assert resized.size == (50, 50)

    @patch('pyzui.tile.QtGui.QImage.save')
    def test_save(self, mock_save):
        """Test save method calls QImage.save."""
        qimage = QtGui.QImage(100, 100, QtGui.QImage.Format_RGB32)
        t = Tile(qimage)
        t.save("test.png")
        mock_save.assert_called_once_with("test.png")

    def test_draw(self):
        """Test draw method with painter."""
        qimage = QtGui.QImage(100, 100, QtGui.QImage.Format_RGB32)
        t = Tile(qimage)
        painter = Mock()
        t.draw(painter, 10, 20)
        painter.drawImage.assert_called_once()


class TestTileFunctions:
    """Test suite for tile module functions."""

    def test_new(self):
        """Test new function creates tile with correct dimensions."""
        t = tile.new(100, 100)
        assert isinstance(t, Tile)
        assert t.size == (100, 100)

    def test_new_different_dimensions(self):
        """Test new function with different dimensions."""
        t = tile.new(200, 150)
        assert t.size == (200, 150)

    def test_fromstring(self):
        """Test fromstring function creates tile from raw pixels."""
        width, height = 2, 2
        raw_pixels = '\xFF\x00\x00\xFF\x00\x00\x00\xFF\x00\x00\xFF\x00'
        t = tile.fromstring(raw_pixels, width, height)
        assert isinstance(t, Tile)
        assert t.size == (width, height)

    def test_merged_all_tiles(self):
        """Test merged function with all four tiles."""
        qimage1 = QtGui.QImage(10, 10, QtGui.QImage.Format_RGB32)
        qimage2 = QtGui.QImage(10, 10, QtGui.QImage.Format_RGB32)
        qimage3 = QtGui.QImage(10, 10, QtGui.QImage.Format_RGB32)
        qimage4 = QtGui.QImage(10, 10, QtGui.QImage.Format_RGB32)

        t1 = Tile(qimage1)
        t2 = Tile(qimage2)
        t3 = Tile(qimage3)
        t4 = Tile(qimage4)

        merged = tile.merged(t1, t2, t3, t4)
        assert isinstance(merged, Tile)
        assert merged.size == (20, 20)

    def test_merged_with_some_none(self):
        """Test merged function with some None tiles."""
        qimage1 = QtGui.QImage(10, 10, QtGui.QImage.Format_RGB32)
        qimage2 = QtGui.QImage(10, 10, QtGui.QImage.Format_RGB32)

        t1 = Tile(qimage1)
        t2 = Tile(qimage2)

        merged = tile.merged(t1, t2, None, None)
        assert isinstance(merged, Tile)
        assert merged.size == (20, 10)

    def test_merged_only_t1(self):
        """Test merged function with only first tile."""
        qimage1 = QtGui.QImage(10, 10, QtGui.QImage.Format_RGB32)
        t1 = Tile(qimage1)

        merged = tile.merged(t1, None, None, None)
        assert isinstance(merged, Tile)
        assert merged.size == (10, 10)
