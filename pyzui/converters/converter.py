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

"""A threaded media converter (abstract base class)."""

from threading import Thread
from ..logger import get_logger

class Converter(Thread):
    """
    Constructor :
        Converter(infile, outfile)
    Parameters :
        infile : str
        outfile : str

    Converter(infile, outfile) --> None

    Converter objects are used for converting media.

    Create a new Converter for converting media at the location given by
    `infile` to the location given by `outfile`.

    Where appropriate, the output format will be determined from the file
    extension of `outfile`.
    """
    def __init__(self, infile: str, outfile: str) -> None:
        Thread.__init__(self)

        self._infile = infile
        self._outfile = outfile

        self._progress = 0.0

        self._logger = get_logger(f'Converter.{infile}')

        self.error = None


    def run(self) -> None:
        """
        Method :
            Converter.run()
        Parameters :
            None

        Converter.run() --> None

        Run the conversion. If any errors are encountered then :attr:`self.error`
        will be set to a string describing the error.
        """
        pass


    @property
    def progress(self) -> float:
        """
        Property :
            Converter.progress
        Parameters :
            None

        Converter.progress --> float

        Conversion progress ranging from 0.0 to 1.0. A value of 1.0
        indicates that the converter has completely finished.
        """
        return self._progress


    def __str__(self) -> str:
        return "Converter(%s, %s)" % (self._infile, self._outfile)


    def __repr__(self) -> str:
        return "Converter(%s, %s)" % (repr(self._infile), repr(self._outfile))
    
    
    
    
    
    
    
