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

from unittest.mock import Mock

import pytest
from PySide6 import QtCore

from pyzui.objects.mediaobjects.mediaobjectsutils.string.textlayout import TextLayoutData
from pyzui.objects.scene.sceneutils.prioritybatcher import BatchPriority, PrioritizedObject, PriorityBatcher


class TestPriorityBatcher:
    """
    Feature: Priority-Based Object Batching

    The PriorityBatcher class organizes text objects into priority batches
    based on their distance from the viewport center, ensuring that objects
    closest to the viewport are rendered first for optimal perceived performance.
    """

    def test_init_default(self):
        """
        Scenario: Initialize with default parameters

        When PriorityBatcher is created with default parameters
        Then it should have default batch size and max batches
        And viewport center should be (0, 0)
        """
        batcher = PriorityBatcher()

        assert batcher.batch_size == 10
        assert batcher.max_batches == 10
        assert batcher.viewport_center == (0.0, 0.0)
        assert batcher.viewport_rect == QtCore.QRectF(0, 0, 800, 800)
        assert batcher.get_object_count() == 0

    def test_init_custom(self):
        """
        Scenario: Initialize with custom parameters

        When PriorityBatcher is created with custom parameters
        Then it should use the provided values
        """
        viewport_center = (500.0, 300.0)
        viewport_rect = QtCore.QRectF(400, 200, 200, 200)

        batcher = PriorityBatcher(
            batch_size=5,
            max_batches=20,
            viewport_center=viewport_center,
            viewport_rect=viewport_rect
        )

        assert batcher.batch_size == 5
        assert batcher.max_batches == 20
        assert batcher.viewport_center == viewport_center
        assert batcher.viewport_rect == viewport_rect

    def test_update_viewport(self):
        """
        Scenario: Update viewport information

        Given a PriorityBatcher
        When update_viewport is called with new values
        Then the viewport center and rectangle should be updated
        And existing batches should be cleared
        """
        batcher = PriorityBatcher()

        new_center = (100.0, 200.0)
        new_rect = QtCore.QRectF(50, 150, 100, 100)

        batcher.update_viewport(new_center, new_rect)

        assert batcher.viewport_center == new_center
        assert batcher.viewport_rect == new_rect

    def test_add_objects(self):
        """
        Scenario: Add objects to batcher

        Given a PriorityBatcher
        When add_objects is called with a list of objects
        Then the objects should be added to the batcher
        And object count should increase
        """
        batcher = PriorityBatcher()

        # Create mock objects
        obj1 = Mock()
        obj1.x = 100.0
        obj1.y = 100.0

        obj2 = Mock()
        obj2.x = 200.0
        obj2.y = 200.0

        objects = [obj1, obj2]

        batcher.add_objects(objects)

        assert batcher.get_object_count() == 2

    def test_clear_objects(self):
        """
        Scenario: Clear all objects

        Given a PriorityBatcher with objects
        When clear_objects is called
        Then all objects should be removed
        And object count should be 0
        """
        batcher = PriorityBatcher()

        obj = Mock()
        obj.x = 100.0
        obj.y = 100.0

        batcher.add_objects([obj])
        assert batcher.get_object_count() == 1

        batcher.clear_objects()
        assert batcher.get_object_count() == 0

    def test_calculate_distance(self):
        """
        Scenario: Calculate distance from object to viewport center

        Given an object with x, y coordinates
        When calculate_distance is called
        Then the Euclidean distance should be returned
        """
        batcher = PriorityBatcher(viewport_center=(0.0, 0.0))

        obj = Mock()
        obj.x = 3.0
        obj.y = 4.0

        distance = batcher.calculate_distance(obj)

        # Distance should be sqrt(3² + 4²) = 5
        assert distance == 5.0

    def test_get_priority(self):
        """
        Scenario: Get priority level based on distance

        Given distance values
        When get_priority is called
        Then the appropriate BatchPriority should be returned
        """
        batcher = PriorityBatcher()

        # Test high priority (distance <= 1000)
        assert batcher.get_priority(500.0) == BatchPriority.HIGH
        assert batcher.get_priority(1000.0) == BatchPriority.HIGH

        # Test medium priority (1000 < distance <= 2000)
        assert batcher.get_priority(1500.0) == BatchPriority.MEDIUM
        assert batcher.get_priority(2000.0) == BatchPriority.MEDIUM

        # Test low priority (2000 < distance <= 4000)
        assert batcher.get_priority(2500.0) == BatchPriority.LOW
        assert batcher.get_priority(4000.0) == BatchPriority.LOW

        # Test background priority (distance > 4000)
        assert batcher.get_priority(4500.0) == BatchPriority.BACKGROUND

    def test_is_in_viewport(self):
        """
        Scenario: Check if object is in viewport

        Given an object with position and size
        When is_in_viewport is called
        Then it should return True if object intersects viewport, False otherwise
        """
        batcher = PriorityBatcher(viewport_rect=QtCore.QRectF(0, 0, 100, 100))

        # Object inside viewport
        obj_inside = Mock()
        obj_inside.x = 50.0
        obj_inside.y = 50.0
        obj_inside.width = 20.0
        obj_inside.height = 20.0

        assert batcher.is_in_viewport(obj_inside)

        # Object outside viewport
        obj_outside = Mock()
        obj_outside.x = 200.0
        obj_outside.y = 200.0
        obj_outside.width = 20.0
        obj_outside.height = 20.0

        assert not batcher.is_in_viewport(obj_outside)

    def test_create_batches_empty(self):
        """
        Scenario: Create batches with no objects

        Given a PriorityBatcher with no objects
        When create_batches is called
        Then it should return an empty list
        """
        batcher = PriorityBatcher()

        batches = batcher.create_batches()

        assert batches == []

    def test_create_batches_single_object(self):
        """
        Scenario: Create batches with single object

        Given a PriorityBatcher with one object
        When create_batches is called
        Then it should return one batch with one object
        """
        batcher = PriorityBatcher(viewport_center=(0.0, 0.0))

        # Create a simple object with float attributes
        class SimpleObject:
            def __init__(self, x, y):
                self.x = x
                self.y = y
                self.width = 20.0
                self.height = 10.0

            def _get_text(self):
                return "Test"

        obj = SimpleObject(10.0, 10.0)

        batcher.add_objects([obj])

        batches = batcher.create_batches()

        assert len(batches) == 1
        assert len(batches[0]) == 1
        assert batches[0][0].object == obj

    def test_create_batches_multiple_objects(self):
        """
        Scenario: Create batches with multiple objects

        Given a PriorityBatcher with multiple objects at different distances
        When create_batches is called
        Then objects should be batched by priority
        And closer objects should be in earlier batches
        """
        batcher = PriorityBatcher(
            batch_size=2,
            max_batches=3,
            viewport_center=(0.0, 0.0)
        )

        # Create simple objects with float attributes
        class SimpleObject:
            def __init__(self, x, y, name):
                self.x = x
                self.y = y
                self.width = 20.0
                self.height = 10.0
                self.name = name

            def _get_text(self):
                return self.name

        # Create objects at different distances
        obj_close = SimpleObject(10.0, 10.0, "Close")  # Distance ~14.14 (HIGH)
        obj_medium = SimpleObject(500.0, 500.0, "Medium")  # Distance ~707.11 (HIGH)
        obj_far = SimpleObject(1500.0, 1500.0, "Far")  # Distance ~2121.32 (MEDIUM)
        obj_very_far = SimpleObject(3000.0, 3000.0, "Very Far")  # Distance ~4242.64 (LOW)

        objects = [obj_close, obj_medium, obj_far, obj_very_far]
        batcher.add_objects(objects)

        batches = batcher.create_batches()

        # We should have at least 1 batch
        assert len(batches) >= 1

        # First batch should have higher priority objects
        first_batch_objects = [p_obj.object for p_obj in batches[0]]
        # Check that we have 2 objects in first batch (batch_size=2)
        assert len(first_batch_objects) == 2
        # The two closest objects should be in first batch
        assert obj_close in first_batch_objects  # Highest priority
        assert obj_medium in first_batch_objects  # High priority

        # Check priority levels
        for p_obj in batches[0]:
            if p_obj.object == obj_close:
                assert p_obj.priority == BatchPriority.HIGH.value
            elif p_obj.object == obj_medium:
                # Distance 707.11 is <= 1000, so HIGH priority
                assert p_obj.priority == BatchPriority.HIGH.value

    def test_get_batch_metadata(self):
        """
        Scenario: Get batch metadata

        Given a PriorityBatcher with objects
        When get_batch_metadata is called
        Then it should return metadata for each batch
        """
        batcher = PriorityBatcher(batch_size=1)

        # Create a simple object with float attributes
        class SimpleObject:
            def __init__(self, x, y):
                self.x = x
                self.y = y
                self.width = 20.0
                self.height = 10.0

            def _get_text(self):
                return "Test"

        obj = SimpleObject(10.0, 10.0)

        batcher.add_objects([obj])

        metadata = batcher.get_batch_metadata()

        assert len(metadata) == 1
        assert 'priority' in metadata[0]
        assert 'average_distance' in metadata[0]
        assert 'size' in metadata[0]

    def test_get_visible_object_count(self):
        """
        Scenario: Get count of visible objects

        Given objects inside and outside viewport
        When get_visible_object_count is called
        Then it should return count of objects in viewport
        """
        batcher = PriorityBatcher(viewport_rect=QtCore.QRectF(0, 0, 100, 100))

        obj_inside = Mock()
        obj_inside.x = 50.0
        obj_inside.y = 50.0
        obj_inside.width = 10.0
        obj_inside.height = 10.0

        obj_outside = Mock()
        obj_outside.x = 200.0
        obj_outside.y = 200.0
        obj_outside.width = 10.0
        obj_outside.height = 10.0

        batcher.add_objects([obj_inside, obj_outside])

        visible_count = batcher.get_visible_object_count()

        assert visible_count == 1

    def test_layout_cache_operations(self):
        """
        Scenario: Layout cache operations

        Given a PriorityBatcher
        When layout cache operations are performed
        Then they should work correctly
        """
        batcher = PriorityBatcher()

        # Test update and get
        layout_data = Mock(spec=TextLayoutData)
        layout_data.is_valid = True
        layout_data.is_stale = Mock(return_value=False)

        batcher.update_layout_cache(0, layout_data)

        cached = batcher.get_layout_cache(0)
        assert cached == layout_data

        # Test cache hit rate (1 object cached out of 0 total = 0)
        assert batcher.get_cache_hit_rate() == 0.0

        # Test invalidate for object
        batcher.invalidate_cache_for_object(0)
        assert batcher.get_layout_cache(0) is None

        # Test clear all cache
        batcher.update_layout_cache(1, layout_data)
        batcher.clear_layout_cache()
        assert batcher.get_layout_cache(1) is None

    def test_get_statistics(self):
        """
        Scenario: Get batcher statistics

        Given a PriorityBatcher with objects
        When get_statistics is called
        Then it should return comprehensive statistics
        """
        batcher = PriorityBatcher()

        obj = Mock()
        obj.x = 10.0
        obj.y = 10.0
        obj._get_text = Mock(return_value="Test")
        obj.width = 20.0
        obj.height = 10.0

        batcher.add_objects([obj])

        stats = batcher.get_statistics()

        assert 'total_objects' in stats
        assert 'visible_objects' in stats
        assert 'cache_hit_rate' in stats
        assert 'batch_count' in stats
        assert 'priority_distribution' in stats
        assert 'average_batch_size' in stats

        assert stats['total_objects'] == 1
        assert stats['batch_count'] == 1

    def test_str_representation(self):
        """
        Scenario: String representation

        Given a PriorityBatcher
        When str() is called
        Then a descriptive string should be returned
        """
        batcher = PriorityBatcher()

        str_repr = str(batcher)

        assert "PriorityBatcher" in str_repr
        assert "objects=0" in str_repr
        assert "visible=0" in str_repr
        assert "batches=0" in str_repr

class TestPrioritizedObject:
    """
    Feature: Prioritized Object Wrapper

    The PrioritizedObject class wraps objects with priority information
    for use in priority queues and batching.
    """

    def test_init_valid(self):
        """
        Scenario: Initialize with valid data

        Given valid priority, distance, index, and object
        When PrioritizedObject is created
        Then all attributes should be set correctly
        """
        obj = Mock()
        prioritized_obj = PrioritizedObject(
            priority=BatchPriority.HIGH.value,
            distance=50.0,
            index=0,
            object=obj
        )

        assert prioritized_obj.priority == BatchPriority.HIGH.value
        assert prioritized_obj.distance == 50.0
        assert prioritized_obj.index == 0
        assert prioritized_obj.object == obj
        assert prioritized_obj.layout_data is None

    def test_init_invalid_distance(self):
        """
        Scenario: Reject invalid distance

        Given negative distance
        When PrioritizedObject is created
        Then ValueError should be raised
        """
        obj = Mock()

        with pytest.raises(ValueError, match="Distance cannot be negative"):
            PrioritizedObject(
                priority=BatchPriority.HIGH.value,
                distance=-10.0,
                index=0,
                object=obj
            )

    def test_init_invalid_priority(self):
        """
        Scenario: Reject invalid priority

        Given invalid priority value
        When PrioritizedObject is created
        Then ValueError should be raised
        """
        obj = Mock()

        with pytest.raises(ValueError, match="Invalid priority value"):
            PrioritizedObject(
                priority=999,  # Invalid priority value
                distance=50.0,
                index=0,
                object=obj
            )

    def test_comparison(self):
        """
        Scenario: Compare prioritized objects

        Given multiple PrioritizedObject instances
        When they are compared
        Then they should be ordered by priority, then distance
        """
        obj = Mock()

        # Higher priority (lower value) comes first
        high_priority = PrioritizedObject(
            priority=BatchPriority.HIGH.value,  # 0
            distance=100.0,
            index=0,
            object=obj
        )

        low_priority = PrioritizedObject(
            priority=BatchPriority.LOW.value,  # 2
            distance=50.0,
            index=1,
            object=obj
        )

        # HIGH priority (0) < LOW priority (2)
        assert high_priority < low_priority

        # Same priority, shorter distance comes first
        short_distance = PrioritizedObject(
            priority=BatchPriority.HIGH.value,
            distance=50.0,
            index=2,
            object=obj
        )

        long_distance = PrioritizedObject(
            priority=BatchPriority.HIGH.value,
            distance=100.0,
            index=3,
            object=obj
        )

        # Same priority, 50.0 < 100.0
        assert short_distance < long_distance
