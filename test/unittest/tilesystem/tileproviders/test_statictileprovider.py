import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
from pyzui.tilesystem.tileproviders import StaticTileProvider

class TestStaticTileProvider:
    """
    Feature: Static Tile Provider

    This test suite validates the StaticTileProvider class which loads pre-generated tiles
    from the tile store on disk for media that has been previously tiled.
    """

    def test_init(self):
        """
        Scenario: Initialize a static tile provider

        Given a mock tile cache
        When a StaticTileProvider is instantiated
        Then it should be successfully created
        """
        tilecache = Mock()
        provider = StaticTileProvider(tilecache)
        assert provider is not None

    def test_inherits_from_tileprovider(self):
        """
        Scenario: Verify inheritance from TileProvider

        Given a mock tile cache
        When a StaticTileProvider is instantiated
        Then it should be an instance of TileProvider
        """
        from pyzui.tilesystem.tileproviders import TileProvider
        tilecache = Mock()
        provider = StaticTileProvider(tilecache)
        assert isinstance(provider, TileProvider)

    @patch('pyzui.tilesystem.tileproviders.statictileprovider.TileStore.get_metadata')
    @patch('pyzui.tilesystem.tileproviders.statictileprovider.TileStore.get_tile_path')
    @patch('pyzui.tilesystem.tileproviders.statictileprovider.Image.open')
    def test_load_success(self, mock_open, mock_path, mock_metadata):
        """
        Scenario: Successfully load a tile from disk

        Given a StaticTileProvider with mocked tile store
        When _load is called with a valid tile_id
        Then the tile image should be loaded from disk
        And the image's load method should be called
        """
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

    @patch('pyzui.tilesystem.tileproviders.statictileprovider.TileStore.get_metadata')
    def test_load_exceeds_maxtilelevel(self, mock_metadata):
        """
        Scenario: Request tile beyond maximum level

        Given a StaticTileProvider with maxtilelevel of 3
        When _load is called with a tile_id at level 5
        Then it should return None as the tile is unavailable
        """
        tilecache = Mock()
        provider = StaticTileProvider(tilecache)

        mock_metadata.return_value = 3
        tile_id = ('media_id', 5, 0, 0)
        result = provider._load(tile_id)

        assert result is None

    @patch('pyzui.tilesystem.tileproviders.statictileprovider.TileStore.get_metadata')
    @patch('pyzui.tilesystem.tileproviders.statictileprovider.TileStore.get_tile_path')
    @patch('pyzui.tilesystem.tileproviders.statictileprovider.Image.open')
    def test_load_ioerror(self, mock_open, mock_path, mock_metadata):
        """
        Scenario: Handle missing tile file

        Given a StaticTileProvider with mocked tile store
        When _load is called and the tile file is not found
        Then it should catch the IOError and return None
        """
        tilecache = Mock()
        provider = StaticTileProvider(tilecache)

        mock_metadata.return_value = 5
        mock_path.return_value = '/path/to/tile.jpg'
        mock_open.side_effect = IOError("File not found")

        tile_id = ('media_id', 2, 0, 0)
        result = provider._load(tile_id)

        assert result is None

    @patch('pyzui.tilesystem.tileproviders.statictileprovider.TileStore.get_metadata')
    @patch('pyzui.tilesystem.tileproviders.statictileprovider.TileStore.get_tile_path')
    @patch('pyzui.tilesystem.tileproviders.statictileprovider.Image.open')
    def test_load_valid_tilelevel(self, mock_open, mock_path, mock_metadata):
        """
        Scenario: Load tile at maximum level boundary

        Given a StaticTileProvider with maxtilelevel of 5
        When _load is called with a tile_id at exactly level 5
        Then the tile should be successfully loaded
        """
        tilecache = Mock()
        provider = StaticTileProvider(tilecache)

        mock_metadata.return_value = 5
        mock_path.return_value = '/path/to/tile.jpg'
        mock_image = Mock(spec=Image.Image)
        mock_open.return_value = mock_image

        tile_id = ('media_id', 5, 0, 0)
        result = provider._load(tile_id)

        assert result == mock_image

    @patch('pyzui.tilesystem.tileproviders.statictileprovider.TileStore.get_metadata')
    @patch('pyzui.tilesystem.tileproviders.statictileprovider.TileStore.get_tile_path')
    @patch('pyzui.tilesystem.tileproviders.statictileprovider.Image.open')
    def test_load_calls_correct_methods(self, mock_open, mock_path, mock_metadata):
        """
        Scenario: Verify tile store interaction

        Given a StaticTileProvider with mocked tile store
        When _load is called with a specific tile_id
        Then it should call get_metadata to retrieve maxtilelevel
        And it should call get_tile_path with the tile_id
        And it should open the image file at the retrieved path
        """
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
