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

"""SVG objects to be displayed in the ZUI."""

from typing import Tuple, Any

from PySide6 import QtCore, QtSvg

from .mediaobject import MediaObject, LoadError, RenderMode

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
    def __init__(self, media_id: str, scene: Any) -> None:
        """
        Constructor :
            SVGMediaObject(media_id, scene)
        Parameters :
            media_id : str
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

        # Attempt to load the SVG file from the path stored in self._media_id
        # load() returns True on success, False if the file cannot be parsed
        if not self.__renderer.load(self._media_id):
            raise LoadError("unable to parse SVG file")

        # Get the default (intrinsic) size of the SVG image as a QSize object
        # defaultSize() returns the size specified in the SVG's width/height attributes
        size: QtCore.QSize = self.__renderer.defaultSize()

        # Extract the width in pixels from the QSize object
        # This is the SVG's native width before any scaling is applied
        self.__width: int = size.width()

        # Extract the height in pixels from the QSize object
        # This is the SVG's native height before any scaling is applied
        self.__height: int = size.height()

    # Class variable: indicates this media object supports transparency
    # SVG images can have transparent backgrounds, so they cannot hide objects behind them
    transparent: bool = True

    def render(self, painter: Any, mode: int) -> None:
        """
        Method :
            SVGMediaObject.render(painter, mode)
        Parameters :
            painter : QPainter
            mode : int

        SVGMediaObject.render(painter, mode) --> None

        Render the SVG image using the given painter and render mode.
        """
        # Visibility check: only render if the SVG is appropriately sized for the viewport
        # self._scene.viewport_size is a tuple (viewport_width, viewport_height)
        # Checks: image not too small (>viewport_min/44) AND not too large (<viewport_max/1.3) AND not invisible
        if min(self.onscreen_size) > int((min(self._scene.viewport_size))/44) and \
        max(self.onscreen_size) < int((max(self._scene.viewport_size))/1.3) and mode \
        != RenderMode.Invisible:
            ## don't bother rendering if the string is too
            ## small to be seen, or invisible mode is set

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

    @property
    def onscreen_size(self) -> Tuple[float, float]:
        """
        Property :
            SVGMediaObject.onscreen_size
        Parameters :
            None

        SVGMediaObject.onscreen_size --> Tuple[float, float]

        Return the on-screen size of the SVG image.

        Multiplies the SVG's native width and height by the current scale factor.
        The scale factor is derived from the combined scene and object zoom levels.
        """
        # Calculate on-screen dimensions by multiplying native pixel size by scale
        # self.scale returns 2^(scene.zoomlevel + object.zoomlevel)
        # self.__width and self.__height are the SVG's intrinsic dimensions
        w: float = self.__width * self.scale
        h: float = self.__height * self.scale
        return (w, h)
