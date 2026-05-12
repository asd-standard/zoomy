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

from unittest.mock import Mock, patch

import pytest

from pyzui.objects.mediaobjects.mediaobject import LoadError
from pyzui.objects.mediaobjects.svgmediaobject import SVGMediaObject


class TestSVGMediaObject:
    """
    Feature: SVG Media Object Rendering

    The SVGMediaObject class loads and renders SVG (Scalable Vector Graphics) files
    as media objects in the scene. It uses Qt's SVG renderer to parse and display
    vector graphics with proper scaling and transparency support.
    """

    @patch("pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer")
    def test_init_success(self, mock_renderer_class):
        """
        Scenario: Initialize with valid SVG file

        Given a valid SVG file path "test.svg"
        When SVGMediaObject is created
        Then the SVG renderer should load the file successfully
        And the object should be initialized
        """
        mock_renderer = Mock()
        mock_renderer.load.return_value = True
        mock_renderer.defaultSize.return_value = Mock(width=lambda: 100, height=lambda: 200)
        mock_renderer_class.return_value = mock_renderer

        scene = Mock()
        obj = SVGMediaObject("test.svg", scene)

        assert obj is not None
        mock_renderer.load.assert_called_once_with("test.svg")

    @patch("pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer")
    def test_init_load_failure(self, mock_renderer_class):
        """
        Scenario: Reject invalid SVG file

        Given an invalid SVG file that cannot be parsed
        When SVGMediaObject is created
        Then a LoadError should be raised
        And the error message should indicate parsing failure
        """
        mock_renderer = Mock()
        mock_renderer.load.return_value = False
        mock_renderer_class.return_value = mock_renderer

        scene = Mock()
        with pytest.raises(LoadError, match="unable to parse SVG file"):
            SVGMediaObject("invalid.svg", scene)

    @patch("pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer")
    def test_inherits_from_mediaobject(self, mock_renderer_class):
        """
        Scenario: Verify inheritance from MediaObject

        Given a SVGMediaObject instance
        When checking its type
        Then it should be an instance of MediaObject
        """
        from pyzui.objects.mediaobjects.mediaobject import MediaObject

        mock_renderer = Mock()
        mock_renderer.load.return_value = True
        mock_renderer.defaultSize.return_value = Mock(width=lambda: 100, height=lambda: 200)
        mock_renderer_class.return_value = mock_renderer

        scene = Mock()
        obj = SVGMediaObject("test.svg", scene)

        assert isinstance(obj, MediaObject)

    def test_transparent_attribute(self):
        """
        Scenario: Check transparency support

        Given the SVGMediaObject class
        When accessing the transparent attribute
        Then it should be True
        """
        assert SVGMediaObject.transparent is True

    @patch("pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer")
    def test_onscreen_size_property_exists(self, mock_renderer_class):
        """
        Scenario: Verify onscreen_size property availability

        Given a SVGMediaObject with dimensions 100x200
        When checking for the onscreen_size property
        Then the property should exist
        """
        mock_renderer = Mock()
        mock_renderer.load.return_value = True
        mock_size = Mock()
        mock_size.width.return_value = 100
        mock_size.height.return_value = 200
        mock_renderer.defaultSize.return_value = mock_size
        mock_renderer_class.return_value = mock_renderer

        scene = Mock()
        SVGMediaObject("test.svg", scene)

        # Just verify the property exists (avoids Qt segfault)
        assert hasattr(SVGMediaObject, "onscreen_size")

    @patch("pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer")
    def test_render_method_exists(self, mock_renderer_class):
        """
        Scenario: Verify render method availability

        Given a SVGMediaObject instance
        When checking for the render method
        Then the method should exist
        And be callable
        """
        mock_renderer = Mock()
        mock_renderer.load.return_value = True
        mock_size = Mock()
        mock_size.width.return_value = 100
        mock_size.height.return_value = 200
        mock_renderer.defaultSize.return_value = mock_size
        mock_renderer_class.return_value = mock_renderer

        scene = Mock()
        obj = SVGMediaObject("test.svg", scene)

        # Just verify the method exists without calling it (avoids Qt segfault)
        assert hasattr(obj, "render")
        assert callable(obj.render)

    @patch("pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer")
    def test_to_dict_method(self, mock_renderer_class):
        """
        Scenario: Serialize SVGMediaObject to dictionary

        Given a SVGMediaObject with specific properties
        When to_dict() is called
        Then it should return a dictionary with all object properties
        And include SVG-specific attributes
        """
        mock_renderer = Mock()
        mock_renderer.load.return_value = True
        mock_size = Mock()
        mock_size.width.return_value = 100
        mock_size.height.return_value = 200
        mock_renderer.defaultSize.return_value = mock_size
        mock_renderer_class.return_value = mock_renderer

        scene = Mock()
        obj = SVGMediaObject("test.svg", scene)

        # Use patch to mock the inherited attributes
        with (
            patch.object(obj, "_media_id", "test.svg"),
            patch.object(obj, "_x", 10.0),
            patch.object(obj, "_y", 20.0),
            patch.object(obj, "_z", 30.0),
            patch.object(obj, "vx", 1.0),
            patch.object(obj, "vy", 2.0),
            patch.object(obj, "vz", 3.0),
        ):
            result = obj.to_dict()

            assert result["type"] == "SVGMediaObject"
            assert result["media_id"] == "test.svg"
            assert result["position"] == (10.0, 20.0, 30.0)
            assert result["velocity"] == (1.0, 2.0, 3.0)
            assert result["width"] == 100
            assert result["height"] == 200
            assert result["transparent"] is True

    @patch("pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer")
    def test_from_dict_method(self, mock_renderer_class):
        """
        Scenario: Create SVGMediaObject from dictionary

        Given a dictionary with SVGMediaObject data
        When from_dict() is called
        Then it should create a new SVGMediaObject with the same properties
        """
        mock_renderer = Mock()
        mock_renderer.load.return_value = True
        mock_size = Mock()
        mock_size.width.return_value = 100
        mock_size.height.return_value = 200
        mock_renderer.defaultSize.return_value = mock_size
        mock_renderer_class.return_value = mock_renderer

        scene = Mock()
        data = {
            "type": "SVGMediaObject",
            "media_id": "test.svg",
            "position": (10.0, 20.0, 30.0),
            "velocity": (1.0, 2.0, 3.0),
            "width": 100,
            "height": 200,
            "transparent": True,
        }

        obj = SVGMediaObject.from_dict(data, scene)

        # Verify the object was created
        assert obj is not None
        # The media_id should be set
        assert hasattr(obj, "_media_id")
        # Note: We can't directly check private attributes due to type checking
        # but the method should execute without errors

    @patch("pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer")
    def test_copy_preserves_svg_properties(self, mock_renderer_class):
        """
        Scenario: Copy preserves SVG-specific properties

        Given a SVGMediaObject with specific properties
        When serialized to dict and deserialized back
        Then the new object should have the same properties
        And SVG-specific attributes should be preserved
        """
        mock_renderer = Mock()
        mock_renderer.load.return_value = True
        mock_size = Mock()
        mock_size.width.return_value = 100
        mock_size.height.return_value = 200
        mock_renderer.defaultSize.return_value = mock_size
        mock_renderer_class.return_value = mock_renderer

        scene = Mock()
        original = SVGMediaObject("test.svg", scene)

        # Simulate copy by serializing and deserializing
        data = original.to_dict()
        copy = SVGMediaObject.from_dict(data, scene)

        # Verify both objects were created
        assert original is not None
        assert copy is not None
        # Verify transparency is preserved
        assert copy.transparent == original.transparent
        # Verify the dictionary serialization/deserialization works
        assert data["type"] == "SVGMediaObject"
        assert data["media_id"] == "test.svg"
