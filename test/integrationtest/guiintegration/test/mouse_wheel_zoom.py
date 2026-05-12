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

"""Step: Mouse scroll wheel zoom on test scene."""

from __future__ import annotations

from typing import TYPE_CHECKING

from guiintegration.conf import DEFAULT_DELAY_MS, ZOOM_STEP_DELAY_MS
from guiintegration.utilities.qt_simulation import simulate_wheel, wait
from guiintegration.utilities.scene_helpers import ensure_test_scene_loaded
from PySide6.QtCore import QPoint

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def run(ctx: GUITestContext) -> None:
    ctx.log.section("MOUSE INTERACTIONS - SCROLL WHEEL ZOOM")
    ensure_test_scene_loaded(ctx)
    zui = ctx.window.zui
    center = QPoint(zui.width() // 2, zui.height() // 2)
    ctx.log.action("Scroll UP to ZOOM IN on images")
    for _i in range(5):
        simulate_wheel(ctx, center, 120)
        wait(ctx, ZOOM_STEP_DELAY_MS)
    wait(ctx, DEFAULT_DELAY_MS, "Observe: Images ZOOMED IN - more detail visible")
    ctx.log.action("Scroll DOWN to ZOOM OUT")
    for _i in range(10):
        simulate_wheel(ctx, center, -120)
        wait(ctx, ZOOM_STEP_DELAY_MS)
    wait(ctx, DEFAULT_DELAY_MS, "Observe: Images ZOOMED OUT - all visible")
    ctx.log.success("Wheel zoom completed")
