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

"""PriorityBatcher class for viewport-aware object batching.

This class manages batching of text objects for parallel rendering based on
their distance from the viewport center, ensuring closest objects are rendered first.
"""

import heapq
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from PySide6 import QtCore

from pyzui.objects.mediaobjects.mediaobjectsutils.string.textlayout import TextLayoutData


class BatchPriority(Enum):
    """Priority levels for text object batching."""

    HIGH = 0  # Objects in viewport center
    MEDIUM = 1  # Objects near viewport
    LOW = 2  # Objects far from viewport
    BACKGROUND = 3  # Objects outside viewport (for pre-calculation)


@dataclass(order=True)
class PrioritizedObject:
    """Wrapper for objects with priority for heapq."""

    priority: int
    distance: float
    index: int = field(compare=False)
    object: Any = field(compare=False)
    layout_data: TextLayoutData | None = field(compare=False, default=None)

    def __post_init__(self):
        """Validate the prioritized object."""
        if self.distance < 0:
            raise ValueError("Distance cannot be negative")
        if self.priority not in [p.value for p in BatchPriority]:
            raise ValueError(f"Invalid priority value: {self.priority}")


class PriorityBatcher:
    """Manages batching of text objects for parallel rendering.

    This class organizes text objects into priority batches based on their
    distance from the viewport center, ensuring that objects closest to the
    viewport are rendered first for optimal perceived performance.

    Attributes:
        batch_size: Number of objects per batch
        max_batches: Maximum number of batches to create
        viewport_center: Current viewport center coordinates
        viewport_rect: Current viewport rectangle
        priority_thresholds: Distance thresholds for each priority level
    """

    def __init__(
        self,
        batch_size: int = 10,
        max_batches: int = 10,
        viewport_center: tuple[float, float] | None = None,
        viewport_rect: QtCore.QRectF | None = None,
    ) -> None:
        """Initialize the PriorityBatcher.

        Args:
            batch_size: Number of objects per batch (default: 10)
            max_batches: Maximum number of batches to create (default: 10)
            viewport_center: Initial viewport center coordinates
            viewport_rect: Initial viewport rectangle
        """
        self.batch_size = batch_size
        self.max_batches = max_batches
        self.viewport_center = viewport_center or (0.0, 0.0)
        self.viewport_rect = viewport_rect or QtCore.QRectF(0, 0, 800, 800)

        # Distance thresholds for priority levels (in scene units)
        # These can be adjusted based on typical scene scale
        self.priority_thresholds = {
            BatchPriority.HIGH: 1000.0,  # Very close to center
            BatchPriority.MEDIUM: 2000.0,  # Within moderate distance
            BatchPriority.LOW: 4000.0,  # Further away but still relevant
            BatchPriority.BACKGROUND: float("inf"),  # Everything else
        }

        # Internal state
        self._objects: list[Any] = []
        self._layout_cache: dict[int, TextLayoutData] = {}
        self._current_batches: list[list[PrioritizedObject]] = []
        self._batch_metadata: list[dict[str, Any]] = []

    def update_viewport(self, viewport_center: tuple[float, float], viewport_rect: QtCore.QRectF) -> None:
        """Update the viewport information.

        Args:
            viewport_center: New viewport center coordinates
            viewport_rect: New viewport rectangle
        """
        self.viewport_center = viewport_center
        self.viewport_rect = viewport_rect

        # Clear batches since viewport changed
        self._current_batches.clear()
        self._batch_metadata.clear()

    def add_objects(self, objects: list[Any]) -> None:
        """Add objects to be batched.

        Args:
            objects: List of objects (typically StringMediaObjects)
        """
        self._objects.extend(objects)

        # Clear batches since objects changed
        self._current_batches.clear()
        self._batch_metadata.clear()

    def clear_objects(self) -> None:
        """Clear all objects from the batcher."""
        self._objects.clear()
        self._layout_cache.clear()
        self._current_batches.clear()
        self._batch_metadata.clear()

    def calculate_distance(self, obj: Any) -> float:
        """Calculate distance from object to viewport center.

        Args:
            obj: Object with x, y attributes

        Returns:
            Euclidean distance to viewport center
        """
        if not hasattr(obj, "x") or not hasattr(obj, "y"):
            raise ValueError("Object must have x and y attributes")

        dx = obj.x - self.viewport_center[0]
        dy = obj.y - self.viewport_center[1]
        return math.sqrt(dx * dx + dy * dy)

    def get_priority(self, distance: float) -> BatchPriority:
        """Get priority level based on distance.

        Args:
            distance: Distance from viewport center

        Returns:
            BatchPriority level
        """
        if distance <= self.priority_thresholds[BatchPriority.HIGH]:
            return BatchPriority.HIGH
        elif distance <= self.priority_thresholds[BatchPriority.MEDIUM]:
            return BatchPriority.MEDIUM
        elif distance <= self.priority_thresholds[BatchPriority.LOW]:
            return BatchPriority.LOW
        else:
            return BatchPriority.BACKGROUND

    def is_in_viewport(self, obj: Any) -> bool:
        """Check if object is in current viewport.

        Args:
            obj: Object with position and size attributes

        Returns:
            True if object intersects viewport, False otherwise
        """
        # Create a bounding rectangle for the object
        # This is simplified - actual implementation would use object's bounds
        if not hasattr(obj, "x") or not hasattr(obj, "y"):
            return False

        # Estimate object size (default to 100x50 for text objects)
        width = getattr(obj, "width", 100)
        height = getattr(obj, "height", 50)

        obj_rect = QtCore.QRectF(obj.x - width / 2, obj.y - height / 2, width, height)

        return bool(obj_rect.intersects(self.viewport_rect))

    def create_batches(self) -> list[list[PrioritizedObject]]:
        """Create priority-based batches of objects.

        Returns:
            List of batches, each batch is a list of PrioritizedObject
        """
        if not self._objects:
            return []

        # If we already have batches, return them
        if self._current_batches:
            return self._current_batches

        # Create priority queue for objects
        priority_queue: list[PrioritizedObject] = []

        for i, obj in enumerate(self._objects):
            # Skip objects that aren't StringMediaObjects
            # Check if it has the required methods for text rendering
            if not hasattr(obj, "_get_text") or not hasattr(obj, "x") or not hasattr(obj, "y"):
                continue

            # Calculate distance and priority
            distance = self.calculate_distance(obj)
            priority_level = self.get_priority(distance)

            # Check if object is in viewport
            in_viewport = self.is_in_viewport(obj)

            # Adjust priority for objects outside viewport
            if not in_viewport and priority_level != BatchPriority.BACKGROUND:
                priority_level = BatchPriority.BACKGROUND

            # Create prioritized object
            prioritized_obj = PrioritizedObject(priority=priority_level.value, distance=distance, index=i, object=obj)

            # Add to priority queue (heapq uses min-heap, so lower priority = higher importance)
            heapq.heappush(priority_queue, prioritized_obj)

        # Create batches from priority queue
        batches: list[list[PrioritizedObject]] = []
        current_batch = []
        batch_metadata = []

        while priority_queue and len(batches) < self.max_batches:
            prioritized_obj = heapq.heappop(priority_queue)

            # Skip BACKGROUND priority objects if we have enough higher priority objects
            if prioritized_obj.priority == BatchPriority.BACKGROUND.value and len(batches) >= self.max_batches // 2:
                continue

            current_batch.append(prioritized_obj)

            # Check if batch is full
            if len(current_batch) >= self.batch_size:
                batches.append(current_batch)
                batch_metadata.append(
                    {
                        "priority": BatchPriority(prioritized_obj.priority),
                        "average_distance": sum(p.distance for p in current_batch) / len(current_batch),
                        "size": len(current_batch),
                    }
                )
                current_batch = []

        # Add remaining objects as last batch
        if current_batch:
            batches.append(current_batch)
            if current_batch:
                avg_priority = BatchPriority(current_batch[0].priority)
                batch_metadata.append(
                    {
                        "priority": avg_priority,
                        "average_distance": sum(p.distance for p in current_batch) / len(current_batch),
                        "size": len(current_batch),
                    }
                )

        # Store batches and metadata
        self._current_batches = batches
        self._batch_metadata = batch_metadata

        return batches

    def get_batch_metadata(self) -> list[dict[str, Any]]:
        """Get metadata for all batches.

        Returns:
            List of metadata dictionaries for each batch
        """
        if not self._batch_metadata:
            self.create_batches()
        return self._batch_metadata

    def get_object_count(self) -> int:
        """Get total number of objects in batcher.

        Returns:
            Number of objects
        """
        return len(self._objects)

    def get_visible_object_count(self) -> int:
        """Get number of objects currently in viewport.

        Returns:
            Number of objects in viewport
        """
        count = 0
        for obj in self._objects:
            if self.is_in_viewport(obj):
                count += 1
        return count

    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate for layout data.

        Returns:
            Cache hit rate as float between 0 and 1
        """
        if not self._layout_cache:
            return 0.0

        # This would be calculated based on actual cache usage
        # For now, return a placeholder value
        total_objects = len(self._objects)
        cached_objects = len(self._layout_cache)

        if total_objects == 0:
            return 0.0

        return cached_objects / total_objects

    def update_layout_cache(self, index: int, layout_data: TextLayoutData) -> None:
        """Update layout cache for an object.

        Args:
            index: Object index
            layout_data: Pre-calculated layout data
        """
        self._layout_cache[index] = layout_data

    def get_layout_cache(self, index: int) -> TextLayoutData | None:
        """Get layout data from cache.

        Args:
            index: Object index

        Returns:
            TextLayoutData if cached, None otherwise
        """
        return self._layout_cache.get(index)

    def clear_layout_cache(self) -> None:
        """Clear all layout cache."""
        self._layout_cache.clear()

    def invalidate_cache_for_object(self, index: int) -> None:
        """Invalidate cache for specific object.

        Args:
            index: Object index
        """
        self._layout_cache.pop(index, None)

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about current batching state.

        Returns:
            Dictionary with statistics
        """
        batches = self.create_batches()

        total_objects = self.get_object_count()
        visible_objects = self.get_visible_object_count()
        cache_hit_rate = self.get_cache_hit_rate()

        # Calculate priority distribution
        priority_dist = dict.fromkeys(BatchPriority, 0)
        for batch in batches:
            for obj in batch:
                priority = BatchPriority(obj.priority)
                priority_dist[priority] = priority_dist.get(priority, 0) + 1

        return {
            "total_objects": total_objects,
            "visible_objects": visible_objects,
            "cache_hit_rate": cache_hit_rate,
            "batch_count": len(batches),
            "priority_distribution": priority_dist,
            "average_batch_size": sum(len(batch) for batch in batches) / max(len(batches), 1),
        }

    def __str__(self) -> str:
        """String representation for debugging."""
        stats = self.get_statistics()
        return (
            f"PriorityBatcher(objects={stats['total_objects']}, "
            f"visible={stats['visible_objects']}, "
            f"batches={stats['batch_count']}, "
            f"cache_hit={stats['cache_hit_rate']:.2f})"
        )
