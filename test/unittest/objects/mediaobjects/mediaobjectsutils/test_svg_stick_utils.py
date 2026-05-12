## PyZUI - Python Zooming User Interface
## Copyright (C) 2009 David Roberts <d@vidr.cc>
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

"""
Feature: SVG Stick (Line) Elongation Utilities

The SVG stick utilities provide detection and elongation functions
for simple line SVG elements (sticks), enabling interactive scaling
with keyboard modifiers (Ctrl).
"""

import os
import shutil
import tempfile

import pytest

from pyzui.objects.mediaobjects.mediaobjectsutils import (
    elongate_diagonal_stick,
    elongate_stick,
    get_diagonal_stick_direction,
    get_stick_direction,
    is_diagonal_stick_svg,
    is_stick_svg,
)


class TestSVGStickUtils:
    """
    Feature: Stick Detection and Elongation

    The stick utilities detect simple line SVG elements and provide
    elongation functionality with Ctrl modifier support.
    """

    def setup_method(self):
        """Create test directory and sample SVG files."""
        self.test_dir = tempfile.mkdtemp(prefix="pyzui_test_")
        self.horizontal_stick_svg = os.path.join(self.test_dir, "horizontal_stick.svg")
        self.vertical_stick_svg = os.path.join(self.test_dir, "vertical_stick.svg")
        self.diagonal_stick_svg = os.path.join(self.test_dir, "diagonal_stick.svg")
        self.non_45_diagonal_svg = os.path.join(self.test_dir, "non_45_diagonal.svg")
        self.arrow_svg = os.path.join(self.test_dir, "arrow.svg")
        self.non_stick_svg = os.path.join(self.test_dir, "not_stick.svg")

        # Create a horizontal stick SVG (similar to provided example)
        horizontal_content = """<?xml version='1.0' encoding='utf-8'?>
<ns0:svg xmlns:ns0="http://www.w3.org/2000/svg" width="265.0" height="100" viewBox="10.0 20.0 245.0 60.0">
    <ns0:line x1="20" y1="50" x2="215.0" y2="50.0" stroke="black" stroke-width="8" stroke-linecap="round" />
</ns0:svg>"""

        # Create a vertical stick SVG (similar to provided example)
        vertical_content = """<?xml version='1.0' encoding='utf-8'?>
<ns0:svg xmlns:ns0="http://www.w3.org/2000/svg" width="100" height="265.0" viewBox="20.0 10.0 60.0 245.0">
    <ns0:line x1="50" y1="245.0" x2="50.0" y2="50.0" stroke="black" stroke-width="8" stroke-linecap="round" />
</ns0:svg>"""

        # Create a 45° diagonal stick SVG
        diagonal_content = """<?xml version='1.0' encoding='utf-8'?>
<ns0:svg xmlns:ns0="http://www.w3.org/2000/svg" width="135" height="135" viewBox="35 30 135 135">
    <ns0:line x1="160" y1="40" x2="57" y2="143" stroke="black" stroke-width="8" stroke-linecap="round" />
</ns0:svg>"""

        # Create a non-45° diagonal line (should not be detected as diagonal stick)
        non_45_diagonal_content = """<?xml version='1.0' encoding='utf-8'?>
<ns0:svg xmlns:ns0="http://www.w3.org/2000/svg" width="200" height="100" viewBox="0 0 200 100">
    <ns0:line x1="20" y1="20" x2="180" y2="80" stroke="black" stroke-width="8" stroke-linecap="round" />
</ns0:svg>"""

        # Create an arrow SVG (should not be detected as stick)
        arrow_content = """<?xml version='1.0' encoding='utf-8'?>
<ns0:svg xmlns:ns0="http://www.w3.org/2000/svg" width="265.0" height="100" viewBox="10.0 20.0 245.0 60.0">
    <ns0:line x1="245.0" y1="50" x2="50.0" y2="50.0" stroke="black" stroke-width="8" stroke-linecap="round" />
    <ns0:polygon points="50.0,30.0 20.0,50.0 50.0,70.0" fill="black" />
</ns0:svg>"""

        # Create a non-stick SVG (circle)
        non_stick_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <circle cx="100" cy="100" r="50" fill="red"/>
</svg>"""

        with open(self.horizontal_stick_svg, 'w') as f:
            f.write(horizontal_content)

        with open(self.vertical_stick_svg, 'w') as f:
            f.write(vertical_content)

        with open(self.diagonal_stick_svg, 'w') as f:
            f.write(diagonal_content)

        with open(self.non_45_diagonal_svg, 'w') as f:
            f.write(non_45_diagonal_content)

        with open(self.arrow_svg, 'w') as f:
            f.write(arrow_content)

        with open(self.non_stick_svg, 'w') as f:
            f.write(non_stick_content)

    def teardown_method(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def test_is_stick_svg_detects_horizontal_stick(self):
        """
        Scenario: Detect horizontal stick SVG

        Given an SVG file containing a single horizontal line element
        When is_stick_svg is called
        Then it should return True
        """
        assert is_stick_svg(self.horizontal_stick_svg) is True

    def test_is_stick_svg_detects_vertical_stick(self):
        """
        Scenario: Detect vertical stick SVG

        Given an SVG file containing a single vertical line element
        When is_stick_svg is called
        Then it should return True
        """
        assert is_stick_svg(self.vertical_stick_svg) is True

    def test_is_stick_svg_detects_diagonal_stick(self):
        """
        Scenario: Detect diagonal stick SVG

        Given an SVG file containing a single 45° diagonal line element
        When is_stick_svg is called
        Then it should return True
        """
        assert is_stick_svg(self.diagonal_stick_svg) is True

    def test_is_diagonal_stick_svg_detects_45_degree(self):
        """
        Scenario: Detect 45° diagonal stick

        Given an SVG file with 45° diagonal line
        When is_diagonal_stick_svg is called
        Then it should return True
        """
        assert is_diagonal_stick_svg(self.diagonal_stick_svg) is True

    def test_is_diagonal_stick_svg_rejects_non_45_degree(self):
        """
        Scenario: Reject non-45° diagonal line

        Given an SVG file with non-45° diagonal line
        When is_diagonal_stick_svg is called
        Then it should return False
        """
        assert is_diagonal_stick_svg(self.non_45_diagonal_svg) is False

    def test_is_stick_svg_rejects_arrow_with_polygon(self):
        """
        Scenario: Reject arrow SVG (has polygon)

        Given an SVG file with line and polygon elements (arrow)
        When is_stick_svg is called
        Then it should return False
        """
        assert is_stick_svg(self.arrow_svg) is False

    def test_is_stick_svg_rejects_non_stick(self):
        """
        Scenario: Reject non-stick SVG

        Given an SVG file without line elements
        When is_stick_svg is called
        Then it should return False
        """
        assert is_stick_svg(self.non_stick_svg) is False

    def test_is_stick_svg_handles_nonexistent_file(self):
        """
        Scenario: Handle nonexistent file

        Given a path to a nonexistent file
        When is_stick_svg is called
        Then it should return False
        """
        nonexistent = os.path.join(self.test_dir, "nonexistent.svg")
        assert is_stick_svg(nonexistent) is False

    def test_get_stick_direction_horizontal(self):
        """
        Scenario: Get direction of horizontal stick

        Given a horizontal stick SVG
        When get_stick_direction is called
        Then it should return 'horizontal'
        """
        direction = get_stick_direction(self.horizontal_stick_svg)
        assert direction == 'horizontal'

    def test_get_stick_direction_vertical(self):
        """
        Scenario: Get direction of vertical stick

        Given a vertical stick SVG
        When get_stick_direction is called
        Then it should return 'vertical'
        """
        direction = get_stick_direction(self.vertical_stick_svg)
        assert direction == 'vertical'

    def test_get_stick_direction_diagonal(self):
        """
        Scenario: Get direction of diagonal stick

        Given a diagonal stick SVG
        When get_stick_direction is called
        Then it should return diagonal direction (e.g., 'downleft')
        """
        direction = get_stick_direction(self.diagonal_stick_svg)
        assert direction in ['upright', 'upleft', 'downright', 'downleft']

    def test_get_diagonal_stick_direction_specific(self):
        """
        Scenario: Get specific diagonal direction

        Given the test diagonal stick SVG (from 160,40 to 57,143)
        When get_diagonal_stick_direction is called
        Then it should return 'downleft'
        """
        direction = get_diagonal_stick_direction(self.diagonal_stick_svg)
        assert direction == 'downleft'

    def test_get_diagonal_stick_direction_returns_none_for_non_diagonal(self):
        """
        Scenario: Return None for non-diagonal stick

        Given a non-45° diagonal line
        When get_diagonal_stick_direction is called
        Then it should return None
        """
        direction = get_diagonal_stick_direction(self.non_45_diagonal_svg)
        assert direction is None

    def test_get_stick_direction_returns_none_for_non_stick(self):
        """
        Scenario: Return None for non-stick SVG

        Given a non-stick SVG file
        When get_stick_direction is called
        Then it should return None
        """
        direction = get_stick_direction(self.non_stick_svg)
        assert direction is None

    def test_elongate_stick_horizontal(self):
        """
        Scenario: Elongate horizontal stick

        Given a horizontal stick SVG
        When elongate_stick is called with scale factor 1.5
        Then it should return a valid cache hash
        """
        cache_hash = elongate_stick(self.horizontal_stick_svg, 1.5)
        assert cache_hash.startswith('svg_')
        assert len(cache_hash) == 12  # svg_ + 8 chars

    def test_elongate_stick_vertical(self):
        """
        Scenario: Elongate vertical stick

        Given a vertical stick SVG
        When elongate_stick is called with scale factor 1.5
        Then it should return a valid cache hash
        """
        cache_hash = elongate_stick(self.vertical_stick_svg, 1.5)
        assert cache_hash.startswith('svg_')
        assert len(cache_hash) == 12  # svg_ + 8 chars

    def test_elongate_stick_diagonal(self):
        """
        Scenario: Elongate diagonal stick

        Given a diagonal stick SVG
        When elongate_stick is called with scale factor 1.5
        Then it should return a valid cache hash
        """
        cache_hash = elongate_stick(self.diagonal_stick_svg, 1.5)
        assert cache_hash.startswith('svg_')
        assert len(cache_hash) == 12  # svg_ + 8 chars

    def test_elongate_diagonal_stick_specific(self):
        """
        Scenario: Elongate diagonal stick using specific function

        Given a diagonal stick SVG
        When elongate_diagonal_stick is called with scale factor 1.5
        Then it should return a valid cache hash
        """
        cache_hash = elongate_diagonal_stick(self.diagonal_stick_svg, 1.5)
        assert cache_hash.startswith('svg_')
        assert len(cache_hash) == 12

    def test_elongate_stick_shorten(self):
        """
        Scenario: Shorten stick

        Given a stick SVG
        When elongate_stick is called with scale factor 0.5
        Then it should return a valid cache hash
        """
        cache_hash = elongate_stick(self.horizontal_stick_svg, 0.5)
        assert cache_hash.startswith('svg_')
        assert len(cache_hash) == 12

    def test_elongate_stick_minimum_factor(self):
        """
        Scenario: Apply minimum scale factor

        Given a stick SVG
        When elongate_stick is called with scale factor 0.1 (below minimum)
        Then it should raise ValueError
        """
        with pytest.raises(ValueError, match="Scale factor must be >= 0.2"):
            elongate_stick(self.horizontal_stick_svg, 0.1)

    def test_elongate_stick_invalid_svg(self):
        """
        Scenario: Handle invalid SVG

        Given a non-stick SVG
        When elongate_stick is called
        Then it should raise ValueError
        """
        with pytest.raises(ValueError, match="Not a stick"):
            elongate_stick(self.non_stick_svg, 1.5)

    def test_elongate_stick_cache_consistency(self):
        """
        Scenario: Ensure cache consistency

        Given a stick SVG
        When elongate_stick is called multiple times with same factor
        Then it should return the same cache hash
        """
        hash1 = elongate_stick(self.horizontal_stick_svg, 1.5)
        hash2 = elongate_stick(self.horizontal_stick_svg, 1.5)
        assert hash1 == hash2

    def test_elongate_stick_different_factors(self):
        """
        Scenario: Different factors produce different cache hashes

        Given a stick SVG
        When elongate_stick is called with different scale factors
        Then it should return different cache hashes
        """
        hash1 = elongate_stick(self.horizontal_stick_svg, 1.5)
        hash2 = elongate_stick(self.horizontal_stick_svg, 2.0)
        assert hash1 != hash2
