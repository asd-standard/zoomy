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

"""Step: View > Fullscreen Toggle — enter and exit fullscreen mode."""

from __future__ import annotations

from typing import TYPE_CHECKING

from guiintegration.conf import DEFAULT_DELAY_MS, LONG_DELAY_MS
from guiintegration.utilities.qt_simulation import trigger_action, wait
from guiintegration.utilities.scene_helpers import ensure_test_scene_loaded

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def run(ctx: GUITestContext) -> None:
    ctx.log.section("VIEW MENU - FULLSCREEN TOGGLE")
    ensure_test_scene_loaded(ctx)
    ctx.log.action("Entering fullscreen")
    trigger_action(ctx, "fullscreen")
    wait(ctx, LONG_DELAY_MS, "Observe: FULLSCREEN mode with all images")
    ctx.log.success("Fullscreen entered")
    ctx.log.action("Exiting fullscreen")
    trigger_action(ctx, "fullscreen")
    wait(ctx, DEFAULT_DELAY_MS, "Observe: Normal window")
    ctx.log.success("Fullscreen exited")
