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

"""PyZui DialogWindows - Main dialog module that aggregates all dialog components."""

# Import all dialog components from their respective modules
from .zoomsensitivitydialog import open_zoom_sensitivity_input_dialog
from .stringinputdialog import OpenNewStringInputDialog
from .modifystringdialog import ModifyStringInputDialog
from .modifytiledmediaobjectdialog import ModifyTiledMediaObjectDialog

class DialogWindows:
    """
    Constructor :
        DialogWindows()
    Parameters :
        None

    DialogWindows() --> None

    All the windows that require a user input rather than simple click.

    This class serves as a namespace/container for dialog-related functionality.
    The actual dialogs are implemented in separate modules.
    """

    # Static method for zoom sensitivity
    _open_zoom_sensitivity_input_dialog = staticmethod(open_zoom_sensitivity_input_dialog)

    # Nested classes for backward compatibility
    open_new_string_input_dialog = OpenNewStringInputDialog
    modify_string_input_dialog = ModifyStringInputDialog
    modify_tiled_media_object_dialog = ModifyTiledMediaObjectDialog

# Also expose at module level for direct imports
__all__ = [
    'DialogWindows',
    'open_zoom_sensitivity_input_dialog',
    'OpenNewStringInputDialog',
    'ModifyStringInputDialog',
    'ModifyTiledMediaObjectDialog',
]
