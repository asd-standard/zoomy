## PyZUI 0.1 - Python Zooming User Interface
## Copyright (C) 2009  David Roberts <d@vidr.cc>
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
## 02110-1301, USA.

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

__all__ = [
    'Converter',
    'PDFConverter',
    'VipsConverter',
    'VIPS_AVAILABLE'
]
