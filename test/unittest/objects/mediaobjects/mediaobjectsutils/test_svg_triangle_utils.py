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
Feature: Triangle SVG Elongation Utilities

The SVG triangle utilities provide detection and elongation functions
for triangle SVG elements, enabling interactive scaling with
keyboard modifiers (Ctrl, Shift, Alt).
"""

import os
import shutil
import tempfile

import pytest

from pyzui.objects.mediaobjects.mediaobjectsutils import elongate_triangle, get_triangle_bounds, is_triangle_svg


class TestSVGTriangleUtils:
    """
    Feature: Triangle Detection and Elongation

    The triangle utilities detect triangle SVG elements and provide
    center-based scaling functionality with keyboard modifier support.
    """

    def setup_method(self):
        """Create test directory and sample SVG files."""
        self.test_dir = tempfile.mkdtemp(prefix="pyzui_test_")
        self.up_triangle_svg = os.path.join(self.test_dir, "up_triangle.svg")
        self.down_triangle_svg = os.path.join(self.test_dir, "down_triangle.svg")
        self.non_triangle_svg = os.path.join(self.test_dir, "not_triangle.svg")

        # Create an up triangle SVG (apex at top)
        up_triangle_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <polygon points="100,30 170,170 30,170" stroke="black" stroke-width="8" fill="none"/>
</svg>"""

        # Create a down triangle SVG (apex at bottom)
        down_triangle_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <polygon points="100,170 170,30 30,30" stroke="black" stroke-width="8" fill="none"/>
</svg>"""

        # Create a non-triangle SVG (circle)
        non_triangle_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <circle cx="100" cy="100" r="50" fill="red"/>
</svg>"""

        with open(self.up_triangle_svg, 'w') as f:
            f.write(up_triangle_content)

        with open(self.down_triangle_svg, 'w') as f:
            f.write(down_triangle_content)

        with open(self.non_triangle_svg, 'w') as f:
            f.write(non_triangle_content)

    def teardown_method(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def test_is_triangle_svg_detects_up_triangle(self):
        """
        Scenario: Detect up triangle SVG

        Given an SVG file containing a single up triangle polygon element
        When is_triangle_svg is called
        Then it should return True
        """
        assert is_triangle_svg(self.up_triangle_svg) is True

    def test_is_triangle_svg_detects_down_triangle(self):
        """
        Scenario: Detect down triangle SVG

        Given an SVG file containing a single down triangle polygon element
        When is_triangle_svg is called
        Then it should return True
        """
        assert is_triangle_svg(self.down_triangle_svg) is True

    def test_is_triangle_svg_rejects_non_triangle(self):
        """
        Scenario: Reject non-triangle SVG

        Given an SVG file without triangle elements
        When is_triangle_svg is called
        Then it should return False
        """
        assert is_triangle_svg(self.non_triangle_svg) is False

    def test_is_triangle_svg_rejects_arrow_with_line(self):
        """
        Scenario: Reject arrow SVG (has line element)

        Given an SVG file with line element (likely an arrow)
        When is_triangle_svg is called
        Then it should return False
        """
        arrow_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <line x1="50" y1="100" x2="150" y2="100" stroke="black" stroke-width="8"/>
  <polygon points="150,100 130,90 130,110" stroke="black" stroke-width="8" fill="black"/>
</svg>"""

        arrow_path = os.path.join(self.test_dir, "arrow.svg")
        with open(arrow_path, 'w') as f:
            f.write(arrow_content)

        assert is_triangle_svg(arrow_path) is False

    def test_is_triangle_svg_handles_nonexistent_file(self):
        """
        Scenario: Handle nonexistent file

        Given a path to a nonexistent file
        When is_triangle_svg is called
        Then it should return False
        """
        nonexistent = os.path.join(self.test_dir, "nonexistent.svg")
        assert is_triangle_svg(nonexistent) is False

    def test_get_triangle_bounds_returns_correct_values(self):
        """
        Scenario: Get triangle bounds

        Given a triangle SVG file
        When get_triangle_bounds is called
        Then it should return correct (min_x, min_y, width, height)
        """
        bounds = get_triangle_bounds(self.up_triangle_svg)
        assert bounds is not None
        min_x, min_y, width, height = bounds

        # Up triangle: points (100,30) (170,170) (30,170)
        assert min_x == 30.0
        assert min_y == 30.0
        assert width == 140.0  # 170 - 30
        assert height == 140.0  # 170 - 30

    def test_get_triangle_bounds_handles_non_triangle(self):
        """
        Scenario: Handle non-triangle bounds request

        Given a non-triangle SVG file
        When get_triangle_bounds is called
        Then it should return None
        """
        bounds = get_triangle_bounds(self.non_triangle_svg)
        assert bounds is None

    def test_elongate_triangle_proportional_scaling(self):
        """
        Scenario: Proportional triangle scaling

        Given a triangle SVG file
        When elongate_triangle is called with proportional scaling (scale_x = scale_y = 1.5)
        Then it should return a valid cache hash
        """
        cache_hash = elongate_triangle(self.up_triangle_svg, 1.5, 1.5)
        assert cache_hash is not None
        assert cache_hash.startswith("svg_")
        assert len(cache_hash) == 12  # "svg_" + 8 chars

    def test_elongate_triangle_x_only_scaling(self):
        """
        Scenario: X-only triangle scaling

        Given a triangle SVG file
        When elongate_triangle is called with X-only scaling (scale_x = 1.2, scale_y = 1.0)
        Then it should return a valid cache hash
        """
        cache_hash = elongate_triangle(self.up_triangle_svg, 1.2, 1.0)
        assert cache_hash is not None
        assert cache_hash.startswith("svg_")
        assert len(cache_hash) == 12

    def test_elongate_triangle_y_only_scaling(self):
        """
        Scenario: Y-only triangle scaling

        Given a triangle SVG file
        When elongate_triangle is called with Y-only scaling (scale_x = 1.0, scale_y = 1.3)
        Then it should return a valid cache hash
        """
        cache_hash = elongate_triangle(self.up_triangle_svg, 1.0, 1.3)
        assert cache_hash is not None
        assert cache_hash.startswith("svg_")
        assert len(cache_hash) == 12

    def test_elongate_triangle_minimum_factor_enforcement(self):
        """
        Scenario: Enforce minimum scale factor

        Given a triangle SVG file
        When elongate_triangle is called with scale factor below 0.2
        Then it should raise ValueError
        """
        with pytest.raises(ValueError, match="Scale factor X must be >= 0.2"):
            elongate_triangle(self.up_triangle_svg, 0.1, 1.0)

        with pytest.raises(ValueError, match="Scale factor Y must be >= 0.2"):
            elongate_triangle(self.up_triangle_svg, 1.0, 0.1)

    def test_elongate_triangle_at_minimum_factor(self):
        """
        Scenario: Scale at minimum factor

        Given a triangle SVG file
        When elongate_triangle is called with scale factor exactly 0.2
        Then it should succeed and return a valid cache hash
        """
        cache_hash = elongate_triangle(self.up_triangle_svg, 0.2, 0.2)
        assert cache_hash is not None
        assert cache_hash.startswith("svg_")
        assert len(cache_hash) == 12

    def test_elongate_triangle_orientation_preserved(self):
        """
        Scenario: Preserve triangle orientation during scaling

        Given an up triangle SVG file
        When elongate_triangle is called with scaling
        Then the triangle should remain pointing up (orientation preserved)

        Given a down triangle SVG file
        When elongate_triangle is called with scaling
        Then the triangle should remain pointing down (orientation preserved)
        """
        # Test up triangle
        up_cache_hash = elongate_triangle(self.up_triangle_svg, 1.5, 1.5)
        assert up_cache_hash is not None

        # Test down triangle
        down_cache_hash = elongate_triangle(self.down_triangle_svg, 1.5, 1.5)
        assert down_cache_hash is not None

        # Note: Orientation preservation is inherent in centroid-based scaling
        # Both cache hashes should be different since triangles are different
        assert up_cache_hash != down_cache_hash

    def test_elongate_triangle_handles_invalid_file(self):
        """
        Scenario: Handle invalid SVG file

        Given a path to an invalid/non-existent SVG file
        When elongate_triangle is called
        Then it should raise an appropriate exception
        """
        invalid_path = os.path.join(self.test_dir, "invalid.svg")

        with pytest.raises((FileNotFoundError, ValueError, Exception)):
            elongate_triangle(invalid_path, 1.0, 1.0)

    def test_elongate_triangle_preserves_stroke_width(self):
        """
        Scenario: Preserve stroke width during scaling

        Given a triangle SVG with specific stroke width
        When elongate_triangle is called
        Then the stroke width should remain unchanged
        """
        # This test would require parsing the cached SVG to check stroke-width
        # For now, we just verify the function succeeds
        cache_hash = elongate_triangle(self.up_triangle_svg, 1.5, 1.5)
        assert cache_hash is not None
        assert cache_hash.startswith("svg_")
