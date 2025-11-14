"""Tests for CLI commands."""

import argparse
from pathlib import Path

from pytest import CaptureFixture, MonkeyPatch

from gnote.cli import (
    cmd_append,
    cmd_branch_create,
    cmd_branch_list,
    cmd_history,
    cmd_read,
    cmd_snapshot,
    cmd_update,
)
from gnote.config_manager import ConfigManager
from gnote.git_manager import GitNoteManager


def test_cli_read(
    temp_gnote_home: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """Test CLI read command."""
    monkeypatch.setattr(ConfigManager, "GNOTE_HOME", temp_gnote_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gnote_home / "repo")

    with GitNoteManager("master") as manager:
        manager.write_note("Test content", "Initial")

    args = argparse.Namespace()
    cmd_read(args)
    captured = capsys.readouterr()
    assert "Test content" in captured.out


def test_cli_update(
    temp_gnote_home: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """Test CLI update command."""
    monkeypatch.setattr(ConfigManager, "GNOTE_HOME", temp_gnote_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gnote_home / "repo")

    with GitNoteManager("master") as manager:
        manager.write_note("Initial", "Initial")

    args = argparse.Namespace(message="Update test", content="Updated content")
    cmd_update(args)
    captured = capsys.readouterr()
    assert "✓ Updated note" in captured.out

    with GitNoteManager("master") as manager:
        content = manager.read_note()
        assert content == "Updated content"


def test_cli_append(
    temp_gnote_home: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """Test CLI append command."""
    monkeypatch.setattr(ConfigManager, "GNOTE_HOME", temp_gnote_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gnote_home / "repo")

    with GitNoteManager("master") as manager:
        manager.write_note("Initial", "Initial")

    args = argparse.Namespace(message="Append test", text="Appended")
    cmd_append(args)
    captured = capsys.readouterr()
    assert "✓ Appended to note" in captured.out

    with GitNoteManager("master") as manager:
        content = manager.read_note()
        assert "Initial" in content
        assert "Appended" in content


def test_cli_history(
    temp_gnote_home: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """Test CLI history command."""
    monkeypatch.setattr(ConfigManager, "GNOTE_HOME", temp_gnote_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gnote_home / "repo")

    with GitNoteManager("master") as manager:
        manager.write_note("Content 1", "Commit 1")
        manager.write_note("Content 2", "Commit 2")
        manager.write_note("Content 3", "Commit 3")

    args = argparse.Namespace(limit=10, starting_after=None)
    cmd_history(args)
    captured = capsys.readouterr()
    assert "Commit 1" in captured.out
    assert "Commit 2" in captured.out
    assert "Commit 3" in captured.out


def test_cli_snapshot(
    temp_gnote_home: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """Test CLI snapshot command."""
    monkeypatch.setattr(ConfigManager, "GNOTE_HOME", temp_gnote_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gnote_home / "repo")

    with GitNoteManager("master") as manager:
        sha = manager.write_note("Snapshot content", "Snapshot commit")
        manager.write_note("Later content", "Later")

    args = argparse.Namespace(sha=sha)
    cmd_snapshot(args)
    captured = capsys.readouterr()
    assert "Snapshot content" in captured.out
    assert "Snapshot commit" in captured.out


def test_cli_branch_list(
    temp_gnote_home: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """Test CLI branch list command."""
    monkeypatch.setattr(ConfigManager, "GNOTE_HOME", temp_gnote_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gnote_home / "repo")

    with GitNoteManager("master") as manager:
        manager.write_note("Initial", "Init")

    with GitNoteManager("test-branch") as manager:
        manager.write_note("Test", "Test")

    args = argparse.Namespace()
    cmd_branch_list(args)
    captured = capsys.readouterr()
    assert "master" in captured.out
    assert "test-branch" in captured.out


def test_cli_branch_create(
    temp_gnote_home: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """Test CLI branch create command."""
    monkeypatch.setattr(ConfigManager, "GNOTE_HOME", temp_gnote_home)
    monkeypatch.setattr(ConfigManager, "REPO_PATH", temp_gnote_home / "repo")

    with GitNoteManager("master") as manager:
        manager.write_note("Initial", "Init")

    args = argparse.Namespace(name="new-branch", from_branch=None)
    cmd_branch_create(args)
    captured = capsys.readouterr()
    assert "✓ Created branch 'new-branch'" in captured.out

    with GitNoteManager("new-branch") as manager:
        content = manager.read_note()
        assert "Initial" in content
