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
5. Pausing and resuming tile providers during process-based conversion
6. Cleaning up stale tile data automatically

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
    │  • init() / shutdown() — lifecycle management                   │
    │  • pause() / resume() — provider control                        │
    └─────────────────────────────────────────────────────────────────┘       
                │                                    │                        
                ▼                                    ▼                        
    ┌─────────────────────┐              ┌─────────────────────┐              
    │     TileCache       │              │    TileProviders    │              
    │  (Memory caching)   │              │ (Tile loading/gen)  │              
    │  2-tier: perm/temp  │              └─────────────────────┘              
    └─────────────────────┘                         │                         
                                           ┌─────────┼──────────────┐          
                                           ▼                        ▼           
                               ┌───────────────────┐    ┌───────────────────┐   
                               │StaticTileProvider │    │DynamicTileProvider│   
                               │ (tiled images)    │    │(Procedural gen)   │   
                               │ • FernTileProvider│    │                   │   
                               └───────────────────┘    └───────────────────┘   
                                       │                    │                   
                                       │                    ▼                   
                                       │            ┌───────────────────┐         
                                        ──────────🢒 │   TileStore       │          
                                                    │  (Disk storage)   │         
                                                    └───────────────────┘  
                                                    │
                                                    ▼
                                            ┌───────────────────┐
                                            │ cleanuptilestore  │
                                            │  (CLI + auto)     │
                                            └───────────────────┘

    **Tile request and loading flow**

    ┌─────────────────────────┐
    │ MediaObject needs tile  │
    │ at specific zoom level  │
    └────────────┬────────────┘
                 │
                 ▼
    ┌─────────────────────────┐
    │ TileManager.get_tile()  │
    │ or get_tile_robust()    │
    └────────────┬────────────┘
                 │
                 ▼
    ┌─────────────────────────┐
    │ Check TileCache         │
    │ (in-memory LRU cache)   │
    └────────────┬────────────┘
                 │
            ┌────┴────┐
            │         │
        CACHE HIT   CACHE MISS
            │         │
            ▼         ▼
      ┌──────────┐ ┌────────────────────┐
      │ Return   │ │ load_tile() —      │
      │ cached   │ │ Queue tile request │
      │ tile     │ │ to provider (LIFO) │
      └──────────┘ └─────────┬──────────┘
                             │
                             ▼
                   ┌─────────────────────┐
                   │ TileProvider Thread │
                   │ processes request   │
                   └─────────┬───────────┘
                             │
                             ▼
                   ┌────────────────────┐
                   │ Check TileStore    │
                   │ (disk cache)       │
                   └─────────┬──────────┘
                             │
                        ┌────┴────┐
                        │         │
                    FOUND     NOT FOUND
                        │         │
                        ▼         ▼
                  ┌─────────┐ ┌──────────┐
                  │ Load    │ │ Generate │
                  │ from    │ │ or load  │
                  │ disk    │ │ from src │
                  └────┬────┘ └─────┬────┘
                       └─────┬──────┘
                             ▼
                   ┌─────────────────────┐
                   │ Store in TileCache  │
                   └─────────┬───────────┘
                             ▼
                   ┌─────────────────────┐
                   │ Save to TileStore   │
                   │ (if static provider)│
                   └─────────┬───────────┘
                             ▼
                   ┌────────────────────┐
                   │ Return tile        │
                   └────────────────────┘

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
abstract base class that runs as a separate thread and uses an internal
``ThreadPoolExecutor`` for parallel tile creation within each row.

**Tile Pyramid Structure:**

For an image with dimensions ``W × H`` and tile size ``T``:

- **T (tile size)**: The width and height of each square tile in pixels (typically 256×256)
- **W**: Image width in pixels
- **H**: Image height in pixels

**Maximum Tile Level Formula:**

``maxtilelevel = ceil(log2(max(W, H) / T))``

This formula calculates how many pyramid levels are needed to represent the full-resolution image:

- ``max(W, H) / T``: How many tiles would fit along the longest dimension at full resolution
- ``log2(...)``: The logarithm base-2 tells us how many times we need to divide by 2 to get down to 1 tile. Since each pyramid level halves the resolution, this gives us the number of levels needed.
- ``ceil(...)``: The ceiling function rounds up to the nearest integer, ensuring we have enough levels even if the division isn't exact (e.g., ``ceil(2.3) = 3``, ``ceil(4.0) = 4``)

**Tiles at Level L Formula:**

``ceil(W / (T × 2^(maxtilelevel - L))) × ceil(H / (T × 2^(maxtilelevel - L)))``

This formula calculates how many tiles exist at a specific pyramid level:

- ``2^(maxtilelevel - L)``: The scaling factor - how much smaller level L is compared to the maximum level

  - At ``L = maxtilelevel`` (full resolution): ``2^0 = 1`` (no scaling)
  - At ``L = maxtilelevel - 1``: ``2^1 = 2`` (half resolution, 2× smaller)
  - At ``L = 0`` (overview): ``2^maxtilelevel`` (smallest, 2^maxtilelevel× smaller)

- ``T × 2^(maxtilelevel - L)``: The effective size each tile covers at level L
- ``W / (T × 2^(...))``: How many tiles fit horizontally
- ``H / (T × 2^(...))``: How many tiles fit vertically
- ``ceil(...)``: Round up to ensure partial tiles are counted

**Example:** A 1024×1024 image with 256×256 tiles::

    Level 0: 1 tile   (1×1)   - Overview (each tile covers 1024×1024 pixels)
    Level 1: 4 tiles  (2×2)   - Half resolution (each tile covers 512×512 pixels)
    Level 2: 16 tiles (4×4)   - Full resolution (each tile covers 256×256 pixels)

    Total: 1 + 4 + 16 = 21 tiles

**Tiling Process:**

1. **Calculate Dimensions**: Determine the number of tiles and pyramid levels
2. **Read Scanlines**: Read the source image row by row using ``_scanchunk()``
3. **Create Base Tiles**: Divide rows into tiles at the maximum level using a
   ``ThreadPoolExecutor`` per row for parallel column processing
4. **Merge Upward**: Combine 2×2 tile groups to create lower-level tiles
5. **Save Tiles**: Write each tile to disk via TileStore. Each tile save
   increments the progress counter: ``progress = saved_count / numtiles``
6. **Write Metadata**: Store image dimensions, tile size, and format

**Concrete Subclasses:**

- ``PPMTiler``: Reads PPM/PGM format images. Provides ``_scanchunk()`` as a
  callable attribute that reads ``bytes_per_pixel * width`` bytes at a time.
  Includes ``read_ppm_header()`` (validates P6 format, maxval=255) and a
  ``__del__`` for output file cleanup.

**Extension Points:**

Subclasses must provide these instance attributes (declared but uninitialized
in the base class):

- ``_width``: Image width in pixels
- ``_height``: Image height in pixels
- ``_bytes_per_pixel``: Number of color channels (1 for grayscale, 3 for RGB)
- ``_scanchunk``: Callable that returns raw pixel data for the next row

**Parallel Tile Processing:**

Within each row, tiles are created in parallel using a ``ThreadPoolExecutor``:

.. code-block:: python

    # In Tiler.__tiles(), for each row:
    workers = min(numtiles_across, cpu_count())
    with ThreadPoolExecutor(max_workers=workers) as executor:
        args = [(self, row, col, tilelevel, ...) for col in range(numtiles_across)]
        for tile_data in executor.map(_make_tile, args):
            __savetile(tile_data, tilelevel, row, col)

The ``_make_tile()`` module-level function creates a ``Tile`` from raw pixel data
via ``Tile.fromstring()`` in a thread-safe manner (no Qt objects are constructed
on worker threads). The executor is shut down in a ``finally`` block to ensure
cleanup even on errors.

**Progress Tracking:**

The ``progress`` property returns a 0.0–1.0 float computed as
``saved_tiles / total_tiles``. Each successful ``__savetile()`` call increments
the counter, providing smooth progress indication during the tiling phase.

Process-Based Tiling (tilerrunner)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``tilerrunner`` module provides process-based tiling execution for parallel
image tiling, avoiding threading conflicts between pyvips, TileManager threads,
and Qt. This is the **recommended** approach for tiling — the thread-based
``Tiler`` class is a legacy API for direct use only.

**Architecture:**

The ``tilerrunner`` module uses ``ProcessPoolExecutor`` with ``'spawn'`` context
(default, for safety). The context can be overridden via the ``PYZUI_MP_CONTEXT``
environment variable (see :doc:`../pyzui/tilerrunner` for details).

**Key Functions:**

.. code-block:: python

    from pyzui.tilesystem.tiler import tilerrunner

    # Initialize process pool (optional, auto-initialized on first use)
    tilerrunner.init(max_workers=2)

    # Submit tiling job
    future = tilerrunner.submit_tiling(
        infile='image.ppm',
        media_id='my_image',
        filext='jpg',
        tilesize=256
    )

    # Create handle for tracking
    handle = tilerrunner.TilingHandle(future, 'image.ppm', 'my_image')

    # Check progress
    if handle.progress == 1.0:
        if handle.error:
            print(f"Tiling failed: {handle.error}")
        else:
            print("Tiling complete!")

    # Shutdown pool when done
    tilerrunner.shutdown()

**TilingHandle Class:**

The ``TilingHandle`` wraps a ``Future`` and provides a compatible interface
with the thread-based ``Tiler`` class:

- ``progress``: Returns 0.0 while running and 1.0 when done
- ``error``: Error message if tiling failed, None otherwise
- ``is_alive()``: Returns True if tiling is still running
- ``join(timeout)``: Wait for tiling to complete

.. note::

   Process-based tilers report progress as 0.0 (running) or 1.0 (complete),
   since subprocess progress cannot be monitored incrementally. The
   ``TilingHandle`` wraps the ``Future`` and provides a compatible interface
   for integration with ``TiledMediaObject``.

**Process Isolation:**

Tilers run in separate processes via ``ProcessPoolExecutor``, providing complete isolation:

1. No threading conflicts with TileManager threads
2. Each pyvips instance runs in its own memory space
3. True parallel tiling (multiple images can be tiled simultaneously)
4. No deadlocks from pyvips internal threading

**Integration with TiledMediaObject:**

TiledMediaObject automatically uses process-based tiling via ``tilerrunner``
when converting and tiling media files. The conversion and tiling pipeline is:

1. Converter runs in separate process via ``converterrunner``
2. Output PPM file is passed to ``tilerrunner``
3. Tiling runs in separate process
4. Progress is tracked across both conversion and tiling phases

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
- ``get_tile_path(tile_id, filext, mkdirp, prefix)``: Get the file path for a specific tile.
  ``mkdirp=True`` creates parent directories (used by Tiler for output).
  ``prefix`` overrides the media directory root (for custom output paths).
- ``load_metadata(media_id)``: Load metadata from disk into memory. Uses a
  lock-free fast path with double-check locking inside ``disk_lock`` for
  on-demand loading.
- ``get_metadata(media_id, key)``: Retrieve a metadata value
- ``write_metadata(media_id, **kwargs)``: Write metadata to disk
- ``tiled(media_id)``: Check if a media has been fully tiled
- ``get_tilestore_stats()``: Get statistics about the tilestore
- ``get_directory_size(path)``: Calculate total disk usage for a directory
- ``cleanup_old_tiles(max_age_days, dry_run)``: Remove old tile directories.
  ``dry_run=True`` reports what would be deleted without actually removing files.
- ``auto_cleanup(max_age_days, enable, collect_stats)``: Automatic cleanup with statistics

**Automatic Cleanup System:**

The tilestore includes an automatic cleanup system that removes old tile
directories to manage disk space. Cleanup runs on application shutdown by
default to improve startup performance.

.. code-block:: python

    # Enable automatic cleanup (runs on shutdown by default)
    tilemanager.init(auto_cleanup=True, cleanup_max_age_days=3)

    # Disable automatic cleanup
    tilemanager.init(auto_cleanup=False)

    # Run cleanup manually
    from pyzui.tilesystem.tilestore import auto_cleanup
    stats = auto_cleanup(max_age_days=3, enable=True, collect_stats=False)

**Cleanup Behavior:**

- **Shutdown Cleanup (default)**: Runs when application exits gracefully
- **Manual Cleanup**: Can be triggered via command-line utility or ``auto_cleanup()``
- **Statistics Collection**: Can be disabled for faster cleanup

**Cleanup Statistics:**

When ``collect_stats=True``, the cleanup process logs:
1. Before cleanup: Media count, file count, total size
2. Cleanup results: Deleted media, freed space, errors
3. After cleanup: Media count, file count, total size

When ``collect_stats=False`` (fast mode, default for shutdown), only cleanup
results are logged.

**Command-line Options:**

.. code-block:: bash

    ./main.py --no-cleanup          # Disable cleanup entirely
    ./main.py --cleanup-age 30      # Clean tiles older than 30 days
    ./main.py --fast-cleanup        # Skip detailed statistics

Standalone Cleanup CLI (cleanuptilestore)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``cleanuptilestore.py`` module provides a standalone CLI utility for manual
tilestore cleanup, runnable via:

.. code-block:: bash

    python -m pyzui.tilesystem.tilestore.cleanuptilestore --age 7 --stats --verbose

**Command-line Options:**

.. code-block:: text

    --age N         Remove tiles older than N days (default: 3)
    --dry-run       Show what would be deleted without actually removing
    --stats         Collect and display before/after statistics
    --verbose       Enable detailed logging output
    --debug         Enable debug-level logging output

The utility initializes its own logger, runs ``cleanup_old_tiles()`` with the
specified options, and prints a formatted summary of the results.

TileCache
~~~~~~~~~

The ``TileCache`` class (at ``pyzui/tilesystem/tilestore/tilecache.py``) provides
in-memory LRU (Least Recently Used) caching of tiles.

**Features:**

- **Size-Based Eviction**: Automatically evicts tiles when ``maxsize`` is exceeded
- **Age-Based Expiration**: Optional ``maxage`` parameter for time-based eviction
- **Access-Based Expiration**: Tiles can expire after N accesses via ``maxaccesses``
  on ``insert()``
- **Immortal Tiles**: Level 0 tiles (overview) and ``None`` values are never evicted.
  The ``__mortal()`` method returns True only when both the tile is not None AND
  ``tile_id[1] != 0``. This prevents both overview tiles and pending/loading slots
  from being discarded.
- **Thread Safety**: RLock protects concurrent access

**Periodic Clean Daemon:**

When ``maxage`` is set, ``TileCache`` spawns a daemon thread that wakes every
``maxage / 3`` seconds and evicts age-expired tiles. The daemon is controlled
via a ``threading.Event`` for clean shutdown:

.. code-block:: python

    # In TileCache.__init__():
    self.__shutdown_event = threading.Event()

    # Shutdown called by TileManager.shutdown():
    def shutdown(self):
        self.__shutdown_event.set()   # Signal daemon to exit

The daemon thread checks the event each cycle and exits gracefully when signalled.

**Insert Method:**

The ``insert(tile_id, tile, maxaccesses=0)`` method adds a tile with optional
access-based expiration. When ``maxaccesses > 0``, the tile is evicted after
the specified number of accesses (reads) to the tile. This is used by
``cut_tile()`` with ``tempcache`` for synthesized tiles that can be regenerated.

**None Tile Protection:**

When ``__setitem__`` attempts to set a tile_id that already holds a valid tile
to ``None``, the operation is silently ignored. This prevents a failed tile
load from overwriting a previously cached valid tile.

**Dual-Tier Caching:**

The TileManager uses two caches:

1. **Permanent Cache (80%)**: Stores tiles loaded from disk and procedurally
   generated tiles (e.g., FernTileProvider tiles go here)
2. **Temporary Cache (20%)**: Stores synthesized/cut tiles that can be regenerated

TileManager
~~~~~~~~~~~

The ``TileManager`` module coordinates tile requests between providers and caches.

**Initialization:**

.. code-block:: python

    tilemanager.init(
        total_cache_size=1024,       # Total cache size in number of tiles
        auto_cleanup=True,           # Enable automatic cleanup
        cleanup_max_age_days=3,      # Remove tiles older than 3 days
        collect_cleanup_stats=False  # Skip detailed stats for faster startup
    )

**Key Functions:**

- ``load_tile(tile_id)``: Request a tile to be loaded (asynchronous)
- ``get_tile(tile_id)``: Get a tile from cache (raises if not available)
- ``get_tile_robust(tile_id)``: Get tile with fallback to synthesis
- ``cut_tile(tile_id)``: Synthesize a tile from parent tiles
- ``tiled(media_id)``: Check if media is tiled
- ``get_metadata(media_id, key)``: Get metadata for a media
- ``purge(media_id=None)``: Remove tiles from providers and cache

**Lifecycle Management:**

- ``init()``: Initialize caches, start provider threads, register shutdown hook
- ``shutdown()``: Stop all provider threads, stop cache clean daemon threads,
  run tilestore cleanup. Connected to Qt's ``aboutToQuit`` signal.
- ``pause()``: Pause all TileProvider threads. Used during process-based
  conversion when ``PYZUI_MP_CONTEXT=fork`` is configured.
- ``resume()``: Resume all paused TileProvider threads.

**Pause/Resume Integration:**

.. code-block:: python

    from pyzui.tilesystem import tilemanager

    # Before forking (if using PYZUI_MP_CONTEXT=fork)
    tilemanager.pause()

    # ... conversion in subprocess ...

    # After forking completes
    tilemanager.resume()

With the default ``'spawn'`` process context, pause/resume is typically not
needed since ``spawn`` creates a fresh interpreter state. It exists primarily
for platforms or configurations where ``fork`` is required.

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

Synthesized tiles are inserted into the temporary cache via ``insert(tile_id,
tile, maxaccesses=tempcache)``, limiting how many times they can be accessed
before being regenerated.

**Negative Tile Levels:**

Negative tile levels represent zoomed-out views beyond level 0:

- Level -1: 50% of level 0
- Level -2: 25% of level 0
- etc.

``get_tile()`` raises ``TileNotAvailable`` for negative tile levels. The
``cut_tile()`` function handles them by resizing the (0,0,0) tile, so use
``get_tile_robust()`` for transparent negative-level support.

TileProviders
~~~~~~~~~~~~~

Tile providers are responsible for loading or generating tiles.

**Base Class: TileProvider**

Abstract base class running as a daemon thread. Provides:

- ``request(tile_id)``: Queue a tile load request (LIFO order)
- ``_load(tile_id)``: Abstract method to load/generate a tile (note: underscore-prefixed)
- ``purge(media_id=None)``: Cancel pending requests
- ``stop()``: Signal the provider thread to exit
- ``pause()``: Pause processing of the task queue (used during forked conversions)
- ``resume()``: Resume processing after a pause

**Synchronization:**

The provider uses three threading primitives beyond RLock:

- ``threading.Condition``: For the LIFO task queue — waiters are notified when
  new tasks arrive
- ``threading.Event`` (pause): Blocks the run loop during pause, signalled by
  ``resume()``
- ``threading.Event`` (shutdown): Signals the run loop to exit gracefully,
  set by ``stop()``

**StaticTileProvider**

Loads pre-tiled images from the TileStore. On a cache miss, the provider
reads the tile from disk using ``PIL.Image.open()`` on the path returned by
``TileStore.get_tile_path()``, then stores it in the permanent cache.

Loading from disk is the only operation — ``StaticTileProvider`` does not
perform synthesis or re-save tiles. It returns ``None`` if the tile file
does not exist on disk.

**DynamicTileProvider**

Generates tiles procedurally. The only concrete subclass in the codebase is:

- ``FernTileProvider``: Barnsley fern fractal (at
  ``pyzui/tilesystem/tileproviders/ferndynamictileprovider.py``)

Dynamic provider tiles go to the permanent cache (like StaticProvider tiles),
not the temporary cache.

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
  (counted by number of tiles, default total: 1024)
- LRU eviction prevents unbounded memory growth
- Level 0 tiles and None values are immortal (always kept) as they're
  frequently accessed or represent pending load slots

**Disk I/O:**

- Tiles are loaded lazily on demand
- LIFO queue prioritizes recently requested tiles
- Disk lock prevents concurrent write conflicts

**Threading:**

- TileProviders run as daemon threads
- Condition variables and Events coordinate provider lifecycle
- Tiler uses internal ``ThreadPoolExecutor`` for parallel row processing
- Process-based tiling (tilerrunner) uses ``ProcessPoolExecutor`` for full isolation

**Recommended Settings:**

- **Cache Size**: 1024 tiles (typical usage)
- **Tile Size**: 256×256 for balance of overhead vs. granularity
- **Process Workers**: 2 (default for tilerrunner)
- **Auto-Cleanup**: Enable with 3-30 day retention for disk management
  - Runs on shutdown by default for faster startup
  - Use ``--fast-cleanup`` to skip detailed statistics
  - Disable with ``--no-cleanup`` if not needed

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

Usage Examples
--------------

**Tiling an Image (Process-Based, Recommended):**

.. code-block:: python

    from pyzui.tilesystem.tiler import tilerrunner
    from pyzui.tilesystem import tilestore, tilemanager

    # Initialize the tilemanager
    tilemanager.init(total_cache_size=1024, auto_cleanup=True,
                     cleanup_max_age_days=3)

    # Submit tiling to process pool
    future = tilerrunner.submit_tiling(
        infile='image.ppm',
        media_id='photo1',
        filext='jpg',
        tilesize=256,
    )
    handle = tilerrunner.TilingHandle(future, 'image.ppm', 'photo1')
    handle.join()

    if handle.error:
        print(f"Tiling failed: {handle.error}")
    else:
        print(f"Tiled successfully: {tilestore.get_metadata('photo1', 'maxtilelevel')} levels")

    # Shutdown when done with all tiling
    tilerrunner.shutdown()

**Pausing Providers (for fork-based conversions):**

.. code-block:: python

    from pyzui.tilesystem import tilemanager

    # Pause all providers before forking
    tilemanager.pause()

    # ... run conversion in a fork-based subprocess ...

    tilemanager.resume()

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

**Manual Tilestore Cleanup:**

.. code-block:: bash

    # CLI utility
    python -m pyzui.tilesystem.tilestore.cleanuptilestore --age 30 --dry-run --stats

    # Or programmatically
    from pyzui.tilesystem.tilestore import cleanup_old_tiles

    cleanup_old_tiles(max_age_days=30, dry_run=True)

API Reference
-------------

For detailed API documentation, see:

- :doc:`../pyzui/tile`
- :doc:`../pyzui/tiler`
- :doc:`../pyzui/tilerrunner`
- :doc:`../pyzui/tilestore`
- :doc:`../pyzui/tilecache`
- :doc:`../pyzui/tilemanager`
- :doc:`../pyzui/tileprovider`

See Also
--------

- :doc:`../technicaldocumentation/tiledmediaobject` — TiledMediaObject implementation
- :doc:`../technicaldocumentation/convertersystem` — Media format conversion
- :doc:`../technicaldocumentation/objectsystem` — Object system architecture
