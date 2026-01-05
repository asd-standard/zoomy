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

"""
Integration Tests: Scene Persistence
====================================

This module contains integration tests for scene save/load functionality,
validating that TiledMediaObjects preserve their position and zoomlevel
after a save/load round-trip.

These tests ensure that the autofit behavior doesn't override saved
properties when loading scenes from .pzs files.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
import shutil
import tempfile
from pathlib import Path
from PIL import Image

from pyzui.objects.scene.scene import Scene, load_scene
from pyzui.objects.mediaobjects.tiledmediaobject import TiledMediaObject
from pyzui.tilesystem.tiler import Tiler
from pyzui.tilesystem import tilestore
from pyzui.tilesystem import tilemanager


class ConcreteTiler(Tiler):
    """
    A concrete implementation of Tiler for testing purposes.
    """

    def __init__(self, infile, media_id=None, filext='png', tilesize=256):
        super().__init__(infile, media_id, filext, tilesize)
        self._image = Image.open(infile).convert('RGB')
        self._width, self._height = self._image.size
        self._bytes_per_pixel = 3
        self._current_row = 0

    def _scanchunk(self):
        if self._current_row >= self._height:
            return b''
        row_data = []
        for x in range(self._width):
            pixel = self._image.getpixel((x, self._current_row))
            row_data.extend(pixel)
        self._current_row += 1
        return bytes(row_data)


@pytest.fixture
def temp_tilestore(tmp_path):
    """
    Fixture: Isolated Temporary Tile Store

    Provides a temporary directory for tile storage that is automatically
    cleaned up after each test, ensuring test isolation.
    Also initializes the TileManager which is required for TiledMediaObject.
    """
    from pyzui.tilesystem.tilestore import tilestore as ts_module

    original_tile_dir = ts_module.tile_dir
    temp_dir = str(tmp_path / "tilestore")
    os.makedirs(temp_dir, exist_ok=True)

    ts_module.tile_dir = temp_dir
    tilestore.tile_dir = temp_dir

    # Initialize TileManager (required for TiledMediaObject to work)
    tilemanager.init()

    yield temp_dir

    ts_module.tile_dir = original_tile_dir
    tilestore.tile_dir = original_tile_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def test_images(tmp_path):
    """
    Fixture: Test Images with Different Dimensions

    Creates test images to verify save/load works correctly for images
    of various sizes, particularly those different from the default_size
    (256x256) which exposed the autofit bug.
    """
    images = {}

    # 256x256: Same as default_size (autofit has no visible effect)
    img_256 = Image.new('RGB', (256, 256), color='red')
    path_256 = tmp_path / "test_256x256.png"
    img_256.save(path_256)
    images['256x256'] = str(path_256)

    # 570x570: Different from default_size (exposes autofit bug)
    img_570 = Image.new('RGB', (570, 570), color='blue')
    path_570 = tmp_path / "test_570x570.png"
    img_570.save(path_570)
    images['570x570'] = str(path_570)

    # 1024x768: Non-square, different from default_size
    img_1024 = Image.new('RGB', (1024, 768), color='green')
    path_1024 = tmp_path / "test_1024x768.png"
    img_1024.save(path_1024)
    images['1024x768'] = str(path_1024)

    yield images


class TestSceneSaveLoadRoundTrip:
    """
    Feature: Scene Save/Load Round-Trip Preservation

    When a scene is saved and loaded, all TiledMediaObject properties
    (position, zoomlevel) must be preserved exactly. This is critical
    because the autofit behavior could override these values if not
    properly disabled during load.
    """

    def test_save_load_preserves_zoomlevel_for_non_default_size_image(
        self, temp_tilestore, test_images, tmp_path
    ):
        """
        Scenario: Save/load preserves zoomlevel for images different from default_size

        Given a TiledMediaObject with a 570x570 image (not 256x256 default)
        And the object has a specific zoomlevel set
        When the scene is saved and loaded
        Then the zoomlevel must be exactly preserved

        This test specifically catches the autofit bug where loading would
        recalculate zoomlevel based on fitting the actual image dimensions
        into the default_size placeholder bounds.
        """
        image_path = test_images['570x570']

        # Pre-tile the image so TiledMediaObject doesn't need to convert
        tiler = ConcreteTiler(image_path, media_id=image_path, tilesize=256)
        tiler.run()
        assert tiler.error is None

        # Create scene and add TiledMediaObject with specific properties
        scene = Scene()
        scene.viewport_size = (1280, 720)

        media_obj = TiledMediaObject(image_path, scene, autofit=False)

        # Set specific zoomlevel and position
        original_zoomlevel = 1.5
        original_pos = (100.0, 200.0)

        media_obj.zoomlevel = original_zoomlevel
        media_obj.pos = original_pos
        scene.add(media_obj)

        # Save the scene
        save_path = tmp_path / "test_scene.pzs"
        scene.save(str(save_path))

        # Load the scene
        loaded_scene = load_scene(str(save_path))
        loaded_scene.viewport_size = (1280, 720)

        # Render the scene to trigger autofit behavior (if autofit=True bug exists)
        # The autofit logic runs during render when image dimensions are loaded
        from unittest.mock import Mock
        mock_painter = Mock()
        loaded_scene.render(mock_painter, draft=True)

        # Verify the loaded object has preserved properties
        loaded_objects = loaded_scene._Scene__objects
        assert len(loaded_objects) == 1, "Should have exactly one object"

        loaded_obj = loaded_objects[0]

        assert loaded_obj.zoomlevel == pytest.approx(original_zoomlevel, rel=1e-5), \
            f"Zoomlevel not preserved: expected {original_zoomlevel}, got {loaded_obj.zoomlevel}"

        assert loaded_obj.pos[0] == pytest.approx(original_pos[0], rel=1e-5), \
            f"Position X not preserved: expected {original_pos[0]}, got {loaded_obj.pos[0]}"

        assert loaded_obj.pos[1] == pytest.approx(original_pos[1], rel=1e-5), \
            f"Position Y not preserved: expected {original_pos[1]}, got {loaded_obj.pos[1]}"

    def test_save_load_preserves_zoomlevel_for_default_size_image(
        self, temp_tilestore, test_images, tmp_path
    ):
        """
        Scenario: Save/load preserves zoomlevel for 256x256 images

        Given a TiledMediaObject with a 256x256 image (same as default_size)
        When the scene is saved and loaded
        Then the zoomlevel must be exactly preserved

        Note: This case would pass even with the autofit bug because
        fitting 256x256 into 256x256 placeholder produces the same zoomlevel.
        """
        image_path = test_images['256x256']

        tiler = ConcreteTiler(image_path, media_id=image_path, tilesize=256)
        tiler.run()
        assert tiler.error is None

        scene = Scene()
        scene.viewport_size = (1280, 720)

        media_obj = TiledMediaObject(image_path, scene, autofit=False)

        original_zoomlevel = 2.0
        original_pos = (50.0, 75.0)

        media_obj.zoomlevel = original_zoomlevel
        media_obj.pos = original_pos
        scene.add(media_obj)

        save_path = tmp_path / "test_scene_256.pzs"
        scene.save(str(save_path))

        loaded_scene = load_scene(str(save_path))
        loaded_scene.viewport_size = (1280, 720)

        # Render to trigger autofit behavior
        from unittest.mock import Mock
        loaded_scene.render(Mock(), draft=True)

        loaded_obj = loaded_scene._Scene__objects[0]

        assert loaded_obj.zoomlevel == pytest.approx(original_zoomlevel, rel=1e-5)
        assert loaded_obj.pos[0] == pytest.approx(original_pos[0], rel=1e-5)
        assert loaded_obj.pos[1] == pytest.approx(original_pos[1], rel=1e-5)

    def test_save_load_multiple_objects_preserves_all_properties(
        self, temp_tilestore, test_images, tmp_path
    ):
        """
        Scenario: Save/load preserves properties for multiple objects

        Given a scene with multiple TiledMediaObjects of different sizes
        When the scene is saved and loaded
        Then all objects preserve their individual zoomlevels and positions
        """
        # Pre-tile all images
        for key, path in test_images.items():
            tiler = ConcreteTiler(path, media_id=path, tilesize=256)
            tiler.run()

        scene = Scene()
        scene.viewport_size = (1280, 720)

        # Add multiple objects with different properties
        test_data = [
            (test_images['256x256'], 1.0, (10.0, 20.0)),
            (test_images['570x570'], 1.5, (100.0, 200.0)),
            (test_images['1024x768'], 0.5, (300.0, 400.0)),
        ]

        for image_path, zoomlevel, pos in test_data:
            media_obj = TiledMediaObject(image_path, scene, autofit=False)
            media_obj.zoomlevel = zoomlevel
            media_obj.pos = pos
            scene.add(media_obj)

        save_path = tmp_path / "test_multi_scene.pzs"
        scene.save(str(save_path))

        loaded_scene = load_scene(str(save_path))
        loaded_scene.viewport_size = (1280, 720)

        # Render to trigger autofit behavior
        from unittest.mock import Mock
        loaded_scene.render(Mock(), draft=True)

        loaded_objects = loaded_scene._Scene__objects

        assert len(loaded_objects) == 3, "Should have three objects"

        # Create lookup by media_id for verification
        loaded_by_id = {obj.media_id: obj for obj in loaded_objects}

        for image_path, expected_zoom, expected_pos in test_data:
            loaded_obj = loaded_by_id[image_path]

            assert loaded_obj.zoomlevel == pytest.approx(expected_zoom, rel=1e-5), \
                f"Zoomlevel not preserved for {image_path}"

            assert loaded_obj.pos[0] == pytest.approx(expected_pos[0], rel=1e-5), \
                f"Position X not preserved for {image_path}"

            assert loaded_obj.pos[1] == pytest.approx(expected_pos[1], rel=1e-5), \
                f"Position Y not preserved for {image_path}"

    def test_save_load_preserves_scene_properties(
        self, temp_tilestore, test_images, tmp_path
    ):
        """
        Scenario: Save/load preserves scene-level properties

        Given a scene with specific zoomlevel and origin
        When the scene is saved and loaded
        Then the scene zoomlevel and origin are preserved
        """
        image_path = test_images['256x256']

        tiler = ConcreteTiler(image_path, media_id=image_path, tilesize=256)
        tiler.run()

        scene = Scene()
        scene.viewport_size = (1280, 720)
        scene.zoomlevel = 2.5
        scene.origin = (150.0, 250.0)

        media_obj = TiledMediaObject(image_path, scene, autofit=False)
        scene.add(media_obj)

        save_path = tmp_path / "test_scene_props.pzs"
        scene.save(str(save_path))

        loaded_scene = load_scene(str(save_path))

        # Scene properties should match (accounting for viewport transformation)
        assert loaded_scene.zoomlevel == pytest.approx(scene.zoomlevel, rel=1e-5)

    def test_negative_zoomlevel_preserved(
        self, temp_tilestore, test_images, tmp_path
    ):
        """
        Scenario: Negative zoomlevels are preserved correctly

        Given a TiledMediaObject with a negative zoomlevel (zoomed out)
        When the scene is saved and loaded
        Then the negative zoomlevel must be exactly preserved
        """
        image_path = test_images['570x570']

        tiler = ConcreteTiler(image_path, media_id=image_path, tilesize=256)
        tiler.run()

        scene = Scene()
        scene.viewport_size = (1280, 720)

        media_obj = TiledMediaObject(image_path, scene, autofit=False)

        original_zoomlevel = -2.0  # Zoomed out
        media_obj.zoomlevel = original_zoomlevel
        media_obj.pos = (0.0, 0.0)
        scene.add(media_obj)

        save_path = tmp_path / "test_negative_zoom.pzs"
        scene.save(str(save_path))

        loaded_scene = load_scene(str(save_path))
        loaded_scene.viewport_size = (1280, 720)

        # Render to trigger autofit behavior
        from unittest.mock import Mock
        loaded_scene.render(Mock(), draft=True)

        loaded_obj = loaded_scene._Scene__objects[0]

        assert loaded_obj.zoomlevel == pytest.approx(original_zoomlevel, rel=1e-5), \
            f"Negative zoomlevel not preserved: expected {original_zoomlevel}, got {loaded_obj.zoomlevel}"
