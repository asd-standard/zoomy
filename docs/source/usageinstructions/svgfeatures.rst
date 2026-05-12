.. PyZUI SVG Features Documentation

SVG Features
============

PyZUI provides comprehensive support for Scalable Vector Graphics (SVG) files,
allowing users to add, modify, and manipulate vector graphics within the
zooming user interface. This document covers all SVG-related features available
in PyZUI.

Overview
--------

SVG (Scalable Vector Graphics) is an XML-based vector image format that
supports interactivity and animation. In PyZUI, SVG files can be:

- Added to scenes as media objects
- Modified with custom colors and line thickness
- Embedded in scene files for portability
- Rendered at any zoom level without quality loss

Key Features
------------

1. **SVG Picker Dialog**: Browse and select SVG files from the ``data/SVG/`` directory
2. **Color Customization**: Apply any color to SVG strokes and fills
3. **Thickness Adjustment**: Modify line/stroke thickness
4. **Modification Dialog**: Edit existing SVG objects in the scene
5. **SVG Cache**: Efficient storage of modified SVG files
6. **Embedding Support**: Modified SVGs embedded in scene files

Adding SVG Objects
------------------

There are two main ways to add SVG objects to your PyZUI scene:

**Method 1: Using the SVG Picker Dialog**

1. Open the SVG picker dialog from the main menu or toolbar
2. Browse available SVG files in the ``data/SVG/`` directory
3. Select an SVG file to preview it
4. Choose a color from the color history or enter a custom hex color
5. Adjust the stroke thickness if needed
6. Click "Apply Changes" to preview modifications
7. Click "OK" to add the modified SVG to your scene

**Method 2: Direct File Import**

SVG files can also be added directly by:
- Dragging and dropping SVG files into the PyZUI window
- Using the "Add Media" dialog to select SVG files
- Loading scene files that contain embedded SVG objects

SVG Picker Dialog
-----------------

The SVG Picker Dialog (``OpenSVGPickerInputDialog``) provides an intuitive
interface for selecting and customizing SVG files:

.. image:: ../images/svg_picker_dialog.png
   :alt: SVG Picker Dialog Interface
   :width: 80%
   :align: center

**Interface Components:**

1. **SVG Preview Grid**: Thumbnail previews of all available SVG files
2. **Color History**: Recently used colors for quick selection
3. **Custom Color Input**: Enter any hex color (with or without #)
4. **Thickness Input**: Adjust stroke width (default: 50)
5. **Apply Changes Button**: Preview modifications before adding
6. **OK/Cancel Buttons**: Add to scene or cancel operation

**Available SVG Files:**

PyZUI includes a collection of basic shapes in the ``data/SVG/`` directory:

- Arrows (various directions)
- Geometric shapes (circles, squares, triangles)
- Basic icons and symbols
- Custom shapes (add your own SVG files)

Modifying Existing SVG Objects
------------------------------

Existing SVG objects in your scene can be modified using the
Modify SVG Dialog (``ModifySVGInputDialog``):

**To modify an existing SVG object:**

1. Select the SVG object in your scene
2. Right-click and choose "Modify SVG" from the context menu
3. Or use the "Modify" option from the object properties panel

**Modify Dialog Features:**

.. image:: ../images/svg_modify_dialog.png
   :alt: SVG Modify Dialog Interface
   :width: 60%
   :align: center

1. **SVG Preview**: Live preview of the SVG with current modifications
2. **Color Selection**: Choose from color history or enter custom color
3. **Thickness Adjustment**: Modify stroke width
4. **Apply Preview Button**: See changes before applying
5. **Reset Button**: Revert to original SVG appearance
6. **OK/Cancel**: Apply changes or cancel

**Note**: The modify dialog is designed for simple shapes (arrows, circles,
squares, triangles) added via the SVG picker dialog. For complex SVG files
added from other sources, default values (black color, stroke-width=10) will
be used with a warning message.

Color Management
----------------

PyZUI maintains a color history system that persists across sessions:

**Color History Features:**

- Stores up to 24 recently used colors
- Colors saved in ``~/.pyzui/colorstore/color_list.txt``
- Colors shared between SVG picker and modify dialogs
- Default colors: white (ffffff), red (ff0000), green (00ff00), blue (0000ff)

**Custom Color Input:**

- Enter hex colors with or without # prefix (e.g., ``ff5733`` or ``#ff5733``)
- Color names are supported (e.g., ``red``, ``blue``, ``green``)
- Invalid colors default to black (000000)

SVG Cache System
----------------

PyZUI uses an efficient SVG cache system to store modified SVG files:

**Cache Features:**

- **Location**: ``/tmp/pyzui_svg_/`` directory (temporary storage)
- **Format**: ``svg_{8_char_sha1_hash}.svg`` files
- **Deduplication**: Same content = same hash (saves storage)
- **Flat Structure**: All files in single directory (no subfolders)

**How it works:**

1. When you modify an SVG (color/thickness), PyZUI creates a modified version
2. The modified content is hashed (SHA1, first 8 chars)
3. File is saved as ``svg_{hash}.svg`` in cache directory
4. SVG objects reference the cache hash instead of original file
5. Cache files are automatically cleaned up on system restart

**Benefits:**

- Fast retrieval of modified SVGs
- No duplication of identical modified files
- Efficient storage for frequently used modifications
- Enables SVG embedding in scene files

SVG Embedding in Scene Files
----------------------------

Modified SVG objects can be embedded directly in PyZUI scene (``.pzs``) files:

**Embedding Behavior:**

- **Modified SVGs**: Embedded as XML content with ``embedded:`` prefix
- **Unmodified SVGs**: Keep file references (not embedded)
- **Large SVGs**: Warning shown for files >1MB (configurable)

**Embedding Example:**

.. code-block:: json

    {
        "objects": [
            {
                "type": "SVGMediaObject",
                "media_id": "embedded:<?xml version=\"1.0\"?><svg>...</svg>",
                "position": [100, 200, 0],
                "is_modified": true,
                "original_file_path": "/path/to/original.svg"
            }
        ]
    }

**Benefits of Embedding:**

1. **Portability**: Scene files can be shared without external SVG files
2. **Version Control**: All modifications stored in single file
3. **Backup Safety**: No risk of losing modified SVG files
4. **Collaboration**: Easy sharing of complete scenes

SVG Utilities
-------------

PyZUI includes specialized utilities for working with SVG files:

**Arrow Utilities (``svgarrowutils.py``):**

- Detect arrow shapes in SVG files
- Elongate arrows while maintaining proportions
- Handle arrowhead positioning and scaling

**Shape Utilities:**

- ``svgcircleutils.py``: Circle manipulation utilities
- ``svgsquareutils.py``: Square/rectangle utilities  
- ``svgtriangleutils.py``: Triangle manipulation utilities

**Common Use Cases:**

1. **Diagram Creation**: Add arrows between objects
2. **Annotation**: Use shapes to highlight areas
3. **Flow Charts**: Create visual workflows with connected shapes
4. **Technical Drawing**: Add precise geometric shapes

Best Practices
--------------

**For Optimal SVG Performance:**

1. **Use Simple Shapes**: Complex SVGs with many paths render slower
2. **Limit Embedding**: Only embed modified SVGs, keep unmodified as file references
3. **Reuse Colors**: Use color history for consistency across objects
4. **Batch Modifications**: Make all changes in one dialog session

**For Scene Portability:**

1. **Embed Modified SVGs**: Ensures scenes work on other systems
2. **Keep Originals**: Maintain original SVG files for future modifications
3. **Document Colors**: Note down custom color codes used in complex scenes
4. **Test Loading**: Verify scenes load correctly after embedding

**Troubleshooting:**

- **SVG Not Rendering**: Check if file is valid XML, try opening in browser
- **Colors Not Applying**: Some SVGs use CSS classes instead of inline attributes
- **Performance Issues**: Reduce number of SVG objects or simplify complex SVGs
- **Cache Issues**: Clear ``/tmp/pyzui_svg_/`` directory and restart PyZUI

Advanced Usage
--------------

**Programmatic SVG Addition:**

SVG objects can be added programmatically:

.. code-block:: python

    from pyzui.objects.scene.scene import Scene
    from pyzui.objects.mediaobjects.svgmediaobject import SVGMediaObject
    
    # Create scene
    scene = Scene()
    
    # Add SVG from file
    svg_from_file = SVGMediaObject("path/to/shape.svg", scene)
    svg_from_file.pos = (100, 200)
    scene.add(svg_from_file)
    
    # Add SVG from cache hash
    svg_from_cache = SVGMediaObject("svg_abc12345", scene)
    svg_from_cache.pos = (300, 400)
    scene.add(svg_from_cache)

**Custom SVG Directory:**

To use your own SVG files:

1. Create a ``data/SVG/`` directory in your PyZUI installation
2. Add ``.svg`` files to this directory
3. Restart PyZUI to see new files in the picker dialog

**SVG Cache Management:**

Advanced users can manage the SVG cache:

.. code-block:: bash

    # List cached SVG files
    ls /tmp/pyzui_svg_/
    
    # Clear cache (will be recreated as needed)
    rm -rf /tmp/pyzui_svg_/
    
    # Monitor cache size
    du -sh /tmp/pyzui_svg_/

Examples
--------

**Example 1: Creating a Simple Diagram**

1. Add a circle SVG, color it blue, thickness 10
2. Add a square SVG, color it red, thickness 15  
3. Add an arrow SVG between them, color it black, thickness 8
4. Position objects to create a flow diagram

**Example 2: Annotation Workflow**

1. Load an image into PyZUI
2. Add triangle SVGs to highlight important areas
3. Color triangles yellow with transparency
4. Add text labels near triangles
5. Save scene with embedded SVG annotations

**Example 3: Technical Drawing**

1. Create grid background
2. Add precise geometric shapes (circles, squares, triangles)
3. Use consistent colors for different element types
4. Add dimension lines using arrow SVGs
5. Export as high-resolution image

Limitations
-----------

1. **Complex SVGs**: Very complex SVGs with gradients, filters, or animations
   may not render correctly
2. **CSS Styling**: External CSS stylesheets in SVG files are not supported
3. **JavaScript**: SVG files with embedded JavaScript will not execute
4. **External References**: Images or fonts referenced in SVG may not load
5. **File Size**: Very large SVG files (>5MB) may cause performance issues

Future Enhancements
-------------------

Planned improvements for SVG support:

1. **SVG Library**: Expanded collection of pre-made SVG shapes
2. **Layer Support**: SVG objects with multiple editable layers
3. **Group Operations**: Modify multiple SVG objects simultaneously
4. **Export Options**: Export SVG objects as standalone files
5. **Template System**: Save and reuse SVG modification templates

See Also
--------

- :doc:`../pyzui/svgmediaobject` - SVGMediaObject API documentation
- :doc:`../pyzui/svgpickerinputdialog` - SVG Picker Dialog API
- :doc:`../pyzui/modifysvginputdialog` - Modify SVG Dialog API
- :doc:`../technicaldocumentation/objectsystem` - Object system overview
