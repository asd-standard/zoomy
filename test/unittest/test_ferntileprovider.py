import pytest
from unittest.mock import Mock, patch
from pyzui.tileproviders import FernTileProvider

class TestFernTileProvider:
    """Test suite for the FernTileProvider class."""

    def test_init(self):
        """Test FernTileProvider initialization."""
        tilecache = Mock()
        provider = FernTileProvider(tilecache)
        assert provider is not None

    def test_inherits_from_dynamictileprovider(self):
        """Test that FernTileProvider inherits from DynamicTileProvider."""
        from pyzui.tileproviders import DynamicTileProvider
        tilecache = Mock()
        provider = FernTileProvider(tilecache)
        assert isinstance(provider, DynamicTileProvider)

    def test_filext_attribute(self):
        """Test filext class attribute."""
        assert FernTileProvider.filext == 'png'

    def test_tilesize_attribute(self):
        """Test tilesize class attribute."""
        assert FernTileProvider.tilesize == 256

    def test_aspect_ratio_attribute(self):
        """Test aspect_ratio class attribute."""
        assert FernTileProvider.aspect_ratio == 1.0

    def test_max_iterations_attribute(self):
        """Test max_iterations attribute."""
        tilecache = Mock()
        provider = FernTileProvider(tilecache)
        assert provider.max_iterations == 50000

    def test_max_points_attribute(self):
        """Test max_points attribute."""
        tilecache = Mock()
        provider = FernTileProvider(tilecache)
        assert provider.max_points == 10000

    def test_transformations_attribute(self):
        """Test transformations attribute exists and has 4 items."""
        tilecache = Mock()
        provider = FernTileProvider(tilecache)
        assert len(provider.transformations) == 4

    def test_color_attribute(self):
        """Test color attribute."""
        tilecache = Mock()
        provider = FernTileProvider(tilecache)
        assert provider.color == (100, 170, 0)

    def test_load_dynamic_negative_row(self):
        """Test _load_dynamic returns None for negative row."""
        tilecache = Mock()
        provider = FernTileProvider(tilecache)
        tile_id = ('fern', 2, -1, 1)
        outfile = '/path/to/tile.png'
        result = provider._load_dynamic(tile_id, outfile)
        assert result is None

    def test_load_dynamic_negative_col(self):
        """Test _load_dynamic returns None for negative col."""
        tilecache = Mock()
        provider = FernTileProvider(tilecache)
        tile_id = ('fern', 2, 1, -1)
        outfile = '/path/to/tile.png'
        result = provider._load_dynamic(tile_id, outfile)
        assert result is None

    def test_load_dynamic_out_of_range(self):
        """Test _load_dynamic returns None for out of range coordinates."""
        tilecache = Mock()
        provider = FernTileProvider(tilecache)
        tile_id = ('fern', 2, 10, 10)
        outfile = '/path/to/tile.png'
        result = provider._load_dynamic(tile_id, outfile)
        assert result is None

    @patch('pyzui.tileproviders.ferntileprovider.Image.new')
    def test_load_dynamic_valid_tile(self, mock_image_new):
        """Test _load_dynamic generates valid tile."""
        tilecache = Mock()
        provider = FernTileProvider(tilecache)

        mock_image = Mock()
        mock_image_new.return_value = mock_image

        tile_id = ('fern', 2, 1, 1)
        outfile = '/path/to/tile.png'

        provider._load_dynamic(tile_id, outfile)

        mock_image.save.assert_called_once_with(outfile)
        mock_image_new.assert_called_once_with('RGB', (256, 256))
