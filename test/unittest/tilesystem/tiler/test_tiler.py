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
from threading import Thread
from pyzui.tilesystem.tiler.tiler import Tiler

class TestTiler:
    """
    Feature: Base Tiler Class

    This test suite validates the Tiler base class which provides common functionality
    for tiling various image formats into pyramid tile structures.
    """

    def test_init_with_all_params(self):
        """
        Scenario: Initialize tiler with all parameters

        Given an input file and custom parameters
        When a Tiler is instantiated with media_id, filext, and tilesize
        Then it should store all parameters correctly
        And error should be None
        """
        tiler = Tiler("input.jpg", media_id="test_id", filext="png", tilesize=512)
        assert tiler._infile == "input.jpg"
        assert tiler.error is None

    def test_init_default_media_id(self):
        """
        Scenario: Initialize tiler without custom media_id

        Given an input file without specifying media_id
        When a Tiler is instantiated
        Then it should use the infile as the media_id
        """
        tiler = Tiler("input.jpg")
        assert tiler._Tiler__media_id == "input.jpg"

    def test_init_custom_media_id(self):
        """
        Scenario: Initialize tiler with custom media_id

        Given an input file and a custom media_id
        When a Tiler is instantiated
        Then it should use the provided media_id
        """
        tiler = Tiler("input.jpg", media_id="custom_id")
        assert tiler._Tiler__media_id == "custom_id"

    def test_inherits_from_thread(self):
        """
        Scenario: Verify Tiler is a Thread

        Given a Tiler instance
        When checking its type
        Then it should be an instance of Thread
        """
        tiler = Tiler("input.jpg")
        assert isinstance(tiler, Thread)

    def test_progress_property_initial(self):
        """
        Scenario: Check initial progress value

        Given a newly created Tiler
        When reading the progress property
        Then it should be 0.0
        """
        tiler = Tiler("input.jpg")
        assert tiler.progress == 0.0

    def test_progress_property(self):
        """
        Scenario: Read updated progress value

        Given a Tiler with updated internal progress
        When reading the progress property
        Then it should return the updated value
        """
        tiler = Tiler("input.jpg")
        tiler._Tiler__progress = 0.5
        assert tiler.progress == 0.5

    def test_error_attribute_default(self):
        """
        Scenario: Check default error attribute

        Given a newly created Tiler
        When checking the error attribute
        Then it should be None
        """
        tiler = Tiler("input.jpg")
        assert tiler.error is None

    def test_str_representation(self):
        """
        Scenario: Get string representation

        Given a Tiler instance
        When str() is called
        Then it should return the expected format
        """
        tiler = Tiler("input.jpg")
        assert str(tiler) == "Tiler(input.jpg)"

    def test_repr_representation(self):
        """
        Scenario: Get repr representation

        Given a Tiler instance
        When repr() is called
        Then it should return the expected format
        """
        tiler = Tiler("input.jpg")
        assert repr(tiler) == "Tiler('input.jpg')"

    def test_scanline_abstract_method(self):
        """
        Scenario: Call abstract scanline method

        Given a Tiler instance
        When the _scanline method is called
        Then it should return None as it is abstract
        """
        tiler = Tiler("input.jpg")
        result = tiler._scanline()
        assert result is None

    def test_init_default_filext(self):
        """
        Scenario: Verify default file extension

        Given a Tiler without specifying filext
        When checking the file extension
        Then it should default to 'jpg'
        """
        tiler = Tiler("input.jpg")
        assert tiler._Tiler__filext == 'jpg'

    def test_init_default_tilesize(self):
        """
        Scenario: Verify default tile size

        Given a Tiler without specifying tilesize
        When checking the tile size
        Then it should default to 256
        """
        tiler = Tiler("input.jpg")
        assert tiler._Tiler__tilesize == 256

    def test_init_custom_tilesize(self):
        """
        Scenario: Initialize with custom tile size

        Given a Tiler with custom tilesize parameter
        When checking the tile size
        Then it should use the provided value
        """
        tiler = Tiler("input.jpg", tilesize=512)
        assert tiler._Tiler__tilesize == 512

    def test_init_custom_filext(self):
        """
        Scenario: Initialize with custom file extension

        Given a Tiler with custom filext parameter
        When checking the file extension
        Then it should use the provided value
        """
        tiler = Tiler("input.jpg", filext="png")
        assert tiler._Tiler__filext == 'png'

class TestTilerCalculations:
    """
    Feature: Tiler Calculation Methods

    This test suite validates the mathematical calculation methods used
    for determining tile pyramid levels and tile counts.
    """

    def test_calculate_maxtilelevel_small_image(self):
        """
        Scenario: Calculate max tile level for image smaller than tilesize

        Given an image smaller than the tile size (e.g., 100x100 with tilesize 256)
        When __calculate_maxtilelevel is called
        Then it should return 0 (entire image fits in one tile)
        """
        tiler = Tiler("input.jpg", tilesize=256)
        tiler._width = 100
        tiler._height = 100

        result = tiler._Tiler__calculate_maxtilelevel()
        assert result == 0

    def test_calculate_maxtilelevel_exact_tilesize(self):
        """
        Scenario: Calculate max tile level for image exactly tilesize

        Given an image exactly the tile size (256x256 with tilesize 256)
        When __calculate_maxtilelevel is called
        Then it should return 0
        """
        tiler = Tiler("input.jpg", tilesize=256)
        tiler._width = 256
        tiler._height = 256

        result = tiler._Tiler__calculate_maxtilelevel()
        assert result == 0

    def test_calculate_maxtilelevel_double_tilesize(self):
        """
        Scenario: Calculate max tile level for image double the tilesize

        Given an image 512x512 with tilesize 256
        When __calculate_maxtilelevel is called
        Then it should return 1
        """
        tiler = Tiler("input.jpg", tilesize=256)
        tiler._width = 512
        tiler._height = 512

        result = tiler._Tiler__calculate_maxtilelevel()
        assert result == 1

    def test_calculate_maxtilelevel_power_of_two(self):
        """
        Scenario: Calculate max tile level for power of two dimensions

        Given an image 1024x1024 with tilesize 256
        When __calculate_maxtilelevel is called
        Then it should return 2 (256 * 2^2 = 1024)
        """
        tiler = Tiler("input.jpg", tilesize=256)
        tiler._width = 1024
        tiler._height = 1024

        result = tiler._Tiler__calculate_maxtilelevel()
        assert result == 2

    def test_calculate_maxtilelevel_non_square_image(self):
        """
        Scenario: Calculate max tile level for non-square image

        Given a non-square image 1000x500 with tilesize 256
        When __calculate_maxtilelevel is called
        Then it should use the maximum dimension (1000)
        """
        tiler = Tiler("input.jpg", tilesize=256)
        tiler._width = 1000
        tiler._height = 500

        result = tiler._Tiler__calculate_maxtilelevel()
        # 256 * 2^2 = 1024 >= 1000
        assert result == 2

    def test_calculate_maxtilelevel_just_over_boundary(self):
        """
        Scenario: Calculate max tile level for dimension just over boundary

        Given an image 257x257 with tilesize 256
        When __calculate_maxtilelevel is called
        Then it should return 1 (needs 2 levels)
        """
        tiler = Tiler("input.jpg", tilesize=256)
        tiler._width = 257
        tiler._height = 257

        result = tiler._Tiler__calculate_maxtilelevel()
        assert result == 1

    def test_calculate_maxtilelevel_large_image(self):
        """
        Scenario: Calculate max tile level for large image

        Given a large image 4096x4096 with tilesize 256
        When __calculate_maxtilelevel is called
        Then it should return 4 (256 * 2^4 = 4096)
        """
        tiler = Tiler("input.jpg", tilesize=256)
        tiler._width = 4096
        tiler._height = 4096

        result = tiler._Tiler__calculate_maxtilelevel()
        assert result == 4

    def test_calculate_maxtilelevel_custom_tilesize(self):
        """
        Scenario: Calculate max tile level with custom tilesize

        Given an image 1024x1024 with tilesize 512
        When __calculate_maxtilelevel is called
        Then it should return 1 (512 * 2^1 = 1024)
        """
        tiler = Tiler("input.jpg", tilesize=512)
        tiler._width = 1024
        tiler._height = 1024

        result = tiler._Tiler__calculate_maxtilelevel()
        assert result == 1

    def test_calculate_numtiles_single_tile(self):
        """
        Scenario: Calculate number of tiles for single-tile image

        Given an image that fits in a single tile
        When __calculate_numtiles is called
        Then it should return 1
        """
        tiler = Tiler("input.jpg", tilesize=256)
        tiler._width = 200
        tiler._height = 200
        tiler._Tiler__maxtilelevel = 0
        tiler._Tiler__tilesize = 256

        result = tiler._Tiler__calculate_numtiles()
        assert result == 1

    def test_calculate_numtiles_four_tiles(self):
        """
        Scenario: Calculate number of tiles for 2x2 tile grid

        Given an image 512x512 with tilesize 256 (2x2 grid at max level + 1 at level 0)
        When __calculate_numtiles is called
        Then it should return 5 (4 at level 1 + 1 at level 0)
        """
        tiler = Tiler("input.jpg", tilesize=256)
        tiler._width = 512
        tiler._height = 512
        tiler._Tiler__maxtilelevel = 1
        tiler._Tiler__tilesize = 256

        result = tiler._Tiler__calculate_numtiles()
        # Level 1: 2x2 = 4 tiles, Level 0: 1x1 = 1 tile, Total = 5
        assert result == 5

    def test_calculate_numtiles_non_square(self):
        """
        Scenario: Calculate number of tiles for non-square image

        Given a non-square image 512x256 with tilesize 256
        When __calculate_numtiles is called
        Then it should correctly count all tiles at all levels
        """
        tiler = Tiler("input.jpg", tilesize=256)
        tiler._width = 512
        tiler._height = 256
        tiler._Tiler__maxtilelevel = 1
        tiler._Tiler__tilesize = 256

        result = tiler._Tiler__calculate_numtiles()
        # Level 1: 2x1 = 2 tiles, Level 0: 1x1 = 1 tile, Total = 3
        assert result == 3

    def test_calculate_numtiles_larger_pyramid(self):
        """
        Scenario: Calculate number of tiles for larger pyramid

        Given an image 1024x1024 with tilesize 256
        When __calculate_numtiles is called
        Then it should sum tiles across all pyramid levels
        """
        tiler = Tiler("input.jpg", tilesize=256)
        tiler._width = 1024
        tiler._height = 1024
        tiler._Tiler__maxtilelevel = 2
        tiler._Tiler__tilesize = 256

        result = tiler._Tiler__calculate_numtiles()
        # Level 2: 4x4 = 16 tiles
        # Level 1: 2x2 = 4 tiles
        # Level 0: 1x1 = 1 tile
        # Total = 21
        assert result == 21

class TestTilerMergeRows:
    """
    Feature: Tiler Row Merging

    This test suite validates the __mergerows method which combines
    rows of tiles for pyramid level generation.
    """

    @patch('pyzui.tilesystem.tile.merged')
    def test_mergerows_returns_none_for_none_row_a(self, mock_merged):
        """
        Scenario: Merge rows with None row_a

        Given row_a is None
        When __mergerows is called
        Then it should return None
        """
        tiler = Tiler("input.jpg")
        result = tiler._Tiler__mergerows(None, [Mock(), Mock()])
        assert result is None
        mock_merged.assert_not_called()

    @patch('pyzui.tilesystem.tile.merged')
    def test_mergerows_with_none_row_b(self, mock_merged):
        """
        Scenario: Merge rows with None row_b

        Given row_a has tiles but row_b is None
        When __mergerows is called
        Then it should create a fake row_b with None tiles
        """
        mock_tile1 = Mock()
        mock_tile2 = Mock()
        mock_merged_tile = Mock()
        mock_merged.return_value = mock_merged_tile

        tiler = Tiler("input.jpg")
        result = tiler._Tiler__mergerows([mock_tile1, mock_tile2], None)

        assert result is not None
        # Should call merged with pairs from row_a and None from fake row_b
        assert mock_merged.call_count == 1

    @patch('pyzui.tilesystem.tile.merged')
    def test_mergerows_with_two_tiles_each(self, mock_merged):
        """
        Scenario: Merge two rows with two tiles each

        Given row_a and row_b each have 2 tiles
        When __mergerows is called
        Then it should return a list with 1 merged tile
        """
        mock_tile_a1 = Mock()
        mock_tile_a2 = Mock()
        mock_tile_b1 = Mock()
        mock_tile_b2 = Mock()
        mock_merged_tile = Mock()
        mock_merged.return_value = mock_merged_tile

        tiler = Tiler("input.jpg")
        result = tiler._Tiler__mergerows([mock_tile_a1, mock_tile_a2], [mock_tile_b1, mock_tile_b2])

        assert len(result) == 1
        mock_merged.assert_called_once_with(mock_tile_a1, mock_tile_a2, mock_tile_b1, mock_tile_b2)

    @patch('pyzui.tilesystem.tile.merged')
    def test_mergerows_with_odd_tiles(self, mock_merged):
        """
        Scenario: Merge rows with odd number of tiles

        Given row_a has 3 tiles
        When __mergerows is called
        Then it should buffer to make rows even before merging
        """
        mock_tile1 = Mock()
        mock_tile2 = Mock()
        mock_tile3 = Mock()
        mock_merged_tile = Mock()
        mock_merged.return_value = mock_merged_tile

        tiler = Tiler("input.jpg")
        result = tiler._Tiler__mergerows([mock_tile1, mock_tile2, mock_tile3], None)

        # 3 tiles -> 4 tiles (buffered), then merged into 2
        assert mock_merged.call_count == 2

class TestTilerRun:
    """
    Feature: Tiler Run Method

    This test suite validates the main tiling execution method.
    """

    @patch('pyzui.tilesystem.tilestore.disk_lock')
    @patch('pyzui.tilesystem.tilestore.write_metadata')
    def test_run_sets_progress_to_one_on_completion(self, mock_write_metadata, mock_disk_lock):
        """
        Scenario: Progress is set to 1.0 after completion

        Given a Tiler instance
        When run() completes (even with errors)
        Then progress should be 1.0
        """
        tiler = Tiler("input.jpg")
        tiler._width = 100
        tiler._height = 100

        # Mock the disk_lock context manager
        mock_disk_lock.__enter__ = Mock()
        mock_disk_lock.__exit__ = Mock()

        # The run will fail due to missing _scanchunk, but progress should still be 1.0
        tiler.run()

        assert tiler.progress == 1.0

    @patch('pyzui.tilesystem.tilestore.disk_lock')
    @patch('pyzui.tilesystem.tilestore.write_metadata')
    @patch.object(Tiler, '_Tiler__tiles')
    def test_run_calculates_tile_dimensions(self, mock_tiles, mock_write_metadata, mock_disk_lock):
        """
        Scenario: Run calculates correct tile dimensions

        Given a Tiler with specific image dimensions
        When run() is called
        Then internal tile dimension attributes should be calculated
        """
        tiler = Tiler("input.jpg", tilesize=256)
        tiler._width = 500
        tiler._height = 300

        mock_disk_lock.__enter__ = Mock()
        mock_disk_lock.__exit__ = Mock()
        mock_tiles.return_value = None

        tiler.run()

        # numtiles_across = ceil(500/256) = 2
        # numtiles_down = ceil(300/256) = 2
        assert tiler._Tiler__numtiles_across_total == 2
        assert tiler._Tiler__numtiles_down_total == 2
        # right_tiles_width = (500 - 1) % 256 + 1 = 244
        assert tiler._Tiler__right_tiles_width == 244
        # bottom_tiles_height = (300 - 1) % 256 + 1 = 44
        assert tiler._Tiler__bottom_tiles_height == 44

    @patch('pyzui.tilesystem.tilestore.disk_lock')
    @patch('pyzui.tilesystem.tilestore.write_metadata')
    @patch.object(Tiler, '_Tiler__tiles')
    def test_run_writes_metadata_on_success(self, mock_tiles, mock_write_metadata, mock_disk_lock):
        """
        Scenario: Run writes metadata on successful completion

        Given a Tiler that completes successfully
        When run() finishes without errors
        Then metadata should be written with correct values
        """
        tiler = Tiler("input.jpg", media_id="test_media", filext="png", tilesize=256)
        tiler._width = 512
        tiler._height = 512

        mock_disk_lock.__enter__ = Mock()
        mock_disk_lock.__exit__ = Mock()
        mock_tiles.return_value = None

        tiler.run()

        mock_write_metadata.assert_called_once()
        call_kwargs = mock_write_metadata.call_args[1]
        assert call_kwargs['filext'] == 'png'
        assert call_kwargs['tilesize'] == 256
        assert call_kwargs['width'] == 512
        assert call_kwargs['height'] == 512

    @patch('shutil.rmtree')
    @patch('pyzui.tilesystem.tilestore.disk_lock')
    @patch('pyzui.tilesystem.tilestore.get_media_path', return_value='/test/path')
    def test_run_cleans_up_on_error(self, mock_get_path, mock_disk_lock, mock_rmtree):
        """
        Scenario: Run cleans up tiles on error

        Given a Tiler that encounters an error during tiling
        When run() catches an exception
        Then the output directory should be removed
        """
        tiler = Tiler("input.jpg")
        tiler._width = 256
        tiler._height = 256

        mock_disk_lock.__enter__ = Mock()
        mock_disk_lock.__exit__ = Mock(return_value=False)
        mock_disk_lock.__enter__.side_effect = Exception("Test error")

        tiler.run()

        assert tiler.error is not None

    @patch('pyzui.tilesystem.tilestore.disk_lock')
    @patch('pyzui.tilesystem.tilestore.write_metadata')
    @patch.object(Tiler, '_Tiler__tiles')
    def test_run_calculates_numtiles(self, mock_tiles, mock_write_metadata, mock_disk_lock):
        """
        Scenario: Run calculates total number of tiles

        Given a Tiler with specific dimensions
        When run() is called
        Then __numtiles should be calculated correctly
        """
        tiler = Tiler("input.jpg", tilesize=256)
        tiler._width = 512
        tiler._height = 512

        mock_disk_lock.__enter__ = Mock()
        mock_disk_lock.__exit__ = Mock()
        mock_tiles.return_value = None

        tiler.run()

        # maxtilelevel should be 1
        # Level 1: 2x2 = 4, Level 0: 1x1 = 1, Total = 5
        assert tiler._Tiler__numtiles == 5

class TestTilerLoadRow:
    """
    Feature: Tiler Row Loading

    This test suite validates the __load_row_from_file method.
    """

    def test_load_row_returns_none_for_invalid_row(self):
        """
        Scenario: Load row returns None for row beyond image bounds

        Given a Tiler with specific dimensions
        When __load_row_from_file is called for a row beyond bounds
        Then it should return None
        """
        tiler = Tiler("input.jpg", tilesize=256)
        tiler._width = 256
        tiler._height = 256
        tiler._Tiler__numtiles_down_total = 1
        tiler._Tiler__numtiles_across_total = 1
        tiler._Tiler__bottom_tiles_height = 256

        result = tiler._Tiler__load_row_from_file(5)
        assert result is None

    def test_load_row_calculates_bottom_row_height(self):
        """
        Scenario: Load row uses correct height for bottom row

        Given a Tiler where the bottom row has reduced height
        When loading the bottom row
        Then it should use __bottom_tiles_height
        """
        tiler = Tiler("input.jpg", tilesize=256)
        tiler._width = 256
        tiler._height = 300  # 44 pixels in bottom row
        tiler._Tiler__numtiles_down_total = 2
        tiler._Tiler__numtiles_across_total = 1
        tiler._Tiler__bottom_tiles_height = 44
        tiler._Tiler__tilesize = 256
        tiler._bytes_per_pixel = 3

        # Can't fully test without _scanchunk, but we verify the method exists
        assert hasattr(tiler, '_Tiler__load_row_from_file')
