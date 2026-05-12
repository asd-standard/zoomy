.. String Media Object Ecosystem Documentation

String Media Object Ecosystem
==============================

This document provides a comprehensive overview of the parallel text rendering
pipeline in PyZUI, explaining how ``StringMediaObject`` renders text using a
hybrid dual-mode approach, viewport-aware priority batching, and thread-pool-based
layout pre-calculation to maintain sharp rendering during zoom and high quality
when stationary.

Overview
--------

The string rendering ecosystem is responsible for:

1. Rendering text strings at any zoom level with automatic font scaling
2. Switching between a fast moving-mode (direct ``drawText`` or parallel layout)
   and a high-quality static mode (cached ``QImage`` blitting)
3. Pre-calculating text layouts in background threads to avoid blocking the
   render loop
4. Prioritizing objects closest to the viewport center via distance-based batching
5. Caching pre-calculated layouts and rendered images to minimize redundant work

The system spans **5 components** across 5 files (~2,200 lines total) organized
as a five-layer pipeline from ``StringMediaObject.render()`` through
``PriorityBatcher`` → ``ParallelLayoutCalculator`` → ``TextLayoutData``
→ ``SceneParallelRenderer``.

Architecture
------------

.. code-block:: text

    Scene.render(painter, draft)
    │
    ├─ [scene.vzmoving = True] ───────────────────────────────────────────┐
    │                                                                     │
    │   SceneParallelRenderer.precalculate_text_layouts()                 │
    │   │                                                                 │
    │   ├─ _get_text_objects() → all StringMediaObjects [RLock]           │
    │   │                                                                 │
    │   ├─ PriorityBatcher.update_viewport() → clear batches              │
    │   ├─ PriorityBatcher.add_objects() → register all objects           │
    │   ├─ PriorityBatcher.create_batches()                               │
    │   │       │                                                         │
    │   │       ├─ calculate_distance() → Euclidean to viewport center    │
    │   │       ├─ get_priority() → HIGH / MEDIUM / LOW / BACKGROUND      │
    │   │       └─ heapq sorted into batches of batch_size                │
    │   │                                                                 │
    │   └─ For each batch:                                                │
    │         ParallelLayoutCalculator.submit_batch(batch, viewport, cb)  │
    │               │                                                     │
    │               ├─ Check results_cache [RLock] → reuse if valid       │
    │               └─ MISS → dispatch to WORKER THREADS:                 │
    │                     TextLayoutData.from_string_object(obj, viewport)│
    │                     → plain data, NO Qt objects constructed         │
    │                     → stored under RLock, callback invoked          │
    │                                                                     │
    │   SceneParallelRenderer.render_text(painter)                        │
    │   │                                                                 │
    │   └─ For each batch / PrioritizedObject:                            │
    │         layout_data = get_layout_cache(index)                       │
    │         if valid and not stale:                                     │
    │             obj.render_with_layout(painter, layout_data)            │
    │             → TextLayoutData.render(painter) [MAIN THREAD]          │
    │             → to_qfont() constructs QFont safely on main thread     │
    │             → drawText() per line                                   │
    │                                                                     │
    └─ Main render loop: skip already-parallel-rendered text objects────── 
                                                                          
    ├─ [scene.vzmoving = False] ──────────────────────────────────────────┐
    │                                                                     │
    │   StringMediaObject.render(painter, mode) [via main loop]           │
    │   │                                                                 │
    │   ├─ __is_image_cache_valid(scale, mode)?                           │
    │   │   YES → painter.drawImage(__cached_text_image)  [instant]       │
    │   │   NO  → __render_text_to_image() → cache → drawImage            │
    │   │                                                                 │
    │   └─ Cache stores: image, scale, mode, content hash                 │
    └─────────────────────────────────────────────────────────────────────

Dual-Mode Decision Logic
------------------------

The entire mode decision hinges on a single property: **``Scene.vzmoving``**.

**Definition** (from ``PhysicalObject``):

.. code-block:: python

    @property
    def vzmoving(self) -> bool:
        if self.vz != 0:
            return True
        for mediaobject in self.__objects:
            if mediaobject.vzmoving:
                return True
        return False

``vzmoving`` is ``True`` when **any zoom velocity is non-zero** — the scene's
own ``vz`` or any contained object's ``vz``. Velocity is damped exponentially:
when ``abs(vz) < 0.4`` it is clamped to zero, and ``vzmoving`` becomes ``False``.

**Decision Matrix:**

.. list-table::
   :header-rows: 1

   * - Condition
     - Render Path
     - Purpose
   * - ``vzmoving=True``, parallel layout valid
     - ``render_with_layout()`` via ``TextLayoutData``
     - Fast parallel rendering from pre-calculated layout
   * - ``vzmoving=True``, no parallel layout
     - ``__render_text_direct()`` / ``QPainter.drawText()``
     - Smooth zoom fallback
   * - ``vzmoving=False``, image cache valid
     - ``painter.drawImage(cached)``
     - Maximum quality, zero recomputation
   * - ``vzmoving=False``, cache invalid
     - ``__render_text_to_image()`` → cache → ``drawImage``
     - First frame after movement stops

**Mode Transition:**

When the scene transitions from static to moving, ``__was_static`` triggers
``invalidate_cache()`` immediately to prevent stale cached images from being
blitted during movement.

Cache State Machine
-------------------

Image Cache (Static Mode)
~~~~~~~~~~~~~~~~~~~~~~~~~

Four state variables control the static-mode image cache:

.. list-table::
   :header-rows: 1

   * - Variable
     - Type
     - Purpose
   * - ``__cached_text_image``
     - ``QImage | None``
     - Rendered text as a premultiplied ARGB image
   * - ``__cached_image_scale``
     - ``float | None``
     - Scale at which the image was rendered
   * - ``__cached_image_mode``
     - ``int | None``
     - Render mode (Draft / HighQuality) used
   * - ``__cached_text_hash``
     - ``int | None``
     - Combined hash of text content and color

**Cache Validation (``__is_image_cache_valid()``):**

The cache is **valid** only if ALL of these conditions are true:

1. ``__cached_text_image`` is not ``None``
2. Scale mode metadata is not ``None``
3. Neither the cached nor current scale is zero
4. **Relative scale difference ≤ 1%**: ``|current - cached| / cached ≤ 0.01``
5. **Mode matches**: ``mode == __cached_image_mode``
6. **Content hash matches**: ``__compute_text_hash() == __cached_text_hash``

**Invalidation:**

``invalidate_cache()`` clears all image cache state. Triggered by:
- Movement starting (``__was_static`` was ``True``, ``vzmoving`` becomes ``True``)
- Text content changed (``lines`` setter)
- Manual call via public API

Layout Cache (Moving Mode)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pre-calculated layouts are managed by ``PriorityBatcher`` and
``ParallelLayoutCalculator``, not by ``StringMediaObject`` directly.
Layouts are considered **stale** after 1000 ms (configurable via
``cache_max_age_ms``).

Priority Batcher
----------------

:class:`PriorityBatcher` organizes text objects into priority batches based on
their distance from the viewport center, ensuring objects closest to the user's
focus are rendered first.

**Priority Levels:**

- ``BatchPriority.HIGH`` — ≤ 1000 scene units, rendered first
- ``BatchPriority.MEDIUM`` — ≤ 2000 scene units, rendered second
- ``BatchPriority.LOW`` — ≤ 4000 scene units, rendered third
- ``BatchPriority.BACKGROUND`` — > 4000 scene units, off-screen pre-calculation

**Batching Algorithm:**

.. code-block:: text

    1. For each StringMediaObject with text and valid position:
       a. Calculate Euclidean distance to viewport center
       b. Map distance to a BatchPriority via thresholds
       c. Create PrioritizedObject(priority, distance, index, obj)
       d. Push onto a min-heap (lower priority value = higher importance)

    2. Objects outside viewport → downgraded to BACKGROUND

    3. Pop from heap into batches of batch_size (default: 10)
       Stop after max_batches batches (default: 10)
       Skip BACKGROUND objects once ≥ half of max_batches are filled

This produces groups of objects ordered by importance, with background objects
only included when there is spare capacity.

Parallel Layout Calculator
---------------------------

:class:`ParallelLayoutCalculator` manages concurrent text layout computation
using a thread pool. It dispatches layout jobs to worker threads and caches
results for reuse.

**Thread Pool:**

- Default workers: ``min(32, cpu_count + 4)``; configurable via ``max_workers``
- Bounded queue: ``queue.Queue(maxsize=100)`` prevents memory blowout
- Workers are **daemon threads** — won't block process exit
- ``shutdown_event`` (``threading.Event``) for coordinated shutdown
- Each worker runs ``_worker_loop()`` with ``queue.get(timeout=0.1)`` polling

**Cache-First Strategy:**

When processing a calculation:

1. Check ``results_cache`` under ``threading.RLock``
2. If a ``COMPLETED`` result exists with non-stale layout data → **reuse**
3. On cache miss: call ``TextLayoutData.from_string_object(obj, viewport)``
   on the worker thread (extracts only plain Python data)
4. Store result under lock, invoke callback if provided

**CalculationResult:**

.. code-block:: python

    @dataclass
    class CalculationResult:
        status: CalculationStatus      # PENDING / IN_PROGRESS / COMPLETED / FAILED
        layout_data: TextLayoutData | None
        error: Exception | None
        processing_time_ms: float
        timestamp: float

Text Layout Data
----------------

:class:`TextLayoutData` is a dataclass storing pre-calculated text layout
information. It is the **thread-safety boundary** between the worker-thread
layout calculation and the main-thread rendering.

**Design Principle:**

All data is stored as plain Python types — no Qt GUI objects (``QFont``,
``QColor``) are stored or constructed until ``render()`` is called on the
main thread.

**Key Fields:**

.. list-table::
   :header-rows: 1

   * - Field
     - Type
     - Purpose
   * - ``text``
     - ``str``
     - The full string content
   * - ``font_family``
     - ``str``
     - Font family name (e.g. ``"Sans Serif"``)
   * - ``font_pointsize``
     - ``float``
     - Scaled font point size
   * - ``font_weight``
     - ``int``
     - Integer weight constant (not a QFont object)
   * - ``color_r/g/b/a``
     - ``int``
     - RGBA components (decomposed from QColor)
   * - ``bounding_rect``
     - ``QRectF``
     - Object bounding box (value type, thread-safe)
   * - ``line_rects``
     - ``list[QRectF]``
     - Per-line bounding rects for multiline text
   * - ``timestamp``
     - ``float``
     - Milliseconds since epoch (staleness check)
   * - ``is_valid``
     - ``bool``
     - Manual invalidation flag

**Worker-Thread Factory: ``from_string_object(obj, viewport)``**

Extracts layout data from a ``StringMediaObject`` **without constructing
any Qt GUI objects**:

1. Reads text via ``obj._get_text()`` → ``str``
2. Reads font properties via ``obj._get_font()`` → ``dict`` (NOT QFont)
3. Reads color components via ``obj._get_color().red()/.green()/...()`` → ``int``
   (read-only access to QColor components, safe from any thread)
4. Reads position, width, height as plain Python values
5. Returns a fully populated ``TextLayoutData``

**Main-Thread Renderer: ``render(painter)``**

Constructs Qt objects **on the calling thread** (must be main thread):

.. code-block:: python

    def render(self, painter):
        font = self.to_qfont()    # Constructs QFont HERE
        color = self.to_qcolor()  # Constructs QColor HERE
        painter.setFont(font)
        painter.setPen(color)
        for line_rect in self.line_rects:
            painter.drawText(line_rect, self.text)

Layout data is considered **stale** after 1000 ms (configurable) and is
recalculated on the next render cycle if expired.

Scene Parallel Renderer
------------------------

:class:`SceneParallelRenderer` orchestrates the entire parallel rendering
pipeline from within ``Scene.render()``.

**Per-Frame Integration:**

.. code-block:: text

    Scene.render(painter, draft)
    │
    ├─ If vzmoving and enabled:
    │   precalculate_text_layouts()
    │       ├─ _get_text_objects() [RLock]
    │       ├─ PriorityBatcher.add_objects() → create_batches()
    │       └─ submit_batch() × N → worker threads
    │
    ├─ If vzmoving and enabled:
    │   render_text(painter)
    │       ├─ For each batch, each PrioritizedObject:
    │       │   layout_data → if valid → render_with_layout()
    │       └─ Collect ids → skip in main loop
    │
    └─ Main render loop:
        For each mediaobject:
          if StringMediaObject and id in parallel_rendered → SKIP
          else → mediaobject.render(painter, mode)

**Configuration (``parallel_rendering`` section):**

.. list-table::
   :header-rows: 1

   * - Key
     - Type
     - Default
     - Purpose
   * - ``enabled``
     - ``bool``
     - ``True``
     - Master switch
   * - ``max_workers``
     - ``int``
     - ``4``
     - Thread pool size
   * - ``batch_size``
     - ``int``
     - ``10``
     - Objects per batch
   * - ``max_batches``
     - ``int``
     - ``10``
     - Maximum number of batches
   * - ``batch_timeout_ms``
     - ``float``
     - ``1000``
     - Batch calculation timeout
   * - ``enable_profiling``
     - ``bool``
     - ``False``
     - Performance profiling output

**Lifecycle:**

.. code-block:: text

    Init:        Scene.__init__ → SceneParallelRenderer(scene, config)
    Lazy-init:   first precalculate_text_layouts() → initialize()
                 → create calculator + batcher
    Per-frame:   render() → precalculate → submit batches
                         → render from cached layouts
    Shutdown:    Scene.__del__ → shutdown()
                 shutdown_event.set() → poison pills → thread_pool.shutdown()
                 → worker.join(timeout=1s)

Thread Safety Architecture
--------------------------

The single most important safety constraint is: **no Qt GUI objects (QFont,
QFontMetrics) are constructed on worker threads**. Qt's font database and
glyph caches are not thread-safe — creating them from a non-main thread causes
C++-level races and ``SIGSEGV``.

**Safety Layers:**

.. list-table::
   :header-rows: 1

   * - Layer
     - Mechanism
     - What It Protects
   * - Scene object access
     - ``threading.RLock`` on ``__objects``
     - All reads/writes to the object list
   * - Font construction guard
     - ``app.thread() != QThread.currentThread()`` check
     - Returns cached font; defers QFont construction to main thread
   * - ``TextLayoutData`` design
     - Plain Python types only
     - Can be created on any thread without Qt interaction
   * - ``_get_font()`` returns ``dict``
     - Font properties as ``{family, pointsize, weight, italic}``
     - No QFont created on worker threads
   * - ``to_qfont()`` / ``to_qcolor()``
     - Lazy construction on calling thread
     - QFont built only in ``render()`` on main thread
   * - Results cache
     - ``threading.RLock``
     - Safe concurrent read/write
   * - Calculation queue
     - ``queue.Queue`` (inherently thread-safe)
     - Work distribution to workers
   * - Shutdown
     - ``threading.Event`` + poison pills + ``daemon=True``
     - Coordinated graceful shutdown

Performance Characteristics
---------------------------

**Cost by Mode:**

.. list-table::
   :header-rows: 1

   * - Mode
     - Cost per frame (per object)
     - Thread
   * - Cached image (static)
     - ``drawImage()`` — O(pixels) blit, ~zero CPU
     - Main thread only
   * - Parallel layout (moving)
     - ``drawText()`` with pre-calculated QRectF
     - Layout on workers; render on main
   * - Direct drawText (fallback)
     - Full ``QPainter.drawText()`` + QFontMetrics
     - Main thread only (blocking)

**Optimization Techniques:**

1. **Skip already-rendered**: Main loop skips parallel-rendered text objects
   via ``id()``-based ``set`` membership — O(1) lookup
2. **Type check optimization**: ``type(obj).__name__ == "StringMediaObject"``
   instead of ``isinstance()`` — ~2.8× faster
3. **Font/metrics caching**: ``__font`` property returns cached QFont when
   scale hasn't changed
4. **Premultiplied alpha**: ``Format_ARGB8565_Premultiplied`` for cached images
   — fastest composition on Qt's raster paint engine
5. **Viewport change gating**: Batcher only updates when viewport has moved
   by >10 scene units
6. **``math.exp2()``**: Used instead of ``2**x`` for zoom exponentiation
   (1.85× faster)

**Resource Cleanup:**

- Worker threads are daemon — won't block process exit
- ``Scene.__del__()`` and ``shutdown_threads()`` guarantee clean termination
- Queue poison pills (``None`` sentinel) for each worker
- ``worker.join(timeout=1.0)`` prevents indefinite hangs

Configuration Tuning
--------------------

**Per-object Control:**

.. code-block:: python

    # Disable parallel rendering for a specific object
    string_obj.enable_parallel_rendering(False)

    # Clear all caches
    string_obj.clear_caches()

**Render Loop Integration:**

.. code-block:: python

    # Check if parallel rendering is active
    if scene.parallel_renderer.is_enabled():
        stats = scene.parallel_renderer.get_stats()
        print(f"Cache hit rate: {stats['cache_hit_rate']:.1%}")
        print(f"Batches processed: {stats['batches_processed']}")

**Recommended Settings:**

.. list-table::
   :header-rows: 1

   * - Scenario
     - ``max_workers``
     - ``batch_size``
     - ``max_batches``
   * - High-density text (1000+ objects)
     - 8–16
     - 20
     - 20
   * - Low-latency interaction
     - 2–4
     - 5
     - 10
   * - Memory-constrained
     - 2
     - 10
     - 5
   * - Debug/development
     - 1
     - 5
     - 3

Usage Examples
--------------

Checking Parallel Rendering Status
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    scene = window.current_zui.scene
    renderer = scene.parallel_renderer

    if renderer.is_enabled():
        stats = renderer.get_stats()
        print(f"Text objects: {stats['total_text_objects']}")
        print(f"Batches: {stats['batches_processed']}")
        print(f"Cache hit rate: {stats['cache_hit_rate']:.1%}")

Disabling Parallel Rendering
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Disable globally via config
    config = {"parallel_rendering": {"enabled": False}}
    scene = Scene(config=config)

    # Disable at runtime
    scene.parallel_renderer.enabled = False

    # Disable per-object
    string_obj.enable_parallel_rendering(False)

Clearing Caches
~~~~~~~~~~~~~~~

.. code-block:: python

    # Clear all StringMediaObject caches
    for obj in scene.objects:
        if type(obj).__name__ == "StringMediaObject":
            obj.clear_caches()

    # Force recalculation of all layouts
    scene.parallel_renderer.invalidate_all_caches()

Synchronous Layout Calculation (Debugging)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pyzui.objects.mediaobjects.mediaobjectsutils.string.parallellayout import (
        ParallelLayoutCalculator,
    )

    calculator = ParallelLayoutCalculator(max_workers=1)

    # Calculate layout synchronously (runs on calling thread)
    result = calculator.calculate_layout_sync(string_obj, viewport_rect)
    if result.layout_data:
        result.layout_data.render(painter)

See Also
--------

- :doc:`objectsystem` — Object system architecture with StringMediaObject details
- :doc:`configsystem` — Configuration system (parallel_rendering section)
- :doc:`windowsystem` — Window system rendering integration
- :doc:`../pyzui/prioritybatcher` — PriorityBatcher API reference
- :doc:`../pyzui/parallellayout` — ParallelLayoutCalculator API reference
- :doc:`../pyzui/textlayout` — TextLayoutData API reference
- :doc:`../pyzui/stringmediaobject` — StringMediaObject API reference
