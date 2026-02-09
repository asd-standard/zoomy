.. Integration Testing Documentation

Integration Testing Guide
==========================

This document provides a comprehensive guide to integration testing PyZUI during development,
covering end-to-end pipeline testing, thread safety validation, component interaction testing,
and full GUI integration verification. Integration tests validate that components work correctly
together as a complete system.

Overview
--------

The PyZUI integration test suite is designed to:

1. Validate complete workflows from input to output
2. Test component interactions and interfaces
3. Verify thread safety and concurrent access patterns
4. Ensure cache-provider coordination works correctly
5. Test the full application with real user interactions
6. Catch integration bugs that unit tests might miss

**Test Framework**: pytest with custom fixtures

**Test Types**:
- **Pipeline Tests**: End-to-end tiling workflows
- **Concurrency Tests**: Thread safety and race conditions
- **Integration Tests**: Component interaction validation
- **GUI Tests**: Full application visual verification

**Key Difference from Unit Tests**:
Integration tests use **real dependencies** (actual images, real disk I/O, threading)
rather than mocks, validating the complete system behavior.

Test Suite Structure
--------------------

Directory Organization
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    test/integrationtest/
    ├── test_tiling_pipeline.py          # End-to-end tiling tests
    ├── test_converter_pipeline.py       # Converter to tiler pipeline tests
    ├── test_concurrent_access.py        # Thread safety tests
    ├── test_cache_provider_integration.py  # Cache-provider interaction
    ├── test_tilemanager_integration.py  # TileManager coordination
    ├── gui_integration.py               # Visual GUI testing (manual)
    ├── GUI_INTEGRATION.md               # GUI test documentation
    └── logs/                            # Test execution logs
        └── pyzui.log

Test Categories
~~~~~~~~~~~~~~~

**1. Tiling Pipeline Tests** (``test_tiling_pipeline.py``)

- Complete image-to-tiles workflow
- Pyramid structure verification
- Tile retrieval and caching
- Multiple image handling
- Error handling in pipeline

**2. Converter Pipeline Tests** (``test_converter_pipeline.py``)

- VipsConverter image format conversion (PNG, JPG, TIFF to PPM)
- PDFConverter PDF rasterization
- Converter to Tiler pipeline integration
- Progress tracking during conversion
- Error handling for invalid/corrupted files
- Process-based parallel conversion via ``converterrunner``
- Output format validation

**3. Concurrent Access Tests** (``test_concurrent_access.py``)

- Thread-safe tile requests
- Concurrent tiling operations
- Cache thread safety
- Provider queue concurrency
- Race condition prevention

**4. Cache-Provider Integration** (``test_cache_provider_integration.py``)

- Provider-cache interaction
- Cache hit prevention of redundant loads
- Eviction and reload behavior
- Multi-provider cache sharing
- Request queue processing

**5. TileManager Coordination** (``test_tilemanager_integration.py``)

- Request routing (static vs dynamic)
- Tile synthesis and fallback
- Metadata access coordination
- Negative tile level handling
- Dual-cache management

**6. GUI Integration** (``gui_integration.py``)

- Full application workflow
- All user interactions
- Visual verification by human
- Menu operations
- Mouse and keyboard input

Running Integration Tests
--------------------------

Basic Usage
~~~~~~~~~~~

**Run all integration tests:**

.. code-block:: bash

    cd test/integrationtest
    pytest

**Run specific test file:**

.. code-block:: bash

    pytest test_tiling_pipeline.py

**Run with verbose output:**

.. code-block:: bash

    pytest -v

**Run specific test class:**

.. code-block:: bash

    pytest test_tiling_pipeline.py::TestTilingPipelineEndToEnd

**Run specific test:**

.. code-block:: bash

    pytest test_tiling_pipeline.py::TestTilingPipelineEndToEnd::test_tile_image_creates_pyramid_structure

**Run converter pipeline tests:**

.. code-block:: bash

    # All converter tests (27 tests)
    pytest test_converter_pipeline.py -v

Integration Test Options
~~~~~~~~~~~~~~~~~~~~~~~~~

**Show detailed output:**

.. code-block:: bash

    pytest -v -s

**Stop on first failure:**

.. code-block:: bash

    pytest -x

**Run with coverage:**

.. code-block:: bash

    pytest --cov=pyzui --cov-report=term

**Parallel execution (use with caution):**

.. code-block:: bash

    # Integration tests may have shared state
    # Only use if tests are truly independent
    pytest -n auto

**Logging:**

Integration tests produce detailed logs. View them with:

.. code-block:: bash

    tail -f logs/pyzui.log

GUI Integration Tests
~~~~~~~~~~~~~~~~~~~~~

GUI tests run separately and require visual verification:

**Run all GUI tests:**

.. code-block:: bash

    python gui_integration.py

**Start from specific step:**

.. code-block:: bash

    python gui_integration.py --start-step 30

**List available test steps:**

.. code-block:: bash

    python gui_integration.py --list-steps

Common Fixtures
---------------

Test fixtures provide isolated environments and test resources.

temp_tilestore Fixture
~~~~~~~~~~~~~~~~~~~~~~

Provides isolated temporary tile storage:

.. code-block:: python

    @pytest.fixture
    def temp_tilestore(tmp_path):
        """
        Fixture: Isolated Tile Storage

        Provides a temporary directory for tile storage,
        ensuring test isolation.

        Yields:
            str: Path to temporary tilestore directory.
        """
        from pyzui.tilesystem.tilestore import tilestore as ts_module

        original_tile_dir = ts_module.tile_dir
        temp_dir = str(tmp_path / "tilestore")
        os.makedirs(temp_dir, exist_ok=True)

        # Patch tilestore directory
        ts_module.tile_dir = temp_dir
        tilestore.tile_dir = temp_dir

        yield temp_dir

        # Restore and cleanup
        ts_module.tile_dir = original_tile_dir
        tilestore.tile_dir = original_tile_dir
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

**Why This Matters:**

- Prevents tests from polluting system tilestore
- Ensures each test starts with clean slate
- Allows parallel test execution
- Automatic cleanup after tests

sample_images Fixture
~~~~~~~~~~~~~~~~~~~~~

Creates test images of various sizes:

.. code-block:: python

    @pytest.fixture
    def sample_images(tmp_path):
        """
        Fixture: Sample Test Images

        Creates test images of various sizes for testing
        different tiling scenarios.

        Yields:
            dict: Mapping of (width, height) to file path.
        """
        images = {}
        test_cases = [
            (256, 256, 'red'),     # Single tile
            (512, 512, 'green'),   # 2x2 grid
            (500, 300, 'blue'),    # Non-power-of-two
            (100, 100, 'yellow'),  # Smaller than tile size
            (1024, 1024, 'purple'), # Larger pyramid
        ]

        for width, height, color in test_cases:
            img = Image.new('RGB', (width, height), color=color)
            # Add gradient pattern for visual verification
            for y in range(height):
                for x in range(min(10, width)):
                    img.putpixel((x, y), (x * 25, y % 256, 128))

            path = tmp_path / f"test_{width}x{height}.png"
            img.save(path)
            images[(width, height)] = str(path)

        yield images

        # Cleanup
        for path in images.values():
            if os.path.exists(path):
                os.remove(path)

**Test Images Provided:**

- **256x256**: Exactly one tile (boundary test)
- **512x512**: 2x2 tile grid (standard pyramid)
- **500x300**: Non-power-of-two dimensions
- **100x100**: Smaller than tile size
- **1024x1024**: Multi-level pyramid (3 levels)

initialized_tilemanager Fixture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Initializes TileManager with test settings:

.. code-block:: python

    @pytest.fixture
    def initialized_tilemanager(temp_tilestore):
        """
        Fixture: Initialized TileManager

        Sets up TileManager with test-appropriate settings
        and ensures cleanup after test.

        Yields:
            None (TileManager is module with global state)
        """
        tilemanager.init(total_cache_size=100, auto_cleanup=False)
        yield
        tilemanager.purge()

**Configuration:**

- Cache size: 100 tiles (small for testing)
- Auto-cleanup: Disabled (manual control)
- Providers: Static and all registered dynamic providers

cache Fixture
~~~~~~~~~~~~~

Provides fresh TileCache instance:

.. code-block:: python

    @pytest.fixture
    def cache():
        """
        Fixture: Fresh TileCache

        Provides isolated TileCache with reasonable defaults.

        Yields:
            TileCache: A fresh cache instance.
        """
        return TileCache(maxsize=100, maxage=3600)

Tiling Pipeline Tests
---------------------

End-to-End Workflow Testing
~~~~~~~~~~~~~~~~~~~~~~~~~~~

These tests validate the complete tiling pipeline from image input to tile retrieval.

**Test Pattern:**

.. code-block:: python

    class TestTilingPipelineEndToEnd:
        """
        Feature: Complete Tiling Pipeline

        The tiling system converts large images into pyramidal
        tile structures for efficient zooming and panning.
        """

        def test_tile_image_creates_pyramid_structure(
                self, temp_tilestore, sample_images):
            """
            Scenario: Tiling creates complete tile pyramid

            Given a 512x512 pixel image
            When the Tiler processes the image
            Then tiles are created at multiple pyramid levels
            And all tiles are stored in TileStore
            """
            image_path = sample_images[(512, 512)]
            media_id = "test_512x512"

            # When: Process the image
            tiler = ConcreteTiler(image_path, media_id=media_id)
            tiler.run()

            # Then: Verify completion
            assert tiler.error is None
            assert tiler.progress == 1.0

            # And: Verify pyramid structure
            # Level 0: 1 tile (overview)
            assert os.path.exists(
                tilestore.get_tile_path((media_id, 0, 0, 0), filext='jpg'))

            # Level 1: 2x2 = 4 tiles (full resolution)
            for row in range(2):
                for col in range(2):
                    tile_path = tilestore.get_tile_path(
                        (media_id, 1, row, col), filext='jpg')
                    assert os.path.exists(tile_path)

            # And: Verify metadata
            assert tilestore.tiled(media_id)
            assert tilestore.get_metadata(media_id, 'width') == 512
            assert tilestore.get_metadata(media_id, 'maxtilelevel') == 1

**Key Validation Points:**

1. **Tiler Completion**: Error-free with 100% progress
2. **Pyramid Structure**: Correct number of tiles at each level
3. **File Creation**: All tile files exist on disk
4. **Metadata Storage**: Width, height, tilesize, maxtilelevel recorded

Tile Retrieval Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Validate tile retrieval after tiling:

.. code-block:: python

    class TestTileRetrievalIntegration:
        def test_retrieve_tiles_after_tiling(
                self, temp_tilestore, sample_images):
            """
            Scenario: Retrieve tiles from TileStore after tiling

            Given an image that has been tiled
            When tiles are requested from TileStore
            Then tile files can be read as valid images
            """
            # Given: Tile the image
            tiler = ConcreteTiler(image_path, media_id=media_id)
            tiler.run()

            # When: Retrieve tile path
            tile_path = tilestore.get_tile_path(
                (media_id, 1, 0, 0), filext='jpg')

            # Then: Tile is readable
            assert os.path.exists(tile_path)

            tile_image = Image.open(tile_path)
            assert tile_image.size[0] <= 256
            assert tile_image.size[1] <= 256

**Verifies:**

- Tile files are valid image format
- Tiles have correct dimensions
- TileStore paths are accurate

Cache Integration Testing
~~~~~~~~~~~~~~~~~~~~~~~~~~

Validate tile caching behavior:

.. code-block:: python

    class TestTileCacheIntegration:
        def test_cache_stores_and_retrieves_tiles(
                self, temp_tilestore, sample_images):
            """
            Scenario: Cache stores and retrieves tiles

            Given a TileCache instance
            When a tile is added
            Then the same tile can be retrieved by ID
            """
            cache = TileCache(maxsize=100)

            # Create test tile
            test_image = Image.new('RGB', (256, 256), color='red')
            tile = Tile(test_image)
            tile_id = ('test_media', 0, 0, 0)

            # Store in cache
            cache[tile_id] = tile

            # Retrieve from cache
            retrieved = cache[tile_id]
            assert retrieved is tile

        def test_cache_lru_eviction(
                self, temp_tilestore, sample_images):
            """
            Scenario: LRU eviction removes least recently used

            Given cache with limited size
            When cache exceeds capacity
            Then LRU tiles are evicted
            """
            cache = TileCache(maxsize=2)

            # Add 3 tiles (using level=1 for mortal tiles)
            cache[('m1', 1, 0, 0)] = Tile(Image.new('RGB', (256, 256)))
            cache[('m2', 1, 0, 0)] = Tile(Image.new('RGB', (256, 256)))
            cache[('m3', 1, 0, 0)] = Tile(Image.new('RGB', (256, 256)))

            # First tile should be evicted
            assert ('m1', 1, 0, 0) not in cache
            assert ('m2', 1, 0, 0) in cache
            assert ('m3', 1, 0, 0) in cache

Converter Pipeline Tests
------------------------

The converter pipeline tests (``test_converter_pipeline.py``) validate the complete workflow
from image/PDF conversion through to tiling. These tests use a ``ConcreteTiler`` implementation
that reads PPM image data using PIL.

ConcreteTiler Implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The test file includes a ``ConcreteTiler`` class that implements the abstract ``_scanchunk``
method for reading image rows:

.. code-block:: python

    class ConcreteTiler(Tiler):
        """
        A concrete implementation of Tiler for testing the converter pipeline.
        Implements the _scanchunk method using PIL to read PPM image data.
        """

        def __init__(self, infile, media_id=None, filext='jpg', tilesize=256):
            super().__init__(infile, media_id, filext, tilesize)
            self._image = Image.open(infile).convert('RGB')
            self._width, self._height = self._image.size
            self._bytes_per_pixel = 3
            self._current_row = 0

        def _scanchunk(self):
            """Read the next scanline from the image."""
            if self._current_row >= self._height:
                return b''
            # Use crop to get entire row at once (much faster than getpixel)
            row_img = self._image.crop(
                (0, self._current_row, self._width, self._current_row + 1))
            row_data = row_img.tobytes()
            self._current_row += 1
            return row_data

**Performance Note:** The ``_scanchunk`` implementation uses ``crop().tobytes()`` rather than
pixel-by-pixel reading with ``getpixel()``. This is critical for performance - reading a
2048x1536 image pixel-by-pixel would require ~3 million ``getpixel()`` calls and cause
tests to hang.

VipsConverter Tests
~~~~~~~~~~~~~~~~~~~

Test VipsConverter image format conversion:

.. code-block:: python

    class TestVipsConverterBasicOperations:
        """
        Feature: VipsConverter Basic Operations

        VipsConverter converts various image formats to PPM for tiling.
        """

        def test_convert_png_to_ppm(self, sample_images, tmp_path):
            """
            Scenario: Convert PNG to PPM format

            Given a PNG image file
            When VipsConverter processes the file
            Then a valid PPM file is created
            And the output has correct dimensions
            """
            infile = sample_images['png']
            outfile = str(tmp_path / "output.ppm")

            converter = VipsConverter(infile, outfile)
            converter.run()

            assert converter.error is None
            assert converter.progress == 1.0
            assert os.path.exists(outfile)

**Test Classes:**

- ``TestVipsConverterBasicOperations``: PNG, JPG, TIFF conversion
- ``TestVipsConverterErrorHandling``: Invalid file handling
- ``TestPDFConverterBasicOperations``: PDF rasterization
- ``TestPDFConverterErrorHandling``: PDF error cases

Converter to Tiler Pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test the complete convert-then-tile workflow:

.. code-block:: python

    class TestConverterToTilerPipeline:
        """
        Feature: Converter to Tiler Pipeline

        Images must be converted to PPM format before tiling.
        This tests the complete conversion-to-tiling workflow.
        """

        def test_convert_then_tile_png(
                self, sample_images, tmp_path, temp_tilestore,
                initialized_tilemanager):
            """
            Scenario: Convert PNG then tile

            Given a PNG image
            When converted to PPM and then tiled
            Then tiles are created successfully
            And tile pyramid is accessible
            """
            infile = sample_images['png']
            ppm_file = str(tmp_path / "converted.ppm")
            media_id = "pipeline_test_png"

            # Convert
            converter = VipsConverter(infile, ppm_file)
            converter.run()
            assert converter.error is None

            # Tile
            tiler = ConcreteTiler(ppm_file, media_id=media_id, tilesize=256)
            tiler.run()
            assert tiler.error is None

            # Verify
            assert tilestore.tiled(media_id)

Process-Based Parallel Conversion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The converter pipeline uses process-based parallelism via ``converterrunner`` to enable
multiple conversions to run concurrently without threading conflicts.

**Why Process-Based?**

pyvips uses its own internal thread pool for image operations. When multiple
``VipsConverter`` instances run in threads alongside TileManager threads, conflicts
can occur. By running conversions in separate processes:

- Each pyvips instance runs in its own memory space
- No interference with TileManager's TileProvider threads
- True parallel execution (not limited by Python's GIL)

**Process-Based Test Pattern:**

.. code-block:: python

    def test_multiple_converters_run_concurrently_via_processes(
            self, sample_images, tmp_path):
        """Test parallel conversion using processes."""
        from pyzui.converters import converterrunner
        from concurrent.futures import wait

        futures = []
        outfiles = []

        for i in range(3):
            infile = sample_images['png']
            outfile = str(tmp_path / f"output_{i}.ppm")
            outfiles.append(outfile)
            future = converterrunner.submit_vips_conversion(infile, outfile)
            futures.append(future)

        # Wait for all to complete with timeout
        done, not_done = wait(futures, timeout=60)
        assert len(not_done) == 0, f"{len(not_done)} conversions timed out"

        # Verify all completed successfully
        for i, future in enumerate(futures):
            error = future.result()
            assert error is None, f"Conversion {i} failed: {error}"

**Thread-Based Test (Single Converter):**

Individual converters can still run in threads for simple use cases:

.. code-block:: python

    def test_converter_runs_in_thread(self, sample_images, tmp_path):
        """Test converter runs correctly in a separate thread."""
        import threading

        converter = VipsConverter(infile, outfile)
        result = {'done': False}

        def run_conversion():
            converter.run()
            result['done'] = True

        thread = threading.Thread(target=run_conversion)
        thread.start()
        thread.join(timeout=30)

        assert result['done'], "Conversion thread timed out"
        assert converter.progress == 1.0

Converter Progress Tracking
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test progress reporting during conversion:

.. code-block:: python

    class TestConverterProgressTracking:
        def test_progress_starts_at_zero(self, sample_images, tmp_path):
            """Progress starts at 0.0 before run()."""
            converter = VipsConverter(sample_images['png'],
                                      str(tmp_path / "out.ppm"))
            assert converter.progress == 0.0

        def test_progress_reaches_one_after_completion(
                self, sample_images, tmp_path):
            """Progress reaches 1.0 after successful conversion."""
            converter = VipsConverter(sample_images['png'],
                                      str(tmp_path / "out.ppm"))
            converter.run()
            assert converter.progress == 1.0

Concurrent Access Tests
-----------------------

Thread Safety Validation
~~~~~~~~~~~~~~~~~~~~~~~~

Concurrent tests validate thread-safe operations:

.. code-block:: python

    class TestConcurrentTileRequests:
        """
        Feature: Concurrent Tile Request Handling

        Multiple threads may request tiles simultaneously.
        System must handle without race conditions.
        """

        def test_same_tile_requested_by_multiple_threads(self, cache):
            """
            Scenario: Same tile requested simultaneously

            Given multiple threads requesting same tile
            When requests arrive concurrently
            Then tile is loaded only once
            And all threads receive the same tile
            """
            provider = MockTileProvider(cache, load_delay=0.1)
            provider.start()

            tile_id = ('media', 1, 0, 0)
            num_threads = 10

            def request_tile():
                provider.request(tile_id)
                time.sleep(0.2)
                if tile_id in cache:
                    results.append(cache[tile_id])

            threads = [threading.Thread(target=request_tile)
                      for _ in range(num_threads)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # Tile loaded only once (or very few times due to race)
            assert provider.load_call_count <= 2
            assert tile_id in cache

**Validates:**

- No duplicate tile loads
- All threads eventually succeed
- Cache consistency under concurrent access

Concurrent Tiling Operations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test concurrent image tiling:

.. code-block:: python

    class TestConcurrentTilingOperations:
        def test_concurrent_tiling_different_images(
                self, temp_tilestore, sample_images, initialized_tilemanager):
            """
            Scenario: Multiple images tiled concurrently

            Given several images to tile
            When tiling operations run in parallel
            Then each image is tiled correctly
            And no cross-contamination occurs
            """
            def tile_image(image_path, index):
                media_id = f"concurrent_media_{index}"
                tiler = ConcreteTiler(image_path, media_id=media_id)
                tiler.run()
                results[media_id] = {
                    'error': tiler.error,
                    'progress': tiler.progress
                }

            threads = []
            for i, path in enumerate(sample_images[:3]):
                t = threading.Thread(target=tile_image, args=(path, i))
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            # All should complete successfully
            for media_id, result in results.items():
                assert result['error'] is None
                assert result['progress'] == 1.0
                assert tilestore.tiled(media_id)

Cache Thread Safety
~~~~~~~~~~~~~~~~~~~

Test cache operations under concurrent load:

.. code-block:: python

    class TestCacheThreadSafety:
        def test_concurrent_read_write_mix(self, cache):
            """
            Scenario: Concurrent reads and writes

            Given ongoing read and write operations
            When executed concurrently
            Then no corruption or crashes occur
            """
            errors = []
            stop_flag = threading.Event()

            def writer():
                i = 0
                while not stop_flag.is_set():
                    tile_id = ('media', 1, 0, i % 50)
                    try:
                        cache[tile_id] = Tile(Image.new('RGB', (256, 256)))
                    except Exception as e:
                        errors.append(('write', e))
                    i += 1
                    time.sleep(0.001)

            def reader():
                while not stop_flag.is_set():
                    for i in range(50):
                        tile_id = ('media', 1, 0, i)
                        try:
                            if tile_id in cache:
                                _ = cache[tile_id]
                        except KeyError:
                            pass  # Expected - evicted
                        except Exception as e:
                            errors.append(('read', e))
                    time.sleep(0.001)

            writers = [threading.Thread(target=writer) for _ in range(3)]
            readers = [threading.Thread(target=reader) for _ in range(5)]

            for t in writers + readers:
                t.start()

            time.sleep(1)  # Run for 1 second
            stop_flag.set()

            for t in writers + readers:
                t.join()

            assert len(errors) == 0

**Stress Test Patterns:**

- High concurrency (many threads)
- Mixed operations (reads and writes)
- Long running (seconds of continuous operation)
- Verification of no errors/crashes

Provider-Cache Integration
--------------------------

Provider-Cache Interaction
~~~~~~~~~~~~~~~~~~~~~~~~~~

Test how providers and cache work together:

.. code-block:: python

    class TestProviderCacheBasicInteraction:
        def test_provider_stores_loaded_tile_in_cache(self, cache):
            """
            Scenario: Provider stores tile in cache

            Given a TileProvider with empty cache
            When provider loads a tile
            Then tile is stored in cache
            """
            provider = MockTileProvider(cache)
            provider.start()
            tile_id = ('test_media', 1, 0, 0)

            # Configure specific image
            expected_image = Image.new('RGB', (256, 256), color='red')
            provider.set_image(tile_id, expected_image)

            # Request tile
            provider.request(tile_id)
            time.sleep(0.2)

            # Verify caching
            assert tile_id in cache
            assert provider.load_call_count == 1

        def test_cache_hit_prevents_provider_reload(self, cache):
            """
            Scenario: Cache hit prevents reload

            Given tile already in cache
            When same tile requested again
            Then provider is not called
            """
            provider = MockTileProvider(cache)
            provider.start()
            tile_id = ('test_media', 1, 0, 0)

            # Pre-populate cache
            cache[tile_id] = Tile(Image.new('RGB', (256, 256), color='blue'))

            # Request tile
            provider.request(tile_id)
            time.sleep(0.1)

            # Provider not called
            assert provider.load_call_count == 0

Dynamic Provider Testing
~~~~~~~~~~~~~~~~~~~~~~~~

Test dynamically generated tiles:

.. code-block:: python

    class TestDynamicProviderCacheInteraction:
        def test_dynamic_provider_caches_generated_tiles(
                self, cache, temp_tilestore):
            """
            Scenario: Dynamic provider caches generated tiles

            Given DynamicTileProvider with empty cache
            When tile is requested for generation
            Then tile is generated and cached
            """
            provider = MockDynamicProvider(cache)
            provider.start()
            tile_id = ('mock:dynamic', 5, 10, 20)

            # Request generation
            provider.request(tile_id)
            time.sleep(0.2)

            # Verify generation and caching
            assert provider.generate_call_count == 1
            assert tile_id in cache

        def test_dynamic_provider_skips_cached_tiles(
                self, cache, temp_tilestore):
            """
            Scenario: Dynamic provider doesn't regenerate cached

            Given generated tile already in cache
            When same coordinates requested
            Then generation is skipped
            """
            provider = MockDynamicProvider(cache)
            provider.start()
            tile_id = ('mock:dynamic', 5, 10, 20)

            # Pre-cache
            cache[tile_id] = Tile(Image.new('RGB', (256, 256), color='white'))

            # Request same tile
            provider.request(tile_id)
            time.sleep(0.1)

            # No generation
            assert provider.generate_call_count == 0

Cache Eviction Behavior
~~~~~~~~~~~~~~~~~~~~~~~~

Test provider behavior during cache eviction:

.. code-block:: python

    class TestCacheEvictionProviderBehavior:
        def test_evicted_tile_triggers_provider_reload(self, small_cache):
            """
            Scenario: Evicted tile is reloaded on next request

            Given cache with limited capacity
            And tile that was loaded then evicted
            When evicted tile requested again
            Then provider reloads the tile
            """
            provider = MockTileProvider(small_cache)
            provider.start()

            # Fill cache (using level > 0 for mortal tiles)
            for i in range(5):
                provider.request(('media', 1, 0, i))

            time.sleep(0.3)

            # Add more to trigger eviction
            for i in range(5, 8):
                provider.request(('media', 1, 0, i))

            time.sleep(0.3)

            # First tile may be evicted
            first_tile_id = ('media', 1, 0, 0)

            # Clear tracking
            provider.load_call_count = 0

            # Re-request
            provider.request(first_tile_id)
            time.sleep(0.2)

            # Should be in cache (reloaded or never evicted)
            assert first_tile_id in small_cache

TileManager Integration
-----------------------

Request Routing
~~~~~~~~~~~~~~~

Test TileManager's routing logic:

.. code-block:: python

    class TestTileRequestRouting:
        def test_static_media_routed_to_static_provider(
                self, temp_tilestore, tiled_media, initialized_tilemanager):
            """
            Scenario: Static media goes to static provider

            Given tiled static media
            When tile requested via load_tile
            Then request routed to StaticTileProvider
            """
            tile_id = (tiled_media, 0, 0, 0)

            # Request tile
            tilemanager.load_tile(tile_id)
            time.sleep(0.3)

            # Should be loadable
            tile = tilemanager.get_tile(tile_id)
            assert tile is not None
            assert isinstance(tile, Tile)

        def test_dynamic_media_routed_to_dynamic_provider(
                self, temp_tilestore, initialized_tilemanager):
            """
            Scenario: Dynamic media goes to dynamic provider

            Given initialized TileManager
            When tile requested for dynamic media
            Then request routed to DynamicTileProvider
            """
            tile_id = ("dynamic:fern", 5, 0, 0)

            # Request tile
            tilemanager.load_tile(tile_id)
            time.sleep(0.5)

            # Should be generated
            try:
                tile = tilemanager.get_tile(tile_id)
                assert tile is not None
            except TileNotLoaded:
                pass  # Still loading - OK

Get Tile Behavior
~~~~~~~~~~~~~~~~~

Test get_tile and get_tile_robust:

.. code-block:: python

    class TestGetTileBehavior:
        def test_get_tile_raises_media_not_tiled(
                self, temp_tilestore, initialized_tilemanager):
            """
            Scenario: get_tile raises MediaNotTiled

            Given media not tiled
            When get_tile called
            Then MediaNotTiled raised
            """
            tile_id = ("never_tiled.jpg", 0, 0, 0)

            with pytest.raises(MediaNotTiled):
                tilemanager.get_tile(tile_id)

        def test_get_tile_raises_tile_not_loaded(
                self, temp_tilestore, tiled_media, initialized_tilemanager):
            """
            Scenario: get_tile raises TileNotLoaded

            Given tiled media with uncached tile
            When get_tile called
            Then TileNotLoaded raised
            """
            tile_id = (tiled_media, 1, 1, 1)

            with pytest.raises(TileNotLoaded):
                tilemanager.get_tile(tile_id)

    class TestGetTileRobust:
        def test_get_tile_robust_synthesizes_missing_tile(
                self, temp_tilestore, tiled_media, initialized_tilemanager):
            """
            Scenario: get_tile_robust synthesizes from parent

            Given tile not cached
            And parent tiles available
            When get_tile_robust called
            Then tile synthesized via cut_tile
            """
            # Ensure level 0 cached
            tilemanager.load_tile((tiled_media, 0, 0, 0))
            time.sleep(0.3)

            # Request higher level
            tile = tilemanager.get_tile_robust((tiled_media, 1, 0, 0))
            assert tile is not None

Negative Tile Levels
~~~~~~~~~~~~~~~~~~~~

Test zoomed-out view handling:

.. code-block:: python

    class TestNegativeTileLevels:
        def test_negative_level_produces_smaller_tile(
                self, temp_tilestore, tiled_media, initialized_tilemanager):
            """
            Scenario: Negative levels produce smaller tiles

            Given base tile at level 0
            When negative levels requested
            Then each level is half the size
            """
            # Cache level 0
            tilemanager.load_tile((tiled_media, 0, 0, 0))
            time.sleep(0.3)

            base_tile = tilemanager.get_tile((tiled_media, 0, 0, 0))
            base_size = base_tile.size

            # Level -1: 50%
            tile_neg1, _ = tilemanager.cut_tile((tiled_media, -1, 0, 0))
            assert tile_neg1.size[0] == base_size[0] // 2
            assert tile_neg1.size[1] == base_size[1] // 2

            # Level -2: 25%
            tile_neg2, _ = tilemanager.cut_tile((tiled_media, -2, 0, 0))
            assert tile_neg2.size[0] == base_size[0] // 4
            assert tile_neg2.size[1] == base_size[1] // 4

GUI Integration Testing
-----------------------

Visual Verification Testing
~~~~~~~~~~~~~~~~~~~~~~~~~~~

GUI tests validate the complete application through visual verification:

**Running GUI Tests:**

.. code-block:: bash

    # Run all tests (with visual observation)
    python test/integrationtest/gui_integration.py

    # Start from specific step
    python gui_integration.py --start-step 30

    # List available steps
    python gui_integration.py --list-steps

**Test Steps Covered:**

.. code-block:: text

    Setup:
      1. Load Test Scene (Media Dir + String)

    File Menu:
      2. New Scene
      3. Open Home Scene
      4. Reload Test Scene
      5. Save Screenshot
      6. Save Scene
      7. Open Saved Scene

    View Menu:
      10. Set Framerate
      11. Adjust Sensitivity
      12. Fullscreen Toggle

    Help Menu:
      20. About Dialog
      21. About Qt Dialog

    Mouse Interactions:
      30. Left Click Select
      31. Click and Drag
      32. Scroll Wheel Zoom

    Keyboard Interactions:
      40. Escape Deselect
      41. Page Up/Down Zoom
      42. Arrow Keys Move
      43. Space Center
      44. Delete Media

    Complete Workflow:
      90. Full Application Workflow

**Test Resources:**

The GUI test creates temporary resources:

.. code-block:: text

    /tmp/pytest-of-{user}/pytest-{n}/pyzui_gui_test0/
    ├── media_directory/
    │   ├── 01_red_stripes.png
    │   ├── 02_green_gradient.png
    │   ├── 03_blue_checkerboard.png
    │   ├── 04_yellow_solid.png
    │   ├── 05_purple_diagonal.png
    │   └── 06_cyan_circles.png
    └── save_output/
        ├── test_screenshot.png
        ├── test_scene.pzs
        └── workflow_complete.pzs

**Timing Configuration:**

.. code-block:: python

    # Configurable timing constants (milliseconds)
    SHORT_DELAY_MS = 2000      # 2 seconds
    DEFAULT_DELAY_MS = 3500    # 3.5 seconds
    LONG_DELAY_MS = 5000       # 5 seconds
    IMAGE_LOAD_DELAY_MS = 10000  # 10 seconds

Writing New Integration Tests
------------------------------

Test Structure Guidelines
~~~~~~~~~~~~~~~~~~~~~~~~~~

**1. Use Appropriate Fixtures**

.. code-block:: python

    class TestNewIntegration:
        def test_feature(self, temp_tilestore, sample_images,
                        initialized_tilemanager):
            """Use fixtures to isolate test environment."""

**2. Test Complete Workflows**

.. code-block:: python

    def test_complete_workflow(self, ...):
        """
        Scenario: Complete user workflow

        Given initial state
        When user performs sequence of actions
        Then final state is correct
        And all intermediate states were valid
        """
        # Setup
        initial_state = create_initial_state()

        # Workflow step 1
        perform_action_1()
        verify_state_1()

        # Workflow step 2
        perform_action_2()
        verify_state_2()

        # Final verification
        verify_final_state()

**3. Use Real Dependencies**

.. code-block:: python

    # Good - uses real image and real tiler
    def test_real_tiling(self, sample_images):
        image_path = sample_images[(512, 512)]
        tiler = ConcreteTiler(image_path, media_id="test")
        tiler.run()
        assert tiler.error is None

    # Avoid - mocking defeats integration testing purpose
    @patch('pyzui.tilesystem.tiler.Tiler')
    def test_with_mock(self, mock_tiler):
        # This is a unit test, not integration test
        pass

**4. Verify File System State**

.. code-block:: python

    def test_tiles_created_on_disk(self, temp_tilestore):
        """Verify actual files created."""
        # Perform operation
        tiler.run()

        # Check files exist
        tile_path = tilestore.get_tile_path(tile_id, filext='jpg')
        assert os.path.exists(tile_path)

        # Verify file contents
        img = Image.open(tile_path)
        assert img.size == (256, 256)

**5. Test Thread Safety**

.. code-block:: python

    def test_concurrent_operation(self):
        """Test thread safety with real threads."""
        results = []
        errors = []

        def worker():
            try:
                result = perform_operation()
                results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 10

**6. Allow Appropriate Timing**

.. code-block:: python

    def test_async_operation(self):
        """Allow time for async operations."""
        # Trigger async operation
        provider.request(tile_id)

        # Wait for completion
        time.sleep(0.3)

        # Verify result
        assert tile_id in cache

**7. Cleanup Properly**

.. code-block:: python

    def test_with_cleanup(self, tmp_path):
        """Ensure resources cleaned up."""
        temp_file = tmp_path / "test.dat"

        try:
            # Test operations
            create_file(temp_file)
            process_file(temp_file)
        finally:
            # Cleanup (fixtures handle most cleanup)
            if temp_file.exists():
                temp_file.unlink()

Best Practices
--------------

Test Design
~~~~~~~~~~~

**Do:**

- Test complete workflows end-to-end
- Use real dependencies (images, files, threads)
- Verify file system state
- Test concurrent scenarios
- Allow appropriate timing for async operations
- Isolate tests with fixtures
- Verify both success and failure paths

**Don't:**

- Mock core components (defeats integration testing)
- Assume instant operations (use time.sleep appropriately)
- Share state between tests (use fixtures)
- Skip cleanup (use try/finally or fixtures)
- Test trivial integrations (use unit tests)

Timing Considerations
~~~~~~~~~~~~~~~~~~~~~

**Async Operations:**

.. code-block:: python

    # Provider operations are async
    provider.request(tile_id)
    time.sleep(0.2)  # Allow processing

    # Tiling operations take time
    tiler.run()  # Blocks until complete
    assert tiler.progress == 1.0

**Thread Operations:**

.. code-block:: python

    # Start threads
    for t in threads:
        t.start()

    # Wait for completion
    for t in threads:
        t.join()  # Blocks until thread finishes

    # Or use timeout
    for t in threads:
        t.join(timeout=5.0)
        assert not t.is_alive()

Resource Management
~~~~~~~~~~~~~~~~~~~

**Temporary Directories:**

.. code-block:: python

    # Fixtures handle most cleanup
    def test_with_temp_dir(self, temp_tilestore, tmp_path):
        # temp_tilestore: Isolated tilestore
        # tmp_path: Pytest temporary directory
        # Both auto-cleaned after test

**File Handles:**

.. code-block:: python

    # Use context managers
    with open(file_path, 'rb') as f:
        data = f.read()

    # Or ensure cleanup
    f = open(file_path, 'rb')
    try:
        data = f.read()
    finally:
        f.close()

**Thread Safety:**

.. code-block:: python

    # Use thread-safe data structures
    results = queue.Queue()
    errors = queue.Queue()

    def worker():
        try:
            results.put(do_work())
        except Exception as e:
            errors.put(e)

Common Patterns
---------------

Testing Pipelines
~~~~~~~~~~~~~~~~~

.. code-block:: python

    def test_complete_pipeline(self, fixtures):
        """Test end-to-end pipeline."""
        # Stage 1: Input
        input_data = create_input()
        assert validate_input(input_data)

        # Stage 2: Processing
        processed = process(input_data)
        assert validate_processed(processed)

        # Stage 3: Storage
        store(processed)
        assert exists_in_store(processed)

        # Stage 4: Retrieval
        retrieved = retrieve(processed.id)
        assert retrieved == processed

Testing Concurrency
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def test_thread_safety(self):
        """Test concurrent access."""
        shared_state = SharedState()
        errors = []

        def concurrent_operation():
            try:
                for _ in range(100):
                    shared_state.operation()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=concurrent_operation)
                  for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert shared_state.is_consistent()

Testing Caching
~~~~~~~~~~~~~~~

.. code-block:: python

    def test_cache_behavior(self, cache):
        """Test caching with real operations."""
        # Miss - initial load
        assert tile_id not in cache
        tile = load_tile(tile_id)
        cache[tile_id] = tile

        # Hit - from cache
        assert tile_id in cache
        cached_tile = cache[tile_id]
        assert cached_tile is tile

        # Eviction - LRU
        fill_cache_to_capacity(cache)
        assert tile_id not in cache  # Evicted

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Tests Fail Intermittently:**

.. code-block:: python

    # Increase timing allowances
    time.sleep(0.5)  # Instead of 0.1

    # Or add retries
    for _ in range(3):
        try:
            result = operation()
            break
        except TileNotLoaded:
            time.sleep(0.1)

**Resource Leaks:**

.. code-block:: python

    # Use fixtures for cleanup
    @pytest.fixture
    def resource():
        r = create_resource()
        yield r
        r.cleanup()

**File System Issues:**

.. code-block:: bash

    # Ensure temp directory writable
    ls -la /tmp

    # Check disk space
    df -h

**Threading Issues:**

.. code-block:: python

    # Add thread debugging
    import threading
    print(f"Active threads: {threading.active_count()}")
    print(f"Thread list: {threading.enumerate()}")

Performance Tips
~~~~~~~~~~~~~~~~

**Parallel Test Execution:**

.. code-block:: bash

    # Only if tests are independent
    pytest -n auto

**Selective Test Running:**

.. code-block:: bash

    # Run specific category
    pytest test_tiling_pipeline.py

    # Skip slow tests
    pytest -m "not slow"

**Reduce Resource Usage:**

.. code-block:: python

    # Use smaller test images
    img = Image.new('RGB', (256, 256))  # Not (4096, 4096)

    # Limit cache size
    cache = TileCache(maxsize=10)  # Not 1000

Quick Reference
---------------

Running Tests
~~~~~~~~~~~~~

.. code-block:: bash

    # All integration tests
    pytest test/integrationtest

    # Specific file
    pytest test_tiling_pipeline.py

    # Verbose
    pytest -v -s

    # With coverage
    pytest --cov=pyzui

    # GUI tests (manual)
    python gui_integration.py

Essential Patterns
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Pipeline test
    def test_pipeline(self, fixtures):
        input -> process -> verify -> store -> retrieve

    # Concurrency test
    def test_concurrent(self):
        spawn threads -> run operations -> join -> verify

    # Cache test
    def test_cache(self, cache):
        miss -> load -> hit -> evict -> verify

    # File system test
    def test_files(self, temp_tilestore):
        create -> verify exists -> read -> verify content

Resources
---------

Documentation
~~~~~~~~~~~~~

- **Pytest**: https://docs.pytest.org/
- **Threading**: https://docs.python.org/3/library/threading.html
- **PIL/Pillow**: https://pillow.readthedocs.io/

PyZUI-Specific
~~~~~~~~~~~~~~

- :doc:`unittest` - Unit testing guide
- :doc:`../technicaldocumentation/tilingsystem` - Understanding tile system
- :doc:`../technicaldocumentation/objectsystem` - Understanding object architecture
- :doc:`../technicaldocumentation/windowsystem` - Understanding UI components

Example Test Files
~~~~~~~~~~~~~~~~~~

Reference these for patterns:

- ``test/integrationtest/test_tiling_pipeline.py`` - Complete pipeline testing
- ``test/integrationtest/test_converter_pipeline.py`` - Converter and tiling pipeline
- ``test/integrationtest/test_concurrent_access.py`` - Thread safety patterns
- ``test/integrationtest/test_cache_provider_integration.py`` - Component interaction
- ``test/integrationtest/test_tilemanager_integration.py`` - Coordination testing
- ``test/integrationtest/gui_integration.py`` - Visual verification

Conclusion
----------

Integration tests validate that PyZUI components work correctly together as a complete system.
When adding new features:

1. Write integration tests for complete workflows
2. Test with real dependencies (images, files, threads)
3. Verify file system state
4. Test concurrent scenarios
5. Use appropriate fixtures for isolation
6. Allow proper timing for async operations
7. Verify both success and failure paths
8. Clean up resources properly

Well-designed integration tests catch bugs that unit tests miss, validate system behavior,
and ensure components interact correctly.
