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

"""Step: Control+click rectangle drawing selection and move."""

from __future__ import annotations

from typing import TYPE_CHECKING

from guiintegration.conf import DEFAULT_DELAY_MS, SHORT_DELAY_MS, ZOOM_STEP_DELAY_MS
from guiintegration.utilities.qt_simulation import (
    simulate_key,
    simulate_key_press,
    simulate_key_release,
    simulate_mouse_drag,
    simulate_wheel,
    wait,
)
from guiintegration.utilities.scene_helpers import ensure_test_scene_loaded
from PySide6.QtCore import QPoint, Qt

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def run(ctx: GUITestContext) -> None:
    ctx.log.section("MOUSE - CONTROL+CLICK RECTANGLE DRAWING SELECTION AND MOVE")
    ensure_test_scene_loaded(ctx)
    zui = ctx.window.zui
    center = QPoint(zui.width() // 2, zui.height() // 2)

    ctx.log.action("Clearing any existing selection")
    simulate_key(ctx, Qt.Key_Escape)
    wait(ctx, DEFAULT_DELAY_MS)

    ctx.log.action("Zooming out slightly (2 wheel scrolls)")
    for _ in range(2):
        simulate_wheel(ctx, center, -120)
        wait(ctx, ZOOM_STEP_DELAY_MS)
    wait(ctx, DEFAULT_DELAY_MS, "Observe: Scene zoomed out slightly")

    w, h = zui.width(), zui.height()
    rect_start = QPoint(50, h // 4)
    rect_end = QPoint(w // 2, 3 * h // 4)

    ctx.log.action(
        f"Rectangle covers left half: ({rect_start.x()},{rect_start.y()}) to ({rect_end.x()},{rect_end.y()})"
    )
    ctx.log.action("Should select objects in left half of scene")
    ctx.log.action("Pressing and holding Control key")
    simulate_key_press(ctx, Qt.Key_Control)
    wait(ctx, DEFAULT_DELAY_MS)

    ctx.log.action("Control+click drag to draw selection rectangle")
    simulate_mouse_drag(ctx, rect_start, rect_end, Qt.LeftButton, Qt.ControlModifier)
    wait(ctx, SHORT_DELAY_MS, "Observe: Green rectangle drawn during drag")

    ctx.log.action("Releasing Control key")
    simulate_key_release(ctx, Qt.Key_Control)

    wait(ctx, DEFAULT_DELAY_MS, "Observe: Rectangle completed, objects in left half selected")

    ctx.log.action("Moving selected objects from center of first test image to left")
    center = QPoint(zui.width() // 2, zui.height() // 2)
    drag_end = QPoint(center.x() - 200, center.y() + 100)
    simulate_mouse_drag(ctx, center, drag_end, Qt.LeftButton, Qt.NoModifier)
    wait(ctx, DEFAULT_DELAY_MS, "Observe: Selected objects moved to the left")

    ctx.log.success("Control+click rectangle drawing completed - selected left half objects and moved them to the left")

    ctx.log.action("Clearing selection")
    simulate_key(ctx, Qt.Key_Escape)
    wait(ctx, DEFAULT_DELAY_MS)
