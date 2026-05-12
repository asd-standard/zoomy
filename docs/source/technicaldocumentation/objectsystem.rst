.. Object System Documentation

Object System
=============

This document provides a comprehensive overview of the object system architecture in PyZUI,
explaining how objects are positioned, rendered, and animated within the Zooming User Interface.
The object system is responsible for managing the spatial relationships, physics simulation,
autosave backups, clipboard operations, parallel rendering, and rendering of all elements
in the scene.

Overview
--------

The object system is responsible for:

1. Managing 3D position and velocity (x, y, zoom level)
2. Simulating physics with exponential damping
3. Handling coordinate transformations between reference frames
4. Rendering media objects at various zoom levels with parallel processing
5. Managing scene composition and object lifecycle
6. Automatically backing up scenes with configurable rotation and expiration
7. Copy/paste operations with grid-aligned positioning

The system uses a **hierarchical class structure** where :class:`PhysicalObject` provides
the base physics simulation, :class:`MediaObject` adds media-specific positioning and rendering,
and concrete media types implement specific rendering strategies. The :class:`Scene` class
delegates advanced functionality to three sub-managers: :class:`SceneParallelRenderer`,
:class:`SceneAutosaveManager`, and :class:`SceneClipboardManager`.

Architecture
------------

The object system consists of the following class hierarchy:

.. code-block:: text

    PhysicalObject (Abstract Base)
    │   • Position: _x, _y, _z (zoom level)
    │   • Velocity: vx, vy, vz
    │   • Damping factor
    │   • Centre point
    │   • Physics simulation (step, move, zoom, aim)
    │
    ├── MediaObject (Abstract)
    │   │   • Media ID and scene reference
    │   │   • Coordinate transforms (scene ↔ screen)
    │   │   • Scaling management (scale, onscreen_size)
    │   │   • Position properties (topleft, bottomright, centre)
    │   │   • Visibility testing (hides, fit)
    │   │   • Abstract render() method
    │   │   • Serialization: to_dict() / from_dict()
    │   │
    │   ├── TiledMediaObject
    │   │       • Large image support via tile pyramid
    │   │       • Tile grid management
    │   │       • Progressive loading with placeholders
    │   │       • Process-based parallel conversion
    │   │       • Converter support (PDF, images)
    │   │       • Efficient for huge images
    │   │
    │   ├── StringMediaObject
    │   │       • Hybrid rendering: moving (direct) vs static (cached)
    │   │       • Multi-line text support
    │   │       • Font scaling based on zoom
    │   │       • Transparent background
    │   │       • ParallelLayoutCalculator (thread-pool text layout)
    │   │       • TextLayoutData (thread-safe pre-calculated layouts)
    │   │
    │   └── SVGMediaObject
    │           • Vector graphics rendering
    │           • Scalable without quality loss
    │           • QSvgRenderer integration
    │           • Transparent background
    │           • SVG content caching (in-memory + disk via SVGCache)
    │           • Modification tracking (picker/clipboard)
    │           • Serialization: to_dict() / from_dict()
    │           • SVG shape utilities (arrow, circle, square, stick, triangle)
    │           • Custom size visibility thresholds
    │
    └── Scene
            • Container for MediaObjects
            • Viewport management
            • Scene persistence (save/load)
            • Thread-safe operations (RLock)
            • Bulk object selection (ctrl+click/drag)
            • Render order toggle (smaller/larger on top)
            • Rendering coordination
            ├── SceneParallelRenderer (parallel.py)
            │       • Parallel rendering with thread pools
            │       • Integrates ParallelLayoutCalculator & PriorityBatcher
            │       • Statistics tracking (batches, cache hits, timing)
            ├── SceneAutosaveManager (autosave.py)
            │       • Timer-based per-scene auto-backup
            │       • Configurable interval, rotation, expiration
            │       • Integrates BackupManager
            └── SceneClipboardManager (clipboard.py)
                    • Copy/paste operations
                    • Grid-aligned positioning
                    • Offset support

    Supporting Services
    ├── ZoomManager (objectsutils/zoom/)
    │       • Zoom level clamping (-10 to 12)
    │       • Crash prevention at extreme zoom levels
    └── PriorityBatcher (sceneutils/)
            • Viewport-aware priority batching
            • 4 priority levels (HIGH, MEDIUM, LOW, BACKGROUND)
            • heapq-based priority sorting

    SVG Utilities (mediaobjectsutils/svg/)
    ├── SVGCache
    │       • Hashed disk cache with svg_ prefix
    │       • Singleton access via get_svg_cache()
    └── Shape Utils (5 files)
            • svgarrowutils, svgcircleutils, svgsquareutils
            • svgstickutils, svgtriangleutils
            • XML ElementTree parsing with SVG namespace
            • Shape detection and elongation

Core Components
---------------

PhysicalObject
~~~~~~~~~~~~~~

The :class:`PhysicalObject` class provides the foundation for all objects that exist in
the zooming user interface. It manages position, velocity, and physics simulation.

**Key Attributes:**

- ``_x, _y, _z``: Position coordinates (z represents zoom level)
- ``vx, vy, vz``: Velocity components
- ``damping_factor``: Controls how quickly velocity decays (default: 512)
- ``_centre``: Center point in object coordinates

**Physics Model:**

The object system uses exponential damping for smooth deceleration:

.. code-block:: text

    v(t) = u * d^(-t)

    where:
        u = initial velocity
        d = damping_factor
        t = time in seconds

Displacement is calculated by integrating the velocity:

.. code-block:: text

    s(t) = (u / log(d)) * (1 - d^(-t))

This creates smooth, natural-feeling motion that gradually comes to rest.

**Key Methods:**

- ``move(dx, dy)``: Move object by displacement (dx, dy)
- ``zoom(amount)``: Zoom by given amount with centre fixed on screen
- ``aim(v, s, t=None)``: Calculate initial velocity for desired displacement
- ``step(t)``: Update position and velocity for time step t
- ``moving``: Property indicating if object has non-zero velocity

MediaObject
~~~~~~~~~~~

The :class:`MediaObject` class extends :class:`PhysicalObject` to add media-specific
functionality and coordinate transformations.

**Key Attributes:**

- ``_media_id``: Unique identifier for the media content
- ``_scene``: Reference to parent Scene object
- ``transparent``: Boolean flag for transparency (subclass-specific)

**Coordinate Systems:**

MediaObjects use three coordinate systems:

1. **Screen Coordinates** - Absolute pixel positions on display
2. **Scene Coordinates** - Positions relative to scene origin, scaled by scene zoom
3. **Image Coordinates** - Positions within the media object, scaled by object zoom

**Coordinate Transformations:**

From MediaObject position to screen coordinates:

.. code-block:: python

    screen_x = scene.origin[0] + obj.pos[0] * (2 ** scene.zoomlevel)
    screen_y = scene.origin[1] + obj.pos[1] * (2 ** scene.zoomlevel)

From MediaObject centre (image coords) to screen coordinates:

.. code-block:: python

    # First convert image coords to scene coords
    C_s_x = obj.pos[0] + obj._centre[0] * (2 ** obj.zoomlevel)
    C_s_y = obj.pos[1] + obj._centre[1] * (2 ** obj.zoomlevel)

    # Then convert scene coords to screen coords
    screen_x = scene.origin[0] + C_s_x * (2 ** scene.zoomlevel)
    screen_y = scene.origin[1] + C_s_y * (2 ** scene.zoomlevel)

**Key Properties:**

- ``scale``: Combined zoom factor: ``2 ** (scene.zoomlevel + self.zoomlevel)``
- ``topleft``: On-screen position of top-left corner
- ``bottomright``: On-screen position of bottom-right corner
- ``onscreen_size``: Tuple (width, height) in screen pixels
- ``onscreen_area``: Total pixel area occupied on screen

**Key Methods:**

- ``render(painter, mode)``: Abstract method for rendering (implemented by subclasses)
- ``move(dx, dy)``: Move relative to scene using screen distance
- ``zoom(amount)``: Zoom with centre fixed on screen
- ``hides(other)``: Check if this object completely obscures another
- ``fit(bbox)``: Fit and center object within bounding box
- ``to_dict()``: Serialize object to dictionary (base implementation)
- ``from_dict(d, scene)``: Deserialize object from dictionary (base implementation)

Scene
~~~~~

The :class:`Scene` class manages collections of MediaObjects and coordinates rendering.
As of v0.3.2+, Scene delegates advanced functionality to three dedicated sub-managers
for cleaner separation of concerns.

**Key Attributes:**

- ``__objects``: List of MediaObjects in the scene
- ``__objects_lock``: Thread-safe access control (RLock)
- ``__viewport_size``: Current viewport dimensions
- ``selection``: Currently selected object (list of MediaObjects for bulk selection)
- ``right_selection``: Right-click selected object
- ``standard_viewport_size``: Default size for scene persistence (1280x720)
- ``__config``: Stored configuration dictionary
- ``__last_save_path``: Path of last saved file (for autosave)
- ``__autosave_manager``: :class:`SceneAutosaveManager` instance
- ``__clipboard_manager``: :class:`SceneClipboardManager` instance
- ``__parallel_renderer``: :class:`SceneParallelRenderer` instance

**Scene Configuration:**

The Scene constructor accepts an optional ``config`` dictionary with the following keys:

.. code-block:: text

    config = {
        "zoom": {
            "zoomlevel": 0.0,       # Initial scene zoom level
            "origin": [640, 360],   # Initial viewport origin
        },
        "render": {
            "order": "smaller_on_top",  # or "larger_on_top"
        },
        "parallel_rendering": {
            "enabled": True,
        },
        "autosave": {
            "enabled": True,
            "interval": 300,        # Seconds (default: 5 minutes)
            "max_backups": 20,
            "expire_days": 7,
        },
    }

**Render Order:**

The ``render_order`` property and ``set_render_order()`` method control the z-ordering
of objects during rendering:

- ``"smaller_on_top"`` (default): Smaller objects render on top (original behavior).
  Sort by onscreen_area ascending, iterate from smallest to largest.
- ``"larger_on_top"``: Larger objects render on top (natural depth).
  Sort by onscreen_area descending, iterate from largest to smallest.

The render order can be toggled via the View menu (Ctrl+R) at runtime. It affects both
the sort direction in ``__sort_objects()`` and the occlusion culling logic.

**Bulk Selection:**

As of v0.3.2, Scene supports multi-object selection:

- **Ctrl+Click**: Add/remove objects from selection group
- **Left-click drag**: Area selection (lasso) to select multiple objects
- ``selection`` is a ``list[MediaObject]`` (was single object in earlier versions)
- Right-click selection remains single-object for context menu operations

**Scene Coordinate System:**

.. code-block:: text

    World Reference Frame
    ────────────────────────────────────────▶ x
    │   Scene
    │  @ ──────────────────────────────+───▶
    │  │  ViewPort        MediaObj     │
    │  │  (Screen View)   *───────+──▶ │
    │  │                  │   &   │    │
    │  │               %  +───────"    │
    │  │                  │            │
    │  │                  ▼            │
    │  │                               │
    │  +───────────────────────────────#
    │  │
    │  ▼
    ▼
    y

    Legend:
        @ → Scene.origin()        (world coordinates)
        % → Scene.centre          (screen coordinates)
        # → Scene.viewport_size   (screen dimensions)
        * → MediaObject.topleft   (screen coordinates)
        " → MediaObject.bottomright
        & → MediaObject.centre

**Scene Origin and Centre:**

The scene origin ``(ox, oy)`` is the world-space coordinate of the top-left corner
of the viewport:

.. code-block:: python

    # Scene centre in screen coordinates
    centre_x = origin[0] + (viewport_size[0] / 2) * (2 ** zoomlevel)
    centre_y = origin[1] + (viewport_size[1] / 2) * (2 ** zoomlevel)

**Scene Lifecycle:**

Scene manages its own cleanup through:

- ``__del__``: Stops autosave timer and shuts down parallel renderer threads
- ``shutdown_threads()``: Public method for explicit cleanup at application shutdown
- Autosave manager handles timer lifecycle separately
- Parallel renderer stops its thread pool gracefully

**Key Methods:**

- ``add(mediaobject)``: Add object to scene
- ``remove(mediaobject)``: Remove object and purge unused tiles
- ``get(pos)``: Get topmost (smallest) object at screen position
- ``render(painter, draft)``: Render all objects with occlusion culling (smaller on top)
- ``step(t)``: Update physics for scene and all objects
- ``save(filename)``: Save scene to .pzs file
- ``load_scene(filename)``: Load scene from .pzs file (static method)
- ``set_render_order(order)``: Set render order ("smaller_on_top" or "larger_on_top")
- ``shutdown_threads()``: Cleanup parallel renderer threads
- ``copy_selected()``: Copy selected objects via clipboard manager
- ``paste()``: Paste objects via clipboard manager

Scene Sub-Managers
~~~~~~~~~~~~~~~~~~

SceneParallelRenderer
^^^^^^^^^^^^^^^^^^^^^

:class:`SceneParallelRenderer` handles parallel rendering of StringMediaObject
text layouts in background threads, improving performance for scenes with many
text objects. Located at :doc:`../pyzui/parallel`.

**Key Features:**

- **Thread Pool**: Concurrent text layout calculation using ``ParallelLayoutCalculator``
- **Priority Batching**: Uses :class:`PriorityBatcher` to prioritize objects
  closest to the viewport center
- **Statistics**: Tracks text object count, batch count, cache hit rate, and timing
- **Configuration**: Controlled via ``parallel_rendering.enabled`` config key

**Rendering Flow:**

.. code-block:: text

    1. PriorityBatcher sorts text objects by viewport distance
    2. Objects are grouped into priority batches (HIGH through BACKGROUND)
    3. ParallelLayoutCalculator computes layouts in thread pool
    4. Pre-calculated TextLayoutData is cached for faster rendering
    5. Scene renders using cached layouts, skipping expensive layout calculation

SceneAutosaveManager
^^^^^^^^^^^^^^^^^^^^

:class:`SceneAutosaveManager` provides timer-based automatic backup creation for
scene files. Located at :doc:`../pyzui/autosave`.

**Key Features:**

- **Timer-based**: Configurable interval (default: 5 minutes)
- **Per-scene directories**: ``~/.pyzui/backups/{filename}_{4char_hash}/``
- **Rotation**: Keeps last N backups, deletes oldest automatically (default: 20)
- **Expiration**: Inactive scene directories expire after N days (default: 7)
- **Enabled by default**: Autosave starts automatically after scene load
- **CLI integration**: ``--autosave-interval``, ``--autosave-max-backups``,
  ``--backup-expire-days``, ``--no-autosave``

SceneClipboardManager
^^^^^^^^^^^^^^^^^^^^^

:class:`SceneClipboardManager` provides copy/paste operations for scene objects.
Located at :doc:`../pyzui/clipboard`.

**Key Features:**

- **Copy**: Serializes selected SVG objects to internal clipboard list
- **Paste**: Deserializes and re-creates objects with optional grid-aligned offset
- **Grid Alignment**: Pasted objects are positioned relative to the current
  selection with configurable offset
- **Supports**: SVGMediaObject serialization with all state fields

MediaObject Types
-----------------

TiledMediaObject
~~~~~~~~~~~~~~~~

:class:`TiledMediaObject` handles large images by breaking them into a pyramid of tiles.

**Features:**

- **Format Support**: PDF, PPM, and standard images (JPG, PNG, GIF, TIFF)
- **Converters**: Automatic conversion via PDFConverter or VipsConverter,
  with process-based parallel conversion via :doc:`../pyzui/converterrunner`
- **Tile Pyramid**: Multi-resolution tile structure for efficient zooming
- **Progressive Loading**: Shows placeholder with progress percentage
- **Caching**: Intelligent tile block caching with age-based invalidation

**Loading Process:**

1. Check if media is already tiled (via TileManager)
2. If not tiled, select appropriate converter based on file extension
3. Convert to PPM format (if needed)
4. Run PPMTiler to create tile pyramid
5. Store tiles on disk via TileStore
6. Load tiles on demand via TileManager

**Rendering Strategy:**

.. code-block:: text

    1. Calculate required tile level from zoom
    2. Determine visible tile range from viewport
    3. Request tileblock (group of adjacent tiles)
    4. Check cache for tileblock
    5. If cache miss or stale, render new tileblock:
       - Request individual tiles from TileManager
       - Composite tiles into tileblock
       - Cache tileblock for reuse
    6. Scale tileblock to match zoom level
    7. Draw scaled tileblock to screen

**Key Attributes:**

- ``__autofit``: Whether to fit media to placeholder area
- ``__loaded``: Flag indicating media is ready
- ``__converter``: PDFConverter or VipsConverter instance
- ``__tiler``: PPMTiler instance
- ``__tileblock``: Cached composite of adjacent tiles
- ``__maxtilelevel``: Maximum tile pyramid level
- ``__tilesize``: Size of individual tiles in pixels

StringMediaObject
~~~~~~~~~~~~~~~~~

:class:`StringMediaObject` renders text strings with automatic font scaling and
dual-mode hybrid rendering for optimal performance.

**Features:**

- **Multi-line Support**: Automatically handles newline characters
- **Color Support**: Parse color from media_id (e.g., 'string:ff0000:Hello')
- **Font Scaling**: Font size scales with zoom level
- **Transparent Background**: Doesn't obscure objects behind it
- **Hybrid Rendering**: Dual-mode rendering for performance (v0.3.0+)

**Media ID Format:**

.. code-block:: text

    string:RRGGBB:text content

    Examples:
        string:ff0000:Hello World    → Red text
        string:00ff00:Line 1\nLine 2 → Green multi-line text
        string:0000ff:Blue Text      → Blue text

**Hybrid Rendering:**

StringMediaObject uses two rendering modes to balance quality and performance:

- **Moving Mode**: When the scene is zooming or panning (``scene.vzmoving``
  is True), text is rendered directly via ``QPainter.drawText()`` for smooth
  animation with minimal overhead.
- **Static Mode**: When the scene is still, text is rendered to a cached ``QImage``
  once, then blitted to screen on subsequent frames. This provides higher quality
  anti-aliased output.

**Cache Management:**

.. code-block:: text

    Cache validity conditions:
    - Cached image exists AND scale hasn't changed beyond 1% threshold
    - Mode hasn't switched (moving ↔ static)
    - Text content hash hasn't changed

    Cache invalidation triggers:
    - Object starts moving (vzmoving becomes True)
    - Scale changes significantly
    - Explicit call to invalidate_cache() or clear_caches()

**Cache Methods:**

- ``__render_text_to_image()``: Renders text to QImage for static mode
- ``__is_cache_valid()``: Checks if cached image can be reused
- ``__compute_text_hash()``: Hashes text content for change detection
- ``invalidate_cache()``: Marks cache as stale
- ``clear_caches()``: Force-clears all cached images

**Rendering:**

- Base font size: 24pt at 100% scale
- Only renders when size is between 2.3% and 77% of viewport
- Uses ``TextLayoutData`` for pre-calculated font metrics and bounding rects
- Creates QRectF for each line in multi-line text

**Parallel Layout Calculation:**

For scenes with many StringMediaObjects, :class:`ParallelLayoutCalculator`
computes text layouts in a thread pool. Located at
:doc:`../pyzui/parallellayout`. Key features:

- Thread-safe design — no Qt objects constructed on worker threads
- Uses ``TextLayoutData`` dataclass for pre-calculated layout results
- Integrated with ``SceneParallelRenderer`` and ``PriorityBatcher``

SVGMediaObject
~~~~~~~~~~~~~~

:class:`SVGMediaObject` renders scalable vector graphics with extensive
caching, modification tracking, and utility support.

**Features:**

- **Vector Rendering**: Uses QSvgRenderer for crisp graphics at any zoom
- **Transparent Background**: SVG transparency is preserved
- **Scalable**: No quality loss when zooming
- **Content Caching**: In-memory SVG content cache for fast re-rendering
- **Modification Tracking**: Tracks changes from picker, clipboard, and shape utilities
- **Serialization**: Full state serialization via ``to_dict()`` / ``from_dict()``
- **SVG Cache Integration**: Disk-backed cache with content-hash addressing
- **Shape Utilities**: 5 shape generators for interactive SVG creation

**SVG Cache Integration:**

SVGs can be loaded from a file path or from the disk-backed SVGCache
(:doc:`../pyzui/svgcache`) using a content-hash based ``media_id`` with
an ``svg_`` prefix:

.. code-block:: text

    media_id formats:
        "path/to/file.svg"     → File-loaded SVG
        "svg_a1b2c3d4..."      → Cache-loaded SVG (content hash)

The ``__get_svg_load_path()`` method resolves both formats, fetching content
from SVGCache when needed.

**Content Caching:**

- ``__cached_svg_content``: In-memory byte buffer of SVG content
- ``get_svg_content()``: Returns content from cache or reads from file
- ``set_svg_content(content)``: Sets embedded SVG content (e.g., from clipboard)
- Reduces disk I/O for frequently rendered SVGs

**Modification Tracking:**

- ``__is_modified``: Boolean flag set when SVG content changes
- ``mark_as_modified()``: Called by picker, clipboard, and shape utilities
- ``original_file_path``: Property that returns the original file path
  (or ``None`` for cache-loaded SVGs)

**Serialization:**

.. code-block:: python

    # to_dict() returns all SVG state:
    {
        "class_name": "SVGMediaObject",
        "media_id": "svg_a1b2c3...",
        "zoomlevel": 0.0,
        "x": 100.0, "y": 200.0,
        "width": 64.0, "height": 64.0,
        "transparent": True,
        "is_modified": False,
        "original_file_path": None,
    }

**Custom Size Visibility:**

SVGMediaObject uses SVG-specific thresholds for visibility testing:

- Minimum dimension > ``viewport_min / 55``
- Maximum dimension < ``viewport_max / 0.5``

**Embedded SVGs:**

SVGs created interactively (via shape utilities or picker) may have their
content embedded directly rather than loaded from disk. A warning is emitted
if the embedded content exceeds ``MAX_EMBEDDED_SVG_SIZE_BYTES`` (1 MB).

**Rendering:**

- Loads SVG file or cached content
- Creates QSvgRenderer for rendering
- Stores default width and height from SVG
- Renders to QRectF scaled by current zoom level
- Only renders when size is between 2.3% and 77% of viewport

MediaObject Utilities
---------------------

SVG Shape Utilities
~~~~~~~~~~~~~~~~~~~

Five utility modules in ``mediaobjectsutils/svg/utils/`` provide shape detection
and elongation for interactive SVG creation. Each utility parses SVG content
using ``xml.etree.ElementTree`` with proper SVG namespace handling.

.. list-table::
   :header-rows: 1

   * - Utility
     - Shape
     - File
   * - ``ArrowUtils``
     - Arrows (directional connectors)
     - ``svgarrowutils.py``
   * - ``CircleUtils``
     - Circles and ellipses
     - ``svgcircleutils.py``
   * - ``SquareUtils``
     - Rectangles and squares
     - ``svgsquareutils.py``
   * - ``StickUtils``
     - Stick figures (line-based)
     - ``svgstickutils.py``
   * - ``TriangleUtils``
     - Triangles of various orientations
     - ``svgtriangleutils.py``

All shape utilities interface with SVGCache for persistent storage of created
and modified shapes.

**Shape Detection:**

Each utility detects whether a given SVG content matches its target shape using
XML element inspection. When a shape is detected, the utility can:

1. Identify key geometric elements (e.g., circle radius, rectangle dimensions)
2. Apply elongation transformations (e.g., stretch an arrow along its axis)
3. Generate modified SVG content
4. Store the result in SVGCache

**See Also:**

- :doc:`../pyzui/svgarrowutils`
- :doc:`../pyzui/svgcircleutils`
- :doc:`../pyzui/svgsquareutils`
- :doc:`../pyzui/svgtriangleutils`
- :doc:`../pyzui/svgcache`

SVGCache
~~~~~~~~

:class:`SVGCache` provides a disk-backed content-addressable cache for SVG data.
Located at :doc:`../pyzui/svgcache`.

**Key Features:**

- **Content Hashing**: SVGs are stored by content hash (``svg_`` prefix)
- **Flat Directory**: Single-level storage under cache root
- **Singleton**: Accessed via ``get_svg_cache()``
- **Human-readable names**: ``get_human_readable_name()`` for display
- **CRUD operations**: ``store_svg()``, ``get_svg_content()``, ``remove_svg()``

**Usage Pattern:**

.. code-block:: python

    from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import get_svg_cache

    cache = get_svg_cache(base_dir)

    # Store SVG content
    cache_hash = cache.store_svg(svg_bytes)

    # Retrieve SVG content
    content = cache.get_svg_content(cache_hash)

    # Remove SVG
    cache.remove_svg(cache_hash)

TextLayoutData
~~~~~~~~~~~~~~

:class:`TextLayoutData` is a dataclass storing pre-calculated text layout
information for StringMediaObject rendering. Located at
:doc:`../pyzui/textlayout`.

**Key Fields:**

- Font metrics (QFont-compatible sizing data)
- Bounding rectangles for each text line
- Text alignment options (``LEFT``, ``CENTER``)
- Layout options (word wrap, line spacing)

**Thread Safety:**

``TextLayoutData`` is designed to be thread-safe — it contains no Qt objects,
making it safe to compute in background threads via ``ParallelLayoutCalculator``
and consume on the main rendering thread.

ParallelLayoutCalculator
~~~~~~~~~~~~~~~~~~~~~~~~

:class:`ParallelLayoutCalculator` manages parallel text layout calculation
using thread pools. Located at :doc:`../pyzui/parallellayout`.

**Key Features:**

- **Thread Pool**: ``concurrent.futures.ThreadPoolExecutor`` for concurrent layout jobs
- **Queue-based**: Incoming layout requests are queued and dispatched
- **Thread Safety**: No Qt objects constructed on worker threads
- **Statistics**: Tracks calculation status (PENDING, IN_PROGRESS, COMPLETED, FAILED)
- **Integration**: Used by ``SceneParallelRenderer`` and ``PriorityBatcher``

Coordinate Systems and Reference Frames
----------------------------------------

Understanding the coordinate transformations is crucial for working with PyZUI.

Reference Frame Hierarchy
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    ┌─────────────────────────────────────────────────────────────┐
    │ World/Absolute Reference Frame                              │
    │ • Origin: (0, 0)                                            │
    │ • Used for: Scene positioning                               │
    └─────────────────────────────────────────────────────────────┘
                            │
                            ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ Scene Reference Frame                                       │
    │ • Origin: Scene.origin (world coords)                       │
    │ • Scaling: 2 ** Scene.zoomlevel                             │
    │ • Used for: MediaObject positioning                         │
    └─────────────────────────────────────────────────────────────┘
                            │
                            ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ MediaObject Reference Frame                                 │
    │ • Origin: MediaObject.pos (scene coords)                    │
    │ • Scaling: 2 ** MediaObject.zoomlevel                       │
    │ • Used for: Internal object coordinates (e.g., centre)      │
    └─────────────────────────────────────────────────────────────┘
                            │
                            ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ Screen/Viewport Reference Frame                             │
    │ • Origin: Top-left corner of window                         │
    │ • Units: Pixels                                             │
    │ • Used for: Rendering and mouse input                       │
    └─────────────────────────────────────────────────────────────┘

Zoom Mechanics
~~~~~~~~~~~~~~

Both Scene and MediaObject can be zoomed independently. Zoom is always centered
on a specific point to maintain visual continuity.

**Scene Zoom:**

When zooming the scene by amount ``a`` with centre point ``P``:

.. code-block:: text

    P = origin + C * (2 ** zoomlevel)

    Solving for new origin:
    origin' = P - (P - origin) * (2 ** a)
    zoomlevel' = zoomlevel + a

**MediaObject Zoom:**

When zooming a media object by amount ``a``:

.. code-block:: text

    C_s = pos + C_i * (2 ** zoomlevel_i)

    Solving for new position:
    pos' = C_s - (C_s - pos) * (2 ** a)
    zoomlevel' = zoomlevel + a

This ensures the centre point ``C`` maintains its screen position during zoom.

**ZoomManager:**

:class:`ZoomManager` enforces zoom level limits to prevent crashes at extreme
zoom levels. Located at :doc:`../pyzui/zoommanager`.

.. code-block:: python

    # Default limits
    min_zoomlevel = -10   # Minimum allowed zoom
    max_zoomlevel = 12    # Maximum allowed zoom
    clamp_enabled = True  # Enable/disable clamping

    # Methods
    clamp_zoomlevel(level)         # Clamp a single level
    is_valid_zoomlevel(level)      # Check if level is within bounds
    validate_and_clamp_zoomlevels(levels)  # Bulk clamp

Physics System
--------------

Motion and Damping
~~~~~~~~~~~~~~~~~~

All objects inherit physics simulation from :class:`PhysicalObject`. The system
uses exponential damping for smooth, natural motion.

**Damping Formula:**

.. code-block:: python

    velocity(t) = initial_velocity * (damping_factor ** -t)

    # Default damping_factor = 512
    # Velocity reduced by factor of 512 every second
    # Velocity < 0.1 is clamped to 0

**Displacement Calculation:**

.. code-block:: python

    displacement(t) = (u / log(d)) * (1 - d**-t)

    where:
        u = initial velocity
        d = damping_factor
        t = time in seconds

**Aim Method:**

The ``aim()`` method calculates the initial velocity needed to achieve a desired
displacement:

.. code-block:: python

    # Aim for displacement s that stops naturally
    obj.aim('x', s)  # s = u / log(d)

    # Aim for displacement s at specific time t
    obj.aim('x', s, t)  # s = (u/log(d)) * (1 - d**-t)

Velocity Components
~~~~~~~~~~~~~~~~~~~

Each object has three velocity components:

- ``vx``: Horizontal velocity (screen pixels per second at current zoom)
- ``vy``: Vertical velocity (screen pixels per second at current zoom)
- ``vz``: Zoom velocity (zoom levels per second)

**Step Method:**

The ``step(t)`` method advances physics simulation by time ``t``:

.. code-block:: python

    def step(self, t):
        if self.vx or self.vy:
            self.move(
                self.__displacement(t, self.vx),
                self.__displacement(t, self.vy))
            self.vx = self.__damp(self.vx, t)
            self.vy = self.__damp(self.vy, t)

        if self.vz:
            self.zoom(self.__displacement(t, self.vz))
            self.vz = self.__damp(self.vz, t)

Rendering Pipeline
------------------

Scene Rendering
~~~~~~~~~~~~~~~

The :meth:`Scene.render` method orchestrates rendering of all objects, integrating
incremental and parallel rendering strategies.

**Render Order:**

The render order (``smaller_on_top`` or ``larger_on_top``) determines how
objects are sorted:

- **smaller_on_top** (default): Objects sorted by ``onscreen_area`` ascending.
  Smaller objects render last, appearing on top.
- **larger_on_top**: Objects sorted by ``onscreen_area`` descending.
  Larger objects render last, appearing on top.

The render order also affects occlusion culling: with ``smaller_on_top``,
a small object that fills the viewport occludes larger objects behind it;
with ``larger_on_top``, large objects occlude smaller ones.

**Rendering Process:**

.. code-block:: text

    1. Sort objects by onscreen_area (direction depends on render order)

    2. Parallel Rendering (if enabled):
       - PriorityBatcher sorts text objects by viewport distance
       - Objects grouped into priority batches (HIGH → BACKGROUND)
       - ParallelLayoutCalculator computes text layouts in thread pool
       - Cached layouts avoid redundant calculation on subsequent frames

    3. Occlusion Culling:
       - Iterate objects in sort order
       - If object fills entire viewport, mark later objects as hidden
       - Render order determines which objects occlude which

    4. Assign Render Modes:
       - Hidden objects: RenderMode.Invisible
       - Draft mode: RenderMode.Draft (fast rendering)
       - Otherwise: RenderMode.HighQuality

    5. Render Each Object (in reverse sort order):
       - Reverse iteration so correct z-order is maintained
       - Topmost objects are painted last
       - Call object.render(painter, mode)
       - Catch LoadError exceptions
       - Remove objects with errors

    6. Draw Selection Borders:
       - Green border for left-click selection
       - Blue border for right-click selection

    7. Return error list

**Z-Order:** With ``smaller_on_top`` (default), smaller objects are always
rendered on top of larger objects. When objects overlap, the smaller one
will be visible and selectable. With ``larger_on_top``, the reverse applies.

**Render Modes:**

.. code-block:: python

    class RenderMode:
        Invisible = 0      # Don't render
        Draft = 1          # Fast, lower quality
        HighQuality = 2    # Slow, higher quality

PriorityBatcher
~~~~~~~~~~~~~~~

:class:`PriorityBatcher` provides viewport-aware priority batching for text
objects in parallel rendering. Located at :doc:`../pyzui/prioritybatcher`.

**Priority Levels:**

.. code-block:: python

    class BatchPriority(Enum):
        HIGH = 0       # Objects in viewport center
        MEDIUM = 1     # Objects near viewport
        LOW = 2        # Objects far from viewport
        BACKGROUND = 3 # Objects outside viewport (pre-calculation)

**How It Works:**

1. Receives current viewport center and dimensions
2. Calculates each text object's distance from viewport center
3. Assigns priority level based on distance thresholds
4. Uses heapq to sort objects by priority
5. Returns groups of objects in priority batches
6. Integrated with ``SceneParallelRenderer`` and ``ParallelLayoutCalculator``

Priority batching ensures objects closest to the user's focus are rendered
first, improving perceived performance.

Object Rendering
~~~~~~~~~~~~~~~~

Each MediaObject subclass implements its own :meth:`render` method:

**TiledMediaObject:**
- Calculates required tile level from zoom
- Determines visible tile range
- Requests and composites tiles
- Scales to match zoom
- Draws to painter

**StringMediaObject:**
- Checks if text is visible size
- Moving mode: creates QFont with scaled point size, measures text with QFontMetrics, creates QRectF for each line, draws with QPainter.drawText()
- Static mode: checks cache validity, serves pre-rendered QImage if valid, or renders new image and caches it

**SVGMediaObject:**
- Checks if SVG is visible size
- Gets content from cache or file
- Creates QRectF at scaled dimensions
- Renders with QSvgRenderer.render()

Thread Safety
~~~~~~~~~~~~~

The Scene uses ``RLock`` for thread-safe access to the object list:

.. code-block:: python

    with self.__objects_lock:
        # Thread-safe operations on self.__objects
        self.__sort_objects()
        for mediaobject in self.__objects:
            # ... render logic ...

Parallel rendering operates in background threads with explicit thread-safety
guarantees:

- ``TextLayoutData`` contains no Qt objects — safe for cross-thread use
- ``ParallelLayoutCalculator`` never creates QFont or QFontMetrics on worker threads
- All Qt operations remain on the main thread
- Thread pool is shut down cleanly via ``Scene.shutdown_threads()``

Scene Persistence
-----------------

Scenes can be saved to and loaded from .pzs files, with automatic backup
protection via the autosave subsystem.

Save Format
~~~~~~~~~~~

.. code-block:: text

    Line 1: scene.zoomlevel    scene.origin[0]    scene.origin[1]
    Line 2+: class_name    media_id    zoomlevel    pos[0]    pos[1]    [extra_fields]

    Example:
    0.0    640.0    360.0
    TiledMediaObject    image.jpg    0.5    100.0    200.0
    StringMediaObject    string:ff0000:Hello    0.0    300.0    400.0
    SVGMediaObject    svg_a1b2c3d4    0.0    500.0    300.0    width=64    height=64    is_modified=0    original_file_path=None

**Extended Fields for SVGMediaObject:**

- ``width`` / ``height``: SVG default dimensions
- ``is_modified``: Whether content was modified since original load (0 or 1)
- ``original_file_path``: Path to original file, or ``None`` for cache SVGs
- ``transparent``: Boolean flag for background transparency

**Saving Process:**

1. Store current viewport size
2. Temporarily set viewport to standard size (1280x720)
3. Write scene zoom and origin
4. Sort and write all objects (with serialized state via ``to_dict()``)
5. Trigger autosave backup if enabled
6. Restore actual viewport size

**Loading Process:**

1. Create new Scene
2. Read scene zoom and origin from first line
3. For each subsequent line:
   - Parse object type and parameters
   - Create appropriate MediaObject subclass via ``from_dict()``
   - Set zoom level, position, and extra state
   - Add to scene
4. Start autosave timer if enabled
5. Return loaded scene

Autosave Subsystem
~~~~~~~~~~~~~~~~~~

The autosave subsystem provides automatic backup creation for scene files to
prevent data loss. See :doc:`../pyzui/autosave` and :doc:`../pyzui/backupmanager`.

**Configuration:**

.. code-block:: json

    {
        "autosave": {
            "enabled": true,
            "interval": 300,
            "max_backups": 20,
            "expire_days": 7
        }
    }

**Storage Layout:**

.. code-block:: text

    ~/.pyzui/backups/
    ├── scene1_a1b2/           ← Per-scene directory (filename + 4-char hash)
    │   ├── 26_05_09_14_30_c3d4.pzs
    │   ├── 26_05_09_14_35_e5f6.pzs
    │   └── ...
    └── scene2_g7h8/
        ├── 26_05_09_14_31_i9j0.pzs
        └── ...

**Key Behaviors:**

- Each scene file gets its own backup directory
- Backup filenames are timestamp-first for chronological sorting:
  ``yy_mm_dd_hh_mm_filename_hash.pzs``
- Oldest backups are deleted when ``max_backups`` limit is exceeded
- Scene directories expire after ``expire_days`` of inactivity
- Autosave can be disabled via ``--no-autosave`` CLI flag

**BackupManager:**

:class:`BackupManager` handles the filesystem operations for the autosave
system. Located at :doc:`../pyzui/backupmanager`. Key methods:

- ``create_backup(scene, filepath)``: Creates timestamped backup
- ``rotate_backups(scene_dir, max_backups)``: Deletes oldest backups
- ``cleanup_expired(base_dir, expire_days)``: Removes expired scene directories

SVG Cache Persistence
~~~~~~~~~~~~~~~~~~~~~

SVGs created or modified via shape utilities, picker, or clipboard may be
persisted to SVGCache rather than saved as standalone files. These SVGs are
referenced in .pzs files by their cache hash (``svg_a1b2c3...``) instead
of a file path. This enables:

- Deduplication: Identical SVGs share the same cache entry
- Portability: Cache-based SVGs don't depend on original file locations
- Modification tracking: ``is_modified`` flag indicates deviation from original

Usage Examples
--------------

Creating and Populating a Scene
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pyzui.objects.scene.scene import Scene, load_scene
    from pyzui.objects.mediaobjects.tiledmediaobject import TiledMediaObject
    from pyzui.objects.mediaobjects.stringmediaobject import StringMediaObject
    from pyzui.objects.mediaobjects.svgmediaobject import SVGMediaObject

    # Create new scene with configuration
    config = {
        "render": {"order": "smaller_on_top"},
        "parallel_rendering": {"enabled": True},
        "autosave": {"enabled": True, "interval": 300, "max_backups": 20},
    }
    scene = Scene(config=config)
    scene.viewport_size = (1920, 1080)

    # Add a tiled image
    image = TiledMediaObject('path/to/large_image.jpg', scene)
    image.pos = (0, 0)
    image.zoomlevel = 0
    scene.add(image)

    # Add text
    text = StringMediaObject('string:ff0000:Welcome to PyZUI!', scene)
    text.pos = (100, 100)
    text.zoomlevel = 0
    scene.add(text)

    # Add SVG from file
    svg = SVGMediaObject('path/to/icon.svg', scene)
    svg.pos = (500, 300)
    svg.zoomlevel = 0
    scene.add(svg)

    # Save scene (triggers autosave backup if enabled)
    scene.save('my_scene.pzs')

    # Load scene later
    scene = load_scene('my_scene.pzs')
    # Autosave timer starts automatically after load

Working with Physics
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Set object velocity directly
    obj.vx = 100.0  # 100 pixels per second
    obj.vy = 50.0
    obj.vz = 0.5    # 0.5 zoom levels per second

    # Use aim() for smooth motion to target
    obj.aim('x', 500)  # Move 500 pixels right, then stop
    obj.aim('y', -200, 2.0)  # Move 200 pixels up in 2 seconds

    # Update physics (typically called each frame)
    dt = 1.0 / 60.0  # 60 FPS
    scene.step(dt)

    # Check if anything is moving
    if scene.moving:
        print("Scene or objects still in motion")

Managing Render Order
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Query current render order
    print(scene.render_order)  # "smaller_on_top" (default)

    # Toggle to larger-on-top (natural depth ordering)
    scene.set_render_order("larger_on_top")

    # Toggle back (also accessible via View menu Ctrl+R)
    scene.set_render_order("smaller_on_top")

Bulk Selection
~~~~~~~~~~~~~~

.. code-block:: python

    # Ctrl+click to select multiple objects
    # Drag to area-select
    # selection is now a list
    for obj in scene.selection:
        print(f"Selected: {obj.media_id}")

Clipboard Operations
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Copy selected objects
    scene.copy_selected()

    # Paste with offset (from last selected position)
    scene.paste()

    # Paste at specific position
    scene.paste(offset_x=100, offset_y=100)

Working with SVGCache
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import (
        get_svg_cache,
    )

    cache = get_svg_cache("/path/to/cache")

    # Store SVG content
    with open("my_shape.svg", "r") as f:
        cache_hash = cache.store_svg(f.read())

    # Create SVGMediaObject from cache
    svg = SVGMediaObject(cache_hash, scene)
    scene.add(svg)

    # Get human-readable name for display
    name = cache.get_human_readable_name(cache_hash)

    # Remove cached SVG
    cache.remove_svg(cache_hash)

Coordinate Transformations
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Get screen position of object
    screen_x, screen_y = obj.topleft

    # Get topmost (smallest) object at mouse position
    clicked_obj = scene.get((mouse_x, mouse_y))

    # Fit object to bounding box
    obj.fit((100, 100, 500, 500))  # x1, y1, x2, y2

    # Center object on screen
    obj.centre = (viewport_width / 2, viewport_height / 2)

    # Get current scale
    scale = obj.scale  # 2 ** (scene.zoom + obj.zoom)

Custom Rendering
~~~~~~~~~~~~~~~~

.. code-block:: python

    from PySide6.QtGui import QPainter

    # Create painter (typically from QWidget.paintEvent)
    painter = QPainter(widget)

    # Render scene
    errors = scene.render(painter, draft=False)

    # Handle errors
    for obj in errors:
        print(f"Failed to render: {obj.media_id}")

    # Clean up when done
    scene.shutdown_threads()

Configuring Autosave
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Enable autosave with custom settings
    from pyzui.objects.scene.sceneutils.autosave import SceneAutosaveManager

    autosave_config = {
        "enabled": True,
        "interval": 600,       # 10 minutes
        "max_backups": 50,     # Keep up to 50 backups
        "expire_days": 14,     # Clean up after 2 weeks
    }

    scene.autosave_manager.set_autosave_config(autosave_config)

    # Disable autosave
    scene.autosave_manager.disable_autosave()

    # Re-enable with default settings
    scene.autosave_manager.enable_autosave()

    # Check status
    if scene.autosave_manager.is_autosave_enabled():
        interval = scene.autosave_manager.get_autosave_interval()
        print(f"Autosave active, interval: {interval}s")

API Reference
-------------

Key Classes
~~~~~~~~~~~

- :class:`pyzui.objects.physicalobject.PhysicalObject` - Base physics simulation
- :class:`pyzui.objects.mediaobjects.mediaobject.MediaObject` - Abstract media object
- :class:`pyzui.objects.mediaobjects.tiledmediaobject.TiledMediaObject` - Tiled images
- :class:`pyzui.objects.mediaobjects.stringmediaobject.StringMediaObject` - Text objects
- :class:`pyzui.objects.mediaobjects.svgmediaobject.SVGMediaObject` - Vector graphics
- :class:`pyzui.objects.scene.scene.Scene` - Scene container and coordinator

Scene Sub-Managers
~~~~~~~~~~~~~~~~~~

- :class:`pyzui.objects.scene.sceneutils.parallel.SceneParallelRenderer` - Parallel rendering
- :class:`pyzui.objects.scene.sceneutils.autosave.SceneAutosaveManager` - Autosave orchestration
- :class:`pyzui.objects.scene.sceneutils.clipboard.SceneClipboardManager` - Copy/paste operations

Rendering Utilities
~~~~~~~~~~~~~~~~~~~

- :class:`pyzui.objects.scene.sceneutils.prioritybatcher.PriorityBatcher` - Priority-based batching
- :class:`pyzui.objects.mediaobjects.mediaobjectsutils.string.parallellayout.ParallelLayoutCalculator` - Thread-pool text layout
- :class:`pyzui.objects.mediaobjects.mediaobjectsutils.string.textlayout.TextLayoutData` - Pre-calculated layouts

Zoom and Backup
~~~~~~~~~~~~~~~

- :class:`pyzui.objects.objectsutils.zoom.zoommanager.ZoomManager` - Zoom level clamping
- :class:`pyzui.backup.backupmanager.BackupManager` - Backup storage management
- :class:`pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache.SVGCache` - SVG disk cache

For detailed API documentation, see the individual class documentation pages.

See Also
--------

- :doc:`tilingsystem` - Details on tile pyramid and caching
- :doc:`pyzui/objects/mediaobjects/tiledmediaobject` - TiledMediaObject implementation details
- :doc:`projectstructure` - Overall project architecture
- :doc:`../pyzui/autosave` - SceneAutosaveManager API
- :doc:`../pyzui/clipboard` - SceneClipboardManager API
- :doc:`../pyzui/parallel` - SceneParallelRenderer API
- :doc:`../pyzui/prioritybatcher` - PriorityBatcher API
- :doc:`../pyzui/parallellayout` - ParallelLayoutCalculator API
- :doc:`../pyzui/textlayout` - TextLayoutData API
- :doc:`../pyzui/zoommanager` - ZoomManager API
- :doc:`../pyzui/backupmanager` - BackupManager API
- :doc:`../pyzui/svgcache` - SVGCache API
- :doc:`../pyzui/svgarrowutils` - Arrow shape utility
- :doc:`../pyzui/svgcircleutils` - Circle shape utility
- :doc:`../pyzui/svgsquareutils` - Square shape utility
- :doc:`../pyzui/svgtriangleutils` - Triangle shape utility
- :doc:`../pyzui/converterrunner` - Process-based parallel conversion
