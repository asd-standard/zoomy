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
Autosave Settings Dialog

Provides a dialog for configuring autosave settings including interval,
max_backups, and enabling/disabling the feature.
"""

from typing import Any

from PySide6 import QtWidgets


class AutosaveSettingsDialog(QtWidgets.QDialog):
    """
    Constructor :
        AutosaveSettingsDialog(parent=None, initial_config=None)
    Parameters :
        parent : Optional[QtWidgets.QWidget]
            Parent widget
        initial_config : Optional[Dict[str, Any]]
            Initial autosave configuration

    AutosaveSettingsDialog(parent=None, initial_config=None) --> None
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None, initial_config: dict[str, Any] | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Autosave Settings")
        self.setModal(True)
        self.resize(400, 340)

        self._config = initial_config or {}
        self._setup_ui()
        self._load_initial_config()

    def _setup_ui(self) -> None:
        """Setup the dialog UI components."""
        layout = QtWidgets.QVBoxLayout(self)

        # Enable checkbox (enabled by default)
        self.enable_checkbox = QtWidgets.QCheckBox("Enable autosave")
        self.enable_checkbox.setChecked(True)  # Enabled by default
        self.enable_checkbox.stateChanged.connect(self._on_enable_changed)
        layout.addWidget(self.enable_checkbox)

        # Interval settings
        interval_group = QtWidgets.QGroupBox("Autosave Interval")
        interval_layout = QtWidgets.QVBoxLayout()

        interval_hbox = QtWidgets.QHBoxLayout()
        interval_hbox.addWidget(QtWidgets.QLabel("Save every:"))

        self.interval_spinbox = QtWidgets.QSpinBox()
        self.interval_spinbox.setRange(1, 1440)  # 1 minute to 24 hours
        self.interval_spinbox.setSuffix(" minutes")
        self.interval_spinbox.setValue(5)
        interval_hbox.addWidget(self.interval_spinbox)
        interval_hbox.addStretch()

        interval_layout.addLayout(interval_hbox)
        interval_group.setLayout(interval_layout)
        layout.addWidget(interval_group)

        # Backup rotation settings
        rotation_group = QtWidgets.QGroupBox("Backup Rotation")
        rotation_layout = QtWidgets.QVBoxLayout()

        rotation_hbox = QtWidgets.QHBoxLayout()
        rotation_hbox.addWidget(QtWidgets.QLabel("Keep last:"))

        self.max_backups_spinbox = QtWidgets.QSpinBox()
        self.max_backups_spinbox.setRange(1, 1000)  # 1 to 1000 backups
        self.max_backups_spinbox.setSuffix(" backups")
        self.max_backups_spinbox.setValue(20)
        rotation_hbox.addWidget(self.max_backups_spinbox)

        rotation_hbox.addWidget(QtWidgets.QLabel("(oldest are deleted automatically)"))
        rotation_hbox.addStretch()

        rotation_layout.addLayout(rotation_hbox)
        rotation_group.setLayout(rotation_layout)
        layout.addWidget(rotation_group)

        # Expiration settings
        expire_group = QtWidgets.QGroupBox("Backup Expiration")
        expire_layout = QtWidgets.QVBoxLayout()

        expire_hbox = QtWidgets.QHBoxLayout()
        expire_hbox.addWidget(QtWidgets.QLabel("Expire backups after:"))

        self.expire_days_spinbox = QtWidgets.QSpinBox()
        self.expire_days_spinbox.setRange(1, 365)
        self.expire_days_spinbox.setSuffix(" days")
        self.expire_days_spinbox.setValue(7)
        expire_hbox.addWidget(self.expire_days_spinbox)

        expire_hbox.addWidget(QtWidgets.QLabel("(scene dirs inactive longer are deleted)"))
        expire_hbox.addStretch()

        expire_layout.addLayout(expire_hbox)
        expire_group.setLayout(expire_layout)
        layout.addWidget(expire_group)

        # Info label
        info_label = QtWidgets.QLabel(
            "Autosave is enabled by default at application start\n"
            "Each scene gets its own backup directory: ~/.pyzui/backups/<scene>_<hash>/\n"
            "Backup naming: yy_mm_dd_hh_mm_filename_hash.pzs\n"
            "Oldest backups are automatically deleted when limit is reached.\n"
            "Inactive scene directories are deleted after expiration."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Button box
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _load_initial_config(self) -> None:
        """Load initial configuration into UI."""
        enabled = self._config.get("enabled", True)  # Enabled by default
        interval = self._config.get("interval", 300)  # Default 5 minutes
        max_backups = self._config.get("max_backups", 20)  # Default 20 backups
        expire_days = self._config.get("expire_days", 7)  # Default 7 days

        self.enable_checkbox.setChecked(enabled)
        self.interval_spinbox.setValue(interval // 60)  # Convert seconds to minutes
        self.max_backups_spinbox.setValue(max_backups)
        self.expire_days_spinbox.setValue(expire_days)

        self._on_enable_changed()

    def _on_enable_changed(self) -> None:
        """Handle enable checkbox state change."""
        enabled = self.enable_checkbox.isChecked()
        self.interval_spinbox.setEnabled(enabled)
        self.max_backups_spinbox.setEnabled(enabled)
        self.expire_days_spinbox.setEnabled(enabled)

    def get_config(self) -> dict[str, Any]:
        """
        Method :
            get_config()

        Get the current configuration from the dialog.

        Returns :
            Dict[str, Any]
                Autosave configuration dictionary

        get_config() --> Dict[str, Any]
        """
        enabled = self.enable_checkbox.isChecked()
        interval_minutes = self.interval_spinbox.value()
        max_backups = self.max_backups_spinbox.value()
        expire_days = self.expire_days_spinbox.value()

        return {
            "enabled": enabled,
            "interval": interval_minutes * 60,  # Convert minutes to seconds
            "max_backups": max_backups,
            "expire_days": expire_days,
        }

    @staticmethod
    def get_autosave_settings(
        parent: QtWidgets.QWidget | None = None, initial_config: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """
        Method :
            get_autosave_settings(parent=None, initial_config=None)

        Static method to show dialog and get autosave settings.

        Parameters :
            parent : Optional[QtWidgets.QWidget]
                Parent widget
            initial_config : Optional[Dict[str, Any]]
                Initial autosave configuration

        Returns :
            Optional[Dict[str, Any]]
                Autosave configuration if accepted, None if cancelled

        get_autosave_settings(parent=None, initial_config=None) --> Optional[Dict[str, Any]]
        """
        dialog = AutosaveSettingsDialog(parent, initial_config)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            return dialog.get_config()
        return None
