#!/usr/bin/env python
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
SemVer version bump utility for PyZUI.

Usage:
    python scripts/bump_version.py patch            # 0.4.0 -> 0.4.1
    python scripts/bump_version.py minor            # 0.4.0 -> 0.5.0
    python scripts/bump_version.py major            # 0.4.0 -> 1.0.0
    python scripts/bump_version.py minor --tag      # also creates git tag
    python scripts/bump_version.py minor -b         # 0.5.0 -> 0.4.0
    python scripts/bump_version.py current          # re-capture screenshot
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

INIT_PATH = Path(__file__).resolve().parent.parent / "pyzui" / "__init__.py"
HOME_PZS_PATH = Path(__file__).resolve().parent.parent / "data" / "home.pzs"
HOME_PNG_PATH = Path(__file__).resolve().parent.parent / "data" / "home.png"
VERSION_RE = re.compile(r'^(\s*__version__\s*=\s*)"(\d+\.\d+\.\d+)"')
PZS_VERSION_RE = re.compile(r"(string:[A-Fa-f0-9]+:)\d+\.\d+\.\d+")


def _read_current_version() -> tuple[str, int, str]:
    """Read the current version string and its line from __init__.py.

    Returns:
        Tuple of (version_string, line_number, full_line_content)
    """
    if not INIT_PATH.exists():
        sys.exit(f"ERROR: {INIT_PATH} not found. Run from project root.")

    lines = INIT_PATH.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        m = VERSION_RE.match(line)
        if m:
            return m.group(2), i, line
    sys.exit("ERROR: __version__ not found in pyzui/__init__.py")


def _write_new_version(line_num: int, old_line: str, new_version: str) -> None:
    """Write the new version string into __init__.py."""
    new_line = VERSION_RE.sub(r'\1"' + new_version + '"', old_line)
    lines = INIT_PATH.read_text(encoding="utf-8").splitlines()
    lines[line_num] = new_line
    INIT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Version bumped in __init__.py: {old_line.strip()} -> {new_line.strip()}")


def _update_home_pzs(old_version: str, new_version: str) -> None:
    """Update the version string in data/home.pzs StringMediaObject.

    Args:
        old_version: Current version string (e.g. '0.4.0').
        new_version: New version string (e.g. '0.4.1').
    """
    if not HOME_PZS_PATH.exists():
        print(f"Warning: {HOME_PZS_PATH} not found, skipping.")
        return

    content = HOME_PZS_PATH.read_text(encoding="utf-8")
    if old_version not in content:
        print(f"Warning: version {old_version} not found in {HOME_PZS_PATH}, skipping.")
        return

    new_content = PZS_VERSION_RE.sub(r"\g<1>" + new_version, content)
    if new_content == content:
        print(f"Warning: no version pattern matched in {HOME_PZS_PATH}, skipping.")
        return

    HOME_PZS_PATH.write_text(new_content, encoding="utf-8")
    print(f"Version bumped in home.pzs: {old_version} -> {new_version}")


def _validate_semver(version: str) -> None:
    """Validate that a string is a proper SemVer."""
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        sys.exit(f"ERROR: Invalid SemVer: {version}")


def _create_git_tag(version: str) -> None:
    """Create an annotated git tag for the release."""
    tag = f"v{version}"
    msg = f"Release v{version}"
    try:
        subprocess.run(
            ["git", "tag", "-a", tag, "-m", msg],
            check=True,
            capture_output=True,
            text=True,
        )
        print(f"Git tag created: {tag}")
    except subprocess.CalledProcessError as e:
        sys.exit(f"ERROR: Failed to create git tag: {e.stderr.strip()}")


def _capture_home_screenshot() -> None:
    """Open home scene offscreen, take screenshot, save as home.png.

    Uses the offscreen Qt platform to render the home scene without a
    display server.  Initialises the minimum dependencies needed for
    rendering (TileManager, ZoomManager), loads the updated home.pzs,
    waits for fern tiles to be generated, snaps the camera to the exact
    position from the .pzs file, then captures the widget to
    data/home.png.
    """
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

    project_root = str(Path(__file__).resolve().parent.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from PySide6 import QtCore, QtWidgets

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)

    import pyzui.tilesystem.tilemanager as TileManager

    TileManager.init(auto_cleanup=False)

    from pyzui.objects.objectsutils import ZoomManager
    from pyzui.objects.physicalobject import PhysicalObject

    PhysicalObject.set_zoom_manager(ZoomManager({}))

    from pyzui.objects.scene.qzui import QZUI

    zui = QZUI(framerate=20, config={})

    from pyzui.objects.scene import scene as Scene

    zui.resize(1280, 720)
    zui.show()
    zui.scene = Scene.load_scene(str(HOME_PZS_PATH))

    # Ensure viewport size is set (resizeEvent may not fire offscreen)
    zui.scene.viewport_size = (1280, 720)

    # Process events to trigger tile requests and start animation
    for _ in range(60):
        app.processEvents(QtCore.QEventLoop.AllEvents, 50)

    # Poll for fern root tile (timeout ~6 s)
    FERN_TILE_ID: tuple[str, int, int, int] = ("dynamic:fern", 0, 0, 0)
    tile_ready = False
    for _ in range(60):
        try:
            TileManager.get_tile(FERN_TILE_ID)
            tile_ready = True
            break
        except (TileManager.TileNotLoaded, TileManager.TileNotAvailable):
            app.processEvents(QtCore.QEventLoop.AllEvents, 100)
    if tile_ready:
        print("Fern root tile loaded.")
    else:
        print("Warning: fern root tile not loaded in time; screenshot may be incomplete.")

    # Read target camera position from home.pzs
    with open(HOME_PZS_PATH) as f:
        target_zoom_str, target_ox_str, target_oy_str = f.readline().split()
    target_zoom = float(target_zoom_str)
    target_ox = float(target_ox_str)
    target_oy = float(target_oy_str)

    # Snap camera directly to the saved position (bypass animation)
    zui.scene.zoomlevel = target_zoom
    zui.scene.origin = (target_ox, target_oy)
    zui.scene.vx = zui.scene.vy = zui.scene.vz = 0.0

    # Let tiles render at the final position
    for _ in range(25):
        app.processEvents(QtCore.QEventLoop.AllEvents, 50)

    # Force a final repaint at full quality
    zui.repaint()
    app.processEvents(QtCore.QEventLoop.AllEvents, 100)

    pixmap = zui.grab()
    pixmap.save(str(HOME_PNG_PATH))
    print(f"Saved home screenshot to {HOME_PNG_PATH}")

    TileManager.shutdown()
    app.quit()


def bump(part: str, tag: bool = False, backwards: bool = False) -> None:
    """Bump the version number.

    Args:
        part: One of 'major', 'minor', 'patch', or 'current'.
        tag: If True, create an annotated git tag after bumping.
        backwards: If True, decrement instead of incrementing.
    """
    current, line_num, old_line = _read_current_version()
    major, minor, patch = map(int, current.split("."))

    if part == "current":
        print(f"Current version: {current} — re-capturing screenshot")
        try:
            _capture_home_screenshot()
        except Exception as e:
            print(f"Warning: failed to capture home screenshot: {e}")
        return

    if backwards:
        if part == "major":
            major = max(0, major - 1)
        elif part == "minor":
            minor = max(0, minor - 1)
        elif part == "patch":
            patch = max(0, patch - 1)
        else:
            sys.exit(f"ERROR: Unknown part '{part}'. Use major, minor, or patch.")
    else:
        if part == "major":
            major += 1
            minor = 0
            patch = 0
        elif part == "minor":
            minor += 1
            patch = 0
        elif part == "patch":
            patch += 1
        else:
            sys.exit(f"ERROR: Unknown part '{part}'. Use major, minor, or patch.")

    new_version = f"{major}.{minor}.{patch}"
    _validate_semver(new_version)
    _write_new_version(line_num, old_line, new_version)
    _update_home_pzs(current, new_version)

    try:
        _capture_home_screenshot()
    except Exception as e:
        print(f"Warning: failed to capture home screenshot: {e}")

    if tag:
        _create_git_tag(new_version)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bump the PyZUI SemVer version in pyzui/__init__.py")
    parser.add_argument(
        "part",
        choices=["major", "minor", "patch", "current"],
        help="Which version segment to bump, or 'current' to re-capture screenshot",
    )
    parser.add_argument(
        "--tag",
        action="store_true",
        help="Create an annotated git tag after bumping",
    )
    parser.add_argument(
        "-b",
        "--backwards",
        action="store_true",
        help="Decrement version instead of incrementing",
    )
    args = parser.parse_args()
    bump(args.part, tag=args.tag, backwards=args.backwards)


if __name__ == "__main__":
    main()
