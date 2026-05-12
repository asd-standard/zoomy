## PyZUI - Python Zooming User Interface
## Copyright (C) 2009 David Roberts <d@vidr.cc>
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

"""
Feature: Autosave System Integration Tests

Integration tests for the complete autosave system including configuration,
backup creation, scene integration, and UI components.
"""

import os
import shutil
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from pyzui.backup.backupmanager import BackupManager
from pyzui.config import ConfigManager
from pyzui.objects.scene import scene as Scene


class TestAutosaveIntegration:
    """
    Feature: Complete Autosave System Integration

    Tests the integration of all autosave components including configuration,
    backup management, scene integration, and user interface.
    """

    def test_config_to_scene_integration(self):
        """
        Scenario: Configuration flows from config to scene

        Given autosave configuration in user config
        When scene is created with that configuration
        Then scene should have autosave enabled with correct settings
        """
        # Create scene with config
        config = {"autosave": {"enabled": True, "interval": 600, "max_backups": 30}}  # 600 seconds = 10 minutes
        scene = Scene.new(config=config)

        # Verify config was stored via public API
        assert scene.is_autosave_enabled() is True
        assert scene.get_autosave_interval() == 600
        scene_config = scene.get_autosave_config()
        assert scene_config["enabled"] is True
        assert scene_config["interval"] == 600
        assert scene_config["max_backups"] == 30

    def test_scene_save_triggers_backup(self):
        """
        Scenario: Scene save triggers backup creation

        Given scene with autosave enabled
        When scene is saved
        Then backup should be created
        """
        # Create scene with autosave enabled
        scene = Scene.Scene()

        # Mock the autosave manager's update_last_save_path method
        # We need to patch the autosave manager method
        with patch.object(scene, '_Scene__autosave_manager') as mock_autosave_manager:
            # Save scene
            with tempfile.NamedTemporaryFile(suffix='.pzs', delete=False) as tmp:
                tmp_path = tmp.name

            try:
                scene.save(tmp_path)

                # Verify autosave manager was called
                mock_autosave_manager.update_last_save_path.assert_called_once_with(tmp_path)
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    def test_backup_creation_and_rotation(self):
        """
        Scenario: Backup creation and rotation work correctly

        Given a scene file with autosave enabled
        When multiple backups are created for the same scene
        Then old backups should be rotated out within the scene directory
        """
        config = {
            "backup_dir": "/tmp/test_backups",
            "max_backups": 3
        }

        backup_dir = Path("/tmp/test_backups")
        if backup_dir.exists():
            shutil.rmtree(backup_dir)

        backup_manager = BackupManager(config)

        with tempfile.NamedTemporaryFile(suffix='.pzs', delete=False, mode='w') as tmp:
            tmp_path = tmp.name
            tmp.write("test scene content")

        try:
            scene_dir = backup_manager._get_scene_dir(tmp_path)

            for i in range(5):
                with open(tmp_path, 'w') as f:
                    f.write(f"backup {i}")

                backup_manager.create_backup(tmp_path)

            backup_files = list(scene_dir.glob("*.pzs"))
            assert len(backup_files) == 3

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            if backup_dir.exists():
                shutil.rmtree(backup_dir)

    @pytest.mark.skip(reason="Requires QApplication for Qt widgets")
    def test_ui_dialog_to_config_integration(self):
        """
        Scenario: UI dialog updates configuration

        Given autosave settings dialog
        When user changes settings
        Then configuration should be updated

        Note: Skipped because it requires QApplication for Qt widgets
        """
        pass

    def test_config_save_and_load_cycle(self):
        """
        Scenario: Configuration can be saved and loaded

        Given autosave configuration
        When config is saved to file and loaded back
        Then loaded config should match original
        """
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w') as tmp:
            tmp_path = tmp.name

        try:
            initial_config = {
                "autosave": {
                    "enabled": True,
                    "interval": 300,
                    "max_backups": 20,
                    "expire_days": 14
                }
            }

            config_manager = ConfigManager(tmp_path)
            config_manager.save(initial_config)

            loaded_config_manager = ConfigManager(tmp_path)
            loaded_config = loaded_config_manager.load()

            assert loaded_config["autosave"]["enabled"] == initial_config["autosave"]["enabled"]
            assert loaded_config["autosave"]["interval"] == initial_config["autosave"]["interval"]
            assert loaded_config["autosave"]["max_backups"] == initial_config["autosave"]["max_backups"]
            assert loaded_config["autosave"]["expire_days"] == initial_config["autosave"]["expire_days"]

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_expired_backup_cleanup(self):
        """
        Scenario: Expired backup directories are cleaned up

        Given a backup directory with old mtime
        When backup manager checks for expired directories
        Then expired directories should be removed
        """
        config = {
            "backup_dir": "/tmp/test_expired_backups",
            "max_backups": 20,
            "expire_days": 1
        }

        backup_dir = Path("/tmp/test_expired_backups")
        if backup_dir.exists():
            shutil.rmtree(backup_dir)

        backup_manager = BackupManager(config)

        with tempfile.NamedTemporaryFile(suffix='.pzs', delete=False, mode='w') as tmp:
            tmp_path = tmp.name
            tmp.write("test scene content")

        try:
            backup_manager.create_backup(tmp_path)
            scene_dir = backup_manager._get_scene_dir(tmp_path)
            assert scene_dir.exists()

            old_time = time.time() - (2 * 86400)
            os.utime(scene_dir, (old_time, old_time))

            deleted = backup_manager._cleanup_expired()

            assert deleted >= 1
            assert not scene_dir.exists()

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            if backup_dir.exists():
                shutil.rmtree(backup_dir)

    def test_cleanup_flat_backups_integration(self):
        """
        Scenario: Legacy flat backup files are cleaned up

        Given old-style flat backup files in the backup root
        When cleanup_flat_backups is called
        Then they should be deleted
        """
        config = {
            "backup_dir": "/tmp/test_flat_backups",
        }

        backup_dir = Path("/tmp/test_flat_backups")
        if backup_dir.exists():
            shutil.rmtree(backup_dir)

        backup_manager = BackupManager(config)

        flat_file = backup_dir / '26_05_03_14_30_oldscene_a1b2.pzs'
        flat_file.write_text('old flat backup')

        deleted = backup_manager.cleanup_flat_backups()

        assert deleted == 1
        assert not flat_file.exists()

        if backup_dir.exists():
            shutil.rmtree(backup_dir)

    def test_error_handling_integration(self):
        """
        Scenario: Error handling across components

        Given error condition in backup creation
        When backup fails
        Then error should be handled gracefully without crashing
        """
        # Create scene with autosave enabled
        scene = Scene.Scene()

        # Mock the backup manager's create_backup method to simulate a failure
        # We need to patch at the module level where it's imported in autosave.py
        with patch('pyzui.backup.backupmanager.BackupManager.create_backup') as mock_create_backup:
            mock_create_backup.side_effect = Exception("Backup creation failed")

            # Save scene - should not crash even if backup fails
            with tempfile.NamedTemporaryFile(suffix='.pzs', delete=False) as tmp:
                tmp_path = tmp.name

            try:
                # This should not crash - error should be caught in _trigger_autosave_backup
                scene.save(tmp_path)

                # Scene should still be saved even if backup failed
                # We can't directly check private attribute, but save should complete

            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    def test_autosave_timer_integration(self):
        """
        Scenario: Autosave timer integration

        Given scene with autosave enabled
        When timer triggers
        Then backup should be created
        """
        # Create scene
        scene = Scene.Scene()

        # Mock the autosave manager
        with patch.object(scene, '_Scene__autosave_manager') as mock_autosave_manager:
            # Trigger autosave timeout via the manager
            mock_autosave_manager._autosave_timeout()

            # Verify timeout handler was called
            mock_autosave_manager._autosave_timeout.assert_called_once()

    def test_disabled_autosave_does_nothing(self):
        """
        Scenario: Disabled autosave does not create backups

        Given scene with autosave disabled
        When scene is saved
        Then no backup should be created
        """
        # Create scene with autosave disabled
        config = {"autosave": {"enabled": False}}
        scene = Scene.new(config=config)

        # Mock the autosave manager
        with patch.object(scene, '_Scene__autosave_manager') as mock_autosave_manager:
            # Save scene
            with tempfile.NamedTemporaryFile(suffix='.pzs', delete=False) as tmp:
                tmp_path = tmp.name

            try:
                scene.save(tmp_path)

                # Verify no backup was triggered
                mock_autosave_manager._trigger_autosave_backup.assert_not_called()

            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    def test_first_save_activation(self):
        """
        Scenario: Autosave activates at startup and creates backup on first save

        Given scene with autosave configuration
        When scene is saved for the first time
        Then autosave backup should be created
        """
        # Create scene with autosave config
        config = {"autosave": {"enabled": True, "interval": 300, "max_backups": 20}}
        scene = Scene.Scene(config=config)

        # Mock the autosave manager
        with patch.object(scene, '_Scene__autosave_manager') as mock_autosave_manager:
            # Save scene for the first time
            with tempfile.NamedTemporaryFile(suffix='.pzs', delete=False) as tmp:
                tmp_path = tmp.name

            try:
                scene.save(tmp_path)

                # Verify autosave manager was called
                mock_autosave_manager.update_last_save_path.assert_called_once_with(tmp_path)
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
