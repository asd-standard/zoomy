Project structure
=================

For human readability the project has been subdivided into the following folder structure::

  pyzui/
  ├── config.py
  ├── logger.py
  ├── converters/
  │   ├── converter.py
  │   ├── converterrunner.py
  │   ├── pdfconverter.py
  │   └── vipsconverter.py
  ├── backup/
  │   └── backupmanager.py
  ├── objects/
  │   ├── physicalobject.py
  │   ├── objectsutils/
  │   │   └── zoom/
  │   │       └── zoommanager.py
  │   ├── mediaobjects/
  │   │   ├── mediaobject.py
  │   │   ├── stringmediaobject.py
  │   │   ├── svgmediaobject.py
  │   │   ├── tiledmediaobject.py
  │   │   └── mediaobjectsutils/
  │   │       ├── string/
  │   │       │   ├── parallellayout.py
  │   │       │   └── textlayout.py
  │   │       └── svg/
  │   │           ├── svgcache/
  │   │           │   └── svgcache.py
  │   │           └── utils/
  │   │               ├── svgarrowutils.py
  │   │               ├── svgcircleutils.py
  │   │               ├── svgsquareutils.py
  │   │               ├── svgstickutils.py
  │   │               └── svgtriangleutils.py
  │   └── scene/
  │       ├── qzui.py
  │       ├── scene.py
  │       └── sceneutils/
  │           ├── autosave.py
  │           ├── clipboard.py
  │           ├── parallel.py
  │           └── prioritybatcher.py
  ├── tilesystem/
  │   ├── tile.py
  │   ├── tilecache.py
  │   ├── tilemanager.py
  │   ├── tiler/
  │   │   ├── ppm.py
  │   │   ├── tiler.py
  │   │   └── tilerrunner.py
  │   ├── tileproviders/
  │   │   ├── tileprovider.py
  │   │   ├── statictileprovider.py
  │   │   ├── dynamictileprovider.py
  │   │   └── ferndynamictileprovider.py
  │   └── tilestore/
  │       ├── cleanuptilestore.py
  │       ├── tilecache.py
  │       └── tilestore.py
  └── windows/
      ├── mainwindow.py
      └── dialogwindows/
          ├── dialogwindows.py
          ├── autosavesettingsdialog.py
          ├── modifystringdialog.py
          ├── modifysvginputdialog.py
          ├── modifytiledmediaobjectdialog.py
          ├── stringinputdialog.py
          ├── svgpickerinputdialog.py
          ├── zoomsensitivitydialog.py
          └── zoomsettingsdialog.py


Project class hierarchy
-----------------------

PhysicalObject and media types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- :doc:`physicalobject <../pyzui/physicalobject>`
    - :doc:`mediaobject <../pyzui/mediaobject>`
        - :doc:`tiledmediaobject <../pyzui/tiledmediaobject>`
        - :doc:`stringmediaobject <../pyzui/stringmediaobject>`
        - :doc:`svgmediaobject <../pyzui/svgmediaobject>`
    - :doc:`scene <../pyzui/scene>`
        - :doc:`qzui <../pyzui/qzui>`
            - :doc:`main <../main>`
        - :doc:`prioritybatcher <../pyzui/prioritybatcher>`
        - :doc:`autosave <../pyzui/autosave>` — Timer-based autosave orchestration
        - :doc:`clipboard <../pyzui/clipboard>` — Copy/paste operations
        - :doc:`parallel <../pyzui/parallel>` — Parallel rendering

Zoom manager
~~~~~~~~~~~~

- :doc:`zoommanager <../pyzui/zoommanager>` — Zoom level tracking and physics

Media object utilities
~~~~~~~~~~~~~~~~~~~~~~

String utilities
  - ``mediaobjectsutils/string/textlayout.py`` — Text layout engine
  - ``mediaobjectsutils/string/parallellayout.py`` — Parallel text rendering

SVG utilities
  - ``mediaobjectsutils/svg/svgcache/svgcache.py`` — SVG rendering cache
  - ``mediaobjectsutils/svg/utils/svgarrowutils.py`` — Arrow shape generator
  - ``mediaobjectsutils/svg/utils/svgcircleutils.py`` — Circle shape generator
  - ``mediaobjectsutils/svg/utils/svgsquareutils.py`` — Square shape generator
  - ``mediaobjectsutils/svg/utils/svgstickutils.py`` — Stick figure generator
  - ``mediaobjectsutils/svg/utils/svgtriangleutils.py`` — Triangle shape generator

Converters
~~~~~~~~~~

- :doc:`converter <../pyzui/converter>`
    - :doc:`pdfconverter <../pyzui/pdfconverter>`
    - :doc:`vipsconverter <../pyzui/vipsconverter>`
    - :doc:`converterrunner <../pyzui/converterrunner>` — Process-based parallel conversion

Tile system
~~~~~~~~~~~

- :doc:`tile <../pyzui/tile>`
- :doc:`tilecache <../pyzui/tilecache>` — In-memory LRU cache
- :doc:`tilemanager <../pyzui/tilemanager>` — Central tile coordinator
- :doc:`tiler <../pyzui/tiler>`
    - :doc:`ppm <../pyzui/ppm>`
    - :doc:`tilerrunner <../pyzui/tilerrunner>` — Process-based parallel tiling
- :doc:`tileprovider <../pyzui/tileprovider>`
    - :doc:`statictileprovider <../pyzui/statictileprovider>`
    - :doc:`dynamictileprovider <../pyzui/dynamictileprovider>`
        - :doc:`ferntileprovider <../pyzui/ferntileprovider>`
- :doc:`tilestore <../pyzui/tilestore>`
    - ``cleanuptilestore.py`` — Auto-cleanup of stale tiles

Windows and dialogs
~~~~~~~~~~~~~~~~~~~

- :doc:`mainwindow <../pyzui/mainwindow>`
- :doc:`dialogwindows <../pyzui/dialogwindows>`
    - :doc:`stringinputdialog <../pyzui/stringinputdialog>`
    - :doc:`modifystringdialog <../pyzui/modifystringdialog>`
    - :doc:`svgpickerinputdialog <../pyzui/svgpickerinputdialog>`
    - :doc:`modifysvginputdialog <../pyzui/modifysvginputdialog>`
    - :doc:`modifytiledmediaobjectdialog <../pyzui/modifytiledmediaobjectdialog>`
    - :doc:`zoomsensitivitydialog <../pyzui/zoomsensitivitydialog>`
    - :doc:`zoomsettingsdialog <../pyzui/zoomsettingsdialog>`
    - :doc:`autosavesettingsdialog <../pyzui/autosavesettingsdialog>`

Configuration and backup
~~~~~~~~~~~~~~~~~~~~~~~~

- ``config.py`` — User configuration management (ConfigManager)
- ``backup/backupmanager.py`` — Per-scene backup creation and rotation


Architecture diagram
--------------------

Here is a schematic of the program architecture, with a legend of
core components and design patterns.

Key Design Patterns:

    - **Abstract Base Classes**: Converter, TileProvider, MediaObject, PhysicalObject
    - **Process Pooling**: Parallel media conversion (:doc:`converterrunner <../pyzui/converterrunner>`) and tile generation (:doc:`tilerrunner <../pyzui/tilerrunner>`)
    - **Thread Pooling**: Concurrent tile creation with worker thread pools in TileManager
    - **Autosave**: Timer-based per-scene backup orchestration with rotation and cleanup
    - **Clipboard**: Copy/paste with grid-aligned positioning via ``sceneutils/clipboard.py``
    - **Parallel Rendering**: Multi-priority render pipeline with render order toggle (Ctrl+R)
    - **Hybrid Rendering**: CPU-efficient text caching for StringMediaObject
    - **Caching Strategy**: Three-tier (Memory → Disk → Source)
    - **Observer Pattern**: Qt signals/slots for event handling
    - **Template Method**: Tile provider request processing
    - **Singleton-like**: TileManager module-level functions


Core Components::

  | Component           | Responsibility                      | Key Files |
  |---------------------|-------------------------------------|-----------|
  | **main.py**         | Application entry, initialization   | main.py |
  | **ConfigManager**   | User configuration management       | pyzui/config.py |
  | **LoggerConfig**    | Centralized logging system          | pyzui/logger.py |
  | **MainWindow**      | Qt main window and menus            | pyzui/windows/mainwindow.py |
  | **QZUI**            | Rendering widget, input handling    | pyzui/objects/scene/qzui.py |
  | **Scene**           | MediaObject container, autosave     | pyzui/objects/scene/scene.py |
  | **Autosave**        | Timer-based per-scene backups       | pyzui/objects/scene/sceneutils/autosave.py |
  | **Clipboard**       | Copy/paste with grid alignment      | pyzui/objects/scene/sceneutils/clipboard.py |
  | **MediaObject**     | Displayable media in ZUI            | pyzui/objects/mediaobjects/ |
  | **ZoomManager**     | Zoom level tracking and physics     | pyzui/objects/objectsutils/zoom/zoommanager.py |
  | **PriorityBatcher** | Priority-based tile request batching| pyzui/objects/scene/sceneutils/prioritybatcher.py |
  | **TileManager**     | Tile coordination and caching       | pyzui/tilesystem/tilemanager.py |
  | **TileProvider**    | Tile loading/generation             | pyzui/tilesystem/tileproviders/ |
  | **TileStore**       | Persistent tile storage             | pyzui/tilesystem/tilestore/ |
  | **Converter**       | Media format conversion             | pyzui/converters/ |
  | **ConverterRunner** | Process-based parallel conversion   | pyzui/converters/converterrunner.py |
  | **TilerRunner**     | Process-based parallel tiling       | pyzui/tilesystem/tiler/tilerrunner.py |
  | **BackupManager**   | Per-scene backup creation/rotation  | pyzui/backup/backupmanager.py |


Complete Application Lifecycle::

     START                                        |    Enter Qt Event Loop ←──────────┐
       ↓                                          |      ↓                            │
     Parse Args → Load Config → Init Logging      |      │  ┌─────────────────────┐   │
       ↓                        ↑                 |      ├─→│ User Input Events   │───┤
     ConfigManager reads       │                  |      │  └─────────────────────┘   │
     pyzui_config.json ←───────┘                  |      │                            │
       ↓                                          |      │  ┌─────────────────────┐   │
     Init TileManager                             |      ├─→│ QZUI Render Loop    │───┤
       ↓                                          |      │  │ • Update physics    │   │
       ├─→ Create TileCache (80% static,          |      │  │ • PriorityBatcher   │   │
       │   20% dynamic)                           |      │  │ • Request tiles     │   │
       ├─→ Start StaticTileProvider thread        |      │  │ • Render scene      │   │
       ├─→ Start DynamicTileProvider threads      |      │  └─────────────────────┘   │
       └─→ Auto cleanup TileStore (if enabled)    |      │                            │
       ↓                                          |      │  ┌─────────────────────┐   │
     Create Qt App                                |      ├─→│ Tile Providers      │───┤
       ↓                                          |      │  │ • Process requests  │   │
     Create MainWindow                            |      │  │ • Load/generate     │   │
       ↓                                          |      │  │ • Cache tiles       │   │
       ├─→ Create QZUI widget                     |      │  │ • PriorityBatcher   │   │
       │   ├─→ Create Scene                       |      │  └─────────────────────┘   │
       │   ├─→ Start render thread (10 fps)       |      │                            │
       │   └─→ Init PriorityBatcher               |      │  ┌─────────────────────┐   │
       ├─→ Setup menus                            |      ├─→│ Autosave Timer      │───┤
       ├─→ Init ConverterRunner (process pool)    |      │  │ • Per-scene backup  │   │
       ├─→ Init TilerRunner (process pool)        |      │  │ • Rotation/cleanup  │   │
       ├─→ Load default scene                     |      │  └─────────────────────┘   │
       └─→ Start autosave timer                   |      │                            │
       ↓                                          |      └────────────────────────────┘
     Show Window                                  |      ↓
       ↓                                          |    User Closes Window
                                                  |      ↓
                                                  |    Stop Autosave → Cleanup Pools
                                                  |      ↓
                                                  |    Exit Event Loop → Cleanup & Exit
                                                  |      ↓
                                                  |    END


Program schematic::

    ┌─────────────────────────────────────────────────────────────────┐
    │                         main.py                                 │
    │  • Parse CLI arguments                                          │
    │  • Load configuration via ConfigManager                         │
    │  • Initialize logging system                                    │
    │  • Initialize TileManager                                       │
    │  • Create MainWindow & QZUI                                     │
    │  • Start process pools (Converter / Tiler)                      │
    └─────────────┬───────────────────────────────────────────────────┘
                  │
                  ├──────────────────────────────────────────────────────────────┐
                  │                                                              │
                  ▼                                                              ▼
    ┌─────────────────────────────┐              ┌──────────────────────────────┐
    │      ConfigManager          │              │     LoggerConfig             │
    │  • JSON config file I/O     │              │  • Centralized logging       │
    │  • CLI override support     │              │  • File + Console handlers   │
    │  • Autosave settings        │              │  • Color-coded output        │
    └─────────────────────────────┘              └──────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────┐
    │                     TileManager (Module)                        │
    │  • init() — Setup caches and thread pools                      │
    │  • load_tile() / get_tile() / get_tile_robust()                │
    │  • Manages Static and Dynamic tile providers                   │
    │  • Coordinates with TilerRunner (process pool)                 │
    └──────────┬──────────────────┬────────────────┬─────────────────┘
               │                  │                │
               ▼                  ▼                ▼
    ┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
    │ TileCache (LRU)  │ │ ConverterRunner│ │  TilerRunner     │
    │ • In-memory cache│ │ (Process Pool) │ │  (Process Pool)  │
    │ • 80% static     │ │ • Parallel fmt │ │  • Parallel tile │
    │ • 20% dynamic    │ │   conversion   │ │    generation    │
    │ • Thread-safe    │ │ • libvips/PIL  │ │  • PPM format    │
    └──────────────────┘ └──────────────┘ └──────────────────┘

    ┌─────────────────────────────┐
    │     MainWindow (Qt)         │
    │  • Menu system              │
    │  • File operations          │
    │  • Central widget: QZUI     │
    │  • Dialog management        │
    └─────────────┬───────────────┘
                  │
                  ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                    QZUI (Qt Widget + Thread)                     │
    │  • Rendering loop (10 fps)                                      │
    │  • Input handling (mouse, touch, keyboard)                      │
    │  • Viewport management (pan, zoom)                              │
    │  • Requests tiles via PriorityBatcher                           │
    │  • Renders Scene content                                         │
    └─────────────┬───────────────────────────────────────────────────┘
                  │
                  ├──────────────────────────────┬────────────────────┐
                  │                              │                    │
                  ▼                              ▼                    ▼
    ┌─────────────────────────────┐ ┌─────────────────────┐ ┌─────────────────┐
    │        Scene                │ │   PriorityBatcher   │ │  ZoomManager   │
    │  • Container for media      │ │  • Priority queue   │ │  • Zoom level  │
    │  • Coordinate transforms    │ │  • Tile request     │ │  • Physics     │
    │  • Thread-safe (RLock)      │ │    batching         │ │  • Sensitivity │
    │  • Save/Load .pzs files     │ └─────────┬───────────┘ └─────────────────┘
    │  • Autosave integration     │           │
    │  • Clipboard integration    │           │ tile requests
    └──────┬──────────────┬───────┘           │
           │              │                   │
           ▼              ▼                   │
    ┌──────────────┐ ┌────────────────┐       │
    │   Autosave    │ │   Clipboard    │       │
    │  • Per-scene  │ │  • Copy/paste  │       │
    │    backups    │ │  • Grid-align  │       │
    │  • Rotation   │ │  • Selection   │       │
    │  • Expiration │ └────────────────┘       │
    └──────┬───────┘                            │
           │                                   │
           ▼                                   │
    ┌──────────────┐                           │
    │ BackupManager │                          │
    │  • Dir mgmt  │                           │
    │  • Cleanup   │                           │
    └──────────────┘                           │
                                               │
    ┌──────────────────────────────────────────┘
    │
    ▼
    ┌───────────────────────────────────┐
    │      MediaObject                  │
    │  ┌─────────────────────┐          │
    │  │  PhysicalObject     │          │
    │  │  • x, y, z coords   │          │
    │  │  • vx, vy, vz       │          │
    │  │  • damping          │          │
    │  └─────────────────────┘          │
    │         ▲                         │
    │         │                         │
    │  ┌──────┴──────────────┐          │
    │  │                     │          │
    │  ▼                     ▼          │
    │ TiledMediaObject  StringMediaObj  │
    │ SVGMediaObject                    │
    │  • SVG cache          • Hybrid   │
    │  • Shape utils          render   │
    │  (5 shape types)      • Text     │
    │                         layout   │
    │                         • Parall │
    └───────────────────────────────────┘
                  │
                  │ requests tiles
                  ▼
    ┌──────────────────────────────────────┐
    │   TileProvider (Abstract)            │◄─── PriorityBatcher
    │  • Thread-based (ThreadPool)         │
    │  • LIFO task queue                   │
    │  • Condition variables               │
    │  • Pause/resume support              │
    └─────────────┬────────────────────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
        ▼                    ▼
    ┌────────────┐    ┌──────────────────┐
    │  Static    │    │  DynamicProvider │
    │  Provider  │    │  • FernProvider  │
    │            │    └────────┬─────────┘
    └────┬───────┘             │
         │                     │
         └─────────┬───────────┘
                   │
                   ▼
         ┌──────────────────┐
         │   TileStore      │
         │  • Disk storage  │
         │  • SHA-1 hashing │
         │  • Auto cleanup  │
         │    (cleanuptls)  │
         └──────────────────┘
