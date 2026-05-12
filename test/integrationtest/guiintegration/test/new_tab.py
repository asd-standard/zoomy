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

"""Step: File > New Tab — create tab and load test scene into it."""

from __future__ import annotations

from typing import TYPE_CHECKING

from guiintegration.conf import DEFAULT_DELAY_MS, SHORT_DELAY_MS
from guiintegration.utilities.qt_simulation import trigger_action, wait, wait_for_image_load
from guiintegration.utilities.scene_helpers import add_test_string, load_media_directory_with_action

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def run(ctx: GUITestContext) -> None:
    ctx.log.section("FILE MENU - NEW TAB")
    tab_widget = ctx.window._MainWindow__tab_widget
    initial_count = tab_widget.count()
    ctx.log.action(f"Creating new tab (current count: {initial_count})")
    trigger_action(ctx, "new_tab")
    wait(ctx, DEFAULT_DELAY_MS, "Waiting for new tab to appear")
    new_count = tab_widget.count()
    ctx.log.detail(f"Tab count: {initial_count} -> {new_count}")
    if new_count == initial_count + 1:
        ctx.log.success(f"New tab created (total: {new_count})")
    else:
        ctx.log.warning(f"Expected {initial_count + 1} tabs, got {new_count}")
    ctx.log.action("Loading test images + string into the new tab")
    load_media_directory_with_action(ctx)
    wait_for_image_load(ctx, "Test images loading into new tab")
    add_test_string(ctx)
    wait(ctx, SHORT_DELAY_MS, "Observe: new tab with 6 images + green test string visible")
    wait(ctx, 1000, "1s pause so you can see the loaded tab")
    ctx.scene_loaded = True
