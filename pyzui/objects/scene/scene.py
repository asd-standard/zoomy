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

"""A collection of media objects."""

import logging
import math
import urllib.error
import urllib.parse
import urllib.request
from threading import RLock

## Performance optimization note:
## Phase 2 optimizations replace 2**x with math.exp2(x) (1.85x faster)
## and math.log(x, 2) with math.log2(x) (2x faster) throughout the codebase.
## These changes are performance-critical for zoom operations.
from typing import TYPE_CHECKING, Any, Optional, Union, cast

if TYPE_CHECKING:
    from pyzui.objects.mediaobjects.stringmediaobject import StringMediaObject

from PySide6 import QtCore
from PySide6.QtGui import QColor, QPainter

from pyzui.logger import get_logger
from pyzui.objects.mediaobjects import mediaobject as MediaObject
from pyzui.objects.mediaobjects.svgmediaobject import SVGMediaObject
from pyzui.objects.mediaobjects.tiledmediaobject import TiledMediaObject
from pyzui.objects.physicalobject import PhysicalObject
from pyzui.objects.scene.sceneutils.autosave import SceneAutosaveManager
from pyzui.objects.scene.sceneutils.clipboard import SceneClipboardManager
from pyzui.objects.scene.sceneutils.parallel import SceneParallelRenderer
from pyzui.tilesystem import tilemanager as TileManager
from pyzui.windows.dialogwindows.dialogwindows import DialogWindows


class Scene(PhysicalObject):
    """
    Constructor :
        Scene()
    Parameters :
        None

    Scene() --> None

    `Scene` objects are used to hold a collection of `MediaObjects`.
    This class manages all the objects that can be rendered in the interface,
    Their positioning (_x, _y) on the scene and their zoom (_z) and the acces
    to them.

    Scene objects can also be saved to files, and loaded from files.
    """

    #: an arbitrary size that is common to all scenes upon creation `scene size`
    standard_viewport_size: tuple[int, int] = (1280, 720)

    #: Flag to indicate that a repaint is needed
    _needs_repaint: bool = False

    def __init__(self, config: dict[str, Any] | None = None):
        """
        New scene is made by initiating a :class:`~pyzui.objects.physicalobject.PhysicalObject`,
        creating an objects list *__objects* and thread safe selection for *__objects* given by
        declaring RLock list *__objects_lock*, seting up *__viewport_size*, setting up mouse
        selection variables *selection* and *right_selection* and logger setup *__logger*.

        For better explaining of this scheme look at :  :class:`pyzui.objects.mediaobjects.mediaobject`

        World::

             --------------------------------------->
            |   Scene
            |  @ ------------------------------+--->
            |  |  ViewPort        MediaObj     |
            |  |  (Screen View)   *-------+--> |
            |  |                  |   &   |    |
            |  |               %  +-------"    |
            |  |                  |            |
            |  |                  ∨            |
            |  |                               |
            |  +-------------------------------#
            |  |
            |  ∨
            ∨

        Legend::

            (All MediaObject attributes are relative to screen view)
            * -> MediaObject.topleft()
            " -> MediaObject.bottomright()
            & -> MediaObject.center()
            # -> Scene.viewport_size()
            % -> Scene.center()
            @ -> Scene.origin()

        We have a center relative to the scene, 'center' and a center relative
        to the absolute frame of reference _center

        @ origin position of the scene it's relative to an absolute frame of
        reference, with 0,0 as it's origin.

        % Scene center it's given by::

            scene.centre[0] = scene.origin + (Scene.viewport_size[0]/2)*2**(zoomlevel)
            scene.centre[1] = scene.origin + (Scene.viewport_size[1]/2)*2**(zoomlevel)

        """

        # Apply default zoom from config if provided
        initial_zoom = None
        if config and "zoom" in config:
            zoom_config = config["zoom"]
            if "default_zoomlevel" in zoom_config:
                initial_zoom = zoom_config["default_zoomlevel"]

        # Store configuration for object creation
        self.__config = config or {}

        # Render order mode: 'smaller_on_top' or 'larger_on_top'
        self.__render_order: str
        if config and "render" in config:
            self.__render_order = config["render"].get("order", "smaller_on_top")
        else:
            self.__render_order = "smaller_on_top"

        # initialize mediobject centre, position and velocity
        PhysicalObject.__init__(self, initial_zoom=initial_zoom)

        self.__objects: list[MediaObject.MediaObject] = []
        self.__objects_lock: RLock = RLock()
        self.__viewport_size: tuple[int, int] = self.standard_viewport_size

        # Left click can initiate area selection while right click just one select
        self.selection: list[MediaObject.MediaObject] | None = None
        self.right_selection: MediaObject.MediaObject | None = None

        self.__logger: logging.Logger = get_logger("Scene")

        # Parallel rendering components
        self.__parallel_renderer: SceneParallelRenderer = SceneParallelRenderer(self, config)

        # Autosave components
        self.__autosave_manager: SceneAutosaveManager = SceneAutosaveManager(self, config)

        # Clipboard components
        self.__clipboard_manager: SceneClipboardManager = SceneClipboardManager(self)

        self.__last_save_path: str | None = None
        self.__first_save_done: bool = False

    def __del__(self):
        """Ensure autosave timer and parallel renderer threads are stopped.

        This prevents Qt threading errors when Python garbage collects
        Scene instances while their background threads are still running.
        """
        try:
            if hasattr(self, "_Scene__autosave_manager"):
                self._Scene__autosave_manager.disable_autosave()
        except Exception:
            pass  # Object is being destroyed anyway

        try:
            if hasattr(self, "_Scene__parallel_renderer"):
                self._Scene__parallel_renderer.shutdown()
        except Exception:
            pass  # Object is being destroyed anyway

    def shutdown_threads(self) -> None:
        """Shutdown all background threads managed by the scene.

        Stops the parallel renderer thread executor.
        Called during application shutdown before Qt cleanup.
        """
        if hasattr(self, "_Scene__parallel_renderer"):
            self._Scene__parallel_renderer.shutdown()

    def save(self, filename: str) -> None:
        """
        Method :
            Scene.save(filename)
        Parameters :
            filename : str

        Scene.save(filename) --> None

        Save the scene to the location given by `filename`.

        It is recommended (but not compulsory) that the file extension of
        filename be '.pzs'.

        open a file `filename`, writes on the first line zoom level (z) and
        position (x, y) of the scene origin defined by Scene.__set_origin()
        then thread safely, once sorted `__objects`, cicles through them,
        writing for each of them a line on `fielname` with::

            object type: `type(mediaobject).__name__`

            media id: mediaobject.media_id (replacing '%3A' with :)

            zoomlevel: mediaobject.zoomlevel

            x position: mediaobject.pos[0]

            y position: mediaobject.pos[1]
        """

        """viewport_size it's saved in a temporary variable `actual_viewport_size`
        so that saving of the scene can be done in a standard size.
        By doing this once the scene it's loaded it can be then scaled to fit
        whatever viewport the user currently has, independent of the viewport
        the scene was having when it was saved."""

        actual_viewport_size = self.viewport_size
        # setting `viewport_size` to standard size
        self.viewport_size = self.standard_viewport_size

        f = open(filename, "w")

        f.write("%s\t%s\t%s\n" % (self.zoomlevel, self.origin[0], self.origin[1]))

        with self.__objects_lock:
            self.__sort_objects()
            for mediaobject in self.__objects:
                self._write_mediaobject_line(f, mediaobject)

        f.close()

        # setting `viewport_size` to it's actual size
        self.viewport_size = actual_viewport_size

        # Store last save path and trigger autosave
        self.__last_save_path = filename

        # Mark first save done
        if not self.__first_save_done:
            self.__first_save_done = True

        # Create backup via autosave manager
        self.__autosave_manager.update_last_save_path(filename)

    def _get_processed_media_id(self, mediaobject: "MediaObject.MediaObject") -> str:
        """
        Process media_id for saving, handling SVG embedding if needed.

        Args:
            mediaobject: MediaObject to process

        Returns:
            str: Processed media_id string ready for writing to file
        """
        # Handle SVG embedding for modified SVGs
        if isinstance(mediaobject, SVGMediaObject) and mediaobject.is_modified:
            # Modified SVG: try to embed content
            svg_content = mediaobject.get_svg_content()
            if svg_content:
                # Check size limit for warning
                content_size = len(svg_content.encode("utf-8"))
                if content_size > SVGMediaObject.MAX_EMBEDDED_SVG_SIZE_BYTES:
                    self.__logger.warning(
                        f"Embedding large SVG ({content_size / 1024 / 1024:.1f}MB) in pzs file: {mediaobject.media_id}"
                    )

                # URL encode and prefix with 'embedded:'
                encoded = urllib.parse.quote(svg_content)
                media_id = f"embedded:{encoded}"
            else:
                # Error: cannot retrieve SVG content
                self.__logger.error(f"Cannot retrieve SVG content for embedding: {mediaobject.media_id}")
                # Try to save original file path if available
                if hasattr(mediaobject, "original_file_path") and mediaobject.original_file_path:
                    media_id = mediaobject.original_file_path
                else:
                    # Fallback to current media_id
                    media_id = mediaobject.media_id
        else:
            # Non-modified SVG or other object
            media_id = mediaobject.media_id

        # For embedded SVG, we already have URL-encoded content
        # For other media IDs (file paths), we need to URL-encode
        if isinstance(mediaobject, SVGMediaObject) and mediaobject.is_modified and media_id.startswith("embedded:"):
            # Embedded SVG content is already URL-encoded
            encoded_media_id = media_id.replace("%3A", ":")
        else:
            # Regular file path or cache hash - URL encode it
            encoded_media_id = urllib.parse.quote(media_id).replace("%3A", ":")

        return encoded_media_id

    def _write_mediaobject_line(
        self, f, mediaobject: "MediaObject.MediaObject", offset: tuple[float, float] | None = None
    ) -> None:
        """
        Write a mediaobject line to file.

        Args:
            f: File object
            mediaobject: MediaObject to write
            offset: Optional offset to apply to position (for save_selection)
        """
        # Get processed media_id
        encoded_media_id = self._get_processed_media_id(mediaobject)

        # Calculate position (with offset if provided)
        if offset is not None:
            pos_x = mediaobject.pos[0] + offset[0]
            pos_y = mediaobject.pos[1] + offset[1]
        else:
            pos_x = mediaobject.pos[0]
            pos_y = mediaobject.pos[1]

        # Write line: type\tmedia_id\tzoomlevel\tx\ty
        f.write(
            "%s\t%s\t%s\t%s\t%s\n" % (type(mediaobject).__name__, encoded_media_id, mediaobject.zoomlevel, pos_x, pos_y)
        )

    def save_selection(self, filename: str) -> None:
        """
        Method :
            Scene.save_selection(filename)
        Parameters :
            filename : str

        Scene.save_selection(filename) --> None

        Save selected mediaobjects to file.

        Saves only the currently selected mediaobjects to the specified file,
        preserving their relative positions. The first line of the file is
        "0\t0\t0" to indicate no scene origin/zoom information.

        The saved positions are offsets from the centroid of the selected
        objects, allowing import_scene to place them at the viewport centre
        while maintaining their relative arrangement.
        """
        # Check if there's a selection
        if not self.selection:
            self.__logger.warning("No selection to save")
            return

        # Get selected objects (handle both single object and list)
        if isinstance(self.selection, list):
            selected_objects = self.selection
            if len(selected_objects) == 0:
                self.__logger.warning("Empty selection list")
                return
        else:
            selected_objects = [self.selection]

        # Calculate centroid of selected objects
        positions = [obj.pos for obj in selected_objects]
        centroid_x = sum(p[0] for p in positions) / len(positions)
        centroid_y = sum(p[1] for p in positions) / len(positions)

        # Open file for writing
        f = open(filename, "w")

        # Write header: 0 0 0 (no scene origin/zoom information)
        f.write("0\t0\t0\n")

        # Write each selected mediaobject with offset from centroid
        for mediaobject in selected_objects:
            # Calculate offset from centroid (negative because we want position relative to centroid)
            offset_x = -centroid_x
            offset_y = -centroid_y
            self._write_mediaobject_line(f, mediaobject, offset=(offset_x, offset_y))

        f.close()

        self.__logger.info(f"Saved {len(selected_objects)} selected mediaobjects to {filename}")

    def add(self, mediaobject: "MediaObject.MediaObject") -> None:
        """
        Method :
            Scene.add(mediaobject)
        Parameters :
            mediaobject : MediaObject

        Scene.add(mediaobject) --> None

        Add mediaobject from the list of elements that get to
        be rendered on the scene.

        Inside a thread safe selection: add `mediaobject` to this scene by
        checking if given mediaobject is already in `__objects` list, if
        it is nothing is done, otherwise mediaobject it's appended to the
        `__objects` list.
        """

        with self.__objects_lock:
            if mediaobject not in self.__objects:
                self.__objects.append(mediaobject)

    def remove(self, mediaobject: Union["MediaObject.MediaObject", list["MediaObject.MediaObject"]]) -> None:
        """
        Method :
            Scene.remove(mediaobject)
        Parameters :
            mediaobject : MediaObject or List[MediaObject]

        Scene.remove(mediaobject) --> None

        Remove mediaobject(s) from the list of elements that get to
        be rendered on the scene and purge all'related tiles through
        TileManager.purge('media_id') method.

        Can accept either a single MediaObject or a list of MediaObjects.
        When passed a list, all objects in the list are removed.

        Thread safely cycle through *__objects* until *mediaobject*
        match with the respective element of the *__objects* list
        and removes it from the *__objects* list. Then gets
        mediaobject.media_id attribute and check if other *__objects*
        elements have the same media_id, if it's not the case the media_id
        gets purged from the TileManager.

        See: :meth:`pyzui.tilesystem.tilemanager.purge`

        """

        # Convert single object to list for uniform handling
        objects = mediaobject if isinstance(mediaobject, list) else [mediaobject]

        with self.__objects_lock:
            # Track media IDs that need cleanup
            media_ids_to_check: dict[str, bool] = {}

            for obj in objects:
                if obj in self.__objects:
                    self.__objects.remove(obj)

                    # Record media_id for cleanup check
                    media_id = obj.media_id
                    if media_id not in media_ids_to_check:
                        media_ids_to_check[media_id] = False

            # Check each media_id to see if it's still active
            for media_id in media_ids_to_check:
                media_active = False
                for other in self.__objects:
                    if other.media_id == media_id:
                        ## another object exists for
                        ## this media, meaning that
                        ## this media is active
                        media_active = True
                        break

                if not media_active:
                    TileManager.purge(media_id)

    def _create_mediaobject_from_line(self, line: str) -> Optional["MediaObject.MediaObject"]:
        """
        Helper method to create a mediaobject from a PZS file line.

        Args:
            line: A line from a PZS file containing mediaobject data

        Returns:
            MediaObject if successfully created, None if line should be ignored
        """
        class_name, media_id, zoomlevel_str, x_str, y_str = line.split()
        media_id = urllib.parse.unquote(media_id)

        # mediaobjects are sorted by their mediaobject type and
        # initialized by their appropriate classes
        if class_name == "TiledMediaObject" or class_name == "StringMediaObject" or class_name == "SVGMediaObject":
            from pyzui.objects.mediaobjects.stringmediaobject import StringMediaObject

            mediaobject: TiledMediaObject | StringMediaObject | SVGMediaObject
            if class_name == "TiledMediaObject":
                # autofit=False is critical: when loading from a file, we must
                # preserve the saved zoomlevel. If autofit=True, the zoomlevel
                # would be recalculated when actual image dimensions load,
                # overwriting the saved value and causing size discrepancies.
                mediaobject = TiledMediaObject(media_id, self, autofit=False)
            elif class_name == "StringMediaObject":
                mediaobject = StringMediaObject(media_id, self)
            elif class_name == "SVGMediaObject":
                if media_id.startswith("embedded:"):
                    # Embedded SVG content
                    try:
                        svg_content = urllib.parse.unquote(media_id[9:])  # Skip 'embedded:' prefix

                        # Validate SVG content
                        if not svg_content or not svg_content.strip():
                            raise ValueError("Empty SVG content in embedded SVG")
                        if not svg_content.startswith("<"):
                            raise ValueError(f"Invalid SVG content (doesn't start with '<'): {svg_content[:50]}...")

                        # Store in cache
                        from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import get_svg_cache

                        svg_cache = get_svg_cache()
                        cache_hash = svg_cache.store_svg(svg_content)

                        # Create SVGMediaObject with cache hash
                        mediaobject = SVGMediaObject(cache_hash, self)
                        # Set content in cache for performance
                        mediaobject.set_svg_content(svg_content)
                    except Exception as e:
                        # Log error and fall back to treating as regular media_id
                        import logging

                        logging.getLogger("Scene").error(f"Failed to load embedded SVG: {e}")
                        mediaobject = SVGMediaObject(media_id, self)
                else:
                    # Regular file path or cache hash
                    mediaobject = SVGMediaObject(media_id, self)

            # Set zoomlevel and position from file
            mediaobject.zoomlevel = float(zoomlevel_str)
            mediaobject.pos = (float(x_str), float(y_str))

            return mediaobject
        else:
            # ignore instances of any other class
            return None

    def _fit_imported_objects(self, mediaobjects: list) -> None:
        """Scale imported mediaobjects to fit within the current viewport.

        Calculates the combined on-screen bounding box of all imported
        objects and uniformly scales both their positions (relative to
        the group centroid) and zoomlevels so the bounding box fits within
        the middle 50% of the viewport.

        Both position offsets and zoomlevels are scaled by the same factor,
        preserving the visual proportions (spacing and sizing) of the
        imported objects relative to each other.

        This matches the behaviour of __open_media when adding single
        media files.

        Args:
            mediaobjects: List of mediaobjects with already-transformed
                positions. Both positions and zoomlevels will be adjusted.
        """
        if not mediaobjects:
            return

        min_x: float = float("inf")
        min_y: float = float("inf")
        max_x: float = float("-inf")
        max_y: float = float("-inf")

        for obj in mediaobjects:
            tl: tuple[float, float] = obj.topleft
            br: tuple[float, float] = obj.bottomright
            if tl[0] < min_x:
                min_x = tl[0]
            if tl[1] < min_y:
                min_y = tl[1]
            if br[0] > max_x:
                max_x = br[0]
            if br[1] > max_y:
                max_y = br[1]

        bbox_w: float = max_x - min_x
        bbox_h: float = max_y - min_y

        vp_w: int
        vp_h: int
        vp_w, vp_h = self.viewport_size
        if bbox_w <= 0 or bbox_h <= 0 or vp_w <= 0 or vp_h <= 0:
            return

        # Target: middle 50% of viewport (matching __open_media behaviour)
        target_w: float = vp_w / 2
        target_h: float = vp_h / 2

        scale: float = min(target_w / bbox_w, target_h / bbox_h)
        zoom_adjust: float = math.log2(scale)

        # Scale both positions (relative to group centroid) and zoomlevels
        # by the same factor to preserve visual proportions between objects
        centroid_x: float = sum(obj.pos[0] for obj in mediaobjects) / len(mediaobjects)
        centroid_y: float = sum(obj.pos[1] for obj in mediaobjects) / len(mediaobjects)

        for obj in mediaobjects:
            obj.pos = (
                centroid_x + (obj.pos[0] - centroid_x) * scale,
                centroid_y + (obj.pos[1] - centroid_y) * scale,
            )
            obj.zoomlevel += zoom_adjust

    def import_scene(self, filename: str) -> None:
        """
        Method :
            Scene.import_scene(filename)
        Parameters :
            filename : str

        Scene.import_scene(filename) --> None

        Import mediaobjects from PZS file into current scene.

        Loads mediaobjects from filename and adds them to the current scene,
        transforming their positions so they appear at the current viewport centre
        while preserving their relative positions to each other.

        The saved scene's zoom level and origin are discarded. Only the relative
        positions between mediaobjects are preserved.
        """
        try:
            f = open(filename)

            # First line contains saved scene's zoomlevel and origin
            # Read and validate format (3 values separated by tabs) but discard the values
            first_line = f.readline()
            if not first_line:
                f.close()
                raise ValueError("Empty scene file")

            # Validate first line has 3 tab-separated values
            parts = first_line.strip().split("\t")
            if len(parts) != 3:
                f.close()
                raise ValueError(f"Invalid scene file header: expected 3 tab-separated values, got {len(parts)}")

            # Try to parse as floats to validate format
            try:
                float(parts[0])  # zoomlevel
                float(parts[1])  # origin_x
                float(parts[2])  # origin_y
            except ValueError:
                f.close()
                raise ValueError(f"Invalid numeric values in scene file header: {first_line.strip()}") from None

            # Get current viewport centre in scene coordinates
            # Calculate screen centre then convert to scene coordinates
            screen_centre_x = self.viewport_size[0] / 2
            screen_centre_y = self.viewport_size[1] / 2
            scale = math.exp2(-self.zoomlevel)
            viewport_centre_scene = (
                (screen_centre_x - self.origin[0]) * scale,
                (screen_centre_y - self.origin[1]) * scale,
            )

            # First pass: collect all mediaobjects and their positions
            mediaobjects = []
            positions = []

            for line in f:
                mediaobject = self._create_mediaobject_from_line(line)
                if mediaobject:
                    mediaobjects.append(mediaobject)
                    positions.append(mediaobject.pos)

            f.close()

            # If we have mediaobjects, calculate centroid and transform positions
            if mediaobjects and positions:
                # Calculate centroid (average position) of all mediaobjects
                centroid_x = sum(p[0] for p in positions) / len(positions)
                centroid_y = sum(p[1] for p in positions) / len(positions)

                # Second pass: transform positions
                for i, mediaobject in enumerate(mediaobjects):
                    offset_x = positions[i][0] - centroid_x
                    offset_y = positions[i][1] - centroid_y

                    pos_transformed = (viewport_centre_scene[0] + offset_x, viewport_centre_scene[1] + offset_y)
                    mediaobject.pos = pos_transformed

                # Scale imported objects to fit within the current viewport
                self._fit_imported_objects(mediaobjects)

                # Add all mediaobjects to the scene
                for mediaobject in mediaobjects:
                    self.add(mediaobject)

        except FileNotFoundError:
            self.__logger.error(f"Scene file not found: {filename}")
            raise
        except ValueError as e:
            self.__logger.error(f"Invalid scene file format in {filename}: {e}")
            raise
        except Exception as e:
            self.__logger.error(f"Error importing scene from {filename}: {e}")
            raise

    # Clipboard functionality has been moved to SceneClipboardManager
    # Methods are available via self.__clipboard_manager

    def copy_selection(self) -> None:
        """Copy selected SVG objects to internal clipboard.

        Only SVGMediaObjects are supported for copy/paste.
        Deselects copied objects after copying.
        """
        self.__clipboard_manager.copy_selection()

    def paste(self, offset_position: tuple[float, float] | None = None) -> list["SVGMediaObject"]:
        """Paste SVG objects from clipboard with fixed offset.

        Only SVGMediaObjects are supported for copy/paste.
        Selects pasted objects after pasting.
        Logs warning for unsupported object types.

        Args:
            offset_position: Optional offset position for pasted objects

        Returns:
            List of pasted MediaObject instances
        """
        return self.__clipboard_manager.paste(offset_position)

    def get(
        self, topleft: tuple[float, float], bottomright: tuple[float, float] | None = None
    ) -> Optional["MediaObject.MediaObject"] | list["MediaObject.MediaObject"]:
        """
        Method :
            Scene.get(topleft, bottomright=None)
        Parameters :
            topleft : Tuple[float, float]
            bottomright : Optional[Tuple[float, float]] = None

        Scene.get(topleft) --> MediaObject or None
        Scene.get(topleft, bottomright) --> List[MediaObject]

        If only `topleft` is provided, return the foremost visible *MediaObject*
        which overlaps the on-screen point *topleft*.

        If both `topleft` and `bottomright` are provided, return a list of all
        *MediaObjects* that intersect the rectangle defined by these two points,
        sorted by current render order (foremost to rearmost).

        Return None or empty list if there are no *MediaObjects* overlapping
        the point or rectangle.

        Mouse click event is caught by: :meth:`pyzui.qzui.QZUI.mousePressEvent`
        which returns mouse position *pos*

        Thread safely cycle through *__objects*. For each mediaobject checks if
        *pos* is within mediaobject area. Objects are sorted by current render
        order, so the first match is the topmost on screen.
        """

        with self.__objects_lock:
            self.__sort_objects()

            if bottomright is None:
                # Point selection - return single object
                for mediaobject in self.__objects:
                    # Skip objects that wouldn't be visible in HighQuality mode
                    if not mediaobject.is_size_visible(MediaObject.RenderMode.HighQuality):
                        continue

                    left, top = mediaobject.topleft
                    right, bottom = mediaobject.bottomright
                    if topleft[0] >= left and topleft[1] >= top and topleft[0] <= right and topleft[1] <= bottom:
                        return mediaobject
                return None
            else:
                # Rectangle selection - return list of intersecting objects
                result: list[MediaObject.MediaObject] = []

                # Normalize rectangle coordinates
                rect_left = min(topleft[0], bottomright[0])
                rect_top = min(topleft[1], bottomright[1])
                rect_right = max(topleft[0], bottomright[0])
                rect_bottom = max(topleft[1], bottomright[1])

                for mediaobject in self.__objects:
                    # Skip size-invisible objects
                    if not mediaobject.is_size_visible(MediaObject.RenderMode.HighQuality):
                        continue

                    obj_left, obj_top = mediaobject.topleft
                    obj_right, obj_bottom = mediaobject.bottomright

                    # Check for rectangle intersection
                    if not (
                        obj_right < rect_left or obj_left > rect_right or obj_bottom < rect_top or obj_top > rect_bottom
                    ):
                        result.append(mediaobject)

                return result

    def zoom(self, amount: float) -> None:
        """Zoom by the given `amount` with the centre maintaining its position
        on the screen.

        Parameters :
            amount : float

        zoom(float) -> None
        """

        ## P is the onscreen objec position of the centre
        ## C is the coordinates of the centre
        ## zoomlevel' = zoomlevel + amount
        ## P  = pos  + C * math.exp2(zoomlevel)
        ##    => C = (P - pos) * math.exp2(-zoomlevel)
        ## P' = pos' + C * math.exp2(zoomlevel')
        ##    = pos' + (P - pos) * math.exp2(zoomlevel'-zoomlevel)
        ## solving for P = P' yields:
        ##   pos' = P - (P - pos) * math.exp2(amount)

        Px, Py = self.centre

        # Calculate new zoomlevel and validate it
        new_zoomlevel = self._z + amount
        if self._zoom_manager:
            new_zoomlevel = self._zoom_manager.validate(new_zoomlevel)
            # Recalculate amount after clamping
            amount = new_zoomlevel - self._z

        self._x = Px - (Px - self._x) * math.exp2(amount)
        self._y = Py - (Py - self._y) * math.exp2(amount)
        self._z = new_zoomlevel

    @property
    def render_order(self) -> str:
        """
        Property :
            Scene.render_order
        Parameters :
            None

        Scene.render_order --> str

        Returns the current render order mode.
        'smaller_on_top' means smaller objects are rendered above larger ones.
        'larger_on_top' means larger objects are rendered above smaller ones.

        See : :meth:`pyzui.objects.scene.scene.Scene.set_render_order`
        """
        return self.__render_order

    def set_render_order(self, mode: str) -> None:
        """
        Method :
            Scene.set_render_order(mode)
        Parameters :
            mode : str

        Scene.set_render_order(mode) --> None

        Set the render order mode. Valid values are 'smaller_on_top' and
        'larger_on_top'. The next render pass will use the new order.

        See : :meth:`pyzui.objects.scene.scene.Scene.__sort_objects`
        """
        if mode not in ("smaller_on_top", "larger_on_top"):
            raise ValueError(f"Invalid render order mode: '{mode}'. Use 'smaller_on_top' or 'larger_on_top'.")
        self.__render_order = mode

    def __sort_objects(self) -> None:
        """
        Method :
            `internal method` self.__sort_objects()
        Parameters :
            None

        __sort_objects() --> None

        Sort self.__objects by onscreen_area. When render_order is
        'smaller_on_top', objects are sorted ascending so that reversed
        iteration paints smaller objects last (on top). When 'larger_on_top',
        objects are sorted descending so that reversed iteration paints
        larger objects last (on top).

        See :  :attr:`pyzui.objects.mediaobjects.mediaobject.MediaObject.onscreen_area`

        """
        with self.__objects_lock:
            self.__objects.sort(
                key=lambda mediaobject: mediaobject.onscreen_area, reverse=(self.__render_order == "larger_on_top")
            )

    def action_draw_rect(
        self, topleft: tuple[float, float], bottomright: tuple[float, float], painter: QPainter, color: QtCore.Qt
    ) -> None:
        """

        Draws a colored rectangle around selected mediaobject
        """
        # using mediaobject.topleft mediaobject.topright attributes
        x1, y1 = topleft[0], topleft[1]
        x2, y2 = bottomright[0], bottomright[1]

        ## clamp values
        x1 = max(0, min(int(x1), self.viewport_size[0] - 1))
        y1 = max(0, min(int(y1), self.viewport_size[1] - 1))
        x2 = max(0, min(int(x2), self.viewport_size[0] - 1))
        y2 = max(0, min(int(y2), self.viewport_size[1] - 1))
        # Draing border using QtGui.QPainter attributes
        painter.setPen(color)
        painter.drawRect(x1, y1, x2 - x1, y2 - y1)

    # Parallel rendering methods (delegated to SceneParallelRenderer)

    def _get_text_objects(self) -> list["StringMediaObject"]:
        """Get all StringMediaObjects in the scene.

        Returns:
            List of StringMediaObject instances
        """
        text_objects = []

        with self.__objects_lock:
            for obj in self.__objects:
                # Use string comparison instead of isinstance() to avoid circular imports
                # This is 2.8x faster and consistent with existing patterns in the codebase
                # (see line 1060 for similar pattern)
                if type(obj).__name__ == "StringMediaObject":
                    text_objects.append(obj)
        return text_objects  # type: ignore[return-value]

    def _precalculate_text_layouts(self) -> None:
        """Pre-calculate text layouts for parallel rendering.

        This method should be called before rendering when the scene is moving
        to prepare layout data for parallel rendering.
        """
        self.__parallel_renderer.precalculate_text_layouts()

    def render_parallel_text(self, painter: QPainter) -> bool:
        """Render text objects using parallel rendering.

        Args:
            painter: QPainter object to render with

        Returns:
            True if parallel rendering was used, False otherwise
        """
        return self.__parallel_renderer.render_text(painter)

    def enable_parallel_rendering(self, enabled: bool = True) -> None:
        """Enable or disable parallel rendering for the scene.

        Args:
            enabled: Whether to enable parallel rendering
        """
        self.__parallel_renderer.enable(enabled)

    def get_parallel_stats(self) -> dict[str, Any]:
        """Get parallel rendering statistics.

        Returns:
            Dictionary with parallel rendering statistics
        """
        return self.__parallel_renderer.get_stats()

    def invalidate_parallel_cache(self) -> None:
        """Invalidate parallel rendering cache."""
        self.__parallel_renderer.invalidate_cache()

    def render(self, painter: QPainter, draft: bool) -> list["MediaObject.MediaObject"]:
        """
        Method :
            Scene.render(painter, draft)
        Parameters :
            painter : QPainter
            draft : bool

        Scene.render(painter, draft) --> List[MediaObject]

        Render the scene using the given `painter`.

        If *draft* is True, draft mode is enabled. Otherwise High-Quality mode
        is enabled.

        If any errors occur rendering any of the *MediaObjects*, then they will
        be removed from the scene and a list of tuples representing the errors
        will be returned. Otherwise the empty list will be returned.

        render(QPainter, bool) -> list[tuple[MediaObject,MediaObject.LoadError]]

        See source code comments :

            :meth:`Scene.render`

        """
        media_id: str | bool
        # Error list to be filled with MediaObject.LoadError.
        errors = []

        """Sort __objects from least to most displayed area and thread safely
        cycle through them"""
        with self.__objects_lock:
            self.__sort_objects()
            # If hidden=True mediaobject is added to hidden_objects set
            hidden = False
            # Creates an empty set for hidden mediaobjects
            hidden_objects = set()
            """Cycles through __objects in sort order (smallest-first for
            'smaller_on_top', largest-first for 'larger_on_top'). Objects
            filling the screen cause those rendered behind them to be
            hidden."""
            for mediaobject in self.__objects:
                # this hidden check gets triggered in case an object is filling the entire screen,
                # marking objects rendered behind it as hidden
                if hidden:
                    hidden_objects.add(mediaobject)
                else:
                    # gets topleft and bottomright coordinates
                    x1, y1 = mediaobject.topleft
                    x2, y2 = mediaobject.bottomright

                    if x1 <= 0 and y1 <= 0 and x2 >= self.viewport_size[0] and y2 >= self.viewport_size[1]:
                        ## mediaobject fills the entire
                        ## screen, so mark larger objects
                        ## (which are rendered behind it)
                        ## as hidden
                        hidden = True

            """Set of hidden_objects is updated: now we cycle through __objects
            in reverse order setting mediaobject.RenderMode.
            We set Invisible if mediaobject is in hidden_objects, we set in Draft
            if draft class input parameter is passed as True, otherwise we set
            HighQuality. Rendering in reverse sort order ensures the objects
            meant to appear on top are painted last."""

            # Pre-calculate text layouts for parallel rendering if scene is moving
            if self.vzmoving and self.__parallel_renderer.is_enabled():
                self._precalculate_text_layouts()

            # Track which text objects have been rendered with parallel rendering
            parallel_rendered_text_objects = set()

            # Try parallel rendering for text objects if scene is moving
            if self.vzmoving and self.__parallel_renderer.is_enabled():
                parallel_success = self.render_parallel_text(painter)
                if parallel_success:
                    # Mark text objects that were rendered in parallel
                    text_objects = self._get_text_objects()
                    for obj in text_objects:
                        parallel_rendered_text_objects.add(id(obj))

            for mediaobject in reversed(self.__objects):
                if mediaobject in hidden_objects:
                    mode = MediaObject.RenderMode.Invisible
                elif draft:
                    mode = MediaObject.RenderMode.Draft
                else:
                    mode = MediaObject.RenderMode.HighQuality

                # Skip text objects that were already rendered in parallel
                # Use string comparison instead of isinstance() to avoid circular imports
                # This is consistent with _get_text_objects() and other type checks in the codebase
                if (
                    type(mediaobject).__name__ == "StringMediaObject"
                    and id(mediaobject) in parallel_rendered_text_objects
                ):
                    continue

                # Check size visibility before rendering
                if not mediaobject.is_size_visible(mode):
                    continue  # Skip rendering size-invisible objects

                """Now we try to render using mediaobject.render() method wich is
                inherited from the specific type of mediaobject, namely:
                tilemediaobject, stringmediaobject, scgmediaobject, each of these
                mediaobjects has it's specific render method"""
                try:
                    mediaobject.render(painter, mode)
                except MediaObject.LoadError:
                    """If mediaobject render fails MediaObject.LoadError type is
                    returned and appended to errors list"""
                    errors.append(mediaobject)

            for mediaobject in errors:
                ## remove mediaobjects that have raised errors
                print("## remove mediaobjects that have raised MediaObject.LoadError")
                print(mediaobject)
                # Remove mediaobject using the Scene.remove() method
                self.remove(mediaobject)

            """qzui.mousePressEvent handles mouse selection and adjourn `selection`
            and right_selection, assigning to them the mouse selected mediaobject.
            If selection or right_selection isn't None a colored border gets drawn
            around selected of right_selected mediaobject using QtGui.QPainter
            `painter`"""

            if isinstance(self.selection, list):
                for selection in self.selection:
                    self.action_draw_rect(selection.topleft, selection.bottomright, painter, QtCore.Qt.green)

            elif isinstance(self.selection, MediaObject.MediaObject):
                self.action_draw_rect(self.selection.topleft, self.selection.bottomright, painter, QtCore.Qt.green)

            if self.right_selection:
                self.action_draw_rect(
                    self.right_selection.topleft, self.right_selection.bottomright, painter, QtCore.Qt.blue
                )

            if type(self.right_selection).__name__ == "StringMediaObject":
                right_selection_obj = cast("MediaObject.MediaObject", self.right_selection)

                for i in range(len(self.__objects)):
                    if self.__objects[i]._media_id[14:] == right_selection_obj._media_id[14:]:
                        dialog = DialogWindows.modify_string_input_dialog(self.__objects[i]._media_id)
                        try:
                            ok, media_id, string_color, edited_text = dialog._run_dialog()

                        except Exception:
                            ok = False
                            media_id = ""
                            string_color = ""
                            edited_text = ""

                        if ok and media_id:
                            # Get lines from input string
                            lines: list[str] = edited_text.split("\n")
                            # Update object props
                            self.__objects[i].lines = lines  # type: ignore[attr-defined]
                            self.__objects[i]._media_id = media_id
                            self.__objects[i]._StringMediaObject__str = edited_text  # type: ignore[attr-defined]
                            self.__objects[i]._StringMediaObject__color = QColor("#" + string_color)  # type: ignore[attr-defined]

                            # Invalidate text image cache after text modification
                            if hasattr(self.__objects[i], "invalidate_cache"):
                                self.__objects[i].invalidate_cache()  # type: ignore[attr-defined]
                            # print(self.__objects[i].__dict__)
                        self.right_selection = None
                        break

            if type(self.right_selection).__name__ == "TiledMediaObject":
                right_selection_obj = cast("MediaObject.MediaObject", self.right_selection)

                for i in range(len(self.__objects)):
                    if self.__objects[i]._media_id == right_selection_obj._media_id:
                        dialog = DialogWindows.modify_tiled_media_object_dialog(self.__objects[i])  # type: ignore[assignment,arg-type]
                        try:
                            ok, media_id = dialog._run_dialog()  # type: ignore[misc]

                        except Exception as e:
                            print(f"Error opening TiledMediaObject dialog: {e}")
                            ok = False
                            media_id = ""

                        if ok and media_id:
                            # Dialog already handles transformations (rotations, invert, grayscale)
                            # media_id is the path to transformed image (if any)
                            pass

                        self.right_selection = None
                        break

            if type(self.right_selection).__name__ == "SVGMediaObject":
                right_selection_obj = cast("MediaObject.MediaObject", self.right_selection)

                for i in range(len(self.__objects)):
                    if self.__objects[i]._media_id == right_selection_obj._media_id:
                        dialog = DialogWindows.modify_svg_input_dialog(self.__objects[i])  # type: ignore[assignment,arg-type]
                        try:
                            ok, cache_hash = dialog._run_dialog()  # type: ignore[misc]
                        except Exception as e:
                            print(f"Error opening SVG dialog: {e}")
                            ok = False
                            cache_hash = None

                        if ok and cache_hash:
                            # Update object with new cache hash
                            svg_obj = self.__objects[i]
                            svg_obj._media_id = cache_hash
                            # Mark as modified for embedding
                            svg_obj.mark_as_modified()  # type: ignore[attr-defined]

                            # Force SVG renderer to reload from cache
                            from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import get_svg_cache

                            cache_path = get_svg_cache().get_cache_path(cache_hash)

                            # Reload the renderer with new cache file
                            if svg_obj._SVGMediaObject__renderer.load(str(cache_path)):  # type: ignore[attr-defined]
                                # Update SVG dimensions from reloaded renderer
                                size = svg_obj._SVGMediaObject__renderer.defaultSize()  # type: ignore[attr-defined]
                                svg_obj._SVGMediaObject__width = size.width()  # type: ignore[attr-defined]
                                svg_obj._SVGMediaObject__height = size.height()  # type: ignore[attr-defined]

                                # Clear size cache to force recalculation
                                svg_obj._SVGMediaObject__cached_scale = None  # type: ignore[attr-defined]
                                svg_obj._SVGMediaObject__cached_onscreen_size = None  # type: ignore[attr-defined]

                                # Clear content cache
                                svg_obj._SVGMediaObject__cached_svg_content = None  # type: ignore[attr-defined]

                                # Set flag to indicate a repaint is needed
                                self._needs_repaint = True

                                print(
                                    f"SVG modified successfully, cache hash: {cache_hash}, dimensions: {size.width()}x{size.height()}"
                                )
                            else:
                                print(f"Failed to reload SVG renderer for cache hash: {cache_hash}")

                        self.right_selection = None
                        break

        # returning MediaObject.LoadError
        return errors

    def step(self, t: float) -> None:
        """
        Method :
            Scene.step(t)
        Parameters :
            t : float

        Scene.step(t) --> None

        Step the scene and all contained `MediaObjects` forward `t` seconds
        in time.

        Thread safely cycle through `__objects` mediaobjects set and for each of
        them call :meth:`pyzui.objects.physicalobject.PhysicalObject.step` inherited method.
        """

        with self.__objects_lock:
            for mediaobject in self.__objects:
                mediaobject.step(t)
            PhysicalObject.step(self, t)

    @property
    def vzmoving(self) -> bool:
        """
        Property :
            Scene.moving
        Parameters :
            None

        Scene.vzmoving --> bool

        Boolean value indicating whether the scene or any contained
        *MediaObjects* have a non-zero velocity.

        Checks if the inherited, vx, vy and vz values from *PhysicalObject*
        are not zero. If it is that means the scene is moving and True is
        returned, If that's not the case it thread safely cycles through
        mediaobjects in *__objects* checking if *mediaobject.moving* is
        True. If it is True is returned. *mediaobject.moving* is also
        inherited property of *PhysicalObject* class.

        See : :class:`pyzui.objects.physicalobject.PhysicalObject`
        """
        if self.vz != 0:
            return True
        else:
            with self.__objects_lock:
                for mediaobject in self.__objects:
                    if mediaobject.vzmoving:
                        return True
        return False

    @property
    def moving(self) -> bool:
        """
        Property :
            Scene.moving
        Parameters :
            None

        Scene.moving --> bool

        Boolean value indicating whether the scene or any contained
        *MediaObjects* have a non-zero velocity.

        Checks if the inherited, vx, vy and vz values from *PhysicalObject*
        are not zero. If it is that means the scene is moving and True is
        returned, If that's not the case it thread safely cycles through
        mediaobjects in *__objects* checking if *mediaobject.moving* is
        True. If it is True is returned. *mediaobject.moving* is also
        inherited property of *PhysicalObject* class.

        See : :class:`pyzui.objects.physicalobject.PhysicalObject`
        """
        if not (self.vx == self.vy == self.vz == 0):
            return True
        else:
            with self.__objects_lock:
                for mediaobject in self.__objects:
                    if mediaobject.moving:
                        return True

        return False

    def __get_origin(self) -> tuple[float, float]:
        """
        Method :
            __get_origin
        Parameters :
            None

        __get_origin --> Tuple[float, float]

        Returns the Scene origin by retrieving _x, and _y variables
        inherited by PhysicalObject class
        """
        return (self._x, self._y)

    def __set_origin(self, origin: tuple[float, float]) -> None:
        """
        Method :
            __set_origin(origin)
        Parameters :
            origin : Tuple[float, float]

        __set_origin --> None

        Set PhysicalObject._x and PhysicalObject._y parameters to new values
        given as input parameters.
        """
        self._x, self._y = origin

    origin = property(__get_origin, __set_origin)
    """Creating Scene.origin property with __get_origin as getter and
    __set_origin as setter"""

    def __get_viewport_size(self) -> tuple[int, int]:
        """
        Method :
            __get_viewport_size
        Parameters :
            None

        __get_viewport_size --> Tuple[int, int]

        Return the current dimensions of the viewport.
        """
        return self.__viewport_size

    def __set_viewport_size(self, viewport_size: tuple[int, int]) -> None:
        """
        Method :
            __set_viewport_size(viewport_size)
        Parameters :
            viewport_size : Tuple[int, int]

        __set_viewport_size --> None

        Happens when mainwindow gets resized or a scene get's loaded having
        different viewport_size than the current mainwindow size. All necessary
        adjustment are handled here

        Centers PhysicalObject._x and PhysicalObject._y to the new input
        parameter viewport_size center, also adjourn PhysicalObject.centre.
        Calculates the ratio between previous viewport_size center and the
        input parameter viewport_size, then calls PhysicalObject.zoom() and
        zooms the scene by base 2 log of the ratio between old and new
        viewport.

        then adjourn the __viewport_size variable with the value given by
        the input parameter viewport_size.

        old_viewport::

            --------------------------------->
            |
            |      ----------------------
            |     |                      |
            |     |             *------  |
            |     |           % |      | |
            |     |             +------" |
            |     |                      |
            |      ----------------------#
            |
            |
            ∨

        new_viewport::

            ----------------------------------->
            |
            |  ------------------------------
            | |                              |
            | |                              |
            | |                              |
            | |                *------       |
            | |              % |      |      |
            | |                +------"      |
            | |                              |
            | |                              |
            |  ------------------------------#
            |
            |
            ∨
        """

        ## centre the scene in the new viewport
        old_viewport_size = self.__viewport_size
        self._x += (viewport_size[0] - old_viewport_size[0]) / 2
        self._y += (viewport_size[1] - old_viewport_size[1]) / 2

        ## scale the scene such that the minimum dimension of the old
        ## viewport is the same in-scene distance as the minimum
        ## dimension of the new viewport
        self.centre = (viewport_size[0] / 2, viewport_size[1] / 2)
        if min(old_viewport_size) > 0 and min(viewport_size) > 0:
            scale = float(min(viewport_size)) / min(old_viewport_size)

            # we have math.log2(scale) as pos' = pos+2**zoomlevel
            self.zoom(math.log2(scale))

        self.__viewport_size = viewport_size

    viewport_size = property(__get_viewport_size, __set_viewport_size)
    """Creating Scene.viewport_size property with __get_viewport_size as
    getter and __set_viewport_size as setter"""

    # Autosave methods
    # Autosave functionality has been moved to SceneAutosaveManager
    # Methods are available via self.__autosave_manager

    # Public autosave API - delegate to SceneAutosaveManager
    def enable_autosave(self, interval_minutes: int) -> None:
        """Enable autosave with specified interval.

        Args:
            interval_minutes: Autosave interval in minutes (minimum 1)
        """
        self.__autosave_manager.enable_autosave(interval_minutes)

    def disable_autosave(self) -> None:
        """Disable autosave and stop timer."""
        self.__autosave_manager.disable_autosave()

    def is_autosave_enabled(self) -> bool:
        """Check if autosave is currently enabled.

        Returns:
            True if autosave is enabled, False otherwise
        """
        return self.__autosave_manager.is_autosave_enabled()

    def get_autosave_interval(self) -> int:
        """Get current autosave interval in seconds.

        Returns:
            Autosave interval in seconds
        """
        return self.__autosave_manager.get_autosave_interval()

    def get_autosave_config(self) -> dict[str, Any]:
        """Get autosave configuration.

        Returns:
            Dictionary with autosave configuration
        """
        return self.__autosave_manager.get_autosave_config()

    def set_autosave_config(self, config: dict[str, Any]) -> None:
        """Update autosave configuration.

        Args:
            config: Dictionary with autosave configuration updates
        """
        self.__autosave_manager.set_autosave_config(config)

    def check_and_clear_repaint_flag(self) -> bool:
        """
        Check if a repaint is needed and clear the flag.

        Returns:
            True if a repaint is needed, False otherwise
        """
        if self._needs_repaint:
            self._needs_repaint = False
            return True
        return False


def new(config: dict[str, Any] | None = None) -> Scene:
    """
    Function :
        new(config=None)
    Parameters :
        config : Optional[Dict[str, Any]]
            Configuration dictionary

    new(config=None) --> Scene

    Create and return a new `Scene` object.
    """
    return Scene(config)


def load_scene(filename: str) -> Scene:
    """
    Function :
        load_scene(filename)
    Parameters :
        filename : str

    load_scene(filename) --> Scene

    Load the scene stored in the file given by `filename`.

    Precondition: `filename` refers to a file in the same format as
    produced by `Scene.save`

    See source code comments:

        :func:`load_scene`
    """

    # Declares a new Scene() object
    scene = Scene()

    f = open(filename)

    # First line of a scene file ale zoomlevel _x and _y of th scene origin
    zoomlevel, ox, oy = f.readline().split()
    scene.zoomlevel = float(zoomlevel)
    scene.origin = (float(ox), float(oy))

    """
    Any line then represent a mediaobject, namely composed by :

            media id: mediaobject.media_id (replacing '%3A' with :)

            zoomlevel: mediaobject.zoomlevel

            x position: mediaobject.pos[0]

            y position: mediaobject.pos[1]
    """
    for line in f:
        mediaobject = scene._create_mediaobject_from_line(line)
        if mediaobject:
            scene.add(mediaobject)

    f.close()

    return scene
