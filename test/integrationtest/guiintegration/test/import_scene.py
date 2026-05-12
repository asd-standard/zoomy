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

"""Step: File > Import Scene."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

from guiintegration.conf import DEFAULT_DELAY_MS, SHORT_DELAY_MS
from guiintegration.utilities.qt_simulation import trigger_action, wait, wait_for_image_load
from PySide6.QtWidgets import QFileDialog

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def run(ctx: GUITestContext) -> None:
    ctx.log.section("FILE MENU - IMPORT SCENE")
    if "test_scene" not in ctx.resources:
        ctx.log.warning("No saved scene available - run save_scene first")
        return
    trigger_action(ctx, "new_scene")
    wait(ctx, SHORT_DELAY_MS, "Starting with blank scene")
    ctx.log.action(f"Importing scene: {ctx.resources['test_scene']}")
    with patch.object(QFileDialog, "getOpenFileName", return_value=(ctx.resources["test_scene"], "")):
        trigger_action(ctx, "import_scene")
    wait_for_image_load(ctx, "Imported scene loading")
    wait(ctx, DEFAULT_DELAY_MS, "Observe: Scene content imported into current scene")
    ctx.scene_loaded = False
    ctx.log.success("Scene imported")
