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

"""Class for loading tiles into memory from somewhere other than the local
filesystem (abstract base class)."""

from typing import Optional, Tuple, Any, TYPE_CHECKING
import os

from PySide6 import QtGui

from .tileprovider import TileProvider
from .. import tilestore as TileStore

if TYPE_CHECKING:
    from PySide6.QtGui import QImage
    from .tileprovider import TileID

TileID = Tuple[str, int, int, int]

class DynamicTileProvider(TileProvider):
    """
    Constructor :
        DynamicTileProvider(tilecache)
    Parameters :
        tilecache : TileCache

    DynamicTileProvider(tilecache) --> DynamicTileProvider

    DynamicTileProvider objects are used for either generating tiles or
    loading them from a remote host, and then loading them into a TileCache.

    This is an abstract base class for tile providers that create tiles
    dynamically (either by generation or remote retrieval) rather than
    loading pre-existing tiles from disk. Derived classes must implement
    the _load_dynamic() method.

    Implementation Notes:
        - Inherits from TileProvider base class
        - Provides default values for filext, tilesize, and aspect_ratio
        - _load() checks if tile exists locally before calling _load_dynamic()
        - Uses QImage for loading tiles after they are created
        - Derived classes should override _load_dynamic() to implement
          specific tile generation or retrieval logic

    Dynamic Tile Provider Flow (Fern Example)::

        ┌─────────────────────────┐               |       ┌──────────┐ ┌────────────────────┐
        │ FernDynamicTileProvider │               |       │ Load     │ │ Generate tile      │
        │ receives request        │               |       │ cached   │ │ algorithmically    │
        └────────────┬────────────┘               |       │ tile     │ │ • Calculate fern   │
                     │                            |       └────┬─────┘ │   parameters       │
                     ▼                            |            │       │ • Draw fractal     │
        ┌─────────────────────────┐               |            │       │ • Create image     │
        │ Parse tile ID           │               |            │       └─────┬──────────────┘
        │ • Zoom level            │               |            │             │
        │ • Tile coordinates      │               |            └─────┬───────┘
        └────────────┬────────────┘               |                  │
                     │                            |                  ▼
                     ▼                            |    ┌─────────────────────────┐
        ┌─────────────────────────┐               |    │ Wrap in Tile object     │
        │ Check TileStore         │               |    └────────────┬────────────┘
        │ (may have been          │               |                 │
        │  generated before)      │               |                 ▼
        └────────────┬────────────┘               |    ┌─────────────────────────┐
                     │                            |    │ Store in TileCache      │
                ┌────┴────┐                       |    └────────────┬────────────┘
                │         │                       |                 │
            EXISTS    NEW TILE                    |                 ▼
                │         │                       |    ┌─────────────────────────┐
                ▼         ▼                       |    │ Save to TileStore       │
                                                  |    └────────────┬────────────┘
                                                  |                 │
                                                  |                 ▼
                                                  |    ┌─────────────────────────┐
                                                  |    │ Return to TileManager   │
                                                  |    └─────────────────────────┘

    """
    def __init__(self, tilecache: Any) -> None:  # type: ignore[no-untyped-def]
        """
        Constructor :
            DynamicTileProvider(tilecache)
        Parameters :
            tilecache : Any

        DynamicTileProvider(tilecache) --> None

        Create a new DynamicTileProvider with the given TileCache.

        The tilecache parameter is the TileCache instance that this provider
        will use to store dynamically generated or retrieved tiles.
        """
        TileProvider.__init__(self, tilecache)

    ## set default values (derived classes may override these values)
    filext = 'png'
    tilesize = 256
    aspect_ratio = 1.0 ## width / height

    def _load_dynamic(self, tile_id: TileID, outfile: str) -> None:
        """
        Method :
            DynamicTileProvider._load_dynamic(tile_id, outfile)
        Parameters :
            tile_id : Tuple[str, int, int, int]
            outfile : str

        DynamicTileProvider._load_dynamic(tile_id, outfile) --> None

        Perform whatever actions necessary to load the tile identified by
        the given tile_id into the location given by outfile.
        """
        pass

    def _load(self, tile_id: TileID) -> Optional['QImage']:
        """
        Method :
            DynamicTileProvider._load(tile_id)
        Parameters :
            tile_id : Tuple[str, int, int, int]

        DynamicTileProvider._load(tile_id) --> QImage or None

        Load a tile, generating it dynamically if it doesn't exist locally.

        The tile_id tuple contains (media_id, tilelevel, row, col). This method
        first checks if the tile exists in the local tilestore. If not, it calls
        _load_dynamic() to generate or retrieve the tile. Finally, it loads the
        tile as a QImage and returns it.

        Implementation Notes:
            - Gets tile path from TileStore with create=True flag
            - Only calls _load_dynamic() if tile file doesn't exist
            - Uses QImage to load the tile after creation
            - Returns None if tile loading fails (logs exception)
            - Assumes tile is unavailable if any exception occurs
        """
        filename = TileStore.get_tile_path(
            tile_id, True, filext=self.filext)

        if not os.path.exists(filename):
            ## tile has not been retrieved yet
            self._load_dynamic(tile_id, filename)

        try:
            return QtGui.QImage(filename)
        except Exception:
            self._logger.exception("error loading tile, "
                "assuming it is unavailable")
            return None
