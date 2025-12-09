## PyZUI 0.1 - Python Zooming User Interface
## Copyright (C) 2009  David Roberts <d@vidr.cc>
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
## 02110-1301, USA.

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
        MediaObject.__init__(self, media_id, scene)

        self.__renderer = QtSvg.QSvgRenderer()
        if not self.__renderer.load(self._media_id):
            raise LoadError("unable to parse SVG file")

        size = self.__renderer.defaultSize()
        self.__width = size.width()
        self.__height = size.height()


    transparent = True

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
        if min(self.onscreen_size) > int((min(self._scene.viewport_size))/44) and \
        max(self.onscreen_size) < int((max(self._scene.viewport_size))/1.3) and mode \
        != RenderMode.Invisible:
            ## don't bother rendering if the string is too
            ## small to be seen, or invisible mode is set

            x,y = self.topleft
            w,h = self.onscreen_size
            self.__renderer.render(painter, QtCore.QRectF(x,y,w,h))


    @property
    def onscreen_size(self) -> Tuple[float, float]:
        """
        Property :
            SVGMediaObject.onscreen_size
        Parameters :
            None

        SVGMediaObject.onscreen_size --> Tuple[float, float]

        Return the on-screen size of the SVG image.
        """
        return (self.__width * self.scale, self.__height * self.scale)
