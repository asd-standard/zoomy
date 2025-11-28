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

"""Media to be displayed in the ZUI (abstract base class)."""

import math

from .physicalobject import PhysicalObject        

class MediaObject(PhysicalObject) :
    """
    Constructor : 
        MediaObject(media_id, scene)
    Parameters :
        media_id['string'], scene['Scene']

    Media_object(media_id, scene) --> PhysicalObject

    MediaObject objects are used to represent media that can be rendered in
    the ZUI.

    Screen view it's fixed unless user change mainwindow size on the screen.
    Both scene and MediaObjects have their own reference systems so that zooms
    can be applied bot to Scene and Mediaobject indipendently trough their 
    reference system transformation.

    You can think about it as fixed window looking at a scene that can strecth or
    shrink beneath it, with this stretch or shrink always having it's origin
    at the Scene center for scene zoom and MediaObject center for the mediobject
    zoom as at the same time individual mediaobject can also strecth 
    or shrink. The fixed window can then move on the 2d plane bringing objects 
    into view.

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

    Legend::

        (All attributes are relative to screen view)
        * -> MediaObject.topleft()
        " -> MediaObject.bottomright()
        & -> MediaObject.center() 
        # -> Scene.viewport_size()
        % -> Scene.center()
        @ -> Scene.origin()

    MediaObject topleft coordinates relative to screen view are given by:

    MediaObject.topleft[0-1] = \
    self._scene.origin[0-1] + self.pos[0-1] * (2 ** self._scene.zoomlevel)

    Where self.pos[0-1] it's MediaObject position relative to Scene reference 
    system wich get's scaled by 2** of scene zoom level

    MediaObject centre coordinates relative to screen view are given firstly by
    calculating image center coordinates relative to Scene reference coordinates:

    C_s[0-1] = self.pos[0-1] + self._centre[0-1] * 2**self._z

    Where self._centre[0-1] are center coordinates relative to the mediaobject
    frame of reference and self._z it's MediaObject reference frame scaling 
    (zoom).

    Take note that self.pos[0-1] dosen't get to be scaled by self._z as that 
    position it's relative to Scene reference frame.

    Then we can calculate MediaObject centre coordinates relative to screen view as:

    MediaObject.centre[0-1] = self._scene.origin[0] + C_s[0-1] * 2**self._scene.zoomlevel

    
    """
    def __init__(self, media_id, scene):
        """Create a new MediaObject from the media identified by `media_id`,
        and the parent Scene referenced by `scene`."""
        #initialize mediobject centre, position and velocity
        PhysicalObject.__init__(self)

        self._media_id = media_id
        self._scene = scene


    def render(self, painter, mode):
        """Render the media using the given `painter` and rendering `mode`.

        render(QPainter, int) -> None

        Precondition: `mode` is equal to one of the constants defined in
        `RenderMode`
        """
        pass


    def move(self, dx, dy):
        """Move the image relative to the scene, where (`dx`,`dy`) is given as
        an on-screen distance.

        move(float, float) -> None
        """

        #self._x and self._y correspond to self.pos[0] and self.pos[1], but 
        #mediaobject.pos dosen't support += operation
        self._x += dx * (2 ** -self._scene.zoomlevel)
        self._y += dy * (2 ** -self._scene.zoomlevel)


    def zoom(self, amount):
        """Zoom by the given `amount` with the centre maintaining its position
        on the screen.

        zoom(float) -> None
        """

        ## C_s is the scene coordinates of the centre
        ## C_i is the image coordinates of the centre
        ## P is the onscreen position of the centre
        ## zoomlevel_i' = zoomlevel_i + amount
        ##    P = scene.origin + C_s * 2**zoomlevel_s
        ##      => C_s = (P - scene.origin) * 2**-zoomlevel_s
        ## C_s  = self.pos  + C_i * 2**zoomlevel_i
        ##      => C_i = (C_s - self.pos) * 2**-zoomlevel_i
        ## C_s' = self.pos' + C_i * 2**zoomlevel_i'
        ##      = self.pos' + (C_s - self.pos)
        ##        * 2**(zoomlevel_i'-zoomlevel_i)
        ## solving for C_s = C_s' yields:
        ##   self.pos' = C_s - (C_s - self.pos) * 2**amount

        # Px, Py = self.centre
        # C_sx = (Px - self._scene.origin[0]) * 2**-self._scene.zoomlevel
        # C_sy = (Py - self._scene.origin[1]) * 2**-self._scene.zoomlevel

        C_ix, C_iy = self._centre
        C_sx = self._x + C_ix * 2**self._z
        C_sy = self._y + C_iy * 2**self._z

        self._x = C_sx - (C_sx - self._x) * 2**amount
        self._y = C_sy - (C_sy - self._y) * 2**amount
        self._z += amount


    def hides(self, other):
        """Returns True iff `other` is completely hidden behind `self` on the
        screen.

        hides(MediaObject) -> bool
        """
        if self.transparent:
            ## nothing can be hidden behind a transparent object
            return False

        viewport_size = self._scene.viewport_size

        s_left, s_top = self.topleft
        s_right, s_bottom = self.bottomright
        ## clamp values
        s_left =   max(0, min(s_left,   viewport_size[0]))
        s_top =    max(0, min(s_top,    viewport_size[1]))
        s_right =  max(0, min(s_right,  viewport_size[0]))
        s_bottom = max(0, min(s_bottom, viewport_size[1]))

        o_left, o_top = other.topleft
        o_right, o_bottom = other.bottomright
        ## clamp values
        o_left =   max(0, min(o_left,   viewport_size[0]))
        o_top =    max(0, min(o_top,    viewport_size[1]))
        o_right =  max(0, min(o_right,  viewport_size[0]))
        o_bottom = max(0, min(o_bottom, viewport_size[1]))

        return o_left  >= s_left  and o_top    >= s_top and \
               o_right <= s_right and o_bottom <= s_bottom


    def fit(self, bbox):
        """Move and resize the image such that it the greatest size possible
        whilst fitting inside and centred in the onscreen bounding box `bbox`
        (x1,y1,x2,y2).

        fit(tuple<float,float,float,float>) -> None
        """
        
        box_x, box_y, box_x2, box_y2 = list(map(float, bbox))
        box_w = box_x2 - box_x
        #print('box_x, box_x2',box_x, box_x2)
        box_h = box_y2 - box_y
        #print('box_y',box_y)

        w, h = self.onscreen_size
        #print('MEDIA',w,h)
        if w/h > box_w/box_h:
            ## need to fit width
            scale = box_w / w
            target_x = box_x
            target_y = box_y + box_h/2 - (h*scale)/2
        else:
            ## need to fit height
            scale = box_h / h
            target_x = box_x + box_w/2 - (w*scale)/2
            target_y = box_y

        self.zoomlevel += math.log(scale, 2)

        self._x = (target_x - self._scene.origin[0]) \
            * (2 ** -self._scene.zoomlevel)
        #print('self._x',self._x)
        self._y = (target_y - self._scene.origin[1]) \
            * (2 ** -self._scene.zoomlevel)
        #print('self._y',self._y)


    def __cmp__(self, other):
        if self is other:
            return 0
        elif self.onscreen_area < other.onscreen_area:
            return -1
        else:
            return 1


    @property
    def media_id(self):
        """The object's media_id."""
        return self._media_id


    @property
    def scale(self):
        """The factor by which each dimension of the image should be scaled
        when rendering it to the screen."""
        return 2 ** (self._scene.zoomlevel + self.zoomlevel)


    @property
    def topleft(self):
        """The on-screen positon of the top-left corner of the image.
        self._scene.origin -> the world-space X coordinate of the top-left of the 
        screen view (the camera/view origin)
        self.pos -> the object’s position inside the view before applying zoom
        (a coordinate in the camera’s internal coordinate system)
        
        here self.pos() is mediaobject 
        """
        
        x = self._scene.origin[0] + self.pos[0] * (2 ** self._scene.zoomlevel)
        y = self._scene.origin[1] + self.pos[1] * (2 ** self._scene.zoomlevel)
        return (x,y)


    @property
    def onscreen_size(self):
        """
        The on-screen size of the image.
        This gets inherited by higher order classes (StringMedia obj
        TiledMedia obj ecc)
        """
        pass


    @property
    def bottomright(self):
        """The on-screen positon of the bottom-right corner of the image."""
        o = self.topleft
        s = self.onscreen_size
        x = o[0] + s[0]
        y = o[1] + s[1]
        return (x,y)


    @property
    def onscreen_area(self):
        """The number of pixels the image occupies on the screen."""
        w,h = self.onscreen_size
        return w * h
    
    def __get_pos(self):
        """
        Constructor :
            __get_pos
        Parameters :
            None

        __set_origin --> MediaObject[float['_x']], MediaObject[float['_y']] 
        """
        return (self._x, self._y)

    def __set_pos(self, pos):
        '''
        Constructor :
            __set_pos(pos)
        Parameters :
            pos[MediaObject[float['_x']], MediaObject[float['_y']]]

        __set_origin --> None

        Set self._x, self._y variables to MediaObject position 
        '''
        self._x, self._y = pos

    pos = property(__get_pos, __set_pos)
    """Creating MediaObject.pos property with __get_pos as 
    getter and __set_pos as setter"""

    def __get_centre(self):
        ## we need to convert image-coordinate C_i to
        ## screen-coordinate P (through scene-coordinate C_s):
        ##   P = scene.origin + C_s * 2**zoomlevel_s
        ## C_s = self.pos + C_i * 2**zoomlevel_i

        #This are the image coordinates relative to scene coordinates.

        C_s = (self.pos[0] + self._centre[0] * 2**self._z,
               self.pos[1] + self._centre[1] * 2**self._z)

        #
        return (self._scene.origin[0] + C_s[0] * 2**self._scene.zoomlevel,
                self._scene.origin[1] + C_s[1] * 2**self._scene.zoomlevel)

    def __set_centre(self, centre):
        ## we need to convert screen-coordinate P to
        ## image-coordinate C_i (through scene-coordinate C_s):
        ##   P = scene.origin + C_s * 2**zoomlevel_s
        ##     => C_s = (P - scene.origin) * 2**-zoomlevel_s
        ## C_s = self.pos  + C_i * 2**zoomlevel_i
        ##     => C_i = (C_s - self.pos) * 2**-zoomlevel_i
        C_s = ((centre[0] - self._scene.origin[0]) * 2**-self._scene.zoomlevel,
               (centre[1] - self._scene.origin[1]) * 2**-self._scene.zoomlevel)
        self._centre = ((C_s[0] - self._x) * 2**-self._z,
                        (C_s[1] - self._y) * 2**-self._z)

    centre = property(__get_centre, __set_centre)

    def __str__(self):
        return "%s(%s)" % (type(self).__name__, self._media_id)


    def __repr__(self):
        return "%s(%s)" % (type(self).__name__, repr(self._media_id))


class LoadError(Exception):
    
    """Exception for if there is an error loading the media."""
    pass


class RenderMode:
    """Namespace for constants used to indicate the render mode."""
    Invisible = 0
    Draft = 1
    HighQuality = 2






