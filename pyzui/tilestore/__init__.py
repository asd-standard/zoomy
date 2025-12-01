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

"""Tilestore package for managing disk-based tile storage and cleanup."""

# Import all public functions from tilestore module
from .tilestore import (
    tile_dir,
    disk_lock,
    get_media_path,
    get_tile_path,
    load_metadata,
    get_metadata,
    write_metadata,
    tiled,
    get_directory_size,
    get_tilestore_stats,
    cleanup_old_tiles,
    auto_cleanup
)

__all__ = [
    'tile_dir',
    'disk_lock',
    'get_media_path',
    'get_tile_path',
    'load_metadata',
    'get_metadata',
    'write_metadata',
    'tiled',
    'get_directory_size',
    'get_tilestore_stats',
    'cleanup_old_tiles',
    'auto_cleanup'
]
