import pytest
import os
import hashlib
from unittest.mock import Mock, patch, mock_open
from pyzui import tilestore

class TestTilestoreModule:
    """Test suite for tilestore module functions."""

    def test_tile_dir_exists(self):
        """Test that tile_dir variable is set."""
        assert tilestore.tile_dir is not None
        assert isinstance(tilestore.tile_dir, str)

    def test_disk_lock_exists(self):
        """Test that disk_lock is available."""
        assert tilestore.disk_lock is not None

    def test_get_media_path(self):
        """Test get_media_path returns valid path."""
        media_id = "test_media"
        path = tilestore.get_media_path(media_id)
        assert isinstance(path, str)
        assert len(path) > 0

    def test_get_media_path_consistent(self):
        """Test get_media_path returns same path for same media_id."""
        media_id = "test_media"
        path1 = tilestore.get_media_path(media_id)
        path2 = tilestore.get_media_path(media_id)
        assert path1 == path2

    def test_get_media_path_different_ids(self):
        """Test get_media_path returns different paths for different media_ids."""
        path1 = tilestore.get_media_path("media1")
        path2 = tilestore.get_media_path("media2")
        assert path1 != path2

    def test_get_media_path_uses_hash(self):
        """Test get_media_path uses SHA1 hash."""
        media_id = "test_media"
        expected_hash = hashlib.sha1(media_id.encode('utf-8')).hexdigest()
        path = tilestore.get_media_path(media_id)
        assert expected_hash in path

    def test_get_tile_path_basic(self):
        """Test get_tile_path returns valid path."""
        tile_id = ('media_id', 0, 0, 0)
        with patch.object(tilestore, 'get_metadata', return_value='jpg'):
            path = tilestore.get_tile_path(tile_id)
            assert isinstance(path, str)
            assert '.jpg' in path

    def test_get_tile_path_with_filext(self):
        """Test get_tile_path with explicit filext."""
        tile_id = ('media_id', 1, 2, 3)
        path = tilestore.get_tile_path(tile_id, filext='png')
        assert '.png' in path
        assert '01' in path  # tilelevel
        assert '000002' in path  # row
        assert '000003' in path  # col

    def test_get_tile_path_with_prefix(self):
        """Test get_tile_path with custom prefix."""
        tile_id = ('media_id', 0, 0, 0)
        prefix = '/custom/path'
        path = tilestore.get_tile_path(tile_id, prefix=prefix, filext='jpg')
        assert path.startswith(prefix)

    @patch('os.makedirs')
    @patch('os.path.exists', return_value=False)
    def test_get_tile_path_mkdirp(self, mock_exists, mock_makedirs):
        """Test get_tile_path creates directories when mkdirp=True."""
        tile_id = ('media_id', 0, 0, 0)
        tilestore.get_tile_path(tile_id, mkdirp=True, filext='jpg')
        mock_makedirs.assert_called_once()

    @patch('builtins.open', new_callable=mock_open, read_data="width\t100\tint\nheight\t200\tint\n")
    @patch('os.path.join')
    def test_load_metadata_success(self, mock_join, mock_file):
        """Test load_metadata successfully loads metadata."""
        mock_join.return_value = '/path/to/metadata'
        result = tilestore.load_metadata('media_id')
        assert result is True

    @patch('builtins.open', side_effect=IOError)
    def test_load_metadata_failure(self, mock_file):
        """Test load_metadata returns False on IOError."""
        result = tilestore.load_metadata('nonexistent_media')
        assert result is False

    @patch('builtins.open', new_callable=mock_open, read_data="key1\tvalue1\tstr\nkey2\t42\tint\n")
    @patch('os.path.join')
    def test_get_metadata(self, mock_join, mock_file):
        """Test get_metadata returns correct value."""
        mock_join.return_value = '/path/to/metadata'
        tilestore._TileStore__metadata = {}  # Reset metadata
        value = tilestore.get_metadata('media_id', 'key2')
        # Metadata should be loaded and parsed

    def test_get_metadata_nonexistent_key(self):
        """Test get_metadata returns None for nonexistent key."""
        tilestore._TileStore__metadata = {}
        with patch.object(tilestore, 'load_metadata', return_value=True):
            tilestore._TileStore__metadata = {'media_id': {}}
            value = tilestore.get_metadata('media_id', 'nonexistent_key')
            assert value is None

    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.join')
    def test_write_metadata(self, mock_join, mock_file):
        """Test write_metadata writes metadata correctly."""
        mock_join.return_value = '/path/to/metadata'
        tilestore.write_metadata('media_id', width=100, height=200)
        mock_file.assert_called()

    @patch('os.path.exists')
    @patch.object(tilestore, 'get_tile_path')
    @patch.object(tilestore, 'get_media_path')
    def test_tiled_true(self, mock_media_path, mock_tile_path, mock_exists):
        """Test tiled returns True when metadata and tile exist."""
        mock_media_path.return_value = '/media/path'
        mock_tile_path.return_value = '/tile/path'
        mock_exists.return_value = True

        result = tilestore.tiled('media_id')
        assert result is True

    @patch('os.path.exists')
    @patch.object(tilestore, 'get_media_path')
    def test_tiled_false(self, mock_media_path, mock_exists):
        """Test tiled returns False when metadata doesn't exist."""
        mock_media_path.return_value = '/media/path'
        mock_exists.return_value = False

        result = tilestore.tiled('media_id')
        assert result is False
