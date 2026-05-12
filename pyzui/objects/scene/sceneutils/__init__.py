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

"""Scene utility modules for PyZUI.

This package contains utility classes and functions that were extracted
from the main Scene class to improve modularity and maintainability.
"""

from .autosave import SceneAutosaveManager
from .clipboard import SceneClipboardManager
from .parallel import SceneParallelRenderer
from .prioritybatcher import PriorityBatcher

__all__ = ["PriorityBatcher", "SceneAutosaveManager", "SceneClipboardManager", "SceneParallelRenderer"]
