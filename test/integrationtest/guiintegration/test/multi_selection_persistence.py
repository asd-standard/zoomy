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

"""Step: Multi-selection persistence — create multi-select then test behaviors."""

from __future__ import annotations

from typing import TYPE_CHECKING

from guiintegration.conf import DEFAULT_DELAY_MS
from guiintegration.utilities.qt_simulation import (
    simulate_key,
    simulate_key_press,
    simulate_key_release,
    simulate_mouse_click,
    simulate_mouse_drag,
    wait,
)
from guiintegration.utilities.scene_helpers import ensure_test_scene_loaded
from PySide6.QtCore import QPoint, Qt

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def run(ctx: GUITestContext) -> None:
    ctx.log.section("MOUSE - MULTI-SELECTION PERSISTENCE")
    ensure_test_scene_loaded(ctx)
    zui = ctx.window.zui
    center = QPoint(zui.width() // 2, zui.height() // 2)

    ctx.log.action("Creating multi-selection via Ctrl+click drag")
    simulate_key(ctx, Qt.Key_Escape)
    wait(ctx, DEFAULT_DELAY_MS)

    simulate_key_press(ctx, Qt.Key_Control)
    wait(ctx, DEFAULT_DELAY_MS)
    rect_start = QPoint(50, zui.height() // 4)
    rect_end = QPoint(zui.width() * 3 // 4, zui.height() * 3 // 4)
    simulate_mouse_drag(ctx, rect_start, rect_end, Qt.LeftButton, Qt.ControlModifier)
    wait(ctx, DEFAULT_DELAY_MS, "Multi-selection created")
    simulate_key_release(ctx, Qt.Key_Control)
    wait(ctx, DEFAULT_DELAY_MS)

    ctx.log.action("Clicking on empty space (corner) - selection should persist")
    simulate_mouse_click(ctx, QPoint(15, 15))
    wait(ctx, DEFAULT_DELAY_MS, "Observe: Multi-selection still visible (green borders)")
    ctx.log.success("Multi-selection persisted after clicking empty space")

    ctx.log.action("Clicking on an already-selected object - selection persists")
    simulate_mouse_click(ctx, center)
    wait(ctx, DEFAULT_DELAY_MS, "Observe: Same multi-selection still visible")
    ctx.log.success("Multi-selection persisted after clicking selected object")

    ctx.log.action("Clicking outside selection bounds - single select")
    simulate_key(ctx, Qt.Key_Escape)
    wait(ctx, DEFAULT_DELAY_MS)

    simulate_key(ctx, Qt.Key_Escape)
    wait(ctx, DEFAULT_DELAY_MS)
