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

"""Step: View > Render Order Toggle — toggle render order and restore."""

from __future__ import annotations

from typing import TYPE_CHECKING

from guiintegration.conf import DEFAULT_DELAY_MS
from guiintegration.utilities.qt_simulation import trigger_action, wait
from guiintegration.utilities.scene_helpers import ensure_test_scene_loaded

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def run(ctx: GUITestContext) -> None:
    ctx.log.section("VIEW MENU - RENDER ORDER TOGGLE")
    ensure_test_scene_loaded(ctx)
    scene = ctx.window.zui.scene
    initial_order = scene.render_order
    ctx.log.action(f"Current render order: {initial_order}")
    trigger_action(ctx, "render_order_smaller_top")
    wait(ctx, DEFAULT_DELAY_MS, "Render order toggled")
    new_order = scene.render_order
    ctx.log.detail(f"Render order: {initial_order} -> {new_order}")
    ctx.log.success(f"Render order toggled to: {new_order}")
    ctx.log.action("Toggling render order back")
    trigger_action(ctx, "render_order_smaller_top")
    wait(ctx, DEFAULT_DELAY_MS, "Render order restored")
    ctx.log.success("Render order restored")
