.. PyZui user instruction file,

Program Configuration
=====================

PyZUI uses a flexible three-tier configuration system that allows you to customize
the application's behavior. Configuration options are applied in the following order
of precedence (later sources override earlier ones):

Configuration Hierarchy::

    1. Default Configuration (built into main.py)
              ↓
    2. JSON Configuration File (--config pyzui.json)
              ↓
    3. Command-Line Arguments (highest priority)

This design allows you to set baseline configuration in a JSON file while being able to
quickly override specific settings via command-line flags for testing or debugging.

Configuration Categories
~~~~~~~~~~~~~~~~~~~~~~~~

**Logging Configuration**
    Controls how PyZUI logs information during execution.

    .. note::
        By default, PyZUI logs only to file (not to console) for silent operation.
        Use ``--console`` to enable console output.

    - ``debug`` (bool): Enable debug mode with maximum logging detail
    - ``verbose`` (bool): Enable verbose mode with detailed info logging
    - ``log_to_file`` (bool): Write logs to rotating log files (default: ``True``)
    - ``log_to_console`` (bool): Display logs in the terminal (default: ``False``)
    - ``colored_output`` (bool): Use ANSI color codes in console output
    - ``log_dir`` (str): Directory path for log files (default: ``./logs``)

**Tilestore Configuration**
    Controls the tile caching system's automatic cleanup behavior.

    - ``auto_cleanup`` (bool): Automatically remove old tiles on startup
    - ``max_age_days`` (int): Maximum age in days for cached tiles (default: 3)
    - ``cleanup_on_startup`` (bool): Run cleanup when application starts

Using a JSON Configuration File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a configuration file (e.g., ``pyzui_config.json``) with your preferred settings:

.. code-block:: json

    {
        "logging": {
            "debug": false,
            "verbose": true,
            "log_to_file": true,
            "log_to_console": true,
            "colored_output": true,
            "log_dir": "logs"
        },
        "tilestore": {
            "auto_cleanup": true,
            "max_age_days": 7,
            "cleanup_on_startup": true
        }
    }

Then launch PyZUI with the configuration file:

.. code-block:: bash

    python main.py --config pyzui_config.json

Command-Line Arguments
~~~~~~~~~~~~~~~~~~~~~~

All configuration options can be overridden via command-line arguments:

**Logging Arguments:**

.. code-block:: bash

    -d, --debug              # Enable debug mode (maximum logging detail)
    -v, --verbose            # Enable verbose mode (detailed info logging)
    --log-dir DIR            # Custom directory for log files
    --console                # Enable console logging (default: disabled)
    --no-console             # Disable console logging
    --no-file                # Disable file logging
    --no-color               # Disable colored console output

**Tilestore Arguments:**

.. code-block:: bash

    --no-cleanup             # Disable automatic tilestore cleanup
    --cleanup-age DAYS       # Set maximum age for tiles (in days)

Configuration Examples
~~~~~~~~~~~~~~~~~~~~~~

**Example 1: Development Mode with Full Debug Logging**

.. code-block:: bash

    # Run with debug logging to both console and file
    python main.py --debug --console

    # This enables:
    # - DEBUG level console output
    # - DEBUG level file logging
    # - Colored console output
    # - File logging to ./logs/pyzui.log

**Example 2: Production Mode with Custom Log Directory**

.. code-block:: bash

    # Run with default settings (file only) to custom directory
    python main.py --log-dir /var/log/pyzui

    # This enables:
    # - No console output (default)
    # - Full logging to /var/log/pyzui/pyzui.log
    # - Default tilestore cleanup

**Example 3: Quick Testing Without Logging**

.. code-block:: bash

    # Run without any logging for performance testing
    python main.py --no-file

**Example 4: Extended Tile Cache**

.. code-block:: bash

    # Keep tiles cached for 30 days instead of default 3
    python main.py --cleanup-age 30

**Example 5: Combining Config File and CLI Overrides**

Create ``production.json``:

.. code-block:: json

    {
        "logging": {
            "verbose": false,
            "log_to_console": false,
            "log_dir": "/var/log/pyzui"
        },
        "tilestore": {
            "max_age_days": 30
        }
    }

Run with temporary debug override and console output:

.. code-block:: bash

    # Use production config but enable debug and console for this session
    python main.py --config production.json --debug --console

    # Result: Production settings are loaded, but debug mode and
    # console output override the settings from the config file

**Example 6: Console-Only Logging for Development**

.. code-block:: bash

    # Log only to console (no file) with verbose output
    python main.py --verbose --console --no-file

**Example 7: Custom Log Directory Structure**

.. code-block:: bash

    # Organize logs by date in a custom location
    python main.py --log-dir ~/pyzui-logs/$(date +%Y-%m-%d)

Default Configuration
~~~~~~~~~~~~~~~~~~~~~

If no configuration file or command-line arguments are provided, PyZUI uses these defaults:

.. code-block:: python

    {
        'logging': {
            'debug': False,
            'verbose': False,
            'log_to_file': True,
            'log_to_console': False,
            'colored_output': True,
            'log_dir': 'logs'
        },
        'tilestore': {
            'auto_cleanup': True,
            'max_age_days': 3,
            'cleanup_on_startup': True
        }
    }

This results in:
    - No console logging (silent operation)
    - File logging at INFO level to ./logs/pyzui.log
    - Automatic tilestore cleanup on startup
    - Tiles older than 3 days are removed

Viewing Current Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PyZUI logs its active configuration when starting. To view this information, either enable
console output with ``--console`` or check the log file:

.. code-block:: bash

    # View configuration on console
    python main.py --console

    # Or check the log file
    tail -f logs/pyzui.log

Look for output like:

.. code-block:: text

    [INFO    ] pyzui.LoggerConfig       | ============================================================
    [INFO    ] pyzui.LoggerConfig       | PyZUI Logging System Initialized
    [INFO    ] pyzui.LoggerConfig       | Debug Mode: False
    [INFO    ] pyzui.LoggerConfig       | Console Level: OFF
    [INFO    ] pyzui.LoggerConfig       | File Level: INFO
    [INFO    ] pyzui.LoggerConfig       | Log File: /path/to/logs/pyzui.log
    [INFO    ] pyzui.LoggerConfig       | ============================================================

Log File Management
~~~~~~~~~~~~~~~~~~~

PyZUI uses rotating log files to prevent unlimited disk usage:

- **Maximum file size**: 10 MB per log file
- **Backup count**: 5 rotated files kept
- **Total maximum size**: ~50 MB (current + 5 backups)
- **File naming**:
    - Current log: ``pyzui.log``
    - Rotated logs: ``pyzui.log.1``, ``pyzui.log.2``, etc.

When the current log reaches 10 MB, it's rotated automatically:

.. code-block:: text

    logs/
    ├── pyzui.log       # Current log (newest)
    ├── pyzui.log.1     # Previous rotation
    ├── pyzui.log.2     # Older rotation
    ├── pyzui.log.3     # Even older
    ├── pyzui.log.4     # Getting old
    └── pyzui.log.5     # Oldest (will be deleted on next rotation)
