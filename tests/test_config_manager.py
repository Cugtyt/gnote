"""Tests for config_manager module."""

from pathlib import Path

from pytest import MonkeyPatch

from gctx.config import TokenApproach
from gctx.config_manager import ConfigManager


def test_config_manager_defaults(temp_gctx_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test that ConfigManager loads default config."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    config = ConfigManager.load_for_branch("test")

    assert config.token_approach == TokenApproach.CHARDIV4
    assert config.token_limit == 8000


def test_config_manager_global_config(temp_gctx_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test global config creation and loading."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    config_data: dict[str, str | int] = {"token_limit": 10000}
    ConfigManager.save_branch_override("", config_data)

    ConfigManager.initialize_default()
    config = ConfigManager.load_for_branch("test")
    assert config.token_limit == 8000


def test_config_manager_branch_config(temp_gctx_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test branch-specific config override."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    ConfigManager.initialize_default()

    override_data: dict[str, str | int] = {"token_limit": 12000}
    ConfigManager.save_branch_override("test", override_data)

    config = ConfigManager.load_for_branch("test")
    assert config.token_limit == 12000


def test_config_manager_merge(temp_gctx_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test config merging between global and branch."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    ConfigManager.initialize_default()

    override_data: dict[str, str | int] = {"token_limit": 15000}
    ConfigManager.save_branch_override("test", override_data)

    config = ConfigManager.load_for_branch("test")
    assert config.token_limit == 15000
    assert config.token_approach == TokenApproach.CHARDIV4


def test_get_branch_override(temp_gctx_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test getting branch override."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    overrides: dict[str, str | int] = {"token_limit": 12000}
    ConfigManager.save_branch_override("test", overrides)

    result = ConfigManager.get_branch_override("test")
    assert result == overrides

    result = ConfigManager.get_branch_override("nonexistent")
    assert result == {}
