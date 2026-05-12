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

"""Step: Keyboard space center."""

from __future__ import annotations

from typing import TYPE_CHECKING

from guiintegration.conf import DEFAULT_DELAY_MS, MOVE_STEP_DELAY_MS, SHORT_DELAY_MS
from guiintegration.utilities.qt_simulation import (
    simulate_key,
    wait,
)
from guiintegration.utilities.scene_helpers import ensure_test_scene_loaded
from PySide6.QtCore import Qt

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def run(ctx: GUITestContext) -> None:
    ctx.log.section("KEYBOARD - SPACE CENTER")
    ensure_test_scene_loaded(ctx)
    ctx.log.action("Moving scene off-center")
    for _ in range(10):
        simulate_key(ctx, Qt.Key_Right)
        wait(ctx, MOVE_STEP_DELAY_MS)
    wait(ctx, SHORT_DELAY_MS, "Scene is now off-center")
    ctx.log.action("Press SPACE to center view")
    simulate_key(ctx, Qt.Key_Space)
    wait(ctx, DEFAULT_DELAY_MS, "Observe: View CENTERED")
    ctx.log.success("Space center completed")
