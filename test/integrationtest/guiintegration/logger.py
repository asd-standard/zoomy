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

"""GUI test logger with visual formatting for human-readable test output."""

from pyzui.logger import get_logger


class GUITestLogger:
    """Helper class for logging GUI test actions with visual markers."""

    def __init__(self, name: str = "GUITest"):
        self.logger = get_logger(name)
        self.step_count = 0

    def action(self, description: str) -> None:
        self.step_count += 1
        self.logger.info("=" * 60)
        self.logger.info(f"STEP {self.step_count}: {description}")
        self.logger.info("=" * 60)

    def detail(self, message: str) -> None:
        self.logger.debug(f"  -> {message}")

    def wait(self, description: str) -> None:
        self.logger.debug(f"  [WAIT] {description}")

    def success(self, message: str) -> None:
        self.logger.info(f"  [OK] {message}")

    def warning(self, message: str) -> None:
        self.logger.warning(f"  [WARN] {message}")

    def section(self, title: str) -> None:
        self.logger.info("")
        self.logger.info("#" * 70)
        self.logger.info(f"# {title}")
        self.logger.info("#" * 70)
        self.logger.info("")
