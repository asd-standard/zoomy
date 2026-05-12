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

"""Step: Actions > Copy SVG — select an SVG object and copy it."""

from __future__ import annotations

from typing import TYPE_CHECKING

from guiintegration.conf import DEFAULT_DELAY_MS
from guiintegration.utilities.qt_simulation import simulate_key, simulate_mouse_click, trigger_action, wait
from guiintegration.utilities.scene_helpers import ensure_test_scene_loaded
from PySide6.QtCore import QPoint, Qt

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def run(ctx: GUITestContext) -> None:
    ctx.log.section("ACTIONS MENU - COPY SVG")
    ensure_test_scene_loaded(ctx)
    zui = ctx.window.zui
    svg_click_pos = QPoint(int(zui.width() * 0.22), int(zui.height() * 0.70))
    ctx.log.action("Selecting an SVG object")
    simulate_key(ctx, Qt.Key_Escape)
    wait(ctx, DEFAULT_DELAY_MS)
    simulate_mouse_click(ctx, svg_click_pos)
    wait(ctx, DEFAULT_DELAY_MS, "SVG object selected")
    ctx.log.action("Copying SVG (Ctrl+C)")
    trigger_action(ctx, "copy")
    wait(ctx, DEFAULT_DELAY_MS, "SVG copied to clipboard")
    ctx.log.success("Copy SVG completed")
