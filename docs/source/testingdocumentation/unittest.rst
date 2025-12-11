.. Unit Testing Documentation

Unit Testing Guide
==================

This document provides a comprehensive guide to unit testing PyZUI during development,
including testing patterns, best practices, and guidelines for writing new tests.
The PyZUI test suite uses pytest with BDD-style documentation and comprehensive coverage
of all major components.

Overview
--------

The PyZUI unit test suite is designed to:

1. Validate core functionality of all components
2. Prevent regressions during development
3. Document expected behavior through tests
4. Enable confident refactoring
5. Catch bugs early in the development cycle

**Test Framework**: pytest (Python Testing Framework)

**Testing Style**: Behavior-Driven Development (BDD) with Given-When-Then scenarios

**Coverage Areas**:
- Objects system (PhysicalObject, MediaObject, Scene)
- Tile system (TileCache, TileManager, TileProviders)
- Converters (PDF, Vips)
- Windows (MainWindow, QZUI, Dialogs)

Test Suite Structure
--------------------

Directory Organization
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    test/unittest/
    ├── conftest.py                    # Pytest configuration
    ├── objects/                       # Object system tests
    │   ├── mediaobjects/
    │   │   ├── test_physicalobject.py
    │   │   ├── test_mediaobject.py
    │   │   ├── test_tiledmediaobject.py
    │   │   ├── test_stringmediaobject.py
    │   │   └── test_svgmediaobject.py
    │   └── scene/
    │       ├── test_scene.py
    │       └── test_qzui.py
    ├── tilesystem/                    # Tile system tests
    │   ├── test_tilecache.py
    │   ├── test_tilemanager.py
    │   ├── test_tile.py
    │   ├── tileproviders/
    │   │   ├── test_tileprovider.py
    │   │   ├── test_statictileprovider.py
    │   │   ├── test_dynamictileprovider.py
    │   │   └── test_ferndynamictileprovider.py
    │   ├── tiler/
    │   │   ├── test_tiler.py
    │   │   └── test_ppm.py
    │   └── tilestore/
    │       ├── test_tilestore.py
    │       └── test_cleanuptilestore.py
    ├── converters/                    # Converter tests
    │   ├── test_converter.py
    │   ├── test_pdfconverter.py
    │   └── test_vipsconverter.py
    ├── windows/                       # Window system tests
    │   └── dialogwindows/
    │       ├── test_mainwindow.py
    │       └── test_dialogwindows.py
    └── test_new_dynamictileprovider_TEMPLATE.py  # Template for new tests

Configuration Files
~~~~~~~~~~~~~~~~~~~

**conftest.py**

Located at ``test/unittest/conftest.py``, this file configures pytest for the test suite:

.. code-block:: python

    """
    Pytest configuration file for unittest directory.
    Sets up Python path so tests can import from pyzui package.
    """
    import sys
    import os

    # Add pyzui root to Python path
    pyzui_root = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '../..'))
    if pyzui_root not in sys.path:
        sys.path.insert(0, pyzui_root)

This ensures all tests can import from the ``pyzui`` package regardless of
the current working directory.

Running Tests
-------------

Basic Usage
~~~~~~~~~~~

**Run all unit tests:**

.. code-block:: bash

    cd test/unittest
    pytest

**Run with verbose output:**

.. code-block:: bash

    pytest -v

**Run specific test file:**

.. code-block:: bash

    pytest objects/mediaobjects/test_physicalobject.py

**Run specific test class:**

.. code-block:: bash

    pytest objects/mediaobjects/test_physicalobject.py::TestPhysicalObject

**Run specific test method:**

.. code-block:: bash

    pytest objects/mediaobjects/test_physicalobject.py::TestPhysicalObject::test_init

Advanced Options
~~~~~~~~~~~~~~~~

**Show print statements:**

.. code-block:: bash

    pytest -v -s

**Stop on first failure:**

.. code-block:: bash

    pytest -x

**Show local variables on failure:**

.. code-block:: bash

    pytest -l

**Run tests in parallel (requires pytest-xdist):**

.. code-block:: bash

    pytest -n auto

**Generate HTML coverage report:**

.. code-block:: bash

    pytest --cov=pyzui --cov-report=html
    # Open htmlcov/index.html in browser

**Run only tests matching pattern:**

.. code-block:: bash

    pytest -k "tile"  # Runs all tests with 'tile' in name

**Run tests marked with specific marker:**

.. code-block:: bash

    pytest -m "integration"  # If using markers

Test Organization Patterns
---------------------------

Test Class Structure
~~~~~~~~~~~~~~~~~~~~

Every test module should follow this structure:

.. code-block:: python

    import pytest
    from unittest.mock import Mock, patch, MagicMock
    from pyzui.module import ClassToTest

    class TestClassName:
        """
        Feature: Class Description

        High-level description of what this class does and why it's being tested.
        Explains the component's role in the system.
        """

        def test_specific_behavior(self):
            """
            Scenario: Describe the test scenario

            Given <preconditions>
            When <action performed>
            Then <expected outcome>
            """
            # Arrange
            obj = ClassToTest()

            # Act
            result = obj.method()

            # Assert
            assert result == expected_value

BDD-Style Documentation
~~~~~~~~~~~~~~~~~~~~~~~

All tests use Given-When-Then format in docstrings:

**Given**: Preconditions and setup
**When**: Action or event
**Then**: Expected outcome

**Example:**

.. code-block:: python

    def test_move(self):
        """
        Scenario: Move object to new position

        Given a PhysicalObject at the origin
        When calling move with x=10 and y=20
        Then the object position should be updated to (10, 20)
        """
        obj = PhysicalObject()
        obj.move(10, 20)
        assert obj._x == 10.0
        assert obj._y == 20.0

Test Categories
~~~~~~~~~~~~~~~

**1. Initialization Tests**

Test object construction and default values:

.. code-block:: python

    def test_init(self):
        """Test object initialization with default values."""
        obj = PhysicalObject()
        assert obj._x == 0.0
        assert obj._y == 0.0
        assert obj._z == 0.0

**2. Property Tests**

Test getters and setters:

.. code-block:: python

    def test_zoomlevel_property(self):
        """Test zoomlevel property getter and setter."""
        obj = PhysicalObject()
        obj.zoomlevel = 5.0
        assert obj.zoomlevel == 5.0
        assert obj._z == 5.0

**3. Method Tests**

Test individual methods:

.. code-block:: python

    def test_move(self):
        """Test move method updates position."""
        obj = PhysicalObject()
        obj.move(10, 20)
        assert obj._x == 10.0
        assert obj._y == 20.0

**4. Edge Case Tests**

Test boundary conditions:

.. code-block:: python

    def test_move_negative(self):
        """Test move with negative coordinates."""
        obj = PhysicalObject()
        obj.move(-5, -10)
        assert obj._x == -5.0
        assert obj._y == -10.0

**5. Integration Tests**

Test with real dependencies:

.. code-block:: python

    def test_small_image_conversion(self):
        """Integration test for PNG conversion."""
        infile = "data/test.png"

        if not os.path.exists(infile):
            pytest.skip(f"Test file not found: {infile}")

        converter = VipsConverter(infile, outfile)
        converter.start()
        converter.join()

        assert converter.error is None
        assert os.path.exists(outfile)

Mocking Strategies
------------------

Basic Mocking
~~~~~~~~~~~~~

Use ``Mock()`` for simple object mocking:

.. code-block:: python

    from unittest.mock import Mock

    def test_with_mock():
        """Test using a mock object."""
        mock_scene = Mock()
        mock_scene.viewport_size = (1280, 720)

        obj = MediaObject('image.jpg', mock_scene)
        assert obj._scene == mock_scene

Patch Decorators
~~~~~~~~~~~~~~~~

Use ``@patch`` to replace dependencies:

.. code-block:: python

    from unittest.mock import patch

    @patch('pyvips.Image.new_from_file')
    def test_run_success(self, mock_new_from_file):
        """Test successful image conversion."""
        mock_image = Mock()
        mock_image.width = 100
        mock_image.height = 100
        mock_image.format = 'uchar'
        mock_new_from_file.return_value = mock_image

        converter = VipsConverter("input.jpg", "output.ppm")
        converter.run()

        assert converter.error is None
        mock_new_from_file.assert_called_once()

MagicMock for Special Methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``MagicMock`` when mocking magic methods:

.. code-block:: python

    from unittest.mock import MagicMock

    def test_with_magic_mock():
        """Test using MagicMock for special methods."""
        mock_obj = MagicMock()
        mock_obj.__len__.return_value = 5

        assert len(mock_obj) == 5

Assertion Patterns
------------------

Basic Assertions
~~~~~~~~~~~~~~~~

.. code-block:: python

    # Equality
    assert obj.value == expected_value
    assert obj.value != wrong_value

    # Identity
    assert obj is same_obj
    assert obj is not None

    # Membership
    assert item in collection
    assert item not in collection

    # Boolean
    assert obj.flag is True
    assert obj.flag is False

Approximate Comparisons
~~~~~~~~~~~~~~~~~~~~~~~

For floating-point comparisons, use ``pytest.approx()``:

.. code-block:: python

    import pytest

    def test_aim_x_no_time(self):
        """Test velocity calculation with approx."""
        obj = PhysicalObject()
        obj.aim('x', 100.0)
        expected = 100.0 * math.log(obj.damping_factor)
        assert obj.vx == pytest.approx(expected)

Exception Testing
~~~~~~~~~~~~~~~~~

Test that exceptions are raised:

.. code-block:: python

    def test_getitem_nonexistent(self):
        """Test KeyError for non-existent item."""
        cache = TileCache()
        with pytest.raises(KeyError):
            _ = cache[('nonexistent', 1, 0, 0)]

Mock Assertions
~~~~~~~~~~~~~~~

Verify mock object interactions:

.. code-block:: python

    def test_mock_calls(self):
        """Test mock method calls."""
        mock_obj = Mock()

        # Call the mock
        result = mock_obj.method('arg1', key='value')

        # Verify calls
        mock_obj.method.assert_called_once()
        mock_obj.method.assert_called_once_with('arg1', key='value')
        mock_obj.method.assert_called_with('arg1', key='value')
        assert mock_obj.method.call_count == 1

Writing New Tests
-----------------

Step-by-Step Guide
~~~~~~~~~~~~~~~~~~

**1. Create Test File**

Match the structure of the source code:

.. code-block:: text

    Source: pyzui/tilesystem/tilecache.py
    Test:   test/unittest/tilesystem/test_tilecache.py

**2. Import Dependencies**

.. code-block:: python

    import pytest
    from unittest.mock import Mock, patch
    from pyzui.module import ClassToTest

**3. Create Test Class**

.. code-block:: python

    class TestClassName:
        """
        Feature: Component Name

        Description of what is being tested.
        """

**4. Add Initialization Test**

.. code-block:: python

    def test_init(self):
        """
        Scenario: Initialize with default values

        Given no custom parameters
        When creating an instance
        Then defaults should be set correctly
        """
        obj = ClassToTest()
        assert obj.attribute == default_value

**5. Test Each Method**

.. code-block:: python

    def test_method_name(self):
        """
        Scenario: Describe what method does

        Given preconditions
        When calling the method
        Then expected results
        """
        obj = ClassToTest()
        result = obj.method(args)
        assert result == expected

**6. Test Edge Cases**

.. code-block:: python

    def test_method_edge_case(self):
        """Test method with boundary condition."""
        obj = ClassToTest()
        result = obj.method(edge_case_value)
        assert result == expected_edge_result

**7. Test Error Handling**

.. code-block:: python

    def test_method_error(self):
        """Test method handles errors gracefully."""
        obj = ClassToTest()
        with pytest.raises(ExpectedError):
            obj.method(invalid_input)

Test Template Example
~~~~~~~~~~~~~~~~~~~~~

Complete test file template:

.. code-block:: python

    """
    Tests for ModuleName component.

    This test suite validates the ModuleName class which [description].
    """

    import pytest
    from unittest.mock import Mock, patch, MagicMock
    from pyzui.module import ClassName

    class TestClassName:
        """
        Feature: ClassName Component

        High-level description of component functionality and purpose.
        """

        # =======================
        # Initialization Tests
        # =======================

        def test_init_default(self):
            """
            Scenario: Initialize with default parameters

            Given no custom parameters
            When creating instance
            Then defaults should be applied
            """
            obj = ClassName()
            assert obj.attribute == default_value

        def test_init_custom(self):
            """
            Scenario: Initialize with custom parameters

            Given custom parameters
            When creating instance
            Then custom values should be used
            """
            obj = ClassName(param=custom_value)
            assert obj.attribute == custom_value

        # =======================
        # Property Tests
        # =======================

        def test_property_get(self):
            """Test property getter."""
            obj = ClassName()
            assert obj.property == expected_value

        def test_property_set(self):
            """Test property setter."""
            obj = ClassName()
            obj.property = new_value
            assert obj.property == new_value

        # =======================
        # Method Tests
        # =======================

        def test_method_success(self):
            """
            Scenario: Method executes successfully

            Given valid input
            When calling method
            Then expected output is returned
            """
            obj = ClassName()
            result = obj.method(input)
            assert result == expected_output

        def test_method_edge_case(self):
            """Test method with edge case input."""
            obj = ClassName()
            result = obj.method(edge_case)
            assert result == expected_edge_output

        # =======================
        # Error Handling Tests
        # =======================

        def test_method_invalid_input(self):
            """Test method rejects invalid input."""
            obj = ClassName()
            with pytest.raises(ValueError):
                obj.method(invalid_input)

        # =======================
        # Integration Tests
        # =======================

        def test_integration_scenario(self):
            """
            Scenario: Integration with real dependencies

            Given real file/resource
            When performing operation
            Then result should be valid
            """
            if not os.path.exists(test_file):
                pytest.skip("Test file not found")

            obj = ClassName()
            result = obj.process(test_file)
            assert result is not None

Testing Specific Components
----------------------------

Testing PhysicalObject
~~~~~~~~~~~~~~~~~~~~~~

**Key Test Areas:**

- Initialization (position, velocity)
- Movement (move, aim)
- Physics simulation (step, damping)
- Properties (zoomlevel, centre, moving)

**Example:**

.. code-block:: python

    class TestPhysicalObject:
        def test_step_damping(self):
            """Test velocity damping during step."""
            obj = PhysicalObject()
            obj.vx = 100.0
            initial_vx = obj.vx

            obj.step(0.5)

            # Velocity should be reduced
            assert obj.vx < initial_vx
            assert obj.vx > 0  # But not zero yet

Testing TileCache
~~~~~~~~~~~~~~~~~

**Key Test Areas:**

- Initialization (maxsize, maxage)
- Storage/retrieval (dict-like interface)
- LRU eviction
- Immortal tiles (None tiles, level-0)
- Access counting (maxaccesses)

**Example:**

.. code-block:: python

    class TestTileCache:
        def test_lru_eviction(self):
            """Test least recently used tiles are evicted."""
            cache = TileCache(maxsize=2)

            cache[('m1', 1, 0, 0)] = Mock()
            cache[('m2', 1, 0, 0)] = Mock()
            cache[('m3', 1, 0, 0)] = Mock()

            # First tile should be evicted
            assert ('m1', 1, 0, 0) not in cache
            assert ('m2', 1, 0, 0) in cache
            assert ('m3', 1, 0, 0) in cache

Testing Converters
~~~~~~~~~~~~~~~~~~

**Key Test Areas:**

- Initialization (file paths, settings)
- Threading behavior
- Progress tracking
- Error handling
- Integration tests (real files)

**Example:**

.. code-block:: python

    class TestVipsConverter:
        @patch('pyvips.Image.new_from_file')
        def test_run_converts_16bit_to_8bit(self, mock_new):
            """Test 16-bit to 8-bit conversion."""
            mock_image = Mock()
            mock_image.format = 'ushort'  # 16-bit
            mock_image.cast = Mock(return_value=mock_image)
            mock_new.return_value = mock_image

            converter = VipsConverter("in.tif", "out.ppm")
            converter.run()

            mock_image.cast.assert_called_once_with('uchar')

Testing TileProviders
~~~~~~~~~~~~~~~~~~~~~

**Key Test Areas:**

- Initialization
- Inheritance verification
- Class attributes (filext, tilesize, aspect_ratio)
- Boundary conditions (negative coords, out of range)
- Tile generation
- Error handling

**Use the Template:**

For new DynamicTileProviders, use ``test_new_dynamictileprovider_TEMPLATE.py``:

1. Copy template file
2. Rename to ``test_yourprovider.py``
3. Replace ``YourProvider`` with actual class name
4. Update import paths
5. Customize test values
6. Uncomment and run tests

**Template Structure:**

.. code-block:: python

    class TestYourProvider:
        # Section 1: Basic initialization
        def test_init(self):
            """Test provider initialization."""

        # Section 2: Required attributes
        def test_filext_attribute(self):
            """Test file extension."""

        def test_tilesize_attribute(self):
            """Test tile size."""

        # Section 3: Boundary conditions
        def test_load_dynamic_negative_row(self):
            """Test negative row handling."""

        # Section 4: Tile generation
        @patch('PIL.Image.new')
        def test_load_dynamic_valid_tile(self, mock_image):
            """Test valid tile generation."""

        # Section 5: Provider-specific tests
        def test_custom_logic(self):
            """Test provider-specific functionality."""

Testing Windows/UI Components
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Special Considerations:**

- May require Qt application context
- Use mocks for heavy Qt objects
- Test logic separately from UI
- Skip if display not available

**Example:**

.. code-block:: python

    @pytest.mark.skipif(
        os.environ.get('DISPLAY') is None,
        reason="No display available"
    )
    def test_qzui_initialization(self):
        """Test QZUI widget initialization."""
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])

        qzui = QZUI()
        assert qzui is not None

Best Practices
--------------

General Guidelines
~~~~~~~~~~~~~~~~~~

**1. One Assert Per Test (When Possible)**

.. code-block:: python

    # Good - focused test
    def test_x_coordinate(self):
        obj = PhysicalObject()
        obj.move(10, 20)
        assert obj._x == 10.0

    # Acceptable - related assertions
    def test_move_updates_position(self):
        obj = PhysicalObject()
        obj.move(10, 20)
        assert obj._x == 10.0
        assert obj._y == 20.0

**2. Descriptive Test Names**

.. code-block:: python

    # Good names
    def test_move_updates_position():
    def test_move_with_negative_coordinates():
    def test_zoom_maintains_centre_position():

    # Bad names
    def test1():
    def test_stuff():
    def test_it_works():

**3. Arrange-Act-Assert Pattern**

.. code-block:: python

    def test_method(self):
        # Arrange - set up test data
        obj = ClassName()
        input_value = 42

        # Act - perform the operation
        result = obj.method(input_value)

        # Assert - verify expectations
        assert result == expected_value

**4. Use Fixtures for Repeated Setup**

.. code-block:: python

    @pytest.fixture
    def physical_object():
        """Provide a PhysicalObject instance."""
        return PhysicalObject()

    def test_move(physical_object):
        """Test using fixture."""
        physical_object.move(10, 20)
        assert physical_object._x == 10.0

**5. Test Behavior, Not Implementation**

.. code-block:: python

    # Good - tests behavior
    def test_cache_evicts_old_items(self):
        cache = TileCache(maxsize=1)
        cache['item1'] = Mock()
        cache['item2'] = Mock()

        assert 'item1' not in cache
        assert 'item2' in cache

    # Bad - tests implementation details
    def test_cache_uses_ordereddict(self):
        cache = TileCache()
        assert isinstance(cache._cache, OrderedDict)

**6. Mock External Dependencies**

.. code-block:: python

    # Good - mocks file I/O
    @patch('builtins.open', mock_open(read_data='data'))
    def test_file_reading(self):
        result = read_file('test.txt')
        assert result == 'data'

    # Bad - depends on actual file system
    def test_file_reading(self):
        # Creates real file!
        with open('test.txt', 'w') as f:
            f.write('data')
        result = read_file('test.txt')
        os.remove('test.txt')

**7. Clean Up Resources**

.. code-block:: python

    def test_with_tempfile(self):
        """Test with proper cleanup."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            outfile = tmp.name

        try:
            # Perform test
            process_file(outfile)
            assert os.path.exists(outfile)
        finally:
            # Clean up
            if os.path.exists(outfile):
                os.unlink(outfile)

**8. Skip Tests When Dependencies Missing**

.. code-block:: python

    def test_integration(self):
        """Test with actual file."""
        if not os.path.exists(test_file):
            pytest.skip(f"Test file not found: {test_file}")

        result = process(test_file)
        assert result is not None

Common Pitfalls
~~~~~~~~~~~~~~~

**1. Testing Multiple Things**

.. code-block:: python

    # Bad - tests too many things
    def test_everything(self):
        obj = ClassName()
        assert obj.init_works()
        assert obj.method1() == value1
        assert obj.method2() == value2
        assert obj.cleanup() is True

    # Good - separate tests
    def test_initialization(self):
        obj = ClassName()
        assert obj.init_works()

    def test_method1(self):
        obj = ClassName()
        assert obj.method1() == value1

**2. Order-Dependent Tests**

.. code-block:: python

    # Bad - tests depend on execution order
    class TestBad:
        def test_a_creates_file(self):
            create_file('test.txt')

        def test_b_reads_file(self):
            # Fails if test_a doesn't run first!
            content = read_file('test.txt')

    # Good - tests are independent
    class TestGood:
        def test_create_file(self):
            create_file('test.txt')
            try:
                assert os.path.exists('test.txt')
            finally:
                os.unlink('test.txt')

        def test_read_file(self):
            # Creates own test file
            with open('test.txt', 'w') as f:
                f.write('data')
            try:
                content = read_file('test.txt')
                assert content == 'data'
            finally:
                os.unlink('test.txt')

**3. Overly Specific Mocks**

.. code-block:: python

    # Bad - too tightly coupled to implementation
    @patch('module.ClassA')
    @patch('module.ClassB')
    @patch('module.function1')
    @patch('module.function2')
    def test_complex(self, m1, m2, m3, m4):
        # If implementation changes slightly, test breaks

    # Good - mocks at boundaries
    @patch('module.external_api_call')
    def test_simpler(self, mock_api):
        # Mocks external dependency only
        mock_api.return_value = {'status': 'ok'}
        result = process_data()
        assert result is not None

**4. Not Testing Edge Cases**

.. code-block:: python

    # Incomplete - only tests happy path
    def test_divide(self):
        assert divide(10, 2) == 5

    # Complete - tests edge cases
    def test_divide_normal(self):
        assert divide(10, 2) == 5

    def test_divide_by_zero(self):
        with pytest.raises(ZeroDivisionError):
            divide(10, 0)

    def test_divide_negative(self):
        assert divide(-10, 2) == -5

**5. Hardcoding Values**

.. code-block:: python

    # Bad - magic numbers
    def test_calculation(self):
        assert calculate(5, 3) == 15

    # Good - clear intent
    def test_calculation(self):
        base = 5
        multiplier = 3
        expected = base * multiplier
        assert calculate(base, multiplier) == expected

Coverage Goals
--------------

Target Metrics
~~~~~~~~~~~~~~

**Line Coverage**: Aim for >80% coverage

**Branch Coverage**: Aim for >70% coverage

**Critical Paths**: 100% coverage for:
- Error handling
- Boundary conditions
- Security-sensitive code
- Data corruption prevention

Generating Coverage Reports
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**HTML Report:**

.. code-block:: bash

    pytest --cov=pyzui --cov-report=html
    open htmlcov/index.html

**Terminal Report:**

.. code-block:: bash

    pytest --cov=pyzui --cov-report=term-missing

**Coverage for Specific Module:**

.. code-block:: bash

    pytest --cov=pyzui.tilesystem --cov-report=term

Interpreting Coverage
~~~~~~~~~~~~~~~~~~~~~

**Focus Areas:**

1. **High Coverage** (>90%):
   - Core algorithms
   - Data transformations
   - Critical paths

2. **Medium Coverage** (70-90%):
   - UI components
   - Integration code
   - Helper utilities

3. **Lower Coverage Acceptable** (<70%):
   - Experimental features
   - Platform-specific code
   - Debug utilities

Continuous Integration
----------------------

Running Tests in CI
~~~~~~~~~~~~~~~~~~~

**Example GitHub Actions Workflow:**

.. code-block:: yaml

    name: Unit Tests

    on: [push, pull_request]

    jobs:
      test:
        runs-on: ubuntu-latest

        steps:
        - uses: actions/checkout@v2

        - name: Set up Python
          uses: actions/setup-python@v2
          with:
            python-version: '3.12'

        - name: Install dependencies
          run: |
            pip install -r requirements.txt
            pip install pytest pytest-cov

        - name: Run tests
          run: |
            cd test/unittest
            pytest --cov=pyzui --cov-report=xml

        - name: Upload coverage
          uses: codecov/codecov-action@v2
          with:
            file: ./coverage.xml

Pre-commit Hooks
~~~~~~~~~~~~~~~~

**Run tests before commit:**

.. code-block:: bash

    # .git/hooks/pre-commit
    #!/bin/sh
    cd test/unittest
    pytest -x
    if [ $? -ne 0 ]; then
        echo "Tests failed. Commit aborted."
        exit 1
    fi

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Import Errors:**

.. code-block:: bash

    # Solution: Run from test/unittest directory
    cd test/unittest
    pytest

    # Or set PYTHONPATH
    export PYTHONPATH=/path/to/pyzui:$PYTHONPATH
    pytest

**Qt Tests Failing:**

.. code-block:: bash

    # Solution: Ensure Qt dependencies installed
    pip install PySide6

    # For headless environments, use virtual display
    Xvfb :99 -screen 0 1024x768x24 &
    export DISPLAY=:99
    pytest

**Slow Tests:**

.. code-block:: bash

    # Run specific test file instead of all
    pytest test_specific.py

    # Or run in parallel
    pytest -n auto

**Mock Not Working:**

.. code-block:: python

    # Problem: Mocking wrong path
    @patch('module.Class')  # Wrong!

    # Solution: Mock where it's used, not where defined
    @patch('test_module.Class')  # Correct!

Debugging Tests
~~~~~~~~~~~~~~~

**Print Debugging:**

.. code-block:: bash

    pytest -v -s test_file.py::TestClass::test_method

**Use pdb:**

.. code-block:: python

    def test_method(self):
        obj = ClassName()
        import pdb; pdb.set_trace()  # Debugger stops here
        result = obj.method()
        assert result == expected

**Verbose Failure Output:**

.. code-block:: bash

    pytest -vv test_file.py

**Show Locals on Failure:**

.. code-block:: bash

    pytest -l test_file.py

Quick Reference
---------------

Essential Commands
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Run all tests
    pytest

    # Run with coverage
    pytest --cov=pyzui

    # Run specific file
    pytest test_file.py

    # Run specific test
    pytest test_file.py::TestClass::test_method

    # Stop on first failure
    pytest -x

    # Show print output
    pytest -s

    # Parallel execution
    pytest -n auto

    # Generate HTML report
    pytest --html=report.html

Essential Imports
~~~~~~~~~~~~~~~~~

.. code-block:: python

    import pytest
    from unittest.mock import Mock, patch, MagicMock, mock_open

    # Pytest features
    pytest.approx()      # Floating point comparison
    pytest.raises()      # Exception testing
    pytest.skip()        # Skip test
    pytest.fixture()     # Test fixture
    pytest.mark.parametrize()  # Parameterized tests

Common Patterns
~~~~~~~~~~~~~~~

.. code-block:: python

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

    # Approximate comparison
    assert value == pytest.approx(expected, rel=1e-6)

    # Skip test
    if condition:
        pytest.skip("Reason for skipping")

Resources
---------

Documentation
~~~~~~~~~~~~~

- **Pytest**: https://docs.pytest.org/
- **Unittest.mock**: https://docs.python.org/3/library/unittest.mock.html
- **Coverage.py**: https://coverage.readthedocs.io/

PyZUI-Specific
~~~~~~~~~~~~~~

- :doc:`../technicaldocumentation/objectsystem` - Understanding object architecture
- :doc:`../technicaldocumentation/tilingsystem` - Understanding tile system
- :doc:`../technicaldocumentation/convertersystem` - Understanding converters
- :doc:`../technicaldocumentation/windowsystem` - Understanding UI components

Example Test Files
~~~~~~~~~~~~~~~~~~

Reference these for patterns:

- ``test/unittest/objects/mediaobjects/test_physicalobject.py`` - Complete coverage example
- ``test/unittest/tilesystem/test_tilecache.py`` - Cache testing patterns
- ``test/unittest/converters/test_vipsconverter.py`` - Integration test example
- ``test/unittest/test_new_dynamictileprovider_TEMPLATE.py`` - New component template

Conclusion
----------

The PyZUI test suite provides comprehensive coverage of all major components using pytest
and BDD-style documentation. When adding new features:

1. Write tests first (TDD) or alongside implementation
2. Follow existing patterns and conventions
3. Use the template for new DynamicTileProviders
4. Aim for >80% coverage
5. Test edge cases and error handling
6. Keep tests independent and focused
7. Mock external dependencies
8. Document with Given-When-Then scenarios

Well-tested code enables confident refactoring, prevents regressions, and serves as
executable documentation of expected behavior.
