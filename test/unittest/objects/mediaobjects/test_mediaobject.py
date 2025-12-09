import pytest
from unittest.mock import Mock, MagicMock, patch
from pyzui.objects.mediaobjects.mediaobject import MediaObject, LoadError, RenderMode

class TestMediaObject:
    """
    Feature: MediaObject Base Class

    The MediaObject class provides the base functionality for all media objects in the ZUI,
    including coordinate transformation, movement, zooming, visibility calculations, and
    rendering infrastructure.
    """

    def test_load_error_exception(self):
        """
        Scenario: Verify LoadError exception type

        Given the MediaObject module
        When checking for the LoadError exception
        Then it should exist and be a subclass of Exception
        """
        assert issubclass(LoadError, Exception)

    def test_render_mode_constants(self):
        """
        Scenario: Verify RenderMode constants exist

        Given the MediaObject module
        When checking for RenderMode attributes
        Then Invisible, Draft, and HighQuality constants should exist
        """
        assert hasattr(RenderMode, 'Invisible')
        assert hasattr(RenderMode, 'Draft')
        assert hasattr(RenderMode, 'HighQuality')

    def test_render_mode_values(self):
        """
        Scenario: Verify RenderMode constant values

        Given the RenderMode constants
        When checking their values
        Then Invisible should be 0, Draft should be 1, and HighQuality should be 2
        """
        assert RenderMode.Invisible == 0
        assert RenderMode.Draft == 1
        assert RenderMode.HighQuality == 2

    def test_init_stores_media_id_and_scene(self):
        """
        Scenario: Initialize MediaObject with media_id and scene

        Given a media_id and a mock scene
        When a MediaObject is created
        Then the media_id and scene should be stored
        """
        scene = Mock()
        media_id = "test_media.jpg"
        obj = MediaObject(media_id, scene)

        assert obj._media_id == media_id
        assert obj._scene == scene

    def test_move_updates_position(self):
        """
        Scenario: Move media object by screen distance

        Given a MediaObject at position (100, 200) in scene coordinates
        When move is called with dx=50, dy=30
        Then the position should be updated based on scene zoomlevel
        """
        scene = Mock()
        scene.zoomlevel = 0  # No scene zoom
        obj = MediaObject("test.jpg", scene)
        obj._x = 100.0
        obj._y = 200.0

        obj.move(50, 30)

        # At zoomlevel 0: dx * 2^0 = 50, dy * 2^0 = 30
        assert obj._x == 150.0
        assert obj._y == 230.0

    def test_move_accounts_for_scene_zoomlevel(self):
        """
        Scenario: Move object with scene zoom applied

        Given a MediaObject with scene zoomlevel = 1
        When move is called with dx=100, dy=50
        Then the position should account for scene zoom
        """
        scene = Mock()
        scene.zoomlevel = 1  # Scene zoomed in 2x
        obj = MediaObject("test.jpg", scene)
        obj._x = 0.0
        obj._y = 0.0

        obj.move(100, 50)

        # At zoomlevel 1: dx * 2^-1 = 50, dy * 2^-1 = 25
        assert obj._x == 50.0
        assert obj._y == 25.0

    def test_zoom_increases_zoom_level(self):
        """
        Scenario: Zoom in on media object

        Given a MediaObject at zoom level 0
        When zoom is called with amount=1.0
        Then the zoom level should increase by 1.0
        """
        scene = Mock()
        scene.zoomlevel = 0
        obj = MediaObject("test.jpg", scene)
        obj._z = 0.0
        obj._x = 100.0
        obj._y = 100.0
        obj._centre = (50.0, 50.0)

        obj.zoom(1.0)

        assert obj._z == 1.0

    def test_zoom_adjusts_position_to_keep_center_fixed(self):
        """
        Scenario: Zoom maintains center position on screen

        Given a MediaObject with a specific center point
        When zoom is applied
        Then the position should adjust so center stays fixed
        """
        scene = Mock()
        scene.zoomlevel = 0
        obj = MediaObject("test.jpg", scene)
        obj._z = 0.0
        obj._x = 0.0
        obj._y = 0.0
        obj._centre = (100.0, 100.0)

        # Store initial center scene coordinates
        initial_c_sx = obj._x + obj._centre[0] * (2 ** obj._z)
        initial_c_sy = obj._y + obj._centre[1] * (2 ** obj._z)

        obj.zoom(1.0)

        # After zoom, center scene coordinates should be preserved
        final_c_sx = obj._x + obj._centre[0] * (2 ** obj._z)
        final_c_sy = obj._y + obj._centre[1] * (2 ** obj._z)

        assert abs(final_c_sx - initial_c_sx) < 0.01
        assert abs(final_c_sy - initial_c_sy) < 0.01

    def test_hides_returns_false_for_transparent_object(self):
        """
        Scenario: Transparent object cannot hide others

        Given a transparent MediaObject
        When checking if it hides another object
        Then it should return False
        """
        scene = Mock()
        scene.viewport_size = (1920, 1080)

        obj1 = MediaObject("transparent.png", scene)
        obj1.transparent = True

        # Mock topleft and bottomright properties
        with patch.object(type(obj1), 'topleft', new_callable=lambda: property(lambda self: (100, 100))):
            with patch.object(type(obj1), 'bottomright', new_callable=lambda: property(lambda self: (500, 500))):
                obj2 = MediaObject("other.jpg", scene)
                with patch.object(type(obj2), 'topleft', new_callable=lambda: property(lambda self: (200, 200))):
                    with patch.object(type(obj2), 'bottomright', new_callable=lambda: property(lambda self: (400, 400))):
                        assert obj1.hides(obj2) is False

    def test_hides_returns_true_when_completely_covering(self):
        """
        Scenario: Opaque object completely hides another

        Given two MediaObjects where one completely covers the other
        When checking if the larger hides the smaller
        Then it should return True
        """
        scene = Mock()
        scene.viewport_size = (1920, 1080)

        obj1 = MediaObject("large.jpg", scene)
        obj1.transparent = False

        obj2 = MediaObject("small.jpg", scene)

        # Mock the properties for both objects
        with patch.object(type(obj1), 'topleft', new_callable=lambda: property(lambda self: (100, 100))):
            with patch.object(type(obj1), 'bottomright', new_callable=lambda: property(lambda self: (500, 500))):
                with patch.object(type(obj2), 'topleft', new_callable=lambda: property(lambda self: (200, 200))):
                    with patch.object(type(obj2), 'bottomright', new_callable=lambda: property(lambda self: (400, 400))):
                        assert obj1.hides(obj2) is True

    def test_hides_method_exists(self):
        """
        Scenario: Verify hides method exists

        Given a MediaObject instance
        When checking for the hides method
        Then it should exist and be callable
        """
        scene = Mock()
        obj = MediaObject("test.jpg", scene)
        assert hasattr(obj, 'hides')
        assert callable(obj.hides)

    def test_hides_clamps_to_viewport(self):
        """
        Scenario: Visibility calculation respects viewport bounds

        Given two MediaObjects with positions outside viewport
        When checking visibility with viewport clamping
        Then coordinates should be clamped to viewport bounds
        """
        scene = Mock()
        scene.viewport_size = (1000, 800)

        obj1 = MediaObject("large.jpg", scene)
        obj1.transparent = False

        obj2 = MediaObject("small.jpg", scene)

        # Mock positions outside viewport
        with patch.object(type(obj1), 'topleft', new_callable=lambda: property(lambda self: (-100, -100))):
            with patch.object(type(obj1), 'bottomright', new_callable=lambda: property(lambda self: (1200, 1000))):
                with patch.object(type(obj2), 'topleft', new_callable=lambda: property(lambda self: (200, 200))):
                    with patch.object(type(obj2), 'bottomright', new_callable=lambda: property(lambda self: (400, 400))):
                        # Should clamp and still detect hiding
                        assert obj1.hides(obj2) is True
