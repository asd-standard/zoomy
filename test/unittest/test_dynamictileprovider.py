import pytest
from unittest.mock import Mock, patch
from PySide6 import QtGui
from pyzui.dynamictileprovider import DynamicTileProvider

class TestDynamicTileProvider:
    """Test suite for the DynamicTileProvider class."""

    def test_init(self):
        """Test DynamicTileProvider initialization."""
        tilecache = Mock()
        provider = DynamicTileProvider(tilecache)
        assert provider is not None

    def test_inherits_from_tileprovider(self):
        """Test that DynamicTileProvider inherits from TileProvider."""
        from pyzui.tileprovider import TileProvider
        tilecache = Mock()
        provider = DynamicTileProvider(tilecache)
        assert isinstance(provider, TileProvider)

    def test_filext_attribute(self):
        """Test filext class attribute."""
        assert DynamicTileProvider.filext == 'png'

    def test_tilesize_attribute(self):
        """Test tilesize class attribute."""
        assert DynamicTileProvider.tilesize == 256

    def test_aspect_ratio_attribute(self):
        """Test aspect_ratio class attribute."""
        assert DynamicTileProvider.aspect_ratio == 1.0

    def test_load_dynamic_abstract_method(self):
        """Test _load_dynamic is abstract and returns None."""
        tilecache = Mock()
        provider = DynamicTileProvider(tilecache)
        tile_id = ('media_id', 0, 0, 0)
        result = provider._load_dynamic(tile_id, '/path/to/file')
        assert result is None

    @patch('pyzui.dynamictileprovider.TileStore.get_tile_path')
    @patch('os.path.exists')
    @patch('pyzui.dynamictileprovider.QtGui.QImage')
    def test_load_existing_tile(self, mock_qimage_class, mock_exists, mock_path):
        """Test _load method with existing tile."""
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

    @patch('pyzui.dynamictileprovider.TileStore.get_tile_path')
    @patch('os.path.exists')
    @patch.object(DynamicTileProvider, '_load_dynamic')
    @patch('pyzui.dynamictileprovider.QtGui.QImage')
    def test_load_nonexistent_tile(self, mock_qimage_class, mock_load_dynamic, mock_exists, mock_path):
        """Test _load method calls _load_dynamic for nonexistent tile."""
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

    @patch('pyzui.dynamictileprovider.TileStore.get_tile_path')
    @patch('os.path.exists')
    @patch('pyzui.dynamictileprovider.QtGui.QImage', side_effect=Exception("Load error"))
    def test_load_handles_exception(self, mock_qimage, mock_exists, mock_path):
        """Test _load method handles exceptions gracefully."""
        tilecache = Mock()
        provider = DynamicTileProvider(tilecache)

        mock_path.return_value = '/path/to/tile.png'
        mock_exists.return_value = True

        tile_id = ('media_id', 0, 0, 0)
        result = provider._load(tile_id)

        assert result is None

    @patch('pyzui.dynamictileprovider.TileStore.get_tile_path')
    def test_load_creates_path_with_mkdirp(self, mock_path):
        """Test _load method calls get_tile_path with mkdirp=True."""
        tilecache = Mock()
        provider = DynamicTileProvider(tilecache)

        mock_path.return_value = '/path/to/tile.png'

        tile_id = ('media_id', 0, 0, 0)

        with patch('os.path.exists', return_value=True):
            with patch('pyzui.dynamictileprovider.QtGui.QImage'):
                provider._load(tile_id)

        mock_path.assert_called_once_with(tile_id, True, filext='png')
