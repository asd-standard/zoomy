# Testing New Dynamic Tile Providers

This guide explains how to test new dynamic tile providers in PyZUI using the provided test template.

## Quick Info: Automatic Testing

**All `*dynamictileprovider.py` files are automatically tested!**

PyZUI includes `test_all_dynamictileproviders.py` which automatically discovers and tests all dynamic tile providers. When you create a new provider following the naming convention `*dynamictileprovider.py`, it will be automatically tested.

Run all provider tests with:
```bash
pytest test/unittest/test_all_dynamictileproviders.py -v
```

See the [Automatic Testing](#automatic-testing-for-all-providers) section below for details.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Understanding the Test Template](#understanding-the-test-template)
- [Required Tests](#required-tests)
- [Step-by-Step Implementation](#step-by-step-implementation)
- [Example: Creating Tests for MandelbrotTileProvider](#example-creating-tests-for-mandelbrottileprovider)
- [Running Tests](#running-tests)
- [Common Issues and Solutions](#common-issues-and-solutions)

---

## Overview

### What is a Dynamic Tile Provider?

A **Dynamic Tile Provider** generates or fetches tiles on-demand rather than loading them from pre-existing files. Examples include:
- Mathematical visualizations (fractals, functions)
- Procedurally generated content
- Remote tile fetching (map tiles, satellite imagery)

### Why Test?

Testing ensures your provider:
1.  Integrates correctly with PyZUI's tile system
2.  Handles edge cases (invalid coordinates, boundary conditions)
3.  Generates tiles with correct dimensions and format
4.  Follows the expected API contract

---

## Quick Start

### Step 1: Copy the Template

```bash
cd /home/asd/Projects/pyzui/test/unittest
cp test_new_dynamictileprovider_TEMPLATE.py test_yourprovider.py
```

### Step 2: Update the Template

Edit `test_yourprovider.py`:

```python
# 1. Update the import
from pyzui.tilesystem.tileproviders import YourProvider  # ← Change this

# 2. Rename the test class
class TestYourProvider:  # ← Change this

    # 3. Uncomment and update each test
    def test_init(self):
        tilecache = Mock()
        provider = YourProvider(tilecache)  # ← Change this
        assert provider is not None
```

### Step 3: Run Tests

```bash
pytest test_yourprovider.py -v
```

---

## Understanding the Test Template

The template is organized into **7 sections**:

### Section 1: Basic Initialization & Structure
Tests that your provider can be instantiated and inherits correctly.

### Section 2: Required Class Attributes
Tests for mandatory attributes that every dynamic provider must define:
- `filext`: File extension ('png', 'jpg')
- `tilesize`: Tile dimensions in pixels (typically 256)
- `aspect_ratio`: Width/height ratio (typically 1.0)

### Section 3: Provider-Specific Attributes
Tests for custom attributes specific to your implementation.

### Section 4: Boundary Condition Tests
Critical tests ensuring your provider handles invalid coordinates gracefully.

### Section 5: Valid Tile Generation
The core test verifying your provider actually generates tiles correctly.

### Section 6: Provider-Specific Logic
Custom tests for your provider's unique generation algorithm.

### Section 7: Edge Cases & Robustness
Additional tests for performance, content validation, etc.

---

## Required Tests

These tests **MUST PASS** for any dynamic tile provider:

###  1. Initialization Test

```python
def test_init(self):
    tilecache = Mock()
    provider = YourProvider(tilecache)
    assert provider is not None
```

**Why?** Ensures basic object creation works.

---

###  2. Inheritance Test

```python
def test_inherits_from_dynamictileprovider(self):
    from pyzui.tilesystem.tileproviders import DynamicTileProvider
    tilecache = Mock()
    provider = YourProvider(tilecache)
    assert isinstance(provider, DynamicTileProvider)
```

**Why?** Ensures your provider integrates with PyZUI's tile system.

---

###  3. Class Attribute Tests

```python
def test_filext_attribute(self):
    assert YourProvider.filext == 'png'

def test_tilesize_attribute(self):
    assert YourProvider.tilesize == 256

def test_aspect_ratio_attribute(self):
    assert YourProvider.aspect_ratio == 1.0
```

**Why?** These attributes are used by the tile system to correctly store and load tiles.

---

###  4. Boundary Condition Tests

```python
def test_load_dynamic_negative_row(self):
    tilecache = Mock()
    provider = YourProvider(tilecache)
    tile_id = ('media_id', 2, -1, 1)  # negative row
    outfile = '/path/to/tile.png'
    result = provider._load_dynamic(tile_id, outfile)
    assert result is None

def test_load_dynamic_negative_col(self):
    # Similar for negative column
    pass

def test_load_dynamic_out_of_range(self):
    tilecache = Mock()
    provider = YourProvider(tilecache)
    tilelevel = 2
    max_coord = 2**tilelevel - 1  # = 3
    tile_id = ('media_id', tilelevel, max_coord + 1, 0)
    result = provider._load_dynamic(tile_id, outfile)
    assert result is None
```

**Why?** Your `_load_dynamic()` method MUST validate coordinates:

```python
def _load_dynamic(self, tile_id, outfile):
    media_id, tilelevel, row, col = tile_id

    # REQUIRED: Validate coordinates
    if row < 0 or col < 0 or \
       row > 2**tilelevel - 1 or col > 2**tilelevel - 1:
        return  # Invalid coordinates

    # ... generate tile ...
```

---

### 5. Valid Tile Generation Test

```python
@patch('PIL.Image.new')
def test_load_dynamic_valid_tile(self, mock_image_new):
    tilecache = Mock()
    provider = YourProvider(tilecache)

    mock_image = Mock()
    mock_image_new.return_value = mock_image

    tile_id = ('media_id', 2, 1, 1)
    outfile = '/path/to/tile.png'

    provider._load_dynamic(tile_id, outfile)

    # Verify image created with correct size
    mock_image_new.assert_called_once_with('RGB', (256, 256))

    # Verify image was saved
    mock_image.save.assert_called_once_with(outfile)
```

**Why?** This is the **core functionality** - your provider must create and save tiles.

---

## Step-by-Step Implementation

### Step 1: Create Your Provider Class

```python
# pyzui/tilesystem/tileproviders/mandelbrottileprovider.py

from PIL import Image
from .dynamictileprovider import DynamicTileProvider

class MandelbrotTileProvider(DynamicTileProvider):
    filext = 'png'
    tilesize = 256
    aspect_ratio = 1.0
    max_iterations = 100

    def _load_dynamic(self, tile_id, outfile):
        media_id, tilelevel, row, col = tile_id

        # Validate coordinates
        if row < 0 or col < 0 or \
           row > 2**tilelevel - 1 or col > 2**tilelevel - 1:
            return

        # Generate Mandelbrot tile
        tile = Image.new('RGB', (self.tilesize, self.tilesize))
        # ... mandelbrot generation logic ...
        tile.save(outfile)
```

### Step 2: Create Test File from Template

```bash
cp test_new_dynamictileprovider_TEMPLATE.py test_mandelbrottileprovider.py
```

### Step 3: Update Imports and Class Names

```python
# test_mandelbrottileprovider.py

from pyzui.tilesystem.tileproviders import MandelbrotTileProvider

class TestMandelbrotTileProvider:
    # ... tests ...
```

### Step 4: Customize Attribute Tests

```python
def test_max_iterations_attribute(self):
    """Test max_iterations attribute."""
    tilecache = Mock()
    provider = MandelbrotTileProvider(tilecache)
    assert provider.max_iterations == 100
```

### Step 5: Uncomment and Update All Required Tests

Go through sections 1-5 and uncomment/update all tests.

### Step 6: Run Tests

```bash
pytest test_mandelbrottileprovider.py -v
```

---

## Example: Creating Tests for MandelbrotTileProvider

Here's a complete minimal example:

```python
import pytest
from unittest.mock import Mock, patch
from pyzui.tilesystem.tileproviders import MandelbrotTileProvider

class TestMandelbrotTileProvider:

    def test_init(self):
        tilecache = Mock()
        provider = MandelbrotTileProvider(tilecache)
        assert provider is not None

    def test_inherits_from_dynamictileprovider(self):
        from pyzui.tilesystem.tileproviders import DynamicTileProvider
        tilecache = Mock()
        provider = MandelbrotTileProvider(tilecache)
        assert isinstance(provider, DynamicTileProvider)

    def test_filext_attribute(self):
        assert MandelbrotTileProvider.filext == 'png'

    def test_tilesize_attribute(self):
        assert MandelbrotTileProvider.tilesize == 256

    def test_aspect_ratio_attribute(self):
        assert MandelbrotTileProvider.aspect_ratio == 1.0

    def test_max_iterations_attribute(self):
        tilecache = Mock()
        provider = MandelbrotTileProvider(tilecache)
        assert provider.max_iterations == 100

    def test_load_dynamic_negative_row(self):
        tilecache = Mock()
        provider = MandelbrotTileProvider(tilecache)
        tile_id = ('mandelbrot', 2, -1, 1)
        result = provider._load_dynamic(tile_id, '/tmp/tile.png')
        assert result is None

    def test_load_dynamic_negative_col(self):
        tilecache = Mock()
        provider = MandelbrotTileProvider(tilecache)
        tile_id = ('mandelbrot', 2, 1, -1)
        result = provider._load_dynamic(tile_id, '/tmp/tile.png')
        assert result is None

    def test_load_dynamic_out_of_range(self):
        tilecache = Mock()
        provider = MandelbrotTileProvider(tilecache)
        tile_id = ('mandelbrot', 2, 10, 10)
        result = provider._load_dynamic(tile_id, '/tmp/tile.png')
        assert result is None

    @patch('pyzui.tilesystem.tileproviders.mandelbrottileprovider.Image.new')
    def test_load_dynamic_valid_tile(self, mock_image_new):
        tilecache = Mock()
        provider = MandelbrotTileProvider(tilecache)

        mock_image = Mock()
        mock_image_new.return_value = mock_image

        tile_id = ('mandelbrot', 2, 1, 1)
        outfile = '/tmp/tile.png'

        provider._load_dynamic(tile_id, outfile)

        mock_image_new.assert_called_once_with('RGB', (256, 256))
        mock_image.save.assert_called_once_with(outfile)
```

---

## Running Tests

### Run All Tests

```bash
cd /home/asd/Projects/pyzui
pytest test/unittest/test_yourprovider.py -v
```

### Run Specific Test

```bash
pytest test/unittest/test_yourprovider.py::TestYourProvider::test_init -v
```

### Run with Coverage

```bash
pytest test/unittest/test_yourprovider.py --cov=pyzui.tilesystem.tileproviders --cov-report=html
```

### Run with Debugging Output

```bash
pytest test/unittest/test_yourprovider.py -v -s
```

### Stop on First Failure

```bash
pytest test/unittest/test_yourprovider.py -x
```

---

## Common Issues and Solutions

### Issue 1: Import Error

**Error:**
```
ModuleNotFoundError: No module named 'pyzui.tilesystem.tileproviders.yourprovider'
```

**Solution:**
1. Ensure your provider file exists in the correct location
2. Add it to `__init__.py`:

```python
# pyzui/tilesystem/tileproviders/__init__.py
from .yourprovider import YourProvider
```

---

### Issue 2: Mock Patch Path Wrong

**Error:**
```
AttributeError: <module 'pyzui.tileproviders'> does not have the attribute 'Image'
```

**Solution:**
Update the patch path to where `Image` is imported **in your provider file**:

```python
# If your provider has: from PIL import Image
@patch('pyzui.tilesystem.tileproviders.yourprovider.Image.new')
```

---

### Issue 3: Boundary Tests Failing

**Error:**
```
AssertionError: assert <some value> is None
```

**Solution:**
Your `_load_dynamic()` must explicitly return `None` or just `return`:

```python
def _load_dynamic(self, tile_id, outfile):
    media_id, tilelevel, row, col = tile_id

    # MUST validate and return early
    if row < 0 or col < 0 or \
       row > 2**tilelevel - 1 or col > 2**tilelevel - 1:
        return  # This returns None implicitly
```

---

### Issue 4: Save Method Not Called

**Error:**
```
AssertionError: Expected 'save' to be called once. Called 0 times.
```

**Solution:**
Ensure your `_load_dynamic()` actually calls `save()`:

```python
def _load_dynamic(self, tile_id, outfile):
    # ... validation ...
    tile = Image.new('RGB', (self.tilesize, self.tilesize))
    # ... generation ...
    tile.save(outfile)  # ← REQUIRED
```

---

## Understanding Tile Coordinates

### Tile ID Format

```python
tile_id = (media_id, tilelevel, row, col)
```

- **media_id** (str): Unique identifier for your tile source
- **tilelevel** (int): Zoom level (0 = zoomed out, higher = zoomed in)
- **row** (int): Vertical tile index
- **col** (int): Horizontal tile index

### Valid Coordinate Ranges

For a given `tilelevel`, valid coordinates are:

```
0 ≤ row ≤ 2^tilelevel - 1
0 ≤ col ≤ 2^tilelevel - 1
```

**Examples:**

| tilelevel | Valid range | Total tiles |
|-----------|-------------|-------------|
| 0         | 0 to 0      | 1×1 = 1     |
| 1         | 0 to 1      | 2×2 = 4     |
| 2         | 0 to 3      | 4×4 = 16    |
| 3         | 0 to 7      | 8×8 = 64    |

---

## Best Practices

###  DO:

1. **Always validate coordinates** in `_load_dynamic()`
2. **Use class attributes** for configuration (filext, tilesize, etc.)
3. **Test multiple zoom levels** to ensure scaling works
4. **Mock external dependencies** (file I/O, network requests)
5. **Add provider-specific tests** for unique algorithms

###  DON'T:

1. **Don't skip boundary tests** - they prevent crashes
2. **Don't hardcode paths** - use the provided `outfile` parameter
3. **Don't forget to save** - tiles must be written to disk
4. **Don't assume coordinates are valid** - always validate
5. **Don't test actual file I/O** - use mocks instead

---

## Reference: FernTileProvider Test Suite

See the complete working example:
- **Provider**: `pyzui/tilesystem/tileproviders/ferntileprovider.py`
- **Tests**: `test/unittest/test_ferntileprovider.py`

The FernTileProvider is a fully-tested dynamic provider that generates Barnsley's fern fractal. Use it as a reference implementation.

---

## Support and Contributing

### Questions?

1. Review the template comments (they contain detailed explanations)
2. Check the FernTileProvider implementation
3. Read the DynamicTileProvider base class

### Found a Bug in the Template?

Please report issues or suggest improvements!

---

## Automatic Testing for All Providers

### The `test_all_dynamictileproviders.py` File

PyZUI includes an **automatic test discovery system** that finds and tests all dynamic tile providers:

**Location:** `test/unittest/test_all_dynamictileproviders.py`

This test file:
1.  **Automatically discovers** all `*dynamictileprovider.py` files
2.  **Runs standard tests** on each discovered provider
3.  **Ensures consistency** across all providers
4.  **No configuration needed** - just follow the naming convention

### How It Works

```python
# Discovery happens automatically at module load time
DISCOVERED_PROVIDERS = discover_dynamic_providers()

# Each test runs for all discovered providers using pytest parametrization
@pytest.mark.parametrize("provider_name,provider_class", PROVIDER_PARAMS)
def test_provider_initialization(self, provider_name, provider_class):
    tilecache = Mock()
    provider = provider_class(tilecache)
    assert provider is not None
```

### Running Automatic Tests

**Test all providers:**
```bash
pytest test/unittest/test_all_dynamictileproviders.py -v
```

**Test a specific provider:**
```bash
pytest test/unittest/test_all_dynamictileproviders.py -v -k "FernTileProvider"
```

**Test specific functionality:**
```bash
pytest test/unittest/test_all_dynamictileproviders.py -v -k "boundary"
```

**See what providers were discovered:**
```bash
pytest test/unittest/test_all_dynamictileproviders.py::TestProviderDiscovery -v
```

### What Gets Tested Automatically

For **EACH** discovered provider, the automatic test suite verifies:

-  Initialization with tilecache
-  Inherits from DynamicTileProvider
-  Has required attributes (filext, tilesize, aspect_ratio)
-  Handles negative row coordinates
-  Handles negative col coordinates
-  Handles row out of valid range
-  Handles col out of valid range
-  Handles both coords out of range
-  Generates and saves valid tiles

### Naming Convention Requirement

**Your provider file MUST be named:** `*dynamictileprovider.py`

**Examples:**
- ✅ `ferndynamictileprovider.py` - Will be discovered
- ✅ `mandeltileprovider.py` - Will be discovered (contains 'tileprovider')
- ❌ `myprovider.py` - Won't be discovered
- ❌ `customtiles.py` - Won't be discovered

### When to Use the Template

Use `test_new_dynamictileprovider_TEMPLATE.py` when you need:

1. **Provider-specific tests** beyond the standard suite
2. **Custom test configuration** for unique behavior
3. **Additional validation** for complex algorithms
4. **Integration tests** with specific data

The template and automatic testing **work together**:
- Automatic tests verify basic compliance with the DynamicTileProvider contract
- Custom tests verify provider-specific behavior and edge cases

---

## Summary Checklist

Before using your new provider in production:

- [ ] File named `*dynamictileprovider.py`
- [ ] Class inherits from `DynamicTileProvider`
- [ ] Defines required attributes: `filext`, `tilesize`, `aspect_ratio`
- [ ] Implements `_load_dynamic()` with coordinate validation
- [ ] Run automatic tests: `pytest test/unittest/test_all_dynamictileproviders.py -v -k "YourProvider"`
- [ ] All automatic tests pass
- [ ] Create custom tests if needed (use template)
- [ ] Test integration with actual PyZUI application
- [ ] Document provider-specific configuration in docstrings

**Your provider is ready when all tests pass! 🎉**
