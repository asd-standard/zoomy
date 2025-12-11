.. PyZui documentation master file, created by
   sphinx-quickstart on Wed Oct 22 11:05:35 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to PyZUI Documentation!
===============================

.. image:: ../../data/home.png
   :align: right
   :width: 540px
   :alt: PyZUI logo

---

PyZUI is an implementation of a Zooming User Interface (ZUI) for Python.
Media is laid out upon an infnite virtual desktop, with the user able to 
pan and zoom through the collection.

---

This project is a fork of `github.com/davidar/pyzui <https://github.com/davidar/pyzui>`_, 
original work from which it derives its initial architecture and features.

PyZUI is compatible with the following media formats:
-----------------------------------------------------
- All images recognised by VIPS
- PDF documents
- SVG (vector graphics)

---

This project is covered under the GNU General Public License v3.0, a copy must
be under LICENCE on project root, otherwise visit `gnu.org <https://www.gnu.org/licenses/gpl-3.0.html>`_

---

.. note::
   This documentation covers setup, usage, technical/development documentation,
   testing/benchmarking documentation and contribution guidelines for PyZUI.

---

.. toctree::
   :maxdepth: 2
   :titlesonly:
   :caption: Getting Started

   gettingstarted/installation

.. toctree::
   :maxdepth: 2
   :titlesonly:
   :caption: Usage Instructions

   usageinstructions/userinterface
   usageinstructions/programconfiguration

.. toctree::
   :maxdepth: 2
   :titlesonly:
   :caption: Technical Documentation

   technicaldocumentation/readingdocumentation
   technicaldocumentation/projectstructure
   technicaldocumentation/objectsystem
   technicaldocumentation/convertersystem
   technicaldocumentation/tiledmediaobject
   technicaldocumentation/tilingsystem
   technicaldocumentation/windowsystem
   technicaldocumentation/logging

.. toctree::
   :maxdepth: 2
   :titlesonly:
   :caption: Testing Documentation

   testingdocumentation/unittest
   testingdocumentation/integrationtest

.. toctree::
   :maxdepth: 2
   :titlesonly:
   :caption: Benchmarks Documentation

   benchmarksdocumentation/qzuibenchmark
   benchmarksdocumentation/converterbenchmark
   
.. toctree::
   :maxdepth: 2
   :titlesonly:
   :caption: Contribution Guidelines

   contributionguidelines/contributiongiudelines



