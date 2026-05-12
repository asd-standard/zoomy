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
Feature: Square/Rectangle Elongation Utilities

The SVG square utilities provide detection and elongation functions
for rectangle SVG elements, enabling interactive scaling with
keyboard modifiers (Ctrl, Shift, Alt).
"""

import os
import shutil
import tempfile

import pytest

from pyzui.objects.mediaobjects.mediaobjectsutils import elongate_square, get_rectangle_bounds, is_square_svg


class TestSVGSquareUtils:
    """
    Feature: Square Detection and Elongation

    The square utilities detect rectangle SVG elements and provide
    center-based scaling functionality with keyboard modifier support.
    """

    def setup_method(self):
        """Create test directory and sample SVG files."""
        self.test_dir = tempfile.mkdtemp(prefix="pyzui_test_")
        self.square_svg = os.path.join(self.test_dir, "square.svg")
        self.non_square_svg = os.path.join(self.test_dir, "not_square.svg")

        # Create a simple square SVG
        square_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <rect x="30" y="30" width="140" height="140" fill="blue"/>
</svg>"""

        # Create a non-rectangle SVG
        non_square_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <circle cx="100" cy="100" r="50" fill="red"/>
</svg>"""

        with open(self.square_svg, 'w') as f:
            f.write(square_content)

        with open(self.non_square_svg, 'w') as f:
            f.write(non_square_content)

    def teardown_method(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def test_is_square_svg_detects_rectangle(self):
        """
        Scenario: Detect rectangle SVG

        Given an SVG file containing a single rectangle element
        When is_square_svg is called
        Then it should return True
        """
        assert is_square_svg(self.square_svg) is True

    def test_is_square_svg_rejects_non_rectangle(self):
        """
        Scenario: Reject non-rectangle SVG

        Given an SVG file without rectangle elements
        When is_square_svg is called
        Then it should return False
        """
        assert is_square_svg(self.non_square_svg) is False

    def test_is_square_svg_handles_nonexistent_file(self):
        """
        Scenario: Handle nonexistent file

        Given a path to a nonexistent file
        When is_square_svg is called
        Then it should return False
        """
        assert is_square_svg("/nonexistent/path/file.svg") is False

    def test_get_rectangle_bounds_returns_correct_values(self):
        """
        Scenario: Extract rectangle bounds

        Given a rectangle SVG file
        When get_rectangle_bounds is called
        Then it should return correct x, y, width, height
        """
        bounds = get_rectangle_bounds(self.square_svg)
        assert bounds == (30.0, 30.0, 140.0, 140.0)

    def test_get_rectangle_bounds_handles_non_rectangle(self):
        """
        Scenario: Handle non-rectangle SVG

        Given a non-rectangle SVG file
        When get_rectangle_bounds is called
        Then it should return None
        """
        bounds = get_rectangle_bounds(self.non_square_svg)
        assert bounds is None

    def test_elongate_square_proportional_scaling(self):
        """
        Scenario: Proportional scaling from center

        Given a rectangle SVG
        When elongated with equal X and Y scale factors
        Then it should scale proportionally from center and return cache hash
        """
        # Test with file path
        cache_hash = elongate_square(self.square_svg, 2.0, 2.0)

        # Verify cache hash format
        assert cache_hash.startswith("svg_")
        assert len(cache_hash) == 12  # "svg_" + 8 chars

        # Verify the cache hash can be retrieved
        from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import get_svg_cache
        cache = get_svg_cache()
        elongated_content = cache.get_svg_content(cache_hash)
        assert elongated_content is not None

        # Verify rectangle dimensions in elongated SVG
        import xml.etree.ElementTree as ET
        tree = ET.ElementTree(ET.fromstring(elongated_content))
        root = tree.getroot()
        rect = root.find('.//{http://www.w3.org/2000/svg}rect')
        assert rect is not None

        # Original: x=30, y=30, width=140, height=140
        # Center: (30 + 140/2, 30 + 140/2) = (100, 100)
        # Scaled 2x from center:
        # new_width = 140 * 2 = 280, new_height = 140 * 2 = 280
        # new_x = 100 - 280/2 = 100 - 140 = -40
        # new_y = 100 - 280/2 = 100 - 140 = -40
        x = float(rect.get('x', 0))
        y = float(rect.get('y', 0))
        width = float(rect.get('width', 0))
        height = float(rect.get('height', 0))

        assert x == -40.0
        assert y == -40.0
        assert width == 280.0
        assert height == 280.0

    def test_elongate_square_x_only_scaling(self):
        """
        Scenario: X-only scaling from center

        Given a rectangle SVG
        When elongated with X scale factor only (Y=1.0)
        Then it should scale width only from center
        """
        cache_hash = elongate_square(self.square_svg, 2.0, 1.0)

        assert cache_hash.startswith("svg_")

        from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import get_svg_cache
        cache = get_svg_cache()
        elongated_content = cache.get_svg_content(cache_hash)
        assert elongated_content is not None

        import xml.etree.ElementTree as ET
        tree = ET.ElementTree(ET.fromstring(elongated_content))
        root = tree.getroot()
        rect = root.find('.//{http://www.w3.org/2000/svg}rect')
        assert rect is not None

        # Original: x=30, y=30, width=140, height=140
        # Center: (30 + 140/2, 30 + 140/2) = (100, 100)
        # Scaled 2x width from center, 1x height:
        # new_width = 140 * 2 = 280, new_height = 140 * 1 = 140
        # new_x = 100 - 280/2 = 100 - 140 = -40
        # new_y = 100 - 140/2 = 100 - 70 = 30
        x = float(rect.get('x', 0))
        y = float(rect.get('y', 0))
        width = float(rect.get('width', 0))
        height = float(rect.get('height', 0))

        assert x == -40.0
        assert y == 30.0
        assert width == 280.0
        assert height == 140.0

    def test_elongate_square_y_only_scaling(self):
        """
        Scenario: Y-only scaling from center

        Given a rectangle SVG
        When elongated with Y scale factor only (X=1.0)
        Then it should scale height only from center
        """
        cache_hash = elongate_square(self.square_svg, 1.0, 2.0)

        assert cache_hash.startswith("svg_")

        from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import get_svg_cache
        cache = get_svg_cache()
        elongated_content = cache.get_svg_content(cache_hash)
        assert elongated_content is not None

        import xml.etree.ElementTree as ET
        tree = ET.ElementTree(ET.fromstring(elongated_content))
        root = tree.getroot()
        rect = root.find('.//{http://www.w3.org/2000/svg}rect')
        assert rect is not None

        # Original: x=30, y=30, width=140, height=140
        # Center: (30 + 140/2, 30 + 140/2) = (100, 100)
        # Scaled 1x width, 2x height from center:
        # new_width = 140 * 1 = 140, new_height = 140 * 2 = 280
        # new_x = 100 - 140/2 = 100 - 70 = 30
        # new_y = 100 - 280/2 = 100 - 140 = -40
        x = float(rect.get('x', 0))
        y = float(rect.get('y', 0))
        width = float(rect.get('width', 0))
        height = float(rect.get('height', 0))

        assert x == 30.0
        assert y == -40.0
        assert width == 140.0
        assert height == 280.0

    def test_elongate_square_minimum_factor_enforcement(self):
        """
        Scenario: Enforce minimum scale factor

        Given a rectangle SVG
        When elongated with scale factor below 0.2
        Then it should reject the operation
        """
        with pytest.raises(ValueError, match="Scale factor X must be >= 0.2"):
            elongate_square(self.square_svg, 0.1, 1.0)

        with pytest.raises(ValueError, match="Scale factor Y must be >= 0.2"):
            elongate_square(self.square_svg, 1.0, 0.1)

    def test_elongate_square_at_minimum_factor(self):
        """
        Scenario: Scale at minimum factor

        Given a rectangle SVG
        When elongated with scale factor exactly 0.2
        Then it should succeed
        """
        cache_hash = elongate_square(self.square_svg, 0.2, 0.2)
        assert cache_hash.startswith("svg_")

        from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import get_svg_cache
        cache = get_svg_cache()
        elongated_content = cache.get_svg_content(cache_hash)
        assert elongated_content is not None

        import xml.etree.ElementTree as ET
        tree = ET.ElementTree(ET.fromstring(elongated_content))
        root = tree.getroot()
        rect = root.find('.//{http://www.w3.org/2000/svg}rect')
        assert rect is not None

        # Original: x=30, y=30, width=140, height=140
        # Center: (30 + 140/2, 30 + 140/2) = (100, 100)
        # Scaled 0.2x from center:
        # new_width = 140 * 0.2 = 28, new_height = 140 * 0.2 = 28
        # new_x = 100 - 28/2 = 100 - 14 = 86
        # new_y = 100 - 28/2 = 100 - 14 = 86
        x = float(rect.get('x', 0))
        y = float(rect.get('y', 0))
        width = float(rect.get('width', 0))
        height = float(rect.get('height', 0))

        assert x == 86.0
        assert y == 86.0
        assert width == 28.0
        assert height == 28.0

    def test_elongate_square_viewbox_updates(self):
        """
        Scenario: Update SVG viewBox

        Given a rectangle SVG
        When elongated
        Then the SVG viewBox should be updated to match content
        """
        cache_hash = elongate_square(self.square_svg, 2.0, 2.0)

        from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import get_svg_cache
        cache = get_svg_cache()
        elongated_content = cache.get_svg_content(cache_hash)

        import xml.etree.ElementTree as ET
        tree = ET.ElementTree(ET.fromstring(elongated_content))
        root = tree.getroot()

        # Check viewBox attribute
        viewbox = root.get('viewBox')
        assert viewbox is not None

        # Parse viewBox values
        viewbox_parts = list(map(float, viewbox.split()))
        assert len(viewbox_parts) == 4

        # Original viewBox: "0 0 200 200"
        # After 2x scaling from center, rectangle goes from (-40,-40) to (240,240)
        # So viewBox should be updated to contain the rectangle
        assert viewbox_parts[0] <= -40.0  # minX <= rectangle x
        assert viewbox_parts[1] <= -40.0  # minY <= rectangle y
        assert viewbox_parts[2] >= 280.0  # width >= rectangle width
        assert viewbox_parts[3] >= 280.0  # height >= rectangle height

    def test_elongate_square_handles_invalid_file(self):
        """
        Scenario: Handle invalid SVG file

        Given an invalid/non-SVG file
        When elongate_square is called
        Then it should raise an exception
        """
        # Create invalid file
        invalid_file = os.path.join(self.test_dir, "invalid.svg")
        with open(invalid_file, 'w') as f:
            f.write("not an svg file")

        # Should raise an exception (ParseError or similar)
        with pytest.raises(Exception):
            elongate_square(invalid_file, 2.0, 2.0)

    def test_elongate_square_preserves_other_elements(self):
        """
        Scenario: Preserve non-rectangle elements

        Given an SVG with rectangle and other elements
        When elongated
        Then only rectangle should be modified
        """
        # Create SVG with rectangle and circle
        complex_svg = os.path.join(self.test_dir, "complex.svg")
        complex_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <rect x="30" y="30" width="140" height="140" fill="blue"/>
  <circle cx="100" cy="100" r="20" fill="red" id="test-circle"/>
</svg>"""

        with open(complex_svg, 'w') as f:
            f.write(complex_content)

        cache_hash = elongate_square(complex_svg, 2.0, 1.0)

        from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import get_svg_cache
        cache = get_svg_cache()
        elongated_content = cache.get_svg_content(cache_hash)

        import xml.etree.ElementTree as ET
        tree = ET.ElementTree(ET.fromstring(elongated_content))
        root = tree.getroot()

        # Rectangle should be modified
        rect = root.find('.//{http://www.w3.org/2000/svg}rect')
        assert rect is not None
        width = float(rect.get('width', 0))
        assert width == 280.0  # 140 * 2.0

        # Check x position too (should be -40 as calculated above)
        x = float(rect.get('x', 0))
        assert x == -40.0

        # Circle should be preserved unchanged
        circle = root.find('.//{http://www.w3.org/2000/svg}circle[@id="test-circle"]')
        assert circle is not None
        assert circle.get('cx') == '100'
        assert circle.get('cy') == '100'
        assert circle.get('r') == '20'
