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

"""Backup manager for automatic scene file backups with per-scene directories."""

import hashlib
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6 import QtWidgets

from pyzui.logger import get_logger


class BackupManager:
    """
    Constructor :
        BackupManager(config: Dict[str, Any])
    Parameters :
        config : Dict[str, Any]
            Configuration dictionary with autosave settings

    BackupManager(config) --> None

    Backup manager that creates per-scene backup directories under
    ~/.pyzui/backups/ with naming convention:
    {scene_filename}_{4char_path_hash}/

    Each scene directory contains backups named:
    yy_mm_dd_hh_mm_filename_hash.pzs

    Rotation is per-scene (keeps last N backups per scene).
    Scene directories expire after a configurable number of days
    since the last backup was written.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """
        Method :
            BackupManager.__init__(config)
        Parameters :
            config : Dict[str, Any]
                Configuration dictionary

        BackupManager.__init__(config) --> None

        Initialize backup manager with configuration.

        Args:
            config: Configuration dictionary with 'max_backups' (default: 20),
                    'expire_days' (default: 7), 'backup_dir' (default: ~/.pyzui/backups)
        """
        self._logger = get_logger("BackupManager")

        # Default configuration
        self._config = {
            "backup_dir": str(Path.home() / ".pyzui" / "backups"),
            "max_backups": 20,
            "expire_days": 7,
        }

        # Update with provided config
        if config:
            self._config.update(config)

        # Setup backup directory with tilde expansion as safety measure
        self._backup_dir = Path(self._config["backup_dir"]).expanduser()
        self._ensure_backup_dir()

        self._logger.debug(
            f"Backup manager initialized with directory: {self._backup_dir}, "
            f"max_backups: {self._config['max_backups']}, "
            f"expire_days: {self._config['expire_days']}"
        )

    def _get_scene_dir(self, source_path: str) -> Path:
        """
        Get the per-scene backup directory for a given source file.

        Directory name format: {filename_stem}_{4char_hash_of_absolute_path}

        Args:
            source_path: Path to the scene file

        Returns:
            Path: Per-scene backup directory path
        """
        abs_path = os.path.abspath(source_path)
        path_hash = hashlib.md5(abs_path.encode()).hexdigest()[:4]
        stem = Path(source_path).stem
        return self._backup_dir / f"{stem}_{path_hash}"

    def _ensure_backup_dir(self) -> None:
        """Ensure backup root directory exists."""
        try:
            self._backup_dir.mkdir(parents=True, exist_ok=True)
            self._logger.debug(f"Backup directory ready: {self._backup_dir}")
        except Exception as e:
            self._logger.error(f"Failed to create backup directory {self._backup_dir}: {e}")
            self._show_error_dialog(f"Failed to create backup directory: {e}")
            raise

    def _show_error_dialog(self, message: str) -> None:
        """Show error dialog without parent widget."""
        try:
            dialog = QtWidgets.QMessageBox()
            dialog.setIcon(QtWidgets.QMessageBox.Critical)
            dialog.setWindowTitle("Backup Error")
            dialog.setText(message)
            dialog.setStandardButtons(QtWidgets.QMessageBox.Ok)
            dialog.exec()
        except Exception as e:
            self._logger.error(f"Failed to show error dialog: {e}")

    def _generate_backup_filename(self, source_path: str) -> str:
        """
        Generate backup filename with format: yy_mm_dd_hh_mm_filename_hash.pzs

        Args:
            source_path: Path to original file

        Returns:
            str: Generated backup filename
        """
        now = datetime.now()
        timestamp = now.strftime("%y_%m_%d_%H_%M")

        hash_input = f"{source_path}_{time.time()}".encode()
        short_hash = hashlib.md5(hash_input).hexdigest()[:4]

        original_name = Path(source_path).stem

        backup_name = f"{timestamp}_{original_name}_{short_hash}.pzs"

        return backup_name

    def create_backup(self, source_path: str) -> str | None:
        """
        Method :
            BackupManager.create_backup(source_path)
        Parameters :
            source_path : str
                Path to the scene file to backup

        BackupManager.create_backup(source_path) --> Optional[str]

        Create a backup of the scene file in its per-scene directory.
        Rotation and expiration cleanup are triggered automatically.

        Args:
            source_path: Path to the scene file to backup

        Returns:
            Optional[str]: Path to created backup file, or None if failed
        """
        if not os.path.exists(source_path):
            self._logger.error(f"Cannot create backup: source file does not exist: {source_path}")
            self._show_error_dialog(f"Cannot create backup: file does not exist: {source_path}")
            return None

        try:
            scene_dir = self._get_scene_dir(source_path)
            scene_dir.mkdir(parents=True, exist_ok=True)

            backup_name = self._generate_backup_filename(source_path)
            backup_path = scene_dir / backup_name

            shutil.copy2(source_path, backup_path)

            self._logger.info(f"Created backup: {backup_path}")

            self._rotate_backups(scene_dir)
            self._cleanup_expired()

            return str(backup_path)

        except PermissionError as e:
            self._logger.error(f"Permission error creating backup: {e}")
            self._show_error_dialog(f"Permission error creating backup: {e}")
            return None
        except Exception as e:
            self._logger.error(f"Failed to create backup: {e}")
            self._show_error_dialog(f"Failed to create backup: {e}")
            return None

    def _rotate_backups(self, scene_dir: Path) -> None:
        """Keep only the last N backups within a scene directory, delete oldest ones.

        Args:
            scene_dir: The per-scene backup directory to rotate
        """
        try:
            backup_files = list(scene_dir.glob("*.pzs"))

            if not backup_files:
                return

            backup_files.sort(key=os.path.getmtime)

            max_backups = self._config.get("max_backups", 20)
            files_to_delete = backup_files[:-max_backups] if len(backup_files) > max_backups else []

            for file_path in files_to_delete:
                try:
                    file_path.unlink()
                    self._logger.debug(f"Rotated out old backup: {file_path.name}")
                except Exception as e:
                    self._logger.error(f"Failed to delete old backup {file_path}: {e}")

            if files_to_delete:
                self._logger.info(
                    f"Rotated backups in {scene_dir.name}: "
                    f"kept {min(max_backups, len(backup_files))}, deleted {len(files_to_delete)}"
                )

        except Exception as e:
            self._logger.error(f"Failed to rotate backups in {scene_dir}: {e}")

    def _cleanup_expired(self) -> int:
        """Delete expired backup scene directories.

        Directories are considered expired if their mtime is older than
        expire_days (default 7). Empty or non-backup directories are
        also cleaned up.

        Returns:
            int: Number of directories deleted
        """
        expire_days = self._config.get("expire_days", 7)
        expire_seconds = expire_days * 86400
        cutoff_time = time.time() - expire_seconds

        deleted = 0

        try:
            for item in sorted(self._backup_dir.iterdir()):
                if not item.is_dir():
                    continue

                has_backups = any(item.glob("*.pzs"))

                if not has_backups:
                    try:
                        item.rmdir()
                        self._logger.debug(f"Cleaned up empty directory: {item.name}")
                        deleted += 1
                    except OSError:
                        pass
                    continue

                dir_mtime = os.path.getmtime(item)
                if dir_mtime < cutoff_time:
                    shutil.rmtree(item)
                    self._logger.info(f"Expired backup directory: {item.name}")
                    deleted += 1
        except Exception as e:
            self._logger.error(f"Failed to cleanup expired backups: {e}")

        if deleted:
            self._logger.info(f"Cleaned up {deleted} expired backup directories")
        return deleted

    def cleanup_expired_dirs(self) -> int:
        """
        Method :
            BackupManager.cleanup_expired_dirs()
        Parameters :
            None

        BackupManager.cleanup_expired_dirs() --> int

        Public method to delete expired backup scene directories.

        Returns:
            int: Number of directories deleted
        """
        return self._cleanup_expired()

    def cleanup_flat_backups(self) -> int:
        r"""
        Method :
            BackupManager.cleanup_flat_backups()
        Parameters :
            None

        BackupManager.cleanup_flat_backups() --> int

        Delete legacy flat backup files from the root backup directory.
        Used for migrating from the old flat structure to the new
        per-scene directory structure. Only deletes \*.pzs files directly
        in the backup root (not in subdirectories).

        Returns:
            int: Number of flat backup files deleted
        """
        try:
            deleted = 0
            for item in self._backup_dir.glob("*.pzs"):
                if item.is_file():
                    try:
                        item.unlink()
                        self._logger.debug(f"Cleaned up legacy flat backup: {item.name}")
                        deleted += 1
                    except Exception as e:
                        self._logger.error(f"Failed to delete legacy backup {item}: {e}")

            if deleted:
                self._logger.info(f"Cleaned up {deleted} legacy flat backup files")
            return deleted

        except Exception as e:
            self._logger.error(f"Failed to cleanup legacy flat backups: {e}")
            return 0

    def get_backup_count(self, source_path: str | None = None) -> int:
        """
        Method :
            BackupManager.get_backup_count(source_path=None)
        Parameters :
            source_path : Optional[str]
                Path to the scene file (counts backups for specific scene),
                or None (counts backups across all scenes)

        BackupManager.get_backup_count(source_path=None) --> int

        Get current number of backup files.

        Args:
            source_path: Optional scene path to count backups for a specific scene.
                         If None, counts all backups across all scenes.

        Returns:
            int: Number of backup files
        """
        try:
            if source_path:
                scene_dir = self._get_scene_dir(source_path)
                if scene_dir.exists():
                    backup_files = list(scene_dir.glob("*.pzs"))
                    return len(backup_files)
                return 0
            else:
                count = 0
                for item in self._backup_dir.iterdir():
                    if item.is_dir():
                        count += len(list(item.glob("*.pzs")))
                return count
        except Exception as e:
            self._logger.error(f"Failed to count backups: {e}")
            return 0

    def list_backups(self, source_path: str | None = None) -> list[str]:
        """
        Method :
            BackupManager.list_backups(source_path=None)
        Parameters :
            source_path : Optional[str]
                Path to the scene file (lists backups for specific scene),
                or None (lists backups across all scenes)

        BackupManager.list_backups(source_path=None) --> List[str]

        List all backup files sorted by modification time (newest first).

        Args:
            source_path: Optional scene path to list backups for a specific scene.
                         If None, lists all backups across all scenes.

        Returns:
            List[str]: List of backup file paths relative to backup root
        """
        try:
            if source_path:
                scene_dir = self._get_scene_dir(source_path)
                if scene_dir.exists():
                    backup_files = list(scene_dir.glob("*.pzs"))
                    backup_files.sort(key=os.path.getmtime, reverse=True)
                    return [str(f.relative_to(self._backup_dir)) for f in backup_files]
                return []
            else:
                all_backups: list[str] = []
                for item in self._backup_dir.iterdir():
                    if item.is_dir():
                        files = list(item.glob("*.pzs"))
                        files.sort(key=os.path.getmtime, reverse=True)
                        all_backups.extend(str(f.relative_to(self._backup_dir)) for f in files)
                all_backups.sort(key=lambda p: os.path.getmtime(self._backup_dir / p), reverse=True)
                return all_backups
        except Exception as e:
            self._logger.error(f"Failed to list backups: {e}")
            return []

    def cleanup_all(self) -> int:
        """
        Method :
            BackupManager.cleanup_all()
        Parameters :
            None

        BackupManager.cleanup_all() --> int

        Delete all backup files and directories.

        Returns:
            int: Number of items (files + directories) deleted
        """
        try:
            deleted_count = 0

            for item in sorted(self._backup_dir.iterdir()):
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                    deleted_count += 1
                except Exception as e:
                    self._logger.error(f"Failed to delete {item}: {e}")

            self._logger.info(f"Cleaned up all backups: deleted {deleted_count} items")
            return deleted_count

        except Exception as e:
            self._logger.error(f"Failed to cleanup backups: {e}")
            return 0
