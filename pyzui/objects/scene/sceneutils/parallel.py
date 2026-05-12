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

"""SceneParallelRenderer class for parallel rendering operations.

This class encapsulates all parallel rendering functionality that was
previously part of the Scene class, providing better separation of concerns.
"""

import logging
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyzui.objects.mediaobjects.stringmediaobject import StringMediaObject
    from pyzui.objects.scene.scene import Scene

from PySide6 import QtCore
from PySide6.QtGui import QPainter

from pyzui.logger import get_logger
from pyzui.objects.mediaobjects.mediaobjectsutils.string.parallellayout import ParallelLayoutCalculator

from .prioritybatcher import PriorityBatcher


class SceneParallelRenderer:
    """Manages parallel rendering operations for a Scene.

    This class encapsulates all parallel rendering functionality that was
    previously part of the Scene class, providing better separation of concerns.

    Attributes:
        _scene: Reference to parent Scene
        _config: Parallel rendering configuration
        _enabled: Whether parallel rendering is enabled
        _layout_calculator: Parallel layout calculator instance
        _priority_batcher: Priority batcher for text objects
        _last_viewport_center: Last known viewport center
        _last_viewport_rect: Last known viewport rectangle
        _stats: Parallel rendering statistics
        _logger: Logger instance
    """

    def __init__(self, scene: "Scene", config: dict[str, Any] | None = None):
        """Initialize the SceneParallelRenderer.

        Args:
            scene: Reference to parent Scene
            config: Configuration dictionary (may contain 'parallel_rendering' key)
        """
        self._scene = scene
        self._config = config.get("parallel_rendering", {}) if config else {}
        self._enabled: bool = self._config.get("enabled", True)
        self._layout_calculator: ParallelLayoutCalculator | None = None
        self._priority_batcher: PriorityBatcher | None = None
        self._last_viewport_center: tuple[float, float] = (0.0, 0.0)
        self._last_viewport_rect: QtCore.QRectF | None = None
        self._stats: dict[str, Any] = {
            "total_text_objects": 0,
            "visible_text_objects": 0,
            "batches_processed": 0,
            "cache_hit_rate": 0.0,
            "average_batch_time_ms": 0.0,
            "total_processing_time_ms": 0.0,
        }
        self._logger: logging.Logger = get_logger("SceneParallelRenderer")

    def is_enabled(self) -> bool:
        """Check if parallel rendering is enabled.

        Returns:
            True if parallel rendering is enabled, False otherwise
        """
        return self._enabled

    def initialize(self) -> None:
        """Initialize parallel rendering components if not already initialized."""
        if self._layout_calculator is None:
            # Use config values or defaults
            max_workers = self._config.get("max_workers", 4)
            batch_timeout_ms = self._config.get("batch_timeout_ms", 1000.0)
            enable_profiling = self._config.get("enable_profiling", False)

            self._layout_calculator = ParallelLayoutCalculator(
                max_workers=max_workers, batch_timeout_ms=batch_timeout_ms, enable_profiling=enable_profiling
            )

        if self._priority_batcher is None:
            # Use config values or defaults
            batch_size = self._config.get("batch_size", 10)
            max_batches = self._config.get("max_batches", 10)

            self._priority_batcher = PriorityBatcher(
                batch_size=batch_size,
                max_batches=max_batches,
                viewport_center=self._last_viewport_center,
                viewport_rect=self._last_viewport_rect or QtCore.QRectF(0, 0, 100, 100),
            )

    def update_viewport(self) -> None:
        """Update viewport information for parallel rendering components."""
        if not self._enabled:
            return

        # Calculate current viewport center and rectangle
        viewport_center = (self._scene.centre[0], self._scene.centre[1])
        viewport_width, viewport_height = self._scene.viewport_size
        viewport_rect = QtCore.QRectF(
            self._scene.centre[0] - viewport_width / 2,
            self._scene.centre[1] - viewport_height / 2,
            viewport_width,
            viewport_height,
        )

        # Check if viewport has changed significantly
        viewport_changed = (
            abs(viewport_center[0] - self._last_viewport_center[0]) > 10.0
            or abs(viewport_center[1] - self._last_viewport_center[1]) > 10.0
            or self._last_viewport_rect is None
        )

        if viewport_changed:
            self._last_viewport_center = viewport_center
            self._last_viewport_rect = viewport_rect

            # Update priority batcher if initialized
            if self._priority_batcher:
                self._priority_batcher.update_viewport(viewport_center, viewport_rect)

    def _get_text_objects(self) -> list["StringMediaObject"]:
        """Get all StringMediaObjects in the scene.

        Returns:
            List of StringMediaObject instances
        """
        # Delegate to Scene's method
        return self._scene._get_text_objects()

    def precalculate_text_layouts(self) -> None:
        """Pre-calculate text layouts for parallel rendering.

        This method should be called before rendering when the scene is moving
        to prepare layout data for parallel rendering.
        """
        if not self._enabled:
            return

        self.initialize()
        self.update_viewport()

        # Get text objects
        text_objects = self._get_text_objects()
        if not text_objects:
            return

        # Update statistics
        self._stats["total_text_objects"] = len(text_objects)

        # Add objects to priority batcher
        if self._priority_batcher:
            self._priority_batcher.clear_objects()
            self._priority_batcher.add_objects(text_objects)

            # Create batches
            batches = self._priority_batcher.create_batches()
            self._stats["visible_text_objects"] = self._priority_batcher.get_visible_object_count()

            # Submit batches for parallel calculation
            if batches and self._layout_calculator:
                viewport_rect = self._last_viewport_rect or QtCore.QRectF(0, 0, 100, 100)

                for batch in batches:
                    # Submit batch for parallel calculation
                    self._layout_calculator.submit_batch(
                        batch, viewport_rect, callback=self._on_layout_calculation_complete
                    )

    def _on_layout_calculation_complete(self, index: int, result: Any) -> None:
        """Callback for when layout calculation completes.

        Args:
            index: Object index
            result: CalculationResult
        """
        # This callback can be used to update statistics or handle errors
        # For now, we just update statistics
        if hasattr(result, "status") and result.status.name == "COMPLETED":
            self._stats["batches_processed"] += 1

    def render_text(self, painter: QPainter) -> bool:
        """Render text objects using parallel rendering.

        Args:
            painter: QPainter object to render with

        Returns:
            True if parallel rendering was used, False otherwise
        """
        if not self._enabled or not self._scene.vzmoving:
            return False

        if not self._priority_batcher or not self._layout_calculator:
            return False

        # Get batches from priority batcher
        batches = self._priority_batcher.create_batches()
        if not batches:
            return False

        start_time = time.time()
        rendered_count = 0

        # Render each batch
        for batch in batches:
            for prioritized_obj in batch:
                # Get layout data from cache
                layout_data = self._priority_batcher.get_layout_cache(prioritized_obj.index)
                if layout_data and layout_data.is_valid and not layout_data.is_stale():
                    # Render using layout data
                    obj = prioritized_obj.object
                    # Use string comparison instead of isinstance() for performance and to avoid circular imports
                    # This is consistent with patterns in scene.py and 2.8x faster
                    if type(obj).__name__ == "StringMediaObject":
                        if obj.render_with_layout(painter, layout_data):
                            rendered_count += 1

        # Update statistics
        processing_time = (time.time() - start_time) * 1000
        self._stats["total_processing_time_ms"] += processing_time

        if rendered_count > 0:
            self._stats["average_batch_time_ms"] = self._stats["total_processing_time_ms"] / max(
                self._stats["batches_processed"], 1
            )

        return rendered_count > 0

    def enable(self, enabled: bool = True) -> None:
        """Enable or disable parallel rendering.

        Args:
            enabled: Whether to enable parallel rendering
        """
        self._enabled = enabled

        if enabled:
            self.initialize()
        else:
            # Clean up resources
            if self._layout_calculator:
                self._layout_calculator.shutdown(wait=True)
                self._layout_calculator = None

            self._priority_batcher = None

    def shutdown(self) -> None:
        """Shut down parallel rendering and release resources.

        Stops the layout calculator and clears the priority batcher.
        Safe to call multiple times.
        """
        self._enabled = False
        if self._layout_calculator:
            self._layout_calculator.shutdown(wait=True)
            self._layout_calculator = None
        self._priority_batcher = None

    def get_stats(self) -> dict[str, Any]:
        """Get parallel rendering statistics.

        Returns:
            Dictionary with parallel rendering statistics
        """
        stats = self._stats.copy()

        # Add current state information
        stats["parallel_enabled"] = self._enabled
        stats["scene_moving"] = self._scene.vzmoving

        if self._priority_batcher:
            batcher_stats = self._priority_batcher.get_statistics()
            stats.update(
                {
                    "batcher_total_objects": batcher_stats["total_objects"],
                    "batcher_visible_objects": batcher_stats["visible_objects"],
                    "batcher_cache_hit_rate": batcher_stats["cache_hit_rate"],
                    "batcher_batch_count": batcher_stats["batch_count"],
                }
            )

        if self._layout_calculator:
            calculator_stats = self._layout_calculator.get_statistics()
            stats.update(
                {
                    "calculator_queue_size": calculator_stats["queue_size"],
                    "calculator_active_workers": calculator_stats["active_workers"],
                    "calculator_cache_size": calculator_stats["cache_size"],
                    "calculator_cache_hit_rate": calculator_stats["cache_hit_rate"],
                }
            )

        return stats

    def invalidate_cache(self) -> None:
        """Invalidate parallel rendering cache."""
        if self._priority_batcher:
            self._priority_batcher.clear_layout_cache()

        if self._layout_calculator:
            self._layout_calculator.invalidate_cache()

        # Also invalidate cache in all text objects
        text_objects = self._get_text_objects()
        for obj in text_objects:
            obj.enable_parallel_rendering(False)  # This clears layout cache
            obj.enable_parallel_rendering(True)  # Re-enable
