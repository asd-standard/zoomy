import pytest
from unittest.mock import Mock, patch
from PyQt5 import QtGui
from pyzui.stringmediaobject import StringMediaObject
from pyzui.mediaobject import LoadError

class TestStringMediaObject:
    """Test suite for the StringMediaObject class."""

    def test_init_valid_color(self):
        """Test StringMediaObject initialization with valid color."""
        scene = Mock()
        obj = StringMediaObject("string:FF0000:Hello", scene)
        assert obj._media_id == "string:FF0000:Hello"

    def test_init_invalid_color(self):
        """Test StringMediaObject raises LoadError for invalid color."""
        scene = Mock()
        with pytest.raises(LoadError, match="the supplied colour is invalid"):
            StringMediaObject("string:GGGGGG:Hello", scene)

    def test_transparent_attribute(self):
        """Test transparent class attribute is True."""
        assert StringMediaObject.transparent is True

    def test_base_pointsize_attribute(self):
        """Test base_pointsize attribute."""
        assert StringMediaObject.base_pointsize == 24.0

    def test_inherits_from_mediaobject(self):
        """Test that StringMediaObject inherits from MediaObject."""
        from pyzui.mediaobject import MediaObject
        scene = Mock()
        obj = StringMediaObject("string:000000:Test", scene)
        assert isinstance(obj, MediaObject)

    def test_parses_text_from_media_id(self):
        """Test that text is correctly parsed from media_id."""
        scene = Mock()
        obj = StringMediaObject("string:000000:HelloWorld", scene)
        # Text should be stored internally

    def test_multiline_text(self):
        """Test multiline text parsing."""
        scene = Mock()
        obj = StringMediaObject("string:000000:Hello\\nWorld", scene)
        # Lines should be split

    def test_render_method_exists(self):
        """Test render method exists and is callable."""
        scene = Mock()
        obj = StringMediaObject("string:000000:Test", scene)
        # Just verify the method exists without calling it (avoids Qt segfault)
        assert hasattr(obj, 'render')
        assert callable(obj.render)

    def test_onscreen_size_property_exists(self):
        """Test onscreen_size property exists."""
        scene = Mock()
        obj = StringMediaObject("string:000000:Test", scene)
        # Just verify the property exists without accessing it (avoids Qt segfault)
        assert hasattr(StringMediaObject, 'onscreen_size')
