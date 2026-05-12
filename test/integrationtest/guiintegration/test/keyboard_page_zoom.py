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

"""Step: Keyboard Page Up/Down zoom."""

from __future__ import annotations

from typing import TYPE_CHECKING

from guiintegration.conf import DEFAULT_DELAY_MS, ZOOM_STEP_DELAY_MS
from guiintegration.utilities.qt_simulation import (
    simulate_key,
    wait,
)
from guiintegration.utilities.scene_helpers import ensure_test_scene_loaded
from PySide6.QtCore import Qt

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def run(ctx: GUITestContext) -> None:
    ctx.log.section("KEYBOARD - PAGE UP/DOWN ZOOM")
    ensure_test_scene_loaded(ctx)
    ctx.log.action("Press PAGE UP to zoom in on images")
    for _i in range(5):
        simulate_key(ctx, Qt.Key_PageUp)
        wait(ctx, ZOOM_STEP_DELAY_MS)
    wait(ctx, DEFAULT_DELAY_MS, "Observe: Images ZOOMED IN")
    ctx.log.action("Press PAGE DOWN to zoom out")
    for _i in range(10):
        simulate_key(ctx, Qt.Key_PageDown)
        wait(ctx, ZOOM_STEP_DELAY_MS)
    wait(ctx, DEFAULT_DELAY_MS, "Observe: Images ZOOMED OUT")
    ctx.log.success("Page zoom completed")
