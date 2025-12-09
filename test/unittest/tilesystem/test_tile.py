import pytest
from unittest.mock import Mock, MagicMock, patch
from PIL import Image
from PySide6 import QtGui
from pyzui.tilesystem import tile
from pyzui.tilesystem.tile import Tile

class TestTile:
    """
    Feature: Tile Image Operations

    The Tile class wraps image data (PIL or QImage) and provides operations
    for manipulating tiles including cropping, resizing, saving, and rendering.
    """

    def test_init_with_pil_image(self):
        """
        Scenario: Create tile from PIL Image

        Given a PIL Image with dimensions 100x100
        When a Tile is created from the PIL Image
        Then the tile size should be (100, 100)
        """
        pil_image = Image.new('RGB', (100, 100))
        t = Tile(pil_image)
        assert t.size == (100, 100)

    def test_init_with_qimage(self):
        """
        Scenario: Create tile from QImage

        Given a QImage with dimensions 100x100
        When a Tile is created from the QImage
        Then the tile size should be (100, 100)
        """
        qimage = QtGui.QImage(100, 100, QtGui.QImage.Format_RGB32)
        t = Tile(qimage)
        assert t.size == (100, 100)

    def test_size_property(self):
        """
        Scenario: Query tile dimensions

        Given a tile created from a 200x150 QImage
        When the size property is accessed
        Then it should return (200, 150)
        """
        qimage = QtGui.QImage(200, 150, QtGui.QImage.Format_RGB32)
        t = Tile(qimage)
        assert t.size == (200, 150)

    def test_crop(self):
        """
        Scenario: Crop a tile to smaller region

        Given a tile with size 100x100
        When cropping to region (10, 10, 50, 50)
        Then a new Tile instance should be returned
        And the new tile size should be 40x40
        """
        qimage = QtGui.QImage(100, 100, QtGui.QImage.Format_RGB32)
        t = Tile(qimage)
        cropped = t.crop((10, 10, 50, 50))
        assert isinstance(cropped, Tile)
        assert cropped.size == (40, 40)

    def test_resize(self):
        """
        Scenario: Resize tile to larger dimensions

        Given a tile with size 100x100
        When resizing to 200x200
        Then a new Tile instance should be returned
        And the new tile size should be 200x200
        """
        qimage = QtGui.QImage(100, 100, QtGui.QImage.Format_RGB32)
        t = Tile(qimage)
        resized = t.resize(200, 200)
        assert isinstance(resized, Tile)
        assert resized.size == (200, 200)

    def test_resize_to_smaller_size(self):
        """
        Scenario: Resize tile to smaller dimensions

        Given a tile with size 100x100
        When resizing to 50x50
        Then the new tile size should be 50x50
        """
        qimage = QtGui.QImage(100, 100, QtGui.QImage.Format_RGB32)
        t = Tile(qimage)
        resized = t.resize(50, 50)
        assert resized.size == (50, 50)

    @patch('pyzui.tilesystem.tile.QtGui.QImage.save')
    def test_save(self, mock_save):
        """
        Scenario: Save tile to disk

        Given a tile instance
        When save is called with a file path
        Then QImage.save should be called with that path
        """
        qimage = QtGui.QImage(100, 100, QtGui.QImage.Format_RGB32)
        t = Tile(qimage)
        t.save("test.png")
        mock_save.assert_called_once_with("test.png")

    def test_draw(self):
        """
        Scenario: Draw tile using painter

        Given a tile instance
        And a QPainter object
        When draw is called with coordinates (10, 20)
        Then painter.drawImage should be called once
        """
        qimage = QtGui.QImage(100, 100, QtGui.QImage.Format_RGB32)
        t = Tile(qimage)
        painter = Mock()
        t.draw(painter, 10, 20)
        painter.drawImage.assert_called_once()


class TestTileFunctions:
    """
    Feature: Tile Factory Functions

    The tile module provides factory functions for creating and composing tiles
    from various sources including raw pixel data and merging multiple tiles.
    """

    def test_new(self):
        """
        Scenario: Create new blank tile

        Given dimensions 100x100
        When tile.new is called
        Then a new Tile instance should be returned
        And the tile size should be (100, 100)
        """
        t = tile.new(100, 100)
        assert isinstance(t, Tile)
        assert t.size == (100, 100)

    def test_new_different_dimensions(self):
        """
        Scenario: Create new blank tile with different dimensions

        Given dimensions 200x150
        When tile.new is called
        Then the tile size should be (200, 150)
        """
        t = tile.new(200, 150)
        assert t.size == (200, 150)

    def test_fromstring(self):
        """
        Scenario: Create tile from raw pixel data

        Given raw pixel string for a 2x2 image
        When tile.fromstring is called with the data
        Then a new Tile instance should be returned
        And the tile size should be (2, 2)
        """
        width, height = 2, 2
        raw_pixels = '\xFF\x00\x00\xFF\x00\x00\x00\xFF\x00\x00\xFF\x00'
        t = tile.fromstring(raw_pixels, width, height)
        assert isinstance(t, Tile)
        assert t.size == (width, height)

    def test_merged_all_tiles(self):
        """
        Scenario: Merge four tiles into one

        Given four 10x10 tiles (t1, t2, t3, t4)
        When tile.merged is called with all four tiles
        Then a new merged Tile should be returned
        And the merged tile size should be 20x20
        """
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
        """
        Scenario: Merge tiles with some missing

        Given two 10x10 tiles (t1, t2) and two None values
        When tile.merged is called
        Then a merged Tile should be returned
        And the merged tile size should be 20x10
        """
        qimage1 = QtGui.QImage(10, 10, QtGui.QImage.Format_RGB32)
        qimage2 = QtGui.QImage(10, 10, QtGui.QImage.Format_RGB32)

        t1 = Tile(qimage1)
        t2 = Tile(qimage2)

        merged = tile.merged(t1, t2, None, None)
        assert isinstance(merged, Tile)
        assert merged.size == (20, 10)

    def test_merged_only_t1(self):
        """
        Scenario: Merge with only first tile present

        Given one 10x10 tile and three None values
        When tile.merged is called
        Then a Tile should be returned
        And the tile size should be 10x10
        """
        qimage1 = QtGui.QImage(10, 10, QtGui.QImage.Format_RGB32)
        t1 = Tile(qimage1)

        merged = tile.merged(t1, None, None, None)
        assert isinstance(merged, Tile)
        assert merged.size == (10, 10)
