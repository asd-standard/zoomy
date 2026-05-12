.. SVG Ecosystem Documentation

SVG Utility Ecosystem
=====================

This document provides a comprehensive overview of the SVG utility ecosystem in PyZUI,
explaining the content-addressable SVG cache, the five shape-type-specific detection and
elongation utilities, their shared architecture patterns, and their integration with the
scene widget and dialog system.

Overview
--------

The SVG utility ecosystem is responsible for:

1. Storing and retrieving SVG content via a content-addressable disk cache
2. Detecting the shape type of loaded SVG content (arrow, stick, circle, square, triangle)
3. Elongating shapes interactively via mouse wheel with modifier keys
4. Managing the ``svg_`` hash-prefix addressing scheme used across the application
5. Modifying SVG stroke color and line thickness via dialog controls

The ecosystem spans **6 files** (~2,620 lines total) organized into a cache layer
and five parallel shape utility modules. All utilities share a common architecture:
XML namespace-aware ElementTree parsing, content-addressable cache integration,
and non-destructive (hash-returning) transformation pipelines.

Architecture
------------

.. code-block:: text

    ┌─────────────────────────────────────────────────────────────────┐
    │                        QZUI Widget                              │
    │  (wheelEvent: Ctrl+wheel on selected SVG triggers elongation)   │
    └─────────────┬───────────────────────────────────────────────────┘
                  │
                  │ Import from mediaobjectsutils.svg.utils
                  │
    ┌─────────────▼───────────────────────────────────────────────────┐
    │                    Shape Detection Cascade                      │
    │  is_straight_arrow_svg? → elongate_straight_arrow()             │
    │  is_diagonal_arrow_svg? → elongate_diagonal_arrow()             │
    │  is_square_svg?         → elongate_square()                     │
    │  is_circle_svg?         → elongate_circle()                     │
    │  is_triangle_svg?       → elongate_triangle()                   │
    │  is_stick_svg?          → elongate_stick()                      │
    └─────────────┬───────────────────────────────────────────────────┘
                  │
                  │ All functions parse SVG via _load_svg_tree()
                  │ (resolves file path OR svg_ cache hash)
                  │
    ┌─────────────▼───────────────────────────────────────────────────┐
    │                     Shape Utility Modules                       │
    │  svgarrowutils.py    (663 lines) — arrow + diagonal             │
    │  svgstickutils.py    (565 lines) — stick/line + diagonal        │
    │  svgcircleutils.py   (391 lines) — circle/ellipse               │
    │  svgtriangleutils.py (398 lines) — triangle                     │
    │  svgsquareutils.py   (326 lines) — square/rectangle             │
    │                                                                 │
    │  Shared patterns across all 5 modules:                          │
    │  • _load_svg_tree() — file-or-cache → ElementTree               │
    │  • SVG_NS = {'svg': 'http://www.w3.org/2000/svg'}               │
    │  • Elongation → store in cache → return svg_ hash               │
    │  • viewBox recalculation with 10%/20px padding                  │
    └─────────────┬───────────────────────────────────────────────────┘
                  │
                  │ Store / retrieve via cache hash
                  │
    ┌─────────────▼───────────────────────────────────────────────────┐
    │                       SVGCache                                  │
    │  • Storage: /tmp/pyzui_svg_/ (flat directory)                   │
    │  • Addressing: svg_{8-char SHA1} content hash                   │
    │  • store_svg() — deduplicate, validate, write                   │
    │  • get_svg_content() — read by hash                             │
    │  • cleanup_on_exit() — remove all files on exit                 │
    └────────────────────────────┬────────────────────────────────────┘
                                 │
                                 │ Consumed by
                                 │
    ┌────────────────────────────┼────────────────────────────────────┐
    │                            ▼                                    │
    │  ┌──────────────────┐  ┌────────────────┐  ┌─────────────────┐  │
    │  │ SVGMediaObject   │  │ SVG Picker     │  │ SVG Modifier    │  │
    │  │ • _get_svg_      │  │ Dialog         │  │ Dialog          │  │
    │  │   load_path()    │  │ • _modify_     │  │ • Uses cache    │  │
    │  │ • svg_ prefix    │  │   svg_file()   │  │   for modified  │  │
    │  │   detection      │  │ • Direct ET    │  │   SVGs          │  │
    │  └──────────────────┘  └────────────────┘  └─────────────────┘  │
    └─────────────────────────────────────────────────────────────────┘

SVGCache
--------

:class:`SVGCache` provides a content-addressable disk cache for SVG data.
All elongation results and picker-created SVGs are stored here.

**Storage Layout:**

.. code-block:: text

    /tmp/pyzui_svg_/
    ├── svg_a1b2c3d4.svg
    ├── svg_e5f6a7b8.svg
    └── ...

Content is stored in a flat directory with no subdirectory hierarchy.
Each file is named ``{hash}.svg`` where the hash is the first 8 characters
of a SHA1 digest of the UTF-8 SVG XML content.

**Content Addressing:**

.. code-block:: python

    import hashlib

    def compute_svg_hash(svg_content: str) -> str:
        return f"svg_{hashlib.sha1(svg_content.encode('utf-8')).hexdigest()[:8]}"

The ``svg_`` prefix is the universal discriminator — every consumer
detects cache references by checking ``if media_id.startswith('svg_')``.

**Singleton Access:**

.. code-block:: python

    from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import (
        get_svg_cache,
    )

    cache = get_svg_cache()
    # Always returns the same SVGCache instance

The singleton is lazily created on first access and stored at module level
in a private ``_svg_cache_instance`` variable.

**Public API:**

.. list-table::
   :header-rows: 1

   * - Method
     - Signature
     - Returns
     - Description
   * - ``store_svg``
     - ``(svg_content: str, max_retries: int = 3) -> str``
     - cache hash
     - Validate, deduplicate, write to disk. Retries on write failure.
   * - ``get_cache_path``
     - ``(content_hash: str) -> Path``
     - file path
     - Resolve hash to filesystem path
   * - ``has_hash``
     - ``(content_hash: str) -> bool``
     - boolean
     - Check if hash exists on disk
   * - ``get_svg_content``
     - ``(content_hash: str) -> str | None``
     - SVG string
     - Read from cache; returns None on miss
   * - ``cleanup_old_files``
     - ``(max_age_days: int = 14) -> tuple[int, int]``
     - ``(files_removed, bytes_freed)``
     - Time-based removal
   * - ``cleanup_on_exit``
     - ``() -> None``
     - —
     - Remove all cache files on program exit
   * - ``get_cache_stats``
     - ``() -> dict``
     - statistics
     - File count, total size, MB

**Retry Logic:**

On write failure, ``store_svg()`` appends ``<!-- retry_N -->`` to the SVG
content to produce a new hash, then retries up to ``max_retries`` times.
This handles rare hash collisions and transient filesystem errors.

XML Parsing and Namespace Handling
----------------------------------

All shape utilities use Python's ``xml.etree.ElementTree`` for SVG parsing.
The SVG namespace is defined as a module-level constant in every utility:

.. code-block:: python

    SVG_NS = {'svg': 'http://www.w3.org/2000/svg'}

**Parsing Patterns:**

.. list-table::
   :header-rows: 1

   * - Operation
     - API Used
   * - Load from file
     - ``ET.parse(filepath).getroot()``
   * - Load from cache string
     - ``ET.fromstring(svg_content)`` then ``ET.ElementTree(root)``
   * - Find single element
     - ``root.find('.//svg:tagname', SVG_NS)``
   * - Find all elements
     - ``root.findall('.//svg:tagname', SVG_NS)``
   * - Read numeric attr
     - ``float(element.get('attr', 0))`` with try/except
   * - Modify attr
     - ``element.set('attr', str(value))``
   * - Serialize to string
     - ``ET.tostring(root, encoding='utf-8').decode('utf-8')``

**Tag Name Expansion:**

When programmatically changing an element's tag (e.g., circle to ellipse),
the fully expanded namespace form is required:

.. code-block:: python

    circle.tag = '{http://www.w3.org/2000/svg}ellipse'

This is a subtlety of ElementTree — tags are stored internally in
``{namespace}localname`` format.

Shape Detection
---------------

Each utility provides ``is_*_svg()`` detection functions that inspect
SVG element structure to determine whether a given SVG matches a known shape.

**Shared Loader:**

All detection functions use a common internal helper:

.. code-block:: python

    def _load_svg_tree(svg_input: str) -> ET.ElementTree:
        if svg_input.startswith('svg_'):
            content = get_svg_cache().get_svg_content(svg_input)
            root = ET.fromstring(content)
            return ET.ElementTree(root)
        else:
            return ET.parse(svg_input)

This adapter makes all detection functions transparently support both
file paths and cache hashes.

**Detection Matrix:**

.. list-table::
   :header-rows: 1

   * - Shape
     - Detection Function
     - SVG Elements Checked
     - Key Validation
   * - **Straight Arrow**
     - ``is_straight_arrow_svg()``
     - 1 ``<line>`` + 1 ``<polygon>``
     - Line must be horizontal (Δy < 0.1) or vertical (Δx < 0.1)
   * - **Diagonal Arrow**
     - ``is_diagonal_arrow_svg()``
     - 1 ``<line>`` + 1 ``<polygon>``
     - Dx ≈ Dy within 10% tolerance
   * - **Any Arrow**
     - ``is_arrow_svg()``
     - (composite)
     - Straight OR diagonal
   * - **Straight Stick**
     - ``is_straight_stick_svg()``
     - 1 ``<line>``, 0 ``<polygon>``
     - No arrowhead present
   * - **Diagonal Stick**
     - ``is_diagonal_stick_svg()``
     - 1 ``<line>``, 0 ``<polygon>``
     - No arrowhead, 45° alignment
   * - **Any Stick**
     - ``is_stick_svg()``
     - (composite)
     - Straight OR diagonal
   * - **Circle**
     - ``is_circle_svg()``
     - 1 ``<circle>`` OR 1 ``<ellipse>``
     - Validates cx, cy, r (circle); cx, cy, rx, ry (ellipse)
   * - **Square**
     - ``is_square_svg()``
     - 1 ``<rect>``
     - Validates x, y, width, height are numeric and > 0
   * - **Triangle**
     - ``is_triangle_svg()``
     - 1 ``<polygon>`` with 3 points, 0 ``<line>``
     - Distinguishes from arrows by requiring zero ``<line>`` elements

**Arrow vs Stick Distinction:**

The critical difference is **element count**: arrows have 1 ``<line>``
plus 1 ``<polygon>`` (the arrowhead), while sticks have only 1 ``<line>``
and zero polygons. The triangle utility additionally checks for zero
``<line>`` elements to avoid misclassifying arrows as triangles.

Shape Elongation
----------------

Elongation transforms a shape's dimensions by a scale factor, producing
a modified copy stored in SVGCache. All elongation functions are
**non-destructive** — the original file is never modified.

**Entry Point — QZUI Wheel Event:**

.. code-block:: text

    User scrolls wheel on selected SVG object
            │
            ▼
    QZUI.wheelEvent() checks modifier keys:
    • Ctrl only     → 1D elongation (arrows, sticks)
    • Ctrl+Shift    → 2D Y-only  (squares, circles, triangles)
    • Shift only    → 2D X-only  (squares, circles, triangles)
    • Ctrl+Shift    → 2D proportional
            │
            ▼
    Detection cascade (first match wins):
    1. is_straight_arrow_svg()?  → elongate_straight_arrow()
    2. is_diagonal_arrow_svg()?  → elongate_diagonal_arrow()
    3. is_square_svg()?          → elongate_square()
    4. is_circle_svg()?          → elongate_circle()
    5. is_triangle_svg()?        → elongate_triangle()
    6. is_stick_svg()?           → elongate_stick()
    7. (fall through to normal zoom)
            │
            ▼
    Result: svg_ hash updated on SVGMediaObject._media_id
            QSvgRenderer reloaded from cache path
            Object dimensions updated and repainted

**Scale Factor Calculation:**

.. code-block:: python

    degrees = event.angleDelta().y()
    elongation_delta = degrees / 360.0
    current_factor = max(1.0 + elongation_delta, 0.2)
    # 720° scroll = factor of 2.0 (doubling)
    # Minimum factor clamped to 0.2

Arrow Elongation
~~~~~~~~~~~~~~~~

**Functions:** ``elongate_straight_arrow()``, ``elongate_diagonal_arrow()``

**Algorithm:**

1. Load SVG via ``_load_svg_tree()`` and detect direction
2. Scale the line endpoint: ``new_x2 = x1 + (x2 - x1) * scale_factor``
3. Translate the 3-point polygon (arrowhead) by the same ``(dx, dy)``
   offset — **uniform translation, not scaling**; the arrowhead maintains
   its original size
4. Recompute ``viewBox`` to encompass all points with padding
   (10% of SVG dimensions or 20px, whichever is larger)
5. Supports negative coordinates in viewBox for left/upward extensions
6. Serialize, store in cache, return cache hash

Stick Elongation
~~~~~~~~~~~~~~~~

**Functions:** ``elongate_stick()`` → dispatches to ``elongate_straight_stick()``
or ``elongate_diagonal_stick()``

**Algorithm:**

Same as arrow elongation but without the arrowhead translation step.
Sticks have only a ``<line>`` element — the endpoint is scaled along the
direction of elongation.

Circle/ellipse Elongation
~~~~~~~~~~~~~~~~~~~~~~~~~

**Function:** ``elongate_circle(svg_path, scale_x, scale_y)``

**Algorithm:**

1. Find ``<circle>`` or ``<ellipse>`` element
2. For proportional scaling: update ``r`` attribute (circle) or ``rx``/``ry`` (ellipse)
3. For non-proportional scaling of a circle: **convert to ellipse** by changing
   ``tag`` to ``{ns}ellipse``, setting ``rx``/``ry``, and removing ``r``
4. Compute axis-aligned bounding box from ``(cx - rx, cy - ry)`` to ``(cx + rx, cy + ry)``
5. Recompute viewBox with padding; serialize; cache; return hash

Triangle Elongation
~~~~~~~~~~~~~~~~~~~

**Function:** ``elongate_triangle(svg_path, scale_x, scale_y)``

**Algorithm:**

1. Parse the 3-point ``<polygon>`` using ``_parse_polygon_points()``
2. Calculate centroid via ``_calculate_triangle_centroid()`` (arithmetic mean)
3. Scale all 3 vertices outward from centroid using ``_scale_points_from_center``
   with separate X and Y factors
4. Format points to 6 decimal precision
5. Recompute bounding box, apply padding, update viewBox
6. Serialize; cache; return hash

Square/Rectangle Elongation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Function:** ``elongate_square(svg_path, scale_x, scale_y)``

**Algorithm:**

1. Read current ``x``, ``y``, ``width``, ``height`` from ``<rect>``
2. Compute center: ``center_x = x + width/2``, ``center_y = y + height/2``
3. Scale dimensions: ``new_width = width * scale_x``, ``new_height = height * scale_y``
4. Recompute position keeping center fixed: ``new_x = center_x - new_width/2``
5. Update all four attributes on the ``<rect>`` element
6. Recompute viewBox from corner points; serialize; cache; return hash

Shared viewBox Update Pattern
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All elongation functions share the same viewBox recalculation logic:

.. code-block:: python

    default_padding = 20.0
    padding_x = max(current_width * 0.1, 20.0)
    padding_y = max(current_height * 0.1, 20.0)

    padded_min_x = min_x - padding_x * 0.5
    padded_max_x = max_x + padding_x * 0.5
    # ... same for Y ...

    root.set('viewBox', f"{padded_min_x} {padded_min_y} "
                        f"{padded_max_x - padded_min_x} "
                        f"{padded_max_y - padded_min_y}")
    root.set('width', str(viewbox_width))
    root.set('height', str(viewbox_height))

The padding is 10% of current SVG dimensions with a 20px floor.
Half-padding is applied to each side. The viewBox supports negative
min values so shapes extending left/up of the origin render correctly.

Direction Detection
-------------------

Arrow and stick utilities provide direction-detection functions that
classify the orientation of the shape:

.. list-table::
   :header-rows: 1

   * - Shape
     - Function
     - Directions
   * - Straight Arrow
     - ``get_arrow_direction()``
     - ``right``, ``left``, ``up``, ``down``
   * - Diagonal Arrow
     - ``get_diagonal_arrow_direction()``
     - ``upright``, ``upleft``, ``downright``, ``downleft``
   * - Straight Stick
     - ``get_straight_stick_direction()``
     - ``horizontal``, ``vertical``
   * - Diagonal Stick
     - ``get_diagonal_stick_direction()``
     - ``upright``, ``upleft``, ``downright``, ``downleft``
   * - Stick (composite)
     - ``get_stick_direction()``
     - tries straight first, then diagonal

Bounds Query Functions
~~~~~~~~~~~~~~~~~~~~~~

Three shape utilities provide bounding-box query functions:

- ``get_circle_bounds()`` → ``(cx, cy, rx, ry)`` — for circles, ``rx = ry = r``
- ``get_triangle_bounds()`` → ``(min_x, min_y, width, height)``
- ``get_rectangle_bounds()`` → ``(x, y, width, height)``

Integration with Dialogs
------------------------

OpenSVGPickerInputDialog
~~~~~~~~~~~~~~~~~~~~~~~~

The SVG picker dialog (**File > Open new SVG**, Ctrl+G) creates new SVG
objects from a browser of ``data/SVG/`` files. It performs **inline XML
manipulation** (not using the shape utility modules) for color/thickness:

.. code-block:: text

    1. User selects SVG file + color + thickness
    2. _modify_svg_file() parses SVG with ET
    3. Applies color to stroke/fill attributes
    4. Applies thickness to stroke-width
    5. Stores result in SVGCache via store_svg()
    6. Returns cache hash as media_id

ModifySVGInputDialog
~~~~~~~~~~~~~~~~~~~~

The SVG modifier dialog (right-click on SVG object) allows changing
stroke color and line thickness of existing SVG shapes:

.. code-block:: text

    1. Loads current SVG content from cache or file
    2. User selects new color and/or thickness
    3. SVG XML is modified in place (stroke, stroke-width)
    4. Result stored in SVGCache with new content hash
    5. Object's media_id updated to new hash
    6. is_modified flag set to True

Unlike the picker, the modifier dialog interacts with SVGCache but does
not use the shape detection/elongation utilities — it operates on
general SVG content rather than detecting specific shapes.

Export Chain
------------

The utilities are exported through a layered module hierarchy:

.. code-block:: text

    mediaobjectsutils/__init__.py       ← Top-level re-export (29 names)
        ├── svg.svgcache.svgcache       → SVGCache, compute_svg_hash, get_svg_cache
        └── svg.utils                   → All shape detection and elongation functions
            ├── svgarrowutils.py        → 8 functions
            ├── svgstickutils.py        → 9 functions
            ├── svgcircleutils.py       → 3 functions
            ├── svgtriangleutils.py     → 3 functions
            └── svgsquareutils.py       → 3 functions

**Import Locations:**

.. list-table::
   :header-rows: 1

   * - Consumer
     - Imports From
     - Used For
   * - ``qzui.py``
     - ``svg.utils`` (direct)
     - Shape detection cascade + elongation in wheelEvent
   * - ``SVGMediaObject``
     - ``svg.svgcache``
     - Resolve cache hashes to file paths for QSvgRenderer
   * - ``OpenSVGPickerInputDialog``
     - ``svg.svgcache`` + ``xml.etree.ElementTree``
     - Create/cache colorized SVGs with inline XML manipulation
   * - ``ModifySVGInputDialog``
     - ``svg.svgcache``
     - Cache modified SVG content

Usage Example
-------------

Programmatic Shape Detection and Elongation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pyzui.objects.mediaobjects.mediaobjectsutils.svg import (
        is_arrow_svg,
        is_circle_svg,
        is_square_svg,
        is_triangle_svg,
        is_stick_svg,
        elongate_square,
    )

    svg_path = "data/SVG/red_square.svg"

    # Detect shape type
    if is_square_svg(svg_path):
        print("Detected: square")

        # Elongate by factor 2.0 in X and 1.5 in Y
        new_hash = elongate_square(svg_path, scale_x=2.0, scale_y=1.5)
        print(f"Elongated SVG cached as: {new_hash}")

    elif is_circle_svg(svg_path):
        print("Detected: circle")

    elif is_triangle_svg(svg_path):
        print("Detected: triangle")

Working with SVGCache
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import (
        get_svg_cache,
        compute_svg_hash,
    )

    cache = get_svg_cache()

    # Store SVG content
    with open("my_custom.svg") as f:
        content = f.read()

    svg_hash = cache.store_svg(content)
    print(f"Stored as: {svg_hash}")  # e.g., svg_a1b2c3d4

    # Retrieve content
    cached = cache.get_svg_content(svg_hash)
    print(f"Content length: {len(cached)} bytes")

    # Get file path for QSvgRenderer
    path = cache.get_cache_path(svg_hash)
    print(f"On disk: {path}")  # /tmp/pyzui_svg_/svg_a1b2c3d4.svg

    # Compute hash without storing
    hash_only = compute_svg_hash("<svg>...</svg>")
    print(f"Would be stored as: {hash_only}")

    # Cleanup
    files_removed, bytes_freed = cache.cleanup_old_files(max_age_days=7)
    print(f"Cleaned up {files_removed} files, freed {bytes_freed} bytes")

See Also
--------

- :doc:`../usageinstructions/svgfeatures` — User-facing SVG features guide
- :doc:`windowsystem` — SVG picker and modifier dialog details
- :doc:`objectsystem` — SVGMediaObject and shape integration
- :doc:`../pyzui/svgcache` — SVGCache API reference
- :doc:`../pyzui/svgarrowutils` — Arrow utility API reference
- :doc:`../pyzui/svgcircleutils` — Circle utility API reference
- :doc:`../pyzui/svgsquareutils` — Square utility API reference
- :doc:`../pyzui/svgtriangleutils` — Triangle utility API reference
