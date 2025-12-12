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
from unittest.mock import Mock, patch
from PySide6 import QtGui
from pyzui.tilesystem.tileproviders import DynamicTileProvider

class TestDynamicTileProvider:
    """
    Feature: DynamicTileProvider Base Class

    This class tests the base DynamicTileProvider functionality including initialization,
    inheritance verification, attribute validation, and dynamic tile loading behavior.
    """

    def test_init(self):
        """
        Scenario: Initialize DynamicTileProvider with tilecache

        Given a mock tilecache
        When DynamicTileProvider is instantiated
        Then the provider object is created successfully
        """
        tilecache = Mock()
        provider = DynamicTileProvider(tilecache)
        assert provider is not None

    def test_inherits_from_tileprovider(self):
        """
        Scenario: Verify DynamicTileProvider inheritance

        Given a DynamicTileProvider instance
        When checking its type
        Then it should be an instance of TileProvider
        """
        from pyzui.tilesystem.tileproviders import TileProvider
        tilecache = Mock()
        provider = DynamicTileProvider(tilecache)
        assert isinstance(provider, TileProvider)

    def test_filext_attribute(self):
        """
        Scenario: Check default file extension

        Given the DynamicTileProvider class
        When accessing the filext attribute
        Then it should be 'png'
        """
        assert DynamicTileProvider.filext == 'png'

    def test_tilesize_attribute(self):
        """
        Scenario: Check default tile size

        Given the DynamicTileProvider class
        When accessing the tilesize attribute
        Then it should be 256
        """
        assert DynamicTileProvider.tilesize == 256

    def test_aspect_ratio_attribute(self):
        """
        Scenario: Check default aspect ratio

        Given the DynamicTileProvider class
        When accessing the aspect_ratio attribute
        Then it should be 1.0
        """
        assert DynamicTileProvider.aspect_ratio == 1.0

    def test_load_dynamic_abstract_method(self):
        """
        Scenario: Call abstract _load_dynamic method

        Given a DynamicTileProvider instance
        When calling _load_dynamic without overriding it
        Then it should return None
        """
        tilecache = Mock()
        provider = DynamicTileProvider(tilecache)
        tile_id = ('media_id', 0, 0, 0)
        result = provider._load_dynamic(tile_id, '/path/to/file')
        assert result is None

    @patch('pyzui.tilesystem.tileproviders.dynamictileprovider.TileStore.get_tile_path')
    @patch('os.path.exists')
    @patch('pyzui.tilesystem.tileproviders.dynamictileprovider.QtGui.QImage')
    def test_load_existing_tile(self, mock_qimage_class, mock_exists, mock_path):
        """
        Scenario: Load an existing tile from disk

        Given a DynamicTileProvider and a tile that exists on disk
        When calling _load with the tile ID
        Then the tile image should be loaded from the file path
        And the QImage object should be returned
        """
        tilecache = Mock()
        provider = DynamicTileProvider(tilecache)

        mock_path.return_value = '/path/to/tile.png'
        mock_exists.return_value = True
        mock_image = Mock()
        mock_image.load = Mock()
        mock_qimage_class.return_value = mock_image

        tile_id = ('media_id', 0, 0, 0)
        result = provider._load(tile_id)

        assert result == mock_image
        mock_qimage_class.assert_called_once_with('/path/to/tile.png')

    @patch('pyzui.tilesystem.tileproviders.dynamictileprovider.TileStore.get_tile_path')
    @patch('os.path.exists')
    @patch.object(DynamicTileProvider, '_load_dynamic')
    @patch('pyzui.tilesystem.tileproviders.dynamictileprovider.QtGui.QImage')
    def test_load_nonexistent_tile(self, mock_qimage_class, mock_load_dynamic, mock_exists, mock_path):
        """
        Scenario: Load a tile that doesn't exist on disk

        Given a DynamicTileProvider and a tile that doesn't exist on disk
        When calling _load with the tile ID
        Then _load_dynamic should be called to generate the tile
        """
        tilecache = Mock()
        provider = DynamicTileProvider(tilecache)

        mock_path.return_value = '/path/to/tile.png'
        mock_exists.return_value = False
        mock_image = Mock()
        mock_image.load = Mock()
        mock_qimage_class.return_value = mock_image

        tile_id = ('media_id', 0, 0, 0)
        result = provider._load(tile_id)

        mock_load_dynamic.assert_called_once_with(tile_id, '/path/to/tile.png')

    @patch('pyzui.tilesystem.tileproviders.dynamictileprovider.TileStore.get_tile_path')
    @patch('os.path.exists')
    @patch('pyzui.tilesystem.tileproviders.dynamictileprovider.QtGui.QImage', side_effect=Exception("Load error"))
    def test_load_handles_exception(self, mock_qimage, mock_exists, mock_path):
        """
        Scenario: Handle exceptions during tile loading

        Given a DynamicTileProvider and an error occurs during loading
        When calling _load with a tile ID
        Then the exception should be caught
        And None should be returned
        """
        tilecache = Mock()
        provider = DynamicTileProvider(tilecache)

        mock_path.return_value = '/path/to/tile.png'
        mock_exists.return_value = True

        tile_id = ('media_id', 0, 0, 0)
        result = provider._load(tile_id)

        assert result is None

    @patch('pyzui.tilesystem.tileproviders.dynamictileprovider.TileStore.get_tile_path')
    def test_load_creates_path_with_mkdirp(self, mock_path):
        """
        Scenario: Create directory structure during tile loading

        Given a DynamicTileProvider
        When calling _load to generate a tile
        Then get_tile_path should be called with mkdirp=True
        And the directory structure should be created automatically
        """
        tilecache = Mock()
        provider = DynamicTileProvider(tilecache)

        mock_path.return_value = '/path/to/tile.png'

        tile_id = ('media_id', 0, 0, 0)

        with patch('os.path.exists', return_value=True):
            with patch('pyzui.tilesystem.tileproviders.dynamictileprovider.QtGui.QImage'):
                provider._load(tile_id)

        mock_path.assert_called_once_with(tile_id, True, filext='png')
