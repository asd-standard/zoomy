Project structure
=================

- :doc:`physicalobject <pyzui/physicalobject>`
    - :doc:`mediaobject <pyzui/mediaobject>`
        - :doc:`tiledmediaobject <pyzui/tiledmediaobject>`
        - :doc:`stringmediaobject <pyzui/stringmediaobject>`
        - :doc:`svgmediaobject <pyzui/svgmediaobject>`
    - :doc:`scene <pyzui/scene>`
        - :doc:`qzui <pyzui/qzui>`
            - :doc:`main <main>`

- :doc:`converter <pyzui/converter>`
    - :doc:`pdfconverter <pyzui/pdfconverter>`
    - :doc:`vipsconverter <pyzui/vipsconverter>`

- :doc:`tiler <pyzui/tiler>`
    - :doc:`ppm <pyzui/ppm>`

- :doc:`tile <pyzui/tile>`
    - :doc:`tilemanager <pyzui/tilemanager>`
    - :doc:`tilecache <pyzui/tilecache>`
    - :doc:`tilestore <pyzui/tilestore>`
    - :doc:`tileprovider <pyzui/tileprovider>`
        - :doc:`statictileprovider <pyzui/statictileprovider>`
        - :doc:`dynamictileprovider <pyzui/dynamictileprovider>`
            - :doc:`ferntileprovider <pyzui/ferntileprovider>`

Architecture diagram
--------------------

Here's a schematic of the program architecture, with a simple legend of
core components:

Key Design Patterns:

    - **Abstract Base Classes**: Converter, TileProvider, MediaObject, PhysicalObject
    - **Threading**: Non-blocking tile loading, rendering, conversion
    - **Caching Strategy**: Three-tier (Memory → Disk → Source)
    - **Observer Pattern**: Qt signals/slots for event handling
    - **Template Method**: Tile provider request processing
    - **Singleton-like**: TileManager module-level functions


Core Components::

| Component        | Responsibility                    | Key Files |
|-----------       |-----------------------------------|-----------|
| **main.py**      | Application entry, initialization | main.py |
| **LoggerConfig** | Centralized logging system        | pyzui/logger.py |
| **TileManager**  | Tile coordination and caching     | pyzui/tilesystem/tilemanager.py |
| **MainWindow**   | Qt main window and menus          | pyzui/windows/mainwindow.py |
| **QZUI**         | Rendering widget, input handling  | pyzui/objects/scene/qzui.py |
| **Scene**        | MediaObject container             | pyzui/objects/scene/scene.py |
| **MediaObject**  | Displayable media in ZUI          | pyzui/objects/mediaobjects/ |
| **TileProvider** | Tile loading/generation           | pyzui/tilesystem/tileproviders/ |
| **TileStore**    | Persistent tile storage           | pyzui/tilesystem/tilestore/ |
| **Converter**    | Media format conversion           | pyzui/converters/ |

Program schematic::

    ┌─────────────────────────────────────────────────────────────────┐
    │                         main.py                                 │
    │  • Parse CLI arguments                                          │
    │  • Load configuration (JSON)                                    │
    │  • Initialize logging system                                    │
    │  • Initialize TileManager                                       │
    │  • Create MainWindow & QZUI                                     │
    └─────────────┬───────────────────────────────────────────────────┘
                  │
                  ├──────────────────────────────────────────────┐
                  │                                              │
                  ▼                                              ▼
    ┌─────────────────────────────┐              ┌──────────────────────────────┐
    │      LoggerConfig           │              │     TileManager (Module)     │
    │  • Centralized logging      │              │  • init() - Setup caches     │
    │  • File + Console handlers  │              │  • load_tile()               │
    │  • Color-coded output       │              │  • get_tile()                │
    │  • Rotation support         │              │  • get_tile_robust()         │
    └─────────────────────────────┘              └──────────┬───────────────────┘
                                                            │
                                                            │
                  ┌─────────────────────────────────────────┴──────────┐
                  │                                                    │
                  ▼                                                    ▼
    ┌─────────────────────────────┐              ┌──────────────────────────────┐
    │     MainWindow (Qt)         │              │   TileCache (LRU)            │
    │  • Menu system              │              │  • In-memory cache           │
    │  • File operations          │              │  • 80% static / 20% dynamic  │
    │  • Central widget: QZUI     │              │  • Thread-safe               │
    └─────────────┬───────────────┘              └──────────┬───────────────────┘
                  │                                         │
                  ▼                                         │
    ┌─────────────────────────────┐                         │
    │   QZUI (Qt Widget+Thread)   │                         │
    │  • Rendering loop           │                         │
    │  • Input handling           │                         │
    │  • Viewport management      │◄────────────────────────┤
    │  • Requests tiles           │                         │
    └─────────────┬───────────────┘                         │
                  │                                         │
                  ▼                                         │
    ┌─────────────────────────────┐                         │
    │        Scene                │                         │
    │  • Container for media      │                         │
    │  • Coordinate transforms    │                         │
    │  • Thread-safe (RLock)      │                         │
    │  • Save/Load .pzs files     │                         │
    └─────────────┬───────────────┘                         │
                  │                                         │
                  ▼                                         │
    ┌───────────────────────────────────┐                   │
    │      MediaObject                  │                   │
    │  ┌─────────────────────┐          │                   │
    │  │  PhysicalObject     │          │                   │
    │  │  • x, y, z coords   │          │                   │
    │  │  • vx, vy, vz       │          │                   │
    │  │  • damping          │          │                   │
    │  └─────────────────────┘          │                   │
    │         ▲                         │                   │ 
    │         │                         │                   │
    │  ┌──────┴──────────────┐          │                   │
    │  │                     │          │                   │
    │  ▼                     ▼          │                   │
    │ TiledMediaObject  StringMediaObj  │                   │
    │ SVGMediaObject                    │                   │
    └───────────────────────────────────┘                   │
                  │                                         │
                  │ requests tiles                          │
                  ▼                                         │
    ┌─────────────────────────────┐                         │
    │   TileProvider (Abstract)   │◄────────────────────────┘
    │  • Thread-based             │
    │  • LIFO task queue          │
    │  • Condition variables      │
    └─────────────┬───────────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
        ▼                    ▼
    ┌────────────┐    ┌──────────────────┐
    │  Static    │    │  DynamicProvider │
    │  Provider  │    │  • FernProvider  │
    │            │    │  • MandelProvider│
    └────┬───────┘    └────────┬─────────┘
         │                     │
         │                     │
         └─────────┬───────────┘
                   │
                   ▼
         ┌──────────────────┐
         │   TileStore      │
         │  • Disk storage  │
         │  • SHA-1 hashing │
         │  • Auto cleanup  │
         └──────────────────┘