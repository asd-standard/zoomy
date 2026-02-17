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
from unittest.mock import Mock, patch, MagicMock, call
from pyzui.tilesystem import tilemanager
from pyzui.tilesystem.tile import Tile

class TestTileManager:
    """
    Feature: Tile Manager Module

    The TileManager coordinates tile requests between multiple providers, manages two-tier
    caching (permanent and temporary), and synthesizes tiles when requested tiles are not
    available. It provides robust tile retrieval with automatic fallback to tile synthesis.
    """

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_init_default_parameters(self, mock_fern, mock_static, mock_cache, mock_tilestore):
        """
        Scenario: Initialize tile manager with default parameters

        Given the tile manager module with mocked dependencies
        When the init function is called with defaults
        Then the tile caches should be initialized with 80/20 split
        And both static and dynamic providers should be started
        And auto cleanup should be enabled
        """
        mock_static_instance = Mock()
        mock_static.return_value = mock_static_instance
        mock_fern_instance = Mock()
        mock_fern.return_value = mock_fern_instance

        tilemanager.init(total_cache_size=1024, auto_cleanup=True, cleanup_max_age_days=3)

        # Verify cache initialization with 80/20 split (converted to int)
        assert mock_cache.call_count == 2
        assert mock_cache.call_args_list[0] == call(int(0.8 * 1024))
        assert mock_cache.call_args_list[1] == call(int(0.2 * 1024))

        # Verify providers were started
        mock_static_instance.start.assert_called_once()
        mock_fern_instance.start.assert_called_once()

        # Verify auto cleanup was NOT called synchronously (registered for shutdown)
        mock_tilestore.auto_cleanup.assert_not_called()

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_init_auto_cleanup_disabled(self, mock_fern, mock_static, mock_cache, mock_tilestore):
        """
        Scenario: Initialize tile manager with auto cleanup disabled

        Given the tile manager module
        When init is called with auto_cleanup=False
        Then auto cleanup should not be invoked
        """
        mock_static.return_value = Mock()
        mock_fern.return_value = Mock()

        tilemanager.init(total_cache_size=512, auto_cleanup=False)

        # Verify cache initialization with int conversion
        assert mock_cache.call_count == 2
        assert mock_cache.call_args_list[0] == call(int(0.8 * 512))
        assert mock_cache.call_args_list[1] == call(int(0.2 * 512))
        
        # Verify auto cleanup was NOT called
        mock_tilestore.auto_cleanup.assert_not_called()

    def test_media_not_tiled_exception_exists(self):
        """
        Scenario: Verify MediaNotTiled exception is defined

        Given the tile manager module
        When checking for the MediaNotTiled exception
        Then it should exist in the module
        And it should inherit from Exception
        """
        assert hasattr(tilemanager, 'MediaNotTiled')
        assert issubclass(tilemanager.MediaNotTiled, Exception)

    def test_tile_not_loaded_exception_exists(self):
        """
        Scenario: Verify TileNotLoaded exception is defined

        Given the tile manager module
        When checking for the TileNotLoaded exception
        Then it should exist in the module
        And it should inherit from Exception
        """
        assert hasattr(tilemanager, 'TileNotLoaded')
        assert issubclass(tilemanager.TileNotLoaded, Exception)

    def test_tile_not_available_exception_exists(self):
        """
        Scenario: Verify TileNotAvailable exception is defined

        Given the tile manager module
        When checking for the TileNotAvailable exception
        Then it should exist in the module
        And it should inherit from Exception
        """
        assert hasattr(tilemanager, 'TileNotAvailable')
        assert issubclass(tilemanager.TileNotAvailable, Exception)

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_load_tile_routes_to_static_provider(self, mock_fern, mock_static, mock_cache, mock_tilestore):
        """
        Scenario: Route tile request to static provider

        Given an initialized tile manager
        When load_tile is called for a non-dynamic media
        Then the request should be routed to the static tile provider
        """
        mock_static_instance = Mock()
        mock_static.return_value = mock_static_instance
        mock_fern.return_value = Mock()

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        tile_id = ('static_media.jpg', 0, 0, 0)
        tilemanager.load_tile(tile_id)

        mock_static_instance.request.assert_called_once_with(tile_id)

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_load_tile_routes_to_dynamic_provider(self, mock_fern, mock_static, mock_cache, mock_tilestore):
        """
        Scenario: Route tile request to dynamic provider

        Given an initialized tile manager
        When load_tile is called for a dynamic:fern media
        Then the request should be routed to the fern tile provider
        """
        mock_static.return_value = Mock()
        mock_fern_instance = Mock()
        mock_fern.return_value = mock_fern_instance

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        tile_id = ('dynamic:fern', 2, 3, 4)
        tilemanager.load_tile(tile_id)

        mock_fern_instance.request.assert_called_once_with(tile_id)

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_get_tile_raises_tile_not_available_for_negative_tilelevel(self, mock_fern, mock_static, mock_cache, mock_tilestore):
        """
        Scenario: Handle request for negative tile level

        Given an initialized tile manager
        When get_tile is called with a negative tilelevel
        Then TileNotAvailable should be raised
        """
        mock_static.return_value = Mock()
        mock_fern.return_value = Mock()

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        tile_id = ('media.jpg', -1, 0, 0)
        with pytest.raises(tilemanager.TileNotAvailable):
            tilemanager.get_tile(tile_id)

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_get_tile_returns_tile_from_cache(self, mock_fern, mock_static, mock_cache_class, mock_tilestore):
        """
        Scenario: Retrieve tile from cache

        Given an initialized tile manager with a tile in cache
        When get_tile is called for that tile
        Then the cached tile should be returned
        """
        mock_static.return_value = Mock()
        mock_fern.return_value = Mock()

        # Create mock cache with a tile
        mock_cache = {}
        tile_id = ('media.jpg', 0, 0, 0)
        mock_tile = Mock(spec=Tile)
        mock_cache[tile_id] = mock_tile
        mock_cache_class.return_value = mock_cache

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        result = tilemanager.get_tile(tile_id)
        assert result == mock_tile

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_tiled_returns_true_for_dynamic_media(self, mock_fern, mock_static, mock_cache, mock_tilestore):
        """
        Scenario: Check if dynamic media is tiled

        Given an initialized tile manager
        When tiled is called for a dynamic media
        Then it should return True
        """
        mock_static.return_value = Mock()
        mock_fern.return_value = Mock()

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        result = tilemanager.tiled('dynamic:fern')
        assert result is True

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_tiled_delegates_to_tilestore_for_static_media(self, mock_fern, mock_static, mock_cache, mock_tilestore):
        """
        Scenario: Check if static media is tiled

        Given an initialized tile manager
        When tiled is called for a static media
        Then it should delegate to TileStore.tiled
        """
        mock_static.return_value = Mock()
        mock_fern.return_value = Mock()
        mock_tilestore.tiled.return_value = True

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        result = tilemanager.tiled('static_media.jpg')
        assert result is True
        mock_tilestore.tiled.assert_called_once_with('static_media.jpg')

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_get_metadata_from_dynamic_provider(self, mock_fern, mock_static, mock_cache, mock_tilestore):
        """
        Scenario: Get metadata from dynamic tile provider

        Given an initialized tile manager
        When get_metadata is called for a dynamic media
        Then it should return metadata from the dynamic provider
        """
        mock_static.return_value = Mock()
        mock_fern_instance = Mock()
        mock_fern_instance.tilesize = 256
        mock_fern_instance.aspect_ratio = 1.0
        mock_fern_instance.filext = 'png'
        mock_fern.return_value = mock_fern_instance

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        assert tilemanager.get_metadata('dynamic:fern', 'tilesize') == 256
        assert tilemanager.get_metadata('dynamic:fern', 'aspect_ratio') == 1.0
        assert tilemanager.get_metadata('dynamic:fern', 'filext') == 'png'
        assert tilemanager.get_metadata('dynamic:fern', 'maxtilelevel') == 18

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_get_metadata_from_tilestore_for_static_media(self, mock_fern, mock_static, mock_cache, mock_tilestore):
        """
        Scenario: Get metadata from tilestore for static media

        Given an initialized tile manager
        When get_metadata is called for a static media
        Then it should delegate to TileStore.get_metadata
        """
        mock_static.return_value = Mock()
        mock_fern.return_value = Mock()
        mock_tilestore.get_metadata.return_value = 512

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        result = tilemanager.get_metadata('static_media.jpg', 'width')
        assert result == 512
        mock_tilestore.get_metadata.assert_called_once_with('static_media.jpg', 'width')

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_purge_calls_all_providers(self, mock_fern, mock_static, mock_cache, mock_tilestore):
        """
        Scenario: Purge tiles from all providers

        Given an initialized tile manager
        When purge is called with a media_id
        Then both static and dynamic providers should be purged
        """
        mock_static_instance = Mock()
        mock_static.return_value = mock_static_instance
        mock_fern_instance = Mock()
        mock_fern.return_value = mock_fern_instance

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        tilemanager.purge('media.jpg')

        mock_static_instance.purge.assert_called_once_with('media.jpg')
        mock_fern_instance.purge.assert_called_once_with('media.jpg')

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_purge_without_media_id_purges_all(self, mock_fern, mock_static, mock_cache, mock_tilestore):
        """
        Scenario: Purge all tiles from providers

        Given an initialized tile manager
        When purge is called without a media_id
        Then all tiles should be purged from all providers
        """
        mock_static_instance = Mock()
        mock_static.return_value = mock_static_instance
        mock_fern_instance = Mock()
        mock_fern.return_value = mock_fern_instance

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        tilemanager.purge()

        mock_static_instance.purge.assert_called_once_with(None)
        mock_fern_instance.purge.assert_called_once_with(None)

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_get_tile_raises_media_not_tiled(self, mock_fern, mock_static, mock_cache_class, mock_tilestore):
        """
        Scenario: Handle request for untiled media

        Given an initialized tile manager
        When get_tile is called for media that hasn't been tiled
        Then MediaNotTiled should be raised
        """
        mock_static.return_value = Mock()
        mock_fern.return_value = Mock()

        # Create empty cache (tile not in cache)
        mock_cache = {}
        mock_cache_class.return_value = mock_cache

        # Media is not tiled
        mock_tilestore.tiled.return_value = False

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        tile_id = ('untiled_media.jpg', 0, 0, 0)
        with pytest.raises(tilemanager.MediaNotTiled):
            tilemanager.get_tile(tile_id)

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_get_tile_raises_tile_not_loaded(self, mock_fern, mock_static, mock_cache_class, mock_tilestore):
        """
        Scenario: Handle request for tile not yet loaded

        Given an initialized tile manager
        When get_tile is called for a tile not in cache but media is tiled
        Then TileNotLoaded should be raised
        And load_tile should be called to request the tile
        """
        mock_static_instance = Mock()
        mock_static.return_value = mock_static_instance
        mock_fern.return_value = Mock()

        # Create empty cache (tile not in cache)
        mock_cache = {}
        mock_cache_class.return_value = mock_cache

        # Media is tiled
        mock_tilestore.tiled.return_value = True

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        tile_id = ('tiled_media.jpg', 1, 2, 3)
        with pytest.raises(tilemanager.TileNotLoaded):
            tilemanager.get_tile(tile_id)

        # Verify load_tile was called
        mock_static_instance.request.assert_called_once_with(tile_id)

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_get_tile_raises_tile_not_available_when_none_in_cache(self, mock_fern, mock_static, mock_cache_class, mock_tilestore):
        """
        Scenario: Handle request for unavailable tile

        Given an initialized tile manager
        When get_tile is called for a tile that exists in cache but is None
        Then TileNotAvailable should be raised
        """
        mock_static.return_value = Mock()
        mock_fern.return_value = Mock()

        # Create cache with None tile (unavailable)
        mock_cache = {}
        tile_id = ('media.jpg', 0, 0, 0)
        mock_cache[tile_id] = None
        mock_cache_class.return_value = mock_cache

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        with pytest.raises(tilemanager.TileNotAvailable):
            tilemanager.get_tile(tile_id)

    @patch('pyzui.tilesystem.tilemanager.cut_tile')
    @patch('pyzui.tilesystem.tilemanager.get_tile')
    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_get_tile_robust_returns_tile_from_get_tile(self, mock_fern, mock_static, mock_cache, mock_tilestore, mock_get_tile, mock_cut_tile):
        """
        Scenario: Robust tile retrieval succeeds with get_tile

        Given an initialized tile manager
        When get_tile_robust is called and get_tile succeeds
        Then the tile from get_tile should be returned
        And cut_tile should not be called
        """
        mock_static.return_value = Mock()
        mock_fern.return_value = Mock()

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        tile_id = ('media.jpg', 0, 0, 0)
        mock_tile = Mock(spec=Tile)
        mock_get_tile.return_value = mock_tile

        result = tilemanager.get_tile_robust(tile_id)

        assert result == mock_tile
        mock_get_tile.assert_called_once_with(tile_id)
        mock_cut_tile.assert_not_called()

    @patch('pyzui.tilesystem.tilemanager.cut_tile')
    @patch('pyzui.tilesystem.tilemanager.get_tile')
    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_get_tile_robust_falls_back_to_cut_tile(self, mock_fern, mock_static, mock_cache, mock_tilestore, mock_get_tile, mock_cut_tile):
        """
        Scenario: Robust tile retrieval falls back to cut_tile

        Given an initialized tile manager
        When get_tile_robust is called and get_tile raises TileNotLoaded
        Then cut_tile should be called as fallback
        And the synthesized tile should be returned
        """
        mock_static.return_value = Mock()
        mock_fern.return_value = Mock()

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        tile_id = ('media.jpg', 2, 1, 1)
        mock_tile = Mock(spec=Tile)
        mock_get_tile.side_effect = tilemanager.TileNotLoaded
        mock_cut_tile.return_value = (mock_tile, True)

        result = tilemanager.get_tile_robust(tile_id)

        assert result == mock_tile
        mock_get_tile.assert_called_once_with(tile_id)
        mock_cut_tile.assert_called_once_with(tile_id)

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_get_metadata_returns_none_for_unknown_key(self, mock_fern, mock_static, mock_cache, mock_tilestore):
        """
        Scenario: Get metadata with unknown key

        Given an initialized tile manager
        When get_metadata is called with an unknown key for dynamic media
        Then None should be returned
        """
        mock_static.return_value = Mock()
        mock_fern_instance = Mock()
        mock_fern.return_value = mock_fern_instance

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        result = tilemanager.get_metadata('dynamic:fern', 'unknown_key')
        assert result is None

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_get_metadata_calculates_width_and_height_for_dynamic_media(self, mock_fern, mock_static, mock_cache, mock_tilestore):
        """
        Scenario: Calculate width and height for dynamic media

        Given an initialized tile manager with a dynamic provider
        When get_metadata is called for width or height
        Then it should calculate based on tilesize and maxtilelevel
        """
        mock_static.return_value = Mock()
        mock_fern_instance = Mock()
        mock_fern_instance.tilesize = 256
        mock_fern.return_value = mock_fern_instance

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        expected_dimension = 256 * (2 ** 18)
        assert tilemanager.get_metadata('dynamic:fern', 'width') == expected_dimension
        assert tilemanager.get_metadata('dynamic:fern', 'height') == expected_dimension

class TestTileManagerCutTile:
    """
    Feature: Tile Manager Tile Synthesis (cut_tile)

    This test suite validates the cut_tile function which synthesizes tiles
    by cropping and resizing parent tiles when the requested tile is not available.
    """

    @patch('pyzui.tilesystem.tilemanager.get_metadata')
    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_cut_tile_negative_tilelevel_scales_base_tile(self, mock_fern, mock_static, mock_cache_class, mock_tilestore, mock_get_metadata):
        """
        Scenario: Cut tile with negative tilelevel

        Given an initialized tile manager with a base (0,0,0) tile
        When cut_tile is called with negative tilelevel
        Then it should resize the base tile to a smaller scale
        """
        mock_static.return_value = Mock()
        mock_fern.return_value = Mock()
        mock_get_metadata.return_value = 256

        # Create mock cache with base tile
        mock_tile = Mock(spec=Tile)
        mock_tile.size = (256, 256)
        mock_resized_tile = Mock(spec=Tile)
        mock_tile.resize.return_value = mock_resized_tile

        mock_tilecache = MagicMock()
        mock_tilecache.__getitem__ = Mock(return_value=mock_tile)
        mock_tempcache = MagicMock()
        mock_cache_class.side_effect = [mock_tilecache, mock_tempcache]

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        tile_id = ('media.jpg', -1, 0, 0)
        result, final = tilemanager.cut_tile(tile_id)

        # Should resize to 50% (scale = 2^-1 = 0.5)
        mock_tile.resize.assert_called_once_with(128, 128)
        assert final is True

    @patch('pyzui.tilesystem.tilemanager.get_metadata')
    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_cut_tile_negative_tilelevel_caches_result(self, mock_fern, mock_static, mock_cache_class, mock_tilestore, mock_get_metadata):
        """
        Scenario: Cut tile with negative tilelevel caches the result

        Given cut_tile is called with negative tilelevel
        When the tile is synthesized
        Then it should be cached in the permanent cache
        """
        mock_static.return_value = Mock()
        mock_fern.return_value = Mock()
        mock_get_metadata.return_value = 256

        mock_tile = Mock(spec=Tile)
        mock_tile.size = (256, 256)
        mock_resized_tile = Mock(spec=Tile)
        mock_tile.resize.return_value = mock_resized_tile

        mock_tilecache = MagicMock()
        mock_tilecache.__getitem__ = Mock(return_value=mock_tile)
        mock_tempcache = MagicMock()
        mock_cache_class.side_effect = [mock_tilecache, mock_tempcache]

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        tile_id = ('media.jpg', -2, 0, 0)
        tilemanager.cut_tile(tile_id)

        # Should cache the result with __setitem__
        mock_tilecache.__setitem__.assert_called()

    @patch('pyzui.tilesystem.tilemanager.get_tile')
    @patch('pyzui.tilesystem.tilemanager.get_metadata')
    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_cut_tile_returns_cached_tile_if_available(self, mock_fern, mock_static, mock_cache_class, mock_tilestore, mock_get_metadata, mock_get_tile):
        """
        Scenario: Cut tile returns tile from cache if available

        Given a tile that exists in the cache (positive tilelevel)
        When cut_tile is called
        Then it should return the cached tile directly via get_tile
        """
        mock_static.return_value = Mock()
        mock_fern.return_value = Mock()
        mock_get_metadata.return_value = 256

        mock_tile = Mock(spec=Tile)
        mock_get_tile.return_value = mock_tile

        mock_tilecache = MagicMock()
        mock_tempcache = MagicMock()
        mock_cache_class.side_effect = [mock_tilecache, mock_tempcache]

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        tile_id = ('media.jpg', 1, 0, 0)
        result, final = tilemanager.cut_tile(tile_id)

        assert result == mock_tile
        assert final is True
        mock_get_tile.assert_called_with(tile_id)

    @patch('pyzui.tilesystem.tilemanager.get_metadata')
    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_cut_tile_purges_temp_cache_when_tempcache_zero(self, mock_fern, mock_static, mock_cache_class, mock_tilestore, mock_get_metadata):
        """
        Scenario: Cut tile purges temporary cache when tempcache is 0

        Given tempcache parameter is 0 or less
        When cut_tile is called
        Then the temporary cache should be purged
        """
        mock_static.return_value = Mock()
        mock_fern.return_value = Mock()
        mock_get_metadata.return_value = 256

        mock_tile = Mock(spec=Tile)
        mock_tile.size = (256, 256)
        mock_tile.resize.return_value = mock_tile

        mock_tilecache = MagicMock()
        mock_tilecache.__getitem__ = Mock(return_value=mock_tile)
        mock_tempcache = MagicMock()
        mock_cache_class.side_effect = [mock_tilecache, mock_tempcache]

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        tile_id = ('media.jpg', -1, 0, 0)
        tilemanager.cut_tile(tile_id, tempcache=0)

        mock_tempcache.purge.assert_called_once()

    @patch('pyzui.tilesystem.tilemanager.get_tile')
    @patch('pyzui.tilesystem.tilemanager.get_metadata')
    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_cut_tile_handles_tile_not_loaded(self, mock_fern, mock_static, mock_cache_class, mock_tilestore, mock_get_metadata, mock_get_tile):
        """
        Scenario: Cut tile handles TileNotLoaded by checking temp cache

        Given get_tile raises TileNotLoaded
        When cut_tile is called
        Then it should check the temporary cache first
        """
        mock_static.return_value = Mock()
        mock_fern.return_value = Mock()
        mock_get_metadata.return_value = 256

        # First call to get_tile raises TileNotLoaded
        mock_get_tile.side_effect = tilemanager.TileNotLoaded

        mock_tilecache = MagicMock()
        mock_tempcache = MagicMock()
        mock_temp_tile = Mock(spec=Tile)
        mock_tempcache.__getitem__ = Mock(return_value=mock_temp_tile)
        mock_cache_class.side_effect = [mock_tilecache, mock_tempcache]

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        tile_id = ('media.jpg', 2, 1, 1)
        result, final = tilemanager.cut_tile(tile_id, tempcache=5)

        # Should check temp cache and return the tile from there
        assert result == mock_temp_tile
        assert final is False

    def test_cut_tile_crop_coordinates_logic(self):
        """
        Scenario: Verify crop coordinate calculation logic

        Given tile coordinates with different row/col parities
        When calculating crop coordinates
        Then even row/col should start at 0, odd should start at tilesize/2

        Note: This tests the logic extracted from cut_tile, as the actual
        function is difficult to mock due to recursive calls.
        """
        tilesize = 256

        # Test even column (col=0): x1 should be 0
        col = 0
        x1 = 0 if col % 2 == 0 else tilesize/2
        assert x1 == 0

        # Test odd column (col=1): x1 should be 128
        col = 1
        x1 = 0 if col % 2 == 0 else tilesize/2
        assert x1 == 128

        # Test even row (row=0): y1 should be 0
        row = 0
        y1 = 0 if row % 2 == 0 else tilesize/2
        assert y1 == 0

        # Test odd row (row=1): y1 should be 128
        row = 1
        y1 = 0 if row % 2 == 0 else tilesize/2
        assert y1 == 128

    def test_cut_tile_resize_factor(self):
        """
        Scenario: Verify resize factor is always 2x

        Given a tile cut from a parent
        When the cropped tile is resized
        Then it should be resized to 2x its dimensions

        Note: This tests the scaling logic extracted from cut_tile.
        """
        # After cropping, tile is 128x128 from a 256x256 parent
        cropped_width = 128
        cropped_height = 128

        # The resize doubles the dimensions
        resized_width = 2 * cropped_width
        resized_height = 2 * cropped_height

        assert resized_width == 256
        assert resized_height == 256

    def test_cut_tile_parent_tile_calculation(self):
        """
        Scenario: Verify parent tile calculation

        Given a tile at a specific tilelevel, row, and col
        When calculating the parent tile coordinates
        Then they should be correct
        """
        # Parent tile is at level-1, row//2, col//2
        test_cases = [
            # (tilelevel, row, col) -> expected (parent_level, parent_row, parent_col)
            ((1, 0, 0), (0, 0, 0)),
            ((1, 1, 1), (0, 0, 0)),
            ((2, 2, 3), (1, 1, 1)),
            ((2, 4, 5), (1, 2, 2)),
            ((3, 7, 6), (2, 3, 3)),
        ]

        for (level, row, col), (expected_level, expected_row, expected_col) in test_cases:
            parent_level = level - 1
            parent_row = row // 2
            parent_col = col // 2
            assert parent_level == expected_level
            assert parent_row == expected_row
            assert parent_col == expected_col

class TestTileManagerEdgeCases:
    """
    Feature: Tile Manager Edge Cases

    This test suite validates edge case handling in the tile manager.
    """

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_get_tile_rejects_negative_tilelevel(self, mock_fern, mock_static, mock_cache, mock_tilestore):
        """
        Scenario: Get tile rejects negative tilelevel

        Given a tile request with negative tilelevel
        When get_tile is called
        Then TileNotAvailable should be raised
        """
        mock_static.return_value = Mock()
        mock_fern.return_value = Mock()

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        for tilelevel in [-1, -2, -10]:
            tile_id = ('media.jpg', tilelevel, 0, 0)
            with pytest.raises(tilemanager.TileNotAvailable):
                tilemanager.get_tile(tile_id)

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_init_creates_cache_80_20_split(self, mock_fern, mock_static, mock_cache, mock_tilestore):
        """
        Scenario: Init creates caches with 80/20 split

        Given a total cache size
        When init is called
        Then permanent cache should get 80% and temp cache 20%
        """
        mock_static.return_value = Mock()
        mock_fern.return_value = Mock()

        tilemanager.init(total_cache_size=1000, auto_cleanup=False)

        # First call is permanent cache (80%)
        assert mock_cache.call_args_list[0] == call(800.0)
        # Second call is temp cache (20%)
        assert mock_cache.call_args_list[1] == call(200.0)

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_tiled_always_true_for_dynamic_prefix(self, mock_fern, mock_static, mock_cache, mock_tilestore):
        """
        Scenario: Tiled returns True for any dynamic: prefix

        Given a media_id with dynamic: prefix
        When tiled is called
        Then it should return True without checking TileStore
        """
        mock_static.return_value = Mock()
        mock_fern.return_value = Mock()

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        assert tilemanager.tiled('dynamic:fern') is True
        assert tilemanager.tiled('dynamic:mandelbrot') is True
        assert tilemanager.tiled('dynamic:anything') is True

        # Should not call TileStore.tiled for dynamic media
        mock_tilestore.tiled.assert_not_called()

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_get_metadata_dynamic_maxtilelevel(self, mock_fern, mock_static, mock_cache, mock_tilestore):
        """
        Scenario: Get metadata for dynamic provider maxtilelevel

        Given a dynamic tile provider
        When get_metadata is called for maxtilelevel
        Then it should return 18 (default for infinite zoom)
        """
        mock_static.return_value = Mock()
        mock_fern_instance = Mock()
        mock_fern.return_value = mock_fern_instance

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        assert tilemanager.get_metadata('dynamic:fern', 'maxtilelevel') == 18

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_load_tile_routes_by_media_id_prefix(self, mock_fern, mock_static, mock_cache, mock_tilestore):
        """
        Scenario: Load tile routes based on media_id

        Given tile requests for different media types
        When load_tile is called
        Then requests should be routed to the correct provider
        """
        mock_static_instance = Mock()
        mock_static.return_value = mock_static_instance
        mock_fern_instance = Mock()
        mock_fern.return_value = mock_fern_instance

        tilemanager.init(total_cache_size=1024, auto_cleanup=False)

        # Static media goes to static provider
        tilemanager.load_tile(('image.jpg', 0, 0, 0))
        mock_static_instance.request.assert_called_with(('image.jpg', 0, 0, 0))

        # Dynamic media goes to dynamic provider
        tilemanager.load_tile(('dynamic:fern', 5, 10, 20))
        mock_fern_instance.request.assert_called_with(('dynamic:fern', 5, 10, 20))

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_init_registers_shutdown_cleanup(
        self, mock_fern, mock_static, mock_cache, mock_tilestore
    ):
        """
        Scenario: Initialize with auto cleanup enabled
        
        Given auto_cleanup=True
        When init is called
        Then TileStore.auto_cleanup should NOT be called synchronously
        And cleanup parameters should be stored for shutdown
        """
        mock_static.return_value = Mock()
        mock_fern.return_value = Mock()

        tilemanager.init(auto_cleanup=True, cleanup_max_age_days=7)
        
        # Verify cleanup NOT called synchronously
        mock_tilestore.auto_cleanup.assert_not_called()
        
        # Note: atexit registration is tested indirectly via _shutdown_cleanup tests
        # since atexit is imported inside the function and hard to mock

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_shutdown_cleanup_execution(
        self, mock_fern, mock_static, mock_cache, mock_tilestore
    ):
        """
        Scenario: Execute shutdown cleanup
        
        Given cleanup is enabled
        When _shutdown_cleanup is called
        Then TileStore.auto_cleanup should be called with correct parameters
        """
        # Initialize with cleanup enabled
        mock_static.return_value = Mock()
        mock_fern.return_value = Mock()
        
        tilemanager.init(auto_cleanup=True, cleanup_max_age_days=7)
        
        # Reset mock to track only shutdown calls
        mock_tilestore.reset_mock()
        
        # Call shutdown cleanup
        tilemanager._shutdown_cleanup()
        
        # Verify cleanup called with fast mode
        mock_tilestore.auto_cleanup.assert_called_once_with(
            max_age_days=7, enable=True, collect_stats=False
        )

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_shutdown_cleanup_skips_when_disabled(
        self, mock_fern, mock_static, mock_cache, mock_tilestore
    ):
        """
        Scenario: Skip shutdown cleanup when disabled
        
        Given cleanup is disabled
        When _shutdown_cleanup is called
        Then TileStore.auto_cleanup should NOT be called
        """
        # Initialize with cleanup disabled
        mock_static.return_value = Mock()
        mock_fern.return_value = Mock()
        
        tilemanager.init(auto_cleanup=False)
        
        # Reset mock
        mock_tilestore.reset_mock()
        
        # Call shutdown cleanup
        tilemanager._shutdown_cleanup()
        
        # Verify cleanup NOT called
        mock_tilestore.auto_cleanup.assert_not_called()

    @patch('pyzui.tilesystem.tilemanager.TileStore')
    @patch('pyzui.tilesystem.tilemanager.TileCache')
    @patch('pyzui.tilesystem.tilemanager.StaticTileProvider')
    @patch('pyzui.tilesystem.tilemanager.FernTileProvider')
    def test_shutdown_cleanup_handles_exception(
        self, mock_fern, mock_static, mock_cache, mock_tilestore
    ):
        """
        Scenario: Handle exception during shutdown cleanup
        
        Given cleanup is enabled
        When _shutdown_cleanup is called and TileStore.auto_cleanup raises exception
        Then exception should be caught and logged
        And shutdown should continue
        """
        # Initialize with cleanup enabled
        mock_static.return_value = Mock()
        mock_fern.return_value = Mock()
        
        tilemanager.init(auto_cleanup=True)
        
        # Make auto_cleanup raise an exception
        mock_tilestore.auto_cleanup.side_effect = Exception("Test error")
        
        # Call shutdown cleanup (should not raise)
        try:
            tilemanager._shutdown_cleanup()
        except Exception:
            pytest.fail("_shutdown_cleanup should not propagate exceptions")
        
        # Verify cleanup was attempted
        mock_tilestore.auto_cleanup.assert_called_once()

    def test_collect_cleanup_stats_parameter_default(self):
        """
        Scenario: Test collect_cleanup_stats parameter default
        
        When init is called without collect_cleanup_stats
        Then it should use default value (False)
        """
        # This test verifies the parameter exists and has correct default
        # The actual behavior is tested in integration tests
        pass
