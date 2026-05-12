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

"""
Feature: Configuration Management

The ConfigManager class manages PyZUI configuration with ~/.pyzui/config.json
as single source of truth. It provides validation, default creation, and
temporary overrides.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from pyzui.config import ConfigManager, ValidationError


class TestConfigManager:
    """
    Feature: Configuration Management Operations

    The ConfigManager class provides methods for managing configuration
    with validation, default creation, and override support.
    """

    def test_init_default_path(self):
        """
        Scenario: Create ConfigManager with default path

        Given no config_file parameter
        When ConfigManager is created
        Then it should use ~/.pyzui/config.json
        """
        manager = ConfigManager()

        expected_path = str(Path.home() / ".pyzui" / "config.json")
        assert manager.get_config_path() == expected_path

    def test_init_custom_path(self):
        """
        Scenario: Create ConfigManager with custom path

        Given config_file parameter
        When ConfigManager is created
        Then it should use the specified path
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'custom_config.json')
            manager = ConfigManager(config_file=config_file)

            assert manager.get_config_path() == config_file

    def test_create_default_config(self):
        """
        Scenario: Create default config when file doesn't exist

        Given config file doesn't exist
        When load() is called
        Then it should create file with defaults
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'config.json')
            manager = ConfigManager(config_file=config_file)

            config = manager.load()

            assert os.path.exists(config_file)
            assert 'logging' in config
            assert 'autosave' in config
            assert config['autosave']['enabled'] is True
            assert config['autosave']['max_backups'] == 20

    def test_load_existing_config(self):
        """
        Scenario: Load existing config file

        Given config file exists with valid configuration
        When load() is called
        Then it should load and validate the configuration
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'config.json')

            # Create valid config file
            test_config = {
                'autosave': {
                    'enabled': False,
                    'interval': 600,
                    'max_backups': 10
                }
            }
            with open(config_file, 'w') as f:
                json.dump(test_config, f)

            manager = ConfigManager(config_file=config_file)
            config = manager.load()

            assert config['autosave']['enabled'] is False
            assert config['autosave']['interval'] == 600
            assert config['autosave']['max_backups'] == 10

            # Other sections should have defaults
            assert 'logging' in config
            assert 'tilestore' in config

    def test_validation_invalid_interval(self):
        """
        Scenario: Validation rejects invalid interval

        Given config with interval < 60
        When load() is called
        Then it should raise ValidationError
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'config.json')

            # Create invalid config
            invalid_config = {
                'autosave': {'interval': 30}  # Too low, minimum 60
            }
            with open(config_file, 'w') as f:
                json.dump(invalid_config, f)

            manager = ConfigManager(config_file=config_file)

            with pytest.raises(ValidationError, match="at least 60"):
                manager.load()

    def test_validation_invalid_max_backups(self):
        """
        Scenario: Validation rejects invalid max_backups

        Given config with max_backups < 1
        When load() is called
        Then it should raise ValidationError
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'config.json')

            invalid_config = {
                'autosave': {'max_backups': 0}  # Too low, minimum 1
            }
            with open(config_file, 'w') as f:
                json.dump(invalid_config, f)

            manager = ConfigManager(config_file=config_file)

            with pytest.raises(ValidationError, match="at least 1"):
                manager.load()

    def test_validation_unknown_section(self):
        """
        Scenario: Validation rejects unknown sections

        Given config with unknown section
        When load() is called
        Then it should raise ValidationError
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'config.json')

            invalid_config = {
                'unknown_section': {'key': 'value'}
            }
            with open(config_file, 'w') as f:
                json.dump(invalid_config, f)

            manager = ConfigManager(config_file=config_file)

            with pytest.raises(ValidationError, match="Unknown configuration section"):
                manager.load()

    def test_validation_unknown_key(self):
        """
        Scenario: Validation rejects unknown keys

        Given config with unknown key in known section
        When load() is called
        Then it should raise ValidationError
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'config.json')

            invalid_config = {
                'autosave': {'unknown_key': 'value'}
            }
            with open(config_file, 'w') as f:
                json.dump(invalid_config, f)

            manager = ConfigManager(config_file=config_file)

            with pytest.raises(ValidationError, match="Unknown configuration key"):
                manager.load()

    def test_validation_wrong_type(self):
        """
        Scenario: Validation rejects wrong type

        Given config with wrong type for key
        When load() is called
        Then it should raise ValidationError
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'config.json')

            invalid_config = {
                'autosave': {'enabled': 'not_a_boolean'}  # Should be bool
            }
            with open(config_file, 'w') as f:
                json.dump(invalid_config, f)

            manager = ConfigManager(config_file=config_file)

            with pytest.raises(ValidationError, match="expected bool"):
                manager.load()

    def test_validation_priority_thresholds(self):
        """
        Scenario: Validation rejects invalid priority thresholds

        Given config with invalid priority thresholds
        When load() is called
        Then it should raise ValidationError
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'config.json')

            # Thresholds not in correct order
            invalid_config = {
                'parallel_rendering': {
                    'priority_thresholds': {
                        'high': 1000.0,
                        'medium': 500.0,  # medium should be > high
                        'low': 2000.0
                    }
                }
            }
            with open(config_file, 'w') as f:
                json.dump(invalid_config, f)

            manager = ConfigManager(config_file=config_file)

            with pytest.raises(ValidationError, match="low > medium > high"):
                manager.load()

    def test_save_config(self):
        """
        Scenario: Save configuration to file

        Given valid configuration
        When save() is called
        Then it should write to file
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'config.json')
            manager = ConfigManager(config_file=config_file)

            # Load to create default
            config = manager.load()

            # Modify config
            config['autosave']['enabled'] = False
            config['autosave']['interval'] = 1200

            # Save
            result = manager.save(config)

            assert result is True
            assert os.path.exists(config_file)

            # Verify saved content
            with open(config_file) as f:
                saved_config = json.load(f)

            assert saved_config['autosave']['enabled'] is False
            assert saved_config['autosave']['interval'] == 1200

    def test_save_invalid_config(self):
        """
        Scenario: Save rejects invalid configuration

        Given invalid configuration
        When save() is called
        Then it should raise ValidationError
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'config.json')
            manager = ConfigManager(config_file=config_file)

            invalid_config = {
                'autosave': {'interval': 30}  # Too low
            }

            with pytest.raises(ValidationError):
                manager.save(invalid_config)

    def test_merge_override(self):
        """
        Scenario: Merge temporary override configuration

        Given current configuration and override
        When merge_override() is called
        Then it should return merged configuration
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'config.json')
            manager = ConfigManager(config_file=config_file)

            # Load default config
            manager.load()

            # Create override
            override = {
                'autosave': {
                    'enabled': False,
                    'interval': 1200
                }
            }

            merged = manager.merge_override(override)

            # Override should take precedence
            assert merged['autosave']['enabled'] is False
            assert merged['autosave']['interval'] == 1200

            # Other sections should remain
            assert 'logging' in merged
            assert 'tilestore' in merged

    def test_merge_override_invalid(self):
        """
        Scenario: Merge rejects invalid override

        Given invalid override configuration
        When merge_override() is called
        Then it should raise ValidationError
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'config.json')
            manager = ConfigManager(config_file=config_file)

            # Load default config
            manager.load()

            # Invalid override (unknown section)
            invalid_override = {
                'unknown_section': {'key': 'value'}
            }

            with pytest.raises(ValidationError, match="Unknown section"):
                manager.merge_override(invalid_override)

    def test_json_decode_error(self):
        """
        Scenario: Handle JSON decode error

        Given config file with invalid JSON
        When load() is called
        Then it should raise ValidationError
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'config.json')

            # Write invalid JSON
            with open(config_file, 'w') as f:
                f.write('{invalid json}')

            manager = ConfigManager(config_file=config_file)

            with pytest.raises(ValidationError, match="Invalid JSON"):
                manager.load()

    def test_missing_sections_added(self):
        """
        Scenario: Missing sections are added with defaults

        Given config file missing some sections
        When load() is called
        Then missing sections should be added with defaults
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'config.json')

            # Config with only autosave section
            partial_config = {
                'autosave': {
                    'enabled': False,
                    'interval': 600
                }
            }
            with open(config_file, 'w') as f:
                json.dump(partial_config, f)

            manager = ConfigManager(config_file=config_file)
            config = manager.load()

            # All sections should be present
            assert 'logging' in config
            assert 'tilestore' in config
            assert 'parallel_rendering' in config
            assert 'autosave' in config

            # Autosave should have our values
            assert config['autosave']['enabled'] is False
            assert config['autosave']['interval'] == 600

            # Other sections should have defaults
            assert config['logging']['debug'] is False
            assert config['tilestore']['auto_cleanup'] is True

    def test_expand_paths_tilde_expansion(self):
        """
        Scenario: Tilde paths are expanded in configuration

        Given configuration dictionary with tilde paths
        When _expand_paths is called
        Then tilde should be expanded to home directory
        """
        manager = ConfigManager()

        # Test config with tilde paths
        config = {
            'autosave': {
                'backup_dir': '~/.pyzui/backups',
                'custom_path': '~/custom/path'
            },
            'logging': {
                'log_dir': '~/my_logs'
            },
            'other_string': 'no_tilde_here',
            'number_value': 123,
            'nested': {
                'deep': {
                    'path': '~~/double_tilde'  # Edge case
                }
            }
        }

        expanded = manager._expand_paths(config)

        # Check tilde expansion
        assert '~' not in expanded['autosave']['backup_dir']
        assert '~' not in expanded['autosave']['custom_path']
        assert '~' not in expanded['logging']['log_dir']

        # Should start with home directory
        home = str(Path.home())
        assert expanded['autosave']['backup_dir'].startswith(home)
        assert expanded['autosave']['custom_path'].startswith(home)
        assert expanded['logging']['log_dir'].startswith(home)

        # Non-string values should remain unchanged
        assert expanded['other_string'] == 'no_tilde_here'
        assert expanded['number_value'] == 123

        # Double tilde - os.path.expanduser doesn't expand ~~, but that's okay
        # It's an edge case that's unlikely in real usage
        # We'll just verify the method doesn't crash on it
        assert 'path' in expanded['nested']['deep']

    def test_default_config_has_expanded_backup_dir(self):
        """
        Scenario: DEFAULT_CONFIG has expanded backup directory

        Given ConfigManager.DEFAULT_CONFIG
        Then backup_dir should not contain tilde
        """
        from pyzui.config import ConfigManager

        # Check that DEFAULT_CONFIG has expanded path
        backup_dir = ConfigManager.DEFAULT_CONFIG['autosave']['backup_dir']
        assert '~' not in backup_dir, f"backup_dir should not contain tilde: {backup_dir}"

        # Should be a valid expanded path
        assert backup_dir.startswith(str(Path.home()))
        assert '.pyzui/backups' in backup_dir or '.pyzui\\backups' in backup_dir

    def test_load_expands_tilde_paths(self):
        """
        Scenario: load() expands tilde paths in config file

        Given config file with tilde paths
        When load() is called
        Then returned config should have expanded paths
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'config.json')

            # Config with tilde paths
            config_with_tilde = {
                'autosave': {
                    'backup_dir': '~/custom_backups',
                    'enabled': True,
                    'interval': 300,
                    'max_backups': 15
                },
                'logging': {
                    'log_dir': '~/app_logs'
                }
            }

            with open(config_file, 'w') as f:
                json.dump(config_with_tilde, f)

            manager = ConfigManager(config_file=config_file)
            config = manager.load()

            # Check tilde expansion
            assert '~' not in config['autosave']['backup_dir']
            assert '~' not in config['logging']['log_dir']

            # Should be expanded paths
            home = str(Path.home())
            assert config['autosave']['backup_dir'].startswith(home)
            assert config['logging']['log_dir'].startswith(home)

            # Other values should be preserved
            assert config['autosave']['enabled'] is True
            assert config['autosave']['interval'] == 300
            assert config['autosave']['max_backups'] == 15

    def test_merge_override_expands_tilde_paths(self):
        """
        Scenario: merge_override() expands tilde paths

        Given override config with tilde paths
        When merge_override() is called
        Then merged config should have expanded paths
        """
        manager = ConfigManager()

        # Load default config first
        manager.load()

        # Override with tilde paths
        override_config = {
            'autosave': {
                'backup_dir': '~/override_backups'
            },
            'logging': {
                'log_dir': '~/override_logs'
            }
        }

        merged = manager.merge_override(override_config)

        # Check tilde expansion
        assert '~' not in merged['autosave']['backup_dir']
        assert '~' not in merged['logging']['log_dir']

        # Should be expanded paths
        home = str(Path.home())
        assert merged['autosave']['backup_dir'].startswith(home)
        assert merged['logging']['log_dir'].startswith(home)

    def test_save_expands_tilde_paths(self):
        """
        Scenario: save() expands tilde paths before saving

        Given config with tilde paths
        When save() is called
        Then saved config should have expanded paths
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, 'config.json')
            manager = ConfigManager(config_file=config_file)

            # Config with tilde paths
            config_with_tilde = {
                'autosave': {
                    'backup_dir': '~/save_test_backups',
                    'enabled': True
                }
            }

            # Save config
            manager.save(config_with_tilde)

            # Load it back
            loaded_config = manager.load()

            # Check tilde expansion
            assert '~' not in loaded_config['autosave']['backup_dir']

            # Should be expanded path
            home = str(Path.home())
            assert loaded_config['autosave']['backup_dir'].startswith(home)
