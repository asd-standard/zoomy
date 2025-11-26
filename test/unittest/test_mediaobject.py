import pytest
from unittest.mock import Mock
from pyzui.mediaobject import MediaObject, LoadError, RenderMode

class TestMediaObject:
    """Test suite for the MediaObject base class."""

    def test_load_error_exception(self):
        """Test LoadError exception exists."""
        assert issubclass(LoadError, Exception)

    def test_render_mode_constants(self):
        """Test RenderMode constants exist."""
        assert hasattr(RenderMode, 'Invisible')
        assert hasattr(RenderMode, 'Draft')
        assert hasattr(RenderMode, 'HighQuality')

    def test_render_mode_values(self):
        """Test RenderMode constant values."""
        assert RenderMode.Invisible == 0
        assert RenderMode.Draft == 1
        assert RenderMode.HighQuality == 2
