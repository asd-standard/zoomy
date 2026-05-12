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

from unittest.mock import Mock, PropertyMock, patch

from pyzui.objects.mediaobjects.mediaobject import MediaObject, RenderMode
from pyzui.objects.mediaobjects.stringmediaobject import StringMediaObject
from pyzui.objects.mediaobjects.svgmediaobject import SVGMediaObject
from pyzui.objects.mediaobjects.tiledmediaobject import TiledMediaObject


class TestSizeVisibility:
    """
    Feature: Size-based visibility checking

    Tests for the is_size_visible() method implementation across different
    media object types.
    """

    def test_mediaobject_base_implementation(self):
        """
        Scenario: Base MediaObject is_size_visible implementation

        Given a MediaObject
        When is_size_visible is called with different render modes
        Then it should return False for Invisible mode, True otherwise
        """
        scene = Mock()
        obj = MediaObject("test.jpg", scene)

        assert obj.is_size_visible(RenderMode.Invisible) is False
        assert obj.is_size_visible(RenderMode.Draft) is True
        assert obj.is_size_visible(RenderMode.HighQuality) is True

    def test_svgmediaobject_size_checks(self):
        """
        Scenario: SVGMediaObject size visibility with thresholds

        Given an SVGMediaObject with viewport 800x600
        When checking is_size_visible with different sizes
        Then it should respect thresholds: > viewport/55 and < viewport/0.5
        """
        scene = Mock()
        scene.viewport_size = (800, 600)
        scene.zoomlevel = 0

        with patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer') as mock_renderer_class:
            mock_renderer = Mock()
            mock_renderer.load.return_value = True
            mock_renderer.defaultSize.return_value = Mock(width=lambda: 100, height=lambda: 100)
            mock_renderer_class.return_value = mock_renderer

            svg_obj = SVGMediaObject('test.svg', scene)

            # Test with different onscreen sizes by mocking the property
            # Thresholds: min > min(viewport)/55 = 600/55 ≈ 10.9 -> int = 10
            #             max < max(viewport)/0.5 = 800/0.5 = 1600

            # Visible case: 50x50 (between thresholds)
            with patch.object(type(svg_obj), 'onscreen_size', PropertyMock(return_value=(50.0, 50.0))):
                assert svg_obj.is_size_visible(RenderMode.HighQuality) is True

            # Too small: 5x5 (< 10)
            with patch.object(type(svg_obj), 'onscreen_size', PropertyMock(return_value=(5.0, 5.0))):
                assert svg_obj.is_size_visible(RenderMode.HighQuality) is False

            # Too large: 2000x2000 (> 1600)
            with patch.object(type(svg_obj), 'onscreen_size', PropertyMock(return_value=(2000.0, 2000.0))):
                assert svg_obj.is_size_visible(RenderMode.HighQuality) is False

            # Edge case: exactly at threshold (10x10, should be invisible since 10 > 10 is False)
            with patch.object(type(svg_obj), 'onscreen_size', PropertyMock(return_value=(10.0, 10.0))):
                assert svg_obj.is_size_visible(RenderMode.HighQuality) is False

            # Test with Invisible mode (should always return False)
            with patch.object(type(svg_obj), 'onscreen_size', PropertyMock(return_value=(50.0, 50.0))):
                assert svg_obj.is_size_visible(RenderMode.Invisible) is False

    def test_stringmediaobject_size_checks(self):
        """
        Scenario: StringMediaObject size visibility with thresholds

        Given a StringMediaObject with viewport 800x600
        When checking is_size_visible with different sizes
        Then it should respect thresholds: > viewport/48 and < viewport/1
        """
        scene = Mock()
        scene.viewport_size = (800, 600)
        scene.zoomlevel = 0

        # Create StringMediaObject with valid color format
        string_obj = StringMediaObject('string:FF0000:Test', scene)

        # Test with different onscreen sizes
        # Thresholds: min > min(viewport)/48 = 600/48 ≈ 12.5 -> int = 12
        #             max < max(viewport)/1 = 800/1 = 800

        # Visible case: 50x50 (between thresholds)
        with patch.object(type(string_obj), 'onscreen_size', PropertyMock(return_value=(50.0, 50.0))):
            assert string_obj.is_size_visible(RenderMode.HighQuality) is True

        # Too small: 5x5 (< 12)
        with patch.object(type(string_obj), 'onscreen_size', PropertyMock(return_value=(5.0, 5.0))):
            assert string_obj.is_size_visible(RenderMode.HighQuality) is False

        # Too large: 900x900 (> 800)
        with patch.object(type(string_obj), 'onscreen_size', PropertyMock(return_value=(900.0, 900.0))):
            assert string_obj.is_size_visible(RenderMode.HighQuality) is False

        # Test with Invisible mode
        with patch.object(type(string_obj), 'onscreen_size', PropertyMock(return_value=(50.0, 50.0))):
            assert string_obj.is_size_visible(RenderMode.Invisible) is False

    def test_tiledmediaobject_size_checks(self):
        """
        Scenario: TiledMediaObject size visibility with 1-pixel threshold

        Given a TiledMediaObject
        When checking is_size_visible with different sizes
        Then it should return False if min dimension <= 1 pixel
        """
        scene = Mock()
        scene.viewport_size = (800, 600)
        scene.zoomlevel = 0

        # Mock tiled media object creation
        with patch('pyzui.objects.mediaobjects.tiledmediaobject.TileManager') as mock_tilemanager:
            mock_tilemanager.get_tile_robust.return_value = Mock(size=(256, 256))

            tiled_obj = TiledMediaObject('test.jpg', scene)

            # Setup basic attributes to avoid initialization errors
            tiled_obj._TiledMediaObject__tilesize = 256
            tiled_obj._TiledMediaObject__maxtilelevel = 0
            tiled_obj._TiledMediaObject__width = 1000
            tiled_obj._TiledMediaObject__height = 1000
            tiled_obj._TiledMediaObject__aspect_ratio = None

            # Visible case: 10x10 (> 1 pixel)
            with patch.object(type(tiled_obj), 'onscreen_size', PropertyMock(return_value=(10.0, 10.0))):
                assert tiled_obj.is_size_visible(RenderMode.HighQuality) is True

            # Too small: 1x1 (<= 1 pixel)
            with patch.object(type(tiled_obj), 'onscreen_size', PropertyMock(return_value=(1.0, 1.0))):
                assert tiled_obj.is_size_visible(RenderMode.HighQuality) is False

            # Too small: 0.5x10 (min = 0.5 <= 1)
            with patch.object(type(tiled_obj), 'onscreen_size', PropertyMock(return_value=(0.5, 10.0))):
                assert tiled_obj.is_size_visible(RenderMode.HighQuality) is False

            # Test with Invisible mode
            with patch.object(type(tiled_obj), 'onscreen_size', PropertyMock(return_value=(10.0, 10.0))):
                assert tiled_obj.is_size_visible(RenderMode.Invisible) is False

    def test_all_mediaobjects_have_method(self):
        """
        Scenario: Verify all media object types have is_size_visible method

        Given the media object classes
        When checking for is_size_visible method
        Then all should have the method
        """
        scene = Mock()

        # Test base class
        media_obj = MediaObject("test.jpg", scene)
        assert hasattr(media_obj, 'is_size_visible')
        assert callable(media_obj.is_size_visible)

        # Test SVGMediaObject
        with patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer') as mock_renderer_class:
            mock_renderer = Mock()
            mock_renderer.load.return_value = True
            mock_renderer.defaultSize.return_value = Mock(width=lambda: 100, height=lambda: 100)
            mock_renderer_class.return_value = mock_renderer

            svg_obj = SVGMediaObject('test.svg', scene)
            assert hasattr(svg_obj, 'is_size_visible')
            assert callable(svg_obj.is_size_visible)

        # Test StringMediaObject
        string_obj = StringMediaObject('string:FF0000:Test', scene)
        assert hasattr(string_obj, 'is_size_visible')
        assert callable(string_obj.is_size_visible)

        # Test TiledMediaObject
        with patch('pyzui.objects.mediaobjects.tiledmediaobject.TileManager') as mock_tilemanager:
            mock_tilemanager.get_tile_robust.return_value = Mock(size=(256, 256))

            tiled_obj = TiledMediaObject('test.jpg', scene)
            # Setup basic attributes
            tiled_obj._TiledMediaObject__tilesize = 256
            tiled_obj._TiledMediaObject__maxtilelevel = 0
            tiled_obj._TiledMediaObject__width = 1000
            tiled_obj._TiledMediaObject__height = 1000
            tiled_obj._TiledMediaObject__aspect_ratio = None

            assert hasattr(tiled_obj, 'is_size_visible')
            assert callable(tiled_obj.is_size_visible)
