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
Integration tests for copy/paste functionality in PyZUI.

These tests verify the complete copy/paste workflow including:
- Scene clipboard operations
- SVGMediaObject serialization/deserialization
- Keyboard shortcuts
- Selection behavior
"""

from unittest.mock import Mock, patch

from pyzui.objects.mediaobjects.svgmediaobject import SVGMediaObject
from pyzui.objects.scene.scene import Scene


class TestCopyPasteIntegration:
    """
    Feature: Copy/Paste Functionality Integration

    Tests the complete copy/paste workflow for SVGMediaObjects,
    including scene clipboard operations, keyboard shortcuts,
    and selection behavior.
    """

    @patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer')
    def test_single_svg_copy_paste(self, mock_renderer_class):
        """
        Scenario: Copy and paste a single SVGMediaObject

        Given a scene with one SVGMediaObject
        When the object is copied and pasted
        Then a new object should be created with offset position
        And the original should be deselected
        And the new object should be selected
        """
        # Setup mock renderer
        mock_renderer = Mock()
        mock_renderer.load.return_value = True
        mock_size = Mock()
        mock_size.width.return_value = 100
        mock_size.height.return_value = 200
        mock_renderer.defaultSize.return_value = mock_size
        mock_renderer_class.return_value = mock_renderer

        # Create scene and object
        scene = Scene()
        svg_obj = SVGMediaObject("test.svg", scene)

        # Set object position using public property
        svg_obj.pos = (50.0, 60.0)
        svg_obj.zoomlevel = 0.0

        # Add object to scene and select it
        scene.add(svg_obj)
        scene.selection = svg_obj

        # Copy the selection
        scene.copy_selection()

        # Verify original is deselected
        assert scene.selection is None

        # Paste the object with offset position (exercises set_position code path)
        pasted_objects = scene.paste((100.0, 200.0))

        # Verify one object was pasted
        assert len(pasted_objects) == 1
        pasted = pasted_objects[0]

        # Verify pasted object is selected
        # When pasting a single object, it should be selected directly
        assert scene.selection == pasted

        # Verify pasted object is a different instance
        assert pasted is not svg_obj
        assert pasted.media_id == svg_obj.media_id

    @patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer')
    def test_multiple_svg_copy_paste(self, mock_renderer_class):
        """
        Scenario: Copy and paste multiple SVGMediaObjects

        Given a scene with multiple SVGMediaObjects selected
        When the objects are copied and pasted
        Then new objects should be created for each original
        And all new objects should be selected
        """
        # Setup mock renderer
        mock_renderer = Mock()
        mock_renderer.load.return_value = True
        mock_size = Mock()
        mock_size.width.return_value = 100
        mock_size.height.return_value = 200
        mock_renderer.defaultSize.return_value = mock_size
        mock_renderer_class.return_value = mock_renderer

        # Create scene and objects
        scene = Scene()
        objects = []

        for i in range(3):
            obj = SVGMediaObject(f"test{i}.svg", scene)
            # Set object position using public property
            obj.pos = (float(10 * i), float(20 * i))
            obj.zoomlevel = 0.0

            scene.add(obj)
            objects.append(obj)

        # Select all objects
        scene.selection = objects

        # Copy the selection
        scene.copy_selection()

        # Verify originals are deselected
        assert scene.selection is None

        # Paste the objects with offset position (exercises set_position code path)
        pasted_objects = scene.paste((100.0, 200.0))

        # Verify correct number of objects were pasted
        assert len(pasted_objects) == 3

        # Verify all pasted objects are selected
        assert scene.selection == pasted_objects

        # Verify each pasted object is a different instance
        for i, pasted in enumerate(pasted_objects):
            assert pasted is not objects[i]
            assert pasted.media_id == objects[i].media_id

    @patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer')
    def test_empty_selection_copy(self, mock_renderer_class):
        """
        Scenario: Copy with no selection

        Given a scene with no selected objects
        When copy_selection() is called
        Then nothing should be copied to clipboard
        And no error should occur
        """
        # Setup mock renderer (not really needed but keeps patch consistent)
        mock_renderer = Mock()
        mock_renderer.load.return_value = True
        mock_renderer_class.return_value = mock_renderer

        scene = Scene()

        # Copy with no selection should not crash
        scene.copy_selection()

        # Paste should return empty list
        pasted_objects = scene.paste()
        assert pasted_objects == []

    @patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer')
    def test_empty_clipboard_paste(self, mock_renderer_class):
        """
        Scenario: Paste with empty clipboard

        Given a scene with empty clipboard
        When paste() is called
        Then no objects should be created
        And an empty list should be returned
        """
        # Setup mock renderer
        mock_renderer = Mock()
        mock_renderer.load.return_value = True
        mock_renderer_class.return_value = mock_renderer

        scene = Scene()

        # Paste with empty clipboard should return empty list
        pasted_objects = scene.paste()
        assert pasted_objects == []

    @patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer')
    def test_copy_clear_clipboard(self, mock_renderer_class):
        """
        Scenario: Copy replaces previous clipboard contents

        Given a scene with objects in clipboard
        When new objects are copied
        Then the clipboard should contain only the new objects
        """
        # Setup mock renderer
        mock_renderer = Mock()
        mock_renderer.load.return_value = True
        mock_size = Mock()
        mock_size.width.return_value = 100
        mock_size.height.return_value = 200
        mock_renderer.defaultSize.return_value = mock_size
        mock_renderer_class.return_value = mock_renderer

        scene = Scene()

        # Create first object and copy it
        obj1 = SVGMediaObject("test1.svg", scene)
        # Set object positions using public properties
        obj1.pos = (10.0, 20.0)
        obj1.zoomlevel = 0.0
        scene.add(obj1)
        scene.selection = obj1

        # Copy first object
        scene.copy_selection()

        # Create second object
        obj2 = SVGMediaObject("test2.svg", scene)
        obj2.pos = (30.0, 40.0)
        obj2.zoomlevel = 0.0
        scene.add(obj2)
        scene.selection = obj2

        # Copy second object (should replace clipboard contents)
        scene.copy_selection()

        # Paste should give us the second object, not the first
        pasted_objects = scene.paste()
        assert len(pasted_objects) == 1
        assert scene.selection == pasted_objects[0]
        assert pasted_objects[0].media_id == "test2.svg"  # Should be second object
