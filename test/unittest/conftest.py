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

"""
Pytest configuration file for unittest directory.
This file sets up the Python path so that tests can import from the pyzui package.
"""

import os
import sys

# Add the parent directory (pyzui root) to the Python path
# This allows imports like "from pyzui.tile import Tile" to work
pyzui_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if pyzui_root not in sys.path:
    sys.path.insert(0, pyzui_root)


def pytest_sessionstart(session):
    """Prevent tilemanager from registering real atexit handlers during tests.

    Tests that call tilemanager.init(auto_cleanup=True) register a real
    atexit handler (atexit.register is stdlib, not mocked). After patches
    are undone, this handler fires on the real 83K-file tilestore, causing
    pytest to appear hung for minutes.
    """
    try:
        from pyzui.tilesystem import tilemanager

        tilemanager.__cleanup_enabled = False
    except Exception:
        pass


def pytest_sessionfinish(session, exitstatus):
    """Ensure cleanup resources don't block pytest exit.

    - TileManager atexit: prevent expensive tilestore walk
    - ConverterRunner/TilerRunner: the 'spawn' multiprocessing context
      creates a resource tracker whose __del__ hangs during interpreter
      shutdown (stuck in _stop_locked). Force-clean the resource tracker
      to prevent this hang.
    """
    try:
        from pyzui.tilesystem import tilemanager

        tilemanager.__cleanup_executed = True
        tilemanager.__cleanup_enabled = False
    except Exception:
        pass

    try:
        from pyzui.converters import converterrunner

        converterrunner._atexit_registered = False
    except (ImportError, AttributeError):
        pass

    try:
        from pyzui.tilesystem.tiler import tilerrunner

        tilerrunner._atexit_registered = False
    except (ImportError, AttributeError):
        pass

    # Force-clean the multiprocessing resource tracker to prevent
    # the hang in resource_tracker._stop_locked during __del__
    try:
        import multiprocessing.resource_tracker

        tracker = multiprocessing.resource_tracker._resource_tracker
        if tracker is not None:
            # Mark tracker as stopped and join its thread if alive
            tracker._stop = lambda *args, **kwargs: None  # no-op to prevent re-stop
            if hasattr(tracker, "_thread") and tracker._thread is not None:
                tracker._thread.join(timeout=0.5)
    except Exception:
        pass
