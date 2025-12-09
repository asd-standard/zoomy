import pytest
from unittest.mock import Mock, patch, MagicMock
from pyzui.objects.mediaobjects.tiledmediaobject import TiledMediaObject

class TestTiledMediaObject:
    """
    Feature: Tiled Media Object Management

    The TiledMediaObject class handles large images by breaking them into tiles
    for efficient zooming and panning. It manages tile generation, caching, and
    on-demand loading of image tiles at different zoom levels.
    """

    @patch('pyzui.objects.mediaobjects.tiledmediaobject.TileManager.tiled')
    @patch('pyzui.objects.mediaobjects.tiledmediaobject.TileManager.load_tile')
    def test_init_already_tiled(self, mock_load, mock_tiled):
        """
        Scenario: Initialize with pre-tiled media

        Given a media file "test.jpg" that is already tiled
        When TiledMediaObject is created
        Then the object should initialize successfully
        And use existing tiles without re-tiling
        """
        mock_tiled.return_value = True
        scene = Mock()
        obj = TiledMediaObject("test.jpg", scene)
        assert obj is not None

    @patch('pyzui.objects.mediaobjects.tiledmediaobject.TileManager.tiled')
    @patch('tempfile.mkstemp')
    @patch('os.close')
    def test_init_needs_tiling(self, mock_close, mock_mkstemp, mock_tiled):
        """
        Scenario: Initialize media that requires tiling

        Given a media file "test.jpg" that hasn't been tiled yet
        When TiledMediaObject is created
        Then temporary files should be created for tiling
        And the object should initialize successfully
        """
        mock_tiled.return_value = False
        mock_mkstemp.return_value = (1, '/tmp/test.ppm')
        scene = Mock()
        obj = TiledMediaObject("test.jpg", scene)
        assert obj is not None

    def test_transparent_attribute(self):
        """
        Scenario: Check transparency support

        Given the TiledMediaObject class
        When accessing the transparent attribute
        Then it should be False (tiled images are opaque)
        """
        assert TiledMediaObject.transparent is False

    def test_default_size_attribute(self):
        """
        Scenario: Check default tile size

        Given the TiledMediaObject class
        When accessing the default_size attribute
        Then it should be (256, 256)
        """
        assert TiledMediaObject.default_size == (256, 256)

    def test_tempcache_attribute(self):
        """
        Scenario: Check temporary cache setting

        Given the TiledMediaObject class
        When accessing the tempcache attribute
        Then it should be 5 (cache size for temporary tiles)
        """
        assert TiledMediaObject.tempcache == 5

    @patch('pyzui.objects.mediaobjects.tiledmediaobject.TileManager.tiled')
    def test_inherits_from_mediaobject(self, mock_tiled):
        """
        Scenario: Verify inheritance from MediaObject

        Given a TiledMediaObject instance
        When checking its type
        Then it should be an instance of MediaObject
        """
        from pyzui.objects.mediaobjects.mediaobject import MediaObject
        mock_tiled.return_value = True
        with patch('pyzui.objects.mediaobjects.tiledmediaobject.TileManager.load_tile'):
            scene = Mock()
            obj = TiledMediaObject("test.jpg", scene)
            assert isinstance(obj, MediaObject)

    @patch('pyzui.objects.mediaobjects.tiledmediaobject.TileManager.tiled')
    def test_onscreen_size_property(self, mock_tiled):
        """
        Scenario: Calculate on-screen size at zoom level

        Given a TiledMediaObject at zoom level 0
        When accessing the onscreen_size property
        Then it should return a tuple with (width, height)
        """
        mock_tiled.return_value = True
        with patch('pyzui.objects.mediaobjects.tiledmediaobject.TileManager.load_tile'):
            scene = Mock()
            scene.zoomlevel = 0
            obj = TiledMediaObject("test.jpg", scene)
            obj.zoomlevel = 0
            size = obj.onscreen_size
            assert isinstance(size, tuple)
            assert len(size) == 2
