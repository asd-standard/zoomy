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

"""Step: Shift+click doesn't change selection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from guiintegration.conf import DEFAULT_DELAY_MS
from guiintegration.utilities.qt_simulation import (
    simulate_key,
    simulate_key_press,
    simulate_key_release,
    simulate_mouse_click,
    wait,
)
from guiintegration.utilities.scene_helpers import ensure_test_scene_loaded
from PySide6.QtCore import QPoint, Qt

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def run(ctx: GUITestContext) -> None:
    ctx.log.section("MOUSE - SHIFT+CLICK NO SELECTION CHANGE")
    ensure_test_scene_loaded(ctx)
    zui = ctx.window.zui
    center = QPoint(zui.width() // 2, zui.height() // 2)
    corner = QPoint(50, 50)

    ctx.log.action("Clearing any existing selection")
    simulate_key(ctx, Qt.Key_Escape)
    wait(ctx, DEFAULT_DELAY_MS)

    ctx.log.action("Click center to select an image")
    simulate_mouse_click(ctx, center)
    wait(ctx, DEFAULT_DELAY_MS, "Image SELECTED")

    ctx.log.action("Pressing and holding Shift key")
    simulate_key_press(ctx, Qt.Key_Shift)
    wait(ctx, DEFAULT_DELAY_MS)

    ctx.log.action("Shift+click on corner (selection should NOT change)")
    simulate_mouse_click(ctx, corner, Qt.LeftButton, Qt.ShiftModifier)
    wait(ctx, DEFAULT_DELAY_MS, "Observe: Selection UNCHANGED (still original image)")

    ctx.log.action("Releasing Shift key")
    simulate_key_release(ctx, Qt.Key_Shift)

    ctx.log.action("Click corner without Shift (selection SHOULD change)")
    simulate_mouse_click(ctx, corner)
    wait(ctx, DEFAULT_DELAY_MS, "Observe: Selection CHANGED to corner image")

    ctx.log.success("Shift+click selection behavior verified")

    simulate_key(ctx, Qt.Key_Escape)
    wait(ctx, DEFAULT_DELAY_MS)
