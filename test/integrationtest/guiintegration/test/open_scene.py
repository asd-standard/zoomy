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

"""Step: File > Open Scene."""

from __future__ import annotations

from typing import TYPE_CHECKING

from guiintegration.conf import DEFAULT_DELAY_MS, SHORT_DELAY_MS
from guiintegration.utilities.qt_simulation import trigger_action, wait, wait_for_image_load

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def run(ctx: GUITestContext) -> None:
    ctx.log.section("FILE MENU - OPEN SCENE")
    if "test_scene" not in ctx.resources:
        ctx.log.warning("No saved scene available - run save_scene first")
        return
    trigger_action(ctx, "new_scene")
    wait(ctx, SHORT_DELAY_MS)
    ctx.log.action(f"Opening scene: {ctx.resources['test_scene']}")
    try:
        from pyzui.objects.scene import scene as Scene

        ctx.window.zui.scene = Scene.load_scene(ctx.resources["test_scene"])
        ctx.app.processEvents()
    except Exception as e:
        ctx.log.warning(f"Error loading scene: {e}")
    wait_for_image_load(ctx, "Scene loading")
    wait(ctx, DEFAULT_DELAY_MS, "Observe: Saved scene restored")
    ctx.log.success("Scene loaded")
