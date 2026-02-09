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

"""An object that obeys the laws of physics."""

#from threading import Thread
import math
from typing import Optional, Tuple

class PhysicalObject(): #removed object from class argument and Thread
    """
    Constructor :
        PhysicalObject()
    Parameters :
        None

    PhysicalObject() --> None

    Physicalobject objects are sets of declarations and methods that are used
    to represent anything that has a 3-dimensional position and velocity,
    where the z-dimension represents a zoomlevel.

    PhysicalObject gets declared on MediaObject and Scene initializations,
    giving them the necessary attributes, (position, zoomlevel, damp factor
    zoomlevel, eccetera).

    """
    def __init__(self) -> None:
        """
        Create a new PhysicalObject at the origin with zero velocity.

        Initializes position coordinates (_x, _y, _z) to 0.0, where
        z represents zoomlevel. Initializes velocity components (vx, vy, vz)
        to 0.0. Sets the center offset (_centre) to (0,0).

        This initialization is used by both Scene and MediaObject classes.

        Class Inheritance Hierarchy::

            PhysicalObject (Abstract Base)
            │   • _x, _y, _z (position & zoom)
            │   • vx, vy, vz (velocity)
            │   • damping factor
            │   • _centre (center point)
            │
            ├── MediaObject (Abstract)
            │   │   • Coordinate transforms
            │   │   • Scaling management
            │   │   • Reference frames
            │   │
            │   ├── TiledMediaObject
            │   │       • Large image support
            │   │       • Tile grid management
            │   │       • Efficient for huge images
            │   │
            │   ├── StringMediaObject
            │   │       • Text rendering
            │   │       • Font support
            │   │
            │   └── SVGMediaObject
            │           • Vector graphics
            │           • Scalable rendering
            │
            └── Scene
                   • Container for MediaObjects
                   • Viewport management
                   • Scene persistence
                   • Thread-safe operations
        """

        self._x: float = 0.0
        self._y: float = 0.0
        self._z: float = 0.0

        self.vx: float = 0.0
        self.vy: float = 0.0
        self.vz: float = 0.0

        self._centre: Tuple[float, float] = (0, 0)

    """the velocity is damped at each frame such that each second it is
    reduced by a factor of damping_factor: v = u * damping_factor**-t"""
    damping_factor: int = 512 #256

    def __damp(self, velocity: float, t: float) -> float:
        """
        Method :
            __damp(velocity, t)
        Parameters :
            velocity : float
            t : float

        __damp(velocity, t) --> float

        Damp the given velocity over time t.

        Applies exponential damping using the formula:
            v = u * damping_factor**-t

        If the absolute value of the velocity falls below 0.1,
        it is set to 0.0 to prevent infinitesimal movements.

        Returns the damped velocity value.
        """
        velocity *= self.damping_factor ** -t
        if abs(velocity) < 0.1:
            velocity = 0.0
        return velocity

    def __displacement(self, t: float, u: float) -> float:
        """
        Method :
            __displacement(t, u)
        Parameters :
            t : float
            u : float

        __displacement(t, u) --> float

        Calculate the displacement at time t given initial velocity u.

        Uses the formula derived from integrating the damped velocity::

            s(t) = (u / log(d)) * (1 - d**-t)

        where d is the damping_factor.

        This accounts for the exponential decay of velocity over time.

        Returns the calculated displacement.
        """

        ## Let d = damping_factor
        ##     u = initial velocity
        ##     t = time in seconds
        ## we know v(t) = u * d**-t
        ## s(t) = \int v(t)  dt
        ##      = \int u * d**-t  dt
        ##      = -u / log(d) * \int -log(d) * exp(-t*log(d))  dt
        ##      = -u * exp(-t*log(d)) / log(d) + C
        ##      = -u * d**-t / log(d) + C
        ## solving C for s=0 at t=0:
        ## s(t) = -u * d**-t / log(d) + u / log(d)
        ##      = (u / log(d)) * (1 - d**-t)

        return (u / math.log(self.damping_factor)) \
               * (1 - self.damping_factor**-t)

    def move(self, dx: float, dy: float) -> None:
        """
        Method :
            PhysicalObject.move(dx, dy)
        Parameters :
            dx : float
            dy : float

        PhysicalObject.move(dx, dy) --> None

        Move the object by the displacement (dx, dy).

        Increments the object's x position by dx and y position by dy.
        """
        self._x += dx
        self._y += dy

    def zoom(self, amount: float) -> None:
        """
        Method :
            PhysicalObject.zoom(amount)
        Parameters :
            amount : float

        PhysicalObject.zoom(amount) --> None

        Zoom by the given amount with the center maintaining its position
        on the screen.

        Adjusts the position and zoom level such that the center point
        remains at the same screen coordinates after the zoom operation.
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

        Px: float
        Py: float
        Px, Py = self.centre
        self._x = Px - (Px - self._x) * 2**amount
        self._y = Py - (Py - self._y) * 2**amount
        self._z += amount


    def aim(self, v: str, s: float, t: Optional[float] = None) -> None:
        """Calculate the initial velocity such that at time `t` the relative
        displacement of the object will be `s`, and increase the velocity
        represented by `v` by this amount.

        If `t` is omitted then it will be taken that `s` is the limit of the
        displacement as `t` approaches infinity
        i.e. the initial velocity will be calculated such that the total
        displacement will be `s` once the object has stopped moving.

        Parameters :
            v : str
            s : float
            t : Optional[float]

        velocity(string, float[, float]) -> None

        Precondition: `v` is either 'x', 'y', or 'z'
        """
        u: float
        if t:
            ## s(t) = (u / log(d)) * (1 - d**-t)
            ## => u = (s(t) * log(d)) / (1 - d**-t)
            u = (s * math.log(self.damping_factor)) \
                   / (1 - self.damping_factor**-t)
        else:
            ## s = lim_t->inf displacement
            ##   = lim_t->inf (u / log(d)) * (1 - d**-t)
            ##   = u / log(d)  since d > 1
            ## therefore u = s * log(d)
            u = s * math.log(self.damping_factor)

        if   v == 'x': self.vx += u
        elif v == 'y': self.vy += u
        elif v == 'z': self.vz += u

    def step(self, t: float) -> None:
        """
        Method :
            PhysicalObject.step(t)
        Parameters :
            t : float

        PhysicalObject.step(t) --> None

        Step forward t seconds in time.

        Updates the object's position based on velocity and damping.
        Calculates displacement for x and y using the velocity and time,
        then damps the velocities.

        If there is z velocity (zoom), applies zoom displacement and
        damps the z velocity.

        This method is called every frame to update physics simulation.
        """
        if self.vx or self.vy:
            self.move(
                self.__displacement(t, self.vx),
                self.__displacement(t, self.vy))
            self.vx = self.__damp(self.vx, t)
            self.vy = self.__damp(self.vy, t)

        if self.vz:
            self.zoom(self.__displacement(t, self.vz))
            self.vz = self.__damp(self.vz, t)

    @property
    def moving(self) -> bool:
        """
        Property :
            PhysicalObject.moving
        Parameters :
            None

        PhysicalObject.moving --> bool

        Boolean value indicating whether the object has a non-zero velocity.

        Returns True if any of vx, vy, or vz are non-zero.
        Returns False if all velocity components are zero.
        """
        return not (self.vx == self.vy == self.vz == 0)

    def __get_zoomlevel(self) -> float:
        """
        Method :
            __get_zoomlevel
        Parameters :
            None

        __get_zoomlevel --> float

        Get the zoomlevel of the object.

        Returns the z-coordinate which represents the zoom level.
        """
        return self._z

    def __set_zoomlevel(self, zoomlevel: float) -> None:
        """
        Method :
            __set_zoomlevel(zoomlevel)
        Parameters :
            zoomlevel : float

        __set_zoomlevel --> None

        Set the zoomlevel of the object.

        Assigns the given zoomlevel value to the z-coordinate.
        """
        self._z = zoomlevel

    zoomlevel = property(__get_zoomlevel, __set_zoomlevel)
    """Creating PhysicalObject.zoomlevel property with __get_zoomlevel as
    getter and __set_zoomlevel as setter"""

    '''
    TN (take note) this center setter getter definition applies to Scenes
    objects, MediaObjects have their own centre definition.
    '''
    def __get_centre(self) -> Tuple[float, float]:
        """
        Method :
            __get_centre
        Parameters :
            None

        __get_centre --> Tuple[float, float]

        Get the on-screen position of the object's center.

        Converts object-coordinate C to screen-coordinate P using:
            P = pos + C * 2**zoomlevel

        Note: This definition applies to Scene objects. MediaObjects
        have their own center definition.

        Returns the screen coordinates of the center.
        """
        ## we need to convert object-coordinate C to
        ## screen-coordinate P:
        ## P = pos + C * 2**zoomlevel
        return (self._x + self._centre[0] * 2**self._z,
                self._y + self._centre[1] * 2**self._z)

    def __set_centre(self, centre: Tuple[float, float]) -> None:
        """
        Method :
            __set_centre(centre)
        Parameters :
            centre : Tuple[float, float]

        __set_centre --> None

        Set the on-screen position of the object's center.

        Converts screen-coordinate P to object-coordinate C using:
            C = (P - pos) * 2**-zoomlevel

        Note: This definition applies to Scene objects. MediaObjects
        have their own center definition.
        """
        ## we need to convert screen-coordinate P to
        ## object-coordinate C:
        ## P = pos + C * 2**zoomlevel
        ##   => C = (P - pos) * 2**-zoomlevel

        self._centre = ((centre[0] - self._x) * 2**-self._z,
                        (centre[1] - self._y) * 2**-self._z)

    centre = property(__get_centre, __set_centre)
    """Creating PhysicalObject.centre property with __get_centre as
    getter and __set_centre as setter"""
