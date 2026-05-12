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

"""
Integration test for group deletion functionality.

Tests the complete workflow:
1. Ctrl+rectangle selection of multiple media objects
2. Pressing Delete key to delete all selected objects
"""

from unittest.mock import Mock, patch

from pyzui.objects.mediaobjects.tiledmediaobject import TiledMediaObject
from pyzui.objects.scene.scene import Scene
from pyzui.tilesystem import tilemanager as TileManager


class TestGroupDeletion:
    """
    Feature: Group Deletion of Media Objects

    Tests the ability to select multiple media objects using Ctrl+rectangle
    selection and delete them all by pressing the Delete key.
    """

    def test_group_deletion_workflow(self):
        """
        Scenario: Delete multiple objects selected via rectangle selection

        Given a scene with multiple media objects
        When user selects multiple objects using Ctrl+rectangle selection
        And presses the Delete key
        Then all selected objects should be removed from the scene
        """
        # Create a scene with multiple objects
        scene = Scene()

        # Create mock objects
        mock_objects = []
        for i in range(4):
            mock_obj = Mock(spec=TiledMediaObject)
            mock_obj.media_id = f"test_image_{i}.jpg"
            mock_obj.topleft = (i * 100, i * 100)
            mock_obj.bottomright = (i * 100 + 80, i * 100 + 80)
            mock_obj.onscreen_area = 6400
            mock_obj.pos = (i * 100, i * 100)
            mock_obj.zoomlevel = 0.0
            mock_obj._x = i * 100
            mock_obj._y = i * 100
            mock_obj._z = 0.0
            mock_obj.vx = 0.0
            mock_obj.vy = 0.0
            mock_obj.vz = 0.0

            # Mock the render method
            mock_obj.render = Mock()

            mock_objects.append(mock_obj)
            scene.add(mock_obj)

        # Mock TileManager.purge
        with patch.object(TileManager, 'purge') as mock_purge:
            # Simulate rectangle selection covering first 3 objects
            # Objects at positions: (0,0), (100,100), (200,200), (300,300)
            # Rectangle covers (0,0) to (250,250) - should select first 3 objects

            # Use Scene.get() to simulate rectangle selection
            topleft = (0, 0)
            bottomright = (250, 250)
            selected_objects = scene.get(topleft, bottomright)

            # Set selection to the list of objects
            scene.selection = selected_objects

            # Verify selection is a list of 3 objects (first 3)
            assert isinstance(scene.selection, list)
            assert len(scene.selection) == 3

            # Verify the correct objects are selected
            selected_ids = {obj.media_id for obj in scene.selection}
            expected_ids = {"test_image_0.jpg", "test_image_1.jpg", "test_image_2.jpg"}
            assert selected_ids == expected_ids

            # Now remove the selected objects (simulating Delete key press)
            scene.remove(scene.selection)

            # Verify selection is cleared (QZUI would do this after remove)
            scene.selection = None

            # Verify objects were removed from scene
            with scene._Scene__objects_lock:
                assert len(scene._Scene__objects) == 1  # Only 4th object should remain
                remaining_ids = {obj.media_id for obj in scene._Scene__objects}
                assert remaining_ids == {"test_image_3.jpg"}

            # Verify TileManager.purge was called for each removed media_id
            # (assuming no other objects share these media_ids)
            assert mock_purge.call_count == 3
            called_ids = {call[0][0] for call in mock_purge.call_args_list}
            assert called_ids == {"test_image_0.jpg", "test_image_1.jpg", "test_image_2.jpg"}

    def test_single_object_deletion_still_works(self):
        """
        Scenario: Single object deletion still works (regression test)

        Given a scene with a single selected object
        When user presses the Delete key
        Then the single object should be removed
        """
        scene = Scene()

        # Create a single mock object
        mock_obj = Mock(spec=TiledMediaObject)
        mock_obj.media_id = "test_single.jpg"
        mock_obj.topleft = (100, 100)
        mock_obj.bottomright = (180, 180)
        mock_obj.onscreen_area = 6400
        mock_obj.pos = (100, 100)
        mock_obj.zoomlevel = 0.0
        mock_obj._x = 100
        mock_obj._y = 100
        mock_obj._z = 0.0
        mock_obj.vx = 0.0
        mock_obj.vy = 0.0
        mock_obj.vz = 0.0
        mock_obj.render = Mock()

        scene.add(mock_obj)

        # Select the single object
        scene.selection = mock_obj

        # Mock TileManager.purge
        with patch.object(TileManager, 'purge') as mock_purge:
            # Remove the object
            scene.remove(mock_obj)

            # Verify object was removed
            with scene._Scene__objects_lock:
                assert len(scene._Scene__objects) == 0

            # Verify TileManager.purge was called
            mock_purge.assert_called_once_with("test_single.jpg")

    def test_empty_selection_does_nothing(self):
        """
        Scenario: Delete key with no selection does nothing

        Given a scene with no selection
        When user presses the Delete key
        Then nothing should happen (no errors)
        """
        scene = Scene()

        # Create a mock object but don't select it
        mock_obj = Mock(spec=TiledMediaObject)
        mock_obj.media_id = "test.jpg"
        mock_obj.topleft = (100, 100)
        mock_obj.bottomright = (180, 180)
        mock_obj.onscreen_area = 6400
        scene.add(mock_obj)

        # Mock TileManager.purge
        with patch.object(TileManager, 'purge') as mock_purge:
            # Try to remove None (simulating Delete with no selection)
            # This should do nothing without errors
            scene.remove(None)

            # Verify nothing was purged
            mock_purge.assert_not_called()

            # Verify object is still in scene
            with scene._Scene__objects_lock:
                assert len(scene._Scene__objects) == 1
                assert scene._Scene__objects[0] == mock_obj
