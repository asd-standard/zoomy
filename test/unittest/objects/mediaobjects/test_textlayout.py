## PyZUI - Python Zooming User Interface
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

from unittest.mock import Mock

import pytest
from PySide6 import QtCore, QtGui

from pyzui.objects.mediaobjects.stringmediaobject import StringMediaObject
from pyzui.objects.mediaobjects.mediaobjectsutils.string.textlayout import TextAlignment, TextLayoutData


class TestTextLayoutData:
    """
    Feature: Text Layout Data Management

    The TextLayoutData class stores pre-calculated text layout information
    for efficient parallel rendering, including font metrics, bounding
    rectangles, and layout options.
    """

    def test_init_valid_data(self):
        """
        Scenario: Initialize with valid data

        Given valid text, font properties, color, position, and rectangles
        When TextLayoutData is created
        Then all attributes should be set correctly
        And the object should be valid
        """
        text = "Hello World"
        position = (100.0, 200.0)
        bounding_rect = QtCore.QRectF(90, 190, 100, 50)
        text_rect = QtCore.QRectF(95, 195, 90, 40)

        layout_data = TextLayoutData(
            text=text,
            font_family="Arial",
            font_pointsize=12.0,
            font_weight=QtGui.QFont.Normal,
            font_italic=False,
            color_r=255,
            color_g=0,
            color_b=0,
            color_a=255,
            position=position,
            bounding_rect=bounding_rect,
            text_rect=text_rect
        )

        assert layout_data.text == text
        assert layout_data.font_family == "Arial"
        assert layout_data.font_pointsize == 12.0
        assert layout_data.font_weight == QtGui.QFont.Normal
        assert not layout_data.font_italic
        assert layout_data.color_r == 255
        assert layout_data.color_g == 0
        assert layout_data.color_b == 0
        assert layout_data.color_a == 255
        assert layout_data.position == position
        assert layout_data.bounding_rect == bounding_rect
        assert layout_data.text_rect == text_rect
        assert layout_data.is_valid
        assert layout_data.alignment == TextAlignment.LEFT
        assert layout_data.rotation == 0.0
        assert layout_data.scale == 1.0
        assert layout_data.opacity == 1.0

    def test_init_invalid_data(self):
        """
        Scenario: Reject invalid data

        Given invalid data (empty text, empty font family, etc.)
        When TextLayoutData is created
        Then ValueError should be raised
        """
        position = (100.0, 200.0)
        bounding_rect = QtCore.QRectF(90, 190, 100, 50)
        text_rect = QtCore.QRectF(95, 195, 90, 40)

        # Test empty text
        with pytest.raises(ValueError, match="Text cannot be empty"):
            TextLayoutData(
                text="",
                font_family="Arial",
                font_pointsize=12.0,
                color_r=255,
                color_g=0,
                color_b=0,
                position=position,
                bounding_rect=bounding_rect,
                text_rect=text_rect
            )

        # Test empty font family
        with pytest.raises(ValueError, match="Font family cannot be empty"):
            TextLayoutData(
                text="Hello",
                font_family="",
                font_pointsize=12.0,
                color_r=255,
                color_g=0,
                color_b=0,
                position=position,
                bounding_rect=bounding_rect,
                text_rect=text_rect
            )

        # Test invalid point size
        with pytest.raises(ValueError, match="Font point size must be positive"):
            TextLayoutData(
                text="Hello",
                font_family="Arial",
                font_pointsize=0.0,
                color_r=255,
                color_g=0,
                color_b=0,
                position=position,
                bounding_rect=bounding_rect,
                text_rect=text_rect
            )

        # Test invalid bounding rectangle
        with pytest.raises(ValueError, match="Bounding rectangle must be valid"):
            TextLayoutData(
                text="Hello",
                font_family="Arial",
                font_pointsize=12.0,
                color_r=255,
                color_g=0,
                color_b=0,
                position=position,
                bounding_rect=QtCore.QRectF(),
                text_rect=text_rect
            )

    def test_from_string_object(self):
        """
        Scenario: Create from StringMediaObject

        Given a StringMediaObject instance
        When TextLayoutData.from_string_object is called
        Then a TextLayoutData instance should be created
        And it should contain the object's text, font properties,
            and color extracted as plain data (no Qt objects)
        """
        # Create a mock StringMediaObject
        mock_string_obj = Mock(spec=StringMediaObject)
        mock_string_obj._get_text.return_value = "Test Text"
        mock_string_obj._get_color.return_value = QtGui.QColor(0, 255, 0)
        mock_string_obj.base_pointsize = 24.0
        mock_string_obj.scale = 1.0
        mock_string_obj.pos = (100.0, 200.0)
        mock_string_obj.width = 80.0
        mock_string_obj.height = 40.0

        viewport_rect = QtCore.QRectF(0, 0, 800, 600)

        layout_data = TextLayoutData.from_string_object(mock_string_obj, viewport_rect)

        assert layout_data.text == "Test Text"
        # Font properties are extracted as plain data (no QFont construction)
        assert layout_data.font_family == "Sans Serif"
        assert layout_data.font_pointsize == pytest.approx(24.0)
        assert layout_data.font_weight == QtGui.QFont.Normal
        assert not layout_data.font_italic
        # Color is extracted as RGBA components
        assert layout_data.color_r == 0
        assert layout_data.color_g == 255
        assert layout_data.color_b == 0
        assert layout_data.color_a == 255
        assert layout_data.position == (100.0, 200.0)
        assert layout_data.is_valid

    def test_distance_to_viewport_center(self):
        """
        Scenario: Calculate distance to viewport center

        Given a TextLayoutData with position (100, 200)
        When distance_to_viewport_center is called with viewport center (150, 250)
        Then the correct Euclidean distance should be returned
        """
        layout_data = TextLayoutData(
            text="Test",
            font_family="Arial",
            font_pointsize=12.0,
            color_r=255,
            color_g=0,
            color_b=0,
            position=(100.0, 200.0),
            bounding_rect=QtCore.QRectF(90, 190, 20, 20),
            text_rect=QtCore.QRectF(95, 195, 10, 10)
        )

        viewport_center = (150.0, 250.0)
        distance = layout_data.distance_to_viewport_center(viewport_center)

        # Calculate expected distance: sqrt((100-150)² + (200-250)²) = sqrt(2500 + 2500) = sqrt(5000) ≈ 70.71
        expected_distance = ((50**2 + 50**2) ** 0.5)
        assert distance == pytest.approx(expected_distance, rel=1e-9)

    def test_is_in_viewport(self):
        """
        Scenario: Check if text is in viewport

        Given a TextLayoutData with bounding rectangle
        When is_in_viewport is called with viewport rectangle
        Then it should return True if intersecting, False otherwise
        """
        layout_data = TextLayoutData(
            text="Test",
            font_family="Arial",
            font_pointsize=12.0,
            color_r=255,
            color_g=0,
            color_b=0,
            position=(100.0, 200.0),
            bounding_rect=QtCore.QRectF(90, 190, 20, 20),
            text_rect=QtCore.QRectF(95, 195, 10, 10)
        )

        # Test intersecting viewport
        viewport_rect = QtCore.QRectF(0, 0, 200, 300)
        assert layout_data.is_in_viewport(viewport_rect)

        # Test non-intersecting viewport
        viewport_rect = QtCore.QRectF(500, 500, 100, 100)
        assert not layout_data.is_in_viewport(viewport_rect)

    def test_invalidate(self):
        """
        Scenario: Invalidate layout data

        Given a valid TextLayoutData
        When invalidate is called
        Then is_valid should be False
        """
        layout_data = TextLayoutData(
            text="Test",
            font_family="Arial",
            font_pointsize=12.0,
            color_r=255,
            color_g=0,
            color_b=0,
            position=(100.0, 200.0),
            bounding_rect=QtCore.QRectF(90, 190, 20, 20),
            text_rect=QtCore.QRectF(95, 195, 10, 10)
        )

        assert layout_data.is_valid
        layout_data.invalidate()
        assert not layout_data.is_valid

    def test_is_stale(self):
        """
        Scenario: Check if layout data is stale

        Given a TextLayoutData
        When is_stale is called
        Then it should return True if older than max age, False otherwise
        """
        layout_data = TextLayoutData(
            text="Test",
            font_family="Arial",
            font_pointsize=12.0,
            color_r=255,
            color_g=0,
            color_b=0,
            position=(100.0, 200.0),
            bounding_rect=QtCore.QRectF(90, 190, 20, 20),
            text_rect=QtCore.QRectF(95, 195, 10, 10)
        )

        # Should not be stale immediately
        assert not layout_data.is_stale(max_age_ms=1000)

        # Make it stale by setting old timestamp
        old_timestamp = QtCore.QDateTime.currentMSecsSinceEpoch() - 2000  # 2 seconds ago
        layout_data.timestamp = old_timestamp

        # Should be stale now
        assert layout_data.is_stale(max_age_ms=1000)

    def test_render(self):
        """
        Scenario: Render text using layout data

        Given a TextLayoutData and a QPainter
        When render is called
        Then the painter should be used to draw the text
        And QFont/QColor should be constructed on the calling thread
        """
        layout_data = TextLayoutData(
            text="Test",
            font_family="Arial",
            font_pointsize=12.0,
            color_r=255,
            color_g=0,
            color_b=0,
            color_a=255,
            position=(100.0, 200.0),
            bounding_rect=QtCore.QRectF(90, 190, 20, 20),
            text_rect=QtCore.QRectF(95, 195, 10, 10)
        )

        # Create a mock painter
        mock_painter = Mock()
        mock_painter.save = Mock()
        mock_painter.restore = Mock()
        mock_painter.setFont = Mock()
        mock_painter.setPen = Mock()
        mock_painter.drawText = Mock()

        # Render the text
        layout_data.render(mock_painter)

        # Verify painter methods were called
        mock_painter.save.assert_called_once()
        mock_painter.restore.assert_called_once()
        mock_painter.setFont.assert_called_once()
        mock_painter.setPen.assert_called_once()
        mock_painter.drawText.assert_called_once()

        # Verify QFont was constructed with correct properties
        font_arg = mock_painter.setFont.call_args[0][0]
        assert isinstance(font_arg, QtGui.QFont)
        assert font_arg.family() == "Arial"
        assert font_arg.pointSizeF() == pytest.approx(12.0)

        # Verify QColor was constructed with correct properties
        pen_arg = mock_painter.setPen.call_args[0][0]
        assert isinstance(pen_arg, QtGui.QColor)
        assert pen_arg.red() == 255
        assert pen_arg.green() == 0
        assert pen_arg.blue() == 0
        assert pen_arg.alpha() == 255

    def test_render_multiline(self):
        """
        Scenario: Render multiline text

        Given a TextLayoutData with multiline text and line rectangles
        When render is called
        Then each line should be rendered separately
        """
        layout_data = TextLayoutData(
            text="Line1\nLine2\nLine3",
            font_family="Arial",
            font_pointsize=12.0,
            color_r=255,
            color_g=0,
            color_b=0,
            position=(100.0, 200.0),
            bounding_rect=QtCore.QRectF(90, 190, 60, 60),
            text_rect=QtCore.QRectF(95, 195, 50, 50),
            line_rects=[
                QtCore.QRectF(95, 195, 50, 15),
                QtCore.QRectF(95, 210, 50, 15),
                QtCore.QRectF(95, 225, 50, 15)
            ]
        )

        # Create a mock painter
        mock_painter = Mock()
        mock_painter.save = Mock()
        mock_painter.restore = Mock()
        mock_painter.setFont = Mock()
        mock_painter.setPen = Mock()
        mock_painter.drawText = Mock()

        # Render the text
        layout_data.render(mock_painter)

        # Verify drawText was called 3 times (once per line)
        assert mock_painter.drawText.call_count == 3

    def test_render_with_transformations(self):
        """
        Scenario: Render text with transformations

        Given a TextLayoutData with rotation and scale
        When render is called
        Then the painter should apply transformations
        """
        layout_data = TextLayoutData(
            text="Test",
            font_family="Arial",
            font_pointsize=12.0,
            color_r=255,
            color_g=0,
            color_b=0,
            position=(100.0, 200.0),
            bounding_rect=QtCore.QRectF(90, 190, 20, 20),
            text_rect=QtCore.QRectF(95, 195, 10, 10),
            rotation=45.0,
            scale=1.5,
            opacity=0.8
        )

        # Create a mock painter
        mock_painter = Mock()
        mock_painter.save = Mock()
        mock_painter.restore = Mock()
        mock_painter.setFont = Mock()
        mock_painter.setPen = Mock()
        mock_painter.drawText = Mock()
        mock_painter.translate = Mock()
        mock_painter.rotate = Mock()
        mock_painter.scale = Mock()
        mock_painter.setOpacity = Mock()

        # Render the text
        layout_data.render(mock_painter)

        # Verify transformations were applied
        assert mock_painter.translate.call_count >= 2  # For rotation and scale
        mock_painter.rotate.assert_called_once_with(45.0)
        mock_painter.scale.assert_called_once_with(1.5, 1.5)
        mock_painter.setOpacity.assert_called_once_with(0.8)

    def test_str_representation(self):
        """
        Scenario: String representation

        Given a TextLayoutData
        When str() is called
        Then a descriptive string should be returned
        """
        layout_data = TextLayoutData(
            text="Hello World this is a long text",
            font_family="Arial",
            font_pointsize=12.0,
            color_r=255,
            color_g=0,
            color_b=0,
            position=(100.0, 200.0),
            bounding_rect=QtCore.QRectF(90, 190, 20, 20),
            text_rect=QtCore.QRectF(95, 195, 10, 10)
        )

        str_repr = str(layout_data)
        assert "TextLayoutData" in str_repr
        assert "text='Hello World this is ..." in str_repr  # Truncated
        assert "position=(100.0, 200.0)" in str_repr
        assert "is_valid=True" in str_repr

    def test_to_qfont_constructs_correctly(self):
        """
        Scenario: Convert plain font data to QFont

        Given a TextLayoutData with plain font data
        When to_qfont() is called
        Then a correctly configured QFont should be returned
        """
        layout_data = TextLayoutData(
            text="Test",
            font_family="Courier",
            font_pointsize=18.0,
            font_weight=QtGui.QFont.Bold,
            font_italic=True,
            color_r=0,
            color_g=128,
            color_b=255,
            color_a=200,
            position=(0.0, 0.0),
            bounding_rect=QtCore.QRectF(0, 0, 100, 50),
            text_rect=QtCore.QRectF(0, 0, 90, 40)
        )

        font = layout_data.to_qfont()
        assert isinstance(font, QtGui.QFont)
        assert font.family() == "Courier"
        assert font.pointSizeF() == pytest.approx(18.0)
        assert font.weight() == QtGui.QFont.Bold
        assert font.italic()

    def test_to_qcolor_constructs_correctly(self):
        """
        Scenario: Convert plain color data to QColor

        Given a TextLayoutData with plain RGBA data
        When to_qcolor() is called
        Then a correctly configured QColor should be returned
        """
        layout_data = TextLayoutData(
            text="Test",
            font_family="Arial",
            font_pointsize=12.0,
            color_r=10,
            color_g=20,
            color_b=30,
            color_a=128,
            position=(0.0, 0.0),
            bounding_rect=QtCore.QRectF(0, 0, 100, 50),
            text_rect=QtCore.QRectF(0, 0, 90, 40)
        )

        color = layout_data.to_qcolor()
        assert isinstance(color, QtGui.QColor)
        assert color.red() == 10
        assert color.green() == 20
        assert color.blue() == 30
        assert color.alpha() == 128
