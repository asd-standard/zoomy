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
import logging
from typing import Optional, Tuple, Any

from PySide6 import QtCore, QtGui

from pyzui.objects.mediaobjects.mediaobject import MediaObject, LoadError, RenderMode
from pyzui.tilesystem import tilemanager as TileManager
from pyzui.logger import get_logger

# Subdivide a ppm image into tiles that fit the mediaobject frame
from pyzui.tilesystem.tiler.ppm import PPMTiler

# Process-based conversion for parallel media conversion
from pyzui.converters import converterrunner

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
        # Initialize the parent MediaObject with media_id and scene reference
        # This sets up self._media_id, self._scene, and PhysicalObject attributes
        MediaObject.__init__(self, media_id, scene)

        # Store whether the media should auto-fit to the placeholder area once loaded
        # When True, the loaded image will be resized to fill the placeholder bounding box
        self.__autofit: bool = autofit

        # Flag indicating whether the tile data has been fully loaded from TileManager
        # Starts as False; set to True in __try_load() once the (0,0,0) tile is available
        self.__loaded: bool = False

        # Path to the temporary PPM file created during conversion
        # Set to None initially; assigned a tempfile path if conversion is needed
        self.__tmpfile: Optional[str] = None

        # Reference to the active ConversionHandle (wraps a Future from process pool)
        # None if no conversion is needed (e.g., already tiled or is a .ppm file)
        self.__converter: Optional[converterrunner.ConversionHandle] = None

        # Reference to the PPMTiler instance that subdivides PPM images into tiles
        # None until __run_tiler() is called after conversion completes
        self.__tiler: Optional[PPMTiler] = None

        # Logger instance for this specific TiledMediaObject, named with the media_id
        # Used for debug/info/error logging throughout the object's lifecycle
        self.__logger: logging.Logger = get_logger(f'TiledMediaObject.{media_id}')

        # Maximum tile level (zoom depth) for this media
        # Initialized to 0; updated from TileManager metadata once tiles are loaded
        self.__maxtilelevel: int = 0

        # Width and height of the media in pixels
        # Initialized to default_size (256, 256); updated from TileManager metadata once loaded
        self.__width: int
        self.__height: int
        self.__width, self.__height = self.default_size

        # Aspect ratio of the media (width / height)
        # None until loaded from TileManager metadata; used for efficient size calculations
        self.__aspect_ratio: Optional[float] = None

        ## for caching tileblocks
        # The cached QImage containing the rendered tileblock
        # Reused across frames if the visible tile region hasn't changed
        self.__tileblock: Optional[QtGui.QImage] = None

        # Tuple identifying the cached tileblock: (tilelevel, row_min, col_min, row_max, col_max)
        # Used to determine if the cache is still valid for the current view
        self.__tileblock_id: Optional[Tuple[int, int, int, int, int]] = None

        # Whether the cached tileblock contains all final (fully loaded) tiles
        # If False, the tileblock may need re-rendering when higher quality tiles become available
        self.__tileblock_final: bool = False

        # Number of render cycles since the tileblock was last re-rendered
        # Compared against self.tempcache to decide when to refresh non-final tileblocks
        self.__tileblock_age: int = 0

        # Check if TileManager already has tiles for this media_id
        # TileManager.tiled() returns True if the media has already been tiled and stored
        if TileManager.tiled(self._media_id):
            # Media is already tiled; request loading of the root tile (level=0, row=0, col=0)
            # This triggers the TileManager to begin loading tile data from disk
            TileManager.load_tile((self._media_id, 0, 0, 0))

        else:
            # Media has not been tiled yet; needs conversion and/or tiling
            self.__logger.info("need to tile media")

            # Create a temporary file with .ppm extension for the converter output
            # tempfile.mkstemp() returns (file_descriptor, file_path)
            fd: int
            fd, self.__tmpfile = tempfile.mkstemp('.ppm')

            # Close the file descriptor immediately; the converter will open the file itself
            os.close(fd)

            # Determine which converter to use based on file extension
            if self._media_id.lower().endswith('.pdf'):
                # PDF files: submit to process pool for PDF-to-PPM conversion
                # submit_pdf_conversion() returns a Future object
                future: Any = converterrunner.submit_pdf_conversion(
                    self._media_id, self.__tmpfile)

                # Wrap the Future in a ConversionHandle for progress/error tracking
                self.__converter = converterrunner.ConversionHandle(
                    future, self._media_id, self.__tmpfile)

                # Store path to the PPM file that the converter will produce
                self.__ppmfile: str = self.__tmpfile

            elif self._media_id.lower().endswith('.ppm'):
                ## assume media_id is a local PPM file
                # No conversion needed; the media_id itself is the PPM file path
                self.__logger.info(
                    "assuming media is a local PPM file")
                self.__ppmfile: str = self._media_id

            else:
                # All other image formats (JPG, PNG, GIF, TIFF, etc.): use Vips conversion
                # submit_vips_conversion() returns a Future object
                future: Any = converterrunner.submit_vips_conversion(
                    self._media_id, self.__tmpfile)

                # Wrap the Future in a ConversionHandle for progress/error tracking
                self.__converter = converterrunner.ConversionHandle(
                    future, self._media_id, self.__tmpfile)

                # Store path to the PPM file that the converter will produce
                self.__ppmfile: str = self.__tmpfile


    # Class variable: indicates this media object does NOT support transparency
    # Tiled images are fully opaque, so they can hide objects behind them
    transparent: bool = False

    ## initial size of the object before the actual dimensions have been
    ## loaded
    # Class variable: default placeholder dimensions (width, height) in pixels
    # Used until the actual media dimensions are loaded from TileManager metadata
    default_size: Tuple[int, int] = (256, 256)

    ## maximum number of cycles to cache temporary tiles for
    # Class variable: number of render cycles before non-final tileblocks are refreshed
    # After this many cycles, temporary (lower quality) tiles will be re-rendered
    tempcache: int = 5

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
        # If neither converter nor tiler has been created, progress is 0%
        if self.__converter is None and self.__tiler is None:
            return 0.0
        elif self.__converter is None:
            # Only tiler is active (e.g., PPM file that didn't need conversion)
            # Tiler progress represents the full 0.0-1.0 range
            return self.__tiler.progress
        elif self.__tiler is None:
            # Only converter is active (tiler hasn't started yet)
            # Converter progress is scaled to 0.0-0.5 range (first half of total progress)
            return 0.5 * self.__converter.progress
        else:
            # Both converter and tiler are active
            # Average both progresses: converter contributes 50%, tiler contributes 50%
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
        # Get the top-left corner of this media object on screen
        # self.topleft returns (x, y) tuple in screen coordinates
        o: Tuple[float, float] = self.topleft

        # Calculate column index: horizontal offset from object's left edge, divided by scaled tile size
        # (pixpos[0] - o[0]) gives the pixel distance from the object's left edge
        # Dividing by (tilescale * tilesize) converts that pixel distance to a tile column index
        col: int = int((pixpos[0] - o[0]) / (tilescale * self.__tilesize))

        # Calculate row index: vertical offset from object's top edge, divided by scaled tile size
        # (pixpos[1] - o[1]) gives the pixel distance from the object's top edge
        # Dividing by (tilescale * tilesize) converts that pixel distance to a tile row index
        row: int = int((pixpos[1] - o[1]) / (tilescale * self.__tilesize))

        return (row, col)

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
            # At tile level 0 or below, there is only one tile: (row=0, col=0)
            row_bound: int = 0
            col_bound: int = 0
        elif self.__aspect_ratio:
            # Aspect ratio is available (media has been loaded)
            # Use aspect ratio to calculate bounds more efficiently
            if self.__aspect_ratio >= 1.0:
                ## width >= height (landscape orientation)
                # At this tilelevel, there are 2^tilelevel columns
                col_bound = 2**tilelevel - 1

                # Rows are fewer because height < width; divide by aspect ratio
                row_bound = int((2**tilelevel) / self.__aspect_ratio) - 1
            else:
                ## height > width (portrait orientation)
                # Columns are fewer because width < height; multiply by aspect ratio
                col_bound = int((2**tilelevel) * self.__aspect_ratio) - 1

                # At this tilelevel, there are 2^tilelevel rows
                row_bound = 2**tilelevel - 1
        else:
            # Fallback: calculate bounds from actual pixel dimensions
            # tile_pixsize is the pixel size each tile covers at this tilelevel
            # Higher tilelevels have smaller tiles; maxtilelevel has tilesize pixels per tile
            tile_pixsize: int = self.__tilesize \
                * 2 ** (self.__maxtilelevel - tilelevel)

            # Calculate the maximum row/col by dividing total dimensions by tile pixel size
            # (self.__height - 1) ensures we get the correct last tile index
            row_bound = int((self.__height - 1) / tile_pixsize)
            col_bound = int((self.__width  - 1) / tile_pixsize)

        return row_bound, col_bound

    def __render_tileblock(self, tileblock_id: Tuple[int, int, int, int, int], mode: int) -> QtGui.QImage:
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

        # Unpack the tileblock_id tuple into its component values
        # tilelevel: the zoom level of tiles to render
        # row_min/col_min: top-left tile coordinates
        # row_max/col_max: bottom-right tile coordinates
        tilelevel: int
        row_min: int
        col_min: int
        row_max: int
        col_max: int
        tilelevel, row_min, col_min, row_max, col_max = tileblock_id

        # Get the bottom-right tile to determine its actual pixel dimensions
        # The bottom-right tile may be smaller than tilesize if the image doesn't divide evenly
        brtile: Any = TileManager.get_tile_robust(
            (self._media_id, tilelevel, row_max, col_max))

        # Calculate total pixel dimensions of the tileblock
        # Width: number of full tiles * tilesize + actual width of the rightmost tile
        w: int = self.__tilesize * (col_max - col_min) + brtile.size[0]

        # Height: number of full tiles * tilesize + actual height of the bottom tile
        h: int = self.__tilesize * (row_max - row_min) + brtile.size[1]

        # Create a new QImage to hold the assembled tileblock
        # Format_RGB32: 32-bit RGB format (0xffRRGGBB), no alpha channel
        tileblock: QtGui.QImage = QtGui.QImage(w, h, QtGui.QImage.Format_RGB32)

        # Create a QPainter to draw individual tiles onto the tileblock image
        tileblock_painter: QtGui.QPainter = QtGui.QPainter()

        # Begin painting on the tileblock QImage
        # QPainter.begin() must be called before any drawing operations
        tileblock_painter.begin(tileblock)

        # Track whether all tiles in the block are in their final (highest quality) state
        # Starts True; set to False if any tile is not yet fully loaded
        tileblock_final: bool = True

        # Iterate over every tile position in the rectangular region [row_min..row_max, col_min..col_max]
        for row in range(row_min, row_max + 1):
            for col in range(col_min, col_max + 1):
                # Construct the unique tile identifier tuple
                # Format: (media_id, tilelevel, row, col)
                tile_id: Tuple[str, int, int, int] = (self._media_id, tilelevel, row, col)
                try:
                    # Try to get the fully loaded tile from TileManager's cache
                    tile: Any = TileManager.get_tile(tile_id)
                except TileManager.TileNotLoaded:
                    # Tile exists in the tile store but hasn't been loaded into memory yet
                    # Mark the tileblock as non-final since we're using a substitute
                    tileblock_final = False
                    if mode == RenderMode.HighQuality:
                        # In HQ mode: cut (generate) a temporary tile without expiry
                        # cut_tile returns (tile, is_final) tuple; [0] gets just the tile
                        tile = TileManager.cut_tile(tile_id)[0]
                    else:
                        # In Draft mode: cut a temporary tile with tempcache expiry cycles
                        tile = TileManager.cut_tile(tile_id, self.tempcache)[0]
                except TileManager.TileNotAvailable:
                    # Tile is not available at all (may need to be generated from parent tiles)
                    if mode == RenderMode.HighQuality:
                        # In HQ mode: generate tile without expiry
                        tile: Any
                        final: bool
                        tile, final = TileManager.cut_tile(tile_id)
                    else:
                        # In Draft mode: generate tile with tempcache expiry cycles
                        tile, final = TileManager.cut_tile(tile_id,
                                                           self.tempcache)
                    # If the generated tile is not final quality, mark the whole block non-final
                    if not final: tileblock_final = False

                # Calculate the pixel position of this tile within the tileblock image
                # Offset from the top-left tile (col_min, row_min) of the block
                x: int = self.__tilesize * (col - col_min)
                y: int = self.__tilesize * (row - row_min)

                # Draw the tile onto the tileblock image at the calculated position
                tile.draw(tileblock_painter, x, y)

        # End the painting session; releases the QPainter from the QImage
        tileblock_painter.end()

        # Delete the old cached tileblock to free memory before replacing it
        del self.__tileblock

        # Cache the newly rendered tileblock and its metadata
        self.__tileblock = tileblock
        self.__tileblock_id = tileblock_id
        self.__tileblock_final = tileblock_final

        # Reset the age counter since this is a freshly rendered tileblock
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

        # Skip rendering if the image is too small to be visible on screen
        # min(self.onscreen_size) returns the smaller of width/height
        # Also skip if mode is Invisible (object should not be drawn)
        if min(self.onscreen_size) <= 1 or mode == RenderMode.Invisible:
            ## don't bother rendering if the image is too
            ## small to be seen, or invisible mode is set
            return

        # Select the image scaling transformation mode based on render quality
        # FastTransformation uses nearest-neighbor interpolation (fast but lower quality)
        if mode == RenderMode.Draft:
            transform_mode: QtCore.Qt.TransformationMode = QtCore.Qt.FastTransformation
        elif mode == RenderMode.HighQuality:
            transform_mode: QtCore.Qt.TransformationMode = QtCore.Qt.FastTransformation

        # Get the viewport dimensions (width, height) in pixels
        viewport_size: Tuple[float, float] = self._scene.viewport_size

        # Calculate the combined zoom level (scene zoom + object zoom)
        # This determines which tile level to use and the sub-tile scaling
        zoomlevel: float = self.zoomlevel + self._scene.zoomlevel

        # tilelevel is the integer ceiling of zoomlevel
        # Tiles are stored at integer zoom levels; we pick the next higher level
        tilelevel: int = int(math.ceil(zoomlevel))

        # tilescale is the fractional scaling between the tile's native resolution and display
        # When zoomlevel == tilelevel, tilescale = 1.0 (tiles displayed at native size)
        # When zoomlevel < tilelevel, tilescale < 1.0 (tiles are scaled down)
        tilescale: float = 2 ** (zoomlevel - tilelevel)

        # Convert viewport corners to tile row/col coordinates
        # (0,0) is the top-left of the viewport; viewport_size is the bottom-right
        row_min: int
        col_min: int
        row_min, col_min = self.__pixpos2rowcol((0, 0), tilescale)

        row_max: int
        col_max: int
        row_max, col_max = self.__pixpos2rowcol(viewport_size, tilescale)

        # Clamp minimum row/col to 0 (cannot have negative tile indices)
        row_min = max(row_min, 0)
        col_min = max(col_min, 0)

        # Get the maximum valid row/col for this tilelevel
        # Tiles beyond these bounds don't exist
        row_bound: int
        col_bound: int
        row_bound, col_bound = self.__rowcol_bound(tilelevel)

        # Clamp maximum row/col to the actual tile bounds
        row_max = min(row_max, row_bound)
        col_max = min(col_max, col_bound)

        if row_max < row_min or col_max < col_min:
            ## the image does not fall within the viewport
            # No tiles are visible; skip rendering entirely
            return

        # Create the tileblock identifier tuple for cache lookup
        # Uniquely identifies the visible tile region at the current zoom level
        tileblock_id: Tuple[int, int, int, int, int] = (tilelevel, row_min, col_min, row_max, col_max)

        # Determine whether the cached tileblock needs to be re-rendered
        if (self.__tileblock_id != tileblock_id) or \
           (not self.__tileblock_final and \
            (mode == RenderMode.HighQuality or \
             self.__tileblock_age >= self.tempcache)):
            ## the cached tileblock is different to the required
            ## one, so we have draw the new tileblock
            ## we also re-render the tileblock if it is not final
            ## and either we are in HQ mode or the tileblock
            ## is at least self.tempcache cycles old
            tileblock: QtGui.QImage = self.__render_tileblock(tileblock_id, mode)
        else:
            # Reuse the cached tileblock and increment its age counter
            tileblock = self.__tileblock
            self.__tileblock_age += 1

        # Scale the tileblock image to match the current display zoom
        # tilescale adjusts for the fractional zoom between integer tile levels
        image_scaled: QtGui.QImage = tileblock.scaled(
            int(tilescale * tileblock.width()),
            int(tilescale * tileblock.height()),
            QtCore.Qt.IgnoreAspectRatio,
            transform_mode)

        # Calculate the on-screen position where the tileblock should be drawn
        # Start from the object's top-left corner and offset by the tile region's position
        o: Tuple[float, float] = self.topleft

        # x position: object left edge + horizontal offset to the first visible tile column
        x: float = o[0] + int(tilescale * self.__tilesize * col_min)

        # y position: object top edge + vertical offset to the first visible tile row
        y: float = o[1] + int(tilescale * self.__tilesize * row_min)

        # Draw the scaled tileblock image onto the painter at the calculated position
        # painter.drawImage(x, y, image) renders the QImage at screen coordinates (x, y)
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
        # Get the on-screen position and size of this media object
        # topleft returns (x, y) screen coordinates of the top-left corner
        x: float
        y: float
        x, y = self.topleft

        # onscreen_size returns (width, height) in screen pixels
        w: float
        h: float
        w, h = self.onscreen_size

        try:
            # Fill the placeholder rectangle with a dark gray background
            # painter.fillRect(x, y, width, height, color) draws a filled rectangle
            painter.fillRect(x, y, w, h, QtCore.Qt.darkGray)
        except TypeError:
            ## rectangle dimensions could not be converted to ints
            # This can happen when dimensions are extremely large or NaN
            pass
        else:
            # fillRect succeeded; now draw progress text on top of the placeholder
            if self.__progress > 0:
                # Conversion/tiling has started; show percentage progress
                # Set text color to white for visibility against dark gray background
                painter.setPen(QtGui.QColor(255, 255, 255))

                # Create a font sized proportionally to the placeholder width
                # w/4 makes the percentage text roughly 25% of the placeholder width
                font: QtGui.QFont = QtGui.QFont()
                font.setPointSizeF(w / 4)
                painter.setFont(font)

                # Draw the progress percentage centered in the placeholder rectangle
                # QtCore.Qt.AlignCenter centers text both horizontally and vertically
                # int(self.__progress * 100) converts 0.0-1.0 to 0-100 percentage
                painter.drawText(x, y, w, h, QtCore.Qt.AlignCenter,
                    str(int(self.__progress * 100)) + '%')
            else:
                # No progress yet; show "loading..." text
                # Set text color to white for visibility
                painter.setPen(QtGui.QColor(255, 255, 255))

                # Create a smaller font (w/10) for the "loading..." text
                font: QtGui.QFont = QtGui.QFont()
                font.setPointSizeF(w / 10)
                painter.setFont(font)

                # Draw "loading..." centered in the placeholder rectangle
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
            # Attempt to retrieve the root tile (level=0, row=0, col=0) from TileManager
            # If this succeeds, the media has been fully tiled and is ready to render
            TileManager.get_tile(
                (self._media_id, 0, 0, 0))
        except TileManager.TileNotLoaded:
            # Tile exists in the store but hasn't been loaded into memory yet
            # This is expected during the loading process; we'll retry on next render cycle
            self.__logger.info("(0,0,0) tile not loaded yet")
            pass
        except (TileManager.MediaNotTiled,
            TileManager.TileNotAvailable):
            # The media could not be tiled at all; raise a LoadError to signal failure
            raise LoadError("unable to correctly tile the image")
        else:
            # Root tile loaded successfully; media is ready for rendering
            self.__logger.info("media loaded")
            self.__loaded = True

            if self.__tiler:
                ## destroy tiler to close tmpfile (required to unlink on Windows)
                # Setting to None allows garbage collection of the PPMTiler object
                self.__tiler = None

            # On Windows, clean up the temporary PPM file
            # On Unix systems, the file can be unlinked even while open
            if os.name == 'nt':
                try:
                    # os.unlink() deletes the file from the filesystem
                    os.unlink(self.__tmpfile)
                except:
                    # Log but don't crash if temp file cleanup fails
                    self.__logger.exception("unable to unlink temporary file "
                        "'%s'" % self.__tmpfile)

            # Save the current bounding box before updating dimensions
            # These are needed for autofit to maintain the placeholder's screen position
            old_x1: float
            old_y1: float
            old_x1, old_y1 = self.topleft

            old_x2: float
            old_y2: float
            old_x2, old_y2 = self.bottomright

            # Save the current centre position for restoration after autofit
            old_centre: Tuple[float, float] = self.centre

            # Load the actual media dimensions from TileManager metadata
            # These replace the default_size (256, 256) placeholder values
            self.__width = TileManager.get_metadata(
                self._media_id, 'width')
            self.__height = TileManager.get_metadata(
                self._media_id, 'height')

            # Load the maximum tile level (deepest zoom level available)
            self.__maxtilelevel = TileManager.get_metadata(
                self._media_id, 'maxtilelevel')

            # Load the tile size in pixels (typically 256)
            self.__tilesize = TileManager.get_metadata(
                self._media_id, 'tilesize')

            # Load the aspect ratio (width / height) for efficient size calculations
            self.__aspect_ratio = TileManager.get_metadata(
                self._media_id, 'aspect_ratio')

            if self.__autofit:
                ## fit to area occupied by placeholder
                # Resize and reposition the media to fill the old placeholder bounding box
                # fit() adjusts zoom level and position to maximize size within the box
                self.fit((old_x1, old_y1, old_x2, old_y2))

                # Restore the centre position to keep the object centered where it was
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

        # Check if the PPM file exists on disk before attempting to tile it
        # os.path.exists() returns True if the file path exists
        if not os.path.exists(self.__ppmfile):

            ## there was a problem converting, or the input file
            ## never actually existed
            if self.__converter and self.__converter.error:
                # Converter reported an error; propagate it as a LoadError
                raise LoadError(self.__converter.error)
            else:
                # No converter error available; raise a generic LoadError
                raise LoadError("there was a problem "
                    "converting and/or loading the input file")

        # Determine the output tile format based on the input file extension
        # JPG files are tiled as JPG to preserve compression; everything else uses PNG
        if self._media_id.lower().endswith('.jpg'):
            filext: str = 'jpg'
        else:
            filext: str = 'png'

        try:
            # Create a PPMTiler to subdivide the PPM image into a tile hierarchy
            # PPMTiler(ppmfile, media_id, format) reads the PPM and creates tiles
            self.__tiler = PPMTiler(self.__ppmfile, self._media_id, filext)

            # Start the tiling process (runs in a separate thread)
            # Tiles are written to the TileManager's tile store as they are created
            self.__tiler.start()

        except IOError:
            # IOError during tiler creation indicates a file read problem
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

        # If the media is fully loaded, render the actual tiled image
        if self.__loaded:
            self.__render_media(painter, mode)

        elif self.__tiler and self.__tiler.error:
            # The tiler encountered an error during the tiling process
            # Log the error but don't raise an exception to avoid crashing the render loop
            self.__logger.exception("an error ocurred during "
                "the tiling process: %s" % self.__tiler.error)

        # Check if TileManager now has tiles available for this media
        # Uses 'if' instead of 'elif' to allow loading even after the __loaded check above
        if TileManager.tiled(self._media_id):

            # Attempt to load the root tile and update media dimensions
            self.__try_load()

            if self.__loaded:
                # Loading succeeded; render the actual media content
                self.__render_media(painter, mode)
            else:
                # Root tile not yet in memory; show placeholder while loading
                self.__render_placeholder(painter)

        elif self.__tiler is None and \
             (self.__converter is None or self.__converter.progress == 1.0):
            ## the tiler has not been run yet and either
            ## it was assumed that media_id is a local PPM
            ## file or the converter has just finished

            # Start the tiling process now that the PPM file is ready
            self.__run_tiler()

            # Show placeholder while tiling is in progress
            self.__render_placeholder(painter)

        else:
            # Conversion/tiling still in progress; show placeholder with progress
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
            # Aspect ratio is available (media has been loaded)
            if self.__aspect_ratio >= 1.0:
                ## width >= height (landscape orientation)
                # Width is determined by the combined zoom level and tile size
                # 2^(scene_zoom + object_zoom) * tilesize gives the full-width at this zoom
                w: float = 2**(self._scene.zoomlevel + self.zoomlevel) * self.__tilesize

                # Height is derived from width using the aspect ratio (width / height)
                h: float = w / self.__aspect_ratio
            else:
                ## height > width (portrait orientation)
                # Height is determined by the combined zoom level and tile size
                h: float = 2**(self._scene.zoomlevel + self.zoomlevel) * self.__tilesize

                # Width is derived from height using the aspect ratio
                w: float = h * self.__aspect_ratio
            return (w, h)
        elif self.__width == 0 or self.__height == 0:
            # Media dimensions are not yet known (still loading)
            return (0, 0)
        else:
            # Fallback: calculate from actual pixel dimensions and zoom levels
            # scale converts from tile-level pixels to screen pixels
            # Subtracting maxtilelevel accounts for the tile hierarchy depth
            scale: float = 2 ** (self._scene.zoomlevel + self.zoomlevel \
                - self.__maxtilelevel)

            # Multiply pixel dimensions by scale to get on-screen size
            w: float = self.__width * scale
            h: float = self.__height * scale
            return (w, h)
