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

"""Strings to be displayed in the ZUI."""

import math
from typing import Optional, Tuple, Any

from PySide6 import QtCore, QtGui

from .mediaobject import MediaObject, LoadError, RenderMode

class StringMediaObject(MediaObject): #, Thread
    """
    Constructor :
        StringMediaObject(media_id, scene)
    Parameters :
        media_id : str
        scene : Scene

    StringMediaObject(media_id, scene) --> None

    StringMediaObject implements a hybrid rendering system for 
    text displayin the ZUI.

    `StringMediaObject.media_id` should be of the form 'string:rrggbb:foobar',
    where 'rrggbb' is a string of three two-digit hexadecimal numbers
    representing the colour of the text, and 'foobar' is the string to be
    displayed.
    
    Overview:

       - render Dual-mode triggered by scene.vzmoving (zoom velocity)
       - moving mode: Direct QPainter.drawText() rendering for smooth zoom/pan operations
       - static mode: Cached QImage rendering for optimal quality when stationary
       - Automatic cache invalidation when movement starts to ensure fresh rendering
    
    From "foobar" string QImage gets generated, from form 'string:rrggbb:foobar' hash get's 
    generated for cache invalidation in case string color of text content changes.
    Also Qfont, QFontMetrics, text dimension (width, height), and scale are cached.

    QImage cached image gets invalidated if relative_scale_diff > 1% or if 
    self__scene_vzmoving returns True 

    For direct text rendering : 
       - longest line index gets Pre-calculated for efficient multi-line rendering
       - Font creation only when point size ≥ 1 (visible text)
       - Visibility culling based on viewport size ratios
       - Automatic cache validation with comprehensive invalidation triggers
    
    """
    def __init__(self, media_id: str, scene: Any) -> None:
        """
        Initialize a new StringMediaObject from the media identified by media_id,
        and the parent Scene referenced by scene.
        """
        MediaObject.__init__(self, media_id, scene)

        # Get color code 'rrggbb' from media_id string and assign it to hexcol variable
        hexcol: str = self._media_id[len('string:'):len('string:rrggbb')]

        # Initialize and assign QtGui.QColor which can then be passed to QtPainter.setPen
        self.__color: QtGui.QColor = QtGui.QColor('#' + hexcol)

        # Check if color is valid to QtGui.QColor() and if not an error is raised
        if not self.__color.isValid():
            raise LoadError("the supplied colour is invalid")

        """Gets to be displayed text `foobar` from media_id string and assign it
        to self.__str variable.
        """
        # Extract the text portion from media_id by slicing from position after 'string:rrggbb:'
        # Example: 'string:FF0000:Hello World' -> 'Hello World'
        self.__str: str = self._media_id[len('string:rrggbb:'):]

        # Returns a list of strings, e.g., 'Hello\nWorld' -> ['Hello', 'World']
        self.lines: list[str] = self.__str.split('\n')

        # Pre-calculate which line is longest to avoid sorting on every render
        # max() finds the maximum value from range(len(self.lines)) using a custom key function
        # range(len(self.lines)) generates indices: 0, 1, 2, ... for each line
        # key=lambda i: len(self.lines[i]) tells max() to compare lines by their length
        # Returns the INDEX of the longest line, not the line itself
        # Example: if lines = ['Hi', 'Hello', 'Hey'], this returns 1 (index of 'Hello')
        self.__longest_line_idx: int = max(range(len(self.lines)), key=lambda i: len(self.lines[i]))

        # Initialize private variables that will be used for caching optimizations                                                                             
        # These start as None and will store computed values when first accessed

        # Stores the scale value (2^(scene.zoomlevel + object.zoomlevel))
        self.__cached_scale: Optional[float] = None

        # Stores the QFont object to avoid recreating it on every render call
        self.__cached_font: Optional[QtGui.QFont] = None

        # Stores the QFontMetrics object (calculates text dimensions)
        self.__cached_font_metrics: Optional[QtGui.QFontMetrics] = None 

        # Stores the calculated (width, height) tuple for this string at current scale
        self.__cached_onscreen_size: Optional[Tuple[float, float]] = None
        
        # Text image caching variables
        # Stores the rendered text as QImage for faster rendering at high zoom
        self.__cached_text_image: Optional[QtGui.QImage] = None
        
        # Stores the scale at which the text image was rendered
        self.__cached_image_scale: Optional[float] = None
        
        # Stores the render mode used for the cached image
        self.__cached_image_mode: Optional[int] = None
        
        # Stores hash of text content and color for cache invalidation
        self.__cached_text_hash: Optional[int] = None
        
        # Track if we were previously static to detect when movement starts
        self.__was_static: bool = True

    # Class variable: indicates this media object supports transparency
    transparent: bool = True

    # Class variable: point size of the font when the scale is 100%
    base_pointsize: float = 24.0

    def __compute_text_hash(self) -> int:
        """
        Method :
            StringMediaObject.__compute_text_hash()
        Parameters :
            None

        StringMediaObject.__compute_text_hash() --> int

        Compute hash of text content and color for cache invalidation.
        Returns a combined hash of all text lines and the color RGB value.
        """
        # Combine all lines into a single string for hashing
        text_content: str = ''.join(self.lines)
        color_rgb: int = self.__color.rgb()
        return hash((text_content, color_rgb))

    def __is_image_cache_valid(self, current_scale: float, mode: int) -> bool:
        """
        Method :
            StringMediaObject.__is_image_cache_valid(current_scale, mode)
        Parameters :
            current_scale : float
            mode : int

        StringMediaObject.__is_image_cache_valid(current_scale, mode) --> bool

        Check if cached text image is valid for current scale and render mode.
        Returns True if cache is valid, False otherwise.
        """
        if self.__cached_text_image is None:
            return False
        if self.__cached_image_scale is None or self.__cached_image_mode is None:
            return False
        
        # Check scale - text rendering is very sensitive to scale changes
        # We need exact scale match for text rendering
        # Use relative difference to handle floating point precision
        if self.__cached_image_scale == 0 or current_scale == 0:
            return False
        
        relative_scale_diff: float = abs(current_scale - self.__cached_image_scale) / self.__cached_image_scale
        if relative_scale_diff > 0.01:  # 1% tolerance
            return False
        
        # Check render mode
        if mode != self.__cached_image_mode:
            return False
        
        # Check text/color hasn't changed
        current_hash: int = self.__compute_text_hash()
        if current_hash != self.__cached_text_hash:
            return False
        
        return True

    def __render_text_direct(self, painter: Any, x: float, y: float, mode: int) -> None:
        """
        Method :
            StringMediaObject.__render_text_direct(painter, x, y, mode)
        Parameters :
            painter : QPainter
            x : float - x position to render at
            y : float - y position to render at
            mode : int

        StringMediaObject.__render_text_direct(painter, x, y, mode) --> None

        Render text directly using QPainter.drawText().
        This is the original rendering method used before caching was implemented.
        """
        # Get dimensions
        onscreen_w: float
        onscreen_h: float
        onscreen_w, onscreen_h = self.onscreen_size
        if onscreen_w <= 0 or onscreen_h <= 0:
            return
        
        # Set pen color for text
        painter.setPen(self.__color)
        
        # Get font
        font: Optional[QtGui.QFont] = self.__font
        if not font:
            return
        
        painter.setFont(font)
        
        # Get font metrics
        fontmetrics: Optional[QtGui.QFontMetrics] = self.__cached_font_metrics
        if fontmetrics is None:
            return
        
        fontmetrics_nonnull: QtGui.QFontMetrics = fontmetrics
        hl: int = fontmetrics_nonnull.height()
        
        # Render multiline or single line text
        if len(self.lines) > 1:
            yr: float = y
            line: str
            for line in self.lines:
                rect: QtCore.QRectF = QtCore.QRectF(int(x), int(yr), int(onscreen_w), int(hl))
                painter.drawText(rect, line)
                yr += hl
        else:
            rect: QtCore.QRectF = QtCore.QRectF(int(x), int(y), int(onscreen_w), int(hl))
            painter.drawText(rect, self.lines[0])

    def __render_text_to_image(self, mode: int) -> QtGui.QImage:
        """
        Method :
            StringMediaObject.__render_text_to_image(mode)
        Parameters :
            mode : int

        StringMediaObject.__render_text_to_image(mode) --> QImage

        Render text to QImage for caching.
        Creates a transparent image with the text rendered at current scale.
        """
        # Get dimensions
        onscreen_w: float
        onscreen_h: float
        onscreen_w, onscreen_h = self.onscreen_size
        if onscreen_w <= 0 or onscreen_h <= 0:
            return QtGui.QImage()
        
        # Create transparent image with appropriate size
        image: QtGui.QImage = QtGui.QImage(
            int(onscreen_w), 
            int(onscreen_h), 
            QtGui.QImage.Format.Format_ARGB8565_Premultiplied #Format_ARGB32_Premultiplied
        )
        image.fill(QtCore.Qt.GlobalColor.transparent)
        
        # Create painter for image
        painter: QtGui.QPainter = QtGui.QPainter(image)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing)
        
        # Render text to image using direct rendering logic at position (0, 0)
        self.__render_text_direct(painter, 0, 0, mode)
        
        painter.end()
        
        return image
    



    def invalidate_cache(self) -> None:
        """
        Method :
            StringMediaObject.invalidate_cache()
        Parameters :
            None

        StringMediaObject.invalidate_cache() --> None

        Invalidate text image cache.
        Clears all cached image data to force re-rendering on next render call.
        """
        self.__cached_text_image = None
        self.__cached_image_scale = None
        self.__cached_image_mode = None
        self.__cached_text_hash = None

    def render(self, painter: Any, mode: int) -> None:
        """
        Method :
            StringMediaObject.render(painter, mode)
        Parameters :
            painter : QPainter
            mode : int

        StringMediaObject.render(painter, mode) --> None

        Given QPainter and Rendering mode renders the string calculating the
        rendering rectangle and using QtPainter.drawText
        """

        # Call onscreen_size property once and unpack into two variables
        onscreen_w: float
        onscreen_h: float
        onscreen_w, onscreen_h = self.onscreen_size

        # Visibility check: only render if text is appropriately sized for viewport
        # self._scene.viewport_size is a tuple (viewport_width, viewport_height)
        # Checks: text not too small (>viewport_min/44) AND not too large (<viewport_max/1.3) AND not invisible
        
        if min(onscreen_w, onscreen_h) > int((min(self._scene.viewport_size))/44) and \
        max(onscreen_w, onscreen_h) < int((max(self._scene.viewport_size))/1.3) and mode \
        != RenderMode.Invisible:
    
            # Get top-left corner position of the text object on scremoen
            x: float
            y: float
            x, y = self.topleft

            # Hybrid rendering: use direct rendering while scene is moving, cached images when static
            if self._scene.vzmoving:
                # Scene is zooming - use direct rendering for smoothness
                # Invalidate cache when zooming starts to ensure fresh cache when movement stops
                if self.__was_static:
                    self.invalidate_cache()
                    self.__was_static = False
                self.__render_text_direct(painter, x, y, mode)
            else:
                # Scene is static - use cached images for optimal rendering quality
                self.__was_static = True
                current_scale: float = self.scale
                if self.__is_image_cache_valid(current_scale, mode):
                    # Draw cached image
                    painter.drawImage(int(x), int(y), self.__cached_text_image)
                else:
                    # Render text to image, cache it, then draw
                    self.__cached_text_image = self.__render_text_to_image(mode)
                    self.__cached_image_scale = current_scale
                    self.__cached_image_mode = mode
                    self.__cached_text_hash = self.__compute_text_hash()
                    
                    # Draw the newly cached image
                    if self.__cached_text_image and not self.__cached_text_image.isNull():
                        painter.drawImage(int(x), int(y), self.__cached_text_image)
                            
    @property
    def __pointsize(self) -> float:
        """
        Property :
            __pointsize
        Parameters :
            None

        __pointsize --> float

        Calculate and return the font point size based on the current scale.

        Returns base_pointsize multiplied by the current scale factor.
        """
        return self.base_pointsize * self.scale

    @property
    def __font(self) -> Optional[QtGui.QFont]:
        """
        Property :
            __font
        Parameters :
            None

        __font --> QFont or None

        Create and return a QFont object with the appropriate point size
        for the current scale.

        Returns None if the point size is less than 1 (too small to be seen).
        Otherwise returns a Sans Serif font with the calculated point size.

        Uses caching to avoid recreating font objects on every access.
        """
        current_scale: float = self.scale

        # Return cached font if scale hasn't changed
        if self.__cached_scale == current_scale and self.__cached_font is not None:
            return self.__cached_font

        pointsize: float = self.__pointsize
        if pointsize < 1:
            ## too small to be seen
            self.__cached_scale = current_scale
            self.__cached_font = None
            self.__cached_font_metrics = None
            return None

        font: QtGui.QFont = QtGui.QFont('Sans Serif')
        font.setPointSizeF(pointsize)

        # Cache the font and metrics
        self.__cached_scale = current_scale
        self.__cached_font = font
        self.__cached_font_metrics = QtGui.QFontMetrics(font)

        return font

    @property
    def onscreen_size(self) -> Tuple[float, float]:
        """
        Property :
            StringMediaObject.onscreen_size
        Parameters :
            None

        StringMediaObject.onscreen_size --> Tuple[float, float]

        Returns width and height of the MediaObject passed to the StringMediaObject Class.

        Uses caching to avoid recalculating size on every access.
        """
        current_scale: float = self.scale

        # Return cached size if scale hasn't changed
        if self.__cached_scale == current_scale and self.__cached_onscreen_size is not None:
            return self.__cached_onscreen_size

        font: Optional[QtGui.QFont] = self.__font

        if font:
            # Use cached font metrics instead of creating new ones
            fontmetrics: Optional[QtGui.QFontMetrics] = self.__cached_font_metrics

            if fontmetrics is None:
                self.__cached_onscreen_size = (0, 0)
                return (0, 0)

            # Type assertion: fontmetrics is not None after the check above
            fontmetrics_nonnull: QtGui.QFontMetrics = fontmetrics

            w: float
            h: float
            if len(self.lines) > 1:
                # Use cached longest line index instead of sorting every time
                longest_line: str = self.lines[self.__longest_line_idx]
                w = fontmetrics_nonnull.horizontalAdvance(longest_line + '-------')
                h = fontmetrics_nonnull.height() * len(self.lines)
            else:
                w = fontmetrics_nonnull.horizontalAdvance(self.__str + '-')
                h = fontmetrics_nonnull.height()

            self.__cached_onscreen_size = (w, h)
            return (w, h)
        else:
            self.__cached_onscreen_size = (0, 0)
            return (0, 0)

