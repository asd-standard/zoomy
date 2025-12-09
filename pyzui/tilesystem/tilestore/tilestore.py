## PyZUI 0.1 - Python Zooming User Interface
## Copyright (C) 2009  David Roberts <d@vidr.cc>
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
## 02110-1301, USA.

"""Module for managing the disk-based tile storage facility."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import hashlib
import time
import shutil
from threading import RLock
from typing import Optional, Tuple, Any, Dict
from logger import get_logger

## set the default tilestore directory, this can be overridden if required
if 'APPDATA' in os.environ:
    ## Windows
    tile_dir = os.path.join(os.environ['APPDATA'], "pyzui", "tilestore")
else:
    ## Unix
    tile_dir = os.path.join(os.path.expanduser('~'), ".pyzui", "tilestore")

## threads which intend performing disk-access-intensive activities should
## acquire this lock first to reduce stress on the disk
disk_lock = RLock()

__metadata = {}
__logger = None

def _get_logger() -> Any:
    """
    Function :
        _get_logger()
    Parameters :
        None

    _get_logger() --> logging.Logger

    Check if there's a __logger instance for the TileStore module
    if not creates a logger instance for the TileStore module.

    """
    global __logger
    if __logger is None:
        __logger = get_logger('TileStore')

    return __logger

def get_media_path(media_id: str) -> str:
    """
    Function :
        get_media_path(media_id)
    Parameters :
        media_id : str

    get_media_path(media_id) --> str

    Return the path to the directory containing the tiles for the media
    identified by `media_id`.
    """
    #media_hash = hashlib.sha1(media_id).hexdigest() #REPLACED BY:
    media_hash = hashlib.sha1(media_id.encode('utf-8')).hexdigest()
    media_dir = os.path.join(tile_dir, media_hash)
    return media_dir


def get_tile_path(tile_id: Tuple[str, int, int, int], mkdirp: bool = False, prefix: Optional[str] = None, filext: Optional[str] = None) -> str:
    """
    Function :
        get_tile_path(tile_id, mkdirp, prefix, filext)
    Parameters :
        tile_id : Tuple[str, int, int, int]
        mkdirp : bool
        prefix : Optional[str]
        filext : Optional[str]

    get_tile_path(tile_id, mkdirp, prefix, filext) --> str

    Return the path to the tile identified by `tile_id`.

    If `mkdirp` is True, then any non-existent parent directories of the tile
    will be created.

    If `prefix` is omitted, it will be set to the value returned by
    :meth:`get_media_path`.

    If `filext` is omitted, it will be set to the value returned by
    :meth:`get_metadata`.

    Note: Precondition - if `filext` is None, then the metadata file for the media
    that this tile belongs to exists and contains an entry for filext.

    """
    
    media_id, tilelevel, row, col = tile_id
    
    if not prefix:
        prefix = get_media_path(media_id)

    if filext is None:
        filext = get_metadata(media_id, 'filext')

    filename = os.path.join(prefix, "%02d" % tilelevel, "%06d" % row)

    if mkdirp and not os.path.exists(filename):
        ## create parent directories
        os.makedirs(filename)

    filename = os.path.join(
        filename, "%02d_%06d_%06d.%s" % (tilelevel, row, col, filext))
    
    return filename


def load_metadata(media_id: str) -> bool:
    """
    Function :
        load_metadata(media_id)
    Parameters :
        media_id : str

    load_metadata(media_id) --> bool

    Load metadata from disk for the given `media_id`, and return a bool
    indicating whether the load was successful.
    """
    path = get_media_path(media_id)

    try:
        f = open(os.path.join(path, "metadata"))
    except IOError:
        return False

    __metadata[media_id] = {}

    for line in f:
        key, val, val_type = line.split()

        try:
            if   val_type == 'int':   val = int(val)
            elif val_type == 'bool':  val = bool(val)
            elif val_type == 'float': val = float(val)
            elif val_type == 'long':  val = int(val)
        except Exception:
            pass
        else:
            __metadata[media_id][key] = val
            
    f.close()

    return True


def get_metadata(media_id: str, key: str) -> Optional[Any]:
    """
    Function :
        get_metadata(media_id, key)
    Parameters :
        media_id : str
        key : str

    get_metadata(media_id, key) --> Optional[Any]

    Return the value associated with the given metadata key, None if there
    is no such value.
    """
    if media_id not in __metadata and not load_metadata(media_id):
        return None
    return __metadata[media_id].get(key)


def write_metadata(media_id: str, **kwargs: Any) -> None:
    """
    Function :
        write_metadata(media_id, \\*\\*kwargs)
    Parameters :
        media_id : str
        \\*\\*kwargs : Any

    write_metadata(media_id, \\*\\*kwargs) --> None

    Write the metadata given in `kwargs` for the given `media_id`.
    """
    path = get_media_path(media_id)
    f = open(os.path.join(path, "metadata"), 'w')
    for key,val in list(kwargs.items()):
        f.write("%s\t%s\t%s\n"
            % (key, str(val), type(val).__name__))
    f.close()


def tiled(media_id: str) -> bool:
    """
    Function :
        tiled(media_id)
    Parameters :
        media_id : str

    tiled(media_id) --> bool

    Return True iff the media identified by `media_id` has been tiled
    i.e. iff both a metadata file and the (0,0,0) tile exist.
    """
    #print('pyzui.tilestore-154',media_id)
    path = get_media_path(media_id)

    ##We have to understand what this return function does
    #print(os.path.join(path, "metadata"))
    return os.path.exists(os.path.join(path, "metadata")) and \
           os.path.exists(get_tile_path((media_id, 0, 0, 0)))


def get_directory_size(path: str) -> int:
    """
    Function :
        get_directory_size(path)
    Parameters :
        path : str

    get_directory_size(path) --> int

    Calculate total size of a directory in bytes.
    """
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
    except Exception as e:
        _get_logger().warning(f'Error calculating directory size for {path}: {e}')
    return total_size


def get_tilestore_stats() -> Dict[str, Any]:
    """
    Function :
        get_tilestore_stats()
    Parameters :
        None

    get_tilestore_stats() --> Dict[str, Any]

    Get statistics about the tilestore directory.

    Returns dictionary containing stats (total_size, file_count, media_count, total_size_mb).
    """
    logger = _get_logger()
    stats = {
        'total_size': 0,
        'file_count': 0,
        'media_count': 0,
        'total_size_mb': 0.0
    }

    if not os.path.exists(tile_dir):
        return stats

    try:
        # Count media directories
        media_dirs = [d for d in os.listdir(tile_dir)
                     if os.path.isdir(os.path.join(tile_dir, d))]
        stats['media_count'] = len(media_dirs)

        # Calculate total size and file count
        for dirpath, dirnames, filenames in os.walk(tile_dir):
            stats['file_count'] += len(filenames)
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    stats['total_size'] += os.path.getsize(filepath)

        stats['total_size_mb'] = stats['total_size'] / (1024 * 1024)

    except Exception as e:
        logger.error(f'Error getting tilestore stats: {e}')

    return stats


def cleanup_old_tiles(max_age_days: int = 3, dry_run: bool = False) -> Dict[str, Any]:
    """
    Function :
        cleanup_old_tiles(max_age_days, dry_run)
    Parameters :
        max_age_days : int
        dry_run : bool

    cleanup_old_tiles(max_age_days, dry_run) --> Dict[str, Any]

    Clean up tile files that haven't been accessed in more than max_age_days.

    This function removes media directories whose files haven't been accessed
    (read or written) in more than the specified number of days.

    Returns dictionary with cleanup statistics:
        - deleted_media_count: Number of media directories deleted
        - deleted_size_mb: Total size freed in MB
        - kept_media_count: Number of media directories kept
        - errors: List of error messages
    """
    logger = _get_logger()

    if not os.path.exists(tile_dir):
        logger.info('Tilestore directory does not exist, nothing to clean')
        return {
            'deleted_media_count': 0,
            'deleted_size_mb': 0.0,
            'kept_media_count': 0,
            'errors': []
        }

    logger.info(f'Starting tilestore cleanup (max_age: {max_age_days} days, dry_run: {dry_run})')

    # Calculate cutoff time
    current_time = time.time()
    max_age_seconds = max_age_days * 24 * 60 * 60
    cutoff_time = current_time - max_age_seconds

    stats = {
        'deleted_media_count': 0,
        'deleted_size_mb': 0.0,
        'kept_media_count': 0,
        'errors': []
    }

    with disk_lock:
        try:
            # Get all media directories
            if not os.path.isdir(tile_dir):
                return stats

            media_dirs = [d for d in os.listdir(tile_dir)
                         if os.path.isdir(os.path.join(tile_dir, d))]

            logger.info(f'Found {len(media_dirs)} media directories to check')

            for media_hash in media_dirs:
                media_path = os.path.join(tile_dir, media_hash)

                try:
                    # Find the most recent access time of any file in the directory
                    most_recent_access = 0

                    for dirpath, dirnames, filenames in os.walk(media_path):
                        for filename in filenames:
                            filepath = os.path.join(dirpath, filename)
                            try:
                                # Use atime (access time) to determine last access
                                # Falls back to mtime if atime is not reliable
                                file_stat = os.stat(filepath)
                                access_time = max(file_stat.st_atime, file_stat.st_mtime)
                                most_recent_access = max(most_recent_access, access_time)
                            except OSError:
                                continue

                    # Check if directory should be deleted
                    if most_recent_access > 0 and most_recent_access < cutoff_time:
                        age_days = (current_time - most_recent_access) / (24 * 60 * 60)
                        dir_size = get_directory_size(media_path)
                        dir_size_mb = dir_size / (1024 * 1024)

                        if dry_run:
                            logger.info(
                                f'[DRY RUN] Would delete: {media_hash} '
                                f'(age: {age_days:.1f} days, size: {dir_size_mb:.2f} MB)'
                            )
                        else:
                            logger.info(
                                f'Deleting old media: {media_hash} '
                                f'(age: {age_days:.1f} days, size: {dir_size_mb:.2f} MB)'
                            )
                            shutil.rmtree(media_path)

                            # Remove from metadata cache if present
                            for media_id in list(__metadata.keys()):
                                if get_media_path(media_id) == media_path:
                                    del __metadata[media_id]

                        stats['deleted_media_count'] += 1
                        stats['deleted_size_mb'] += dir_size_mb
                    else:
                        stats['kept_media_count'] += 1
                        if most_recent_access > 0:
                            age_days = (current_time - most_recent_access) / (24 * 60 * 60)
                            logger.debug(f'Keeping: {media_hash} (age: {age_days:.1f} days)')

                except Exception as e:
                    error_msg = f'Error processing {media_hash}: {e}'
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)

        except Exception as e:
            error_msg = f'Error during cleanup: {e}'
            logger.error(error_msg)
            stats['errors'].append(error_msg)

    # Log summary
    if dry_run:
        logger.info(
            f'[DRY RUN] Cleanup would delete {stats["deleted_media_count"]} media directories, '
            f'freeing {stats["deleted_size_mb"]:.2f} MB. '
            f'{stats["kept_media_count"]} directories would be kept.'
        )
    else:
        logger.info(
            f'Cleanup complete: Deleted {stats["deleted_media_count"]} media directories, '
            f'freed {stats["deleted_size_mb"]:.2f} MB. '
            f'{stats["kept_media_count"]} directories kept.'
        )

    if stats['errors']:
        logger.warning(f'Cleanup completed with {len(stats["errors"])} errors')

    return stats


def auto_cleanup(max_age_days: int = 3, enable: bool = True) -> Optional[Dict[str, Any]]:
    """
    Function :
        auto_cleanup(max_age_days, enable)
    Parameters :
        max_age_days : int
        enable : bool

    auto_cleanup(max_age_days, enable) --> Optional[Dict[str, Any]]

    Automatically clean up old tiles if enabled.

    This function is designed to be called on startup or periodically.
    Returns cleanup statistics or None if disabled.
    """
    logger = _get_logger()

    if not enable:
        logger.debug('Auto cleanup disabled')
        return None

    logger.info('Running automatic tilestore cleanup')

    # Get stats before cleanup
    before_stats = get_tilestore_stats()
    logger.info(
        f'Tilestore before cleanup: {before_stats["media_count"]} media directories, '
        f'{before_stats["file_count"]} files, '
        f'{before_stats["total_size_mb"]:.2f} MB'
    )

    # Run cleanup
    cleanup_stats = cleanup_old_tiles(max_age_days=max_age_days, dry_run=False)

    # Get stats after cleanup
    after_stats = get_tilestore_stats()
    logger.info(
        f'Tilestore after cleanup: {after_stats["media_count"]} media directories, '
        f'{after_stats["file_count"]} files, '
        f'{after_stats["total_size_mb"]:.2f} MB'
    )

    return cleanup_stats


















