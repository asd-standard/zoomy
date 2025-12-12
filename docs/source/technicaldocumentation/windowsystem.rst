.. Window System Documentation

Window System
=============

This document provides a comprehensive overview of the window system architecture in PyZUI,
explaining how the graphical user interface is structured, how user input is handled, and how
the application integrates with the PySide6 (Qt) framework to create an interactive zooming
interface.

Overview
--------

The window system is responsible for:

1. Creating the main application window with menus and toolbar
2. Rendering the zooming user interface in real-time
3. Handling user input (mouse, keyboard, touch)
4. Managing dialogs for user interactions
5. Coordinating between UI events and scene updates
6. Providing visual feedback (selection borders, loading indicators)

The system uses **PySide6 (Qt6)** as the GUI framework, providing cross-platform window
management, event handling, and rendering capabilities. The architecture follows the
Model-View pattern, where Scene/MediaObjects represent the data model and the window
system provides the interactive view.

Architecture
------------

The window system consists of the following components:

.. code-block:: text

    Application (QApplication)
    │
    └── MainWindow (QMainWindow)
        │   • Application window frame
        │   • Menu bar and actions
        │   • File operations (open/save)
        │   • Media import dialogs
        │   • Settings and configuration
        │   • Error message display
        │
        └── QZUI (QWidget + Thread)
            │   • Central rendering widget
            │   • Scene rendering coordination
            │   • Mouse event handling
            │   • Keyboard event handling
            │   • Wheel event handling (zoom)
            │   • Timer-based animation
            │   • Draft/high-quality rendering
            │
            └── Scene
                └── MediaObjects


    DialogWindows (Static Container)
    │   • Aggregates dialog components
    │   • Provides unified interface
    │
    ├── OpenNewStringInputDialog
    │       • Create new text objects
    │       • Color selection (24 recent colors)
    │       • Custom color input (hex codes)
    │       • Multi-line text support
    │       • Color persistence
    │
    ├── ModifyStringInputDialog
    │       • Edit existing text objects
    │       • Change text content
    │       • Change text color
    │       • Preserves original text
    │
    └── ZoomSensitivityDialog
            • Adjust zoom sensitivity (0-100)
            • Real-time sensitivity update

**UI Event Flow:**

.. code-block:: text

    User Input (Mouse/Keyboard)
            │
            ▼
    ┌─────────────────────────┐
    │   Qt Event System       │
    │   (Event Queue)         │
    └────────────┬────────────┘
                 │
                 ▼
    ┌─────────────────────────┐
    │   QZUI Event Handlers   │
    │   • mousePressEvent     │
    │   • mouseMoveEvent      │
    │   • wheelEvent          │
    │   • keyPressEvent       │
    └────────────┬────────────┘
                 │
                 ▼
    ┌─────────────────────────┐
    │   Scene/Object Update   │
    │   • Set velocity        │
    │   • Update position     │
    │   • Update selection    │
    └────────────┬────────────┘
                 │
                 ▼
    ┌─────────────────────────┐
    │   Timer Triggers        │
    │   (timerEvent)          │
    └────────────┬────────────┘
                 │
                 ▼
    ┌─────────────────────────┐
    │   QZUI.paintEvent       │
    │   • Step physics        │
    │   • Render scene        │
    │   • Draw selection      │
    └─────────────────────────┘

Core Components
---------------

MainWindow
~~~~~~~~~~

The :class:`MainWindow` class extends :class:`QMainWindow` and serves as the main
application window, providing menus, actions, and file operations.

**Class Definition:**

.. code-block:: python

    class MainWindow(QtWidgets.QMainWindow):
        def __init__(self, framerate: int = 10,
                     zoom_sensitivity: int = 50) -> None:
            QtWidgets.QMainWindow.__init__(self)

            self.setWindowTitle("PyZUI")
            self.zui = QZUI(self, framerate, zoom_sensitivity)
            self.zui.start()
            self.setCentralWidget(self.zui)

            self.__create_actions()
            self.__create_menus()

**Key Attributes:**

- ``zui``: Central QZUI widget for rendering
- ``__action``: Dictionary of QAction objects for menu items
- ``__menu``: Dictionary of QMenu objects
- ``__prev_dir``: Last used directory for file dialogs
- ``__logger``: Logger instance for error reporting

**Window Properties:**

- **Default Size**: 1280x720 pixels (sizeHint)
- **Minimum Size**: 160x120 pixels (minimumSizeHint)
- **Resizable**: Yes, viewport adapts to window size

**Menu Structure:**

.. code-block:: text

    File
    ├── New Scene                   (Ctrl+N)
    ├── Open Scene                  (Ctrl+O)
    ├── Open Home Scene             (Ctrl+Home)
    ├── Save Scene                  (Ctrl+S)
    ├── Save Screenshot             (Ctrl+H)
    ├── Open Local Media            (Ctrl+L)
    ├── Open new String             (Ctrl+U)
    ├── Open Media Directory        (Ctrl+D)
    └── Quit                        (Ctrl+Q)

    View
    ├── Set Framerate ▶
    │   ├── 10 FPS
    │   ├── 20 FPS
    │   ├── 30 FPS
    │   └── 40 FPS
    ├── Adjust Sensitivity
    └── Fullscreen                  (Ctrl+F)

    Help
    ├── About
    └── About Qt

**Key Methods:**

Scene Operations
^^^^^^^^^^^^^^^^

.. code-block:: python

    def __action_new_scene(self) -> None:
        """Create a new empty scene."""
        self.zui.scene = Scene.new()

    def __action_open_scene(self) -> None:
        """Open scene from .pzs file via file dialog."""
        filename = QFileDialog.getOpenFileName(
            self, "Open scene", self.__prev_dir,
            "PyZUI Scenes (*.pzs)")
        if filename:
            self.zui.scene = Scene.load_scene(filename)

    def __action_save_scene(self) -> None:
        """Save current scene to .pzs file."""
        filename = QFileDialog.getSaveFileName(
            self, "Save scene", "scene.pzs",
            "PyZUI Scenes (*.pzs)")
        if filename:
            self.zui.scene.save(filename)

    def __action_save_screenshot(self) -> None:
        """Save screenshot to image file."""
        filename = QFileDialog.getSaveFileName(
            self, "Save screenshot", "screenshot.png",
            "Images (*.bmp *.jpg *.png ...)")
        if filename:
            pixmap = self.zui.grab()
            pixmap.save(filename)

Media Import
^^^^^^^^^^^^

.. code-block:: python

    def __open_media(self, media_id: str, add: bool = True):
        """Open media and optionally add to scene."""
        # Detect media type from file extension
        if media_id.startswith('string:'):
            mediaobject = StringMediaObject(media_id, self.zui.scene)
        elif media_id.lower().endswith('.svg'):
            mediaobject = SVGMediaObject(media_id, self.zui.scene)
        else:
            mediaobject = TiledMediaObject(media_id, self.zui.scene)

        if add:
            # Fit to center 50% of viewport
            w, h = self.zui.width(), self.zui.height()
            mediaobject.fit((w/4, h/4, w*3/4, h*3/4))
            self.zui.scene.add(mediaobject)

    def __action_open_media_local(self) -> None:
        """Open single media file via file dialog."""
        filename = QFileDialog.getOpenFileName(
            self, "Open local media", self.__prev_dir)
        if filename:
            self.__open_media(filename)

    def __action_open_media_string(self) -> None:
        """Open string input dialog to create text object."""
        dialog = DialogWindows.open_new_string_input_dialog()
        ok, uri = dialog._run_dialog()
        if ok and uri:
            self.__open_media(uri)

    def __action_open_media_dir(self) -> None:
        """Open all media files from directory in grid layout."""
        directory = QFileDialog.getExistingDirectory(
            self, "Open media directory", self.__prev_dir)

        if directory:
            # Load all files
            media = []
            for filename in os.listdir(directory):
                if not os.path.isdir(filename):
                    mediaobject = self.__open_media(filename, add=False)
                    if mediaobject:
                        media.append(mediaobject)

            # Arrange in grid
            cells_per_side = ceil(sqrt(len(media)))
            cellsize = min(width, height) / cells_per_side

            for y in range(cells_per_side):
                for x in range(cells_per_side):
                    if not media: break
                    mediaobject = media.pop(0)

                    # Position in grid cell
                    mediaobject.fit(bbox)
                    mediaobject.centre = centre
                    mediaobject.aim('x', (x - grid_centre) * cellsize)
                    mediaobject.aim('y', (y - grid_centre) * cellsize)

                    self.zui.scene.add(mediaobject)

View Settings
^^^^^^^^^^^^^

.. code-block:: python

    def __action_set_fps(self, act: QAction) -> None:
        """Set framerate from action group."""
        self.zui.framerate = int(act.fps / 2)

    def __action_set_zoom_sensitivity(self) -> None:
        """Open dialog to adjust zoom sensitivity."""
        ok, text = DialogWindows._open_zoom_sensitivity_input_dialog(
            self.zui.zoom_sensitivity)

        if ok and text:
            value = int(text)
            if 0 < value <= 100:
                self.zui.zoom_sensitivity = int(1000 / value)
            elif value == 0:
                self.zui.zoom_sensitivity = 1000

    def __action_fullscreen(self) -> None:
        """Toggle fullscreen mode."""
        self.setWindowState(
            self.windowState() ^ Qt.WindowFullScreen)

Error Handling
^^^^^^^^^^^^^^

.. code-block:: python

    def __show_error(self, text: str, details: Any) -> None:
        """Display error dialog with details."""
        dialog = QMessageBox(self)
        dialog.setWindowTitle("PyZUI - Error")
        dialog.setText(text)
        dialog.setDetailedText(str(details))
        dialog.setIcon(QMessageBox.Warning)
        dialog.exec()

**Quit Confirmation:**

When the user attempts to quit (Ctrl+Q), a confirmation dialog is shown with three options:

- **Yes**: Quit without saving
- **No**: Cancel quit
- **Save and Quit**: Save scene then quit

QZUI Widget
~~~~~~~~~~~

The :class:`QZUI` class extends both :class:`QWidget` and :class:`Thread`, serving as
the central rendering widget that displays the scene and handles user input.

**Class Definition:**

.. code-block:: python

    class QZUI(QtWidgets.QWidget, Thread):
        # Signal for error reporting
        error = QtCore.Signal()

        def __init__(self, parent=None, framerate=10,
                     zoom_sensitivity=20):
            QtWidgets.QWidget.__init__(self, parent)
            Thread.__init__(self)

            self.__scene = Scene.new()
            self.__timer = QtCore.QBasicTimer()

            self.framerate = framerate
            self.zoom_sensitivity = zoom_sensitivity
            self.reduced_framerate = 3

            self.setFocusPolicy(Qt.ClickFocus)
            self.setMouseTracking(True)

**Key Attributes:**

- ``__scene``: The Scene object being rendered
- ``__timer``: QBasicTimer for animation updates
- ``framerate``: Target framerate (default: 10 FPS)
- ``zoom_sensitivity``: Zoom speed (default: 20)
- ``reduced_framerate``: Framerate when idle (default: 3 FPS)
- ``__draft``: Boolean flag for draft vs high-quality rendering
- ``__mouse_left_down``: Left mouse button state
- ``__mouse_right_down``: Right mouse button state
- ``__mousepos``: Current mouse position (x, y)
- ``__shift_held``: Shift key state
- ``__alt_held``: Alt key state
- ``__dropped_frames``: Counter for frame skipping
- ``__active_object``: Currently active object (scene or selection)

**Active Object Logic:**

The active object determines what gets moved/zoomed:

.. code-block:: python

    @property
    def __active_object(self):
        """Return the currently active object (selection or scene)."""
        if self.scene.selection:
            return self.scene.selection  # Selected object
        else:
            return self.scene  # Whole scene

Rendering System
^^^^^^^^^^^^^^^^

The rendering system uses a timer-based approach with frame dropping for performance:

**Paint Event:**

.. code-block:: python

    def paintEvent(self, event: QPaintEvent) -> None:
        """Custom painting - render the scene."""
        # Step physics simulation
        if self.framerate:
            self.scene.step(1.0 / self.framerate)

        painter = QPainter()
        painter.begin(self)
        try:
            # Fill background
            painter.fillRect(0, 0, width, height, Qt.black)

            # Render scene (draft or high-quality)
            self.scene.render(painter, self.__draft)
        finally:
            painter.end()

        # Stop velocity if dragging
        if self.__mouse_left_down:
            self.__active_object.vx = 0.0
            self.__active_object.vy = 0.0

**Timer Event:**

.. code-block:: python

    def timerEvent(self, event: QTimerEvent) -> None:
        """Handle timer ticks for animation."""
        if self.scene.moving:
            # Scene is animating - use draft mode
            self.__dropped_frames = 0
            self.__draft = True
            self.update()  # Trigger repaint
        else:
            # Scene is idle - can do high-quality rendering
            if self.__dropped_frames >= framerate / reduced_framerate:
                # Enough frames dropped, do HQ render
                self.__dropped_frames = 0
                self.__draft = False
                self.repaint()
            else:
                # Drop this frame
                self.__dropped_frames += 1

**Rendering Modes:**

- **Draft Mode**: Fast rendering when scene is moving
  - Used during animation
  - Lower quality but responsive

- **High-Quality Mode**: Slow rendering when scene is idle
  - Used after animation stops
  - Higher quality but expensive
  - Only rendered at reduced framerate (e.g., 3 FPS)

Mouse Event Handling
^^^^^^^^^^^^^^^^^^^^

**Mouse Press:**

.. code-block:: python

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse button press."""
        pos = (int(event.position().x()),
               int(event.position().y()))

        if event.button() == Qt.LeftButton:
            self.__mouse_left_down = True
            self.__mousepos = pos

            if not self.__shift_held:
                # Select object under cursor
                self.scene.selection = self.scene.get(pos)

        elif event.button() == Qt.RightButton:
            self.__mouse_right_down = True
            self.__mousepos = pos

            if not self.__shift_held:
                # Right-click selection (for editing)
                self.scene.right_selection = self.scene.get(pos)

**Mouse Move:**

.. code-block:: python

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse movement (dragging)."""
        if (event.buttons() & Qt.LeftButton) and self.__mouse_left_down:
            # Calculate mouse delta
            mx = int(event.position().x()) - self.__mousepos[0]
            my = int(event.position().y()) - self.__mousepos[1]

            # Set velocity to reach mouse position in one frame
            t = 1.0 / self.framerate
            self.__active_object.aim('x', mx, t)
            self.__active_object.aim('y', my, t)

        # Update mouse position
        self.__mousepos = (int(event.position().x()),
                          int(event.position().y()))

**Mouse Release:**

.. code-block:: python

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse button release."""
        if event.button() == Qt.LeftButton:
            self.__mouse_left_down = False

**Mouse Wheel (Zoom):**

.. code-block:: python

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle mouse wheel for zooming."""
        num_degrees = event.angleDelta().y()
        num_steps = round(num_degrees / self.zoom_sensitivity, 3)

        self.__mousepos = (int(event.position().x()),
                          int(event.position().y()))
        self.__zoom(num_steps)

    def __zoom(self, num_steps: float) -> None:
        """Zoom active object by num_steps."""
        if self.__alt_held:
            scale = 1.0 / 16  # Fine zoom with Alt
        else:
            scale = 1.0

        # Set zoom center to mouse position
        self.__active_object.centre = self.__mousepos
        # Add to zoom velocity
        self.__active_object.vz += scale * num_steps

Keyboard Event Handling
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events."""
        key = event.key()

        # Navigation
        if key == Qt.Key_Escape:
            self.scene.selection = None

        elif key == Qt.Key_PageUp:
            self.__zoom(1.0)  # Zoom in

        elif key == Qt.Key_PageDown:
            self.__zoom(-1.0)  # Zoom out

        elif key == Qt.Key_Up:
            self.__active_object.vy -= move_amount

        elif key == Qt.Key_Down:
            self.__active_object.vy += move_amount

        elif key == Qt.Key_Left:
            self.__active_object.vx -= move_amount

        elif key == Qt.Key_Right:
            self.__active_object.vx += move_amount

        # Centering
        elif key == Qt.Key_Space:
            self.__centre()  # Center object under mouse

        # Object removal
        elif key == Qt.Key_Delete:
            if self.scene.selection:
                self.scene.remove(self.scene.selection)
                self.scene.selection = None

        # Modifier keys
        elif key == Qt.Key_Shift:
            self.__shift_held = True

        elif key == Qt.Key_Alt:
            self.__alt_held = True

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        """Handle key release events."""
        key = event.key()

        if key == Qt.Key_Shift:
            self.__shift_held = False

        elif key == Qt.Key_Alt:
            self.__alt_held = False

**Keyboard Shortcuts:**

.. code-block:: text

    Navigation:
        Arrow Keys      - Pan scene/object
        Page Up/Down    - Zoom in/out
        Mouse Wheel     - Zoom in/out
        Space           - Center object under cursor
        Alt + Action    - Fine control (1/16 speed)

    Selection:
        Left Click      - Select object
        Right Click     - Right-select (for editing StringMediaObject)
        Escape          - Clear selection
        Shift + Click   - Interact without changing selection

    Object Manipulation:
        Left Drag       - Move object/scene
        Wheel           - Zoom object/scene
        Delete          - Remove selected object

Dialog System
-------------

DialogWindows Container
~~~~~~~~~~~~~~~~~~~~~~~

The :class:`DialogWindows` class serves as a static container for all dialog components:

.. code-block:: python

    class DialogWindows:
        """Container for dialog-related functionality."""

        # Static methods
        _open_zoom_sensitivity_input_dialog = staticmethod(...)

        # Nested classes
        open_new_string_input_dialog = OpenNewStringInputDialog
        modify_string_input_dialog = ModifyStringInputDialog

OpenNewStringInputDialog
~~~~~~~~~~~~~~~~~~~~~~~~

Dialog for creating new text objects with color selection.

**Features:**

- **Text Input**: Multi-line text editor with 16pt font
- **Color Selection**: Grid of 24 recently used colors
- **Custom Colors**: Hex color input field (e.g., #ff5733)
- **Color Persistence**: Recent colors saved to ``~/.pyzui/colorstore/color_list.txt``
- **Color Display**: Visual color squares next to hex codes

**Dialog Layout:**

.. code-block:: text

    ┌───────────────────────────────────────────────────┐
    │  String input:                            [X]     │
    ├───────────────────────────────────────────────────┤
    │                                                   │
    │  ┌──────────────────────┐  ┌──────────┐           │
    │  │                      │  │ ■ ff0000 │           │
    │  │  Multi-line text     │  │ ■ 00ff00 │           │
    │  │  editor              │  │ ■ 0000ff │           │
    │  │  (QTextEdit)         │  │ ■ ffff00 │           │
    │  │                      │  │ ■ ff00ff │           │
    │  │                      │  │    ...   │           │
    │  └──────────────────────┘  │          │           │
    │  ┌──────────────────────┐  │          │           │
    │  │ Custom color: #_____ │  │          │           │
    │  └──────────────────────┘  └──────────┘           │
    │                                                   │
    │              [Cancel]  [OK]                       │
    └───────────────────────────────────────────────────┘

**Usage:**

.. code-block:: python

    dialog = DialogWindows.open_new_string_input_dialog()
    ok, uri = dialog._run_dialog()

    if ok and uri:
        # uri format: "string:RRGGBB:text content"
        # Example: "string:ff0000:Hello World"
        mediaobject = StringMediaObject(uri, scene)

**Color Storage:**

Colors are stored in a deque (max 24 items) and persisted to disk:

- **Windows**: ``%APPDATA%\pyzui\colorstore\color_list.txt``
- **Unix/Linux**: ``~/.pyzui/colorstore/color_list.txt``

Format: One hex color per line (e.g., ``ff0000``)

ModifyStringInputDialog
~~~~~~~~~~~~~~~~~~~~~~~

Dialog for editing existing text objects.

**Features:**

- **Pre-filled Text**: Loads existing text from media_id
- **Pre-selected Color**: Shows current color
- **Same Interface**: Identical to OpenNewStringInputDialog
- **Color Change**: Can change text color
- **Text Edit**: Can modify text content

**Usage:**

.. code-block:: python

    # Right-click on StringMediaObject triggers this
    dialog = DialogWindows.modify_string_input_dialog(media_id)
    ok, new_media_id, color, text = dialog._run_dialog()

    if ok and new_media_id:
        # Update StringMediaObject properties
        obj._media_id = new_media_id
        obj._StringMediaObject__str = text
        obj._StringMediaObject__color = QColor('#' + color)
        obj.lines = parsed_lines

**Media ID Parsing:**

.. code-block:: python

    # Parse existing media_id
    if media_id.startswith('string:'):
        color = media_id[7:13]   # Extract RRGGBB
        text = media_id[14:]     # Extract text content

ZoomSensitivityDialog
~~~~~~~~~~~~~~~~~~~~~

Simple input dialog for adjusting zoom sensitivity.

**Features:**

- **Range**: 0-100 (higher = more sensitive)
- **Current Value**: Displays current setting
- **Real-time Update**: Changes take effect immediately

**Dialog:**

.. code-block:: text

    ┌────────────────────────────────────────┐
    │  Set zoom sensitivity           [X]    │
    ├────────────────────────────────────────┤
    │                                        │
    │  Sensitivity goes from 0 to 100,       │
    │  current: 50                           │
    │                                        │
    │  ┌──────────────────────────────────┐  │
    │  │ 50                               │  │
    │  └──────────────────────────────────┘  │
    │                                        │
    │              [Cancel]  [OK]            │
    └────────────────────────────────────────┘

**Usage:**

.. code-block:: python

    ok, text = DialogWindows._open_zoom_sensitivity_input_dialog(
        current_sensitivity)

    if ok and text:
        value = int(text)
        if 0 < value <= 100:
            # Convert to internal representation
            zoom_sensitivity = int(1000 / value)
        elif value == 0:
            zoom_sensitivity = 1000  # Maximum sensitivity

**Sensitivity Mapping:**

.. code-block:: text

    User Value → Internal Value → Zoom Speed
    ──────────────────────────────────────────
    100        → 10               → Fastest
    50         → 20               → Medium
    10         → 100              → Slow
    1          → 1000             → Very slow
    0          → 1000             → Maximum

Integration Patterns
--------------------

Scene and Window Communication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The window system communicates with the scene through property access and method calls:

.. code-block:: python

    # MainWindow → QZUI → Scene
    main_window.zui.scene = new_scene

    # QZUI → Scene (rendering)
    self.scene.step(dt)
    self.scene.render(painter, draft)

    # QZUI → Scene (selection)
    self.scene.selection = self.scene.get(mouse_pos)

    # QZUI → Scene (modification)
    self.scene.add(mediaobject)
    self.scene.remove(mediaobject)

**Signal/Slot Connections:**

.. code-block:: python

    # Error reporting from QZUI to MainWindow
    self.zui.error.connect(self.__show_error)

    # When QZUI encounters an error
    self.error.emit("Error message", details)

Viewport Resizing
~~~~~~~~~~~~~~~~~

When the window is resized, the scene viewport automatically adjusts:

.. code-block:: python

    # In QZUI.resizeEvent (implicit from QWidget)
    def resizeEvent(self, event: QResizeEvent) -> None:
        """Handle window resize."""
        # Qt automatically triggers this
        # Scene viewport_size property handles the update
        self.scene.viewport_size = (self.width(), self.height())

The Scene's ``viewport_size`` setter handles:

1. Centering the scene in new viewport
2. Scaling to maintain apparent size
3. Updating all MediaObject positions

Selection Visualization
~~~~~~~~~~~~~~~~~~~~~~~

Selected objects are highlighted with colored borders:

.. code-block:: python

    # In Scene.render()
    if self.selection:
        x1, y1 = self.selection.topleft
        x2, y2 = self.selection.bottomright

        painter.setPen(Qt.green)  # Green for left-click selection
        painter.drawRect(x1, y1, x2-x1, y2-y1)

    if self.right_selection:
        x1, y1 = self.right_selection.topleft
        x2, y2 = self.right_selection.bottomright

        painter.setPen(Qt.blue)  # Blue for right-click selection
        painter.drawRect(x1, y1, x2-x1, y2-y1)

Performance Optimization
------------------------

Frame Rate Management
~~~~~~~~~~~~~~~~~~~~~

The window system uses adaptive frame rates to balance responsiveness and quality:

**Normal Operation:**

- **Target Framerate**: 10 FPS (configurable: 10, 20, 30, 40)
- **Rendering Mode**: Draft (fast)
- **Triggered**: When scene.moving is True

**Idle Optimization:**

- **Reduced Framerate**: 3 FPS
- **Rendering Mode**: High-quality (slow)
- **Triggered**: When scene.moving is False

**Frame Dropping Logic:**

.. code-block:: python

    frames_to_skip = framerate / reduced_framerate
    # Example: 10 / 3 ≈ 3 frames

    # Drop 3 frames, then do HQ render on 4th frame
    # Effective rate: 10 FPS → ~2.5 FPS for HQ rendering

Draft vs High-Quality Rendering
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Draft Mode:**

- Used during animation and interaction
- Fast tile scaling (Qt.FastTransformation)
- Temporary tile caching
- Lower visual quality but responsive

**High-Quality Mode:**

- Used when idle
- Better tile rendering
- Final tile loading
- Higher visual quality but slower

Memory Management
~~~~~~~~~~~~~~~~~

**Tile Caching:**

The window system triggers tile loading through the rendering pipeline:

.. code-block:: python

    # TiledMediaObject.render() loads tiles on demand
    # TileManager caches tiles in memory (LRU)
    # Old tiles automatically purged when scene objects removed

**Scene Object Limits:**

No hard limit on objects, but performance degrades with:

- More than ~100 visible objects
- Very large viewport sizes
- High frame rates (30-40 FPS)

Event Handling Details
----------------------

Event Propagation
~~~~~~~~~~~~~~~~~

Qt events propagate through the widget hierarchy:

.. code-block:: text

    QApplication
        │
        ▼
    MainWindow
        │
        ▼
    QZUI (central widget)
        │
        ▼
    Event handlers
        • mousePressEvent
        • mouseMoveEvent
        • keyPressEvent
        • etc.

**Event Acceptance:**

.. code-block:: python

    def mousePressEvent(self, event: QMouseEvent) -> None:
        # Handle event
        ...
        # Event is implicitly accepted
        # (doesn't propagate to parent)

Mouse Tracking
~~~~~~~~~~~~~~

Mouse tracking is enabled to receive move events even without buttons pressed:

.. code-block:: python

    self.setMouseTracking(True)

This allows:

- Updating ``__mousepos`` continuously
- Zoom centering on mouse position
- Cursor position tracking

Focus Policy
~~~~~~~~~~~~

The QZUI widget uses click focus:

.. code-block:: python

    self.setFocusPolicy(Qt.ClickFocus)

This means:

- Keyboard events only received when widget has focus
- Focus gained by clicking widget
- Focus automatically set when MainWindow shown

Thread Safety
~~~~~~~~~~~~~

The QZUI class extends Thread but doesn't actually use threading for rendering.
Instead, Qt's event loop handles all updates:

.. code-block:: python

    class QZUI(QWidget, Thread):
        # Thread inheritance is legacy
        # All rendering happens in main Qt thread
        pass

**Timer-based Updates:**

.. code-block:: python

    # Timer runs in main thread
    self.__timer = QBasicTimer()
    self.__timer.start(1000 / framerate, self)

    # timerEvent called in main thread
    def timerEvent(self, event):
        self.update()  # Trigger repaint

Usage Examples
--------------

Basic Application Setup
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from PySide6.QtWidgets import QApplication
    from pyzui.windows.mainwindow import MainWindow

    # Create Qt application
    app = QApplication(sys.argv)

    # Create main window with custom settings
    window = MainWindow(framerate=20, zoom_sensitivity=50)

    # Show window
    window.show()
    window.resize(1920, 1080)

    # Run event loop
    sys.exit(app.exec())

Custom QZUI Widget
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Embed QZUI in custom window
    from pyzui.objects.scene.qzui import QZUI
    from pyzui.objects.scene.scene import Scene

    class CustomWindow(QMainWindow):
        def __init__(self):
            super().__init__()

            # Create QZUI widget
            self.zui = QZUI(self, framerate=30, zoom_sensitivity=20)
            self.setCentralWidget(self.zui)

            # Load custom scene
            self.zui.scene = Scene.load_scene('custom.pzs')

            # Start animation timer
            self.zui.start()

Programmatic Scene Manipulation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Access scene through window
    scene = window.zui.scene

    # Add media programmatically
    from pyzui.objects.mediaobjects import TiledMediaObject

    img = TiledMediaObject('photo.jpg', scene)
    img.pos = (0, 0)
    img.zoomlevel = 0
    scene.add(img)

    # Animate to position
    img.aim('x', 500)  # Move 500 pixels right
    img.aim('z', 1.0)  # Zoom in by factor of 2

Custom Dialogs
~~~~~~~~~~~~~~

.. code-block:: python

    # Custom string input
    from pyzui.windows.dialogwindows import OpenNewStringInputDialog

    dialog = OpenNewStringInputDialog()
    ok, uri = dialog._run_dialog()

    if ok and uri:
        print(f"Created string: {uri}")
        # uri format: "string:RRGGBB:text"

Event Filtering
~~~~~~~~~~~~~~~

.. code-block:: python

    # Install event filter to intercept events
    class EventFilter(QObject):
        def eventFilter(self, obj, event):
            if event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_F1:
                    print("Help requested")
                    return True  # Event handled
            return False  # Continue propagation

    event_filter = EventFilter()
    window.zui.installEventFilter(event_filter)

API Reference
-------------

MainWindow
~~~~~~~~~~

.. code-block:: python

    class MainWindow(QMainWindow):
        def __init__(self, framerate: int = 10,
                     zoom_sensitivity: int = 50) -> None

        def sizeHint(self) -> QSize
        def minimumSizeHint(self) -> QSize

        # Public attributes
        self.zui: QZUI

QZUI
~~~~

.. code-block:: python

    class QZUI(QWidget, Thread):
        error = Signal()  # Qt signal for error reporting

        def __init__(self, parent=None, framerate=10,
                     zoom_sensitivity=20) -> None

        # Properties
        @property
        def scene(self) -> Scene

        @scene.setter
        def scene(self, scene: Scene) -> None

        # Event handlers (called by Qt)
        def paintEvent(self, event: QPaintEvent) -> None
        def timerEvent(self, event: QTimerEvent) -> None
        def wheelEvent(self, event: QWheelEvent) -> None
        def mousePressEvent(self, event: QMouseEvent) -> None
        def mouseMoveEvent(self, event: QMouseEvent) -> None
        def mouseReleaseEvent(self, event: QMouseEvent) -> None
        def keyPressEvent(self, event: QKeyEvent) -> None
        def keyReleaseEvent(self, event: QKeyEvent) -> None

DialogWindows
~~~~~~~~~~~~~

.. code-block:: python

    class DialogWindows:
        # Static container for dialog components

        @staticmethod
        def _open_zoom_sensitivity_input_dialog(
            current: float) -> Tuple[bool, str]

        class open_new_string_input_dialog:
            def __init__(self) -> None
            def _run_dialog(self) -> Tuple[bool, str]

        class modify_string_input_dialog:
            def __init__(self, media_id: Optional[str]) -> None
            def _run_dialog(self) -> Tuple[bool, str, str, str]

Key Classes
~~~~~~~~~~~

- :class:`pyzui.windows.mainwindow.MainWindow` - Main application window
- :class:`pyzui.objects.scene.qzui.QZUI` - Central rendering widget
- :class:`pyzui.windows.dialogwindows.dialogwindows.DialogWindows` - Dialog container
- :class:`pyzui.windows.dialogwindows.stringinputdialog.OpenNewStringInputDialog` - New string dialog
- :class:`pyzui.windows.dialogwindows.modifystringdialog.ModifyStringInputDialog` - Edit string dialog
- :class:`pyzui.windows.dialogwindows.zoomsensitivitydialog.open_zoom_sensitivity_input_dialog` - Zoom settings

See Also
--------

- :doc:`objectsystem` - Scene and MediaObject architecture
- :doc:`tilingsystem` - Tile rendering system
- :doc:`../usageinstructions/userinterface` - User interaction guide
- :doc:`projectstructure` - Overall project organization
