"""Logging utilities for gctx."""

import logging
from pathlib import Path


def get_logger(branch: str) -> logging.Logger:
    """Get or create logger for specific branch.

    Logs to ~/.gctx/logs/{branch}.log

    Args:
        branch: Branch name

    Returns:
        Configured logger instance
    """
    gctx_home = Path.home() / ".gctx"
    log_path = gctx_home / "logs" / f"{branch}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger_name = f"gctx.{branch}"
    logger = logging.getLogger(logger_name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.FileHandler(log_path, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
