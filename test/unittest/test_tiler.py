import pytest
from unittest.mock import Mock, patch
from threading import Thread
from pyzui.tiler import Tiler

class TestTiler:
    """Test suite for the Tiler class."""

    def test_init_with_all_params(self):
        """Test Tiler initialization with all parameters."""
        tiler = Tiler("input.jpg", media_id="test_id", filext="png", tilesize=512)
        assert tiler._infile == "input.jpg"
        assert tiler.error is None

    def test_init_default_media_id(self):
        """Test Tiler uses infile as media_id if not provided."""
        tiler = Tiler("input.jpg")
        assert tiler._Tiler__media_id == "input.jpg"

    def test_init_custom_media_id(self):
        """Test Tiler uses custom media_id."""
        tiler = Tiler("input.jpg", media_id="custom_id")
        assert tiler._Tiler__media_id == "custom_id"

    def test_inherits_from_thread(self):
        """Test that Tiler inherits from Thread."""
        tiler = Tiler("input.jpg")
        assert isinstance(tiler, Thread)

    def test_progress_property_initial(self):
        """Test progress property initial value."""
        tiler = Tiler("input.jpg")
        assert tiler.progress == 0.0

    def test_progress_property(self):
        """Test progress property."""
        tiler = Tiler("input.jpg")
        tiler._Tiler__progress = 0.5
        assert tiler.progress == 0.5

    def test_error_attribute_default(self):
        """Test error attribute is None by default."""
        tiler = Tiler("input.jpg")
        assert tiler.error is None

    def test_str_representation(self):
        """Test string representation."""
        tiler = Tiler("input.jpg")
        assert str(tiler) == "Tiler(input.jpg)"

    def test_repr_representation(self):
        """Test repr representation."""
        tiler = Tiler("input.jpg")
        assert repr(tiler) == "Tiler('input.jpg')"

    def test_scanline_abstract_method(self):
        """Test _scanline is abstract and returns None."""
        tiler = Tiler("input.jpg")
        result = tiler._scanline()
        assert result is None

    def test_init_default_filext(self):
        """Test default filext is jpg."""
        tiler = Tiler("input.jpg")
        assert tiler._Tiler__filext == 'jpg'

    def test_init_default_tilesize(self):
        """Test default tilesize is 256."""
        tiler = Tiler("input.jpg")
        assert tiler._Tiler__tilesize == 256

    def test_init_custom_tilesize(self):
        """Test custom tilesize."""
        tiler = Tiler("input.jpg", tilesize=512)
        assert tiler._Tiler__tilesize == 512

    def test_init_custom_filext(self):
        """Test custom filext."""
        tiler = Tiler("input.jpg", filext="png")
        assert tiler._Tiler__filext == 'png'
