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

"""QWidget for displaying the ZUI."""

from typing import Any

from PySide6 import QtCore, QtGui, QtWidgets

from pyzui.logger import get_logger
from pyzui.objects.mediaobjects.mediaobjectsutils.svg.utils import (
    elongate_circle,
    elongate_diagonal_arrow,
    elongate_square,
    elongate_stick,
    elongate_straight_arrow,
    elongate_triangle,
    is_circle_svg,
    is_diagonal_arrow_svg,
    is_square_svg,
    is_stick_svg,
    is_straight_arrow_svg,
    is_triangle_svg,
)
from pyzui.objects.mediaobjects.svgmediaobject import SVGMediaObject
from pyzui.objects.scene import scene as Scene
from pyzui.tilesystem import tilemanager as TileManager


class QZUI(QtWidgets.QWidget):
    """
    Constructor :
        QZUI(parent, framerate, zoom_sensitivity)
    Parameters :
        parent : Optional[QtWidgets.QWidget]
        framerate : int
        zoom_sensitivity : int

    QZUI(parent, framerate, zoom_sensitivity) --> None

    QZUI widgets that are used for rendering the ZUI.
    This class defines all the methods to retrieve events, Mouse, Keyboard, etc.

    """

    #: link error variable to QtCore.Signal()
    error = QtCore.Signal(str)

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        framerate: int = 20,
        zoom_sensitivity: int = 50,
        config: dict[str, Any] | None = None,
        autosave_config: dict[str, Any] | None = None,
    ) -> None:
        """
        Constructor :
            QZUI(parent, framerate, zoom_sensitivity, config, autosave_config)
        Parameters :
            parent : Optional[QtWidgets.QWidget]
            framerate : int
            zoom_sensitivity : int
            config : Optional[Dict[str, Any]]
            autosave_config : Optional[Dict[str, Any]]

        QZUI(parent, framerate, zoom_sensitivity, config, autosave_config) --> None

        Create a new QZUI QWidget with the given `parent` widget.
        Initializes the widget with specified framerate and zoom sensitivity.
        """
        QtWidgets.QWidget.__init__(self, parent)

        # Use provided config or create empty dict
        config_dict = config or {}
        # Merge autosave config if provided separately (backward compatibility)
        if autosave_config and "autosave" not in config_dict:
            config_dict["autosave"] = autosave_config

        self.__scene: Scene.Scene = Scene.new(config=config_dict)

        self.__mouse_right_down: bool = False
        self.__mouse_left_down: bool = False
        self.__mousepos: tuple[int, int] | None = None
        self.__shift_held: bool = False
        self.__alt_held: bool = False
        self.__control_held: bool = False
        self.__dropped_frames: int = 0
        self.__draft: bool = True

        # Rectangle drawing state
        self.__drawing_rect: bool = False
        self.__rect_start: tuple[int, int] | None = None
        self.__rect_end: tuple[int, int] | None = None

        # Deferred zoom animation for when widget hasn't been sized yet
        self.__scene_animation_pending: bool = False

        self.__timer: QtCore.QBasicTimer = QtCore.QBasicTimer()
        self.__framerate: int

        self.zoom_sensitivity: int = zoom_sensitivity
        self.reduced_framerate: int = 3
        self.framerate: int = framerate  # type: ignore[no-redef]

        # Logger for arrow elongation and other operations
        self.__logger = get_logger("QZUI")

        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setMouseTracking(True)

    def __zoom(self, num_steps: float) -> None:
        """
        Method :
            __zoom(num_steps)
        Parameters :
            num_steps : float

        __zoom(num_steps) --> None

        Increase the z velocity of the appropriate object by an amount
        proportional to num_steps.
        """
        if self.__alt_held:
            scale = 1.0 / 16
        else:
            scale = 1.0

        if isinstance(self.__active_object, list):
            for active_object in self.__active_object:
                active_object.centre = self.__mousepos
                active_object.vz += scale * num_steps
        else:
            self.__active_object.centre = self.__mousepos
            self.__active_object.vz += scale * num_steps

    def __centre(self) -> None:
        """
        Method :
            __centre()
        Parameters :
            None

        __centre() --> None

        Aim the appropriate object such that the point under the cursor will
        move to the centre of the screen.
        """
        if self.__mousepos is None:
            return
        self.__active_object.vx = self.__active_object.vy = 0.0
        self.__active_object.aim("x", self.width() / 2 - self.__mousepos[0])
        self.__active_object.aim("y", self.height() / 2 - self.__mousepos[1])

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """
        Method :
            paintEvent(event)
        Parameters :
            event : QtGui.QPaintEvent

        paintEvent(event) --> None

        Method that allows you to perform custom painting on a widget.

        It is part of the event handling system, and you typically override it in a subclass of a QWidget
        (or any subclass like QLabel, QFrame, etc.) to draw graphics using the QPainter class.
        """
        if self.framerate:
            self.scene.step(1.0 / self.framerate)

        painter = QtGui.QPainter()
        painter.begin(self)
        try:
            ## paint background
            painter.fillRect(0, 0, self.width(), self.height(), QtCore.Qt.black)

            errors = []
            ## render scene
            errors = self.scene.render(painter, self.__draft)  #

            ## show errors
            for mediaobject in errors:
                self.error.emit("Error loading %s" + str(mediaobject))

            ## Check if scene needs repaint (e.g., after SVG modification)
            if self.scene.check_and_clear_repaint_flag():
                # Schedule another repaint to show updated content
                self.update()

            ## Draw selection rectangle if currently drawing
            if self.__drawing_rect and self.__rect_start and self.__rect_end:
                self.scene.action_draw_rect(self.__rect_start, self.__rect_end, painter, QtCore.Qt.green)

        finally:
            painter.end()

        if self.__mouse_left_down:
            if isinstance(self.__active_object, list):
                for active_object in self.__active_object:
                    active_object.vx = active_object.vy = 0.0
            else:
                self.__active_object.vx = self.__active_object.vy = 0.0

    def timerEvent(self, event: QtCore.QTimerEvent) -> None:
        """
        Method :
            timerEvent(event)
        Parameters :
            event : QtCore.QTimerEvent

        timerEvent(event) --> None

        Handle timer events to update the scene rendering.
        """
        if not self.isVisible():
            return
        if event.timerId() == self.__timer.timerId():
            if self.scene.moving:
                self.__dropped_frames = 0
                self.__draft = True
                self.update()
            else:
                ## Scene or MediaObjects are moving so drop Frames

                if self.__dropped_frames >= self.framerate / self.reduced_framerate:
                    self.__dropped_frames = 0

                    ## since the framerate is reduced, we
                    ## can do high-quality rendering
                    self.__draft = False
                    self.repaint()
                else:
                    ## drop current frame
                    self.__dropped_frames += 1
        else:
            QtWidgets.QWidget.timerEvent(self, event)

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        """
        Method :
            wheelEvent(event)
        Parameters :
            event : QtGui.QWheelEvent

        wheelEvent(event) --> None

        Handle mouse wheel events for zooming or shape elongation.

        Arrow elongation: Ctrl+wheel on selected arrow SVG
        Square elongation: Ctrl/Shift/Alt+wheel on selected square SVG
        720° scroll = 2x factor change (1° = 1/360 factor change)
        """
        # Check for modifier key+wheel with single SVG selection
        # Check both tracked state and event modifiers (Alt key might be intercepted by window manager)
        modifiers = event.modifiers()
        ctrl_pressed = bool(modifiers & QtCore.Qt.KeyboardModifier.ControlModifier)
        shift_pressed = bool(modifiers & QtCore.Qt.KeyboardModifier.ShiftModifier)
        alt_pressed = bool(modifiers & QtCore.Qt.KeyboardModifier.AltModifier)

        has_modifier = (
            self.__control_held or self.__shift_held or self.__alt_held or ctrl_pressed or shift_pressed or alt_pressed
        )

        # Debug logging
        self.__logger.debug(
            f"Wheel event - Tracked: Ctrl={self.__control_held}, Shift={self.__shift_held}, Alt={self.__alt_held}"
        )
        self.__logger.debug(
            f"Wheel event - Event modifiers: Ctrl={ctrl_pressed}, Shift={shift_pressed}, Alt={alt_pressed}"
        )
        self.__logger.debug(f"Wheel event - has_modifier={has_modifier}, selection={self.scene.selection is not None}")

        if (
            has_modifier
            and self.scene.selection
            and not isinstance(self.scene.selection, list)
            and isinstance(self.scene.selection, SVGMediaObject)
        ):
            svg_obj = self.scene.selection
            svg_path = svg_obj._media_id

            # Check if it's any type of arrow SVG
            is_arrow = False
            arrow_type = None

            if is_straight_arrow_svg(svg_path):
                is_arrow = True
                arrow_type = "straight"
            elif is_diagonal_arrow_svg(svg_path):
                is_arrow = True
                arrow_type = "diagonal"

            if is_arrow:
                # Arrow elongation only works with Ctrl key
                # Check both tracked state and event modifiers
                if not (self.__control_held or ctrl_pressed):
                    # Fall through to normal zoom if not Ctrl
                    self.__logger.debug("Arrow elongation requires Ctrl key, falling through to normal zoom")
                    pass
                else:
                    # Calculate elongation factor from wheel delta
                    # 720° = 2x factor, so 1° = 1/360 factor change
                    num_degrees = event.angleDelta().y()

                    # Sensitivity: 1/360 per degree
                    # Positive scroll (up) elongates, negative shortens
                    elongation_delta = num_degrees / 360.0
                    current_factor = 1.0 + elongation_delta

                    # Apply minimum factor (0.2x)
                    if current_factor < 0.2:
                        current_factor = 0.2
                        self.__logger.debug("Clamped scale factor to minimum 0.2")

                    self.__logger.debug(
                        f"Attempting {arrow_type} arrow elongation: factor={current_factor:.3f}, degrees={num_degrees}"
                    )

                    try:
                        # Elongate arrow (returns cache hash)
                        cache_hash = ""
                        if arrow_type == "straight":
                            cache_hash = elongate_straight_arrow(svg_path, current_factor)
                        else:  # diagonal
                            cache_hash = elongate_diagonal_arrow(svg_path, current_factor)

                        # Update SVGMediaObject with new cache hash
                        svg_obj._media_id = cache_hash
                        svg_obj.mark_as_modified()

                        # Force SVG renderer to reload from cache
                        renderer = svg_obj._SVGMediaObject__renderer
                        # Get cache path directly
                        from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import get_svg_cache

                        cache_path = get_svg_cache().get_cache_path(cache_hash)
                        if renderer.load(str(cache_path)):
                            # Update SVG dimensions from reloaded renderer
                            size = renderer.defaultSize()
                            svg_obj._SVGMediaObject__width = size.width()
                            svg_obj._SVGMediaObject__height = size.height()

                            # Clear size cache to force recalculation
                            svg_obj._SVGMediaObject__cached_scale = None
                            svg_obj._SVGMediaObject__cached_onscreen_size = None

                            # Trigger repaint
                            self.update()
                            self.__logger.debug(
                                f"{(arrow_type or 'Arrow').capitalize()} arrow elongated successfully, cache hash: {cache_hash}, dimensions: {size.width()}x{size.height()}"
                            )
                        else:
                            self.__logger.error(f"Failed to reload SVG renderer for cache hash: {cache_hash}")

                    except Exception as e:
                        # Log error but don't crash
                        self.__logger.error(f"{(arrow_type or 'Arrow').capitalize()} arrow elongation failed: {e}")
                        # Fall through to normal zoom

                    return  # Skip normal zoom when arrow elongation was attempted

            # Check if it's a square SVG
            elif is_square_svg(svg_path):
                # Calculate elongation factor from wheel delta
                # 720° = 2x factor, so 1° = 1/360 factor change
                num_degrees = event.angleDelta().y()

                # Sensitivity: 1/360 per degree
                # Positive scroll (up) elongates, negative shortens
                elongation_delta = num_degrees / 360.0
                current_factor = 1.0 + elongation_delta

                # Apply minimum factor (0.2x)
                if current_factor < 0.2:
                    current_factor = 0.2
                    self.__logger.debug("Clamped scale factor to minimum 0.2")

                # Use event modifiers (already calculated above)
                # ctrl_pressed, shift_pressed, alt_pressed are already defined

                scale_x = 1.0
                scale_y = 1.0
                scaling_mode = None

                if ctrl_pressed and not shift_pressed:
                    # Ctrl only: proportional scaling (both axes)
                    scale_x = scale_y = current_factor
                    scaling_mode = "proportional"
                elif shift_pressed and not ctrl_pressed:
                    # Shift only: X-only scaling
                    scale_x = current_factor
                    scale_y = 1.0
                    scaling_mode = "X-only"
                elif ctrl_pressed and shift_pressed:
                    # Ctrl+Shift: Y-only scaling
                    scale_x = 1.0
                    scale_y = current_factor
                    scaling_mode = "Y-only (Ctrl+Shift)"

                # Only attempt square elongation if we have a valid modifier combination
                if scaling_mode:
                    self.__logger.debug(
                        f"Attempting square elongation: X={scale_x:.3f}, Y={scale_y:.3f}, mode={scaling_mode}, degrees={num_degrees}"
                    )

                    try:
                        # Elongate square (returns cache hash)
                        cache_hash = elongate_square(svg_path, scale_x, scale_y)

                        # Update SVGMediaObject with new cache hash
                        svg_obj._media_id = cache_hash
                        svg_obj.mark_as_modified()

                        # Force SVG renderer to reload from cache
                        renderer = svg_obj._SVGMediaObject__renderer
                        # Get cache path directly
                        from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import get_svg_cache

                        cache_path = get_svg_cache().get_cache_path(cache_hash)
                        if renderer.load(str(cache_path)):
                            # Update SVG dimensions from reloaded renderer
                            size = renderer.defaultSize()
                            svg_obj._SVGMediaObject__width = size.width()
                            svg_obj._SVGMediaObject__height = size.height()

                            # Clear size cache to force recalculation
                            svg_obj._SVGMediaObject__cached_scale = None
                            svg_obj._SVGMediaObject__cached_onscreen_size = None

                            # Trigger repaint
                            self.update()
                            self.__logger.debug(
                                f"Square elongated successfully, cache hash: {cache_hash}, dimensions: {size.width()}x{size.height()}"
                            )
                        else:
                            self.__logger.error(f"Failed to reload SVG renderer for cache hash: {cache_hash}")

                    except Exception as e:
                        # Log error but don't crash
                        self.__logger.error(f"Square elongation failed: {e}")
                        # Fall through to normal zoom

                    return  # Skip normal zoom when square elongation was attempted
                else:
                    self.__logger.debug(f"No valid scaling mode for square. Ctrl={ctrl_pressed}, Shift={shift_pressed}")
                    # Fall through to normal zoom

            # Check if it's a circle SVG
            elif is_circle_svg(svg_path):
                # Calculate elongation factor from wheel delta
                # 720° = 2x factor, so 1° = 1/360 factor change
                num_degrees = event.angleDelta().y()

                # Sensitivity: 1/360 per degree
                # Positive scroll (up) elongates, negative shortens
                elongation_delta = num_degrees / 360.0
                current_factor = 1.0 + elongation_delta

                # Apply minimum factor (0.2x)
                if current_factor < 0.2:
                    current_factor = 0.2
                    self.__logger.debug("Clamped scale factor to minimum 0.2")

                # Use event modifiers (already calculated above)
                # ctrl_pressed, shift_pressed, alt_pressed are already defined

                scale_x = 1.0
                scale_y = 1.0
                scaling_mode = None

                if ctrl_pressed and not shift_pressed:
                    # Ctrl only: proportional scaling (both axes)
                    scale_x = scale_y = current_factor
                    scaling_mode = "proportional"
                elif shift_pressed and not ctrl_pressed:
                    # Shift only: X-only scaling
                    scale_x = current_factor
                    scale_y = 1.0
                    scaling_mode = "X-only"
                elif ctrl_pressed and shift_pressed:
                    # Ctrl+Shift: Y-only scaling
                    scale_x = 1.0
                    scale_y = current_factor
                    scaling_mode = "Y-only (Ctrl+Shift)"

                # Only attempt circle elongation if we have a valid modifier combination
                if scaling_mode:
                    self.__logger.debug(
                        f"Attempting circle elongation: X={scale_x:.3f}, Y={scale_y:.3f}, mode={scaling_mode}, degrees={num_degrees}"
                    )

                    try:
                        # Elongate circle (returns cache hash)
                        cache_hash = elongate_circle(svg_path, scale_x, scale_y)

                        # Update SVGMediaObject with new cache hash
                        svg_obj._media_id = cache_hash
                        svg_obj.mark_as_modified()

                        # Force SVG renderer to reload from cache
                        renderer = svg_obj._SVGMediaObject__renderer
                        # Get cache path directly
                        from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import get_svg_cache

                        cache_path = get_svg_cache().get_cache_path(cache_hash)
                        if renderer.load(str(cache_path)):
                            # Update SVG dimensions from reloaded renderer
                            size = renderer.defaultSize()
                            svg_obj._SVGMediaObject__width = size.width()
                            svg_obj._SVGMediaObject__height = size.height()

                            # Clear size cache to force recalculation
                            svg_obj._SVGMediaObject__cached_scale = None
                            svg_obj._SVGMediaObject__cached_onscreen_size = None

                            # Trigger repaint
                            self.update()
                            self.__logger.debug(
                                f"Circle elongated successfully, cache hash: {cache_hash}, dimensions: {size.width()}x{size.height()}"
                            )
                        else:
                            self.__logger.error(f"Failed to reload SVG renderer for cache hash: {cache_hash}")

                    except Exception as e:
                        # Log error but don't crash
                        self.__logger.error(f"Circle elongation failed: {e}")
                        # Fall through to normal zoom

                    return  # Skip normal zoom when circle elongation was attempted
                else:
                    self.__logger.debug(f"No valid scaling mode for circle. Ctrl={ctrl_pressed}, Shift={shift_pressed}")
                    # Fall through to normal zoom

            # Check if it's a triangle SVG
            elif is_triangle_svg(svg_path):
                # Calculate elongation factor from wheel delta
                # 720° = 2x factor, so 1° = 1/360 factor change
                num_degrees = event.angleDelta().y()

                # Sensitivity: 1/360 per degree
                # Positive scroll (up) elongates, negative shortens
                elongation_delta = num_degrees / 360.0
                current_factor = 1.0 + elongation_delta

                # Apply minimum factor (0.2x)
                if current_factor < 0.2:
                    current_factor = 0.2
                    self.__logger.debug("Clamped scale factor to minimum 0.2")

                # Use event modifiers (already calculated above)
                # ctrl_pressed, shift_pressed, alt_pressed are already defined

                scale_x = 1.0
                scale_y = 1.0
                scaling_mode = None

                if ctrl_pressed and not shift_pressed:
                    # Ctrl only: proportional scaling (both axes)
                    scale_x = scale_y = current_factor
                    scaling_mode = "proportional"
                elif shift_pressed and not ctrl_pressed:
                    # Shift only: X-only scaling
                    scale_x = current_factor
                    scale_y = 1.0
                    scaling_mode = "X-only"
                elif ctrl_pressed and shift_pressed:
                    # Ctrl+Shift: Y-only scaling
                    scale_x = 1.0
                    scale_y = current_factor
                    scaling_mode = "Y-only (Ctrl+Shift)"

                # Only attempt triangle elongation if we have a valid modifier combination
                if scaling_mode:
                    self.__logger.debug(
                        f"Attempting triangle elongation: X={scale_x:.3f}, Y={scale_y:.3f}, mode={scaling_mode}, degrees={num_degrees}"
                    )

                    try:
                        # Elongate triangle (returns cache hash)
                        cache_hash = elongate_triangle(svg_path, scale_x, scale_y)

                        # Update SVGMediaObject with new cache hash
                        svg_obj._media_id = cache_hash
                        svg_obj.mark_as_modified()

                        # Force SVG renderer to reload from cache
                        renderer = svg_obj._SVGMediaObject__renderer
                        # Get cache path directly
                        from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import get_svg_cache

                        cache_path = get_svg_cache().get_cache_path(cache_hash)
                        if renderer.load(str(cache_path)):
                            # Update SVG dimensions from reloaded renderer
                            size = renderer.defaultSize()
                            svg_obj._SVGMediaObject__width = size.width()
                            svg_obj._SVGMediaObject__height = size.height()

                            # Clear size cache to force recalculation
                            svg_obj._SVGMediaObject__cached_scale = None
                            svg_obj._SVGMediaObject__cached_onscreen_size = None

                            # Trigger repaint
                            self.update()
                            self.__logger.debug(
                                f"Triangle elongated successfully, cache hash: {cache_hash}, dimensions: {size.width()}x{size.height()}"
                            )
                        else:
                            self.__logger.error(f"Failed to reload SVG renderer for cache hash: {cache_hash}")

                    except Exception as e:
                        # Log error but don't crash
                        self.__logger.error(f"Triangle elongation failed: {e}")
                        # Fall through to normal zoom

                    return  # Skip normal zoom when triangle elongation was attempted
                else:
                    self.__logger.debug(
                        f"No valid scaling mode for triangle. Ctrl={ctrl_pressed}, Shift={shift_pressed}"
                    )
                    # Fall through to normal zoom

            # Check if it's a stick SVG
            elif is_stick_svg(svg_path):
                # Calculate elongation factor from wheel delta
                # 720° = 2x factor, so 1° = 1/360 factor change
                num_degrees = event.angleDelta().y()

                # Sensitivity: 1/360 per degree
                # Positive scroll (up) elongates, negative shortens
                elongation_delta = num_degrees / 360.0
                current_factor = 1.0 + elongation_delta

                # Apply minimum factor (0.2x)
                if current_factor < 0.2:
                    current_factor = 0.2
                    self.__logger.debug("Clamped scale factor to minimum 0.2")

                # For sticks, we only need Ctrl modifier (like arrows)
                # No need for X/Y scaling modes since sticks are 1D
                if ctrl_pressed:
                    self.__logger.debug(
                        f"Attempting stick elongation: factor={current_factor:.3f}, degrees={num_degrees}"
                    )

                    try:
                        # Elongate stick (returns cache hash)
                        cache_hash = elongate_stick(svg_path, current_factor)

                        # Update SVGMediaObject with new cache hash
                        svg_obj._media_id = cache_hash
                        svg_obj.mark_as_modified()

                        # Force SVG renderer to reload from cache
                        renderer = svg_obj._SVGMediaObject__renderer
                        # Get cache path directly
                        from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import get_svg_cache

                        cache_path = get_svg_cache().get_cache_path(cache_hash)
                        if renderer.load(str(cache_path)):
                            # Update SVG dimensions from reloaded renderer
                            size = renderer.defaultSize()
                            svg_obj._SVGMediaObject__width = size.width()
                            svg_obj._SVGMediaObject__height = size.height()

                            # Clear size cache to force recalculation
                            svg_obj._SVGMediaObject__cached_scale = None
                            svg_obj._SVGMediaObject__cached_onscreen_size = None

                            # Trigger repaint
                            self.update()
                            self.__logger.debug(
                                f"Stick elongated successfully, cache hash: {cache_hash}, dimensions: {size.width()}x{size.height()}"
                            )
                        else:
                            self.__logger.error(f"Failed to reload SVG renderer for cache hash: {cache_hash}")

                    except Exception as e:
                        # Log error but don't crash
                        self.__logger.error(f"Stick elongation failed: {e}")
                        # Fall through to normal zoom

                    return  # Skip normal zoom when stick elongation was attempted
                else:
                    self.__logger.debug(f"No Ctrl modifier for stick elongation. Ctrl={ctrl_pressed}")
                    # Fall through to normal zoom

        # Normal zoom behavior
        num_degrees = event.angleDelta().y()
        num_steps = round(num_degrees / self.zoom_sensitivity, 3)
        self.__mousepos = (int(event.position().x()), int(event.position().y()))
        self.__zoom(num_steps)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """
        Method :
            mousePressEvent(event)
        Parameters :
            event : QtGui.QMouseEvent

        mousePressEvent(event) --> None

        Handle mouse press events for object selection.
        """
        if event.button() == QtCore.Qt.LeftButton:
            self.__mouse_left_down = True
            self.__mousepos = (int(event.position().x()), int(event.position().y()))

            if self.__control_held:
                # Start rectangle drawing
                self.__drawing_rect = True
                self.__rect_start = self.__mousepos
                self.__rect_end = self.__mousepos
                # Don't change selection when drawing rectangle

            elif not self.__shift_held:
                ## shift-click won't change the selection
                # Only change selection if clicking on a non-selected object
                clicked_object = self.scene.get(self.__mousepos)

                # Check if we're clicking on an already-selected object
                if isinstance(self.scene.selection, list):
                    # Multiple selection - check if clicked object is in the list
                    if clicked_object in self.scene.selection:
                        # Don't change selection, allow dragging
                        pass
                    elif clicked_object is None:
                        # Clicking on empty space - keep multi-selection for dragging
                        pass
                    else:
                        # Clicking on a different object - select just that object
                        self.scene.selection = clicked_object
                elif self.scene.selection is not None and clicked_object == self.scene.selection:
                    # Don't change selection, allow dragging
                    pass
                elif clicked_object is None and self.scene.selection is not None:
                    # Clicking on empty space with single selection - keep selection for dragging
                    pass
                else:
                    self.scene.selection = clicked_object

            else:
                self.__drawing_rect = False
                self.__rect_start = None
                self.__rect_end = None

        if event.button() == QtCore.Qt.RightButton:
            self.__mouse_right_down = True
            self.__mousepos = (int(event.position().x()), int(event.position().y()))
            if not self.__shift_held:
                ## shift-click won't change the selection
                self.scene.right_selection = self.scene.get(self.__mousepos)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        """
        Method :
            mouseMoveEvent(event)
        Parameters :
            event : QtGui.QMouseEvent

        mouseMoveEvent(event) --> None

        Handle mouse move events for dragging objects.
        """
        if (event.buttons() & QtCore.Qt.LeftButton) and self.__mouse_left_down:
            if self.__mousepos is None:
                return

            if self.__drawing_rect:
                # Update rectangle end position for drawing
                self.__rect_end = (int(event.position().x()), int(event.position().y()))
                # Trigger repaint to show updated rectangle
                self.update()
            else:
                # Original object dragging logic
                mx = int(event.position().x()) - self.__mousepos[0]
                my = int(event.position().y()) - self.__mousepos[1]

                t = 1.0 / self.framerate

                if isinstance(self.__active_object, list):
                    for active_object in self.__active_object:
                        active_object.aim("y", my, t)
                        active_object.aim("x", mx, t)

                else:
                    self.__active_object.aim("y", my, t)
                    self.__active_object.aim("x", mx, t)

        self.__mousepos = (int(event.position().x()), int(event.position().y()))

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        """
        Method :
            mouseReleaseEvent(event)
        Parameters :
            event : QtGui.QMouseEvent

        mouseReleaseEvent(event) --> None

        Handle mouse release events.
        """
        if event.button() == QtCore.Qt.LeftButton and self.__mouse_left_down:
            self.__mouse_left_down = False

            if self.__drawing_rect:
                # Finish rectangle drawing
                self.__drawing_rect = False

                # If we have valid rectangle coordinates, select objects within it
                if self.__rect_start and self.__rect_end:
                    # Get objects within the rectangle
                    selected_objects = self.scene.get(self.__rect_start, self.__rect_end)
                    if selected_objects:
                        self.scene.selection = selected_objects

                # Clear rectangle coordinates
                self.__rect_start = None
                self.__rect_end = None
                # Trigger repaint to remove rectangle
                self.update()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """
        Method :
            keyPressEvent(event)
        Parameters :
            event : QtGui.QKeyEvent

        keyPressEvent(event) --> None

        Handle key press events for navigation and control.
        """
        if self.__alt_held:
            move_amount = 16
        else:
            move_amount = 16

        key = event.key()
        if key == QtCore.Qt.Key_Escape:
            self.scene.selection = None
        elif key == QtCore.Qt.Key_PageUp:
            self.__zoom(1.0)
        elif key == QtCore.Qt.Key_PageDown:
            self.__zoom(-1.0)
        elif key == QtCore.Qt.Key_Up:
            self.__active_object.aim("y", -move_amount)
        elif key == QtCore.Qt.Key_Down:
            self.__active_object.aim("y", move_amount)
        elif key == QtCore.Qt.Key_Left:
            self.__active_object.aim("x", -move_amount)
        elif key == QtCore.Qt.Key_Right:
            self.__active_object.aim("x", move_amount)
        elif key == QtCore.Qt.Key_Shift:
            self.__shift_held = True
        elif key == QtCore.Qt.Key_Alt:
            self.__alt_held = True
        elif key == QtCore.Qt.Key_Control:
            self.__control_held = True
        elif key == QtCore.Qt.Key_Space:
            self.__centre()
        elif key == QtCore.Qt.Key_Delete:
            if self.scene.selection:
                self.scene.remove(self.scene.selection)
                self.scene.selection = None
        elif key == QtCore.Qt.Key_C and (event.modifiers() & QtCore.Qt.ControlModifier):
            if self.scene.selection:
                self.scene.copy_selection()
        elif key == QtCore.Qt.Key_V and (event.modifiers() & QtCore.Qt.ControlModifier):
            # Paste at mouse position or viewport centre
            # Convert from screen coordinates to scene coordinates
            scene_origin = self.scene.origin
            scene_zoomlevel = self.scene.zoomlevel
            scale = 2**-scene_zoomlevel

            if self.__mousepos:
                # Convert mouse position from screen to scene coordinates
                mouse_x, mouse_y = self.__mousepos
                scene_x = (mouse_x - scene_origin[0]) * scale
                scene_y = (mouse_y - scene_origin[1]) * scale
                paste_pos = (scene_x, scene_y)
            else:
                # Calculate viewport centre in scene coordinates
                # Viewport centre is at (width/2, height/2) in screen coordinates
                viewport_centre_x = self.width() / 2
                viewport_centre_y = self.height() / 2
                scene_x = (viewport_centre_x - scene_origin[0]) * scale
                scene_y = (viewport_centre_y - scene_origin[1]) * scale
                paste_pos = (scene_x, scene_y)
            self.scene.paste(paste_pos)
        else:
            QtWidgets.QWidget.keyPressEvent(self, event)

    def keyReleaseEvent(self, event: QtGui.QKeyEvent) -> None:
        """
        Method :
            keyReleaseEvent(event)
        Parameters :
            event : QtGui.QKeyEvent

        keyReleaseEvent(event) --> None

        Handle key release events.
        """
        key = event.key()
        if key == QtCore.Qt.Key_Shift:
            self.__shift_held = False
        elif key == QtCore.Qt.Key_Alt:
            self.__alt_held = False
        elif key == QtCore.Qt.Key_Control:
            # Clear rectangle drawing state when Control key is released
            if self.__drawing_rect:
                self.__drawing_rect = False
                self.__rect_start = None
                self.__rect_end = None
                # Trigger repaint to clear drawn rectangle
                self.update()
            self.__control_held = False
        else:
            QtWidgets.QWidget.keyPressEvent(self, event)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """
        Method :
            resizeEvent(event)
        Parameters :
            event : QtGui.QResizeEvent

        resizeEvent(event) --> None

        Handle resize events to update the viewport size.
        """
        self.__scene.viewport_size = (self.width(), self.height())

        # Defer zoom animation to next event loop iteration so the widget
        # has its final layout size (avoids running at intermediate sizes
        # during progressive layout passes with QTabWidget).
        if self.__scene_animation_pending:
            QtCore.QTimer.singleShot(0, self._run_pending_animation)

    def _run_pending_animation(self) -> None:
        """Run the deferred zoom-in animation once the widget is sized."""
        if not self.__scene_animation_pending:
            return
        self.__scene_animation_pending = False
        if self.width() > 0 and self.height() > 0:
            try:
                if hasattr(self.__scene, "_Scene__objects") and len(self.__scene._Scene__objects) > 0:
                    self.__scene.centre = (self.width() / 2, self.height() / 2)
                    self.__scene.zoom(-5.0)
                    self.__scene.aim("z", 5.0)
            except (TypeError, AttributeError):
                pass

    def focusOutEvent(self, event: QtGui.QFocusEvent) -> None:
        """
        Method :
            focusOutEvent(event)
        Parameters :
            event : QtGui.QFocusEvent

        focusOutEvent(event) --> None

        Handle focus out events to reset keyboard modifiers and rectangle drawing state.
        This prevents rectangle drawing from persisting when widget loses focus (e.g., during save dialog).
        """
        # Reset all keyboard modifiers
        self.__shift_held = False
        self.__alt_held = False
        self.__control_held = False

        # Reset rectangle drawing state
        self.__drawing_rect = False
        self.__rect_start = None
        self.__rect_end = None

        # Trigger repaint to clear any drawn rectangle
        self.update()

        QtWidgets.QWidget.focusOutEvent(self, event)

    @property
    def __active_object(self) -> Any:
        """
        Property :
            __active_object
        Parameters :
            None

        __active_object --> Any

        Return the currently active object (either selected object or scene).
        """
        if self.scene.selection and not self.__shift_held:
            return self.scene.selection
        else:
            return self.scene

    def __get_framerate(self) -> int:
        """
        Method :
            __get_framerate()
        Parameters :
            None

        __get_framerate() --> int

        Return the rendering framerate.
        """
        return self.__framerate

    def __set_framerate(self, framerate: int) -> None:
        """
        Method :
            __set_framerate(framerate)
        Parameters :
            framerate : int

        __set_framerate(framerate) --> None

        Set the rendering framerate.
        """
        self.__framerate = framerate
        if self.__framerate:
            self.__timer.start(int(1000 / self.__framerate), self)
        elif self.__timer.isActive():
            self.__timer.stop()

    framerate = property(__get_framerate, __set_framerate)

    def __get_scene(self) -> "Scene.Scene":
        """
        Method :
            __get_scene()
        Parameters :
            None

        __get_scene() --> Scene.Scene

        Return the scene currently being viewed.
        """

        return self.__scene

    def __set_scene(self, scene: "Scene.Scene") -> None:
        """
        Method :
            __set_scene(scene)
        Parameters :
            scene : Scene.Scene

        __set_scene(scene) --> None

        Set the scene to be viewed.
        """
        # Stop autosave on current scene before replacement.
        # Only call disable_autosave if it is actually active —
        # avoids redundant QTimer.stop() and prevents log noise
        # from the rapid disable/enable/disable cycle during
        # scene open / new-scene operations.
        if self.__scene and hasattr(self.__scene, "_Scene__autosave_manager"):
            try:
                mgr = self.__scene._Scene__autosave_manager
                if mgr._autosave_active:
                    mgr.disable_autosave()
            except Exception:
                pass  # Scene is being replaced anyway
        TileManager.purge()
        self.__scene = scene
        if self.width() > 0 and self.height() > 0:
            self.__scene.viewport_size = (self.width(), self.height())

        ## Reset mouse/keyboard and rectangle selection state when loading new scene
        self.__mouse_right_down = False
        self.__mouse_left_down = False
        self.__mousepos = None
        self.__shift_held = False
        self.__alt_held = False
        self.__control_held = False
        self.__dropped_frames = 0
        self.__draft = True

        # Reset rectangle drawing state
        self.__drawing_rect = False
        self.__rect_start = None
        self.__rect_end = None

        # Apply zoom animation only for loaded scenes (not new scenes)
        # New scenes should use the default_zoomlevel from config
        # Loaded scenes have objects, new scenes are empty
        # Defer animation if widget hasn't been sized yet (e.g. during init with QTabWidget)
        try:
            if hasattr(self.__scene, "_Scene__objects") and len(self.__scene._Scene__objects) > 0:
                if self.width() > 0 and self.height() > 0:
                    self.__scene.centre = (self.width() / 2, self.height() / 2)
                    self.__scene.zoom(-5.0)
                    self.__scene.aim("z", 5.0)
                    self.__scene_animation_pending = False
                else:
                    self.__scene_animation_pending = True
        except (TypeError, AttributeError):
            # Handle mock objects in tests
            pass

    scene = property(__get_scene, __set_scene)
