"""Tests for MCP server tools."""

import asyncio
from pathlib import Path

import pytest
from pytest import MonkeyPatch

from gnote.config import GnoteConfig
from gnote.config_manager import ConfigManager
from gnote.git_manager import GitNoteManager
from gnote.mcp import setup_mcp


def test_mcp_setup(temp_gnote_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test MCP server setup and read_note tool."""
    monkeypatch.setattr(ConfigManager, "GNOTE_HOME", temp_gnote_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gnote_home / "repo")

    initial_content = "Initial test content"
    with GitNoteManager("test") as manager:
        manager.write_note(initial_content, "Initial commit")

    mcp = setup_mcp("test")

    assert mcp is not None
    assert mcp.name == "gnote"

    result = asyncio.run(mcp._tool_manager._tools["read_note"].fn())
    assert result.success is True
    assert result.content == initial_content
    assert result.token_count > 0
    assert result.error == ""


@pytest.mark.asyncio
async def test_mcp_read_note_tool(temp_gnote_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test read_note tool actually works."""
    monkeypatch.setattr(ConfigManager, "GNOTE_HOME", temp_gnote_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gnote_home / "repo")

    test_content = "Test note content"
    with GitNoteManager("test") as manager:
        manager.write_note(test_content, "Initial")

    mcp = setup_mcp("test")
    read_note_tool = mcp._tool_manager._tools["read_note"]
    result = await read_note_tool.fn()

    assert result.success is True
    assert result.content == test_content
    assert result.token_count > 0
    assert result.error == ""


@pytest.mark.asyncio
async def test_mcp_update_note_tool(temp_gnote_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test update_note tool actually works."""
    monkeypatch.setattr(ConfigManager, "GNOTE_HOME", temp_gnote_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gnote_home / "repo")

    with GitNoteManager("test") as manager:
        manager.write_note("Initial content", "Initial")

    mcp = setup_mcp("test")
    update_note_tool = mcp._tool_manager._tools["update_note"]

    new_content = "Updated content"
    result = await update_note_tool.fn(new_content, "Update test")

    assert result.success is True
    assert result.new_token_count > 0
    assert result.error == ""

    read_note_tool = mcp._tool_manager._tools["read_note"]
    read_result = await read_note_tool.fn()
    assert read_result.content == new_content


@pytest.mark.asyncio
async def test_mcp_append_to_note_tool(temp_gnote_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test append_to_note tool actually works."""
    monkeypatch.setattr(ConfigManager, "GNOTE_HOME", temp_gnote_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gnote_home / "repo")

    initial_content = "Initial content"
    with GitNoteManager("test") as manager:
        manager.write_note(initial_content, "Initial")

    mcp = setup_mcp("test")
    append_note_tool = mcp._tool_manager._tools["append_to_note"]

    append_text = "\nAppended text"
    result = await append_note_tool.fn(append_text, "Append test")

    assert result.success is True
    assert result.token_delta > 0
    assert result.error == ""

    read_note_tool = mcp._tool_manager._tools["read_note"]
    read_result = await read_note_tool.fn()
    assert initial_content in read_result.content
    assert append_text in read_result.content


@pytest.mark.asyncio
async def test_mcp_history_tool(temp_gnote_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test get_note_history tool actually works."""
    monkeypatch.setattr(ConfigManager, "GNOTE_HOME", temp_gnote_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gnote_home / "repo")

    with GitNoteManager("test") as manager:
        manager.write_note("Content 1", "First commit")
        manager.write_note("Content 2", "Second commit")
        manager.write_note("Content 3", "Third commit")

    mcp = setup_mcp("test")
    history_tool = mcp._tool_manager._tools["get_note_history"]
    result = await history_tool.fn(limit=10)

    assert result.success is True
    assert len(result.commits) == 4
    assert result.total_commits == 4
    assert result.commits[0].message == "Third commit"
    assert result.commits[1].message == "Second commit"
    assert result.commits[2].message == "First commit"
    assert result.error == ""


@pytest.mark.asyncio
async def test_mcp_search_tool(temp_gnote_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test search_note_history tool actually works."""
    monkeypatch.setattr(ConfigManager, "GNOTE_HOME", temp_gnote_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gnote_home / "repo")

    with GitNoteManager("test") as manager:
        manager.write_note("Python code here", "Add Python")
        manager.write_note("JavaScript code here", "Add JavaScript")
        manager.write_note("More Python code", "More Python")

    mcp = setup_mcp("test")
    search_tool = mcp._tool_manager._tools["search_note_history"]
    result = await search_tool.fn(keywords=["Python"], limit=100)

    assert result.success is True
    assert result.total_matches == 2
    assert len(result.commits) == 2
    assert result.error == ""


def test_mcp_setup_with_config_override(temp_gnote_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test MCP server setup with config override."""
    monkeypatch.setattr(ConfigManager, "GNOTE_HOME", temp_gnote_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gnote_home / "repo")

    with GitNoteManager("test") as manager:
        manager.write_note("Initial content", "Initial")

    custom_config = GnoteConfig(token_limit=15000)
    mcp = setup_mcp("test", config_override=custom_config)

    assert mcp is not None
    assert mcp.name == "gnote"

    tool_names = set(mcp._tool_manager._tools.keys())
    expected_tools = {
        "read_note",
        "update_note",
        "append_to_note",
        "get_note_history",
        "get_snapshot",
        "search_note_history",
    }
    assert expected_tools.issubset(tool_names)


def test_mcp_with_different_branches(temp_gnote_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test MCP server works with different branches."""
    monkeypatch.setattr(ConfigManager, "GNOTE_HOME", temp_gnote_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gnote_home / "repo")

    with GitNoteManager("master") as manager:
        manager.write_note("Master content", "Initial")

    with GitNoteManager("develop") as manager:
        manager.write_note("Develop content", "Initial")

    mcp_master = setup_mcp("master")
    assert mcp_master is not None
    assert mcp_master.name == "gnote"

    mcp_develop = setup_mcp("develop")
    assert mcp_develop is not None
    assert mcp_develop.name == "gnote"

    tool_names_master = set(mcp_master._tool_manager._tools.keys())
    tool_names_develop = set(mcp_develop._tool_manager._tools.keys())
    assert tool_names_master == tool_names_develop


def test_mcp_note_manager_cleanup(temp_gnote_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test that MCP tools properly use note managers."""
    monkeypatch.setattr(ConfigManager, "GNOTE_HOME", temp_gnote_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gnote_home / "repo")

    with GitNoteManager("test") as manager:
        manager.write_note("Test content", "Initial")
        manager.write_note("Update 1", "Update 1")
        manager.write_note("Update 2", "Update 2")

    mcp = setup_mcp("test")

    assert mcp is not None
    assert mcp.name == "gnote"

    tool_names = set(mcp._tool_manager._tools.keys())
    assert "read_note" in tool_names
    assert "get_note_history" in tool_names


def test_mcp_setup_with_guidance_tool_enabled(
    temp_gnote_home: Path, monkeypatch: MonkeyPatch
) -> None:
    """Test MCP server setup with guidance tool enabled."""
    monkeypatch.setattr(ConfigManager, "GNOTE_HOME", temp_gnote_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gnote_home / "repo")

    with GitNoteManager("test") as manager:
        manager.write_note("Initial content", "Initial")

    mcp = setup_mcp("test", enable_guidance_tool=True)

    assert mcp is not None
    assert mcp.name == "gnote"

    tool_names = set(mcp._tool_manager._tools.keys())
    assert "guidance" in tool_names


def test_mcp_setup_with_guidance_tool_disabled(
    temp_gnote_home: Path, monkeypatch: MonkeyPatch
) -> None:
    """Test MCP server setup with guidance tool disabled (default)."""
    monkeypatch.setattr(ConfigManager, "GNOTE_HOME", temp_gnote_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gnote_home / "repo")

    with GitNoteManager("test") as manager:
        manager.write_note("Initial content", "Initial")

    mcp = setup_mcp("test", enable_guidance_tool=False)

    assert mcp is not None
    assert mcp.name == "gnote"

    tool_names = set(mcp._tool_manager._tools.keys())
    assert "guidance" not in tool_names
