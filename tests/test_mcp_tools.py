"""Tests for MCP server tools."""

from pathlib import Path

from pytest import MonkeyPatch

from gctx.config import GctxConfig
from gctx.config_manager import ConfigManager
from gctx.git_manager import GitContextManager
from gctx.mcp import setup_mcp


def test_mcp_setup(temp_gctx_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test MCP server setup."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    with GitContextManager("test") as manager:
        manager.write_context("Initial content", "Initial")

    mcp = setup_mcp("test")

    assert mcp is not None
    assert mcp.name == "gctx"


def test_mcp_setup_with_config_override(temp_gctx_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test MCP server setup with config override."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    with GitContextManager("test") as manager:
        manager.write_context("Initial content", "Initial")

    custom_config = GctxConfig(token_limit=15000)
    mcp = setup_mcp("test", config_override=custom_config)

    assert mcp is not None
    assert mcp.name == "gctx"


def test_mcp_with_different_branches(temp_gctx_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test MCP server works with different branches."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    with GitContextManager("master") as manager:
        manager.write_context("Master content", "Initial")

    with GitContextManager("develop") as manager:
        manager.write_context("Develop content", "Initial")

    mcp_master = setup_mcp("master")
    assert mcp_master is not None

    mcp_develop = setup_mcp("develop")
    assert mcp_develop is not None


def test_mcp_context_manager_cleanup(temp_gctx_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test that MCP tools properly use context managers."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    with GitContextManager("test") as manager:
        manager.write_context("Test content", "Initial")
        manager.write_context("Update 1", "Update 1")
        manager.write_context("Update 2", "Update 2")

    mcp = setup_mcp("test")

    assert mcp is not None
    assert mcp.name == "gctx"
