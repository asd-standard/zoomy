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

"""Scene helper utilities for adding content and managing dialogs."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING
from unittest.mock import patch

from guiintegration.conf import SHORT_DELAY_MS
from PySide6 import QtCore
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext

    from pyzui.objects.mediaobjects.svgmediaobject import SVGMediaObject


def load_media_directory_with_action(ctx: GUITestContext) -> None:
    """Load all images from media_directory using the open_media_dir action."""
    from guiintegration.utilities.qt_simulation import trigger_action

    ctx.log.detail(f"Loading media directory via action: {ctx.resources['media_dir']}")

    with patch.object(QFileDialog, "getExistingDirectory", return_value=ctx.resources["media_dir"]):
        trigger_action(ctx, "open_media_dir")


def add_test_string(ctx: GUITestContext) -> None:
    """Add a test string below the images."""
    ctx.log.detail("Adding test string to scene")
    try:
        from pyzui.objects.mediaobjects.stringmediaobject import StringMediaObject

        test_string = "string:00ff00:GUI Integration Test - All Images Loaded"
        mediaobject = StringMediaObject(test_string, ctx.window.zui.scene)

        w, h = ctx.window.zui.width(), ctx.window.zui.height()
        mediaobject.fit((w * 0.1, h * 0.75, w * 0.9, h * 0.95))

        ctx.window.zui.scene.add(mediaobject)
        ctx.app.processEvents()
        ctx.log.success("Test string added")
    except Exception as e:
        ctx.log.warning(f"Error adding string: {e}")


def add_svg_to_scene(ctx: GUITestContext, svg_filename: str, position: tuple | None = None) -> SVGMediaObject | None:
    """Add an SVG shape from data/SVG/ to the scene.

    Reads the original SVG, replaces 'black' with 'white' so shapes
    are visible on the dark background, and caches the result in the
    temp directory.

    Args:
        svg_filename: SVG filename (relative to data/SVG/)
        position: Optional (x, y) scene position override

    Returns:
        The created SVGMediaObject
    """
    from pyzui.objects.mediaobjects.svgmediaobject import SVGMediaObject

    ctx.log.detail(f"Adding SVG: {svg_filename}")
    try:
        svg_path = os.path.join(ctx.project_root, "data", "SVG", svg_filename)
        if not os.path.exists(svg_path):
            ctx.log.warning(f"SVG not found: {svg_path}")
            return None

        with open(svg_path) as f:
            svg_content = f.read()
        svg_content = svg_content.replace('"black"', '"white"').replace("'black'", "'white'")

        cache_key = svg_filename.replace(".svg", "") + "_white"
        cached_path = os.path.join(ctx.temp_dir, f"{cache_key}.svg")
        with open(cached_path, "w") as f:
            f.write(svg_content)

        mediaobject = SVGMediaObject(cached_path, ctx.window.zui.scene)
        zui = ctx.window.zui
        w, h = zui.width(), zui.height()

        if position:
            px, py = position
            mediaobject.fit((px - 90, py - 40, px + 90, py + 40))
        else:
            mediaobject.fit((int(w * 0.7), int(h * 0.15), int(w * 0.95), int(h * 0.85)))

        ctx.window.zui.scene.add(mediaobject)
        ctx.app.processEvents()
        ctx.log.success(f"SVG added: {svg_filename}")
        return mediaobject
    except Exception as e:
        ctx.log.warning(f"Error adding SVG {svg_filename}: {e}")
        return None


def close_open_dialog(ctx: GUITestContext) -> None:
    """Schedule closing any open modal dialog via reject() after a delay."""
    QtCore.QTimer.singleShot(SHORT_DELAY_MS // 2, lambda: _reject_visible_dialog(ctx))


def _reject_visible_dialog(ctx: GUITestContext) -> None:
    """Find and close any visible QDialog by calling reject()."""
    for widget in QApplication.topLevelWidgets():
        if isinstance(widget, QDialog) and widget.isVisible():
            ctx.log.detail(f"Closing dialog: {widget.windowTitle()}")
            widget.reject()
            break


def ensure_test_scene_loaded(ctx: GUITestContext) -> None:
    """Ensure the test scene with images and string is loaded."""
    if not ctx.scene_loaded:
        from guiintegration.test.load_test_scene import run

        run(ctx)
