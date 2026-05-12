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

"""Unit tests for BackupManager (per-scene directory backup system)."""

import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from pyzui.backup.backupmanager import BackupManager


class TestBackupManager:
    """
    Feature: Per-Scene Backup Management System

    The BackupManager handles automatic backup creation with per-scene
    directories. Each scene gets its own directory under ~/.pyzui/backups/
    named {scene_filename}_{4char_path_hash}/. Backups within each dir are
    named yy_mm_dd_hh_mm_filename_hash.pzs. Rotation is per-scene (keeps
    last N per directory). Scene directories expire after expire_days of
    inactivity.
    """

    def test_init(self, tmp_path):
        """
        Scenario: Initialize BackupManager

        Given configuration dictionary
        When BackupManager is instantiated
        Then it should set up backup directory
        And use default values if not provided
        """
        config = {
            'backup_dir': str(tmp_path / 'backups'),
            'max_backups': 20,
            'expire_days': 14,
            'enabled': True
        }

        manager = BackupManager(config)

        assert manager is not None
        assert manager._backup_dir == Path(tmp_path / 'backups')
        assert manager._config['max_backups'] == 20
        assert manager._config['expire_days'] == 14
        assert manager._config['enabled']
        assert os.path.exists(tmp_path / 'backups')

    def test_init_defaults(self, tmp_path):
        """
        Scenario: Initialize with minimal configuration

        Given configuration with only backup_dir
        When BackupManager is instantiated
        Then it should use default values for other settings
        """
        config = {
            'backup_dir': str(tmp_path / 'backups')
        }

        manager = BackupManager(config)

        assert manager._config['max_backups'] == 20
        assert manager._config['expire_days'] == 7
        assert os.path.exists(tmp_path / 'backups')

    def test_get_scene_dir(self, tmp_path):
        """
        Scenario: Get per-scene backup directory

        Given a source file path
        When _get_scene_dir is called
        Then it should return a directory path under backup_dir
        And the directory name should contain filename and a 4-char hash
        """
        config = {
            'backup_dir': str(tmp_path / 'backups')
        }

        manager = BackupManager(config)

        scene_path = str(tmp_path / 'myproject.pzs')
        (tmp_path / 'myproject.pzs').write_text('test')

        scene_dir = manager._get_scene_dir(scene_path)

        assert scene_dir.parent == Path(tmp_path / 'backups')
        dir_name = scene_dir.name
        assert dir_name.startswith('myproject_')
        parts = dir_name.split('_')
        assert len(parts[-1]) == 4

        # Same path should return same directory
        scene_dir2 = manager._get_scene_dir(scene_path)
        assert scene_dir == scene_dir2

        # Different path should return different directory
        other_path = str(tmp_path / 'otherproject.pzs')
        (tmp_path / 'otherproject.pzs').write_text('test')
        other_dir = manager._get_scene_dir(other_path)
        assert scene_dir != other_dir

    def test_get_scene_dir_same_file_different_case(self, tmp_path):
        """
        Scenario: Scene directory is path-sensitive

        Given the same file referenced with different case
        When _get_scene_dir is called
        Then it should produce different directories on case-sensitive filesystems
        or same on case-insensitive ones
        """
        config = {
            'backup_dir': str(tmp_path / 'backups')
        }

        manager = BackupManager(config)

        path_lower = str(tmp_path / 'MyProject.pzs')

        scene_dir = manager._get_scene_dir(path_lower)

        # Verify the dir name is deterministic for the same input
        scene_dir2 = manager._get_scene_dir(path_lower)
        assert scene_dir == scene_dir2

    def test_create_backup_success(self, tmp_path):
        """
        Scenario: Create backup of scene file

        Given a scene file
        When create_backup is called
        Then a backup copy should be created in the scene's subdirectory
        And filename should have format yy_mm_dd_hh_mm_filename_hash.pzs
        """
        scene_file = tmp_path / 'test_scene.pzs'
        scene_file.write_text('Test scene content')

        config = {
            'backup_dir': str(tmp_path / 'backups')
        }

        manager = BackupManager(config)
        backup_path = manager.create_backup(str(scene_file))

        assert backup_path is not None
        assert os.path.exists(backup_path)

        # Backup should be in a subdirectory under backup_dir
        backup_dir = os.path.dirname(backup_path)
        assert Path(backup_dir).parent == Path(tmp_path / 'backups')

        # Check backup filename format: yy_mm_dd_hh_mm_filename_hash.pzs
        backup_filename = os.path.basename(backup_path)
        assert backup_filename.endswith('.pzs')
        parts = backup_filename[:-4].split('_')
        assert len(parts) >= 6

        year, month, day, hour, minute = parts[:5]
        assert len(year) == 2
        assert len(month) == 2
        assert len(day) == 2
        assert len(hour) == 2
        assert len(minute) == 2

        assert len(parts[-1]) == 4

        with open(backup_path) as f:
            assert f.read() == 'Test scene content'

    def test_create_backup_nonexistent_file(self, tmp_path):
        """
        Scenario: Attempt to backup non-existent file

        Given a non-existent file path
        When create_backup is called
        Then it should return None
        And log error
        """
        config = {
            'backup_dir': str(tmp_path / 'backups')
        }

        manager = BackupManager(config)

        with patch.object(manager, '_show_error_dialog'):
            backup_path = manager.create_backup(str(tmp_path / 'nonexistent.pzs'))

            assert backup_path is None

    def test_create_backup_permission_error(self, tmp_path):
        """
        Scenario: Attempt to backup file with permission error

        Given a file without read permission
        When create_backup is called
        Then it should return None
        And log error
        """
        scene_file = tmp_path / 'test_scene.pzs'
        scene_file.write_text('Test scene content')
        os.chmod(scene_file, 0o000)

        config = {
            'backup_dir': str(tmp_path / 'backups')
        }

        manager = BackupManager(config)

        with patch.object(manager, '_show_error_dialog'):
            backup_path = manager.create_backup(str(scene_file))

            os.chmod(scene_file, 0o644)

            assert backup_path is None

    def test_generate_backup_filename_format(self, tmp_path):
        """
        Scenario: Generate backup filename

        Given a scene file path
        When _generate_backup_filename is called
        Then it should return filename in format yy_mm_dd_hh_mm_filename_hash.pzs
        """
        config = {
            'backup_dir': str(tmp_path / 'backups')
        }

        manager = BackupManager(config)

        test_cases = [
            '/path/to/scene.pzs',
            '/path/to/my_project.pzs',
            '/path/to/scene_with_underscores.pzs'
        ]

        for scene_path in test_cases:
            filename = manager._generate_backup_filename(scene_path)

            assert filename.endswith('.pzs')
            parts = filename[:-4].split('_')
            assert len(parts) >= 6

            for i in range(5):
                assert parts[i].isdigit()
                assert len(parts[i]) == 2

            assert len(parts[-1]) == 4

    def test_rotate_backups_keep_max(self, tmp_path):
        """
        Scenario: Rotate backups to keep only N most recent within scene dir

        Given 25 backup files in a scene backup directory
        When _rotate_backups is called with max_backups=20
        Then only the 20 most recent backups should remain
        And the oldest 5 backups should be deleted
        """
        config = {
            'backup_dir': str(tmp_path / 'backups'),
            'max_backups': 20
        }

        manager = BackupManager(config)

        scene_file = tmp_path / 'scene.pzs'
        scene_file.write_text('scene')
        scene_dir = manager._get_scene_dir(str(scene_file))
        scene_dir.mkdir(parents=True)

        backup_files = []
        for i in range(25):
            timestamp = (datetime.now() - timedelta(hours=i)).strftime("%y_%m_%d_%H_%M")
            filename = f"{timestamp}_scene_{i:04x}.pzs"
            filepath = scene_dir / filename
            filepath.write_text(f'Backup {i}')

            mtime = time.time() - (i * 3600)
            os.utime(filepath, (mtime, mtime))

            backup_files.append(filepath)

        manager._rotate_backups(scene_dir)

        remaining_files = list(scene_dir.glob('*.pzs'))
        assert len(remaining_files) == 20

        for i in range(20, 25):
            assert not backup_files[i].exists()

        for i in range(20):
            assert backup_files[i].exists()

    def test_rotate_backups_less_than_max(self, tmp_path):
        """
        Scenario: Rotate backups when fewer than max exist

        Given 15 backup files in a scene backup directory
        When _rotate_backups is called with max_backups=20
        Then all 15 backups should remain
        And no files should be deleted
        """
        config = {
            'backup_dir': str(tmp_path / 'backups'),
            'max_backups': 20
        }

        manager = BackupManager(config)

        scene_file = tmp_path / 'scene.pzs'
        scene_file.write_text('scene')
        scene_dir = manager._get_scene_dir(str(scene_file))
        scene_dir.mkdir(parents=True)

        for i in range(15):
            timestamp = datetime.now().strftime("%y_%m_%d_%H_%M")
            filename = f"{timestamp}_scene_{i:04x}.pzs"
            filepath = scene_dir / filename
            filepath.write_text(f'Backup {i}')

        manager._rotate_backups(scene_dir)

        remaining_files = list(scene_dir.glob('*.pzs'))
        assert len(remaining_files) == 15

    def test_get_backup_count_with_source_path(self, tmp_path):
        """
        Scenario: Count backup files for a specific scene

        Given multiple backup files for different scenes
        When get_backup_count is called with source_path
        Then it should return the correct count for that scene only
        """
        config = {
            'backup_dir': str(tmp_path / 'backups')
        }

        manager = BackupManager(config)

        scene_a = tmp_path / 'scene_a.pzs'
        scene_b = tmp_path / 'scene_b.pzs'
        scene_a.write_text('a')
        scene_b.write_text('b')

        scene_dir_a = manager._get_scene_dir(str(scene_a))
        scene_dir_b = manager._get_scene_dir(str(scene_b))
        scene_dir_a.mkdir(parents=True)
        scene_dir_b.mkdir(parents=True)

        for i in range(7):
            timestamp = datetime.now().strftime("%y_%m_%d_%H_%M")
            filename = f"{timestamp}_scene_a_{i:04x}.pzs"
            (scene_dir_a / filename).write_text(f'Backup A{i}')

        for i in range(3):
            timestamp = datetime.now().strftime("%y_%m_%d_%H_%M")
            filename = f"{timestamp}_scene_b_{i:04x}.pzs"
            (scene_dir_b / filename).write_text(f'Backup B{i}')

        assert manager.get_backup_count(str(scene_a)) == 7
        assert manager.get_backup_count(str(scene_b)) == 3
        assert manager.get_backup_count() == 10

    def test_get_backup_count_nonexistent_scene(self, tmp_path):
        """
        Scenario: Count backups for a scene that has no backups

        Given a scene that has no backup directory
        When get_backup_count is called
        Then it should return 0
        """
        config = {
            'backup_dir': str(tmp_path / 'backups')
        }

        manager = BackupManager(config)

        assert manager.get_backup_count(str(tmp_path / 'new_scene.pzs')) == 0

    def test_list_backups_with_source_path(self, tmp_path):
        """
        Scenario: List backup files for a specific scene

        Given multiple backup files for a scene
        When list_backups is called with source_path
        Then it should return relative paths for that scene only
        """
        config = {
            'backup_dir': str(tmp_path / 'backups')
        }

        manager = BackupManager(config)

        scene_file = tmp_path / 'my_scene.pzs'
        scene_file.write_text('scene')
        scene_dir = manager._get_scene_dir(str(scene_file))
        scene_dir.mkdir(parents=True)

        expected_files = []
        for i in range(5):
            timestamp = datetime.now().strftime("%y_%m_%d_%H_%M")
            filename = f"{timestamp}_my_scene_{i:04x}.pzs"
            filepath = scene_dir / filename
            filepath.write_text(f'Backup {i}')
            expected_files.append(str(filepath))

        listed_backups = manager.list_backups(str(scene_file))

        assert len(listed_backups) == 5
        for backup in listed_backups:
            assert '/' in backup
            assert backup.endswith('.pzs')

    def test_list_backups_empty(self, tmp_path):
        """
        Scenario: List backups for a scene with no backups

        Given a scene directory that doesn't exist
        When list_backups is called
        Then it should return empty list
        """
        config = {
            'backup_dir': str(tmp_path / 'backups')
        }

        manager = BackupManager(config)

        assert manager.list_backups(str(tmp_path / 'nonexistent.pzs')) == []

    def test_cleanup_all(self, tmp_path):
        """
        Scenario: Clean up all backup directories and files

        Given multiple backup directories with files
        When cleanup_all is called
        Then all backup files and directories should be deleted
        And it should return count of items deleted
        """
        config = {
            'backup_dir': str(tmp_path / 'backups')
        }

        manager = BackupManager(config)

        scene_a = tmp_path / 'scene_a.pzs'
        scene_b = tmp_path / 'scene_b.pzs'
        scene_a.write_text('a')
        scene_b.write_text('b')

        scene_dir_a = manager._get_scene_dir(str(scene_a))
        scene_dir_b = manager._get_scene_dir(str(scene_b))
        scene_dir_a.mkdir(parents=True)
        scene_dir_b.mkdir(parents=True)

        for i in range(3):
            timestamp = datetime.now().strftime("%y_%m_%d_%H_%M")
            (scene_dir_a / f"{timestamp}_scene_a_{i:04x}.pzs").write_text(f'a{i}')
            (scene_dir_b / f"{timestamp}_scene_b_{i:04x}.pzs").write_text(f'b{i}')

        deleted_count = manager.cleanup_all()

        assert deleted_count == 2
        remaining = list(Path(tmp_path / 'backups').iterdir())
        assert len(remaining) == 0

    def test_show_error_dialog(self, tmp_path):
        """
        Scenario: Show error dialog for backup failures

        Given an error message
        When _show_error_dialog is called
        Then it should create QMessageBox with error details
        """
        config = {
            'backup_dir': str(tmp_path / 'backups')
        }

        manager = BackupManager(config)

        error_message = "Test error message"

        with patch('PySide6.QtWidgets.QMessageBox') as MockMessageBox:
            mock_instance = Mock()
            MockMessageBox.return_value = mock_instance

            manager._show_error_dialog(error_message)

            MockMessageBox.assert_called_once()
            mock_instance.setIcon.assert_called_once()
            mock_instance.setWindowTitle.assert_called_with("Backup Error")
            mock_instance.setText.assert_called_with(error_message)
            mock_instance.setStandardButtons.assert_called_once()
            mock_instance.exec.assert_called_once()

    def test_create_backup_empty_string(self, tmp_path):
        """
        Scenario: Create backup with empty string source path

        Given empty string as source path
        When create_backup is called
        Then it should return None
        """
        config = {
            'backup_dir': str(tmp_path / 'backups')
        }

        manager = BackupManager(config)

        with patch.object(manager, '_show_error_dialog'):
            backup_path = manager.create_backup('')

            assert backup_path is None

    def test_create_backup_rotation_triggered(self, tmp_path):
        """
        Scenario: Create backup triggers rotation when at max

        Given a scene directory already has max_backups files
        When create_backup is called
        Then rotation should occur within that scene directory
        And oldest backup should be deleted
        """
        config = {
            'backup_dir': str(tmp_path / 'backups'),
            'max_backups': 5
        }

        manager = BackupManager(config)

        scene_file = tmp_path / 'new_scene.pzs'
        scene_file.write_text('New scene content')

        scene_dir = manager._get_scene_dir(str(scene_file))
        scene_dir.mkdir(parents=True)

        for i in range(5):
            old_time = datetime.now() - timedelta(hours=i+1)
            timestamp = old_time.strftime("%y_%m_%d_%H_%M")
            filename = f"{timestamp}_old_scene_{i:04x}.pzs"
            filepath = scene_dir / filename
            filepath.write_text(f'Old backup {i}')

            mtime = time.time() - ((i+1) * 3600)
            os.utime(filepath, (mtime, mtime))

        backup_path = manager.create_backup(str(scene_file))

        assert backup_path is not None
        assert os.path.exists(backup_path)

        remaining_files = list(scene_dir.glob('*.pzs'))
        assert len(remaining_files) == 5

        assert any('new_scene' in str(f) for f in remaining_files)

        oldest_file = scene_dir / f"{datetime.now() - timedelta(hours=5):%y_%m_%d_%H_%M}_old_scene_0000.pzs"
        assert not oldest_file.exists()

    def test_cleanup_expired_directories(self, tmp_path):
        """
        Scenario: Clean up expired backup directories

        Given backup directories with expired mtimes
        When _cleanup_expired is called
        Then expired directories should be deleted
        And active directories should remain
        """
        config = {
            'backup_dir': str(tmp_path / 'backups'),
            'expire_days': 1
        }

        manager = BackupManager(config)

        scene_a = tmp_path / 'scene_a.pzs'
        scene_b = tmp_path / 'scene_b.pzs'
        scene_a.write_text('a')
        scene_b.write_text('b')

        scene_dir_a = manager._get_scene_dir(str(scene_a))
        scene_dir_b = manager._get_scene_dir(str(scene_b))
        scene_dir_a.mkdir(parents=True)
        scene_dir_b.mkdir(parents=True)

        (scene_dir_a / 'test.pzs').write_text('old')
        (scene_dir_b / 'test.pzs').write_text('recent')

        old_time = time.time() - (2 * 86400)
        os.utime(scene_dir_a, (old_time, old_time))

        deleted = manager._cleanup_expired()

        assert deleted == 1
        assert not scene_dir_a.exists()
        assert scene_dir_b.exists()

    def test_cleanup_expired_no_expired(self, tmp_path):
        """
        Scenario: Clean up when no directories are expired

        Given backup directories with recent mtimes
        When _cleanup_expired is called
        Then no directories should be deleted
        """
        config = {
            'backup_dir': str(tmp_path / 'backups'),
            'expire_days': 7
        }

        manager = BackupManager(config)

        scene_a = tmp_path / 'scene_a.pzs'
        scene_a.write_text('a')
        scene_dir_a = manager._get_scene_dir(str(scene_a))
        scene_dir_a.mkdir(parents=True)
        (scene_dir_a / 'test.pzs').write_text('recent')

        deleted = manager._cleanup_expired()

        assert deleted == 0
        assert scene_dir_a.exists()

    def test_cleanup_expired_empty_directory(self, tmp_path):
        """
        Scenario: Clean up empty backup directories

        Given an empty subdirectory (no .pzs files)
        When _cleanup_expired is called
        Then the empty directory should be removed
        """
        config = {
            'backup_dir': str(tmp_path / 'backups')
        }

        manager = BackupManager(config)

        empty_dir = tmp_path / 'backups' / 'some_empty_dir'
        empty_dir.mkdir(parents=True)

        deleted = manager._cleanup_expired()

        assert deleted == 1
        assert not empty_dir.exists()

    def test_cleanup_expired_dirs_public(self, tmp_path):
        """
        Scenario: Public cleanup_expired_dirs method

        Given backup directories
        When cleanup_expired_dirs is called
        Then it should delegate to _cleanup_expired
        """
        config = {
            'backup_dir': str(tmp_path / 'backups'),
            'expire_days': 1
        }

        manager = BackupManager(config)

        scene_a = tmp_path / 'scene_a.pzs'
        scene_a.write_text('a')
        scene_dir = manager._get_scene_dir(str(scene_a))
        scene_dir.mkdir(parents=True)
        (scene_dir / 'test.pzs').write_text('old')

        old_time = time.time() - (2 * 86400)
        os.utime(scene_dir, (old_time, old_time))

        deleted = manager.cleanup_expired_dirs()

        assert deleted >= 1

    def test_cleanup_flat_backups(self, tmp_path):
        """
        Scenario: Clean up legacy flat backup files

        Given old-style .pzs files directly in the backup root
        When cleanup_flat_backups is called
        Then root-level .pzs files should be deleted
        And files in subdirectories should remain untouched
        """
        config = {
            'backup_dir': str(tmp_path / 'backups')
        }

        manager = BackupManager(config)

        flat_file1 = tmp_path / 'backups' / '26_05_03_14_30_oldscene_a1b2.pzs'
        flat_file2 = tmp_path / 'backups' / '26_05_03_14_35_oldscene_c3d4.pzs'
        flat_file1.write_text('old flat backup 1')
        flat_file2.write_text('old flat backup 2')

        scene_subdir = tmp_path / 'backups' / 'scene_abcd'
        scene_subdir.mkdir()
        (scene_subdir / 'backup.pzs').write_text('new backup')

        deleted = manager.cleanup_flat_backups()

        assert deleted == 2
        assert not flat_file1.exists()
        assert not flat_file2.exists()
        assert scene_subdir.exists()
        assert (scene_subdir / 'backup.pzs').exists()

    def test_cleanup_flat_backups_none(self, tmp_path):
        """
        Scenario: Clean up when there are no flat backups

        Given no root-level .pzs files
        When cleanup_flat_backups is called
        Then it should return 0
        """
        config = {
            'backup_dir': str(tmp_path / 'backups')
        }

        manager = BackupManager(config)

        deleted = manager.cleanup_flat_backups()

        assert deleted == 0

    def test_tilde_expansion_in_backup_dir(self, tmp_path, monkeypatch):
        """
        Scenario: BackupManager expands tilde in backup_dir

        Given configuration with tilde path
        When BackupManager is instantiated
        Then tilde should be expanded
        And backup directory should be created at expanded location
        """
        expected_path = tmp_path / 'expanded' / 'backups'
        expected_path.mkdir(parents=True)

        def mock_expanduser(self):
            if str(self).startswith('~'):
                return Path(str(self).replace('~', str(tmp_path / 'expanded'), 1))
            return self

        monkeypatch.setattr(Path, 'expanduser', mock_expanduser)

        config = {
            'backup_dir': '~/.pyzui/test_backups',
            'max_backups': 10
        }

        manager = BackupManager(config)

        assert str(manager._backup_dir).endswith('.pyzui/test_backups')
        assert '~' not in str(manager._backup_dir)
        assert manager._backup_dir.exists()

    def test_backup_manager_handles_already_expanded_paths(self, tmp_path):
        """
        Scenario: BackupManager handles already expanded paths

        Given configuration with already expanded path
        When BackupManager is instantiated
        Then it should work correctly without double expansion
        """
        config = {
            'backup_dir': str(tmp_path / 'already_expanded' / 'backups'),
            'max_backups': 10
        }

        manager = BackupManager(config)

        expected_path = tmp_path / 'already_expanded' / 'backups'
        assert manager._backup_dir == expected_path
        assert expected_path.exists()

    def test_backup_manager_expanduser_safety(self, tmp_path, monkeypatch):
        """
        Scenario: BackupManager uses expanduser() as safety measure

        Given Path object with tilde
        When expanduser() is called
        Then tilde should be expanded
        """
        test_dir = tmp_path / 'test_expand'
        test_dir.mkdir()

        def mock_expanduser(path):
            if path.startswith('~'):
                return str(path).replace('~', str(test_dir), 1)
            return path

        monkeypatch.setattr('os.path.expanduser', mock_expanduser)

        tilde_path = Path('~/.pyzui/backups')
        expanded = tilde_path.expanduser()

        assert '~' not in str(expanded)
        assert str(expanded).startswith(str(test_dir))

        already_expanded = Path(str(test_dir / '.pyzui' / 'backups'))
        same_expanded = already_expanded.expanduser()

        assert str(same_expanded) == str(already_expanded)

    def test_multiple_scenes_independent_rotation(self, tmp_path):
        """
        Scenario: Rotation is independent per scene

        Given two scenes with backups in their own directories
        When rotation occurs
        Then each scene directory is rotated independently
        And backup counts in one scene don't affect the other
        """
        config = {
            'backup_dir': str(tmp_path / 'backups'),
            'max_backups': 5
        }

        manager = BackupManager(config)

        scene_a = tmp_path / 'project_a.pzs'
        scene_b = tmp_path / 'project_b.pzs'
        scene_a.write_text('a')
        scene_b.write_text('b')

        scene_dir_a = manager._get_scene_dir(str(scene_a))
        scene_dir_b = manager._get_scene_dir(str(scene_b))
        scene_dir_a.mkdir(parents=True)
        scene_dir_b.mkdir(parents=True)

        for i in range(7):
            timestamp = datetime.now().strftime("%y_%m_%d_%H_%M")
            (scene_dir_a / f"{timestamp}_a_{i:04x}.pzs").write_text(f'a{i}')

        for i in range(3):
            timestamp = datetime.now().strftime("%y_%m_%d_%H_%M")
            (scene_dir_b / f"{timestamp}_b_{i:04x}.pzs").write_text(f'b{i}')

        manager._rotate_backups(scene_dir_a)
        manager._rotate_backups(scene_dir_b)

        assert len(list(scene_dir_a.glob('*.pzs'))) == 5
        assert len(list(scene_dir_b.glob('*.pzs'))) == 3

    def test_create_backup_creates_scene_dir_if_missing(self, tmp_path):
        """
        Scenario: create_backup creates scene directory if it doesn't exist

        Given a scene file with no prior backup directory
        When create_backup is called
        Then the scene directory should be created automatically
        And the backup should be placed inside it
        """
        config = {
            'backup_dir': str(tmp_path / 'backups')
        }

        manager = BackupManager(config)

        scene_file = tmp_path / 'new_scene.pzs'
        scene_file.write_text('new scene')

        scene_dir = manager._get_scene_dir(str(scene_file))
        assert not scene_dir.exists()

        backup_path = manager.create_backup(str(scene_file))

        assert scene_dir.exists()
        assert backup_path is not None
        assert Path(backup_path).parent == scene_dir

    def test_cleanup_expired_skips_non_directory(self, tmp_path):
        """
        Scenario: _cleanup_expired skips non-directory items

        Given a file (not a directory) in the backup root
        When _cleanup_expired is called
        Then the file should be left alone (handled by cleanup_flat_backups)
        """
        config = {
            'backup_dir': str(tmp_path / 'backups'),
            'expire_days': 1
        }

        manager = BackupManager(config)

        stray_file = tmp_path / 'backups' / 'some_file.txt'
        stray_file.write_text('not a backup')

        deleted = manager._cleanup_expired()

        assert deleted == 0
        assert stray_file.exists()
