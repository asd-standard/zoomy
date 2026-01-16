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

"""PyZUI QMainWindow."""

import math
import os
from typing import Optional, Any

from PySide6 import QtCore, QtGui, QtWidgets

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QDialogButtonBox, QLabel
)

from pyzui import __init__ as PyZUI
from pyzui.objects.scene import scene as Scene
from pyzui.tilesystem import tilemanager as TileManager
from pyzui.objects.scene.qzui import QZUI
from pyzui.objects.mediaobjects.tiledmediaobject import TiledMediaObject
from pyzui.objects.mediaobjects.stringmediaobject import StringMediaObject
from pyzui.objects.mediaobjects.svgmediaobject import SVGMediaObject

from pyzui.windows.dialogwindows.dialogwindows import DialogWindows
from pyzui.logger import get_logger

class MainWindow(QtWidgets.QMainWindow):
    """
    Constructor :
        MainWindow(framerate, zoom_sensitivity)
    Parameters :
        framerate : int
        zoom_sensitivity : int

    MainWindow(framerate, zoom_sensitivity) --> None

    MainWindow windows are used for displaying the PyZUI interface.
    This class defines all the interface affordances, menus, widgets, frames etc.
    Framerate and zoom_sensitivity variables have to be declared the same value as
    in qzui class
    """

    def __init__(self, framerate: int = 20, zoom_sensitivity: int = 50) -> None:
        """
        Create a new MainWindow.
        """
        
        QtWidgets.QMainWindow.__init__(self)

        self.__logger = get_logger("MainWindow")

        self.__prev_dir = ''
        
        self.setWindowTitle("PyZUI")

        self.zui = QZUI(self, framerate, zoom_sensitivity)
        self.zui.start()        
        self.setCentralWidget(self.zui)

        self.__create_actions()
        self.__create_menus()

        self.zui.error.connect(self.__show_error)

        self.__action_open_scene_home()

    def sizeHint(self) -> QtCore.QSize:
        """
        Method :
            MainWindow.sizeHint()
        Parameters :
            None

        MainWindow.sizeHint() --> QtCore.QSize

        Return the recommended size for the widget.
        """
        return QtCore.QSize(1280,720)

    def minimumSizeHint(self) -> QtCore.QSize:
        """
        Method :
            MainWindow.minimumSizeHint()
        Parameters :
            None

        MainWindow.minimumSizeHint() --> QtCore.QSize

        Return the minimum size hint for the widget.
        """
        return QtCore.QSize(160,120)

    def __show_error(self, text: str, details: Any) -> None:
        """
        Method :
            MainWindow.__show_error(text, details)
        Parameters :
            text : str
            details : Any

        MainWindow.__show_error(text, details) --> None

        Show an error dialog with the given text and details.
        """
        dialog = QtWidgets.QMessageBox(self)
        dialog.setWindowTitle("PyZUI - Error")
        dialog.setText(text)
        dialog.setDetailedText(str(details))
        dialog.setIcon(QtWidgets.QMessageBox.Warning)
        dialog.exec()

    def __create_action(self, key: str, text: str, callback: Optional[Any] = None,
                        shortcut: Optional[str] = None, checkable: bool = False) -> None:
        """
        Method :
            MainWindow.__create_action(key, text, callback, shortcut, checkable)
        Parameters :
            key : str
            text : str
            callback : Optional[Any]
            shortcut : Optional[str]
            checkable : bool

        MainWindow.__create_action(key, text, callback, shortcut, checkable) --> None

        Create a QAction and store it in self.__action[key].
        """
        self.__action[key] = QtGui.QAction(text, self)

        if shortcut:
            self.__action[key].setShortcut(shortcut)

        if callback:
            self.__action[key].triggered.connect(callback)

        self.__action[key].setCheckable(checkable)

    def __action_new_scene(self) -> None:
        """
        Method :
            MainWindow.__action_new_scene()
        Parameters :
            None

        MainWindow.__action_new_scene() --> None

        Create a new scene.
        """
        self.zui.scene = Scene.new()

    def __action_open_scene(self) -> None:
        """
        Method :
            MainWindow.__action_open_scene()
        Parameters :
            None

        MainWindow.__action_open_scene() --> None

        Open a scene from the location chosen by the user in a file
        selection dialog.
        """
        filename = str(QtWidgets.QFileDialog.getOpenFileName(
            self, "Open scene", self.__prev_dir, "PyZUI Scenes (*.pzs)")[0])

        if filename:
            self.__prev_dir = os.path.dirname(filename)
            try:
                self.zui.scene = Scene.load_scene(filename)
            except Exception as e :
                self.__show_error("Unable to open scene ERROR in mainwindow.__action_open_scene \n", e)

    def __action_open_scene_home(self) -> None:
        """
        Method :
            MainWindow.__action_open_scene_home()
        Parameters :
            None

        MainWindow.__action_open_scene_home() --> None

        Open the Home scene.
        """
        try:
            self.zui.scene = Scene.load_scene(os.path.join("data", "home.pzs"))
        except Exception as e:
            self.__show_error('Unable to open the Home scene, ERROR in mainwindow.__action_open_scene_home \n', str(e))

    def __action_save_scene(self) -> None:
        """
        Method :
            MainWindow.__action_save_scene()
        Parameters :
            None

        MainWindow.__action_save_scene() --> None

        Save the scene to the location chosen by the user in a file
        selection dialog.
        """
        
        filename = str(QtWidgets.QFileDialog.getSaveFileName(
            self, "Save scene", os.path.join(self.__prev_dir, "scene.pzs"),
            "PyZUI Scenes (*.pzs)")[0])
        
        if filename:
            self.__prev_dir = os.path.dirname(filename)
            try:
                self.zui.scene.save(filename)
            except Exception as e:
                self.__show_error("Unable to save scene ERROR in mainwindow.__action_save_scene \n", e)

    def __action_save_screenshot(self) -> None:
        """
        Method :
            MainWindow.__action_save_screenshot()
        Parameters :
            None

        MainWindow.__action_save_screenshot() --> None

        Save a screenshot to the location chosen by the user in a file
        selection dialog.
        """
        filename = (QtWidgets.QFileDialog.getSaveFileName(
            self, "Save screenshot",
            os.path.join(self.__prev_dir, "screenshot.png"),
            "Images (*.bmp *.jpg *.jpeg *.png *.ppm *.tif *.tiff "
            "*.xbm *.xpm)"))

        if filename :
            #print(filename)
            self.__prev_dir = os.path.dirname(filename[0])
            try:
                pixmap = self.zui.grab()
                pixmap.save(filename[0])
            except Exception as e:
                self.__show_error("Unable to save screenshot ERROR in mainwindow.__action_save_screenshot", e)

    def __open_media(self, media_id: str, add: bool = True) -> Optional[Any]:
        """
        Method :
            MainWindow.__open_media(media_id, add)
        Parameters :
            media_id : str
            add : bool

        MainWindow.__open_media(media_id, add) --> Optional[Any]

        Open the media with the given media_id.

        If add is True then the media will be fit to the screen and added to
        the scene. Otherwise it will be returned.
        """
        try:
            if media_id.startswith('string:'):
                mediaobject = StringMediaObject(media_id, self.zui.scene)
            elif media_id.lower().endswith('.svg'):
                mediaobject = SVGMediaObject(media_id, self.zui.scene)
            else:
                mediaobject = TiledMediaObject(media_id, self.zui.scene, True)
                #print(vars(mediaobject))
        except Exception as e:
        
            self.__show_error("Unable to open media ERROR in mainwindow.__open_media \n", e)
        
        if add:
             
            w = self.zui.width()
            h = self.zui.height()
            try :
                mediaobject.fit((w/4, h/4, w*3/4, h*3/4))
                self.zui.scene.add(mediaobject)
            except Exception as e:
                self.__show_error("Error in opening media in __open_media \n", e)
        #This return actually never engages as add is set to True in the method input arguments
        else:
            return mediaobject
        

    def __action_open_media_local(self) -> None:
        """
        Method :
            MainWindow.__action_open_media_local()
        Parameters :
            None

        MainWindow.__action_open_media_local() --> None

        Open media from the location chosen by the user in a file
        selection dialog.
        """
        filename = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open local media", self.__prev_dir)
        #print(filename)
        if filename and filename[0]:
            #print('mainwindow-216-filename', filename)
            self.__prev_dir = os.path.dirname(filename[0])
            self.__open_media(filename[0])

    def __action_open_media_string(self) -> None:
        """
        Method :
            MainWindow.__action_open_media_string()
        Parameters :
            None

        MainWindow.__action_open_media_string() --> None

        Render string given by the user in an input dialog.
        """
        dialog = DialogWindows.open_new_string_input_dialog()
        try :
            ok, uri = dialog._run_dialog()
        except Exception as e :
            self.__show_error('Error loading Media String: \n', e)
            ok = False
            uri = False
        if ok and uri:
            self.__open_media(uri)

    # Supported file extensions for media opening
    # SVG handled by SVGMediaObject, PDF/PPM/images handled by TiledMediaObject
    SUPPORTED_EXTENSIONS = {
        '.svg',                         # SVGMediaObject
        '.pdf',                         # PDFConverter
        '.ppm',                         # Direct PPM support
        '.jpg', '.jpeg',                # VipsConverter - JPEG
        '.png',                         # VipsConverter - PNG
        '.gif',                         # VipsConverter - GIF
        '.tif', '.tiff',                # VipsConverter - TIFF
        '.webp',                        # VipsConverter - WebP
        '.bmp',                         # VipsConverter - BMP
        '.heic', '.heif',               # VipsConverter - HEIC
        '.avif',                        # VipsConverter - AVIF
        '.jxl',                         # VipsConverter - JPEG XL
    }

    # Maximum file size for PDF files (2 MB)
    MAX_PDF_SIZE_BYTES = 2 * 1024 * 1024

    def __action_open_media_dir(self) -> None:
        """
        Method :
            MainWindow.__action_open_media_dir()
        Parameters :
            None

        MainWindow.__action_open_media_dir() --> None

        Open media from the directory chosen by the user in a file
        selection dialog. Only files with supported extensions are opened.
        PDF files larger than MAX_PDF_SIZE_BYTES are skipped.
        """
        directory = str(QtWidgets.QFileDialog.getExistingDirectory(
            self, "Open media directory", self.__prev_dir))

        if directory:
            self.__prev_dir = os.path.dirname(directory)
            media = []
            for filename in os.listdir(directory):
                filename = os.path.join(directory, filename)
                if not os.path.isdir(filename):
                    # Check if file has a supported extension
                    ext = os.path.splitext(filename)[1].lower()
                    if ext not in self.SUPPORTED_EXTENSIONS:
                        continue
                    # Skip PDF files larger than 2 MB
                    if ext == '.pdf' and os.path.getsize(filename) > self.MAX_PDF_SIZE_BYTES:
                        continue
                    mediaobject = self.__open_media(filename, False)
                    if mediaobject:
                        media.append(mediaobject)

            cells_per_side = int(math.ceil(math.sqrt(len(media))))
            cellsize = float(min(self.zui.width(),
                                 self.zui.height())) / cells_per_side
            innersize = 0.9 * cellsize
            centre = (self.zui.width()/2, self.zui.height()/2)
            bbox = (centre[0] - innersize/2, centre[1] - innersize/2,
                    centre[0] + innersize/2, centre[1] + innersize/2)
            grid_centre = 0.5 * cells_per_side

            for y in range(cells_per_side):
                for x in range(cells_per_side):
                    if not media: break
                    mediaobject = media.pop(0)

                    ## resize and centre object
                    mediaobject.fit(bbox)
                    mediaobject.centre = centre

                    ## aim object towards grid cell
                    mediaobject.aim('x', (x+0.5 - grid_centre) * cellsize)
                    mediaobject.aim('y', (y+0.5 - grid_centre) * cellsize)

                    self.zui.scene.add(mediaobject)

    def __action_set_fps(self, act: QtGui.QAction) -> None:
        """
        Method :
            MainWindow.__action_set_fps(act)
        Parameters :
            act : QtGui.QAction

        MainWindow.__action_set_fps(act) --> None

        Set the framerate to the value specified in act.
        """
        self.zui.framerate = int(act.fps/2)

    def __action_fullscreen(self) -> None:
        """
        Method :
            MainWindow.__action_fullscreen()
        Parameters :
            None

        MainWindow.__action_fullscreen() --> None

        Toggles fullscreen mode.
        """
        self.setWindowState(self.windowState() ^ QtCore.Qt.WindowFullScreen)

    def __action_about(self) -> None:
        """
        Method :
            MainWindow.__action_about()
        Parameters :
            None

        MainWindow.__action_about() --> None

        Display the PyZUI about dialog.
        """
        QtWidgets.QMessageBox.about(self,
            "PyZUI %s" % PyZUI.__version__,
            PyZUI.__doc__ + '\n' +
            PyZUI.__copyright__ + '\n' +
            PyZUI.__copyright_notice__)

    def __action_about_qt(self) -> None:
        """
        Method :
            MainWindow.__action_about_qt()
        Parameters :
            None

        MainWindow.__action_about_qt() --> None

        Display the Qt about dialog.
        """
        QtWidgets.QMessageBox.aboutQt(self)

    def __action_save_and_quit(self) -> None:
        """
        Method :
            MainWindow.__action_save_and_quit()
        Parameters :
            None

        MainWindow.__action_save_and_quit() --> None

        Calls the __action_save_scene and then quit.
        """
        self.__action_save_scene()
        QtWidgets.QApplication.closeAllWindows()
    
    def __action_confirm_quit(self) -> None:
        """
        Method :
            MainWindow.__action_confirm_quit()
        Parameters :
            None

        MainWindow.__action_confirm_quit() --> None

        Ask user if it really wants to quit.
        """
        # Create the dialog window
        dialog = QDialog()
        dialog.setWindowTitle("Confirm Quit")
        
        # Add label to the layout
        label = QLabel("Are you sure you want to quit?")
        
        buttons = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No,  dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        save_button = QPushButton('Save and Quit', dialog)
        save_button.setIcon(QtGui.QIcon.fromTheme("document-save"))
        
        save_button.clicked.connect(self.__action_save_and_quit)
        

        buttons.addButton(save_button, QDialogButtonBox.ActionRole)

        layout = QVBoxLayout(dialog)
        layout.addWidget(label)
        layout.addWidget(buttons)

        # Make dialog wrap content instead of having fixed large size
        dialog.adjustSize()
        dialog.setFixedSize(dialog.sizeHint())

        response = dialog.exec()

        if response  == QDialog.Accepted :
            QtWidgets.QApplication.closeAllWindows() 
        elif response == QDialog.Rejected :
            dialog.close()
    
    def __action_set_zoom_sensitivity(self) -> None:
        """
        Method :
            MainWindow.__action_set_zoom_sensitivity()
        Parameters :
            None

        MainWindow.__action_set_zoom_sensitivity() --> None

        Set the zoom sensitivity for the ZUI.
        """
        ok_pressed, text_input = DialogWindows._open_zoom_sensitivity_input_dialog(self.zui.zoom_sensitivity)

        '''
        dialog = QInputDialog()
        dialog.setWindowTitle("Set zoom sensitivity")
        
        dialog.resize(300, 80)  # Set the size here

        ok_pressed = dialog.exec()
        text_input = dialog.textValue()
        '''
           
        if ok_pressed and text_input :
            if int(text_input) < 0 or int(text_input) > 100 :
                self.__show_error("Sensitivity input must range from 0 to 100, current")
            elif int(text_input) == 0 :
                self.zui.zoom_sensitivity = 1000
            else :
                self.zui.zoom_sensitivity = int(1000 / int(text_input)) 
            

    def __create_actions(self) -> None:
        """
        Method :
            MainWindow.__create_actions()
        Parameters :
            None

        MainWindow.__create_actions() --> None

        Create the QActions required for the interface.
        """
        self.__action = {}

        self.__create_action('new_scene', "&New Scene",
            self.__action_new_scene, "Ctrl+N")
        self.__create_action('open_scene', "&Open Scene",
            self.__action_open_scene, "Ctrl+O")
        self.__create_action('open_scene_home', "Open &Home Scene",
            self.__action_open_scene_home, "Ctrl+Home")
        self.__create_action('save_scene', "&Save Scene",
            self.__action_save_scene, "Ctrl+S")
        self.__create_action('save_screenshot', "Save Screens&hot",
            self.__action_save_screenshot, "Ctrl+H")
        self.__create_action('open_media_local', "Open &Local Media",
            self.__action_open_media_local, "Ctrl+L")
        self.__create_action('open_media_string', "Open new &String",
            self.__action_open_media_string, "Ctrl+U")
        self.__create_action('open_media_dir', "Open Media &Directory",
            self.__action_open_media_dir, "Ctrl+D")
        self.__create_action('quit', "&Quit",
            self.__action_confirm_quit, "Ctrl+Q")
        self.__create_action('set_zoom_sensitivity', "Adjust &Sensitivity",
            self.__action_set_zoom_sensitivity)

        self.__action['group_set_fps'] = QtGui.QActionGroup(self)
        for i in range(10, 41, 10):
            key = "set_fps_%d" % i
            self.__create_action(key, "%d FPS" % i, checkable=True)
            self.__action[key].fps = i
            self.__action['group_set_fps'].addAction(self.__action[key])
        
        
        self.__action['group_set_fps'].triggered[QtGui.QAction].connect(self.__action_set_fps)
        self.__action['set_fps_%d' % self.zui.framerate].setChecked(True)

        self.__create_action('fullscreen', "&Fullscreen",
            self.__action_fullscreen, "Ctrl+F")

        self.__create_action('about', "&About", self.__action_about)
        self.__create_action('about_qt', "About &Qt", self.__action_about_qt)

    def __create_menus(self) -> None:
        """
        Method :
            MainWindow.__create_menus()
        Parameters :
            None

        MainWindow.__create_menus() --> None

        Create the menus.
        """
        self.__menu = {}

        self.__menu['file'] = self.menuBar().addMenu("&File")
        self.__menu['file'].addAction(self.__action['new_scene'])
        self.__menu['file'].addAction(self.__action['open_scene'])
        self.__menu['file'].addAction(self.__action['open_scene_home'])
        self.__menu['file'].addAction(self.__action['save_scene'])
        self.__menu['file'].addAction(self.__action['save_screenshot'])
        self.__menu['file'].addAction(self.__action['open_media_local'])
        self.__menu['file'].addAction(self.__action['open_media_string'])
        self.__menu['file'].addAction(self.__action['open_media_dir'])
        self.__menu['file'].addAction(self.__action['quit'])

        self.__menu['view'] = self.menuBar().addMenu("&View")
        self.__menu['set_fps'] = self.__menu['view'].addMenu("Set &Framerate")
        self.__menu['set_fps'].addActions(self.__action['group_set_fps'].actions())
        self.__menu['view'].addAction(self.__action['set_zoom_sensitivity'])
        self.__menu['view'].addAction(self.__action['fullscreen'])

        self.__menu['help'] = self.menuBar().addMenu("&Help")
        self.__menu['help'].addAction(self.__action['about'])
        self.__menu['help'].addAction(self.__action['about_qt'])

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        """
        Method :
            MainWindow.showEvent(event)
        Parameters :
            event : QtGui.QShowEvent

        MainWindow.showEvent(event) --> None

        Handle show event by focusing the QZUI widget.
        """
        ## focus the QZUI widget whenever this window is shown
        self.zui.setFocus(QtCore.Qt.OtherFocusReason)
