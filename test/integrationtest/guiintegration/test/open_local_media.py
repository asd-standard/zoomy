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

"""Step: File > Open Local Media."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING
from unittest.mock import patch

from guiintegration.conf import DEFAULT_DELAY_MS
from guiintegration.utilities.qt_simulation import trigger_action, wait, wait_for_image_load
from guiintegration.utilities.scene_helpers import ensure_test_scene_loaded
from PySide6.QtWidgets import QFileDialog

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def run(ctx: GUITestContext) -> None:
    ctx.log.section("FILE MENU - OPEN LOCAL MEDIA")
    ensure_test_scene_loaded(ctx)
    ctx.log.action("Opening local media file")
    local_image = os.path.join(ctx.resources["media_dir"], "04_yellow_solid.png")
    if not os.path.exists(local_image):
        local_image = os.path.join(ctx.resources["media_dir"], "04_yellow_solid.ppm")
    with patch.object(QFileDialog, "getOpenFileName", return_value=(local_image, "")):
        trigger_action(ctx, "open_media_local")
    wait_for_image_load(ctx, "Local media loading")
    wait(ctx, DEFAULT_DELAY_MS, "Observe: Yellow solid image should now appear")
    ctx.log.success("Local media opened")
