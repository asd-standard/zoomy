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

    StringMediaObject objects are used to represent strings that can be
    rendered in the ZUI.

    `StringMediaObject.media_id` should be of the form 'string:rrggbb:foobar',
    where 'rrggbb' is a string of three two-digit hexadecimal numbers
    representing the colour of the text, and 'foobar' is the string to be
    displayed.
    """
    def __init__(self, media_id: str, scene: Any) -> None:
        """
        Constructor :
            StringMediaObject(media_id, scene)
        Parameters :
            media_id : str
            scene : Scene

        StringMediaObject(media_id, scene) --> None

        Initialize a new StringMediaObject from the media identified by media_id,
        and the parent Scene referenced by scene.

        The media_id should be of the form 'string:rrggbb:foobar', where
        'rrggbb' is a string of three two-digit hexadecimal numbers representing
        the color of the text, and 'foobar' is the string to be displayed.

        Parses the media_id to extract color and text content, then processes
        the text to handle multi-line strings by splitting on newline characters.
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
        
        

    # Class variable: indicates this media object supports transparency
    transparent: bool = True

    # Class variable: point size of the font when the scale is 100%
    base_pointsize: float = 24.0

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
        # Tuple unpacking: (w, h) -> onscreen_w=w, onscreen_h=h
        onscreen_w: float
        onscreen_h: float
        onscreen_w, onscreen_h = self.onscreen_size

        # Visibility check: only render if text is appropriately sized for viewport
        # self._scene.viewport_size is a tuple (viewport_width, viewport_height)
        # Checks: text not too small (>viewport_min/44) AND not too large (<viewport_max/1.3) AND not invisible
        
        if min(onscreen_w, onscreen_h) > int((min(self._scene.viewport_size))/44) and \
        max(onscreen_w, onscreen_h) < int((max(self._scene.viewport_size))/1.3) and mode \
        != RenderMode.Invisible:
    

            # painter.setPen() sets the color for subsequent drawing operations
            # Uses the QColor object we created in __init__ from the hex color code
            painter.setPen(self.__color)

            # Accessing self.__font property triggers the getter which checks cache first
            # Get cached font from property (returns cached value if scale unchanged)
            # Returns QFont object or None if pointsize < 1
            font: Optional[QtGui.QFont] = self.__font

            # Early return if font is None (text too small to render)
            # return exits the method immediately, skipping all drawing code below
            if not font:
                return

            # painter.setFont() configures the painter to use this font for text rendering
            # QFont object contains typeface, size, weight, and other font properties
            painter.setFont(font)

            # Get top-left corner position of the text object on screen
            # self.topleft is a property that returns tuple (x, y) in screen coordinates
            x: float
            y: float
            x, y = self.topleft

            # Access the cached QFontMetrics object created in __font property
            fontmetrics: QtGui.QFontMetrics = self.__cached_font_metrics

            # fontmetrics.height() returns the vertical spacing for a line of text in pixels
            # Includes ascent (above baseline) + descent (below baseline) + leading (line spacing)
            # Used to calculate y-position for each subsequent line
            hl: int = fontmetrics.height()
                     
            
            # Check if we have multiple lines (multiline text)
            if len(self.lines) > 1 :
                # yr (y-rendering) tracks the current y-position as we draw each line
                # Start at the top y position
                yr: float = y

                # for loop iterates through each string in self.lines
                line: str
                for line in self.lines:
                    # QtCore.QRectF creates a floating-point rectangle for text rendering
                    # Parameters: (x, y, width, height) - all converted to integers
                    rect: QtCore.QRectF = QtCore.QRectF(int(x), int(yr), int(onscreen_w), int(hl))

                    # painter.drawText() renders the text string within the rectangle
                    # Uses the font and color set earlier with setFont() and setPen()
                    painter.drawText(rect, line)

                    # Move y-position down by one line height for next line
                    # += adds hl to yr (yr = yr + hl)
                    yr += hl 
 
            else:
                # Single line rendering
                # Create a single rectangle for the entire text
                # QtCore.QRectF(x, y, width, height) as above
                rect: QtCore.QRectF = QtCore.QRectF(int(x), int(y), int(onscreen_w), int(hl))

                # Draw the first (and only) line
                # self.lines[0] accesses the first element (index 0) of lines list
                painter.drawText(rect, self.lines[0])

           
            

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
            fontmetrics: QtGui.QFontMetrics = self.__cached_font_metrics

            w: float
            h: float
            if len(self.lines) > 1:
                # Use cached longest line index instead of sorting every time
                longest_line: str = self.lines[self.__longest_line_idx]
                w = fontmetrics.horizontalAdvance(longest_line + '-------')
                h = fontmetrics.height() * len(self.lines)
            else:
                w = fontmetrics.horizontalAdvance(self.__str + '-')
                h = fontmetrics.height()

            self.__cached_onscreen_size = (w, h)
            return (w, h)
        else:
            self.__cached_onscreen_size = (0, 0)
            return (0, 0)

