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

"""SVG modification dialog for changing color and thickness of SVG objects."""

import os
import xml.etree.ElementTree as ET
from collections import deque
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtSvg, QtWidgets
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from pyzui.logger import get_logger
from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import get_svg_cache

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintEvent

    from pyzui.objects.mediaobjects.svgmediaobject import SVGMediaObject

# Type aliases
ColorCode = str
DialogResult = tuple[bool, str | None]


class ModifySVGInputDialog:
    """
    Constructor :
        ModifySVGInputDialog(svg_media_object)
    Parameters :
        svg_media_object : SVGMediaObject

    ModifySVGInputDialog(svg_media_object) --> None

    Dialog for modifying color and thickness of existing SVG objects.
    Designed for simple shapes (arrows, triangles, circles, squares)
    that were added via svgpickerinputdialog.py.
    """

    # Default values for non-cache files
    DEFAULT_COLOR: str = "000000"  # Black
    DEFAULT_THICKNESS: str = "10"

    def __init__(self, svg_media_object: "SVGMediaObject") -> None:
        """
        Constructor :
            ModifySVGInputDialog(svg_media_object)
        Parameters :
            svg_media_object : SVGMediaObject

        ModifySVGInputDialog(svg_media_object) --> None

        Initialize dialog for modifying an existing SVG object.
        """
        self.svg_object = svg_media_object
        self.original_media_id = svg_media_object._media_id
        self.__logger = get_logger("ModifySVGInputDialog")

        # Determine source type
        self.is_cache_file = self.original_media_id.startswith("svg_")
        self.is_tmp_file = False

        if not self.is_cache_file:
            # Check if file path is in /tmp/pyzui_svg_
            self.is_tmp_file = self.original_media_id.startswith("/tmp/pyzui_svg_")

        # Current values (extract from SVG content)
        self.current_color = self._extract_current_color()
        self.current_thickness = self._extract_current_thickness()

        # Modification state
        self.modified_color: str | None = None
        self.modified_thickness: str | None = None
        self.preview_applied = False

        # UI state
        self.shape_color = self.current_color or self.DEFAULT_COLOR
        self.color_codes: deque[ColorCode] = deque(maxlen=24)
        self.custom_color_input: QLineEdit | None = None
        self.thickness_input: QLineEdit | None = None
        self.preview_widget: QWidget | None = None

        # SVG cache
        self._svg_cache = get_svg_cache()

        # Load color history
        self._load_color_history()

    def _load_color_history(self) -> None:
        """Load color history from color store file."""
        if "APPDATA" in os.environ:
            color_dir = os.path.join(os.environ["APPDATA"], "pyzui", "colorstore")
        else:
            color_dir = os.path.join(os.path.expanduser("~"), ".pyzui", "colorstore")

        color_file = os.path.join(color_dir, "color_list.txt")

        if os.path.isfile(color_file):
            with open(color_file) as f:
                for line in f:
                    stripline = line.strip().lower()
                    if len(stripline) == 6 and stripline not in self.color_codes:
                        self.color_codes.append(stripline)
        else:
            # Create default colors if file doesn't exist
            os.makedirs(color_dir, exist_ok=True)
            with open(color_file, "w") as f:
                for color in ["ffffff", "ff0000", "00ff00", "0000ff"]:
                    self.color_codes.append(color)
                    f.write(color + "\n")

    def _validate_svg_source(self) -> bool:
        """
        Check if SVG is from safe source (``/tmp/pyzui_svg_``).
        Show warning dialog for other sources.

        Returns:
            True if safe or user confirms, False if user cancels
        """
        if self.is_cache_file or self.is_tmp_file:
            return True  # Safe cache file

        # Show warning for non-cache files
        return self._show_source_warning_dialog()

    def _show_source_warning_dialog(self) -> bool:
        """
        Warning: This SVG was not added via SVG Picker dialog.
        The modify dialog is designed for simple shapes from data/SVG/.

        Default values will be used: color=black, stroke-width=10
        Continue anyway?
        """
        dialog = QMessageBox()
        dialog.setWindowTitle("PyZUI - Warning")
        dialog.setText("SVG Source Warning")
        dialog.setInformativeText(
            "This SVG was not added via the SVG Picker dialog.\n"
            "The modify dialog is designed for simple shapes (arrows, triangles, circles, squares).\n\n"
            "Default values will be used: color=black, stroke-width=10\n"
            "Continue anyway?"
        )
        dialog.setIcon(QtWidgets.QMessageBox.Warning)
        dialog.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        dialog.setDefaultButton(QtWidgets.QMessageBox.No)

        return bool(dialog.exec() == QtWidgets.QMessageBox.Yes)

    def _color_name_to_hex(self, color_name: str) -> str:
        """
        Convert color name to hex code.

        Args:
            color_name: Color name (e.g., 'black', 'red') or hex code

        Returns:
            Hex color without # (e.g., '000000')
        """
        # If it's already hex, return it
        if color_name.startswith("#"):
            return color_name[1:].lower()

        # Try to convert color name using QColor
        try:
            color = QColor(color_name)
            if color.isValid():
                # Convert to hex without #
                return str(color.name()[1:].lower())
        except Exception:
            pass

        # Default to black if conversion fails
        return "000000"

    def _extract_current_color(self) -> str | None:
        """
        Extract color from SVG content.
        For simple shapes, look for stroke or fill attributes.
        Returns hex color without # (e.g., '000000' for black).
        """
        content = self.svg_object.get_svg_content()
        if not content:
            return None

        try:
            # Parse XML
            root = ET.fromstring(content)

            # Define namespace
            ns = {"svg": "http://www.w3.org/2000/svg"}

            # Look for stroke or fill attributes in shape elements
            for tag in ["path", "rect", "circle", "ellipse", "line", "polyline", "polygon"]:
                elements = root.findall(f".//svg:{tag}", ns) or []
                for elem in elements:
                    # Check stroke first
                    stroke = elem.get("stroke")
                    if stroke and stroke.lower() not in ("none", "transparent"):
                        return self._color_name_to_hex(stroke)

                    # Check fill
                    fill = elem.get("fill")
                    if fill and fill.lower() not in ("none", "transparent"):
                        return self._color_name_to_hex(fill)

            # Also check root element
            stroke = root.get("stroke")
            if stroke and stroke.lower() not in ("none", "transparent"):
                return self._color_name_to_hex(stroke)

        except Exception as e:
            self.__logger.error("Error extracting color from SVG: %s", e)

        return None

    def _extract_current_thickness(self) -> str | None:
        """
        Extract stroke-width from SVG content.
        Returns string value (e.g., '8').
        """
        content = self.svg_object.get_svg_content()
        if not content:
            return None

        try:
            # Parse XML
            root = ET.fromstring(content)

            # Define namespace
            ns = {"svg": "http://www.w3.org/2000/svg"}

            # Look for stroke-width in shape elements
            for tag in ["path", "rect", "circle", "ellipse", "line", "polyline", "polygon"]:
                elements = root.findall(f".//svg:{tag}", ns) or []
                for elem in elements:
                    stroke_width = elem.get("stroke-width")
                    if stroke_width:
                        return stroke_width

        except Exception as e:
            self.__logger.error("Error extracting thickness from SVG: %s", e)

        return None

    def _color_square(self, color_code: ColorCode) -> QWidget:
        """
        Create a colored square widget.
        """
        color_square = QWidget()
        color = QColor("#" + str(color_code))
        color_square.setFixedSize(20, 20)

        def paintEvent(event: "QPaintEvent") -> None:
            painter = QPainter(color_square)
            painter.fillRect(color_square.rect(), color)
            # Explicit .end() required: an unended QPainter corrupts
            # Qt's C++ paint engine, ultimately causing SIGSEGV.
            painter.end()

        color_square.paintEvent = paintEvent

        return color_square

    def _color_button_click(self, color: ColorCode) -> None:
        """
        Handle color button click event.
        """
        self.shape_color = color
        self.modified_color = color
        self._update_preview()

    def _color_button(self, color_code: ColorCode) -> QWidget:
        """
        Create a color selection button.
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
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

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

    def _svg_preview_widget(self) -> QWidget:
        """
        Create widget showing the SVG preview (300x300).
        """
        widget = QWidget()
        widget.setFixedSize(300, 300)

        # Create a custom paint event
        #
        # NOTE: QPainter MUST be explicitly ended via .end() at every
        # exit point.  An unended painter left on its paint device
        # corrupts Qt's C++ paint engine, causing SIGSEGV crashes
        # after extended runtime (e.g. hours/days of use).
        def paintEvent(event: "QPaintEvent") -> None:
            painter = QPainter(widget)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Clear background with light gray
            painter.fillRect(widget.rect(), QColor("#c0c0c0"))

            # Draw border
            painter.setPen(QPen(QColor("#cccccc"), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(2, 2, 296, 296)

            # Get SVG content to render
            svg_content = self._get_current_svg_content()
            if not svg_content:
                # Draw placeholder
                painter.setPen(QPen(QColor("#ff0000"), 2))
                painter.setBrush(QBrush(QColor("#ffcccc")))
                painter.drawRect(50, 50, 200, 200)
                painter.drawText(QRectF(50, 50, 200, 200), Qt.AlignmentFlag.AlignCenter, "No SVG content")
                painter.end()
                return

            # Create temporary renderer
            renderer = QtSvg.QSvgRenderer()
            if not renderer.load(QtCore.QByteArray(svg_content.encode("utf-8"))):
                # Draw error placeholder
                painter.setPen(QPen(QColor("#ff0000"), 2))
                painter.setBrush(QBrush(QColor("#ffcccc")))
                painter.drawRect(50, 50, 200, 200)
                painter.drawText(QRectF(50, 50, 200, 200), Qt.AlignmentFlag.AlignCenter, "Invalid SVG")
                painter.end()
                return

            # Calculate scaling to fit within 280x280 area (with 10px margin)
            svg_size = renderer.defaultSize()
            if svg_size.width() > 0 and svg_size.height() > 0:
                target_size = 280
                scale = min(target_size / svg_size.width(), target_size / svg_size.height())
                scaled_width = svg_size.width() * scale
                scaled_height = svg_size.height() * scale
                x_offset = (300 - scaled_width) / 2
                y_offset = (300 - scaled_height) / 2

                # Render the SVG
                renderer.render(painter, QRectF(x_offset, y_offset, scaled_width, scaled_height))

            # Required at every exit path (see note at top of paintEvent)
            painter.end()

        widget.paintEvent = paintEvent
        self.preview_widget = widget
        return widget

    def _get_current_svg_content(self) -> str | None:
        """
        Get current SVG content with modifications applied.
        """
        # Get original content
        content = self.svg_object.get_svg_content()
        if not content:
            return None

        # Apply modifications if any
        color = self.modified_color or self.current_color
        thickness = self.modified_thickness if self.preview_applied else self.current_thickness

        if not color and not thickness:
            return content

        try:
            # Parse XML
            root = ET.fromstring(content)

            # Define namespace
            ns = {"svg": "http://www.w3.org/2000/svg"}

            # Find all shape elements
            elements = []
            for tag in ["path", "rect", "circle", "ellipse", "line", "polyline", "polygon", "g"]:
                elements.extend(root.findall(f".//svg:{tag}", ns) or [])

            # Also include root element for color
            elements.append(root)

            for elem in elements:
                # Apply color if specified
                if color:
                    color_hex = f"#{color}"

                    # Update stroke attribute
                    stroke = elem.get("stroke")
                    if stroke and stroke.lower() not in ("none", "transparent"):
                        elem.set("stroke", color_hex)
                    elif "stroke" in elem.attrib and elem.get("stroke") == "none":
                        pass  # Keep as "none"
                    elif (
                        elem.tag.endswith("path")
                        or elem.tag.endswith("rect")
                        or elem.tag.endswith("circle")
                        or elem.tag.endswith("ellipse")
                        or elem.tag.endswith("line")
                        or elem.tag.endswith("polyline")
                        or elem.tag.endswith("polygon")
                    ):
                        elem.set("stroke", color_hex)

                    # Update fill attribute
                    fill = elem.get("fill")
                    if fill is not None and fill.lower() not in ("none", "transparent"):
                        elem.set("fill", color_hex)

                # Apply thickness if specified and preview is applied
                if thickness and self.preview_applied and elem != root:
                    elem.set("stroke-width", thickness)

            # Convert back to string
            return str(ET.tostring(root, encoding="utf-8").decode("utf-8"))

        except Exception as e:
            self.__logger.error("Error modifying SVG content: %s", e)
            return content

    def _update_preview(self) -> None:
        """Update the preview widget."""
        if self.preview_widget:
            self.preview_widget.update()

    def _apply_preview(self) -> None:
        """Apply thickness changes to preview."""
        if self.thickness_input:
            thickness_text = self.thickness_input.text().strip()
            if thickness_text:
                try:
                    thickness = float(thickness_text)
                    if thickness > 0:
                        self.modified_thickness = thickness_text
                        self.preview_applied = True
                        self._update_preview()
                except ValueError:
                    pass  # Invalid thickness

    def _reset_to_original(self) -> None:
        """Reset to original values."""
        self.modified_color = None
        self.modified_thickness = None
        self.preview_applied = False
        self.shape_color = self.current_color or self.DEFAULT_COLOR

        if self.thickness_input:
            self.thickness_input.setText(self.current_thickness or self.DEFAULT_THICKNESS)

        self._update_preview()

    def _modify_svg_file(self, color: str | None, thickness: str | None) -> str:
        """
        Create modified SVG in cache.

        Returns:
            Cache hash of modified SVG
        """
        # Get SVG content
        content = self.svg_object.get_svg_content()
        if not content:
            # Fallback: create simple SVG
            content = '<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg"><circle cx="100" cy="100" r="70" stroke="black" stroke-width="8" fill="none"/></svg>'

        try:
            # Parse XML
            root = ET.fromstring(content)

            # Define namespace
            ns = {"svg": "http://www.w3.org/2000/svg"}

            # Find all shape elements
            elements = []
            for tag in ["path", "rect", "circle", "ellipse", "line", "polyline", "polygon", "g"]:
                elements.extend(root.findall(f".//svg:{tag}", ns) or [])

            # Also include root element for color
            elements.append(root)

            for elem in elements:
                # Apply color if specified
                if color:
                    color_hex = f"#{color}"

                    # Update stroke attribute
                    stroke = elem.get("stroke")
                    if stroke and stroke.lower() not in ("none", "transparent"):
                        elem.set("stroke", color_hex)
                    elif "stroke" in elem.attrib and elem.get("stroke") == "none":
                        pass  # Keep as "none"
                    elif (
                        elem.tag.endswith("path")
                        or elem.tag.endswith("rect")
                        or elem.tag.endswith("circle")
                        or elem.tag.endswith("ellipse")
                        or elem.tag.endswith("line")
                        or elem.tag.endswith("polyline")
                        or elem.tag.endswith("polygon")
                    ):
                        elem.set("stroke", color_hex)

                    # Update fill attribute
                    fill = elem.get("fill")
                    if fill is not None and fill.lower() not in ("none", "transparent"):
                        elem.set("fill", color_hex)

                # Apply thickness if specified
                if thickness and elem != root:
                    elem.set("stroke-width", thickness)

            # Convert back to string and store in cache
            svg_content = ET.tostring(root, encoding="utf-8").decode("utf-8")
            cache_hash = self._svg_cache.store_svg(svg_content)

            return cache_hash

        except Exception as e:
            self.__logger.error("Error creating modified SVG: %s", e)
            # Fallback: store original content in cache
            return self._svg_cache.store_svg(content)

    def _main_dialog(self) -> QDialog:
        """
        Create and configure the main dialog window.
        """
        dialog = QDialog()
        dialog.setWindowTitle("Modify SVG")
        dialog.resize(800, 600)

        # Create main layout
        main_layout = QHBoxLayout(dialog)

        # Left side: SVG preview
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("SVG Preview:"))

        preview_widget = self._svg_preview_widget()
        left_layout.addWidget(preview_widget)
        left_layout.addStretch()

        # Right side: controls
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(10, 0, 0, 0)

        # Color history
        right_layout.addWidget(QLabel("Color History:"))

        color_scroll = QScrollArea()
        color_scroll.setWidgetResizable(True)
        color_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        color_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        color_scroll.setFrameShape(QFrame.Shape.NoFrame)

        color_container = QWidget()
        color_grid = QGridLayout(color_container)
        color_grid.setSpacing(5)

        # Add color buttons in 2 columns
        for i, code in enumerate(self.color_codes):
            row = i // 2
            col = i % 2
            btn = self._color_button(code)
            btn.setFixedWidth(140)
            color_grid.addWidget(btn, row, col)

        color_scroll.setWidget(color_container)
        right_layout.addWidget(color_scroll)

        # Color input
        right_layout.addWidget(QLabel("Color (hex without #):"))
        self.custom_color_input = QLineEdit()
        self.custom_color_input.setText(self.shape_color)
        self.custom_color_input.textChanged.connect(lambda text: self._color_button_click(text.strip()))
        right_layout.addWidget(self.custom_color_input)

        # Thickness input
        right_layout.addWidget(QLabel("Stroke Thickness:"))
        self.thickness_input = QLineEdit()
        self.thickness_input.setText(self.current_thickness or self.DEFAULT_THICKNESS)
        right_layout.addWidget(self.thickness_input)

        # Apply/Reset buttons
        button_layout = QHBoxLayout()
        apply_btn = QPushButton("Apply Preview")
        apply_btn.clicked.connect(self._apply_preview)
        button_layout.addWidget(apply_btn)

        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self._reset_to_original)
        button_layout.addWidget(reset_btn)

        right_layout.addLayout(button_layout)

        # OK/Cancel buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        right_layout.addWidget(buttons)

        right_layout.addStretch()

        # Add layouts to main layout
        main_layout.addLayout(left_layout, 2)  # 2 parts for preview
        main_layout.addLayout(right_layout, 1)  # 1 part for controls

        return dialog

    def _run_dialog(self) -> DialogResult:
        """
        Run the dialog and return result.

        Returns:
            (ok, cache_hash) where:
            - ok: True if accepted, False if cancelled
            - cache_hash: New cache hash if modified, None if no changes
        """
        # Validate source (show warning if needed)
        if not self._validate_svg_source():
            return False, None

        # For non-cache files, use defaults
        if not (self.is_cache_file or self.is_tmp_file):
            self.current_color = self.DEFAULT_COLOR
            self.current_thickness = self.DEFAULT_THICKNESS
            self.shape_color = self.DEFAULT_COLOR
            self.modified_color = self.DEFAULT_COLOR
            self.modified_thickness = self.DEFAULT_THICKNESS

        # Create and show dialog
        dialog = self._main_dialog()

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Determine final color
            final_color = self.modified_color or self.current_color or self.DEFAULT_COLOR

            # Determine final thickness
            final_thickness = None
            if self.thickness_input:
                thickness_text = self.thickness_input.text().strip()
                if thickness_text:
                    try:
                        thickness = float(thickness_text)
                        if thickness > 0:
                            final_thickness = thickness_text
                    except ValueError:
                        pass

            # Check if any changes were made
            color_changed = final_color != (self.current_color or self.DEFAULT_COLOR)
            thickness_changed = final_thickness != (self.current_thickness or self.DEFAULT_THICKNESS)

            if color_changed or thickness_changed:
                # Create modified SVG in cache
                cache_hash = self._modify_svg_file(final_color, final_thickness)

                # Update color history
                if final_color not in self.color_codes:
                    self.color_codes.append(final_color)
                    # Save color list
                    if "APPDATA" in os.environ:
                        color_dir = os.path.join(os.environ["APPDATA"], "pyzui", "colorstore")
                    else:
                        color_dir = os.path.join(os.path.expanduser("~"), ".pyzui", "colorstore")

                    color_file = os.path.join(color_dir, "color_list.txt")
                    with open(color_file, "w") as f:
                        for code in self.color_codes:
                            f.write(str(code) + "\n")

                return True, cache_hash
            else:
                # No changes made
                return True, None
        else:
            # User cancelled
            return False, None
