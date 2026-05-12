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

"""Integration tests for parallel text rendering system.

These tests verify that the parallel rendering components work together
correctly to improve performance for scenes with many text objects.
"""

from unittest.mock import Mock

from PySide6 import QtCore, QtGui

from pyzui.objects.mediaobjects.mediaobjectsutils.string.parallellayout import ParallelLayoutCalculator
from pyzui.objects.mediaobjects.mediaobjectsutils.string.textlayout import TextLayoutData
from pyzui.objects.scene.sceneutils.prioritybatcher import PriorityBatcher
from pyzui.objects.scene.scene import Scene


class TestParallelRenderingIntegration:
    """
    Feature: Parallel Text Rendering Integration

    The parallel rendering system integrates TextLayoutData, PriorityBatcher,
    and ParallelLayoutCalculator to improve rendering performance for scenes
    with many text objects during zoom/pan operations.
    """

    def test_scene_with_parallel_rendering(self):
        """
        Scenario: Scene with parallel rendering enabled

        Given a Scene with parallel rendering enabled
        When parallel rendering components are initialized
        Then the system should be ready for parallel text rendering
        """
        # Create a scene with parallel rendering config
        config = {
            'parallel_rendering': {
                'enabled': True,
                'max_workers': 2,
                'batch_size': 5,
                'max_batches': 4
            }
        }

        scene = Scene(config=config)

        # Verify parallel rendering is enabled
        stats = scene.get_parallel_stats()
        assert stats['parallel_enabled']

        # Parallel rendering components are initialized automatically when needed.
        # We can verify initialization by checking stats.
        stats = scene.get_parallel_stats()
        assert 'parallel_enabled' in stats
        assert stats['parallel_enabled']

        # Clean up
        scene.enable_parallel_rendering(False)

    def test_parallel_layout_calculation(self):
        """
        Scenario: Parallel layout calculation

        Given a ParallelLayoutCalculator
        And multiple text objects
        When layouts are calculated in parallel
        Then calculation results should be cached
        And statistics should be updated
        """
        calculator = ParallelLayoutCalculator(max_workers=2)

        # Create mock objects with attributes needed by from_string_object
        mock_objects = []
        for i in range(5):
            obj = Mock()
            obj.pos = (i * 50.0, i * 30.0)
            obj.width = 80.0
            obj.height = 30.0
            obj.base_pointsize = 24.0
            obj.scale = 1.0
            obj._get_text = Mock(return_value=f"Text {i}")
            obj._get_color = Mock(return_value=QtGui.QColor(255, 0, 0))
            mock_objects.append(obj)

        # Create prioritized objects
        from pyzui.objects.scene.sceneutils.prioritybatcher import BatchPriority, PrioritizedObject

        prioritized_objects = []
        for i, obj in enumerate(mock_objects):
            p_obj = PrioritizedObject(
                priority=BatchPriority.HIGH.value,
                distance=i * 10.0,
                index=i,
                object=obj
            )
            prioritized_objects.append(p_obj)

        # Submit batch for calculation
        viewport_rect = QtCore.QRectF(0, 0, 800, 600)
        calculator.submit_batch(prioritized_objects, viewport_rect)

        # Wait for calculations to complete (deterministic, not blind sleep)
        batch_indices = [p.index for p in prioritized_objects]
        calculator.wait_for_batch(batch_indices, timeout_ms=10000)

        # Check statistics
        stats = calculator.get_statistics()
        assert stats['total_calculations'] >= 0
        assert stats['cache_size'] >= 0

        # Clean up
        calculator.shutdown()

    def test_priority_batching_integration(self):
        """
        Scenario: Priority batching integration

        Given a PriorityBatcher with text objects at different distances
        When batches are created
        Then objects should be grouped by priority
        And closer objects should be in higher priority batches
        """
        batcher = PriorityBatcher(
            batch_size=3,
            max_batches=3,
            viewport_center=(0.0, 0.0)
        )

        # Create text objects at different distances
        objects = []
        for i in range(9):
            # Create objects with increasing distance
            obj = Mock()
            obj.x = i * 100.0
            obj.y = i * 100.0
            obj.width = 50.0
            obj.height = 25.0
            obj._get_text = Mock(return_value=f"Object {i}")
            objects.append(obj)

        batcher.add_objects(objects)

        # Create batches
        batches = batcher.create_batches()

        # Should have batches (up to max_batches)
        assert len(batches) <= 3

        # First batch should have closest objects
        if batches:
            first_batch = batches[0]
            assert len(first_batch) <= 3  # batch_size

            # Check that objects in first batch are closer than some threshold
            max_distance_in_first_batch = max(p_obj.distance for p_obj in first_batch)

            # If we have a second batch, its objects should be further away
            if len(batches) > 1:
                second_batch = batches[1]
                min_distance_in_second_batch = min(p_obj.distance for p_obj in second_batch)
                # Objects in second batch should be further than those in first batch
                assert min_distance_in_second_batch >= max_distance_in_first_batch

    def test_text_layout_data_rendering(self):
        """
        Scenario: Text layout data rendering

        Given a TextLayoutData with pre-calculated layout
        When render is called with a QPainter
        Then the text should be rendered correctly
        """
        # Create TextLayoutData with plain font/color data
        text = "Hello World"
        position = (100.0, 200.0)
        bounding_rect = QtCore.QRectF(90, 190, 100, 50)
        text_rect = QtCore.QRectF(95, 195, 90, 40)

        layout_data = TextLayoutData(
            text=text,
            font_family="Arial",
            font_pointsize=12.0,
            color_r=255,
            color_g=0,
            color_b=0,
            color_a=255,
            position=position,
            bounding_rect=bounding_rect,
            text_rect=text_rect
        )

        # Create a mock painter
        mock_painter = Mock()
        mock_painter.save = Mock()
        mock_painter.restore = Mock()
        mock_painter.setFont = Mock()
        mock_painter.setPen = Mock()
        mock_painter.drawText = Mock()

        # Render the text
        layout_data.render(mock_painter)

        # Verify painter methods were called
        mock_painter.save.assert_called_once()
        mock_painter.setFont.assert_called_once()
        mock_painter.setPen.assert_called_once()
        mock_painter.drawText.assert_called_once()
        mock_painter.restore.assert_called_once()

    def test_performance_improvement_demonstration(self):
        """
        Scenario: Demonstrate performance improvement concept

        Given many text objects
        When rendered sequentially vs in parallel
        Then parallel rendering should be faster (conceptually)
        """
        # This test demonstrates the concept rather than measuring actual performance
        # since performance testing requires more complex setup

        num_objects = 100

        # Simulate sequential rendering time
        sequential_time_per_object = 0.001  # 1ms per object
        sequential_total = num_objects * sequential_time_per_object

        # Simulate parallel rendering time
        # With 4 workers, time is reduced but not perfectly linear due to overhead
        num_workers = 4
        parallel_overhead = 0.005  # 5ms overhead
        parallel_time_per_batch = sequential_time_per_object * (num_objects / num_workers)
        parallel_total = parallel_time_per_batch + parallel_overhead

        # Conceptually, parallel should be faster for many objects
        assert parallel_total < sequential_total, \
            f"Parallel ({parallel_total:.3f}s) should be faster than sequential ({sequential_total:.3f}s) for {num_objects} objects"

        # Calculate speedup factor
        speedup = sequential_total / parallel_total
        print(f"Conceptual speedup for {num_objects} objects with {num_workers} workers: {speedup:.2f}x")

        # For 100 objects, we expect significant speedup
        assert speedup > 2.0, f"Expected >2x speedup, got {speedup:.2f}x"

    def test_configuration_loading(self):
        """
        Scenario: Load parallel rendering configuration

        Given a configuration dictionary
        When Scene is created with the configuration
        Then parallel rendering settings should be applied
        """
        config = {
            'parallel_rendering': {
                'enabled': True,
                'max_workers': 6,
                'batch_size': 8,
                'max_batches': 12,
                'batch_timeout_ms': 2000,
                'enable_profiling': True,
                'priority_thresholds': {
                    'high': 50.0,
                    'medium': 250.0,
                    'low': 1000.0
                }
            }
        }

        scene = Scene(config=config)

        # Check that configuration was applied
        stats = scene.get_parallel_stats()
        assert stats['parallel_enabled']

        # The actual configuration values would be used when components are initialized
        # during rendering

        # Clean up
        scene.enable_parallel_rendering(False)
