# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
sys.path.insert(0, os.path.abspath('../..'))
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'PyZui'
copyright = '2025, David Roberts, Andrea Silvestri'
author = 'David Roberts, Andrea Silvestri'
release = '0.11'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',        # automatically document Python docstrings
    'sphinx.ext.autosummary',    # create summary tables
    'sphinx.ext.napoleon',       # support for Google/NumPy-style docstrings
    'sphinx.ext.viewcode',       # add links to highlighted source code
] 

templates_path = ['_templates']
exclude_patterns = []

# Automatically generate autosummary pages
autosummary_generate = True


# -- Options for autodoc -----------------------------------------------------

autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
autoclass_content = 'both'


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
