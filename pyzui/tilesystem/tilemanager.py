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

"""The TileManager is responsible for requesting tiles from TileProviders,
caching them in memory, and providing them to MediaObjects when requested
to do so.

It is also responsible for creating new tiles from available ones when
no tiles of the requested resolution are available.
"""

from typing import Optional, Tuple, Any

from . import tilestore as TileStore
from .tilestore import TileCache
from .tileproviders import (
    StaticTileProvider,
    FernTileProvider
)
from pyzui.logger import get_logger

# Module-level global variables (initialized by init())
__tilecache = None
__temptilecache = None
__tp_static = None
__tp_dynamic = {}
__logger = None

def init(total_cache_size: int = 1024, auto_cleanup: bool = True, cleanup_max_age_days: int = 3) -> None:
    """
    Function :
        init(total_cache_size, auto_cleanup, cleanup_max_age_days)
    Parameters :
        total_cache_size : int
            - Total cache size: number of total cached tiles (default: 1024)
        auto_cleanup : bool
            - Enable automatic cleanup of old tiles (default: True)
        cleanup_max_age_days : int
            - Maximum age in days for tiles (default: 3)

    init(total_cache_size, auto_cleanup, cleanup_max_age_days) --> None

    Initialise the TileManager. This **must** be called before any other
    functions are called.

    The central coordinator that:
        - Routes tile requests to appropriate providers
        - Manages two-tier caching (80% permanent / 20% temporary)
        - Synthesizes missing tiles from available ones via cut_tile()
        - Key methods: load_tile(), get_tile(), get_tile_robust()

    
    """

    global __tilecache, __temptilecache, __tp_static, __tp_dynamic, __logger

    #tile cache reserved for static tile provider.
    __tilecache =     TileCache(0.8 * total_cache_size)
    
    #tile cache reserved for dynamic tile provider
    __temptilecache = TileCache(0.2 * total_cache_size)

    #creates a tileproviders.tileprovider(tilecache: Any) thread instance 
    #and starts it
    __tp_static = StaticTileProvider(__tilecache)
    __tp_static.start()

    #define dynamic tile providers instances list
    __tp_dynamic = {
        'dynamic:fern': FernTileProvider(__tilecache),
    }
    #Starts dynamic tile providers thread instances
    for tp in list(__tp_dynamic.values()):
        tp.start()

    #set up TileManager logger
    __logger = get_logger("TileManager")

    # Run automatic cleanup if enabled
    if auto_cleanup:
        __logger.info('Running tilestore cleanup on startup')
        TileStore.auto_cleanup(max_age_days=cleanup_max_age_days, enable=True)
    else:
        __logger.debug('Tilestore auto cleanup disabled')

def load_tile(tile_id: Tuple[str, int, int, int]) -> None:
    """
    Function :
        load_tile(tile_id)
    Parameters :
        tile_id : Tuple[str, int, int, int]

    load_tile(tile_id) --> None

    Request that the tile identified by `tile_id` be loaded into the
    tilecache.
    """
    
    media_id = tile_id[0]

    if media_id in __tp_dynamic:
        __tp_dynamic[media_id].request(tile_id)
    else:
        __tp_static.request(tile_id)

def get_tile(tile_id: Tuple[str, int, int, int]) -> Any:
    """
    Function :
        get_tile(tile_id)
    Parameters :
        tile_id : Tuple[str, int, int, int]

    get_tile(tile_id) --> Tile

    Return the requested tile identified by `tile_id`.

    If the tile is not available in the tilecache, one of three errors will be
    raised: :class:`MediaNotTiled`, :class:`TileNotLoaded`, or :class:`TileNotAvailable`
    """

    if tile_id[1] < 0:
        ## negative tilelevel
        raise TileNotAvailable

    try:
        tile = __tilecache[tile_id]
    except KeyError:
        media_id = tile_id[0]
        if tiled(media_id):
            load_tile(tile_id)
            raise TileNotLoaded
        else:
            raise MediaNotTiled

    if tile:
        return tile
    else:
        raise TileNotAvailable

def cut_tile(tile_id: Tuple[str, int, int, int], tempcache: int = 0) -> Tuple[Any, bool]:
    """
    Function :
        cut_tile(tile_id, tempcache)
    Parameters :
        tile_id : Tuple[str, int, int, int]
        tempcache : int

    cut_tile(tile_id, tempcache) --> Tuple[Tile, bool]

    Create a tile from resizing and cropping those loaded into the tile
    cache. Returns a tuple containing the tile, and a bool `final` which is
    False iff the tile is not the greatest resolution possible and should
    therefore not be cached indefinitely.

    If `tempcache` > 0, then tiles with `final`=False will cached in the
    :class:`TileCache`, but will expire after they have been accessed `tempcache` times.

    This function should only be called if a :class:`TileNotLoaded` or
    :class:`TileNotAvailable` error has been encountered.

    Precondition: the (0,0,0) tile exists for the given media
    Precondition: the requested tile doesn't fall outside the bounds of the
    image
    """

    media_id, tilelevel, row, col = tile_id
    tilesize = get_metadata(media_id, 'tilesize')

    if tempcache <= 0:
        ## purge temporary tiles
        __temptilecache.purge()

    if tilelevel < 0:
        ## resize the (0,0,0) tile
        tile000 = __tilecache[media_id,0,0,0]
        scale = 2**tilelevel
        tile = tile000.resize(
            int(tile000.size[0] * scale), int(tile000.size[1] * scale))
        final = True
    else:
        big_tile_id = (media_id, tilelevel-1, row//2, col//2)
        try:
            return get_tile(tile_id), True
        except TileNotLoaded:
            final = False
            try:
                ## check if there is a temporary cut tile in the cache
                return __temptilecache[tile_id], False
            except KeyError:
                ## don't worry if there isn't
                pass
            big_tile = cut_tile(big_tile_id)[0]
        except TileNotAvailable:
            big_tile, final = cut_tile(big_tile_id)

        if col % 2 == 0:
            x1 = 0
            x2 = min(tilesize/2, big_tile.size[0])
        else:
            x1 = tilesize/2
            x2 = big_tile.size[0]

        if row % 2 == 0:
            y1 = 0
            y2 = min(tilesize/2, big_tile.size[1])
        else:
            y1 = tilesize/2
            y2 = big_tile.size[1]

        tile = big_tile.crop((x1, y1, x2, y2))
        tile = tile.resize(2*tile.size[0], 2*tile.size[1])

    if final:
        __tilecache[tile_id] = tile
    elif tempcache > 0:
        __temptilecache.insert(tile_id, tile, tempcache)

    return tile, final

def get_tile_robust(tile_id: Tuple[str, int, int, int]) -> Any:
    """
    Function :
        get_tile_robust(tile_id)
    Parameters :
        tile_id : Tuple[str, int, int, int]

    get_tile_robust(tile_id) --> Tile

    Will try returning the result of :func:`get_tile`, and if that fails will
    return the result of :func:`cut_tile`.

    This function will not raise :class:`TileNotLoaded` or :class:`TileNotAvailable`, but may
    raise :class:`MediaNotTiled`.
    """
    try:
        return get_tile(tile_id)
    except (TileNotLoaded, TileNotAvailable):
        return cut_tile(tile_id)[0]

def tiled(media_id: str) -> bool:
    """
    Function :
        tiled(media_id)
    Parameters :
        media_id : str

    tiled(media_id) --> bool

    Returns True iff the media identified by `media_id` has been tiled.

    Will always return True for dynamic media.
    """
    return media_id.startswith('dynamic:') or TileStore.tiled(media_id)

def get_metadata(media_id: str, key: str) -> Optional[Any]:
    """
    Function :
        get_metadata(media_id, key)
    Parameters :
        media_id : str
        key : str

    get_metadata(media_id, key) --> object or None

    Return the value associated with the given metadata `key` for the given
    `media_id`, None if there is no such value.
    """
    if media_id in __tp_dynamic:
        tp = __tp_dynamic[media_id]
        if   key == 'filext':       return tp.filext
        elif key == 'tilesize':     return tp.tilesize
        elif key == 'aspect_ratio': return tp.aspect_ratio
        # Dynamic tile providers have infinite zoom levels
        # Set reasonable defaults for infinite tiled media
        elif key == 'maxtilelevel': return 18  # OSM typically goes to level 18-19
        elif key == 'width':        return tp.tilesize * (2 ** 18)  # Based on maxtilelevel
        elif key == 'height':       return tp.tilesize * (2 ** 18)  # Based on maxtilelevel
        else: return None
    else:
        return TileStore.get_metadata(media_id, key)

def purge(media_id: Optional[str] = None) -> None:
    """
    Function :
        purge(media_id)
    Parameters :
        media_id : Optional[str]

    purge(media_id) --> None

    Purge the specified *media_id* from the *TileProviders*. If *media_id*
    is omitted then all media will be purged.

    Precondition: the media to be purged should not be active (i.e. no
    *MediaObjects* for the media should exist).
    """
    __tp_static.purge(media_id)
    for tp in list(__tp_dynamic.values()):
        tp.purge(media_id)

def pause() -> None:
    """
    Function :
        pause()
    Parameters :
        None

    pause() --> None

    Pause all TileProvider threads. This should be called before running
    converter processes to avoid conflicts between pyvips and tile loading.
    """
    if __tp_static:
        __tp_static.pause()
    for tp in list(__tp_dynamic.values()):
        tp.pause()
    if __logger:
        __logger.debug("all tile providers paused")

def resume() -> None:
    """
    Function :
        resume()
    Parameters :
        None

    resume() --> None

    Resume all TileProvider threads after they were paused.
    """
    if __tp_static:
        __tp_static.resume()
    for tp in list(__tp_dynamic.values()):
        tp.resume()
    if __logger:
        __logger.debug("all tile providers resumed")

class MediaNotTiled(Exception):
    """Exception for when tiles are requested from a media that has not been
    tiled yet.

    This exception will never be thrown when requesting a tile from a dynamic
    media.
    """
    pass

class TileNotLoaded(Exception):
    """Exception for when tiles are requested before they have been loaded into
    the tile cache."""
    pass

class TileNotAvailable(Exception):
    """Exception for when an attempt to load the requested tile has previously
    failed."""
    pass
