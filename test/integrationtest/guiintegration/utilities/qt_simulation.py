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

"""Qt event simulation utilities for GUI integration tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from guiintegration.conf import DEFAULT_DELAY_MS, IMAGE_LOAD_DELAY_MS
from PySide6 import QtCore, QtGui
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

if TYPE_CHECKING:
    from guiintegration.main import GUITestContext


def wait(ctx: GUITestContext, ms: int = DEFAULT_DELAY_MS, description: str = "") -> None:
    """Wait for specified milliseconds, processing Qt events."""
    if description:
        ctx.log.wait(f"Waiting {ms}ms - {description}")
    QTest.qWait(ms)


def wait_for_image_load(ctx: GUITestContext, description: str = "") -> None:
    """Wait for images to load and tile, with progress checking."""
    ctx.log.detail(f"Waiting for image to load: {description}")

    total_wait = IMAGE_LOAD_DELAY_MS
    chunk = 500
    elapsed = 0

    while elapsed < total_wait:
        QTest.qWait(chunk)
        ctx.app.processEvents()
        elapsed += chunk

        if elapsed % 2000 == 0:
            ctx.log.detail(f"  ... still loading ({elapsed}ms / {total_wait}ms)")

    ctx.log.detail("Image load wait complete")


def trigger_action(ctx: GUITestContext, action_key: str) -> bool:
    """Trigger a menu action by its internal key."""
    try:
        action = ctx.window._MainWindow__action.get(action_key)
        if action:
            ctx.log.detail(f"Triggering action: {action_key}")
            action.trigger()
            ctx.app.processEvents()
            return True
        else:
            ctx.log.warning(f"Action not found: {action_key}")
            return False
    except Exception as e:
        ctx.log.warning(f"Failed to trigger action {action_key}: {e}")
        return False


def simulate_key(ctx: GUITestContext, key: Qt.Key, modifiers: Qt.KeyboardModifier = Qt.NoModifier) -> None:
    """Simulate a key press."""
    ctx.log.detail(f"Simulating key press: {key}")
    QTest.keyClick(ctx.window.zui, key, modifiers)
    ctx.app.processEvents()


def simulate_key_press(ctx: GUITestContext, key: Qt.Key, modifiers: Qt.KeyboardModifier = Qt.NoModifier) -> None:
    """Simulate a key press (without release)."""
    ctx.log.detail(f"Simulating key press (hold): {key}")
    QTest.keyPress(ctx.window.zui, key, modifiers)
    ctx.app.processEvents()


def simulate_key_release(ctx: GUITestContext, key: Qt.Key, modifiers: Qt.KeyboardModifier = Qt.NoModifier) -> None:
    """Simulate a key release."""
    ctx.log.detail(f"Simulating key release: {key}")
    QTest.keyRelease(ctx.window.zui, key, modifiers)
    ctx.app.processEvents()


def simulate_mouse_click(
    ctx: GUITestContext,
    pos: QPoint,
    button: Qt.MouseButton = Qt.LeftButton,
    modifiers: Qt.KeyboardModifier = Qt.NoModifier,
) -> None:
    """Simulate a mouse click."""
    ctx.log.detail(f"Simulating mouse click at ({pos.x()}, {pos.y()}) with modifiers {modifiers}")
    QTest.mouseClick(ctx.window.zui, button, modifiers, pos)
    ctx.app.processEvents()


def simulate_mouse_drag(
    ctx: GUITestContext,
    start: QPoint,
    end: QPoint,
    button: Qt.MouseButton = Qt.LeftButton,
    modifiers: Qt.KeyboardModifier = Qt.NoModifier,
) -> None:
    """Simulate a mouse drag operation."""
    ctx.log.detail(
        f"Simulating drag from ({start.x()}, {start.y()}) to ({end.x()}, {end.y()}) with modifiers {modifiers}"
    )
    zui = ctx.window.zui

    QTest.mousePress(zui, button, modifiers, start)
    QTest.qWait(100)

    steps = 20
    for i in range(1, steps + 1):
        x = start.x() + (end.x() - start.x()) * i // steps
        y = start.y() + (end.y() - start.y()) * i // steps
        event = QtGui.QMouseEvent(QtCore.QEvent.MouseMove, QtCore.QPointF(x, y), button, button, modifiers)
        QApplication.postEvent(zui, event)
        QTest.qWait(50)

    QTest.mouseRelease(zui, button, modifiers, end)
    ctx.app.processEvents()


def simulate_wheel(
    ctx: GUITestContext,
    pos: QPoint,
    delta: int,
    modifiers: Qt.KeyboardModifier = Qt.NoModifier,
) -> None:
    """Simulate a mouse wheel scroll."""
    ctx.log.detail(f"Simulating wheel scroll: delta={delta}, modifiers={modifiers}")
    event = QtGui.QWheelEvent(
        QtCore.QPointF(pos),
        QtCore.QPointF(pos),
        QPoint(0, delta),
        QPoint(0, delta),
        Qt.NoButton,
        modifiers,
        Qt.ScrollUpdate,
        False,
    )
    QApplication.postEvent(ctx.window.zui, event)
    QTest.qWait(100)
    ctx.app.processEvents()
