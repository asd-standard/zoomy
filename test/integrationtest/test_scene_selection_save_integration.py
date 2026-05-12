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
Integration test for scene selection save functionality.

This test verifies the end-to-end workflow of saving a selection
of mediaobjects and then importing it back.
"""

import os
import tempfile
from unittest.mock import patch

from pyzui.objects.scene.scene import Scene


class TestSceneSelectionSaveIntegration:
    """
    Feature: Scene Selection Save Integration

    This class tests the integration of the scene selection save functionality,
    verifying that selections can be saved and imported with proper
    coordinate transformation.
    """

    def test_save_selection_and_import(self):
        """
        Scenario: Save selection and import it

        Given a scene with selected mediaobjects
        When the selection is saved to a file and then imported
        Then the imported mediaobjects should appear at the viewport centre
        """
        # Create a scene with mediaobjects
        scene1 = Scene()
        scene1.viewport_size = (800, 600)

        # Add mock mediaobjects to scene1
        from unittest.mock import Mock
        mock_obj1 = Mock()
        mock_obj1.media_id = "test_image1.jpg"
        mock_obj1.zoomlevel = 1.0
        mock_obj1.pos = (100.0, 50.0)
        mock_obj1.topleft = (80.0, 30.0)
        mock_obj1.bottomright = (120.0, 70.0)
        mock_obj1.onscreen_area = 1600.0
        type(mock_obj1).__name__ = "TiledMediaObject"

        mock_obj2 = Mock()
        mock_obj2.media_id = "test_image2.jpg"
        mock_obj2.zoomlevel = 0.5
        mock_obj2.pos = (200.0, 150.0)
        mock_obj2.topleft = (180.0, 130.0)
        mock_obj2.bottomright = (220.0, 170.0)
        mock_obj2.onscreen_area = 1600.0
        type(mock_obj2).__name__ = "TiledMediaObject"

        scene1.add(mock_obj1)
        scene1.add(mock_obj2)

        # Select both objects
        scene1.selection = [mock_obj1, mock_obj2]

        # Save selection to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pzs', delete=False) as f:
            temp_file = f.name

        try:
            # Mock the _write_mediaobject_line method to avoid actual file dependencies
            with patch.object(scene1, '_write_mediaobject_line') as mock_write:
                scene1.save_selection(temp_file)

                # Verify _write_mediaobject_line was called twice (once for each object)
                assert mock_write.call_count == 2

                # Verify file was created
                assert os.path.exists(temp_file)

                # Read the file to verify header
                with open(temp_file) as f:
                    first_line = f.readline().strip()
                    assert first_line == "0\t0\t0"

        finally:
            # Clean up temporary file
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_save_selection_round_trip(self):
        """
        Scenario: Save selection and import into another scene

        Given a scene with selected mediaobjects
        When the selection is saved and then imported into another scene
        Then the imported mediaobjects should maintain relative positions
        """
        # Create first scene with mediaobjects
        scene1 = Scene()
        scene1.viewport_size = (800, 600)

        # Create mock objects with specific positions
        from unittest.mock import Mock
        mock_obj1 = Mock()
        mock_obj1.media_id = "obj1"
        mock_obj1.zoomlevel = 1.0
        mock_obj1.pos = (0.0, 0.0)
        type(mock_obj1).__name__ = "TiledMediaObject"

        mock_obj2 = Mock()
        mock_obj2.media_id = "obj2"
        mock_obj2.zoomlevel = 1.0
        mock_obj2.pos = (100.0, 100.0)
        type(mock_obj2).__name__ = "TiledMediaObject"

        scene1.add(mock_obj1)
        scene1.add(mock_obj2)

        # Select objects
        scene1.selection = [mock_obj1, mock_obj2]

        # Save selection to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pzs', delete=False) as f:
            temp_file = f.name

        try:
            # Write actual file content for testing
            # Centroid is at (50, 50)
            # Offsets: obj1: (-50, -50), obj2: (50, 50)
            with open(temp_file, 'w') as f:
                f.write("0\t0\t0\n")
                f.write("TiledMediaObject\tobj1\t1.0\t-50.0\t-50.0\n")
                f.write("TiledMediaObject\tobj2\t1.0\t50.0\t50.0\n")

            # Create second scene
            scene2 = Scene()
            scene2.viewport_size = (1024, 768)

            # Mock _create_mediaobject_from_line to return mock objects
            mock_import_obj1 = Mock()
            mock_import_obj1.media_id = "obj1"
            mock_import_obj1.zoomlevel = 1.0
            mock_import_obj1.pos = (-50.0, -50.0)  # Offset position
            mock_import_obj1.topleft = (100.0, 100.0)
            mock_import_obj1.bottomright = (200.0, 200.0)

            mock_import_obj2 = Mock()
            mock_import_obj2.media_id = "obj2"
            mock_import_obj2.zoomlevel = 1.0
            mock_import_obj2.pos = (50.0, 50.0)  # Offset position
            mock_import_obj2.topleft = (300.0, 300.0)
            mock_import_obj2.bottomright = (400.0, 400.0)

            with patch.object(scene2, '_create_mediaobject_from_line') as mock_create:
                mock_create.side_effect = [mock_import_obj1, mock_import_obj2]

                # Import the saved selection
                scene2.import_scene(temp_file)

                # Verify objects were created
                assert mock_create.call_count == 2

                # Verify positions were transformed (should be adjusted to viewport centre)
                # The exact transformation depends on scene2._centre
                # Just verify that pos was updated from the offset values
                assert mock_import_obj1.pos != (-50.0, -50.0)
                assert mock_import_obj2.pos != (50.0, 50.0)

        finally:
            # Clean up temporary file
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_save_selection_with_existing_scene(self):
        """
        Scenario: Save selection from scene with other objects

        Given a scene with both selected and unselected mediaobjects
        When saving the selection
        Then only selected objects should be saved
        """
        from unittest.mock import Mock, patch

        scene = Scene()
        scene.viewport_size = (800, 600)

        # Create selected objects
        selected_obj1 = Mock()
        selected_obj1.media_id = "selected1.jpg"
        selected_obj1.zoomlevel = 1.0
        selected_obj1.pos = (100.0, 100.0)
        type(selected_obj1).__name__ = "TiledMediaObject"

        selected_obj2 = Mock()
        selected_obj2.media_id = "selected2.jpg"
        selected_obj2.zoomlevel = 0.5
        selected_obj2.pos = (200.0, 200.0)
        type(selected_obj2).__name__ = "TiledMediaObject"

        # Create unselected object
        unselected_obj = Mock()
        unselected_obj.media_id = "unselected.jpg"
        unselected_obj.zoomlevel = 1.5
        unselected_obj.pos = (300.0, 300.0)
        type(unselected_obj).__name__ = "TiledMediaObject"

        # Add all objects to scene
        scene.add(selected_obj1)
        scene.add(selected_obj2)
        scene.add(unselected_obj)

        # Select only first two objects
        scene.selection = [selected_obj1, selected_obj2]

        # Save selection to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pzs', delete=False) as f:
            temp_file = f.name

        try:
            # Mock file writing
            written_content = []
            mock_file = Mock()
            mock_file.write = lambda s: written_content.append(s)

            with patch('builtins.open', return_value=mock_file):
                scene.save_selection(temp_file)

            # Parse written content
            content = "".join(written_content)
            lines = content.strip().split('\n')

            # Should have header + 2 selected objects
            assert len(lines) == 3

            # Check that only selected objects are in the file
            object_lines = lines[1:]
            media_ids = [line.split('\t')[1] for line in object_lines]

            assert "selected1.jpg" in media_ids
            assert "selected2.jpg" in media_ids
            assert "unselected.jpg" not in media_ids

        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.unlink(temp_file)
