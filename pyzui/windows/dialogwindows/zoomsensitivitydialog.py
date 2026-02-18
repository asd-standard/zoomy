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

"""Zoom sensitivity input dialog."""

from typing import Tuple
from PySide6.QtWidgets import QInputDialog, QDialog

# Type alias
DialogResult = Tuple[bool, str]

def OpenZoomSensitivityInputDialog(current_sensitivity: float) -> DialogResult:
    """
    Function :
        OpenZoomSensitivityInputDialog(current_sensitivity)
    Parameters :
        current_sensitivity : float

    OpenZoomSensitivityInputDialog(current_sensitivity) --> Tuple[bool, str]

    Opens a dialog to set zoom sensitivity.
    Returns (ok_pressed, text_input) tuple.
    """
    dialog = QInputDialog()
    dialog.setWindowTitle("Set zoom sensitivity")
    dialog.setLabelText("sensitivity goes from 0 to 100, current: "+str(int(1000/current_sensitivity)))
    dialog.resize(300, 80)  # Set the size here

    ok_pressed = dialog.exec()
    text_input = dialog.textValue()

    return ok_pressed == QDialog.DialogCode.Accepted, str(text_input)
