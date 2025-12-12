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

import pytest
from unittest.mock import Mock, patch
from PySide6 import QtGui
from pyzui.objects.mediaobjects.stringmediaobject import StringMediaObject
from pyzui.objects.mediaobjects.mediaobject import LoadError

class TestStringMediaObject:
    """
    Feature: String Media Object Rendering

    The StringMediaObject class renders text strings as media objects in the scene.
    It parses color and text from media IDs and provides text rendering with
    customizable colors and multiline support.
    """

    def test_init_valid_color(self):
        """
        Scenario: Initialize with valid hex color

        Given a media ID with valid hex color "FF0000" and text "Hello"
        When StringMediaObject is created
        Then the media_id should be stored
        And the object should be initialized successfully
        """
        scene = Mock()
        obj = StringMediaObject("string:FF0000:Hello", scene)
        assert obj._media_id == "string:FF0000:Hello"

    def test_init_invalid_color(self):
        """
        Scenario: Reject invalid hex color

        Given a media ID with invalid hex color "GGGGGG"
        When StringMediaObject is created
        Then a LoadError should be raised
        And the error message should indicate invalid color
        """
        scene = Mock()
        with pytest.raises(LoadError, match="the supplied colour is invalid"):
            StringMediaObject("string:GGGGGG:Hello", scene)

    def test_transparent_attribute(self):
        """
        Scenario: Check transparency support

        Given the StringMediaObject class
        When accessing the transparent attribute
        Then it should be True
        """
        assert StringMediaObject.transparent is True

    def test_base_pointsize_attribute(self):
        """
        Scenario: Check default font size

        Given the StringMediaObject class
        When accessing the base_pointsize attribute
        Then it should be 24.0 points
        """
        assert StringMediaObject.base_pointsize == 24.0

    def test_inherits_from_mediaobject(self):
        """
        Scenario: Verify inheritance from MediaObject

        Given a StringMediaObject instance
        When checking its type
        Then it should be an instance of MediaObject
        """
        from pyzui.objects.mediaobjects.mediaobject import MediaObject
        scene = Mock()
        obj = StringMediaObject("string:000000:Test", scene)
        assert isinstance(obj, MediaObject)

    def test_parses_text_from_media_id(self):
        """
        Scenario: Parse text from media ID

        Given a media ID "string:000000:HelloWorld"
        When StringMediaObject is created
        Then the text "HelloWorld" should be extracted
        And stored internally as lines
        """
        scene = Mock()
        obj = StringMediaObject("string:000000:HelloWorld", scene)

        # Text should be parsed into lines
        assert obj.lines == [['H', 'e', 'l', 'l', 'o', 'W', 'o', 'r', 'l', 'd']]

    def test_multiline_text_parses_into_separate_lines(self):
        """
        Scenario: Handle multiline text with newlines

        Given a media ID containing "Hello\nWorld"
        When StringMediaObject is created
        Then the text should be split into two lines
        """
        scene = Mock()
        obj = StringMediaObject("string:000000:Hello\nWorld", scene)

        # Should have 2 lines
        assert len(obj.lines) == 2
        assert obj.lines[0] == ['H', 'e', 'l', 'l', 'o']
        assert obj.lines[1] == ['W', 'o', 'r', 'l', 'd']

    def test_multiline_text_with_multiple_newlines(self):
        """
        Scenario: Handle text with multiple newlines

        Given a media ID with "Line1\nLine2\nLine3"
        When StringMediaObject is created
        Then three separate lines should be created
        """
        scene = Mock()
        obj = StringMediaObject("string:000000:Line1\nLine2\nLine3", scene)

        assert len(obj.lines) == 3
        assert obj.lines[0] == ['L', 'i', 'n', 'e', '1']
        assert obj.lines[1] == ['L', 'i', 'n', 'e', '2']
        assert obj.lines[2] == ['L', 'i', 'n', 'e', '3']

    def test_parses_various_colors(self):
        """
        Scenario: Parse different hex colors

        Given media IDs with different valid hex colors
        When StringMediaObjects are created
        Then all should initialize successfully
        """
        scene = Mock()

        # Test various valid colors
        colors = ["000000", "FFFFFF", "FF0000", "00FF00", "0000FF", "123456", "ABCDEF"]
        for color in colors:
            obj = StringMediaObject(f"string:{color}:Test", scene)
            assert obj._media_id == f"string:{color}:Test"

    def test_empty_string_creates_single_empty_line(self):
        """
        Scenario: Handle empty string text

        Given a media ID with no text after color
        When StringMediaObject is created
        Then it should create a single empty line
        """
        scene = Mock()
        obj = StringMediaObject("string:000000:", scene)

        assert len(obj.lines) == 1
        assert obj.lines[0] == []

    def test_text_with_special_characters(self):
        """
        Scenario: Handle special characters in text

        Given a media ID with special characters
        When StringMediaObject is created
        Then special characters should be preserved
        """
        scene = Mock()
        obj = StringMediaObject("string:000000:Hello @#$%!", scene)

        expected_chars = ['H', 'e', 'l', 'l', 'o', ' ', '@', '#', '$', '%', '!']
        assert obj.lines[0] == expected_chars

    def test_zoomlevel_attribute(self):
        """
        Scenario: Verify zoomlevel attribute

        Given a StringMediaObject instance
        When checking the zoomlevel attribute
        Then it should default to 0.0
        """
        scene = Mock()
        obj = StringMediaObject("string:000000:Test", scene)
        assert obj._z == 0.0

    def test_position_attributes(self):
        """
        Scenario: Verify position attributes

        Given a StringMediaObject instance
        When checking position attributes
        Then x and y should default to 0.0
        """
        scene = Mock()
        obj = StringMediaObject("string:000000:Test", scene)
        assert obj._x == 0.0
        assert obj._y == 0.0

    def test_render_method_exists(self):
        """
        Scenario: Verify render method availability

        Given a StringMediaObject instance
        When checking for the render method
        Then the method should exist
        And be callable
        """
        scene = Mock()
        obj = StringMediaObject("string:000000:Test", scene)
        assert hasattr(obj, 'render')
        assert callable(obj.render)

    def test_onscreen_size_property_exists(self):
        """
        Scenario: Verify onscreen_size property availability

        Given the StringMediaObject class
        When checking for the onscreen_size property
        Then the property should exist
        """
        scene = Mock()
        obj = StringMediaObject("string:000000:Test", scene)
        assert hasattr(StringMediaObject, 'onscreen_size')
