"""
Pytest configuration file for unittest directory.
This file sets up the Python path so that tests can import from the pyzui package.
"""
import sys
import os

# Add the parent directory (pyzui root) to the Python path
# This allows imports like "from pyzui.tile import Tile" to work
pyzui_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if pyzui_root not in sys.path:
    sys.path.insert(0, pyzui_root)
