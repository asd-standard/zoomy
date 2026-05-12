.. Configuration System Documentation

Configuration System
====================

This document provides a comprehensive overview of the configuration system in PyZUI,
explaining how user settings are loaded, validated, merged, and persisted. The configuration
system is the central hub through which all other subsystems receive their settings.

Overview
--------

The configuration system is responsible for:

1. Loading user configuration from ``~/.pyzui/config.json``
2. Validating all values against a schema of 43+ rules across 6 sections
3. Merging CLI overrides (``--config``) with per-key granularity
4. Auto-creating the config file and directory on first run
5. Expanding tilde paths (``~``) in string values
6. Auto-swapping inverted zoom limits (``min > max``) and clamping defaults

The system uses :class:`ConfigManager` as the single source of truth. Every
subsystem — logging, tilestore, parallel rendering, autosave, zoom, and render
order — reads its settings through a unified validation pipeline.

Architecture
------------

.. code-block:: text

    ┌─────────────────────────────────────────────────────────────┐
    │                     ConfigManager                           │
    │  • DEFAULT_CONFIG — 6 sections with factory defaults        │
    │  • VALIDATION_SCHEMA — 43+ per-key validation rules         │
    │  • ~/.pyzui/config.json — single source of truth            │
    └─────────────┬───────────────────────────────────────────────┘
                  │
                  │ load() / save() / merge_override()
                  │
    ┌─────────────┼───────────────────────────────────────────────┐
    │             ▼                                               │
    │  ┌────────────────────────────────────────────────────┐     │
    │  │ load() — Application startup                       │     │
    │  │  1. Create config dir if missing                   │     │
    │  │  2. Create default config.json if missing          │     │
    │  │  3. Load JSON from disk                            │     │
    │  │  4. Merge with DEFAULT_CONFIG (fill missing)       │     │
    │  │  5. Expand tilde paths                             │     │
    │  │  6. Validate against VALIDATION_SCHEMA             │     │
    │  │  7. Save validated config (fixes gaps)             │     │
    │  └────────────────────────────────────────────────────┘     │
    │             │                                               │
    │             ▼                                               │
    │  ┌────────────────────────────────────────────────────┐     │
    │  │ Consumer subsystems read their section:            │     │
    │  │  • LoggerConfig ← config["logging"]                │     │
    │  │  • TileManager  ← config["tilestore"]              │     │
    │  │  • Scene        ← config["parallel_rendering"]     │     │
    │  │  • Scene        ← config["autosave"]               │     │
    │  │  • Scene        ← config["zoom"]                   │     │
    │  │  • Scene        ← config["render"]                 │     │
    │  └────────────────────────────────────────────────────┘     │
    │                                                             │
    │             ┌──────────────────────────┐                    │
    │             │ merge_override() — --config file              │
    │             │  • Deep-merge CLI config into defaults        │
    │             │  • Validate merged result                     │
    │             │  • Does NOT persist to disk                   │
    │             └──────────────────────────┘                    │
    └─────────────────────────────────────────────────────────────┘

Configuration Sections
----------------------

Default Configuration
~~~~~~~~~~~~~~~~~~~~~

The ``DEFAULT_CONFIG`` class attribute defines factory defaults for every
supported configuration key:

.. code-block:: python

    ConfigManager.DEFAULT_CONFIG = {
        "logging": {
            "debug": False,
            "verbose": False,
            "log_to_file": True,
            "log_to_console": True,
            "colored_output": True,
            "log_dir": "logs",
        },
        "tilestore": {
            "auto_cleanup": True,
            "max_age_days": 3,
            "cleanup_on_startup": True,
            "collect_cleanup_stats": True,
        },
        "parallel_rendering": {
            "enabled": True,
            "max_workers": 4,
            "batch_size": 10,
            "max_batches": 10,
            "batch_timeout_ms": 1000,
            "enable_profiling": False,
            "priority_thresholds": {"high": 100.0, "medium": 500.0, "low": 2000.0},
            "cache_max_age_ms": 1000,
            "viewport_update_threshold": 10.0,
        },
        "autosave": {
            "enabled": True,
            "interval": 300,
            "max_backups": 20,
            "backup_dir": "~/.pyzui/backups",
            "expire_days": 7,
        },
        "zoom": {"min_zoomlevel": -12.0, "max_zoomlevel": 10.0,
                  "clamp_enabled": True, "default_zoomlevel": -4.0},
        "render": {"order": "smaller_on_top"},
    }

Section Consumers
~~~~~~~~~~~~~~~~~

Each configuration section feeds a specific subsystem:

.. list-table::
   :header-rows: 1

   * - Section
     - Consumer
     - Purpose
   * - ``logging``
     - :class:`LoggerConfig`
     - Console/file log levels, colors, and output targets
   * - ``tilestore``
     - :class:`TileManager`
     - Auto-cleanup timing, stats collection
   * - ``parallel_rendering``
     - :class:`SceneParallelRenderer`
     - Thread pool size, batch processing, priority thresholds
   * - ``autosave``
     - :class:`SceneAutosaveManager`
     - Backup interval, rotation count, expiration
   * - ``zoom``
     - :class:`ZoomManager`
     - Zoom level clamping limits and default zoom
   * - ``render``
     - :class:`Scene`
     - Render order: ``smaller_on_top`` or ``larger_on_top``

Validation Schema
-----------------

The ``VALIDATION_SCHEMA`` class attribute defines 43+ per-key validation
rules organized as ``(section, key) -> rule`` mappings. Each rule specifies:

- ``type``: Expected Python type (``int``, ``bool``, ``str``, or tuple of types)
- ``min``: Minimum allowed value (numeric types only)
- ``message``: Human-readable error message
- ``required_keys``: For dictionary-type values (e.g., ``priority_thresholds``)

**Example schema entries:**

.. code-block:: python

    ("autosave", "interval"): {
        "type": int, "min": 60,
        "message": "Autosave interval must be at least 60 seconds (1 minute)",
    },
    ("autosave", "enabled"): {
        "type": bool, "message": "enabled must be true or false",
    },
    ("logging", "log_dir"): {
        "type": str, "message": "log_dir must be a string",
    },
    ("render", "order"): {
        "type": str, "message": "render.order must be a string",
    },

**Special Validation Rules:**

Three keys have validation logic beyond simple type/range checking:

.. code-block:: text

    render.order
        Must be one of: "smaller_on_top", "larger_on_top".
        Any other value is rejected with a clear error message.

    priority_thresholds
        Must contain all three keys: "high", "medium", "low".
        Must satisfy: low > medium > high.
        Values outside this ordering are rejected.

    zoom.{min,max,default}_zoomlevel
        If min > max: auto-swap them (silent correction).
        If default < min: clamp default to min.
        If default > max: clamp default to max.

Loading and Saving
------------------

Load Flow (``load()``)
~~~~~~~~~~~~~~~~~~~~~~

The ``load()`` method is called at application startup:

.. code-block:: text

    1. Create ~/.pyzui/ directory if missing
    2. If ~/.pyzui/config.json does not exist:
       → Write DEFAULT_CONFIG and return it
    3. Parse config.json as JSON
       → On parse failure: raise ValidationError
       → On IO error: raise OSError
    4. Merge loaded config with DEFAULT_CONFIG
       → Missing sections are filled from defaults
       → Unknown sections (not in DEFAULT_CONFIG) are rejected
       → Unknown keys within known sections are rejected
    5. Expand tilde paths in string values (recursively)
       → ~/.pyzui/backups becomes /home/user/.pyzui/backups
    6. Validate merged config against VALIDATION_SCHEMA
       → On failure: raise ValidationError with all errors listed
    7. Save validated config (writes missing fields back to disk)
    8. Return validated config copy

**Error Accumulation:**

Unlike early-exit validation, ``_validate_config()`` collects **all**
validation errors into a list, then raises a single ``ValidationError``
with every error listed:

.. code-block:: text

    Configuration validation failed:
      - Unknown configuration key: 'logging.foo'
      - Invalid type for 'autosave.interval': expected int, got str
      - Invalid value for 'autosave.interval': must be at least 60, got 30

This gives the user a complete picture of what needs fixing in one pass.

Merge Override (``merge_override()``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``--config`` CLI flag loads a separate JSON file and merges it into
the current configuration. The merge is **temporary** — it does not
persist to ``~/.pyzui/config.json``. This is useful for:

- Testing configuration changes without modifying the persistent config
- Per-session overrides (e.g., enable debug logging for one run)
- CI/test environments where file-based config is preferred over CLI flags

**Deep Merge Algorithm:**

.. code-block:: python

    def _deep_merge(base, override):
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = _deep_merge(result[key], value)  # Recurse into dicts
            else:
                result[key] = value  # Overwrite scalar or replace whole dict
        return result

This allows partial overrides — you can specify only ``"logging": {"debug": true}``
in your override file and all other settings remain unchanged.

Tilde Path Expansion
~~~~~~~~~~~~~~~~~~~~

After merging but before validation, all string values in the config are
recursively scanned for tilde (``~``) and expanded using ``os.path.expanduser()``:

.. code-block:: python

    def _expand_paths(self, config):
        expanded = {}
        for key, value in config.items():
            if isinstance(value, dict):
                expanded[key] = self._expand_paths(value)  # Recurse
            elif isinstance(value, str) and "~" in value:
                expanded[key] = os.path.expanduser(value)
            else:
                expanded[key] = value
        return expanded

This runs on both ``load()`` and ``save()`` paths, ensuring ``backup_dir``
and other path-containing values are always in their expanded form.

Save Flow (``save()``)
~~~~~~~~~~~~~~~~~~~~~~

The ``save()`` method persists configuration to disk:

1. If a config dict is provided: merge it with defaults (fill missing sections)
2. Expand tilde paths
3. Validate the merged config
4. Write to ``~/.pyzui/config.json`` as indented JSON (``indent=2``)
5. Return ``True`` on success, ``False`` on ``OSError``

Config File Format
------------------

The configuration file lives at ``~/.pyzui/config.json`` and uses standard
JSON with 2-space indentation:

.. code-block:: json

    {
      "logging": {
        "debug": false,
        "verbose": false,
        "log_to_file": true,
        "log_to_console": true,
        "colored_output": true,
        "log_dir": "logs"
      },
      "tilestore": {
        "auto_cleanup": true,
        "max_age_days": 3,
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
        "backup_dir": "/home/user/.pyzui/backups",
        "expire_days": 7
      },
      "zoom": {
        "min_zoomlevel": -12.0,
        "max_zoomlevel": 10.0,
        "clamp_enabled": true,
        "default_zoomlevel": -4.0
      },
      "render": {
        "order": "smaller_on_top"
      }
    }

CLI Integration
---------------

Configuration is loaded in ``main.py`` after argument parsing:

.. code-block:: text

    Parse CLI Args → Load Config → Merge Override → Distribute to Subsystems

    1. argparse parses --config, --debug, --verbose, --no-console, etc.
    2. ConfigManager.load() reads ~/.pyzui/config.json
    3. If --config FILE is provided:
       → Load FILE as JSON
       → config.merge_override(override_config)
       → Result is used for this session only (not persisted)
    4. CLI flags (--debug, --verbose) override config values at runtime
    5. Config sections are distributed:
       → LoggerConfig.initialize(**config["logging"])
       → TileManager.init(**config["tilestore"])
       → Scene.__init__(config=config)

.. note::

   CLI flags take precedence over both the config file and override config.
   For example, ``--debug`` always enables debug logging regardless of
   what ``config.json`` or ``--config`` specify.

Error Handling
--------------

**ValidationError Hierarchy:**

All configuration errors are reported as :class:`ValidationError` (a custom
exception inheriting from ``Exception``). The error message includes every
violation found:

.. code-block:: python

    try:
        config = config_manager.load()
    except ValidationError as e:
        print(f"Invalid configuration:\n{e}")
    except OSError as e:
        print(f"Cannot read config file: {e}")
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in config: {e}")

**ConfigManager Exceptions:**

.. list-table::
   :header-rows: 1

   * - Exception
     - Condition
     - Raised By
   * - ``ValidationError``
     - Invalid config structure, unknown keys, wrong types, out-of-range
     - ``load()``, ``save()``, ``merge_override()``
   * - ``OSError``
     - Cannot read or write config file (permissions, disk full)
     - ``load()``, ``save()``
   * - ``json.JSONDecodeError``
     - Config file contains malformed JSON
     - ``load()``

Usage Examples
--------------

Loading Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pyzui.config import ConfigManager

    manager = ConfigManager()
    config = manager.load()

    # Read specific settings
    log_level = config["logging"]["verbose"]
    autosave_interval = config["autosave"]["interval"]
    render_order = config["render"]["order"]

    print(f"Config file: {manager.get_config_path()}")

Saving Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pyzui.config import ConfigManager

    manager = ConfigManager()
    config = manager.load()

    # Modify settings
    config["autosave"]["interval"] = 600  # 10 minutes
    config["render"]["order"] = "larger_on_top"

    # Save (validates before writing)
    try:
        manager.save(config)
        print("Configuration saved successfully")
    except ValidationError as e:
        print(f"Invalid configuration: {e}")

Temporary Overrides (--config)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pyzui.config import ConfigManager
    import json

    manager = ConfigManager()
    manager.load()  # Load persistent config

    # Load override from file (like --config CLI flag)
    with open("override.json") as f:
        override = json.load(f)

    # Merge override (temporary, not persisted)
    merged = manager.merge_override(override)

    # Use merged config for this session
    print(f"Debug logging: {merged['logging']['debug']}")

Custom Config Path (Testing)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pyzui.config import ConfigManager

    # Use a test-specific config file
    manager = ConfigManager(config_file="/tmp/test_config.json")
    config = manager.load()  # Creates test_config.json with defaults

    # Verify defaults
    assert config["autosave"]["enabled"] is True
    assert config["autosave"]["interval"] == 300

API Reference
-------------

ConfigManager
~~~~~~~~~~~~~

.. py:class:: ConfigManager

   Central configuration manager. Defaults to ``~/.pyzui/config.json``.

   .. py:attribute:: DEFAULT_CONFIG
      :type: dict

      Factory defaults for all 6 configuration sections.

   .. py:attribute:: VALIDATION_SCHEMA
      :type: dict

      43+ per-key validation rules.

   .. py:method:: __init__(config_file: str | None = None)

      Initialize with optional custom config file path.

   .. py:method:: load() -> dict[str, Any]

      Load, merge, validate, expand, and save config. Returns validated config.

   .. py:method:: save(config: dict[str, Any] | None = None) -> bool

      Validate and persist config to disk. Returns True on success.

   .. py:method:: merge_override(override_config: dict[str, Any]) -> dict[str, Any]

      Deep-merge an override config. Returns merged result. Does not persist.

   .. py:method:: get_config_path() -> str

      Return the filesystem path to the config file.

   .. py:method:: get_config_dir() -> str

      Return the directory containing the config file.

   .. py:method:: _expand_paths(config: dict) -> dict

      Recursively expand tilde in string values.

   .. py:method:: _merge_with_defaults(user_config: dict) -> dict

      Fill missing sections from DEFAULT_CONFIG. Reject unknown sections.

   .. py:method:: _validate_config(config: dict) -> None

      Validate all keys against VALIDATION_SCHEMA. Raises ValidationError.

   .. py:method:: _validate_override_config(config: dict) -> None

      Validate override config structure (section-level only).

   .. py:method:: _deep_merge(base: dict, override: dict) -> dict

      Recursively merge two configuration dictionaries.

ValidationError
~~~~~~~~~~~~~~~

.. py:class:: ValidationError

   Raised when configuration validation fails. Contains a human-readable
   message listing all validation errors found.

See Also
--------

- :doc:`../usageinstructions/programconfiguration` — User-facing configuration guide
- :doc:`logging` — Logging system configuration
- :doc:`objectsystem` — Scene configuration (autosave, zoom, render order)
- :doc:`tilingsystem` — Tilestore configuration (cleanup)
- :doc:`backup` — Autosave configuration
- :doc:`projectstructure` — Project organization
