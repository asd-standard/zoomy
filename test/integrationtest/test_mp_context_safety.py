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

"""Integration tests for multiprocessing context safety.

Verifies that tilerrunner and converterrunner use 'spawn' as the default
multiprocessing context (avoiding fork-after-threads deadlocks) and that
no DeprecationWarning is emitted when submitting jobs with threads active.
"""

import threading
import warnings

from pyzui.converters import converterrunner
from pyzui.tilesystem.tiler import tilerrunner


class TestMPContextSafety:
    """
    Feature: Multiprocessing Context Safety

    The tilerrunner and converterrunner use 'spawn' as the default
    multiprocessing context to avoid fork-after-threads deadlocks.
    These tests verify the spawn context works correctly with threads
    and that no DeprecationWarning is emitted.
    """

    def test_spawn_context_initialization(self):
        """
        Scenario: Both runners initialize with spawn context by default

        Given no PYZUI_MP_CONTEXT environment variable
        When tilerrunner and converterrunner initialize
        Then both should use 'spawn' context
        """
        tilerrunner.init(max_workers=1)
        assert tilerrunner._executor_context_name == 'spawn'
        tilerrunner.shutdown()

        converterrunner.init(max_workers=1)
        assert converterrunner._executor_context_name == 'spawn'
        converterrunner.shutdown()

    def test_submit_tiling_with_threads_no_deprecation_warning(self):
        """
        Scenario: Tiling submit with threads — no DeprecationWarning

        Given multiple background threads running
        When a tiling job is submitted
        Then no DeprecationWarning about fork-with-threads is emitted
        And the future is successfully created
        """
        # Start background threads
        started = threading.Event()
        keep_running = threading.Event()
        keep_running.set()

        def bg_thread():
            started.set()
            keep_running.wait()

        threads = [
            threading.Thread(target=bg_thread, daemon=True)
            for _ in range(3)
        ]
        for t in threads:
            t.start()

        # Wait for at least one thread to be active
        assert started.wait(timeout=2), "Background thread did not start"

        try:
            tilerrunner.init(max_workers=1)

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                future = tilerrunner.submit_tiling(
                    "test.ppm", media_id="media_test"
                )
                assert future is not None

            fork_warnings = [
                w for w in caught
                if "fork()" in str(w.message)
                or "multi-threaded" in str(w.message)
            ]
            assert len(fork_warnings) == 0, (
                f"DeprecationWarning about fork-with-threads: {fork_warnings}"
            )
        finally:
            keep_running.clear()
            tilerrunner.shutdown()
            for t in threads:
                t.join(timeout=1.0)

    def test_submit_conversion_with_threads_no_deprecation_warning(self):
        """
        Scenario: Conversion submit with threads — no DeprecationWarning

        Given multiple background threads running
        When a conversion job is submitted
        Then no DeprecationWarning about fork-with-threads is emitted
        """
        started = threading.Event()
        keep_running = threading.Event()
        keep_running.set()

        def bg_thread():
            started.set()
            keep_running.wait()

        threads = [
            threading.Thread(target=bg_thread, daemon=True)
            for _ in range(3)
        ]
        for t in threads:
            t.start()

        assert started.wait(timeout=2), "Background thread did not start"

        try:
            converterrunner.init(max_workers=1)

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                future = converterrunner.submit_vips_conversion(
                    "test.png", "test.ppm"
                )
                assert future is not None

            fork_warnings = [
                w for w in caught
                if "fork()" in str(w.message)
                or "multi-threaded" in str(w.message)
            ]
            assert len(fork_warnings) == 0, (
                f"DeprecationWarning about fork-with-threads: {fork_warnings}"
            )
        finally:
            keep_running.clear()
            converterrunner.shutdown()
            for t in threads:
                t.join(timeout=1.0)

    def test_env_override_to_fork_still_works(self, monkeypatch):
        """
        Scenario: PYZUI_MP_CONTEXT=fork override still works

        Given PYZUI_MP_CONTEXT=fork
        When runner initializes
        Then it should use 'fork' context (opt-in to old behavior)
        """
        monkeypatch.setenv('PYZUI_MP_CONTEXT', 'fork')

        tilerrunner.init(max_workers=1)
        assert tilerrunner._executor_context_name == 'fork'
        tilerrunner.shutdown()

    def test_submit_vips_conversion_returns_future(self):
        """
        Scenario: submit_vips_conversion returns a valid Future

        Given an initialized converter runner (spawn context)
        When a conversion is submitted
        Then a Future object is returned
        """
        converterrunner.init(max_workers=1)

        future = converterrunner.submit_vips_conversion(
            "test.png", "test.ppm"
        )
        assert future is not None

        converterrunner.shutdown()

    def test_submit_pdf_conversion_returns_future(self):
        """
        Scenario: submit_pdf_conversion returns a valid Future

        Given an initialized converter runner (spawn context)
        When a PDF conversion is submitted
        Then a Future object is returned
        """
        converterrunner.init(max_workers=1)

        future = converterrunner.submit_pdf_conversion(
            "test.pdf", "test.ppm"
        )
        assert future is not None

        converterrunner.shutdown()

    def test_submit_tiling_returns_future(self):
        """
        Scenario: submit_tiling returns a valid Future

        Given an initialized tiler runner (spawn context)
        When a tiling job is submitted
        Then a Future object is returned
        """
        tilerrunner.init(max_workers=1)

        future = tilerrunner.submit_tiling(
            "test.ppm", media_id="media_test"
        )
        assert future is not None

        tilerrunner.shutdown()
