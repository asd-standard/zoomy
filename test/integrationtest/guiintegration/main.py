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
GUI Integration Tests for PyZUI
================================

This module contains end-to-end GUI integration tests that launch the full PyZUI
application and perform all possible user interactions as described in the
userinterface.rst documentation.

These tests are designed for human verification - each action is logged at DEBUG
level and executed with appropriate time delays so a human observer can verify
the behavior visually.

NOTE: Run directly with python from the project root directory.

Usage:
    # Run all tests
    python test/integrationtest/guiintegration/main.py

    # Run starting from a specific step number
    python test/integrationtest/guiintegration/main.py --start-step 5

    # List all available steps
    python test/integrationtest/guiintegration/main.py --list-steps

Actions tested (from userinterface.rst):
- File menu: New Tab, Close Tab, New Scene, Open Scene, Import Scene,
             Open Home Scene, Save Scene, Save Screenshot,
             Open Local Media, Open new String, Open new SVG,
             Open Media Directory, Quit
- View menu: Set Framerate, Adjust Sensitivity, Fullscreen,
             Render Order Toggle
- Settings menu: Autosave Settings, Zoom Settings
- Actions menu: Copy SVG, Paste SVG
- Help menu: About, About Qt
- Mouse: Left-click (select), Click'n'drag, Scrollwheel (zoom),
          Control+click rectangle selection, Shift+click preserve selection,
          Multi-selection persistence, Right-click (String/Image/SVG dialogs),
          Ctrl+Wheel arrow elongation, Modifier+Wheel shape elongation
- Keyboard: Esc (deselect), PgUp/PgDn (zoom), Arrow keys (move),
            Space bar (centre), Del (delete), Alt fine zoom,
            Ctrl+C/V copy-paste, Shift/Alt/Control modifiers
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

# Determine project root and ensure we're running from there
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.resolve()
# Directory containing the guiintegration package (test/integrationtest/)
GUIINTEGRATION_PARENT = Path(__file__).parent.parent.resolve()

# Add project root and guiintegration parent to path
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(GUIINTEGRATION_PARENT))

# Change to project root so relative paths (like 'data/home.pzs') work correctly
os.chdir(PROJECT_ROOT)

from guiintegration.conf import SHORT_DELAY_MS  # noqa: E402
from guiintegration.logger import GUITestLogger  # noqa: E402

# Import all test step modules
from guiintegration.test import (  # noqa: E402
    about,
    about_qt,
    adjust_sensitivity,
    alt_fine_zoom,
    autosave_settings,
    close_tab,
    control_click_rectangle,
    copy_svg,
    fullscreen,
    import_scene,
    keyboard_arrows,
    keyboard_copy_paste,
    keyboard_delete,
    keyboard_escape,
    keyboard_page_zoom,
    keyboard_space,
    load_test_scene,
    mouse_click_select,
    mouse_drag,
    mouse_wheel_zoom,
    multi_selection_persistence,
    new_scene,
    new_string_dialog,
    new_tab,
    open_home_scene,
    open_local_media,
    open_scene,
    open_svg,
    paste_svg,
    reload_test_scene,
    render_order,
    right_click_image,
    right_click_string,
    right_click_svg,
    save_scene,
    save_screenshot,
    sensitivity_dialog,
    set_framerate,
    shift_click_selection,
    svg_elongation,
    workflow,
    zoom_settings,
)
from guiintegration.test import (  # noqa: E402
    quit as quit_test,
)
from guiintegration.utilities.image_creation import create_png_image, create_ppm_image  # noqa: E402
from guiintegration.utilities.qt_simulation import trigger_action  # noqa: E402
from guiintegration.utilities.temp_dirs import get_pytest_style_temp_dir  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

import pyzui.tilesystem.tilemanager as TileManager  # noqa: E402
from pyzui.logger import LoggerConfig  # noqa: E402
from pyzui.windows.mainwindow import MainWindow  # noqa: E402


@dataclass
class GUITestContext:
    """Holds shared state for test steps."""

    app: QApplication | None = None
    window: MainWindow | None = None
    log: GUITestLogger = field(default_factory=GUITestLogger)
    resources: dict = field(default_factory=dict)
    temp_dir: Path | None = None
    scene_loaded: bool = False
    project_root: Path = PROJECT_ROOT


class GUIIntegrationTest:
    """
    GUI Integration Test Runner

    This class manages the PyZUI application and performs all GUI tests.
    Run directly with python (not pytest).
    """

    def __init__(self):
        self.app: QApplication | None = None
        self.window: MainWindow | None = None
        self.resources: dict = {}
        self.temp_dir: Path | None = None
        self.ctx: GUITestContext | None = None

        # Define all test steps in execution order
        self.steps: list[tuple[int, str, Callable]] = [
            (1, "Setup - Load Test Scene (Media Dir + String)", load_test_scene.run),
            (2, "File Menu - New Scene", new_scene.run),
            (3, "File Menu - Open Home Scene", open_home_scene.run),
            (4, "File Menu - Reload Test Scene", reload_test_scene.run),
            (5, "File Menu - Save Screenshot", save_screenshot.run),
            (6, "File Menu - Save Scene", save_scene.run),
            (7, "File Menu - Open Saved Scene", open_scene.run),
            (8, "File Menu - Open New String Dialog", new_string_dialog.run),
            (9, "File Menu - Open Local Media", open_local_media.run),
            (10, "View Menu - Set Framerate", set_framerate.run),
            (11, "View Menu - Adjust Sensitivity", adjust_sensitivity.run),
            (12, "View Menu - Fullscreen Toggle", fullscreen.run),
            (13, "View Menu - Adjust Sensitivity Dialog", sensitivity_dialog.run),
            (14, "File Menu - Open new SVG", open_svg.run),
            (15, "File Menu - Import Scene", import_scene.run),
            (16, "File Menu - New Tab", new_tab.run),
            (17, "File Menu - Close Tab", close_tab.run),
            (18, "View Menu - Render Order Toggle", render_order.run),
            (19, "Settings Menu - Autosave Settings", autosave_settings.run),
            (20, "Help Menu - About", about.run),
            (21, "Help Menu - About Qt", about_qt.run),
            (22, "Settings Menu - Zoom Settings", zoom_settings.run),
            (25, "SVG - Full Elongation Test", svg_elongation.run),
            (23, "Actions Menu - Copy SVG", copy_svg.run),
            (24, "Actions Menu - Paste SVG", paste_svg.run),
            (37, "Keyboard - Ctrl+C/V Copy Paste", keyboard_copy_paste.run),
            (47, "Mouse Right-Click - SVG Modification Dialog", right_click_svg.run),
            (26, "SVG - Reload Test Scene", reload_test_scene.run),
            (30, "Mouse - Left Click Select", mouse_click_select.run),
            (31, "Mouse - Click and Drag", mouse_drag.run),
            (32, "Mouse - Scroll Wheel Zoom", mouse_wheel_zoom.run),
            (33, "Mouse - Multi-Selection Persistence", multi_selection_persistence.run),
            (34, "Keyboard - Alt Fine Zoom Control", alt_fine_zoom.run),
            (35, "Mouse - Control+Click Rectangle Drawing and Move", control_click_rectangle.run),
            (36, "Mouse - Shift+Click No Selection Change", shift_click_selection.run),
            (40, "Keyboard - Escape Deselect", keyboard_escape.run),
            (41, "Keyboard - Page Up/Down Zoom", keyboard_page_zoom.run),
            (42, "Keyboard - Arrow Keys Move", keyboard_arrows.run),
            (43, "Keyboard - Space Center", keyboard_space.run),
            (44, "Keyboard - Delete Media", keyboard_delete.run),
            (45, "Mouse Right-Click - String Modification Dialog", right_click_string.run),
            (46, "Mouse Right-Click - Image Modification Dialog", right_click_image.run),
            (90, "Complete Workflow", workflow.run),
            (99, "File Menu - Quit", quit_test.run),
        ]

    def list_steps(self) -> None:
        """Print all available test steps."""
        print("\nAvailable test steps:")
        print("-" * 50)
        for step_num, description, _ in self.steps:
            print(f"  {step_num:3d}: {description}")
        print("-" * 50)
        print()

    def setup(self, debug: bool = False, verbose: bool = False) -> None:
        """Initialize Qt application, create test resources, and show main window."""
        # Initialize logging
        LoggerConfig._initialized = False
        LoggerConfig.initialize(
            debug=debug, log_to_file=True, log_to_console=True, log_dir="logs", colored_output=True, verbose=verbose
        )

        log = GUITestLogger("GUIIntegrationTest")
        log.section("INITIALIZING GUI INTEGRATION TEST")

        # Create Qt application
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)

        # Create test resources (pytest-style directory)
        self.create_test_resources()

        # Initialize TileManager
        TileManager.init(auto_cleanup=False)

        # Create and show main window
        self.window = MainWindow()
        self.window.show()
        self.app.processEvents()
        wait_raw(1000, "Window initializing")

        # Start with a new scene (not home scene)
        # Temporarily create a context for trigger_action
        ctx = GUITestContext(
            app=self.app,
            window=self.window,
            log=log,
            resources=self.resources,
            temp_dir=self.temp_dir,
        )
        trigger_action(ctx, "new_scene")
        wait_raw(SHORT_DELAY_MS, "Starting with blank scene")

        # Create the permanent context
        self.ctx = GUITestContext(
            app=self.app,
            window=self.window,
            log=log,
            resources=self.resources,
            temp_dir=self.temp_dir,
        )

        log.success("GUI test environment initialized")

    def create_test_resources(self) -> None:
        """Create all test images and directories in pytest-style structure."""
        self.temp_dir = get_pytest_style_temp_dir()

        # Media directory with multiple images
        media_dir = self.temp_dir / "media_directory"
        media_dir.mkdir(exist_ok=True)
        self.resources["media_dir"] = str(media_dir)

        # Create distinctive test images
        test_images = [
            ("01_red_stripes", (255, 64, 64), "stripes"),
            ("02_green_gradient", (64, 200, 64), "gradient"),
            ("03_blue_checkerboard", (64, 64, 255), "checkerboard"),
            ("04_yellow_solid", (255, 220, 64), "solid"),
            ("05_purple_diagonal", (180, 64, 255), "diagonal"),
            ("06_cyan_circles", (64, 220, 220), "circles"),
        ]

        for name, color, pattern in test_images:
            img_path = media_dir / f"{name}.png"
            if not create_png_image(str(img_path), 256, 256, color=color, pattern=pattern):
                img_path = media_dir / f"{name}.ppm"
                create_ppm_image(str(img_path), 256, 256, color=color, pattern=pattern)

        # Save directory for screenshots and scenes
        save_dir = self.temp_dir / "save_output"
        save_dir.mkdir(exist_ok=True)
        self.resources["save_dir"] = str(save_dir)

        # Create temp SVG file for Open Local Media / Open SVG tests
        svg_content = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">\n'
            '  <rect x="10" y="10" width="80" height="80" fill="red" stroke="black" stroke-width="2"/>\n'
            "</svg>"
        )
        temp_svg_path = self.temp_dir / "test_rect.svg"
        temp_svg_path.write_text(svg_content)
        self.resources["temp_svg"] = str(temp_svg_path)

        print("\n" + "=" * 60)
        print("[Test Resources Created]")
        print("=" * 60)
        print(f"  Temp directory:   {self.temp_dir}")
        print(f"  Media directory:  {self.resources['media_dir']}")
        print(f"  Save directory:   {self.resources['save_dir']}")
        print(f"  Images created:   {len(test_images)}")
        print(f"  Temp SVG:         {self.resources['temp_svg']}")
        print("=" * 60 + "\n")

    def teardown(self) -> None:
        """Clean up resources."""
        if self.window:
            self.window.close()
            self.app.processEvents()

        print(f"\n[Test files preserved at: {self.temp_dir}]")

        self.ctx.log.section("GUI INTEGRATION TEST COMPLETED")

    def run(
        self,
        start_step: int = 1,
        only_module: str | None = None,
        only_step: int | None = None,
        debug: bool = False,
        verbose: bool = False,
    ) -> None:
        """Run tests starting from the specified step.

        Args:
            start_step: Skip steps with number below this.
            only_module: Run only the test whose module name matches (e.g. 'new_tab').
            only_step: Run only the test with this step number.
            debug: Enable debug logging (DEBUG on console + file).
            verbose: Enable verbose logging (INFO on console, DEBUG on file).
        """
        try:
            self.setup(debug=debug, verbose=verbose)

            for step_num, description, step_func in self.steps:
                if only_step is not None and step_num != only_step:
                    print(f"Skipping step {step_num}: {description}")
                    continue
                if only_module is not None:
                    module_name = step_func.__module__.split(".")[-1]
                    if module_name != only_module:
                        print(f"Skipping step {step_num}: {description}")
                        continue
                if step_num < start_step:
                    print(f"Skipping step {step_num}: {description}")
                    continue

                print(f"\n>>> Running step {step_num}: {description}")
                try:
                    step_func(self.ctx)
                except Exception as e:
                    self.ctx.log.warning(f"Step {step_num} failed: {e}")
                    import traceback

                    traceback.print_exc()

        except KeyboardInterrupt:
            print("\n\nTest interrupted by user (Ctrl+C)")
        finally:
            self.teardown()


# =============================================================================
# Raw wait helper (used before context is fully set up)
# =============================================================================


def wait_raw(ms: int, _description: str = "") -> None:
    """Wait for specified milliseconds, processing Qt events. No context needed."""
    from PySide6.QtTest import QTest

    QTest.qWait(ms)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="PyZUI GUI Integration Tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python guiintegration/main.py                   # Run all tests (quiet)
  python guiintegration/main.py -v                # Run with verbose logging
  python guiintegration/main.py -d                # Run with debug logging
  python guiintegration/main.py --start-step 5    # Start from step 5
  python guiintegration/main.py --only new_tab    # Run only the new_tab test
  python guiintegration/main.py --only-step 16    # Run only step 16
  python guiintegration/main.py --list-steps      # List all steps

Note: Run directly with python from the project root directory.
        """,
    )
    parser.add_argument(
        "--start-step", "-s", type=int, default=1, help="Start from this step number (default: 1)"
    )
    parser.add_argument(
        "--list-steps", "-l", action="store_true", help="List all available test steps and exit"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--only", type=str, metavar="MODULE", help="Run only the specified test module (e.g., 'new_tab')"
    )
    group.add_argument(
        "--only-step", type=int, metavar="N", help="Run only the specified step number (e.g., 16)"
    )
    log_group = parser.add_mutually_exclusive_group()
    log_group.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose: print INFO+ on console, DEBUG+ to log file"
    )
    log_group.add_argument(
        "-d", "--debug", action="store_true", help="Debug: print DEBUG+ on console and log file"
    )

    args = parser.parse_args()

    test = GUIIntegrationTest()

    if args.list_steps:
        test.list_steps()
        return

    test.run(
        start_step=args.start_step,
        only_module=args.only,
        only_step=args.only_step,
        debug=args.debug,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
