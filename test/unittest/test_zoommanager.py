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

"""
Feature: Zoom Manager

The ZoomManager class enforces zoom limits to prevent crashes at extreme
zoom levels by clamping values to configurable minimum and maximum bounds.
"""

from pyzui.objects.objectsutils import ZoomManager


class TestZoomManager:
    """
    Feature: Zoom Manager Operations

    The ZoomManager class provides methods for validating and clamping
    zoom levels to prevent crashes and ensure numerical stability.
    """

    def test_init_defaults(self):
        """
        Scenario: Create ZoomManager with default configuration

        Given no configuration
        When ZoomManager is created
        Then it should use default limits (-10.0 to 12.0)
        """
        manager = ZoomManager()

        assert manager.min_zoomlevel == -10.0
        assert manager.max_zoomlevel == 12.0
        assert manager.clamp_enabled is True

    def test_init_custom_config(self):
        """
        Scenario: Create ZoomManager with custom configuration

        Given custom configuration with min=-15.0, max=25.0
        When ZoomManager is created
        Then it should use the custom limits
        """
        config = {
            'min_zoomlevel': -15.0,
            'max_zoomlevel': 25.0,
            'clamp_enabled': False
        }
        manager = ZoomManager(config)

        assert manager.min_zoomlevel == -15.0
        assert manager.max_zoomlevel == 25.0
        assert manager.clamp_enabled is False

    def test_init_auto_swap_min_max(self):
        """
        Scenario: Create ZoomManager with min > max

        Given configuration with min=10.0, max=-10.0
        When ZoomManager is created
        Then it should automatically swap min and max
        """
        config = {
            'min_zoomlevel': 10.0,
            'max_zoomlevel': -10.0
        }
        manager = ZoomManager(config)

        assert manager.min_zoomlevel == -10.0
        assert manager.max_zoomlevel == 10.0

    def test_validate_within_limits(self):
        """
        Scenario: Validate zoom level within limits

        Given ZoomManager with limits -20.0 to 20.0
        When validate() is called with zoomlevel=5.0
        Then it should return 5.0 unchanged
        """
        manager = ZoomManager()

        result = manager.validate(5.0)
        assert result == 5.0

    def test_validate_below_min(self):
        """
        Scenario: Validate zoom level below minimum

        Given ZoomManager with limits -10.0 to 12.0
        When validate() is called with zoomlevel=-30.0
        Then it should return -10.0 (clamped to min)
        """
        manager = ZoomManager()

        result = manager.validate(-30.0)
        assert result == -10.0

    def test_validate_above_max(self):
        """
        Scenario: Validate zoom level above maximum

        Given ZoomManager with limits -10.0 to 12.0
        When validate() is called with zoomlevel=30.0
        Then it should return 12.0 (clamped to max)
        """
        manager = ZoomManager()

        result = manager.validate(30.0)
        assert result == 12.0

    def test_validate_clamp_disabled(self):
        """
        Scenario: Validate with clamping disabled

        Given ZoomManager with clamp_enabled=False
        When validate() is called with out-of-bounds zoomlevel
        Then it should return the value unchanged
        """
        config = {'clamp_enabled': False}
        manager = ZoomManager(config)

        result = manager.validate(-30.0)
        assert result == -30.0

        result = manager.validate(30.0)
        assert result == 30.0

    def test_is_within_limits(self):
        """
        Scenario: Check if zoom level is within limits

        Given ZoomManager with limits -10.0 to 12.0
        When is_within_limits() is called with various values
        Then it should return True for values within limits, False otherwise
        """
        manager = ZoomManager()

        assert manager.is_within_limits(-10.0) is True
        assert manager.is_within_limits(0.0) is True
        assert manager.is_within_limits(12.0) is True
        assert manager.is_within_limits(-30.0) is False
        assert manager.is_within_limits(30.0) is False

    def test_get_limits(self):
        """
        Scenario: Get current zoom limits

        Given ZoomManager with custom limits
        When get_limits() is called
        Then it should return tuple of (min_zoomlevel, max_zoomlevel)
        """
        config = {'min_zoomlevel': -15.0, 'max_zoomlevel': 25.0}
        manager = ZoomManager(config)

        limits = manager.get_limits()
        assert limits == (-15.0, 25.0)

    def test_update_config(self):
        """
        Scenario: Update ZoomManager configuration

        Given existing ZoomManager
        When update_config() is called with new configuration
        Then it should update the limits and clamping setting
        """
        manager = ZoomManager()

        new_config = {
            'min_zoomlevel': -10.0,
            'max_zoomlevel': 15.0,
            'clamp_enabled': False
        }
        manager.update_config(new_config)

        assert manager.min_zoomlevel == -10.0
        assert manager.max_zoomlevel == 15.0
        assert manager.clamp_enabled is False

    def test_update_config_auto_swap(self):
        """
        Scenario: Update configuration with min > max

        Given existing ZoomManager
        When update_config() is called with min > max
        Then it should automatically swap min and max
        """
        manager = ZoomManager()

        new_config = {
            'min_zoomlevel': 10.0,
            'max_zoomlevel': -10.0
        }
        manager.update_config(new_config)

        assert manager.min_zoomlevel == -10.0
        assert manager.max_zoomlevel == 10.0

    def test_edge_cases(self):
        """
        Scenario: Test edge cases

        Given ZoomManager
        When validate() is called with edge values
        Then it should handle them correctly
        """
        manager = ZoomManager({'min_zoomlevel': -20.0, 'max_zoomlevel': 20.0})

        # Exactly at limits
        assert manager.validate(-20.0) == -20.0
        assert manager.validate(20.0) == 20.0

        # Zero
        assert manager.validate(0.0) == 0.0

        # Very small negative
        assert manager.validate(-0.001) == -0.001

        # Very small positive
        assert manager.validate(0.001) == 0.001
