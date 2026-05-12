Tiled media object
==================

Tiled media objects handle large images by breaking them into a pyramid of tiles
for efficient zooming. Source media is first converted to PPM format using the
:doc:`../technicaldocumentation/convertersystem`, then passed to the
:doc:`../technicaldocumentation/tilingsystem` which creates a multi-resolution
tile pyramid stored on disk via :doc:`../pyzui/tilestore`.

Application Flow
----------------

Here is the complete lifecycle of a TiledMediaObject, from creation to rendering::

        ┌─────────────────────────────────────────────────────────────────┐
        │ 1. USER ACTION: Add media to scene                              │
        │    scene.add(TiledMediaObject("image.jpg", scene))              │
        └────────────────────┬────────────────────────────────────────────┘
                             │
        ┌────────────────────▼────────────────────────────────────────────┐
        │ 2. TiledMediaObject.__init__(media_id, scene, autofit=True)     │
        │                                                                 │
        │    • Check if already tiled: TileManager.tiled(media_id)        │
        │    • If NOT tiled, determine file type and submit to pool:      │
        │                                                                 │
        │      ┌──────────────────────────────────────────────┐           │
        │      │ File Type Detection:                         │           │
        │      │  • .pdf     → converterrunner.submit_pdf()   │           │
        │      │  • .ppm     → No conversion (direct use)     │           │
        │      │  • others   → converterrunner.submit_vips()  │           │
        │      │    (.jpg, .png, .gif, .tiff, etc.)           │           │
        │      └──────────────────────────────────────────────┘           │
        └────────────────────┬────────────────────────────────────────────┘
                             │
        ┌────────────────────▼────────────────────────────────────────────┐
        │ 3. CONVERTER PHASE (process-based, if needed)                  │
        │    future = converterrunner.submit_*_conversion(...)           │
        │    self.__converter = ConversionHandle(future, ...)            │
        │                                                                 │
        │    • Converts source file to PPM in a separate process          │
        │    • Saves to temporary file: /tmp/tmpXXXXXX.ppm                │
        │    • ConversionHandle tracks progress (0.0 → 1.0)               │
        │    • Process isolation avoids pyvips/TileManager conflicts      │
        └────────────────────┬────────────────────────────────────────────┘
                             │
        ┌────────────────────▼────────────────────────────────────────────┐
        │ 4. RENDER LOOP (TiledMediaObject.render() called by scene)      │
        │                                                                 │
        │    • If converter finished (__converter.progress == 1.0):       │
        │      → Start tiling via tilerrunner (if not started)            │
        │    • While converter/tiler running:                             │
        │      → Show placeholder with progress percentage                │
        │    • After tiling complete:                                     │
        │      → Load tiles via TileManager.get_tile()                    │
        │      → Assemble and render tileblock                            │
        └────────────────────┬────────────────────────────────────────────┘
                             │
        ┌────────────────────▼────────────────────────────────────────────┐
        │ 5. TILER INITIALIZATION (process-based)                         │
        │    __run_tiler():                                               │
        │      • Determine tile format (jpg if source is jpg, else png)   │
        │      • Submit to tilerrunner:                                   │
        │        future = tilerrunner.submit_tiling(...)                  │
        │        self.__tiler = TilingHandle(future, ...)                 │
        │      • Runs PPMTiler in a separate process                      │
        └────────────────────┬────────────────────────────────────────────┘
                             │
        ┌────────────────────▼────────────────────────────────────────────┐
        │ 6. PPMTiler.__init__(infile, media_id, filext, tilesize=256)    │
        │    Inherits from Tiler                                          │
        │                                                                 │
        │    • Opens PPM file                                             │
        │    • Reads PPM header: read_ppm_header(f)                       │
        │    • Gets image dimensions (width, height)                      │
        │    • Sets __outpath = TileStore.get_media_path(media_id)        │
        │      → ~/.pyzui/tilestore/<media_id_hash>/                      │
        └────────────────────┬────────────────────────────────────────────┘
                             │
        ┌────────────────────▼────────────────────────────────────────────┐
        │ 7. Tiler.run() - THE TILING PROCESS                             │
        │                                                                 │
        │    Step 7a: Calculate tile pyramid                              │
        │    ┌──────────────────────────────────────────────────┐         │
        │    │ • maxtilelevel = calculate_maxtilelevel()        │         │
        │    │   (How many zoom levels needed)                  │         │
        │    │ • numtiles = calculate_numtiles()                │         │
        │    │   (Total tiles across all levels)                │         │
        │    │ • Calculate grid: numtiles_across × numtiles_down│         │
        │    └──────────────────────────────────────────────────┘         │
        │                                                                 │
        │    Step 7b: Lock disk access                                    │
        │    ┌─────────────────────────────────────────────────┐          │
        │    │ with TileStore.disk_lock:                       │          │
        │    │   __tiles(tilelevel=0, row=0)  # Recursive!     │          │
        │    └─────────────────────────────────────────────────┘          │
        └────────────────────┬────────────────────────────────────────────┘
                             │ 
        ┌────────────────────▼────────────────────────────────────────────┐
        │ 8. __tiles() - RECURSIVE TILE GENERATION                        │
        │    (Called for each zoom level, starting from highest detail)   │
        │                                                                 │
        │    For tilelevel=0 (original resolution):                       │
        │    ┌─────────────────────────────────────────────────┐          │
        │    │ a) __load_row_from_file(row)                    │          │
        │    │    • Read scanlines from PPM using _scanchunk() │          │ 
        │    │    • Create Tile objects from raw pixel data    │          │
        │    │    • Build complete row of tiles                │          │
        │    │                                                 │          │
        │    │ b) __savetile(tile, tilelevel, row, col)        │          │
        │    │    • tile_id = (media_id, level, row, col)      │          │
        │    │    • filename = TileStore.get_tile_path(...)    │          │
        │    │    • tile.save(filename) → Saves to disk!       │          │
        │    └─────────────────────────────────────────────────┘          │
        │                                                                 │
        │    For tilelevel > 0 (lower resolutions):                       │
        │    ┌─────────────────────────────────────────────────┐          │
        │    │ a) Get previous level tiles via recursion       │          │
        │    │ b) __mergerows(row_a, row_b)                    │          │
        │    │    • Combine 4 tiles (2×2) into 1 tile          │          │
        │    │    • Tile.merged(t1, t2, t3, t4)                │          │
        │    │ c) __savetile(...) each merged tile             │          │
        │    └─────────────────────────────────────────────────┘          │
        └────────────────────┬────────────────────────────────────────────┘
                             │
        ┌────────────────────▼────────────────────────────────────────────┐
        │ 9. TILE STORAGE: TileStore.get_tile_path()                      │ 
        │                                                                 │
        │    Directory structure created:                                 │
        │    ~/.pyzui/tilestore/                                          │
        │    └── <media_id_hash>/                                         │
        │        ├── metadata.json  (width, height, tilesize, etc.)       │
        │        ├── 0/             (Level 0: full resolution)            │
        │        │   ├── 0/                                               │
        │        │   │   ├── 0.jpg   (tile at row=0, col=0)               │
        │        │   │   ├── 1.jpg   (tile at row=0, col=1)               │
        │        │   │   └── ...                                          │
        │        │   ├── 1/                                               │
        │        │   │   ├── 0.jpg   (tile at row=1, col=0)               │
        │        │   │   └── ...                                          │
        │        ├── 1/             (Level 1: 50% scale)                  │
        │        │   └── 0/0.jpg                                          │
        │        ├── 2/             (Level 2: 25% scale)                  │
        │        └── ...            (More levels as needed)               │
        │                                                                 │
        │    File naming: <tilelevel>/<row>/<col>.<filext>                │
        └────────────────────┬────────────────────────────────────────────┘
                             │
        ┌────────────────────▼────────────────────────────────────────────┐
        │ 10. METADATA STORAGE                                            │
        │     TileStore.write_metadata(media_id, ...)                     │
        │                                                                 │
        │     Saves to: ~/.pyzui/tilestore/<hash>/metadata.json           │
        │     Content:                                                    │
        │     {                                                           │
        │       "filext": "jpg",                                          │
        │       "tilesize": 256,                                          │
        │       "width": 4096,                                            │
        │       "height": 3072,                                           │
        │       "maxtilelevel": 4,                                        │
        │       "aspect_ratio": 1.333,                                    │
        │       "tiled": true                                             │
        │     }                                                           │
        └────────────────────┬────────────────────────────────────────────┘
                             │
        ┌────────────────────▼────────────────────────────────────────────┐
        │ 11. RENDERING: TiledMediaObject.render()                        │
        │                                                                 │
        │     • TileManager.get_tile(tile_id) loads tiles from disk       │
        │     • Tiles are cached in TileCache (LRU cache)                 │
        │     • __render_tileblock() assembles visible tiles              │
        │     • Tileblock is cached with age-based invalidation           │
        │     • Scales tileblock to screen resolution                     │
        │     • Draws to painter (displayed on screen)                    │
        └─────────────────────────────────────────────────────────────────┘

Tileblock Caching
-----------------

To avoid re-assembling the visible tile region on every frame,
``TiledMediaObject`` caches a composite ``QImage`` called the **tileblock**.
The cache is invalidated based on the age of its constituent tiles and the
current render mode.

**Cache State Variables:**

.. code-block:: python

    self.__tileblock          # QImage: cached composite of visible tiles
    self.__tileblock_id       # Tuple: (level, row_min, col_min, row_max, col_max)
    self.__tileblock_final    # Bool: are all tiles in the block fully loaded?
    self.__tileblock_age      # Int: render cycles since last rebuild

**Age-Based Invalidation:**

.. code-block:: python

    tempcache = 5  # Class constant: max cycles for non-final tileblock reuse

    def __render_tileblock(self, ..., mode):
        # Build tileblock_id from current viewport
        tileblock_id = (level, row_min, col_min, row_max, col_max)

        # Check if cache is valid
        if (self.__tileblock is not None
                and tileblock_id == self.__tileblock_id
                and (self.__tileblock_final
                     or (mode == RenderMode.Draft
                         and self.__tileblock_age < tempcache))):
            # Reuse cached tileblock
            self.__tileblock_age += 1
            return self.__tileblock

        # Cache miss or expired — rebuild
        self.__tileblock = assemble_tileblock(...)
        self.__tileblock_id = tileblock_id
        self.__tileblock_final = all_tiles_loaded()
        self.__tileblock_age = 0
        return self.__tileblock

**Invalidation Rules:**

- Always rebuild if the viewport changes (different tile range)
- Always rebuild if the tileblock is not final AND mode is ``HighQuality``
- Rebuild a non-final tileblock after ``tempcache`` cycles in ``Draft`` mode
- A final tileblock (all tiles loaded) is never invalidated by age alone

**Draft vs HighQuality Rendering:**

The render mode affects how tileblocks are assembled:

- **Draft**: Non-final tileblocks are cached up to ``tempcache`` (5) cycles
  before being force-rebuilt. This provides faster frame rates during
  progressive loading at the cost of showing partially-loaded tiles longer.
- **HighQuality**: Non-final tileblocks are rebuilt every frame, ensuring
  newly-arrived tiles are displayed as soon as they load. This provides
  the best visual quality at the cost of more frequent tileblock assembly.

Both modes use ``Qt.FastTransformation`` for scaling.

Placeholder Rendering
---------------------

While the converter or tiler is running, users see a **placeholder** displayed
in the object's screen region via ``__render_placeholder()``:

- A dark gray filled rectangle occupies the object's on-screen area
- Text is drawn at the center of the rectangle using the scene's registration font at 14pt
- The text shows **"loading..."** when the converter is running but hasn't reported progress yet, or the tiler hasn't started
- The text shows **"XX%"** (a percentage from 0% to 100%) once progress data is available

The placeholder is only rendered while ``__converter`` or ``__tiler`` is not
None and the object would otherwise render nothing (``__loaded`` is False).

Progress Tracking
-----------------

The ``__progress`` property combines converter and tiler progress into a
single 0.0–1.0 value for displaying the loading percentage:

.. code-block:: python

    @property
    def __progress(self) -> float:
        if self.__converter is None and self.__tiler is None:
            return 0.0                    # Nothing started
        elif self.__converter is None:
            return self.__tiler.progress   # Only tiling (scaled to 0–1)
        elif self.__tiler is None:
            return 0.5 * self.__converter.progress  # Only conversion (0–0.5)
        else:
            return 0.5 * (self.__converter.progress + self.__tiler.progress)

This creates smooth progress indication:

- ``0% – 50%``: Conversion phase
- ``50% – 100%``: Tiling phase

.. note::

   Process-based converters and tilers (via ``converterrunner`` /
   ``tilerrunner``) report progress as 0.0 (running) or 1.0 (complete),
   since subprocess progress cannot be monitored incrementally. The
   ``ConversionHandle`` and ``TilingHandle`` wrappers provide compatible
   interfaces that mirror the thread-based ``Converter`` and ``Tiler``
   ``progress`` properties.

Rendering Details
-----------------

Viewport Culling
~~~~~~~~~~~~~~~~

Before assembling a tileblock, the render method checks whether any part
of the object falls within the current viewport:

.. code-block:: python

    if row_max < row_min or col_max < col_min:
        return  # Object is off-screen, skip rendering

If no tiles intersect the visible region, rendering is skipped entirely,
avoiding unnecessary tile requests and assembly.

Tile Loading with Retry
~~~~~~~~~~~~~~~~~~~~~~~~

The ``__try_load()`` method is called on **every render cycle** while
``__loaded`` is False. It attempts to load the root tile (level 0, row 0,
col 0) via ``TileManager.get_tile()``, which may raise ``TileNotLoaded`` if
the tile hasn't been generated yet or isn't in the cache. This exception is
caught silently, and ``__try_load()`` retries on the next render frame.

This retry loop is the mechanism by which:

- Already-tiled media is detected (root tile loads immediately)
- Newly-tiled media becomes available (root tile loads once tiling finishes)
- Network or disk errors are tolerated (retry on next cycle)

onscreen_size and is_size_visible
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``onscreen_size`` property efficiently calculates the pixel dimensions
of the object on screen using the stored ``aspect_ratio`` metadata when
available, avoiding the need to query tile dimensions repeatedly.

The ``is_size_visible`` property adds a minimum 1-pixel size check to the
standard visibility test, ensuring that images with non-zero screen area
are always considered visible even at extreme zoom-out levels.

Performance Optimization: math.exp2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The tiled media system uses ``math.exp2(x)`` instead of ``2 ** x`` for
zoom-level exponentiation (1.85× faster), and ``math.log2(x)`` instead of
``math.log(x, 2)`` for logarithmic scaling (2× faster). These are CPython
intrinsics that avoid the overhead of the generic ``**`` and ``log`` operators.

Error Handling
--------------

**Converter and Tiler Errors:**

Both ``ConversionHandle`` and ``TilingHandle`` expose an ``error`` attribute
that is populated if the subprocess raises an exception. During rendering,
``TiledMediaObject`` checks these attributes:

.. code-block:: python

    if self.__converter and self.__converter.error:
        raise LoadError(self.__converter.error)

    if self.__tiler and self.__tiler.error:
        self.__clean()
        raise LoadError(self.__tiler.error)

A ``LoadError`` propagates up to the Scene, which catches it during rendering
and removes the offending object from the scene. This ensures a failed
conversion or tiling job doesn't crash the application.

**Cleanup on Failure:**

When a tiler error occurs, ``__clean()`` closes file handles, removes the
temporary PPM file, clears the progress-related state, and sets
``__tiler = None``. Converter errors similarly clean up partially-written
output files before storing the error message.

ModifyTiledMediaObjectDialog
----------------------------

:class:`ModifyTiledMediaObjectDialog` provides interactive image
manipulation for tiled media objects. It is triggered from the right-click
context menu on a ``TiledMediaObject``.

**Available Operations:**

.. list-table::
   :header-rows: 1

   * - Operation
     - Effect
     - State
   * - **Rotate Left** (90° CCW)
     - Rotates image 90 degrees counter-clockwise
     - Preview only until Apply
   * - **Rotate Right** (90° CW)
     - Rotates image 90 degrees clockwise
     - Preview only until Apply
   * - **Invert Colors**
     - Negative color effect (toggle)
     - Preview only until Apply
   * - **Black and White**
     - Converts to grayscale/luminance (toggle)
     - Preview only until Apply

**Preview and Apply Pattern:**

Operations are **preview-only** — the modifications are accumulated but not
persisted until the user clicks **OK**:

1. Each operation toggles its internal state (rotation angle, invert flag,
   BW flag) and updates the preview image
2. Multiple operations can be stacked (e.g., rotate + invert)
3. On **OK**, all accumulated transformations are applied in a single
   ``VipsConverter`` pass via ``converterrunner.submit_vips_conversion()``
4. The transformed PPM replaces the original temporary file
5. The current ``TiledMediaObject`` is **removed from the scene** and
   **replaced** with a new ``TiledMediaObject`` using the transformed PPM,
   preserving the original position, zoom level, and center point
6. The old object's tile data is purged, and the new object starts the
   tiling pipeline fresh

**Dialog Implementation:**

.. code-block:: python

    # Transformation parameters accumulate across operations
    self._rotation = 0       # 0, 90, 180, or 270
    self._invert = False     # Color inversion toggle
    self._bw = False         # Black and white toggle

    # On OK: single-pass conversion with all transformations
    future = converterrunner.submit_vips_conversion(
        ppm_file, tmpfile,
        rotation=self._rotation,
        invert_colors=self._invert,
        black_and_white=self._bw,
    )

Serialization and Persistence
-----------------------------

PZS File Format
~~~~~~~~~~~~~~~

``TiledMediaObject`` is stored in ``.pzs`` scene files as a simple line
referencing the ``media_id``:

.. code-block:: text

    TiledMediaObject    image.jpg    0.5    100.0    200.0

The scene loader bypasses the standard ``from_dict()`` deserialization
mechanism (which ``TiledMediaObject`` does not implement) and instead creates
new ``TiledMediaObject(media_id, scene, autofit=False)`` instances directly
from the parsed line. Position, zoom level, and centre point are restored
from the saved values.

**Why from_dict is not implemented:**

Unlike ``SVGMediaObject``, which stores editable content in memory and
requires ``from_dict`` for clipboard copy/paste operations,
``TiledMediaObject`` references an external file whose tile data is
persisted in the ``~/.pyzui/tilestore/`` directory. The ``media_id``
reference is the only state that needs to be preserved.

TileStore Persistence
~~~~~~~~~~~~~~~~~~~~~

Tile data survives across scene saves because:

1. Converted and tiled data is stored persistently in
   ``~/.pyzui/tilestore/<media_id_hash>/``
2. The scene ``.pzs`` file stores only the ``media_id`` reference, not the
   tile data itself
3. On reload, ``TileManager.tiled(media_id)`` at init time detects
   already-tiled media and skips conversion
4. Tiles are loaded on demand as the user zooms and pans

This means a single large image can be referenced by multiple scene files
without requiring re-conversion or re-tiling.

Clipboard Support
~~~~~~~~~~~~~~~~~

``TiledMediaObject`` is **not supported** by the clipboard system
(``SceneClipboardManager``). Copy/paste operations are limited to
``SVGMediaObject``. Attempting to copy a ``TiledMediaObject`` results in the
message ``"Unsupported object type in clipboard"``. This is by design —
tiled media references to external files would be meaningless in a clipboard
context without the underlying file.

See Also
--------

- :doc:`../technicaldocumentation/convertersystem` — Media format conversion
- :doc:`../technicaldocumentation/tilingsystem` — Tile pyramid generation
- :doc:`../technicaldocumentation/objectsystem` — Object system architecture
- :doc:`../pyzui/converterrunner` — Process-based parallel conversion
- :doc:`../pyzui/tilerrunner` — Process-based parallel tiling
- :doc:`../pyzui/tilestore` — Persistent tile storage
- :doc:`../pyzui/tilecache` — In-memory LRU tile cache
- :doc:`../pyzui/tilemanager` — Tile coordination and caching
- :doc:`../pyzui/modifytiledmediaobjectdialog` — Image manipulation dialog
