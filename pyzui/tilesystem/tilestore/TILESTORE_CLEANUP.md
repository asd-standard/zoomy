# PyZUI Tilestore Cleanup System

This document describes the automatic tilestore cleanup system that prevents the tile cache from growing indefinitely.

## Overview

The tilestore cleanup system automatically removes tile files that haven't been accessed in a configurable number of days (default: 3 days). This prevents the tilestore directory from accumulating old, unused tiles over time.

## Features

- **Automatic cleanup on startup** - Runs automatically when PyZUI starts (configurable)
- **Manual cleanup utility** - Standalone script for manual cleanup
- **Dry-run mode** - Preview what would be deleted without actually deleting
- **Configurable age threshold** - Set custom maximum age for tiles
- **Statistics reporting** - View tilestore size and file counts
- **Safe deletion** - Uses file access times to determine unused files
- **Comprehensive logging** - All cleanup operations are logged

## Automatic Cleanup

### Default Behavior

By default, PyZUI will automatically clean up tiles older than 3 days on startup.

### Configuration

#### Via Configuration File

Edit `pyzui_config.json`:

```json
{
  "tilestore": {
    "auto_cleanup": true,
    "max_age_days": 3,
    "cleanup_on_startup": true
  }
}
```

- `auto_cleanup`: Enable/disable automatic cleanup (default: true)
- `max_age_days`: Maximum age in days before deletion (default: 3)
- `cleanup_on_startup`: Run cleanup when PyZUI starts (default: true)

#### Via Command-Line

```bash
# Disable automatic cleanup
python main.py --no-cleanup

# Change age threshold to 7 days
python main.py --cleanup-age 7

# Combine options
python main.py --cleanup-age 5 --verbose
```

### Command-Line Options

```
--no-cleanup          Disable automatic tilestore cleanup on startup
--cleanup-age DAYS    Maximum age in days for tilestore cleanup (default: 3)
```

## Manual Cleanup

### Using the Cleanup Utility

A standalone cleanup utility is provided: `cleanuptilestore.py`

#### Basic Usage

```bash
# Clean files older than 3 days (default)
python cleanuptilestore.py

# Preview what would be deleted (dry-run)
python cleanuptilestore.py --dry-run

# Clean files older than 7 days
python cleanuptilestore.py --age 7

# Show tilestore statistics only
python cleanuptilestore.py --stats

# Verbose output
python cleanuptilestore.py --verbose

# Debug output
python cleanuptilestore.py --debug
```

#### Examples

**Dry run to see what would be deleted:**
```bash
$ python cleanuptilestore.py --dry-run

[INFO    ] cleanup                  | Starting tilestore cleanup (max_age: 3 days)
[INFO    ] cleanup                  | [DRY RUN MODE] No files will be deleted
[INFO    ] TileStore                | Starting tilestore cleanup (max_age: 3 days, dry_run: True)
[INFO    ] TileStore                | Found 15 media directories to check
[INFO    ] TileStore                | [DRY RUN] Would delete: abc123... (age: 5.2 days, size: 12.5 MB)
[INFO    ] TileStore                | [DRY RUN] Would delete: def456... (age: 4.1 days, size: 8.3 MB)

============================================================
CLEANUP SUMMARY
============================================================
[DRY RUN] No files were actually deleted
Would delete: 2 media directories
Would free: 20.8 MB
Kept: 13 media directories
============================================================
```

**Clean old files:**
```bash
$ python cleanuptilestore.py --age 7

[INFO    ] cleanup                  | Starting tilestore cleanup (max_age: 7 days)
[INFO    ] TileStore                | Starting tilestore cleanup (max_age: 7 days, dry_run: False)
[INFO    ] TileStore                | Found 15 media directories to check
[INFO    ] TileStore                | Deleting old media: abc123... (age: 9.3 days, size: 15.2 MB)
[INFO    ] TileStore                | Cleanup complete: Deleted 1 media directories, freed 15.2 MB. 14 directories kept.

============================================================
CLEANUP SUMMARY
============================================================
Deleted: 1 media directories
Freed: 15.2 MB
Kept: 14 media directories
============================================================
```

**View statistics:**
```bash
$ python cleanuptilestore.py --stats

============================================================
TILESTORE STATISTICS
============================================================
Location: /home/user/.pyzui/tilestore
Media directories: 15
Total files: 2,345
Total size: 456.78 MB
============================================================
```

## How It Works

### File Age Detection

The cleanup system uses file access times to determine which tiles are old:

1. For each media directory in the tilestore, it finds the **most recent access time** among all files
2. If the most recent access is older than the threshold (e.g., 3 days), the entire media directory is marked for deletion
3. Both `atime` (access time) and `mtime` (modification time) are checked, using whichever is more recent

### What Gets Deleted

- **Entire media directories** - If all tiles for a media item are old, the entire directory is removed
- **Metadata files** - Metadata is also removed for deleted media
- **Empty directories** - Parent directories are cleaned up if they become empty

### What's Preserved

- Media accessed or modified within the age threshold
- Currently open files (even if old)
- Files being actively used by PyZUI

## Tilestore Location

The tilestore directory location depends on your operating system:

- **Linux/Unix**: `~/.pyzui/tilestore`
- **Windows**: `%APPDATA%\pyzui\tilestore`

## Logging

All cleanup operations are logged:

```
2025-11-30 14:23:45 | [INFO    ] | TileStore | auto_cleanup | Running automatic tilestore cleanup
2025-11-30 14:23:45 | [INFO    ] | TileStore | auto_cleanup | Tilestore before cleanup: 15 media directories, 2345 files, 456.78 MB
2025-11-30 14:23:46 | [INFO    ] | TileStore | cleanup_old_tiles | Starting tilestore cleanup (max_age: 3 days, dry_run: False)
2025-11-30 14:23:46 | [INFO    ] | TileStore | cleanup_old_tiles | Found 15 media directories to check
2025-11-30 14:23:46 | [INFO    ] | TileStore | cleanup_old_tiles | Deleting old media: abc123... (age: 5.2 days, size: 12.5 MB)
2025-11-30 14:23:46 | [INFO    ] | TileStore | cleanup_old_tiles | Cleanup complete: Deleted 2 media directories, freed 20.8 MB. 13 directories kept.
```

View logs:
```bash
# Real-time log viewing
tail -f logs/pyzui.log

# Search cleanup logs
grep "cleanup" logs/pyzui.log
grep "TileStore" logs/pyzui.log
```

## Programmatic Usage

You can also use the cleanup functions programmatically:

```python
from pyzui import tilestore as TileStore

# Get statistics
stats = TileStore.get_tilestore_stats()
print(f"Total size: {stats['total_size_mb']:.2f} MB")

# Run cleanup (dry run)
results = TileStore.cleanup_old_tiles(max_age_days=3, dry_run=True)
print(f"Would delete {results['deleted_media_count']} directories")

# Run actual cleanup
results = TileStore.cleanup_old_tiles(max_age_days=3, dry_run=False)
print(f"Freed {results['deleted_size_mb']:.2f} MB")

# Auto cleanup (with logging)
TileStore.auto_cleanup(max_age_days=3, enable=True)
```

## Best Practices

1. **Start with dry-run** - Always test with `--dry-run` first to see what would be deleted

2. **Adjust age threshold** - If you work with the same media frequently, increase the age threshold:
   ```bash
   python main.py --cleanup-age 7
   ```

3. **Monitor tilestore size** - Periodically check tilestore statistics:
   ```bash
   python cleanuptilestore.py --stats
   ```

4. **Manual cleanup for large cleanups** - For major cleanups, use the standalone utility:
   ```bash
   python cleanuptilestore.py --age 30 --verbose
   ```

5. **Disable if needed** - If you want to keep all tiles, disable auto-cleanup:
   ```bash
   python main.py --no-cleanup
   ```

## Troubleshooting

### Problem: Cleanup deletes files too aggressively

**Solution**: Increase the age threshold in the config file or via command line:
```json
{
  "tilestore": {
    "max_age_days": 7
  }
}
```
or
```bash
python main.py --cleanup-age 7
```

### Problem: Tilestore growing too large

**Solution**: Decrease the age threshold or run manual cleanup more frequently:
```bash
python cleanuptilestore.py --age 1
```

### Problem: Want to see what would be deleted first

**Solution**: Use dry-run mode:
```bash
python cleanuptilestore.py --dry-run
```

### Problem: Cleanup not running on startup

**Solution**: Check that auto_cleanup is enabled in config:
```json
{
  "tilestore": {
    "auto_cleanup": true
  }
}
```

And ensure you're not using `--no-cleanup` flag.

### Problem: Can't find tilestore directory

**Solution**: Check the logs or use the stats command:
```bash
python cleanuptilestore.py --stats
```

The location will be shown in the output.

## Technical Details

### File Access Time Notes

- **Linux**: By default, access times are updated on file read
- **Some filesystems**: May have `noatime` or `relatime` options that affect access time tracking
- **Fallback**: If `atime` is not reliable, the system uses `mtime` (modification time)

### Thread Safety

- The cleanup system uses the same `disk_lock` as the rest of PyZUI
- This prevents conflicts with tiling operations
- Safe to run cleanup while PyZUI is running (though not recommended)

### Performance

- Cleanup is fast, typically completing in < 1 second for most tilestores
- Large tilestores (thousands of media items) may take several seconds
- Disk I/O is the primary bottleneck

## Summary

The tilestore cleanup system provides:

✅ **Automatic cleanup** on startup (configurable)
✅ **Manual cleanup utility** for on-demand cleaning
✅ **Dry-run mode** to preview deletions
✅ **Configurable age thresholds** (default 3 days)
✅ **Statistics reporting** for monitoring
✅ **Comprehensive logging** of all operations
✅ **Safe deletion** based on file access times

For most users, the default settings (automatic cleanup, 3-day threshold) work well. Adjust as needed based on your usage patterns.
