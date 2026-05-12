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

"""SVG triangle detection and elongation utilities."""

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
_logger = get_logger("SVGTriangleUtils")


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


def _parse_polygon_points(points_str: str) -> list[tuple[float, float]]:
    """
    Parse SVG polygon points string into list of (x,y) tuples.

    Args:
        points_str: SVG polygon points attribute value

    Returns:
        List of (x, y) coordinate tuples

    Raises:
        ValueError: If points string is malformed
    """
    points = []
    for pair in points_str.strip().split():
        if "," in pair:
            try:
                x, y = map(float, pair.split(","))
                points.append((x, y))
            except ValueError as e:
                raise ValueError(f"Invalid point coordinate: {pair}") from e
    return points


def _calculate_triangle_centroid(points: list[tuple[float, float]]) -> tuple[float, float]:
    """
    Calculate triangle centroid (center of mass).

    Args:
        points: List of 3 (x, y) coordinate tuples

    Returns:
        (centroid_x, centroid_y) tuple
    """
    if len(points) != 3:
        raise ValueError(f"Expected 3 points for triangle, got {len(points)}")

    x_sum = sum(p[0] for p in points)
    y_sum = sum(p[1] for p in points)

    return (x_sum / 3.0, y_sum / 3.0)


def _scale_points_from_center(
    points: list[tuple[float, float]], center: tuple[float, float], scale_x: float, scale_y: float
) -> list[tuple[float, float]]:
    """
    Scale points relative to center with separate X/Y scaling.

    Args:
        points: List of (x, y) coordinate tuples
        center: (center_x, center_y) tuple
        scale_x: X-axis scaling factor
        scale_y: Y-axis scaling factor

    Returns:
        List of scaled (x, y) coordinate tuples
    """
    cx, cy = center
    scaled_points = []

    for x, y in points:
        new_x = cx + (x - cx) * scale_x
        new_y = cy + (y - cy) * scale_y
        scaled_points.append((new_x, new_y))

    return scaled_points


def is_triangle_svg(svg_path: str) -> bool:
    """
    Check if SVG contains a single triangle polygon element.

    Returns:
        True if SVG contains exactly one <polygon> element with 3 points, False otherwise
    """
    try:
        tree = _load_svg_tree(svg_path)
        root = tree.getroot()

        # Find polygon elements
        polygons = root.findall(".//svg:polygon", SVG_NS)

        if len(polygons) != 1:
            _logger.debug(f"Not a single polygon: found {len(polygons)} polygon elements")
            return False

        polygon = polygons[0]

        # Get points attribute
        points_str = polygon.get("points")
        if points_str is None:
            _logger.debug("Polygon missing 'points' attribute")
            return False

        # Parse points
        try:
            points = _parse_polygon_points(points_str)
        except ValueError as e:
            _logger.debug(f"Invalid polygon points: {e}")
            return False

        # Check for exactly 3 points (triangle)
        if len(points) != 3:
            _logger.debug(f"Not a triangle: polygon has {len(points)} points")
            return False

        # Check that there are no line elements (distinguish from arrows)
        lines = root.findall(".//svg:line", SVG_NS)
        if len(lines) > 0:
            _logger.debug(f"Contains line elements (likely an arrow): found {len(lines)} lines")
            return False

        # Validate coordinates are reasonable
        try:
            for i, (x, y) in enumerate(points):
                if not (math.isfinite(x) and math.isfinite(y)):
                    _logger.debug(f"Point {i} has non-finite coordinates: ({x}, {y})")
                    return False
        except (ValueError, TypeError):
            _logger.debug("Invalid polygon coordinate values")
            return False

        _logger.debug(f"Detected triangle at {svg_path} with points: {points}")
        return True

    except ET.ParseError as e:
        _logger.error(f"Failed to parse SVG {svg_path}: {e}")
        return False
    except Exception as e:
        _logger.error(f"Error checking SVG {svg_path}: {e}")
        return False


def get_triangle_bounds(svg_path: str) -> tuple[float, float, float, float] | None:
    """
    Get triangle bounds: (min_x, min_y, width, height).

    Returns:
        Tuple of (min_x, min_y, width, height) or None if not a triangle
    """
    try:
        if not is_triangle_svg(svg_path):
            return None

        tree = _load_svg_tree(svg_path)
        root = tree.getroot()

        polygon = root.find(".//svg:polygon", SVG_NS)
        if polygon is None:
            return None

        points_str = polygon.get("points")
        if points_str is None:
            return None

        points = _parse_polygon_points(points_str)

        # Calculate bounds
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]

        min_x = min(x_coords)
        max_x = max(x_coords)
        min_y = min(y_coords)
        max_y = max(y_coords)

        width = max_x - min_x
        height = max_y - min_y

        return (min_x, min_y, width, height)

    except Exception as e:
        _logger.error(f"Error getting triangle bounds from {svg_path}: {e}")
        return None


def elongate_triangle(svg_path: str, scale_x: float, scale_y: float) -> str:
    """
    Elongate triangle by scaling from center with separate X/Y scaling.

    Stores modified SVG in cache and returns cache hash.

    Args:
        svg_path: Path to SVG file (will be read but not modified)
        scale_x: Multiplier for X-axis (minimum 0.2)
        scale_y: Multiplier for Y-axis (minimum 0.2)

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

        # Get polygon element
        polygon = root.find(".//svg:polygon", SVG_NS)
        if polygon is None:
            raise ValueError(f"No polygon element found in {svg_path}")

        # Get points attribute
        points_str = polygon.get("points")
        if points_str is None:
            raise ValueError(f"Polygon missing 'points' attribute in {svg_path}")

        # Parse points
        points = _parse_polygon_points(points_str)
        if len(points) != 3:
            raise ValueError(f"Expected triangle with 3 points, got {len(points)} points")

        # Calculate triangle centroid
        centroid = _calculate_triangle_centroid(points)
        _logger.debug(f"Triangle centroid: {centroid}")

        # Scale points from centroid
        scaled_points = _scale_points_from_center(points, centroid, scale_x, scale_y)
        _logger.debug(f"Scaled points: {scaled_points}")

        # Update polygon points attribute
        points_formatted = " ".join(f"{x:.6f},{y:.6f}" for x, y in scaled_points)
        polygon.set("points", points_formatted)

        # Get current SVG dimensions
        current_width = root.get("width")
        current_height = root.get("height")

        # Calculate bounds of scaled triangle
        x_coords = [p[0] for p in scaled_points]
        y_coords = [p[1] for p in scaled_points]

        min_x = min(x_coords)
        max_x = max(x_coords)
        min_y = min(y_coords)
        max_y = max(y_coords)

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

        _logger.info(f"Elongated triangle by factors X={scale_x:.2f}, Y={scale_y:.2f}, cache hash: {cache_hash}")

        return cache_hash

    except Exception as e:
        _logger.error(f"Error elongating triangle {svg_path}: {e}")
        raise
