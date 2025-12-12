## PyZUI - Python Zooming User Interface
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 3
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, see <https://www.gnu.org/licenses/>.

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
    'sphinx.ext.autodoc',           # automatically document Python docstrings
    'sphinx.ext.autosummary',       # create summary tables
    'sphinx.ext.napoleon',          # support for Google/NumPy-style docstrings
    'sphinx.ext.viewcode',          # add links to highlighted source code
] 

templates_path = ['_templates']
exclude_patterns = []

# Automatically generate autosummary pages
autosummary_generate = True

# -- Options for autodoc -----------------------------------------------------

autodoc_default_options = {
    'members': True,
    'private-members': True,   # include names starting with _ or __
}
autodoc_member_order = 'bysource'
autodoc_typehints = 'none'  # Don't auto-generate type hint documentation
autoclass_content = 'both'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
html_css_files = ['custom.css']
