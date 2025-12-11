PyZui installation instructions
===============================

This PyZUI fork was developed with debian 13 "trixie" as d.e and a miniconda for 
dependencies management. It has also been tested on AArch64 and Win11, always 
with a miniconda enviroment managing all dependencies.

original project can be found at:
https://github.com/davidar/pyzui

Dependencies
============

PyZui has been developed with the following python version

- python = 3.12.12

All dependencies have been installed in a miniconda enviroment, for all 3 
platforms tested the procedure has always been to install miniconda, create an 
enviroment:

  conda create -n "enviroment name" python = 3.12.12
  
And activate such enviroment

  conda activate "enviroment name"

with all the core dependencies installed trough the default Anaconda channel:

  conda install "package"="version number"

PyZUI depends on the following Python packages:

- pyside6 = 6.7.2 
- pillow= 11.0.3
- pyvips = 2.2.3

The following non-Python packages are also required by certain features of the
application, those are installed trough the Conda-Forge Anaconda channel. 
Especially if you run linux those packages may already be present on your system 
and may work, it's nevertheless highly reccomended to install them in the conda 
enviroment:

  conda install -c conda-forge "package"="version number"

- poppler=24.09.0
  pdftoppm from Poppler or Xpdf (optional if you do not intend viewing PDFs);

After completion of this dependencies set up you can install  

Ubuntu/Debian, AArch64, specific instructions
---------------------------------------------

- Install miniconda and follow the instructions in the DEPENDENCIES section

Running PyZUI
=============

- PyZUI can be run by activating the enviroment as explained in the DEPENDENCIES 
  section:

  conda activate "enviroment name"

- Then executing 'main.py' with python interpreter:

  python main.py
 
- It is not necessary to run this from the command-line (unless you want to view
  the logging), and it can be run from any directory (the script will set the 
  working directory appropriately by itself).

Windows specific instructions
-----------------------------

- You have to install Windows subsystem for linux, (wsl), the default linux 
  distribution should work, nevertheless if you want to be 100% sure th PyZui 
  have been tested with ubuntu 24.04.

- Once you have wsl installed you need to install miniconda on it, then you can 
  create an enviroment and install all the dependencies as explained in the 
  DEPENDENCIES section.  

Running PyZui (Windows)
-----------------------

- You can then run PyZui by launching your wsl enviroment, navigate to the root 
  of the pyzui project and run:

  python main.py 

Generating Documentation
========================

- Install sphinx on the conda enviroment you have created for the PyZui project.

 conda activate "enviroment name"
 conda install sphinx

- Once installed sphinx on the PyZui project enviroment go to the project root 
  and then: 
  
 ./docs
  
 and run:

 make clean
 make html

- this will generate all the documentation adding changes to the project docstring
  you might have added. You can visualize documentation by opening 

 ./docs/build/html/index.html with any web browser 


Building documentation
----------------------

- Be aware, building documentation cause certains docs project configuration 
  files to be wiped, if you just wish to update documentation go to GENERATING 
  DOCUMENTATION  
- Install sphinx on the conda enviroment you have created for the PyZui project.

 conda activate "enviroment name"
 conda install sphinx

- Once installed sphinx on the PyZui project enviroment go to "project root"/docs
  and run:

 sphinx-quickstart

- This will guide you through a few prompts:

  Project name: your project’s name
  Author name: your name or org
  Project release: version
  Separate source and build dirs: usually Yes

- This creates a structure like::

    docs/
    |__ build/
    |__ source/
    |   |__ conf.py
    |   |__ index.rst
    |   |__ _static/
    |__ Makefile

- Then navigate to ./docs and run

  sphinx-apidoc -e -o source/ ..
  sphinx-apidoc -e -o source/ ../pyzui

- Then open ./docs/source/conf.py and add
  
  import os
  import sys
  sys.path.insert(0, os.path.abspath('../..'))
  sys.path.insert(0, os.path.abspath('..'))

- insert there all'the sphinx stilings and then run:

  make clean
  make html

- this will generate all'the documentation adding changes to the project docstring
  you might have added. You can visualize documentation by opening ./docs/build/html/index.html with any web browser