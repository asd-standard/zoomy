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

"""Module for reading PPM images."""

from typing import Optional, Tuple, Any
from .tiler import Tiler

def read_ppm_header(f: Any) -> Tuple[int, int]:
    """
    Function :
        read_ppm_header(f)
    Parameters :
        f : Any

    read_ppm_header(f) --> Tuple[int, int]

    Read the PPM header in the given file object `f` and return a tuple
    representing the dimensions of the image.

    Raises IOError if the header is invalid and/or unsupported (must be 'P6'
    binary PPM format with maxval=255).
    """
    header = []

    while len(header) < 4:
        line = f.readline()

        if not line:
            ## we've hit EOF
            raise IOError("not enough entries in PPM header")

        # Split line and filter out comments (# and everything after)
        tokens = line.split()
        for token in tokens:
            # Skip comments (lines starting with #)
            if token.startswith(b'#'):
                break  # Skip rest of line after #
            header.append(token)

    magic = header[0]
    
    if str(magic) != str(b'P6'):
        raise IOError("can only load binary PPM (P6 format)")

    try:
        width = int(header[1])
        height = int(header[2])
        maxval = int(header[3])
    except ValueError:
        raise IOError("invalid PPM header")

    if maxval != 255:
        raise IOError("PPM maxval must equal 255")

    return (width, height)

class PPMTiler(Tiler):
    """
    Constructor:
        PPMTiler(infile, media_id, filext, tilesize)
    Parameters :
        infile : str
        media_id : Optional[str]
        filext : str
        tilesize : int

    PPMTiler(infile, media_id, filext, tilesize) --> None

    PPMTiler objects are used for tiling PPM images.
    Inherits from Tiler class and provides PPM-specific image reading.
    """
    def __init__(self, infile: str, media_id: Optional[str] = None, filext: str = 'jpg', tilesize: int = 256) -> None:
        """
        Constructor:
            PPMTiler(infile, media_id, filext, tilesize)
        Parameters :
            infile : str
            media_id : Optional[str]
            filext : str
            tilesize : int

        PPMTiler(infile, media_id, filext, tilesize) --> None

        Create a new PPMTiler for tiling the media given by media_id with the
        PPM image given by infile.

        If media_id is omitted, it will be set to infile.

        Tiles will be saved in the format indicated by filext and with the
        dimensions given by tilesize.
        """
        
        
        Tiler.__init__(self, infile, media_id, filext, tilesize)
        
        
        try:
            self.__ppm_fileobj = open(self._infile, 'rb')
            
        except IOError:
            raise

        self._width, self._height = read_ppm_header(self.__ppm_fileobj)

        self._bytes_per_pixel = 3
        

    def _scanchunk(self) -> bytes:
        """
        Method :
            PPMTiler._scanchunk()
        Parameters :
            None

        PPMTiler._scanchunk() --> bytes

        Scan a chunk of ppm image bytes correspondent of a tile row.
        The row length of the tile is given by self._bytes_per_pixel*self._width.
        """
        return self.__ppm_fileobj.read(self._bytes_per_pixel*self._width) 
         

    def __del__(self) -> None:
        """
        Method :
            PPMTiler.__del__()
        Parameters :
            None

        PPMTiler.__del__() --> None

        Cleanup method to close the PPM file object when the object is destroyed.
        Handles AttributeError if object was never fully initialized.
        """
        try:
            self.__ppm_fileobj.close()
        except AttributeError:
            pass  # Object was never fully initialized

