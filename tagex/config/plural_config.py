#!/usr/bin/env python3
"""
Configuration for plural preference behavior.

Allows users to configure how plural/singular variants are handled.
"""
import yaml
from pathlib import Path
from typing import Literal, Optional
from enum import Enum


class PluralPreference(str, Enum):
    """Plural preference modes."""
    PLURAL = "plural"      # Always prefer plural form
    SINGULAR = "singular"  # Always prefer singular form
    USAGE = "usage"        # Prefer most-used form


# Default configuration
DEFAULT_PLURAL_PREFERENCE = PluralPreference.USAGE
DEFAULT_USAGE_RATIO_THRESHOLD = 2.0  # Prefer most-used if ratio >= this


class PluralConfig:
    """Configuration for plural normalization behavior."""

    def __init__(self,
                 preference: PluralPreference = DEFAULT_PLURAL_PREFERENCE,
                 usage_ratio_threshold: float = DEFAULT_USAGE_RATIO_THRESHOLD):
        """Initialize plural configuration.

        Args:
            preference: How to choose between singular/plural variants
            usage_ratio_threshold: Minimum usage ratio to prefer most-used form
        """
        self.preference = preference
        self.usage_ratio_threshold = usage_ratio_threshold

    @classmethod
    def from_vault(cls, vault_path: str) -> 'PluralConfig':
        """Load configuration from vault's .tagex-config.yaml file.

        Args:
            vault_path: Path to vault directory

        Returns:
            PluralConfig instance with loaded or default settings
        """
        config_file = Path(vault_path) / '.tagex-config.yaml'

        if not config_file.exists():
            return cls()  # Return defaults

        try:
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f) or {}

            plural_config = config_data.get('plural', {})

            preference = plural_config.get('preference', DEFAULT_PLURAL_PREFERENCE)
            if isinstance(preference, str):
                preference = PluralPreference(preference)

            usage_ratio = plural_config.get('usage_ratio_threshold',
                                           DEFAULT_USAGE_RATIO_THRESHOLD)

            return cls(preference=preference, usage_ratio_threshold=usage_ratio)

        except Exception:
            # If there's any error loading config, use defaults
            return cls()

    def to_dict(self) -> dict:
        """Convert configuration to dictionary format.

        Returns:
            Dictionary representation of configuration
        """
        return {
            'preference': self.preference.value,
            'usage_ratio_threshold': self.usage_ratio_threshold
        }
