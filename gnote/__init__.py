"""gnote - Simplified Git-based context management for LLM agents via MCP."""

from gnote.config import GnoteConfig, TokenApproach
from gnote.config_manager import ConfigManager
from gnote.git_manager import (
    CommitInfo,
    GitNoteManager,
    History,
    Search,
    Snapshot,
)
from gnote.mcp import (
    AppendNoteResult,
    HistoryResult,
    ReadNoteResult,
    SearchResult,
    SnapshotResult,
    UpdateNoteResult,
    setup_mcp,
)
from gnote.token_counter import TokenCounter

__all__ = [
    "GnoteConfig",
    "TokenApproach",
    "ConfigManager",
    "GitNoteManager",
    "TokenCounter",
    "CommitInfo",
    "History",
    "Snapshot",
    "Search",
    "setup_mcp",
    "ReadNoteResult",
    "UpdateNoteResult",
    "AppendNoteResult",
    "HistoryResult",
    "SnapshotResult",
    "SearchResult",
]
