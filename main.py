#!/usr/bin/env python
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

import sys
import os
import argparse
import json
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from pyzui.objects.scene.qzui import QZUI
import pyzui.tilemanager as TileManager
from pyzui.objects.scene.mainwindow import MainWindow
from pyzui.logger import LoggerConfig, get_logger


def load_config(config_file=None):
    """Load configuration from JSON file.

    Args:
        config_file (str): Path to configuration file

    Returns:
        dict: Configuration dictionary with logging and tilestore sections
    """
    default_config = {
        'logging': {
            'debug': False,
            'verbose': False,
            'log_to_file': True,
            'log_to_console': True,
            'colored_output': True,
            'log_dir': 'logs'
        },
        'tilestore': {
            'auto_cleanup': True,
            'max_age_days': 3,
            'cleanup_on_startup': True
        }
    }

    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                # Merge logging config
                if 'logging' in user_config:
                    default_config['logging'].update(user_config['logging'])
                # Merge tilestore config
                if 'tilestore' in user_config:
                    default_config['tilestore'].update(user_config['tilestore'])
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load config file: {e}")

    return default_config


def parse_arguments():
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='PyZUI - Python Zooming User Interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                      # Run with default settings
  %(prog)s --debug              # Run in debug mode with verbose logging
  %(prog)s --verbose            # Run with verbose logging to console
  %(prog)s --config pyzui.json  # Load settings from config file
  %(prog)s --no-console         # Disable console logging
  %(prog)s --log-dir /tmp/logs  # Use custom log directory
        """
    )

    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Enable debug mode (maximum logging detail)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose mode (detailed info logging)'
    )

    parser.add_argument(
        '--config',
        type=str,
        metavar='FILE',
        help='Path to configuration file (JSON format)'
    )

    parser.add_argument(
        '--log-dir',
        type=str,
        metavar='DIR',
        help='Directory for log files (default: ./logs)'
    )

    parser.add_argument(
        '--no-console',
        action='store_true',
        help='Disable console logging'
    )

    parser.add_argument(
        '--no-file',
        action='store_true',
        help='Disable file logging'
    )

    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored console output'
    )

    parser.add_argument(
        '--no-cleanup',
        action='store_true',
        help='Disable automatic tilestore cleanup on startup'
    )

    parser.add_argument(
        '--cleanup-age',
        type=int,
        metavar='DAYS',
        help='Maximum age in days for tilestore cleanup (default: 3)'
    )

    return parser.parse_args()


def main():
    """Start the PyZUI application."""

    # Parse command-line arguments
    args = parse_arguments()

    # Load configuration from file if specified
    config = load_config(args.config)

    # Command-line arguments override config file
    if args.debug:
        config['logging']['debug'] = True
    if args.verbose:
        config['logging']['verbose'] = True
    if args.log_dir:
        config['logging']['log_dir'] = args.log_dir
    if args.no_console:
        config['logging']['log_to_console'] = False
    if args.no_file:
        config['logging']['log_to_file'] = False
    if args.no_color:
        config['logging']['colored_output'] = False
    if args.no_cleanup:
        config['tilestore']['auto_cleanup'] = False
    if args.cleanup_age:
        config['tilestore']['max_age_days'] = args.cleanup_age

    # Set working directory
    if os.path.dirname(__file__):
        os.chdir(os.path.dirname(__file__))

    # Initialize logging system
    LoggerConfig.initialize(
        debug=config['logging']['debug'],
        log_to_file=config['logging']['log_to_file'],
        log_to_console=config['logging']['log_to_console'],
        log_dir=config['logging'].get('log_dir'),
        colored_output=config['logging']['colored_output'],
        verbose=config['logging']['verbose']
    )

    logger = get_logger('main')
    logger.info('Starting PyZUI application')
    logger.debug(f'Working directory: {os.getcwd()}')
    logger.debug(f'Python version: {sys.version}')

    # Initialize TileManager (includes automatic cleanup if enabled)
    TileManager.init(
        auto_cleanup=config['tilestore']['auto_cleanup'],
        cleanup_max_age_days=config['tilestore']['max_age_days']
    )

    # Create Qt application
    app = QtWidgets.QApplication(sys.argv)
    icon_path = os.path.join("data", "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QtGui.QIcon(icon_path))
        logger.debug(f'Application icon loaded from {icon_path}')
    else:
        logger.warning(f'Application icon not found at {icon_path}')

    # Create and show main window
    window = MainWindow()
    window.show()
    logger.info('Main window displayed')

    # Start event loop
    logger.info('Entering Qt event loop')
    exit_code = app.exec()
    logger.info(f'Application exiting with code {exit_code}')

    sys.exit(exit_code)


if __name__ == '__main__':
    main()



