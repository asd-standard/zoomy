==================
Logging System
==================

Overview
========

PyZUI implements a centralized logging system that provides consistent, configurable logging across all modules. The system is designed to facilitate debugging, track application behavior, and diagnose issues effectively.

Architecture
============

The logging system is built around the ``LoggerConfig`` class in ``pyzui/logger.py``, which provides:

* **Centralized configuration** - Single initialization point for all logging behavior
* **Multiple output targets** - Console and/or file logging with independent level control
* **Color-coded console output** - Visual identification of log levels (optional)
* **Rotating log files** - Automatic file rotation to manage disk space (10 MB max, 5 backups)
* **Runtime control** - Dynamic log level adjustment during execution
* **Per-module loggers** - Granular control over individual module logging

Log Levels
==========

The system uses Python's standard logging levels:

+-------------+-------+---------------------------------------------------+
| Level       | Value | Usage                                             |
+=============+=======+===================================================+
| DEBUG       | 10    | Detailed diagnostic information for development   |
+-------------+-------+---------------------------------------------------+
| INFO        | 20    | General informational messages about normal flow  |
+-------------+-------+---------------------------------------------------+
| WARNING     | 30    | Potentially harmful situations (default level)    |
+-------------+-------+---------------------------------------------------+
| ERROR       | 40    | Serious problems that need attention              |
+-------------+-------+---------------------------------------------------+
| CRITICAL    | 50    | Critical failures that may halt the application   |
+-------------+-------+---------------------------------------------------+

Level Behavior by Mode
-----------------------

The effective log level depends on the execution mode:

**Normal Mode** (default)
    - Console: WARNING and above
    - File: INFO and above

**Verbose Mode** (``--verbose``)
    - Console: INFO and above
    - File: DEBUG and above

**Debug Mode** (``--debug``)
    - Console: DEBUG and above
    - File: DEBUG and above

Configuration
=============

Command-Line Interface
----------------------

The primary way to configure logging is through command-line arguments:

.. code-block:: bash

   # Enable debug mode (maximum detail)
   python main.py --debug

   # Enable verbose mode (informational messages)
   python main.py --verbose

   # Specify custom log directory
   python main.py --log-dir /tmp/pyzui-logs

   # Disable console output (file logging only)
   python main.py --no-console

   # Disable file logging (console only)
   python main.py --no-file

   # Disable colored output
   python main.py --no-color

Configuration File
------------------

Logging can also be configured via JSON configuration file:

.. code-block:: json

   {
     "logging": {
       "debug": false,
       "verbose": true,
       "log_to_file": true,
       "log_to_console": true,
       "colored_output": true,
       "log_dir": "logs"
     }
   }

Load the configuration with:

.. code-block:: bash

   python main.py --config pyzui_config.json

Programmatic Configuration
---------------------------

Initialize logging programmatically using the ``LoggerConfig`` class:

.. code-block:: python

   from pyzui.logger import LoggerConfig

   LoggerConfig.initialize(
       debug=True,              # Enable debug mode
       log_to_file=True,        # Enable file logging
       log_to_console=True,     # Enable console logging
       log_dir='custom_logs',   # Custom log directory
       colored_output=True,     # Enable colored console output
       verbose=False            # Verbose mode
   )

Usage
=====

Basic Usage in Modules
-----------------------

To use logging in your code, import the ``get_logger`` function:

.. code-block:: python

   from pyzui.logger import get_logger

   class MyClass:
       def __init__(self):
           self.logger = get_logger('MyClass')
           self.logger.info('MyClass initialized')

       def process_data(self, data):
           self.logger.debug(f'Processing data: {data}')
           try:
               result = self._compute(data)
               self.logger.info(f'Processing successful: {result}')
               return result
           except Exception as e:
               self.logger.error(f'Processing failed: {e}')
               raise

Logging Exceptions
------------------

Use ``logger.exception()`` to automatically include traceback information:

.. code-block:: python

   try:
       risky_operation()
   except Exception as e:
       # Logs the exception with full traceback
       self.logger.exception('Operation failed')
       # Alternative with custom message
       self.logger.exception(f'Failed to process {item}: {e}')

Runtime Control
---------------

Adjust logging behavior during execution:

.. code-block:: python

   from pyzui.logger import LoggerConfig
   import logging

   # Enable debug mode at runtime
   LoggerConfig.enable_debug()

   # Disable debug mode
   LoggerConfig.disable_debug()

   # Set specific log level globally
   LoggerConfig.set_level(logging.INFO)

   # Set log level for specific module
   LoggerConfig.set_level(logging.DEBUG, module='TileManager')

   # Get log file path
   log_path = LoggerConfig.get_log_file_path()
   print(f'Logs are being written to: {log_path}')

Effective Debugging Strategies
===============================

Progressive Debugging
---------------------

Start with higher log levels and progressively increase detail:

1. **Start with ERROR/WARNING** - Identify obvious problems
2. **Enable INFO** - Understand application flow
3. **Enable DEBUG** - Examine detailed behavior
4. **Enable per-module DEBUG** - Focus on specific components

Example workflow:

.. code-block:: bash

   # Step 1: Check for errors
   python main.py | grep ERROR

   # Step 2: Add context with verbose mode
   python main.py --verbose

   # Step 3: Full debugging for specific issue
   python main.py --debug

   # Step 4: Review detailed logs in file
   tail -f logs/pyzui.log | grep TileManager

Debugging Specific Components
------------------------------

For targeted debugging, enable debug logging only for specific modules:

.. code-block:: python

   from pyzui.logger import LoggerConfig
   import logging

   # Initialize with normal logging
   LoggerConfig.initialize()

   # Enable debug only for TileManager
   LoggerConfig.set_level(logging.DEBUG, module='TileManager')

   # Enable debug for multiple specific modules
   for module in ['TileManager', 'TileCache', 'TileStore']:
       LoggerConfig.set_level(logging.DEBUG, module=module)

Strategic Log Placement
-----------------------

Place log statements strategically for maximum debugging value:

**At Entry Points**
    Log function entry with key parameters:

    .. code-block:: python

       def load_tile(self, tile_id, level):
           self.logger.debug(f'load_tile called: tile_id={tile_id}, level={level}')

**At Decision Points**
    Log conditional branches:

    .. code-block:: python

       if tile in self.cache:
           self.logger.debug(f'Tile {tile_id} found in cache')
       else:
           self.logger.debug(f'Tile {tile_id} not in cache, loading from disk')

**At State Changes**
    Log significant state transitions:

    .. code-block:: python

       self.logger.info(f'Scene state changed: {old_state} -> {new_state}')

**Before Expensive Operations**
    Log before time-consuming operations:

    .. code-block:: python

       self.logger.debug(f'Starting conversion of {image_path} ({size} MB)')
       result = self.converter.convert(image_path)
       self.logger.debug(f'Conversion completed in {elapsed}s')

**At Error Boundaries**
    Log at exception handling points:

    .. code-block:: python

       try:
           result = operation()
       except SpecificError as e:
           self.logger.error(f'Specific error occurred: {e}')
           # Handle error
       except Exception as e:
           self.logger.exception(f'Unexpected error: {e}')
           raise

Performance Considerations
--------------------------

Logging can impact performance. Follow these guidelines:

**Avoid Logging in Tight Loops**
    Don't log every iteration:

    .. code-block:: python

       # Bad: logs millions of times
       for i in range(1000000):
           self.logger.debug(f'Processing item {i}')

       # Good: logs periodically
       total = len(items)
       self.logger.info(f'Processing {total} items')
       for i, item in enumerate(items):
           # Log every 10,000 items
           if i % 10000 == 0:
               self.logger.debug(f'Progress: {i}/{total} ({i*100//total}%)')

**Use Lazy Formatting**
    Let the logger handle string formatting:

    .. code-block:: python

       # Good: formatting only happens if message is logged
       self.logger.debug('Processing tile %s at level %d', tile_id, level)

       # Also good: f-strings are acceptable
       self.logger.debug(f'Processing tile {tile_id} at level {level}')

**Disable File Logging for Performance Testing**
    When measuring performance, disable file I/O:

    .. code-block:: bash

       python main.py --no-file

Log Output Formats
==================

Console Format
--------------

The console output uses a compact format for readability:

.. code-block:: text

   [LEVEL   ] ModuleName               | Message

Example output:

.. code-block:: text

   [INFO    ] main                      | Starting PyZUI application
   [DEBUG   ] TileManager               | Initializing tile cache with 100 MB
   [WARNING ] Scene                     | Object 'text1' outside visible bounds
   [ERROR   ] PDFConverter              | Failed to convert document.pdf: File not found

When colored output is enabled (default), each level has a distinct color:

* **DEBUG**: Cyan
* **INFO**: Green
* **WARNING**: Yellow
* **ERROR**: Red
* **CRITICAL**: Magenta

File Format
-----------

Log files include additional information for post-mortem analysis:

.. code-block:: text

   YYYY-MM-DD HH:MM:SS | [LEVEL   ] | ModuleName               | FunctionName         | Message

Example output:

.. code-block:: text

   2025-12-09 14:23:45 | [INFO    ] | main                      | main                 | Starting PyZUI application
   2025-12-09 14:23:45 | [DEBUG   ] | TileManager               | __init__             | Initializing tile cache with 100 MB
   2025-12-09 14:23:46 | [WARNING ] | Scene                     | add_object           | Object 'text1' outside visible bounds
   2025-12-09 14:23:47 | [ERROR   ] | PDFConverter              | convert              | Failed to convert document.pdf: File not found

File Management
===============

Log File Location
-----------------

By default, logs are written to:

.. code-block:: text

   ./logs/pyzui.log

Specify a custom location with:

.. code-block:: bash

   python main.py --log-dir /var/log/pyzui

Rotation Strategy
-----------------

Log files automatically rotate when they reach 10 MB. The system maintains:

* ``pyzui.log`` - Current log file
* ``pyzui.log.1`` - Previous log file
* ``pyzui.log.2`` - Second previous log file
* ``pyzui.log.3`` - Third previous log file
* ``pyzui.log.4`` - Fourth previous log file
* ``pyzui.log.5`` - Fifth previous log file (oldest retained)

When ``pyzui.log`` reaches 10 MB:
1. ``pyzui.log.5`` is deleted
2. ``pyzui.log.4`` → ``pyzui.log.5``
3. ``pyzui.log.3`` → ``pyzui.log.4``
4. ``pyzui.log.2`` → ``pyzui.log.3``
5. ``pyzui.log.1`` → ``pyzui.log.2``
6. ``pyzui.log`` → ``pyzui.log.1``
7. New ``pyzui.log`` is created

Viewing Logs
------------

Common commands for log analysis:

.. code-block:: bash

   # View real-time logs
   tail -f logs/pyzui.log

   # Search for errors
   grep ERROR logs/pyzui.log

   # View recent errors
   grep ERROR logs/pyzui.log | tail -20

   # Find logs for specific module
   grep TileManager logs/pyzui.log

   # View logs with context (5 lines before/after)
   grep -C 5 "Exception" logs/pyzui.log

   # Count errors by type
   grep ERROR logs/pyzui.log | cut -d'|' -f4 | sort | uniq -c

API Reference
=============

LoggerConfig Class
------------------

.. py:class:: LoggerConfig

   Centralized logger configuration for PyZUI.

   .. py:method:: initialize(debug=False, log_to_file=True, log_to_console=True, log_dir=None, colored_output=True, verbose=False)

      Initialize the logging system.

      :param bool debug: Enable debug mode (sets console level to DEBUG)
      :param bool log_to_file: Enable logging to file
      :param bool log_to_console: Enable logging to console
      :param str log_dir: Directory for log files (default: ./logs)
      :param bool colored_output: Enable colored console output
      :param bool verbose: Enable verbose mode (shows more detailed info)

   .. py:method:: get_logger(name)

      Get a logger instance for the specified module.

      :param str name: Name of the module/class requesting the logger
      :return: Configured logger instance
      :rtype: logging.Logger

   .. py:method:: set_level(level, module=None)

      Change the logging level at runtime.

      :param int level: Logging level (e.g., logging.DEBUG, logging.INFO)
      :param str module: Specific module name, or None for all modules

   .. py:method:: enable_debug()

      Enable debug mode at runtime.

   .. py:method:: disable_debug()

      Disable debug mode at runtime.

   .. py:method:: get_log_file_path()

      Get the path to the current log file.

      :return: Path to log file, or None if file logging is disabled
      :rtype: Path

Convenience Functions
---------------------

.. py:function:: get_logger(name)

   Convenience function to get a logger instance.

   :param str name: Name of the module/class requesting the logger
   :return: Configured logger instance
   :rtype: logging.Logger

   Example:

   .. code-block:: python

      from pyzui.logger import get_logger

      logger = get_logger('MyModule')
      logger.info('Module initialized')

Best Practices
==============

Log Level Selection
-------------------

Choose appropriate log levels based on the significance of the message:

**DEBUG**
    * Internal state changes
    * Function entry/exit points
    * Detailed parameter values
    * Iteration progress
    * Cache hits/misses

**INFO**
    * Significant state transitions
    * Successful completion of major operations
    * Configuration values on startup
    * User-initiated actions

**WARNING**
    * Deprecated features in use
    * Recoverable errors
    * Unexpected but handled conditions
    * Performance degradation
    * Resource limits approaching

**ERROR**
    * Failed operations that require intervention
    * Unhandled but caught exceptions
    * Data corruption or loss
    * Configuration errors

**CRITICAL**
    * Application cannot continue
    * Severe system failures
    * Data integrity compromised

Message Content
---------------

Write clear, actionable log messages:

**Good Messages**
    .. code-block:: python

       logger.error(f'Failed to load tile {tile_id} at level {level}: {error}')
       logger.debug(f'Cache hit for tile {tile_id} (size: {size} bytes)')
       logger.warning(f'Tile generation took {elapsed}s, expected <1s')

**Poor Messages**
    .. code-block:: python

       logger.error('Error')  # No context
       logger.debug('Here')   # Unclear location
       logger.warning('Something wrong')  # No specifics

Include Context
---------------

Provide sufficient context for debugging:

.. code-block:: python

   # Include relevant identifiers
   self.logger.error(f'Failed to process tile={tile_id}, level={level}, coord=({x},{y})')

   # Include state information
   self.logger.debug(f'Cache status: {len(self.cache)}/{self.max_cache} tiles')

   # Include timing information
   self.logger.info(f'Operation completed in {elapsed:.2f}s')

   # Include error details
   self.logger.exception(f'Conversion failed for {path}: {e}')

Avoid Sensitive Data
--------------------

Don't log sensitive information:

.. code-block:: python

   # Bad: logs password
   logger.debug(f'Connecting to {host} with password {password}')

   # Good: omits password
   logger.debug(f'Connecting to {host}')

   # Bad: logs entire user object (may contain sensitive data)
   logger.debug(f'User data: {user}')

   # Good: logs only necessary information
   logger.debug(f'Processing request for user_id={user.id}')

Troubleshooting
===============

Common Issues
-------------

**No logs appearing**
    - Verify logging is initialized (should be automatic in main.py)
    - Check log level is appropriate for the messages
    - Ensure handlers are configured:

    .. code-block:: python

       from pyzui.logger import LoggerConfig
       LoggerConfig.initialize(debug=True)

**Too much console output**
    - Run without ``--debug`` or ``--verbose`` flags
    - Disable console logging: ``python main.py --no-console``
    - Use file logging for detailed logs: ``python main.py --verbose --no-console``

**Cannot find log files**
    - Check log file path:

    .. code-block:: python

       from pyzui.logger import LoggerConfig
       print(LoggerConfig.get_log_file_path())

    - Verify log directory exists and is writable
    - Check if file logging is enabled (not using ``--no-file``)

**Colors not showing in console**
    - Ensure terminal supports ANSI color codes
    - Try disabling and re-enabling: ``python main.py --no-color`` then run normally
    - Check if running in environment that strips color codes

**Log file not rotating**
    - Check file permissions on log directory
    - Verify files aren't being held open by other processes
    - Check disk space availability

Migration from Old System
=========================

If you have old code using the standard logging module directly:

**Old Code**

.. code-block:: python

   import logging

   class MyClass:
       def __init__(self):
           self.__logger = logging.getLogger("MyClass")

       def my_method(self):
           self.__logger.debug("Processing")

**New Code**

.. code-block:: python

   from pyzui.logger import get_logger

   class MyClass:
       def __init__(self):
           self.logger = get_logger("MyClass")

       def my_method(self):
           self.logger.debug("Processing")

All existing logger method calls (``.debug()``, ``.info()``, ``.warning()``, ``.error()``, ``.critical()``, ``.exception()``) work identically.

Examples
========

Complete Debugging Session
---------------------------

Here's a complete example of debugging a tile loading issue:

**Step 1: Identify the problem**

.. code-block:: bash

   $ python main.py
   [ERROR   ] TileManager               | Failed to load tile 12345

**Step 2: Enable verbose logging**

.. code-block:: bash

   $ python main.py --verbose
   [INFO    ] TileManager               | Loading tile 12345 from cache
   [INFO    ] TileCache                 | Cache miss for tile 12345
   [INFO    ] TileManager               | Loading tile 12345 from disk
   [ERROR   ] TileManager               | Failed to load tile 12345

**Step 3: Enable full debug logging**

.. code-block:: bash

   $ python main.py --debug
   [DEBUG   ] TileManager               | Searching for tile 12345 in cache
   [DEBUG   ] TileCache                 | Cache stats: 245/1000 tiles, 45 MB/100 MB
   [DEBUG   ] TileCache                 | Tile 12345 not in cache
   [DEBUG   ] TileManager               | Computing tile path: level=3, x=456, y=789
   [DEBUG   ] TileManager               | Tile path: /data/tiles/3/456/789.png
   [DEBUG   ] TileManager               | Checking if file exists: /data/tiles/3/456/789.png
   [ERROR   ] TileManager               | File not found: /data/tiles/3/456/789.png

**Step 4: Review detailed logs**

.. code-block:: bash

   $ grep "tile 12345" logs/pyzui.log
   2025-12-09 14:23:45 | [DEBUG   ] | TileManager  | load_tile     | Loading tile 12345
   2025-12-09 14:23:45 | [ERROR   ] | TileManager  | load_tile     | Failed to load tile 12345

Now we know the issue: the tile file doesn't exist at the expected path.

Conditional Debugging
---------------------

Enable debugging conditionally based on runtime conditions:

.. code-block:: python

   from pyzui.logger import LoggerConfig, get_logger
   import logging

   class TileManager:
       def __init__(self):
           self.logger = get_logger('TileManager')
           self.debug_tile_ids = set()  # Tiles to debug

       def enable_tile_debugging(self, tile_id):
           """Enable detailed logging for specific tile."""
           self.debug_tile_ids.add(tile_id)

       def load_tile(self, tile_id):
           # Temporarily enable debug for this tile if marked
           if tile_id in self.debug_tile_ids:
               old_level = logging.getLogger(f'pyzui.{self.logger.name}').level
               LoggerConfig.set_level(logging.DEBUG, module='TileManager')

           self.logger.debug(f'Loading tile {tile_id}')
           # ... tile loading logic ...

           # Restore old level
           if tile_id in self.debug_tile_ids:
               LoggerConfig.set_level(old_level, module='TileManager')

Performance Profiling with Logging
-----------------------------------

Use logging to identify performance bottlenecks:

.. code-block:: python

   import time
   from pyzui.logger import get_logger

   class Converter:
       def __init__(self):
           self.logger = get_logger('Converter')

       def convert(self, input_path, output_path):
           start = time.time()
           self.logger.debug(f'Starting conversion: {input_path}')

           # Step 1
           step_start = time.time()
           self._load_image(input_path)
           self.logger.debug(f'Image loaded in {time.time()-step_start:.3f}s')

           # Step 2
           step_start = time.time()
           self._process_image()
           self.logger.debug(f'Image processed in {time.time()-step_start:.3f}s')

           # Step 3
           step_start = time.time()
           self._save_image(output_path)
           self.logger.debug(f'Image saved in {time.time()-step_start:.3f}s')

           total = time.time() - start
           self.logger.info(f'Conversion completed in {total:.3f}s')

           if total > 5.0:
               self.logger.warning(f'Slow conversion detected: {total:.3f}s for {input_path}')

See Also
========

* :doc:`contributiongiudelines` - Guidelines for contributing to PyZUI
* :doc:`installation` - Installation instructions
* :doc:`main` - Main documentation
