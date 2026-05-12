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

"""Image creation utilities for test resources (no external dependencies)."""


def create_ppm_image(
    filepath: str, width: int, height: int, color: tuple = (128, 128, 128), pattern: str = "solid"
) -> None:
    """Create a PPM image file (no external dependencies required)."""
    pixels = []

    for y in range(height):
        row = []
        for x in range(width):
            if pattern == "solid":
                r, g, b = color
            elif pattern == "gradient":
                factor = x / width
                r = int(color[0] + (255 - color[0]) * factor)
                g = int(color[1] + (255 - color[1]) * factor)
                b = int(color[2] + (255 - color[2]) * factor)
            elif pattern == "checkerboard":
                cell_size = 32
                if ((x // cell_size) + (y // cell_size)) % 2 == 0:
                    r, g, b = color
                else:
                    r, g, b = 255, 255, 255
            elif pattern == "stripes":
                stripe_width = 20
                if (y // stripe_width) % 2 == 0:
                    r, g, b = color
                else:
                    r, g, b = 255, 255, 255
            elif pattern == "diagonal":
                factor = (x + y) / (width + height)
                r = int(color[0] * (1 - factor) + 100 * factor)
                g = int(color[1] * (1 - factor) + 100 * factor)
                b = int(color[2] * (1 - factor) + 200 * factor)
            else:
                r, g, b = color

            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            row.extend([r, g, b])
        pixels.append(bytes(row))

    with open(filepath, "wb") as f:
        header = f"P6\n{width} {height}\n255\n"
        f.write(header.encode("ascii"))
        for row in pixels:
            f.write(row)


def create_png_image(
    filepath: str, width: int, height: int, color: tuple = (128, 128, 128), pattern: str = "solid"
) -> bool:
    """Create a PNG image using PIL if available."""
    try:
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (width, height), color=color)
        draw = ImageDraw.Draw(img)

        if pattern == "gradient":
            for x in range(width):
                factor = x / width
                r = int(color[0] + (255 - color[0]) * factor)
                g = int(color[1] + (255 - color[1]) * factor)
                b = int(color[2] + (255 - color[2]) * factor)
                draw.line([(x, 0), (x, height)], fill=(r, g, b))

        elif pattern == "checkerboard":
            cell_size = 32
            for cy in range(0, height, cell_size):
                for cx in range(0, width, cell_size):
                    if ((cx // cell_size) + (cy // cell_size)) % 2 == 1:
                        draw.rectangle([cx, cy, cx + cell_size, cy + cell_size], fill=(255, 255, 255))

        elif pattern == "stripes":
            stripe_width = 20
            for sy in range(0, height, stripe_width * 2):
                draw.rectangle([0, sy + stripe_width, width, sy + stripe_width * 2], fill=(255, 255, 255))

        elif pattern == "diagonal":
            for i in range(-height, width, 10):
                factor = (i + height) / (width + height)
                line_color = (
                    int(color[0] * (1 - factor) + 100 * factor),
                    int(color[1] * (1 - factor) + 100 * factor),
                    int(color[2] * (1 - factor) + 200 * factor),
                )
                draw.line([(i, 0), (i + height, height)], fill=line_color, width=5)

        elif pattern == "circles":
            center_x, center_y = width // 2, height // 2
            max_radius = min(width, height) // 2
            for rad in range(max_radius, 0, -20):
                factor = rad / max_radius
                circle_color = (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))
                draw.ellipse([center_x - rad, center_y - rad, center_x + rad, center_y + rad], fill=circle_color)

        img.save(filepath)
        return True

    except ImportError:
        return False
