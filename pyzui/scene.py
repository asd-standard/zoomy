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

"""A collection of media objects."""


import logging
from threading import RLock
import urllib.request, urllib.parse, urllib.error
import math


from PyQt5 import QtCore
from PyQt5.QtGui import QColor

from .dialogwindows import DialogWindows
from .physicalobject import PhysicalObject
from . import tilemanager as TileManager
from . import mediaobject as MediaObject
from .tiledmediaobject import TiledMediaObject
from .stringmediaobject import StringMediaObject
from .svgmediaobject import SVGMediaObject

class Scene(PhysicalObject):
    """
    Constructor :
        Scene()
    Parameters :
        None

    Scene() --> None

    `Scene` objects are used to hold a collection of `MediaObjects`.
    This class manages all the objects that can be rendered in the interface,
    Their positioning (_x, _y) on the scene and their zoom (_z) and the acces to 
    them.

    Scene objects can also be saved to files, and loaded from files.

    """

    #: an arbitrary size that is common to all scenes upon creation `scene size`
    standard_viewport_size = (1280,720)

    def __init__(self):

        """
        New scene is made by initiating a :doc:`physicalobject <pyzui.physicalobject>`, 

        creating an objects list `__objects` and thread safe selection for `__objects`
        given by declaring RLock list `__objects_lock`, 
        
        set up `__viewport_size`

        mouse selection variables `selection` and `right_selection` and logger setup
        `__logger`. 
        
        World::

             --------------------------------------->
            |   Scene
            |  @ ------------------------------+--->
            |  |  ViewPort        MediaObj     |                 
            |  |  (Screen View)   *-------+--> |       
            |  |                  |   &   |    |   
            |  |               %  +-------"    |      
            |  |                  |            |
            |  |                  ∨            |
            |  |                               | 
            |  +-------------------------------#
            |  |
            |  ∨
            ∨  

        Legend:
        (All MediaObject attributes are relative to screen view)
        * -> MediaObject.topleft()
        " -> MediaObject.bottomright()
        & -> MediaObject.center() 
        # -> Scene.viewport_size()
        % -> Scene.center()
        @ -> Scene.origin() 

        We have a center relative to the scene, 'center' and a center relative
        to the absolute frame of reference _center
        
        @ origin position of the scene it's relative to an absolute frame of 
        reference, with 0,0 as it's origin.

        % Scene center it's given by
          scene.centre[0] = scene.origin + (Scene.viewport_size[0]/2)*2**(zoomlevel)
          scene.centre[1] = scene.origin + (Scene.viewport_size[1]/2)*2**(zoomlevel)



        """

        #initialize mediobject centre, position and velocity    
        PhysicalObject.__init__(self)        

        self.__objects = []
        self.__objects_lock = RLock()
        self.__viewport_size = self.standard_viewport_size

        self.selection = None
        self.right_selection = None
        
        #commented out on 20250314 
        self.__logger = logging.getLogger("Scene")

    def save(self, filename):
        """
        Constructor : 
            Scene.save(filename)
        Parameters :
            filename['string']

        Scene.save(filename) --> None

        Save the scene to the location given by `filename`.

        It is recommended (but not compulsory) that the file extension of
        filename be '.pzs'.
        
        open a file `filename`, writes on the first line zoom level (z) and 
        position (x, y) of the scene origin defined by Scene.__set_origin()
        then thread safely, once sorted `__objects`, cicles through them, 
        writing for each of them a line on `fielname` with:  
            
            object type: `type(mediaobject).__name__`
            
            media id: mediaobject.media_id (replacing '%3A' with :) 
            
            zoomlevel: mediaobject.zoomlevel 
            
            x position: mediaobject.pos[0]
            
            y position: mediaobject.pos[1]
        """
        
        """viewport_size it's saved in a temporary variable `actual_viewport_size`
        so that saving of the scene can be done in a standard size.
        By doing this once the scene it's loaded it can be then scaled to fit
        whatever viewport the user currently has, independent of the viewport 
        the scene was having when it was saved."""
        actual_viewport_size = self.viewport_size
        # setting `viewport_size` to standard size
        self.viewport_size = self.standard_viewport_size

        f = open(filename, 'w')

        f.write("%s\t%s\t%s\n" % \
            (self.zoomlevel, self.origin[0], self.origin[1]))

        with self.__objects_lock:
            self.__sort_objects()
            for mediaobject in self.__objects:
                f.write("%s\t%s\t%s\t%s\t%s\n" % \
                    (type(mediaobject).__name__,
                    urllib.parse.quote(mediaobject.media_id) \
                        .replace('%3A', ':'),
                    mediaobject.zoomlevel,
                    mediaobject.pos[0],
                    mediaobject.pos[1]))

        f.close()

        # setting `viewport_size` to it's actual size 
        self.viewport_size = actual_viewport_size


    def add(self, mediaobject):
        """
        Constructor :
            Scene.add(mediaobject)
        Parameters :
            mediaobject[':doc:`mediaobject <pyzui.mediaobject>`']

        Scene.add(mediaobject) --> None

        Add mediaobject from the list of elements that get to
        be rendered on the scene.

        Inside a thread safe selection: add `mediaobject` to this scene by 
        checking if given mediaobject is already in `__objects` list, if 
        it is nothing is done, otherwise mediaobject it's appended to the 
        `__objects` list.
        """

        with self.__objects_lock:
            if mediaobject not in self.__objects:

                self.__objects.append(mediaobject)

    def remove(self, mediaobject):
        """
        Constructor :
            Scene.remove(mediaobject)
        Parameters :
            mediaobject[':doc:`mediaobject <pyzui.mediaobject>`']

        Scene.remove(mediaobject) --> None

        Remove mediaobject from the list of elements that get to
        be rendered on the scene and purge all'related tiles through
        TileManager.purge('media_id') method.

        Thread safely cycle through `__objects` until `mediaobject`
        match with the respective element of the `__objects` list
        and removes it from the `__objects` list. Then gets
        mediaobject.media_id attribute and check if other `__objects`
        elements have the same media_id, if it's not the case the media_id
        gets purged from the TileManager. 

        See: `tilemanager.purge <file:///home/asd/Projects/pyzui/docs/build/
        html/_modules/pyzui/tilemanager.html#purge>`_

        """

        with self.__objects_lock:
            if mediaobject in self.__objects:
                self.__objects.remove(mediaobject)

                media_id = mediaobject.media_id
                media_active = False
                for other in self.__objects:
                    if other.media_id == media_id:
                        ## another object exists for
                        ## this media, meaning that
                        ## this media is active
                        media_active = True

                if not media_active:
                    TileManager.purge(media_id)


    def __sort_objects(self):
        """
        Contructor :
            `internal method` self.__sort_objects()
        Parameters :
            None

        __sort_objects() --> None

        Sort self.__objects from largest to smallest area using 
        mediaobject.onscreen_area attribute wich return mediaobject
        current onscreen area.

        See :  `mediaobject.onscreen_area <file:///home/asd/
        Projects/pyzui/docs/build/html/pyzui.mediaobject.html
        #module-pyzui.mediaobject>`_ 

        """
        with self.__objects_lock:
            self.__objects.sort(key=lambda mediaobject: \
                mediaobject.onscreen_area)
            


    def get(self, pos):
        """
        Contructors :
            Scene.get(pos)
        Parameters :
            pos[tuple[float,float]]

        Scene.get(pos) --> None
        
        Return the foremost visible `MediaObject` which overlaps the
        on-screen point `pos`. `pos` is the mouse polition at the last
        left or right click mouse event.

        Return None if there are no `MediaObject`s overlapping the point.

        get(tuple[float,float]) --> MediaObject or None

        Mouse click event is catched by: `qzui.mousePressEvent <file:///home/
        asd/Projects/pyzui/docs/build/html/_modules/pyzui/qzui.html#QZUI.mouse
        PressEvent>`_ wich returns mouse position `pos`
        
        Thread safely cycle through `__objects`. for each mediaobject checks if 
        `pos` is within mediaobject area, if it is the mediaobject is returned as 
        `foremost` 
        """
        foremost = None

        with self.__objects_lock:
            self.__sort_objects()
            for mediaobject in self.__objects:
                left, top = mediaobject.topleft
                right, bottom = mediaobject.bottomright
                if pos[0] >= left  and pos[1] >= top and \
                   pos[0] <= right and pos[1] <= bottom:
                    foremost = mediaobject

        return foremost

    def zoom(self, amount):
        """Zoom by the given `amount` with the centre maintaining its position
        on the screen.

        zoom(float) -> None
        """

        ## P is the onscreen objec position of the centre
        ## C is the coordinates of the centre
        ## zoomlevel' = zoomlevel + amount
        ## P  = pos  + C * 2**zoomlevel
        ##    => C = (P - pos) * 2**-zoomlevel
        ## P' = pos' + C * 2**zoomlevel'
        ##    = pos' + (P - pos) * 2**(zoomlevel'-zoomlevel)
        ## solving for P = P' yields:
        ##   pos' = P - (P - pos) * 2**amount


        Px, Py = self.centre
        self._x = Px - (Px - self._x) * 2**amount
        self._y = Py - (Py - self._y) * 2**amount
        self._z += amount
    

    def render(self, painter, draft):
        """
        Constructor :
            Scene.render(painter, draft)
        Parameters :
            painter['QtGui.QPainter'], draft['bool']
        
        Scene.render(painter, draft) --> errors['MediaObject.LoadError']

        Render the scene using the given `painter`.

        If `draft` is True, draft mode is enabled. Otherwise High-Quality mode
        is enabled.

        If any errors occur rendering any of the `MediaObject`s, then they will
        be removed from the scene and a list of tuples representing the errors
        will be returned. Otherwise the empty list will be returned.

        render(QPainter, bool) -> list[tuple[MediaObject,MediaObject.LoadError]]
        
        See source code comments :

            `Source <file:///home/asd/Projects/pyzui/docs/build/html/_modules/
            pyzui/scene.html#Scene.render>`_ 

        """

        #Error list to be filled with MediaObject.LoadError.
        errors = []

        """Sort __objects from least to most displayed area and thread safely 
        cycle through them""" 
        with self.__objects_lock:
            self.__sort_objects()
            #If hidden=True mediaobject is added to hidden_objects set 
            hidden = False
            #Creates an empty set for hidden mediaobjects
            hidden_objects = set()
            """cycles through __objects in reverse order, from smallest area to
            biggest area, if they result hidden they don't get to be rendered
            and they're added to hidden_objects set""" 
            for mediaobject in reversed(self.__objects):
                if hidden:
                    hidden_objects.add(mediaobject)
                else:
                    #gets topleft and bottomright coordinates
                    x1, y1 = mediaobject.topleft
                    x2, y2 = mediaobject.bottomright

                    if x1 <= 0 and y1 <= 0 and \
                       x2 >= self.viewport_size[0] and \
                       y2 >= self.viewport_size[1]:
                        ## mediaobject fills the entire
                        ## screen, so mark the rest of
                        ## the mediaobjects behind it
                        ## as hidden
                        hidden = True

            """Set of hidden_objects it's updated: now we cycle through __objects
            once again setting mediaobject.RenderMode, we set Invisible is 
            mediaobject is in hidden_objects, we set in Draft if draft class input
            parameter is passed as True, otherwise we set HighQuality"""

            for mediaobject in self.__objects:
                if mediaobject in hidden_objects:
                    mode = MediaObject.RenderMode.Invisible
                elif draft:
                    mode = MediaObject.RenderMode.Draft
                else:
                    mode = MediaObject.RenderMode.HighQuality
                
                """Now we try to render using mediaobject.render() method wich is 
                inherited from the specific type of mediaobject, namely: 
                tilemediaobject, stringmediaobject, scgmediaobject, each of these
                mediaobjects has it's specific render method"""
                try:   
                    mediaobject.render(painter, mode)
                except MediaObject.LoadError :
                    """If mediaobject render fails MediaObject.LoadError type is 
                    returned and appended to errors list"""
                    errors.append((mediaobject))
                    
            for mediaobject in errors:
                ## remove mediaobjects that have raised errors
                print('## remove mediaobjects that have raised MediaObject.LoadError')
                print(mediaobject)
                #Remove mediaobject using the Scene.remove() method
                self.remove(mediaobject)
            
            """qzui.mousePressEvent handles mouse selection and adjourn `selection`
            and right_selection, assigning to them the mouse selected mediaobject. 
            If selection or right_selection isn't None a colored border gets drawn 
            around selected of right_selected mediaobject using QtGui.QPainter 
            `painter`"""

            if self.selection :
                #using mediaobject.topleft mediaobject.topright attributes
                x1, y1 = self.selection.topleft
                x2, y2 = self.selection.bottomright

                ## clamp values
                x1 = max(0, min(int(x1), self.viewport_size[0] - 1))
                y1 = max(0, min(int(y1), self.viewport_size[1] - 1))
                x2 = max(0, min(int(x2), self.viewport_size[0] - 1))
                y2 = max(0, min(int(y2), self.viewport_size[1] - 1))
                #Draing border using QtGui.QPainter attributes
                painter.setPen(QtCore.Qt.green)
                painter.drawRect(x1, y1, x2-x1, y2-y1)
                

            if self.right_selection :
                #using mediaobject.topleft mediaobject.toptight attributes
                x1, y1 = self.right_selection.topleft
                x2, y2 = self.right_selection.bottomright

                ## clamp values
                x1 = max(0, min(int(x1), self.viewport_size[0] - 1))
                y1 = max(0, min(int(y1), self.viewport_size[1] - 1))
                x2 = max(0, min(int(x2), self.viewport_size[0] - 1))
                y2 = max(0, min(int(y2), self.viewport_size[1] - 1))
                #Draing border using QtGui.QPainter attributes
                painter.setPen(QtCore.Qt.blue)
                painter.drawRect(x1, y1, x2-x1, y2-y1)

            if type(self.right_selection).__name__ == 'StringMediaObject' :

                for i in range(len(self.__objects)) :

                    if self.__objects[i]._media_id[14:] ==\
                      self.right_selection._media_id[14:] :                        
                        
                        dialog = DialogWindows.modify_string_input_dialog(\
                            self.__objects[i]._media_id)
                        try :
                            ok, media_id, string_color, edited_text = dialog._run_dialog() 

                        except Exception as e :   
                            ok = False
                            media_id = False      
                        if ok and media_id: 
                            
                            lines = []
                            lines.append([])

                            j=0
                            for k in list(edited_text) :  
                                    # If a \n char is encountered a new sublist is appended to self.lines              
                                    if k == '\n' :                    
                                        lines.append([])
                                        j += 1
                                    else :
                                    # Otherwise the char is appended to the currend self.lines sublist
                                        lines[j] += str(k)
                            
                            self.__objects[i].lines = lines
                            self.__objects[i]._media_id = media_id
                            self.__objects[i]._StringMediaObject__str = edited_text
                            self.__objects[i]._StringMediaObject__color =\
                                QColor('#'+string_color)
                            #print(self.__objects[i].__dict__)
                        self.right_selection = None
                        break




        #returning MediaObject.LoadError
        return errors


    def step(self, t):
        """
        Constructor : 
            Scene.step(t)
        Parameters :
            t['float']
        
        Scene.step(t) --> None

        Step the scene and all contained `MediaObjects` forward `t` seconds
        in time.
    
        Thread safely cycle through `__objects` mediaobjects set and for each of 
        them call `PhysicalObject.step(t) <file:///home/asd/Projects/
        pyzui/docs/build/html/_modules/pyzui/physicalobject.html#
        PhysicalObject.step>`_ inherited method.
        """
        
        with self.__objects_lock:
            for mediaobject in self.__objects:
                mediaobject.step(t)
            PhysicalObject.step(self, t)


    @property
    def moving(self):
        """
        Constructor : 
            Scene.moving
        Parameters :
            None

        Scene.moving --> bool

        Boolean value indicating whether the scene or any contained
        `MediaObject`s have a non-zero velocity.

        Checks if the inherited, vx, vy and vz values from `PhysicalObject`
        are not zero. If it is that means the scene is moving and True is 
        returned, If thats not the case it thread safely cycle trough 
        mediaobjects in `__objects` checking if `mediaobject.moving` is
        True. If it is True is returned. `mediaobject.moving` is also 
        inherited property of `PhysicalObject` class.

        See : `physicalobject <file:///home/asd/Projects/pyzui/docs/build/html/
        pyzui.physicalobject.html#module-pyzui.physicalobject>`_ 
        """
        if not (self.vx == self.vy == self.vz == 0):
            return True
        else:
            with self.__objects_lock :
                for mediaobject in self.__objects:
                    if mediaobject.moving:
                        return True

        return False

    def __get_origin(self):
        """
        Constructor :
            __get_origin
        Parameters :
            None

        __get_origin --> PhysicalObject._x['float'], PhysicalObject._y['float'] 

        Returns the Scene origin by retrieving _x, and _y variables
        inherited by PhysicalObject class
        """
        return (self._x, self._y)

    def __set_origin(self, origin):
        """
        Constructor :
            __set_origin(origin)
        Parameters :
            origin[__get_origin[PhysicalObject._x['float'], 
            PhysicalObject._y['float']]]

        __set_origin --> None

        Set PhysicalObject._x and PhysicalObject._y parameters to new values 
        given as input parameters.
        """
        self._x, self._y = origin

    origin = property(__get_origin, __set_origin)
    """Creating Scene.origin property with __get_origin as getter and 
    __set_origin as setter"""

    def __get_viewport_size(self):
        """
        Contructor :
            __get_viewport_size
        Parameters :
            None

        __get_viewport_size --> self.__viewport_size 
        
        Return the current dimensions of the viewport.
        """
        return self.__viewport_size

    def __set_viewport_size(self, viewport_size):
        """
        Constructor :
            __set_viewport_size(viewport_size)
        Parameters :
            viewport_size['__get_viewport_size']

        __get_viewport_size --> None
        
        Happens when mainwindow gets resized or a scene get's loaded having 
        different viewport_size that the currewn mainwindow size. All necessary
        adjustement are handled here

        Centers PhysicalObject._x and PhysicalObject._y to the new input 
        parameter viewport_size center, also adjourn PhysicalObject.centre. 
        Calculates the ratio between previous viewport_size center and the 
        input parameter viewport_size, then calls PhysicalObject.zoom() and
        zooms the scene by base 2 log of the ratio between old and new 
        viewport.

        then adjourn the __viewport_size variable with the value given by 
        the input parameter viewport_size.

        old_viewport::

            --------------------------------->
            |
            |      ----------------------#
            |     |                      |                 
            |     |             *------  |       
            |     |           % |      | |   
            |     |             +------" |      
            |     |                      |
            |     @----------------------
            |
            |
            ∨
        
        new_viewport::

            ----------------------------------->
            |
            |  ------------------------------#
            | |                              |
            | |                              |
            | |                              |                 
            | |                *------       |       
            | |              % |      |      |   
            | |                +------"      |      
            | |                              |
            | |                              | 
            | @------------------------------
            |
            |
            ∨
        """

        ## centre the scene in the new viewport
        old_viewport_size = self.__viewport_size
        self._x += (viewport_size[0] - old_viewport_size[0]) / 2
        self._y += (viewport_size[1] - old_viewport_size[1]) / 2

        ## scale the scene such that the minimum dimension of the old
        ## viewport is the same in-scene distance as the minimum
        ## dimension of the new viewport
        self.centre = (viewport_size[0]/2, viewport_size[1]/2)
        scale = float(min(viewport_size)) / min(old_viewport_size)
        
        #we have math.log(scale, 2) as pos' = pos+2**zoomlevel
        self.zoom(math.log(scale, 2))

        self.__viewport_size = viewport_size

        
    viewport_size = property(__get_viewport_size, __set_viewport_size)
    """Creating Scene.viewport_size property with __get_viewport_size as 
    getter and __set_viewport_size as setter"""

def new():
    """
    Constructor :
        Scene.new()
    Parameters :
        None

    new() --> Scene['PhysicaObject']

    Create and return a new `Scene` object.
    """
    return Scene()


def load_scene(filename):
    """
    Constructor :
        Scene.load_scene(filename)
    Parameters :
        filename['string']

    Scene.load_scene(filename) --> Scene['PhysicalObject']

    Load the scene stored in the file given by `filename`.

    Precondition: `filename` refers to a file in the same format as 
    produced by `Scene.save`

    See source code comments:

        `source <file:///home/asd/Projects/pyzui/docs/build/html/_modules/pyzui/
        scene.html#load_scene>`_
    """

    #Declares a new Scene() object
    scene = Scene()
    
    f = open(filename) 

    #First line of a scene file ale zoomlevel _x and _y of th scene origin
    zoomlevel, ox, oy = f.readline().split()
    scene.zoomlevel = float(zoomlevel)
    scene.origin = (float(ox), float(oy))
    #print('HERE', '\n', '\n', '\n', '\n')
    #print(float(ox),float(oy))

    """
    Any line then represent a mediaobject, namely composed by :    
            
            media id: mediaobject.media_id (replacing '%3A' with :) 
            
            zoomlevel: mediaobject.zoomlevel 
            
            x position: mediaobject.pos[0]
            
            y position: mediaobject.pos[1]
    """
    for line in f:
        class_name, media_id, zoomlevel, x, y = line.split()
        media_id = urllib.parse.unquote(media_id)

        """ mediaobjects are sorted by their mediaobject type and 
        initialized by their appropiate classes"""

        if class_name == 'TiledMediaObject' or \
           class_name == 'StringMediaObject' or \
           class_name == 'SVGMediaObject':
            if   class_name ==   'TiledMediaObject':
                mediaobject = TiledMediaObject(
                    media_id, scene)
            elif class_name ==   'StringMediaObject':
                mediaobject = StringMediaObject(
                    media_id, scene)
                
            elif class_name ==   'SVGMediaObject':
                mediaobject = SVGMediaObject(
                    media_id, scene)

            #mediaobjects are zoomed by the level read in the loaded scene file
            mediaobject.zoomlevel = float(zoomlevel)
            #mediaobjects are placed in the position read in the loaded scene file
            mediaobject.pos = (float(x), float(y))
            #mediaobjects are added to the scene
            scene.add(mediaobject)
        else:
            ## ignore instances of any other class
            pass


    f.close()

    return scene
