## PyZUI - Python Zooming User Interface
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

"""SceneAutosaveManager - Autosave functionality for Scene class.

This class manages automatic backup creation for scene files with configurable
interval and rotation. It was extracted from the Scene class to improve
modularity and maintainability.
"""

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyzui.backup.backupmanager import BackupManager

from PySide6 import QtCore
from PySide6.QtCore import QMetaObject, Qt, QThread


def stop_timer_safely(timer):
    """Safely stop a QTimer, ensuring thread safety.

    This function ensures that QTimer.stop() is called from the same
    thread that created the timer, preventing Qt threading errors.

    Args:
        timer: QTimer instance to stop, or None
    """
    if not timer:
        return

    if timer.isActive():
        if timer.thread() == QThread.currentThread():
            timer.stop()
        else:
            QMetaObject.invokeMethod(timer, "stop", Qt.QueuedConnection)


class SceneAutosaveManager:
    """Manager for scene autosave functionality.

    This class handles automatic backup creation for scene files with
    configurable interval and rotation. It manages the backup timer,
    configuration, and integration with the BackupManager.

    Attributes:
        _scene: Reference to the parent Scene object
        _logger: Logger instance for autosave operations
        _autosave_enabled: Whether autosave is enabled
        _autosave_interval: Autosave interval in seconds
        _autosave_config: Autosave configuration dictionary
        _autosave_timer: QTimer for periodic autosave
        _autosave_active: Whether autosave timer is active
        _backup_manager: BackupManager instance for creating backups
        _last_save_path: Path of last saved scene file
    """

    def __init__(self, scene, config: dict[str, Any] | None = None):
        """Initialize SceneAutosaveManager.

        Args:
            scene: Parent Scene object
            config: Optional configuration dictionary with autosave settings
        """
        self._scene = scene
        self._logger = logging.getLogger(__name__)

        # Get autosave config or use defaults
        autosave_config = config.get("autosave", {}) if config else {}
        self._autosave_enabled: bool = autosave_config.get("enabled", True)  # Enabled by default
        self._autosave_interval: int = autosave_config.get("interval", 300)  # Default: 300 seconds = 5 minutes
        self._autosave_config: dict[str, Any] = autosave_config

        self._autosave_timer: QtCore.QTimer | None = None
        self._backup_manager: BackupManager | None = None
        self._autosave_active: bool = False
        self._cleanup_performed: bool = False

        # Enable autosave immediately if configured
        if self._autosave_enabled:
            self._enable_autosave_if_configured()

    def _enable_autosave_if_configured(self) -> None:
        """Enable autosave if configured in settings.

        Creates backup manager, runs expiration cleanup, and starts
        autosave timer.
        """
        if self._autosave_enabled and not self._autosave_active:
            try:
                # Import locally to avoid circular imports
                from pyzui.backup.backupmanager import BackupManager

                self._backup_manager = BackupManager(self._autosave_config)

                # Clean up expired backup directories on startup
                expired = self._backup_manager.cleanup_expired_dirs()
                if expired:
                    self._logger.info(f"Cleaned up {expired} expired backup directories on startup")

                self._autosave_active = True
                self._cleanup_performed = True

                interval_minutes = max(1, self._autosave_interval // 60)
                self._logger.info(
                    f"Autosave enabled with interval: {interval_minutes} minutes ({self._autosave_interval} seconds)"
                )

                # Start autosave timer (convert seconds to minutes)
                interval_minutes = max(1, self._autosave_interval // 60)  # At least 1 minute
                self.enable_autosave(interval_minutes)
            except ImportError as e:
                self._logger.error(f"Failed to import BackupManager: {e}")
                self._autosave_active = False
            except Exception as e:
                self._logger.error(f"Failed to enable autosave: {e}")
                self._autosave_active = False

    def _trigger_autosave_backup(self, filename: str) -> None:
        """Trigger autosave backup creation via BackupManager.

        Args:
            filename: Path to the scene file to backup
        """
        if self._backup_manager and self._autosave_active:
            try:
                self._backup_manager.create_backup(filename)
                self._logger.debug(f"Autosave backup created for: {filename}")
            except Exception as e:
                self._logger.error(f"Error during autosave backup: {e}")

    def _autosave_timeout(self) -> None:
        """Timer callback for periodic autosave.

        Called when autosave timer expires to create a backup.
        """
        if self._autosave_active and hasattr(self._scene, "_Scene__last_save_path"):
            last_save_path = self._scene._Scene__last_save_path
            if last_save_path:
                self._trigger_autosave_backup(last_save_path)

    def enable_autosave(self, interval_minutes: int) -> None:
        """Enable autosave with specified interval.

        Starts QTimer for periodic autosave.

        Args:
            interval_minutes: Autosave interval in minutes (minimum 1)
        """
        if interval_minutes < 1:
            self._logger.warning(f"Invalid autosave interval: {interval_minutes} minutes")
            return

        self._autosave_interval = interval_minutes * 60
        self._autosave_enabled = True
        self._autosave_active = True

        # Create and start timer if not already exists
        if self._autosave_timer is None:
            self._autosave_timer = QtCore.QTimer()
            self._autosave_timer.timeout.connect(self._autosave_timeout)

        # Convert minutes to milliseconds
        interval_ms = interval_minutes * 60 * 1000
        self._autosave_timer.start(interval_ms)
        self._logger.info(f"Autosave timer started with {interval_minutes} minute interval")

    def cleanup_legacy_backups(self) -> int:
        """Clean up legacy flat backup files from old backup structure.

        Called during application shutdown to migrate from the old flat
        backup system to the new per-scene directory structure.

        Returns:
            int: Number of legacy backup files deleted
        """
        if self._backup_manager:
            return self._backup_manager.cleanup_flat_backups()
        return 0

    def disable_autosave(self) -> None:
        """Disable autosave and stop timer safely.

        Idempotent: if autosave is already disabled, this is a no-op.
        """
        if not self._autosave_enabled and not self._autosave_active:
            return

        if self._autosave_timer:
            if self._autosave_timer.isActive():
                self._logger.debug(f"Stopping autosave timer safely (active: {self._autosave_timer.isActive()})")
                stop_timer_safely(self._autosave_timer)
            else:
                self._logger.debug("Autosave timer already stopped")
        else:
            self._logger.debug("No autosave timer to stop")

        self._autosave_enabled = False
        self._autosave_active = False
        self._logger.info("Autosave disabled")

    def is_autosave_enabled(self) -> bool:
        """Check if autosave is currently enabled.

        Returns:
            True if autosave is enabled, False otherwise
        """
        return self._autosave_enabled and self._autosave_active

    def get_autosave_interval(self) -> int:
        """Get current autosave interval in seconds.

        Returns:
            Autosave interval in seconds
        """
        return self._autosave_interval

    def get_autosave_config(self) -> dict[str, Any]:
        """Get autosave configuration.

        Returns:
            Dictionary with autosave configuration
        """
        return self._autosave_config.copy()

    def set_autosave_config(self, config: dict[str, Any]) -> None:
        """Update autosave configuration.

        Args:
            config: Dictionary with autosave configuration updates
        """
        old_interval = self._autosave_interval
        old_enabled = self._autosave_enabled

        # Update configuration
        self._autosave_config.update(config)
        self._autosave_enabled = config.get("enabled", self._autosave_enabled)
        self._autosave_interval = config.get("interval", self._autosave_interval)

        # Restart autosave if configuration changed
        if old_interval != self._autosave_interval or old_enabled != self._autosave_enabled:
            if self._autosave_enabled:
                interval_minutes = max(1, self._autosave_interval // 60)
                self.enable_autosave(interval_minutes)
            else:
                self.disable_autosave()

    def update_last_save_path(self, filename: str) -> None:
        """Update the last save path and trigger autosave if enabled.

        Args:
            filename: Path to the saved scene file
        """
        # Store last save path in scene
        if hasattr(self._scene, "_Scene__last_save_path"):
            self._scene._Scene__last_save_path = filename

        # Create backup if autosave enabled
        if self._autosave_enabled and self._autosave_active:
            self._trigger_autosave_backup(filename)

    def __del__(self):
        """Ensure autosave timer is stopped before destruction.

        This prevents Qt threading errors when Python garbage collects
        SceneAutosaveManager instances while their QTimer is still running.
        """
        try:
            self._logger.debug("SceneAutosaveManager destructor called, stopping autosave timer")
            self.disable_autosave()
        except Exception as e:
            self._logger.debug(f"Ignoring error in SceneAutosaveManager destructor: {e}")
