## PyZUI 0.11 - Python Zooming User Interface
## Copyright (C) 2009  David Roberts <d@vidr.cc>
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
## 02110-1301, USA.

"""String input dialog with color selection."""

from typing import Tuple, Any
import os
from collections import deque

from PySide6.QtWidgets import (
    QDialog, QTextEdit, QVBoxLayout, QPushButton, QDialogButtonBox,
    QLineEdit, QWidget, QLabel, QHBoxLayout, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QPainter


class OpenNewStringInputDialog:
    """
    Constructor :
        OpenNewStringInputDialog()
    Parameters :
        None

    OpenNewStringInputDialog() --> None

    Gather the string through a dialog and let select the color.
    Also gives a selection column of the last 20 used colors.
    """
    def __init__(self) -> None:
        self.string_color = ''
        self.passed_color = ''
        self.color_codes = deque(maxlen=24)

        ## set the default tilestore directory, this can be overridden if required
        if 'APPDATA' in os.environ:
            ## Windows
            self.color_dir = os.path.join(os.environ['APPDATA'], "pyzui", "colorstore")
        else:
            ## Unix
            self.color_dir = os.path.join(os.path.expanduser('~'), ".pyzui", "colorstore")

        if os.path.isfile(self.color_dir+'/color_list.txt'):
            with open(self.color_dir+'/color_list.txt', 'r') as f:
                for line in f:
                    self.color_codes.append(line.strip())

        else:
            if os.path.isdir(self.color_dir):
                f = open(self.color_dir+'/color_list.txt', 'w')
                self.color_codes.append('ff0000')
                f.write('ff0000\n')
                self.color_codes.append('00ff00')
                f.write('00ff00\n')
                self.color_codes.append('0000ff')
                f.write('0000ff\n')
                f.close()
            else:
                os.mkdir(self.color_dir)
                f = open(self.color_dir+'/color_list.txt', 'w')
                self.color_codes.append('ff0000')
                f.write('ff0000\n')
                self.color_codes.append('00ff00')
                f.write('00ff00\n')
                self.color_codes.append('0000ff')
                f.write('0000ff\n')
                f.close()

    def _color_square(self, color_code: str) -> QWidget:
        """
        Method :
            OpenNewStringInputDialog._color_square(color_code)
        Parameters :
            color_code : str

        OpenNewStringInputDialog._color_square(color_code) --> QWidget

        Creates a colored square widget.
        """
        color_square = QWidget()
        color = QColor('#' + str(color_code))
        color_square.setFixedSize(20, 20)

        def paintEvent(event: Any) -> None:
            painter = QPainter(color_square)
            painter.fillRect(color_square.rect(), color)

        color_square.paintEvent = paintEvent

        return color_square

    def _color_button_click(self, color: str) -> None:
        """
        Method :
            OpenNewStringInputDialog._color_button_click(color)
        Parameters :
            color : str

        OpenNewStringInputDialog._color_button_click(color) --> None

        Handles color button click event.
        """
        self.string_color = color

    def _color_button(self, color_code: str) -> QWidget:
        """
        Method :
            OpenNewStringInputDialog._color_button(color_code)
        Parameters :
            color_code : str

        OpenNewStringInputDialog._color_button(color_code) --> QWidget

        Creates a color selection button.
        """
        color_widget = QWidget()

        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(10)

        color_square = self._color_square(color_code)
        label = QLabel(color_code)

        # Create a QPushButton but use a QWidget wrapper to hold square + label
        button = QPushButton()
        button.setLayout(layout)
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Add widget and label to the layout inside the button
        layout.addWidget(color_square)
        layout.addWidget(label)
        layout.addStretch()

        # Make the whole widget act like a button by forwarding clicks
        button.clicked.connect(lambda: self._color_button_click(color_code))

        # Our main layout for this widget is the button only
        main_layout = QHBoxLayout(color_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(button)

        return color_widget

    def _main_dialog(self) -> QDialog:
        """
        Method :
            OpenNewStringInputDialog._main_dialog()
        Parameters :
            None

        OpenNewStringInputDialog._main_dialog() --> QDialog

        Creates and configures the main dialog window.
        """
        dialog = QDialog()
        dialog.setWindowTitle("String input:")
        dialog.resize(900, 600)

        # Create text edit widget
        self.text_edit = QTextEdit(dialog)  # Input string is going to be typed in here
        font = QFont()
        font.setPointSize(16)  # Set desired font size
        self.text_edit.setFont(font)

        # Align text to top-left (horizontal only by default)
        self.text_edit.setAlignment(Qt.AlignLeft)

        # Create a text input field for custom color entry
        self.custom_color_input = QLineEdit(dialog)  # Color code it's going to be typed here
        self.custom_color_input.setPlaceholderText("Enter custom color (e.g., #ff5733)")

        # Create OK/Cancel buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        # Layout setup
        main_layout = QHBoxLayout(dialog)
        color_layout = QVBoxLayout()
        color_layout.setContentsMargins(0, 0, 0, 0)
        color_layout.setSpacing(2)

        for code in self.color_codes:
            btn = self._color_button(code)
            btn.setFixedWidth(120)
            color_layout.addWidget(btn)

        color_layout.addStretch()

        text_layout = QVBoxLayout()
        text_layout.addWidget(self.text_edit)
        text_layout.addWidget(self.custom_color_input)
        text_layout.addWidget(buttons)

        main_layout.addLayout(text_layout)
        main_layout.addLayout(color_layout)

        return dialog

    def _run_dialog(self) -> Tuple[bool, str]:
        """
        Method :
            OpenNewStringInputDialog._run_dialog()
        Parameters :
            None

        OpenNewStringInputDialog._run_dialog() --> Tuple[bool, str]

        Runs the dialog and returns the result.
        Returns (ok, uri) where ok is True if accepted, uri is the formatted string.
        """
        dialog = self._main_dialog()
        # Run dialog and get result
        if dialog.exec() == QDialog.Accepted:
            if len(self.string_color) != 6:
                self.string_color = self.custom_color_input.text()
                self.color_codes.append(self.string_color)
                f = open(self.color_dir+'/color_list.txt', 'w')
                for i in self.color_codes:
                    f.write(str(i)+'\n')
                f.close()

            elif len(self.string_color) != 6:
                print('Error')
            uri = 'string:'+str(self.string_color)+str(':') + str(self.text_edit.toPlainText())
            ok = True
        else:
            ok = False

        if ok and uri:
            return ok, uri
