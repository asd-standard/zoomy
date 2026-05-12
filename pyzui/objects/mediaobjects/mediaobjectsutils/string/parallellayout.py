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

"""ParallelLayoutCalculator class for parallel text layout calculation.

This class manages parallel calculation of text layouts using thread pools,
ensuring thread safety and efficient resource usage.
"""

from __future__ import annotations

import concurrent.futures
import contextlib
import queue
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from PySide6 import QtCore

from pyzui.logger import get_logger
from pyzui.objects.mediaobjects.mediaobjectsutils.string.textlayout import TextLayoutData

if TYPE_CHECKING:
    from pyzui.objects.scene.sceneutils.prioritybatcher import PrioritizedObject


class CalculationStatus(Enum):
    """Status of layout calculation."""

    PENDING = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    FAILED = 3
    CANCELLED = 4


@dataclass
class CalculationResult:
    """Result of a layout calculation."""

    status: CalculationStatus
    layout_data: TextLayoutData | None = None
    error: Exception | None = None
    processing_time_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)


class ParallelLayoutCalculator:
    """Manages parallel calculation of text layouts using thread pools.

    This class provides thread-safe parallel calculation of text layouts
    for batches of objects, with progress tracking and error handling.

    Attributes:
        max_workers: Maximum number of worker threads
        batch_timeout_ms: Timeout for batch calculations in milliseconds
        enable_profiling: Whether to enable performance profiling
        thread_pool: Thread pool executor for parallel calculations
        calculation_queue: Queue for pending calculations
        results_cache: Cache for calculation results
        lock: Thread lock for thread-safe operations
        shutdown_event: Event to signal shutdown
    """

    def __init__(
        self, max_workers: int | None = None, batch_timeout_ms: float = 5000.0, enable_profiling: bool = False
    ) -> None:
        """Initialize the ParallelLayoutCalculator.

        Args:
            max_workers: Maximum number of worker threads (default: CPU count)
            batch_timeout_ms: Timeout for batch calculations (default: 5000ms)
            enable_profiling: Enable performance profiling (default: False)
        """
        import os

        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.batch_timeout_ms = batch_timeout_ms
        self.enable_profiling = enable_profiling
        self._logger = get_logger("ParallelLayoutCalculator")

        # Thread pool for parallel calculations
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers, thread_name_prefix="TextLayoutWorker"
        )

        # Queue for pending calculations
        self.calculation_queue: queue.Queue[
            tuple[int, PrioritizedObject, QtCore.QRectF, Callable[..., Any] | None] | None
        ] = queue.Queue(maxsize=100)

        # Cache for calculation results
        self.results_cache: dict[int, CalculationResult] = {}

        # Thread synchronization
        self.lock = threading.RLock()
        self.shutdown_event = threading.Event()

        # Statistics
        self._stats = {
            "total_calculations": 0,
            "successful_calculations": 0,
            "failed_calculations": 0,
            "cached_hits": 0,
            "total_processing_time_ms": 0.0,
            "average_processing_time_ms": 0.0,
        }

        # Start worker threads
        self._workers: list[threading.Thread] = []
        self._start_workers()

    def _start_workers(self) -> None:
        """Start worker threads for processing calculations."""
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop, name=f"TextLayoutWorker-{i}", daemon=True)
            worker.start()
            self._workers.append(worker)

    def _worker_loop(self) -> None:
        """Worker thread main loop."""
        while not self.shutdown_event.is_set():
            try:
                # Get calculation task from queue with timeout
                task = self.calculation_queue.get(timeout=0.1)
                if task is None:  # Shutdown signal
                    break

                index, prioritized_obj, viewport_rect, callback = task
                self._process_calculation(index, prioritized_obj, viewport_rect, callback)

                self.calculation_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                self._logger.error("Worker thread error: %s", e)
                continue

    def _process_calculation(
        self,
        index: int,
        prioritized_obj: PrioritizedObject,
        viewport_rect: QtCore.QRectF,
        callback: Callable[[int, CalculationResult], None] | None = None,
    ) -> None:
        """Process a single layout calculation.

        Args:
            index: Object index
            prioritized_obj: Prioritized object to calculate layout for
            viewport_rect: Current viewport rectangle
            callback: Optional callback function for completion
        """
        start_time = time.time()
        result = CalculationResult(status=CalculationStatus.IN_PROGRESS)

        try:
            # Check if we already have a valid result in cache
            with self.lock:
                cached_result = self.results_cache.get(index)
                if (
                    cached_result
                    and cached_result.status == CalculationStatus.COMPLETED
                    and cached_result.layout_data is not None
                    and not cached_result.layout_data.is_stale()
                ):
                    result = cached_result
                    result.processing_time_ms = 0.0  # Cache hit, no processing time
                    self._stats["cached_hits"] += 1
                else:
                    # Calculate new layout
                    layout_data = TextLayoutData.from_string_object(prioritized_obj.object, viewport_rect)
                    processing_time = (time.time() - start_time) * 1000

                    result = CalculationResult(
                        status=CalculationStatus.COMPLETED,
                        layout_data=layout_data,
                        processing_time_ms=processing_time,
                        timestamp=time.time(),
                    )

                    # Update cache
                    with self.lock:
                        self.results_cache[index] = result
                        self._stats["successful_calculations"] += 1
                        self._stats["total_processing_time_ms"] += processing_time
                        self._stats["total_calculations"] += 1

                        # Update average processing time
                        if self._stats["successful_calculations"] > 0:
                            self._stats["average_processing_time_ms"] = (
                                self._stats["total_processing_time_ms"] / self._stats["successful_calculations"]
                            )

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            result = CalculationResult(
                status=CalculationStatus.FAILED, error=e, processing_time_ms=processing_time, timestamp=time.time()
            )

            with self.lock:
                self._stats["failed_calculations"] += 1
                self._stats["total_calculations"] += 1

        finally:
            # Call callback if provided
            if callback:
                try:
                    callback(index, result)
                except Exception as e:
                    self._logger.error("Callback error: %s", e)

    def submit_batch(
        self,
        batch: list[PrioritizedObject],
        viewport_rect: QtCore.QRectF,
        callback: Callable[[int, CalculationResult], None] | None = None,
    ) -> dict[int, CalculationResult]:
        """Submit a batch of objects for parallel layout calculation.

        Args:
            batch: List of prioritized objects
            viewport_rect: Current viewport rectangle
            callback: Optional callback for individual completions

        Returns:
            Dictionary mapping object indices to calculation results
        """
        results = {}

        # Submit each object in the batch for calculation
        for prioritized_obj in batch:
            index = prioritized_obj.index

            # Check cache first
            with self.lock:
                cached_result = self.results_cache.get(index)
                if (
                    cached_result
                    and cached_result.status == CalculationStatus.COMPLETED
                    and cached_result.layout_data is not None
                    and not cached_result.layout_data.is_stale()
                ):
                    results[index] = cached_result
                    self._stats["cached_hits"] += 1
                    continue

            # Submit to calculation queue
            try:
                self.calculation_queue.put((index, prioritized_obj, viewport_rect, callback), timeout=0.1)
                results[index] = CalculationResult(status=CalculationStatus.PENDING)
            except queue.Full:
                # Queue is full, mark as failed
                results[index] = CalculationResult(
                    status=CalculationStatus.FAILED, error=RuntimeError("Calculation queue is full")
                )

        return results

    def wait_for_batch(self, batch_indices: list[int], timeout_ms: float | None = None) -> dict[int, CalculationResult]:
        """Wait for a batch of calculations to complete.

        Args:
            batch_indices: List of object indices to wait for
            timeout_ms: Timeout in milliseconds (default: batch_timeout_ms)

        Returns:
            Dictionary mapping object indices to calculation results
        """
        if timeout_ms is None:
            timeout_ms = self.batch_timeout_ms

        start_time = time.time()
        results = {}

        # Wait for all calculations to complete or timeout
        while time.time() - start_time < timeout_ms / 1000.0:
            with self.lock:
                # Check which calculations are complete
                for index in batch_indices:
                    if index not in results:
                        result = self.results_cache.get(index)
                        if result and result.status in [
                            CalculationStatus.COMPLETED,
                            CalculationStatus.FAILED,
                            CalculationStatus.CANCELLED,
                        ]:
                            results[index] = result

            # Check if all calculations are complete
            if len(results) == len(batch_indices):
                break

            # Sleep briefly to avoid busy waiting
            time.sleep(0.01)

        # Fill in any missing results with pending status
        for index in batch_indices:
            if index not in results:
                results[index] = CalculationResult(status=CalculationStatus.PENDING)

        return results

    def get_result(self, index: int) -> CalculationResult | None:
        """Get calculation result for a specific object.

        Args:
            index: Object index

        Returns:
            CalculationResult if available, None otherwise
        """
        with self.lock:
            return self.results_cache.get(index)

    def invalidate_cache(self, index: int | None = None) -> None:
        """Invalidate cache for specific object or all objects.

        Args:
            index: Object index to invalidate, or None for all objects
        """
        with self.lock:
            if index is not None:
                self.results_cache.pop(index, None)
            else:
                self.results_cache.clear()

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about calculator performance.

        Returns:
            Dictionary with statistics
        """
        with self.lock:
            stats = self._stats.copy()

            # Add queue information
            stats["queue_size"] = self.calculation_queue.qsize()
            stats["active_workers"] = sum(1 for w in self._workers if w.is_alive())
            stats["total_workers"] = len(self._workers)

            # Add cache information
            stats["cache_size"] = len(self.results_cache)
            stats["cache_hit_rate"] = stats["cached_hits"] / max(stats["total_calculations"], 1)

            return stats

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the calculator and worker threads.

        Args:
            wait: Whether to wait for pending calculations to complete
        """
        # Signal shutdown
        self.shutdown_event.set()

        # Add shutdown signals to queue
        for _ in range(self.max_workers):
            with contextlib.suppress(queue.Full):
                self.calculation_queue.put(None, timeout=0.1)

        # Shutdown thread pool
        self.thread_pool.shutdown(wait=wait)

        # Wait for worker threads
        for worker in self._workers:
            if worker.is_alive():
                worker.join(timeout=1.0)

    def calculate_layout_sync(
        self, prioritized_obj: PrioritizedObject, viewport_rect: QtCore.QRectF
    ) -> CalculationResult:
        """Calculate layout synchronously (for testing/debugging).

        Args:
            prioritized_obj: Prioritized object to calculate layout for
            viewport_rect: Current viewport rectangle

        Returns:
            CalculationResult
        """
        start_time = time.time()

        try:
            layout_data = TextLayoutData.from_string_object(prioritized_obj.object, viewport_rect)
            processing_time = (time.time() - start_time) * 1000

            result = CalculationResult(
                status=CalculationStatus.COMPLETED,
                layout_data=layout_data,
                processing_time_ms=processing_time,
                timestamp=time.time(),
            )

            # Update cache
            with self.lock:
                self.results_cache[prioritized_obj.index] = result
                self._stats["successful_calculations"] += 1
                self._stats["total_processing_time_ms"] += processing_time
                self._stats["total_calculations"] += 1

            return result

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            result = CalculationResult(
                status=CalculationStatus.FAILED, error=e, processing_time_ms=processing_time, timestamp=time.time()
            )

            with self.lock:
                self._stats["failed_calculations"] += 1
                self._stats["total_calculations"] += 1

            return result

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - shutdown calculator."""
        self.shutdown(wait=True)

    def __str__(self) -> str:
        """String representation for debugging."""
        stats = self.get_statistics()
        return (
            f"ParallelLayoutCalculator(workers={stats['active_workers']}/{stats['total_workers']}, "
            f"queue={stats['queue_size']}, "
            f"cache={stats['cache_size']}, "
            f"hit_rate={stats['cache_hit_rate']:.2f})"
        )
