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

"""SVG utilities package."""

from .svgarrowutils import (
    elongate_diagonal_arrow,
    elongate_straight_arrow,
    get_arrow_direction,
    get_diagonal_arrow_direction,
    is_arrow_svg,
    is_diagonal_arrow_svg,
    is_straight_arrow_svg,
)
from .svgcircleutils import (
    elongate_circle,
    get_circle_bounds,
    is_circle_svg,
)
from .svgsquareutils import (
    elongate_square,
    get_rectangle_bounds,
    is_square_svg,
)
from .svgstickutils import (
    elongate_diagonal_stick,
    elongate_stick,
    elongate_straight_stick,
    get_diagonal_stick_direction,
    get_stick_direction,
    get_straight_stick_direction,
    is_diagonal_stick_svg,
    is_stick_svg,
    is_straight_stick_svg,
)
from .svgtriangleutils import (
    elongate_triangle,
    get_triangle_bounds,
    is_triangle_svg,
)

__all__ = [
    "elongate_circle",
    "elongate_diagonal_arrow",
    "elongate_diagonal_stick",
    "elongate_square",
    "elongate_stick",
    "elongate_straight_arrow",
    "elongate_straight_stick",
    "elongate_triangle",
    "get_arrow_direction",
    "get_circle_bounds",
    "get_diagonal_arrow_direction",
    "get_diagonal_stick_direction",
    "get_rectangle_bounds",
    "get_stick_direction",
    "get_straight_stick_direction",
    "get_triangle_bounds",
    "is_arrow_svg",
    "is_circle_svg",
    "is_diagonal_arrow_svg",
    "is_diagonal_stick_svg",
    "is_square_svg",
    "is_stick_svg",
    "is_straight_arrow_svg",
    "is_straight_stick_svg",
    "is_triangle_svg",
]
