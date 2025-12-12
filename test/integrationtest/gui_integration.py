#!/usr/bin/env python3
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
GUI Integration Tests for PyZUI
================================

This module contains end-to-end GUI integration tests that launch the full PyZUI
application and perform all possible user interactions as described in the
userinterface.rst documentation.

These tests are designed for human verification - each action is logged at DEBUG
level and executed with appropriate time delays so a human observer can verify
the behavior visually.

NOTE: This file is named gui_integration.py (not test_*.py) so pytest won't
automatically pick it up. Run it directly with python.

Usage:
    # Run all tests
    python test/integrationtest/gui_integration.py

    # Run starting from a specific step number
    python test/integrationtest/gui_integration.py --start-step 5

    # List all available steps
    python test/integrationtest/gui_integration.py --list-steps

The test will launch the PyZUI application and perform all GUI actions in sequence.
If something doesn't work, you can stop the test (Ctrl+C) and check the logs to see
where the program was at.

Actions tested (from userinterface.rst):
- File menu: New Scene, Open Scene, Open Home Scene, Save Scene, Save Screenshot,
             Open Local Media, Open new String, Open Media Directory, Quit
- View menu: Set Framerate, Adjust Sensitivity, Fullscreen
- Help menu: About, About Qt
- Mouse: Left-click (select), Click'n'drag, Scrollwheel (zoom)
- Keyboard: Esc (deselect), PgUp/PgDn (zoom), Arrow keys (move),
            Space bar (centre), Del (delete), Shift/Alt modifiers
"""

import sys
import os
import argparse
import getpass
from pathlib import Path
from typing import Optional, List
from unittest.mock import patch

# Determine project root and ensure we're running from there
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()

# Add project root to path
sys.path.insert(0, str(PROJECT_ROOT))

# Change to project root so relative paths (like 'data/home.pzs') work correctly
os.chdir(PROJECT_ROOT)

from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt, QPoint
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFileDialog

from pyzui.logger import LoggerConfig, get_logger
from pyzui.windows.mainwindow import MainWindow
import pyzui.tilesystem.tilemanager as TileManager

# =============================================================================
# TIMING CONFIGURATION - Adjust these for slower/faster testing
# =============================================================================
SHORT_DELAY_MS = 2000       # Short pauses (2 seconds)
DEFAULT_DELAY_MS = 3500     # Standard delay between actions (3.5 seconds)
LONG_DELAY_MS = 5000        # Long delay for loading/rendering (5 seconds)
IMAGE_LOAD_DELAY_MS = 10000 # Extra time for images to fully load/tile (10 seconds)
ZOOM_STEP_DELAY_MS = 800    # Delay between zoom steps (0.8 seconds)
MOVE_STEP_DELAY_MS = 500    # Delay between movement steps (0.5 seconds)

# =============================================================================
# IMAGE CREATION UTILITIES
# =============================================================================

def create_ppm_image(filepath: str, width: int, height: int,
                     color: tuple = (128, 128, 128), pattern: str = "solid") -> None:
    """Create a PPM image file (no external dependencies required)."""
    pixels = []

    for y in range(height):
        row = []
        for x in range(width):
            if pattern == "solid":
                r, g, b = color
            elif pattern == "gradient":
                factor = x / width
                r = int(color[0] + (255 - color[0]) * factor)
                g = int(color[1] + (255 - color[1]) * factor)
                b = int(color[2] + (255 - color[2]) * factor)
            elif pattern == "checkerboard":
                cell_size = 32
                if ((x // cell_size) + (y // cell_size)) % 2 == 0:
                    r, g, b = color
                else:
                    r, g, b = 255, 255, 255
            elif pattern == "stripes":
                stripe_width = 20
                if (y // stripe_width) % 2 == 0:
                    r, g, b = color
                else:
                    r, g, b = 255, 255, 255
            elif pattern == "diagonal":
                factor = (x + y) / (width + height)
                r = int(color[0] * (1 - factor) + 100 * factor)
                g = int(color[1] * (1 - factor) + 100 * factor)
                b = int(color[2] * (1 - factor) + 200 * factor)
            else:
                r, g, b = color

            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            row.extend([r, g, b])
        pixels.append(bytes(row))

    with open(filepath, 'wb') as f:
        header = f"P6\n{width} {height}\n255\n"
        f.write(header.encode('ascii'))
        for row in pixels:
            f.write(row)

def create_png_image(filepath: str, width: int, height: int,
                     color: tuple = (128, 128, 128), pattern: str = "solid") -> bool:
    """Create a PNG image using PIL if available."""
    try:
        from PIL import Image, ImageDraw

        img = Image.new('RGB', (width, height), color=color)
        draw = ImageDraw.Draw(img)

        if pattern == "gradient":
            for x in range(width):
                factor = x / width
                r = int(color[0] + (255 - color[0]) * factor)
                g = int(color[1] + (255 - color[1]) * factor)
                b = int(color[2] + (255 - color[2]) * factor)
                draw.line([(x, 0), (x, height)], fill=(r, g, b))

        elif pattern == "checkerboard":
            cell_size = 32
            for cy in range(0, height, cell_size):
                for cx in range(0, width, cell_size):
                    if ((cx // cell_size) + (cy // cell_size)) % 2 == 1:
                        draw.rectangle([cx, cy, cx + cell_size, cy + cell_size],
                                       fill=(255, 255, 255))

        elif pattern == "stripes":
            stripe_width = 20
            for sy in range(0, height, stripe_width * 2):
                draw.rectangle([0, sy + stripe_width, width, sy + stripe_width * 2],
                               fill=(255, 255, 255))

        elif pattern == "diagonal":
            for i in range(-height, width, 10):
                factor = (i + height) / (width + height)
                line_color = (
                    int(color[0] * (1 - factor) + 100 * factor),
                    int(color[1] * (1 - factor) + 100 * factor),
                    int(color[2] * (1 - factor) + 200 * factor)
                )
                draw.line([(i, 0), (i + height, height)], fill=line_color, width=5)

        elif pattern == "circles":
            center_x, center_y = width // 2, height // 2
            max_radius = min(width, height) // 2
            for rad in range(max_radius, 0, -20):
                factor = rad / max_radius
                circle_color = (
                    int(color[0] * factor),
                    int(color[1] * factor),
                    int(color[2] * factor)
                )
                draw.ellipse([center_x - rad, center_y - rad,
                              center_x + rad, center_y + rad],
                             fill=circle_color)

        img.save(filepath)
        return True

    except ImportError:
        return False

def get_pytest_style_temp_dir() -> Path:
    """
    Create a temp directory structure similar to pytest:
    /tmp/pytest-of-{username}/pytest-{n}/pyzui_gui_test0/
    """
    username = getpass.getuser()
    base_dir = Path(f"/tmp/pytest-of-{username}")
    base_dir.mkdir(exist_ok=True)

    # Find next pytest-N number
    existing = list(base_dir.glob("pytest-*"))
    if existing:
        nums = []
        for p in existing:
            try:
                nums.append(int(p.name.split("-")[1]))
            except (IndexError, ValueError):
                pass
        next_num = max(nums) + 1 if nums else 0
    else:
        next_num = 0

    pytest_dir = base_dir / f"pytest-{next_num}"
    pytest_dir.mkdir(exist_ok=True)

    test_dir = pytest_dir / "pyzui_gui_test0"
    test_dir.mkdir(exist_ok=True)

    return test_dir

# =============================================================================
# TEST LOGGER
# =============================================================================

class GUITestLogger:
    """Helper class for logging GUI test actions with visual markers."""

    def __init__(self, name: str = "GUITest"):
        self.logger = get_logger(name)
        self.step_count = 0

    def action(self, description: str) -> None:
        self.step_count += 1
        self.logger.info("=" * 60)
        self.logger.info(f"STEP {self.step_count}: {description}")
        self.logger.info("=" * 60)

    def detail(self, message: str) -> None:
        self.logger.debug(f"  -> {message}")

    def wait(self, description: str) -> None:
        self.logger.debug(f"  [WAIT] {description}")

    def success(self, message: str) -> None:
        self.logger.info(f"  [OK] {message}")

    def warning(self, message: str) -> None:
        self.logger.warning(f"  [WARN] {message}")

    def section(self, title: str) -> None:
        self.logger.info("")
        self.logger.info("#" * 70)
        self.logger.info(f"# {title}")
        self.logger.info("#" * 70)
        self.logger.info("")

# =============================================================================
# MAIN GUI TEST CLASS
# =============================================================================

class GUIIntegrationTest:
    """
    GUI Integration Test Runner

    This class manages the PyZUI application and performs all GUI tests.
    Run directly with python (not pytest).
    """

    def __init__(self):
        self.app: Optional[QApplication] = None
        self.window: Optional[MainWindow] = None
        self.log = GUITestLogger("GUIIntegrationTest")
        self.resources = {}
        self.temp_dir: Optional[Path] = None
        self.scene_loaded = False  # Track if main test scene is loaded

        # Define all test steps
        self.steps: List[tuple] = [
            (1, "Setup - Load Test Scene (Media Dir + String)", self.step_load_test_scene),
            (2, "File Menu - New Scene", self.step_new_scene),
            (3, "File Menu - Open Home Scene", self.step_open_home_scene),
            (4, "File Menu - Reload Test Scene", self.step_reload_test_scene),
            (5, "File Menu - Save Screenshot", self.step_save_screenshot),
            (6, "File Menu - Save Scene", self.step_save_scene),
            (7, "File Menu - Open Saved Scene", self.step_open_scene),
            (10, "View Menu - Set Framerate", self.step_set_framerate),
            (11, "View Menu - Adjust Sensitivity", self.step_adjust_sensitivity),
            (12, "View Menu - Fullscreen Toggle", self.step_fullscreen),
            (20, "Help Menu - About", self.step_about),
            (21, "Help Menu - About Qt", self.step_about_qt),
            (30, "Mouse - Left Click Select", self.step_mouse_click_select),
            (31, "Mouse - Click and Drag", self.step_mouse_drag),
            (32, "Mouse - Scroll Wheel Zoom", self.step_mouse_wheel_zoom),
            (40, "Keyboard - Escape Deselect", self.step_keyboard_escape),
            (41, "Keyboard - Page Up/Down Zoom", self.step_keyboard_page_zoom),
            (42, "Keyboard - Arrow Keys Move", self.step_keyboard_arrows),
            (43, "Keyboard - Space Center", self.step_keyboard_space),
            (44, "Keyboard - Delete Media", self.step_keyboard_delete),
            (90, "Complete Workflow", self.step_complete_workflow),
            (99, "File Menu - Quit", self.step_quit),
        ]

    def list_steps(self) -> None:
        """Print all available test steps."""
        print("\nAvailable test steps:")
        print("-" * 50)
        for step_num, description, _ in self.steps:
            print(f"  {step_num:3d}: {description}")
        print("-" * 50)
        print()

    def wait(self, ms: int = DEFAULT_DELAY_MS, description: str = "") -> None:
        """Wait for specified milliseconds, processing Qt events."""
        if description:
            self.log.wait(f"Waiting {ms}ms - {description}")
        QTest.qWait(ms)

    def wait_for_image_load(self, description: str = "") -> None:
        """Wait for images to load and tile, with progress checking."""
        self.log.detail(f"Waiting for image to load: {description}")

        total_wait = IMAGE_LOAD_DELAY_MS
        chunk = 500
        elapsed = 0

        while elapsed < total_wait:
            QTest.qWait(chunk)
            self.app.processEvents()
            elapsed += chunk

            if elapsed % 2000 == 0:
                self.log.detail(f"  ... still loading ({elapsed}ms / {total_wait}ms)")

        self.log.detail("Image load wait complete")

    def trigger_action(self, action_key: str) -> bool:
        """Trigger a menu action by its internal key."""
        try:
            action = self.window._MainWindow__action.get(action_key)
            if action:
                self.log.detail(f"Triggering action: {action_key}")
                action.trigger()
                self.app.processEvents()
                return True
            else:
                self.log.warning(f"Action not found: {action_key}")
                return False
        except Exception as e:
            self.log.warning(f"Failed to trigger action {action_key}: {e}")
            return False

    def simulate_key(self, key: Qt.Key, modifiers: Qt.KeyboardModifier = Qt.NoModifier) -> None:
        """Simulate a key press."""
        self.log.detail(f"Simulating key press: {key}")
        QTest.keyClick(self.window.zui, key, modifiers)
        self.app.processEvents()

    def simulate_mouse_click(self, pos: QPoint, button: Qt.MouseButton = Qt.LeftButton) -> None:
        """Simulate a mouse click."""
        self.log.detail(f"Simulating mouse click at ({pos.x()}, {pos.y()})")
        QTest.mouseClick(self.window.zui, button, Qt.NoModifier, pos)
        self.app.processEvents()

    def simulate_mouse_drag(self, start: QPoint, end: QPoint,
                            button: Qt.MouseButton = Qt.LeftButton) -> None:
        """Simulate a mouse drag operation."""
        self.log.detail(f"Simulating drag from ({start.x()}, {start.y()}) to ({end.x()}, {end.y()})")
        zui = self.window.zui

        QTest.mousePress(zui, button, Qt.NoModifier, start)
        QTest.qWait(100)

        steps = 20
        for i in range(1, steps + 1):
            x = start.x() + (end.x() - start.x()) * i // steps
            y = start.y() + (end.y() - start.y()) * i // steps
            event = QtGui.QMouseEvent(
                QtCore.QEvent.MouseMove,
                QtCore.QPointF(x, y),
                button,
                button,
                Qt.NoModifier
            )
            QApplication.postEvent(zui, event)
            QTest.qWait(50)

        QTest.mouseRelease(zui, button, Qt.NoModifier, end)
        self.app.processEvents()

    def simulate_wheel(self, pos: QPoint, delta: int) -> None:
        """Simulate a mouse wheel scroll."""
        self.log.detail(f"Simulating wheel scroll: delta={delta}")
        event = QtGui.QWheelEvent(
            QtCore.QPointF(pos),
            QtCore.QPointF(pos),
            QPoint(0, delta),
            QPoint(0, delta),
            Qt.NoButton,
            Qt.NoModifier,
            Qt.ScrollUpdate,
            False
        )
        QApplication.postEvent(self.window.zui, event)
        QTest.qWait(100)
        self.app.processEvents()

    def load_media_directory_with_action(self) -> None:
        """Load all images from media_directory using the open_media_dir action."""
        self.log.detail(f"Loading media directory via action: {self.resources['media_dir']}")

        # Patch QFileDialog.getExistingDirectory to return our media directory
        with patch.object(QFileDialog, 'getExistingDirectory',
                          return_value=self.resources['media_dir']):
            self.trigger_action('open_media_dir')

    def add_test_string(self) -> None:
        """Add a test string below the images."""
        self.log.detail("Adding test string to scene")
        try:
            from pyzui.objects.mediaobjects.stringmediaobject import StringMediaObject
            test_string = "string:00ff00:GUI Integration Test - All Images Loaded"
            mediaobject = StringMediaObject(test_string, self.window.zui.scene)

            # Position the string at the bottom of the view
            w, h = self.window.zui.width(), self.window.zui.height()
            mediaobject.fit((w * 0.1, h * 0.75, w * 0.9, h * 0.95))

            self.window.zui.scene.add(mediaobject)
            self.app.processEvents()
            self.log.success("Test string added")
        except Exception as e:
            self.log.warning(f"Error adding string: {e}")

    def ensure_test_scene_loaded(self) -> None:
        """Ensure the test scene with images and string is loaded."""
        if not self.scene_loaded:
            self.step_load_test_scene()

    # =========================================================================
    # SETUP AND TEARDOWN
    # =========================================================================

    def setup(self) -> None:
        """Initialize Qt application, create test resources, and show main window."""
        # Initialize logging
        LoggerConfig._initialized = False
        LoggerConfig.initialize(
            debug=True,
            log_to_file=True,
            log_to_console=True,
            log_dir='logs',
            colored_output=True,
            verbose=True
        )

        self.log.section("INITIALIZING GUI INTEGRATION TEST")

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
        self.wait(1000, "Window initializing")

        # Start with a new scene (not home scene)
        self.trigger_action('new_scene')
        self.wait(SHORT_DELAY_MS, "Starting with blank scene")

        self.log.success("GUI test environment initialized")

    def create_test_resources(self) -> None:
        """Create all test images and directories in pytest-style structure."""
        self.temp_dir = get_pytest_style_temp_dir()

        # Media directory with multiple images
        media_dir = self.temp_dir / "media_directory"
        media_dir.mkdir(exist_ok=True)
        self.resources['media_dir'] = str(media_dir)

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
        self.resources['save_dir'] = str(save_dir)

        print("\n" + "=" * 60)
        print("[Test Resources Created]")
        print("=" * 60)
        print(f"  Temp directory:   {self.temp_dir}")
        print(f"  Media directory:  {self.resources['media_dir']}")
        print(f"  Save directory:   {self.resources['save_dir']}")
        print(f"  Images created:   {len(test_images)}")
        print("=" * 60 + "\n")

    def teardown(self) -> None:
        """Clean up resources."""
        if self.window:
            self.window.close()
            self.app.processEvents()

        # Note: We don't delete temp_dir so user can inspect the files
        print(f"\n[Test files preserved at: {self.temp_dir}]")

        self.log.section("GUI INTEGRATION TEST COMPLETED")

    # =========================================================================
    # TEST STEPS
    # =========================================================================

    def step_load_test_scene(self) -> None:
        """Step 1: Load the main test scene with media directory + string."""
        self.log.section("SETUP - LOAD TEST SCENE")

        # Start fresh
        self.trigger_action('new_scene')
        self.wait(SHORT_DELAY_MS, "Starting with blank scene")

        # Load all images from media directory using the action
        self.log.action(f"Loading media directory: {self.resources['media_dir']}")
        self.load_media_directory_with_action()

        self.wait_for_image_load("All images from media directory loading")

        # Add test string below the images
        self.log.action("Adding test string below images")
        self.add_test_string()

        self.wait(LONG_DELAY_MS, "Observe: All images in grid + green test string below")

        self.scene_loaded = True
        self.log.success("Test scene loaded with all images and string")

    def step_new_scene(self) -> None:
        """Step 2: File > New Scene."""
        self.log.section("FILE MENU - NEW SCENE")
        self.log.action("Creating new blank scene (Ctrl+N)")
        self.wait(SHORT_DELAY_MS, "Observe current state")
        self.trigger_action('new_scene')
        self.wait(DEFAULT_DELAY_MS, "Observe: Scene should be blank (black)")
        self.scene_loaded = False
        self.log.success("New scene created")

    def step_open_home_scene(self) -> None:
        """Step 3: File > Open Home Scene."""
        self.log.section("FILE MENU - OPEN HOME SCENE")
        self.trigger_action('new_scene')
        self.wait(SHORT_DELAY_MS)
        self.log.action("Opening home scene (Ctrl+Home)")
        self.trigger_action('open_scene_home')
        self.wait_for_image_load("Home scene with PyZUI logo")
        self.wait(DEFAULT_DELAY_MS, "Observe: PyZUI logo should be visible")
        self.scene_loaded = False
        self.log.success("Home scene loaded")

    def step_reload_test_scene(self) -> None:
        """Step 4: Reload the test scene with images + string."""
        self.log.section("FILE MENU - RELOAD TEST SCENE")
        self.scene_loaded = False
        self.step_load_test_scene()

    def step_save_screenshot(self) -> None:
        """Step 5: File > Save Screenshot."""
        self.log.section("FILE MENU - SAVE SCREENSHOT")

        # Ensure test scene is loaded
        self.ensure_test_scene_loaded()

        screenshot_path = os.path.join(self.resources['save_dir'], 'test_screenshot.png')
        self.log.action(f"Saving screenshot to: {screenshot_path}")

        try:
            pixmap = self.window.zui.grab()
            pixmap.save(screenshot_path)
            if os.path.exists(screenshot_path):
                self.log.success(f"Screenshot saved: {os.path.getsize(screenshot_path)} bytes")
            else:
                self.log.warning("Screenshot not saved")
        except Exception as e:
            self.log.warning(f"Error saving screenshot: {e}")

        self.wait(DEFAULT_DELAY_MS)

    def step_save_scene(self) -> None:
        """Step 6: File > Save Scene."""
        self.log.section("FILE MENU - SAVE SCENE")

        # Ensure test scene is loaded
        self.ensure_test_scene_loaded()

        scene_path = os.path.join(self.resources['save_dir'], 'test_scene.pzs')
        self.log.action(f"Saving scene to: {scene_path}")

        try:
            self.window.zui.scene.save(scene_path)
            if os.path.exists(scene_path):
                self.log.success(f"Scene saved: {os.path.getsize(scene_path)} bytes")
                self.resources['test_scene'] = scene_path
            else:
                self.log.warning("Scene not saved")
        except Exception as e:
            self.log.warning(f"Error saving scene: {e}")

        self.wait(DEFAULT_DELAY_MS)

    def step_open_scene(self) -> None:
        """Step 7: File > Open Scene."""
        self.log.section("FILE MENU - OPEN SCENE")

        if 'test_scene' not in self.resources:
            self.log.warning("No saved scene available - run step 6 first")
            return

        self.trigger_action('new_scene')
        self.wait(SHORT_DELAY_MS)

        self.log.action(f"Opening scene: {self.resources['test_scene']}")

        try:
            from pyzui.objects.scene import scene as Scene
            self.window.zui.scene = Scene.load_scene(self.resources['test_scene'])
            self.app.processEvents()
        except Exception as e:
            self.log.warning(f"Error loading scene: {e}")

        self.wait_for_image_load("Scene loading")
        self.wait(DEFAULT_DELAY_MS, "Observe: Saved scene restored")
        self.log.success("Scene loaded")

    def step_set_framerate(self) -> None:
        """Step 10: View > Set Framerate."""
        self.log.section("VIEW MENU - SET FRAMERATE")

        self.ensure_test_scene_loaded()

        for fps in [10, 20, 30, 40]:
            self.log.action(f"Setting framerate to {fps} FPS")
            self.trigger_action(f'set_fps_{fps}')
            self.wait(SHORT_DELAY_MS, f"Framerate: {fps} FPS")
            self.log.success(f"Framerate: {fps} FPS")

        self.trigger_action('set_fps_10')

    def step_adjust_sensitivity(self) -> None:
        """Step 11: View > Adjust Sensitivity."""
        self.log.section("VIEW MENU - ADJUST SENSITIVITY")

        self.ensure_test_scene_loaded()

        self.log.action("Adjusting zoom sensitivity")
        self.window.zui.zoom_sensitivity = 20
        self.wait(DEFAULT_DELAY_MS, "Sensitivity adjusted")
        self.log.success("Sensitivity adjusted")

    def step_fullscreen(self) -> None:
        """Step 12: View > Fullscreen."""
        self.log.section("VIEW MENU - FULLSCREEN TOGGLE")

        self.ensure_test_scene_loaded()

        self.log.action("Entering fullscreen")
        self.trigger_action('fullscreen')
        self.wait(LONG_DELAY_MS, "Observe: FULLSCREEN mode with all images")
        self.log.success("Fullscreen entered")

        self.log.action("Exiting fullscreen")
        self.trigger_action('fullscreen')
        self.wait(DEFAULT_DELAY_MS, "Observe: Normal window")
        self.log.success("Fullscreen exited")

    def step_about(self) -> None:
        """Step 20: Help > About."""
        self.log.section("HELP MENU - ABOUT")
        self.log.action("Showing About dialog")
        self.wait(SHORT_DELAY_MS, "About dialog would show here")
        self.log.success("About dialog (skipped)")

    def step_about_qt(self) -> None:
        """Step 21: Help > About Qt."""
        self.log.section("HELP MENU - ABOUT QT")
        self.log.action("Showing About Qt dialog")
        self.wait(SHORT_DELAY_MS, "About Qt dialog would show here")
        self.log.success("About Qt dialog (skipped)")

    def step_mouse_click_select(self) -> None:
        """Step 30: Mouse left-click select on test scene."""
        self.log.section("MOUSE INTERACTIONS - LEFT CLICK SELECT")

        self.ensure_test_scene_loaded()

        zui = self.window.zui
        center = QPoint(zui.width() // 2, zui.height() // 2)
        corner = QPoint(50, 50)

        self.log.action("Left-click CENTER to select an image")
        self.simulate_mouse_click(center)
        self.wait(DEFAULT_DELAY_MS, "Observe: Image SELECTED (highlighted)")

        self.log.action("Left-click CORNER to deselect")
        self.simulate_mouse_click(corner)
        self.wait(DEFAULT_DELAY_MS, "Observe: Image DESELECTED")

        self.log.success("Click select test completed")

    def step_mouse_drag(self) -> None:
        """Step 31: Mouse click and drag on test scene."""
        self.log.section("MOUSE INTERACTIONS - CLICK AND DRAG")

        self.ensure_test_scene_loaded()

        zui = self.window.zui
        center = QPoint(zui.width() // 2, zui.height() // 2)
        drag_end = QPoint(center.x() + 150, center.y() + 100)

        self.log.action("Dragging scene content")
        self.simulate_mouse_drag(center, drag_end)
        self.wait(DEFAULT_DELAY_MS, "Observe: All images MOVED together")

        # Drag back
        self.log.action("Dragging back")
        self.simulate_mouse_drag(drag_end, center)
        self.wait(DEFAULT_DELAY_MS, "Observe: Content returned")

        self.log.success("Drag completed")

    def step_mouse_wheel_zoom(self) -> None:
        """Step 32: Mouse scroll wheel zoom on test scene."""
        self.log.section("MOUSE INTERACTIONS - SCROLL WHEEL ZOOM")

        self.ensure_test_scene_loaded()

        zui = self.window.zui
        center = QPoint(zui.width() // 2, zui.height() // 2)

        self.log.action("Scroll UP to ZOOM IN on images")
        for i in range(5):
            self.simulate_wheel(center, 120)
            self.wait(ZOOM_STEP_DELAY_MS)
        self.wait(DEFAULT_DELAY_MS, "Observe: Images ZOOMED IN - more detail visible")

        self.log.action("Scroll DOWN to ZOOM OUT")
        for i in range(10):
            self.simulate_wheel(center, -120)
            self.wait(ZOOM_STEP_DELAY_MS)
        self.wait(DEFAULT_DELAY_MS, "Observe: Images ZOOMED OUT - all visible")

        self.log.success("Wheel zoom completed")

    def step_keyboard_escape(self) -> None:
        """Step 40: Keyboard Escape deselect on test scene."""
        self.log.section("KEYBOARD - ESCAPE DESELECT")

        self.ensure_test_scene_loaded()

        zui = self.window.zui
        center = QPoint(zui.width() // 2, zui.height() // 2)

        self.log.action("Click to select an image")
        self.simulate_mouse_click(center)
        self.wait(DEFAULT_DELAY_MS, "Image SELECTED")

        self.log.action("Press ESCAPE to deselect")
        self.simulate_key(Qt.Key_Escape)
        self.wait(DEFAULT_DELAY_MS, "Observe: Image DESELECTED")
        self.log.success("Escape deselect completed")

    def step_keyboard_page_zoom(self) -> None:
        """Step 41: Keyboard Page Up/Down zoom on test scene."""
        self.log.section("KEYBOARD - PAGE UP/DOWN ZOOM")

        self.ensure_test_scene_loaded()

        self.log.action("Press PAGE UP to zoom in on images")
        for i in range(5):
            self.simulate_key(Qt.Key_PageUp)
            self.wait(ZOOM_STEP_DELAY_MS)
        self.wait(DEFAULT_DELAY_MS, "Observe: Images ZOOMED IN")

        self.log.action("Press PAGE DOWN to zoom out")
        for i in range(10):
            self.simulate_key(Qt.Key_PageDown)
            self.wait(ZOOM_STEP_DELAY_MS)
        self.wait(DEFAULT_DELAY_MS, "Observe: Images ZOOMED OUT")

        self.log.success("Page zoom completed")

    def step_keyboard_arrows(self) -> None:
        """Step 42: Keyboard arrow keys move on test scene."""
        self.log.section("KEYBOARD - ARROW KEYS MOVE")

        self.ensure_test_scene_loaded()

        self.log.action("Arrow keys to move all images")
        for key, name in [(Qt.Key_Up, "UP"), (Qt.Key_Down, "DOWN"),
                          (Qt.Key_Left, "LEFT"), (Qt.Key_Right, "RIGHT")]:
            self.log.detail(f"Moving {name}")
            for _ in range(5):
                self.simulate_key(key)
                self.wait(MOVE_STEP_DELAY_MS)
            self.wait(SHORT_DELAY_MS, f"Observe: All images moved {name}")

        self.log.success("Arrow movement completed")

    def step_keyboard_space(self) -> None:
        """Step 43: Keyboard space center on test scene."""
        self.log.section("KEYBOARD - SPACE CENTER")

        self.ensure_test_scene_loaded()

        # Move off-center first
        self.log.action("Moving scene off-center")
        for _ in range(10):
            self.simulate_key(Qt.Key_Right)
            self.wait(MOVE_STEP_DELAY_MS)
        self.wait(SHORT_DELAY_MS, "Scene is now off-center")

        self.log.action("Press SPACE to center view")
        self.simulate_key(Qt.Key_Space)
        self.wait(DEFAULT_DELAY_MS, "Observe: View CENTERED")
        self.log.success("Space center completed")

    def step_keyboard_delete(self) -> None:
        """Step 44: Keyboard delete media on test scene."""
        self.log.section("KEYBOARD - DELETE MEDIA")

        self.ensure_test_scene_loaded()

        zui = self.window.zui
        center = QPoint(zui.width() // 2, zui.height() // 2)

        self.log.action("Click to select an image")
        self.simulate_mouse_click(center)
        self.wait(DEFAULT_DELAY_MS, "Image SELECTED")

        self.log.action("Press DELETE to remove selected image")
        self.simulate_key(Qt.Key_Delete)
        self.wait(DEFAULT_DELAY_MS, "Observe: One image DELETED")

        # Reload test scene for subsequent tests
        self.log.action("Reloading test scene")
        self.scene_loaded = False
        self.ensure_test_scene_loaded()

        self.log.success("Delete completed, scene reloaded")

    def step_complete_workflow(self) -> None:
        """Step 90: Complete workflow with test scene."""
        self.log.section("COMPLETE WORKFLOW TEST")

        # 1. Load test scene
        self.log.action("Step 1: Load test scene with all images")
        self.scene_loaded = False
        self.step_load_test_scene()

        # 2. Navigate - zoom and pan
        self.log.action("Step 2: Navigate - zoom in")
        zui = self.window.zui
        center = QPoint(zui.width() // 2, zui.height() // 2)
        for _ in range(5):
            self.simulate_wheel(center, 120)
            self.wait(ZOOM_STEP_DELAY_MS)
        self.wait(SHORT_DELAY_MS, "Zoomed in on images")

        self.log.action("Step 3: Navigate - pan around")
        for key in [Qt.Key_Left, Qt.Key_Down, Qt.Key_Right, Qt.Key_Up]:
            for _ in range(3):
                self.simulate_key(key)
                self.wait(MOVE_STEP_DELAY_MS)
        self.wait(SHORT_DELAY_MS, "Panned around images")

        # 3. Save
        self.log.action("Step 4: Save scene")
        workflow_path = os.path.join(self.resources['save_dir'], 'workflow_complete.pzs')
        try:
            self.window.zui.scene.save(workflow_path)
            self.log.success(f"Scene saved to {workflow_path}")
        except Exception as e:
            self.log.warning(f"Save failed: {e}")
        self.wait(DEFAULT_DELAY_MS)

        # 4. Zoom out to see all
        self.log.action("Step 5: Zoom out to see everything")
        for _ in range(10):
            self.simulate_wheel(center, -120)
            self.wait(ZOOM_STEP_DELAY_MS)
        self.wait(DEFAULT_DELAY_MS, "Full view of all images + string")

        self.log.section("WORKFLOW COMPLETED SUCCESSFULLY")

    def step_quit(self) -> None:
        """Step 99: Quit (skip actual quit)."""
        self.log.section("FILE MENU - QUIT")
        self.log.action("Quit test (skipped to avoid closing)")
        self.wait(DEFAULT_DELAY_MS)
        self.log.success("Quit test skipped")

    # =========================================================================
    # RUN METHODS
    # =========================================================================

    def run(self, start_step: int = 1) -> None:
        """Run tests starting from the specified step."""
        try:
            self.setup()

            for step_num, description, step_func in self.steps:
                if step_num < start_step:
                    print(f"Skipping step {step_num}: {description}")
                    continue

                print(f"\n>>> Running step {step_num}: {description}")
                try:
                    step_func()
                except Exception as e:
                    self.log.warning(f"Step {step_num} failed: {e}")
                    import traceback
                    traceback.print_exc()

        except KeyboardInterrupt:
            print("\n\nTest interrupted by user (Ctrl+C)")
        finally:
            self.teardown()

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="PyZUI GUI Integration Tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python gui_integration.py                  # Run all tests
  python gui_integration.py --start-step 5   # Start from step 5
  python gui_integration.py --list-steps     # List all steps

Note: This file is named gui_integration.py (not test_*.py) so pytest
won't automatically pick it up. Run it directly with python.
        """
    )
    parser.add_argument(
        '--start-step', '-s',
        type=int,
        default=1,
        help='Start from this step number (default: 1)'
    )
    parser.add_argument(
        '--list-steps', '-l',
        action='store_true',
        help='List all available test steps and exit'
    )

    args = parser.parse_args()

    test = GUIIntegrationTest()

    if args.list_steps:
        test.list_steps()
        return

    test.run(start_step=args.start_step)

if __name__ == '__main__':
    main()
