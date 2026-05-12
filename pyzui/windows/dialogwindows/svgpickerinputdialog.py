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

"""SVG picker input dialog with color selection."""

import os
import xml.etree.ElementTree as ET
from collections import deque
from typing import TYPE_CHECKING, Any

from PySide6 import QtSvg
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
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

# Type aliases
ColorCode = str
DialogResult = tuple[bool, str]


class OpenSVGPickerInputDialog:
    """
    Constructor :
        OpenSVGPickerInputDialog()
    Parameters :
        None

    OpenSVGPickerInputDialog() --> None

    Gather SVG file selection through a dialog with color selection.
    Also gives a selection column of the last 20 used colors.
    """

    # SVG directory relative to project root
    SVG_DIR: str = "../data/SVG"

    # All available SVG files (populated in __init__)
    SVG_FILES: list[str] = []

    # SVG display names (filename without extension)
    SVG_NAMES: dict[str, str] = {}

    # Default SVG thickness
    DEFAULT_SVG_THICKNESS: str = "50"

    def __init__(self) -> None:
        """
        Constructor :
            OpenSVGPickerInputDialog()
        Parameters :
            None

        OpenSVGPickerInputDialog() --> None

        Create a new OpenSVGPickerInputDialog for gathering SVG file selection with color selection.

        Initializes the dialog with empty color, loads previously used colors
        from the color store file, or creates default colors (red, green, blue) if
        no color history exists. Also scans the SVG directory for available SVG files.
        """
        self.shape_color: str = ""
        self.selected_svg: str = ""
        self.__logger = get_logger("OpenSVGPickerInputDialog")
        self.color_codes: deque[ColorCode] = deque(maxlen=24)
        self.custom_color_input: Any = None  # Will be QLineEdit if needed
        self.thickness_input: Any = None  # Will be QLineEdit for thickness
        self._svg_buttons: dict[str, QPushButton] = {}
        self._svg_colors: dict[str, str] = {}  # Store color for each SVG
        self._svg_thicknesses: dict[str, str] = {}  # Store thickness for each SVG
        self._svg_contents: dict[str, str] = {}  # Store original SVG content
        self._svg_renderers: dict[str, QtSvg.QSvgRenderer] = {}  # Store renderers
        self._modified_svg_files: dict[str, str] = {}  # Store cache hashes of modified SVG files

        # Scan SVG directory
        self.SVG_FILES = []
        self.SVG_NAMES = {}
        svg_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "SVG")
        svg_dir = os.path.abspath(svg_dir)
        if os.path.isdir(svg_dir):
            for filename in os.listdir(svg_dir):
                if filename.lower().endswith(".svg"):
                    filepath = os.path.join(svg_dir, filename)
                    self.SVG_FILES.append(filepath)
                    self.SVG_NAMES[filepath] = filename[:-4]  # remove .svg extension

        # Initialize default thickness for all SVGs
        for svg_path in self.SVG_FILES:
            self._svg_thicknesses[svg_path] = self.DEFAULT_SVG_THICKNESS

        # Initialize default color (white) for all SVGs
        for svg_path in self.SVG_FILES:
            self._svg_colors[svg_path] = "ffffff"

        # Initialize SVG cache
        self._svg_cache = get_svg_cache()

        ## set the default tilestore directory, this can be overridden if required
        if "APPDATA" in os.environ:
            ## Windows
            self.color_dir = os.path.join(os.environ["APPDATA"], "pyzui", "colorstore")
        else:
            ## Unix
            self.color_dir = os.path.join(os.path.expanduser("~"), ".pyzui", "colorstore")

        if os.path.isfile(self.color_dir + "/color_list.txt"):
            with open(self.color_dir + "/color_list.txt") as f:
                for line in f:
                    stripline = line.strip()
                    stripline = stripline.lower()
                    if len(stripline) == 6 and stripline not in self.color_codes:
                        self.color_codes.append(stripline)

        else:
            if os.path.isdir(self.color_dir):
                f = open(self.color_dir + "/color_list.txt", "w")
                self.color_codes.append("ffffff")
                f.write("ffffff\n")
                self.color_codes.append("ff0000")
                f.write("ff0000\n")
                self.color_codes.append("00ff00")
                f.write("00ff00\n")
                self.color_codes.append("0000ff")
                f.write("0000ff\n")
                f.close()
            else:
                os.mkdir(self.color_dir)
                f = open(self.color_dir + "/color_list.txt", "w")
                self.color_codes.append("ffffff")
                f.write("ffffff\n")
                self.color_codes.append("ff0000")
                f.write("ff0000\n")
                self.color_codes.append("00ff00")
                f.write("00ff00\n")
                self.color_codes.append("0000ff")
                f.write("0000ff\n")
                f.close()

    def _modify_svg_file(self, svg_path: str, color: str | None = None, thickness: str | None = None) -> str:
        """
        Modify an SVG file with new color and/or thickness using XML parsing.

        Args:
            svg_path: Path to the original SVG file
            color: Hex color code (without #) to apply to stroke and fill
            thickness: Stroke width value

        Returns:
            Cache hash of modified SVG (format: svg_{8_char_hex})
        """
        try:
            # Parse the SVG file
            tree = ET.parse(svg_path)
            root = tree.getroot()

            # Define SVG namespace
            ns = {"svg": "http://www.w3.org/2000/svg"}

            # Find all elements that can have stroke and fill attributes
            # This includes: path, rect, circle, ellipse, line, polyline, polygon
            elements = []
            for tag in ["path", "rect", "circle", "ellipse", "line", "polyline", "polygon", "g"]:
                elements.extend(root.findall(f".//svg:{tag}", ns) or [])

            # Also include the root svg element itself (for color only, not stroke-width)
            elements.append(root)

            for elem in elements:
                # Apply color if specified
                if color:
                    color_hex = f"#{color}"

                    # Update stroke attribute if it exists and is not "none"
                    stroke = elem.get("stroke")
                    if stroke and stroke.lower() not in ("none", "transparent"):
                        elem.set("stroke", color_hex)
                    elif "stroke" in elem.attrib and elem.get("stroke") == "none":
                        # Keep as "none" - don't add color to outlines that should be invisible
                        pass
                    elif (
                        elem.tag.endswith("path")
                        or elem.tag.endswith("rect")
                        or elem.tag.endswith("circle")
                        or elem.tag.endswith("ellipse")
                        or elem.tag.endswith("line")
                        or elem.tag.endswith("polyline")
                        or elem.tag.endswith("polygon")
                    ):
                        # For shape elements without stroke attribute, add it
                        elem.set("stroke", color_hex)

                    # Update fill attribute if it exists
                    fill = elem.get("fill")
                    if fill is not None:
                        # Only update if not "none" or "transparent"
                        if fill.lower() not in ("none", "transparent"):
                            elem.set("fill", color_hex)
                    # Note: we don't add fill to elements that don't have it
                    # to avoid filling outlines that should remain empty

                # Apply thickness if specified
                # Don't apply stroke-width to root svg element, only to shape elements
                if thickness and elem != root:
                    # Update stroke-width attribute
                    elem.set("stroke-width", thickness)

            # Convert to string and store in cache
            svg_content = ET.tostring(root, encoding="utf-8").decode("utf-8")
            cache_hash = self._svg_cache.store_svg(svg_content)

            return cache_hash

        except Exception as e:
            # If XML parsing fails, re-raise the exception
            self.__logger.error("Error modifying SVG file %s: %s", svg_path, e)
            raise

    def _color_square(self, color_code: ColorCode) -> QWidget:
        """
        Method :
            OpenSVGPickerInputDialog._color_square(color_code)
        Parameters :
            color_code : str

        OpenSVGPickerInputDialog._color_square(color_code) --> QWidget

        Creates a colored square widget.
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
        Method :
            OpenSVGPickerInputDialog._color_button_click(color)
        Parameters :
            color : str

        OpenSVGPickerInputDialog._color_button_click(color) --> None

        Handles color button click event.
        """
        self.shape_color = color

    def _color_button(self, color_code: ColorCode) -> QWidget:
        """
        Method :
            OpenSVGPickerInputDialog._color_button(color_code)
        Parameters :
            color_code : str

        OpenSVGPickerInputDialog._color_button(color_code) --> QWidget

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

    def _svg_widget(self, svg_path: str) -> QWidget:
        """
        Create a widget that displays an SVG preview and acts as a button.
        """
        widget = QWidget()
        # Increased size to accommodate larger preview and label
        widget.setFixedSize(140, 140)

        # Create a button that will fill most of the widget (leaving space for label)
        button = QPushButton(widget)
        button.setFixedSize(140, 120)  # 120 height leaves 20 for label
        button.setFlat(True)  # Remove default button styling
        button.setStyleSheet("background-color: transparent; border: none;")  # Make transparent
        self._svg_buttons[svg_path] = button

        # Load and store original SVG content
        with open(svg_path) as f:
            self._svg_contents[svg_path] = f.read()

        # Create initial renderer with default color and thickness applied
        renderer = self._create_modified_svg_renderer(svg_path)

        # Create a custom paint event for the button to draw the SVG
        #
        # NOTE: painter.end() at the bottom is required.  An unended
        # QPainter corrupts Qt's C++ paint engine state, which can
        # trigger a SIGSEGV crash after the app runs for many hours.
        def paintEvent(arg__1: "QPaintEvent") -> None:
            painter = QPainter(button)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Clear background with dark gray for better visibility of white outlines
            painter.fillRect(button.rect(), QColor("#404040"))

            # Draw SVG centered and scaled to fit button
            # Use colored renderer if available, otherwise use original
            current_renderer = self._svg_renderers.get(svg_path, renderer)

            if current_renderer.isValid():
                # Calculate scaling to fit within 80x80 area (further reduced to prevent overflow)
                svg_size = current_renderer.defaultSize()
                if svg_size.width() > 0 and svg_size.height() > 0:
                    target_size = 80  # Further reduced to ensure no overflow
                    scale = min(target_size / svg_size.width(), target_size / svg_size.height())
                    scaled_width = svg_size.width() * scale
                    scaled_height = svg_size.height() * scale
                    x_offset = (140 - scaled_width) / 2
                    y_offset = (120 - scaled_height) / 2  # Center in button area (120 height)

                    # Set clipping region to prevent overflow (10px margins for safety)
                    # painter.setClipRect(QRectF(4, 4, 130, 110))

                    # Render the SVG (already colored if apply was clicked)
                    current_renderer.render(painter, QRectF(x_offset, y_offset, scaled_width, scaled_height))

                else:
                    # Draw placeholder for zero-dimension SVG
                    painter.setPen(QPen(QColor("#ff0000"), 2))
                    painter.setBrush(QBrush(QColor("#ffcccc")))
                    painter.drawRect(30, 20, 80, 80)
                    painter.drawText(QRectF(30, 20, 80, 80), Qt.AlignmentFlag.AlignCenter, "Invalid SVG")
            else:
                # Draw placeholder for invalid SVG
                painter.setPen(QPen(QColor("#ff0000"), 2))
                painter.setBrush(QBrush(QColor("#ffcccc")))
                painter.drawRect(30, 20, 80, 80)
                painter.drawText(QRectF(30, 20, 80, 80), Qt.AlignmentFlag.AlignCenter, "Invalid SVG")

            # Draw selection border if this SVG is selected
            if self.selected_svg == svg_path:
                painter.setPen(QPen(QColor("#0000ff"), 3))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                # Draw selection rectangle only around button area (140x120), not including label
                painter.drawRect(2, 2, 136, 116)

            painter.end()

        button.paintEvent = paintEvent

        # Connect click
        button.clicked.connect(lambda: self._svg_button_click(svg_path))

        # Add label below button with dedicated space
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)  # No spacing between button and label

        # Add button (takes most of the space)
        layout.addWidget(button)

        # Add label in dedicated space at bottom
        filename = os.path.basename(svg_path)
        display_name = filename[:-4] if filename.lower().endswith(".svg") else filename
        label = QLabel(display_name)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFixedHeight(20)  # Dedicated space for label
        label.setStyleSheet("QLabel { background-color: #f0f0f0; border-top: 1px solid #cccccc; color: #000000; }")
        layout.addWidget(label)

        return widget

    def _svg_button_click(self, svg_path: str) -> None:
        """
        Handle SVG button click event.
        """
        old_selection = self.selected_svg
        self.selected_svg = svg_path
        # Force repaint of both previously selected and newly selected buttons
        if hasattr(self, "_svg_buttons"):
            if old_selection in self._svg_buttons:
                self._svg_buttons[old_selection].update()
            if svg_path in self._svg_buttons:
                self._svg_buttons[svg_path].update()

    def _create_modified_svg_renderer(self, svg_path: str, force_update: bool = False) -> QtSvg.QSvgRenderer:
        """
        Create a modified SVG renderer with color and thickness applied.
        Uses XML parsing instead of regex for more reliable modification.

        Args:
            svg_path: Path to the SVG file
            force_update: If True, always create new renderer even if cached
        """
        # Get color and thickness for this SVG
        color = self._svg_colors.get(svg_path)
        thickness = self._svg_thicknesses.get(svg_path)

        # Always create modified SVG file if we have color or thickness
        # Don't cache based on original file since modifications change the renderer
        if color or thickness:
            # Create modified SVG and get cache hash
            cache_hash = self._modify_svg_file(svg_path, color, thickness)

            # Store the cache hash for later use
            self._modified_svg_files[svg_path] = cache_hash

            # Get cache path and create renderer
            cache_path = self._svg_cache.get_cache_path(cache_hash)
            renderer = QtSvg.QSvgRenderer(str(cache_path))
            self._svg_renderers[svg_path] = renderer
            return renderer
        else:
            # No modifications, use original SVG
            if force_update or svg_path not in self._svg_renderers:
                self._svg_renderers[svg_path] = QtSvg.QSvgRenderer(svg_path)
            return self._svg_renderers[svg_path]

    def _apply_color_to_svg(self) -> None:
        """
        Apply the selected color to the selected SVG preview.
        """
        if not self.selected_svg:
            return  # No SVG selected

        if not self.shape_color:
            return  # No color selected

        # Store the color for this SVG
        self._svg_colors[self.selected_svg] = self.shape_color

        # Create modified renderer with color (and thickness if any)
        modified_renderer = self._create_modified_svg_renderer(self.selected_svg)
        self._svg_renderers[self.selected_svg] = modified_renderer

        # Force repaint of the selected SVG button
        if self.selected_svg in self._svg_buttons:
            self._svg_buttons[self.selected_svg].update()

    def _apply_thickness_to_svg(self) -> None:
        """
        Apply the entered thickness to the selected SVG preview.
        """
        if not self.selected_svg:
            return  # No SVG selected

        if not self.thickness_input:
            return  # No thickness input widget

        thickness_text = self.thickness_input.text().strip()
        if not thickness_text:
            return  # No thickness entered

        # Validate thickness is a positive number
        try:
            thickness = float(thickness_text)
            if thickness <= 0:
                return  # Invalid thickness
        except ValueError:
            return  # Not a valid number

        # Store the thickness for this SVG
        self._svg_thicknesses[self.selected_svg] = thickness_text

        # Create modified renderer with thickness (and color if any)
        modified_renderer = self._create_modified_svg_renderer(self.selected_svg)
        self._svg_renderers[self.selected_svg] = modified_renderer

        # Force repaint of the selected SVG button
        if self.selected_svg in self._svg_buttons:
            self._svg_buttons[self.selected_svg].update()

    def _apply_changes_to_svg(self) -> None:
        """
        Apply both color and thickness changes to the selected SVG preview.
        """
        if not self.selected_svg:
            return  # No SVG selected

        applied_changes = False

        # Apply color if selected
        if self.shape_color:
            self._svg_colors[self.selected_svg] = self.shape_color
            applied_changes = True

        # Apply thickness if entered
        if self.thickness_input:
            thickness_text = self.thickness_input.text().strip()
            if thickness_text:
                try:
                    thickness = float(thickness_text)
                    if thickness > 0:
                        self._svg_thicknesses[self.selected_svg] = thickness_text
                        applied_changes = True
                except ValueError:
                    pass  # Invalid thickness, ignore

        if applied_changes:
            # Create modified renderer with all changes
            modified_renderer = self._create_modified_svg_renderer(self.selected_svg)
            self._svg_renderers[self.selected_svg] = modified_renderer

            # Force repaint of the selected SVG button
            if self.selected_svg in self._svg_buttons:
                self._svg_buttons[self.selected_svg].update()

    def _main_dialog(self) -> QDialog:
        """
        Method :
            OpenSVGPickerInputDialog._main_dialog()
        Parameters :
            None

        OpenSVGPickerInputDialog._main_dialog() --> QDialog

        Creates and configures the main dialog window.
        """
        dialog = QDialog()
        dialog.setWindowTitle("Select SVG:")
        dialog.resize(800, 800)  # Increased size for larger previews

        # Create SVG selection grid
        svg_container = QWidget()
        svg_layout = QGridLayout(svg_container)
        svg_layout.setSpacing(15)
        svg_layout.setContentsMargins(10, 10, 10, 10)

        # Add SVG buttons in 3 columns
        if not self.SVG_FILES:
            label = QLabel("No SVG files found in data/SVG directory")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            svg_layout.addWidget(label, 0, 0, 1, 3)
        else:
            for i, svg_path in enumerate(self.SVG_FILES):
                row = i // 3
                col = i % 3
                svg_widget = self._svg_widget(svg_path)
                svg_layout.addWidget(svg_widget, row, col)

        # Add stretch to fill remaining space
        svg_layout.setRowStretch(svg_layout.rowCount(), 1)

        # Create scroll area for SVG grid
        scroll_area = QScrollArea()
        scroll_area.setWidget(svg_container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Create a text input field for custom color entry (optional)
        from PySide6.QtWidgets import QLineEdit

        self.custom_color_input = QLineEdit(dialog)
        self.custom_color_input.setPlaceholderText("Enter custom color (e.g., #ff5733)")

        # Create a text input field for SVG thickness
        self.thickness_input = QLineEdit(dialog)
        self.thickness_input.setPlaceholderText(f"Enter SVG thickness (default: {self.DEFAULT_SVG_THICKNESS})")
        # self.thickness_input.setText(self.DEFAULT_SVG_THICKNESS)  # Set default value
        self.thickness_input.returnPressed.connect(self._apply_thickness_to_svg)

        # Create OK/Cancel buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        # Layout setup
        main_layout = QHBoxLayout(dialog)

        # Left side: SVG selection
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Select SVG:"))
        left_layout.addWidget(scroll_area)
        left_layout.addWidget(QLabel("Custom color:"))
        left_layout.addWidget(self.custom_color_input)
        left_layout.addWidget(QLabel("SVG thickness:"))
        left_layout.addWidget(self.thickness_input)
        left_layout.addWidget(buttons)

        # Right side: color selection
        color_layout = QVBoxLayout()
        color_layout.setContentsMargins(0, 0, 0, 0)
        color_layout.setSpacing(2)
        color_layout.addWidget(QLabel("Color history:"))

        for code in self.color_codes:
            btn = self._color_button(code)
            btn.setFixedWidth(120)
            color_layout.addWidget(btn)

        # Add apply button to preview SVG with selected color and thickness
        apply_button = QPushButton("Apply Changes")
        apply_button.clicked.connect(self._apply_changes_to_svg)
        color_layout.addWidget(apply_button)

        color_layout.addStretch()

        # Add layouts to main layout
        main_layout.addLayout(left_layout, 3)  # 3 parts for SVG
        main_layout.addLayout(color_layout, 1)  # 1 part for colors

        return dialog

    def _run_dialog(self) -> DialogResult:
        """
        Method :
            OpenSVGPickerInputDialog._run_dialog()
        Parameters :
            None

        OpenSVGPickerInputDialog._run_dialog() --> Tuple[bool, str]

        Runs the dialog and returns the result.
        Returns (ok, filepath) where ok is True if accepted, filepath is the selected SVG file path.
        """
        dialog = self._main_dialog()
        # Run dialog and get result
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Determine final color (optional, kept for color history)
            final_color = self.shape_color
            if len(final_color) != 6:
                # Try custom color input
                if self.custom_color_input:
                    color_text = self.custom_color_input.text().strip()
                    if color_text:
                        if color_text.startswith("#"):
                            color_text = color_text[1:]
                        if len(color_text) == 6:
                            final_color = color_text
            # If still no valid color, default to white
            if len(final_color) != 6:
                final_color = "ffffff"

            # Check if SVG is selected
            if not self.selected_svg:
                # No SVG selected, return empty
                ok = False
                return ok, ""

            # Append color to history if not already present
            if final_color not in self.color_codes:
                self.color_codes.append(final_color)
                # Save color list
                with open(self.color_dir + "/color_list.txt", "w") as f:
                    for code in self.color_codes:
                        f.write(str(code) + "\n")

            # Get thickness if entered
            thickness = None
            if self.thickness_input:
                thickness_text = self.thickness_input.text().strip()
                if thickness_text:
                    try:
                        thickness_val = float(thickness_text)
                        if thickness_val > 0:
                            thickness = thickness_text
                    except ValueError:
                        pass  # Invalid thickness, ignore

            # Create final modified SVG file with all changes
            cache_hash = self._modify_svg_file(self.selected_svg, final_color, thickness)

            # Return cache hash
            ok = True
            return ok, cache_hash
        else:
            ok = False
            return ok, ""
