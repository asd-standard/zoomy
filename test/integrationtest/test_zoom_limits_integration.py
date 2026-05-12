## PyZUI - Python Zooming User Interface
## Copyright (C) 2009 David Roberts <d@vidr.cc>
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

"""
Feature: Zoom Limits Integration

Integration tests for zoom limits functionality to prevent crashes
when inserting StringMediaObject at extreme zoom levels.
"""

import pytest
from PySide6 import QtWidgets

from pyzui.objects.mediaobjects.stringmediaobject import StringMediaObject
from pyzui.objects.objectsutils import ZoomManager
from pyzui.objects.physicalobject import PhysicalObject
from pyzui.objects.scene import scene as Scene


class TestZoomLimitsIntegration:
    """
    Feature: Zoom Limits Integration with Scene and MediaObjects

    Tests that zoom limits prevent crashes when working with StringMediaObjects
    at extreme zoom levels.
    """

    @pytest.fixture(scope="class")
    def qapp(self):
        """Create QApplication instance for tests."""
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication([])
        yield app
        app.quit()

    def setup_method(self):
        """Setup ZoomManager for each test."""
        config = {'min_zoomlevel': -20.0, 'max_zoomlevel': 20.0, 'clamp_enabled': True}
        self.zoom_manager = ZoomManager(config)
        PhysicalObject.set_zoom_manager(self.zoom_manager)

    def teardown_method(self):
        """Clean up after each test."""
        PhysicalObject.set_zoom_manager(None)

    def test_stringmediaobject_insertion_at_extreme_zoom(self):
        """
        Scenario: Insert StringMediaObject while zoomed out beyond limits

        Given a Scene with zoomlevel set to -30 (beyond default limit of -20)
        When a StringMediaObject is created
        Then it should not crash and zoomlevel should be clamped to -20
        """
        # Create scene
        scene = Scene.new()

        # Set zoomlevel beyond limit (should be clamped to -20)
        scene.zoomlevel = -30.0
        assert scene.zoomlevel == -20.0, f"Zoomlevel should be clamped to -20, got {scene.zoomlevel}"

        # Create StringMediaObject (this would crash without limits)
        # StringMediaObject requires color code in format "string:rrggbb:text"
        # Just creating it should not crash
        string_obj = StringMediaObject("string:ff0000:Test text", scene)

        # Verify object was created successfully
        assert string_obj._get_text() == "Test text"
        # StringMediaObject starts with zoomlevel 0.0 (default), doesn't inherit scene zoomlevel
        assert string_obj.zoomlevel == 0.0

    def test_stringmediaobject_insertion_at_very_negative_zoom(self):
        """
        Scenario: Insert StringMediaObject at very negative zoom level

        Given a Scene with zoomlevel set to -50
        When a StringMediaObject is inserted
        Then it should not crash and zoomlevel should be clamped
        """
        scene = Scene.new()

        # Test with extremely negative zoom
        scene.zoomlevel = -50.0
        assert scene.zoomlevel == -20.0, f"Zoomlevel should be clamped to -20, got {scene.zoomlevel}"

        # Add multiple string objects
        objects = []
        for i in range(3):
            string_obj = StringMediaObject(f"string:{i:06x}:Text {i}", scene)
            scene.add(string_obj)
            objects.append(string_obj)

        # Clean up
        for obj in objects:
            scene.remove(obj)

    def test_zoom_operation_with_limits(self):
        """
        Scenario: Zoom operations respect limits

        Given a Scene at zoomlevel 0
        When zoom() is called with large negative amount
        Then zoomlevel should be clamped to minimum
        """
        scene = Scene.new()

        # Try to zoom way out
        scene.zoom(-50.0)  # Should clamp to -20
        assert scene.zoomlevel == -20.0, f"Zoom should clamp to -20, got {scene.zoomlevel}"

        # Try to zoom way in
        scene.zoom(50.0)  # Should clamp to 20
        assert scene.zoomlevel == 20.0, f"Zoom should clamp to 20, got {scene.zoomlevel}"

        # Normal zoom within limits
        scene.zoomlevel = 0.0
        scene.zoom(5.0)
        assert scene.zoomlevel == 5.0, f"Zoom within limits should work, got {scene.zoomlevel}"

    def test_mediaobject_zoom_with_limits(self):
        """
        Scenario: MediaObject zoom operations respect limits

        Given a MediaObject in a Scene
        When zoom() is called with extreme amounts
        Then zoomlevel should be clamped
        """
        scene = Scene.new()
        string_obj = StringMediaObject("string:00ff00:Test", scene)
        scene.add(string_obj)

        # Set initial zoom
        string_obj.zoomlevel = 0.0

        # Try to zoom beyond limits
        string_obj.zoom(-30.0)  # Should clamp
        assert string_obj.zoomlevel == -20.0, f"MediaObject zoom should clamp to -20, got {string_obj.zoomlevel}"

        string_obj.zoom(50.0)  # Should clamp
        assert string_obj.zoomlevel == 20.0, f"MediaObject zoom should clamp to 20, got {string_obj.zoomlevel}"

        # Clean up
        scene.remove(string_obj)

    def test_zoommanager_config_update(self):
        """
        Scenario: Update ZoomManager configuration at runtime

        Given a ZoomManager with default limits
        When configuration is updated with new limits
        Then zoom operations should use new limits
        """
        # Create ZoomManager with default limits
        config = {'min_zoomlevel': -20.0, 'max_zoomlevel': 20.0}
        zoom_manager = ZoomManager(config)
        PhysicalObject.set_zoom_manager(zoom_manager)

        # Create scene and test with default limits
        scene = Scene.new()
        scene.zoomlevel = -30.0
        assert scene.zoomlevel == -20.0

        # Update limits
        new_config = {'min_zoomlevel': -10.0, 'max_zoomlevel': 15.0}
        zoom_manager.update_config(new_config)

        # Test with new limits
        scene.zoomlevel = -30.0
        assert scene.zoomlevel == -10.0, f"Should clamp to new min -10, got {scene.zoomlevel}"

        scene.zoomlevel = 30.0
        assert scene.zoomlevel == 15.0, f"Should clamp to new max 15, got {scene.zoomlevel}"

    def test_fit_operation_with_limits(self, qapp):
        """
        Scenario: MediaObject.fit() respects zoom limits

        Given a MediaObject
        When fit() is called with scale that would exceed limits
        Then zoomlevel should be clamped
        """
        scene = Scene.new()
        string_obj = StringMediaObject("string:0000ff:Test fit", scene)
        scene.add(string_obj)

        # Try to fit with extreme scale (would cause math.log(very_small) without limits)
        # This tests that fit() doesn't crash when scale calculations produce extreme values
        bbox = (0.0, 0.0, 100.0, 100.0)

        # This should not crash even if internal calculations would produce
        # zoomlevel beyond limits
        string_obj.fit(bbox)

        # Zoomlevel should be within limits
        assert -20.0 <= string_obj.zoomlevel <= 20.0, \
            f"fit() should keep zoomlevel within limits, got {string_obj.zoomlevel}"

        # Clean up
        scene.remove(string_obj)

    def test_config_auto_swap_min_max(self):
        """
        Scenario: Configuration with min > max is auto-swapped

        Given configuration with min_zoomlevel > max_zoomlevel
        When ZoomManager is created
        Then min and max should be automatically swapped
        """
        config = {'min_zoomlevel': 10.0, 'max_zoomlevel': -10.0}
        zoom_manager = ZoomManager(config)

        assert zoom_manager.min_zoomlevel == -10.0
        assert zoom_manager.max_zoomlevel == 10.0

        # Test that clamping works with swapped limits
        PhysicalObject.set_zoom_manager(zoom_manager)
        scene = Scene.new()

        scene.zoomlevel = -20.0
        assert scene.zoomlevel == -10.0, f"Should clamp to swapped min -10, got {scene.zoomlevel}"

        scene.zoomlevel = 20.0
        assert scene.zoomlevel == 10.0, f"Should clamp to swapped max 10, got {scene.zoomlevel}"
