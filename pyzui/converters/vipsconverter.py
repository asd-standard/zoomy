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

"""Image converter based upon libvips (via pyvips)."""

import pyvips
import os

from .converter import Converter
from pyzui.tilesystem import tilestore as TileStore

class VipsConverter(Converter):
    """
    Constructor :
        VipsConverter(infile, outfile)
    Parameters :
        infile : str
        outfile : str

    VipsConverter(infile, outfile) --> None

    VipsConverter objects are used for converting media with libvips.
    libvips is a fast image processing library that can handle very large images
    with low memory usage. For a list of supported image formats see
    https://www.libvips.org/API/current/file-format.html
    """
    def __init__(self, infile: str, outfile: str) -> None:
        
        Converter.__init__(self, infile, outfile)

        ## since PPMTiler only supports 8-bit images
        self.bitdepth = 8


    def run(self) -> None:
        """
        Method :
            VipsConverter.run()
        Parameters :
            None

        VipsConverter.run() --> None

        Run the conversion using libvips. Loads the image from the input file,
        converts it to the appropriate format (8-bit RGB or grayscale), and writes
        it to the output file in PPM format.

        If any errors are encountered then :attr:`self.error` will be set to a
        string describing the error.
        """
        try:
            with TileStore.disk_lock:
                self._logger.debug("loading image with libvips")

                # Load the image using libvips
                image = pyvips.Image.new_from_file(self._infile, access='sequential')

                self._logger.debug(f"loaded {image.width}x{image.height} image with {image.bands} bands")

                # Convert to the specified bit depth if needed
                if self.bitdepth == 8 and image.format != 'uchar':
                    self._logger.debug(f"converting from {image.format} to 8-bit")
                    # Scale to 8-bit range
                    image = image.cast('uchar')

                # Ensure we have RGB or grayscale format for PPM
                if image.bands == 4:  # RGBA
                    self._logger.debug("flattening RGBA to RGB")
                    image = image.flatten()
                elif image.bands > 3 and image.bands != 1:
                    self._logger.debug(f"extracting first 3 bands from {image.bands}-band image")
                    image = image.extract_band(0, n=3)

                # Write to PPM format
                self._logger.debug(f"writing to {self._outfile}")
                image.write_to_file(self._outfile)

        except Exception as e:
            self.error = f"conversion failed: {str(e)}"
            self._logger.error(self.error)

            try:
                if os.path.exists(self._outfile):
                    os.unlink(self._outfile)
            except Exception:
                try:
                    self._logger.exception("unable to unlink temporary file "
                        "'%s'" % self._outfile)
                except AttributeError:
                    pass  # Logger not initialized

        self._progress = 1.0


    def __str__(self) -> str:
        return "VipsConverter(%s, %s)" %  (self._infile, self._outfile)


    def __repr__(self) -> str:
        return "VipsConverter(%s, %s)" % \
            (repr(self._infile), repr(self._outfile))





