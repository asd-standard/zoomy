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

"""SceneClipboardManager - Clipboard functionality for Scene class.

This class manages copy/paste operations for SVG objects within a scene.
It was extracted from the Scene class to improve modularity and maintainability.
"""

import logging
from typing import Any

from pyzui.objects.mediaobjects.svgmediaobject import SVGMediaObject


class SceneClipboardManager:
    """Manager for scene clipboard functionality.

    This class handles copy and paste operations for SVG objects within a scene.
    It maintains an internal clipboard and provides methods for copying selected
    objects and pasting them with optional offset.

    Attributes:
        _scene: Reference to the parent Scene object
        _logger: Logger instance for clipboard operations
        _clipboard: List of serialized object data for clipboard storage
    """

    def __init__(self, scene):
        """Initialize SceneClipboardManager.

        Args:
            scene: Parent Scene object
        """
        self._scene = scene
        self._logger = logging.getLogger(__name__)
        self._clipboard: list[dict[str, Any]] = []

    def copy_selection(self) -> None:
        """Copy selected SVG objects to internal clipboard.

        Only SVGMediaObjects are supported for copy/paste.
        Deselects copied objects after copying.
        """
        if not hasattr(self._scene, "selection") or not self._scene.selection:
            return

        self._clipboard.clear()

        # Handle both single object and list selection
        objects = self._scene.selection if isinstance(self._scene.selection, list) else [self._scene.selection]

        svg_count = 0
        for obj in objects:
            # Only copy SVGMediaObjects
            if isinstance(obj, SVGMediaObject):
                self._clipboard.append(obj.to_dict())
                svg_count += 1
            else:
                # Silent fail for non-SVG objects as requested
                self._logger.debug(f"Skipping non-SVG object in copy: {type(obj).__name__}")

        # Deselect copied objects as requested
        self._scene.selection = None

        # Log at debug level for developer visibility
        if svg_count > 0:
            self._logger.debug(f"Copied {svg_count} SVG object(s) to clipboard")

    def paste(self, offset_position: tuple[float, float] | None = None) -> list["SVGMediaObject"]:
        """Paste SVG objects from clipboard with fixed offset.

        Only SVGMediaObjects are supported for copy/paste.
        Selects pasted objects after pasting.
        Logs warning for unsupported object types.

        Args:
            offset_position: Optional offset position for pasted objects

        Returns:
            List of pasted SVGMediaObject instances
        """
        if not self._clipboard:
            return []

        pasted_objects: list[SVGMediaObject] = []
        has_unsupported_types = False

        # First pass: collect SVG positions and create objects
        svg_objects = []
        svg_positions = []

        for obj_data in self._clipboard:
            try:
                obj_type = obj_data["type"]
                if obj_type == "SVGMediaObject":
                    obj = SVGMediaObject.from_dict(obj_data, self._scene)
                    svg_objects.append(obj)
                    pos = obj_data["position"]
                    svg_positions.append((pos[0], pos[1]))
                else:
                    has_unsupported_types = True
                    self._logger.warning(f"Unsupported object type in clipboard: {obj_type}")
            except Exception as e:
                self._logger.warning(f"Failed to deserialize object from clipboard: {e}")
                continue

        # Calculate centroid if we have positions and offset
        centroid_x = 0.0
        centroid_y = 0.0
        if svg_positions and offset_position is not None:
            centroid_x = sum(p[0] for p in svg_positions) / len(svg_positions)
            centroid_y = sum(p[1] for p in svg_positions) / len(svg_positions)

        # Second pass: apply offset and add to scene
        for i, obj in enumerate(svg_objects):
            try:
                if offset_position is not None and svg_positions:
                    # Apply offset relative to centroid
                    old_x, old_y = svg_positions[i]
                    offset_x, offset_y = offset_position
                    new_x = old_x + (offset_x - centroid_x)
                    new_y = old_y + (offset_y - centroid_y)
                    obj.pos = (new_x, new_y)

                # Add to scene using public add method
                if hasattr(self._scene, "add"):
                    self._scene.add(obj)
                    pasted_objects.append(obj)
            except Exception as e:
                self._logger.warning(f"Failed to paste object: {e}")
                continue

        # Select pasted objects
        if pasted_objects:
            self._scene.selection = pasted_objects[0] if len(pasted_objects) == 1 else pasted_objects

        # Log warnings if needed
        if has_unsupported_types:
            self._logger.warning("Clipboard contains unsupported object types (only SVG supported)")

        return pasted_objects

    def clear(self) -> None:
        """Clear the clipboard."""
        self._clipboard.clear()
        self._logger.debug("Clipboard cleared")

    def has_content(self) -> bool:
        """Check if clipboard has content.

        Returns:
            True if clipboard has content, False otherwise
        """
        return len(self._clipboard) > 0

    def get_content_count(self) -> int:
        """Get number of items in clipboard.

        Returns:
            Number of items in clipboard
        """
        return len(self._clipboard)
