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

"""Step: Load the main test scene with media directory + string."""

from __future__ import annotations

from typing import TYPE_CHECKING

from guiintegration.conf import LONG_DELAY_MS, SHORT_DELAY_MS
from guiintegration.utilities.qt_simulation import trigger_action, wait, wait_for_image_load
from guiintegration.utilities.scene_helpers import add_test_string, load_media_directory_with_action

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def run(ctx: GUITestContext) -> None:
    ctx.log.section("SETUP - LOAD TEST SCENE")

    trigger_action(ctx, "new_scene")
    wait(ctx, SHORT_DELAY_MS, "Starting with blank scene")

    ctx.log.action(f"Loading media directory: {ctx.resources['media_dir']}")
    load_media_directory_with_action(ctx)
    wait_for_image_load(ctx, "All images from media directory loading")

    ctx.log.action("Adding test string below images")
    add_test_string(ctx)

    wait(ctx, LONG_DELAY_MS, "Observe: All images in grid + green test string below")

    ctx.scene_loaded = True
    ctx.log.success("Test scene loaded with all images and string")
