# GUI Integration Test Documentation

This document describes the GUI integration test suite for PyZUI, located at `test/integrationtest/gui_integration.py`.

## Overview

The GUI integration test is a comprehensive end-to-end test that launches the full PyZUI application and performs all possible user interactions as documented in `userinterface.rst`. The test is designed for **human visual verification** - each action is logged at DEBUG level and executed with appropriate time delays so a human observer can verify the behavior visually.

## Important Notes

- **Not a pytest test**: The file is intentionally named `gui_integration.py` (not `test_*.py`) so pytest won't automatically discover and run it
- **Run directly with Python**: Execute the script directly using the Python interpreter
- **Visual verification**: The test includes deliberate delays for human observation
- **Interruptible**: Press `Ctrl+C` at any time to stop the test

## Usage

### Running All Tests

```bash
# From project root
python test/integrationtest/gui_integration.py

# Or from the test directory
cd test/integrationtest
python gui_integration.py
```

### Starting from a Specific Step

Use the `--start-step` or `-s` argument to skip earlier steps:

```bash
# Start from step 10 (View Menu tests)
python test/integrationtest/gui_integration.py --start-step 10

# Short form
python test/integrationtest/gui_integration.py -s 30
```

### Listing Available Steps

```bash
python test/integrationtest/gui_integration.py --list-steps
python test/integrationtest/gui_integration.py -l
```

## Test Steps

The test suite is organized into numbered steps grouped by functionality:

| Step | Description |
|------|-------------|
| **Setup** | |
| 1 | Setup - Load Test Scene (Media Dir + String) |
| **File Menu** | |
| 2 | File Menu - New Scene |
| 3 | File Menu - Open Home Scene |
| 4 | File Menu - Reload Test Scene |
| 5 | File Menu - Save Screenshot |
| 6 | File Menu - Save Scene |
| 7 | File Menu - Open Saved Scene |
| **View Menu** | |
| 10 | View Menu - Set Framerate |
| 11 | View Menu - Adjust Sensitivity |
| 12 | View Menu - Fullscreen Toggle |
| **Help Menu** | |
| 20 | Help Menu - About |
| 21 | Help Menu - About Qt |
| **Mouse Interactions** | |
| 30 | Mouse - Left Click Select |
| 31 | Mouse - Click and Drag |
| 32 | Mouse - Scroll Wheel Zoom |
| **Keyboard Interactions** | |
| 40 | Keyboard - Escape Deselect |
| 41 | Keyboard - Page Up/Down Zoom |
| 42 | Keyboard - Arrow Keys Move |
| 43 | Keyboard - Space Center |
| 44 | Keyboard - Delete Media |
| **Workflow** | |
| 90 | Complete Workflow |
| 99 | File Menu - Quit (skipped) |

## Test Resources

### Temporary Directory Structure

The test creates a pytest-style temporary directory structure:

```
/tmp/pytest-of-{username}/pytest-{n}/pyzui_gui_test0/
├── media_directory/
│   ├── 01_red_stripes.png
│   ├── 02_green_gradient.png
│   ├── 03_blue_checkerboard.png
│   ├── 04_yellow_solid.png
│   ├── 05_purple_diagonal.png
│   └── 06_cyan_circles.png
└── save_output/
    ├── test_screenshot.png
    ├── test_scene.pzs
    └── workflow_complete.pzs
```

- **media_directory**: Contains 6 test images with distinctive colors and patterns
- **save_output**: Contains screenshots and saved scenes created during the test
- **Files are preserved**: The temp directory is NOT deleted after the test, allowing inspection

### Test Images

Six test images are automatically generated with different colors and patterns:

| Image | Color | Pattern |
|-------|-------|---------|
| 01_red_stripes.png | Red (255, 64, 64) | Horizontal stripes |
| 02_green_gradient.png | Green (64, 200, 64) | Horizontal gradient |
| 03_blue_checkerboard.png | Blue (64, 64, 255) | Checkerboard |
| 04_yellow_solid.png | Yellow (255, 220, 64) | Solid color |
| 05_purple_diagonal.png | Purple (180, 64, 255) | Diagonal lines |
| 06_cyan_circles.png | Cyan (64, 220, 220) | Concentric circles |

Images are created as PNG (if PIL/Pillow is available) or PPM format (fallback).

## Timing Configuration

The test includes configurable timing constants (in milliseconds) that control the pace of execution:

| Constant | Default | Description |
|----------|---------|-------------|
| `SHORT_DELAY_MS` | 2000 | Short pauses (2 seconds) |
| `DEFAULT_DELAY_MS` | 3500 | Standard delay between actions (3.5 seconds) |
| `LONG_DELAY_MS` | 5000 | Long delay for loading/rendering (5 seconds) |
| `IMAGE_LOAD_DELAY_MS` | 10000 | Extra time for images to fully load/tile (10 seconds) |
| `ZOOM_STEP_DELAY_MS` | 800 | Delay between zoom steps (0.8 seconds) |
| `MOVE_STEP_DELAY_MS` | 500 | Delay between movement steps (0.5 seconds) |

To adjust timing, edit these constants at the top of `gui_integration.py`.

## Logging

The test uses DEBUG-level logging with visual markers:

- **STEP markers**: Each major action is marked with `=====` lines
- **Section headers**: Test categories are marked with `#####` lines
- **Action details**: Detailed logging with `->` prefix
- **Wait indicators**: `[WAIT]` prefix shows delays
- **Success/Warning**: `[OK]` and `[WARN]` prefixes indicate results

Log files are written to the `logs/` directory in the project root.

## What Gets Tested

### File Menu Operations
- Creating new blank scenes
- Opening the home scene (PyZUI logo)
- Loading images from a directory (`open_media_dir` action)
- Saving and loading scenes (`.pzs` format)
- Saving screenshots

### View Menu Operations
- Changing framerate (10, 20, 30, 40 FPS)
- Adjusting zoom sensitivity
- Toggling fullscreen mode

### Help Menu Operations
- About dialog (skipped to avoid blocking)
- About Qt dialog (skipped to avoid blocking)

### Mouse Interactions
- Left-click selection of media objects
- Click-and-drag to pan the view
- Scroll wheel zoom (in/out)

### Keyboard Interactions
- **Escape**: Deselect current selection
- **Page Up/Down**: Zoom in/out
- **Arrow keys**: Pan the view
- **Space**: Center the view
- **Delete**: Remove selected media object

## Architecture

### Main Classes

- **`GUIIntegrationTest`**: Main test runner class that manages the application lifecycle and test execution
- **`GUITestLogger`**: Custom logger with visual formatting for test output

### Key Methods

| Method | Description |
|--------|-------------|
| `setup()` | Initialize Qt app, create resources, show window |
| `teardown()` | Clean up resources (preserves temp files) |
| `run(start_step)` | Execute tests starting from specified step |
| `trigger_action(key)` | Trigger a menu action by internal key |
| `simulate_key(key, modifiers)` | Simulate keyboard input |
| `simulate_mouse_click(pos, button)` | Simulate mouse click |
| `simulate_mouse_drag(start, end)` | Simulate click-and-drag |
| `simulate_wheel(pos, delta)` | Simulate scroll wheel |
| `wait(ms, description)` | Wait with Qt event processing |

### Qt Testing Utilities Used

- `QTest.qWait()` - Wait while processing events
- `QTest.mouseClick()` - Simulate mouse clicks
- `QTest.mousePress()/mouseRelease()` - Simulate drag operations
- `QTest.keyClick()` - Simulate keyboard input
- `QWheelEvent` - Custom wheel events for zoom
- `QMouseEvent` - Custom mouse events for drag

## Troubleshooting

### Test Runs Too Fast

Increase the timing constants at the top of the file. The default values are designed for reasonable human observation.

### Images Don't Load

1. Check that PIL/Pillow is installed for PNG support
2. Verify the temp directory was created correctly
3. Check the console output for error messages

### Test Crashes on Startup

Ensure you're running from the project root directory, or that the script can find `data/home.pzs` and other required files.

### Can't See Visual Output

The test requires a graphical display. If running via SSH, ensure X11 forwarding is enabled or use a virtual display (Xvfb).

### Keyboard/Mouse Events Not Working

Some window managers may intercept certain key combinations. Try running in fullscreen mode or disabling conflicting shortcuts.

## Example Output

```
============================================================
[Test Resources Created]
============================================================
  Temp directory:   /tmp/pytest-of-user/pytest-5/pyzui_gui_test0
  Media directory:  /tmp/pytest-of-user/pytest-5/pyzui_gui_test0/media_directory
  Save directory:   /tmp/pytest-of-user/pytest-5/pyzui_gui_test0/save_output
  Images created:   6
============================================================

>>> Running step 1: Setup - Load Test Scene (Media Dir + String)

######################################################################
# SETUP - LOAD TEST SCENE
######################################################################

============================================================
STEP 1: Loading media directory: /tmp/pytest-of-user/pytest-5/pyzui_gui_test0/media_directory
============================================================
  -> Loading media directory via action: /tmp/pytest-of-user/pytest-5/...
  -> Waiting for image to load: All images from media directory loading
  ...
  [OK] Test scene loaded with all images and string
```

## Dependencies

- **PySide6**: Qt bindings for Python
- **PIL/Pillow** (optional): For PNG image generation (falls back to PPM)

## Related Files

- `doc/userinterface.rst` - User interface documentation that defines all tested interactions
- `pyzui/windows/mainwindow.py` - Main window implementation
- `pyzui/objects/scene/scene.py` - Scene management
- `pyzui/tilesystem/tilemanager.py` - Image tiling system
