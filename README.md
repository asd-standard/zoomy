# Welcome to PyZUI Documentation!

---

PyZUI is an implementation of a Zooming User Interface (ZUI) for Python.
Media is laid out upon an infinite virtual desktop, with the user able to
pan and zoom through the collection.

---

Full documentation available at [asd-standard.github.io/zoomy](https://asd-standard.github.io/zoomy/)

---

This project is a fork of [github.com/davidar/pyzui](https://github.com/davidar/pyzui),
original work from which it derives its architecture and features.

## PyZUI is compatible with the following media formats:

- All images recognized by VIPS
- PDF documents
- SVG (vector graphics)

---

This project is covered under the GNU General Public License v3.0, a copy must
be under COPYING.txt on project root, otherwise visit [gnu.org](https://www.gnu.org/licenses/gpl-3.0.html)

---

> **Note:** This documentation covers setup, usage, technical/development documentation,
> testing/benchmarking documentation and contribution guidelines for PyZUI.

---

# PyZui installation instructions

This PyZUI fork was developed with debian 13 "trixie" as d.e and a miniconda for
dependencies management. It has also been tested on AArch64 and Win11, always
with a miniconda environment managing all dependencies.

This project is a fork, original project can be found at:
https://github.com/davidar/pyzui

## Dependencies

PyZui has been developed with the following python version

- python=3.12.12

All dependencies have been installed in a miniconda environment, for all 3
platforms tested the procedure has always been to install miniconda, create an
environment:

```bash
conda create -n "envirnoment name" python=3.12.12
```

And activate such envirnoment

```bash
conda activate "environment name"
```

with all the core dependencies installed trough the default Anaconda channel:

```bash
conda install "package"="version number"
```

PyZUI depends on the following Python packages:

- pyside6=6.7.2
- pillow=12.0.0

The following non-Python packages are also required by certain features of the
application, those are installed trough the Conda-Forge Anaconda channel.
Especially if you run linux those packages may already be present on your system
and may work, it's nevertheless highly recomended to install them in the conda
environment:

```bash
conda install -c conda-forge "package"="version number"
```

- pyvips=3.0.0

  Poppler usually gets installed with pyvips so it's not necessary to
  install it's anyway an explicit codebase dependency for pdf management.

- poppler=24.12.0

pdftoppm from Poppler or Xpdf (optional if you do not intend viewing PDFs);

These are the bare minimum dependencies for the project to run, on linux DE's
using Wayland as display server you can also install:

- qt6-wayland-6.7.2

  This allow the project to run natively and take advantage of hardware acceleration

### Ubuntu/Debian, AArch64, specific instructions

- Install miniconda and follow the instructions in the DEPENDENCIES section

## Running PyZUI

- PyZUI can be run by activating the environment as explained in the DEPENDENCIES
  section:

```bash
conda activate "environment name"
```

- Then executing 'main.py' with python interpreter:

```bash
python main.py
```

- It is not necessary to run this from the command-line (unless you want to view
  the logging), and it can be run from any directory (the script will set the
  working directory appropriately by itself).

### Windows specific instructions

- You have to install Windows subsystem for linux, (wsl), the default linux
  distribution should work, nevertheless if you want to be 100% sure the PyZui
  have been tested with ubuntu 24.04.

- Once you have wsl installed you need to install miniconda on it, then you can
  create an environment and install all the dependencies as explained in the
  DEPENDENCIES section.

### Running PyZui (Windows)

- You can then run PyZui by launching your wsl environment, navigate to the root
  of the pyzui project and run:

```bash
python main.py
```

## Generating Documentation

- Install sphinx on the conda environment you have created for the PyZui project.

```bash
conda activate "environment name"
conda install sphinx
```

- Once installed sphinx on the PyZui project environment go to the project root
  and then:

```bash
./docs
```

 and run:

```bash
make clean
make html
```

- this will generate all the documentation adding changes to the project docstring
  you might have added. You can visualize documentation by opening

```
./docs/build/html/index.html
```

with any web browser


### Building documentation

- Be aware, building documentation cause certain s docs project configuration
  files to be wiped, if you just wish to update documentation go to GENERATING
  DOCUMENTATION
- Install sphinx on the conda environment you have created for the PyZui project.

```bash
conda activate "environment name"
conda install sphinx
```

- Once installed sphinx on the PyZui project environment go to "project root"/docs
  and run:

```bash
sphinx-quickstart
```

- This will guide you through a few prompts:

  - Project name: your project's name
  - Author name: your name or org
  - Project release: version
  - Separate source and build dirs: usually Yes

- This creates a structure like:

```
docs/
|__ build/
|__ source/
|   |__ conf.py
|   |__ index.rst
|   |__ _static/
|__ Makefile
```

- Then navigate to ./docs and run

```bash
sphinx-apidoc -e -o source/ ..
sphinx-apidoc -e -o source/ ../pyzui
```

- Then open ./docs/source/conf.py and add

```python
import os
import sys
sys.path.insert(0, os.path.abspath('../..'))
sys.path.insert(0, os.path.abspath('..'))
```

- insert there all the sphinx stilings and then run:

```bash
make clean
make html
```

- this will generate all'the documentation adding changes to the project docstring
  you might have added. You can visualize documentation by opening ./docs/build/html/index.html with any web browser
