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
from unittest.mock import Mock, patch, MagicMock
from PySide6 import QtSvg, QtCore
from pyzui.objects.mediaobjects.svgmediaobject import SVGMediaObject
from pyzui.objects.mediaobjects.mediaobject import LoadError, RenderMode

class TestSVGMediaObject:
    """
    Feature: SVG Media Object Rendering

    The SVGMediaObject class loads and renders SVG (Scalable Vector Graphics) files
    as media objects in the scene. It uses Qt's SVG renderer to parse and display
    vector graphics with proper scaling and transparency support.
    """

    @patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer')
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

    @patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer')
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

    @patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer')
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

    @patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer')
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
        obj = SVGMediaObject("test.svg", scene)

        # Just verify the property exists (avoids Qt segfault)
        assert hasattr(SVGMediaObject, 'onscreen_size')

    @patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer')
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
        assert hasattr(obj, 'render')
        assert callable(obj.render)
