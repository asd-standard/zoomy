import pytest
import sys
from unittest.mock import Mock, patch, MagicMock, call
from io import StringIO

# Mock the problematic imports before importing cleanuptilestore
sys.modules['tilestore'] = MagicMock()
sys.modules['logger'] = MagicMock()

# Import the cleanuptilestore module
from pyzui.tilesystem.tilestore import cleanuptilestore


class TestCleanupTilestore:
    """
    Feature: Tilestore Cleanup Utility

    The cleanuptilestore module provides a command-line utility for manually
    cleaning up old tiles from the tilestore directory. It supports dry-run mode,
    statistics display, and configurable age-based cleanup.
    """

    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.TileStore.get_tilestore_stats')
    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.TileStore.cleanup_old_tiles')
    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.LoggerConfig.initialize')
    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.get_logger')
    @patch('sys.argv', ['cleanuptilestore.py'])
    def test_main_default_behavior(self, mock_logger_factory, mock_logger_init, mock_cleanup, mock_stats):
        """
        Scenario: Run cleanup with default parameters

        Given no command line arguments
        When main() is called
        Then cleanup should run with age=3 days
        And logger should be initialized
        And cleanup summary should be printed
        """
        mock_logger = Mock()
        mock_logger_factory.return_value = mock_logger

        mock_cleanup.return_value = {
            'deleted_media_count': 5,
            'deleted_size_mb': 123.45,
            'kept_media_count': 10,
            'errors': []
        }

        mock_stats.return_value = {
            'media_count': 10,
            'file_count': 100,
            'total_size_mb': 500.0
        }

        with patch('builtins.print') as mock_print:
            result = cleanuptilestore.main()

        assert result == 0
        mock_cleanup.assert_called_once_with(max_age_days=3, dry_run=False)
        mock_logger_init.assert_called_once()

    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.TileStore.get_tilestore_stats')
    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.LoggerConfig.initialize')
    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.get_logger')
    @patch('sys.argv', ['cleanuptilestore.py', '--stats'])
    def test_main_stats_only(self, mock_logger_factory, mock_logger_init, mock_stats):
        """
        Scenario: Display tilestore statistics only

        Given --stats command line argument
        When main() is called
        Then statistics should be displayed
        And no cleanup should be performed
        """
        mock_logger = Mock()
        mock_logger_factory.return_value = mock_logger

        mock_stats.return_value = {
            'media_count': 15,
            'file_count': 200,
            'total_size_mb': 750.5
        }

        with patch('builtins.print') as mock_print:
            result = cleanuptilestore.main()

        assert result == 0
        assert mock_print.call_count > 0
        # Verify statistics were printed
        print_output = ' '.join([str(call[0][0]) for call in mock_print.call_args_list])
        assert '15' in print_output  # media count
        assert '200' in print_output  # file count
        assert '750.5' in print_output or '750.50' in print_output  # total size

    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.TileStore.get_tilestore_stats')
    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.TileStore.cleanup_old_tiles')
    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.LoggerConfig.initialize')
    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.get_logger')
    @patch('sys.argv', ['cleanuptilestore.py', '--dry-run'])
    def test_main_dry_run(self, mock_logger_factory, mock_logger_init, mock_cleanup, mock_stats):
        """
        Scenario: Run cleanup in dry-run mode

        Given --dry-run command line argument
        When main() is called
        Then cleanup should run with dry_run=True
        And no files should actually be deleted
        """
        mock_logger = Mock()
        mock_logger_factory.return_value = mock_logger

        mock_cleanup.return_value = {
            'deleted_media_count': 8,
            'deleted_size_mb': 256.0,
            'kept_media_count': 12,
            'errors': []
        }

        mock_stats.return_value = {
            'media_count': 20,
            'file_count': 300,
            'total_size_mb': 1000.0
        }

        with patch('builtins.print') as mock_print:
            result = cleanuptilestore.main()

        assert result == 0
        mock_cleanup.assert_called_once_with(max_age_days=3, dry_run=True)

        # Verify dry-run message was printed
        print_output = ' '.join([str(call[0][0]) for call in mock_print.call_args_list])
        assert 'DRY RUN' in print_output or 'Would delete' in print_output

    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.TileStore.get_tilestore_stats')
    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.TileStore.cleanup_old_tiles')
    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.LoggerConfig.initialize')
    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.get_logger')
    @patch('sys.argv', ['cleanuptilestore.py', '--age', '7'])
    def test_main_custom_age(self, mock_logger_factory, mock_logger_init, mock_cleanup, mock_stats):
        """
        Scenario: Run cleanup with custom age parameter

        Given --age 7 command line argument
        When main() is called
        Then cleanup should use 7 days as the age threshold
        """
        mock_logger = Mock()
        mock_logger_factory.return_value = mock_logger

        mock_cleanup.return_value = {
            'deleted_media_count': 3,
            'deleted_size_mb': 50.0,
            'kept_media_count': 17,
            'errors': []
        }

        mock_stats.return_value = {
            'media_count': 17,
            'file_count': 250,
            'total_size_mb': 800.0
        }

        with patch('builtins.print'):
            result = cleanuptilestore.main()

        assert result == 0
        mock_cleanup.assert_called_once_with(max_age_days=7, dry_run=False)

    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.TileStore.get_tilestore_stats')
    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.TileStore.cleanup_old_tiles')
    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.LoggerConfig.initialize')
    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.get_logger')
    @patch('sys.argv', ['cleanuptilestore.py', '--verbose'])
    def test_main_verbose_mode(self, mock_logger_factory, mock_logger_init, mock_cleanup, mock_stats):
        """
        Scenario: Run cleanup with verbose output

        Given --verbose command line argument
        When main() is called
        Then logger should be initialized with verbose=True
        """
        mock_logger = Mock()
        mock_logger_factory.return_value = mock_logger

        mock_cleanup.return_value = {
            'deleted_media_count': 2,
            'deleted_size_mb': 30.0,
            'kept_media_count': 18,
            'errors': []
        }

        mock_stats.return_value = {
            'media_count': 18,
            'file_count': 220,
            'total_size_mb': 700.0
        }

        with patch('builtins.print'):
            result = cleanuptilestore.main()

        assert result == 0
        # Verify logger was initialized with verbose=True
        init_call = mock_logger_init.call_args
        assert init_call.kwargs['verbose'] is True

    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.TileStore.get_tilestore_stats')
    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.TileStore.cleanup_old_tiles')
    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.LoggerConfig.initialize')
    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.get_logger')
    @patch('sys.argv', ['cleanuptilestore.py', '--debug'])
    def test_main_debug_mode(self, mock_logger_factory, mock_logger_init, mock_cleanup, mock_stats):
        """
        Scenario: Run cleanup with debug output

        Given --debug command line argument
        When main() is called
        Then logger should be initialized with debug=True
        """
        mock_logger = Mock()
        mock_logger_factory.return_value = mock_logger

        mock_cleanup.return_value = {
            'deleted_media_count': 1,
            'deleted_size_mb': 10.0,
            'kept_media_count': 19,
            'errors': []
        }

        mock_stats.return_value = {
            'media_count': 19,
            'file_count': 210,
            'total_size_mb': 650.0
        }

        with patch('builtins.print'):
            result = cleanuptilestore.main()

        assert result == 0
        # Verify logger was initialized with debug=True
        init_call = mock_logger_init.call_args
        assert init_call.kwargs['debug'] is True

    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.TileStore.get_tilestore_stats')
    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.TileStore.cleanup_old_tiles')
    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.LoggerConfig.initialize')
    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.get_logger')
    @patch('sys.argv', ['cleanuptilestore.py'])
    def test_main_with_errors(self, mock_logger_factory, mock_logger_init, mock_cleanup, mock_stats):
        """
        Scenario: Handle cleanup errors gracefully

        Given cleanup encounters errors
        When main() is called
        Then errors should be displayed in the summary
        And the function should still return successfully
        """
        mock_logger = Mock()
        mock_logger_factory.return_value = mock_logger

        mock_cleanup.return_value = {
            'deleted_media_count': 4,
            'deleted_size_mb': 100.0,
            'kept_media_count': 15,
            'errors': [
                'Failed to delete /path/to/tile1',
                'Permission denied for /path/to/tile2'
            ]
        }

        mock_stats.return_value = {
            'media_count': 15,
            'file_count': 180,
            'total_size_mb': 600.0
        }

        with patch('builtins.print') as mock_print:
            result = cleanuptilestore.main()

        assert result == 0

        # Verify errors were printed
        print_output = ' '.join([str(call[0][0]) for call in mock_print.call_args_list])
        assert 'Errors:' in print_output or '2' in print_output

    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.TileStore.get_tilestore_stats')
    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.TileStore.cleanup_old_tiles')
    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.LoggerConfig.initialize')
    @patch('pyzui.tilesystem.tilestore.cleanuptilestore.get_logger')
    @patch('sys.argv', ['cleanuptilestore.py', '--stats', '--dry-run'])
    def test_main_stats_with_dry_run(self, mock_logger_factory, mock_logger_init, mock_cleanup, mock_stats):
        """
        Scenario: Display statistics with dry-run flag

        Given both --stats and --dry-run arguments
        When main() is called
        Then statistics should be displayed
        And cleanup should also run in dry-run mode
        """
        mock_logger = Mock()
        mock_logger_factory.return_value = mock_logger

        mock_stats.return_value = {
            'media_count': 12,
            'file_count': 150,
            'total_size_mb': 550.0
        }

        mock_cleanup.return_value = {
            'deleted_media_count': 6,
            'deleted_size_mb': 150.0,
            'kept_media_count': 6,
            'errors': []
        }

        with patch('builtins.print') as mock_print:
            result = cleanuptilestore.main()

        assert result == 0
        # Both stats and cleanup should be called
        assert mock_stats.call_count >= 1
        mock_cleanup.assert_called_once_with(max_age_days=3, dry_run=True)
