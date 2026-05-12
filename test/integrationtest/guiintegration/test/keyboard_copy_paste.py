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

"""Step: Keyboard Ctrl+C/Ctrl+V copy-paste."""

from __future__ import annotations

from typing import TYPE_CHECKING

from guiintegration.conf import DEFAULT_DELAY_MS
from guiintegration.utilities.qt_simulation import (
    simulate_key,
    simulate_mouse_click,
    wait,
    wait_for_image_load,
)
from guiintegration.utilities.scene_helpers import ensure_test_scene_loaded
from PySide6.QtCore import QPoint, Qt

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def run(ctx: GUITestContext) -> None:
    ctx.log.section("KEYBOARD - CTRL+C/V COPY PASTE")
    ensure_test_scene_loaded(ctx)
    zui = ctx.window.zui
    scene = ctx.window.zui.scene

    ctx.log.action("Selecting SVG object")
    simulate_key(ctx, Qt.Key_Escape)
    wait(ctx, DEFAULT_DELAY_MS)
    svg_pos = QPoint(int(zui.width() * 0.22), int(zui.height() * 0.70))
    simulate_mouse_click(ctx, svg_pos)
    wait(ctx, DEFAULT_DELAY_MS, "SVG object selected")

    obj_count_before = len(scene._Scene__objects)

    ctx.log.action("Pressing Ctrl+C to copy")
    simulate_key(ctx, Qt.Key_C, Qt.ControlModifier)
    wait(ctx, DEFAULT_DELAY_MS)

    ctx.log.action("Pressing Ctrl+V to paste")
    simulate_key(ctx, Qt.Key_V, Qt.ControlModifier)
    wait_for_image_load(ctx, "Pasted SVG rendering")
    wait(ctx, DEFAULT_DELAY_MS, "Observe: Pasted SVG appears at mouse position")

    obj_count_after = len(scene._Scene__objects)
    if obj_count_after > obj_count_before:
        ctx.log.success(f"Copy-pasted via keyboard (objects: {obj_count_before} -> {obj_count_after})")
    else:
        ctx.log.warning("No new objects detected after keyboard copy-paste")
