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

"""Class for representing image tiles."""

from typing import Optional, Tuple, List, Any
from PIL import Image, ImageQt
from PySide6 import QtCore, QtGui

class Tile(object):
    """
    Constructor:
        Tile(image)
    Parameters :
        image : QImage

    Tile(image) --> None

    A simple wrapper around image data (PIL/QImage) with operations:
        - crop(), resize(), save(), draw()
        - merged() - Combines 4 tiles into one (2×2 grid layout)

    """
    def __init__(self, image: Any) -> None:

        """
        Create a new tile with the given image.
        checks if image type is ImageQt of QtGui.QImage if not calls
        ImageQt.ImageQt to try convert given image to ImageQt type.
        """
        if image.__class__ is ImageQt or type(image) is QtGui.QImage:
            self.__image = image
            
        else:
            try :
                self.__image = ImageQt.ImageQt(image)
            except Exception as e :
                print('ERROR on tile __init__ \n', e)
                

            


    def crop(self, bbox: Tuple[int, int, int, int]) -> 'Tile':
        """
        Method :
            Tile.crop(bbox)
        Parameters :
            bbox : Tuple[int, int, int, int]

        Tile.crop(bbox) --> Tile

        Return the region of the tile contained in the bounding box `bbox`
        (x1,y1,x2,y2).
        """
        x, y, x2, y2 = bbox
        w = x2 - x
        h = y2 - y
        
        return Tile(self.__image.copy(int(x), int(y), int(w), int(h)))


    def resize(self, width: int, height: int) -> 'Tile':
        """
        Method :
            Tile.resize(width, height)
        Parameters :
            width : int
            height : int

        Tile.resize(width, height) --> Tile

        Return a resized copy of the tile by calling ImageQt.scaled() method.
        """
        return Tile(self.__image.scaled(int(width), int(height),
            QtCore.Qt.IgnoreAspectRatio,
            QtCore.Qt.FastTransformation))


    def save(self, filename: str) -> None:
        """
        Method :
            Tile.save(filename)
        Parameters :
            filename : str

        Tile.save(filename) --> None

        Save the tile to the location given by `filename` calling ImageQt.save()
        method.
        """
        self.__image.save(filename)


    def draw(self, painter: 'QtGui.QPainter', x: int, y: int) -> None:
        """
        Method :
            Tile.draw(painter, x, y)
        Parameters :
            painter : QPainter
            x : int
            y : int

        Tile.draw(painter, x, y) --> None

        Draw the tile on the given painter: 'QtGui.QPainter' at the given position.
        """
        painter.drawImage(x, y, self.__image)


    @property
    def size(self) -> Tuple[int, int]:
        """
        Property :
            Tile.size
        Parameters :
            None

        Tile.size --> Tuple[int, int]

        Returns the dimensions of the tile calling ImageQt.width and ImageQt.height 
        methods.
        """
        return (self.__image.width(), self.__image.height())



def new(width: int, height: int) -> Tile:
    """
    Function :
        new(width, height)
    Parameters :
        width : int
        height : int

    new(width, height) --> Tile

    Create a new tile with the given dimensions calling QtGui.QImage() istance.
    """
    return Tile(QtGui.QImage(width, height, QtGui.QImage.Format_RGB32))


def fromstring(string: str, width: int, height: int) -> Tile:
    """
    Function :
        fromstring(string, width, height)
    Parameters :
        string : str
        width : int
        height : int

    fromstring(string, width, height) --> Tile

    Create a new tile from a `string` of raw pixels, with the given
    dimensions, calling Image.frombytes() class instance.
    """
      
    return Tile(Image.frombytes('RGB', (width, height), string.encode('latin-1')))


def merged(t1: Tile, t2: Optional[Tile], t3: Optional[Tile], t4: Optional[Tile]) -> Tile:
    """
    Function :
        merged(t1, t2, t3, t4)
    Parameters :
        t1 : Tile
        t2 : Optional[Tile]
        t3 : Optional[Tile]
        t4 : Optional[Tile]

    merged(t1, t2, t3, t4) --> Tile

    Merge the given tiles into a single tile by freating new size ImageQt with
    QtGui.QImage class instance and then drawing merged tiles with QtGui.QPainter()
    class instance.

    `t1` must be a Tile, but any or all of `t2`,`t3`,`t4` may be None, in which
    case they will be ignored.
    """

    ## tiles are merged in the following layout:
    ## +---------+
    ## | t1 | t2 |
    ## |----+----|
    ## | t3 | t4 |
    ## +---------+

    tilewidth, tileheight = t1.size
    if t2: tilewidth  += t2.size[0]
    if t3: tileheight += t3.size[1]

    painter = QtGui.QPainter()
    image = QtGui.QImage(tilewidth, tileheight, QtGui.QImage.Format_RGB32)
    painter.begin(image)

    if t1: t1.draw(painter, 0,          0         )
    if t2: t2.draw(painter, t1.size[0], 0         )
    if t3: t3.draw(painter, 0,          t1.size[1])
    if t4: t4.draw(painter, t1.size[0], t1.size[1])

    painter.end()

    return Tile(image)
