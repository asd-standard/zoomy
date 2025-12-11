.. Object System Documentation

Object System
=============

This document provides a comprehensive overview of the object system architecture in PyZUI,
explaining how objects are positioned, rendered, and animated within the Zooming User Interface.
The object system is responsible for managing the spatial relationships, physics simulation,
and rendering of all elements in the scene.

Overview
--------

The object system is responsible for:

1. Managing 3D position and velocity (x, y, zoom level)
2. Simulating physics with exponential damping
3. Handling coordinate transformations between reference frames
4. Rendering media objects at various zoom levels
5. Managing scene composition and object lifecycle

The system uses a **hierarchical class structure** where :class:`PhysicalObject` provides
the base physics simulation, :class:`MediaObject` adds media-specific positioning and rendering,
and concrete media types implement specific rendering strategies.

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
    │   │
    │   ├── TiledMediaObject
    │   │       • Large image support via tile pyramid
    │   │       • Tile grid management
    │   │       • Progressive loading with placeholders
    │   │       • Converter support (PDF, images)
    │   │       • Efficient for huge images
    │   │
    │   ├── StringMediaObject
    │   │       • Text rendering with QFont
    │   │       • Multi-line text support
    │   │       • Font scaling based on zoom
    │   │       • Transparent background
    │   │
    │   └── SVGMediaObject
    │           • Vector graphics rendering
    │           • Scalable without quality loss
    │           • QSvgRenderer integration
    │           • Transparent background
    │
    └── Scene
            • Container for MediaObjects
            • Viewport management
            • Scene persistence (save/load)
            • Thread-safe operations (RLock)
            • Object selection (left/right click)
            • Rendering coordination

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

Scene
~~~~~

The :class:`Scene` class manages collections of MediaObjects and coordinates rendering.

**Key Attributes:**

- ``__objects``: List of MediaObjects in the scene
- ``__objects_lock``: Thread-safe access control (RLock)
- ``__viewport_size``: Current viewport dimensions
- ``selection``: Currently selected object (left-click)
- ``right_selection``: Right-click selected object
- ``standard_viewport_size``: Default size for scene persistence (1280x720)

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

**Key Methods:**

- ``add(mediaobject)``: Add object to scene
- ``remove(mediaobject)``: Remove object and purge unused tiles
- ``get(pos)``: Get foremost object at screen position
- ``render(painter, draft)``: Render all objects with occlusion culling
- ``step(t)``: Update physics for scene and all objects
- ``save(filename)``: Save scene to .pzs file
- ``load_scene(filename)``: Load scene from .pzs file (static method)

MediaObject Types
-----------------

TiledMediaObject
~~~~~~~~~~~~~~~~

:class:`TiledMediaObject` handles large images by breaking them into a pyramid of tiles.

**Features:**

- **Format Support**: PDF, PPM, and standard images (JPG, PNG, GIF, TIFF)
- **Converters**: Automatic conversion via PDFConverter or VipsConverter
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

:class:`StringMediaObject` renders text strings with automatic font scaling.

**Features:**

- **Multi-line Support**: Automatically handles newline characters
- **Color Support**: Parse color from media_id (e.g., 'string:ff0000:Hello')
- **Font Scaling**: Font size scales with zoom level
- **Transparent Background**: Doesn't obscure objects behind it

**Media ID Format:**

.. code-block:: text

    string:RRGGBB:text content

    Examples:
        string:ff0000:Hello World    → Red text
        string:00ff00:Line 1\nLine 2 → Green multi-line text
        string:0000ff:Blue Text      → Blue text

**Rendering:**

- Base font size: 24pt at 100% scale
- Only renders when size is between 2.3% and 77% of viewport
- Uses QFontMetrics for accurate text measurement
- Creates QRectF for each line in multi-line text

SVGMediaObject
~~~~~~~~~~~~~~

:class:`SVGMediaObject` renders scalable vector graphics.

**Features:**

- **Vector Rendering**: Uses QSvgRenderer for crisp graphics at any zoom
- **Transparent Background**: SVG transparency is preserved
- **Scalable**: No quality loss when zooming

**Rendering:**

- Loads SVG file using QSvgRenderer
- Stores default width and height from SVG
- Renders to QRectF scaled by current zoom level
- Only renders when size is between 2.3% and 77% of viewport

Coordinate Systems and Reference Frames
----------------------------------------

Understanding the coordinate transformations is crucial for working with PyZUI.

Reference Frame Hierarchy
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    ┌─────────────────────────────────────────────────────────────┐
    │ World/Absolute Reference Frame                              │
    │ • Origin: (0, 0)                                            │
    │ • Used for: Scene positioning                              │
    └─────────────────────────────────────────────────────────────┘
                            │
                            ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ Scene Reference Frame                                       │
    │ • Origin: Scene.origin (world coords)                      │
    │ • Scaling: 2 ** Scene.zoomlevel                           │
    │ • Used for: MediaObject positioning                        │
    └─────────────────────────────────────────────────────────────┘
                            │
                            ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ MediaObject Reference Frame                                 │
    │ • Origin: MediaObject.pos (scene coords)                   │
    │ • Scaling: 2 ** MediaObject.zoomlevel                     │
    │ • Used for: Internal object coordinates (e.g., centre)     │
    └─────────────────────────────────────────────────────────────┘
                            │
                            ▼
    ┌─────────────────────────────────────────────────────────────┐
    │ Screen/Viewport Reference Frame                             │
    │ • Origin: Top-left corner of window                        │
    │ • Units: Pixels                                            │
    │ • Used for: Rendering and mouse input                      │
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

The :meth:`Scene.render` method orchestrates rendering of all objects:

**Rendering Process:**

.. code-block:: text

    1. Sort objects by onscreen_area (smallest to largest)

    2. Occlusion Culling:
       - Iterate objects in reverse (largest first)
       - If object fills entire viewport, mark rest as hidden

    3. Assign Render Modes:
       - Hidden objects: RenderMode.Invisible
       - Draft mode: RenderMode.Draft (fast rendering)
       - Otherwise: RenderMode.HighQuality

    4. Render Each Object:
       - Call object.render(painter, mode)
       - Catch LoadError exceptions
       - Remove objects with errors

    5. Draw Selection Borders:
       - Green border for left-click selection
       - Blue border for right-click selection

    6. Return error list

**Render Modes:**

.. code-block:: python

    class RenderMode:
        Invisible = 0      # Don't render
        Draft = 1          # Fast, lower quality
        HighQuality = 2    # Slow, higher quality

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
- Creates QFont with scaled point size
- Measures text with QFontMetrics
- Creates QRectF for each line
- Draws text with QPainter.drawText()

**SVGMediaObject:**
- Checks if SVG is visible size
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

Scene Persistence
-----------------

Scenes can be saved to and loaded from .pzs files.

Save Format
~~~~~~~~~~~

.. code-block:: text

    Line 1: scene.zoomlevel    scene.origin[0]    scene.origin[1]
    Line 2+: class_name    media_id    zoomlevel    pos[0]    pos[1]

    Example:
    0.0    640.0    360.0
    TiledMediaObject    image.jpg    0.5    100.0    200.0
    StringMediaObject    string:ff0000:Hello    0.0    300.0    400.0

**Saving Process:**

1. Store current viewport size
2. Temporarily set viewport to standard size (1280x720)
3. Write scene zoom and origin
4. Sort and write all objects
5. Restore actual viewport size

**Loading Process:**

1. Create new Scene
2. Read scene zoom and origin from first line
3. For each subsequent line:
   - Parse object type and parameters
   - Create appropriate MediaObject subclass
   - Set zoom level and position
   - Add to scene
4. Return loaded scene

Usage Examples
--------------

Creating and Populating a Scene
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pyzui.objects.scene.scene import Scene, load_scene
    from pyzui.objects.mediaobjects.tiledmediaobject import TiledMediaObject
    from pyzui.objects.mediaobjects.stringmediaobject import StringMediaObject

    # Create new scene
    scene = Scene()
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

    # Save scene
    scene.save('my_scene.pzs')

    # Load scene later
    scene = load_scene('my_scene.pzs')

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

Coordinate Transformations
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Get screen position of object
    screen_x, screen_y = obj.topleft

    # Get object at mouse position
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

For detailed API documentation, see the individual class documentation pages.

See Also
--------

- :doc:`tilingsystem` - Details on tile pyramid and caching
- :doc:`tiledmediaobject` - TiledMediaObject implementation details
- :doc:`projectstructure` - Overall project architecture
