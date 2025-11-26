import pytest
from unittest.mock import Mock, patch, MagicMock
from PyQt5 import QtSvg, QtCore
from pyzui.svgmediaobject import SVGMediaObject
from pyzui.mediaobject import LoadError, RenderMode

class TestSVGMediaObject:
    """Test suite for the SVGMediaObject class."""

    @patch('pyzui.svgmediaobject.QtSvg.QSvgRenderer')
    def test_init_success(self, mock_renderer_class):
        """Test SVGMediaObject initialization with valid SVG."""
        mock_renderer = Mock()
        mock_renderer.load.return_value = True
        mock_renderer.defaultSize.return_value = Mock(width=lambda: 100, height=lambda: 200)
        mock_renderer_class.return_value = mock_renderer

        scene = Mock()
        obj = SVGMediaObject("test.svg", scene)

        assert obj is not None
        mock_renderer.load.assert_called_once_with("test.svg")

    @patch('pyzui.svgmediaobject.QtSvg.QSvgRenderer')
    def test_init_load_failure(self, mock_renderer_class):
        """Test SVGMediaObject raises LoadError on invalid SVG."""
        mock_renderer = Mock()
        mock_renderer.load.return_value = False
        mock_renderer_class.return_value = mock_renderer

        scene = Mock()
        with pytest.raises(LoadError, match="unable to parse SVG file"):
            SVGMediaObject("invalid.svg", scene)

    @patch('pyzui.svgmediaobject.QtSvg.QSvgRenderer')
    def test_inherits_from_mediaobject(self, mock_renderer_class):
        """Test that SVGMediaObject inherits from MediaObject."""
        from pyzui.mediaobject import MediaObject
        mock_renderer = Mock()
        mock_renderer.load.return_value = True
        mock_renderer.defaultSize.return_value = Mock(width=lambda: 100, height=lambda: 200)
        mock_renderer_class.return_value = mock_renderer

        scene = Mock()
        obj = SVGMediaObject("test.svg", scene)

        assert isinstance(obj, MediaObject)

    def test_transparent_attribute(self):
        """Test transparent class attribute is True."""
        assert SVGMediaObject.transparent is True

    @patch('pyzui.svgmediaobject.QtSvg.QSvgRenderer')
    def test_onscreen_size_property_exists(self, mock_renderer_class):
        """Test onscreen_size property exists."""
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

    @patch('pyzui.svgmediaobject.QtSvg.QSvgRenderer')
    def test_render_method_exists(self, mock_renderer_class):
        """Test render method exists."""
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
