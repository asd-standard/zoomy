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

"""SVG square/rectangle detection and elongation utilities."""

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
_logger = get_logger("SVGSquareUtils")


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


def is_square_svg(svg_path: str) -> bool:
    """
    Check if SVG contains a single rectangle element.

    Returns:
        True if SVG contains exactly one <rect> element, False otherwise
    """
    try:
        tree = _load_svg_tree(svg_path)
        root = tree.getroot()

        # Find rectangle elements
        rects = root.findall(".//svg:rect", SVG_NS)

        if len(rects) != 1:
            _logger.debug(f"Not a single rectangle: found {len(rects)} rect elements")
            return False

        rect = rects[0]

        # Check required attributes
        required_attrs = ["x", "y", "width", "height"]
        for attr in required_attrs:
            if rect.get(attr) is None:
                _logger.debug(f"Rectangle missing required attribute: {attr}")
                return False

        # Validate coordinates are numeric
        try:
            x = float(rect.get("x", 0))
            y = float(rect.get("y", 0))
            width = float(rect.get("width", 0))
            height = float(rect.get("height", 0))

            # Check for valid dimensions
            if width <= 0 or height <= 0:
                _logger.debug(f"Invalid rectangle dimensions: width={width}, height={height}")
                return False

        except (ValueError, TypeError):
            _logger.debug("Invalid rectangle coordinate values")
            return False

        _logger.debug(f"Detected rectangle at {svg_path}: x={x}, y={y}, width={width}, height={height}")
        return True

    except ET.ParseError as e:
        _logger.error(f"Failed to parse SVG {svg_path}: {e}")
        return False
    except Exception as e:
        _logger.error(f"Error checking SVG {svg_path}: {e}")
        return False


def get_rectangle_bounds(svg_path: str) -> tuple[float, float, float, float] | None:
    """
    Get rectangle bounds: (x, y, width, height).

    Returns:
        Tuple of (x, y, width, height) or None if not a rectangle
    """
    try:
        if not is_square_svg(svg_path):
            return None

        tree = _load_svg_tree(svg_path)
        root = tree.getroot()

        rect = root.find(".//svg:rect", SVG_NS)
        if rect is None:
            return None

        x = float(rect.get("x", 0))
        y = float(rect.get("y", 0))
        width = float(rect.get("width", 0))
        height = float(rect.get("height", 0))

        return (x, y, width, height)

    except Exception as e:
        _logger.error(f"Error getting rectangle bounds from {svg_path}: {e}")
        return None


def elongate_square(svg_path: str, scale_x: float, scale_y: float) -> str:
    """
    Elongate rectangle by scaling width and height from center.

    Stores modified SVG in cache and returns cache hash.

    Args:
        svg_path: Path to SVG file (will be read but not modified)
        scale_x: Multiplier for width (minimum 0.2)
        scale_y: Multiplier for height (minimum 0.2)

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

        # Get rectangle element
        rect = root.find(".//svg:rect", SVG_NS)
        if rect is None:
            raise ValueError(f"No rectangle element found in {svg_path}")

        # Get current rectangle attributes
        try:
            x = float(rect.get("x", 0))
            y = float(rect.get("y", 0))
            width = float(rect.get("width", 0))
            height = float(rect.get("height", 0))
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid rectangle coordinates in {svg_path}: {e}") from e

        # Calculate center point
        center_x = x + width / 2.0
        center_y = y + height / 2.0

        # Calculate center point
        center_x = x + width / 2.0
        center_y = y + height / 2.0

        # Calculate new dimensions
        new_width = width * scale_x
        new_height = height * scale_y

        # Calculate new position to keep center fixed
        new_x = center_x - new_width / 2.0
        new_y = center_y - new_height / 2.0

        # Update rectangle attributes
        rect.set("x", str(new_x))
        rect.set("y", str(new_y))
        rect.set("width", str(new_width))
        rect.set("height", str(new_height))

        _logger.debug(
            f"Updated rectangle: x={new_x:.2f}, y={new_y:.2f}, width={new_width:.2f}, height={new_height:.2f}"
        )

        # Get current SVG dimensions
        current_width = root.get("width")
        current_height = root.get("height")

        # Calculate bounds of rectangle (after update)
        rect_points = [
            (new_x, new_y),
            (new_x + new_width, new_y),
            (new_x, new_y + new_height),
            (new_x + new_width, new_y + new_height),
        ]

        # Calculate bounds
        all_x_coords = [x for x, _ in rect_points]
        all_y_coords = [y for _, y in rect_points]

        min_x = min(all_x_coords)
        max_x = max(all_x_coords)
        min_y = min(all_y_coords)
        max_y = max(all_y_coords)

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

        _logger.info(f"Elongated rectangle by factors X={scale_x:.2f}, Y={scale_y:.2f}, cache hash: {cache_hash}")

        return cache_hash

    except Exception as e:
        _logger.error(f"Error elongating rectangle {svg_path}: {e}")
        raise
