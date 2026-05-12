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

"""
Timing configuration for GUI integration tests.

Adjust these constants for slower or faster testing.
"""

# Short pauses (2 seconds)
SHORT_DELAY_MS = 2000

# Standard delay between actions (0.15 seconds)
DEFAULT_DELAY_MS = 150

# Long delay for loading/rendering (0.2 seconds)
LONG_DELAY_MS = 200

# Extra time for images to fully load/tile (0.5 seconds)
IMAGE_LOAD_DELAY_MS = 500

# Delay between zoom steps (0.05 seconds)
ZOOM_STEP_DELAY_MS = 50

# Delay between movement steps (0.03 seconds)
MOVE_STEP_DELAY_MS = 30
