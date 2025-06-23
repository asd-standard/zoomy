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

"""QWidget for displaying the ZUI."""

from PyQt5 import QtCore, QtGui, QtWidgets
from threading import Thread

from . import scene as Scene
from . import tilemanager as TileManager

class QZUI(QtWidgets.QWidget, Thread):
    """QZUI widgets that are used for rendering the ZUI.
        This class defines all the methods to retieve events, Mouse, Keyboard, ecc
    Constructor: QZUI([QWidget])
    """
    error = QtCore.pyqtSignal()

    def __init__(self, parent=None, framerate=int, zoom_sensitivity=int):
        """Create a new QZUI QWidget with the given `parent` widget."""
        QtWidgets.QWidget.__init__(self, parent)

        Thread.__init__(self)
        self.__scene = Scene.new()
        
        self.__mouse_right_down = False
        self.__mouse_left_down = False
        self.__mousepos = None
        self.__shift_held = False
        self.__alt_held = False
        self.__dropped_frames = 0
        self.__draft = True

        self.__timer = QtCore.QBasicTimer()

        self.zoom_sensitivity = zoom_sensitivity
        self.framerate = framerate
        self.reduced_framerate = 3

        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setMouseTracking(True)


    def __zoom(self, num_steps):
        """Increase the z velocity of the appropriate object by an amount
        proportional to num_steps.

        __zoom(float) -> None
        """
        if self.__alt_held:
            scale = 1.0/16
        else:
            scale = 1.0

        self.__active_object.centre = self.__mousepos
        self.__active_object.vz += scale * num_steps


    def __centre(self):
        """Aim the appropriate object such that the point under the cursor will
        move to the centre of the screen

        __centre() -> None
        """
        self.__active_object.vx = self.__active_object.vy = 0.0
        self.__active_object.aim('x', self.width()/2  - self.__mousepos[0])
        self.__active_object.aim('y', self.height()/2 - self.__mousepos[1])


    def paintEvent(self, event):
        '''
            method that allows you to perform custom painting on a widget. 
            It is part of the event handling system, and you typically override it in a subclass of a QWidget 
            (or any subclass like QLabel, QFrame, etc.) to draw graphics using the QPainter class.
        '''
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


    def timerEvent(self, event):
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


    def wheelEvent(self, event):
        num_degrees = event.angleDelta().y() #/ 8
        num_steps = round(num_degrees / self.zoom_sensitivity , 3) #15
        self.__zoom(num_steps)
        self.__mousepos = (event.x(), event.y())


    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.__mouse_left_down = True
            self.__mousepos = (event.x(), event.y())
            if not self.__shift_held:
                ## shift-click won't change the selection
                self.scene.selection = self.scene.get(self.__mousepos)
        
        if event.button() == QtCore.Qt.RightButton:
            self.__mouse_right_down = True
            self.__mousepos = (event.x(), event.y())
            if not self.__shift_held:
                ## shift-click won't change the selection
                self.scene.right_selection = self.scene.get(self.__mousepos)

    def mouseMoveEvent(self, event):
        if (event.buttons()&QtCore.Qt.LeftButton) and self.__mouse_left_down:
            mx = event.x() - self.__mousepos[0]
            my = event.y() - self.__mousepos[1]

            t = 1.0 / self.framerate
            self.__active_object.aim('x', mx, t)
            self.__active_object.aim('y', my, t)

        self.__mousepos = (event.x(), event.y())


    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.__mouse_left_down:
            self.__mouse_left_down = False


    def keyPressEvent(self, event):
        if self.__alt_held:
            move_amount = 1
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


    def keyReleaseEvent(self, event):
        key = event.key()
        if   key == QtCore.Qt.Key_Shift:
            self.__shift_held = False
        elif key == QtCore.Qt.Key_Alt:
            self.__alt_held = False
        else:
            QtWidgets.QWidget.keyPressEvent(self, event)


    def resizeEvent(self, event):
        self.__scene.viewport_size = (self.width(), self.height())


    @property
    def __active_object(self):
        if self.scene.selection and not self.__shift_held:
            return self.scene.selection
        else:
            return self.scene


    def __get_framerate(self):
        """Rendering framerate."""
        return self.__framerate

    def __set_framerate(self, framerate):
        self.__framerate = framerate
        if self.__framerate:
            self.__timer.start(int(1000/self.__framerate), self)
        elif self.__timer.isActive():
            self.__timer.stop()
    framerate = property(__get_framerate, __set_framerate)

    def __get_scene(self):
        """Scene currently being viewed."""
        return self.__scene

    def __set_scene(self, scene):

        self.__scene = Scene.new() ## erase scene
        TileManager.purge()
        self.__scene = scene
        self.__scene.viewport_size = (self.width(), self.height())

        ## zoom into scene
        self.__scene.centre = (self.width()/2, self.height()/2)
        self.__scene.zoom(-5.0)
        self.__scene.aim('z', 5.0)

    scene = property(__get_scene, __set_scene)





