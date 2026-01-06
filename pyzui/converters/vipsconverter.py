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

"""Image converter based upon libvips (via pyvips)."""

import pyvips
import os
from typing import Literal

from .converter import Converter

class VipsConverter(Converter):
    """
    Constructor :
        VipsConverter(infile, outfile, rotation=0, invert_colors=False, black_and_white=False)
    Parameters :
        infile : str
        outfile : str
        rotation : int (0, 90, 180, or 270)
        invert_colors : bool
        black_and_white : bool

    VipsConverter(infile, outfile, rotation=0, invert_colors=False, black_and_white=False) --> None

    VipsConverter objects are used for converting media with libvips.
    libvips is a fast image processing library that can handle very large images
    with low memory usage. For a list of supported image formats see
    https://www.libvips.org/API/current/file-format.html
    """
    def __init__(self, infile: str, outfile: str,
                 rotation: Literal[0, 90, 180, 270] = 0,
                 invert_colors: bool = False,
                 black_and_white: bool = False) -> None:
        """
        Constructor :
            VipsConverter(infile, outfile, rotation, invert_colors, black_and_white)
        Parameters :
            infile : str
            outfile : str
            rotation : Literal[0, 90, 180, 270]
            invert_colors : bool
            black_and_white : bool

        VipsConverter(infile, outfile, rotation, invert_colors, black_and_white) --> None

        Create a new VipsConverter for converting media files using libvips.

        The infile parameter is the path to the source image file.
        The outfile parameter is the path where the converted PPM will be written.
        The rotation parameter specifies rotation angle in degrees (0, 90, 180, or 270).
        The invert_colors parameter enables color inversion when True.
        The black_and_white parameter enables grayscale conversion when True.
        """
        Converter.__init__(self, infile, outfile)

        ## since PPMTiler only supports 8-bit images
        self.bitdepth = 8

        ## rotation angle in degrees (0, 90, 180, or 270)
        self.rotation = rotation

        ## color manipulation flags
        self.invert_colors = invert_colors
        self.black_and_white = black_and_white

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
            self._logger.debug("loading image with libvips")

            # Load the image using libvips
            image = pyvips.Image.new_from_file(self._infile, access='sequential')

            self._logger.debug(f"loaded {image.width}x{image.height} image with {image.bands} bands")

            # Apply rotation if specified
            if self.rotation != 0:
                self._logger.debug(f"rotating image by {self.rotation} degrees")
                angle_map = {
                    90: pyvips.Angle.D90,
                    180: pyvips.Angle.D180,
                    270: pyvips.Angle.D270,
                }
                image = image.rot(angle_map[self.rotation])

            # Apply black and white conversion if specified (before invert)
            if self.black_and_white:
                self._logger.debug("converting to black and white (grayscale)")
                # Convert to grayscale using colourspace, then back to sRGB for PPM
                image = image.colourspace('b-w').colourspace('srgb')

            # Apply color inversion if specified
            if self.invert_colors:
                self._logger.debug("inverting colors")
                image = image.invert()

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
        """
        Method :
            VipsConverter.__str__()
        Parameters :
            None

        VipsConverter.__str__() --> str

        Return a human-readable string representation of the VipsConverter.
        """
        return "VipsConverter(%s, %s, rotation=%d, invert_colors=%s, black_and_white=%s)" % (
            self._infile, self._outfile, self.rotation,
            self.invert_colors, self.black_and_white)

    def __repr__(self) -> str:
        """
        Method :
            VipsConverter.__repr__()
        Parameters :
            None

        VipsConverter.__repr__() --> str

        Return a formal string representation of the VipsConverter.
        """
        return "VipsConverter(%s, %s, rotation=%d, invert_colors=%s, black_and_white=%s)" % (
            repr(self._infile), repr(self._outfile), self.rotation,
            self.invert_colors, self.black_and_white)

