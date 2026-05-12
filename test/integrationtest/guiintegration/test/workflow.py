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

"""Step: Complete workflow - load, zoom, pan, save, zoom out."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from guiintegration.conf import DEFAULT_DELAY_MS, MOVE_STEP_DELAY_MS, SHORT_DELAY_MS, ZOOM_STEP_DELAY_MS
from guiintegration.utilities.qt_simulation import simulate_key, simulate_wheel, wait
from guiintegration.utilities.scene_helpers import ensure_test_scene_loaded
from PySide6.QtCore import QPoint, Qt

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def run(ctx: GUITestContext) -> None:
    ctx.log.section("COMPLETE WORKFLOW TEST")

    ctx.log.action("Step 1: Load test scene with all images")
    ctx.scene_loaded = False
    ensure_test_scene_loaded(ctx)

    ctx.log.action("Step 2: Navigate - zoom in")
    zui = ctx.window.zui
    center = QPoint(zui.width() // 2, zui.height() // 2)
    for _ in range(5):
        simulate_wheel(ctx, center, 120)
        wait(ctx, ZOOM_STEP_DELAY_MS)
    wait(ctx, SHORT_DELAY_MS, "Zoomed in on images")

    ctx.log.action("Step 3: Navigate - pan around")
    for key in [Qt.Key_Left, Qt.Key_Down, Qt.Key_Right, Qt.Key_Up]:
        for _ in range(3):
            simulate_key(ctx, key)
            wait(ctx, MOVE_STEP_DELAY_MS)
    wait(ctx, SHORT_DELAY_MS, "Panned around images")

    ctx.log.action("Step 4: Save scene")
    workflow_path = os.path.join(ctx.resources["save_dir"], "workflow_complete.pzs")
    try:
        ctx.window.zui.scene.save(workflow_path)
        ctx.log.success(f"Scene saved to {workflow_path}")
    except Exception as e:
        ctx.log.warning(f"Save failed: {e}")
    wait(ctx, DEFAULT_DELAY_MS)

    ctx.log.action("Step 5: Zoom out to see everything")
    for _ in range(10):
        simulate_wheel(ctx, center, -120)
        wait(ctx, ZOOM_STEP_DELAY_MS)
    wait(ctx, DEFAULT_DELAY_MS, "Full view of all images + string")

    ctx.log.section("WORKFLOW COMPLETED SUCCESSFULLY")
