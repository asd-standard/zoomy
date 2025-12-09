.. Tiling System Documentation

Tiling System
=============

This document provides a comprehensive overview of the tiling system architecture,
explaining how large images are converted into pyramidal tile structures and how 
such tiles are stored to be then retrieved and rendered on the interface.

Overview
--------

The tiling system is responsible for:

1. Converting large images into pyramidal tile structures
2. Storing tiles on disk for persistence
3. Caching tiles in memory for fast access
4. Providing tiles on demand for display

The system uses a **tile pyramid** structure where each level represents the image
at a different zoom level. Level 0 contains a single overview tile, and higher
levels contain progressively more tiles at higher resolutions.

Architecture
------------

The tiling system consists of the following components:

.. code-block:: text

    ┌─────────────────────────────────────────────────────────────────┐
    │                        TileManager                              │
    │  (Coordinates tile requests, caching, and provider routing)     │
    └─────────────────────────────────────────────────────────────────┘
                │                                    │
                ▼                                    ▼
    ┌─────────────────────┐              ┌─────────────────────┐
    │     TileCache       │              │    TileProviders    │
    │  (Memory caching)   │              │ (Tile loading/gen)  │
    └─────────────────────┘              └─────────────────────┘
                                                    │
                                          ┌─────────┼──────────────┐
                                          ▼                        ▼        
                              ┌───────────────────┐    ┌───────────────────┐
                              │StaticTileProvider │    │DynamicTileProvider│  
                              │ Providers         │    │                   │
                              │ (tiled images)    │    │ (Procedural gen)  │
                              └───────────────────┘    └───────────────────┘ 
                                      │                    │
                                      │                    ▼
                                      │         ┌─────────────────┐
                                      │_______  │   TileStore     │
                                                │ (Disk storage)  │
                                                └─────────────────┘
                      
Component Details
-----------------

Tile
~~~~

The ``Tile`` class is a wrapper around image data (QImage/PIL) providing operations
for manipulation and rendering.

**Key Operations:**

- ``crop(bbox)``: Extract a rectangular region from the tile
- ``resize(width, height)``: Scale the tile to new dimensions
- ``save(filename)``: Write the tile to disk
- ``draw(painter, x, y)``: Render the tile using a QPainter

**Factory Functions:**

- ``new(width, height)``: Create an empty tile
- ``fromstring(string, width, height)``: Create a tile from raw pixel data
- ``merged(t1, t2, t3, t4)``: Combine four tiles into one (2×2 grid)

Tiler
~~~~~

The ``Tiler`` class converts source images into pyramidal tile structures. It is an
abstract base class that runs as a separate thread.

**Tile Pyramid Structure:**

For an image with dimensions ``W × H`` and tile size ``T``:

- **Maximum Tile Level**: ``maxtilelevel = ceil(log2(max(W, H) / T))``
- **Tiles at Level L**: ``ceil(W / (T × 2^(maxtilelevel - L))) × ceil(H / (T × 2^(maxtilelevel - L)))``

**Example:** A 1024×1024 image with 256×256 tiles:

.. code-block:: text

    Level 0: 1 tile   (1×1)   - Overview
    Level 1: 4 tiles  (2×2)   - 2× zoom
    Level 2: 16 tiles (4×4)   - Full resolution

    Total: 21 tiles

**Tiling Process:**

1. **Calculate Dimensions**: Determine the number of tiles and pyramid levels
2. **Read Scanlines**: Read the source image row by row using ``_scanline()``
3. **Create Base Tiles**: Divide rows into tiles at the maximum level
4. **Merge Upward**: Combine 2×2 tile groups to create lower-level tiles
5. **Save Tiles**: Write each tile to disk via TileStore
6. **Write Metadata**: Store image dimensions, tile size, and format

**Subclasses:**

Concrete implementations must provide the ``_scanline(y)`` method to read image data:

- ``VIPSTiler``: Uses libvips for memory-efficient processing of large images
- ``PPMTiler``: Reads PPM/PGM format images

TileStore
~~~~~~~~~

The ``TileStore`` module manages disk-based tile storage and metadata persistence.

**Directory Structure:**

Tiles are organized by media ID using SHA1 hashing::

    ~/.pyzui/tilestore/
    └── <sha1_hash_of_media_id>/
        ├── metadata
        ├── 00/
        │   └── 00_000000_000000.jpg
        ├── 01/
        │   ├── 01_000000_000000.jpg
        │   ├── 01_000000_000001.jpg
        │   ├── 01_000001_000000.jpg
        │   └── 01_000001_000001.jpg
        └── 02/
            └── ...

**Tile Path Format:**

``<tilelevel>/<tilelevel>_<row>_<col>.<ext>``

Where row and column are zero-padded to 6 digits.

**Metadata File Format:**

Tab-separated values with type information::

    width	1024	int
    height	768	int
    tilesize	256	int
    filext	jpg	str
    maxtilelevel	2	int

**Key Functions:**

- ``get_media_path(media_id)``: Get the directory for a media's tiles
- ``get_tile_path(tile_id, filext)``: Get the file path for a specific tile
- ``load_metadata(media_id)``: Load metadata from disk into memory
- ``get_metadata(media_id, key)``: Retrieve a metadata value
- ``write_metadata(media_id, **kwargs)``: Write metadata to disk
- ``tiled(media_id)``: Check if a media has been fully tiled
- ``get_tilestore_stats()``: Get statistics about the tilestore
- ``cleanup_old_tiles(max_age_days)``: Remove old tile directories

TileCache
~~~~~~~~~

The ``TileCache`` class provides in-memory LRU (Least Recently Used) caching of tiles.

**Features:**

- **Size-Based Eviction**: Automatically evicts tiles when ``maxsize`` is exceeded
- **Age-Based Expiration**: Optional ``maxage`` parameter for time-based eviction
- **Access-Based Expiration**: Tiles can expire after N accesses via ``maxaccesses``
- **Immortal Tiles**: Level 0 tiles (overview) are never evicted
- **Thread Safety**: RLock protects concurrent access

**Dual-Tier Caching:**

The TileManager uses two caches:

1. **Permanent Cache (80%)**: Stores tiles loaded from disk
2. **Temporary Cache (20%)**: Stores synthesized/cut tiles that can be regenerated

TileManager
~~~~~~~~~~~

The ``TileManager`` module coordinates tile requests between providers and caches.

**Initialization:**

.. code-block:: python

    tilemanager.init(
        total_cache_size=500,     # Total cache size in MB
        auto_cleanup=True,        # Enable automatic cleanup
        cleanup_max_age_days=7    # Remove tiles older than 7 days
    )

**Key Functions:**

- ``load_tile(tile_id)``: Request a tile to be loaded (asynchronous)
- ``get_tile(tile_id)``: Get a tile from cache (raises if not available)
- ``get_tile_robust(tile_id)``: Get tile with fallback to synthesis
- ``cut_tile(tile_id)``: Synthesize a tile from parent tiles
- ``tiled(media_id)``: Check if media is tiled
- ``get_metadata(media_id, key)``: Get metadata for a media
- ``purge(media_id=None)``: Remove tiles from providers and cache

**Tile Synthesis (cut_tile):**

When a tile is not available, it can be synthesized from parent tiles:

.. code-block:: text

    Requested: (media, level=2, row=3, col=5)
    Parent:    (media, level=1, row=1, col=2)

    Parent tile is cropped to the correct quadrant:
    ┌─────┬─────┐
    │ 0,0 │ 0,1 │  ← row=3 is odd, col=5 is odd
    ├─────┼─────┤     so we take bottom-right quadrant
    │ 1,0 │*1,1*│
    └─────┴─────┘

    Then resized to full tile dimensions.

**Negative Tile Levels:**

Negative tile levels represent zoomed-out views beyond level 0:

- Level -1: 50% of level 0
- Level -2: 25% of level 0
- etc.

These are created by resizing the (0,0,0) tile.

TileProviders
~~~~~~~~~~~~~

Tile providers are responsible for loading or generating tiles.

**Base Class: TileProvider**

Abstract base class running as a daemon thread. Provides:

- ``request(tile_id)``: Queue a tile load request (LIFO order)
- ``load(tile_id)``: Abstract method to load/generate a tile
- ``purge(media_id=None)``: Cancel pending requests

**StaticTileProvider**

Loads pre-tiled images from the TileStore::

    tile = tilestore.load_tile(tile_id)
    cache[tile_id] = tile

**DynamicTileProvider**

Generates tiles procedurally (e.g., fractals, maps). Subclasses:

- ``FernTileProvider``: Barnsley fern fractal
- ``MandelbrotTileProvider``: Mandelbrot set
- ``OSMTileProvider``: OpenStreetMap tiles

Tile ID Format
--------------

A tile is identified by a 4-tuple::

    (media_id, tilelevel, row, col)

- **media_id**: String identifying the source image or dynamic content
- **tilelevel**: Integer pyramid level (0 = overview, higher = more detail)
- **row**: Integer row index (0-based, top to bottom)
- **col**: Integer column index (0-based, left to right)

**Examples:**

- ``("photo.jpg", 0, 0, 0)``: Overview tile of photo.jpg
- ``("photo.jpg", 2, 3, 5)``: Detail tile at level 2, row 3, column 5
- ``("dynamic:fern", 10, 512, 256)``: Procedurally generated fern tile

Tile Request Flow
-----------------

The following sequence describes how a tile is requested and delivered:

.. code-block:: text

    1. Application requests tile via get_tile_robust(tile_id)
                    │
                    ▼
    2. TileManager checks permanent cache
       ├─ Cache HIT → Return tile
       └─ Cache MISS → Continue
                    │
                    ▼
    3. TileManager routes to appropriate provider
       ├─ "dynamic:*" → DynamicTileProvider
       └─ Otherwise  → StaticTileProvider
                    │
                    ▼
    4. Provider loads/generates tile
       ├─ StaticTileProvider reads from TileStore
       └─ DynamicTileProvider generates procedurally
                    │
                    ▼
    5. Tile is stored in cache
                    │
                    ▼
    6. Tile is returned to application

**Fallback Synthesis:**

If a tile is not available (TileNotLoaded/TileNotAvailable), the system
attempts to synthesize it from parent tiles via ``cut_tile()``.

Performance Considerations
--------------------------

**Memory Management:**

- The cache uses approximately 80/20 split between permanent and temporary tiles
- LRU eviction prevents unbounded memory growth
- Level 0 tiles are immortal (always kept) as they're frequently accessed

**Disk I/O:**

- Tiles are loaded lazily on demand
- LIFO queue prioritizes recently requested tiles
- Disk lock prevents concurrent write conflicts

**Threading:**

- TileProviders run as daemon threads
- RLocks protect shared state (caches, metadata)
- Multiple providers can run concurrently

**Recommended Settings:**

- **Cache Size**: 200-500 MB for typical usage
- **Tile Size**: 256×256 for balance of overhead vs. granularity
- **Auto-Cleanup**: Enable with 7-30 day retention for disk management

Exception Handling
------------------

The tiling system defines three exception types:

**MediaNotTiled**

Raised when accessing a media that hasn't been tiled yet::

    try:
        tile = tilemanager.get_tile(tile_id)
    except MediaNotTiled:
        # Need to tile the image first
        start_tiling(media_path)

**TileNotLoaded**

Raised when a tile exists but isn't in the cache yet::

    try:
        tile = tilemanager.get_tile(tile_id)
    except TileNotLoaded:
        # Request tile load and wait or use cut_tile
        tilemanager.load_tile(tile_id)

**TileNotAvailable**

Raised when a tile cannot be loaded (file missing, error, or ``None`` in cache)::

    try:
        tile = tilemanager.get_tile(tile_id)
    except TileNotAvailable:
        # Tile doesn't exist, synthesize from parent
        tile = tilemanager.cut_tile(tile_id)[0]

**Robust Access:**

Use ``get_tile_robust()`` for automatic fallback handling::

    tile = tilemanager.get_tile_robust(tile_id)
    # Never raises TileNotLoaded or TileNotAvailable

Usage Example
-------------

**Tiling an Image:**

.. code-block:: python

    from pyzui.tilesystem.converters.vipsconverter import VIPSTiler
    from pyzui.tilesystem import tilestore, tilemanager

    # Initialize the tilemanager
    tilemanager.init(total_cache_size=500, auto_cleanup=True)

    # Tile an image
    tiler = VIPSTiler("large_photo.tif", media_id="photo1", tilesize=256)
    tiler.start()  # Run in background thread
    tiler.join()   # Wait for completion

    if tiler.error:
        print(f"Tiling failed: {tiler.error}")
    else:
        print(f"Tiled successfully: {tilestore.get_metadata('photo1', 'maxtilelevel')} levels")

**Retrieving Tiles:**

.. code-block:: python

    # Request tiles for display
    tile_id = ("photo1", 2, 0, 0)

    # Ensure tile is loaded
    tilemanager.load_tile(tile_id)

    # Get tile (may need retry if loading is async)
    try:
        tile = tilemanager.get_tile(tile_id)
        tile.draw(painter, x, y)
    except TileNotLoaded:
        # Show placeholder, tile is loading
        pass

**Working with Dynamic Content:**

.. code-block:: python

    # Dynamic tiles are always "tiled"
    assert tilemanager.tiled("dynamic:fern") == True

    # Get procedurally generated tile
    tile = tilemanager.get_tile_robust(("dynamic:fern", 10, 100, 200))

    # Metadata for dynamic content
    tilesize = tilemanager.get_metadata("dynamic:fern", "tilesize")  # 256
    maxlevel = tilemanager.get_metadata("dynamic:fern", "maxtilelevel")  # 18

API Reference
-------------

For detailed API documentation, see:

- :doc:`pyzui/tile`
- :doc:`pyzui/tiler`
- :doc:`pyzui/tilestore`
- :doc:`pyzui/tilecache`
- :doc:`pyzui/tilemanager`
- :doc:`pyzui/tileprovider`
