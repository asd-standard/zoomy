import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
from pyzui.statictileprovider import StaticTileProvider

class TestStaticTileProvider:
    """Test suite for the StaticTileProvider class."""

    def test_init(self):
        """Test StaticTileProvider initialization."""
        tilecache = Mock()
        provider = StaticTileProvider(tilecache)
        assert provider is not None

    def test_inherits_from_tileprovider(self):
        """Test that StaticTileProvider inherits from TileProvider."""
        from pyzui.tileprovider import TileProvider
        tilecache = Mock()
        provider = StaticTileProvider(tilecache)
        assert isinstance(provider, TileProvider)

    @patch('pyzui.statictileprovider.TileStore.get_metadata')
    @patch('pyzui.statictileprovider.TileStore.get_tile_path')
    @patch('pyzui.statictileprovider.Image.open')
    def test_load_success(self, mock_open, mock_path, mock_metadata):
        """Test _load method successfully loads a tile."""
        tilecache = Mock()
        provider = StaticTileProvider(tilecache)

        mock_metadata.return_value = 5
        mock_path.return_value = '/path/to/tile.jpg'
        mock_image = Mock(spec=Image.Image)
        mock_open.return_value = mock_image

        tile_id = ('media_id', 2, 0, 0)
        result = provider._load(tile_id)

        assert result == mock_image
        mock_image.load.assert_called_once()

    @patch('pyzui.statictileprovider.TileStore.get_metadata')
    def test_load_exceeds_maxtilelevel(self, mock_metadata):
        """Test _load returns None when tilelevel exceeds maxtilelevel."""
        tilecache = Mock()
        provider = StaticTileProvider(tilecache)

        mock_metadata.return_value = 3
        tile_id = ('media_id', 5, 0, 0)
        result = provider._load(tile_id)

        assert result is None

    @patch('pyzui.statictileprovider.TileStore.get_metadata')
    @patch('pyzui.statictileprovider.TileStore.get_tile_path')
    @patch('pyzui.statictileprovider.Image.open')
    def test_load_ioerror(self, mock_open, mock_path, mock_metadata):
        """Test _load returns None on IOError."""
        tilecache = Mock()
        provider = StaticTileProvider(tilecache)

        mock_metadata.return_value = 5
        mock_path.return_value = '/path/to/tile.jpg'
        mock_open.side_effect = IOError("File not found")

        tile_id = ('media_id', 2, 0, 0)
        result = provider._load(tile_id)

        assert result is None

    @patch('pyzui.statictileprovider.TileStore.get_metadata')
    @patch('pyzui.statictileprovider.TileStore.get_tile_path')
    @patch('pyzui.statictileprovider.Image.open')
    def test_load_valid_tilelevel(self, mock_open, mock_path, mock_metadata):
        """Test _load with valid tilelevel at boundary."""
        tilecache = Mock()
        provider = StaticTileProvider(tilecache)

        mock_metadata.return_value = 5
        mock_path.return_value = '/path/to/tile.jpg'
        mock_image = Mock(spec=Image.Image)
        mock_open.return_value = mock_image

        tile_id = ('media_id', 5, 0, 0)
        result = provider._load(tile_id)

        assert result == mock_image

    @patch('pyzui.statictileprovider.TileStore.get_metadata')
    @patch('pyzui.statictileprovider.TileStore.get_tile_path')
    @patch('pyzui.statictileprovider.Image.open')
    def test_load_calls_correct_methods(self, mock_open, mock_path, mock_metadata):
        """Test _load calls TileStore methods with correct parameters."""
        tilecache = Mock()
        provider = StaticTileProvider(tilecache)

        mock_metadata.return_value = 5
        mock_path.return_value = '/path/to/tile.jpg'
        mock_image = Mock(spec=Image.Image)
        mock_open.return_value = mock_image

        tile_id = ('media_id', 2, 3, 4)
        provider._load(tile_id)

        mock_metadata.assert_called_once_with('media_id', 'maxtilelevel')
        mock_path.assert_called_once_with(tile_id)
        mock_open.assert_called_once_with('/path/to/tile.jpg')
