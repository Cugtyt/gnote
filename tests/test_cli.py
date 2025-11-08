"""Tests for CLI commands."""

import argparse
from pathlib import Path

from pytest import CaptureFixture, MonkeyPatch

from gctx.cli import (
    cmd_append,
    cmd_branch_create,
    cmd_branch_list,
    cmd_history,
    cmd_read,
    cmd_snapshot,
    cmd_update,
)
from gctx.config_manager import ConfigManager
from gctx.git_manager import GitContextManager


def test_cli_read(
    temp_gctx_home: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """Test CLI read command."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    with GitContextManager("master") as manager:
        manager.write_context("Test content", "Initial")

    args = argparse.Namespace()
    cmd_read(args)
    captured = capsys.readouterr()
    assert "Test content" in captured.out


def test_cli_update(
    temp_gctx_home: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """Test CLI update command."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    with GitContextManager("master") as manager:
        manager.write_context("Initial", "Initial")

    args = argparse.Namespace(message="Update test", content="Updated content")
    cmd_update(args)
    captured = capsys.readouterr()
    assert "✓ Updated context" in captured.out

    with GitContextManager("master") as manager:
        content = manager.read_context()
        assert content == "Updated content"


def test_cli_append(
    temp_gctx_home: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """Test CLI append command."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    with GitContextManager("master") as manager:
        manager.write_context("Initial", "Initial")

    args = argparse.Namespace(message="Append test", text="Appended")
    cmd_append(args)
    captured = capsys.readouterr()
    assert "✓ Appended to context" in captured.out

    with GitContextManager("master") as manager:
        content = manager.read_context()
        assert "Initial" in content
        assert "Appended" in content


def test_cli_history(
    temp_gctx_home: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """Test CLI history command."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    with GitContextManager("master") as manager:
        manager.write_context("Content 1", "Commit 1")
        manager.write_context("Content 2", "Commit 2")
        manager.write_context("Content 3", "Commit 3")

    args = argparse.Namespace(limit=10, starting_after=None)
    cmd_history(args)
    captured = capsys.readouterr()
    assert "Commit 1" in captured.out
    assert "Commit 2" in captured.out
    assert "Commit 3" in captured.out


def test_cli_snapshot(
    temp_gctx_home: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """Test CLI snapshot command."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    with GitContextManager("master") as manager:
        sha = manager.write_context("Snapshot content", "Snapshot commit")
        manager.write_context("Later content", "Later")

    args = argparse.Namespace(sha=sha)
    cmd_snapshot(args)
    captured = capsys.readouterr()
    assert "Snapshot content" in captured.out
    assert "Snapshot commit" in captured.out


def test_cli_branch_list(
    temp_gctx_home: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """Test CLI branch list command."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    with GitContextManager("master") as manager:
        manager.write_context("Initial", "Init")

    with GitContextManager("test-branch") as manager:
        manager.write_context("Test", "Test")

    args = argparse.Namespace()
    cmd_branch_list(args)
    captured = capsys.readouterr()
    assert "master" in captured.out
    assert "test-branch" in captured.out


def test_cli_branch_create(
    temp_gctx_home: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """Test CLI branch create command."""
    monkeypatch.setattr(ConfigManager, "GCTX_HOME", temp_gctx_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gctx_home / "repo")

    with GitContextManager("master") as manager:
        manager.write_context("Initial", "Init")

    args = argparse.Namespace(name="new-branch", from_branch=None)
    cmd_branch_create(args)
    captured = capsys.readouterr()
    assert "✓ Created branch 'new-branch'" in captured.out

    with GitContextManager("new-branch") as manager:
        content = manager.read_context()
        assert "Initial" in content
