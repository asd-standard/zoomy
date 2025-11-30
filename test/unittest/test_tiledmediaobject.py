import pytest
from unittest.mock import Mock, patch, MagicMock
from pyzui.objects.mediaobjects.tiledmediaobject import TiledMediaObject

class TestTiledMediaObject:
    """Test suite for the TiledMediaObject class."""

    @patch('pyzui.objects.mediaobjects.tiledmediaobject.TileManager.tiled')
    @patch('pyzui.objects.mediaobjects.tiledmediaobject.TileManager.load_tile')
    def test_init_already_tiled(self, mock_load, mock_tiled):
        """Test initialization with already tiled media."""
        mock_tiled.return_value = True
        scene = Mock()
        obj = TiledMediaObject("test.jpg", scene)
        assert obj is not None

    @patch('pyzui.objects.mediaobjects.tiledmediaobject.TileManager.tiled')
    @patch('tempfile.mkstemp')
    @patch('os.close')
    def test_init_needs_tiling(self, mock_close, mock_mkstemp, mock_tiled):
        """Test initialization with media that needs tiling."""
        mock_tiled.return_value = False
        mock_mkstemp.return_value = (1, '/tmp/test.ppm')
        scene = Mock()
        obj = TiledMediaObject("test.jpg", scene)
        assert obj is not None

    def test_transparent_attribute(self):
        """Test transparent class attribute is False."""
        assert TiledMediaObject.transparent is False

    def test_default_size_attribute(self):
        """Test default_size attribute."""
        assert TiledMediaObject.default_size == (256, 256)

    def test_tempcache_attribute(self):
        """Test tempcache attribute."""
        assert TiledMediaObject.tempcache == 5

    @patch('pyzui.objects.mediaobjects.tiledmediaobject.TileManager.tiled')
    def test_inherits_from_mediaobject(self, mock_tiled):
        """Test that TiledMediaObject inherits from MediaObject."""
        from pyzui.objects.mediaobjects.mediaobject import MediaObject
        mock_tiled.return_value = True
        with patch('pyzui.objects.mediaobjects.tiledmediaobject.TileManager.load_tile'):
            scene = Mock()
            obj = TiledMediaObject("test.jpg", scene)
            assert isinstance(obj, MediaObject)

    @patch('pyzui.objects.mediaobjects.tiledmediaobject.TileManager.tiled')
    def test_onscreen_size_property(self, mock_tiled):
        """Test onscreen_size property."""
        mock_tiled.return_value = True
        with patch('pyzui.objects.mediaobjects.tiledmediaobject.TileManager.load_tile'):
            scene = Mock()
            scene.zoomlevel = 0
            obj = TiledMediaObject("test.jpg", scene)
            obj.zoomlevel = 0
            size = obj.onscreen_size
            assert isinstance(size, tuple)
            assert len(size) == 2
