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

"""Webpage renderer based upon QtWebKit."""

from typing import Optional, Tuple, List, Any
import os
import sys
import time

#replaced QtWebKitWidgets QtWebEngineWidgets

from PySide6 import QtCore, QtGui, QtSvg, QtWebEngineWidgets, QtWidgets

from .converter import Converter

class WebKitConverter(Converter):
    """WebKitConverter objects are used for rendering webpages.

    `infile` may be either a URI or the location of a local file.

    Supported output formats are: BMP, JPG/JPEG, PNG, PPM, TIFF, XBM, XPM
    (see http://doc.trolltech.com/qimage.html#reading-and-writing-image-files)

    Constructor:
        WebKitConverter(infile, outfile)
    Parameters :
        infile : str
        outfile : str
    """
    def __init__(self, infile: str, outfile: str) -> None:
        Converter.__init__(self, infile, outfile)


    def start(self) -> None:
        """If a global QApplication has already been instantiated, then this
        method will call :meth:`run` directly, as Qt requires us to call :meth:`run`
        from the same thread as the global QApplication. This will not block as
        Qt will then handle the threading.

        Otherwise, if no QApplication exists yet, then the default
        :meth:`Converter.start` method will be called allowing Python to natively
        handle the threading.

        Method:
            WebKitConverter.start()
        Parameters :
            None

        WebKitConverter.start() -> None
        """
        if QtWidgets.QApplication.instance() is None:
            self._logger.info("using Python threading")
            Converter.start(self)
        else:
            self._logger.info("using Qt threading")
            self.run()


    def run(self) -> None:
        if QtWidgets.QApplication.instance() is None:
            ## no QApplication exists yet
            self.__qapp = QtWidgets.QApplication([])
        else:
            ## a global QApplication already exists
            self.__qapp = None

        self.__qpage = QtWebEngineWidgets.QWebPage()

        self.__qpage.loadFinished[bool].connect(self.__load_finished)
        self.__qpage.loadProgress[int].connect(self.__load_progress)

        self.__qpage.mainFrame().setScrollBarPolicy(
            QtCore.Qt.Horizontal, QtCore.Qt.ScrollBarAlwaysOff)
        self.__qpage.mainFrame().setScrollBarPolicy(
            QtCore.Qt.Vertical, QtCore.Qt.ScrollBarAlwaysOff)

        pagewidth = 1024
        pageminheight = 0
        self.__qpage.setViewportSize(
            QtCore.QSize(pagewidth, pageminheight))

        self.__qpage.mainFrame().load(QtCore.QUrl(self._infile))

        if self.__qapp is not None:
            self.__qapp.exec()


    def __load_finished(self, ok: bool) -> None:
        """Qt slot called when the page has finished loading.

        Method:
            WebKitConverter.__load_finished(ok)
        Parameters :
            ok : bool

        WebKitConverter.__load_finished(ok) -> None
        """
        if ok and self.__qpage.mainFrame().contentsSize().height() != 0:
            ## load was successful

            self._logger.info("page successfully loaded")

            painter = QtGui.QPainter()

            ## resize height to fit page
            self.__qpage.setViewportSize(
                self.__qpage.mainFrame().contentsSize())

            if self._outfile.lower().endswith('.svg'):
                svg = QtSvg.QSvgGenerator()
                svg.setFileName(self._outfile)
                svg.setSize(self.__qpage.viewportSize())
                painter.begin(svg)
                self.__qpage.mainFrame().render(painter)
                painter.end()
            else:
                image = QtGui.QImage(
                    self.__qpage.viewportSize(),
                    QtGui.QImage.Format_RGB32)
                painter.begin(image)
                self.__qpage.mainFrame().render(painter)
                painter.end()
                image.save(self._outfile)
        else:
            self.error = "unable to load the page"
            self._logger.error(self.error)
            try:
                os.unlink(self._outfile)
            except:
                self.__logger.exception("unable to unlink temporary file "
                    "'%s'" % self._outfile)

        if self.__qapp is not None:
            self.__qapp.exit()

        self._progress = 1.0


    def __load_progress(self, progress: int) -> None:
        """Qt slot called when the page load progress changes.

        Method:
            WebKitConverter.__load_progress(progress)
        Parameters :
            progress : int

        WebKitConverter.__load_progress(progress) -> None
        """
        self._logger.info("page %3d%% loaded", progress)
        self._progress = 0.01*progress


    def __str__(self) -> str:
        return "WebKitConverter(%s, %s)" % (self._infile, self._outfile)


    def __repr__(self) -> str:
        return "WebKitConverter(%s, %s)" % \
            (repr(self._infile), repr(self._outfile))


if __name__ == '__main__' and len(sys.argv) == 3:
    logging.basicConfig(level=logging.INFO)
    c = WebKitConverter(sys.argv[1], sys.argv[2])
    c.start()
    c.join()
