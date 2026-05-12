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

"""Step: Start blank scene, add 7 SVG types, test all elongation modes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from guiintegration.conf import DEFAULT_DELAY_MS, LONG_DELAY_MS, SHORT_DELAY_MS, ZOOM_STEP_DELAY_MS
from guiintegration.utilities.qt_simulation import (
    simulate_key,
    simulate_key_press,
    simulate_key_release,
    simulate_mouse_click,
    simulate_wheel,
    trigger_action,
    wait,
)
from guiintegration.utilities.scene_helpers import add_svg_to_scene
from PySide6.QtCore import QPoint, Qt

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def run(ctx: GUITestContext) -> None:
    ctx.log.section("SVG - FULL ELONGATION TEST")

    ctx.log.action("Starting with blank scene for SVG tests")
    trigger_action(ctx, "new_scene")
    wait(ctx, SHORT_DELAY_MS, "Blank scene ready")

    zui = ctx.window.zui
    w, h = zui.width(), zui.height()

    simulate_key(ctx, Qt.Key_Escape)
    wait(ctx, DEFAULT_DELAY_MS)

    ctx.log.action("Adding 7 SVG shapes for elongation tests")
    cols = [
        ("right_arrow.svg", (int(w * 0.15), int(h * 0.30))),
        ("bottomright_arrow.svg", (int(w * 0.35), int(h * 0.30))),
        ("horizontal_stick.svg", (int(w * 0.55), int(h * 0.30))),
        ("diagonal_stick.svg", (int(w * 0.75), int(h * 0.30))),
        ("square.svg", (int(w * 0.22), int(h * 0.70))),
        ("circle.svg", (int(w * 0.50), int(h * 0.70))),
        ("up_triangle.svg", (int(w * 0.78), int(h * 0.70))),
    ]
    for filename, pos in cols:
        add_svg_to_scene(ctx, filename, position=pos)
    wait(ctx, LONG_DELAY_MS, "Row 1: arrow, diag-arrow, stick, diag-stick — Row 2: square, circle, triangle")

    _key_to_mod = {
        Qt.Key_Control: Qt.ControlModifier,
        Qt.Key_Shift: Qt.ShiftModifier,
        Qt.Key_Alt: Qt.AltModifier,
    }

    def _elongate(name, click_pos, modifiers_sequence):
        """Run one elongation sequence (select, hold modifiers, wheel, release)."""
        ctx.log.action(f"Elongate {name}")
        simulate_mouse_click(ctx, QPoint(click_pos[0], click_pos[1]))
        wait(ctx, DEFAULT_DELAY_MS)
        wheel_mod = Qt.NoModifier
        for mod in modifiers_sequence:
            simulate_key_press(ctx, mod)
            wheel_mod |= _key_to_mod[mod]
        for _ in range(3):
            simulate_wheel(ctx, QPoint(click_pos[0], click_pos[1]), 120, modifiers=wheel_mod)
            wait(ctx, ZOOM_STEP_DELAY_MS)
        for mod in reversed(modifiers_sequence):
            simulate_key_release(ctx, mod)
        wait(ctx, DEFAULT_DELAY_MS)

    _elongate("right_arrow (straight)", cols[0][1], [Qt.Key_Control])
    _elongate("bottomright_arrow (diagonal)", cols[1][1], [Qt.Key_Control])

    _elongate("horizontal_stick (straight)", cols[2][1], [Qt.Key_Control])
    _elongate("diagonal_stick (diagonal)", cols[3][1], [Qt.Key_Control])

    _elongate("square proportional (Ctrl)", cols[4][1], [Qt.Key_Control])
    _elongate("square X-only (Shift)", cols[4][1], [Qt.Key_Shift])
    _elongate("square Y-only (Ctrl+Shift)", cols[4][1], [Qt.Key_Control, Qt.Key_Shift])

    _elongate("circle proportional (Ctrl)", cols[5][1], [Qt.Key_Control])
    _elongate("circle X-only (Shift)", cols[5][1], [Qt.Key_Shift])
    _elongate("circle Y-only (Ctrl+Shift)", cols[5][1], [Qt.Key_Control, Qt.Key_Shift])

    _elongate("triangle proportional (Ctrl)", cols[6][1], [Qt.Key_Control])
    _elongate("triangle X-only (Shift)", cols[6][1], [Qt.Key_Shift])
    _elongate("triangle Y-only (Ctrl+Shift)", cols[6][1], [Qt.Key_Control, Qt.Key_Shift])

    simulate_key(ctx, Qt.Key_Escape)
    wait(ctx, DEFAULT_DELAY_MS)

    ctx.log.success("All SVG elongations complete — SVGs remain for copy/paste/right-click steps")
    ctx.scene_loaded = True
