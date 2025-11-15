"""Configuration file management for gnote."""

import json
from pathlib import Path

from gnote.config import GnoteConfig


class ConfigManager:
    """Manages configuration files and merging logic."""

    GNOTE_HOME: Path = Path.home() / ".gnote"
    REPO_PATH: Path = GNOTE_HOME / "repo"
    NOTE_FILE: str = "note"
    GLOBAL_CONFIG_FILE: str = "global.config.json"

    @classmethod
    def load_for_branch(cls, branch: str) -> GnoteConfig:
        """Load merged config for a branch.

        Loads global config from ~/.gnote/config.json, then merges with
        branch-specific overrides from ~/.gnote/configs/{branch}.json.

        Args:
            branch: Branch name

        Returns:
            Merged GnoteConfig instance
        """
        global_path = cls.GNOTE_HOME / cls.GLOBAL_CONFIG_FILE
        branch_path = cls.GNOTE_HOME / "configs" / f"{branch}.json"

        if global_path.exists():
            with open(global_path, encoding="utf-8") as f:
                global_data = json.load(f)
        else:
            global_data = {}

        if branch_path.exists():
            with open(branch_path, encoding="utf-8") as f:
                branch_data = json.load(f)
                global_data.update(branch_data)

        return GnoteConfig(**global_data) if global_data else GnoteConfig()

    @classmethod
    def save_global(cls, config: GnoteConfig) -> None:
        """Save global configuration.

        Args:
            config: Config instance to save
        """
        global_path = cls.GNOTE_HOME / cls.GLOBAL_CONFIG_FILE
        global_path.parent.mkdir(parents=True, exist_ok=True)

        with open(global_path, "w", encoding="utf-8") as f:
            json.dump(config.model_dump(), f, indent=2)

    @classmethod
    def save_branch_override(cls, branch: str, overrides: dict[str, str | int]) -> None:
        """Save branch-specific config overrides.

        Args:
            branch: Branch name
            overrides: Dictionary of config values to override
        """
        branch_path = cls.GNOTE_HOME / "configs" / f"{branch}.json"
        branch_path.parent.mkdir(parents=True, exist_ok=True)

        with open(branch_path, "w", encoding="utf-8") as f:
            json.dump(overrides, f, indent=2)

    @classmethod
    def get_branch_override(cls, branch: str) -> dict[str, str | int]:
        """Get branch-specific config overrides.

        Args:
            branch: Branch name

        Returns:
            Dictionary of overrides, or empty dict if no overrides exist
        """
        branch_path = cls.GNOTE_HOME / "configs" / f"{branch}.json"

        if not branch_path.exists():
            return {}

        with open(branch_path, encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def initialize_default(cls) -> None:
        """Create default global config file if it doesn't exist."""
        global_path = cls.GNOTE_HOME / cls.GLOBAL_CONFIG_FILE

        if not global_path.exists():
            global_path.parent.mkdir(parents=True, exist_ok=True)
            config = GnoteConfig()
            cls.save_global(config)
