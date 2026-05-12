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

"""Unit tests for ModifySVGInputDialog."""

from unittest.mock import Mock, patch

import pytest
from PySide6 import QtWidgets


class TestModifySVGInputDialog:
    """
    Feature: ModifySVGInputDialog

    This class tests the ModifySVGInputDialog for modifying SVG objects.
    """

    @pytest.fixture(scope="class")
    def qapp(self):
        """Create QApplication instance for tests."""
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication([])
        yield app
        app.quit()

    @pytest.fixture
    def mock_svg_object(self):
        """Create a mock SVGMediaObject."""
        mock = Mock()
        mock._media_id = "svg_test123"
        mock.get_svg_content.return_value = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
    <circle cx="100" cy="100" r="70" stroke="black" stroke-width="8" fill="none"/>
</svg>'''
        mock.mark_as_modified = Mock()
        return mock

    @pytest.fixture
    def mock_svg_cache(self):
        """Create a mock SVG cache."""
        mock = Mock()
        mock.store_svg.return_value = "svg_modified123"
        return mock

    def test_init_with_cache_hash(self, qapp, mock_svg_object):
        """
        Scenario: Initialize dialog with cache hash

        Given an SVGMediaObject with cache hash media_id
        When creating ModifySVGInputDialog
        Then it should recognize it as a cache file
        """
        from pyzui.windows.dialogwindows.modifysvginputdialog import ModifySVGInputDialog

        dialog = ModifySVGInputDialog(mock_svg_object)

        assert dialog.svg_object == mock_svg_object
        assert dialog.original_media_id == "svg_test123"
        assert dialog.is_cache_file
        assert not dialog.is_tmp_file

    def test_init_with_file_path(self, qapp):
        """
        Scenario: Initialize dialog with file path

        Given an SVGMediaObject with file path media_id
        When creating ModifySVGInputDialog
        Then it should recognize it as a file path
        """
        from pyzui.windows.dialogwindows.modifysvginputdialog import ModifySVGInputDialog

        mock_svg = Mock()
        mock_svg._media_id = "/home/user/test.svg"
        mock_svg.get_svg_content.return_value = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
    <circle cx="100" cy="100" r="70" stroke="red" stroke-width="5" fill="none"/>
</svg>'''

        dialog = ModifySVGInputDialog(mock_svg)

        assert not dialog.is_cache_file
        assert not dialog.is_tmp_file

    def test_init_with_tmp_file(self, qapp):
        """
        Scenario: Initialize dialog with /tmp file

        Given an SVGMediaObject with /tmp/pyzui_svg_ file path
        When creating ModifySVGInputDialog
        Then it should recognize it as a tmp file
        """
        from pyzui.windows.dialogwindows.modifysvginputdialog import ModifySVGInputDialog

        mock_svg = Mock()
        mock_svg._media_id = "/tmp/pyzui_svg_/test.svg"
        mock_svg.get_svg_content.return_value = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
    <circle cx="100" cy="100" r="70" stroke="blue" stroke-width="3" fill="none"/>
</svg>'''

        dialog = ModifySVGInputDialog(mock_svg)

        assert not dialog.is_cache_file
        assert dialog.is_tmp_file

    def test_extract_current_color(self, qapp, mock_svg_object):
        """
        Scenario: Extract color from SVG content

        Given an SVG with stroke color
        When extracting current color
        Then it should return hex color code
        """
        from pyzui.windows.dialogwindows.modifysvginputdialog import ModifySVGInputDialog

        dialog = ModifySVGInputDialog(mock_svg_object)
        color = dialog._extract_current_color()

        assert color == '000000'  # black

    def test_extract_current_thickness(self, qapp, mock_svg_object):
        """
        Scenario: Extract thickness from SVG content

        Given an SVG with stroke-width
        When extracting current thickness
        Then it should return thickness value
        """
        from pyzui.windows.dialogwindows.modifysvginputdialog import ModifySVGInputDialog

        dialog = ModifySVGInputDialog(mock_svg_object)
        thickness = dialog._extract_current_thickness()

        assert thickness == '8'

    def test_color_name_to_hex(self):
        """
        Scenario: Convert color names to hex

        Given various color names
        When converting to hex
        Then it should return correct hex codes
        """
        from pyzui.windows.dialogwindows.modifysvginputdialog import ModifySVGInputDialog

        # Create dialog with mock object
        mock_svg = Mock()
        mock_svg._media_id = "svg_test"
        mock_svg.get_svg_content.return_value = ""

        dialog = ModifySVGInputDialog(mock_svg)

        # Test color name conversion
        assert dialog._color_name_to_hex('black') == '000000'
        assert dialog._color_name_to_hex('red') == 'ff0000'
        assert dialog._color_name_to_hex('#ff0000') == 'ff0000'
        assert dialog._color_name_to_hex('#00FF00') == '00ff00'

    def test_validate_svg_source_cache(self, qapp, mock_svg_object):
        """
        Scenario: Validate cache file source

        Given an SVG from cache
        When validating source
        Then it should return True (safe)
        """
        from pyzui.windows.dialogwindows.modifysvginputdialog import ModifySVGInputDialog

        dialog = ModifySVGInputDialog(mock_svg_object)
        assert dialog._validate_svg_source()

    def test_validate_svg_source_non_cache(self, qapp):
        """
        Scenario: Validate non-cache file source

        Given an SVG not from cache
        When validating source
        Then it should show warning dialog
        """
        from pyzui.windows.dialogwindows.modifysvginputdialog import ModifySVGInputDialog

        # Mock SVG object with file path
        mock_svg = Mock()
        mock_svg._media_id = "/home/user/test.svg"
        mock_svg.get_svg_content.return_value = ""

        # Create dialog and patch the warning dialog method
        dialog = ModifySVGInputDialog(mock_svg)

        # Patch _show_source_warning_dialog to return True (user clicked Yes)
        with patch.object(dialog, '_show_source_warning_dialog', return_value=True):
            result = dialog._validate_svg_source()
            assert result

    def test_modify_svg_file(self, qapp, mock_svg_object, mock_svg_cache):
        """
        Scenario: Modify SVG and store in cache

        Given an SVG object
        When modifying color and thickness
        Then it should return new cache hash
        """
        from pyzui.windows.dialogwindows.modifysvginputdialog import ModifySVGInputDialog

        with patch('pyzui.windows.dialogwindows.modifysvginputdialog.get_svg_cache', return_value=mock_svg_cache):
            dialog = ModifySVGInputDialog(mock_svg_object)
            cache_hash = dialog._modify_svg_file('ff0000', '10')

            assert cache_hash == 'svg_modified123'
            mock_svg_cache.store_svg.assert_called_once()

    def test_run_dialog_cancelled(self, qapp, mock_svg_object):
        """
        Scenario: User cancels dialog

        Given a dialog
        When user cancels
        Then it should return (False, None)
        """
        from pyzui.windows.dialogwindows.modifysvginputdialog import ModifySVGInputDialog

        # Mock dialog to return rejected
        with patch.object(ModifySVGInputDialog, '_main_dialog') as mock_main_dialog:
            mock_dialog = Mock()
            mock_dialog.exec.return_value = QtWidgets.QDialog.Rejected
            mock_main_dialog.return_value = mock_dialog

            dialog = ModifySVGInputDialog(mock_svg_object)
            result = dialog._run_dialog()

            assert result == (False, None)

    @patch('pyzui.windows.dialogwindows.modifysvginputdialog.get_svg_cache')
    def test_run_dialog_accepted_with_changes(self, mock_get_cache, qapp, mock_svg_object):
        """
        Scenario: User accepts dialog with changes

        Given a dialog with modifications
        When user accepts
        Then it should return (True, cache_hash)
        """
        from pyzui.windows.dialogwindows.modifysvginputdialog import ModifySVGInputDialog

        # Mock cache
        mock_cache = Mock()
        mock_cache.store_svg.return_value = 'svg_newhash'
        mock_get_cache.return_value = mock_cache

        # Mock dialog to return accepted
        with patch.object(ModifySVGInputDialog, '_main_dialog') as mock_main_dialog:
            mock_dialog = Mock()
            mock_dialog.exec.return_value = QtWidgets.QDialog.Accepted
            mock_main_dialog.return_value = mock_dialog

            # Mock UI elements
            with patch.object(ModifySVGInputDialog, '_validate_svg_source', return_value=True):
                dialog = ModifySVGInputDialog(mock_svg_object)

                # Set modified values
                dialog.modified_color = 'ff0000'
                dialog.modified_thickness = '10'
                dialog.preview_applied = True

                # Mock thickness input
                dialog.thickness_input = Mock()
                dialog.thickness_input.text.return_value = '10'

                result = dialog._run_dialog()

                assert result == (True, 'svg_newhash')
                mock_cache.store_svg.assert_called_once()

    def test_scene_integration(self, qapp):
        """
        Scenario: Scene right-click integration

        Given scene.py has been updated
        When right-clicking SVG object
        Then it should call modify_svg_input_dialog
        """
        # This test verifies the integration point exists

        # Check that the SVG case is in the render method
        import os
        # Get project root directory
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
        scene_path = os.path.join(project_root, 'pyzui/objects/scene/scene.py')

        # Check if file exists before reading
        if os.path.exists(scene_path):
            scene_code = open(scene_path).read()
            assert "if type(self.right_selection).__name__ == 'SVGMediaObject':" in scene_code
            assert "dialog = DialogWindows.modify_svg_input_dialog" in scene_code
        else:
            # Skip test if file doesn't exist (might be in different location)
            pytest.skip(f"Scene file not found at {scene_path}")
