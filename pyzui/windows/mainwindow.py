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
from logging import Logger
from typing import Any

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QPushButton, QVBoxLayout

import pyzui as PyZUI
from pyzui.config import ConfigManager, ValidationError
from pyzui.logger import get_logger
from pyzui.objects.mediaobjects.stringmediaobject import StringMediaObject
from pyzui.objects.mediaobjects.svgmediaobject import SVGMediaObject
from pyzui.objects.mediaobjects.tiledmediaobject import TiledMediaObject
from pyzui.objects.scene import scene as Scene
from pyzui.objects.scene.qzui import QZUI
from pyzui.objects.scene.qzui import QZUI as QZUIType
from pyzui.windows.dialogwindows.dialogwindows import DialogWindows

# Type aliases
ActionKey = str
MenuKey = str
MediaID = str


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

    def __init__(
        self,
        framerate: int = 20,
        zoom_sensitivity: int = 50,
        icon: QtGui.QIcon | None = None,
        config: dict[str, Any] | None = None,
        autosave_config: dict[str, Any] | None = None,
    ) -> None:
        """
        Create a new MainWindow.

        Args:
            framerate: Frame rate for the QZUI widget
            zoom_sensitivity: Zoom sensitivity for the QZUI widget
            icon: Optional QIcon to set as window icon
            config: Optional full application configuration dictionary
            autosave_config: Optional autosave configuration dictionary
        """

        QtWidgets.QMainWindow.__init__(self)

        self.__logger: Logger = get_logger("MainWindow")
        self.__prev_dir: str = ""
        self.__action: dict[ActionKey, QtGui.QAction] = {}
        self.__menu: dict[MenuKey, QtWidgets.QMenu] = {}
        self.__config: dict[str, Any] = config or {}
        self.__autosave_config: dict[str, Any] | None = autosave_config

        self.setWindowTitle("PyZUI")

        # Set window icon if provided
        if icon and not icon.isNull():
            self.setWindowIcon(icon)
            self.__logger.debug("Window icon set in MainWindow constructor")

        # Create QTabWidget as central widget for multi-tab support
        self.__tab_widget = QtWidgets.QTabWidget()
        self.__tab_widget.setTabsClosable(True)
        self.__tab_widget.setMovable(True)
        self.__tab_widget.setDocumentMode(True)
        self.setCentralWidget(self.__tab_widget)

        # Track QZUI instances per tab (parallel to tab indices)
        self.__zui_tabs: list[QZUIType] = []
        self.__framerate = framerate
        self.__zoom_sensitivity = zoom_sensitivity

        # Connect tab signals
        self.__tab_widget.tabCloseRequested.connect(self._close_tab)
        self.__tab_widget.currentChanged.connect(self._on_tab_changed)

        self.__create_actions()
        self.__create_menus()

        # Create the first tab and load home scene
        self._add_tab("Home")
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
        return QtCore.QSize(1280, 720)

    def minimumSizeHint(self) -> QtCore.QSize:
        """
        Method :
            MainWindow.minimumSizeHint()
        Parameters :
            None

        MainWindow.minimumSizeHint() --> QtCore.QSize

        Return the minimum size hint for the widget.
        """
        return QtCore.QSize(160, 120)

    @property
    def current_zui(self) -> "QZUIType":
        """
        Property :
            MainWindow.current_zui
        Parameters :
            None

        MainWindow.current_zui --> QZUI

        Return the QZUI instance of the currently active tab.
        """
        index = self.__tab_widget.currentIndex()
        if index < 0 or index >= len(self.__zui_tabs):
            raise IndexError("No active tab")
        return self.__zui_tabs[index]  # type: ignore[no-any-return]

    @property
    def zui(self) -> "QZUIType":
        """
        Backward-compatible property returning the current tab's QZUI.
        """
        return self.current_zui

    def _add_tab(self, title: str = "Untitled") -> int:
        """
        Method :
            MainWindow._add_tab(title)
        Parameters :
            title : str

        MainWindow._add_tab(title) --> int

        Create a new tab with a fresh QZUI and Scene. Returns the tab index.
        """
        zui = QZUI(self, self.__framerate, self.__zoom_sensitivity, self.__config, self.__autosave_config)
        zui.error.connect(self.__show_error)
        self.__zui_tabs.append(zui)
        index = self.__tab_widget.addTab(zui, title)
        self.__tab_widget.setCurrentIndex(index)
        zui.setFocus(QtCore.Qt.FocusReason.OtherFocusReason)
        return index  # type: ignore[no-any-return]

    def _close_tab(self, index: int) -> None:
        """
        Method :
            MainWindow._close_tab(index)
        Parameters :
            index : int

        MainWindow._close_tab(index) --> None

        Close the tab at the given index. Prevents closing the last remaining tab.
        Stops autosave and purges tiles for the closed scene.
        """
        if self.__tab_widget.count() <= 1:
            return

        zui = self.__zui_tabs[index]
        scene = zui.scene

        # Stop autosave on the closing scene
        if hasattr(scene, "_Scene__autosave_manager"):
            try:
                mgr = scene._Scene__autosave_manager
                if mgr._autosave_active:
                    mgr.disable_autosave()
            except Exception:
                pass

        # Purge tiles for the closing scene
        from pyzui.tilesystem import tilemanager as TileManager

        TileManager.purge()

        self.__tab_widget.removeTab(index)
        del self.__zui_tabs[index]

    def _on_tab_changed(self, index: int) -> None:
        """
        Method :
            MainWindow._on_tab_changed(index)
        Parameters :
            index : int

        MainWindow._on_tab_changed(index) --> None

        Handle tab change: set focus on the new active QZUI and update window title.
        """
        if index < 0 or index >= len(self.__zui_tabs):
            return

        zui = self.__zui_tabs[index]
        zui.setFocus(QtCore.Qt.FocusReason.OtherFocusReason)

        # Sync render order menu check state with current scene
        if "render_order_smaller_top" in self.__action:
            scene = zui.scene
            is_smaller_top = scene.render_order == "smaller_on_top"
            self.__action["render_order_smaller_top"].setChecked(is_smaller_top)

        self.__update_window_title()

    def __update_window_title(self) -> None:
        """Update the window title to reflect the current tab."""
        title = self.__tab_widget.tabText(self.__tab_widget.currentIndex())
        self.setWindowTitle(f"PyZUI — {title}")

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

    def __create_action(
        self,
        key: ActionKey,
        text: str,
        callback: Any | None = None,
        shortcut: str | None = None,
        checkable: bool = False,
    ) -> None:
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

        Create a new scene in the current tab.
        """
        zui = self.current_zui
        # Stop autosave on current scene before creating new one
        if hasattr(zui.scene, "_Scene__autosave_manager"):
            try:
                logger = get_logger("MainWindow")
                logger.debug("Stopping autosave on current scene before creating new scene")
                zui.scene._Scene__autosave_manager.disable_autosave()
            except Exception as e:
                logger = get_logger("MainWindow")
                logger.debug(f"Error stopping autosave on current scene: {e}")

        zui.scene = Scene.new(config=self.__config)
        current_index = self.__tab_widget.currentIndex()
        self.__tab_widget.setTabText(current_index, "Untitled")
        self.__update_window_title()

    def __action_new_tab(self) -> None:
        """
        Method :
            MainWindow.__action_new_tab()
        Parameters :
            None

        MainWindow.__action_new_tab() --> None

        Create a new tab with a fresh scene.
        """
        self._add_tab("Untitled")

    def __action_close_tab(self) -> None:
        """
        Method :
            MainWindow.__action_close_tab()
        Parameters :
            None

        MainWindow.__action_close_tab() --> None

        Close the current tab.
        """
        self._close_tab(self.__tab_widget.currentIndex())

    def __action_open_scene(self) -> None:
        """
        Method :
            MainWindow.__action_open_scene()
        Parameters :
            None

        MainWindow.__action_open_scene() --> None

        Open a scene from the location chosen by the user in a file
        selection dialog into the current tab.
        """
        filename = str(
            QtWidgets.QFileDialog.getOpenFileName(self, "Open scene", self.__prev_dir, "PyZUI Scenes (*.pzs)")[0]
        )

        if filename:
            self.__prev_dir = os.path.dirname(filename)
            try:
                zui = self.current_zui
                # Stop autosave on current scene before opening new one
                if hasattr(zui.scene, "_Scene__autosave_manager"):
                    try:
                        logger = get_logger("MainWindow")
                        logger.debug("Stopping autosave on current scene before opening new scene")
                        zui.scene._Scene__autosave_manager.disable_autosave()
                    except Exception as e:
                        logger = get_logger("MainWindow")
                        logger.debug(f"Error stopping autosave on current scene: {e}")

                zui.scene = Scene.load_scene(filename)
                current_index = self.__tab_widget.currentIndex()
                self.__tab_widget.setTabText(current_index, os.path.basename(filename))
                self.__update_window_title()
            except Exception as e:
                self.__show_error("Unable to open scene ERROR in mainwindow.__action_open_scene \n", e)

    def __action_open_scene_home(self) -> None:
        """
        Method :
            MainWindow.__action_open_scene_home()
        Parameters :
            None

        MainWindow.__action_open_scene_home() --> None

        Open the Home scene in the current tab.
        """
        try:
            zui = self.current_zui
            zui.scene = Scene.load_scene(os.path.join("data", "home.pzs"))
            current_index = self.__tab_widget.currentIndex()
            self.__tab_widget.setTabText(current_index, "Home")
            self.__update_window_title()
        except Exception as e:
            self.__show_error("Unable to open the Home scene, ERROR in mainwindow.__action_open_scene_home \n", str(e))

    def __action_import_scene(self) -> None:
        """
        Method :
            MainWindow.__action_import_scene()
        Parameters :
            None

        MainWindow.__action_import_scene() --> None

        Import a scene from the location chosen by the user in a file
        selection dialog, merging it into the current tab's scene.
        """
        filename = str(
            QtWidgets.QFileDialog.getOpenFileName(self, "Import scene", self.__prev_dir, "PyZUI Scenes (*.pzs)")[0]
        )

        if filename:
            self.__prev_dir = os.path.dirname(filename)
            try:
                self.current_zui.scene.import_scene(filename)
            except Exception as e:
                self.__show_error("Unable to import scene ERROR in mainwindow.__action_import_scene \n", e)

    def __action_save_scene(self) -> None:
        """
        Method :
            MainWindow.__action_save_scene()
        Parameters :
            None

        MainWindow.__action_save_scene() --> None

        Save the scene or selected mediaobjects to the location chosen by
        the user in a file selection dialog.

        If mediaobjects are selected, saves only the selection with "0 0 0"
        as the first line in the PZS file, preserving relative positions.
        If no selection, saves the entire scene.
        """
        scene = self.current_zui.scene

        # Determine if we have a valid selection
        has_selection = False
        if scene.selection:
            if isinstance(scene.selection, list):
                has_selection = len(scene.selection) > 0
            else:
                has_selection = True  # Single object is selected

        # Choose appropriate dialog title and default filename
        if has_selection:
            dialog_title = "Save Selection"
            default_name = "selection.pzs"
        else:
            dialog_title = "Save Scene"
            default_name = "scene.pzs"

        filename = str(
            QtWidgets.QFileDialog.getSaveFileName(
                self, dialog_title, os.path.join(self.__prev_dir, default_name), "PyZUI Scenes (*.pzs)"
            )[0]
        )

        if filename:
            self.__prev_dir = os.path.dirname(filename)
            try:
                if has_selection:
                    scene.save_selection(filename)
                else:
                    scene.save(filename)
                current_index = self.__tab_widget.currentIndex()
                self.__tab_widget.setTabText(current_index, os.path.basename(filename))
                self.__update_window_title()
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
        filename = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save screenshot",
            os.path.join(self.__prev_dir, "screenshot.png"),
            "Images (*.bmp *.jpg *.jpeg *.png *.ppm *.tif *.tiff *.xbm *.xpm)",
        )

        if filename:
            self.__prev_dir = os.path.dirname(filename[0])
            try:
                pixmap = self.current_zui.grab()
                pixmap.save(filename[0])
            except Exception as e:
                self.__show_error("Unable to save screenshot ERROR in mainwindow.__action_save_screenshot", e)

    def __open_media(self, media_id: str, add: bool = True) -> Any | None:  # type: ignore[return]
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
        zui = self.current_zui
        try:
            if media_id.startswith("string:"):
                mediaobject = StringMediaObject(media_id, zui.scene)
            elif media_id.lower().endswith(".svg") or media_id.startswith("svg_"):
                mediaobject = SVGMediaObject(media_id, zui.scene)  # type: ignore[assignment]
            else:
                mediaobject = TiledMediaObject(media_id, zui.scene, True)  # type: ignore[assignment]
        except Exception as e:
            self.__show_error("Unable to open media ERROR in mainwindow.__open_media \n", e)

        if add:
            w = zui.width()
            h = zui.height()

            try:
                mediaobject.fit((w // 4, h // 4, w * 3 // 4, h * 3 // 4))
                zui.scene.add(mediaobject)
            except Exception as e:
                self.__show_error("Error in opening media in __open_media \n", e)
        # This return actually never engages as add is set to True in the method input arguments
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
        filename = QtWidgets.QFileDialog.getOpenFileName(self, "Open local media", self.__prev_dir)

        if filename and filename[0]:
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
        try:
            ok, uri = dialog._run_dialog()
        except Exception as e:
            self.__show_error("Error loading Media String: \n", e)
            ok = False
            uri = ""
        if ok and uri:
            self.__open_media(uri)

    def __action_open_svg_pick(self) -> None:
        """
        Method :
            MainWindow.__action_open_svg_pick()
        Parameters :
            None

        MainWindow.__action_open_svg_pick() --> None

        Open SVG file selected by the user in a picker dialog.
        """
        dialog = DialogWindows.open_svg_picker_input_dialog()
        try:
            ok, filepath = dialog._run_dialog()
            self.__logger.debug("SVG filepath: %s", filepath)
        except Exception as e:
            self.__show_error("Error loading SVG: \n", e)
            ok = False
            filepath = ""
        if ok and filepath:
            self.__open_media(filepath)

    # Supported file extensions for media opening
    # SVG handled by SVGMediaObject, PDF/PPM/images handled by TiledMediaObject
    SUPPORTED_EXTENSIONS = {
        ".svg",  # SVGMediaObject
        ".pdf",  # PDFConverter
        ".ppm",  # Direct PPM support
        ".jpg",
        ".jpeg",  # VipsConverter - JPEG
        ".png",  # VipsConverter - PNG
        ".gif",  # VipsConverter - GIF
        ".tif",
        ".tiff",  # VipsConverter - TIFF
        ".webp",  # VipsConverter - WebP
        ".bmp",  # VipsConverter - BMP
        ".heic",
        ".heif",  # VipsConverter - HEIC
        ".avif",  # VipsConverter - AVIF
        ".jxl",  # VipsConverter - JPEG XL
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
        directory = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Open media directory", self.__prev_dir))

        if directory:
            self.__prev_dir = os.path.dirname(directory)
            zui = self.current_zui
            media = []
            for filename in os.listdir(directory):
                filename = os.path.join(directory, filename)
                if not os.path.isdir(filename):
                    # Check if file has a supported extension
                    ext = os.path.splitext(filename)[1].lower()
                    if ext not in self.SUPPORTED_EXTENSIONS:
                        continue
                    # Skip PDF files larger than 2 MB
                    if ext == ".pdf" and os.path.getsize(filename) > self.MAX_PDF_SIZE_BYTES:
                        continue
                    mediaobject = self.__open_media(filename, False)
                    if mediaobject:
                        media.append(mediaobject)

            cells_per_side = math.ceil(math.sqrt(len(media)))
            cellsize = float(min(zui.width(), zui.height())) // cells_per_side
            innersize = 0.9 * cellsize
            centre = (zui.width() // 2, zui.height() // 2)
            bbox = (
                centre[0] - innersize // 2,
                centre[1] - innersize // 2,
                centre[0] + innersize // 2,
                centre[1] + innersize // 2,
            )
            grid_centre = 0.5 * cells_per_side

            for y in range(cells_per_side):
                for x in range(cells_per_side):
                    if not media:
                        break
                    mediaobject = media.pop(0)

                    ## resize and centre object
                    mediaobject.fit(bbox)
                    mediaobject.centre = centre

                    ## aim object towards grid cell
                    mediaobject.aim("x", (x + 0.5 - grid_centre) * cellsize)
                    mediaobject.aim("y", (y + 0.5 - grid_centre) * cellsize)

                    zui.scene.add(mediaobject)

    def __action_set_fps(self, act: QtGui.QAction) -> None:
        """
        Method :
            MainWindow.__action_set_fps(act)
        Parameters :
            act : QtGui.QAction

        MainWindow.__action_set_fps(act) --> None

        Set the framerate to the value specified in act.
        """
        self.current_zui.framerate = int(act.fps // 2)

    def __action_fullscreen(self) -> None:
        """
        Method :
            MainWindow.__action_fullscreen()
        Parameters :
            None

        MainWindow.__action_fullscreen() --> None

        Toggles fullscreen mode.
        """
        self.setWindowState(self.windowState() ^ QtCore.Qt.WindowState.WindowFullScreen)

    def __action_toggle_render_order(self) -> None:
        """
        Method :
            MainWindow.__action_toggle_render_order()
        Parameters :
            None

        MainWindow.__action_toggle_render_order() --> None

        Toggle render order between smaller_on_top and larger_on_top.
        """
        action = self.__action["render_order_smaller_top"]
        new_mode = "smaller_on_top" if action.isChecked() else "larger_on_top"
        scene = self.current_zui.scene
        scene.set_render_order(new_mode)

        # Persist to config
        try:
            config_manager = ConfigManager()
            full_config = config_manager.load()
            full_config.setdefault("render", {})["order"] = new_mode
            config_manager.save(full_config)
            self.__logger.debug(f"Render order set to '{new_mode}'")
        except ValidationError as e:
            self.__logger.error(f"Cannot save render order: {e}")
        except Exception as e:
            self.__show_error(f"Failed to save render order: {e!s}", e)

    def __action_about(self) -> None:
        """
        Method :
            MainWindow.__action_about()
        Parameters :
            None

        MainWindow.__action_about() --> None

        Display the PyZUI about dialog.
        """
        QtWidgets.QMessageBox.about(
            self,
            f"PyZUI {PyZUI.__version__}",
            PyZUI.__doc__ + "\n" + PyZUI.__copyright__ + "\n" + PyZUI.__copyright_notice__,
        )

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

        buttons = QDialogButtonBox(QDialogButtonBox.Yes | QDialogButtonBox.No, dialog)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        save_button = QPushButton("Save and Quit", dialog)
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

        if response == QDialog.Accepted:
            QtWidgets.QApplication.closeAllWindows()
        elif response == QDialog.Rejected:
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
        ok_pressed, text_input = DialogWindows.open_zoom_sensitivity_input_dialog(self.current_zui.zoom_sensitivity)

        """
        dialog = QInputDialog()
        dialog.setWindowTitle("Set zoom sensitivity")

        dialog.resize(300, 80)  # Set the size here

        ok_pressed = dialog.exec()
        text_input = dialog.textValue()
        """

        if ok_pressed and text_input:
            try:
                value = int(text_input)
            except ValueError:
                self.__show_error("Sensitivity input must be an integer", "")
                return
            current_sens = (
                int(1000 / self.current_zui.zoom_sensitivity) if self.current_zui.zoom_sensitivity != 0 else 0
            )
            if value < 0 or value > 100:
                self.__show_error(f"Sensitivity input must range from 0 to 100, current: {current_sens}", "")
            elif value == 0:
                self.current_zui.zoom_sensitivity = 1000
            else:
                self.current_zui.zoom_sensitivity = int(1000 // value)

    def __action_copy(self) -> None:
        """
        Method :
            MainWindow.__action_copy()
        Parameters :
            None

        MainWindow.__action_copy() --> None

        Handle Copy menu action.
        """
        if self.current_zui.scene.selection:
            self.current_zui.scene.copy_selection()

    def __action_paste(self) -> None:
        """
        Method :
            MainWindow.__action_paste()
        Parameters :
            None

        MainWindow.__action_paste() --> None

        Handle Paste menu action.
        """
        zui = self.current_zui
        # Paste at viewport centre (center of visible area)
        # Calculate viewport centre in scene coordinates
        # Viewport centre is at (width/2, height/2) in screen coordinates
        viewport_centre_x = zui.width() / 2
        viewport_centre_y = zui.height() / 2

        # Convert screen coordinates to scene coordinates
        # Formula: scene_x = (screen_x - scene.origin[0]) * (2 ** -scene.zoomlevel)
        scene = zui.scene
        scene_origin = scene.origin
        scene_zoomlevel = scene.zoomlevel
        scale = 2**-scene_zoomlevel
        scene_x = (viewport_centre_x - scene_origin[0]) * scale
        scene_y = (viewport_centre_y - scene_origin[1]) * scale

        zui.scene.paste((scene_x, scene_y))

    def __action_autosave_settings(self) -> None:
        """
        Method :
            MainWindow.__action_autosave_settings()
        Parameters :
            None

        MainWindow.__action_autosave_settings() --> None

        Handle Autosave Settings menu action.
        """
        # Get current autosave configuration from scene
        scene = self.current_zui.scene
        current_config = scene.get_autosave_config() if hasattr(scene, "get_autosave_config") else None

        # Show dialog to get new configuration
        from pyzui.windows.dialogwindows.autosavesettingsdialog import AutosaveSettingsDialog

        new_config = AutosaveSettingsDialog.get_autosave_settings(self, current_config)

        if new_config is not None:
            # Update scene configuration
            if hasattr(scene, "set_autosave_config"):
                scene.set_autosave_config(new_config)

            # Save to user config using ConfigManager
            try:
                config_manager = ConfigManager()
                # Load current config to preserve other sections
                full_config = config_manager.load()
                # Update autosave section, preserving keys not in the dialog
                # (e.g. backup_dir which is only configurable via JSON)
                full_config["autosave"].update(new_config)
                # Save back
                config_manager.save(full_config)
                self.__logger.info("Autosave settings saved to user configuration")
            except ValidationError as e:
                self.__logger.error(f"Cannot save autosave settings: {e}")
                QtWidgets.QMessageBox.warning(self, "Configuration Error", f"Cannot save settings: {e}")
            except Exception as e:
                self.__show_error(f"Failed to save autosave settings: {e!s}", e)

    def __action_zoom_settings(self) -> None:
        """
        Method :
            MainWindow.__action_zoom_settings()
        Parameters :
            None

        MainWindow.__action_zoom_settings() --> None

        Handle Zoom Settings menu action.
        """
        # Get current zoom configuration
        config_manager = ConfigManager()
        current_config = config_manager.load()
        zoom_config = current_config.get("zoom", {})

        # Show dialog to get new configuration
        from pyzui.windows.dialogwindows.zoomsettingsdialog import ZoomSettingsDialog

        new_config = ZoomSettingsDialog.get_zoom_settings(self, zoom_config)

        if new_config is not None:
            # Update config
            current_config["zoom"] = new_config
            try:
                config_manager.save(current_config)
                self.__logger.info("Zoom settings saved to user configuration")
            except ValidationError as e:
                self.__logger.error(f"Cannot save zoom settings: {e}")
                QtWidgets.QMessageBox.warning(self, "Configuration Error", f"Cannot save settings: {e}")
            except Exception as e:
                self.__show_error(f"Failed to save zoom settings: {e!s}", e)

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

        self.__create_action("new_tab", "&New Tab", self.__action_new_tab, "Ctrl+T")
        self.__create_action("close_tab", "&Close Tab", self.__action_close_tab, "Ctrl+W")
        self.__create_action("new_scene", "&New Scene", self.__action_new_scene, "Ctrl+N")
        self.__create_action("open_scene", "&Open Scene", self.__action_open_scene, "Ctrl+O")
        self.__create_action("import_scene", "&Import Scene", self.__action_import_scene, "Ctrl+I")
        self.__create_action("open_scene_home", "Open &Home Scene", self.__action_open_scene_home, "Ctrl+Home")
        self.__create_action("save_scene", "&Save Scene", self.__action_save_scene, "Ctrl+S")
        self.__create_action("save_screenshot", "Save Screens&hot", self.__action_save_screenshot, "Ctrl+H")
        self.__create_action("open_media_local", "Open &Local Media", self.__action_open_media_local, "Ctrl+L")
        self.__create_action("open_media_string", "Open new &String", self.__action_open_media_string, "Ctrl+U")
        self.__create_action("open_svg_pick", "Open new &SVG", self.__action_open_svg_pick, "Ctrl+G")
        self.__create_action("open_media_dir", "Open Media &Directory", self.__action_open_media_dir, "Ctrl+D")
        self.__create_action("quit", "&Quit", self.__action_confirm_quit, "Ctrl+Q")
        self.__create_action("set_zoom_sensitivity", "Adjust &Sensitivity", self.__action_set_zoom_sensitivity)

        self.__action["group_set_fps"] = QtGui.QActionGroup(self)
        for i in range(10, 41, 10):
            key = "set_fps_%d" % i
            self.__create_action(key, "%d FPS" % i, checkable=True)
            self.__action[key].fps = i
            self.__action["group_set_fps"].addAction(self.__action[key])

        self.__action["group_set_fps"].triggered[QtGui.QAction].connect(self.__action_set_fps)
        self.__action["set_fps_%d" % self.__framerate].setChecked(True)

        self.__create_action("fullscreen", "&Fullscreen", self.__action_fullscreen, "Ctrl+F")

        self.__create_action(
            "render_order_smaller_top",
            "Render Order: &Smaller on Top",
            self.__action_toggle_render_order,
            "Ctrl+R",
            checkable=True,
        )
        self.__action["render_order_smaller_top"].setChecked(True)

        self.__create_action("copy", "Copy &SVG", self.__action_copy, "Ctrl+C")
        self.__create_action("paste", "Paste &SVG", self.__action_paste, "Ctrl+V")

        self.__create_action("autosave_settings", "&Autosave Settings", self.__action_autosave_settings)
        self.__create_action("zoom_settings", "&Zoom Settings", self.__action_zoom_settings)

        self.__create_action("about", "&About", self.__action_about)
        self.__create_action("about_qt", "About &Qt", self.__action_about_qt)

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

        self.__menu["file"] = self.menuBar().addMenu("&File")
        self.__menu["file"].addAction(self.__action["new_tab"])
        self.__menu["file"].addAction(self.__action["close_tab"])
        self.__menu["file"].addSeparator()
        self.__menu["file"].addAction(self.__action["new_scene"])
        self.__menu["file"].addAction(self.__action["open_scene"])
        self.__menu["file"].addAction(self.__action["import_scene"])
        self.__menu["file"].addAction(self.__action["open_scene_home"])
        self.__menu["file"].addAction(self.__action["save_scene"])
        self.__menu["file"].addAction(self.__action["save_screenshot"])
        self.__menu["file"].addAction(self.__action["open_media_local"])
        self.__menu["file"].addAction(self.__action["open_media_string"])
        self.__menu["file"].addAction(self.__action["open_svg_pick"])
        self.__menu["file"].addAction(self.__action["open_media_dir"])
        self.__menu["file"].addAction(self.__action["quit"])

        self.__menu["view"] = self.menuBar().addMenu("&View")
        self.__menu["set_fps"] = self.__menu["view"].addMenu("Set &Framerate")
        self.__menu["set_fps"].addActions(self.__action["group_set_fps"].actions())
        self.__menu["view"].addAction(self.__action["set_zoom_sensitivity"])
        self.__menu["view"].addAction(self.__action["fullscreen"])
        self.__menu["view"].addSeparator()
        self.__menu["view"].addAction(self.__action["render_order_smaller_top"])

        self.__menu["actions"] = self.menuBar().addMenu("&Actions")
        self.__menu["actions"].addAction(self.__action["copy"])
        self.__menu["actions"].addAction(self.__action["paste"])

        self.__menu["settings"] = self.menuBar().addMenu("&Settings")
        self.__menu["settings"].addAction(self.__action["autosave_settings"])
        self.__menu["settings"].addAction(self.__action["zoom_settings"])

        self.__menu["help"] = self.menuBar().addMenu("&Help")
        self.__menu["help"].addAction(self.__action["about"])
        self.__menu["help"].addAction(self.__action["about_qt"])

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        """
        Method :
            MainWindow.showEvent(event)
        Parameters :
            event : QtGui.QShowEvent

        MainWindow.showEvent(event) --> None

        Handle show event by focusing the current tab's QZUI widget.
        """
        ## focus the current tab's QZUI widget whenever this window is shown
        self.current_zui.setFocus(QtCore.Qt.FocusReason.OtherFocusReason)
