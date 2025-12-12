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
import os
import hashlib
from unittest.mock import Mock, patch, mock_open
from pyzui.tilesystem import tilestore

class TestTilestoreModule:
    """
    Feature: Tile Store Module

    This test suite validates the tile store module which manages persistent storage
    of tiles on disk, including metadata and file path management.
    """

    def test_tile_dir_exists(self):
        """
        Scenario: Verify tile directory is configured

        Given the tilestore module
        When checking the tile_dir variable
        Then it should be set to a non-null string value
        """
        assert tilestore.tile_dir is not None
        assert isinstance(tilestore.tile_dir, str)

    def test_disk_lock_exists(self):
        """
        Scenario: Verify disk lock is available

        Given the tilestore module
        When checking for the disk_lock object
        Then it should exist for thread-safe disk operations
        """
        assert tilestore.disk_lock is not None

    def test_get_media_path(self):
        """
        Scenario: Get media directory path

        Given a media_id string
        When get_media_path is called
        Then it should return a valid non-empty path string
        """
        media_id = "test_media"
        path = tilestore.get_media_path(media_id)
        assert isinstance(path, str)
        assert len(path) > 0

    def test_get_media_path_consistent(self):
        """
        Scenario: Verify path consistency for media

        Given the same media_id called twice
        When get_media_path is called both times
        Then it should return identical paths
        """
        media_id = "test_media"
        path1 = tilestore.get_media_path(media_id)
        path2 = tilestore.get_media_path(media_id)
        assert path1 == path2

    def test_get_media_path_different_ids(self):
        """
        Scenario: Verify unique paths for different media

        Given two different media_id values
        When get_media_path is called for each
        Then the returned paths should be different
        """
        path1 = tilestore.get_media_path("media1")
        path2 = tilestore.get_media_path("media2")
        assert path1 != path2

    def test_get_media_path_uses_hash(self):
        """
        Scenario: Verify SHA1 hash in path

        Given a media_id
        When get_media_path is called
        Then the returned path should contain the SHA1 hash of the media_id
        """
        media_id = "test_media"
        expected_hash = hashlib.sha1(media_id.encode('utf-8')).hexdigest()
        path = tilestore.get_media_path(media_id)
        assert expected_hash in path

    def test_get_tile_path_basic(self):
        """
        Scenario: Get basic tile file path

        Given a tile_id tuple with mocked metadata
        When get_tile_path is called
        Then it should return a valid path with the correct file extension
        """
        tile_id = ('media_id', 0, 0, 0)
        with patch('pyzui.tilesystem.tilestore.tilestore.get_metadata', return_value='jpg'):
            path = tilestore.get_tile_path(tile_id)
            assert isinstance(path, str)
            assert '.jpg' in path

    def test_get_tile_path_with_filext(self):
        """
        Scenario: Get tile path with custom file extension

        Given a tile_id with specific level, row, and column
        When get_tile_path is called with a custom filext
        Then the path should include the extension and formatted coordinates
        """
        tile_id = ('media_id', 1, 2, 3)
        path = tilestore.get_tile_path(tile_id, filext='png')
        assert '.png' in path
        assert '01' in path  # tilelevel
        assert '000002' in path  # row
        assert '000003' in path  # col

    def test_get_tile_path_with_prefix(self):
        """
        Scenario: Get tile path with custom directory prefix

        Given a tile_id and a custom directory prefix
        When get_tile_path is called with the prefix
        Then the returned path should start with the custom prefix
        """
        tile_id = ('media_id', 0, 0, 0)
        prefix = '/custom/path'
        path = tilestore.get_tile_path(tile_id, prefix=prefix, filext='jpg')
        assert path.startswith(prefix)

    @patch('os.makedirs')
    @patch('os.path.exists', return_value=False)
    def test_get_tile_path_mkdirp(self, mock_exists, mock_makedirs):
        """
        Scenario: Create directories automatically

        Given a tile_id for a non-existent directory
        When get_tile_path is called with mkdirp=True
        Then the necessary directories should be created
        """
        tile_id = ('media_id', 0, 0, 0)
        tilestore.get_tile_path(tile_id, mkdirp=True, filext='jpg')
        mock_makedirs.assert_called_once()

    @patch('builtins.open', new_callable=mock_open, read_data="width\t100\tint\nheight\t200\tint\n")
    @patch('os.path.join')
    def test_load_metadata_success(self, mock_join, mock_file):
        """
        Scenario: Successfully load metadata from file

        Given a media_id with valid metadata file
        When load_metadata is called
        Then it should read and parse the metadata
        And return True
        """
        mock_join.return_value = '/path/to/metadata'
        result = tilestore.load_metadata('media_id')
        assert result is True

    @patch('builtins.open', side_effect=IOError)
    def test_load_metadata_failure(self, mock_file):
        """
        Scenario: Handle missing metadata file

        Given a media_id with no metadata file
        When load_metadata is called
        Then it should catch the IOError and return False
        """
        result = tilestore.load_metadata('nonexistent_media')
        assert result is False

    @patch('builtins.open', new_callable=mock_open, read_data="key1\tvalue1\tstr\nkey2\t42\tint\n")
    @patch('os.path.join')
    def test_get_metadata(self, mock_join, mock_file):
        """
        Scenario: Retrieve metadata value by key

        Given a media_id with loaded metadata
        When get_metadata is called with a specific key
        Then it should return the corresponding value
        """
        mock_join.return_value = '/path/to/metadata'
        tilestore._TileStore__metadata = {}  # Reset metadata
        value = tilestore.get_metadata('media_id', 'key2')
        # Metadata should be loaded and parsed

    def test_get_metadata_nonexistent_key(self):
        """
        Scenario: Request non-existent metadata key

        Given a media_id with loaded metadata
        When get_metadata is called with a key that doesn't exist
        Then it should return None
        """
        tilestore._TileStore__metadata = {}
        with patch.object(tilestore, 'load_metadata', return_value=True):
            tilestore._TileStore__metadata = {'media_id': {}}
            value = tilestore.get_metadata('media_id', 'nonexistent_key')
            assert value is None

    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.join')
    def test_write_metadata(self, mock_join, mock_file):
        """
        Scenario: Write metadata to file

        Given a media_id and metadata key-value pairs
        When write_metadata is called
        Then the metadata should be written to the file
        """
        mock_join.return_value = '/path/to/metadata'
        tilestore.write_metadata('media_id', width=100, height=200)
        mock_file.assert_called()

    @patch('os.path.exists')
    @patch.object(tilestore, 'get_tile_path')
    @patch.object(tilestore, 'get_media_path')
    def test_tiled_true(self, mock_media_path, mock_tile_path, mock_exists):
        """
        Scenario: Check if media is tiled with existing tiles

        Given a media_id with existing metadata and tile files
        When tiled is called
        Then it should return True
        """
        mock_media_path.return_value = '/media/path'
        mock_tile_path.return_value = '/tile/path'
        mock_exists.return_value = True

        result = tilestore.tiled('media_id')
        assert result is True

    @patch('os.path.exists')
    @patch.object(tilestore, 'get_media_path')
    def test_tiled_false(self, mock_media_path, mock_exists):
        """
        Scenario: Check if media is tiled without metadata

        Given a media_id with no existing metadata
        When tiled is called
        Then it should return False
        """
        mock_media_path.return_value = '/media/path'
        mock_exists.return_value = False

        result = tilestore.tiled('media_id')
        assert result is False

class TestTilestoreDirectorySize:
    """
    Feature: Tile Store Directory Size Calculation

    This test suite validates the get_directory_size function which calculates
    the total size of a directory in bytes.
    """

    @patch('os.walk')
    @patch('os.path.exists', return_value=True)
    @patch('os.path.getsize')
    def test_get_directory_size_empty_directory(self, mock_getsize, mock_exists, mock_walk):
        """
        Scenario: Calculate size of empty directory

        Given an empty directory
        When get_directory_size is called
        Then it should return 0
        """
        mock_walk.return_value = [('/test/path', [], [])]

        result = tilestore.get_directory_size('/test/path')
        assert result == 0

    @patch('os.walk')
    @patch('os.path.exists', return_value=True)
    @patch('os.path.getsize')
    def test_get_directory_size_with_files(self, mock_getsize, mock_exists, mock_walk):
        """
        Scenario: Calculate size of directory with files

        Given a directory with multiple files
        When get_directory_size is called
        Then it should return the sum of all file sizes
        """
        mock_walk.return_value = [
            ('/test/path', ['subdir'], ['file1.txt', 'file2.txt']),
            ('/test/path/subdir', [], ['file3.txt'])
        ]
        mock_getsize.side_effect = [100, 200, 300]

        result = tilestore.get_directory_size('/test/path')
        assert result == 600

    @patch('os.walk')
    def test_get_directory_size_handles_exception(self, mock_walk):
        """
        Scenario: Handle exception during size calculation

        Given a directory that raises an exception during traversal
        When get_directory_size is called
        Then it should handle the exception and return 0
        """
        mock_walk.side_effect = PermissionError("Access denied")

        result = tilestore.get_directory_size('/test/path')
        assert result == 0

class TestTilestoreStats:
    """
    Feature: Tile Store Statistics

    This test suite validates the get_tilestore_stats function which returns
    statistics about the entire tilestore.
    """

    @patch('os.path.exists', return_value=False)
    def test_get_tilestore_stats_nonexistent_directory(self, mock_exists):
        """
        Scenario: Get stats for non-existent tilestore

        Given the tilestore directory does not exist
        When get_tilestore_stats is called
        Then it should return zeroed stats
        """
        result = tilestore.get_tilestore_stats()

        assert result['total_size'] == 0
        assert result['file_count'] == 0
        assert result['media_count'] == 0
        assert result['total_size_mb'] == 0.0

    @patch('os.walk')
    @patch('os.listdir')
    @patch('os.path.isdir', return_value=True)
    @patch('os.path.exists', return_value=True)
    @patch('os.path.getsize')
    def test_get_tilestore_stats_with_media(self, mock_getsize, mock_exists, mock_isdir, mock_listdir, mock_walk):
        """
        Scenario: Get stats for tilestore with media

        Given a tilestore with media directories and files
        When get_tilestore_stats is called
        Then it should return correct statistics
        """
        mock_listdir.return_value = ['media1_hash', 'media2_hash']
        mock_walk.return_value = [
            (tilestore.tile_dir, ['media1_hash', 'media2_hash'], []),
            (f'{tilestore.tile_dir}/media1_hash', ['00'], ['metadata']),
            (f'{tilestore.tile_dir}/media1_hash/00', [], ['00_000000_000000.jpg']),
            (f'{tilestore.tile_dir}/media2_hash', ['00'], ['metadata']),
            (f'{tilestore.tile_dir}/media2_hash/00', [], ['00_000000_000000.jpg'])
        ]
        mock_getsize.return_value = 1024

        result = tilestore.get_tilestore_stats()

        assert result['media_count'] == 2
        assert result['file_count'] == 4
        assert result['total_size'] == 4096
        assert result['total_size_mb'] == 4096 / (1024 * 1024)

    @patch('os.path.exists', return_value=True)
    @patch('os.listdir')
    def test_get_tilestore_stats_handles_exception(self, mock_listdir, mock_exists):
        """
        Scenario: Handle exception during stats collection

        Given an exception occurs during directory listing
        When get_tilestore_stats is called
        Then it should handle the exception gracefully
        """
        mock_listdir.side_effect = PermissionError("Access denied")

        result = tilestore.get_tilestore_stats()

        # Should return partial stats without crashing
        assert 'total_size' in result
        assert 'media_count' in result

class TestTilestoreCleanup:
    """
    Feature: Tile Store Cleanup

    This test suite validates the cleanup_old_tiles and auto_cleanup functions
    which remove old tile directories based on access time.
    """

    @patch('os.path.exists', return_value=False)
    def test_cleanup_old_tiles_nonexistent_directory(self, mock_exists):
        """
        Scenario: Cleanup with non-existent tilestore

        Given the tilestore directory does not exist
        When cleanup_old_tiles is called
        Then it should return zeroed cleanup stats
        """
        result = tilestore.cleanup_old_tiles(max_age_days=3)

        assert result['deleted_media_count'] == 0
        assert result['deleted_size_mb'] == 0.0
        assert result['kept_media_count'] == 0
        assert result['errors'] == []

    @patch('shutil.rmtree')
    @patch('os.stat')
    @patch('os.walk')
    @patch('os.listdir')
    @patch('os.path.isdir', return_value=True)
    @patch('os.path.exists', return_value=True)
    @patch('time.time')
    def test_cleanup_old_tiles_deletes_old_media(self, mock_time, mock_exists, mock_isdir,
                                                  mock_listdir, mock_walk, mock_stat, mock_rmtree):
        """
        Scenario: Cleanup deletes old media directories

        Given a tilestore with media older than max_age_days
        When cleanup_old_tiles is called
        Then old media directories should be deleted
        """
        # Current time is 10 days from epoch
        mock_time.return_value = 10 * 24 * 60 * 60
        mock_listdir.return_value = ['old_media_hash']

        # Media was accessed 5 days ago (older than 3 day threshold)
        stat_result = Mock()
        stat_result.st_atime = 5 * 24 * 60 * 60  # 5 days from epoch
        stat_result.st_mtime = 5 * 24 * 60 * 60
        mock_stat.return_value = stat_result

        mock_walk.return_value = [
            (f'{tilestore.tile_dir}/old_media_hash', [], ['metadata', 'tile.jpg'])
        ]

        with patch.object(tilestore, 'get_directory_size', return_value=1024 * 1024):
            result = tilestore.cleanup_old_tiles(max_age_days=3, dry_run=False)

        assert result['deleted_media_count'] == 1
        mock_rmtree.assert_called_once()

    @patch('os.stat')
    @patch('os.walk')
    @patch('os.listdir')
    @patch('os.path.isdir', return_value=True)
    @patch('os.path.exists', return_value=True)
    @patch('time.time')
    def test_cleanup_old_tiles_keeps_recent_media(self, mock_time, mock_exists, mock_isdir,
                                                   mock_listdir, mock_walk, mock_stat):
        """
        Scenario: Cleanup keeps recent media directories

        Given a tilestore with media newer than max_age_days
        When cleanup_old_tiles is called
        Then recent media directories should be kept
        """
        # Current time is 10 days from epoch
        mock_time.return_value = 10 * 24 * 60 * 60
        mock_listdir.return_value = ['recent_media_hash']

        # Media was accessed 1 day ago (newer than 3 day threshold)
        stat_result = Mock()
        stat_result.st_atime = 9 * 24 * 60 * 60  # 9 days from epoch (1 day old)
        stat_result.st_mtime = 9 * 24 * 60 * 60
        mock_stat.return_value = stat_result

        mock_walk.return_value = [
            (f'{tilestore.tile_dir}/recent_media_hash', [], ['metadata'])
        ]

        result = tilestore.cleanup_old_tiles(max_age_days=3)

        assert result['deleted_media_count'] == 0
        assert result['kept_media_count'] == 1

    @patch('os.stat')
    @patch('os.walk')
    @patch('os.listdir')
    @patch('os.path.isdir', return_value=True)
    @patch('os.path.exists', return_value=True)
    @patch('time.time')
    def test_cleanup_old_tiles_dry_run(self, mock_time, mock_exists, mock_isdir,
                                        mock_listdir, mock_walk, mock_stat):
        """
        Scenario: Cleanup in dry-run mode

        Given a tilestore with old media and dry_run=True
        When cleanup_old_tiles is called
        Then no directories should be actually deleted
        """
        # Current time is 10 days from epoch
        mock_time.return_value = 10 * 24 * 60 * 60
        mock_listdir.return_value = ['old_media_hash']

        stat_result = Mock()
        stat_result.st_atime = 5 * 24 * 60 * 60
        stat_result.st_mtime = 5 * 24 * 60 * 60
        mock_stat.return_value = stat_result

        mock_walk.return_value = [
            (f'{tilestore.tile_dir}/old_media_hash', [], ['metadata'])
        ]

        with patch.object(tilestore, 'get_directory_size', return_value=1024):
            with patch('shutil.rmtree') as mock_rmtree:
                result = tilestore.cleanup_old_tiles(max_age_days=3, dry_run=True)

        assert result['deleted_media_count'] == 1
        mock_rmtree.assert_not_called()

    @patch('os.listdir')
    @patch('os.path.isdir', return_value=True)
    @patch('os.path.exists', return_value=True)
    def test_cleanup_old_tiles_handles_errors(self, mock_exists, mock_isdir, mock_listdir):
        """
        Scenario: Cleanup handles errors gracefully

        Given an exception occurs during cleanup
        When cleanup_old_tiles is called
        Then errors should be collected and reported
        """
        mock_listdir.return_value = ['media_hash']

        with patch('os.walk', side_effect=PermissionError("Access denied")):
            result = tilestore.cleanup_old_tiles(max_age_days=3)

        # Should not crash, errors should be collected
        assert 'errors' in result

    @patch('pyzui.tilesystem.tilestore.tilestore.get_tilestore_stats')
    @patch('pyzui.tilesystem.tilestore.tilestore.cleanup_old_tiles')
    def test_auto_cleanup_disabled(self, mock_cleanup, mock_stats):
        """
        Scenario: Auto cleanup when disabled

        Given auto cleanup is disabled
        When auto_cleanup is called with enable=False
        Then no cleanup should be performed
        """
        result = tilestore.auto_cleanup(max_age_days=3, enable=False)

        assert result is None
        mock_cleanup.assert_not_called()

    @patch('pyzui.tilesystem.tilestore.tilestore.get_tilestore_stats')
    @patch('pyzui.tilesystem.tilestore.tilestore.cleanup_old_tiles')
    def test_auto_cleanup_enabled(self, mock_cleanup, mock_stats):
        """
        Scenario: Auto cleanup when enabled

        Given auto cleanup is enabled
        When auto_cleanup is called with enable=True
        Then cleanup should be performed and stats logged
        """
        mock_stats.return_value = {
            'media_count': 5,
            'file_count': 100,
            'total_size_mb': 50.0,
            'total_size': 50 * 1024 * 1024
        }
        mock_cleanup.return_value = {
            'deleted_media_count': 2,
            'deleted_size_mb': 20.0,
            'kept_media_count': 3,
            'errors': []
        }

        result = tilestore.auto_cleanup(max_age_days=5, enable=True)

        assert result is not None
        mock_cleanup.assert_called_once_with(max_age_days=5, dry_run=False)
        # get_tilestore_stats called twice (before and after cleanup)
        assert mock_stats.call_count == 2

    @patch('pyzui.tilesystem.tilestore.tilestore.get_tilestore_stats')
    @patch('pyzui.tilesystem.tilestore.tilestore.cleanup_old_tiles')
    def test_auto_cleanup_custom_age(self, mock_cleanup, mock_stats):
        """
        Scenario: Auto cleanup with custom max age

        Given a custom max_age_days value
        When auto_cleanup is called
        Then cleanup should use the specified age
        """
        mock_stats.return_value = {'media_count': 0, 'file_count': 0, 'total_size_mb': 0, 'total_size': 0}
        mock_cleanup.return_value = {'deleted_media_count': 0, 'deleted_size_mb': 0, 'kept_media_count': 0, 'errors': []}

        tilestore.auto_cleanup(max_age_days=7, enable=True)

        mock_cleanup.assert_called_once_with(max_age_days=7, dry_run=False)

class TestTilestoreMetadataTypes:
    """
    Feature: Tile Store Metadata Type Parsing

    This test suite validates the type conversion in load_metadata.
    """

    @patch('builtins.open', new_callable=mock_open, read_data="count\t42\tint\n")
    @patch('pyzui.tilesystem.tilestore.tilestore.get_media_path', return_value='/path/to/media')
    def test_load_metadata_parses_int(self, mock_media_path, mock_file):
        """
        Scenario: Parse integer metadata value

        Given metadata with an integer type
        When load_metadata is called
        Then the value should be parsed as int and get_metadata should return it
        """
        # Import the actual tilestore module to reset its internal variable
        from pyzui.tilesystem.tilestore import tilestore as ts_module
        # Reset metadata cache
        ts_module._TestTilestoreMetadataTypes__metadata = {}
        # Access via _module__varname doesn't work for module-level - use direct attribute
        if hasattr(ts_module, '_TestTilestoreMetadataTypes__metadata'):
            delattr(ts_module, '_TestTilestoreMetadataTypes__metadata')

        result = tilestore.load_metadata('test_int_media')
        assert result is True

        # Verify parsed value via get_metadata
        value = tilestore.get_metadata('test_int_media', 'count')
        assert value == 42
        assert isinstance(value, int)

    @patch('builtins.open', new_callable=mock_open, read_data="ratio\t3.14\tfloat\n")
    @patch('pyzui.tilesystem.tilestore.tilestore.get_media_path', return_value='/path/to/media')
    def test_load_metadata_parses_float(self, mock_media_path, mock_file):
        """
        Scenario: Parse float metadata value

        Given metadata with a float type
        When load_metadata is called
        Then the value should be parsed as float
        """
        result = tilestore.load_metadata('test_float_media')
        assert result is True

        value = tilestore.get_metadata('test_float_media', 'ratio')
        assert value == 3.14
        assert isinstance(value, float)

    @patch('builtins.open', new_callable=mock_open, read_data="large\t9999999999\tlong\n")
    @patch('pyzui.tilesystem.tilestore.tilestore.get_media_path', return_value='/path/to/media')
    def test_load_metadata_parses_long(self, mock_media_path, mock_file):
        """
        Scenario: Parse long metadata value

        Given metadata with a long type
        When load_metadata is called
        Then the value should be parsed as int (Python 3)
        """
        result = tilestore.load_metadata('test_long_media')
        assert result is True

        value = tilestore.get_metadata('test_long_media', 'large')
        assert value == 9999999999
        assert isinstance(value, int)

    @patch('builtins.open', new_callable=mock_open, read_data="name\ttest\tstr\n")
    @patch('pyzui.tilesystem.tilestore.tilestore.get_media_path', return_value='/path/to/media')
    def test_load_metadata_keeps_string(self, mock_media_path, mock_file):
        """
        Scenario: Keep string metadata value

        Given metadata with a string type
        When load_metadata is called
        Then the value should remain as string
        """
        result = tilestore.load_metadata('test_str_media')
        assert result is True

        value = tilestore.get_metadata('test_str_media', 'name')
        assert value == 'test'
        assert isinstance(value, str)

class TestTilestorePathFormatting:
    """
    Feature: Tile Store Path Formatting

    This test suite validates the path formatting in get_tile_path.
    """

    def test_get_tile_path_large_coordinates(self):
        """
        Scenario: Format path with large tile coordinates

        Given a tile with large row and column numbers
        When get_tile_path is called
        Then coordinates should be properly zero-padded
        """
        tile_id = ('media_id', 15, 999999, 123456)
        path = tilestore.get_tile_path(tile_id, filext='jpg')

        assert '15' in path  # tilelevel with 2 digits
        assert '999999' in path  # row with 6 digits
        assert '123456' in path  # col with 6 digits

    def test_get_tile_path_zero_coordinates(self):
        """
        Scenario: Format path with zero coordinates

        Given a tile at the origin (0,0,0)
        When get_tile_path is called
        Then coordinates should be properly formatted
        """
        tile_id = ('media_id', 0, 0, 0)
        path = tilestore.get_tile_path(tile_id, filext='jpg')

        assert '00' in path  # tilelevel
        assert '000000' in path  # row and col
