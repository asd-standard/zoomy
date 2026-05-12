.. PyZui user instruction file,

Program Configuration
=====================

PyZUI uses a single source of truth configuration system with `~/.pyzui/config.json`
as the primary configuration file. Configuration options can be overridden via:

Configuration Hierarchy::

    1. User Configuration File (~/.pyzui/config.json) - Primary source
              ↓
    2. Temporary Configuration File (--config pyzui.json) - Session override
              ↓
    3. Command-Line Arguments - Highest priority (temporary)

This design provides a consistent configuration experience where user preferences
are stored in `~/.pyzui/config.json` and can be temporarily overridden for testing
or debugging via command-line arguments.

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

**Parallel Rendering Configuration**
    Controls the parallel text rendering system for improved performance.

    - ``enabled`` (bool): Enable parallel text rendering (default: ``True``)
    - ``max_workers`` (int): Maximum number of worker threads (default: 4)
    - ``batch_size`` (int): Number of text objects per batch (default: 10)
    - ``max_batches`` (int): Maximum batches to process (default: 10)
    - ``batch_timeout_ms`` (int): Timeout for batch processing in milliseconds (default: 1000)
    - ``enable_profiling`` (bool): Enable performance profiling (default: ``False``)
    - ``priority_thresholds`` (dict): Priority thresholds for rendering:
        - ``high`` (float): High priority threshold (default: 100.0)
        - ``medium`` (float): Medium priority threshold (default: 500.0)
        - ``low`` (float): Low priority threshold (default: 2000.0)
    - ``cache_max_age_ms`` (int): Maximum age for cached layouts in milliseconds (default: 1000)
    - ``viewport_update_threshold`` (float): Viewport update threshold (default: 10.0)

**Autosave Configuration**
    Controls automatic backup creation for scene files.

    - ``enabled`` (bool): Enable autosave functionality (default: ``True``)
    - ``interval`` (int): Autosave interval in seconds (default: 300 = 5 minutes)
    - ``max_backups`` (int): Maximum number of backups to keep per scene (default: 20)
    - ``backup_dir`` (str): Root directory for per-scene backup directories (default: ``~/.pyzui/backups``)
    - ``expire_days`` (int): Days of inactivity before a scene's backup directory is deleted (default: 7)

**Zoom Limits Configuration**
    Controls the minimum and maximum zoom levels allowed in the application.
    These limits prevent crashes when inserting StringMediaObjects at extreme zoom levels.

    - ``min_zoom`` (int): Minimum allowed zoom level (default: ``-10``)
    - ``max_zoom`` (int): Maximum allowed zoom level (default: ``+12``)

    .. note::
        The default limits (-10 to +12) are specifically chosen to prevent crashes
        when inserting StringMediaObjects. At zoom levels below -10, font sizes
        become less than 1 point, causing rendering issues.

    .. note::
        If ``min_zoom`` is set greater than ``max_zoom``, the values are automatically
        swapped to maintain logical consistency.

**Render Order Configuration**
    Controls the stacking order of media objects on screen.

    - ``order`` (str): Render order mode. Valid values are ``"smaller_on_top"``
      (default) and ``"larger_on_top"``.

      - ``"smaller_on_top"``: Smaller objects are painted last and appear on top of
        larger ones.
      - ``"larger_on_top"``: Larger objects are painted last and appear on top of
        smaller ones.

    This setting can also be toggled at runtime via **View → Render Order:
    Smaller on Top (Ctrl+R)**.

Using Configuration Files
~~~~~~~~~~~~~~~~~~~~~~~~~~

PyZUI uses `~/.pyzui/config.json` as its primary configuration file. This file is
automatically created with default values if it doesn't exist.

You can also create a temporary configuration file (e.g., ``pyzui_config.json``) with
your preferred settings for testing or specific sessions:

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
            "cleanup_on_startup": true,
            "collect_cleanup_stats": true
        },
        "parallel_rendering": {
            "enabled": true,
            "max_workers": 4,
            "batch_size": 10,
            "max_batches": 10,
            "batch_timeout_ms": 1000,
            "enable_profiling": false,
            "priority_thresholds": {
                "high": 100.0,
                "medium": 500.0,
                "low": 2000.0
            },
            "cache_max_age_ms": 1000,
            "viewport_update_threshold": 10.0
        },
        "autosave": {
            "enabled": true,
            "interval": 300,
            "max_backups": 20,
            "backup_dir": "~/.pyzui/backups",
            "expire_days": 7
        },
        "zoom_limits": {
            "min_zoom": -10,
            "max_zoom": 12
        },
        "render": {
            "order": "smaller_on_top"
        }
    }

Then launch PyZUI with the temporary configuration file:

.. code-block:: bash

    python main.py --config pyzui_config.json

.. note::
    The ``--config`` file provides temporary overrides for the current session only.
    Settings from this file are not saved to `~/.pyzui/config.json`. To make permanent
    changes, edit `~/.pyzui/config.json` directly.

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

**Autosave Arguments:**

.. code-block:: bash

    --autosave-interval MINUTES   # Set autosave interval in minutes
    --autosave-max-backups COUNT  # Set maximum number of backups to keep per scene
    --backup-expire-days DAYS     # Days before inactive scene backup dirs expire (default: 7)
    --no-autosave                 # Disable autosave functionality

**Zoom Limits Arguments:**

.. code-block:: bash

    --min-zoom LEVEL            # Set minimum zoom level (default: -10)
    --max-zoom LEVEL            # Set maximum zoom level (default: +12)

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

**Example 8: Configure Autosave Behavior**

.. code-block:: bash

    # Enable autosave with 1-minute interval, keep 50 backups per scene, 14-day expiration
    python main.py --autosave-interval 1 --autosave-max-backups 50 --backup-expire-days 14

    # Disable autosave entirely
    python main.py --no-autosave

    # Configure via JSON file
    python main.py --config pyzui_config_example.json

    # Set backup expiration to 30 days
    python main.py --backup-expire-days 30

    # Default: autosave enabled, 5-minute interval, keep 20 backups per scene, 7-day expiration
    python main.py

**Example 9: Configure Zoom Limits**

.. code-block:: bash

    # Set custom zoom limits for specialized workflows
    python main.py --min-zoom -5 --max-zoom 20

    # Use default zoom limits for StringMediaObject compatibility
    python main.py

    # Configure via JSON file
    python main.py --config pyzui_config_example.json

    # Default: zoom limits -10 to +12 for StringMediaObject compatibility
    python main.py

Default Configuration
~~~~~~~~~~~~~~~~~~~~~

When PyZUI starts for the first time (or when `~/.pyzui/config.json` doesn't exist),
it creates the configuration file with these default values:

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
            'cleanup_on_startup': True,
            'collect_cleanup_stats': True
        },
        'parallel_rendering': {
            'enabled': True,
            'max_workers': 4,
            'batch_size': 10,
            'max_batches': 10,
            'batch_timeout_ms': 1000,
            'enable_profiling': False,
            'priority_thresholds': {
                'high': 100.0,
                'medium': 500.0,
                'low': 2000.0
            },
            'cache_max_age_ms': 1000,
            'viewport_update_threshold': 10.0
        },
        'autosave': {
            'enabled': True,
            'interval': 300,
            'max_backups': 20,
            'backup_dir': '~/.pyzui/backups',
            'expire_days': 7
        }
    }

This results in:
    - No console logging (silent operation)
    - File logging at INFO level to ./logs/pyzui.log
    - Automatic tilestore cleanup on startup
    - Tiles older than 3 days are removed
    - Parallel rendering enabled for performance
    - Autosave enabled with 5-minute interval, keeping 20 backups per scene, 7-day expiration
    - Zoom limits set to -10 (minimum) and +12 (maximum) for StringMediaObject compatibility

Configuration Validation
~~~~~~~~~~~~~~~~~~~~~~~~

PyZUI validates all configuration values when loading configuration files. Invalid
values are rejected with clear error messages. The validation rules include:

- **Type checking**: All configuration values must be of the correct type (boolean,
  integer, float, string, or dictionary as specified).
- **Range validation**: Numeric values must be within valid ranges (e.g., 
  ``autosave.interval`` must be at least 60 seconds, ``autosave.max_backups`` 
  must be at least 1).
- **Priority thresholds**: For ``parallel_rendering.priority_thresholds``, the values
  must satisfy ``low > medium > high``.
- **Zoom limits**: For ``zoom_limits``, if ``min_zoom`` is greater than ``max_zoom``,
  the values are automatically swapped to maintain logical consistency.
- **Unknown keys**: Unknown configuration sections or keys are rejected.

If PyZUI fails to start with a configuration error, check your configuration file
for invalid values or syntax errors.

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
