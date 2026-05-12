#!/usr/bin/env python
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

import argparse
import json
import os
import sys
from typing import Any

from PySide6 import QtGui, QtWidgets

import pyzui.tilesystem.tilemanager as TileManager
from pyzui.config import ConfigManager, ValidationError
from pyzui.logger import LoggerConfig, get_logger
from pyzui.windows.mainwindow import MainWindow


def load_config_file(config_path: str) -> dict[str, Any]:
    """Load configuration from JSON file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary

    Raises:
        ValidationError: If file cannot be loaded or contains invalid JSON
    """
    try:
        with open(config_path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in config file {config_path}: {e}") from e
    except OSError as e:
        raise ValidationError(f"Cannot read config file {config_path}: {e}") from e


def apply_command_line_args(config: dict[str, Any], args) -> dict[str, Any]:
    """Apply command-line arguments to configuration.

    Args:
        config: Current configuration
        args: Parsed command-line arguments

    Returns:
        Updated configuration with command-line overrides
    """
    result = config.copy()

    # Logging arguments
    if args.debug:
        result["logging"]["debug"] = True
    if args.verbose:
        result["logging"]["verbose"] = True
    if args.log_dir:
        # Expand tilde in command-line argument
        result["logging"]["log_dir"] = os.path.expanduser(args.log_dir)
    if args.console:
        result["logging"]["log_to_console"] = True
    if args.no_console:
        result["logging"]["log_to_console"] = False
    if args.no_file:
        result["logging"]["log_to_file"] = False
    if args.no_color:
        result["logging"]["colored_output"] = False

    # Tilestore arguments
    if args.no_cleanup:
        result["tilestore"]["auto_cleanup"] = False
    if args.cleanup_age:
        result["tilestore"]["max_age_days"] = args.cleanup_age
    if args.fast_cleanup:
        result["tilestore"]["collect_cleanup_stats"] = False

    # Autosave arguments
    if args.autosave_interval:
        result["autosave"]["interval"] = args.autosave_interval * 60
        result["autosave"]["enabled"] = True
    if args.autosave_max_backups:
        result["autosave"]["max_backups"] = args.autosave_max_backups
        result["autosave"]["enabled"] = True
    if args.backup_expire_days:
        result["autosave"]["expire_days"] = args.backup_expire_days
    if args.no_autosave:
        result["autosave"]["enabled"] = False

    # Zoom arguments
    if args.default_zoom:
        result["zoom"]["default_zoomlevel"] = args.default_zoom

    return result


def parse_arguments():
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="PyZUI - Python Zooming User Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                      # Run with default settings (logs to console and file)
  %(prog)s --no-console         # Disable console output (file only)
  %(prog)s --debug              # Run in debug mode with console output
  %(prog)s --verbose            # Run with verbose logging to console
  %(prog)s --config pyzui.json  # Load settings from config file
  %(prog)s --no-file            # Log to console only (disable file logging)
  %(prog)s --log-dir /tmp/logs  # Use custom log directory
  %(prog)s --autosave-interval 2  # Set autosave interval to 2 minutes
  %(prog)s --autosave-max-backups 30  # Set maximum backups to keep
  %(prog)s --backup-expire-days 14  # Set backup directory expiration to 14 days
  %(prog)s --no-autosave        # Disable autosave feature
        """,
    )

    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode (maximum logging detail)")

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode (detailed info logging)")

    parser.add_argument("--config", type=str, metavar="FILE", help="Path to configuration file (JSON format)")

    parser.add_argument("--log-dir", type=str, metavar="DIR", help="Directory for log files (default: ./logs)")

    parser.add_argument("--console", action="store_true", help="Enable console logging (default: enabled)")

    parser.add_argument("--no-console", action="store_true", help="Disable console logging (default: enabled)")

    parser.add_argument("--no-file", action="store_true", help="Disable file logging")

    parser.add_argument("--no-color", action="store_true", help="Disable colored console output")

    parser.add_argument("--no-cleanup", action="store_true", help="Disable automatic tilestore cleanup on startup")

    parser.add_argument(
        "--cleanup-age", type=int, metavar="DAYS", help="Maximum age in days for tilestore cleanup (default: 3)"
    )

    parser.add_argument(
        "--fast-cleanup",
        action="store_true",
        help="Use fast cleanup mode (skips detailed statistics for faster startup)",
    )

    parser.add_argument(
        "--autosave-interval", type=int, metavar="MINUTES", help="Autosave interval in minutes (default: 5)"
    )

    parser.add_argument(
        "--autosave-max-backups", type=int, metavar="COUNT", help="Maximum number of backups to keep (default: 20)"
    )

    parser.add_argument(
        "--backup-expire-days", type=int, metavar="DAYS", help="Days after which backup directories expire (default: 7)"
    )

    parser.add_argument("--no-autosave", action="store_true", help="Disable autosave feature")

    parser.add_argument(
        "--default-zoom", type=float, metavar="LEVEL", help="Default zoom level for new scenes (e.g., -4.0)"
    )

    return parser.parse_args()


def main():
    """Start the PyZUI application."""

    # Parse command-line arguments
    args = parse_arguments()

    # Initialize ConfigManager
    config_manager = ConfigManager()

    try:
        # Load user configuration (creates default if missing)
        config = config_manager.load()

        # Apply --config file override if specified
        if args.config:
            # Expand tilde in config file path
            config_path = os.path.expanduser(args.config)
            override_config = load_config_file(config_path)
            config = config_manager.merge_override(override_config)

        # Apply command-line arguments (highest priority)
        config = apply_command_line_args(config, args)

        # Final validation
        config_manager._validate_config(config)

    except ValidationError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # Set working directory
    if os.path.dirname(__file__):
        os.chdir(os.path.dirname(__file__))

    # Initialize logging system
    LoggerConfig.initialize(
        debug=config["logging"]["debug"],
        log_to_file=config["logging"]["log_to_file"],
        log_to_console=config["logging"]["log_to_console"],
        log_dir=config["logging"].get("log_dir"),
        colored_output=config["logging"]["colored_output"],
        verbose=config["logging"]["verbose"],
    )

    logger = get_logger("main")
    logger.info("Starting PyZUI application")
    logger.debug(f"Working directory: {os.getcwd()}")
    logger.debug(f"Python version: {sys.version}")

    # Initialize TileManager (cleanup registered for shutdown execution)
    TileManager.init(
        auto_cleanup=config["tilestore"]["auto_cleanup"],
        cleanup_max_age_days=config["tilestore"]["max_age_days"],
        collect_cleanup_stats=config["tilestore"]["collect_cleanup_stats"],
    )

    # Initialize ZoomManager for enforcing zoom limits
    from pyzui.objects.objectsutils import ZoomManager
    from pyzui.objects.physicalobject import PhysicalObject

    zoom_config = config.get("zoom", {})
    zoom_manager = ZoomManager(zoom_config)
    PhysicalObject.set_zoom_manager(zoom_manager)
    logger.info(f"Zoom limits initialized: {zoom_manager.get_limits()}")

    # Initialize SVG cache (cleanup registered for shutdown execution)
    from pyzui.objects.mediaobjects.mediaobjectsutils.svg.svgcache.svgcache import get_svg_cache

    svg_cache = get_svg_cache()
    logger.debug(f"SVG cache initialized at {svg_cache.cache_root}")

    # Perform startup cleanup of old cache files (older than 2 weeks)
    if config["tilestore"]["auto_cleanup"]:
        files_removed, bytes_freed = svg_cache.cleanup_old_files(max_age_days=14)
        logger.info(f"SVG cache startup cleanup: removed {files_removed} old files, freed {bytes_freed} bytes")

    # Create Qt application
    app = QtWidgets.QApplication(sys.argv)

    # Unified shutdown of all background threads — runs before cleanup handlers,
    # so threads are joined before Qt begins destroying internals
    def _shutdown_all_threads() -> None:
        """Orchestrate shutdown of all background threads."""
        TileManager.shutdown()
        try:
            if window.zui and window.zui.scene:
                window.zui.scene.shutdown_threads()
        except Exception:
            pass

    app.aboutToQuit.connect(_shutdown_all_threads)

    # Connect Qt shutdown signal for cleanup
    if config["tilestore"]["auto_cleanup"]:
        app.aboutToQuit.connect(lambda: TileManager._shutdown_cleanup())
        logger.debug("Qt shutdown cleanup hook registered for tile manager")

    # Connect Qt shutdown signal for SVG cache cleanup
    app.aboutToQuit.connect(lambda: svg_cache.cleanup_on_exit())
    logger.debug("Qt shutdown cleanup hook registered for SVG cache")

    # Get absolute path to icon based on script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(script_dir, "data", "icon.png")

    # Load and set application icon with better error handling
    app_icon = None
    if os.path.exists(icon_path):
        try:
            app_icon = QtGui.QIcon(icon_path)
            if not app_icon.isNull():
                app.setWindowIcon(app_icon)
                logger.debug(f"Application icon loaded from {icon_path}")
                logger.debug(f"Icon available sizes: {app_icon.availableSizes()}")
            else:
                logger.warning(f"Failed to create QIcon from {icon_path} - icon is null")
        except Exception as e:
            logger.warning(f"Error loading icon from {icon_path}: {e}")
    else:
        logger.warning(f"Icon file not found at {icon_path}")

    # Create and show main window with icon
    window = MainWindow(icon=app_icon, config=config, autosave_config=config.get("autosave"))
    window.show()
    logger.info("Main window displayed")

    # Start event loop
    logger.info("Entering Qt event loop")
    exit_code = app.exec()
    logger.info(f"Application exiting with code {exit_code}")

    # Migrate legacy flat backup files on shutdown
    try:
        from pyzui.backup.backupmanager import BackupManager

        bm = BackupManager(config.get("autosave", {}))
        deleted = bm.cleanup_flat_backups()
        if deleted:
            logger.info(f"Migrated {deleted} legacy flat backup files on shutdown")
    except Exception as e:
        logger.debug(f"Migration cleanup skipped or failed: {e}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
