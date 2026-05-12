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

"""SVG cache management with hashed storage."""

import contextlib
import hashlib
import time
from pathlib import Path

from pyzui.logger import get_logger


class SVGCache:
    """
    Manages hashed SVG cache with ``svg_`` prefix and flat directory structure.

    Hash format: ``svg_{8_char_sha1}``
    Directory: ``/tmp/pyzui_svg_/`` (flat, no subdirectories)
    """

    def __init__(self, cache_root: str = "/tmp/pyzui_svg_"):
        """
        Initialize SVG cache.

        Args:
            cache_root: Root directory for cache (default: ``/tmp/pyzui_svg_``)
        """
        self.cache_root = Path(cache_root)
        self.cache_root.mkdir(exist_ok=True)
        self._logger = get_logger("SVGCache")
        self._logger.debug(f"Initialized SVG cache at {self.cache_root}")

    def _compute_hash(self, svg_content: str) -> str:
        """
        Compute 8-character SHA1 hash with ``svg_`` prefix.

        Args:
            svg_content: SVG XML content as UTF-8 string

        Returns:
            Hash in format: ``svg_{8_char_hex}``
        """
        content_hash = hashlib.sha1(svg_content.encode("utf-8")).hexdigest()[:8]
        return f"svg_{content_hash}"

    def store_svg(self, svg_content: str, max_retries: int = 3) -> str:
        """
        Store SVG content in cache with retry logic on write failure.

        Args:
            svg_content: SVG XML content as UTF-8 string
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            Cache hash (``svg_{8_char_hex}``)

        Raises:
            ValueError: If svg_content is empty or invalid
            Exception: If cache write fails after all retry attempts
        """
        # Validate input
        if not svg_content or not isinstance(svg_content, str):
            raise ValueError(f"Invalid SVG content: {type(svg_content)}")

        if not svg_content.strip():
            raise ValueError("Empty SVG content")

        if not svg_content.startswith("<"):
            self._logger.warning(f"SVG content doesn't start with '<': {svg_content[:100]}...")

        original_content = svg_content

        for attempt in range(max_retries):
            # Compute hash for current content
            content_hash = self._compute_hash(svg_content)
            cache_path = self.cache_root / f"{content_hash}.svg"

            # Check if already exists (content-based deduplication)
            if cache_path.exists():
                # Verify file is not empty/corrupted
                try:
                    if cache_path.stat().st_size == 0:
                        self._logger.warning(f"Cache file exists but is empty: {content_hash}, overwriting")
                    else:
                        self._logger.debug(f"Cache hit for hash: {content_hash}")
                        return content_hash
                except Exception as e:
                    self._logger.warning(f"Error checking cache file {content_hash}: {e}, overwriting")

            try:
                # Write to cache
                cache_path.write_text(svg_content, encoding="utf-8")
                # Verify write succeeded
                if not cache_path.exists() or cache_path.stat().st_size == 0:
                    raise OSError("Cache file write failed: file empty or doesn't exist")

                self._logger.debug(f"Stored SVG to cache: {content_hash} (attempt {attempt + 1})")
                return content_hash
            except Exception as e:
                if attempt < max_retries - 1:
                    # Retry with new hash by modifying content slightly
                    svg_content = original_content + f"<!-- retry_{attempt} -->"
                    self._logger.debug(f"Cache write failed, retrying with new hash: {e}")
                else:
                    self._logger.error(f"Cache write failed after {max_retries} attempts: {e}")
                    raise

        # Should never reach here due to raise in loop
        raise RuntimeError("Cache write failed unexpectedly")

    def get_cache_path(self, content_hash: str) -> Path:
        """
        Get file path for given cache hash.

        Args:
            content_hash: Cache hash in format svg_{8_char_hex}

        Returns:
            Path to cached SVG file
        """
        return self.cache_root / f"{content_hash}.svg"

    def has_hash(self, content_hash: str) -> bool:
        """
        Check if hash exists in cache.

        Args:
            content_hash: Cache hash to check

        Returns:
            True if hash exists in cache
        """
        return self.get_cache_path(content_hash).exists()

    def get_svg_content(self, content_hash: str) -> str | None:
        """
        Get SVG content from cache.

        Args:
            content_hash: Cache hash to retrieve

        Returns:
            SVG content as string, or None if not found
        """
        cache_path = self.get_cache_path(content_hash)
        if not cache_path.exists():
            self._logger.warning(f"Cache miss for hash: {content_hash}")
            return None

        try:
            content = cache_path.read_text(encoding="utf-8")
            self._logger.debug(f"Retrieved SVG from cache: {content_hash}")
            return content
        except Exception as e:
            self._logger.error(f"Failed to read cache file {content_hash}: {e}")
            return None

    def cleanup_old_files(self, max_age_days: int = 14) -> tuple[int, int]:
        """
        Remove cache files older than specified days.

        Args:
            max_age_days: Maximum age in days (default: 14)

        Returns:
            Tuple of (files_removed, bytes_freed)
        """
        cutoff_time = time.time() - (max_age_days * 86400)
        files_removed = 0
        bytes_freed = 0

        self._logger.debug(f"Cleaning up cache files older than {max_age_days} days")

        for file_path in self.cache_root.glob("*.svg"):
            try:
                if file_path.stat().st_mtime < cutoff_time:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    files_removed += 1
                    bytes_freed += file_size
                    self._logger.debug(f"Removed old cache file: {file_path.name}")
            except Exception as e:
                self._logger.warning(f"Failed to remove cache file {file_path.name}: {e}")

        # Record cleanup time
        timestamp_file = self.cache_root / "cleanup_timestamp.txt"
        try:
            timestamp_file.write_text(str(time.time()))
        except Exception as e:
            self._logger.warning(f"Failed to write cleanup timestamp: {e}")

        self._logger.info(f"Cache cleanup: removed {files_removed} files, freed {bytes_freed} bytes")
        return files_removed, bytes_freed

    def cleanup_on_exit(self) -> None:
        """
        Perform cleanup on program exit.

        Currently removes all cache files. Could be modified to keep
        recent files if needed.
        """
        self._logger.debug("Performing exit cleanup")

        files_removed = 0
        for file_path in self.cache_root.glob("*.svg"):
            try:
                file_path.unlink()
                files_removed += 1
                self._logger.debug(f"Removed cache file on exit: {file_path.name}")
            except Exception as e:
                self._logger.warning(f"Failed to remove cache file on exit {file_path.name}: {e}")

        # Try to remove cleanup timestamp file
        timestamp_file = self.cache_root / "cleanup_timestamp.txt"
        if timestamp_file.exists():
            with contextlib.suppress(Exception):
                timestamp_file.unlink()

        self._logger.info(f"Exit cleanup: removed {files_removed} cache files")

    def get_cache_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        svg_files = list(self.cache_root.glob("*.svg"))
        total_size = sum(f.stat().st_size for f in svg_files if f.exists())

        return {
            "cache_root": str(self.cache_root),
            "file_count": len(svg_files),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
        }


# Global cache instance for easy access
_svg_cache_instance: SVGCache | None = None


def get_svg_cache() -> SVGCache:
    """
    Get global SVG cache instance (singleton pattern).

    Returns:
        Global SVGCache instance
    """
    global _svg_cache_instance
    if _svg_cache_instance is None:
        _svg_cache_instance = SVGCache()
    return _svg_cache_instance


def compute_svg_hash(svg_content: str) -> str:
    """
    Compute SVG hash without storing in cache.

    Args:
        svg_content: SVG XML content as UTF-8 string

    Returns:
        Hash in format: ``svg_{8_char_hex}``
    """
    return f"svg_{hashlib.sha1(svg_content.encode('utf-8')).hexdigest()[:8]}"
