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
import sys
import os

# Add the parent directory (pyzui root) to the Python path
# This allows imports like "from pyzui.tile import Tile" to work
pyzui_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if pyzui_root not in sys.path:
    sys.path.insert(0, pyzui_root)
