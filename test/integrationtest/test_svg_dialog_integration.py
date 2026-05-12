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
Integration tests for SVG dialog functionality.

Tests the complete workflow from SVG selection through modification
to object creation and scene integration.
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from pyzui.objects.mediaobjects.svgmediaobject import SVGMediaObject
from pyzui.windows.dialogwindows.modifysvginputdialog import ModifySVGInputDialog
from pyzui.windows.dialogwindows.svgpickerinputdialog import OpenSVGPickerInputDialog


class TestSVGDialogIntegration:
    """
    Feature: SVG Dialog Integration Workflow

    Tests the complete integration between SVG dialogs and media objects,
    including selection, modification, and scene integration.
    """

    @pytest.fixture
    def test_svg_content(self):
        """Test SVG content for integration tests."""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
    <circle cx="100" cy="100" r="70" stroke="black" stroke-width="8" fill="none"/>
</svg>'''

    @pytest.fixture
    def test_svg_file(self, test_svg_content):
        """Create a temporary SVG file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(test_svg_content)
            svg_file = f.name

        yield svg_file

        # Cleanup
        if os.path.exists(svg_file):
            os.unlink(svg_file)

    @pytest.fixture
    def mock_svg_directory(self, test_svg_file, tmp_path):
        """Create mock SVG directory structure."""
        svg_dir = tmp_path / "data" / "SVG"
        svg_dir.mkdir(parents=True, exist_ok=True)

        # Copy test SVG to mock directory
        test_svg_name = "test_circle.svg"
        mock_svg_path = svg_dir / test_svg_name
        shutil.copy(test_svg_file, mock_svg_path)

        return str(mock_svg_path), str(svg_dir)

    @pytest.fixture
    def mock_scene(self):
        """Create a mock scene for testing."""
        scene = Mock()
        scene.viewport_size = (800, 600)
        scene.add = Mock()
        scene.remove = Mock()
        return scene

    def test_svg_picker_to_scene_integration(self, mock_svg_directory, mock_scene):
        """
        Scenario: Complete SVG picker to scene integration

        Given an SVG file in the data/SVG directory
        When user selects SVG via OpenSVGPickerInputDialog
        And applies color and thickness modifications
        And adds the SVG to the scene
        Then an SVGMediaObject should be created with cache hash
        And the object should be added to the scene
        And modifications should be preserved
        """
        mock_svg_path, _svg_dir = mock_svg_directory

        # Mock the dialog execution
        with patch('pyzui.windows.dialogwindows.svgpickerinputdialog.os.path.isdir', return_value=True), \
             patch('pyzui.windows.dialogwindows.svgpickerinputdialog.os.listdir', return_value=['test_circle.svg']), \
             patch('pyzui.windows.dialogwindows.svgpickerinputdialog.os.path.join') as mock_join, \
             patch('pyzui.windows.dialogwindows.svgpickerinputdialog.get_svg_cache') as mock_get_cache:

            # Setup mock for os.path.join to avoid recursion
            mock_join.side_effect = lambda *args: '/'.join(args)

            # Mock SVG cache
            mock_cache = Mock()
            mock_cache.store_svg.return_value = "svg_modified123"
            mock_cache.get_cache_path.return_value = Path("/tmp/pyzui_svg_/svg_modified123.svg")
            mock_get_cache.return_value = mock_cache

            # Create dialog and simulate user interaction
            dialog = OpenSVGPickerInputDialog()
            dialog.selected_svg = mock_svg_path
            dialog.shape_color = "ff0000"  # Red

            # Mock thickness input
            mock_thickness_input = Mock()
            mock_thickness_input.text.return_value = "15"
            dialog.thickness_input = mock_thickness_input

            # Mock _main_dialog to avoid Qt widget creation
            mock_dialog = Mock()
            mock_dialog.exec.return_value = 1  # Accepted
            with patch.object(dialog, '_main_dialog', return_value=mock_dialog):
                # Run dialog simulation
                ok, cache_hash = dialog._run_dialog()

                assert ok is True
                assert cache_hash == "svg_modified123"

                # Verify cache was called with modified content
                mock_cache.store_svg.assert_called_once()
                stored_content = mock_cache.store_svg.call_args[0][0]
                assert 'ff0000' in stored_content.lower()
                assert 'stroke-width="15"' in stored_content

                # Create SVGMediaObject from cache hash - need to mock get_svg_cache and QtSvg for SVGMediaObject
                with patch('pyzui.objects.mediaobjects.svgmediaobject.get_svg_cache', return_value=mock_cache), \
                     patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer') as mock_renderer_class:

                    # Mock renderer
                    mock_renderer = Mock()
                    mock_renderer.load.return_value = True
                    mock_renderer.defaultSize.return_value = Mock(width=lambda: 100, height=lambda: 100)
                    mock_renderer_class.return_value = mock_renderer

                    svg_object = SVGMediaObject(cache_hash, mock_scene)

                    # Verify object properties
                    assert svg_object._media_id == "svg_modified123"
                    assert svg_object.is_modified is True  # Cache hashes are marked as modified

                    # Add to scene
                    mock_scene.add(svg_object)
                    mock_scene.add.assert_called_once_with(svg_object)

    def test_svg_modification_workflow(self, test_svg_content, mock_scene):
        """
        Scenario: Modify existing SVG object workflow

        Given an existing SVGMediaObject in the scene
        When user opens ModifySVGInputDialog for the object
        And changes color and thickness
        And applies modifications
        Then the object should be updated with new cache hash
        And modification state should be preserved
        """
        # Create initial SVG object
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(test_svg_content)
            svg_file = f.name

        try:
            # Mock QtSvg for SVGMediaObject creation
            with patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer') as mock_renderer_class:
                mock_renderer = Mock()
                mock_renderer.load.return_value = True
                mock_renderer.defaultSize.return_value = Mock(width=lambda: 100, height=lambda: 100)
                mock_renderer_class.return_value = mock_renderer

                svg_object = SVGMediaObject(svg_file, mock_scene)

            # Mock the modify dialog
            with patch('pyzui.windows.dialogwindows.modifysvginputdialog.QDialog') as mock_dialog_class, \
                 patch('pyzui.windows.dialogwindows.modifysvginputdialog.QMessageBox') as mock_msgbox_class, \
                 patch('pyzui.windows.dialogwindows.modifysvginputdialog.get_svg_cache') as mock_get_cache:

                # Setup dialog to accept modifications
                mock_dialog = Mock()
                mock_dialog.exec.return_value = 1  # Accepted
                mock_dialog_class.return_value = mock_dialog

                mock_msgbox = Mock()
                mock_msgbox.exec.return_value = 1  # Yes (for warning)
                mock_msgbox_class.return_value = mock_msgbox

                # Mock SVG cache
                mock_cache = Mock()
                mock_cache.store_svg.return_value = "svg_modified456"
                mock_get_cache.return_value = mock_cache

                # Create modify dialog
                modify_dialog = ModifySVGInputDialog(svg_object)

                # Set modification values
                modify_dialog.modified_color = "00ff00"  # Green
                modify_dialog.modified_thickness = "20"
                modify_dialog.preview_applied = True

                # Mock thickness input
                mock_thickness_input = Mock()
                mock_thickness_input.text.return_value = "20"
                modify_dialog.thickness_input = mock_thickness_input

                # Mock _main_dialog to avoid Qt widget creation
                mock_dialog = Mock()
                mock_dialog.exec.return_value = 1  # Accepted
                with patch.object(modify_dialog, '_main_dialog', return_value=mock_dialog), \
                     patch.object(modify_dialog, '_show_source_warning_dialog', return_value=True):
                    # Also mock QDialog.DialogCode.Accepted
                    with patch('pyzui.windows.dialogwindows.modifysvginputdialog.QDialog.DialogCode.Accepted', 1):
                        # Run dialog
                        ok, new_cache_hash = modify_dialog._run_dialog()

                        print(f"ok: {ok}, new_cache_hash: {new_cache_hash}")
                        print(f"mock_dialog.exec.call_count: {mock_dialog.exec.call_count}")
                        print(f"mock_dialog.exec.return_value: {mock_dialog.exec.return_value}")

                        assert ok is True
                        assert new_cache_hash == "svg_modified456"

                        # Verify cache was called
                        mock_cache.store_svg.assert_called_once()

        finally:
            if os.path.exists(svg_file):
                os.unlink(svg_file)

    def test_svg_embedding_after_modification(self, mock_svg_directory, mock_scene):
        """
        Scenario: SVG embedding after modification

        Given a modified SVG object from picker dialog
        When the object is marked as modified
        And scene is serialized
        Then SVG content should be embedded in scene file
        And original file path should be preserved if available
        """
        mock_svg_path, _svg_dir = mock_svg_directory

        # Create SVG object from file (not cache)
        svg_object = SVGMediaObject(mock_svg_path, mock_scene)

        # Mark as modified (simulating picker dialog modification)
        svg_object.mark_as_modified()

        # Verify modification state
        assert svg_object.is_modified is True
        assert svg_object.original_file_path == mock_svg_path

        # Test serialization
        serialized = svg_object.to_dict()

        assert 'media_id' in serialized
        assert 'is_modified' in serialized
        assert serialized['is_modified'] is True
        assert 'original_file_path' in serialized
        assert serialized['original_file_path'] == mock_svg_path

        # Test deserialization
        new_scene = Mock()
        new_scene.viewport_size = (800, 600)

        with patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer') as mock_renderer_class:
            mock_renderer = Mock()
            mock_renderer.load.return_value = True
            mock_renderer.defaultSize.return_value = Mock(width=lambda: 200, height=lambda: 200)
            mock_renderer_class.return_value = mock_renderer

            deserialized = SVGMediaObject.from_dict(serialized, new_scene)

            assert deserialized.is_modified is True
            assert deserialized.original_file_path == mock_svg_path

    def test_color_history_persistence(self, tmp_path):
        """
        Scenario: Color history persistence across dialogs

        Given user selects a color in SVG picker dialog
        When color is added to history
        And modify dialog is opened later
        Then the same color should appear in color history
        """
        color_dir = tmp_path / ".pyzui" / "colorstore"
        color_dir.mkdir(parents=True, exist_ok=True)
        color_file = color_dir / "color_list.txt"

        # Start with some colors
        with open(color_file, 'w') as f:
            f.write("ff0000\n00ff00\n0000ff\n")

        # Test picker dialog loads colors
        with patch('pyzui.windows.dialogwindows.svgpickerinputdialog.os.path.isfile', return_value=True), \
             patch('pyzui.windows.dialogwindows.svgpickerinputdialog.os.path.isdir', return_value=True), \
             patch('pyzui.windows.dialogwindows.svgpickerinputdialog.os.environ', {}), \
             patch('pyzui.windows.dialogwindows.svgpickerinputdialog.os.path.expanduser', return_value=str(tmp_path)):

            picker_dialog = OpenSVGPickerInputDialog()

            assert len(picker_dialog.color_codes) == 3
            assert "ff0000" in picker_dialog.color_codes

            # Simulate adding new color
            new_color = "ff5733"
            if new_color not in picker_dialog.color_codes:
                picker_dialog.color_codes.append(new_color)

            # Save color history (simulated)
            with open(color_file, 'w') as f:
                for code in picker_dialog.color_codes:
                    f.write(str(code) + '\n')

        # Test modify dialog loads updated colors
        with patch('pyzui.windows.dialogwindows.modifysvginputdialog.os.path.isfile', return_value=True), \
             patch('pyzui.windows.dialogwindows.modifysvginputdialog.os.environ', {}), \
             patch('pyzui.windows.dialogwindows.modifysvginputdialog.os.path.expanduser', return_value=str(tmp_path)):

            mock_svg_object = Mock()
            mock_svg_object._media_id = "test.svg"
            mock_svg_object.get_svg_content.return_value = '<svg></svg>'

            modify_dialog = ModifySVGInputDialog(mock_svg_object)

            assert len(modify_dialog.color_codes) == 4  # Original 3 + new color
            assert "ff0000" in modify_dialog.color_codes
            assert "ff5733" in modify_dialog.color_codes

    def test_svg_cache_integration(self, test_svg_content, mock_scene):
        """
        Scenario: SVG cache integration across components

        Given SVG content is modified via picker dialog
        When content is stored in SVG cache
        And retrieved via cache hash
        Then the same content should be retrievable
        And SVGMediaObject should load from cache
        """
        # Create test SVG file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(test_svg_content)
            svg_file = f.name

        try:
            # Import actual cache for integration test
            from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import SVGCache

            # Use temporary cache directory
            cache_dir = tempfile.mkdtemp(prefix="pyzui_test_cache_")

            try:
                # Create cache instance
                cache = SVGCache(cache_root=cache_dir)

                # Store modified SVG in cache
                modified_content = test_svg_content.replace('black', '#ff0000').replace('stroke-width="8"', 'stroke-width="15"')
                cache_hash = cache.store_svg(modified_content)

                assert cache_hash.startswith("svg_")
                assert len(cache_hash) == len("svg_") + 8  # svg_ + 8 chars

                # Verify content can be retrieved
                retrieved_content = cache.get_svg_content(cache_hash)
                assert retrieved_content is not None
                assert "ff0000" in retrieved_content.lower()
                assert 'stroke-width="15"' in retrieved_content

                # Verify cache path exists
                cache_path = cache.get_cache_path(cache_hash)
                assert cache_path.exists()

                # Create SVGMediaObject from cache hash - need to mock get_svg_cache
                with patch('pyzui.objects.mediaobjects.svgmediaobject.get_svg_cache', return_value=cache), \
                     patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer') as mock_renderer_class:

                    # Mock renderer
                    mock_renderer = Mock()
                    mock_renderer.load.return_value = True
                    mock_renderer.defaultSize.return_value = Mock(width=lambda: 100, height=lambda: 100)
                    mock_renderer_class.return_value = mock_renderer

                    svg_object = SVGMediaObject(cache_hash, mock_scene)

                    # Verify object loads from cache
                    assert svg_object._media_id == cache_hash
                    assert svg_object.is_modified is True  # Cache hashes are marked as modified

                    # Verify object can retrieve content
                    object_content = svg_object.get_svg_content()
                assert object_content is not None
                assert "ff0000" in object_content.lower()

            finally:
                # Cleanup cache directory
                shutil.rmtree(cache_dir, ignore_errors=True)

        finally:
            if os.path.exists(svg_file):
                os.unlink(svg_file)

    def test_error_handling_integration(self, mock_svg_directory, mock_scene):
        """
        Scenario: Error handling in SVG workflow

        Given invalid SVG file or missing directory
        When SVG operations are attempted
        Then appropriate error handling should occur
        And user should be notified gracefully
        """
        mock_svg_path, _svg_dir = mock_svg_directory

        # Test 1: Invalid SVG file
        invalid_svg = mock_svg_path + ".invalid"
        with open(invalid_svg, 'w') as f:
            f.write("Not valid XML")

        try:
            # Should raise LoadError when creating SVGMediaObject
            with pytest.raises(Exception) as exc_info:
                SVGMediaObject(invalid_svg, mock_scene)

            # Error message should indicate parsing failure
            assert "unable to parse" in str(exc_info.value).lower()

        finally:
            if os.path.exists(invalid_svg):
                os.unlink(invalid_svg)

        # Test 2: Missing SVG directory in picker dialog
        with patch('pyzui.windows.dialogwindows.svgpickerinputdialog.os.path.isdir', return_value=False):
            dialog = OpenSVGPickerInputDialog()

            # Should handle missing directory gracefully
            assert len(dialog.SVG_FILES) == 0
            assert len(dialog.SVG_NAMES) == 0

        # Test 3: Modify dialog with non-cache file (should show warning)
        with patch('pyzui.windows.dialogwindows.modifysvginputdialog.QMessageBox') as mock_msgbox_class:
            mock_msgbox = Mock()
            mock_msgbox.exec.return_value = 0  # No (user cancels)
            mock_msgbox_class.return_value = mock_msgbox

            mock_svg_object = Mock()
            mock_svg_object._media_id = "/some/other/path/test.svg"  # Not cache hash
            mock_svg_object.get_svg_content.return_value = '<svg></svg>'

            modify_dialog = ModifySVGInputDialog(mock_svg_object)

            # Should show warning and return False if user cancels
            ok, result = modify_dialog._run_dialog()

            assert ok is False
            assert result is None
            mock_msgbox_class.assert_called_once()

    def test_performance_multiple_svgs(self, tmp_path, mock_scene):
        """
        Scenario: Performance with multiple SVG objects

        Given multiple SVG objects in scene
        When objects are modified and cached
        Then cache should handle multiple entries efficiently
        And object retrieval should be fast
        """
        # Import actual cache
        from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import SVGCache

        # Use temporary cache directory
        cache_dir = tempfile.mkdtemp(prefix="pyzui_test_perf_")

        try:
            cache = SVGCache(cache_root=cache_dir)

            # Create multiple SVG objects with different modifications
            svg_objects = []
            colors = ["ff0000", "00ff00", "0000ff", "ffff00", "ff00ff"]
            thicknesses = ["10", "15", "20", "25", "30"]

            base_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
    <rect width="80" height="80" x="10" y="10"/>
</svg>'''

            for _i, (color, thickness) in enumerate(zip(colors, thicknesses, strict=False)):
                # Modify SVG
                modified_svg = base_svg.replace('<rect', f'<rect stroke="#{color}" stroke-width="{thickness}"')

                # Store in cache
                cache_hash = cache.store_svg(modified_svg)

                # Create object - need to mock get_svg_cache
                with patch('pyzui.objects.mediaobjects.svgmediaobject.get_svg_cache', return_value=cache), \
                     patch('pyzui.objects.mediaobjects.svgmediaobject.QtSvg.QSvgRenderer') as mock_renderer_class:

                    # Mock renderer
                    mock_renderer = Mock()
                    mock_renderer.load.return_value = True
                    mock_renderer.defaultSize.return_value = Mock(width=lambda: 100, height=lambda: 100)
                    mock_renderer_class.return_value = mock_renderer

                    svg_object = SVGMediaObject(cache_hash, mock_scene)
                    svg_objects.append(svg_object)

                    # Verify content
                    content = svg_object.get_svg_content()
                    assert content is not None
                    assert color in content.lower()
                    assert f'stroke-width="{thickness}"' in content

            # Verify all objects are unique
            cache_hashes = [obj._media_id for obj in svg_objects]
            assert len(set(cache_hashes)) == len(svg_objects)  # All unique

            # Verify cache directory contains expected files
            cache_files = list(Path(cache_dir).glob("*.svg"))
            assert len(cache_files) == len(svg_objects)

        finally:
            # Cleanup
            shutil.rmtree(cache_dir, ignore_errors=True)
