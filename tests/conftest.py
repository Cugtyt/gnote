"""Pytest configuration and fixtures."""

import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from pytest import MonkeyPatch


@pytest.fixture
def temp_gctx_home(monkeypatch: MonkeyPatch) -> Generator[Path]:
    """Create a temporary .gctx directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        gctx_home = Path(tmpdir) / ".gctx"
        gctx_home.mkdir()
        monkeypatch.setenv("HOME", tmpdir)
        monkeypatch.setenv("USERPROFILE", tmpdir)
        yield gctx_home
        if gctx_home.exists():
            shutil.rmtree(gctx_home, ignore_errors=True)
