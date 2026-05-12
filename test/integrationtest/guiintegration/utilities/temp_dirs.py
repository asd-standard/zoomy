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

"""Temporary directory utilities for pytest-style test directory creation."""

import getpass
from pathlib import Path


def get_pytest_style_temp_dir() -> Path:
    """
    Create a temp directory structure similar to pytest:
    /tmp/pytest-of-{username}/pytest-{n}/pyzui_gui_test0/
    """
    username = getpass.getuser()
    base_dir = Path(f"/tmp/pytest-of-{username}")
    base_dir.mkdir(exist_ok=True)

    # Find next pytest-N number
    existing = list(base_dir.glob("pytest-*"))
    if existing:
        nums = []
        for p in existing:
            try:
                nums.append(int(p.name.split("-")[1]))
            except (IndexError, ValueError):
                pass
        next_num = max(nums) + 1 if nums else 0
    else:
        next_num = 0

    pytest_dir = base_dir / f"pytest-{next_num}"
    pytest_dir.mkdir(exist_ok=True)

    test_dir = pytest_dir / "pyzui_gui_test0"
    test_dir.mkdir(exist_ok=True)

    return test_dir
