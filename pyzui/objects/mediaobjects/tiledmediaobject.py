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

"""Tiled media to be displayed in the ZUI."""

import tempfile
import os
import math
from typing import Tuple, Any

from PySide6 import QtCore, QtGui

from pyzui.objects.mediaobjects.mediaobject import MediaObject, LoadError, RenderMode
from pyzui.tilesystem import tilemanager as TileManager
from pyzui.logger import get_logger

# Subdivide a ppm image into tiles that fit the mediaobject frame
from pyzui.tilesystem.tiler.ppm import PPMTiler

# Process-based conversion for parallel media conversion
from pyzui.converters import converter_runner

class TiledMediaObject(MediaObject):
    """
    Constructor :
        TiledMediaObject(media_id, scene, autofit)
    Parameters :
        media_id : str
        scene : Scene
        autofit : bool

    TiledMediaObject(media_id, scene, autofit) --> None

    TileMedia object wraps given media_id in MediaObject type,
    (calling converter if necessary) so that it can be
    rendered in the ZUI.

    If `autofit` is True, then once the media has loaded it will be fitted to
    the area occupied by the placeholder.

    Supported formats:
    - PDF files (.pdf) via PDFConverter
    - PPM files (.ppm) used directly
    - Image files (JPG, PNG, GIF, TIFF, etc.) via VipsConverter

    For any acceptable filetype the adequate converter gets called.
    The converter returns a ppm image file on which we can run the tiler on.
    """
    def __init__(self, media_id: str, scene: Any, autofit: bool = True) -> None:
        """
        Constructor :
            TiledMediaObject(media_id, scene, autofit)
        Parameters :
            media_id : str
            scene : Scene
            autofit : bool (default=True)

        TiledMediaObject(media_id, scene, autofit) --> None

        Initialize a new TiledMediaObject from the media identified by media_id,
        the parent Scene referenced by scene, and optionally autofit behavior.

        If autofit is True, once the media has loaded it will be fitted to
        the area occupied by the placeholder.

        Sets up conversion and tiling infrastructure based on the media file type.
        Initializes caching variables for tileblocks and rendering optimization.
        """
        MediaObject.__init__(self, media_id, scene)

        self.__autofit = autofit

        self.__loaded = False

        self.__tmpfile = None

        self.__converter = None
        self.__tiler = None

        self.__logger = get_logger(f'TiledMediaObject.{media_id}')

        self.__maxtilelevel = 0
        self.__width, self.__height = self.default_size
        self.__aspect_ratio = None

        ## for caching tileblocks
        self.__tileblock = None
        self.__tileblock_id = None
        self.__tileblock_final = False
        self.__tileblock_age = 0
        
        #print('tiledmediaobject-70-TileManager.tiled(self._media_id):',TileManager.tiled(self._media_id))
        
        if TileManager.tiled(self._media_id):
            #print(self._media_id)
            TileManager.load_tile((self._media_id, 0, 0, 0))

        else:
            #print('tiledmediaobject-75-need-to-tile', self._media_id)
            self.__logger.info("need to tile media")
            fd, self.__tmpfile = tempfile.mkstemp('.ppm')
            os.close(fd)

            if self._media_id.lower().endswith('.pdf'):
                # Use process-based PDF conversion
                future = converter_runner.submit_pdf_conversion(
                    self._media_id, self.__tmpfile)
                self.__converter = converter_runner.ConversionHandle(
                    future, self._media_id, self.__tmpfile)
                self.__ppmfile = self.__tmpfile
            elif self._media_id.lower().endswith('.ppm'):
                ## assume media_id is a local PPM file
                self.__logger.info(
                    "assuming media is a local PPM file")
                self.__ppmfile = self._media_id

            else:
                # Use process-based Vips conversion
                future = converter_runner.submit_vips_conversion(
                    self._media_id, self.__tmpfile)
                self.__converter = converter_runner.ConversionHandle(
                    future, self._media_id, self.__tmpfile)
                self.__ppmfile = self.__tmpfile
            

    transparent = False

    ## initial size of the object before the actual dimensions have been
    ## loaded
    default_size = (256,256)

    ## maximum number of cycles to cache temporary tiles for
    tempcache = 5

    @property
    def __progress(self) -> float:
        """
        Property :
            __progress
        Parameters :
            None

        __progress --> float

        Calculate and return the current loading progress as a float
        between 0.0 and 1.0.

        If only tiler is active, returns tiler progress.
        If only converter is active, returns half of converter progress.
        If both are active, returns average of both progresses.
        """
        if self.__converter is None and self.__tiler is None:
            return 0.0
        elif self.__converter is None:
            return self.__tiler.progress
        elif self.__tiler is None:
            return 0.5 * self.__converter.progress
        else:
            return 0.5 * (self.__converter.progress + self.__tiler.progress)

    def __pixpos2rowcol(self, pixpos: Tuple[float, float], tilescale: float) -> Tuple[int, int]:
        """
        Method :
            __pixpos2rowcol(pixpos, tilescale)
        Parameters :
            pixpos : Tuple[float, float]
            tilescale : float

        __pixpos2rowcol(pixpos, tilescale) --> Tuple[int, int]

        Convert the on-screen pixel position to a (row,col) tile
        position.
        """
        o = self.topleft
        col = int((pixpos[0]-o[0]) / (tilescale*self.__tilesize))
        row = int((pixpos[1]-o[1]) / (tilescale*self.__tilesize))
        return (row,col)

    def __rowcol_bound(self, tilelevel: int) -> Tuple[int, int]:
        """
        Method :
            __rowcol_bound(tilelevel)
        Parameters :
            tilelevel : int

        __rowcol_bound(tilelevel) --> Tuple[int, int]

        Return the maximum row and column for the given tilelevel.
        """
        if tilelevel <= 0:
            row_bound = col_bound = 0
        elif self.__aspect_ratio:
            if self.__aspect_ratio >= 1.0:
                ## width >= height
                col_bound = 2**tilelevel - 1
                row_bound = int((2**tilelevel)/self.__aspect_ratio) - 1
            else:
                ## height > width
                col_bound = int((2**tilelevel)*self.__aspect_ratio) - 1
                row_bound = 2**tilelevel - 1
        else:
            tile_pixsize = self.__tilesize \
                * 2 ** (self.__maxtilelevel - tilelevel)
            row_bound = int((self.__height - 1) / tile_pixsize)
            col_bound = int((self.__width  - 1) / tile_pixsize)

        return row_bound, col_bound

    def __render_tileblock(self, tileblock_id: Tuple[int, int, int, int, int], mode: int) -> Any:
        """
        Method :
            __render_tileblock(tileblock_id, mode)
        Parameters :
            tileblock_id : Tuple[int, int, int, int, int]
            mode : int

        __render_tileblock(tileblock_id, mode) --> QImage

        Render, cache, and return the tileblock given the unique
        tileblock_id and render mode.

        Precondition: mode is equal to either :attr:`RenderMode.Draft` or
        :attr:`RenderMode.HighQuality`
        """
        
        self.__logger.debug("rendering tileblock")
        
        
        tilelevel, row_min, col_min, row_max, col_max = tileblock_id

        brtile = TileManager.get_tile_robust(
            (self._media_id, tilelevel, row_max, col_max))
        w = self.__tilesize * (col_max - col_min) + brtile.size[0]
        h = self.__tilesize * (row_max - row_min) + brtile.size[1]
        tileblock = QtGui.QImage(w, h, QtGui.QImage.Format_RGB32)

        tileblock_painter = QtGui.QPainter()
        tileblock_painter.begin(tileblock)

        tileblock_final = True

        for row in range(row_min, row_max+1):
            for col in range(col_min, col_max+1):
                tile_id = (self._media_id, tilelevel, row, col)
                try:
                    tile = TileManager.get_tile(tile_id)
                except TileManager.TileNotLoaded:
                    tileblock_final = False
                    if mode == RenderMode.HighQuality:
                        tile = TileManager.cut_tile(tile_id)[0]
                    else:
                        tile = TileManager.cut_tile(tile_id, self.tempcache)[0]
                except TileManager.TileNotAvailable:
                    if mode == RenderMode.HighQuality:
                        tile, final = TileManager.cut_tile(tile_id)
                    else:
                        tile, final = TileManager.cut_tile(tile_id,
                                                           self.tempcache)
                    if not final: tileblock_final = False
                x = self.__tilesize * (col-col_min)
                y = self.__tilesize * (row-row_min)
                tile.draw(tileblock_painter, x, y)

        tileblock_painter.end()

        del self.__tileblock
        self.__tileblock = tileblock
        self.__tileblock_id = tileblock_id
        self.__tileblock_final = tileblock_final
        self.__tileblock_age = 0

        return tileblock

    def __render_media(self, painter: Any, mode: int) -> None:
        """
        Method :
            __render_media(painter, mode)
        Parameters :
            painter : QPainter
            mode : int

        __render_media(painter, mode) --> None

        Render the media using the given painter and render mode.

        Precondition: mode is equal to one of the constants defined in
        :class:`RenderMode`
        """
        
        if min(self.onscreen_size) <= 1 or mode == RenderMode.Invisible:
            ## don't bother rendering if the image is too
            ## small to be seen, or invisible mode is set
            return
        if mode == RenderMode.Draft:
            transform_mode = QtCore.Qt.FastTransformation
        elif mode == RenderMode.HighQuality:
            transform_mode = QtCore.Qt.FastTransformation

        viewport_size = self._scene.viewport_size

        zoomlevel = self.zoomlevel + self._scene.zoomlevel
        tilelevel = int(math.ceil(zoomlevel))
        tilescale = 2 ** (zoomlevel - tilelevel)

        row_min,col_min = self.__pixpos2rowcol((0,0),        tilescale)
        row_max,col_max = self.__pixpos2rowcol(viewport_size,tilescale)

        row_min = max(row_min, 0)
        col_min = max(col_min, 0)

        row_bound, col_bound = self.__rowcol_bound(tilelevel)
        row_max = min(row_max, row_bound)
        col_max = min(col_max, col_bound)

        if row_max < row_min or col_max < col_min:
            ## the image does not fall within the viewport
            return

        tileblock_id = (tilelevel, row_min, col_min, row_max, col_max)

        if (self.__tileblock_id != tileblock_id) or \
           (not self.__tileblock_final and \
            (mode == RenderMode.HighQuality or \
             self.__tileblock_age >= self.tempcache)):
            ## the cached tileblock is different to the required
            ## one, so we have draw the new tileblock
            ## we also re-render the tileblock if it is not final
            ## and either we are in HQ mode or the tileblock
            ## is at least self.tempcache cycles old
            tileblock = self.__render_tileblock(tileblock_id, mode)
        else:
            tileblock = self.__tileblock
            self.__tileblock_age += 1

        image_scaled = tileblock.scaled(
            int(tilescale * tileblock.width()),
            int(tilescale * tileblock.height()),
            QtCore.Qt.IgnoreAspectRatio,
            transform_mode)

        o = self.topleft
        x = o[0] + int(tilescale * self.__tilesize*col_min)
        y = o[1] + int(tilescale * self.__tilesize*row_min)
        
        painter.drawImage(int(x), int(y), image_scaled)

    def __render_placeholder(self, painter: Any) -> None:
        """
        Method :
            __render_placeholder(painter)
        Parameters :
            painter : QPainter

        __render_placeholder(painter) --> None

        Render a placeholder indicating that the image is still loading,
        using the given painter.
        """
        x,y = self.topleft
        w,h = self.onscreen_size

        try:
            painter.fillRect(x, y, w, h, QtCore.Qt.darkGray) #darkGray
        except TypeError:
            ## rectangle dimensions could not be converted to ints
            pass
        else:
            if self.__progress > 0:
                painter.setPen(QtGui.QColor(255,255,255))
                font = QtGui.QFont()
                font.setPointSizeF(w/4)
                painter.setFont(font)
                painter.drawText(x, y, w, h, QtCore.Qt.AlignCenter,
                    str(int(self.__progress*100)) + '%')
            else:
                painter.setPen(QtGui.QColor(255,255,255))
                font = QtGui.QFont()
                font.setPointSizeF(w/10)
                painter.setFont(font)
                painter.drawText(x, y, w, h, QtCore.Qt.AlignCenter,
                    "loading...")

    def __try_load(self) -> None:
        """
        Method :
            __try_load()
        Parameters :
            None

        __try_load() --> None

        Try to load the (0,0,0) tile from the TileManager.
        """
        
        try:
            TileManager.get_tile(
                (self._media_id, 0, 0, 0))
        except TileManager.TileNotLoaded:
            self.__logger.info("(0,0,0) tile not loaded yet")
            pass
        except (TileManager.MediaNotTiled,
            TileManager.TileNotAvailable):
            raise LoadError("unable to correctly tile the image")
        else:
            self.__logger.info("media loaded")
            self.__loaded = True

            if self.__tiler:
                ## destory tiler to close tmpfile (reqd to unlink on Windows)
                self.__tiler = None

            if os.name == 'nt' : #self.__tmpfile
                try:
                    os.unlink(self.__tmpfile)
                except:
                    self.__logger.exception("unable to unlink temporary file "
                        "'%s'" % self.__tmpfile)

            old_x1, old_y1 = self.topleft
            old_x2, old_y2 = self.bottomright
            old_centre = self.centre

            self.__width = TileManager.get_metadata(
                self._media_id, 'width')
            self.__height = TileManager.get_metadata(
                self._media_id, 'height')
            self.__maxtilelevel = TileManager.get_metadata(
                self._media_id, 'maxtilelevel')
            self.__tilesize = TileManager.get_metadata(
                self._media_id, 'tilesize')
            self.__aspect_ratio = TileManager.get_metadata(
                self._media_id, 'aspect_ratio')

            if self.__autofit:
                ## fit to area occupied by placeholder
                self.fit((old_x1, old_y1, old_x2, old_y2))
                self.centre = old_centre

    def __run_tiler(self) -> None:
        """
        Method :
            __run_tiler()
        Parameters :
            None

        __run_tiler() --> None

        Run the tiler (after checking that there is an image to run
        the tiler on).
        """
        
        if not os.path.exists(self.__ppmfile):

            ## there was a problem converting, or the input file
            ## never actually existed
            if self.__converter and self.__converter.error:
                raise LoadError(self.__converter.error)
            else:
                raise LoadError("there was a problem "
                    "converting and/or loading the input file")

        if self._media_id.lower().endswith('.jpg'):
            filext = 'jpg'
        else:
            filext = 'png'

        try:
            self.__tiler = PPMTiler(self.__ppmfile, self._media_id, filext)
            self.__tiler.start()
            
        except IOError :
            raise LoadError("there was an error creating the tiler: %s")

    def render(self, painter: Any, mode: int) -> None:
        """
        Method :
            TiledMediaObject.render(painter, mode)
        Parameters :
            painter : QPainter
            mode : int

        TiledMediaObject.render(painter, mode) --> None

        Render the tiled media using the given painter and rendering mode.

        If the media is loaded, renders the actual media content.
        Otherwise, renders a placeholder showing loading progress.

        Handles tiler initialization if converter has finished but tiler
        hasn't started yet.

        Precondition: mode is equal to one of the constants defined in
        :class:`RenderMode`
        """

        if self.__loaded:
            self.__render_media(painter, mode)

        elif self.__tiler and self.__tiler.error:
            
            self.__logger.exception("an error ocurred during "
                "the tiling process: %s" % self.__tiler.error)
            #raise LoadError("an error ocurred during "
            #    "the tiling process: %s" % self.__tiler.error)
        
        if TileManager.tiled(self._media_id): #replaced elif with if
            
            self.__try_load()
            if self.__loaded:
                
                self.__render_media(painter, mode)
            else:
                self.__render_placeholder(painter)

        elif self.__tiler is None and \
             (self.__converter is None or self.__converter.progress == 1.0):
            ## the tiler has not been run yet and either
            ## it was assumed that media_id is a local PPM
            ## file or the converter has just finished

            self.__run_tiler()
            self.__render_placeholder(painter)

        else:
            self.__render_placeholder(painter)

    @property
    def onscreen_size(self) -> Tuple[float, float]:
        """
        Property :
            TiledMediaObject.onscreen_size
        Parameters :
            None

        TiledMediaObject.onscreen_size --> Tuple[float, float]

        Return the on-screen size of the tiled media.

        Calculates the width and height based on aspect ratio if available,
        otherwise uses the actual width and height scaled by zoom levels.

        Returns (0,0) if the media dimensions are not yet known.
        """
        if self.__aspect_ratio:
            if self.__aspect_ratio >= 1.0:
                ## width >= height
                w = 2**(self._scene.zoomlevel+self.zoomlevel) * self.__tilesize
                h = w / self.__aspect_ratio
            else:
                ## height > width
                h = 2**(self._scene.zoomlevel+self.zoomlevel) * self.__tilesize
                w = h * self.__aspect_ratio
            return (w,h)
        elif self.__width == 0 or self.__height == 0:
            return (0,0)
        else:
            scale = 2 ** (self._scene.zoomlevel + self.zoomlevel \
                - self.__maxtilelevel)
            w = self.__width * scale
            h = self.__height * scale
            return (w,h)
