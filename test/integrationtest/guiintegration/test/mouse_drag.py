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

"""Step: Mouse click and drag on test scene."""

from __future__ import annotations

from typing import TYPE_CHECKING

from guiintegration.conf import DEFAULT_DELAY_MS
from guiintegration.utilities.qt_simulation import simulate_mouse_drag, wait
from guiintegration.utilities.scene_helpers import ensure_test_scene_loaded
from PySide6.QtCore import QPoint

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def run(ctx: GUITestContext) -> None:
    ctx.log.section("MOUSE INTERACTIONS - CLICK AND DRAG")
    ensure_test_scene_loaded(ctx)
    zui = ctx.window.zui
    center = QPoint(zui.width() // 2, zui.height() // 2)
    drag_end = QPoint(center.x() + 150, center.y() + 100)
    ctx.log.action("Dragging scene content")
    simulate_mouse_drag(ctx, center, drag_end)
    wait(ctx, DEFAULT_DELAY_MS, "Observe: All images MOVED together")
    ctx.log.action("Dragging back")
    simulate_mouse_drag(ctx, drag_end, center)
    wait(ctx, DEFAULT_DELAY_MS, "Observe: Content returned")
    ctx.log.success("Drag completed")
