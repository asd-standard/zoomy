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
from pyzui.tilesystem.tileproviders import FernTileProvider

class TestFernTileProvider:
    """
    Feature: Fern Dynamic Tile Provider

    This test suite validates the FernTileProvider class which dynamically generates
    Barnsley fern fractal tiles on demand using iterated function systems.
    """

    def test_init(self):
        """
        Scenario: Initialize fern tile provider

        Given a mock tile cache
        When a FernTileProvider is instantiated
        Then it should be successfully created
        """
        tilecache = Mock()
        provider = FernTileProvider(tilecache)
        assert provider is not None

    def test_inherits_from_dynamictileprovider(self):
        """
        Scenario: Verify inheritance from DynamicTileProvider

        Given a mock tile cache
        When a FernTileProvider is instantiated
        Then it should be an instance of DynamicTileProvider
        """
        from pyzui.tilesystem.tileproviders import DynamicTileProvider
        tilecache = Mock()
        provider = FernTileProvider(tilecache)
        assert isinstance(provider, DynamicTileProvider)

    def test_filext_attribute(self):
        """
        Scenario: Verify file extension configuration

        Given the FernTileProvider class
        When checking the filext attribute
        Then it should be 'png'
        """
        assert FernTileProvider.filext == 'png'

    def test_tilesize_attribute(self):
        """
        Scenario: Verify tile size configuration

        Given the FernTileProvider class
        When checking the tilesize attribute
        Then it should be 256
        """
        assert FernTileProvider.tilesize == 256

    def test_aspect_ratio_attribute(self):
        """
        Scenario: Verify aspect ratio configuration

        Given the FernTileProvider class
        When checking the aspect_ratio attribute
        Then it should be 1.0
        """
        assert FernTileProvider.aspect_ratio == 1.0

    def test_max_iterations_attribute(self):
        """
        Scenario: Verify maximum iterations setting

        Given a FernTileProvider instance
        When checking the max_iterations attribute
        Then it should be 50000
        """
        tilecache = Mock()
        provider = FernTileProvider(tilecache)
        assert provider.max_iterations == 50000

    def test_max_points_attribute(self):
        """
        Scenario: Verify maximum points setting

        Given a FernTileProvider instance
        When checking the max_points attribute
        Then it should be 10000
        """
        tilecache = Mock()
        provider = FernTileProvider(tilecache)
        assert provider.max_points == 10000

    def test_transformations_attribute(self):
        """
        Scenario: Verify transformation matrices exist

        Given a FernTileProvider instance
        When checking the transformations attribute
        Then it should contain 4 transformation matrices
        """
        tilecache = Mock()
        provider = FernTileProvider(tilecache)
        assert len(provider.transformations) == 4

    def test_color_attribute(self):
        """
        Scenario: Verify fern color configuration

        Given a FernTileProvider instance
        When checking the color attribute
        Then it should be green RGB tuple (100, 170, 0)
        """
        tilecache = Mock()
        provider = FernTileProvider(tilecache)
        assert provider.color == (100, 170, 0)

    def test_load_dynamic_negative_row(self):
        """
        Scenario: Handle negative row coordinate

        Given a FernTileProvider instance
        When _load_dynamic is called with a negative row coordinate
        Then it should return None as the tile is out of bounds
        """
        tilecache = Mock()
        provider = FernTileProvider(tilecache)
        tile_id = ('fern', 2, -1, 1)
        outfile = '/path/to/tile.png'
        result = provider._load_dynamic(tile_id, outfile)
        assert result is None

    def test_load_dynamic_negative_col(self):
        """
        Scenario: Handle negative column coordinate

        Given a FernTileProvider instance
        When _load_dynamic is called with a negative column coordinate
        Then it should return None as the tile is out of bounds
        """
        tilecache = Mock()
        provider = FernTileProvider(tilecache)
        tile_id = ('fern', 2, 1, -1)
        outfile = '/path/to/tile.png'
        result = provider._load_dynamic(tile_id, outfile)
        assert result is None

    def test_load_dynamic_out_of_range(self):
        """
        Scenario: Handle coordinates beyond valid range

        Given a FernTileProvider instance
        When _load_dynamic is called with coordinates outside the valid range
        Then it should return None as the tile is out of bounds
        """
        tilecache = Mock()
        provider = FernTileProvider(tilecache)
        tile_id = ('fern', 2, 10, 10)
        outfile = '/path/to/tile.png'
        result = provider._load_dynamic(tile_id, outfile)
        assert result is None

    @patch('pyzui.tilesystem.tileproviders.ferndynamictileprovider.Image.new')
    def test_load_dynamic_valid_tile(self, mock_image_new):
        """
        Scenario: Generate valid fern fractal tile

        Given a FernTileProvider with mocked image creation
        When _load_dynamic is called with valid coordinates
        Then a 256x256 RGB image should be created
        And the image should be saved to the output file
        """
        tilecache = Mock()
        provider = FernTileProvider(tilecache)

        mock_image = Mock()
        mock_image_new.return_value = mock_image

        tile_id = ('fern', 2, 1, 1)
        outfile = '/path/to/tile.png'

        provider._load_dynamic(tile_id, outfile)

        mock_image.save.assert_called_once_with(outfile)
        mock_image_new.assert_called_once_with('RGB', (256, 256))
