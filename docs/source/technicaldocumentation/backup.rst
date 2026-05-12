Backup System
=============

The backup system provides automatic backup creation for scene files with
per-scene directories, configurable interval, rotation, and expiration policies.

Overview
--------

The backup system creates timestamped backups of scene files in per-scene
directories under ``~/.pyzui/backups/``. Each scene file gets its own
backup directory named ``{scene_filename}_{4char_path_hash}/``, containing
backups named ``yy_mm_dd_hh_mm_filename_hash.pzs`` with chronological sorting.

Scene directories expire after a configurable number of days of inactivity
and are automatically garbage-collected.

Key Features
------------

- **Per-scene directories**: Each scene file has its own backup directory,
  isolating rotation and preventing cross-scene interference
- **Timer-based autosave**: Creates backups at configurable intervals (default: 5 minutes)
- **File rotation**: Keeps last N backups per scene (configurable), deletes oldest automatically
- **Directory expiration**: Scene directories expire after ``expire_days`` of inactivity
  and are automatically cleaned up
- **Collision avoidance**: Directory name includes path hash; individual backup
  filenames include a timestamp hash to prevent collisions
- **Error handling**: Graceful error recovery with user notifications
- **Configurable**: All settings can be configured via UI, CLI, or configuration files
- **Enabled by default**: Autosave is active from application start
- **Legacy migration**: Old flat backup files are cleaned up automatically on shutdown

Backup Directory Structure
--------------------------

Backups are stored with per-scene subdirectories:

.. code-block:: text

    ~/.pyzui/backups/
    ├── myscene_a1b2/
    │   ├── 26_05_03_14_30_myscene_c3d4.pzs    # Backup file (timestamp_filename_hash.pzs)
    │   ├── 26_05_03_14_35_myscene_e5f6.pzs
    │   └── 26_05_03_14_40_myscene_g7h8.pzs
    ├── project1_h9i0/
    │   ├── 26_05_03_14_25_project1_j1k2.pzs
    │   └── 26_05_03_14_30_project1_l3m4.pzs
    └── test-scene_n5o6/
        └── 26_05_03_14_20_test-scene_p7q8.pzs

Scene Directory Naming
----------------------

Scene directories follow the format: ``{filename_stem}_{4char_path_hash}``

- **Filename stem**: The original scene filename without extension (for human readability)
- **Path hash**: 4-character hexadecimal MD5 hash of the absolute file path (for uniqueness)

This ensures that the same scene file at the same location always maps to
the same backup directory, while different scenes (even with the same
filename at different locations) get separate directories.

File Naming Convention
----------------------

Backup files within each scene directory follow the format:
``yy_mm_dd_hh_mm_filename_hash.pzs``

- **Timestamp**: ``yy_mm_dd_hh_mm`` - Year, month, day, hour, minute (24-hour format)
- **Original filename**: The original scene filename without extension
- **Hash**: 4-character hexadecimal MD5 hash to prevent intra-minute collisions

Examples:
- ``26_05_03_14_30_myscene_a1b2.pzs`` - Backup of "myscene.pzs" at 14:30
- ``26_05_03_09_15_project_v2_c3d4.pzs`` - Backup of "project_v2.pzs" at 09:15

Rotation and Expiration
-----------------------

- **Rotation**: Each scene directory independently keeps its last ``max_backups`` files.
  When a new backup is created, the oldest excess files in that directory are deleted.
- **Expiration**: Scene directories are checked on backup creation and at startup.
  Directories whose mtime is older than ``expire_days`` are deleted entirely.
  Empty directories (no ``*.pzs`` files) are also cleaned up.

Configuration
-------------

Autosave behavior can be configured through:

1. **Command-line arguments**:
   - ``--autosave-interval MINUTES``: Set autosave interval in minutes
   - ``--autosave-max-backups COUNT``: Set maximum backups kept per scene
   - ``--backup-expire-days DAYS``: Set expiration period for inactive scene directories
   - ``--no-autosave``: Disable autosave

2. **JSON configuration file**:

   .. code-block:: json

       {
           "autosave": {
               "enabled": true,
               "interval": 300,
               "max_backups": 20,
               "backup_dir": "~/.pyzui/backups",
               "expire_days": 7
           }
       }

3. **UI Settings menu**: Settings → Autosave Settings

Default Settings
----------------

- **Enabled**: ``True`` (enabled by default from application start)
- **Interval**: 300 seconds (5 minutes)
- **Max backups**: 20 backups per scene
- **Expire days**: 7 days (inactive scene directories are deleted)
- **Backup location**: ``~/.pyzui/backups/``

Usage Flow
----------

1. **Application start**: Autosave is enabled by default. Expired backup
   directories are cleaned up.
2. **First save**: A per-scene backup directory is created (named
   ``{scene_filename}_{hash}``), and the first backup is stored inside it.
3. **Periodic backups**: Additional backups are created at configured intervals
   in the scene's directory.
4. **File rotation**: When the maximum backup count per scene is reached,
   oldest backups within that directory are deleted.
5. **Expiration**: Backup directories for scenes not saved for ``expire_days``
   days are deleted.
6. **Shutdown migration**: Legacy flat ``*.pzs`` files from the old backup
   system are cleaned up on application shutdown.

Error Handling
--------------

The backup system includes comprehensive error handling:

- **Permission errors**: Notifies user if backup directory cannot be created
- **Disk space errors**: Warns user if disk is full
- **File access errors**: Gracefully handles locked or inaccessible files

All errors are displayed to the user via Qt message boxes without blocking
application operation.

API Reference
-------------

BackupManager
~~~~~~~~~~~~~~~~~~~

.. automodule:: pyzui.backup.backupmanager
   :members:
   :undoc-members:
   :show-inheritance:

Main Methods
^^^^^^^^^^^^

- ``create_backup(scene_path: str) -> Optional[str]``: Create backup of scene file
  in its per-scene directory. Returns backup path. Triggers rotation and expiration cleanup.
- ``_get_scene_dir(source_path: str) -> Path``: Get per-scene backup directory path
  from source file path
- ``_rotate_backups(scene_dir: Path) -> None``: Rotate backups within a scene directory
- ``_cleanup_expired() -> int``: Delete expired backup directories
- ``cleanup_expired_dirs() -> int``: Public method to delete expired backup directories
- ``cleanup_flat_backups() -> int``: Delete legacy flat backup files (migration)
- ``get_backup_count(source_path=None) -> int``: Get backup count (per scene or global)
- ``list_backups(source_path=None) -> List[str]``: List backup files (per scene or global)
- ``cleanup_all() -> int``: Delete all backup files and directories

SceneAutosaveManager
~~~~~~~~~~~~~~~~~~~~~

.. automodule:: pyzui.objects.scene.sceneutils.autosave
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

UI Integration
--------------

The backup system is accessible through:

- **Settings menu**: Settings → Autosave Settings dialog
- **Configuration**: User preferences stored in ``~/.pyzui/config.json``

Testing
-------

The backup system includes comprehensive tests:

- **Unit tests**: ``test/unittest/backup/test_backupmanager.py`` (30 tests)
- **Scene integration tests**: ``test/unittest/objects/scene/test_scene_autosave.py``
- **UI tests**: ``test/unittest/windows/dialogwindows/test_autosavesettingsdialog.py``
- **Integration tests**: ``test/integrationtest/test_autosave_integration.py``

Example Usage
-------------

.. code-block:: python

    from pyzui.backup.backupmanager import BackupManager

    # Create backup manager with custom configuration
    config = {
        "max_backups": 10,
        "expire_days": 14,
        "enabled": True,
        "interval": 60
    }
    backup_manager = BackupManager(config)

    # Create backup of scene file
    backup_path = backup_manager.create_backup("/path/to/scene.pzs")

    if backup_path:
        print(f"Backup created successfully: {backup_path}")

        # List backups for this scene
        backups = backup_manager.list_backups("/path/to/scene.pzs")
        print(f"Total backups for this scene: {len(backups)}")
        for backup in backups[:5]:
            print(f"  - {backup}")

        # Check backup count for specific scene
        count = backup_manager.get_backup_count("/path/to/scene.pzs")
        print(f"Backups for scene: {count}")

        # Clean up expired directories
        expired = backup_manager.cleanup_expired_dirs()
        print(f"Cleaned up {expired} expired directories")
    else:
        print("Backup failed")

Command-Line Examples
----------------------

.. code-block:: bash

    # Default: autosave enabled, 5-minute interval, keep 20 backups, 7-day expiration
    python main.py

    # 1-minute interval, keep 50 backups per scene, 14-day expiration
    python main.py --autosave-interval 1 --autosave-max-backups 50 --backup-expire-days 14

    # Disable autosave
    python main.py --no-autosave

    # Configure via settings file
    python main.py --config pyzui_config_example.json

    # 10-minute interval only (uses defaults for other settings)
    python main.py --autosave-interval 10

    # Keep backups for 30 days before expiration
    python main.py --backup-expire-days 30
