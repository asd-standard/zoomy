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

"""TextLayoutData class for storing pre-calculated text layout information.

This class encapsulates all the information needed to render text efficiently
in parallel, including font metrics, bounding rectangles, and layout options.

Thread safety: All data is stored as plain Python types (str, float, int).
Qt GUI objects (QFont, QColor) are only constructed on the main thread in
render() or via the to_qfont()/to_qcolor() convenience methods. This ensures
that TextLayoutData can be safely created and passed between threads without
triggering Qt-internal C++ font database races.
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from PySide6 import QtCore, QtGui


class TextAlignment(Enum):
    """Text alignment options."""

    LEFT = 0
    CENTER = 1
    RIGHT = 2
    JUSTIFY = 3


@dataclass
class TextLayoutData:
    """Stores pre-calculated text layout information for efficient parallel rendering.

    This class encapsulates all the information needed to render text without
    recalculating font metrics, bounding rectangles, or layout options during
    the rendering phase.

    Font and color are stored as plain data (not Qt objects) so that
    TextLayoutData instances can be safely created on any thread.
    Qt objects are only constructed in render() (called from the main thread).
    """

    text: str
    font_family: str = "Sans Serif"
    font_pointsize: float = 12.0
    font_weight: int = QtGui.QFont.Normal
    font_italic: bool = False
    color_r: int = 0
    color_g: int = 0
    color_b: int = 0
    color_a: int = 255
    position: tuple[float, float] = (0.0, 0.0)
    bounding_rect: QtCore.QRectF = field(default_factory=lambda: QtCore.QRectF())
    text_rect: QtCore.QRectF = field(default_factory=lambda: QtCore.QRectF())
    line_rects: list[QtCore.QRectF] = field(default_factory=list)
    alignment: TextAlignment = TextAlignment.LEFT
    rotation: float = 0.0
    scale: float = 1.0
    opacity: float = 1.0
    timestamp: float = field(default_factory=lambda: QtCore.QDateTime.currentMSecsSinceEpoch())
    is_valid: bool = True

    def __post_init__(self):
        """Validate the layout data after initialization."""
        if not self.text:
            raise ValueError("Text cannot be empty")
        if not self.font_family:
            raise ValueError("Font family cannot be empty")
        if self.font_pointsize <= 0:
            raise ValueError("Font point size must be positive")
        if not self.bounding_rect.isValid():
            raise ValueError("Bounding rectangle must be valid")
        if not self.text_rect.isValid():
            raise ValueError("Text rectangle must be valid")

    def to_qfont(self) -> QtGui.QFont:
        """Construct a QFont from the stored plain font data.

        Must be called from the main thread. QFont accesses the global
        system font database, which is not thread-safe.

        Returns:
            QtGui.QFont configured with the stored family, size, weight and italic.
        """
        font = QtGui.QFont(self.font_family)
        font.setPointSizeF(self.font_pointsize)
        font.setWeight(self.font_weight)
        font.setItalic(self.font_italic)
        return font

    def to_qcolor(self) -> QtGui.QColor:
        """Construct a QColor from the stored RGBA values.

        Safe to call from any thread, but typically called from the main
        thread during rendering.

        Returns:
            QtGui.QColor with the stored red, green, blue and alpha.
        """
        return QtGui.QColor(self.color_r, self.color_g, self.color_b, self.color_a)

    @classmethod
    def from_string_object(cls, string_obj: Any, viewport_rect: QtCore.QRectF) -> "TextLayoutData":
        """Create TextLayoutData from a StringMediaObject.

        Thread-safe: extracts plain data from the string object without
        constructing Qt GUI objects. All Qt object construction is deferred
        to render() (main thread).

        Args:
            string_obj: StringMediaObject instance
            viewport_rect: Current viewport rectangle in scene coordinates

        Returns:
            TextLayoutData instance with pre-calculated layout
        """
        # Extract text from the string object
        text = string_obj._get_text()

        # Extract font properties as plain data (NO Qt object construction)
        font_family = "Sans Serif"
        font_pointsize = max(string_obj.base_pointsize * string_obj.scale, 1.0)
        font_weight = QtGui.QFont.Normal
        font_italic = False

        # Extract color components from the pre-existing QColor (read-only access)
        color = string_obj._get_color()
        color_r = color.red()
        color_g = color.green()
        color_b = color.blue()
        color_a = color.alpha()

        # Get position from the object's pos tuple
        pos_x = string_obj.pos[0] if hasattr(string_obj, "pos") else 0.0
        pos_y = string_obj.pos[1] if hasattr(string_obj, "pos") else 0.0
        position = (pos_x, pos_y)

        # Calculate bounding rectangle based on viewport
        # This is a simplified version - actual implementation would use
        # the object's size and scale properties
        width = string_obj.width if hasattr(string_obj, "width") else 100
        height = string_obj.height if hasattr(string_obj, "height") else 50

        bounding_rect = QtCore.QRectF(pos_x - width / 2, pos_y - height / 2, width, height)

        # Calculate text rectangle (tight bounds)
        # In actual implementation, this would use QFontMetrics
        text_rect = QtCore.QRectF(pos_x - width / 2, pos_y - height / 2, width, height)

        # Calculate line rectangles for multiline text
        line_rects = []
        if "\n" in text:
            lines = text.split("\n")
            line_height = height / len(lines)
            for i, _line in enumerate(lines):
                line_rect = QtCore.QRectF(pos_x - width / 2, pos_y - height / 2 + i * line_height, width, line_height)
                line_rects.append(line_rect)

        return cls(
            text=text,
            font_family=font_family,
            font_pointsize=font_pointsize,
            font_weight=font_weight,
            font_italic=font_italic,
            color_r=color_r,
            color_g=color_g,
            color_b=color_b,
            color_a=color_a,
            position=position,
            bounding_rect=bounding_rect,
            text_rect=text_rect,
            line_rects=line_rects,
            alignment=TextAlignment.LEFT,
            rotation=0.0,
            scale=1.0,
            opacity=1.0,
        )

    def distance_to_viewport_center(self, viewport_center: tuple[float, float]) -> float:
        """Calculate distance from text position to viewport center.

        Args:
            viewport_center: (x, y) tuple of viewport center

        Returns:
            Euclidean distance
        """
        dx = self.position[0] - viewport_center[0]
        dy = self.position[1] - viewport_center[1]
        return math.sqrt(dx * dx + dy * dy)

    def is_in_viewport(self, viewport_rect: QtCore.QRectF) -> bool:
        """Check if this text is visible in the current viewport.

        Args:
            viewport_rect: Current viewport rectangle

        Returns:
            True if text is visible, False otherwise
        """
        return bool(self.bounding_rect.intersects(viewport_rect))

    def render(self, painter: QtGui.QPainter) -> None:
        """Render the text using the pre-calculated layout.

        Constructs QFont and QColor on the calling thread (must be the main
        thread for QFont). Uses to_qfont() and to_qcolor() internally.

        Args:
            painter: QPainter object to render with
        """
        if not self.is_valid:
            return

        # Save painter state
        painter.save()

        try:
            # Apply transformations
            if self.rotation != 0.0:
                painter.translate(self.position[0], self.position[1])
                painter.rotate(self.rotation)
                painter.translate(-self.position[0], -self.position[1])

            if self.scale != 1.0:
                painter.translate(self.position[0], self.position[1])
                painter.scale(self.scale, self.scale)
                painter.translate(-self.position[0], -self.position[1])

            # Construct QFont and QColor on this thread (main thread)
            font = self.to_qfont()
            color = self.to_qcolor()
            painter.setFont(font)
            painter.setPen(color)

            # Set opacity if needed
            if self.opacity < 1.0:
                painter.setOpacity(self.opacity)

            # Render text based on alignment
            if self.line_rects:
                # Multiline text
                lines = self.text.split("\n")
                for i, (line, line_rect) in enumerate(zip(lines, self.line_rects, strict=False)):
                    if i < len(self.line_rects):
                        painter.drawText(line_rect, QtCore.Qt.AlignLeft, line)
            else:
                # Single line text
                painter.drawText(self.text_rect, QtCore.Qt.AlignLeft, self.text)

        finally:
            # Restore painter state
            painter.restore()

    def invalidate(self) -> None:
        """Mark this layout data as invalid (e.g., after font change)."""
        self.is_valid = False

    def is_stale(self, max_age_ms: float = 1000.0) -> bool:
        """Check if this layout data is stale and should be recalculated.

        Args:
            max_age_ms: Maximum age in milliseconds before considered stale

        Returns:
            True if stale, False otherwise
        """
        current_time = QtCore.QDateTime.currentMSecsSinceEpoch()
        age = current_time - self.timestamp
        return age > max_age_ms or not self.is_valid

    def __str__(self) -> str:
        """String representation for debugging."""
        return (
            f"TextLayoutData(text='{self.text[:20]}...', "
            f"position={self.position}, "
            f"bounding_rect={self.bounding_rect}, "
            f"is_valid={self.is_valid})"
        )
