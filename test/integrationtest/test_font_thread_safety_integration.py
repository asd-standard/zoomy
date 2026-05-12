## PyZUI - Python Zooming User Interface
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

"""Integration tests for font thread safety.

Verifies that TextLayoutData.from_string_object() does not construct
QtGui.QFont or QtGui.QFontMetrics objects on non-main worker threads.

Qt GUI objects (QFont, QFontMetrics, QPainter, etc.) must only be
constructed on the main thread. Constructing them from daemon worker
threads can cause C++-level races in Qt's font database and glyph
caches, leading to intermittent SIGSEGV crashes.
"""

import threading
from unittest.mock import Mock, patch

import pytest
from PySide6 import QtCore, QtGui

from pyzui.objects.mediaobjects.stringmediaobject import StringMediaObject
from pyzui.objects.mediaobjects.mediaobjectsutils.string.textlayout import TextLayoutData


class TestFontThreadSafety:
    """
    Feature: Font Construction Thread Safety

    TextLayoutData.from_string_object() calls StringMediaObject._get_font()
    which accesses the __font property. This property constructs QFont and
    QFontMetrics objects. These Qt GUI objects must only be instantiated
    on the main thread to avoid segfaults in Qt's C++ font engine.
    """

    def test_no_qfont_construction_on_worker_thread_during_from_string_object(
        self
    ):
        """
        Scenario: from_string_object called from worker thread

        Given a StringMediaObject with no cached font
        When TextLayoutData.from_string_object() is called from a
             non-main worker thread
        Then no QtGui.QFont or QtGui.QFontMetrics objects should be
             constructed on the worker thread
        And the worker thread should complete without exception
        """
        # Track QFont constructions on non-main threads
        qfont_worker_constructions = []
        qfontmetrics_worker_constructions = []
        original_qfont_init = QtGui.QFont.__init__
        original_qfontmetrics_init = QtGui.QFontMetrics.__init__

        def patched_qfont_init(self, *args, **kwargs):
            if threading.current_thread() is not threading.main_thread():
                qfont_worker_constructions.append(
                    threading.current_thread().name
                )
            return original_qfont_init(self, *args, **kwargs)

        def patched_qfontmetrics_init(self, *args, **kwargs):
            if threading.current_thread() is not threading.main_thread():
                qfontmetrics_worker_constructions.append(
                    threading.current_thread().name
                )
            return original_qfontmetrics_init(self, *args, **kwargs)

        # Create a StringMediaObject with a mock scene
        scene = Mock()
        scene.zoomlevel = 0
        obj = StringMediaObject("string:FF0000:Hello World", scene)

        # Force font cache miss by invalidating the cached scale/font
        obj._StringMediaObject__cached_scale = -999.0
        obj._StringMediaObject__cached_font = None
        obj._StringMediaObject__cached_font_metrics = None

        viewport_rect = QtCore.QRectF(0, 0, 800, 600)

        exception_in_thread = []

        def worker():
            try:
                with patch.object(
                    QtGui.QFont, '__init__', patched_qfont_init
                ), patch.object(
                    QtGui.QFontMetrics, '__init__', patched_qfontmetrics_init
                ):
                    _layout_data = TextLayoutData.from_string_object(
                        obj, viewport_rect
                    )
            except Exception as e:
                exception_in_thread.append(e)

        t = threading.Thread(target=worker, name="TestWorkerFont")
        t.start()
        t.join(timeout=5.0)

        # Verify no exception in worker thread
        assert not exception_in_thread, (
            f"Exception in worker thread: {exception_in_thread}"
        )
        # Verify the thread completed
        assert not t.is_alive(), "Worker thread did not complete"

        # Verify no QFont was constructed on the worker thread
        assert not qfont_worker_constructions, (
            f"QtGui.QFont constructed on worker threads: "
            f"{qfont_worker_constructions}"
        )
        # Verify no QFontMetrics was constructed on the worker thread
        assert not qfontmetrics_worker_constructions, (
            f"QtGui.QFontMetrics constructed on worker threads: "
            f"{qfontmetrics_worker_constructions}"
        )

    def test_no_qfont_construction_on_worker_thread_during_get_font(self):
        """
        Scenario: _get_font called from worker thread

        Given a StringMediaObject with no cached font
        When _get_font() is called from a non-main worker thread
        Then no QtGui.QFont or QtGui.QFontMetrics objects should be
             constructed on the worker thread
        """
        qfont_worker_constructions = []
        qfontmetrics_worker_constructions = []
        original_qfont_init = QtGui.QFont.__init__
        original_qfontmetrics_init = QtGui.QFontMetrics.__init__

        def patched_qfont_init(self, *args, **kwargs):
            if threading.current_thread() is not threading.main_thread():
                qfont_worker_constructions.append(
                    threading.current_thread().name
                )
            return original_qfont_init(self, *args, **kwargs)

        def patched_qfontmetrics_init(self, *args, **kwargs):
            if threading.current_thread() is not threading.main_thread():
                qfontmetrics_worker_constructions.append(
                    threading.current_thread().name
                )
            return original_qfontmetrics_init(self, *args, **kwargs)

        scene = Mock()
        scene.zoomlevel = 0
        obj = StringMediaObject("string:0000FF:Test", scene)

        # Force font cache miss
        obj._StringMediaObject__cached_scale = -999.0
        obj._StringMediaObject__cached_font = None
        obj._StringMediaObject__cached_font_metrics = None

        exception_in_thread = []

        def worker():
            try:
                with patch.object(
                    QtGui.QFont, '__init__', patched_qfont_init
                ), patch.object(
                    QtGui.QFontMetrics, '__init__', patched_qfontmetrics_init
                ):
                    _font = obj._get_font()
            except Exception as e:
                exception_in_thread.append(e)

        t = threading.Thread(target=worker, name="TestWorkerGetFont")
        t.start()
        t.join(timeout=5.0)

        assert not exception_in_thread, (
            f"Exception in worker thread: {exception_in_thread}"
        )
        assert not qfont_worker_constructions, (
            f"QtGui.QFont constructed on worker threads: "
            f"{qfont_worker_constructions}"
        )
        assert not qfontmetrics_worker_constructions, (
            f"QtGui.QFontMetrics constructed on worker threads: "
            f"{qfontmetrics_worker_constructions}"
        )

    def test_parallel_layout_calculator_worker_does_not_construct_qfont(
        self
    ):
        """
        Scenario: ParallelLayoutCalculator worker does not construct QFont

        Given a ParallelLayoutCalculator with worker threads
        And a StringMediaObject with no cached font submitted for
            calculation
        When the worker thread processes the calculation
        Then no QFont or QFontMetrics should be constructed on the
             worker thread
        """
        from pyzui.objects.mediaobjects.mediaobjectsutils.string.parallellayout import (
            ParallelLayoutCalculator,
        )
        from pyzui.objects.scene.sceneutils.prioritybatcher import (
            BatchPriority,
            PrioritizedObject,
        )

        qfont_worker_constructions = []
        qfontmetrics_worker_constructions = []
        original_qfont_init = QtGui.QFont.__init__
        original_qfontmetrics_init = QtGui.QFontMetrics.__init__

        def patched_qfont_init(self, *args, **kwargs):
            if threading.current_thread() is not threading.main_thread():
                qfont_worker_constructions.append(
                    threading.current_thread().name
                )
            return original_qfont_init(self, *args, **kwargs)

        def patched_qfontmetrics_init(self, *args, **kwargs):
            if threading.current_thread() is not threading.main_thread():
                qfontmetrics_worker_constructions.append(
                    threading.current_thread().name
                )
            return original_qfontmetrics_init(self, *args, **kwargs)

        with patch.object(
            QtGui.QFont, '__init__', patched_qfont_init
        ), patch.object(
            QtGui.QFontMetrics, '__init__', patched_qfontmetrics_init
        ):
            calculator = ParallelLayoutCalculator(max_workers=2)

            scene = Mock()
            scene.zoomlevel = 0
            obj1 = StringMediaObject("string:FF0000:Hello", scene)
            obj2 = StringMediaObject("string:00FF00:World", scene)

            for o in (obj1, obj2):
                o._StringMediaObject__cached_scale = -999.0
                o._StringMediaObject__cached_font = None
                o._StringMediaObject__cached_font_metrics = None

            prioritized = []
            for i, sobj in enumerate((obj1, obj2)):
                p = PrioritizedObject(
                    priority=BatchPriority.HIGH.value,
                    distance=float(i * 10),
                    index=i,
                    object=sobj,
                )
                prioritized.append(p)

            viewport_rect = QtCore.QRectF(0, 0, 800, 600)
            _results = calculator.submit_batch(
                prioritized, viewport_rect
            )

            # Wait for worker threads to complete (deterministic)
            batch_indices = [p.index for p in prioritized]
            calculator.wait_for_batch(batch_indices, timeout_ms=10000)

            calculator.shutdown()

        assert not qfont_worker_constructions, (
            f"QtGui.QFont constructed on worker threads: "
            f"{qfont_worker_constructions}"
        )
        assert not qfontmetrics_worker_constructions, (
            f"QtGui.QFontMetrics constructed on worker threads: "
            f"{qfontmetrics_worker_constructions}"
        )

    def test_qfont_construction_on_main_thread_still_works(self):
        """
        Scenario: QFont construction on main thread still works

        Given a TextLayoutData with plain font data
        When render() or to_qfont() is called from the main thread
        Then QFont should be constructed successfully on the main thread
        """
        layout_data = TextLayoutData(
            text="Main Thread Test",
            font_family="Sans Serif",
            font_pointsize=12.0,
            font_weight=QtGui.QFont.Normal,
            font_italic=False,
            color_r=255,
            color_g=0,
            color_b=0,
            color_a=255,
            position=(100.0, 200.0),
            bounding_rect=QtCore.QRectF(90, 190, 100, 50),
            text_rect=QtCore.QRectF(95, 195, 90, 40),
        )

        # Construct QFont and QColor on main thread
        font = layout_data.to_qfont()
        color = layout_data.to_qcolor()

        assert isinstance(font, QtGui.QFont)
        assert font.family() == "Sans Serif"
        assert font.pointSizeF() == pytest.approx(12.0)
        assert isinstance(color, QtGui.QColor)
        assert color.red() == 255
        assert color.green() == 0
        assert color.blue() == 0
        assert color.alpha() == 255

        # Render should work with a mock painter
        mock_painter = Mock()
        mock_painter.save = Mock()
        mock_painter.restore = Mock()
        mock_painter.setFont = Mock()
        mock_painter.setPen = Mock()
        mock_painter.drawText = Mock()

        layout_data.render(mock_painter)

        mock_painter.save.assert_called_once()
        mock_painter.setFont.assert_called_once()
        mock_painter.setPen.assert_called_once()
        mock_painter.drawText.assert_called_once()
        mock_painter.restore.assert_called_once()
