User Interface
==============

Upon startup of PyZUI, the user is presented with the home scene:

.. image:: ../../../data/home.png
   :align: center
   :width: 800px
   :alt: PyZUI logo

The menus provide the following actions:
----------------------------------------

File menu:
~~~~~~~~~~

- **New Tab (Ctrl+T)** Open a new tab with a fresh scene
- **Close Tab (Ctrl+W)** Close the current tab (does not close the last tab)
- **New Scene (Ctrl+N)** Create a blank scene in the current tab
- **Open Scene (Ctrl+O)** Open a saved scene in the current tab
- **Import Scene (Ctrl+I)** Import objects from a saved scene into the current scene
- **Open Home Scene (Ctrl+Home)** Return to the *home scene*
- **Save Scene (Ctrl+S)** Save the current scene
- **Save Screenshot (Ctrl+H)** Export the current viewport to an image
- **Open Local Media (Ctrl+L)** Open media from a local file
- **Open new String (Ctrl+U)** Opens an input window that allows you to insert
  text strings to be rendered on the interface. Newlines are considered making
  it possible to write paragraphs
- **Open new SVG (Ctrl+G)** Open the SVG picker to insert an SVG shape
- **Open Media Directory (Ctrl+D)** Open the media contained in a directory,
  and arrange it into a grid
- **Quit (Ctrl+Q)** Exit the application

View menu:
~~~~~~~~~~

- **Set Framerate** Set the rendering framerate: 10 FPS, 20 FPS, 30 FPS,
  or 40 FPS
- **Adjust Sensitivity** Set the movement/zoom sensitivity
- **Fullscreen (Ctrl+F)** Toggle fullscreen mode
- **Render Order: Smaller on Top (Ctrl+R)** Toggle whether smaller objects
  render above larger ones. When checked (default), smaller objects appear
  on top; when unchecked, larger objects render above smaller ones.

Settings menu:
~~~~~~~~~~~~~~

- **Autosave Settings** Configure autosave behavior including:
  - Enable/disable autosave (enabled by default)
  - Set autosave interval (1-1440 minutes)
  - Set maximum backups to keep per scene (1-1000)
  - Set backup directory expiration after inactivity (1-365 days)
  - Each scene gets its own backup directory: ``~/.pyzui/backups/<scene>_<hash>/``
  - Backup naming: ``yy_mm_dd_hh_mm_filename_hash.pzs``
  - Oldest backups are automatically deleted when limit is reached
  - Inactive scene directories are deleted after expiration period
  - Autosave is active from application start

- **Zoom Settings** Configure zoom level limits including:
  - Set minimum zoom level (default: -10)
  - Set maximum zoom level (default: +12)
  - Limits prevent crashes when inserting StringMediaObjects at extreme zoom levels
  - If minimum is set greater than maximum, values are automatically swapped
  - Default limits (-10 to +12) ensure font sizes remain ≥1 point for StringMediaObjects

Actions menu:
~~~~~~~~~~~~~

- **Copy SVG (Ctrl+C)** Copy the currently selected SVG object to the
  clipboard
- **Paste SVG (Ctrl+V)** Paste the copied SVG at the current mouse
  position (or center of the viewport)

Help menu:
~~~~~~~~~~

- **About** Show PyZUI copyright information
- **About Qt** Show Qt about dialog

Mouse/Keyboard actions:
-----------------------

- **Left-click** Select the topmost media under the cursor (by default,
  smaller objects appear on top of larger ones; this can be toggled via
  **View → Render Order: Smaller on Top**):

    - if there is no media under the cursor then the currently selected media
      will be deselected
    - if the Shift key is currently being held then no change will be made
      to the current selection

- **Shift+Left-click** Add an object to the current multi-selection without
  deselecting previously selected objects. Clicking a selected object again
  with Shift held allows dragging all selected objects together.

- **Right-click** Open a context dialog for the media object under the cursor:
    - **StringMediaObject**: Opens the Modify String dialog allowing you to edit
      the text content and change the color of the string
    - **TiledMediaObject**: Opens the Tiled Media Object Options dialog with
      image manipulation tools:

      - Rotate Left/Right: Rotate the image by 90° increments
      - Invert Colors: Apply color inversion effect
      - Black and White: Convert the image to grayscale

      Changes are previewed in the dialog and applied when clicking Apply.

    - **SVGMediaObject**: Opens the Modify SVG dialog allowing you to edit
      the SVG source or change to a different SVG shape

- **Click`n'drag** Select and move the topmost media under the cursor
    - by default smaller objects are rendered above larger ones and will be
      selected first; this can be toggled via the View menu
    - if there is no media under the cursor then the currently selected media
      will be deselected and the entire scene will be moved
    - if the Shift key is currently being held then no change will be made
      to the current selection and the entire scene will be moved

- **Control+Left-click drag** Draw a selection rectangle to select multiple media objects:
    - Hold the Control key
    - Click and drag with left mouse button to draw a green rectangle
    - Release to select all objects within the rectangle
    - Visual feedback: A green rectangle is drawn during the drag operation
    - Multiple selection: All selected objects are highlighted with green borders
    - Moving multiple objects: After rectangle selection, drag any selected object to move all selected objects together
    - Clicking between selected objects maintains the selection for dragging

- **Esc** Deselect the currently selected media

- **PgUp/PgDn or Scrollwheel** Zoom the currently selected media
    - if there is no currently selected media, or if the Shift key is currently
      being held, then the entire scene will be zoomed
    - if the Alt key is currently being held, then the zoom amount will
      reduced allowing for finer control
    - Note: the point under the cursor will maintain its position on the
      screen

- **Arrow keys** Move the currently selected media in the specified direction
    - if there is no currently selected media, or if the Shift key is currently
      being held, then the entire scene will be moved
    - if the Alt key is currently being held, then the move amount will
      reduced allowing for finer control

- **Space bar** Move the point under the cursor to the centre of the screen
    - holding the Space bar allows panning by moving the cursor around
      the centre of the viewport

- **Del** Delete the currently selected media

- **Ctrl+C** Copy the currently selected SVG object to the clipboard

- **Ctrl+V** Paste the clipboard content as an SVG object at the current
  mouse position (or center of the viewport)

- **Scrollwheel + modifiers on an SVG shape** Elongate (resize) the selected
  SVG object. Only works when a single SVG object is selected:

    - **Ctrl + Scrollwheel** on squares/circles/triangles: proportional
      scaling (both axes equally); on arrows/sticks: elongate length
    - **Shift + Scrollwheel** on squares/circles/triangles: scale X-axis only
    - **Ctrl+Shift + Scrollwheel** on squares/circles/triangles: scale Y-axis
      only

