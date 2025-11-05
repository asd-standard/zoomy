.. PyZui user instruction file,

User interface
==============

Upon startup of PyZUI, the user is presented with the home scene:

.. image:: _static/home_scene.png
   :align: center
   :width: 500px
   :alt: PyZUI logo

The menus provide the following actions:
----------------------------------------

File menu:
~~~~~~~~~~

- **New Scene (Ctrl+N)** Create a blank scene
- **Open Scene (Ctrl+O)**  Open a saved scene
- **Open Home Scene (Ctrl+Home)** Return to the *home scene*
- **Save Scene (Ctrl+S)** Save the current scene
- **Save Screenshot (Ctrl+H)** Export the current viewport to an
  image
- **Open Local Media (Ctrl+L)** Open media from a local file
- **Open new string (Ctrl+U)** Opens an input window that 
  allows you to insert text strings to be rendered on the 
  interface. Newlines are considered making possible to write 
  paragraphs
- **Open Media Directory (Ctrl+D)** Open the media contained in
  a directory, and arrange it into a grid
- **Quit (Ctrl+Q)** Exit the application

View menu:
~~~~~~~~~~

- **Set Framerate** Set the rendering framerate to the selected
  frequency
- **Adjust Sensitivity** Set the movement/zoom sensitivity 
- **Fullscreen (Ctrl+F)** Toggle fullscreen mode

Help menu:
~~~~~~~~~~

- **About** Show PyZUI copyright information
- **About Qt** Show Qt about dialog

Mouse/Keyboard actions:
-----------------------

- **Left-click** Select the foremost media under the cursor:
  	- if there is no media under the cursor then the currently selected media
  	  will be deselected
  	- if the Shift key is currently being held then no change will be made
  	  to the current selection

- **Click`n'drag** Select and move the foremost media under the cursor
    - if there is no media under the cursor then the currently selected media
      will be deselected and the entire scene will be moved
    - if the Shift key is currently being held then no change will be made
      to the current selection and the entire scene will be moved

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

