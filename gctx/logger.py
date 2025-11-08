"""Logging utilities for gctx."""

import logging
from pathlib import Path
from typing import Self


class BranchLogger:
    """Logger manager for branch-specific logging with proper cleanup."""

    def __init__(self, branch: str) -> None:
        """Initialize logger for specific branch.

        Args:
            branch: Branch name
        """
        self.branch = branch
        self.logger_name = f"gctx.{branch}"
        self.logger = logging.getLogger(self.logger_name)

        if not self.logger.handlers:
            gctx_home = Path.home() / ".gctx"
            log_path = gctx_home / "logs" / f"{branch}.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)

            self.logger.setLevel(logging.INFO)

            handler = logging.FileHandler(log_path, encoding="utf-8")
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def __enter__(self) -> Self:
        """Context manager entry."""
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit - close all handlers."""
        self.close()

    def close(self) -> None:
        """Close and remove all handlers."""
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

    def info(self, message: str) -> None:
        """Log info message."""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Log warning message."""
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Log error message."""
        self.logger.error(message)

    def debug(self, message: str) -> None:
        """Log debug message."""
        self.logger.debug(message)
