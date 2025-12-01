#!/usr/bin/env python
"""Manual tilestore cleanup utility for PyZUI.

This script allows you to manually clean up old tiles from the tilestore directory.
It can be run standalone without starting the full PyZUI application.
"""

import sys
import os
import argparse
from typing import Optional, Tuple, List, Any

# Add pyzui to path (go up two directories to get to project root)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pyzui import tilestore as TileStore
from pyzui.logger import LoggerConfig, get_logger


def main() -> int:
    """Run manual tilestore cleanup.

    Method :
        main()
    Parameters :
        None

    Returns
    -------
    int
        Exit code (0 for success)
    """

    parser = argparse.ArgumentParser(
        description='PyZUI Tilestore Cleanup Utility',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --dry-run              # Show what would be deleted
  %(prog)s --age 7                # Delete files older than 7 days
  %(prog)s --stats                # Show tilestore statistics
  %(prog)s                        # Clean files older than 3 days
        """
    )

    parser.add_argument(
        '--age',
        type=int,
        default=3,
        metavar='DAYS',
        help='Maximum age in days before deletion (default: 3)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )

    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show tilestore statistics only (no cleanup)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )

    args = parser.parse_args()

    # Initialize logging
    LoggerConfig.initialize(
        debug=args.debug,
        verbose=args.verbose,
        log_to_file=False,  # Don't create log files for cleanup utility
        log_to_console=True,
        colored_output=True
    )

    logger = get_logger('cleanup')

    # Show statistics
    if args.stats:
        logger.info('Gathering tilestore statistics...')
        stats = TileStore.get_tilestore_stats()

        print('\n' + '='*60)
        print('TILESTORE STATISTICS')
        print('='*60)
        print(f'Location: {TileStore.tile_dir}')
        print(f'Media directories: {stats["media_count"]}')
        print(f'Total files: {stats["file_count"]}')
        print(f'Total size: {stats["total_size_mb"]:.2f} MB')
        print('='*60 + '\n')

        if not args.dry_run:
            return 0

    # Run cleanup
    logger.info(f'Starting tilestore cleanup (max_age: {args.age} days)')

    if args.dry_run:
        logger.info('[DRY RUN MODE] No files will be deleted')

    cleanup_stats = TileStore.cleanup_old_tiles(
        max_age_days=args.age,
        dry_run=args.dry_run
    )

    # Print summary
    print('\n' + '='*60)
    print('CLEANUP SUMMARY')
    print('='*60)

    if args.dry_run:
        print('[DRY RUN] No files were actually deleted')
        print(f'Would delete: {cleanup_stats["deleted_media_count"]} media directories')
        print(f'Would free: {cleanup_stats["deleted_size_mb"]:.2f} MB')
    else:
        print(f'Deleted: {cleanup_stats["deleted_media_count"]} media directories')
        print(f'Freed: {cleanup_stats["deleted_size_mb"]:.2f} MB')

    print(f'Kept: {cleanup_stats["kept_media_count"]} media directories')

    if cleanup_stats['errors']:
        print(f'Errors: {len(cleanup_stats["errors"])}')
        for error in cleanup_stats['errors']:
            print(f'  - {error}')

    print('='*60 + '\n')

    # Show statistics after cleanup
    if not args.dry_run:
        stats = TileStore.get_tilestore_stats()
        print('TILESTORE AFTER CLEANUP')
        print('='*60)
        print(f'Media directories: {stats["media_count"]}')
        print(f'Total files: {stats["file_count"]}')
        print(f'Total size: {stats["total_size_mb"]:.2f} MB')
        print('='*60 + '\n')

    return 0


if __name__ == '__main__':
    sys.exit(main())
