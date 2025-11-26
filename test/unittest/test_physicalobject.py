import pytest
import math
from unittest.mock import Mock
from pyzui.physicalobject import PhysicalObject

class TestPhysicalObject:
    """Test suite for the PhysicalObject class."""

    def test_init(self):
        """Test PhysicalObject initialization."""
        obj = PhysicalObject()
        assert obj._x == 0.0
        assert obj._y == 0.0
        assert obj._z == 0.0
        assert obj.vx == 0.0
        assert obj.vy == 0.0
        assert obj.vz == 0.0
        assert obj._centre == (0, 0)

    def test_damping_factor(self):
        """Test damping_factor attribute."""
        obj = PhysicalObject()
        assert obj.damping_factor == 512

    def test_move(self):
        """Test move method."""
        obj = PhysicalObject()
        obj.move(10, 20)
        assert obj._x == 10.0
        assert obj._y == 20.0

    def test_move_negative(self):
        """Test move with negative values."""
        obj = PhysicalObject()
        obj.move(-5, -10)
        assert obj._x == -5.0
        assert obj._y == -10.0

    def test_zoom(self):
        """Test zoom method."""
        obj = PhysicalObject()
        obj._x = 0.0
        obj._y = 0.0
        obj._centre = (0, 0)
        initial_z = obj._z
        obj.zoom(1.0)
        assert obj._z == initial_z + 1.0

    def test_zoomlevel_property(self):
        """Test zoomlevel property getter and setter."""
        obj = PhysicalObject()
        obj.zoomlevel = 5.0
        assert obj.zoomlevel == 5.0
        assert obj._z == 5.0

    def test_centre_property_get(self):
        """Test centre property getter."""
        obj = PhysicalObject()
        obj._x = 10.0
        obj._y = 20.0
        obj._z = 0.0
        obj._centre = (5, 10)
        centre = obj.centre
        assert centre == (15.0, 30.0)

    def test_centre_property_set(self):
        """Test centre property setter."""
        obj = PhysicalObject()
        obj._x = 0.0
        obj._y = 0.0
        obj._z = 0.0
        obj.centre = (100, 200)
        assert obj._centre == (100.0, 200.0)

    def test_moving_property_false(self):
        """Test moving property when object is stationary."""
        obj = PhysicalObject()
        assert obj.moving is False

    def test_moving_property_true(self):
        """Test moving property when object has velocity."""
        obj = PhysicalObject()
        obj.vx = 10.0
        assert obj.moving is True

    def test_aim_x_no_time(self):
        """Test aim method for x-axis without time parameter."""
        obj = PhysicalObject()
        obj.aim('x', 100.0)
        expected = 100.0 * math.log(obj.damping_factor)
        assert obj.vx == pytest.approx(expected)

    def test_aim_y_no_time(self):
        """Test aim method for y-axis without time parameter."""
        obj = PhysicalObject()
        obj.aim('y', 50.0)
        expected = 50.0 * math.log(obj.damping_factor)
        assert obj.vy == pytest.approx(expected)

    def test_aim_z_no_time(self):
        """Test aim method for z-axis without time parameter."""
        obj = PhysicalObject()
        obj.aim('z', 2.0)
        expected = 2.0 * math.log(obj.damping_factor)
        assert obj.vz == pytest.approx(expected)

    def test_aim_with_time(self):
        """Test aim method with time parameter."""
        obj = PhysicalObject()
        obj.aim('x', 100.0, t=1.0)
        expected = (100.0 * math.log(obj.damping_factor)) / (1 - obj.damping_factor**-1.0)
        assert obj.vx == pytest.approx(expected)

    def test_step(self):
        """Test step method."""
        obj = PhysicalObject()
        obj.vx = 100.0
        obj.vy = 50.0
        initial_x = obj._x
        initial_y = obj._y
        obj.step(0.1)
        # Object should have moved
        assert obj._x != initial_x or obj._y != initial_y

    def test_step_damping(self):
        """Test step method applies damping."""
        obj = PhysicalObject()
        obj.vx = 100.0
        initial_vx = obj.vx
        obj.step(0.5)
        # Velocity should be damped
        assert obj.vx < initial_vx

    def test_step_zero_velocity(self):
        """Test step method with zero velocity."""
        obj = PhysicalObject()
        obj._x = 10.0
        obj._y = 20.0
        obj.step(1.0)
        # Position shouldn't change
        assert obj._x == 10.0
        assert obj._y == 20.0

    def test_step_z_axis(self):
        """Test step method affects z-axis."""
        obj = PhysicalObject()
        obj.vz = 10.0
        initial_z = obj._z
        obj.step(0.1)
        assert obj._z != initial_z

    def test_multiple_moves(self):
        """Test multiple move operations accumulate."""
        obj = PhysicalObject()
        obj.move(10, 20)
        obj.move(5, 10)
        assert obj._x == 15.0
        assert obj._y == 30.0

    def test_aim_accumulates(self):
        """Test aim method accumulates velocity."""
        obj = PhysicalObject()
        obj.aim('x', 100.0)
        first_vx = obj.vx
        obj.aim('x', 50.0)
        # Second aim should add to velocity
        assert obj.vx > first_vx
