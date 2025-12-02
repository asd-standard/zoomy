"""Tile provider classes for loading tiles into TileCache objects."""

from .tileprovider import TileProvider
from .statictileprovider import StaticTileProvider
from .dynamictileprovider import DynamicTileProvider
from .osmtileprovider import OSMTileProvider
from .globalmosaictileprovider import GlobalMosaicTileProvider
from .mandeltileprovider import MandelTileProvider
from .ferntileprovider import FernTileProvider

__all__ = [
    'TileProvider',
    'StaticTileProvider',
    'DynamicTileProvider',
    'OSMTileProvider',
    'GlobalMosaicTileProvider',
    'MandelTileProvider',
    'FernTileProvider',
]
