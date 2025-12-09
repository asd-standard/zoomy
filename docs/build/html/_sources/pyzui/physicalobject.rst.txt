pyzui.objects.physicalobject module
====================================

Class Inheritance Hierarchy::

   PhysicalObject (Abstract Base)
   │   • _x, _y, _z (position & zoom)
   │   • vx, vy, vz (velocity)
   │   • damping factor
   │   • _centre (center point)
   │
   ├── MediaObject (Abstract)
   │   │   • Coordinate transforms
   │   │   • Scaling management
   │   │   • Reference frames
   │   │
   │   ├── TiledMediaObject
   │   │       • Large image support
   │   │       • Tile grid management
   │   │       • Efficient for huge images
   │   │
   │   ├── StringMediaObject
   │   │       • Text rendering
   │   │       • Font support
   │   │
   │   └── SVGMediaObject
   │           • Vector graphics
   │           • Scalable rendering
   │
   └── Scene
           • Container for MediaObjects
           • Viewport management
           • Scene persistence
           • Thread-safe operations

.. automodule:: pyzui.objects.physicalobject
   :members:
   :show-inheritance:
   :undoc-members:

