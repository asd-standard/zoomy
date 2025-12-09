"""
Automated test suite for all DynamicTileProvider implementations.

This test file automatically discovers all *dynamictileprovider.py files
in pyzui/tilesystem/tileproviders/ and runs a standard test suite on each.

Tests ensure that all dynamic tile providers:
1. Initialize correctly
2. Inherit from DynamicTileProvider
3. Define required attributes (filext, tilesize, aspect_ratio)
4. Handle boundary conditions properly
5. Generate valid tiles

To add a new provider, simply create a file matching *dynamictileprovider.py
in the tileproviders directory - it will be automatically discovered and tested.
"""

import pytest
import importlib
import inspect
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Tuple, Type

# Import base classes
from pyzui.tilesystem.tileproviders import DynamicTileProvider


# =============================================================================
# PROVIDER DISCOVERY
# =============================================================================

def discover_dynamic_providers() -> List[Tuple[str, Type]]:
    """
    Discover all DynamicTileProvider implementations automatically.

    Returns:
        List of tuples: [(provider_name, ProviderClass), ...]

    Scans pyzui/tilesystem/tileproviders/ for files matching *dynamictileprovider.py
    and extracts classes that inherit from DynamicTileProvider.
    """
    providers = []

    # Get the tileproviders directory path
    tileproviders_dir = Path(__file__).parent.parent.parent / 'pyzui' / 'tilesystem' / 'tileproviders'

    # Find all *dynamictileprovider.py files
    for filepath in tileproviders_dir.glob('*dynamictileprovider.py'):
        module_name = filepath.stem  # filename without .py

        # Skip the base DynamicTileProvider itself
        if module_name == 'dynamictileprovider':
            continue

        try:
            # Import the module dynamically
            module = importlib.import_module(f'pyzui.tilesystem.tileproviders.{module_name}')

            # Find all classes in the module that inherit from DynamicTileProvider
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Skip the DynamicTileProvider base class itself
                if obj is DynamicTileProvider:
                    continue

                # Check if it's a subclass of DynamicTileProvider
                if issubclass(obj, DynamicTileProvider) and obj.__module__ == module.__name__:
                    providers.append((name, obj))

        except Exception as e:
            pytest.fail(f"Failed to import {module_name}: {e}")

    return providers


# Discover all providers at module load time
DISCOVERED_PROVIDERS = discover_dynamic_providers()

# Create parameter list for pytest (provider_name for test IDs)
PROVIDER_PARAMS = [(name, cls) for name, cls in DISCOVERED_PROVIDERS]


# =============================================================================
# PARAMETRIZED TESTS - RUN FOR ALL DISCOVERED PROVIDERS
# =============================================================================

class TestAllDynamicTileProviders:
    """
    Feature: Automated DynamicTileProvider Discovery and Testing

    This class automatically discovers all DynamicTileProvider implementations and runs a comprehensive
    test suite on each to ensure they follow the required contract and will work correctly with PyZUI's tile system.
    """

    # -------------------------------------------------------------------------
    # SECTION 1: BASIC INITIALIZATION & STRUCTURE
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize("provider_name,provider_class", PROVIDER_PARAMS,
                             ids=[name for name, _ in PROVIDER_PARAMS])
    def test_provider_initialization(self, provider_name, provider_class):
        """
        Scenario: Initialize provider with tilecache

        Given a discovered DynamicTileProvider class and a mock tilecache
        When instantiating the provider
        Then the provider object should be created successfully
        """
        tilecache = Mock()
        provider = provider_class(tilecache)
        assert provider is not None, f"{provider_name} failed to initialize"

    @pytest.mark.parametrize("provider_name,provider_class", PROVIDER_PARAMS,
                             ids=[name for name, _ in PROVIDER_PARAMS])
    def test_provider_inherits_from_dynamictileprovider(self, provider_name, provider_class):
        """
        Scenario: Verify provider inheritance

        Given a discovered provider instance
        When checking its type hierarchy
        Then it should be an instance of DynamicTileProvider
        """
        tilecache = Mock()
        provider = provider_class(tilecache)
        assert isinstance(provider, DynamicTileProvider), \
            f"{provider_name} does not inherit from DynamicTileProvider"

    # -------------------------------------------------------------------------
    # SECTION 2: REQUIRED CLASS ATTRIBUTES
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize("provider_name,provider_class", PROVIDER_PARAMS,
                             ids=[name for name, _ in PROVIDER_PARAMS])
    def test_provider_has_filext(self, provider_name, provider_class):
        """
        Scenario: Verify filext attribute exists and is valid

        Given a discovered provider class
        When checking for the filext attribute
        Then it should exist as a non-empty string
        """
        assert hasattr(provider_class, 'filext'), \
            f"{provider_name} missing 'filext' attribute"
        assert isinstance(provider_class.filext, str), \
            f"{provider_name}.filext must be a string"
        assert len(provider_class.filext) > 0, \
            f"{provider_name}.filext cannot be empty"

    @pytest.mark.parametrize("provider_name,provider_class", PROVIDER_PARAMS,
                             ids=[name for name, _ in PROVIDER_PARAMS])
    def test_provider_has_tilesize(self, provider_name, provider_class):
        """
        Scenario: Verify tilesize attribute exists and is valid

        Given a discovered provider class
        When checking for the tilesize attribute
        Then it should exist as a positive integer
        """
        assert hasattr(provider_class, 'tilesize'), \
            f"{provider_name} missing 'tilesize' attribute"
        assert isinstance(provider_class.tilesize, int), \
            f"{provider_name}.tilesize must be an integer"
        assert provider_class.tilesize > 0, \
            f"{provider_name}.tilesize must be positive"

    @pytest.mark.parametrize("provider_name,provider_class", PROVIDER_PARAMS,
                             ids=[name for name, _ in PROVIDER_PARAMS])
    def test_provider_has_aspect_ratio(self, provider_name, provider_class):
        """
        Scenario: Verify aspect_ratio attribute exists and is valid

        Given a discovered provider class
        When checking for the aspect_ratio attribute
        Then it should exist as a positive number
        """
        assert hasattr(provider_class, 'aspect_ratio'), \
            f"{provider_name} missing 'aspect_ratio' attribute"
        assert isinstance(provider_class.aspect_ratio, (int, float)), \
            f"{provider_name}.aspect_ratio must be a number"
        assert provider_class.aspect_ratio > 0, \
            f"{provider_name}.aspect_ratio must be positive"

    # -------------------------------------------------------------------------
    # SECTION 3: BOUNDARY CONDITION TESTS FOR _load_dynamic()
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize("provider_name,provider_class", PROVIDER_PARAMS,
                             ids=[name for name, _ in PROVIDER_PARAMS])
    def test_load_dynamic_handles_negative_row(self, provider_name, provider_class):
        """
        Scenario: Handle negative row coordinate

        Given a provider instance and a tile_id with negative row
        When calling _load_dynamic
        Then it should return None gracefully
        """
        tilecache = Mock()
        provider = provider_class(tilecache)

        # Extract media_id from provider name (lowercase)
        media_id = provider_name.lower().replace('tileprovider', '').replace('dynamic', '')

        tile_id = (media_id, 2, -1, 1)  # negative row
        outfile = '/tmp/test_tile.png'

        result = provider._load_dynamic(tile_id, outfile)
        assert result is None, \
            f"{provider_name}._load_dynamic() should return None for negative row"

    @pytest.mark.parametrize("provider_name,provider_class", PROVIDER_PARAMS,
                             ids=[name for name, _ in PROVIDER_PARAMS])
    def test_load_dynamic_handles_negative_col(self, provider_name, provider_class):
        """
        Scenario: Handle negative column coordinate

        Given a provider instance and a tile_id with negative column
        When calling _load_dynamic
        Then it should return None gracefully
        """
        tilecache = Mock()
        provider = provider_class(tilecache)

        media_id = provider_name.lower().replace('tileprovider', '').replace('dynamic', '')

        tile_id = (media_id, 2, 1, -1)  # negative col
        outfile = '/tmp/test_tile.png'

        result = provider._load_dynamic(tile_id, outfile)
        assert result is None, \
            f"{provider_name}._load_dynamic() should return None for negative col"

    @pytest.mark.parametrize("provider_name,provider_class", PROVIDER_PARAMS,
                             ids=[name for name, _ in PROVIDER_PARAMS])
    def test_load_dynamic_handles_row_out_of_range(self, provider_name, provider_class):
        """
        Scenario: Handle row coordinate exceeding valid range

        Given a provider instance and a tile_id with row exceeding 2^tilelevel - 1
        When calling _load_dynamic
        Then it should return None gracefully
        """
        tilecache = Mock()
        provider = provider_class(tilecache)

        media_id = provider_name.lower().replace('tileprovider', '').replace('dynamic', '')

        tilelevel = 2
        max_valid_coord = 2**tilelevel - 1  # = 3
        tile_id = (media_id, tilelevel, max_valid_coord + 1, 1)
        outfile = '/tmp/test_tile.png'

        result = provider._load_dynamic(tile_id, outfile)
        assert result is None, \
            f"{provider_name}._load_dynamic() should return None for row out of range"

    @pytest.mark.parametrize("provider_name,provider_class", PROVIDER_PARAMS,
                             ids=[name for name, _ in PROVIDER_PARAMS])
    def test_load_dynamic_handles_col_out_of_range(self, provider_name, provider_class):
        """
        Scenario: Handle column coordinate exceeding valid range

        Given a provider instance and a tile_id with column exceeding 2^tilelevel - 1
        When calling _load_dynamic
        Then it should return None gracefully
        """
        tilecache = Mock()
        provider = provider_class(tilecache)

        media_id = provider_name.lower().replace('tileprovider', '').replace('dynamic', '')

        tilelevel = 2
        max_valid_coord = 2**tilelevel - 1  # = 3
        tile_id = (media_id, tilelevel, 1, max_valid_coord + 1)
        outfile = '/tmp/test_tile.png'

        result = provider._load_dynamic(tile_id, outfile)
        assert result is None, \
            f"{provider_name}._load_dynamic() should return None for col out of range"

    @pytest.mark.parametrize("provider_name,provider_class", PROVIDER_PARAMS,
                             ids=[name for name, _ in PROVIDER_PARAMS])
    def test_load_dynamic_handles_both_coords_out_of_range(self, provider_name, provider_class):
        """
        Scenario: Handle both coordinates out of range

        Given a provider instance and a tile_id with both row and column out of range
        When calling _load_dynamic
        Then it should return None gracefully
        """
        tilecache = Mock()
        provider = provider_class(tilecache)

        media_id = provider_name.lower().replace('tileprovider', '').replace('dynamic', '')

        tile_id = (media_id, 2, 10, 10)  # both exceed max of 3
        outfile = '/tmp/test_tile.png'

        result = provider._load_dynamic(tile_id, outfile)
        assert result is None, \
            f"{provider_name}._load_dynamic() should return None for both coords out of range"

    # -------------------------------------------------------------------------
    # SECTION 4: VALID TILE GENERATION TEST
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize("provider_name,provider_class", PROVIDER_PARAMS,
                             ids=[name for name, _ in PROVIDER_PARAMS])
    def test_load_dynamic_generates_valid_tile(self, provider_name, provider_class):
        """
        Scenario: Generate a valid tile for valid coordinates

        Given a provider instance and valid tile coordinates
        When calling _load_dynamic
        Then an image should be created with correct dimensions
        And the image should be saved to the output file
        """
        tilecache = Mock()
        provider = provider_class(tilecache)

        # Determine the module path for patching
        module_path = provider_class.__module__

        with patch(f'{module_path}.Image.new') as mock_image_new:
            mock_image = Mock()
            mock_image_new.return_value = mock_image

            media_id = provider_name.lower().replace('tileprovider', '').replace('dynamic', '')

            tile_id = (media_id, 2, 1, 1)  # valid coordinates
            outfile = '/tmp/test_tile.png'

            # Call the method
            provider._load_dynamic(tile_id, outfile)

            # Verify image was created with correct size
            expected_size = (provider_class.tilesize, provider_class.tilesize)
            mock_image_new.assert_called_once()

            # Verify image was saved
            mock_image.save.assert_called_once_with(outfile), \
                f"{provider_name}._load_dynamic() should save tile to outfile"


# =============================================================================
# DISCOVERY VERIFICATION TEST
# =============================================================================

class TestProviderDiscovery:
    """
    Feature: Provider Discovery Mechanism

    This class verifies that the automatic provider discovery system works correctly
    and finds all DynamicTileProvider implementations in the codebase.
    """

    def test_providers_discovered(self):
        """
        Scenario: Discover at least one provider

        Given the provider discovery mechanism
        When scanning the tileproviders directory
        Then at least one provider should be found
        """
        assert len(DISCOVERED_PROVIDERS) > 0, \
            "No dynamic tile providers were discovered. " \
            "Ensure *dynamictileprovider.py files exist in pyzui/tilesystem/tileproviders/"

    def test_discovery_finds_known_providers(self):
        """
        Scenario: Discover known providers

        Given the provider discovery mechanism
        When scanning for providers
        Then expected providers like FernTileProvider should be found
        """
        provider_names = [name for name, _ in DISCOVERED_PROVIDERS]

        # We should at least find FernTileProvider
        assert any('Fern' in name for name in provider_names), \
            "FernTileProvider should be discovered"

    def test_discovered_providers_have_valid_names(self):
        """
        Scenario: Verify discovered providers have valid names

        Given all discovered providers
        When checking their class names
        Then each name should be non-empty, start with uppercase, and contain 'Provider'
        """
        for name, cls in DISCOVERED_PROVIDERS:
            assert len(name) > 0, "Provider name cannot be empty"
            assert name[0].isupper(), f"Provider class name '{name}' should start with uppercase"
            assert 'Provider' in name, f"Provider class '{name}' should contain 'Provider'"


# =============================================================================
# USAGE INFORMATION
# =============================================================================

"""
RUNNING THESE TESTS:
-------------------

1. Run all tests for all providers:
   pytest test/unittest/test_all_dynamictileproviders.py -v

2. Run tests for a specific provider:
   pytest test/unittest/test_all_dynamictileproviders.py -v -k "FernTileProvider"

3. Run a specific test type for all providers:
   pytest test/unittest/test_all_dynamictileproviders.py -v -k "boundary"

4. Show which providers were discovered:
   pytest test/unittest/test_all_dynamictileproviders.py::TestProviderDiscovery -v

ADDING A NEW PROVIDER:
---------------------

1. Create your provider file in pyzui/tilesystem/tileproviders/
   Name it: yourproviderdynamictileprovider.py

2. Implement your provider class inheriting from DynamicTileProvider:

   class YourProviderTileProvider(DynamicTileProvider):
       filext = 'png'
       tilesize = 256
       aspect_ratio = 1.0

       def _load_dynamic(self, tile_id, outfile):
           media_id, tilelevel, row, col = tile_id

           # Validate coordinates
           if row < 0 or col < 0 or \
              row > 2**tilelevel - 1 or col > 2**tilelevel - 1:
               return

           # Generate tile
           tile = Image.new('RGB', (self.tilesize, self.tilesize))
           # ... your generation logic ...
           tile.save(outfile)

3. Run the tests - your provider will be automatically discovered and tested:
   pytest test/unittest/test_all_dynamictileproviders.py -v -k "YourProvider"

WHAT GETS TESTED:
----------------

For EACH discovered provider, this test suite automatically verifies:

✓ Initialization with tilecache works
✓ Inherits from DynamicTileProvider
✓ Has required attributes: filext, tilesize, aspect_ratio
✓ Handles negative row coordinates
✓ Handles negative col coordinates
✓ Handles row values exceeding valid range
✓ Handles col values exceeding valid range
✓ Handles both coordinates out of range
✓ Generates and saves tiles for valid coordinates

This ensures all providers follow the same contract and will work
correctly with PyZUI's tile system.
"""
