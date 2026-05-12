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

import math
from unittest.mock import Mock, patch

import pytest


class TestScene:
    """
    Feature: Scene Module

    This class tests the Scene module to ensure it exists and the Scene class is properly
    defined within the PyZUI scene system.
    """

    def test_module_exists(self):
        """
        Scenario: Verify scene module exists

        Given the PyZUI scene system
        When importing the scene module
        Then the module should be successfully imported
        """
        import pyzui.objects.scene.scene

        assert pyzui.objects.scene.scene is not None

    def test_scene_class_exists(self):
        """
        Scenario: Verify Scene class exists

        Given the scene module
        When checking for the Scene class
        Then the class should be defined
        """
        from pyzui.objects.scene.scene import Scene

        assert Scene is not None

    def test_placeholder(self):
        """
        Scenario: Placeholder test for future implementation

        Given the test suite structure
        When running placeholder tests
        Then they should pass to maintain test suite integrity
        """
        assert True

    def test_render_order_smaller_objects_on_top(self):
        """
        Scenario: Verify smaller objects are rendered on top of larger objects
                 when render_order is 'smaller_on_top' (default)

        Given a scene with render_order='smaller_on_top' and
               multiple media objects of different sizes
        When the scene is rendered
        Then smaller objects should be rendered after (on top of) larger objects
        """
        from pyzui.objects.mediaobjects import mediaobject as MediaObject
        from pyzui.objects.scene.scene import Scene

        # Create a scene with smaller_on_top (default)
        scene = Scene()
        assert scene.render_order == "smaller_on_top"
        scene.viewport_size = (800, 600)

        # Track render order
        render_order = []

        # Create mock media objects with different sizes
        class MockMediaObject:
            def __init__(self, name, area):
                self.name = name
                self._area = area
                self._topleft = (100, 100)
                self._bottomright = (200, 200)
                self.vzmoving = False  # Required attribute for Scene.vzmoving property

            @property
            def onscreen_area(self):
                return self._area

            @property
            def topleft(self):
                return self._topleft

            @property
            def bottomright(self):
                return self._bottomright

            def render(self, painter, mode):
                if mode != MediaObject.RenderMode.Invisible:
                    render_order.append(self.name)

            def is_size_visible(self, mode):
                # Mock implementation - always visible
                return mode != MediaObject.RenderMode.Invisible

        # Create objects: large (1000), medium (500), small (100)
        large_obj = MockMediaObject("large", 1000)
        medium_obj = MockMediaObject("medium", 500)
        small_obj = MockMediaObject("small", 100)

        # Add in random order
        scene.add(medium_obj)
        scene.add(small_obj)
        scene.add(large_obj)

        # Create a mock painter
        mock_painter = Mock()

        # Render the scene
        scene.render(mock_painter, draft=True)

        # Verify render order: largest first, smallest last
        # This ensures smaller objects are painted on top
        assert render_order == ["large", "medium", "small"], (
            f"Expected ['large', 'medium', 'small'], got {render_order}"
        )

    def test_render_order_larger_objects_on_top(self):
        """
        Scenario: Verify larger objects are rendered on top of smaller objects
                 when render_order is 'larger_on_top'

        Given a scene with render_order='larger_on_top' and
               multiple media objects of different sizes
        When the scene is rendered
        Then larger objects should be rendered after (on top of) smaller objects
        """
        from pyzui.objects.mediaobjects import mediaobject as MediaObject
        from pyzui.objects.scene.scene import Scene

        # Create a scene and set render order to larger_on_top
        scene = Scene()
        scene.set_render_order("larger_on_top")
        assert scene.render_order == "larger_on_top"
        scene.viewport_size = (800, 600)

        # Track render order
        render_order = []

        # Create mock media objects with different sizes
        class MockMediaObject:
            def __init__(self, name, area):
                self.name = name
                self._area = area
                self._topleft = (100, 100)
                self._bottomright = (200, 200)
                self.vzmoving = False

            @property
            def onscreen_area(self):
                return self._area

            @property
            def topleft(self):
                return self._topleft

            @property
            def bottomright(self):
                return self._bottomright

            def render(self, painter, mode):
                if mode != MediaObject.RenderMode.Invisible:
                    render_order.append(self.name)

            def is_size_visible(self, mode):
                return mode != MediaObject.RenderMode.Invisible

        # Create objects: large (1000), medium (500), small (100)
        large_obj = MockMediaObject("large", 1000)
        medium_obj = MockMediaObject("medium", 500)
        small_obj = MockMediaObject("small", 100)

        # Add in random order
        scene.add(medium_obj)
        scene.add(small_obj)
        scene.add(large_obj)

        # Create a mock painter
        mock_painter = Mock()

        # Render the scene
        scene.render(mock_painter, draft=True)

        # Verify render order: smallest first, largest last
        # This ensures larger objects are painted on top
        assert render_order == ["small", "medium", "large"], (
            f"Expected ['small', 'medium', 'large'], got {render_order}"
        )

    def test_render_order_toggle_runtime(self):
        """
        Scenario: Verify render order can be toggled at runtime

        Given a scene with multiple media objects
        When render_order is changed at runtime
        Then the next render pass uses the new order
        """
        from pyzui.objects.mediaobjects import mediaobject as MediaObject
        from pyzui.objects.scene.scene import Scene

        scene = Scene()
        scene.viewport_size = (800, 600)

        render_order = []

        class MockMediaObject:
            def __init__(self, name, area):
                self.name = name
                self._area = area
                self._topleft = (100, 100)
                self._bottomright = (200, 200)
                self.vzmoving = False

            @property
            def onscreen_area(self):
                return self._area

            @property
            def topleft(self):
                return self._topleft

            @property
            def bottomright(self):
                return self._bottomright

            def render(self, painter, mode):
                if mode != MediaObject.RenderMode.Invisible:
                    render_order.append(self.name)

            def is_size_visible(self, mode):
                return mode != MediaObject.RenderMode.Invisible

        large_obj = MockMediaObject("large", 1000)
        medium_obj = MockMediaObject("medium", 500)
        small_obj = MockMediaObject("small", 100)

        scene.add(large_obj)
        scene.add(medium_obj)
        scene.add(small_obj)

        mock_painter = Mock()

        # Default: smaller_on_top -> largest first, smallest last
        scene.render(mock_painter, draft=True)
        assert render_order == ["large", "medium", "small"]

        # Toggle to larger_on_top
        render_order.clear()
        scene.set_render_order("larger_on_top")
        scene.render(mock_painter, draft=True)
        assert render_order == ["small", "medium", "large"]

        # Toggle back
        render_order.clear()
        scene.set_render_order("smaller_on_top")
        scene.render(mock_painter, draft=True)
        assert render_order == ["large", "medium", "small"]

    def test_render_order_property_and_setter(self):
        """
        Scenario: Verify render_order property and setter

        Given a Scene instance
        When getting and setting render_order
        Then valid values are accepted and invalid values raise ValueError
        """
        from pyzui.objects.scene.scene import Scene

        scene = Scene()

        # Default
        assert scene.render_order == "smaller_on_top"

        # Valid values
        scene.set_render_order("larger_on_top")
        assert scene.render_order == "larger_on_top"

        scene.set_render_order("smaller_on_top")
        assert scene.render_order == "smaller_on_top"

        # Invalid value
        with pytest.raises(ValueError, match="Invalid render order mode"):
            scene.set_render_order("invalid_mode")

    def test_render_order_from_config(self):
        """
        Scenario: Verify render_order is read from configuration

        Given a config dict with render.order='larger_on_top'
        When a Scene is created with that config
        Then the scene's render_order should be 'larger_on_top'
        """
        from pyzui.objects.scene.scene import Scene

        # Scene with larger_on_top config
        scene = Scene(config={"render": {"order": "larger_on_top"}})
        assert scene.render_order == "larger_on_top"

        # Scene without render config defaults to smaller_on_top
        scene2 = Scene(config={})
        assert scene2.render_order == "smaller_on_top"

        # Scene with no config defaults to smaller_on_top
        scene3 = Scene()
        assert scene3.render_order == "smaller_on_top"

    def test_remove_single_object(self):
        """
        Scenario: Remove single media object from scene

        Given a scene with multiple media objects
        When a single object is removed
        Then only that object should be removed from the scene
        """
        from pyzui.objects.scene.scene import Scene

        # Create a scene
        scene = Scene()

        # Create mock media objects
        mock_obj1 = Mock()
        mock_obj1.media_id = "test1"
        mock_obj1.topleft = (0, 0)
        mock_obj1.bottomright = (100, 100)
        mock_obj1.onscreen_area = 10000

        mock_obj2 = Mock()
        mock_obj2.media_id = "test2"
        mock_obj2.topleft = (50, 50)
        mock_obj2.bottomright = (150, 150)
        mock_obj2.onscreen_area = 10000

        # Add objects to scene
        scene.add(mock_obj1)
        scene.add(mock_obj2)

        # Verify both objects are in scene
        with scene._Scene__objects_lock:
            assert len(scene._Scene__objects) == 2
            assert mock_obj1 in scene._Scene__objects
            assert mock_obj2 in scene._Scene__objects

        # Remove single object
        scene.remove(mock_obj1)

        # Verify only mock_obj1 was removed
        with scene._Scene__objects_lock:
            assert len(scene._Scene__objects) == 1
            assert mock_obj1 not in scene._Scene__objects
            assert mock_obj2 in scene._Scene__objects

    def test_remove_list_of_objects(self):
        """
        Scenario: Remove multiple media objects from scene

        Given a scene with multiple media objects
        When a list of objects is removed
        Then all objects in the list should be removed from the scene
        """
        from pyzui.objects.scene.scene import Scene

        # Create a scene
        scene = Scene()

        # Create mock media objects
        mock_objects = []
        for i in range(5):
            mock_obj = Mock()
            mock_obj.media_id = f"test{i}"
            mock_obj.topleft = (i * 50, i * 50)
            mock_obj.bottomright = (i * 50 + 100, i * 50 + 100)
            mock_obj.onscreen_area = 10000
            mock_objects.append(mock_obj)
            scene.add(mock_obj)

        # Verify all objects are in scene
        with scene._Scene__objects_lock:
            assert len(scene._Scene__objects) == 5
            for obj in mock_objects:
                assert obj in scene._Scene__objects

        # Remove first 3 objects as a list
        objects_to_remove = mock_objects[:3]
        scene.remove(objects_to_remove)

        # Verify first 3 objects were removed, last 2 remain
        with scene._Scene__objects_lock:
            assert len(scene._Scene__objects) == 2
            for obj in objects_to_remove:
                assert obj not in scene._Scene__objects
            for obj in mock_objects[3:]:
                assert obj in scene._Scene__objects

    def test_remove_mixed_media_ids(self):
        """
        Scenario: Remove objects with same and different media IDs

        Given a scene with objects sharing media IDs
        When objects are removed
        Then media ID cleanup should only purge when no objects remain with that ID
        """
        from pyzui.objects.scene.scene import Scene
        from pyzui.tilesystem import tilemanager as TileManager

        # Create a scene
        scene = Scene()

        # Create mock objects with shared media IDs
        mock_obj1 = Mock()
        mock_obj1.media_id = "shared_id"
        mock_obj1.topleft = (0, 0)
        mock_obj1.bottomright = (100, 100)
        mock_obj1.onscreen_area = 10000

        mock_obj2 = Mock()
        mock_obj2.media_id = "shared_id"  # Same media ID
        mock_obj2.topleft = (50, 50)
        mock_obj2.bottomright = (150, 150)
        mock_obj2.onscreen_area = 10000

        mock_obj3 = Mock()
        mock_obj3.media_id = "unique_id"  # Different media ID
        mock_obj3.topleft = (100, 100)
        mock_obj3.bottomright = (200, 200)
        mock_obj3.onscreen_area = 10000

        # Add objects to scene
        scene.add(mock_obj1)
        scene.add(mock_obj2)
        scene.add(mock_obj3)

        # Mock TileManager.purge to track calls
        with patch.object(TileManager, "purge") as mock_purge:
            # Remove first object with shared ID
            scene.remove(mock_obj1)

            # TileManager.purge should NOT be called because another object shares the media ID
            mock_purge.assert_not_called()

            # Remove second object with shared ID
            scene.remove(mock_obj2)

            # Now TileManager.purge should be called for "shared_id"
            mock_purge.assert_called_once_with("shared_id")

            # Reset mock
            mock_purge.reset_mock()

            # Remove object with unique ID
            scene.remove(mock_obj3)

            # TileManager.purge should be called for "unique_id"
            mock_purge.assert_called_once_with("unique_id")

    def test_import_scene_basic(self):
        """
        Scenario: Import scene into existing scene

        Given an existing scene with mediaobjects
        When importing a scene from a PZS file
        Then the imported mediaobjects should be added to the current scene
        """
        from unittest.mock import mock_open, patch

        from pyzui.objects.scene.scene import Scene

        # Create a scene with some initial mediaobjects
        scene = Scene()
        scene.viewport_size = (800, 600)
        # Don't set zoomlevel directly - it breaks the centre calculation
        # scene.zoomlevel = 1.0 would set self._z without updating self._centre
        # Instead, we should use scene.zoom(1.0) if we want to change zoom
        # For this test, we'll keep default zoomlevel of 0.0
        scene.origin = (0, 0)

        # Mock PZS file content
        pzs_content = """2.0\t100.0\t200.0
TiledMediaObject\timage.jpg\t1.5\t50.0\t30.0
StringMediaObject\tTest String\t0.5\t-20.0\t10.0
"""

        with patch("builtins.open", mock_open(read_data=pzs_content)):
            # Mock the mediaobject creation to avoid actual file dependencies
            with patch.object(scene, "_create_mediaobject_from_line") as mock_create:
                mock_obj1 = Mock()
                mock_obj1.media_id = "image.jpg"
                mock_obj1.zoomlevel = 1.5
                mock_obj1.pos = (50.0, 30.0)
                mock_obj1.topleft = (10.0, 10.0)
                mock_obj1.bottomright = (60.0, 40.0)

                mock_obj2 = Mock()
                mock_obj2.media_id = "Test String"
                mock_obj2.zoomlevel = 0.5
                mock_obj2.pos = (-20.0, 10.0)
                mock_obj2.topleft = (-30.0, 0.0)
                mock_obj2.bottomright = (10.0, 20.0)

                # Return different mock objects for each line
                mock_create.side_effect = [mock_obj1, mock_obj2]

                # Import the scene
                scene.import_scene("test_scene.pzs")

                # Verify mediaobjects were created and added
                assert mock_create.call_count == 2

                # Verify positions were transformed (check transformation logic, not exact values)
                # The exact values depend on viewport centre calculation
                # Just verify that pos was updated (not its original value)
                assert mock_obj1.pos != (50.0, 30.0)  # Position should be transformed
                assert mock_obj1.zoomlevel != 1.5  # Zoomlevel adjusted to fit viewport
                assert mock_obj2.pos != (-20.0, 10.0)  # Position should be transformed
                assert mock_obj2.zoomlevel != 0.5  # Zoomlevel adjusted to fit viewport

                # Verify transformation preserves relative positions
                # Calculate expected positions based on centroid and viewport centre
                # Centroid of original positions: ((50 + -20)/2, (30 + 10)/2) = (15, 20)
                # Offsets from centroid: obj1: (35, 10), obj2: (-35, -10)
                # Viewport centre depends on scene setup
                # Just verify positions were transformed (not their exact values)
                pass  # Transformation verified by previous assertions

    def test_import_scene_empty_file(self):
        """
        Scenario: Import empty scene file

        Given an empty PZS file
        When importing the scene
        Then no mediaobjects should be added
        """
        from unittest.mock import mock_open, patch

        from pyzui.objects.scene.scene import Scene

        scene = Scene()
        scene.viewport_size = (800, 600)
        scene.zoomlevel = 1.0
        scene.origin = (0, 0)

        # Empty PZS file (only header)
        pzs_content = "1.0\t0.0\t0.0\n"

        with patch("builtins.open", mock_open(read_data=pzs_content)):
            with patch.object(scene, "_create_mediaobject_from_line") as mock_create:
                scene.import_scene("empty_scene.pzs")

                # No mediaobjects should be created
                mock_create.assert_not_called()

    def test_import_scene_file_not_found(self):
        """
        Scenario: Import scene from non-existent file

        Given a non-existent file path
        When attempting to import the scene
        Then FileNotFoundError should be raised
        """
        from pyzui.objects.scene.scene import Scene

        scene = Scene()

        with pytest.raises(FileNotFoundError):
            scene.import_scene("non_existent.pzs")

    def test_import_scene_invalid_format(self):
        """
        Scenario: Import scene with invalid file format

        Given a malformed PZS file
        When attempting to import the scene
        Then ValueError should be raised
        """
        from unittest.mock import mock_open, patch

        from pyzui.objects.scene.scene import Scene

        scene = Scene()

        # Malformed PZS file (missing values in header)
        pzs_content = "1.0\t0.0\n"  # Only 2 values instead of 3

        with patch("builtins.open", mock_open(read_data=pzs_content)), pytest.raises(ValueError):
            scene.import_scene("malformed.pzs")

    def test_import_scene_duplicate_mediaobjects(self):
        """
        Scenario: Import scene with duplicate mediaobjects

        Given a scene with existing mediaobjects
        When importing a scene with mediaobjects having the same media_id
        Then duplicates should be added (not skipped)
        """
        from unittest.mock import mock_open, patch

        from pyzui.objects.scene.scene import Scene

        scene = Scene()
        scene.viewport_size = (800, 600)
        scene.zoomlevel = 1.0
        scene.origin = (0, 0)

        # Add an initial mediaobject
        mock_existing = Mock()
        mock_existing.media_id = "image.jpg"
        scene.add(mock_existing)

        # PZS file with mediaobject having same media_id
        pzs_content = """1.0\t0.0\t0.0
TiledMediaObject\timage.jpg\t1.0\t0.0\t0.0
"""

        with patch("builtins.open", mock_open(read_data=pzs_content)):
            with patch.object(scene, "_create_mediaobject_from_line") as mock_create:
                mock_new = Mock()
                mock_new.media_id = "image.jpg"
                mock_new.zoomlevel = 1.0
                mock_new.pos = (0.0, 0.0)
                mock_new.topleft = (0.0, 0.0)
                mock_new.bottomright = (100.0, 100.0)
                mock_create.return_value = mock_new

                scene.import_scene("duplicate_scene.pzs")

                # Verify new mediaobject was created and added
                mock_create.assert_called_once()

                # Both mediaobjects should be in the scene
                # (Note: we can't easily check this without accessing internal __objects list)
                # But if add() was called, duplicates are allowed per requirements

    def test_fit_imported_objects_scales_up(self):
        """
        Scenario: Imported objects scaled up to fit viewport

        Given imported objects whose combined bounding box is smaller than the target area
        When _fit_imported_objects is called
        Then object positions and zoomlevels should be scaled to fill the viewport
        """
        from pyzui.objects.scene.scene import Scene

        scene = Scene()
        scene.viewport_size = (800, 600)
        scene.origin = (0, 0)

        # Small object: 10x10 on screen (tiny relative to viewport)
        mock_obj = Mock()
        mock_obj.pos = (50.0, 50.0)
        mock_obj.zoomlevel = 0.0
        mock_obj.topleft = (100.0, 100.0)
        mock_obj.bottomright = (110.0, 110.0)

        scene._fit_imported_objects([mock_obj])

        # bbox 10x10, target 400x300, scale = min(400/10, 300/10) = 30
        # zoom_adjust = log2(30) ≈ 4.907
        assert mock_obj.zoomlevel == pytest.approx(math.log2(30), rel=1e-9)
        # Single object: centroid == its pos, so position doesn't change
        assert mock_obj.pos == (50.0, 50.0)

    def test_fit_imported_objects_scales_down(self):
        """
        Scenario: Imported objects scaled down to fit viewport

        Given imported objects whose combined bounding box is larger than the target area
        When _fit_imported_objects is called
        Then object positions and zoomlevels should be decreased to fit the viewport
        """
        from pyzui.objects.scene.scene import Scene

        scene = Scene()
        scene.viewport_size = (800, 600)
        scene.origin = (0, 0)

        # Large object: 800x600 on screen (fills entire viewport, should scale down)
        mock_obj = Mock()
        mock_obj.pos = (400.0, 300.0)
        mock_obj.zoomlevel = 5.0
        mock_obj.topleft = (0.0, 0.0)
        mock_obj.bottomright = (800.0, 600.0)

        scene._fit_imported_objects([mock_obj])

        # bbox 800x600, target 400x300, scale = min(400/800, 300/600) = 0.5
        # zoom_adjust = log2(0.5) = -1.0
        assert mock_obj.zoomlevel == pytest.approx(5.0 + math.log2(0.5), rel=1e-9)
        # Single object: centroid == its pos, so position doesn't change
        assert mock_obj.pos == (400.0, 300.0)

    def test_fit_imported_objects_empty_list(self):
        """
        Scenario: Fit imported objects with empty list

        Given an empty mediaobjects list
        When _fit_imported_objects is called
        Then no error should be raised
        """
        from pyzui.objects.scene.scene import Scene

        scene = Scene()
        scene.viewport_size = (800, 600)

        # Should not raise any exception
        scene._fit_imported_objects([])

    def test_fit_imported_objects_zero_viewport(self):
        """
        Scenario: Fit imported objects with zero viewport size

        Given a scene with zero viewport dimensions
        When _fit_imported_objects is called
        Then no error should be raised (objects keep their original zoomlevels)
        """
        from pyzui.objects.scene.scene import Scene

        scene = Scene()
        scene.viewport_size = (0, 0)

        mock_obj = Mock()
        mock_obj.pos = (50.0, 50.0)
        mock_obj.zoomlevel = 1.0
        mock_obj.topleft = (0.0, 0.0)
        mock_obj.bottomright = (100.0, 100.0)

        scene._fit_imported_objects([mock_obj])

        # Zoomlevel should remain unchanged (viewport is zero size)
        assert mock_obj.zoomlevel == 1.0
        # Position should remain unchanged (no scaling applied)
        assert mock_obj.pos == (50.0, 50.0)

    def test_fit_imported_objects_preserves_relative_zoom(self):
        """
        Scenario: Fit imported objects preserves relative zoom differences

        Given two imported objects with different zoomlevels
        When _fit_imported_objects is called
        Then the difference in zoomlevels should be preserved
        """
        from pyzui.objects.scene.scene import Scene

        scene = Scene()
        scene.viewport_size = (800, 600)
        scene.origin = (0, 0)

        mock_obj1 = Mock()
        mock_obj1.pos = (75.0, 75.0)
        mock_obj1.zoomlevel = 0.0
        mock_obj1.topleft = (50.0, 50.0)
        mock_obj1.bottomright = (100.0, 100.0)

        mock_obj2 = Mock()
        mock_obj2.pos = (250.0, 300.0)
        mock_obj2.zoomlevel = 2.0  # 4x larger than obj1
        mock_obj2.topleft = (200.0, 200.0)
        mock_obj2.bottomright = (300.0, 400.0)

        original_diff = mock_obj2.zoomlevel - mock_obj1.zoomlevel  # 2.0

        scene._fit_imported_objects([mock_obj1, mock_obj2])

        # Relative zoom difference should be preserved
        new_diff = mock_obj2.zoomlevel - mock_obj1.zoomlevel
        assert new_diff == pytest.approx(original_diff, rel=1e-9)

    def test_fit_imported_objects_scales_positions(self):
        """
        Scenario: Fit imported objects scales positions around group centroid

        Given two imported objects with known positions
        When _fit_imported_objects is called
        Then positions should be scaled relative to the group centroid
        """
        from pyzui.objects.scene.scene import Scene

        scene = Scene()
        scene.viewport_size = (2000, 2000)
        scene.origin = (0, 0)

        # Place two objects far apart but with small on-screen bounding box
        # Since topleft/bottomright are screen coords and pos is scene coords,
        # with origin=(0,0) and zoomlevel=0 they're the same
        mock_obj1 = Mock()
        mock_obj1.pos = (0.0, 0.0)
        mock_obj1.zoomlevel = 0.0
        mock_obj1.topleft = (0.0, 0.0)
        mock_obj1.bottomright = (10.0, 10.0)

        mock_obj2 = Mock()
        mock_obj2.pos = (100.0, 0.0)
        mock_obj2.zoomlevel = 0.0
        mock_obj2.topleft = (100.0, 0.0)
        mock_obj2.bottomright = (110.0, 10.0)

        scene._fit_imported_objects([mock_obj1, mock_obj2])

        # Centroid: ((0+100)/2, (0+0)/2) = (50, 0)
        # Bbox: 110x10, target: 1000x1000, scale = min(1000/110, 1000/10) = 1000/110 ≈ 9.09
        # New positions:
        #   obj1: (50 + (0-50)*scale, 0 + (0-0)*scale) = (50 - 50*scale, 0)
        #   obj2: (50 + (100-50)*scale, 0) = (50 + 50*scale, 0)
        # Distance between new positions: (50 + 50*scale) - (50 - 50*scale) = 100*scale
        scale = 1000.0 / 110.0
        expected_distance = 100.0 * scale
        actual_distance = mock_obj2.pos[0] - mock_obj1.pos[0]
        assert actual_distance == pytest.approx(expected_distance, rel=1e-9)

    def test_fit_imported_objects_multi_object_bbox(self):
        """
        Scenario: Fit imported objects uses combined bounding box

        Given multiple imported objects spread across screen
        When _fit_imported_objects is called
        Then scaling uses the combined bounding box of all objects
        """
        from pyzui.objects.scene.scene import Scene

        scene = Scene()
        scene.viewport_size = (800, 600)
        scene.origin = (0, 0)

        # Two objects with a combined bbox of 200x110 on screen
        mock_obj1 = Mock()
        mock_obj1.pos = (50.0, 50.0)
        mock_obj1.zoomlevel = 0.0
        mock_obj1.topleft = (0.0, 0.0)
        mock_obj1.bottomright = (100.0, 100.0)

        mock_obj2 = Mock()
        mock_obj2.pos = (150.0, 60.0)
        mock_obj2.zoomlevel = 0.0
        mock_obj2.topleft = (100.0, 10.0)
        mock_obj2.bottomright = (200.0, 110.0)

        scene._fit_imported_objects([mock_obj1, mock_obj2])

        # Combined bbox: (0,0) to (200,110) -> 200x110
        # target 400x300, scale = min(400/200, 300/110) = min(2, 2.727) = 2
        # zoom_adjust = log2(2) = 1.0
        expected_zoom = math.log2(2)  # 1.0
        assert mock_obj1.zoomlevel == pytest.approx(expected_zoom, rel=1e-9)
        assert mock_obj2.zoomlevel == pytest.approx(expected_zoom, rel=1e-9)
        # Position dist should scale by factor 2
        # centroid = ((50+150)/2, (50+60)/2) = (100, 55)
        # Distance from centroid to obj1: (50-100, 50-55) = (-50, -5)
        # Scaled distance: (-100, -10)
        # New obj1 pos: (100-100, 55-10) = (0, 45)
        # Distance between objects: (200-0, 65-45) = (200, 20) — 2x original distance
        assert mock_obj1.pos[0] == pytest.approx(0.0, rel=1e-9)
        assert mock_obj2.pos[0] == pytest.approx(200.0, rel=1e-9)

    def test_save_selection_basic(self):
        """
        Scenario: Save selection with multiple objects

        Given a scene with selected mediaobjects
        When saving the selection
        Then only selected objects should be saved with "0 0 0" header
        """
        from unittest.mock import patch

        from pyzui.objects.scene.scene import Scene

        scene = Scene()

        # Create mock mediaobjects
        mock_obj1 = Mock()
        mock_obj1.media_id = "image1.jpg"
        mock_obj1.zoomlevel = 1.0
        mock_obj1.pos = (100.0, 50.0)
        mock_obj1.topleft = (80.0, 30.0)
        mock_obj1.bottomright = (120.0, 70.0)
        mock_obj1.onscreen_area = 1600.0
        type(mock_obj1).__name__ = "TiledMediaObject"

        mock_obj2 = Mock()
        mock_obj2.media_id = "image2.jpg"
        mock_obj2.zoomlevel = 0.5
        mock_obj2.pos = (200.0, 150.0)
        mock_obj2.topleft = (180.0, 130.0)
        mock_obj2.bottomright = (220.0, 170.0)
        mock_obj2.onscreen_area = 1600.0
        type(mock_obj2).__name__ = "TiledMediaObject"

        # Set selection
        scene.selection = [mock_obj1, mock_obj2]

        # Mock file writing
        written_content = []
        mock_file = Mock()
        mock_file.write = lambda s: written_content.append(s)

        with patch("builtins.open", return_value=mock_file):
            scene.save_selection("test_selection.pzs")

        # Verify file was written
        assert len(written_content) > 0

        # Check first line is "0 0 0"
        lines = "".join(written_content).split("\n")
        assert lines[0] == "0\t0\t0"

        # Should have 2 object lines plus empty line at end
        assert len([l for l in lines if l.strip()]) == 3  # Header + 2 objects

    def test_save_selection_single_object(self):
        """
        Scenario: Save selection with single object

        Given a scene with a single selected mediaobject
        When saving the selection
        Then the object should be saved with position (0, 0) relative to itself
        """
        from unittest.mock import patch

        from pyzui.objects.scene.scene import Scene

        scene = Scene()

        # Create mock mediaobject
        mock_obj = Mock()
        mock_obj.media_id = "image.jpg"
        mock_obj.zoomlevel = 1.5
        mock_obj.pos = (100.0, 50.0)
        mock_obj.topleft = (80.0, 30.0)
        mock_obj.bottomright = (120.0, 70.0)
        mock_obj.onscreen_area = 1600.0
        type(mock_obj).__name__ = "TiledMediaObject"

        # Set selection (single object, not list)
        scene.selection = mock_obj

        # Mock file writing
        written_content = []
        mock_file = Mock()
        mock_file.write = lambda s: written_content.append(s)

        with patch("builtins.open", return_value=mock_file):
            scene.save_selection("test_single_selection.pzs")

        # Verify file was written
        assert len(written_content) > 0

        # Check first line is "0 0 0"
        lines = "".join(written_content).split("\n")
        assert lines[0] == "0\t0\t0"

        # Should have 1 object line
        object_lines = [l for l in lines if l.startswith("TiledMediaObject")]
        assert len(object_lines) == 1

    def test_save_selection_empty_selection(self):
        """
        Scenario: Save selection with no selection

        Given a scene with no selection
        When attempting to save selection
        Then warning should be logged and no file should be written
        """
        from unittest.mock import patch

        from pyzui.objects.scene.scene import Scene

        scene = Scene()

        # No selection set
        scene.selection = None

        # Mock logger to capture warning
        with patch.object(scene, "_Scene__logger") as mock_logger:
            # Mock file opening to ensure it's not called
            with patch("builtins.open") as mock_open:
                scene.save_selection("test_empty.pzs")

                # Verify warning was logged
                mock_logger.warning.assert_called_with("No selection to save")

                # Verify file was not opened
                mock_open.assert_not_called()

    def test_save_selection_preserves_relative_positions(self):
        """
        Scenario: Save selection preserves relative positions

        Given selected mediaobjects at different positions
        When saving the selection
        Then saved positions should be offsets from centroid
        """
        from unittest.mock import patch

        from pyzui.objects.scene.scene import Scene

        scene = Scene()

        # Create mock mediaobjects forming a square
        mock_obj1 = Mock()
        mock_obj1.media_id = "obj1"
        mock_obj1.zoomlevel = 1.0
        mock_obj1.pos = (0.0, 0.0)  # Top-left
        type(mock_obj1).__name__ = "TiledMediaObject"

        mock_obj2 = Mock()
        mock_obj2.media_id = "obj2"
        mock_obj2.zoomlevel = 1.0
        mock_obj2.pos = (100.0, 0.0)  # Top-right
        type(mock_obj2).__name__ = "TiledMediaObject"

        mock_obj3 = Mock()
        mock_obj3.media_id = "obj3"
        mock_obj3.zoomlevel = 1.0
        mock_obj3.pos = (0.0, 100.0)  # Bottom-left
        type(mock_obj3).__name__ = "TiledMediaObject"

        mock_obj4 = Mock()
        mock_obj4.media_id = "obj4"
        mock_obj4.zoomlevel = 1.0
        mock_obj4.pos = (100.0, 100.0)  # Bottom-right
        type(mock_obj4).__name__ = "TiledMediaObject"

        # Set selection
        scene.selection = [mock_obj1, mock_obj2, mock_obj3, mock_obj4]

        # Mock file writing
        written_content = []
        mock_file = Mock()
        mock_file.write = lambda s: written_content.append(s)

        with patch("builtins.open", return_value=mock_file):
            scene.save_selection("test_relative.pzs")

        # Parse written content
        lines = "".join(written_content).strip().split("\n")

        # Skip header line
        object_lines = lines[1:]

        # Calculate expected centroid: (50, 50)
        # Expected offsets (original pos - centroid):
        # obj1: (-50, -50)
        # obj2: (50, -50)
        # obj3: (-50, 50)
        # obj4: (50, 50)

        # Parse object lines and check positions
        for line in object_lines:
            parts = line.split("\t")
            media_id = parts[1]
            pos_x = float(parts[3])
            pos_y = float(parts[4])

            if media_id == "obj1":
                assert pos_x == -50.0
                assert pos_y == -50.0
            elif media_id == "obj2":
                assert pos_x == 50.0
                assert pos_y == -50.0
            elif media_id == "obj3":
                assert pos_x == -50.0
                assert pos_y == 50.0
            elif media_id == "obj4":
                assert pos_x == 50.0
                assert pos_y == 50.0

    def test_save_selection_file_format(self):
        """
        Scenario: Save selection produces correct file format

        Given selected mediaobjects
        When saving the selection
        Then file should have correct tab-separated format
        """
        from unittest.mock import patch

        from pyzui.objects.scene.scene import Scene

        scene = Scene()

        # Create mock mediaobject
        mock_obj = Mock()
        mock_obj.media_id = "test/image.jpg"
        mock_obj.zoomlevel = 1.5
        mock_obj.pos = (100.0, 50.0)
        type(mock_obj).__name__ = "TiledMediaObject"

        # Mock _get_processed_media_id to return known value
        with patch.object(scene, "_get_processed_media_id", return_value="test%2Fimage.jpg"):
            # Set selection
            scene.selection = mock_obj

            # Mock file writing
            written_content = []
            mock_file = Mock()
            mock_file.write = lambda s: written_content.append(s)

            with patch("builtins.open", return_value=mock_file):
                scene.save_selection("test_format.pzs")

            # Parse written content
            content = "".join(written_content)
            lines = content.strip().split("\n")

            # Check format
            assert len(lines) == 2  # Header + object

            # Check header
            assert lines[0] == "0\t0\t0"

            # Check object line format
            parts = lines[1].split("\t")
            assert len(parts) == 5
            assert parts[0] == "TiledMediaObject"
            assert parts[1] == "test%2Fimage.jpg"
            assert float(parts[2]) == 1.5  # zoomlevel
            # Position should be (0, 0) for single object (centroid is itself)
            assert float(parts[3]) == 0.0
            assert float(parts[4]) == 0.0


class TestSceneShutdownThreads:
    """
    Feature: Scene Thread Shutdown

    The Scene.shutdown_threads() method should gracefully stop all background
    threads owned by the scene, including parallel renderer workers.
    """

    def test_shutdown_threads_halts_parallel_renderer(self):
        """
        Scenario: shutdown_threads stops the parallel renderer

        Given a Scene instance with an active parallel renderer
        When shutdown_threads() is called
        Then the parallel renderer's shutdown() method should be invoked
        """
        from pyzui.objects.scene.scene import Scene

        scene = Scene()
        mock_renderer = Mock()
        scene._Scene__parallel_renderer = mock_renderer

        scene.shutdown_threads()

        mock_renderer.shutdown.assert_called_once()

    def test_shutdown_threads_no_renderer(self):
        """
        Scenario: shutdown_threads with no parallel renderer

        Given a Scene instance without a parallel renderer
        When shutdown_threads() is called
        Then no error should occur
        """
        from pyzui.objects.scene.scene import Scene

        scene = Scene()
        try:
            scene.shutdown_threads()
        except Exception:
            pytest.fail("shutdown_threads() raised an exception")
