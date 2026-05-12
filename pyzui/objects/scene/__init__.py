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

"""Scene module for PyZUI.

This module contains the Scene class and related utilities for managing
collections of media objects in a zooming user interface.
"""

from .scene import Scene, load_scene, new
from .sceneutils import SceneAutosaveManager, SceneClipboardManager, SceneParallelRenderer

__all__ = ["Scene", "SceneAutosaveManager", "SceneClipboardManager", "SceneParallelRenderer", "load_scene", "new"]
