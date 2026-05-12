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

"""Step: File > Save Screenshot."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from guiintegration.conf import DEFAULT_DELAY_MS
from guiintegration.utilities.qt_simulation import wait
from guiintegration.utilities.scene_helpers import ensure_test_scene_loaded

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def run(ctx: GUITestContext) -> None:
    ctx.log.section("FILE MENU - SAVE SCREENSHOT")
    ensure_test_scene_loaded(ctx)
    screenshot_path = os.path.join(ctx.resources["save_dir"], "test_screenshot.png")
    ctx.log.action(f"Saving screenshot to: {screenshot_path}")
    try:
        pixmap = ctx.window.zui.grab()
        pixmap.save(screenshot_path)
        if os.path.exists(screenshot_path):
            ctx.log.success(f"Screenshot saved: {os.path.getsize(screenshot_path)} bytes")
        else:
            ctx.log.warning("Screenshot not saved")
    except Exception as e:
        ctx.log.warning(f"Error saving screenshot: {e}")
    wait(ctx, DEFAULT_DELAY_MS)
