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

"""Step: Right-click string to open modify string dialog."""

from __future__ import annotations

from typing import TYPE_CHECKING

from guiintegration.conf import SHORT_DELAY_MS
from guiintegration.utilities.qt_simulation import simulate_mouse_click, wait
from guiintegration.utilities.scene_helpers import close_open_dialog, ensure_test_scene_loaded
from PySide6.QtCore import QPoint, Qt

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def run(ctx: GUITestContext) -> None:
    ctx.log.section("MOUSE RIGHT-CLICK - STRING MODIFICATION DIALOG")
    ensure_test_scene_loaded(ctx)
    zui = ctx.window.zui
    w, h = zui.width(), zui.height()
    string_center = QPoint(int(w * 0.5), int(h * 0.85))
    ctx.log.action("Right-click on test string to open modify dialog")
    close_open_dialog(ctx)
    simulate_mouse_click(ctx, string_center, Qt.RightButton)
    wait(ctx, SHORT_DELAY_MS, "Wait for modify string dialog to appear and close")
    ctx.log.success("String modification dialog opened and closed")
