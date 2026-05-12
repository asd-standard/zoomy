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

"""Zoom Manager for enforcing zoom limits and preventing crashes."""

from typing import Any


class ZoomManager:
    """
    Manages zoom limits and validation to prevent crashes at extreme zoom levels.

    Zoom levels use base-2 exponential scale:
    - zoomlevel = 0: 1x scale (2**0 = 1)
    - zoomlevel = 1: 2x scale (2**1 = 2)
    - zoomlevel = -1: 0.5x scale (2**-1 = 0.5)

    Default limits: -10 to +12 (safe for StringMediaObjects)
    - -10: 0.00098x scale (0.098%)
    - +12: 4096x scale
    """

    def __init__(self, config: dict[str, Any] | None = None):
        """
        Initialize ZoomManager with configuration.

        Args:
            config: Zoom configuration dictionary with keys:
                - min_zoomlevel: Minimum allowed zoom level (default: -10.0)
                - max_zoomlevel: Maximum allowed zoom level (default: 12.0)
                - clamp_enabled: Whether to clamp values (default: True)
        """
        config = config or {}
        self.min_zoomlevel = float(config.get("min_zoomlevel", -10.0))
        self.max_zoomlevel = float(config.get("max_zoomlevel", 12.0))
        self.clamp_enabled = bool(config.get("clamp_enabled", True))

        # Ensure min <= max (auto-swap if needed)
        if self.min_zoomlevel > self.max_zoomlevel:
            self.min_zoomlevel, self.max_zoomlevel = self.max_zoomlevel, self.min_zoomlevel

    def validate(self, zoomlevel: float) -> float:
        """
        Validate and optionally clamp zoom level.

        Args:
            zoomlevel: Zoom level to validate

        Returns:
            Validated (and possibly clamped) zoom level

        Note:
            If clamp_enabled is False and zoomlevel is out of bounds,
            the value is returned unchanged (no clamping).
        """
        if not self.clamp_enabled:
            return zoomlevel

        if zoomlevel < self.min_zoomlevel:
            return self.min_zoomlevel

        if zoomlevel > self.max_zoomlevel:
            return self.max_zoomlevel

        return zoomlevel

    def is_within_limits(self, zoomlevel: float) -> bool:
        """
        Check if zoom level is within configured limits.

        Args:
            zoomlevel: Zoom level to check

        Returns:
            True if zoomlevel is within [min_zoomlevel, max_zoomlevel]
        """
        return self.min_zoomlevel <= zoomlevel <= self.max_zoomlevel

    def get_limits(self) -> tuple[float, float]:
        """
        Get current zoom limits.

        Returns:
            Tuple of (min_zoomlevel, max_zoomlevel)
        """
        return (self.min_zoomlevel, self.max_zoomlevel)

    def update_config(self, config: dict[str, Any]) -> None:
        """
        Update zoom manager configuration.

        Args:
            config: New zoom configuration dictionary
        """
        if "min_zoomlevel" in config:
            self.min_zoomlevel = float(config["min_zoomlevel"])
        if "max_zoomlevel" in config:
            self.max_zoomlevel = float(config["max_zoomlevel"])
        if "clamp_enabled" in config:
            self.clamp_enabled = bool(config["clamp_enabled"])

        # Ensure min <= max (auto-swap if needed)
        if self.min_zoomlevel > self.max_zoomlevel:
            self.min_zoomlevel, self.max_zoomlevel = self.max_zoomlevel, self.min_zoomlevel
