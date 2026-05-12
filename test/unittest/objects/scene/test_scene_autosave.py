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
Feature: Scene Autosave Functionality

The Scene class provides autosave functionality that automatically creates
backups of scene files at configurable intervals after the first manual save.
"""

import os
import tempfile
from unittest.mock import Mock, patch

from pyzui.objects.scene import scene as Scene


class TestSceneAutosave:
    """
    Feature: Scene Autosave Operations

    The Scene class provides methods for enabling, disabling, and configuring
    autosave functionality including timer-based backups and configuration
    management.
    """

    def test_autosave_enabled_by_default(self):
        """
        Scenario: Autosave is enabled by default

        Given a newly created Scene instance
        When checking autosave status
        Then autosave should be enabled by default
        """
        scene = Scene.Scene()

        assert scene.is_autosave_enabled() is True  # Enabled by default
        assert scene.get_autosave_interval() == 300  # Default: 300 seconds = 5 minutes

    def test_autosave_with_configuration(self):
        """
        Scenario: Autosave uses provided configuration

        Given a Scene instance with autosave configuration
        When Scene is created
        Then autosave should use the configured settings
        """
        config = {"autosave": {"enabled": True, "interval": 600, "max_backups": 30}}  # 600 seconds = 10 minutes
        scene = Scene.new(config=config)

        assert scene.is_autosave_enabled() is True
        assert scene.get_autosave_interval() == 600
        assert scene.get_autosave_config() == {"enabled": True, "interval": 600, "max_backups": 30}

    def test_autosave_disabled_by_configuration(self):
        """
        Scenario: Autosave can be disabled by configuration

        Given a Scene instance with disabled autosave configuration
        When Scene is created
        Then autosave should be disabled
        """
        config = {"autosave": {"enabled": False, "interval": 300, "max_backups": 20}}
        scene = Scene.new(config=config)

        assert scene.is_autosave_enabled() is False
        assert scene.get_autosave_config() == {"enabled": False, "interval": 300, "max_backups": 20}

    def test_enable_autosave_method(self):
        """
        Scenario: Enable autosave via public method

        Given a Scene instance
        When enable_autosave() is called with interval
        Then autosave should be enabled with specified interval
        """
        scene = Scene.Scene()

        # Disable first to test enabling
        scene.disable_autosave()
        assert scene.is_autosave_enabled() is False

        # Enable with 10 minute interval
        scene.enable_autosave(10)

        assert scene.is_autosave_enabled() is True
        assert scene.get_autosave_interval() == 600  # 10 minutes = 600 seconds

    def test_disable_autosave_method(self):
        """
        Scenario: Disable autosave via public method

        Given a Scene instance with active autosave
        When disable_autosave() is called
        Then autosave should be disabled
        """
        scene = Scene.Scene()

        # Autosave is enabled by default
        assert scene.is_autosave_enabled() is True

        # Disable autosave
        scene.disable_autosave()

        assert scene.is_autosave_enabled() is False

    def test_get_autosave_interval_method(self):
        """
        Scenario: Get autosave interval

        Given a Scene instance with autosave interval
        When get_autosave_interval() is called
        Then it should return the interval
        """
        scene = Scene.Scene()

        # Default interval is 300 seconds (5 minutes)
        assert scene.get_autosave_interval() == 300

        # Change interval and verify
        scene.enable_autosave(15)  # 15 minutes
        assert scene.get_autosave_interval() == 900  # 15 minutes = 900 seconds

    def test_get_autosave_config_method(self):
        """
        Scenario: Get autosave configuration

        Given a Scene instance with autosave configuration
        When get_autosave_config() is called
        Then it should return the configuration
        """
        config = {"autosave": {"enabled": True, "interval": 300, "max_backups": 20}}
        scene = Scene.new(config=config)

        returned_config = scene.get_autosave_config()
        assert returned_config["enabled"] is True
        assert returned_config["interval"] == 300
        assert returned_config["max_backups"] == 20

    def test_set_autosave_config_method(self):
        """
        Scenario: Set autosave configuration

        Given a Scene instance
        When set_autosave_config() is called with configuration
        Then configuration should be updated
        """
        scene = Scene.Scene()
        config = {"enabled": True, "interval": 600, "max_backups": 30}  # 600 seconds = 10 minutes

        scene.set_autosave_config(config)

        returned_config = scene.get_autosave_config()
        assert returned_config["enabled"] is True
        assert returned_config["interval"] == 600
        assert returned_config["max_backups"] == 30
        assert scene.is_autosave_enabled() is True
        assert scene.get_autosave_interval() == 600

    def test_save_triggers_backup_when_autosave_active(self):
        """
        Scenario: Manual save triggers backup when autosave is active

        Given a Scene instance with active autosave
        When save() is called
        Then a backup should be created
        """
        scene = Scene.Scene()

        # Mock the autosave manager's update_last_save_path method
        with patch.object(scene._Scene__autosave_manager, 'update_last_save_path') as mock_update:
            with tempfile.NamedTemporaryFile(suffix='.pzs', delete=False) as tmp:
                tmp_path = tmp.name

            try:
                scene.save(tmp_path)

                # Verify save path was stored
                assert scene._Scene__last_save_path == tmp_path
                assert scene._Scene__first_save_done is True

                # Verify autosave manager was called
                mock_update.assert_called_once_with(tmp_path)
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    def test_save_does_not_trigger_backup_when_autosave_inactive(self):
        """
        Scenario: Manual save does not trigger backup when autosave is inactive

        Given a Scene instance with inactive autosave
        When save() is called
        Then update_last_save_path should be called but no backup created
        """
        config = {"autosave": {"enabled": False}}
        scene = Scene.new(config=config)

        # Mock the autosave manager's _trigger_autosave_backup method
        with patch.object(scene._Scene__autosave_manager, '_trigger_autosave_backup') as mock_trigger:
            with tempfile.NamedTemporaryFile(suffix='.pzs', delete=False) as tmp:
                tmp_path = tmp.name

            try:
                scene.save(tmp_path)

                # Verify save path was stored
                assert scene._Scene__last_save_path == tmp_path
                assert scene._Scene__first_save_done is True

                # Verify backup creation was NOT called (autosave is disabled)
                mock_trigger.assert_not_called()
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

    def test_backup_manager_initialization(self):
        """
        Scenario: Backup manager is initialized at startup when autosave enabled

        Given a Scene instance with autosave enabled
        When Scene is created
        Then backup manager should be initialized
        """
        config = {"autosave": {"enabled": True, "interval": 300, "max_backups": 20}}

        with patch('pyzui.backup.backupmanager.BackupManager') as mock_backup_class:
            mock_backup = Mock()
            mock_backup_class.return_value = mock_backup

            Scene.Scene(config=config)

            # Backup manager should be initialized at startup
            mock_backup_class.assert_called_once_with(config['autosave'])

    def test_autosave_configuration_updates(self):
        """
        Scenario: Autosave configuration updates affect autosave state

        Given a Scene instance
        When set_autosave_config() is called with different settings
        Then autosave state should update accordingly
        """
        scene = Scene.Scene()

        # Initially enabled by default
        assert scene.is_autosave_enabled() is True

        # Disable via config
        scene.set_autosave_config({"enabled": False})
        assert scene.is_autosave_enabled() is False

        # Re-enable with different interval
        scene.set_autosave_config({"enabled": True, "interval": 120})  # 2 minutes
        assert scene.is_autosave_enabled() is True
        assert scene.get_autosave_interval() == 120
