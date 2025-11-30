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

"""PDF rasterizer based upon either Xpdf or Poppler."""

import inspect

import subprocess
import tempfile
import os
import shutil

from .converter import Converter
from .ppm import read_ppm_header
from . import tilestore as TileStore

class PDFConverter(Converter):
    """PDFConverter objects are used for rasterizing PDFs.

    The output format will always be PPM irrespective of the file extension of
    the output file. If another output format is required then PDFConverter
    should be used in conjunction with VipsConverter.

    Constructor: PDFConverter(string, string)
    """
    def __init__(self, infile, outfile):
        Converter.__init__(self, infile, outfile)

        self.resolution = 300


    def __merge(self, tmpdir):
        """Merge the PPM pages located in tmpdir.

        __merge(string) -> None
        """
        self._logger.info("merging pages")
        self._progress = 0.5

        #total_width = 0
        total_height = 0

        page_filename = {}
        for filename in os.listdir(tmpdir):
            ## output files don't have a consistent format, so we need to
            ## determine which files are for which page
            ## filename[5:-4] extracts '1234' from 'page-1234.ppm'
            page_filename[int(filename[5:-4])] = filename
        
        num_pages = len(page_filename)
        f = []

        for i in range(num_pages):
            ## open files and process headers
            wip_file = os.path.join(tmpdir, page_filename[i+1])
            
            f.append(open(wip_file, 'rb'))
            try:
                width, height = read_ppm_header(f[i])
            
            except IOError as e:
                print("error loading PPM images ",\
                    "produced by pdftoppm: %s" % e)
                print("Truncating PDF")
                        

            total_height += height
            

        fout = open(self._outfile, 'wb')
        
        fout.write(("P6\n" + str(width) + " " + str(total_height) + "\n255\n").encode('latin-1'))

        for i in range(num_pages):
            ## concatenate pixel data into output file
            shutil.copyfileobj(f[i], fout)

        fout.close()
        

    #'-scale-to',str(1000),
    def run(self):

        with TileStore.disk_lock:
            tmpdir = tempfile.mkdtemp()
            self._logger.info("calling pdftoppm")
            process = subprocess.Popen(['pdftoppm',
                '-r', str(self.resolution),
                self._infile, os.path.join(tmpdir, 'page')],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            stdout = process.communicate()[0]

            if process.returncode == 0:
                try:
                    self.__merge(tmpdir)
                
                except Exception as e:
                    self.error = 'Error in PDFConverter.__merge() \n' + str(e)
                    self._logger.error(self.error)
                    
                    try:
                        os.unlink(self._outfile)
                    except:
                        self.__logger.exception("unable to unlink temporary "
                            "file '%s'" % self._outfile)
                          
            else:
                self.error = "conversion failed with return code %d:\n%s" % \
                    (process.returncode, stdout)
                self._logger.error(self.error)

            shutil.rmtree(tmpdir, ignore_errors=True)
            self._progress = 1.0


    def __str__(self):
        return "PDFConverter(%s, %s)" % (self._infile, self._outfile)


    def __repr__(self):
        return "PDFConverter(%s, %s)" % \
            (repr(self._infile), repr(self._outfile))



