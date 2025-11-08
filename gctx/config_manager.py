"""Configuration file management for gctx."""

import json
from pathlib import Path

from gctx.config import GctxConfig


class ConfigManager:
    """Manages configuration files and merging logic."""

    GCTX_HOME: Path = Path.home() / ".gctx"
    REPO_PATH: Path = GCTX_HOME / "repo"
    CONTEXT_FILE: str = "context"

    @classmethod
    def load_for_branch(cls, branch: str) -> GctxConfig:
        """Load merged config for a branch.

        Loads global config from ~/.gctx/config.json, then merges with
        branch-specific overrides from ~/.gctx/configs/{branch}.json.

        Args:
            branch: Branch name

        Returns:
            Merged GctxConfig instance
        """
        global_path = cls.GCTX_HOME / "config.json"
        branch_path = cls.GCTX_HOME / "configs" / f"{branch}.json"

        if global_path.exists():
            with open(global_path, encoding="utf-8") as f:
                global_data = json.load(f)
        else:
            global_data = {}

        if branch_path.exists():
            with open(branch_path, encoding="utf-8") as f:
                branch_data = json.load(f)
                global_data.update(branch_data)

        # Create config from merged data, or use defaults if empty
        return GctxConfig(**global_data) if global_data else GctxConfig()

    @classmethod
    def save_global(cls, config: GctxConfig) -> None:
        """Save global configuration.

        Args:
            config: Config instance to save
        """
        global_path = cls.GCTX_HOME / "config.json"
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
        branch_path = cls.GCTX_HOME / "configs" / f"{branch}.json"
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
        branch_path = cls.GCTX_HOME / "configs" / f"{branch}.json"

        if not branch_path.exists():
            return {}

        with open(branch_path, encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def initialize_default(cls) -> None:
        """Create default global config file if it doesn't exist."""
        global_path = cls.GCTX_HOME / "config.json"

        if not global_path.exists():
            global_path.parent.mkdir(parents=True, exist_ok=True)
            config = GctxConfig()
            cls.save_global(config)
