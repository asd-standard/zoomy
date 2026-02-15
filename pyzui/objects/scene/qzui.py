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

"""QWidget for displaying the ZUI."""

from typing import Optional, Any, Tuple
from PySide6 import QtCore, QtGui, QtWidgets
from threading import Thread

from pyzui.objects.scene import scene as Scene
from pyzui.tilesystem import tilemanager as TileManager

class QZUI(QtWidgets.QWidget, Thread) :
    """
    Constructor :
        QZUI(parent, framerate, zoom_sensitivity)
    Parameters :
        parent : Optional[QtWidgets.QWidget]
        framerate : int
        zoom_sensitivity : int

    QZUI(parent, framerate, zoom_sensitivity) --> None

    QZUI widgets that are used for rendering the ZUI.
    This class defines all the methods to retrieve events, Mouse, Keyboard, etc.

    """

    #: link error variable to QtCore.Signal()
    error = QtCore.Signal()

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None,
                 framerate: int = 10, zoom_sensitivity: int = 10) -> None:
        """
        Constructor :
            QZUI(parent, framerate, zoom_sensitivity)
        Parameters :
            parent : Optional[QtWidgets.QWidget]
            framerate : int
            zoom_sensitivity : int

        QZUI(parent, framerate, zoom_sensitivity) --> None

        Create a new QZUI QWidget with the given `parent` widget.
        Initializes the widget with specified framerate and zoom sensitivity.
        """
        QtWidgets.QWidget.__init__(self, parent)

        Thread.__init__(self)
        self.__scene: 'Scene.Scene' = Scene.new()
        
        self.__mouse_right_down: bool = False
        self.__mouse_left_down: bool = False
        self.__mousepos: Optional[Tuple[int, int]] = None
        self.__shift_held: bool = False
        self.__alt_held: bool = False
        self.__dropped_frames: int = 0
        self.__draft: bool = True

        self.__timer: QtCore.QBasicTimer = QtCore.QBasicTimer()
        self.__framerate: int

        self.zoom_sensitivity: int = zoom_sensitivity
        self.reduced_framerate: int = 3
        self.framerate: int = framerate

        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setMouseTracking(True)

    def __zoom(self, num_steps: float) -> None:
        """
        Method :
            __zoom(num_steps)
        Parameters :
            num_steps : float

        __zoom(num_steps) --> None

        Increase the z velocity of the appropriate object by an amount
        proportional to num_steps.
        """
        if self.__alt_held:
            scale = 1.0/16
        else:
            scale = 1.0

        self.__active_object.centre = self.__mousepos
        self.__active_object.vz += scale * num_steps

    def __centre(self) -> None:
        """
        Method :
            __centre()
        Parameters :
            None

        __centre() --> None

        Aim the appropriate object such that the point under the cursor will
        move to the centre of the screen.
        """
        if self.__mousepos is None:
            return
        self.__active_object.vx = self.__active_object.vy = 0.0
        self.__active_object.aim('x', self.width()/2  - self.__mousepos[0])
        self.__active_object.aim('y', self.height()/2 - self.__mousepos[1])

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """
        Method :
            paintEvent(event)
        Parameters :
            event : QtGui.QPaintEvent

        paintEvent(event) --> None

        Method that allows you to perform custom painting on a widget.

        It is part of the event handling system, and you typically override it in a subclass of a QWidget
        (or any subclass like QLabel, QFrame, etc.) to draw graphics using the QPainter class.
        """
        if self.framerate:
            self.scene.step(1.0 / self.framerate)

        painter = QtGui.QPainter()
        painter.begin(self)
        try:
            ## paint background
            painter.fillRect(
                    0, 0, self.width(), self.height(), QtCore.Qt.black)

            ## render scene
            self.scene.render(painter, self.__draft) #errors = 
            
            ## show errors
            #for mediaobject in errors:
                
            #    self.error.emit("Error loading %s" + str(mediaobject))

        finally:
            painter.end()

        if self.__mouse_left_down:
            self.__active_object.vx = self.__active_object.vy = 0.0

    def timerEvent(self, event: QtCore.QTimerEvent) -> None:
        """
        Method :
            timerEvent(event)
        Parameters :
            event : QtCore.QTimerEvent

        timerEvent(event) --> None

        Handle timer events to update the scene rendering.
        """
        if event.timerId() == self.__timer.timerId():
            if self.scene.moving :
                self.__dropped_frames = 0
                self.__draft = True
                self.update()
            else:
                ## Scene or MediaObjects are moving so drop Frames 
                
                if self.__dropped_frames >= \
                   self.framerate/self.reduced_framerate:
                    self.__dropped_frames = 0

                    ## since the framerate is reduced, we
                    ## can do high-quality rendering
                    self.__draft = False
                    self.repaint()
                else:
                    ## drop current frame
                    self.__dropped_frames += 1
        else:
            QtWidgets.QWidget.timerEvent(self, event)

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        """
        Method :
            wheelEvent(event)
        Parameters :
            event : QtGui.QWheelEvent

        wheelEvent(event) --> None

        Handle mouse wheel events for zooming.
        """
        num_degrees = event.angleDelta().y() #/ 8
        num_steps = round(num_degrees / self.zoom_sensitivity , 3) #15
        self.__mousepos = (int(event.position().x()), int(event.position().y()))
        self.__zoom(num_steps)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """
        Method :
            mousePressEvent(event)
        Parameters :
            event : QtGui.QMouseEvent

        mousePressEvent(event) --> None

        Handle mouse press events for object selection.
        """
        if event.button() == QtCore.Qt.LeftButton:
            self.__mouse_left_down = True
            self.__mousepos = (int(event.position().x()), int(event.position().y()))
            if not self.__shift_held:
                ## shift-click won't change the selection
                self.scene.selection = self.scene.get(self.__mousepos)

        if event.button() == QtCore.Qt.RightButton:
            self.__mouse_right_down = True
            self.__mousepos = (int(event.position().x()), int(event.position().y()))
            if not self.__shift_held:
                ## shift-click won't change the selection
                self.scene.right_selection = self.scene.get(self.__mousepos)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        """
        Method :
            mouseMoveEvent(event)
        Parameters :
            event : QtGui.QMouseEvent

        mouseMoveEvent(event) --> None

        Handle mouse move events for dragging objects.
        """
        if (event.buttons()&QtCore.Qt.LeftButton) and self.__mouse_left_down:
            if self.__mousepos is None:
                return
            mx = int(event.position().x()) - self.__mousepos[0]
            my = int(event.position().y()) - self.__mousepos[1]

            t = 1.0 / self.framerate
            self.__active_object.aim('x', mx, t)
            self.__active_object.aim('y', my, t)

        self.__mousepos = (int(event.position().x()), int(event.position().y()))

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        """
        Method :
            mouseReleaseEvent(event)
        Parameters :
            event : QtGui.QMouseEvent

        mouseReleaseEvent(event) --> None

        Handle mouse release events.
        """
        if event.button() == QtCore.Qt.LeftButton and self.__mouse_left_down:
            self.__mouse_left_down = False

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """
        Method :
            keyPressEvent(event)
        Parameters :
            event : QtGui.QKeyEvent

        keyPressEvent(event) --> None

        Handle key press events for navigation and control.
        """
        if self.__alt_held:
            move_amount = 16
        else:
            move_amount = 16

        key = event.key()
        if   key == QtCore.Qt.Key_Escape:
            self.scene.selection = None
        elif key == QtCore.Qt.Key_PageUp:
            self.__zoom(1.0)
        elif key == QtCore.Qt.Key_PageDown:
            self.__zoom(-1.0)
        elif key == QtCore.Qt.Key_Up:
            self.__active_object.aim('y', -move_amount)
        elif key == QtCore.Qt.Key_Down:
            self.__active_object.aim('y', move_amount)
        elif key == QtCore.Qt.Key_Left:
            self.__active_object.aim('x', -move_amount)
        elif key == QtCore.Qt.Key_Right:
            self.__active_object.aim('x', move_amount)
        elif key == QtCore.Qt.Key_Shift:
            self.__shift_held = True
        elif key == QtCore.Qt.Key_Alt:
            self.__alt_held = True
        elif key == QtCore.Qt.Key_Space:
            self.__centre()
        elif key == QtCore.Qt.Key_Delete:
            if self.scene.selection:
                self.scene.remove(self.scene.selection)
                self.scene.selection = None
        else:
            QtWidgets.QWidget.keyPressEvent(self, event)

    def keyReleaseEvent(self, event: QtGui.QKeyEvent) -> None:
        """
        Method :
            keyReleaseEvent(event)
        Parameters :
            event : QtGui.QKeyEvent

        keyReleaseEvent(event) --> None

        Handle key release events.
        """
        key = event.key()
        if   key == QtCore.Qt.Key_Shift:
            self.__shift_held = False
        elif key == QtCore.Qt.Key_Alt:
            self.__alt_held = False
        else:
            QtWidgets.QWidget.keyPressEvent(self, event)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """
        Method :
            resizeEvent(event)
        Parameters :
            event : QtGui.QResizeEvent

        resizeEvent(event) --> None

        Handle resize events to update the viewport size.
        """
        self.__scene.viewport_size = (self.width(), self.height())

    @property
    def __active_object(self) -> Any:
        """
        Property :
            __active_object
        Parameters :
            None

        __active_object --> Any

        Return the currently active object (either selected object or scene).
        """
        if self.scene.selection and not self.__shift_held:
            return self.scene.selection
        else:
            return self.scene

    def __get_framerate(self) -> int:
        """
        Method :
            __get_framerate()
        Parameters :
            None

        __get_framerate() --> int

        Return the rendering framerate.
        """
        return self.__framerate

    def __set_framerate(self, framerate: int) -> None:
        """
        Method :
            __set_framerate(framerate)
        Parameters :
            framerate : int

        __set_framerate(framerate) --> None

        Set the rendering framerate.
        """
        self.__framerate = framerate
        if self.__framerate:
            self.__timer.start(int(1000/self.__framerate), self)
        elif self.__timer.isActive():
            self.__timer.stop()

    framerate = property(__get_framerate, __set_framerate)

    def __get_scene(self) -> 'Scene.Scene':
        """
        Method :
            __get_scene()
        Parameters :
            None

        __get_scene() --> Scene.Scene

        Return the scene currently being viewed.
        """
        return self.__scene

    def __set_scene(self, scene: 'Scene.Scene') -> None:
        """
        Method :
            __set_scene(scene)
        Parameters :
            scene : Scene.Scene

        __set_scene(scene) --> None

        Set the scene to be viewed.
        """
        self.__scene = Scene.new() ## erase scene
        TileManager.purge()
        self.__scene = scene
        self.__scene.viewport_size = (self.width(), self.height())

        ## zoom into scene
        self.__scene.centre = (self.width()/2, self.height()/2)
        self.__scene.zoom(-5.0)
        self.__scene.aim('z', 5.0)

    scene = property(__get_scene, __set_scene)

