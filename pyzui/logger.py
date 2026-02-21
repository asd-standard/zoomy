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

"""Centralized logging configuration for PyZUI."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import cast

class LoggerConfig:
    """
    Constructor :
        LoggerConfig()
    Parameters :
        None

    LoggerConfig() --> None

    Centralized logger configuration for PyZUI.

    Provides consistent logging across all modules with support for:
    - Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Console and file output
    - Rotating log files
    - Color-coded console output (optional)
    - Per-module log level control
    """

    _initialized = False
    _log_dir = None
    _log_file = None
    _console_level = logging.INFO
    _file_level = logging.DEBUG
    _loggers = {}

    # ANSI color codes for console output
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    @classmethod
    def initialize(cls, debug: bool = False, log_to_file: bool = True, log_to_console: bool = True,
                   log_dir: str | None = None, colored_output: bool = True, verbose: bool = False) -> None:
        """
        Method :
            LoggerConfig.initialize(debug, log_to_file, log_to_console, log_dir, colored_output, verbose)
        Parameters :
            debug : bool
            log_to_file : bool
            log_to_console : bool
            log_dir : str
            colored_output : bool
            verbose : bool

        LoggerConfig.initialize(debug, log_to_file, log_to_console, log_dir, colored_output, verbose) --> None

        Initialize the logging system.

        Args:
            debug (bool): Enable debug mode (sets console level to DEBUG)
            log_to_file (bool): Enable logging to file
            log_to_console (bool): Enable logging to console
            log_dir (str): Directory for log files (default: ./logs)
            colored_output (bool): Enable colored console output
            verbose (bool): Enable verbose mode (shows more detailed info)
        """
        if cls._initialized:
            return

        # Determine log levels
        if debug:
            cls._console_level = logging.DEBUG
            cls._file_level = logging.DEBUG
        elif verbose:
            cls._console_level = logging.INFO
            cls._file_level = logging.DEBUG
        else:
            cls._console_level = logging.WARNING
            cls._file_level = logging.INFO

        # Setup log directory
        if log_dir:
            cls._log_dir = Path(log_dir)
        else:
            cls._log_dir = Path.cwd() / 'logs'

        if log_to_file:
            cls._log_dir.mkdir(parents=True, exist_ok=True)
            cls._log_file = cls._log_dir / 'pyzui.log'

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)  # Capture everything, handlers will filter

        # Remove existing handlers
        for handler in root_logger.handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)

        # Create formatters
        if colored_output and log_to_console:
            console_formatter = ColoredFormatter(
                '%(color)s[%(levelname)-8s]%(reset)s %(name)-25s | %(message)s'
            )
        else:
            console_formatter = logging.Formatter(
                '[%(levelname)-8s] %(name)-25s | %(message)s'
            )

        file_formatter = logging.Formatter(
            '%(asctime)s | [%(levelname)-8s] | %(name)-25s | %(funcName)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Add console handler
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(cls._console_level)
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)

        # Add file handler with rotation
        if log_to_file:
            # _log_file is guaranteed to be set when log_to_file is True
            file_handler = RotatingFileHandler(
                cast(Path, cls._log_file),
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5
            )
            file_handler.setLevel(cls._file_level)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

        cls._initialized = True

        # Log initialization
        init_logger = cls.get_logger('LoggerConfig')
        init_logger.info('='*60)
        init_logger.info('PyZUI Logging System Initialized')
        init_logger.info(f'Debug Mode: {debug}')
        init_logger.info(f'Console Level: {logging.getLevelName(cls._console_level)}')
        init_logger.info(f'File Level: {logging.getLevelName(cls._file_level)}')
        if log_to_file:
            init_logger.info(f'Log File: {cls._log_file}')
        init_logger.info('='*60)

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Method :
            LoggerConfig.get_logger(name)
        Parameters :
            name : str

        LoggerConfig.get_logger(name) --> logging.Logger

        Get a logger instance for the specified module.

        Args:
            name (str): Name of the module/class requesting the logger

        Returns:
            logging.Logger: Configured logger instance
        """
        if not cls._initialized:
            # Initialize with default settings if not already done
            cls.initialize()

        if name not in cls._loggers:
            logger = logging.getLogger(f'pyzui.{name}')
            cls._loggers[name] = logger

        return cls._loggers[name]

    @classmethod
    def set_level(cls, level: int, module: str | None = None) -> None:
        """
        Method :
            LoggerConfig.set_level(level, module)
        Parameters :
            level : int
            module : str

        LoggerConfig.set_level(level, module) --> None

        Change the logging level at runtime.

        Args:
            level (int): Logging level (e.g., logging.DEBUG, logging.INFO)
            module (str): Specific module name, or None for all modules
        """
        if module:
            logger = cls.get_logger(module)
            logger.setLevel(level)
        else:
            # Update all loggers
            cls._console_level = level
            root_logger = logging.getLogger()
            for handler in root_logger.handlers:
                # Update both console and file handlers
                handler.setLevel(level)

    @classmethod
    def enable_debug(cls) -> None:
        """
        Method :
            LoggerConfig.enable_debug()
        Parameters :
            None

        LoggerConfig.enable_debug() --> None

        Enable debug mode at runtime.
        """
        cls.set_level(logging.DEBUG)
        logger = cls.get_logger('LoggerConfig')
        logger.info('Debug mode enabled')

    @classmethod
    def disable_debug(cls) -> None:
        """
        Method :
            LoggerConfig.disable_debug()
        Parameters :
            None

        LoggerConfig.disable_debug() --> None

        Disable debug mode at runtime.
        """
        cls.set_level(logging.INFO)
        logger = cls.get_logger('LoggerConfig')
        logger.info('Debug mode disabled')

    @classmethod
    def get_log_file_path(cls) -> Path | None:
        """
        Method :
            LoggerConfig.get_log_file_path()
        Parameters :
            None

        LoggerConfig.get_log_file_path() --> Path

        Get the path to the current log file.

        Returns:
            Path: Path to log file, or None if file logging is disabled
        """
        return cls._log_file

class ColoredFormatter(logging.Formatter):
    """
    Constructor :
        ColoredFormatter()
    Parameters :
        None

    ColoredFormatter() --> None

    Custom formatter that adds color to console output.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Method :
            ColoredFormatter.format(record)
        Parameters :
            record : logging.LogRecord

        ColoredFormatter.format(record) --> str

        Format the log record with color codes.

        Add color codes to the record based on log level.
        """
        # Add color codes to the record
        levelname = record.levelname
        if levelname in LoggerConfig.COLORS:
            record.color = LoggerConfig.COLORS[levelname]
            record.reset = LoggerConfig.COLORS['RESET']
        else:
            record.color = ''
            record.reset = ''

        return super().format(record)

def get_logger(name: str) -> logging.Logger:
    """
    Function :
        get_logger(name)
    Parameters :
        name : str

    get_logger(name) --> logging.Logger

    Convenience function to get a logger.

    Args:
        name (str): Name of the module/class requesting the logger

    Returns:
        logging.Logger: Configured logger instance
    """
    return LoggerConfig.get_logger(name)
