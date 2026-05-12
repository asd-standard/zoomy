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

"""SVG circle/ellipse detection and elongation utilities."""

import math
import os
import shutil
import xml.etree.ElementTree as ET

from pyzui.logger import get_logger

from ..svgcache.svgcache import get_svg_cache

# SVG namespace for XML parsing
SVG_NS = {"svg": "http://www.w3.org/2000/svg"}


def _load_svg_tree(svg_input: str) -> ET.ElementTree:
    """
    Load SVG XML tree from either file path or cache hash.

    Args:
        svg_input: Either a file path or cache hash (starting with ``'svg_'``)

    Returns:
        ElementTree object

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If cache hash not found
        ET.ParseError: If XML parsing fails
    """
    if svg_input.startswith("svg_"):
        # It's a cache hash, load from cache
        cache = get_svg_cache()
        svg_content = cache.get_svg_content(svg_input)
        if svg_content is None:
            raise ValueError(f"Cache hash not found: {svg_input}")
        root = ET.fromstring(svg_content)
        assert root is not None, f"Failed to parse SVG content: {svg_content[:100]}"
        return ET.ElementTree(root)
    else:
        # It's a file path
        if not os.path.exists(svg_input):
            raise FileNotFoundError(f"SVG file not found: {svg_input}")
        return ET.parse(svg_input)


# Module logger
_logger = get_logger("SVGCircleUtils")


def _create_backup(svg_path: str) -> str | None:
    """
    Create a backup copy of the SVG file.

    Returns:
        Path to backup file or None on failure
    """
    try:
        backup_path = svg_path + ".backup"
        shutil.copy2(svg_path, backup_path)
        _logger.debug(f"Created backup: {backup_path}")
        return backup_path
    except Exception as e:
        _logger.error(f"Failed to create backup for {svg_path}: {e}")
        return None


def _restore_from_backup(svg_path: str, backup_path: str) -> bool:
    """
    Restore SVG file from backup.

    Returns:
        True if successful, False otherwise
    """
    try:
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, svg_path)
            _logger.debug(f"Restored from backup: {svg_path}")
            return True
        else:
            _logger.error(f"Backup file not found: {backup_path}")
            return False
    except Exception as e:
        _logger.error(f"Failed to restore from backup {backup_path}: {e}")
        return False


def _cleanup_backup(backup_path: str) -> None:
    """Remove backup file if it exists."""
    try:
        if os.path.exists(backup_path):
            os.remove(backup_path)
            _logger.debug(f"Cleaned up backup: {backup_path}")
    except Exception as e:
        _logger.warning(f"Failed to cleanup backup {backup_path}: {e}")


def is_circle_svg(svg_path: str) -> bool:
    """
    Check if SVG contains a single circle or ellipse element.

    Returns:
        True if SVG contains exactly one <circle> or <ellipse> element, False otherwise
    """
    try:
        tree = _load_svg_tree(svg_path)
        root = tree.getroot()

        # Find circle and ellipse elements
        circles = root.findall(".//svg:circle", SVG_NS)
        ellipses = root.findall(".//svg:ellipse", SVG_NS)

        total_shapes = len(circles) + len(ellipses)

        if total_shapes != 1:
            _logger.debug(f"Not a single circle/ellipse: found {len(circles)} circles and {len(ellipses)} ellipses")
            return False

        # Check if it's a circle
        if circles:
            circle = circles[0]

            # Check required attributes for circle
            required_attrs = ["cx", "cy", "r"]
            for attr in required_attrs:
                if circle.get(attr) is None:
                    _logger.debug(f"Circle missing required attribute: {attr}")
                    return False

            # Validate coordinates are numeric
            try:
                cx = float(circle.get("cx", 0))
                cy = float(circle.get("cy", 0))
                r = float(circle.get("r", 0))

                # Check for valid radius
                if r <= 0:
                    _logger.debug(f"Invalid circle radius: r={r}")
                    return False

                _logger.debug(f"Detected circle at {svg_path}: cx={cx}, cy={cy}, r={r}")
                return True

            except (ValueError, TypeError):
                _logger.debug("Invalid circle coordinate values")
                return False

        # Check if it's an ellipse
        elif ellipses:
            ellipse = ellipses[0]

            # Check required attributes for ellipse
            required_attrs = ["cx", "cy", "rx", "ry"]
            for attr in required_attrs:
                if ellipse.get(attr) is None:
                    _logger.debug(f"Ellipse missing required attribute: {attr}")
                    return False

            # Validate coordinates are numeric
            try:
                cx = float(ellipse.get("cx", 0))
                cy = float(ellipse.get("cy", 0))
                rx = float(ellipse.get("rx", 0))
                ry = float(ellipse.get("ry", 0))

                # Check for valid radii
                if rx <= 0 or ry <= 0:
                    _logger.debug(f"Invalid ellipse radii: rx={rx}, ry={ry}")
                    return False

                _logger.debug(f"Detected ellipse at {svg_path}: cx={cx}, cy={cy}, rx={rx}, ry={ry}")
                return True

            except (ValueError, TypeError):
                _logger.debug("Invalid ellipse coordinate values")
                return False

        return False

    except ET.ParseError as e:
        _logger.error(f"Failed to parse SVG {svg_path}: {e}")
        return False
    except Exception as e:
        _logger.error(f"Error checking SVG {svg_path}: {e}")
        return False


def get_circle_bounds(svg_path: str) -> tuple[float, float, float, float] | None:
    """
    Get circle/ellipse bounds: (cx, cy, rx, ry).

    For circles, rx = ry = r.

    Returns:
        Tuple of (cx, cy, rx, ry) or None if not a circle/ellipse
    """
    try:
        if not is_circle_svg(svg_path):
            return None

        tree = _load_svg_tree(svg_path)
        root = tree.getroot()

        # Check for circle first
        circle = root.find(".//svg:circle", SVG_NS)
        if circle is not None:
            cx = float(circle.get("cx", 0))
            cy = float(circle.get("cy", 0))
            r = float(circle.get("r", 0))
            return (cx, cy, r, r)

        # Check for ellipse
        ellipse = root.find(".//svg:ellipse", SVG_NS)
        if ellipse is not None:
            cx = float(ellipse.get("cx", 0))
            cy = float(ellipse.get("cy", 0))
            rx = float(ellipse.get("rx", 0))
            ry = float(ellipse.get("ry", 0))
            return (cx, cy, rx, ry)

        return None

    except Exception as e:
        _logger.error(f"Error getting circle bounds from {svg_path}: {e}")
        return None


def elongate_circle(svg_path: str, scale_x: float, scale_y: float) -> str:
    """
    Elongate circle/ellipse by scaling radii from center.

    Stores modified SVG in cache and returns cache hash.

    Args:
        svg_path: Path to SVG file (will be read but not modified)
        scale_x: Multiplier for rx (minimum 0.2)
        scale_y: Multiplier for ry (minimum 0.2)

    Returns:
        Cache hash of modified SVG (format: svg_{8_char_hex})

    Raises:
        ValueError: If scale_x < 0.2 or scale_y < 0.2
        Exception: If SVG parsing or modification fails
    """
    if scale_x < 0.2:
        raise ValueError(f"Scale factor X must be >= 0.2, got {scale_x}")
    if scale_y < 0.2:
        raise ValueError(f"Scale factor Y must be >= 0.2, got {scale_y}")

    # Get SVG cache
    svg_cache = get_svg_cache()

    try:
        # Parse SVG
        tree = _load_svg_tree(svg_path)
        root = tree.getroot()

        # Get circle or ellipse element
        circle = root.find(".//svg:circle", SVG_NS)
        ellipse = root.find(".//svg:ellipse", SVG_NS)

        if circle is None and ellipse is None:
            raise ValueError(f"No circle or ellipse element found in {svg_path}")

        # Initialize variables
        cx: float = 0.0
        cy: float = 0.0
        new_rx: float = 0.0
        new_ry: float = 0.0

        # Get current SVG dimensions
        current_width = root.get("width")
        current_height = root.get("height")

        # Handle circle
        if circle is not None:
            # Get current circle attributes
            try:
                cx = float(circle.get("cx", 0))
                cy = float(circle.get("cy", 0))
                r = float(circle.get("r", 0))
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid circle coordinates in {svg_path}: {e}") from e

            new_rx = r * scale_x
            new_ry = r * scale_y

            # If scaling is proportional (scale_x == scale_y), keep as circle
            if math.isclose(scale_x, scale_y, rel_tol=1e-9):
                # Update circle radius
                circle.set("r", str(new_rx))
                _logger.debug(f"Updated circle: cx={cx}, cy={cy}, r={new_rx:.2f}")
            else:
                # Convert circle to ellipse with different radii
                # Change tag from circle to ellipse
                circle.tag = "{http://www.w3.org/2000/svg}ellipse"

                # Update attributes for ellipse
                circle.set("rx", str(new_rx))
                circle.set("ry", str(new_ry))

                # Remove 'r' attribute (not used for ellipse)
                if "r" in circle.attrib:
                    del circle.attrib["r"]

                _logger.debug(f"Converted circle to ellipse: cx={cx}, cy={cy}, rx={new_rx:.2f}, ry={new_ry:.2f}")

        # Handle ellipse
        elif ellipse is not None:
            # Get current ellipse attributes
            try:
                cx = float(ellipse.get("cx", 0))
                cy = float(ellipse.get("cy", 0))
                rx = float(ellipse.get("rx", 0))
                ry = float(ellipse.get("ry", 0))
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid ellipse coordinates in {svg_path}: {e}") from e

            # Calculate new radii
            new_rx = rx * scale_x
            new_ry = ry * scale_y

            # Update ellipse radii
            ellipse.set("rx", str(new_rx))
            ellipse.set("ry", str(new_ry))
            _logger.debug(f"Updated ellipse: cx={cx}, cy={cy}, rx={new_rx:.2f}, ry={new_ry:.2f}")

        # Calculate bounds of circle/ellipse
        # Use new_rx and new_ry which are already calculated
        min_x = cx - new_rx
        max_x = cx + new_rx
        min_y = cy - new_ry
        max_y = cy + new_ry

        # Calculate padding based on current dimensions or default
        default_padding = 20.0
        if current_width and current_height:
            try:
                current_width_val = float(current_width)
                current_height_val = float(current_height)
                padding_x = max(current_width_val * 0.1, default_padding)
                padding_y = max(current_height_val * 0.1, default_padding)
            except (ValueError, TypeError):
                padding_x = padding_y = default_padding
        else:
            padding_x = padding_y = default_padding

        # Apply padding to bounds (allow negative coordinates in viewBox)
        padded_min_x = min_x - padding_x * 0.5
        padded_max_x = max_x + padding_x * 0.5
        padded_min_y = min_y - padding_y * 0.5
        padded_max_y = max_y + padding_y * 0.5

        # Calculate dimensions from padded bounds
        viewbox_width = padded_max_x - padded_min_x
        viewbox_height = padded_max_y - padded_min_y

        # Set viewBox (allows negative coordinates)
        root.set("viewBox", f"{padded_min_x} {padded_min_y} {viewbox_width} {viewbox_height}")
        _logger.debug(f"Updated viewBox: {padded_min_x} {padded_min_y} {viewbox_width} {viewbox_height}")

        # Update width and height to match viewBox dimensions
        # This ensures consistent aspect ratio
        if current_width:
            root.set("width", str(viewbox_width))
        if current_height:
            root.set("height", str(viewbox_height))

        # Log dimension updates
        if current_width and current_height:
            _logger.debug(f"Updated dimensions: width={viewbox_width}, height={viewbox_height}")

        # Convert to string and store in cache
        svg_content = ET.tostring(root, encoding="utf-8").decode("utf-8")
        cache_hash = svg_cache.store_svg(svg_content)

        _logger.info(f"Elongated circle/ellipse by factors X={scale_x:.2f}, Y={scale_y:.2f}, cache hash: {cache_hash}")

        return cache_hash

    except Exception as e:
        _logger.error(f"Error elongating circle/ellipse {svg_path}: {e}")
        raise
