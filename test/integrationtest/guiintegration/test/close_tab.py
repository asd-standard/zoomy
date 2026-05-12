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

"""Step: File > Close Tab — close current tab and verify last tab protected."""

from __future__ import annotations

from typing import TYPE_CHECKING

from guiintegration.conf import DEFAULT_DELAY_MS
from guiintegration.utilities.qt_simulation import trigger_action, wait
from guiintegration.utilities.scene_helpers import ensure_test_scene_loaded

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def run(ctx: GUITestContext) -> None:
    ctx.log.section("FILE MENU - CLOSE TAB")
    tab_widget = ctx.window._MainWindow__tab_widget
    initial_count = tab_widget.count()
    if initial_count < 2:
        ctx.log.warning("Need at least 2 tabs to test close — creating one")
        trigger_action(ctx, "new_tab")
        wait(ctx, DEFAULT_DELAY_MS)
        initial_count = tab_widget.count()
    ctx.log.action(f"Closing current tab (count: {initial_count})")
    wait(ctx, 1000, "1s pause before closing — observe the loaded tab")
    trigger_action(ctx, "close_tab")
    wait(ctx, DEFAULT_DELAY_MS, "Waiting for tab to close")
    after_count = tab_widget.count()
    ctx.log.detail(f"Tab count: {initial_count} -> {after_count}")
    if after_count == initial_count - 1:
        ctx.log.success(f"Tab closed (remaining: {after_count})")
    else:
        ctx.log.warning(f"Expected {initial_count - 1} tabs, got {after_count}")
    if after_count == 1:
        ctx.log.action("Attempting to close last tab (should be prevented)")
        trigger_action(ctx, "close_tab")
        wait(ctx, DEFAULT_DELAY_MS)
        if tab_widget.count() == 1:
            ctx.log.success("Last tab preserved (close prevented)")
        else:
            ctx.log.warning("Last tab was closed unexpectedly")
    ctx.log.action("Reloading test scene on remaining tab")
    ctx.scene_loaded = False
    ensure_test_scene_loaded(ctx)
