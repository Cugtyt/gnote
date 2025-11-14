"""MCP tools for Git-based context and memory management."""

import asyncio
from dataclasses import dataclass, field

from mcp.server.fastmcp import FastMCP

from gnote.config import GnoteConfig
from gnote.config_manager import ConfigManager
from gnote.git_manager import CommitInfo
from gnote.logger import BranchLogger
from gnote.token_counter import TokenCounter


@dataclass(frozen=True)
class ReadNoteResult:
    """Result from reading note."""

    success: bool
    content: str = ""
    token_count: int = 0
    token_limit: int = 0
    token_pressure_percentage: float = 0.0
    error: str = ""


@dataclass(frozen=True)
class UpdateNoteResult:
    """Result from updating note."""

    success: bool
    commit_sha: str = ""
    new_token_count: int = 0
    token_delta: int = 0
    token_pressure_percentage: float = 0.0
    error: str = ""


@dataclass(frozen=True)
class AppendNoteResult:
    """Result from appending to note."""

    success: bool
    commit_sha: str = ""
    new_token_count: int = 0
    token_delta: int = 0
    token_pressure_percentage: float = 0.0
    error: str = ""


@dataclass(frozen=True)
class HistoryResult:
    """Result from getting history with error handling."""

    success: bool
    commits: list[CommitInfo] = field(default_factory=list)
    total_commits: int = 0
    has_more: bool = False
    error: str = ""


@dataclass(frozen=True)
class SnapshotResult:
    """Result from getting snapshot with error handling."""

    success: bool
    content: str = ""
    commit_message: str = ""
    timestamp: str = ""
    error: str = ""


@dataclass(frozen=True)
class SearchResult:
    """Result from searching history with error handling."""

    success: bool
    commits: list[CommitInfo] = field(default_factory=list)
    total_matches: int = 0
    error: str = ""


def setup_mcp(
    branch: str,
    config_override: GnoteConfig | None = None,
    enable_guidance_tool: bool = False,
) -> FastMCP:
    """Initialize tools for a specific branch.

    Args:
        branch: Branch name to operate on
        config_override: Optional config to override loaded configuration
        enable_guidance_tool: Whether to enable the guidance tool (default: False)

    Returns:
        Configured FastMCP server instance
    """
    with BranchLogger(branch) as logger:
        logger.info(f"Setting up MCP tools for branch: {branch}")

        if config_override:
            config = config_override
            logger.info(f"Using config override: {config.model_dump_json()}")
        else:
            config = ConfigManager.load_for_branch(branch)
            logger.info(f"Config loaded: {config.model_dump_json()}")

        logger.info("MCP tools setup complete")

    counter = TokenCounter(config.token_approach)

    mcp = FastMCP("gnote")

    USAGE_GUIDE = """Follow this guidance to use gnote context management tools effectively.

Actively use these tools to manage note across conversations with the user.
These tools provide Git-based note versioning with token pressure monitoring.
You can actively offload the conversation to gnote-managed note, allowing for better
organization and compression when token limits are approached.

**Core operations:**
- `read_note()` - Restore project knowledge and check token metrics
- `append_to_note(text, message)` - Incrementally add findings, decisions, or progress
- `update_note(new_note, message)` - Compress, restructure, or replace entire note
- `get_note_history(limit, starting_after)` - View past commits with pagination
- `get_snapshot(commit_sha)` - Retrieve content from specific commits
- `search_note_history(keywords, limit)` - Search commits by keywords

**Best practices:**
- Always check `success` field; handle errors via `error` field
- Use descriptive commit messages for easier history navigation and searchability
- Consider compression when `token_pressure_percentage` > 0.8
- Review history before compression to avoid losing important information
"""

    @mcp.resource("gnote://usage-guide")
    async def get_usage_guide() -> str:
        """Usage guide for gnote note management tools."""
        return f"# Context Management with gnote\n\n{USAGE_GUIDE}"

    if enable_guidance_tool:

        @mcp.tool(description=USAGE_GUIDE)
        async def guidance() -> None:
            pass

    @mcp.tool()
    async def read_note() -> ReadNoteResult:
        """Read the current note content and token usage metrics.

        Use this tool to check the current note state and token usage.
        The tool returns the full note content along with token metrics
        including current count, limit, and pressure percentage.

        Returns:
            ReadNoteResult containing:
            - success (bool): True if operation succeeded
            - content (str): Current note file content
            - token_count (int): Number of tokens in current note
            - token_limit (int): Configured maximum token limit
            - token_pressure_percentage (float): Percentage of limit used (0.0-1.0)
            - error (str): Error message if failed
        """
        with BranchLogger(branch) as logger:
            logger.info("Tool called: read_note")

            try:
                with GitNoteManager(branch) as manager:
                    content = await asyncio.to_thread(manager.read_note)
                    token_count = counter.count(content)
                    pressure = counter.calculate_pressure(token_count, config.token_limit)

                    logger.info(f"Read note: {token_count} tokens")

                    return ReadNoteResult(
                        success=True,
                        content=content,
                        token_count=token_count,
                        token_limit=config.token_limit,
                        token_pressure_percentage=pressure["token_pressure_percentage"],
                    )
            except Exception as e:
                logger.error(f"Failed to read note: {e}")
                return ReadNoteResult(
                    success=False,
                    error=str(e),
                )

    @mcp.tool()
    async def update_note(new_note: str, commit_message: str) -> UpdateNoteResult:
        """Update the note file with new content and commit the change.

        Use this tool when compressing note to reduce token usage, or when updating
        note with new important information. The commit message should describe what
        changed or why the update was made (e.g., "Compress note to reduce token
        usage" or "Add new project requirements").

        After updating, the tool returns metrics showing the new token count and how
        much the token usage changed (delta). Use this to verify that compression was
        effective.

        Args:
            new_note: The new note content to save
            commit_message: Descriptive message for this update (required for Git history)

        Returns:
            UpdateNoteResult containing:
            - success (bool): True if update succeeded
            - commit_sha (str): Git commit hash for this change
            - new_token_count (int): Token count after update
            - token_delta (int): Change in token count (negative means reduction)
            - token_pressure_percentage (float): New pressure percentage
            - error (str): Error message if failed
        """
        with BranchLogger(branch) as logger:
            logger.info(f"Tool called: update_note - {commit_message}")

            try:
                with GitNoteManager(branch) as manager:
                    old_content = await asyncio.to_thread(manager.read_note)
                    old_token_count = counter.count(old_content)

                    commit_sha = await asyncio.to_thread(
                        manager.write_note, new_note, commit_message
                    )

                    new_token_count = counter.count(new_note)
                    token_delta = new_token_count - old_token_count

                    pressure = counter.calculate_pressure(new_token_count, config.token_limit)

                    logger.info(f"Updated note: {new_token_count} tokens (delta: {token_delta})")

                    return UpdateNoteResult(
                        success=True,
                        commit_sha=commit_sha,
                        new_token_count=new_token_count,
                        token_delta=token_delta,
                        token_pressure_percentage=pressure["token_pressure_percentage"],
                    )
            except Exception as e:
                logger.error(f"Failed to update note: {e}")
                return UpdateNoteResult(
                    success=False,
                    error=str(e),
                )

    @mcp.tool()
    async def append_to_note(text: str, commit_message: str) -> AppendNoteResult:
        """Append text to the end of the note file and commit the change.

        Use this tool to add new information to note without rewriting everything.
        This is efficient for:
        - Adding timeline entries or logs
        - Appending new findings without modifying existing content
        - Building up note incrementally

        The text will be appended to the end of the current note with proper
        line separation. Use update_note() for full rewrites or major restructuring.

        Args:
            text: Text to append to the note
            commit_message: Descriptive message for this append operation

        Returns:
            AppendNoteResult containing:
            - success (bool): True if append succeeded
            - commit_sha (str): Git commit hash for this change
            - new_token_count (int): Token count after append
            - token_delta (int): Number of tokens added
            - token_pressure_percentage (float): New pressure percentage
            - error (str): Error message if failed
        """
        with BranchLogger(branch) as logger:
            logger.info(f"Tool called: append_to_note - {commit_message}")

            try:
                with GitNoteManager(branch) as manager:
                    old_content = await asyncio.to_thread(manager.read_note)
                    old_token_count = counter.count(old_content)

                    commit_sha = await asyncio.to_thread(manager.append_note, text, commit_message)

                    new_content = await asyncio.to_thread(manager.read_note)
                    new_token_count = counter.count(new_content)
                    token_delta = new_token_count - old_token_count

                    pressure = counter.calculate_pressure(new_token_count, config.token_limit)

                    log_msg = f"Appended to note: {new_token_count} tokens (delta: +{token_delta})"
                    logger.info(log_msg)

                    return AppendNoteResult(
                        success=True,
                        commit_sha=commit_sha,
                        new_token_count=new_token_count,
                        token_delta=token_delta,
                        token_pressure_percentage=pressure["token_pressure_percentage"],
                    )
            except Exception as e:
                logger.error(f"Failed to append to note: {e}")
                return AppendNoteResult(
                    success=False,
                    error=str(e),
                )

    @mcp.tool()
    async def get_note_history(limit: int = 10, starting_after: str | None = None) -> HistoryResult:
        """Retrieve paginated commit history of note changes.

        Use this tool to explore past note states and find relevant historical
        information. The history shows all commits with their messages, timestamps,
        allowing you to identify which past states might be useful to recall.

        Navigation: Use starting_after to get older commits. For example:
        - No starting_after: Get the most recent commits
        - starting_after="abc123": Get commits older than abc123
        - Chain calls using the last SHA from previous results to paginate

        After finding a relevant commit in the history, use get_snapshot() with the
        commit SHA to retrieve the actual note content from that point in time.

        Args:
            limit: Number of commits to retrieve (default: 10)
            starting_after: SHA of commit to start after (get older commits), or None
                for most recent

        Returns:
            HistoryResult containing:
            - success (bool): True if operation succeeded
            - commits (list[CommitInfo]): Array of CommitInfo objects with sha, message, timestamp
            - total_commits (int): Total number of commits in history
            - has_more (bool): True if more commits exist beyond this page
            - error (str): Error message if failed
        """
        with BranchLogger(branch) as logger:
            logger.info(f"Tool called: get_note_history (limit={limit})")

            try:
                if limit <= 0:
                    raise ValueError("limit must be positive")

                with GitNoteManager(branch) as manager:
                    result = await asyncio.to_thread(manager.get_history, limit, starting_after)
                    logger.info(f"Retrieved {len(result.commits)} commits")

                    return HistoryResult(
                        success=True,
                        commits=result.commits,
                        total_commits=result.total_commits,
                        has_more=result.has_more,
                    )
            except Exception as e:
                logger.error(f"Failed to get history: {e}")
                return HistoryResult(
                    success=False,
                    error=str(e),
                )

    @mcp.tool()
    async def get_snapshot(commit_sha: str) -> SnapshotResult:
        """Retrieve the note content from a specific historical commit.

        Use this tool after exploring history to recall specific past note states.
        This allows you to access historical information without modifying the current
        note. The snapshot is read-only and does not change your working note.

        You can use information from historical snapshots to:
        - Recall facts or details that were removed during compression
        - Compare current note with past states
        - Restore important information that was accidentally removed

        To find commit SHAs, use get_note_history() first to browse the commit log.

        Args:
            commit_sha: Git commit SHA hash to retrieve (from get_note_history)

        Returns:
            SnapshotResult containing:
            - success (bool): True if snapshot retrieved successfully
            - content (str): Note file content at that commit
            - commit_message (str): Commit message for that change
            - timestamp (str): ISO format timestamp when commit was made
            - error (str): Error message if success is False
        """
        with BranchLogger(branch) as logger:
            logger.info(f"Tool called: get_snapshot (sha={commit_sha[:8]})")
            try:
                if not commit_sha or len(commit_sha) < 7:
                    raise ValueError("commit_sha must be at least 7 characters")
                if not all(c in "0123456789abcdefABCDEF" for c in commit_sha):
                    raise ValueError("commit_sha must be a valid hexadecimal hash")

                with GitNoteManager(branch) as manager:
                    result = await asyncio.to_thread(manager.get_snapshot, commit_sha)
                    logger.info(f"Retrieved snapshot from {commit_sha[:8]}")

                    return SnapshotResult(
                        success=True,
                        content=result.content,
                        commit_message=result.commit_message,
                        timestamp=result.timestamp,
                    )
            except Exception as e:
                logger.error(f"Failed to get snapshot: {e}")
                return SnapshotResult(
                    success=False,
                    error=str(e),
                )

    @mcp.tool()
    async def search_note_history(keywords: list[str], limit: int = 100) -> SearchResult:
        """Search commit history for keywords in messages or content.

        Searches through commit history and returns commits where any keyword
        matches either the commit message or the note content.

        Args:
            keywords: List of keywords to search for (case-insensitive)
            limit: Maximum number of commits to search (default: 100)

        Returns:
            SearchResult containing:
            - success (bool): True if search succeeded
            - commits (list[CommitInfo]): Matching commits with sha, message, timestamp
            - total_matches (int): Number of matching commits found
            - error (str): Error message if failed
        """
        with BranchLogger(branch) as logger:
            logger.info(f"Tool called: search_note_history (keywords={keywords}, limit={limit})")
            try:
                with GitNoteManager(branch) as manager:
                    result = await asyncio.to_thread(manager.search_history, keywords, limit)
                    logger.info(f"Found {result.total_matches} matches")

                    return SearchResult(
                        success=True,
                        commits=result.commits,
                        total_matches=result.total_matches,
                    )
            except Exception as e:
                logger.error(f"Failed to search history: {e}")
                return SearchResult(
                    success=False,
                    error=str(e),
                )

    return mcp
