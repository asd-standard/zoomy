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

"""Class for loading tiles from the local tilestore."""

from typing import Optional, Tuple, Any

from PIL import Image

from .tileprovider import TileProvider
from .. import tilestore as TileStore

class StaticTileProvider(TileProvider):
    """
    Constructor :
        StaticTileProvider(tilecache)
    Parameters :
        tilecache : TileCache

    StaticTileProvider(tilecache) --> StaticTileProvider

    StaticTileProvider objects are used for loading tiles from the
    disk-cache into a TileCache.

    This provider retrieves pre-generated tiles from the local filesystem
    tilestore. It checks the maximum tile level before attempting to load
    and returns None if the requested tile does not exist or cannot be loaded.

    Implementation Notes:
        - Inherits from TileProvider base class
        - Uses PIL Image.open() to load tiles from disk
        - Validates tilelevel against maxtilelevel metadata
        - Returns None for invalid or missing tiles

    Static Tile Provider Flow::

        ┌─────────────────────────┐               |       ┌──────────┐ ┌────────────┐
        │ StaticTileProvider      │               |       │ Load     │ │ Try to     │
        │ task queue receives     │               |       │ existing │ │ synthesize │
        │ tile request            │               |       │ tile     │ │ from lower │
        └────────────┬────────────┘               |       │ image    │ │ zoom tiles │
                     │                            |       └────┬─────┘ └─────┬──────┘
                     ▼                            |            │             │
        ┌─────────────────────────┐               |            │             ▼
        │ Pop request from queue  │               |            │       ┌────────────┐
        │ (LIFO - newest first)   │               |            │       │ If synth   │
        └────────────┬────────────┘               |            │       │ fails,     │
                     │                            |            │       │ load       │
                     ▼                            |            │       │ source     │
        ┌─────────────────────────┐               |            │       │ image      │
        │ Check TileStore         │               |            │       └─────┬──────┘
        │ get_tile_path()         │               |            └─────┬───────┘
        └────────────┬────────────┘               |                  │
                     │                            |                  ▼
                ┌────┴────┐                       |    ┌─────────────────────────┐
                │         │                       |    │ Create Tile object      │
            EXISTS    DOESN'T EXIST               |    │ (PIL Image wrapper)     │
                │         │                       |    └────────────┬────────────┘
                ▼         ▼                       |                 │
                                                  |                 ▼
                                                  |    ┌─────────────────────────┐
                                                  |    │ Store in TileCache      │
                                                  |    └────────────┬────────────┘
                                                  |                 │
                                                  |                 ▼
                                                  |    ┌─────────────────────────┐
                                                  |    │ Save to TileStore       │
                                                  |    │ (if not already there)  │
                                                  |    └────────────┬────────────┘
                                                  |                 │
                                                  |                 ▼
                                                  |    ┌─────────────────────────┐
                                                  |    │ Notify completion       │
                                                  |    │ (tile now available)    │
                                                  |    └─────────────────────────┘

    """
    def __init__(self, tilecache: Any) -> None:
        TileProvider.__init__(self, tilecache)


    def _load(self, tile_id: Tuple[str, int, int, int]) -> Optional[Any]:
        """
        Method :
            StaticTileProvider._load(tile_id)
        Parameters :
            tile_id : Tuple[str, int, int, int]

        StaticTileProvider._load(tile_id) --> Image or None

        Load a tile from the local tilestore.

        The tile_id tuple contains (media_id, tilelevel, row, col). This method
        first validates that the requested tilelevel does not exceed the maximum
        tilelevel for the media. It then attempts to load the tile from disk
        using the path provided by TileStore.get_tile_path().

        Implementation Notes:
            - Checks tilelevel against maxtilelevel metadata
            - Returns None if tilelevel exceeds maxtilelevel
            - Uses PIL Image.open() to load the tile
            - Calls tile.load() to ensure pixel data is loaded
            - Returns None on IOError (file not found or unreadable)
        """

        media_id, tilelevel, row, col = tile_id
        
        maxtilelevel = TileStore.get_metadata(media_id, 'maxtilelevel')
        if tilelevel > maxtilelevel:
            return None
        
        filename = TileStore.get_tile_path(tile_id)
        try:
            tile = Image.open(filename)
            tile.load()
            return tile
            
        except IOError:
            return None
