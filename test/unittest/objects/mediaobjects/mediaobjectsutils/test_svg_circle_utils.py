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
Feature: Circle/Ellipse Elongation Utilities

The SVG circle utilities provide detection and elongation functions
for circle and ellipse SVG elements, enabling interactive scaling with
keyboard modifiers (Ctrl, Shift, Ctrl+Shift).
"""

import os
import shutil
import tempfile
import xml.etree.ElementTree as ET

import pytest

from pyzui.objects.mediaobjects.mediaobjectsutils import elongate_circle, get_circle_bounds, is_circle_svg


class TestSVGCircleUtils:
    """
    Feature: Circle Detection and Elongation

    The circle utilities detect circle and ellipse SVG elements and provide
    center-based scaling functionality with keyboard modifier support.
    """

    def setup_method(self):
        """Create test directory and sample SVG files."""
        self.test_dir = tempfile.mkdtemp(prefix="pyzui_test_circle_")
        self.circle_svg = os.path.join(self.test_dir, "circle.svg")
        self.ellipse_svg = os.path.join(self.test_dir, "ellipse.svg")
        self.non_circle_svg = os.path.join(self.test_dir, "not_circle.svg")
        self.multiple_shapes_svg = os.path.join(self.test_dir, "multiple_shapes.svg")

        # Create a simple circle SVG
        circle_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <circle cx="100" cy="100" r="50" fill="blue"/>
</svg>"""

        # Create a simple ellipse SVG
        ellipse_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <ellipse cx="100" cy="100" rx="60" ry="40" fill="red"/>
</svg>"""

        # Create a non-circle SVG (rectangle)
        non_circle_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <rect x="50" y="50" width="100" height="100" fill="green"/>
</svg>"""

        # Create SVG with multiple shapes
        multiple_shapes_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <circle cx="50" cy="50" r="20" fill="blue"/>
  <ellipse cx="150" cy="150" rx="30" ry="20" fill="red"/>
</svg>"""

        with open(self.circle_svg, 'w') as f:
            f.write(circle_content)

        with open(self.ellipse_svg, 'w') as f:
            f.write(ellipse_content)

        with open(self.non_circle_svg, 'w') as f:
            f.write(non_circle_content)

        with open(self.multiple_shapes_svg, 'w') as f:
            f.write(multiple_shapes_content)

    def teardown_method(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir)

    def test_is_circle_svg_detects_circle(self):
        """
        Scenario: Detect circle SVG

        Given an SVG file containing a single circle element
        When is_circle_svg is called
        Then it should return True
        """
        assert is_circle_svg(self.circle_svg) is True

    def test_is_circle_svg_detects_ellipse(self):
        """
        Scenario: Detect ellipse SVG

        Given an SVG file containing a single ellipse element
        When is_circle_svg is called
        Then it should return True
        """
        assert is_circle_svg(self.ellipse_svg) is True

    def test_is_circle_svg_rejects_non_circle(self):
        """
        Scenario: Reject non-circle SVG

        Given an SVG file without circle or ellipse elements
        When is_circle_svg is called
        Then it should return False
        """
        assert is_circle_svg(self.non_circle_svg) is False

    def test_is_circle_svg_rejects_multiple_shapes(self):
        """
        Scenario: Reject SVG with multiple shapes

        Given an SVG file with multiple circle/ellipse elements
        When is_circle_svg is called
        Then it should return False
        """
        assert is_circle_svg(self.multiple_shapes_svg) is False

    def test_is_circle_svg_handles_nonexistent_file(self):
        """
        Scenario: Handle nonexistent file

        Given a path to a nonexistent file
        When is_circle_svg is called
        Then it should return False
        """
        nonexistent = os.path.join(self.test_dir, "nonexistent.svg")
        assert is_circle_svg(nonexistent) is False

    def test_get_circle_bounds_returns_correct_values(self):
        """
        Scenario: Get circle bounds

        Given a circle SVG file
        When get_circle_bounds is called
        Then it should return (cx, cy, r, r)
        """
        bounds = get_circle_bounds(self.circle_svg)
        assert bounds is not None
        cx, cy, rx, ry = bounds
        assert cx == 100.0
        assert cy == 100.0
        assert rx == 50.0
        assert ry == 50.0

    def test_get_circle_bounds_returns_ellipse_values(self):
        """
        Scenario: Get ellipse bounds

        Given an ellipse SVG file
        When get_circle_bounds is called
        Then it should return (cx, cy, rx, ry)
        """
        bounds = get_circle_bounds(self.ellipse_svg)
        assert bounds is not None
        cx, cy, rx, ry = bounds
        assert cx == 100.0
        assert cy == 100.0
        assert rx == 60.0
        assert ry == 40.0

    def test_get_circle_bounds_handles_non_circle(self):
        """
        Scenario: Handle non-circle in get_circle_bounds

        Given a non-circle SVG file
        When get_circle_bounds is called
        Then it should return None
        """
        bounds = get_circle_bounds(self.non_circle_svg)
        assert bounds is None

    def test_elongate_circle_proportional_scaling(self):
        """
        Scenario: Proportional scaling of circle

        Given a circle SVG file
        When elongate_circle is called with scale_x=1.5, scale_y=1.5
        Then the circle should be scaled proportionally
        And the radius should increase by 50%
        And the center should remain unchanged
        And it should return a cache hash
        """
        # Test with file path
        cache_hash = elongate_circle(self.circle_svg, 1.5, 1.5)

        # Verify cache hash format
        assert cache_hash.startswith("svg_")

        # Verify the cache hash can be retrieved
        from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import get_svg_cache
        cache = get_svg_cache()
        elongated_content = cache.get_svg_content(cache_hash)
        assert elongated_content is not None

        # Verify circle dimensions in elongated SVG
        tree = ET.ElementTree(ET.fromstring(elongated_content))
        root = tree.getroot()
        circle = root.find('.//{http://www.w3.org/2000/svg}circle')
        assert circle is not None

        # Original: cx=100, cy=100, r=50
        # Scaled 1.5x: r=75
        cx = float(circle.get('cx', 0))
        cy = float(circle.get('cy', 0))
        r = float(circle.get('r', 0))

        assert cx == 100.0
        assert cy == 100.0
        assert r == 75.0  # 50 * 1.5

    def test_elongate_circle_x_only_scaling(self):
        """
        Scenario: X-only scaling of circle

        Given a circle SVG file
        When elongate_circle is called with scale_x=1.5, scale_y=1.0
        Then the circle should be converted to ellipse
        And rx should increase by 50%
        And ry should remain unchanged
        And the center should remain unchanged
        """
        cache_hash = elongate_circle(self.circle_svg, 1.5, 1.0)

        assert cache_hash.startswith("svg_")

        from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import get_svg_cache
        cache = get_svg_cache()
        elongated_content = cache.get_svg_content(cache_hash)
        assert elongated_content is not None

        tree = ET.ElementTree(ET.fromstring(elongated_content))
        root = tree.getroot()

        # Circle should be converted to ellipse
        circle = root.find('.//{http://www.w3.org/2000/svg}circle')
        ellipse = root.find('.//{http://www.w3.org/2000/svg}ellipse')

        assert circle is None  # Circle should be gone
        assert ellipse is not None  # Replaced with ellipse

        # Check ellipse dimensions
        cx = float(ellipse.get('cx', 0))
        cy = float(ellipse.get('cy', 0))
        rx = float(ellipse.get('rx', 0))
        ry = float(ellipse.get('ry', 0))

        assert cx == 100.0
        assert cy == 100.0
        assert rx == 75.0  # 50 * 1.5
        assert ry == 50.0  # 50 * 1.0

    def test_elongate_circle_y_only_scaling(self):
        """
        Scenario: Y-only scaling of circle

        Given a circle SVG file
        When elongate_circle is called with scale_x=1.0, scale_y=1.5
        Then the circle should be converted to ellipse
        And rx should remain unchanged
        And ry should increase by 50%
        And the center should remain unchanged
        """
        cache_hash = elongate_circle(self.circle_svg, 1.0, 1.5)

        assert cache_hash.startswith("svg_")

        from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import get_svg_cache
        cache = get_svg_cache()
        elongated_content = cache.get_svg_content(cache_hash)
        assert elongated_content is not None

        tree = ET.ElementTree(ET.fromstring(elongated_content))
        root = tree.getroot()

        # Circle should be converted to ellipse
        circle = root.find('.//{http://www.w3.org/2000/svg}circle')
        ellipse = root.find('.//{http://www.w3.org/2000/svg}ellipse')

        assert circle is None  # Circle should be gone
        assert ellipse is not None  # Replaced with ellipse

        # Check ellipse dimensions
        cx = float(ellipse.get('cx', 0))
        cy = float(ellipse.get('cy', 0))
        rx = float(ellipse.get('rx', 0))
        ry = float(ellipse.get('ry', 0))

        assert cx == 100.0
        assert cy == 100.0
        assert rx == 50.0  # 50 * 1.0
        assert ry == 75.0  # 50 * 1.5

    def test_elongate_ellipse_proportional_scaling(self):
        """
        Scenario: Proportional scaling of ellipse

        Given an ellipse SVG file
        When elongate_circle is called with scale_x=1.5, scale_y=1.5
        Then the ellipse should be scaled proportionally
        And both rx and ry should increase by 50%
        And the center should remain unchanged
        """
        cache_hash = elongate_circle(self.ellipse_svg, 1.5, 1.5)

        assert cache_hash.startswith("svg_")

        from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import get_svg_cache
        cache = get_svg_cache()
        elongated_content = cache.get_svg_content(cache_hash)
        assert elongated_content is not None

        tree = ET.ElementTree(ET.fromstring(elongated_content))
        root = tree.getroot()
        ellipse = root.find('.//{http://www.w3.org/2000/svg}ellipse')
        assert ellipse is not None

        # Original: cx=100, cy=100, rx=60, ry=40
        # Scaled 1.5x: rx=90, ry=60
        cx = float(ellipse.get('cx', 0))
        cy = float(ellipse.get('cy', 0))
        rx = float(ellipse.get('rx', 0))
        ry = float(ellipse.get('ry', 0))

        assert cx == 100.0
        assert cy == 100.0
        assert rx == 90.0  # 60 * 1.5
        assert ry == 60.0  # 40 * 1.5

    def test_elongate_circle_minimum_factor_enforcement(self):
        """
        Scenario: Minimum scale factor enforcement

        Given a circle SVG file
        When elongate_circle is called with scale_x=0.1, scale_y=0.1
        Then it should raise ValueError
        """
        with pytest.raises(ValueError, match="Scale factor X must be >= 0.2"):
            elongate_circle(self.circle_svg, 0.1, 1.0)

        with pytest.raises(ValueError, match="Scale factor Y must be >= 0.2"):
            elongate_circle(self.circle_svg, 1.0, 0.1)

    def test_elongate_circle_at_minimum_factor(self):
        """
        Scenario: Scaling at minimum factor

        Given a circle SVG file
        When elongate_circle is called with scale_x=0.2, scale_y=0.2
        Then it should succeed
        And the radius should be scaled to 20% of original
        """
        cache_hash = elongate_circle(self.circle_svg, 0.2, 0.2)
        assert cache_hash.startswith("svg_")

        from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import get_svg_cache
        cache = get_svg_cache()
        elongated_content = cache.get_svg_content(cache_hash)
        assert elongated_content is not None

        tree = ET.ElementTree(ET.fromstring(elongated_content))
        root = tree.getroot()
        circle = root.find('.//{http://www.w3.org/2000/svg}circle')
        assert circle is not None

        # Original: r=50
        # Scaled 0.2x: r=10
        r = float(circle.get('r', 0))
        assert r == 10.0  # 50 * 0.2

    def test_elongate_circle_viewbox_updates(self):
        """
        Scenario: ViewBox updates with scaling

        Given a circle SVG file
        When elongate_circle is called
        Then the viewBox should be updated to accommodate the scaled shape
        """
        cache_hash = elongate_circle(self.circle_svg, 2.0, 2.0)

        from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import get_svg_cache
        cache = get_svg_cache()
        elongated_content = cache.get_svg_content(cache_hash)

        tree = ET.ElementTree(ET.fromstring(elongated_content))
        root = tree.getroot()

        # Check viewBox attribute
        viewbox = root.get('viewBox')
        assert viewbox is not None

        # Parse viewBox values
        viewbox_parts = list(map(float, viewbox.split()))
        assert len(viewbox_parts) == 4

        # Original circle: cx=100, cy=100, r=50
        # After 2x scaling: r=100
        # Circle bounds: (0, 0) to (200, 200)
        # ViewBox should contain the circle
        assert viewbox_parts[0] <= 0.0  # minX <= circle left
        assert viewbox_parts[1] <= 0.0  # minY <= circle top
        assert viewbox_parts[2] >= 200.0  # width >= circle diameter
        assert viewbox_parts[3] >= 200.0  # height >= circle diameter

    def test_elongate_circle_handles_invalid_file(self):
        """
        Scenario: Handle invalid file

        Given a path to a nonexistent file
        When elongate_circle is called
        Then it should raise an exception
        """
        nonexistent = os.path.join(self.test_dir, "nonexistent.svg")

        # Should raise an exception (FileNotFoundError or similar)
        with pytest.raises(Exception):
            elongate_circle(nonexistent, 1.5, 1.5)

    def test_elongate_circle_preserves_other_attributes(self):
        """
        Scenario: Preserve non-geometric attributes

        Given a circle SVG with additional attributes
        When elongate_circle is called
        Then non-geometric attributes should be preserved
        """
        # Create circle with additional attributes
        complex_circle_svg = os.path.join(self.test_dir, "complex_circle.svg")
        complex_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <circle cx="100" cy="100" r="50" fill="blue" stroke="black" stroke-width="2" id="test-circle" class="shape"/>
</svg>"""

        with open(complex_circle_svg, 'w') as f:
            f.write(complex_content)

        cache_hash = elongate_circle(complex_circle_svg, 1.5, 1.0)

        from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import get_svg_cache
        cache = get_svg_cache()
        elongated_content = cache.get_svg_content(cache_hash)

        tree = ET.ElementTree(ET.fromstring(elongated_content))
        root = tree.getroot()

        # Should be converted to ellipse
        ellipse = root.find('.//{http://www.w3.org/2000/svg}ellipse')
        assert ellipse is not None

        # Check geometric attributes were updated
        rx = float(ellipse.get('rx', 0))
        ry = float(ellipse.get('ry', 0))
        assert rx == 75.0  # 50 * 1.5
        assert ry == 50.0  # 50 * 1.0

        # Check non-geometric attributes were preserved
        assert ellipse.get('fill') == 'blue'
        assert ellipse.get('stroke') == 'black'
        assert ellipse.get('stroke-width') == '2'
        assert ellipse.get('id') == 'test-circle'
        assert ellipse.get('class') == 'shape'
