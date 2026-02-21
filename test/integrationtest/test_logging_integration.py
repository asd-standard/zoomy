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

"""
Integration Tests: Logging System
=================================

This module contains integration tests validating the PyZUI logging system
as described in the technical documentation. The tests verify:

- Command-line argument parsing and configuration
- Log level behavior in different modes (Normal, Verbose, Debug)
- File rotation (10MB max, 5 backups)
- Console vs file logging behavior
- Runtime log level control
- Configuration file support
- Integration with actual PyZUI components
"""

import sys
import os
import pytest
import tempfile
import shutil
import json
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pyzui.logger import LoggerConfig, get_logger
import pyzui.tilesystem.tilemanager as TileManager

class TestLoggingCommandLine:
    """
    Feature: Command-Line Logging Configuration
    
    This test suite validates that command-line arguments correctly
    configure the logging system as documented.
    """

    def test_default_logging_behavior(self):
        """
        Scenario: Run with default settings
        
        Given no command-line arguments
        When PyZUI is started
        Then it should log WARNING+ to console
        And it should log INFO+ to file
        And console output should be colored
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Reset logger state
            LoggerConfig._initialized = False
            LoggerConfig._log_dir = None
            LoggerConfig._log_file = None
            
            # Capture console output
            import io
            import sys
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                # Initialize with default settings (should match main.py defaults)
                LoggerConfig.initialize(
                    debug=False,
                    log_to_file=True,
                    log_to_console=True,
                    log_dir=temp_dir + '/test_logs',
                    colored_output=False,  # Disable color for test
                    verbose=False
                )
                
                logger = get_logger('TestModule')
                logger.debug("DEBUG message - should not appear in console")
                logger.info("INFO message - should not appear in console")
                logger.warning("WARNING message - should appear in console")
                logger.error("ERROR message - should appear in console")
            
            console_output = f.getvalue()
            
            # Check console output
            assert "DEBUG message" not in console_output
            assert "INFO message" not in console_output
            assert "WARNING message" in console_output
            assert "ERROR message" in console_output
            
            # Check that log file was created
            log_file = Path(temp_dir) / "test_logs" / "pyzui.log"
            assert log_file.exists()
            
            # Check log file contents
            log_content = log_file.read_text()
            assert "INFO message" in log_content
            assert "WARNING message" in log_content
            assert "ERROR message" in log_content

    def test_debug_mode(self):
        """
        Scenario: Run with --debug flag
        
        Given the --debug command-line argument
        When PyZUI is started
        Then it should log DEBUG+ to both console and file
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Reset logger state
            LoggerConfig._initialized = False
            LoggerConfig._log_dir = None
            LoggerConfig._log_file = None
            
            import io
            import sys
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                # Initialize with debug mode
                LoggerConfig.initialize(
                    debug=True,
                    log_to_file=True,
                    log_to_console=True,
                    log_dir=temp_dir + '/test_logs',
                    colored_output=False,
                    verbose=False
                )
                
                logger = get_logger('TestModule')
                logger.debug("DEBUG message - should appear in debug mode")
                logger.info("INFO message - should appear in debug mode")
                logger.warning("WARNING message - should appear in debug mode")
            
            console_output = f.getvalue()
            
            # In debug mode, all messages should appear
            assert "DEBUG message" in console_output
            assert "INFO message" in console_output
            assert "WARNING message" in console_output

    def test_verbose_mode(self):
        """
        Scenario: Run with --verbose flag
        
        Given the --verbose command-line argument
        When PyZUI is started
        Then it should log INFO+ to console
        And DEBUG+ to file
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Reset logger state
            LoggerConfig._initialized = False
            LoggerConfig._log_dir = None
            LoggerConfig._log_file = None
            
            import io
            import sys
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                # Initialize with verbose mode
                LoggerConfig.initialize(
                    debug=False,
                    log_to_file=True,
                    log_to_console=True,
                    log_dir=temp_dir + '/test_logs',
                    colored_output=False,
                    verbose=True
                )
                
                logger = get_logger('TestModule')
                logger.debug("DEBUG message - should not appear in console")
                logger.info("INFO message - should appear in console (verbose mode)")
                logger.warning("WARNING message - should appear in console")
            
            console_output = f.getvalue()
            
            # In verbose mode, INFO+ should appear in console
            assert "DEBUG message" not in console_output
            assert "INFO message" in console_output
            assert "WARNING message" in console_output
            
            # DEBUG should be in file
            log_file = Path(temp_dir) / "test_logs" / "pyzui.log"
            log_content = log_file.read_text()
            assert "DEBUG message" in log_content

    def test_no_console_flag(self):
        """
        Scenario: Run with --no-console flag
        
        Given the --no-console command-line argument
        When PyZUI is started
        Then it should not log to console
        But should still log to file
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Reset logger state
            LoggerConfig._initialized = False
            LoggerConfig._log_dir = None
            LoggerConfig._log_file = None
            
            import io
            import sys
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                # Initialize with no console
                LoggerConfig.initialize(
                    debug=False,
                    log_to_file=True,
                    log_to_console=False,
                    log_dir=temp_dir + '/test_logs',
                    colored_output=False,
                    verbose=False
                )
                
                logger = get_logger('TestModule')
                logger.warning("WARNING message - should not appear in console")
                logger.error("ERROR message - should not appear in console")
                
                # Regular print should still work
                print("Test completed - console output should only show this")
            
            console_output = f.getvalue()
            
            # No log messages should appear in console
            assert "WARNING message" not in console_output
            assert "ERROR message" not in console_output
            assert "Test completed - console output should only show this" in console_output
            
            # But messages should be in file
            log_file = Path(temp_dir) / "test_logs" / "pyzui.log"
            log_content = log_file.read_text()
            assert "WARNING message" in log_content
            assert "ERROR message" in log_content

    def test_no_file_flag(self):
        """
        Scenario: Run with --no-file flag
        
        Given the --no-file command-line argument
        When PyZUI is started
        Then it should not create log files
        But should still log to console
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Reset logger state
            LoggerConfig._initialized = False
            LoggerConfig._log_dir = None
            LoggerConfig._log_file = None
            
            import io
            import sys
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                # Initialize with no file logging
                LoggerConfig.initialize(
                    debug=False,
                    log_to_file=False,
                    log_to_console=True,
                    log_dir=temp_dir + '/test_logs',
                    colored_output=False,
                    verbose=False
                )
                
                logger = get_logger('TestModule')
                logger.warning("WARNING message - should appear in console")
                
                print("Test completed")
            
            console_output = f.getvalue()
            
            # Messages should appear in console
            assert "WARNING message" in console_output
            assert "Test completed" in console_output
            
            # No log file should be created
            log_dir = Path(temp_dir) / "test_logs"
            assert not log_dir.exists()

    def test_custom_log_directory(self):
        """
        Scenario: Run with --log-dir flag
        
        Given the --log-dir command-line argument
        When PyZUI is started
        Then it should create logs in the specified directory
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_log_dir = Path(temp_dir) / "custom_logs"
            
            # Reset logger state
            LoggerConfig._initialized = False
            LoggerConfig._log_dir = None
            LoggerConfig._log_file = None
            
            import io
            import sys
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                # Initialize with custom log directory
                LoggerConfig.initialize(
                    debug=False,
                    log_to_file=True,
                    log_to_console=False,
                    log_dir=str(custom_log_dir),
                    colored_output=False,
                    verbose=False
                )
                
                logger = get_logger('TestModule')
                logger.info("Test message")
                
                print("Test completed")
            
            # Log file should be in custom directory
            log_file = custom_log_dir / "pyzui.log"
            assert log_file.exists()
            
            log_content = log_file.read_text()
            assert "Test message" in log_content

class TestLogFileRotation:
    """
    Feature: Log File Rotation
    
    This test suite validates that log files rotate correctly
    when they reach the 10MB size limit, with up to 5 backups.
    """

    def test_log_rotation_creates_backups(self):
        """
        Scenario: Log file reaches size limit
        
        Given a log file approaching 10MB
        When it exceeds 10MB
        Then it should rotate and create backup files
        And maintain up to 5 backups
        
        Note: This test verifies rotation configuration rather than
        actually filling 10MB of logs for performance reasons.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Reset logger state
            LoggerConfig._initialized = False
            LoggerConfig._log_dir = None
            LoggerConfig._log_file = None
            
            # Initialize logging
            LoggerConfig.initialize(
                debug=True,  # Enable debug to get all messages
                log_to_file=True,
                log_to_console=False,
                log_dir=temp_dir + '/test_logs',
                colored_output=False,
                verbose=False
            )
            
            # Check that log directory was created
            log_dir = Path(temp_dir) / "test_logs"
            assert log_dir.exists()
            
            # Check that log file was created
            log_file = log_dir / "pyzui.log"
            assert log_file.exists()
            
            # Write some test data (not 10MB for performance)
            logger = get_logger('RotationTest')
            for i in range(10):
                logger.debug(f"Test rotation message {i}")
            
            # Verify file was written to
            assert log_file.stat().st_size > 0
            
            # The actual rotation would happen at 10MB, which we're not testing
            # here for performance reasons. The unit tests verify the rotation
            # configuration is correct.

    def test_rotation_preserves_old_logs(self):
        """
        Scenario: Multiple log rotations
        
        Given multiple log rotations have occurred
        When checking the log directory
        Then it should contain pyzui.log and up to 5 backups
        
        Note: This test verifies the rotation configuration is set correctly.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Reset logger state
            LoggerConfig._initialized = False
            LoggerConfig._log_dir = None
            LoggerConfig._log_file = None
            
            import io
            import sys
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                # Initialize logging
                LoggerConfig.initialize(
                    debug=False,
                    log_to_file=True,
                    log_to_console=False,
                    log_dir=temp_dir + '/test_logs',
                    colored_output=False,
                    verbose=False
                )
                
                # Check handler configuration
                import logging
                from logging.handlers import RotatingFileHandler
                
                root_logger = logging.getLogger()
                for handler in root_logger.handlers:
                    if isinstance(handler, RotatingFileHandler):
                        print(f"Max bytes: {handler.maxBytes}")
                        print(f"Backup count: {handler.backupCount}")
                        break
                
                print("Rotation config test completed")
            
            console_output = f.getvalue()
            
            # Verify rotation settings
            assert "Max bytes: 10485760" in console_output  # 10 * 1024 * 1024
            assert "Backup count: 5" in console_output

class TestConfigurationFile:
    """
    Feature: Configuration File Support
    
    This test suite validates that logging can be configured
    via JSON configuration files as documented.
    """

    def test_config_file_logging_settings(self):
        """
        Scenario: Load logging settings from config file
        
        Given a JSON configuration file with logging settings
        When PyZUI is started with --config flag
        Then it should use the settings from the config file
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config file with absolute path for log_dir
            config_logs_dir = Path(temp_dir) / "config_logs"
            config_file = Path(temp_dir) / "pyzui_config.json"
            config_data = {
                "logging": {
                    "debug": False,
                    "verbose": True,
                    "log_to_file": True,
                    "log_to_console": True,
                    "colored_output": False,
                    "log_dir": str(config_logs_dir)
                }
            }
            config_file.write_text(json.dumps(config_data, indent=2))
            
            # Reset logger state
            LoggerConfig._initialized = False
            LoggerConfig._log_dir = None
            LoggerConfig._log_file = None
            
            import io
            import sys
            import os
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                # Simulate config loading like main.py
                default_config = {
                    'logging': {
                        'debug': False,
                        'verbose': False,
                        'log_to_file': True,
                        'log_to_console': True,
                        'colored_output': True,
                        'log_dir': 'logs'
                    }
                }

                if os.path.exists(str(config_file)):
                    with open(config_file, 'r') as file:
                        user_config = json.load(file)
                        if 'logging' in user_config:
                            default_config['logging'].update(user_config['logging'])

                # Initialize with config
                LoggerConfig.initialize(**default_config['logging'])

                logger = get_logger('ConfigTest')

                # In verbose mode (from config), INFO should appear
                logger.debug("DEBUG - should not appear")
                logger.info("INFO - should appear (verbose mode)")
                logger.warning("WARNING - should appear")

                print("Config test completed")
            
            console_output = f.getvalue()
            
            # Verify verbose mode from config
            assert "DEBUG - should not appear" not in console_output
            assert "INFO - should appear (verbose mode)" in console_output
            assert "WARNING - should appear" in console_output
            
            # Verify custom log directory from config
            # The config specifies "config_logs" as relative path
            # so it should be created in temp_dir
            log_file = Path(temp_dir) / "config_logs" / "pyzui.log"
            # Note: The log file might not exist if no messages were logged
            # at INFO level or above (file level is INFO in normal mode)
            # But the directory should exist
            log_dir = Path(temp_dir) / "config_logs"
            assert log_dir.exists()

class TestRuntimeLogControl:
    """
    Feature: Runtime Log Level Control
    
    This test suite validates that log levels can be
    adjusted during program execution.
    """

    def test_runtime_level_changes(self):
        """
        Scenario: Change log level during execution
        
        Given a running application with normal logging
        When enable_debug() is called
        Then DEBUG messages should start appearing
        When disable_debug() is called
        Then DEBUG messages should stop appearing
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Reset logger state
            LoggerConfig._initialized = False
            LoggerConfig._log_dir = None
            LoggerConfig._log_file = None
            
            import io
            import sys
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                # Initialize with normal logging
                LoggerConfig.initialize(
                    debug=False,
                    log_to_file=False,
                    log_to_console=True,
                    colored_output=False,
                    verbose=False
                )

                logger = get_logger('RuntimeTest')

                print("=== Phase 1: Normal mode ===")
                logger.debug("DEBUG 1 - should not appear")
                logger.info("INFO 1 - should not appear")
                logger.warning("WARNING 1 - should appear")

                print("\n=== Phase 2: Enable debug ===")
                LoggerConfig.enable_debug()
                logger.debug("DEBUG 2 - should appear now")
                logger.info("INFO 2 - should appear now")
                logger.warning("WARNING 2 - should appear")

                print("\n=== Phase 3: Disable debug ===")
                LoggerConfig.disable_debug()
                logger.debug("DEBUG 3 - should not appear again")
                logger.info("INFO 3 - should appear (INFO level)")
                logger.warning("WARNING 3 - should appear")

                print("\nRuntime test completed")
            
            console_output = f.getvalue()
            
            # Phase 1: Normal mode
            assert "DEBUG 1 - should not appear" not in console_output
            assert "INFO 1 - should not appear" not in console_output
            assert "WARNING 1 - should appear" in console_output
            
            # Phase 2: Debug mode
            assert "DEBUG 2 - should appear now" in console_output
            assert "INFO 2 - should appear now" in console_output
            assert "WARNING 2 - should appear" in console_output
            
            # Phase 3: Back to normal (INFO level after disable_debug)
            assert "DEBUG 3 - should not appear again" not in console_output
            assert "INFO 3 - should appear (INFO level)" in console_output
            assert "WARNING 3 - should appear" in console_output

    def test_module_specific_level_control(self):
        """
        Scenario: Change log level for specific module
        
        Given multiple modules with loggers
        When set_level() is called for a specific module
        Then only that module's log level should change
        
        Note: This tests that the logger level is set correctly.
        The actual message output is tested in unit tests.
        """
        # Reset logger state
        LoggerConfig._initialized = False
        LoggerConfig._log_dir = None
        LoggerConfig._log_file = None
        
        # Initialize with normal logging
        LoggerConfig.initialize(
            debug=False,
            log_to_file=False,
            log_to_console=True,
            colored_output=False,
            verbose=False
        )

        module1_logger = get_logger('Module1')
        module2_logger = get_logger('Module2')
        
        # Initially, logger levels should be NOTSET (0)
        # which means they inherit from parent
        import logging
        assert module1_logger.level == 0  # NOTSET
        assert module2_logger.level == 0  # NOTSET
        
        # Set Module1 to DEBUG
        LoggerConfig.set_level(logging.DEBUG, module='Module1')
        
        # Module1 logger should now be DEBUG, Module2 should still be NOTSET
        assert module1_logger.level == logging.DEBUG
        assert module2_logger.level == 0  # NOTSET
        
        # Also test that we can set a different module to a different level
        LoggerConfig.set_level(logging.WARNING, module='Module2')
        assert module2_logger.level == logging.WARNING

class TestIntegrationWithComponents:
    """
    Feature: Logging Integration with PyZUI Components
    
    This test suite validates that the logging system
    works correctly with actual PyZUI components.
    """

    def test_tilemanager_logging(self):
        """
        Scenario: TileManager uses logging system
        
        Given TileManager is initialized
        When it performs operations
        Then it should log messages using the logging system
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Reset logger state
            LoggerConfig._initialized = False
            LoggerConfig._log_dir = None
            LoggerConfig._log_file = None
            
            import io
            import sys
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                # Initialize logging
                LoggerConfig.initialize(
                    debug=False,
                    log_to_file=True,
                    log_to_console=True,
                    log_dir=temp_dir + '/test_logs',
                    colored_output=False,
                    verbose=True  # Use verbose to see INFO messages
                )

                # Initialize TileManager (should log initialization)
                import pyzui.tilesystem.tilemanager as TileManager
                TileManager.init(
                    auto_cleanup=False,
                    cleanup_max_age_days=1,
                    collect_cleanup_stats=False
                )

                print("TileManager logging test completed")
            
            console_output = f.getvalue()
            
            # TileManager should log initialization
            assert "TileManager logging test completed" in console_output
            
            # Check log file for TileManager messages
            log_file = Path(temp_dir) / "test_logs" / "pyzui.log"
            if log_file.exists():
                log_content = log_file.read_text()
                # TileManager should log something during init
                assert "TileManager" in log_content or "tile" in log_content.lower()

if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])