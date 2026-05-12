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

"""Unit tests for SVGPickerInputDialog - simplified version."""

import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from pyzui.windows.dialogwindows.svgpickerinputdialog import OpenSVGPickerInputDialog


class TestOpenSVGPickerInputDialogSimple:
    """
    Feature: SVG Picker Input Dialog - Simplified Tests

    Simplified tests that avoid complex mocking of file system operations.
    """

    @pytest.fixture
    def dialog_without_init(self):
        """Create dialog instance without calling __init__."""
        dialog = OpenSVGPickerInputDialog.__new__(OpenSVGPickerInputDialog)
        # Initialize minimal attributes
        dialog.shape_color = ''
        dialog.selected_svg = ''
        dialog.color_codes = []
        dialog.custom_color_input = None
        dialog.thickness_input = None
        dialog._svg_buttons = {}
        dialog._svg_colors = {}
        dialog._svg_thicknesses = {}
        dialog._svg_contents = {}
        dialog._svg_renderers = {}
        dialog._modified_svg_files = {}
        dialog.SVG_FILES = []
        dialog.SVG_NAMES = {}
        dialog._svg_cache = Mock()
        return dialog

    def test_color_button_click(self, dialog_without_init):
        """
        Scenario: Click color button

        Given a color button is created
        When _color_button_click is called with a color code
        Then shape_color should be updated
        """
        dialog = dialog_without_init
        dialog._color_button_click("ff5733")

        assert dialog.shape_color == "ff5733"

    def test_svg_button_click(self, dialog_without_init):
        """
        Scenario: Click SVG button

        Given an SVG button is created
        When _svg_button_click is called with SVG path
        Then selected_svg should be updated
        """
        dialog = dialog_without_init
        dialog.selected_svg = ""
        dialog._svg_buttons = {"test.svg": Mock()}

        dialog._svg_button_click("test.svg")

        assert dialog.selected_svg == "test.svg"

    def test_modify_svg_file_success(self, dialog_without_init):
        """
        Scenario: Modify SVG file with color and thickness

        Given a valid SVG content
        When _modify_svg_file is called with color and thickness
        Then it should parse the XML and apply modifications
        And return a cache hash
        """
        dialog = dialog_without_init
        dialog._svg_cache = Mock()
        dialog._svg_cache.store_svg.return_value = "svg_test123"

        # Create a simple SVG file
        svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
    <circle cx="100" cy="100" r="70" stroke="black" stroke-width="8" fill="none"/>
</svg>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(svg_content)
            svg_file = f.name

        try:
            cache_hash = dialog._modify_svg_file(svg_file, "ff5733", "15")

            assert cache_hash == "svg_test123"
            dialog._svg_cache.store_svg.assert_called_once()

            # Verify stored content contains modifications
            stored_content = dialog._svg_cache.store_svg.call_args[0][0]
            assert 'ff5733' in stored_content.lower()
            assert 'stroke-width="15"' in stored_content
        finally:
            if os.path.exists(svg_file):
                os.unlink(svg_file)

    def test_modify_svg_file_no_modifications(self, dialog_without_init):
        """
        Scenario: Modify SVG file without color or thickness

        Given a valid SVG file
        When _modify_svg_file is called without modifications
        Then it should still store the SVG in cache
        And return a cache hash
        """
        dialog = dialog_without_init
        dialog._svg_cache = Mock()
        dialog._svg_cache.store_svg.return_value = "svg_test123"

        # Create a simple SVG file
        svg_content = '''<svg></svg>'''

        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(svg_content)
            svg_file = f.name

        try:
            cache_hash = dialog._modify_svg_file(svg_file, None, None)

            assert cache_hash == "svg_test123"
            dialog._svg_cache.store_svg.assert_called_once()
        finally:
            if os.path.exists(svg_file):
                os.unlink(svg_file)

    def test_apply_color_to_svg(self, dialog_without_init):
        """
        Scenario: Apply color to selected SVG

        Given an SVG is selected and a color is chosen
        When _apply_color_to_svg is called
        Then it should update the SVG's color
        """
        dialog = dialog_without_init
        dialog.selected_svg = "test.svg"
        dialog.shape_color = "ff0000"
        dialog._svg_colors = {}
        dialog._svg_renderers = {}
        dialog._svg_cache = Mock()
        dialog._svg_cache.store_svg.return_value = "svg_modified"

        # Mock _create_modified_svg_renderer
        with patch.object(dialog, '_create_modified_svg_renderer') as mock_create:
            mock_renderer = Mock()
            mock_create.return_value = mock_renderer

            dialog._apply_color_to_svg()

            assert dialog._svg_colors["test.svg"] == "ff0000"
            mock_create.assert_called_once_with("test.svg")

    def test_apply_thickness_to_svg_valid(self, dialog_without_init):
        """
        Scenario: Apply valid thickness to SVG

        Given an SVG is selected and valid thickness is entered
        When _apply_thickness_to_svg is called
        Then it should update the SVG's thickness
        """
        dialog = dialog_without_init
        dialog.selected_svg = "test.svg"
        dialog.thickness_input = Mock()
        dialog.thickness_input.text.return_value = "20"
        dialog._svg_thicknesses = {}
        dialog._svg_renderers = {}
        dialog._svg_cache = Mock()
        dialog._svg_cache.store_svg.return_value = "svg_modified"

        # Mock _create_modified_svg_renderer
        with patch.object(dialog, '_create_modified_svg_renderer') as mock_create:
            mock_renderer = Mock()
            mock_create.return_value = mock_renderer

            dialog._apply_thickness_to_svg()

            assert dialog._svg_thicknesses["test.svg"] == "20"
            mock_create.assert_called_once_with("test.svg")

    def test_apply_thickness_to_svg_invalid(self, dialog_without_init):
        """
        Scenario: Apply invalid thickness to SVG

        Given an SVG is selected and invalid thickness is entered
        When _apply_thickness_to_svg is called
        Then it should not update the SVG's thickness
        """
        dialog = dialog_without_init
        dialog.selected_svg = "test.svg"
        dialog.thickness_input = Mock()
        dialog.thickness_input.text.return_value = "invalid"
        dialog._svg_thicknesses = {}

        dialog._apply_thickness_to_svg()

        # Should not raise exception
        assert "test.svg" not in dialog._svg_thicknesses

    def test_apply_changes_to_svg(self, dialog_without_init):
        """
        Scenario: Apply both color and thickness changes

        Given an SVG is selected with color and thickness
        When _apply_changes_to_svg is called
        Then it should update both color and thickness
        """
        dialog = dialog_without_init
        dialog.selected_svg = "test.svg"
        dialog.shape_color = "00ff00"
        dialog.thickness_input = Mock()
        dialog.thickness_input.text.return_value = "25"
        dialog._svg_colors = {}
        dialog._svg_thicknesses = {}
        dialog._svg_renderers = {}
        dialog._svg_cache = Mock()
        dialog._svg_cache.store_svg.return_value = "svg_modified"

        # Mock _create_modified_svg_renderer
        with patch.object(dialog, '_create_modified_svg_renderer') as mock_create:
            mock_renderer = Mock()
            mock_create.return_value = mock_renderer

            dialog._apply_changes_to_svg()

            assert dialog._svg_colors["test.svg"] == "00ff00"
            assert dialog._svg_thicknesses["test.svg"] == "25"
            mock_create.assert_called_once_with("test.svg")

    def test_create_modified_svg_renderer_with_modifications(self, dialog_without_init):
        """
        Scenario: Create modified SVG renderer with modifications

        Given an SVG with color and thickness modifications
        When _create_modified_svg_renderer is called
        Then it should create a renderer with modifications applied
        """
        dialog = dialog_without_init
        dialog._svg_cache = Mock()
        dialog._svg_cache.store_svg.return_value = "svg_modified123"
        dialog._svg_cache.get_cache_path.return_value = Mock(exists=lambda: True)

        dialog._svg_colors = {"test.svg": "ff0000"}
        dialog._svg_thicknesses = {"test.svg": "15"}

        # Mock _modify_svg_file
        with patch.object(dialog, '_modify_svg_file') as mock_modify:
            mock_modify.return_value = "svg_modified123"

            dialog._create_modified_svg_renderer("test.svg")

            mock_modify.assert_called_once_with("test.svg", "ff0000", "15")
            assert "test.svg" in dialog._svg_renderers
            assert "test.svg" in dialog._modified_svg_files

    def test_create_modified_svg_renderer_no_modifications(self, dialog_without_init):
        """
        Scenario: Create SVG renderer without modifications

        Given an SVG without modifications
        When _create_modified_svg_renderer is called
        Then it should create a renderer from cache
        """
        dialog = dialog_without_init
        dialog._svg_renderers = {}

        # Mock QtSvg.QSvgRenderer
        with patch('pyzui.windows.dialogwindows.svgpickerinputdialog.QtSvg.QSvgRenderer') as mock_renderer_class:
            mock_renderer = Mock()
            mock_renderer_class.return_value = mock_renderer

            renderer = dialog._create_modified_svg_renderer("test.svg")

            assert renderer == mock_renderer
            assert "test.svg" in dialog._svg_renderers
            mock_renderer_class.assert_called_once()

    def test_color_history_loading(self, tmp_path):
        """
        Scenario: Load color history from file

        Given a color history file exists
        When OpenSVGPickerInputDialog loads colors
        Then it should load color codes from the file
        """
        color_dir = tmp_path / ".pyzui" / "colorstore"
        color_dir.mkdir(parents=True, exist_ok=True)
        color_file = color_dir / "color_list.txt"

        with open(color_file, 'w') as f:
            f.write("ff0000\n00ff00\n0000ff\n")

        # Mock the environment to use our temp directory
        with patch('pyzui.windows.dialogwindows.svgpickerinputdialog.os.path.isfile', return_value=True), \
             patch('pyzui.windows.dialogwindows.svgpickerinputdialog.os.path.isdir', return_value=True), \
             patch('pyzui.windows.dialogwindows.svgpickerinputdialog.os.environ', {}), \
             patch('pyzui.windows.dialogwindows.svgpickerinputdialog.os.path.expanduser', return_value=str(tmp_path)):

            # Mock the SVG directory scan to avoid file system issues
            with patch('pyzui.windows.dialogwindows.svgpickerinputdialog.os.path.isdir', return_value=False):
                dialog = OpenSVGPickerInputDialog()

                assert len(dialog.color_codes) == 3
                assert 'ff0000' in dialog.color_codes
                assert '00ff00' in dialog.color_codes
                assert '0000ff' in dialog.color_codes

    def test_color_history_creation(self, tmp_path):
        """
        Scenario: Create default color history when file doesn't exist

        Given no color history file exists
        When OpenSVGPickerInputDialog is initialized
        Then it should create default colors
        """
        tmp_path / ".pyzui" / "colorstore"

        with patch('pyzui.windows.dialogwindows.svgpickerinputdialog.os.path.isfile', return_value=False), \
             patch('pyzui.windows.dialogwindows.svgpickerinputdialog.os.path.isdir', return_value=True), \
             patch('pyzui.windows.dialogwindows.svgpickerinputdialog.os.environ', {}), \
             patch('pyzui.windows.dialogwindows.svgpickerinputdialog.os.path.expanduser', return_value=str(tmp_path)):

            # Mock the SVG directory scan to avoid file system issues
            with patch('pyzui.windows.dialogwindows.svgpickerinputdialog.os.path.isdir', return_value=False), \
                 patch('pyzui.windows.dialogwindows.svgpickerinputdialog.os.mkdir') as mock_mkdir, \
                 patch('pyzui.windows.dialogwindows.svgpickerinputdialog.open') as mock_open:

                dialog = OpenSVGPickerInputDialog()

                assert len(dialog.color_codes) == 4
                assert 'ffffff' in dialog.color_codes
                assert 'ff0000' in dialog.color_codes
                assert '00ff00' in dialog.color_codes
                assert '0000ff' in dialog.color_codes

                # Verify mkdir was called for color directory (not SVG cache)
                # The mock will capture all mkdir calls, we just check it was called
                assert mock_mkdir.call_count >= 1
                # Verify open was called to write color file
                mock_open.assert_called_once()

    def test_init_without_svg_directory(self):
        """
        Scenario: Initialize dialog without SVG directory

        Given no SVG directory exists
        When OpenSVGPickerInputDialog is initialized
        Then it should handle missing directory gracefully
        """
        with patch('pyzui.windows.dialogwindows.svgpickerinputdialog.os.path.isdir', return_value=False):
            dialog = OpenSVGPickerInputDialog()

            assert len(dialog.SVG_FILES) == 0
            assert len(dialog.SVG_NAMES) == 0
