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

import pytest
import logging
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from pyzui.logger import LoggerConfig, get_logger, ColoredFormatter

class TestLoggerConfig:
    """
    Feature: Logger Configuration
    
    This test suite validates the LoggerConfig class which provides centralized
    logging configuration for PyZUI with support for multiple log levels,
    console and file output, rotating log files, and runtime control.
    """

    def setup_method(self):
        """Reset LoggerConfig state before each test."""
        LoggerConfig._initialized = False
        LoggerConfig._log_dir = None
        LoggerConfig._log_file = None
        LoggerConfig._console_level = logging.INFO
        LoggerConfig._file_level = logging.DEBUG
        LoggerConfig._loggers = {}

    def test_initialize_normal_mode(self):
        """
        Scenario: Initialize logging in normal mode
        
        Given no special mode flags
        When LoggerConfig.initialize() is called
        Then console level should be WARNING
        And file level should be INFO
        And logging should be marked as initialized
        """
        LoggerConfig.initialize(
            debug=False,
            log_to_file=False,
            log_to_console=False,
            colored_output=False,
            verbose=False
        )
        
        assert LoggerConfig._initialized is True
        assert LoggerConfig._console_level == logging.WARNING
        assert LoggerConfig._file_level == logging.INFO

    def test_initialize_verbose_mode(self):
        """
        Scenario: Initialize logging in verbose mode
        
        Given verbose mode is enabled
        When LoggerConfig.initialize() is called with verbose=True
        Then console level should be INFO
        And file level should be DEBUG
        """
        LoggerConfig.initialize(
            debug=False,
            log_to_file=False,
            log_to_console=False,
            colored_output=False,
            verbose=True
        )
        
        assert LoggerConfig._console_level == logging.INFO
        assert LoggerConfig._file_level == logging.DEBUG

    def test_initialize_debug_mode(self):
        """
        Scenario: Initialize logging in debug mode
        
        Given debug mode is enabled
        When LoggerConfig.initialize() is called with debug=True
        Then console level should be DEBUG
        And file level should be DEBUG
        """
        LoggerConfig.initialize(
            debug=True,
            log_to_file=False,
            log_to_console=False,
            colored_output=False,
            verbose=False
        )
        
        assert LoggerConfig._console_level == logging.DEBUG
        assert LoggerConfig._file_level == logging.DEBUG

    def test_initialize_with_file_logging(self):
        """
        Scenario: Initialize logging with file output
        
        Given file logging is enabled
        When LoggerConfig.initialize() is called with log_to_file=True
        Then log directory should be created
        And log file path should be set
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            LoggerConfig.initialize(
                debug=False,
                log_to_file=True,
                log_to_console=False,
                log_dir=temp_dir,
                colored_output=False,
                verbose=False
            )
            
            assert LoggerConfig._log_dir == Path(temp_dir)
            assert LoggerConfig._log_file == Path(temp_dir) / 'pyzui.log'
            assert LoggerConfig._log_file.parent.exists()

    def test_get_logger_auto_initializes(self):
        """
        Scenario: Get logger without explicit initialization
        
        Given LoggerConfig is not initialized
        When get_logger() is called
        Then LoggerConfig should be auto-initialized
        And a logger instance should be returned
        """
        logger = LoggerConfig.get_logger('TestModule')
        
        assert LoggerConfig._initialized is True
        assert logger.name == 'pyzui.TestModule'
        assert isinstance(logger, logging.Logger)

    def test_get_logger_caches_loggers(self):
        """
        Scenario: Get logger returns cached instance
        
        Given a logger has been requested before
        When get_logger() is called with the same name
        Then the cached logger instance should be returned
        """
        logger1 = LoggerConfig.get_logger('TestModule')
        logger2 = LoggerConfig.get_logger('TestModule')
        
        assert logger1 is logger2
        assert 'TestModule' in LoggerConfig._loggers

    def test_set_level_specific_module(self):
        """
        Scenario: Set log level for specific module
        
        Given a logger for a specific module
        When set_level() is called with module name
        Then only that module's logger level should change
        """
        LoggerConfig.initialize(
            debug=False,
            log_to_file=False,
            log_to_console=False,
            colored_output=False,
            verbose=False
        )
        
        test_logger = LoggerConfig.get_logger('TestModule')
        other_logger = LoggerConfig.get_logger('OtherModule')
        
        # Initially both should have default level
        assert test_logger.level == 0  # NOTSET
        assert other_logger.level == 0  # NOTSET
        
        # Set level for TestModule only
        LoggerConfig.set_level(logging.DEBUG, module='TestModule')
        
        # TestModule logger should have new level
        assert test_logger.level == logging.DEBUG
        # OtherModule logger should still have default level
        assert other_logger.level == 0  # NOTSET

    def test_set_level_all_modules(self):
        """
        Scenario: Set log level for all modules
        
        Given multiple loggers exist
        When set_level() is called without module parameter
        Then all handlers should have their level updated
        """
        LoggerConfig.initialize(
            debug=False,
            log_to_file=True,
            log_to_console=True,
            colored_output=False,
            verbose=False
        )
        
        # Get root logger to check handlers
        root_logger = logging.getLogger()
        
        # Store initial levels
        initial_levels = [handler.level for handler in root_logger.handlers]
        
        # Change level globally
        LoggerConfig.set_level(logging.DEBUG)
        
        # All handlers should now have DEBUG level
        for handler in root_logger.handlers:
            assert handler.level == logging.DEBUG
        
        # Console level should be updated
        assert LoggerConfig._console_level == logging.DEBUG

    def test_enable_disable_debug(self):
        """
        Scenario: Enable and disable debug mode at runtime
        
        Given logging is initialized in normal mode
        When enable_debug() is called
        Then log level should be set to DEBUG
        When disable_debug() is called
        Then log level should be set to INFO
        """
        LoggerConfig.initialize(
            debug=False,
            log_to_file=False,
            log_to_console=True,
            colored_output=False,
            verbose=False
        )
        
        # Initially should be WARNING (normal mode)
        assert LoggerConfig._console_level == logging.WARNING
        
        # Enable debug
        LoggerConfig.enable_debug()
        assert LoggerConfig._console_level == logging.DEBUG
        
        # Disable debug
        LoggerConfig.disable_debug()
        assert LoggerConfig._console_level == logging.INFO

    def test_get_log_file_path(self):
        """
        Scenario: Get log file path
        
        Given file logging is enabled
        When get_log_file_path() is called
        Then it should return the log file path
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            LoggerConfig.initialize(
                debug=False,
                log_to_file=True,
                log_to_console=False,
                log_dir=temp_dir,
                colored_output=False,
                verbose=False
            )
            
            log_path = LoggerConfig.get_log_file_path()
            assert log_path == Path(temp_dir) / 'pyzui.log'

    def test_get_log_file_path_no_file_logging(self):
        """
        Scenario: Get log file path when file logging is disabled
        
        Given file logging is disabled
        When get_log_file_path() is called
        Then it should return None
        """
        LoggerConfig.initialize(
            debug=False,
            log_to_file=False,
            log_to_console=False,
            colored_output=False,
            verbose=False
        )
        
        log_path = LoggerConfig.get_log_file_path()
        assert log_path is None

    def test_initialization_idempotent(self):
        """
        Scenario: Initialize multiple times
        
        Given LoggerConfig is already initialized
        When initialize() is called again
        Then it should not reinitialize
        """
        # First initialization
        LoggerConfig.initialize(
            debug=False,
            log_to_file=False,
            log_to_console=False,
            colored_output=False,
            verbose=False
        )
        
        # Store initial state
        initial_console_level = LoggerConfig._console_level
        
        # Try to initialize again with different settings
        LoggerConfig.initialize(
            debug=True,  # Different setting
            log_to_file=False,
            log_to_console=False,
            colored_output=False,
            verbose=False
        )
        
        # Should still have original settings
        assert LoggerConfig._console_level == initial_console_level

class TestColoredFormatter:
    """
    Feature: Colored Formatter
    
    This test suite validates the ColoredFormatter class which adds
    ANSI color codes to console log output based on log level.
    """

    def test_format_with_color(self):
        """
        Scenario: Format log record with color codes
        
        Given a log record with WARNING level
        When ColoredFormatter.format() is called
        Then it should add color codes to the record
        """
        formatter = ColoredFormatter('%(color)s[%(levelname)s]%(reset)s %(message)s')
        
        # Create a log record
        record = logging.LogRecord(
            name='Test',
            level=logging.WARNING,
            pathname='test.py',
            lineno=1,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        
        # Should contain color codes for WARNING (yellow)
        assert '\033[33m' in formatted  # Yellow for WARNING
        assert '\033[0m' in formatted   # Reset code
        assert '[WARNING]' in formatted
        assert 'Test message' in formatted

    def test_format_unknown_level(self):
        """
        Scenario: Format log record with unknown level
        
        Given a log record with custom level
        When ColoredFormatter.format() is called
        Then it should not add color codes
        """
        formatter = ColoredFormatter('%(color)s[%(levelname)s]%(reset)s %(message)s')
        
        # Create a log record with custom level
        record = logging.LogRecord(
            name='Test',
            level=15,  # Custom level between DEBUG and INFO
            pathname='test.py',
            lineno=1,
            msg='Test message',
            args=(),
            exc_info=None
        )
        record.levelname = 'CUSTOM'
        
        formatted = formatter.format(record)
        
        # Should not contain color codes for unknown level
        assert '\033[' not in formatted
        assert '[CUSTOM]' in formatted
        assert 'Test message' in formatted

class TestGetLoggerFunction:
    """
    Feature: get_logger convenience function
    
    This test suite validates the get_logger convenience function
    which provides a simplified interface to get logger instances.
    """

    def test_get_logger_function(self):
        """
        Scenario: Use get_logger convenience function
        
        Given the get_logger function is imported
        When get_logger() is called with module name
        Then it should return a configured logger instance
        """
        logger = get_logger('TestModule')
        
        assert logger.name == 'pyzui.TestModule'
        assert isinstance(logger, logging.Logger)

    def test_get_logger_consistent_with_class_method(self):
        """
        Scenario: Compare get_logger function with class method
        
        Given both get_logger function and LoggerConfig.get_logger method
        When called with the same module name
        Then they should return the same logger instance
        """
        logger1 = get_logger('TestModule')
        logger2 = LoggerConfig.get_logger('TestModule')
        
        assert logger1 is logger2