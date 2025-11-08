"""Tests for git_manager module."""

from pathlib import Path

from pytest import MonkeyPatch

from gctx.config_manager import ConfigManager
from gctx.git_manager import GitContextManager


def test_git_manager_initialization(temp_gctx_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test GitContextManager initialization."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    with GitContextManager("test") as manager:
        assert manager.branch == "test"
        assert (temp_gctx_home / "repo" / ".git").exists()


def test_git_manager_write_and_read(temp_gctx_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test writing and reading context."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    with GitContextManager("test") as manager:
        content = "Test context content"
        commit_sha = manager.write_context(content, "Test commit")

        assert len(commit_sha) > 0

        read_content = manager.read_context()
        assert read_content == content


def test_git_manager_append(temp_gctx_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test appending to context."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    with GitContextManager("test") as manager:
        initial_content = "Initial content"
        manager.write_context(initial_content, "Initial commit")

        append_text = "Appended text"
        manager.append_context(append_text, "Append commit")

        read_content = manager.read_context()
        expected = "Initial content\nAppended text"
        assert read_content.replace("\r\n", "\n") == expected


def test_git_manager_history(temp_gctx_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test getting commit history."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    with GitContextManager("test") as manager:
        manager.write_context("Content 1", "Commit 1")
        manager.write_context("Content 2", "Commit 2")
        manager.write_context("Content 3", "Commit 3")

        history = manager.get_history(10, None)

        assert len(history.commits) >= 3
        assert history.commits[0].message == "Commit 3"
        assert history.commits[1].message == "Commit 2"
        assert history.commits[2].message == "Commit 1"


def test_git_manager_snapshot(temp_gctx_home: Path, monkeypatch: MonkeyPatch) -> None:
    """Test getting snapshot from commit."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    with GitContextManager("test") as manager:
        content1 = "Content 1"
        sha1 = manager.write_context(content1, "Commit 1")

        manager.write_context("Content 2", "Commit 2")

        snapshot = manager.get_snapshot(sha1)
        assert snapshot.content == content1
        assert snapshot.commit_message == "Commit 1"
