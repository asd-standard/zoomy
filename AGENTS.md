# PyZUI Agent Guidelines

This document provides essential information for AI agents working on the PyZUI codebase. PyZUI is a Python Zooming User Interface (ZUI) application built with PySide6/Qt.

## Table of Contents
1. [Build and Run Commands](#build-and-run-commands)
2. [Testing Commands](#testing-commands)
3. [Code Style Guidelines](#code-style-guidelines)
4. [Project Structure](#project-structure)
5. [Development Workflow](#development-workflow)
6. [Versioning](#versioning)
7. [Agent-Specific Instructions](#agent-specific-instructions)

## Build and Run Commands

### Running the Application
```bash
# With Wayland support (recommended - uses PyZui-wayland environment)
./pyzui.sh

# Or manually with conda run
conda run -n PyZui-wayland python main.py

# Basic execution (uses current active environment)
python main.py

# With configuration file
python main.py --config pyzui_config_example.json
```

### Environment Setup
**Available Environments:**
- `PyZui` - Base environment with core dependencies
- `PyZui-wayland` - Active environment with Wayland support (`qt6-wayland` installed)

**Setup Commands:**
```bash
# List available environments
conda info --envs

# Activate PyZui-wayland (recommended for Wayland display servers)
conda activate PyZui-wayland

# Or use conda run without activating
conda run -n PyZui-wayland python main.py

# Create base environment from YAML
conda env create -f PyZui.yml
conda activate PyZui

# Install development dependencies
pip install pytest pytest-cov pytest-xdist
```

**Environment Notes:**
- `PyZui-wayland` includes `qt6-wayland` for native Wayland support
- Use `PyZui-wayland` for hardware acceleration on Wayland display servers
- The `pyzui.sh` launcher script automatically uses `PyZui-wayland`

### Documentation Generation
```bash
# Generate Sphinx documentation
cd docs
make clean
make html
# Output: docs/build/html/index.html
```

## Testing Commands

### Unit Tests
```bash
# Run all unit tests
cd test/unittest
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest test/unittest/tilesystem/test_tile.py

# Run specific test class
pytest test/unittest/tilesystem/test_tile.py::TestTile

# Run specific test method
pytest test/unittest/tilesystem/test_tile.py::TestTile::test_init_with_pil_image

# Run tests matching pattern
pytest -k "tile"  # Runs all tests with 'tile' in name

# Stop on first failure
pytest -x

# Show print statements
pytest -v -s
```

### Integration Tests (Pytest-based)
```bash
# Run all integration tests
cd test/integrationtest
pytest

# Run specific integration test
pytest test/integrationtest/test_tilemanager_integration.py

# Run with verbose output
pytest -v

# Run tests matching pattern
pytest -k "converter"  # Runs converter integration tests
```

### GUI Integration Test (Special Case - Human Verification)
```bash
# GUI integration test (requires display, human verification)
python test/integrationtest/guiintegration/main.py

# Start from specific step
python test/integrationtest/guiintegration/main.py --start-step 10
python test/integrationtest/guiintegration/main.py -s 30

# List available steps
python test/integrationtest/guiintegration/main.py --list-steps
```

**Note**: The `guiintegration/` directory contains a structured GUI test suite for human visual verification. Each test step is in its own module under `test/`. For automated testing, use the pytest-based integration tests.

### Coverage Reports
```bash
# Generate HTML coverage report (from project root)
pytest --cov=pyzui --cov-report=html
# Open htmlcov/index.html in browser

# Terminal coverage report
pytest --cov=pyzui --cov-report=term-missing

# Coverage for specific module
pytest --cov=pyzui.tilesystem --cov-report=term

# Parallel test execution
pytest -n auto
```

### Running All Tests
```bash
# Run both unit and integration tests
cd test
pytest unittest/ integrationtest/

# Alternative: Run from project root with path specification
pytest test/unittest/ test/integrationtest/
```

## Linting Commands

### Ruff (linter + formatter)
```bash
# Run linter on source code only
conda run -n PyZui-wayland ruff check

# Run linter + autofix (safe fixes)
conda run -n PyZui-wayland ruff check --fix

# Run linter + autofix (all fixes, including unsafe)
conda run -n PyZui-wayland ruff check --fix --unsafe-fixes

# Format code (like Black)
conda run -n PyZui-wayland ruff format

# Check formatting without applying
conda run -n PyZui-wayland ruff format --check
```

### mypy (type checker)
```bash
# Run type checker on source code
conda run -n PyZui-wayland mypy --explicit-package-bases --follow-imports=skip pyzui/

# Run on a single file
conda run -n PyZui-wayland mypy pyzui/path/to/file.py
```

**Note:** mypy is run manually, not in pre-commit. There are ~176 type issues to fix
incrementally before it can be added to CI.

### pre-commit (runs automatically before every commit)
```bash
# Run all hooks manually on all files
conda run -n PyZui-wayland pre-commit run --all-files

# Install hooks (one-time setup)
conda run -n PyZui-wayland pre-commit install
```

**Current hooks:** ruff (checks + autofix imports/style) and ruff-format (code formatting).
Test files (`test/`) and scripts (`scripts/`) are excluded from linting.

## Code Style Guidelines

### File Headers
Every Python file must start with the GPL license header:
```python
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
```

### Imports Organization
```python
# Standard library imports
import sys
import os
from typing import Optional, Any, Tuple
from pathlib import Path

# Third-party imports
from PySide6 import QtCore, QtGui, QtWidgets
from PIL import Image

# Local imports
from pyzui.objects.scene import scene as Scene
from pyzui.tilesystem import tilemanager as TileManager
```

### Type Hints
Always use type hints for function signatures and class methods:
```python
def __init__(self, parent: Optional[QtWidgets.QWidget] = None,
             framerate: int = 10, zoom_sensitivity: int = 10) -> None:
```

### Documentation Style
Use descriptive docstrings with Given-When-Then format for tests:

**Class docstrings:**
```python
class TestTile:
    """
    Feature: Tile Image Operations

    The Tile class wraps image data (PIL or QImage) and provides operations
    for manipulating tiles including cropping, resizing, saving, and rendering.
    """
```

**Method docstrings (BDD style):**
```python
def test_init_with_pil_image(self):
    """
    Scenario: Create tile from PIL Image

    Given a PIL Image with dimensions 100x100
    When a Tile is created from the PIL Image
    Then the tile size should be (100, 100)
    """
```

**Function docstrings:**
```python
def load_config(config_file=None):
    """Load configuration from JSON file.

    Args:
        config_file (str): Path to configuration file

    Returns:
        dict: Configuration dictionary with logging and tilestore sections
    """
```

### Naming Conventions
- **Classes**: `CamelCase` (e.g., `PhysicalObject`, `TileCache`)
- **Methods/Functions**: `snake_case` (e.g., `load_config`, `test_init`)
- **Variables**: `snake_case` (e.g., `tile_size`, `max_accesses`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_FRAMERATE`, `MAX_TILE_SIZE`)
- **Private attributes**: `_leading_underscore` (e.g., `_initialized`, `_log_dir`)

### Error Handling
- Use explicit exception types
- Log errors using the centralized logger
- Provide meaningful error messages
- Clean up resources in finally blocks

### Testing Patterns
- Follow Arrange-Act-Assert pattern
- One assert per test (when possible)
- Mock external dependencies
- Test edge cases and error conditions
- Use `pytest.approx()` for floating-point comparisons
- Skip tests when dependencies are missing

## Project Structure

```
pyzui/
├── __init__.py              # Package exports and metadata
├── logger.py               # Centralized logging configuration
├── objects/                # Object system
│   ├── scene/             # Scene management and QZUI widget
│   └── mediaobjects/      # Media object types
├── tilesystem/            # Tile generation and caching
│   ├── tile.py            # Tile class
│   ├── tilecache.py       # LRU tile cache
│   ├── tilemanager.py     # Tile management
│   ├── tiler/             # Tile generation
│   ├── tileproviders/     # Tile provider implementations
│   └── tilestore/         # Tile storage
├── converters/            # Image format converters
│   ├── vipsconverter.py   # VIPS-based converter
│   ├── pdfconverter.py    # PDF converter
│   └── converter.py       # Base converter class
└── windows/               # UI windows and dialogs
    └── mainwindow.py      # Main application window

test/
├── unittest/              # Unit tests (pytest)
│   ├── conftest.py        # Pytest configuration
│   ├── objects/           # Object system tests
│   ├── tilesystem/        # Tile system tests
│   ├── converters/        # Converter tests
│   └── windows/           # Window system tests
├── integrationtest/       # Integration tests
│   ├── test_*.py          # Pytest integration tests (9 files)
│   └── guiintegration/    # GUI integration test (human verification)
└── benchmarks/           # Performance benchmarks

docs/                     # Sphinx documentation
data/                     # Application data files
logs/                     # Log files (gitignored)
```

### Key Configuration Files
- `PyZui.yml` - Conda environment specification
- `pyzui_config_example.json` - Example configuration
- `.gitignore` - Git ignore patterns
- `pyzui.sh` - Application launcher script (uses PyZui-wayland)

## Development Workflow

### Setting Up Development Environment
1. Create conda environment: `conda env create -f PyZui.yml`
2. Activate environment: `conda activate PyZui-wayland`
3. Install dev dependencies: `pip install pytest pytest-cov pytest-xdist`

### Adding New Features
1. **New DynamicTileProvider**: Use template `test/unittest/test_new_dynamictileprovider_TEMPLATE.py`
2. **New Converter**: Follow patterns in `pyzui/converters/`
3. **New UI Component**: Follow patterns in `pyzui/windows/`

### Writing Tests
1. Create test file matching source structure
2. Use BDD-style docstrings (Given-When-Then)
3. Mock external dependencies
4. Test edge cases and error conditions
5. Aim for >80% coverage

### Before Committing
1. Run unit tests: `cd test/unittest && pytest`
2. Run integration tests: `cd test/integrationtest && pytest`
3. Check coverage: `pytest --cov=pyzui --cov-report=term-missing`
4. Ensure all tests pass
5. Update `CHANGELOG.md` under `[Unreleased]` with your changes
6. Update documentation if needed

## Agent-Specific Instructions

### Navigating the Codebase
- **Start with `main.py`** to understand application entry point
- **Check `pyzui/__init__.py`** for package structure and exports
- **Review test files** to understand component behavior
- **Consult documentation** in `docs/` for detailed explanations

### Finding Examples
- **Tile system**: `test/unittest/tilesystem/test_tilecache.py`
- **Object system**: `test/unittest/objects/mediaobjects/test_physicalobject.py`
- **Converters**: `test/unittest/converters/test_vipsconverter.py`
- **UI components**: `test/unittest/windows/dialogwindows/test_mainwindow.py`
- **Integration tests**: `test/integrationtest/test_tilemanager_integration.py`

### Common Patterns to Follow
1. **License headers**: Include GPL header in all new files
2. **Type hints**: Always use type annotations
3. **BDD documentation**: Use Given-When-Then format for tests
4. **Mocking**: Mock external dependencies in tests
5. **Error handling**: Use centralized logger for errors
6. **Resource management**: Clean up resources properly

### When Adding New Components
1. **Check existing patterns** in similar components
2. **Create comprehensive tests** before implementation
3. **Update `__init__.py`** exports if needed
4. **Add documentation** to relevant `.rst` files
5. **Test integration** with existing components

### Testing Guidelines for Agents
- **Always run tests** after making changes
- **Check coverage** for new code
- **Verify no regressions** in existing functionality
- **Test edge cases** and error conditions
- **Use appropriate mocks** for external dependencies

### Code Quality Checks
- **Type consistency**: Ensure type hints match usage
- **Import organization**: Follow import order guidelines
- **Documentation**: Update docstrings for new/changed functionality
- **Error messages**: Provide clear, actionable error messages
- **Resource cleanup**: Ensure proper cleanup in finally blocks

## Quick Reference

### Essential Commands
```bash
# Run application
./pyzui.sh

# Run all unit tests
cd test/unittest && pytest

# Run all integration tests
cd test/integrationtest && pytest

# Run specific test
pytest test/unittest/tilesystem/test_tile.py::TestTile::test_init_with_pil_image

# Generate coverage report
pytest --cov=pyzui --cov-report=html

# Generate documentation
cd docs && make html
```

### Key Imports for Testing
```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from pyzui.module import ClassToTest

# Common pytest features
pytest.approx()      # Floating point comparison
pytest.raises()      # Exception testing
pytest.skip()        # Skip test
pytest.fixture()     # Test fixture
```

### Common Mock Patterns
```python
# Mock object
mock = Mock()
mock.method.return_value = value

# Patch function
@patch('module.function')
def test(mock_func):
    mock_func.return_value = value

# Expect exception
with pytest.raises(ValueError):
    function(bad_input)
```

## Versioning

PyZUI uses [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH).
The single source of truth is `pyzui/__init__.py` → `__version__`.

### Version Bump Criteria

| PATCH (0.4.0 → 0.4.1) | MINOR (0.4.0 → 0.5.0) |
|---|---|
| Bug fixes | Major new features |
| Internal refactors | New capabilities |
| Type annotations and code quality | New architectures (e.g., process pools) |
| Documentation improvements | New subsystems |
| Minor UI elements and enhancements | |

**MAJOR** (0.x.y → 1.0.0): Breaking changes to config format, data file format,
or public API.

### Release Workflow

1. **Update CHANGELOG.md**: Move entries from `[Unreleased]` to a new version heading
2. **Bump version** (updates `pyzui/__init__.py` and `data/home.pzs` automatically):
   ```bash
   python scripts/bump_version.py patch    # bug fixes, refactors, docs, minor UI
   python scripts/bump_version.py minor    # major features, new capabilities, new architectures
   python scripts/bump_version.py major    # breaking changes
   ```
3. **Tag the release**:
   ```bash
   python scripts/bump_version.py minor --tag   # bumps AND creates git tag
   ```
4. **Push the tag**:
   ```bash
   git push origin vX.Y.Z
   ```

### Key Files
- `pyzui/__init__.py` — canonical version string (`__version__`)
- `CHANGELOG.md` — per-version change log (Keep a Changelog format)
- `data/home.pzs` — default scene file (version text updated automatically by bump script)
- `scripts/bump_version.py` — version bump utility
- `docs/source/conf.py` — reads version from `pyzui.__version__`

## Autosave Feature Reference

### Overview
The autosave feature provides automatic backup creation for scene files with per-scene directories, configurable interval, rotation, and expiration. Enabled by default.

### Configuration
- **Root location**: `~/.pyzui/backups/`
- **Per-scene directories**: `{scene_filename}_{4char_path_hash}/` under backup root
- **File naming**: `yy_mm_dd_hh_mm_filename_hash.pzs` (timestamp first for chronological sorting)
- **Rotation**: Keep last N backups per scene (configurable), delete oldest automatically
- **Expiration**: Scene directories expire after `expire_days` of inactivity (default: 7)
- **Enabled by default**: Autosave active from application start

### Command-Line Arguments
```bash
--autosave-interval MINUTES  # Set autosave interval in minutes (default: 5)
--autosave-max-backups COUNT # Set maximum backups to keep per scene (default: 20)
--backup-expire-days DAYS    # Days before inactive scene dirs expire (default: 7)
--no-autosave                # Disable autosave
```

### Configuration File Example
```json
{
    "autosave": {
        "enabled": true,
        "interval": 300,
        "max_backups": 20,
        "expire_days": 7
    }
}
```

### Key Components
1. **`pyzui/config.py`**: User configuration management
2. **`pyzui/backup/backupmanager.py`**: Per-scene backup creation and rotation
3. **`pyzui/objects/scene/sceneutils/autosave.py`**: Timer-based autosave orchestration
4. **`pyzui/windows/dialogwindows/autosavesettingsdialog.py`**: Settings UI (enabled by default)
5. **`pyzui/objects/scene/scene.py`**: Scene integration (enabled at startup)

### Testing
- **Config tests**: `test/unittest/test_config.py`
- **Backup tests**: `test/unittest/backup/test_backupmanager.py` (per-scene directory system)
- **Scene tests**: `test/unittest/objects/scene/test_scene_autosave.py`
- **Dialog tests**: `test/unittest/windows/dialogwindows/test_autosavesettingsdialog.py`
- **Integration tests**: `test/integrationtest/test_autosave_integration.py`

## Additional Resources
- **Full documentation**: `docs/build/html/index.html`
- **Testing guide**: `docs/build/html/_sources/testingdocumentation/unittest.rst.txt`
- **Integration test docs**: `test/integrationtest/GUI_INTEGRATION.md`
- **Claude configuration**: `.claude/claude.md`

---

*Last updated: Based on codebase analysis on March 27, 2026*