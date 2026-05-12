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

"""Step: Alt key fine zoom control on test scene."""

from __future__ import annotations

from typing import TYPE_CHECKING

from guiintegration.conf import DEFAULT_DELAY_MS, ZOOM_STEP_DELAY_MS
from guiintegration.utilities.qt_simulation import (
    simulate_key,
    simulate_key_press,
    simulate_key_release,
    simulate_mouse_click,
    simulate_wheel,
    wait,
)
from guiintegration.utilities.scene_helpers import ensure_test_scene_loaded
from PySide6.QtCore import QPoint, Qt

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def run(ctx: GUITestContext) -> None:
    ctx.log.section("KEYBOARD - ALT FINE ZOOM CONTROL")
    ensure_test_scene_loaded(ctx)
    zui = ctx.window.zui
    center = QPoint(zui.width() // 2, zui.height() // 2)

    ctx.log.action("Selecting an object for fine zoom test")
    simulate_key(ctx, Qt.Key_Escape)
    wait(ctx, DEFAULT_DELAY_MS)
    simulate_mouse_click(ctx, center)
    wait(ctx, DEFAULT_DELAY_MS)

    ctx.log.action("Zooming with Alt held (fine zoom - 1/16 normal)")
    simulate_key_press(ctx, Qt.Key_Alt)
    wait(ctx, DEFAULT_DELAY_MS)
    for _ in range(5):
        simulate_wheel(ctx, center, 120)
        wait(ctx, ZOOM_STEP_DELAY_MS)
    wait(ctx, DEFAULT_DELAY_MS, "Observe: Subtle zoom with Alt key")
    simulate_key_release(ctx, Qt.Key_Alt)
    wait(ctx, DEFAULT_DELAY_MS)

    ctx.log.success("Alt fine zoom control completed")
