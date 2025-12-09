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

"""Dynamic tile provider for Barnsley's fern."""

from typing import Tuple, Any
import random

from PIL import Image

from .dynamictileprovider import DynamicTileProvider

class FernTileProvider(DynamicTileProvider):
    """
    Constructor :
        FernTileProvider(tilecache)
    Parameters :
        tilecache : TileCache

    FernTileProvider(tilecache) --> FernTileProvider

    FernTileProvider objects are used for generating tiles of Barnsley's
    fern iterated function system.

    This dynamic tile provider generates fractal images of Barnsley's fern
    using an iterated function system (IFS). The fern is created by randomly
    applying one of four affine transformations to points, with each
    transformation having a specific probability of being chosen.

    Implementation Notes:
        - Inherits from DynamicTileProvider
        - Uses four affine transformations with different probabilities:
            * rachis (stem): 1% probability
            * left hand first pinna: 7% probability
            * right hand first pinna: 7% probability
            * body of fern: 85% probability
        - Generates up to max_iterations (50000) points
        - Stops after max_points (10000) points are drawn on tile
        - Tiles are 256x256 pixels saved as PNG
        - Color is RGB (100, 170, 0) for a green fern appearance
    """
    def __init__(self, tilecache: Any) -> None:
        DynamicTileProvider.__init__(self, tilecache)


    filext = 'png'
    tilesize = 256
    aspect_ratio = 1.0

    max_iterations = 50000
    max_points = 10000
    transformations = [
        ## (probability, (a, b, c, d, e, f))
        ## x_n+1 = a*x_n + b*y_n + c
        ## y_n+1 = d*x_n + e*y_n + f

        ## for details about the transformations, see:
        ## <http://en.wikipedia.org/wiki/Barnsley's_fern>
        ## <http://books.google.com/books?id=oh7NoePgmOIC
        ##  &printsec=frontcover#PPA86,M1>
        ## <http://mathworld.wolfram.com/BarnsleysFern.html>
        ## <http://www.home.aone.net.au/~byzantium/ferns/fractal.html>

        ## rachis
        (0.01, ( 0.00,  0.00,  0.00,  0.00,  0.16,  0.00)),

        ## left hand first pinna
        (0.07, ( 0.20, -0.26,  0.00,  0.23,  0.22,  1.60)),

        ## right hand first pinna
        (0.07, (-0.15,  0.28,  0.00,  0.26,  0.24,  0.44)),

        ## body of fern
        (0.85, ( 0.85,  0.04,  0.00, -0.04,  0.85,  1.60)),
    ]
    color = (100, 170, 0)

    def __choose_transformation(self) -> Tuple[float, float, float, float, float, float]:
        """
        Method :
            FernTileProvider.__choose_transformation()
        Parameters :
            None

        FernTileProvider.__choose_transformation() --> Tuple[float, float, float, float, float, float]

        Randomly choose a transformation based on the probability of each
        transformation being chosen.

        This method implements probabilistic selection from the four fern
        transformations. A random value between 0 and 1 is generated, and
        transformations are tested in order until one is selected based on
        cumulative probability.

        Implementation Notes:
            - Generates random float in range [0, 1)
            - Iterates through transformations in order
            - Subtracts each probability from random value
            - Returns transformation when random value <= probability
            - Returns 6-tuple: (a, b, c, d, e, f) for affine transform
        """
        n = random.uniform(0,1)
        for probability, transformation in self.transformations:
            if n <= probability:
                break
            else:
                n -= probability
        return transformation


    def __transform(self, x: float, y: float) -> Tuple[float, float]:
        """
        Method :
            FernTileProvider.__transform(x, y)
        Parameters :
            x : float
            y : float

        FernTileProvider.__transform(x, y) --> Tuple[float, float]

        Randomly choose a transformation and apply it to x and y, returning
        the result as a tuple.

        This method applies one iteration of the fern's iterated function system.
        It selects a transformation using __choose_transformation() and applies
        the affine transformation to the input coordinates.

        Implementation Notes:
            - Calls __choose_transformation() to get transformation coefficients
            - Applies affine transformation: x' = a*x + b*y + c
            - Applies affine transformation: y' = d*x + e*y + f
            - Returns new coordinates as tuple (x', y')
        """
        t = self.__choose_transformation()
        x_new = t[0]*x + t[1]*y + t[2]
        y_new = t[3]*x + t[4]*y + t[5]
        return (x_new,y_new)


    def __draw_point(self, tile: Any, x: float, y: float, tilesize_units: float) -> None:
        """
        Method :
            FernTileProvider.__draw_point(tile, x, y, tilesize_units)
        Parameters :
            tile : Image
            x : float
            y : float
            tilesize_units : float

        FernTileProvider.__draw_point(tile, x, y, tilesize_units) --> None

        Draw the given point on the given tile.

        Converts fern coordinate space to pixel coordinates and draws a single
        pixel on the tile. The y-coordinate is inverted to match image coordinate
        system (origin at top-left).

        Preconditions:
            - 0.0 <= x <= tilesize_units
            - 0.0 <= y <= tilesize_units

        Implementation Notes:
            - Scales x from [0, tilesize_units] to [0, tilesize]
            - Clamps x to valid pixel range [0, tilesize-1]
            - Scales y from [0, tilesize_units] to [0, tilesize]
            - Inverts y-coordinate: pixel_y = tilesize - scaled_y
            - Clamps y to valid pixel range [0, tilesize-1]
            - Sets pixel color using self.color (green)
        """

        x = x * self.tilesize / tilesize_units
        x = min(int(x), self.tilesize-1)
        y = y * self.tilesize / tilesize_units
        y = min(int(self.tilesize - y), self.tilesize-1)

        tile.putpixel((x,y), self.color)


    def _load_dynamic(self, tile_id: Tuple[str, int, int, int], outfile: str) -> None:
        """
        Method :
            FernTileProvider._load_dynamic(tile_id, outfile)
        Parameters :
            tile_id : Tuple[str, int, int, int]
            outfile : str

        FernTileProvider._load_dynamic(tile_id, outfile) --> None

        Generate a tile of Barnsley's fern and save it to outfile.

        This method generates a fractal fern image for the specified tile by
        iterating the fern's IFS transformations. The tile coordinates (row, col)
        and tilelevel determine which portion of the fern to render. Points are
        generated starting from (0, 0) and transformed repeatedly, with points
        falling within the tile's boundaries being drawn.

        Implementation Notes:
            - Returns early if row/col are out of range for the tilelevel
            - Calculates tile boundaries in fern coordinate space (-5 to 5 for x, 0 to 10 for y)
            - Creates a black RGB image of size tilesize x tilesize
            - Iterates up to max_iterations times, starting from origin (0, 0)
            - Only draws points that fall within the tile boundaries
            - Stops after max_points are drawn to the tile
            - Saves the resulting tile as PNG to outfile
        """
        media_id, tilelevel, row, col = tile_id

        if row < 0 or col < 0 or \
           row > 2**tilelevel - 1 or col > 2**tilelevel - 1:
            ## row,col out of range
            return

        tilesize_units = 10.0 * 2**-tilelevel
        x = col * tilesize_units
        y = row * tilesize_units

        ## the corners of the tile are:
        ## (x1,y2) +----+ (x2,y2)
        ##         |    |
        ## (x1,y1) +----+ (x2,y1)

        x1 = x - 5.0
        y2 = 10.0 - y
        x2 = x1 + tilesize_units
        y1 = y2 - tilesize_units

        tile = Image.new('RGB', (self.tilesize,self.tilesize))

        num_points = 0

        x = 0.0
        y = 0.0
        for i in range(self.max_iterations):
            if x1 <= x <= x2 and y1 <= y <= y2:
                self.__draw_point(
                    tile, x-x1, y-y1, tilesize_units)

                num_points += 1
                if num_points > self.max_points:
                    break

            x,y = self.__transform(x,y)

        tile.save(outfile)
