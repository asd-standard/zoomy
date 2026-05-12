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

"""SVG arrow detection and elongation utilities."""

import os
import shutil
import xml.etree.ElementTree as ET

from pyzui.logger import get_logger

from ..svgcache.svgcache import get_svg_cache

# SVG namespace for XML parsing
SVG_NS = {"svg": "http://www.w3.org/2000/svg"}

# Module logger
_logger = get_logger("SVGArrowUtils")


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


def is_straight_arrow_svg(svg_input: str) -> bool:
    """
    Check if SVG is a straight arrow (up, down, left, right).

    Args:
        svg_input: Either a file path or cache hash (starting with ``'svg_'``)

    Returns:
        True if SVG matches straight arrow pattern, False otherwise
    """
    try:
        tree = _load_svg_tree(svg_input)
        root = tree.getroot()

        # Find line and polygon elements
        lines = root.findall(".//svg:line", SVG_NS)
        polygons = root.findall(".//svg:polygon", SVG_NS)

        if len(lines) != 1 or len(polygons) != 1:
            _logger.debug(f"Not a straight arrow: wrong element count (lines={len(lines)}, polygons={len(polygons)})")
            return False

        line = lines[0]
        polygon = polygons[0]

        # Get coordinates
        try:
            x1 = float(line.get("x1", 0))
            y1 = float(line.get("y1", 0))
            x2 = float(line.get("x2", 0))
            y2 = float(line.get("y2", 0))
        except (ValueError, TypeError):
            _logger.debug("Invalid line coordinates")
            return False

        # Check if line is straight (horizontal or vertical)
        # Allow small floating point errors (0.1 units)
        is_horizontal = abs(y1 - y2) < 0.1
        is_vertical = abs(x1 - x2) < 0.1

        if not (is_horizontal or is_vertical):
            _logger.debug(f"Line not straight: ({x1},{y1}) to ({x2},{y2})")
            return False

        # Check polygon has points
        if polygon.get("points") is None:
            _logger.debug("Polygon has no points")
            return False

        _logger.debug(f"Detected straight arrow at {svg_input}")
        return True

    except ET.ParseError as e:
        _logger.error(f"Failed to parse SVG {svg_input}: {e}")
        return False
    except Exception as e:
        _logger.error(f"Error checking SVG {svg_input}: {e}")
        return False


def get_arrow_direction(svg_path: str) -> str | None:
    """
    Determine arrow direction: 'right', 'left', 'up', or 'down'.

    Returns:
        Direction string or None if not a straight arrow
    """
    try:
        tree = _load_svg_tree(svg_path)
        root = tree.getroot()

        line = root.find(".//svg:line", SVG_NS)
        if line is None:
            return None

        try:
            x1 = float(line.get("x1", 0))
            y1 = float(line.get("y1", 0))
            x2 = float(line.get("x2", 0))
            y2 = float(line.get("y2", 0))
        except (ValueError, TypeError):
            return None

        # Determine direction with tolerance
        if abs(y1 - y2) < 0.1:  # Horizontal
            if x1 < x2:
                return "right"
            else:
                return "left"
        elif abs(x1 - x2) < 0.1:  # Vertical
            if y1 < y2:
                return "down"
            else:
                return "up"
        else:
            return None

    except Exception as e:
        _logger.error(f"Error getting arrow direction from {svg_path}: {e}")
        return None


def is_diagonal_arrow_svg(svg_path: str) -> bool:
    """
    Check if SVG is a 45° diagonal arrow (upright, upleft, downright, downleft).

    Returns:
        True if SVG matches 45° diagonal arrow pattern, False otherwise
    """
    try:
        tree = _load_svg_tree(svg_path)
        root = tree.getroot()

        # Find line and polygon elements
        lines = root.findall(".//svg:line", SVG_NS)
        polygons = root.findall(".//svg:polygon", SVG_NS)

        if len(lines) != 1 or len(polygons) != 1:
            _logger.debug(f"Not a diagonal arrow: wrong element count (lines={len(lines)}, polygons={len(polygons)})")
            return False

        line = lines[0]
        polygon = polygons[0]

        # Get coordinates
        try:
            x1 = float(line.get("x1", 0))
            y1 = float(line.get("y1", 0))
            x2 = float(line.get("x2", 0))
            y2 = float(line.get("y2", 0))
        except (ValueError, TypeError):
            _logger.debug("Invalid line coordinates")
            return False

        # Check if line is at 45° (± tolerance)
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)

        # 10% tolerance or 0.1 units (match existing straight arrow logic)
        tolerance = max(dx, dy) * 0.1
        is_45_degree = abs(dx - dy) < max(tolerance, 0.1)

        if not is_45_degree:
            _logger.debug(f"Line not 45°: dx={dx}, dy={dy}, tolerance={max(tolerance, 0.1)}")
            return False

        # Check polygon has points
        if polygon.get("points") is None:
            _logger.debug("Polygon has no points")
            return False

        _logger.debug(f"Detected 45° diagonal arrow at {svg_path}")
        return True

    except ET.ParseError as e:
        _logger.error(f"Failed to parse SVG {svg_path}: {e}")
        return False
    except Exception as e:
        _logger.error(f"Error checking SVG {svg_path}: {e}")
        return False


def get_diagonal_arrow_direction(svg_path: str) -> str | None:
    """
    Determine diagonal arrow direction: 'upright', 'upleft', 'downright', or 'downleft'.

    Returns:
        Direction string or None if not a 45° diagonal arrow
    """
    try:
        tree = _load_svg_tree(svg_path)
        root = tree.getroot()

        line = root.find(".//svg:line", SVG_NS)
        if line is None:
            return None

        try:
            x1 = float(line.get("x1", 0))
            y1 = float(line.get("y1", 0))
            x2 = float(line.get("x2", 0))
            y2 = float(line.get("y2", 0))
        except (ValueError, TypeError):
            return None

        # Check if line is at 45° (± tolerance)
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        tolerance = max(dx, dy) * 0.1
        is_45_degree = abs(dx - dy) < max(tolerance, 0.1)

        if not is_45_degree:
            return None

        # Determine diagonal direction
        if x1 < x2:  # Rightward
            if y1 < y2:  # Downward
                return "downright"
            else:  # Upward
                return "upright"
        else:  # Leftward
            if y1 < y2:  # Downward
                return "downleft"
            else:  # Upward
                return "upleft"

    except Exception as e:
        _logger.error(f"Error getting diagonal arrow direction from {svg_path}: {e}")
        return None


def is_arrow_svg(svg_path: str) -> bool:
    """
    Check if SVG is any arrow (straight or 45° diagonal).

    Returns:
        True if SVG matches any arrow pattern, False otherwise
    """
    return is_straight_arrow_svg(svg_path) or is_diagonal_arrow_svg(svg_path)


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


def elongate_straight_arrow(svg_path: str, scale_factor: float) -> str:
    """
    Elongate straight arrow SVG.

    Stores modified SVG in cache and returns cache hash.

    Args:
        svg_path: Path to SVG file (will be read but not modified)
        scale_factor: Multiplier for arrow length (minimum 0.2)

    Returns:
        Cache hash of modified SVG (format: svg_{8_char_hex})

    Raises:
        ValueError: If scale_factor < 0.2
        Exception: If SVG parsing or modification fails
    """
    if scale_factor < 0.2:
        raise ValueError(f"Scale factor must be >= 0.2, got {scale_factor}")

    # Get SVG cache
    svg_cache = get_svg_cache()

    try:
        # Parse SVG
        tree = _load_svg_tree(svg_path)
        root = tree.getroot()

        # Get arrow direction
        direction = get_arrow_direction(svg_path)
        if direction is None:
            raise ValueError(f"Not a straight arrow: {svg_path}")

        # Find elements
        line = root.find(".//svg:line", SVG_NS)
        polygon = root.find(".//svg:polygon", SVG_NS)

        if line is None or polygon is None:
            raise ValueError(f"Missing line or polygon in {svg_path}")

        # Get current coordinates
        try:
            x1 = float(line.get("x1", 0))
            y1 = float(line.get("y1", 0))
            x2 = float(line.get("x2", 0))
            y2 = float(line.get("y2", 0))
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid coordinates in {svg_path}: {e}") from e

        # Parse polygon points
        points_str = polygon.get("points", "")
        points = []
        for pair in points_str.split():
            if "," in pair:
                try:
                    x, y = map(float, pair.split(","))
                    points.append((x, y))
                except (ValueError, TypeError):
                    _logger.error(f"Invalid polygon point: {pair}")
                    return False

        if len(points) != 3:
            _logger.error(f"Expected triangle arrowhead, got {len(points)} points")
            return False

        # Calculate new line end coordinates
        # Initialize shift variables (used for left/up arrows that go negative)

        if direction == "right" or direction == "left":
            new_x2 = x1 + (x2 - x1) * scale_factor
            new_y2 = y1
            line_base_x = x2
            line_base_y = y2
        elif direction == "up" or direction == "down":
            new_x2 = x1
            new_y2 = y1 + (y2 - y1) * scale_factor
            line_base_x = x2
            line_base_y = y2
        else:
            _logger.error(f"Unknown direction: {direction}")
            raise ValueError(f"Unknown direction: {direction}")

        # Update line coordinates
        line.set("x2", str(new_x2))
        line.set("y2", str(new_y2))

        # Calculate arrowhead offset
        dx = new_x2 - line_base_x
        dy = new_y2 - line_base_y

        # Update polygon points (uniform scaling - maintain arrowhead size)
        new_points = []
        for px, py in points:
            # Move points by the same offset as line end
            new_px = px + dx
            new_py = py + dy
            new_points.append(f"{new_px},{new_py}")

        polygon.set("points", " ".join(new_points))

        # Update SVG dimensions to accommodate elongated/shortened arrow
        # Get current SVG dimensions
        current_width = root.get("width")
        current_height = root.get("height")

        # Calculate all points after modification (before any potential shifting)
        all_points = [(x1, y1), (new_x2, new_y2)] + [(px + dx, py + dy) for px, py in points]

        # Calculate bounds of all points
        all_x_coords = [x for x, _ in all_points]
        all_y_coords = [y for _, y in all_points]

        # Initialize bounds
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

        # Handle each direction separately
        # Don't shift coordinates - allow negative values in viewBox

        # For all directions, we'll update dimensions based on actual bounds

        # For straight arrows, allow negative coordinates in viewBox
        # Don't shift coordinates - just calculate proper bounds with padding

        # Apply padding to bounds
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

        _logger.info(f"Elongated {direction} arrow by factor {scale_factor:.2f}, cache hash: {cache_hash}")

        return cache_hash

    except Exception as e:
        _logger.error(f"Error elongating arrow {svg_path}: {e}")
        raise


def elongate_diagonal_arrow(svg_path: str, scale_factor: float) -> str:
    """
    Elongate 45° diagonal arrow SVG.

    Stores modified SVG in cache and returns cache hash.

    Args:
        svg_path: Path to SVG file (will be read but not modified)
        scale_factor: Multiplier for arrow length (minimum 0.2)

    Returns:
        Cache hash of modified SVG (format: svg_{8_char_hex})

    Raises:
        ValueError: If scale_factor < 0.2
        Exception: If SVG parsing or modification fails
    """
    if scale_factor < 0.2:
        raise ValueError(f"Scale factor must be >= 0.2, got {scale_factor}")

    # Get SVG cache
    svg_cache = get_svg_cache()

    try:
        # Parse SVG
        tree = _load_svg_tree(svg_path)
        root = tree.getroot()

        # Get arrow direction
        direction = get_diagonal_arrow_direction(svg_path)
        if direction is None:
            raise ValueError(f"Not a 45° diagonal arrow: {svg_path}")

        # Find elements
        line = root.find(".//svg:line", SVG_NS)
        polygon = root.find(".//svg:polygon", SVG_NS)

        if line is None or polygon is None:
            raise ValueError(f"Missing line or polygon in {svg_path}")

        # Get current coordinates
        try:
            x1 = float(line.get("x1", 0))
            y1 = float(line.get("y1", 0))
            x2 = float(line.get("x2", 0))
            y2 = float(line.get("y2", 0))
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid coordinates in {svg_path}: {e}") from e

        # Parse polygon points
        points_str = polygon.get("points", "")
        points = []
        for pair in points_str.split():
            if "," in pair:
                try:
                    x, y = map(float, pair.split(","))
                    points.append((x, y))
                except (ValueError, TypeError):
                    _logger.error(f"Invalid polygon point: {pair}")
                    return False

        if len(points) != 3:
            _logger.error(f"Expected triangle arrowhead, got {len(points)} points")
            return False

        # Initialize shift variables (used for arrows that go negative)

        # Calculate new line end coordinates (scale both x and y)
        if direction == "upright" or direction == "upleft" or direction == "downright" or direction == "downleft":
            new_x2 = x1 + (x2 - x1) * scale_factor
            new_y2 = y1 + (y2 - y1) * scale_factor
            line_base_x = x2
            line_base_y = y2
        else:
            _logger.error(f"Unknown diagonal direction: {direction}")
            return False

        # Update line coordinates
        line.set("x2", str(new_x2))
        line.set("y2", str(new_y2))

        # Calculate arrowhead offset
        dx = new_x2 - line_base_x
        dy = new_y2 - line_base_y

        # Update polygon points (uniform scaling - maintain arrowhead size)
        new_points = []
        for px, py in points:
            # Move points by the same offset as line end
            new_px = px + dx
            new_py = py + dy
            new_points.append(f"{new_px},{new_py}")

        polygon.set("points", " ".join(new_points))

        # Update SVG dimensions to accommodate elongated/shortened arrow
        # Get current SVG dimensions
        current_width = root.get("width")
        current_height = root.get("height")

        # Calculate all points after modification (before any potential shifting)
        all_points = [(x1, y1), (new_x2, new_y2)] + [(px + dx, py + dy) for px, py in points]

        # Calculate bounds of all points
        all_x_coords = [x for x, _ in all_points]
        all_y_coords = [y for _, y in all_points]

        # Initialize bounds
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

        # For diagonal arrows, allow negative coordinates in viewBox
        # Don't shift coordinates - just calculate proper bounds with padding

        # Apply padding to bounds
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

        _logger.info(f"Elongated {direction} diagonal arrow by factor {scale_factor:.2f}, cache hash: {cache_hash}")

        return cache_hash

    except Exception as e:
        _logger.error(f"Error elongating diagonal arrow {svg_path}: {e}")
        raise
