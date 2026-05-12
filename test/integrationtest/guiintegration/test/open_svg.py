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

"""Step: File > Open new SVG."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from guiintegration.conf import DEFAULT_DELAY_MS, SHORT_DELAY_MS
from guiintegration.utilities.qt_simulation import trigger_action, wait
from guiintegration.utilities.scene_helpers import close_open_dialog, ensure_test_scene_loaded

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def run(ctx: GUITestContext) -> None:
    ctx.log.section("FILE MENU - OPEN NEW SVG")
    ensure_test_scene_loaded(ctx)
    ctx.log.action("Opening SVG picker dialog")
    close_open_dialog(ctx)
    from pyzui.windows.dialogwindows.dialogwindows import DialogWindows

    with patch.object(
        DialogWindows.open_svg_picker_input_dialog, "_run_dialog", return_value=(True, ctx.resources["temp_svg"])
    ):
        trigger_action(ctx, "open_svg_pick")
    wait(ctx, SHORT_DELAY_MS, "Wait for SVG picker dialog to appear and close")
    wait(ctx, DEFAULT_DELAY_MS, "Observe: Red rectangle SVG should be visible")
    ctx.log.success("New SVG opened")
