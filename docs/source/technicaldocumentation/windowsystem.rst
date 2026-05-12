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
2. Managing multiple scene tabs via a ``QTabWidget``
3. Rendering the zooming user interface in real-time
4. Handling user input (mouse, keyboard, touch)
5. Managing dialogs for user interactions (string, SVG, tiled media, zoom, autosave)
6. Coordinating between UI events and scene updates
7. Providing visual feedback (selection borders, loading indicators)

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
        │   • Tab management (add/close/switch)
        │
        └── QTabWidget (central widget)
            │   • Contains one or more QZUI tabs
            │   • Tab bar for switching scenes
            │   • Close button on each tab
            │
            └── QZUI (QWidget + Thread) × N
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
    ├── OpenSVGPickerInputDialog
    │       • Browse SVG files from data/SVG/
    │       • Scrollable SVG preview panels
    │       • Color selection (24 recent colors)
    │       • Thickness control
    │
    ├── ModifySVGInputDialog
    │       • Modify stroke color of SVG shapes
    │       • Change line thickness
    │       • Integrates with SVGCache
    │       • Triggered by right-click on SVG
    │
    ├── ModifyTiledMediaObjectDialog
    │       • Rotate left / rotate right
    │       • Invert colors toggle
    │       • Black and white toggle
    │       • Preview then apply pattern
    │       • Triggered by right-click on tiled media
    │
    ├── ZoomSensitivityDialog
    │       • Adjust zoom speed (0–100)
    │       • Real-time sensitivity update
    │
    ├── ZoomSettingsDialog
    │       • Configure min/max zoom levels
    │       • Clamp zoom to limits toggle
    │       • Default zoom for new scenes
    │       • Accessed via Settings menu
    │
    └── AutosaveSettingsDialog
            • Enable/disable autosave
            • Set interval (1–1440 min)
            • Set max backups (1–1000)
            • Set expire days (1–365)
            • Accessed via Settings menu

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
application window, providing menus, actions, tab management, and file operations.

**Class Definition:**

.. code-block:: python

    class MainWindow(QtWidgets.QMainWindow):
        def __init__(self, framerate: int = 20,
                     zoom_sensitivity: int = 50,
                     icon: QtGui.QIcon | None = None,
                     config: dict[str, Any] | None = None,
                     autosave_config: dict[str, Any] | None = None) -> None:
            QtWidgets.QMainWindow.__init__(self)

            self.setWindowTitle("PyZUI")
            self.__config = config or {}
            self.__autosave_config = autosave_config or {}

            # Tab widget is the central widget
            self.__tab_widget = QTabWidget()
            self.__tab_widget.setTabsClosable(True)
            self.setCentralWidget(self.__tab_widget)

            self.__create_actions()
            self.__create_menus()

            # Create initial tab
            self._add_tab()

**Key Attributes:**

- ``__tab_widget``: QTabWidget central widget containing all scene tabs
- ``__zui_tabs``: List of ``(QZUI, Scene)`` tuples, one per tab
- ``current_zui``: Property returning the active tab's QZUI
- ``zui``: Backward-compatible property returning current tab's QZUI
- ``__action``: Dictionary of QAction objects for menu items
- ``__menu``: Dictionary of QMenu objects
- ``__prev_dir``: Last used directory for file dialogs
- ``__config``: Configuration dictionary loaded at startup
- ``__autosave_config``: Autosave configuration subsection

**Window Properties:**

- **Default Size**: 1280x720 pixels (sizeHint)
- **Minimum Size**: 160x120 pixels (minimumSizeHint)
- **Resizable**: Yes, viewport adapts to window size

**Tab System:**

MainWindow manages multiple scenes through a ``QTabWidget``:

.. code-block:: python

    @property
    def current_zui(self) -> QZUI | None:
        """Return the QZUI of the currently active tab."""
        idx = self.__tab_widget.currentIndex()
        if idx >= 0 and idx < len(self.__zui_tabs):
            return self.__zui_tabs[idx][0]
        return None

    @property
    def zui(self) -> QZUI | None:
        """Backward-compatible accessor for current tab's QZUI."""
        return self.current_zui

    def _add_tab(self, scene: Scene | None = None) -> None:
        """Create a new tab with a fresh QZUI and Scene."""
        zui = QZUI(self, self.__config.get('framerate', self.framerate),
                    self.__config.get('zoom_sensitivity', self.zoom_sensitivity))
        if scene is not None:
            zui.scene = scene
        zui.start()
        tab_idx = self.__tab_widget.addTab(zui, f"Scene {len(self.__zui_tabs) + 1}")
        self.__zui_tabs.append((zui, zui.scene))
        self.__tab_widget.setCurrentIndex(tab_idx)

    def _close_tab(self, index: int) -> None:
        """Close a tab, stop autosave, and purge tiles."""
        zui, scene = self.__zui_tabs[index]
        scene.shutdown_threads()
        tilemanager.purge()  # Purge tiles from closed scene
        self.__tab_widget.removeTab(index)
        del self.__zui_tabs[index]

    def _on_tab_changed(self, index: int) -> None:
        """Sync render order checkbox and window title on tab switch."""
        zui = self.current_zui
        if zui:
            self.setWindowTitle(f"PyZUI - {zui.scene.__last_save_path or 'Untitled'}")

**Menu Structure:**

.. code-block:: text

    File
    ├── New Tab                     (Ctrl+T)
    ├── Close Tab                   (Ctrl+W)
    ├── ─────────────────────────
    ├── New Scene                   (Ctrl+N)
    ├── Open Scene                  (Ctrl+O)
    ├── Import Scene                (Ctrl+I)
    ├── Open Home Scene             (Ctrl+Home)
    ├── Save Scene                  (Ctrl+S)
    ├── Save Screenshot             (Ctrl+H)
    ├── Open Local Media            (Ctrl+L)
    ├── Open new String             (Ctrl+U)
    ├── Open new SVG                (Ctrl+G)
    ├── Open Media Directory        (Ctrl+D)
    └── Quit                        (Ctrl+Q)

    View
    ├── Set Framerate ▶
    │   ├── 10 FPS
    │   ├── 20 FPS
    │   ├── 30 FPS
    │   └── 40 FPS
    ├── Adjust Sensitivity
    ├── Fullscreen                  (Ctrl+F)
    └── Render Order: Smaller on Top (Ctrl+R)

    Actions
    ├── Copy SVG                    (Ctrl+C)
    └── Paste SVG                   (Ctrl+V)

    Settings
    ├── Autosave Settings
    └── Zoom Settings

    Help
    ├── About
    └── About Qt

**Right-Click Context Menu:**

The Scene handles right-click events and shows a context menu based on
the selected object type:

- **TiledMediaObject**: Opens :ref:`modify-tiled-media-dialog` for image
  manipulation (rotate, invert, B&W)
- **SVGMediaObject**: Opens :ref:`modify-svg-input-dialog` for changing
  stroke color and line thickness
- **StringMediaObject**: Opens :ref:`modify-string-input-dialog` for
  editing text content and color

**Key Methods:**

Scene Operations
^^^^^^^^^^^^^^^^

.. code-block:: python

    def __action_new_scene(self) -> None:
        """Create a new empty scene in current tab."""
        self.current_zui.scene = Scene.new()

    def __action_open_scene(self) -> None:
        """Open scene from .pzs file via file dialog. Opens in new tab."""
        filename = QFileDialog.getOpenFileName(
            self, "Open scene", self.__prev_dir,
            "PyZUI Scenes (*.pzs)")
        if filename:
            scene = Scene.load_scene(filename)
            self._add_tab(scene)

    def __action_save_scene(self) -> None:
        """Save current scene to .pzs file.
        If objects are selected, saves only the selection."""
        filename = QFileDialog.getSaveFileName(
            self, "Save scene", "scene.pzs",
            "PyZUI Scenes (*.pzs)")
        if not filename:
            return
        scene = self.current_zui.scene
        if scene.selection:
            # Save only selected objects (header: "0 0 0")
            scene.save_selection(filename, scene.selection)
        else:
            scene.save(filename)

    def __action_save_screenshot(self) -> None:
        """Save screenshot to image file."""
        filename = QFileDialog.getSaveFileName(
            self, "Save screenshot", "screenshot.png",
            "Images (*.bmp *.jpg *.png ...)")
        if filename:
            pixmap = self.current_zui.grab()
            pixmap.save(filename)

Media Import
^^^^^^^^^^^^

.. code-block:: python

    def __open_media(self, media_id: str, add: bool = True):
        """Open media and optionally add to scene."""
        # Detect media type from file extension
        if media_id.startswith('string:'):
            mediaobject = StringMediaObject(media_id, self.current_zui.scene)
        elif media_id.lower().endswith('.svg'):
            mediaobject = SVGMediaObject(media_id, self.current_zui.scene)
        else:
            mediaobject = TiledMediaObject(media_id, self.current_zui.scene)

        if add:
            # Fit to center 50% of viewport
            zui = self.current_zui
            w, h = zui.width(), zui.height()
            mediaobject.fit((w/4, h/4, w*3/4, h*3/4))
            zui.scene.add(mediaobject)

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

    def __action_open_media_svg(self) -> None:
        """Open SVG picker dialog to create SVG object."""
        dialog = DialogWindows.open_svg_picker_input_dialog()
        ok, uri = dialog._run_dialog()
        if ok and uri:
            self.__open_media(uri)

    # Supported file extensions for media opening
    SUPPORTED_EXTENSIONS = {
        '.svg',                         # SVGMediaObject
        '.pdf',                         # PDFConverter
        '.ppm',                         # Direct PPM support
        '.jpg', '.jpeg',                # VipsConverter - JPEG
        '.png',                         # VipsConverter - PNG
        '.gif',                         # VipsConverter - GIF
        '.tif', '.tiff',                # VipsConverter - TIFF
        '.webp',                        # VipsConverter - WebP
        '.bmp',                         # VipsConverter - BMP
        '.heic', '.heif',               # VipsConverter - HEIC
        '.avif',                        # VipsConverter - AVIF
        '.jxl',                         # VipsConverter - JPEG XL
    }

    # Maximum file size for PDF files (2 MB)
    MAX_PDF_SIZE_BYTES = 2 * 1024 * 1024

    def __action_open_media_dir(self) -> None:
        """Open supported media files from directory in grid layout.

        Only files with extensions in SUPPORTED_EXTENSIONS are opened.
        PDF files larger than MAX_PDF_SIZE_BYTES (2 MB) are skipped.
        """
        directory = QFileDialog.getExistingDirectory(
            self, "Open media directory", self.__prev_dir)

        if directory:
            # Load supported files only
            media = []
            for filename in os.listdir(directory):
                if not os.path.isdir(filename):
                    # Check if file has a supported extension
                    ext = os.path.splitext(filename)[1].lower()
                    if ext not in self.SUPPORTED_EXTENSIONS:
                        continue
                    # Skip PDF files larger than 2 MB
                    if ext == '.pdf' and os.path.getsize(filename) > self.MAX_PDF_SIZE_BYTES:
                        continue
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

                    self.current_zui.scene.add(mediaobject)

View Settings
^^^^^^^^^^^^^

.. code-block:: python

    def __action_set_fps(self, act: QAction) -> None:
        """Set framerate from action group."""
        self.current_zui.framerate = int(act.fps / 2)

    def __action_set_zoom_sensitivity(self) -> None:
        """Open dialog to adjust zoom sensitivity."""
        ok, text = DialogWindows._open_zoom_sensitivity_input_dialog(
            self.current_zui.zoom_sensitivity)

        if ok and text:
            value = int(text)
            if 0 < value <= 100:
                self.current_zui.zoom_sensitivity = int(1000 / value)
            elif value == 0:
                self.current_zui.zoom_sensitivity = 1000

    def __action_fullscreen(self) -> None:
        """Toggle fullscreen mode."""
        self.setWindowState(
            self.windowState() ^ Qt.WindowFullScreen)

    def __action_toggle_render_order(self) -> None:
        """Toggle render order between smaller_on_top and larger_on_top.
        Persists setting to ~/.pyzui/config.json."""
        action = self.__action["render_order_smaller_top"]
        new_mode = "smaller_on_top" if action.isChecked() else "larger_on_top"
        scene = self.current_zui.scene
        scene.set_render_order(new_mode)

        # Persist to config
        config_manager = ConfigManager()
        full_config = config_manager.load()
        full_config["render"] = {"order": new_mode}
        config_manager.save(full_config)

    def __action_autosave_settings(self) -> None:
        """Open autosave settings dialog."""
        dialog = DialogWindows.autosave_settings_dialog(
            self.__autosave_config)
        ok, config = dialog._run_dialog()
        if ok and config:
            self.__autosave_config = config
            # Apply to current scene
            scene = self.current_zui.scene
            if hasattr(scene, 'autosave_manager'):
                scene.autosave_manager.set_autosave_config(config)

    def __action_zoom_settings(self) -> None:
        """Open zoom settings dialog for level limits."""
        from pyzui.windows.dialogwindows.zoomsettingsdialog import ZoomSettingsDialog
        dialog = ZoomSettingsDialog(self.__config.get('zoom', {}))
        ok, zoom_config = dialog._run_dialog()
        if ok and zoom_config:
            self.__config['zoom'] = zoom_config

Clipboard Actions
^^^^^^^^^^^^^^^^^

.. code-block:: python

    def __action_copy_svg(self) -> None:
        """Copy selected SVG objects to clipboard."""
        scene = self.current_zui.scene
        scene.copy_selected()

    def __action_paste_svg(self) -> None:
        """Paste SVG objects from clipboard."""
        scene = self.current_zui.scene
        scene.paste()

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
- ``framerate``: Target framerate (default: 10 FPS, overridden to 20 by MainWindow)
- ``zoom_sensitivity``: Zoom speed (default: 20, overridden to 50 by MainWindow)
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
            return self.scene.selection[0]  # First selected object
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
        Ctrl+Click      - Add to selection (bulk)
        Left Drag       - Area selection (lasso)
        Right Click     - Right-select (context menu for editing)
        Escape          - Clear selection
        Shift + Click   - Interact without changing selection

    Object Manipulation:
        Left Drag       - Move object/scene
        Wheel           - Zoom object/scene
        Delete          - Remove selected object
        Ctrl+C          - Copy SVG
        Ctrl+V          - Paste SVG

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

        # Nested classes / class-level references
        open_new_string_input_dialog = OpenNewStringInputDialog
        modify_string_input_dialog = ModifyStringInputDialog
        open_svg_picker_input_dialog = OpenSVGPickerInputDialog
        modify_svg_input_dialog = ModifySVGInputDialog
        modify_tiled_media_object_dialog = ModifyTiledMediaObjectDialog
        autosave_settings_dialog = AutosaveSettingsDialog

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

.. _modify-string-input-dialog:

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

.. _svg-picker-input-dialog:

OpenSVGPickerInputDialog

Dialog for browsing and selecting SVG files from ``data/SVG/``, with color
and thickness customization. Triggered by **File > Open new SVG** (Ctrl+G).

**Features:**

- **SVG Browser**: Scrollable grid of SVG file previews loaded from ``data/SVG/``
- **Preview Panels**: Each SVG is rendered at 64×64 for visual selection
- **Color Selection**: Grid of 24 recently used colors (shared with string dialogs)
- **Custom Colors**: Hex color input field
- **Thickness Control**: Line thickness for the selected SVG shape
- **Color Persistence**: Recent colors saved to ``~/.pyzui/colorstore/color_list.txt``

**Dialog Layout:**

.. code-block:: text

    ┌───────────────────────────────────────────────────┐
    │  SVG picker:                              [X]     │
    ├───────────────────────────────────────────────────┤
    │                                                   │
    │  ┌──────┬──────┬──────┬──────┬──────┐             │
    │  │ SVG  │ SVG  │ SVG  │ SVG  │ SVG  │             │
    │  │ icon │ icon │ icon │ icon │ icon │   ┌──────┐  │
    │  ├──────┼──────┼──────┼──────┼──────┤   │Color │  │
    │  │ SVG  │ SVG  │ SVG  │ SVG  │ SVG  │   │Grid  │  │
    │  │ icon │ icon │ icon │ icon │ icon │   │24 col│  │
    │  ├──────┼──────┼──────┼──────┼──────┤   │      │  │
    │  │ ...  │ ...  │ ...  │ ...  │ ...  │   │      │  │
    │  └──────┴──────┴──────┴──────┴──────┘   └──────┘  │
    │                                                   │
    │  Thickness: [===slider===]                        │
    │  Custom color: #_____                             │
    │                                                   │
    │              [Cancel]  [OK]                       │
    └───────────────────────────────────────────────────┘

**Usage:**

.. code-block:: python

    # Triggered by File > Open new SVG (Ctrl+G)
    dialog = DialogWindows.open_svg_picker_input_dialog()
    ok, uri = dialog._run_dialog()

    if ok and uri:
        # uri format: "svg:<hash>:<color>:<thickness>"
        mediaobject = SVGMediaObject(uri, scene)
        scene.add(mediaobject)

**Output Format:**

The dialog returns a ``uri`` string encoding the selected SVG, color, and thickness:

.. code-block:: text

    svg:<cache_hash>:<hex_color>:<thickness>

    Example:
        svg:a1b2c3d4:ff0000:3   → Red arrow, thickness 3

The SVG file is stored in SVGCache with its content hash, and the created
object references the cache entry.

.. _modify-svg-input-dialog:

ModifySVGInputDialog
~~~~~~~~~~~~~~~~~~~~

Dialog for modifying the stroke color and line thickness of existing SVG
objects. Triggered by right-clicking an SVG shape in the scene.

**Features:**

- **Color Change**: Recolor the SVG stroke using the color picker grid
- **Thickness Change**: Adjust line thickness with a slider
- **SVG Cache Integration**: Modified SVG is stored in SVGCache via content hash
- **Shape Detection**: Works with simple shapes (arrows, circles, squares,
  triangles) added via the SVG picker
- **Live Preview**: The dialog shows a preview of the current SVG

**Usage:**

.. code-block:: python

    # Triggered by right-click on SVGMediaObject in the scene
    dialog = DialogWindows.modify_svg_input_dialog(
        media_id=obj.media_id, color=current_color, thickness=current_thickness)
    ok, new_media_id = dialog._run_dialog()

    if ok and new_media_id:
        # Update the object's media reference
        obj._media_id = new_media_id
        obj._SVGMediaObject__is_modified = True
        obj.mark_as_modified()

**SVG Modification Process:**

1. The dialog loads the SVG content from SVGCache or file
2. User selects new color and/or thickness
3. The SVG XML is parsed and modified (stroke color and stroke-width)
4. Modified SVG is stored in SVGCache with a new content hash
5. The object's ``media_id`` is updated to point to the new cache entry
6. ``is_modified`` is set to True

**See Also:**

- :doc:`../pyzui/modifysvginputdialog` — API reference
- :doc:`../pyzui/svgcache` — SVG cache storage

.. _modify-tiled-media-dialog:

ModifyTiledMediaObjectDialog
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dialog for image manipulation of tiled media objects. Triggered by right-clicking
a ``TiledMediaObject`` in the scene. Added in v0.1.5.

**Features:**

- **Rotate Left**: 90° counter-clockwise rotation
- **Rotate Right**: 90° clockwise rotation
- **Invert Colors**: Negative color effect (toggle)
- **Black and White**: Convert to grayscale (toggle)
- **Preview then Apply**: All operations are preview-only until OK is clicked

**Dialog Layout:**

.. code-block:: text

    ┌────────────────────────────────────────┐
    │  Modify Image                   [X]    │
    ├────────────────────────────────────────┤
    │                                        │
    │  ┌──────────────────────────────────┐  │
    │  │                                  │  │
    │  │         Image Preview            │  │
    │  │                                  │  │
    │  └──────────────────────────────────┘  │
    │                                        │
    │  [Rotate Left]  [Rotate Right]         │
    │  [✓] Invert Colors                     │
    │  [✓] Black and White                   │
    │                                        │
    │              [Cancel]  [OK]            │
    └────────────────────────────────────────┘

**Usage:**

.. code-block:: python

    # Triggered by right-click on TiledMediaObject in the scene
    dialog = DialogWindows.modify_tiled_media_object_dialog(
        media_id=obj.media_id, ppmfile=tmpfile)
    ok, rotation, invert, bw = dialog._run_dialog()

    if ok:
        # Submit to converterrunner with accumulated transformations
        future = converterrunner.submit_vips_conversion(
            ppmfile, new_tmpfile,
            rotation=rotation,
            invert_colors=invert,
            black_and_white=bw,
        )
        handle = converterrunner.ConversionHandle(future, ppmfile, new_tmpfile)
        handle.join()

        # Replace object in scene preserving position/zoom
        scene.remove(obj)
        new_obj = TiledMediaObject(new_tmpfile, scene)
        new_obj.pos = obj.pos
        new_obj.zoomlevel = obj.zoomlevel
        new_obj.centre = obj.centre
        scene.add(new_obj)

**Object Replacement:**

When OK is clicked, all accumulated transformations are applied in a single
``VipsConverter`` pass. The original ``TiledMediaObject`` is removed from the
scene and replaced with a new one using the transformed PPM, preserving the
original position, zoom level, and center point.

**See Also:**

- :doc:`../pyzui/modifytiledmediaobjectdialog` — API reference
- :doc:`../pyzui/converterrunner` — Process-based parallel conversion

ZoomSensitivityDialog
~~~~~~~~~~~~~~~~~~~~~

Simple input dialog for adjusting zoom sensitivity (zoom speed).

**Features:**

- **Range**: 0–100 (higher = more sensitive)
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

ZoomSettingsDialog
~~~~~~~~~~~~~~~~~~

Dialog for configuring zoom level limits and clamping. Accessed via
**Settings > Zoom Settings**. This is distinct from ``ZoomSensitivityDialog``
(which controls zoom speed, not limits).

**Features:**

- **Min Zoom Level**: Minimum allowed zoom (range: -50 to 0, default: -10)
- **Max Zoom Level**: Maximum allowed zoom (range: 0 to 50, default: 12)
- **Clamp Toggle**: Enable or disable zoom clamping (checked by default)
- **Default Zoom Level**: Zoom level for new scenes (range: -10 to 12, default: 0)
- **Info Text**: Explanatory text about why limits exist (font visibility, float overflow, input precision)

**Dialog Layout:**

.. code-block:: text

    ┌────────────────────────────────────────────┐
    │  Zoom Settings                      [X]    │
    ├────────────────────────────────────────────┤
    │                                            │
    │  Configuration for zoom level limits.      │
    │  These settings prevent crashes at         │
    │  extreme zoom values and improve           │
    │  usability.                                │
    │                                            │
    │  Min Zoom Level: [-10]  (range: -50 to 0) │
    │  Max Zoom Level: [12 ]  (range: 0 to 50)  │
    │  [✓] Clamp zoom to limits                 │
    │                                            │
    │  Default Zoom Level: [0] (new scenes)      │
    │                                            │
    │  Performance note:                         │
    │  Extreme zoom levels can cause font        │
    │  rendering issues (too small) and          │
    │  floating-point overflow (too large).      │
    │                                            │
    │              [Cancel]  [OK]                │
    └────────────────────────────────────────────┘

**Usage:**

.. code-block:: python

    from pyzui.windows.dialogwindows.zoomsettingsdialog import ZoomSettingsDialog

    dialog = ZoomSettingsDialog({'min': -10, 'max': 12, 'default': 0})
    ok, zoom_config = dialog._run_dialog()

    if ok:
        # zoom_config = {'min': -5, 'max': 10, 'clamp': True, 'default': 0}
        zoom_manager.set_limits(zoom_config['min'], zoom_config['max'])
        zoom_manager.clamp_enabled = zoom_config['clamp']

**Integration with ZoomManager:**

The configured limits are applied to :class:`ZoomManager` which enforces them
during zoom operations. See :doc:`../pyzui/zoommanager` for details.

.. note::

   ``ZoomSettingsDialog`` (zoom level limits) and ``ZoomSensitivityDialog``
   (zoom speed) are **different dialogs** accessed from different menus:
   Settings > Zoom Settings vs. View > Adjust Sensitivity.

AutosaveSettingsDialog
~~~~~~~~~~~~~~~~~~~~~~

Dialog for configuring the autosave backup system. Accessed via
**Settings > Autosave Settings**.

**Features:**

- **Enable/Disable**: Checkbox to toggle autosave on/off
- **Interval**: Spinbox for backup interval in minutes (1–1440, default: 5)
- **Max Backups**: Spinbox for maximum backups per scene (1–1000, default: 20)
- **Expire Days**: Spinbox for days before inactive directories expire (1–365, default: 7)
- **Info Labels**: Explanatory text about backup directory structure and naming conventions

**Dialog Layout:**

.. code-block:: text

    ┌────────────────────────────────────────────┐
    │  Autosave Settings                  [X]    │
    ├────────────────────────────────────────────┤
    │                                            │
    │  [✓] Enable Autosave                       │
    │                                            │
    │  Backup Interval (minutes): [5  ]          │
    │  Max Backups to Keep:        [20 ]         │
    │  Expire After (days):        [7  ]         │
    │                                            │
    │  Backups are stored in:                    │
    │  ~/.pyzui/backups/                         │
    │  Each scene has its own subdirectory.      │
    │  Oldest backups are rotated automatically. │
    │                                            │
    │              [Cancel]  [OK]                │
    └────────────────────────────────────────────┘

**Usage:**

.. code-block:: python

    dialog = DialogWindows.autosave_settings_dialog({
        'enabled': True,
        'interval': 300,
        'max_backups': 20,
        'expire_days': 7,
    })
    ok, config = dialog._run_dialog()

    if ok:
        scene.autosave_manager.set_autosave_config(config)

**See Also:**

- :doc:`../pyzui/autosavesettingsdialog` — API reference
- :doc:`../pyzui/autosave` — SceneAutosaveManager
- :doc:`../pyzui/backupmanager` — BackupManager

Integration Patterns
--------------------

Scene and Window Communication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The window system communicates with the scene through property access and method calls:

.. code-block:: python

    # MainWindow → QZUI → Scene
    main_window.current_zui.scene = new_scene

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

**Context Menu Flow:**

.. code-block:: text

    User Right-Clicks Object in Scene
            │
            ▼
    Scene identifies object type
            │
    ┌───────┼───────────┬───────────┐
    ▼                   ▼           ▼
    StringMediaObject   SVGMedia    TiledMedia
    │                   Object      Object
    ▼                   ▼           ▼
    ModifyStringInput   ModifySVG   ModifyTiled
    Dialog              Dialog      MediaDialog
    (edit text/color)   (stroke     (rotate/
                         color/      invert/
                         thickness)  B&W)

Copy/Paste Flow:

.. code-block:: text

    User presses Ctrl+C
            │
            ▼
    MainWindow.__action_copy_svg()
            │
            ▼
    Scene.copy_selected() → SceneClipboardManager
            │
            ▼
    Selected SVGMediaObjects serialized to clipboard list

    User presses Ctrl+V
            │
            ▼
    MainWindow.__action_paste_svg()
            │
            ▼
    Scene.paste() → SceneClipboardManager
            │
            ▼
    New SVGMediaObjects created with offset

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
        for obj in self.selection:
            x1, y1 = obj.topleft
            x2, y2 = obj.bottomright

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

- **Target Framerate**: Configurable (10, 20, 30, 40 FPS — default 20)
- **Rendering Mode**: Draft (fast)
- **Triggered**: When scene.moving is True

**Idle Optimization:**

- **Reduced Framerate**: 3 FPS
- **Rendering Mode**: High-quality (slow)
- **Triggered**: When scene.moving is False

**Frame Dropping Logic:**

.. code-block:: python

    frames_to_skip = framerate / reduced_framerate
    # Example: 20 / 3 ≈ 6 frames

    # Drop 6 frames, then do HQ render on 7th frame
    # Effective rate: 20 FPS → ~2.9 FPS for HQ rendering

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
    # Old tiles automatically purged when tabs are closed

**Scene Object Limits:**

No hard limit on objects, but performance degrades with:

- More than ~100 visible objects
- Very large viewport sizes
- High frame rates (30–40 FPS)

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
    QTabWidget
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
    scene = window.current_zui.scene

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

    # String input
    from pyzui.windows.dialogwindows import OpenNewStringInputDialog

    dialog = OpenNewStringInputDialog()
    ok, uri = dialog._run_dialog()
    if ok and uri:
        print(f"Created string: {uri}")

    # SVG picker
    from pyzui.windows.dialogwindows import OpenSVGPickerInputDialog

    dialog = OpenSVGPickerInputDialog()
    ok, uri = dialog._run_dialog()
    if ok and uri:
        print(f"Created SVG: {uri}")

    # Autosave settings
    from pyzui.windows.dialogwindows import AutosaveSettingsDialog

    dialog = AutosaveSettingsDialog({'enabled': True, 'interval': 300})
    ok, config = dialog._run_dialog()
    if ok:
        print(f"New autosave config: {config}")

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
    window.current_zui.installEventFilter(event_filter)

API Reference
-------------

MainWindow
~~~~~~~~~~

.. code-block:: python

    class MainWindow(QMainWindow):
        # Class constants for media directory import
        SUPPORTED_EXTENSIONS: set[str]  # Supported file extensions
        MAX_PDF_SIZE_BYTES: int         # Maximum PDF file size (2 MB)

        def __init__(self, framerate: int = 20,
                     zoom_sensitivity: int = 50,
                     icon: QIcon | None = None,
                     config: dict[str, Any] | None = None,
                     autosave_config: dict[str, Any] | None = None) -> None

        def sizeHint(self) -> QSize
        def minimumSizeHint(self) -> QSize

        # Public attributes and properties
        current_zui: QZUI  # Active tab's QZUI
        zui: QZUI          # Backward-compatible alias for current_zui

        # Tab management
        def _add_tab(self, scene: Scene | None = None) -> None
        def _close_tab(self, index: int) -> None
        def _on_tab_changed(self, index: int) -> None

**Class Constants:**

- ``SUPPORTED_EXTENSIONS``: Set of supported file extensions for "Open Media Directory"
  (``.svg``, ``.pdf``, ``.ppm``, ``.jpg``, ``.jpeg``, ``.png``, ``.gif``, ``.tif``,
  ``.tiff``, ``.webp``, ``.bmp``, ``.heic``, ``.heif``, ``.avif``, ``.jxl``)
- ``MAX_PDF_SIZE_BYTES``: Maximum file size for PDF files when opening from directory
  (default: 2 MB = 2,097,152 bytes). Larger PDFs are skipped.

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

        class open_svg_picker_input_dialog:
            def __init__(self) -> None
            def _run_dialog(self) -> Tuple[bool, str]

        class modify_svg_input_dialog:
            def __init__(self, media_id: str, color: str,
                         thickness: int) -> None
            def _run_dialog(self) -> Tuple[bool, str]

        class modify_tiled_media_object_dialog:
            def __init__(self, media_id: str, ppmfile: str) -> None
            def _run_dialog(self) -> Tuple[bool, int, bool, bool]

        class autosave_settings_dialog:
            def __init__(self, config: dict) -> None
            def _run_dialog(self) -> Tuple[bool, dict]

Key Classes
~~~~~~~~~~~

- :class:`pyzui.windows.mainwindow.MainWindow` - Main application window with tab management
- :class:`pyzui.objects.scene.qzui.QZUI` - Central rendering widget (per tab)
- :class:`pyzui.windows.dialogwindows.dialogwindows.DialogWindows` - Dialog container
- :class:`pyzui.windows.dialogwindows.stringinputdialog.OpenNewStringInputDialog` - New string dialog
- :class:`pyzui.windows.dialogwindows.modifystringdialog.ModifyStringInputDialog` - Edit string dialog
- :class:`pyzui.windows.dialogwindows.svgpickerinputdialog.OpenSVGPickerInputDialog` - SVG file browser
- :class:`pyzui.windows.dialogwindows.modifysvginputdialog.ModifySVGInputDialog` - SVG color/thickness editor
- :class:`pyzui.windows.dialogwindows.modifytiledmediaobjectdialog.ModifyTiledMediaObjectDialog` - Image manipulation
- :class:`pyzui.windows.dialogwindows.zoomsensitivitydialog.open_zoom_sensitivity_input_dialog` - Zoom speed settings
- :class:`pyzui.windows.dialogwindows.zoomsettingsdialog.ZoomSettingsDialog` - Zoom level limits
- :class:`pyzui.windows.dialogwindows.autosavesettingsdialog.AutosaveSettingsDialog` - Autosave configuration

See Also
--------

- :doc:`objectsystem` - Scene and MediaObject architecture
- :doc:`tilingsystem` - Tile rendering system
- :doc:`../usageinstructions/userinterface` - User interaction guide
- :doc:`projectstructure` - Overall project organization
- :doc:`../pyzui/svgpickerinputdialog` - SVG picker dialog API
- :doc:`../pyzui/modifysvginputdialog` - SVG modifier dialog API
- :doc:`../pyzui/modifytiledmediaobjectdialog` - Tiled media modifier dialog API
- :doc:`../pyzui/autosavesettingsdialog` - Autosave settings dialog API
- :doc:`../pyzui/zoommanager` - Zoom level clamping
- :doc:`../pyzui/zoomsettingsdialog` - Zoom settings dialog API
- :doc:`../pyzui/autosave` - SceneAutosaveManager
