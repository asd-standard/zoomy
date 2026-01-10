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

"""Converters package for converting various media formats to PPM."""

# Import base converter
from .converter import Converter

# Import specific converters
from .pdfconverter import PDFConverter

# VipsConverter may not be available (requires pyvips)
try:
    from .vipsconverter import VipsConverter
    VIPS_AVAILABLE = True
except ImportError:
    VipsConverter = None
    VIPS_AVAILABLE = False

# Process-based converter runner for parallel conversion
from . import converter_runner

__all__ = [
    'Converter',
    'PDFConverter',
    'VipsConverter',
    'VIPS_AVAILABLE',
    'converter_runner'
]
