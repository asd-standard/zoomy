## PyZUI - Python Zooming User Interface
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

import pytest
import math
from unittest.mock import Mock
from pyzui.objects.physicalobject import PhysicalObject

class TestPhysicalObject:
    """
    Feature: PhysicalObject Class

    This class tests the PhysicalObject functionality including position tracking, velocity management,
    physics simulation, and coordinate transformations used for animation and movement in PyZUI.
    """

    def test_init(self):
        """
        Scenario: Initialize PhysicalObject with default values

        Given a new PhysicalObject
        When it is instantiated
        Then all position and velocity attributes should be initialized to zero
        """
        obj = PhysicalObject()
        assert obj._x == 0.0
        assert obj._y == 0.0
        assert obj._z == 0.0
        assert obj.vx == 0.0
        assert obj.vy == 0.0
        assert obj.vz == 0.0
        assert obj._centre == (0, 0)

    def test_damping_factor(self):
        """
        Scenario: Verify damping factor attribute

        Given a PhysicalObject
        When accessing the damping_factor attribute
        Then it should be 512
        """
        obj = PhysicalObject()
        assert obj.damping_factor == 512

    def test_move(self):
        """
        Scenario: Move object to new position

        Given a PhysicalObject at the origin
        When calling move with x=10 and y=20
        Then the object position should be updated to (10, 20)
        """
        obj = PhysicalObject()
        obj.move(10, 20)
        assert obj._x == 10.0
        assert obj._y == 20.0

    def test_move_negative(self):
        """
        Scenario: Move object to negative coordinates

        Given a PhysicalObject
        When calling move with negative x and y values
        Then the object should accept and store negative coordinates
        """
        obj = PhysicalObject()
        obj.move(-5, -10)
        assert obj._x == -5.0
        assert obj._y == -10.0

    def test_zoom(self):
        """
        Scenario: Zoom by delta amount

        Given a PhysicalObject with initial zoom level
        When calling zoom with delta value
        Then the z-coordinate should increase by the delta amount
        """
        obj = PhysicalObject()
        obj._x = 0.0
        obj._y = 0.0
        obj._centre = (0, 0)
        initial_z = obj._z
        obj.zoom(1.0)
        assert obj._z == initial_z + 1.0

    def test_zoomlevel_property(self):
        """
        Scenario: Set and get zoomlevel property

        Given a PhysicalObject
        When setting zoomlevel to 5.0
        Then both zoomlevel and internal _z should be 5.0
        """
        obj = PhysicalObject()
        obj.zoomlevel = 5.0
        assert obj.zoomlevel == 5.0
        assert obj._z == 5.0

    def test_centre_property_get(self):
        """
        Scenario: Get centre coordinates

        Given a PhysicalObject with position and centre offset
        When accessing the centre property
        Then it should return the combined coordinates
        """
        obj = PhysicalObject()
        obj._x = 10.0
        obj._y = 20.0
        obj._z = 0.0
        obj._centre = (5, 10)
        centre = obj.centre
        assert centre == (15.0, 30.0)

    def test_centre_property_set(self):
        """
        Scenario: Set centre coordinates

        Given a PhysicalObject
        When setting the centre property to (100, 200)
        Then the internal _centre should be updated to (100.0, 200.0)
        """
        obj = PhysicalObject()
        obj._x = 0.0
        obj._y = 0.0
        obj._z = 0.0
        obj.centre = (100, 200)
        assert obj._centre == (100.0, 200.0)

    def test_moving_property_false(self):
        """
        Scenario: Check moving property when stationary

        Given a PhysicalObject with zero velocity
        When checking the moving property
        Then it should return False
        """
        obj = PhysicalObject()
        assert obj.moving is False

    def test_moving_property_true(self):
        """
        Scenario: Check moving property when in motion

        Given a PhysicalObject with non-zero velocity
        When checking the moving property
        Then it should return True
        """
        obj = PhysicalObject()
        obj.vx = 10.0
        assert obj.moving is True

    def test_aim_x_no_time(self):
        """
        Scenario: Aim for target x displacement

        Given a PhysicalObject
        When calling aim for x-axis with a target displacement
        Then velocity should be calculated based on damping factor
        """
        obj = PhysicalObject()
        obj.aim('x', 100.0)
        expected = 100.0 * math.log(obj.damping_factor)
        assert obj.vx == pytest.approx(expected)

    def test_aim_y_no_time(self):
        """
        Scenario: Aim for target y displacement

        Given a PhysicalObject
        When calling aim for y-axis with a target displacement
        Then velocity should be calculated based on damping factor
        """
        obj = PhysicalObject()
        obj.aim('y', 50.0)
        expected = 50.0 * math.log(obj.damping_factor)
        assert obj.vy == pytest.approx(expected)

    def test_aim_z_no_time(self):
        """
        Scenario: Aim for target z displacement

        Given a PhysicalObject
        When calling aim for z-axis with a target displacement
        Then velocity should be calculated based on damping factor
        """
        obj = PhysicalObject()
        obj.aim('z', 2.0)
        expected = 2.0 * math.log(obj.damping_factor)
        assert obj.vz == pytest.approx(expected)

    def test_aim_with_time(self):
        """
        Scenario: Aim with specific time constraint

        Given a PhysicalObject
        When calling aim with a time parameter
        Then velocity should be adjusted to reach target in specified time
        """
        obj = PhysicalObject()
        obj.aim('x', 100.0, t=1.0)
        expected = (100.0 * math.log(obj.damping_factor)) / (1 - obj.damping_factor**-1.0)
        assert obj.vx == pytest.approx(expected)

    def test_step(self):
        """
        Scenario: Advance physics simulation by time step

        Given a PhysicalObject with non-zero velocity
        When calling step with a time delta
        Then the object position should be updated
        """
        obj = PhysicalObject()
        obj.vx = 100.0
        obj.vy = 50.0
        initial_x = obj._x
        initial_y = obj._y
        obj.step(0.1)
        # Object should have moved
        assert obj._x != initial_x or obj._y != initial_y

    def test_step_damping(self):
        """
        Scenario: Apply velocity damping during step

        Given a PhysicalObject with velocity
        When calling step
        Then the velocity should be reduced by damping
        """
        obj = PhysicalObject()
        obj.vx = 100.0
        initial_vx = obj.vx
        obj.step(0.5)
        # Velocity should be damped
        assert obj.vx < initial_vx

    def test_step_zero_velocity(self):
        """
        Scenario: Step with zero velocity

        Given a PhysicalObject with zero velocity
        When calling step
        Then the position should remain unchanged
        """
        obj = PhysicalObject()
        obj._x = 10.0
        obj._y = 20.0
        obj.step(1.0)
        # Position shouldn't change
        assert obj._x == 10.0
        assert obj._y == 20.0

    def test_step_z_axis(self):
        """
        Scenario: Update z-axis position during step

        Given a PhysicalObject with z-velocity
        When calling step
        Then the z position should be updated
        """
        obj = PhysicalObject()
        obj.vz = 10.0
        initial_z = obj._z
        obj.step(0.1)
        assert obj._z != initial_z

    def test_multiple_moves(self):
        """
        Scenario: Accumulate multiple move operations

        Given a PhysicalObject
        When calling move multiple times
        Then the position changes should accumulate
        """
        obj = PhysicalObject()
        obj.move(10, 20)
        obj.move(5, 10)
        assert obj._x == 15.0
        assert obj._y == 30.0

    def test_aim_accumulates(self):
        """
        Scenario: Accumulate velocity from multiple aim calls

        Given a PhysicalObject with some velocity
        When calling aim multiple times
        Then the velocity changes should accumulate
        """
        obj = PhysicalObject()
        obj.aim('x', 100.0)
        first_vx = obj.vx
        obj.aim('x', 50.0)
        # Second aim should add to velocity
        assert obj.vx > first_vx
