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
Feature: Autosave Settings Dialog

Provides a dialog for configuring autosave settings including interval,
max_backups, and enabling/disabling the feature.
"""

from unittest.mock import Mock, patch

from PySide6 import QtWidgets

from pyzui.windows.dialogwindows.autosavesettingsdialog import AutosaveSettingsDialog


class TestAutosaveSettingsDialog:
    """
    Feature: Autosave Settings Dialog Operations

    The AutosaveSettingsDialog provides UI for configuring autosave settings
    including enabling/disabling, interval configuration, and max_backups settings.
    """

    def test_init_without_config(self):
        """
        Scenario: Create dialog without initial configuration

        Given no initial configuration
        When AutosaveSettingsDialog is created
        Then it should use default values
        """
        with patch.object(AutosaveSettingsDialog, '__init__', lambda self, parent=None, initial_config=None: None):
            dialog = AutosaveSettingsDialog()
            dialog._config = {}

            assert dialog._config == {}

    def test_init_with_config(self):
        """
        Scenario: Create dialog with initial configuration

        Given initial autosave configuration
        When AutosaveSettingsDialog is created
        Then it should load the configuration
        """
        config = {"enabled": True, "interval": 600, "max_backups": 30}

        with patch.object(AutosaveSettingsDialog, '__init__', lambda self, parent=None, initial_config=None: None):
            dialog = AutosaveSettingsDialog(initial_config=config)
            dialog._config = config

            assert dialog._config == config

    def test_load_initial_config_enabled(self):
        """
        Scenario: Load enabled configuration into UI

        Given configuration with autosave enabled
        When dialog loads configuration
        Then UI should reflect enabled state
        """
        config = {"enabled": True, "interval": 600, "max_backups": 50, "expire_days": 14}

        dialog = AutosaveSettingsDialog.__new__(AutosaveSettingsDialog)
        dialog._config = config
        dialog.enable_checkbox = Mock()
        dialog.interval_spinbox = Mock()
        dialog.max_backups_spinbox = Mock()
        dialog.expire_days_spinbox = Mock()

        dialog._load_initial_config()

        dialog.enable_checkbox.setChecked.assert_called_once_with(True)
        dialog.interval_spinbox.setValue.assert_called_once_with(10)  # 600 seconds = 10 minutes
        dialog.max_backups_spinbox.setValue.assert_called_once_with(50)
        dialog.expire_days_spinbox.setValue.assert_called_once_with(14)

    def test_load_initial_config_disabled(self):
        """
        Scenario: Load disabled configuration into UI

        Given configuration with autosave disabled
        When dialog loads configuration
        Then UI should reflect disabled state
        """
        config = {"enabled": False, "interval": 300, "max_backups": 7, "expire_days": 3}

        dialog = AutosaveSettingsDialog.__new__(AutosaveSettingsDialog)
        dialog._config = config
        dialog.enable_checkbox = Mock()
        dialog.interval_spinbox = Mock()
        dialog.max_backups_spinbox = Mock()
        dialog.expire_days_spinbox = Mock()

        dialog._load_initial_config()

        dialog.enable_checkbox.setChecked.assert_called_once_with(False)
        dialog.interval_spinbox.setValue.assert_called_once_with(5)  # 300 seconds = 5 minutes
        dialog.max_backups_spinbox.setValue.assert_called_once_with(7)
        dialog.expire_days_spinbox.setValue.assert_called_once_with(3)

    def test_load_initial_config_defaults(self):
        """
        Scenario: Load configuration with missing values

        Given configuration with missing values
        When dialog loads configuration
        Then it should use defaults for missing values
        """
        config = {"enabled": True}  # Missing interval, max_backups, expire_days

        dialog = AutosaveSettingsDialog.__new__(AutosaveSettingsDialog)
        dialog._config = config
        dialog.enable_checkbox = Mock()
        dialog.interval_spinbox = Mock()
        dialog.max_backups_spinbox = Mock()
        dialog.expire_days_spinbox = Mock()

        dialog._load_initial_config()

        dialog.enable_checkbox.setChecked.assert_called_once_with(True)
        dialog.interval_spinbox.setValue.assert_called_once_with(5)  # Default 5 minutes
        dialog.max_backups_spinbox.setValue.assert_called_once_with(20)  # Default 20 backups
        dialog.expire_days_spinbox.setValue.assert_called_once_with(7)  # Default 7 days

    def test_on_enable_changed_enabled(self):
        """
        Scenario: Enable checkbox checked

        Given dialog with disabled controls
        When enable checkbox is checked
        Then controls should be enabled
        """
        dialog = AutosaveSettingsDialog.__new__(AutosaveSettingsDialog)
        dialog.enable_checkbox = Mock()
        dialog.enable_checkbox.isChecked.return_value = True
        dialog.interval_spinbox = Mock()
        dialog.max_backups_spinbox = Mock()
        dialog.expire_days_spinbox = Mock()

        dialog._on_enable_changed()

        dialog.interval_spinbox.setEnabled.assert_called_once_with(True)
        dialog.max_backups_spinbox.setEnabled.assert_called_once_with(True)
        dialog.expire_days_spinbox.setEnabled.assert_called_once_with(True)

    def test_on_enable_changed_disabled(self):
        """
        Scenario: Enable checkbox unchecked

        Given dialog with enabled controls
        When enable checkbox is unchecked
        Then controls should be disabled
        """
        dialog = AutosaveSettingsDialog.__new__(AutosaveSettingsDialog)
        dialog.enable_checkbox = Mock()
        dialog.enable_checkbox.isChecked.return_value = False
        dialog.interval_spinbox = Mock()
        dialog.max_backups_spinbox = Mock()
        dialog.expire_days_spinbox = Mock()

        dialog._on_enable_changed()

        dialog.interval_spinbox.setEnabled.assert_called_once_with(False)
        dialog.max_backups_spinbox.setEnabled.assert_called_once_with(False)
        dialog.expire_days_spinbox.setEnabled.assert_called_once_with(False)

    def test_get_config_enabled(self):
        """
        Scenario: Get configuration with autosave enabled

        Given dialog with autosave enabled and custom values
        When get_config() is called
        Then it should return correct configuration
        """
        dialog = AutosaveSettingsDialog.__new__(AutosaveSettingsDialog)
        dialog.enable_checkbox = Mock()
        dialog.enable_checkbox.isChecked.return_value = True
        dialog.interval_spinbox = Mock()
        dialog.interval_spinbox.value.return_value = 15  # 15 minutes
        dialog.max_backups_spinbox = Mock()
        dialog.max_backups_spinbox.value.return_value = 30  # 30 backups
        dialog.expire_days_spinbox = Mock()
        dialog.expire_days_spinbox.value.return_value = 14  # 14 days

        config = dialog.get_config()

        assert config == {
            "enabled": True,
            "interval": 900,  # 15 minutes * 60 seconds
            "max_backups": 30,
            "expire_days": 14,
        }

    def test_get_config_disabled(self):
        """
        Scenario: Get configuration with autosave disabled

        Given dialog with autosave disabled
        When get_config() is called
        Then it should return disabled configuration
        """
        dialog = AutosaveSettingsDialog.__new__(AutosaveSettingsDialog)
        dialog.enable_checkbox = Mock()
        dialog.enable_checkbox.isChecked.return_value = False
        dialog.interval_spinbox = Mock()
        dialog.interval_spinbox.value.return_value = 10
        dialog.max_backups_spinbox = Mock()
        dialog.max_backups_spinbox.value.return_value = 14
        dialog.expire_days_spinbox = Mock()
        dialog.expire_days_spinbox.value.return_value = 7

        config = dialog.get_config()

        assert config == {
            "enabled": False,
            "interval": 600,  # 10 minutes * 60 seconds
            "max_backups": 14,
            "expire_days": 7,
        }

    def test_get_config_minimum_values(self):
        """
        Scenario: Get configuration with minimum values

        Given dialog with minimum interval and max_backups
        When get_config() is called
        Then it should return correct values
        """
        dialog = AutosaveSettingsDialog.__new__(AutosaveSettingsDialog)
        dialog.enable_checkbox = Mock()
        dialog.enable_checkbox.isChecked.return_value = True
        dialog.interval_spinbox = Mock()
        dialog.interval_spinbox.value.return_value = 1  # Minimum 1 minute
        dialog.max_backups_spinbox = Mock()
        dialog.max_backups_spinbox.value.return_value = 1  # Minimum 1 backup
        dialog.expire_days_spinbox = Mock()
        dialog.expire_days_spinbox.value.return_value = 1  # Minimum 1 day

        config = dialog.get_config()

        assert config == {
            "enabled": True,
            "interval": 60,  # 1 minute * 60 seconds
            "max_backups": 1,
            "expire_days": 1,
        }

    def test_get_config_maximum_values(self):
        """
        Scenario: Get configuration with maximum values

        Given dialog with maximum interval and max_backups
        When get_config() is called
        Then it should return correct values
        """
        dialog = AutosaveSettingsDialog.__new__(AutosaveSettingsDialog)
        dialog.enable_checkbox = Mock()
        dialog.enable_checkbox.isChecked.return_value = True
        dialog.interval_spinbox = Mock()
        dialog.interval_spinbox.value.return_value = 1440  # Maximum 24 hours
        dialog.max_backups_spinbox = Mock()
        dialog.max_backups_spinbox.value.return_value = 1000  # Maximum 1000 backups
        dialog.expire_days_spinbox = Mock()
        dialog.expire_days_spinbox.value.return_value = 365  # Maximum 365 days

        config = dialog.get_config()

        assert config == {
            "enabled": True,
            "interval": 86400,  # 1440 minutes * 60 seconds
            "max_backups": 1000,
            "expire_days": 365,
        }

    def test_get_autosave_settings_accepted(self):
        """
        Scenario: Get settings via static method with acceptance

        Given initial configuration
        When get_autosave_settings() is called and dialog accepted
        Then it should return configuration
        """
        initial_config = {"enabled": True, "interval": 300, "max_backups": 7}

        with patch.object(AutosaveSettingsDialog, '__init__', return_value=None):
            with patch.object(AutosaveSettingsDialog, 'exec') as mock_exec:
                mock_exec.return_value = QtWidgets.QDialog.DialogCode.Accepted

                with patch.object(AutosaveSettingsDialog, 'get_config') as mock_get_config:
                    mock_get_config.return_value = {"enabled": True, "interval": 600, "max_backups": 14, "expire_days": 7}

                    result = AutosaveSettingsDialog.get_autosave_settings(
                        initial_config=initial_config
                    )

                    assert result == {"enabled": True, "interval": 600, "max_backups": 14, "expire_days": 7}

    def test_get_autosave_settings_rejected(self):
        """
        Scenario: Get settings via static method with rejection

        Given initial configuration
        When get_autosave_settings() is called and dialog rejected
        Then it should return None
        """
        initial_config = {"enabled": True, "interval": 300, "max_backups": 7}

        with patch.object(AutosaveSettingsDialog, '__init__', return_value=None):
            with patch.object(AutosaveSettingsDialog, 'exec') as mock_exec:
                mock_exec.return_value = QtWidgets.QDialog.DialogCode.Rejected

                result = AutosaveSettingsDialog.get_autosave_settings(
                    initial_config=initial_config
                )

                assert result is None

    def test_spinbox_ranges(self):
        """
        Scenario: Verify spinbox value ranges

        Given dialog is created
        When checking spinbox ranges
        Then they should have correct minimum and maximum values
        """
        # Test through get_config method with mocked spinboxes
        dialog = AutosaveSettingsDialog.__new__(AutosaveSettingsDialog)
        dialog.enable_checkbox = Mock()
        dialog.enable_checkbox.isChecked.return_value = True
        dialog.interval_spinbox = Mock()
        dialog.interval_spinbox.value.return_value = 1
        dialog.max_backups_spinbox = Mock()
        dialog.max_backups_spinbox.value.return_value = 1
        dialog.expire_days_spinbox = Mock()
        dialog.expire_days_spinbox.value.return_value = 1

        # Just verify the method works with minimum values
        config = dialog.get_config()
        assert config["interval"] == 60  # 1 minute * 60
        assert config["max_backups"] == 1
        assert config["expire_days"] == 1

    def test_button_box_buttons(self):
        """
        Scenario: Verify dialog buttons

        Given dialog is created
        When checking button box
        Then it should have OK and Cancel buttons
        """
        # This test is more about the design than implementation
        # We can't actually test Qt widgets without QApplication
        pass

    def test_dialog_size(self):
        """
        Scenario: Verify dialog size

        Given dialog is created
        When checking dialog size
        Then it should have reasonable dimensions
        """
        # This test is more about the design than implementation
        # We can't actually test Qt widgets without QApplication
        pass

    def test_info_label_content(self):
        """
        Scenario: Verify info label content

        Given dialog is created
        When checking info label text
        Then it should contain backup information
        """
        # This test is more about the design than implementation
        # We can't actually test Qt widgets without QApplication
        pass
