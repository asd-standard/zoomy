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
Zoom Settings Dialog

Provides a dialog for configuring zoom limits including minimum and maximum
zoom levels with clamping to prevent crashes at extreme zoom values.
"""

from typing import Any

from PySide6 import QtWidgets


class ZoomSettingsDialog(QtWidgets.QDialog):
    """
    Constructor :
        ZoomSettingsDialog(parent=None, initial_config=None)
    Parameters :
        parent : Optional[QtWidgets.QWidget]
            Parent widget
        initial_config : Optional[Dict[str, Any]]
            Initial zoom configuration

    ZoomSettingsDialog(parent=None, initial_config=None) --> None
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None, initial_config: dict[str, Any] | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Zoom Settings")
        self.setModal(True)
        self.resize(600, 500)

        self._config = initial_config or {}
        self._setup_ui()
        self._load_initial_config()

    def _setup_ui(self) -> None:
        """Setup the dialog UI components."""
        layout = QtWidgets.QVBoxLayout(self)

        # Zoom limits group
        limits_group = QtWidgets.QGroupBox("Zoom Limits")
        limits_layout = QtWidgets.QVBoxLayout()

        # Minimum zoom level
        min_hbox = QtWidgets.QHBoxLayout()
        min_hbox.addWidget(QtWidgets.QLabel("Minimum zoom level:"))

        self.min_spinbox = QtWidgets.QDoubleSpinBox()
        self.min_spinbox.setRange(-50.0, 0.0)
        self.min_spinbox.setDecimals(1)
        self.min_spinbox.setSingleStep(1.0)
        self.min_spinbox.setValue(-12.0)
        min_hbox.addWidget(self.min_spinbox)
        min_hbox.addStretch()

        limits_layout.addLayout(min_hbox)

        # Maximum zoom level
        max_hbox = QtWidgets.QHBoxLayout()
        max_hbox.addWidget(QtWidgets.QLabel("Maximum zoom level:"))

        self.max_spinbox = QtWidgets.QDoubleSpinBox()
        self.max_spinbox.setRange(0.0, 50.0)
        self.max_spinbox.setDecimals(1)
        self.max_spinbox.setSingleStep(1.0)
        self.max_spinbox.setValue(10.0)
        max_hbox.addWidget(self.max_spinbox)
        max_hbox.addStretch()

        limits_layout.addLayout(max_hbox)

        # Clamp enabled checkbox
        self.clamp_checkbox = QtWidgets.QCheckBox("Clamp zoom to limits (recommended)")
        self.clamp_checkbox.setChecked(True)
        limits_layout.addWidget(self.clamp_checkbox)

        limits_group.setLayout(limits_layout)
        layout.addWidget(limits_group)

        # Default zoom level section
        default_group = QtWidgets.QGroupBox("Default Zoom for New Scenes")
        default_layout = QtWidgets.QVBoxLayout()

        default_hbox = QtWidgets.QHBoxLayout()
        default_hbox.addWidget(QtWidgets.QLabel("Default zoom level:"))

        self.default_spinbox = QtWidgets.QDoubleSpinBox()
        self.default_spinbox.setRange(-50.0, 50.0)
        self.default_spinbox.setDecimals(1)
        self.default_spinbox.setSingleStep(1.0)
        self.default_spinbox.setValue(-4.0)
        default_hbox.addWidget(self.default_spinbox)

        # Performance note label
        note_label = QtWidgets.QLabel("(Negative values improve performance)")
        note_label.setStyleSheet("color: #666666; font-style: italic;")
        default_hbox.addWidget(note_label)
        default_hbox.addStretch()

        default_layout.addLayout(default_hbox)
        default_group.setLayout(default_layout)
        layout.addWidget(default_group)

        # Info/explanation text in read-only QTextEdit (theme-consistent)
        info_text = (
            "Zoom Limits: Prevent crashes when zoomed too far out or too far in\n\n"
            "Default range: -12 to +10 (safe for StringMediaObjects)\n"
            "  • -12: 0.00024x scale (0.024%)\n"
            "  • -4: 0.0625x scale (6.25%) - Default for new scenes\n"
            "  • +10: 1024x scale\n\n"
            "Default Zoom: Sets initial zoom level for new scenes\n"
            "  • Negative values improve performance (less computation)\n"
            "  • Applies only to new scenes, not loaded ones\n\n"
            "Why these limits?\n"
            "• Below -12: StringMediaObject fonts become too small (<0.5 point)\n"
            "• Below -20: Fonts become invisible (<0.1 point)\n"
            "• Below -30: Position calculations overflow\n"
            "• Above +10: UI elements become unusably large\n\n"
            "Values are clamped automatically when limits are reached.\n"
            "If min > max, they will be automatically swapped."
        )

        # Create QTextEdit widget for theme-consistent info display
        info_edit = QtWidgets.QTextEdit()
        info_edit.setReadOnly(True)  # Make it non-editable
        info_edit.setPlainText(info_text)
        info_edit.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)  # Remove border
        info_edit.setMinimumHeight(150)  # Minimum height for readability
        info_edit.setMaximumHeight(250)  # Maximum height to prevent taking too much space

        layout.addWidget(info_edit)

        # Button box
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _load_initial_config(self) -> None:
        """Load initial configuration into UI."""
        min_zoom = self._config.get("min_zoomlevel", -12.0)
        max_zoom = self._config.get("max_zoomlevel", 10.0)
        default_zoom = self._config.get("default_zoomlevel", -4.0)
        clamp_enabled = self._config.get("clamp_enabled", True)

        self.min_spinbox.setValue(min_zoom)
        self.max_spinbox.setValue(max_zoom)
        self.default_spinbox.setValue(default_zoom)
        self.clamp_checkbox.setChecked(clamp_enabled)

    def get_config(self) -> dict[str, Any]:
        """
        Method :
            get_config()

        Get the current configuration from the dialog.

        Returns :
            Dict[str, Any]
                Zoom configuration dictionary

        get_config() --> Dict[str, Any]
        """
        min_zoom = self.min_spinbox.value()
        max_zoom = self.max_spinbox.value()
        default_zoom = self.default_spinbox.value()
        clamp_enabled = self.clamp_checkbox.isChecked()

        # Ensure min <= max (auto-swap if needed)
        if min_zoom > max_zoom:
            min_zoom, max_zoom = max_zoom, min_zoom

        # Ensure default stays within bounds
        if default_zoom < min_zoom:
            default_zoom = min_zoom
        elif default_zoom > max_zoom:
            default_zoom = max_zoom

        return {
            "min_zoomlevel": min_zoom,
            "max_zoomlevel": max_zoom,
            "default_zoomlevel": default_zoom,
            "clamp_enabled": clamp_enabled,
        }

    @staticmethod
    def get_zoom_settings(
        parent: QtWidgets.QWidget | None = None, initial_config: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """
        Method :
            get_zoom_settings(parent=None, initial_config=None)

        Static method to show dialog and get zoom settings.

        Parameters :
            parent : Optional[QtWidgets.QWidget]
                Parent widget
            initial_config : Optional[Dict[str, Any]]
                Initial zoom configuration

        Returns :
            Optional[Dict[str, Any]]
                Zoom configuration if accepted, None if cancelled

        get_zoom_settings(parent=None, initial_config=None) --> Optional[Dict[str, Any]]
        """
        dialog = ZoomSettingsDialog(parent, initial_config)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            return dialog.get_config()
        return None
