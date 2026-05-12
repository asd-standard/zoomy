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

"""Step: Keyboard arrow keys move."""

from __future__ import annotations

from typing import TYPE_CHECKING

from guiintegration.conf import MOVE_STEP_DELAY_MS, SHORT_DELAY_MS
from guiintegration.utilities.qt_simulation import (
    simulate_key,
    wait,
)
from guiintegration.utilities.scene_helpers import ensure_test_scene_loaded
from PySide6.QtCore import Qt

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def run(ctx: GUITestContext) -> None:
    ctx.log.section("KEYBOARD - ARROW KEYS MOVE")
    ensure_test_scene_loaded(ctx)
    ctx.log.action("Arrow keys to move all images")
    for key, name in [
        (Qt.Key_Up, "UP"),
        (Qt.Key_Down, "DOWN"),
        (Qt.Key_Left, "LEFT"),
        (Qt.Key_Right, "RIGHT"),
    ]:
        ctx.log.detail(f"Moving {name}")
        for _ in range(5):
            simulate_key(ctx, key)
            wait(ctx, MOVE_STEP_DELAY_MS)
        wait(ctx, SHORT_DELAY_MS, f"Observe: All images moved {name}")
    ctx.log.success("Arrow movement completed")
