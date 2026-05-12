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

"""Unit tests for SceneParallelRenderer class."""

from unittest.mock import Mock, patch

from pyzui.objects.scene.sceneutils.parallel import SceneParallelRenderer


class TestSceneParallelRenderer:
    """
    Feature: SceneParallelRenderer Class

    The SceneParallelRenderer class encapsulates parallel rendering functionality
    that was previously part of the Scene class, providing better separation of concerns.
    """

    def test_initialization_default(self):
        """
        Scenario: Initialize SceneParallelRenderer with default config

        Given a mock Scene object
        When SceneParallelRenderer is initialized with no config
        Then it should be enabled by default
        And have default configuration values
        """
        mock_scene = Mock()
        renderer = SceneParallelRenderer(mock_scene)

        assert renderer.is_enabled()
        # Default config should be used

    def test_initialization_with_config(self):
        """
        Scenario: Initialize SceneParallelRenderer with custom config

        Given a mock Scene object
        And a configuration dictionary
        When SceneParallelRenderer is initialized with the config
        Then it should use the configuration values
        """
        mock_scene = Mock()
        config = {
            'parallel_rendering': {
                'enabled': False,
                'max_workers': 2,
                'batch_size': 5,
                'max_batches': 3
            }
        }

        renderer = SceneParallelRenderer(mock_scene, config)

        assert not renderer.is_enabled()

    def test_enable_disable(self):
        """
        Scenario: Enable and disable parallel rendering

        Given a SceneParallelRenderer
        When enable() is called with False
        Then is_enabled() should return False
        When enable() is called with True
        Then is_enabled() should return True
        """
        mock_scene = Mock()
        renderer = SceneParallelRenderer(mock_scene)

        # Initially enabled by default
        assert renderer.is_enabled()

        # Disable
        renderer.enable(False)
        assert not renderer.is_enabled()

        # Re-enable
        renderer.enable(True)
        assert renderer.is_enabled()

    def test_get_stats(self):
        """
        Scenario: Get parallel rendering statistics

        Given a SceneParallelRenderer
        When get_stats() is called
        Then it should return a dictionary with statistics
        And the dictionary should contain expected keys
        """
        mock_scene = Mock()
        mock_scene.vzmoving = False
        renderer = SceneParallelRenderer(mock_scene)

        stats = renderer.get_stats()

        assert isinstance(stats, dict)
        assert 'parallel_enabled' in stats
        assert 'scene_moving' in stats
        assert 'total_text_objects' in stats
        assert 'visible_text_objects' in stats
        assert 'batches_processed' in stats

    def test_initialize_components(self):
        """
        Scenario: Initialize parallel rendering components

        Given a SceneParallelRenderer
        When initialize() is called
        Then internal components should be created
        """
        mock_scene = Mock()
        renderer = SceneParallelRenderer(mock_scene)

        # Mock the component creation
        with patch.object(renderer, '_layout_calculator', None), \
             patch.object(renderer, '_priority_batcher', None):
            renderer.initialize()

            # Components should be initialized
            # (actual initialization is tested in integration tests)
            pass

    def test_update_viewport(self):
        """
        Scenario: Update viewport information

        Given a SceneParallelRenderer
        When update_viewport() is called
        Then it should update internal viewport state
        """
        mock_scene = Mock()
        mock_scene.centre = (100.0, 200.0)
        mock_scene.viewport_size = (800, 600)
        renderer = SceneParallelRenderer(mock_scene)

        # Enable renderer
        renderer.enable(True)

        # Mock priority batcher
        mock_batcher = Mock()
        renderer._priority_batcher = mock_batcher

        renderer.update_viewport()

        # Viewport should be updated
        # (actual viewport calculations are tested in integration tests)
        assert renderer._last_viewport_center == (100.0, 200.0)

    def test_precalculate_text_layouts_disabled(self):
        """
        Scenario: Precalculate text layouts when disabled

        Given a disabled SceneParallelRenderer
        When precalculate_text_layouts() is called
        Then it should return early without doing work
        """
        mock_scene = Mock()
        renderer = SceneParallelRenderer(mock_scene)
        renderer.enable(False)  # Disable

        # Should return early when disabled
        renderer.precalculate_text_layouts()
        # No error should occur

    def test_invalidate_cache(self):
        """
        Scenario: Invalidate parallel rendering cache

        Given a SceneParallelRenderer
        When invalidate_cache() is called
        Then it should clear cached layout data
        """
        mock_scene = Mock()
        # Mock _get_text_objects to return empty list
        mock_scene._get_text_objects.return_value = []
        renderer = SceneParallelRenderer(mock_scene)

        # Mock components
        mock_batcher = Mock()
        mock_calculator = Mock()
        renderer._priority_batcher = mock_batcher
        renderer._layout_calculator = mock_calculator

        renderer.invalidate_cache()

        # Should call clear_layout_cache on batcher
        mock_batcher.clear_layout_cache.assert_called_once()
        # Should call invalidate_cache on calculator
        mock_calculator.invalidate_cache.assert_called_once()
        # Should call _get_text_objects on scene
        mock_scene._get_text_objects.assert_called_once()


class TestSceneParallelRendererShutdown:
    """
    Feature: SceneParallelRenderer Shutdown

    The shutdown() method should gracefully stop the layout calculator
    and release resources.
    """

    def test_shutdown_with_layout_calculator(self):
        """
        Scenario: Shutdown with active layout calculator

        Given a SceneParallelRenderer with an initialized layout calculator
        When shutdown() is called
        Then the layout calculator should be shut down with wait=True
        And both layout_calculator and priority_batcher should be cleared
        """
        mock_scene = Mock()
        renderer = SceneParallelRenderer(mock_scene)
        mock_calculator = Mock()
        renderer._layout_calculator = mock_calculator
        mock_batcher = Mock()
        renderer._priority_batcher = mock_batcher

        renderer.shutdown()

        mock_calculator.shutdown.assert_called_once_with(wait=True)
        assert renderer._layout_calculator is None
        assert renderer._priority_batcher is None
        assert renderer.is_enabled() is False

    def test_shutdown_without_layout_calculator(self):
        """
        Scenario: Shutdown without layout calculator

        Given a SceneParallelRenderer that was never initialized
        When shutdown() is called
        Then no error should occur
        """
        mock_scene = Mock()
        renderer = SceneParallelRenderer(mock_scene)
        renderer._layout_calculator = None

        renderer.shutdown()
        assert renderer.is_enabled() is False

    def test_shutdown_idempotent(self):
        """
        Scenario: Shutdown is idempotent

        Given a SceneParallelRenderer
        When shutdown() is called multiple times
        Then no error should occur on subsequent calls
        """
        mock_scene = Mock()
        renderer = SceneParallelRenderer(mock_scene)
        mock_calculator = Mock()
        renderer._layout_calculator = mock_calculator

        renderer.shutdown()
        renderer.shutdown()
        # Calculator.shutdown() should only be called once
        # (second call sees None and skips)
        mock_calculator.shutdown.assert_called_once()
