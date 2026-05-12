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

"""``SVG`` objects to be displayed in the ZUI."""

from pathlib import Path
from typing import Any

from PySide6 import QtCore, QtSvg

from pyzui.logger import get_logger

from .mediaobject import LoadError, MediaObject
from .mediaobjectsutils.svg.svgcache.svgcache import get_svg_cache


class SVGMediaObject(MediaObject):
    """
    Constructor :
        SVGMediaObject(media_id, scene)
    Parameters :
        media_id : str
        scene : Scene

    SVGMediaObject(media_id, scene) --> None

    SVGMediaObject objects are used to represent SVG images that can be
    rendered in the ZUI.
    """

    def __get_svg_load_path(self, media_id: str) -> str:
        """
        Get the file path to load SVG from, handling cache hashes.

        Args:
            media_id: Either a file path or cache hash (starting with ``'svg_'``)

        Returns:
            File path to load
        """
        # Check if media_id is a cache hash (starts with 'svg_')
        if media_id.startswith("svg_"):
            # It's a cache hash, get path from cache
            svg_cache = get_svg_cache()
            cache_path = svg_cache.get_cache_path(media_id)
            if not cache_path.exists():
                # Try to get content from cache (might have been stored elsewhere)
                content = svg_cache.get_svg_content(media_id)
                if content is None:
                    raise LoadError(f"SVG cache hash not found: {media_id}")
                # Re-store in cache (in case cache was cleaned up)
                svg_cache.store_svg(content)
            return str(cache_path)
        else:
            # It's a file path
            return media_id

    def __init__(self, media_id: str, scene: Any) -> None:
        """
        Constructor :
            SVGMediaObject(media_id, scene)
        Parameters :
            media_id : str (can be file path or cache hash starting with ``'svg_'``)
            scene : Scene

        SVGMediaObject(media_id, scene) --> None

        Initialize a new SVGMediaObject from the SVG file identified by media_id,
        and the parent Scene referenced by scene.

        Creates a QSvgRenderer and attempts to load the SVG file.
        Raises LoadError if the SVG file cannot be parsed.

        Stores the default width and height of the SVG image for rendering
        calculations.
        """
        # Initialize the parent MediaObject with media_id and scene reference
        # This sets up self._media_id, self._scene, and PhysicalObject attributes
        MediaObject.__init__(self, media_id, scene)

        # Create a QSvgRenderer instance to parse and render SVG content
        # QSvgRenderer handles SVG parsing, animation, and rendering onto QPainter
        self.__renderer: QtSvg.QSvgRenderer = QtSvg.QSvgRenderer()

        # Determine if media_id is a cache hash or file path
        load_path = self.__get_svg_load_path(media_id)

        # Attempt to load the SVG file
        # load() returns True on success, False if the file cannot be parsed
        if not self.__renderer.load(load_path):
            raise LoadError(f"unable to parse SVG file: {media_id}")

        # Get the default (intrinsic) size of the SVG image as a QSize object
        # defaultSize() returns the size specified in the SVG's width/height attributes
        size: QtCore.QSize = self.__renderer.defaultSize()

        # Extract the width in pixels from the QSize object
        # This is the SVG's native width before any scaling is applied
        self.__width: int = size.width()

        # Extract the height in pixels from the QSize object
        # This is the SVG's native height before any scaling is applied
        self.__height: int = size.height()

        # Initialize private variables for caching optimizations
        # These start as None and store computed values when first accessed

        # Stores the scale value (2^(scene.zoomlevel + object.zoomlevel))
        self.__cached_scale: float | None = None

        # Stores the calculated (width, height) tuple for this SVG at current scale
        self.__cached_onscreen_size: tuple[float, float] | None = None

        # Track modification state and cache SVG content
        self.__logger = get_logger("SVGMediaObject")

        # Track if SVG has been modified (picker, clipboard, or svg_*_utils)
        self.__is_modified: bool = False

        # Cache SVG content in memory for performance
        self.__cached_svg_content: str | None = None

        # Store original file path for file-based SVGs
        self.__original_file_path: str | None = None
        if not media_id.startswith("svg_"):
            # It's a file path, not cache hash
            self.__original_file_path = media_id
        else:
            # Cache hash - mark as modified (from picker/clipboard)
            self.__is_modified = True

    # Class variable: indicates this media object supports transparency
    # SVG images can have transparent backgrounds, so they cannot hide objects behind them
    transparent: bool = True

    # Maximum SVG size for embedding warning (1MB)
    MAX_EMBEDDED_SVG_SIZE_BYTES: int = 1 * 1024 * 1024

    def render(self, painter: Any, mode: int) -> None:
        """
        Method :
            SVGMediaObject.render(painter, mode)
        Parameters :
            painter : QPainter
            mode : int

        SVGMediaObject.render(painter, mode) --> None

        Render the SVG image using the given painter and render mode.

        Note: Size visibility is checked by the scene via is_size_visible().
        """
        # Get top-left corner position of the SVG object on screen
        # self.topleft is a property that returns tuple (x, y) in screen coordinates
        x: float
        y: float
        x, y = self.topleft

        # Get the on-screen dimensions of the SVG at current scale
        # onscreen_size returns (width, height) scaled by the current zoom level
        w: float
        h: float
        w, h = self.onscreen_size

        # Render the SVG into a floating-point rectangle on the painter
        # QtCore.QRectF(x, y, width, height) defines the target rendering area
        # QSvgRenderer.render() scales the SVG vector graphics to fit the rectangle
        self.__renderer.render(painter, QtCore.QRectF(x, y, w, h))

    def is_size_visible(self, mode: int) -> bool:
        """
        SVG-specific size visibility check.

        Returns False if SVG is too small or too large to be visible,
        otherwise returns super().is_size_visible(mode).
        """
        # First check base class (handles Invisible mode)
        if not super().is_size_visible(mode):
            return False

        # SVG-specific size checks (same thresholds as current render())
        w, h = self.onscreen_size
        viewport_w, viewport_h = self._scene.viewport_size

        # Check if too small: min dimension > viewport_min / 55
        not_too_small = min(w, h) > int((min(viewport_w, viewport_h)) / 55)

        # Check if too large: max dimension < viewport_max / 0.5
        not_too_large = max(w, h) < int((max(viewport_w, viewport_h)) / 0.5)

        return not_too_small and not_too_large

    @property
    def onscreen_size(self) -> tuple[float, float]:
        """
        Property :
            SVGMediaObject.onscreen_size
        Parameters :
            None

        SVGMediaObject.onscreen_size --> Tuple[float, float]

        Return the on-screen size of the SVG image.

        Multiplies the SVG's native width and height by the current scale factor.
        The scale factor is derived from the combined scene and object zoom levels.

        Uses caching to avoid recalculating size on every access.
        """
        current_scale: float = self.scale

        # Return cached size if scale hasn't changed
        if self.__cached_scale == current_scale and self.__cached_onscreen_size is not None:
            return self.__cached_onscreen_size

        # Calculate on-screen dimensions by multiplying native pixel size by scale
        # self.scale returns 2^(scene.zoomlevel + object.zoomlevel)
        # self.__width and self.__height are the SVG's intrinsic dimensions
        w: float = self.__width * current_scale
        h: float = self.__height * current_scale

        # Update cache
        self.__cached_scale = current_scale
        self.__cached_onscreen_size = (w, h)
        return (w, h)

    @property
    def is_modified(self) -> bool:
        """Check if SVG has been modified."""
        return self.__is_modified

    def mark_as_modified(self) -> None:
        """Mark SVG as modified (e.g., after svg_*_utils modification)."""
        self.__is_modified = True
        # Clear cached content since it will change
        self.__cached_svg_content = None

    @property
    def original_file_path(self) -> str | None:
        """Get original file path if SVG was loaded from file."""
        return self.__original_file_path

    def get_svg_content(self) -> str | None:
        """
        Get current SVG content with caching.
        Returns None if content cannot be retrieved.
        """
        # Return cached content if available
        if self.__cached_svg_content is not None:
            return self.__cached_svg_content

        # Get content from cache or file
        if self._media_id.startswith("svg_"):
            # Cache hash - get from SVG cache
            svg_cache = get_svg_cache()
            content = svg_cache.get_svg_content(self._media_id)
        else:
            # File path - read from file
            try:
                content = Path(self._media_id).read_text(encoding="utf-8")
            except Exception as e:
                self.__logger.error(f"Failed to read SVG file {self._media_id}: {e}")
                content = None

        # Cache the content
        if content is not None:
            self.__cached_svg_content = content

        return content

    def set_svg_content(self, content: str) -> None:
        """Set SVG content (for embedded SVGs on load)."""
        self.__cached_svg_content = content
        self.__is_modified = True

    def to_dict(self) -> dict[str, Any]:
        """
        Method :
            SVGMediaObject.to_dict()
        Parameters :
            None

        SVGMediaObject.to_dict() --> Dict[str, Any]

        Serialize SVGMediaObject with SVG-specific state.
        """
        data = super().to_dict()
        data.update(
            {
                "width": self.__width,
                "height": self.__height,
                "transparent": self.transparent,
                "is_modified": self.__is_modified,
                "original_file_path": self.__original_file_path if self.__original_file_path else "",
            }
        )
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any], scene: Any) -> "SVGMediaObject":
        """
        Method :
            SVGMediaObject.from_dict(data, scene)
        Parameters :
            data : Dict[str, Any]
            scene : Any

        SVGMediaObject.from_dict(data, scene) --> SVGMediaObject

        Create SVGMediaObject from serialized data.
        """
        obj = cls(data["media_id"], scene)
        obj._x, obj._y, obj._z = data["position"]
        obj.vx, obj.vy, obj.vz = data["velocity"]

        # Restore modification state if present
        if "is_modified" in data:
            obj.__is_modified = data["is_modified"]

        # Restore original file path if present
        if data.get("original_file_path"):
            obj.__original_file_path = data["original_file_path"]

        return obj
