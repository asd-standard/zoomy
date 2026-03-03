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

"""Threaded image tiler (abstract base class)."""

from typing import Optional, List, Any, TYPE_CHECKING, Tuple
from threading import Thread
import math
import shutil
import traceback
import os

import time 
from .. import tilestore as TileStore
from .. import tile as Tile
from pyzui.logger import get_logger

from concurrent.futures import ThreadPoolExecutor

if TYPE_CHECKING:
    from ..tile import Tile as TileType

TileID = Tuple[str, int, int, int]

def _make_tile(args):
    """Worker function for parallel tile creation.
    
    Unpacks the tuple (string, width, height) and calls Tile.fromstring.
    This function is designed to be used with ThreadPoolExecutor.map,
    which expects a single‑argument callable.
    """
    string, width, height = args
    return Tile.fromstring(string, width, height)

#Thread
class Tiler(Thread):
    """
    Constructor:
        Tiler(infile, media_id, filext, tilesize)
    Parameters :
        infile : str
        media_id : Optional[str]
        filext : str
        tilesize : int

    Tiler(infile, media_id, filext, tilesize) --> None

    Tiler objects are used for tiling images.
    """
    def __init__(self, infile: str, media_id: Optional[str] = None, filext: str = 'jpg', tilesize: int = 256) -> None:
        """
        Constructor:
            Tiler(infile, media_id, filext, tilesize)
        Parameters :
            infile : str
            media_id : Optional[str]
            filext : str
            tilesize : int

        Tiler(infile, media_id, filext, tilesize) --> None

        Create a new Tiler for tiling the media given by `media_id` with the
        image given by `infile`.

        If `media_id` is omitted, it will be set to `infile`.

        Tiles will be saved in the format indicated by `filext` and with the
        dimensions given by `tilesize`.

        images are tiled with the following procedure:
        the number of tiles to cover a row of the image is calculated, the last tile
        of the row is of the minimum width to finish the image and standard height (256).
        the last row tiles are of the minimum height to finish the image and the last tile is of
        the minimum size to cover the bottom right corner of the image.
        The example below will have a self.numtiles_across_total = 2::

           +-------+
           | t1 |t2|
           |    |  |
           |----+--|
           | t3 |t4|
           +-------+
        """
        
        Thread.__init__(self)
        
        
        #print(type(infile))
        #print(type(filext))
        #print(type(tilesize)) 
        
        self._infile = infile
        self.__filext = filext
        self.__tilesize = tilesize
        

        if media_id:
            self.__media_id = media_id
        else:
            self.__media_id = infile

        self.__outpath = TileStore.get_media_path(self.__media_id)
        #print('OUTPATH: ', self.__outpath)

        self.__progress = 0.0

        self.__logger = get_logger(f'Tiler.{self.__media_id}')

        self.error = None
        self.__executor = None
        

    def _scanline(self) -> str:
        """
        Method :
            Tiler._scanline()
        Parameters :
            None

        Tiler._scanline() --> str

        Return string containing pixels of the next row.
        """
        return ""
    

    def __savetile(self, tile: 'TileType', tilelevel: int, row: int, col: int) -> None:
        """
        Method :
            __savetile(tile, tilelevel, row, col)
        Parameters :
            tile : Tile
            tilelevel : int
            row : int
            col : int

        __savetile(tile, tilelevel, row, col) --> None

        Save the given tile to disk.
        """
        
        tile_id = (self.__media_id, tilelevel, row, col)
        filename = TileStore.get_tile_path(
            tile_id, True, self.__outpath, self.__filext)
        
        tile.save(filename)
        
        self.__progress += 1.0/self.__numtiles
        self.__logger.info("%3d%% tiled", int(self.__progress*100))

    def __load_row_from_file(self, row: int) -> Optional[List['TileType']]:
        """
        Method :
            __load_row_from_file(row)
        Parameters :
            row : int

        __load_row_from_file(row) --> Optional[List[Tile]]

        Load the requested row from the image file.

        Precondition: calls to this function must take consecutive values for
        row i.e. the first call must have row=0, then the next call must have
        row=1, etc.
        """
        #print('Tiler 125, Row', row)
        if row >= self.__numtiles_down_total:
            #print('tiler127 requested row does not exist')
            ## requested row does not exist
            return None

        tiles = [''] * self.__numtiles_across_total

        if row == self.__numtiles_down_total-1:
            ## we're in the bottom row
            tileheight = self.__bottom_tiles_height
        else:
            tileheight = self.__tilesize
        
        '''
            for every tile row we cicle all row tiles.
        '''

        for pixrow in range(tileheight):
            
            scanchunk = self._scanchunk()
            
            if scanchunk == '':
                ## we've gone past the end of the file
                raise IOError("less data in image than "
                    "reported by the header")  
            
            for i in range(self.__numtiles_across_total):
                
                p = self._bytes_per_pixel * i * self.__tilesize        
                
                if i == self.__numtiles_across_total-1:
                    ## last tile in row 
                    tiles[i] += (scanchunk[p:]).decode('latin-1') 
                else:
                    tiles[i] += (scanchunk[p : p + self._bytes_per_pixel*self.__tilesize]).decode('latin-1')
                    #print(tiles[i],'\n')
        
        '''
        Each tile in the row is independent, so we can decode multiple tiles concurrently.
        The thread pool is created in run() only when there is more than one tile per row.
        Arguments for each tile (raw string, width, height) are built into a list,
        then dispatched via executor.map(_make_tile, args). Results are collected
        in the same order, preserving tile positions.
        If the executor is not available (single‑tile rows), we fall back to sequential
        processing. Tile.fromstring uses PIL's C‑code, which releases the GIL and allows
        true parallelism across threads.
        '''
        if self.__executor is not None:
            # Build argument list for each tile
            args = []
            for i in range(self.__numtiles_across_total):
                if i == self.__numtiles_across_total-1:
                    width = self.__right_tiles_width
                else:
                    width = self.__tilesize
                args.append((tiles[i], width, tileheight))
            # Process tiles in parallel
            try:
                results = list(self.__executor.map(_make_tile, args))
            except Exception as e:
                self.__logger.error("Parallel tile creation failed", exc_info=True)
                raise
            # Assign results back in order
            for i, tile in enumerate(results):
                tiles[i] = tile
        else:
            # Fallback sequential processing
            for i in range(self.__numtiles_across_total):
                if i == self.__numtiles_across_total-1:
                    tiles[i] = Tile.fromstring(tiles[i],
                        self.__right_tiles_width, tileheight)
                else:
                    tiles[i] = Tile.fromstring(tiles[i],
                        self.__tilesize, tileheight)
        return tiles

    def __mergerows(self, row_a: Optional[List['TileType']], row_b: Optional[List['TileType']] = None) -> Optional[List['TileType']]:
        """
        Method :
            __mergerows(row_a, row_b)
        Parameters :
            row_a : Optional[List[Tile]]
            row_b : Optional[List[Tile]]

        __mergerows(row_a, row_b) --> Optional[List[Tile]]

        Merge blocks of 4 tiles (or blocks of 2 if row_b is None) into a
        single tile.
        """
        if not row_a:
            ## requested row does not exist
            return None
        if not row_b:
            ## make a fake row_b
            row_b = [None] * len(row_a)

        if len(row_a) % 2 == 1:
            ## buffer rows to make them even
            row_a.append(None)
            row_b.append(None)

        tiles = []
        while row_a:
            tiles.append(Tile.merged(
                row_a.pop(0), row_a.pop(0),
                row_b.pop(0), row_b.pop(0)))

        return tiles

    def __tiles(self, tilelevel: int = 0, row: int = 0) -> Optional[List['TileType']]:
        """
        Method :
            __tiles(tilelevel, row)
        Parameters :
            tilelevel : int
            row : int

        __tiles(tilelevel, row) --> Optional[List[Tile]]

        Recursive function which retrieves the tiles in the given row, saves
        them, scales each dimension by 1/2, and then returns them as a list.

        As the function is recursive, all higher-resolution sub-tiles contained
        within the requested tile will be saved in the process. Therefore,
        requesting row 0 from tilelevel 0 will result in the entire image being
        tiled.
        """
        tiles = None

        if tilelevel == self.__maxtilelevel:
            try :

                tiles = self.__load_row_from_file(row)

            except Exception as e :
                self.error = str(e)
                outpath = TileStore.get_media_path(self.__media_id)
                shutil.rmtree(outpath, ignore_errors=True)
                return None

        else:
            ## load the requested row by merging sub-tiles from
            ## tilelevel (tilelevel+1)

            try :
                row_a = self.__tiles(tilelevel+1, row*2)
                row_b = self.__tiles(tilelevel+1, row*2+1)
                tiles = self.__mergerows(row_a, row_b)

            except Exception as e :
                self.error = str(e)
                outpath = TileStore.get_media_path(self.__media_id)
                shutil.rmtree(outpath, ignore_errors=True)
                traceback.print_stack()
                return None

        if not tiles:
            ## requested row does not exist
            return None

        for i in range(len(tiles)):
            #tiles[i]._Tile__image
            try :
                self.__savetile(tiles[i], tilelevel, row, i)
                tiles[i] = tiles[i].resize(tiles[i].size[0]//2, tiles[i].size[1]//2)
            except Exception as e :
                self.error = str(e)
                outpath = TileStore.get_media_path(self.__media_id)
                shutil.rmtree(outpath, ignore_errors=True)
                traceback.print_stack()

        return tiles

    def __calculate_maxtilelevel(self) -> int:
        """
        Method :
            __calculate_maxtilelevel()
        Parameters :
            None

        __calculate_maxtilelevel() --> int

        Calculate the maxtilelevel, which is the smallest non-negative
        integer such that:
        tilesize * (2**maxtilelevel) >= max(width, height)
        i.e. if tilelevel 0 contains a single tile, then the tiles in
        maxtilelevel are the same resolution as the input image
        """
        maxdim = max(self._width, self._height)
        if maxdim <= self.__tilesize:
            ## entire image can be contained within
            ## the (0,0,0) tile
            return 0
        else:
            ## above equation can be rearranged to
            ##   maxtilelevel >= log_2(maxdim) - log_2(tilesize)
            ## and using ceil to find smallest integer maxtilelevel
            ## satisfying this equation
            maxtilelevel = int(math.ceil(
                math.log(maxdim,2)
                 - math.log(self.__tilesize,2)))

            ## check if rounding errors caused maxtilelevel to be
            ## mistakenly rounded up to the next integer
            ## i.e. if maxtilelevel-1 also fulfills the req'ment
            if self.__tilesize * (2**(maxtilelevel-1)) >= maxdim:
                maxtilelevel -= 1
            
            return maxtilelevel

    def __calculate_numtiles(self) -> int:
        """
        Method :
            __calculate_numtiles()
        Parameters :
            None

        __calculate_numtiles() --> int

        Calculate the total number of tiles required.
        """
        numtiles = 0
        for tilelevel in range(self.__maxtilelevel+1):
            tilescale = 2**(self.__maxtilelevel-tilelevel)

            ## number of pixels on the original image taken by the
            ## side of the tile
            real_tilesize = tilescale*self.__tilesize

            numtiles_across = \
                (self._width+real_tilesize-1)//real_tilesize
            numtiles_down = \
                (self._height+real_tilesize-1)//real_tilesize

            numtiles += numtiles_across * numtiles_down

        return numtiles

    def run(self) -> None:
        """
        Method :
            Tiler.run()
        Parameters :
            None

        Tiler.run() --> None

        Tile the image. If any errors are encountered then `self.error` will
        be set to a string describing the error.
        """

        self.__logger.debug("beginning tiling process")

        self.__maxtilelevel = self.__calculate_maxtilelevel()
        self.__numtiles = self.__calculate_numtiles()

        ## number of tiles that fit on the original image
        
        self.__numtiles_across_total = \
            (self._width+self.__tilesize-1)//self.__tilesize
        

        self.__numtiles_down_total = \
            (self._height+self.__tilesize-1)//self.__tilesize
        #print(self.__numtiles_down_total)

        ## width and height of the right-most and bottom-most tiles
        ## respectively
        self.__right_tiles_width =   (self._width  - 1) % self.__tilesize + 1
        self.__bottom_tiles_height = (self._height - 1) % self.__tilesize + 1
        #print(self.__bottom_tiles_height, self.__right_tiles_width) 

        try:
            # Create thread pool executor for parallel tile creation.
            # The executor is only created when there is more than one tile per row,
            # avoiding overhead for single‑tile rows. Worker count is capped at the
            # smaller of the number of tiles per row and the available CPU cores.
            # See __load_row_from_file for where the executor is used.
            if self.__numtiles_across_total > 1:
                max_workers = min(self.__numtiles_across_total, os.cpu_count() or 1)
                self.__executor = ThreadPoolExecutor(max_workers=max_workers)
                self.__logger.debug(f"created ThreadPoolExecutor with {max_workers} workers")
            else:
                self.__executor = None
                self.__logger.debug("skipping ThreadPoolExecutor (single tile per row)")
              
            with TileStore.disk_lock:
                ## recursively tile the image
                self.__tiles()
            
        except Exception as e:       
            self.error = str(e)
            outpath = TileStore.get_media_path(self.__media_id)
            shutil.rmtree(outpath, ignore_errors=True)
                
        else:
            
            TileStore.write_metadata(self.__media_id,
                filext=self.__filext,
                tilesize=self.__tilesize,

                maxtilelevel=self.__maxtilelevel,

                width=self._width,
                height=self._height,
            )
        finally:
            if self.__executor is not None:
                self.__executor.shutdown(wait=True)
                self.__executor = None
                self.__logger.debug("ThreadPoolExecutor shut down")
        
        self.__progress = 1.0
        self.__logger.debug("tiling complete")

    @property
    def progress(self) -> float:
        """
        Property :
            Tiler.progress
        Parameters :
            None

        Tiler.progress --> float

        Tiling progress ranging from 0.0 to 1.0. A value of 1.0 indicates
        that the tiling has completely finished.
        """
        return self.__progress

    def __str__(self) -> str:
        """
        Method :
            Tiler.__str__()
        Parameters :
            None

        Tiler.__str__() --> str

        Return string representation of the Tiler object.
        """
        return "Tiler(%s)" % self._infile

    def __repr__(self) -> str:
        """
        Method :
            Tiler.__repr__()
        Parameters :
            None

        Tiler.__repr__() --> str

        Return formal string representation of the Tiler object.
        """
        return "Tiler(%s)" % repr(self._infile)

