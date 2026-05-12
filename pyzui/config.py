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

"""Configuration management for PyZUI."""

import json
import os
from pathlib import Path
from typing import Any

from pyzui.logger import get_logger


class ValidationError(Exception):
    """Raised when configuration validation fails."""

    pass


class ConfigManager:
    """
    Manages PyZUI configuration with ~/.pyzui/config.json as single source of truth.

    Features:
    - Creates default config file if missing
    - Validates configuration against schema
    - Rejects invalid values with clear errors
    - Supports temporary overrides via --config
    """

    # Centralized defaults for ALL configuration sections
    DEFAULT_CONFIG = {
        "logging": {
            "debug": False,
            "verbose": False,
            "log_to_file": True,
            "log_to_console": True,
            "colored_output": True,
            "log_dir": "logs",
        },
        "tilestore": {
            "auto_cleanup": True,
            "max_age_days": 3,
            "cleanup_on_startup": True,
            "collect_cleanup_stats": True,
        },
        "parallel_rendering": {
            "enabled": True,
            "max_workers": 4,
            "batch_size": 10,
            "max_batches": 10,
            "batch_timeout_ms": 1000,
            "enable_profiling": False,
            "priority_thresholds": {"high": 100.0, "medium": 500.0, "low": 2000.0},
            "cache_max_age_ms": 1000,
            "viewport_update_threshold": 10.0,
        },
        "autosave": {
            "enabled": True,
            "interval": 300,
            "max_backups": 20,
            "backup_dir": str(Path.home() / ".pyzui" / "backups"),
            "expire_days": 7,
        },
        "zoom": {"min_zoomlevel": -12.0, "max_zoomlevel": 10.0, "clamp_enabled": True, "default_zoomlevel": -4.0},
        "render": {"order": "smaller_on_top"},
    }

    # Validation schema: (section, key) -> validation rules
    VALIDATION_SCHEMA = {
        # Autosave validation
        ("autosave", "interval"): {
            "type": int,
            "min": 60,
            "message": "Autosave interval must be at least 60 seconds (1 minute)",
        },
        ("autosave", "max_backups"): {"type": int, "min": 1, "message": "max_backups must be at least 1"},
        ("autosave", "expire_days"): {"type": int, "min": 1, "message": "expire_days must be at least 1 day"},
        # Tilestore validation
        ("tilestore", "max_age_days"): {"type": int, "min": 1, "message": "max_age_days must be at least 1"},
        # Parallel rendering validation
        ("parallel_rendering", "max_workers"): {"type": int, "min": 1, "message": "max_workers must be at least 1"},
        ("parallel_rendering", "batch_size"): {"type": int, "min": 1, "message": "batch_size must be at least 1"},
        ("parallel_rendering", "max_batches"): {"type": int, "min": 1, "message": "max_batches must be at least 1"},
        ("parallel_rendering", "batch_timeout_ms"): {
            "type": (int, float),
            "min": 1,
            "message": "batch_timeout_ms must be positive",
        },
        ("parallel_rendering", "cache_max_age_ms"): {
            "type": (int, float),
            "min": 1,
            "message": "cache_max_age_ms must be positive",
        },
        ("parallel_rendering", "viewport_update_threshold"): {
            "type": (int, float),
            "min": 0,
            "message": "viewport_update_threshold must be non-negative",
        },
        # Priority thresholds validation
        ("parallel_rendering", "priority_thresholds"): {
            "type": dict,
            "required_keys": ["high", "medium", "low"],
            "message": "priority_thresholds must contain high, medium, and low keys",
        },
        # Boolean field validation
        ("logging", "debug"): {"type": bool, "message": "debug must be true or false"},
        ("logging", "verbose"): {"type": bool, "message": "verbose must be true or false"},
        ("logging", "log_to_file"): {"type": bool, "message": "log_to_file must be true or false"},
        ("logging", "log_to_console"): {"type": bool, "message": "log_to_console must be true or false"},
        ("logging", "colored_output"): {"type": bool, "message": "colored_output must be true or false"},
        ("tilestore", "auto_cleanup"): {"type": bool, "message": "auto_cleanup must be true or false"},
        ("tilestore", "cleanup_on_startup"): {"type": bool, "message": "cleanup_on_startup must be true or false"},
        ("tilestore", "collect_cleanup_stats"): {
            "type": bool,
            "message": "collect_cleanup_stats must be true or false",
        },
        ("parallel_rendering", "enabled"): {"type": bool, "message": "enabled must be true or false"},
        ("parallel_rendering", "enable_profiling"): {"type": bool, "message": "enable_profiling must be true or false"},
        ("autosave", "enabled"): {"type": bool, "message": "enabled must be true or false"},
        ("zoom", "clamp_enabled"): {"type": bool, "message": "clamp_enabled must be true or false"},
        # String field validation
        ("logging", "log_dir"): {"type": str, "message": "log_dir must be a string"},
        ("autosave", "backup_dir"): {"type": str, "message": "backup_dir must be a string"},
        ("render", "order"): {"type": str, "message": "render.order must be a string"},
        # Zoom validation
        ("zoom", "min_zoomlevel"): {"type": (int, float), "message": "min_zoomlevel must be a number"},
        ("zoom", "max_zoomlevel"): {"type": (int, float), "message": "max_zoomlevel must be a number"},
        ("zoom", "default_zoomlevel"): {"type": (int, float), "message": "default_zoomlevel must be a number"},
    }

    def __init__(self, config_file: str | None = None) -> None:
        """
        Initialize ConfigManager.

        Args:
            config_file: Optional custom config file path (for testing)
        """
        self._logger = get_logger("ConfigManager")

        if config_file is None:
            self._config_file = str(Path.home() / ".pyzui" / "config.json")
        else:
            self._config_file = config_file

        self._config = self.DEFAULT_CONFIG.copy()

    def _expand_paths(self, config: dict[str, Any]) -> dict[str, Any]:
        """Recursively expand tilde (~) in all string values.

        Args:
            config: Configuration dictionary

        Returns:
            Configuration with tilde paths expanded
        """
        expanded = {}
        for key, value in config.items():
            if isinstance(value, dict):
                expanded[key] = self._expand_paths(value)
            elif isinstance(value, str) and "~" in value:
                # Expand tilde using os.path.expanduser
                expanded[key] = os.path.expanduser(value)
            else:
                expanded[key] = value
        return expanded

    def load(self) -> dict[str, Any]:
        """
        Load configuration from ~/.pyzui/config.json.

        Returns:
            Validated configuration dictionary

        Raises:
            ValidationError: If configuration is invalid
            IOError: If file cannot be read (except when creating default)
            json.JSONDecodeError: If file contains invalid JSON
        """
        config_dir = os.path.dirname(self._config_file)

        # Create directory if it doesn't exist
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
            self._logger.info(f"Created config directory: {config_dir}")

        # Create default config if file doesn't exist
        if not os.path.exists(self._config_file):
            self._logger.info(f"Creating default config at {self._config_file}")
            self._config = self.DEFAULT_CONFIG.copy()
            self.save()
            return self._config.copy()

        # Load existing config
        try:
            with open(self._config_file) as f:
                loaded_config = json.load(f)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON in config file {self._config_file}: {e}") from e
        except OSError as e:
            raise OSError(f"Cannot read config file {self._config_file}: {e}") from e

        # Merge with defaults (missing sections get defaults)
        self._config = self._merge_with_defaults(loaded_config)

        # Expand tilde paths in merged config
        self._config = self._expand_paths(self._config)

        # Validate the configuration
        self._validate_config(self._config)

        # Save validated config (fixes any missing fields)
        self.save()

        return self._config.copy()

    def save(self, config: dict[str, Any] | None = None) -> bool:
        """
        Save configuration to ~/.pyzui/config.json.

        Args:
            config: Configuration to save (uses current config if None)

        Returns:
            True if successful

        Raises:
            ValidationError: If configuration is invalid
        """
        if config is not None:
            self._config = self._merge_with_defaults(config)

        # Ensure config has expanded paths before saving
        self._config = self._expand_paths(self._config)

        # Validate before saving
        self._validate_config(self._config)

        try:
            with open(self._config_file, "w") as f:
                json.dump(self._config, f, indent=2)
            self._logger.debug(f"Saved config to {self._config_file}")
            return True
        except OSError as e:
            self._logger.error(f"Cannot save config to {self._config_file}: {e}")
            return False

    def merge_override(self, override_config: dict[str, Any]) -> dict[str, Any]:
        """
        Merge temporary override configuration (from --config file).

        Args:
            override_config: Configuration to merge

        Returns:
            Merged configuration

        Raises:
            ValidationError: If override config is invalid
        """
        # Validate override config structure
        self._validate_override_config(override_config)

        # Deep merge with current config
        merged = self._deep_merge(self._config.copy(), override_config)

        # Expand tilde paths in merged config
        merged = self._expand_paths(merged)

        # Validate merged config
        self._validate_config(merged)

        return merged

    def _merge_with_defaults(self, user_config: dict[str, Any]) -> dict[str, Any]:
        """Merge user config with defaults, adding missing sections."""
        # Deep copy of defaults
        merged = {}
        for section, section_config in self.DEFAULT_CONFIG.items():
            merged[section] = section_config.copy()

        for section, section_config in user_config.items():
            if section not in merged:
                # Unknown section - reject it
                raise ValidationError(f"Unknown configuration section: '{section}'")

            if not isinstance(section_config, dict):
                raise ValidationError(f"Section '{section}' must be a dictionary")

            # Merge section config (create copy of section dict first)
            if section in merged:
                # Create a copy of the section dict before updating
                section_copy = merged[section].copy()
                section_copy.update(section_config)
                merged[section] = section_copy
            else:
                merged[section] = section_config.copy()

        return merged

    def _validate_config(self, config: dict[str, Any]) -> None:
        """
        Validate configuration against schema.

        Raises:
            ValidationError: With clear error message
        """
        errors = []

        # Check all sections exist
        for section in self.DEFAULT_CONFIG:
            if section not in config:
                errors.append(f"Missing section: '{section}'")
                continue

            if not isinstance(config[section], dict):
                errors.append(f"Section '{section}' must be a dictionary")
                continue

            # Validate each key in section
            for key, value in config[section].items():
                validation_key = (section, key)

                if validation_key not in self.VALIDATION_SCHEMA:
                    errors.append(f"Unknown configuration key: '{section}.{key}'")
                    continue

                rule = self.VALIDATION_SCHEMA[validation_key]

                # Type validation
                if not isinstance(value, rule["type"]):
                    if isinstance(rule["type"], tuple):
                        type_names = [t.__name__ for t in rule["type"]]
                        expected = " or ".join(type_names)
                    else:
                        expected = rule["type"].__name__

                    errors.append(
                        f"Invalid type for '{section}.{key}': expected {expected}, got {type(value).__name__}"
                    )
                    continue

                # Range validation for numeric types
                if "min" in rule and isinstance(value, (int, float)) and value < rule["min"]:
                    errors.append(f"Invalid value for '{section}.{key}': must be at least {rule['min']}, got {value}")

                # Special validation for priority_thresholds
                if key == "priority_thresholds":
                    if not all(k in value for k in ["high", "medium", "low"]):
                        errors.append(f"Missing keys in '{section}.{key}': must contain 'high', 'medium', and 'low'")
                    else:
                        # Check ordering: low > medium > high
                        if not (value["low"] > value["medium"] > value["high"]):
                            errors.append(f"Invalid values in '{section}.{key}': must satisfy low > medium > high")

                # Special validation for render order
                if section == "render" and key == "order":
                    valid_orders = ["smaller_on_top", "larger_on_top"]
                    if value not in valid_orders:
                        errors.append(
                            f"Invalid value for '{section}.{key}': must be one of {valid_orders}, got '{value}'"
                        )

                # Special validation for zoom limits (auto-swap if min > max)
                if section == "zoom" and key in ["min_zoomlevel", "max_zoomlevel", "default_zoomlevel"]:
                    # Check if both min and max are present
                    if "min_zoomlevel" in config[section] and "max_zoomlevel" in config[section]:
                        min_val = config[section]["min_zoomlevel"]
                        max_val = config[section]["max_zoomlevel"]
                        if min_val > max_val:
                            # Auto-swap: swap min and max
                            config[section]["min_zoomlevel"], config[section]["max_zoomlevel"] = max_val, min_val

                    # Ensure default stays within bounds
                    if "default_zoomlevel" in config[section]:
                        default_val = config[section]["default_zoomlevel"]
                        if "min_zoomlevel" in config[section] and default_val < config[section]["min_zoomlevel"]:
                            config[section]["default_zoomlevel"] = config[section]["min_zoomlevel"]
                        if "max_zoomlevel" in config[section] and default_val > config[section]["max_zoomlevel"]:
                            config[section]["default_zoomlevel"] = config[section]["max_zoomlevel"]

        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValidationError(error_msg)

    def _validate_override_config(self, config: dict[str, Any]) -> None:
        """Validate override config has correct structure."""
        if not isinstance(config, dict):
            raise ValidationError("Override config must be a dictionary")

        for section, section_config in config.items():
            if section not in self.DEFAULT_CONFIG:
                raise ValidationError(f"Unknown section in override config: '{section}'")

            if not isinstance(section_config, dict):
                raise ValidationError(f"Section '{section}' in override must be a dictionary")

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def get_config_path(self) -> str:
        """Get the path to the configuration file."""
        return self._config_file

    def get_config_dir(self) -> str:
        """Get the path to the configuration directory."""
        return os.path.dirname(self._config_file)
