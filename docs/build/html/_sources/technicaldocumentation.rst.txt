.. PyZui project structure file,

Reading Guide
=============

Each class or method, (private or pubblic), has it's docstring, 
all'docstring starts with such form:

Constructor:
    Class['var1', 'var2', ...]

How the method is called or the class is initialized properly.

'var1', 'var2', ... are the class/method internal variable 
names on wich the input parameters are passed on.

Parameters :
    var1['type(var1)'], var2['type(var2)'], ...

type(var1), type(var2) are variables types. In order to 
correctly call or initialize the method or class types 
have to match 

    Class('var1', 'var2', ...) --> type(Class('var1', 'var2', ...))

Type returned by a proper call of the method or class initialization.



Project structure
=================

- :doc:`physicalobject <pyzui.physicalobject>`
    - :doc:`mediaobject <pyzui.mediaobject>`
        - :doc:`tiledmediaobject <pyzui.tiledmediaobject>`
        - :doc:`stringmediaobject <pyzui.stringmediaobject>`
        - :doc:`svgmediaobject <pyzui.svgmediaobject>`
    - :doc:`scene <pyzui.scene>`
        - :doc:`qzui <pyzui.qzui>`
        - :doc:`main window <pyzui.mainwindow>`
            - :doc:`main <main>`
- :doc:`converter <pyzui.converter>`
    - :doc:`magickconverter <pyzui.magickconverter>`
    - :doc:`pdfconverter <pyzui.pdfconverter>`
    - :doc:`webkitconverter <pyzui.webkitconverter>`
- :doc:`ppm <pyzui.ppm>`

- :doc:`tilestore <pyzui.tilestore>`
- :doc:`tilecache <pyzui.tilecache>`

- :doc:`tile <pyzui.tile>`
    - :doc:`tilemanager <pyzui.tilemanager>`
    - :doc:`tiler <pyzui.tiler>`
    - :doc:`tileprovider <pyzui.tileprovider>`
        - :doc:`statictileprovider <pyzui.statictileprovider>`
        - :doc:`dynamictileprovider <pyzui.dynamictileprovider>`
            - :doc:`osmtileprovider <pyzui.osmtileprovider>`
            - :doc:`globalmosaictileprovider <pyzui.globalmosaictileprovider>`
            - :doc:`mandeltileprovider <pyzui.mandeltileprovider>`
            - :doc:`ferntileprovider <pyzui.ferntileprovider>`

