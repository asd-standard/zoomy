import pytest
from unittest.mock import Mock, patch
from pyzui.tileproviders import OSMTileProvider

class TestOSMTileProvider:
    """Test suite for the OSMTileProvider class."""

    def test_init(self):
        """Test OSMTileProvider initialization."""
        tilecache = Mock()
        provider = OSMTileProvider(tilecache)
        assert provider is not None

    def test_inherits_from_dynamictileprovider(self):
        """Test that OSMTileProvider inherits from DynamicTileProvider."""
        from pyzui.tileproviders import DynamicTileProvider
        tilecache = Mock()
        provider = OSMTileProvider(tilecache)
        assert isinstance(provider, DynamicTileProvider)

    def test_filext_attribute(self):
        """Test filext class attribute."""
        assert OSMTileProvider.filext == 'png'

    def test_tilesize_attribute(self):
        """Test tilesize class attribute."""
        assert OSMTileProvider.tilesize == 256

    def test_aspect_ratio_attribute(self):
        """Test aspect_ratio class attribute."""
        assert OSMTileProvider.aspect_ratio == 1.0

    @patch('urllib.request.urlretrieve')
    def test_load_dynamic_success(self, mock_retrieve):
        """Test _load_dynamic method successfully downloads tile."""
        tilecache = Mock()
        provider = OSMTileProvider(tilecache)

        tile_id = ('osm', 2, 1, 1)
        outfile = '/path/to/tile.png'

        provider._load_dynamic(tile_id, outfile)
        mock_retrieve.assert_called_once()

    @patch('urllib.request.urlretrieve')
    def test_load_dynamic_correct_url(self, mock_retrieve):
        """Test _load_dynamic constructs correct URL."""
        tilecache = Mock()
        provider = OSMTileProvider(tilecache)

        tile_id = ('osm', 3, 2, 1)
        outfile = '/path/to/tile.png'

        provider._load_dynamic(tile_id, outfile)

        expected_url = "http://tile.openstreetmap.org/3/1/2.png"
        mock_retrieve.assert_called_once_with(expected_url, outfile)

    def test_load_dynamic_negative_row(self):
        """Test _load_dynamic returns None for negative row."""
        tilecache = Mock()
        provider = OSMTileProvider(tilecache)

        tile_id = ('osm', 2, -1, 1)
        outfile = '/path/to/tile.png'

        result = provider._load_dynamic(tile_id, outfile)
        assert result is None

    def test_load_dynamic_negative_col(self):
        """Test _load_dynamic returns None for negative col."""
        tilecache = Mock()
        provider = OSMTileProvider(tilecache)

        tile_id = ('osm', 2, 1, -1)
        outfile = '/path/to/tile.png'

        result = provider._load_dynamic(tile_id, outfile)
        assert result is None

    def test_load_dynamic_out_of_range(self):
        """Test _load_dynamic returns None for out of range coordinates."""
        tilecache = Mock()
        provider = OSMTileProvider(tilecache)

        tile_id = ('osm', 2, 10, 10)  # 2**2 = 4, so max is 3
        outfile = '/path/to/tile.png'

        result = provider._load_dynamic(tile_id, outfile)
        assert result is None

    @patch('urllib.request.urlretrieve', side_effect=IOError("Network error"))
    def test_load_dynamic_ioerror(self, mock_retrieve):
        """Test _load_dynamic handles IOError gracefully."""
        tilecache = Mock()
        provider = OSMTileProvider(tilecache)

        tile_id = ('osm', 2, 1, 1)
        outfile = '/path/to/tile.png'

        # Should not raise exception
        provider._load_dynamic(tile_id, outfile)
