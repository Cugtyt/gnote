"""MCP tools for Git-based context and memory management."""

import asyncio
import logging

from mcp.server.fastmcp import FastMCP

from gctx.config import GctxConfig
from gctx.config_manager import ConfigManager
from gctx.git_manager import GitContextManager, HistoryResult
from gctx.logger import get_logger
from gctx.token_counter import TokenCounter

manager: GitContextManager | None = None
counter: TokenCounter | None = None
config: GctxConfig | None = None
logger: logging.Logger | None = None

mcp: FastMCP = FastMCP("gctx")


def setup_tools(branch: str) -> FastMCP:
    """Initialize tools for a specific branch.

    Args:
        branch: Branch name to operate on

    Returns:
        Configured FastMCP server instance
    """
    global manager, counter, config, logger

    logger = get_logger(branch)
    logger.info(f"Setting up MCP tools for branch: {branch}")

    config = ConfigManager.load_for_branch(branch)
    logger.info(f"Config loaded: {config.model_dump_json()}")

    manager = GitContextManager(branch)

    counter = TokenCounter(config.token_approach)

    logger.info("MCP tools setup complete")
    return mcp


@mcp.tool()
async def read_context() -> dict[str, str | int | float]:
    """Read the current context content and token usage metrics.

    Use this tool to check the current context state and token usage.
    The tool returns the full context content along with token metrics
    including current count, limit, and pressure percentage.

    Returns:
        Dictionary containing:
        - content (str): Current context file content
        - token_count (int): Number of tokens in current context
        - token_limit (int): Configured maximum token limit
        - token_pressure_percentage (float): Percentage of limit used (0.0-1.0)
    """
    if not manager or not counter or not config or not logger:
        raise RuntimeError("Tools not initialized. Call setup_tools() first.")

    logger.info("Tool called: read_context")

    content = await asyncio.to_thread(manager.read_context)
    token_count = counter.count(content)
    pressure = counter.calculate_pressure(token_count, config.token_limit)

    logger.info(f"Read context: {token_count} tokens")

    return {"content": content, **pressure}


@mcp.tool()
async def update_context(
    new_context: str, commit_message: str
) -> dict[str, bool | str | int | float]:
    """Update the context file with new content and commit the change.

    Use this tool when compressing context to reduce token usage, or when updating
    context with new important information. The commit message should describe what
    changed or why the update was made (e.g., "Compress context to reduce token
    usage" or "Add new project requirements").

    After updating, the tool returns metrics showing the new token count and how
    much the token usage changed (delta). Use this to verify that compression was
    effective.

    Args:
        new_context: The new context content to save
        commit_message: Descriptive message for this update (required for Git history)

    Returns:
        Dictionary containing:
        - success (bool): True if update succeeded
        - commit_sha (str): Git commit hash for this change
        - new_token_count (int): Token count after update
        - token_delta (int): Change in token count (negative means reduction)
        - token_pressure_percentage (float): New pressure percentage
    """
    if not manager or not counter or not config or not logger:
        raise RuntimeError("Tools not initialized. Call setup_tools() first.")

    logger.info(f"Tool called: update_context - {commit_message}")

    old_content = await asyncio.to_thread(manager.read_context)
    old_token_count = counter.count(old_content)

    commit_sha = await asyncio.to_thread(manager.write_context, new_context, commit_message)

    new_token_count = counter.count(new_context)
    token_delta = new_token_count - old_token_count

    pressure = counter.calculate_pressure(new_token_count, config.token_limit)

    logger.info(f"Updated context: {new_token_count} tokens (delta: {token_delta})")

    return {
        "success": True,
        "commit_sha": commit_sha,
        "new_token_count": new_token_count,
        "token_delta": token_delta,
        "token_pressure_percentage": pressure["token_pressure_percentage"],
    }


@mcp.tool()
async def append_to_context(text: str, commit_message: str) -> dict[str, bool | str | int | float]:
    """Append text to the end of the context file and commit the change.

    Use this tool to add new information to context without rewriting everything.
    This is efficient for:
    - Adding timeline entries or logs
    - Appending new findings without modifying existing content
    - Building up context incrementally

    The text will be appended to the end of the current context with proper
    line separation. Use update_context() for full rewrites or major restructuring.

    Args:
        text: Text to append to the context
        commit_message: Descriptive message for this append operation

    Returns:
        Dictionary containing:
        - success (bool): True if append succeeded
        - commit_sha (str): Git commit hash for this change
        - new_token_count (int): Token count after append
        - token_delta (int): Number of tokens added
        - token_pressure_percentage (float): New pressure percentage
    """
    if not manager or not counter or not config or not logger:
        raise RuntimeError("Tools not initialized. Call setup_tools() first.")

    logger.info(f"Tool called: append_to_context - {commit_message}")

    old_content = await asyncio.to_thread(manager.read_context)
    old_token_count = counter.count(old_content)

    commit_sha = await asyncio.to_thread(manager.append_context, text, commit_message)

    new_content = await asyncio.to_thread(manager.read_context)
    new_token_count = counter.count(new_content)
    token_delta = new_token_count - old_token_count

    pressure = counter.calculate_pressure(new_token_count, config.token_limit)

    logger.info(f"Appended to context: {new_token_count} tokens (delta: +{token_delta})")

    return {
        "success": True,
        "commit_sha": commit_sha,
        "new_token_count": new_token_count,
        "token_delta": token_delta,
        "token_pressure_percentage": pressure["token_pressure_percentage"],
    }


@mcp.tool()
async def get_context_history(limit: int = 10, starting_after: str | None = None) -> HistoryResult:
    """Retrieve paginated commit history of context changes.

    Use this tool to explore past context states and find relevant historical
    information. The history shows all commits with their messages, timestamps,
    allowing you to identify which past states might be useful to recall.

    Navigation: Use starting_after to get older commits. For example:
    - No starting_after: Get the most recent commits
    - starting_after="abc123": Get commits older than abc123
    - Chain calls using the last SHA from previous results to paginate

    After finding a relevant commit in the history, use get_snapshot() with the
    commit SHA to retrieve the actual context content from that point in time.

    Args:
        limit: Number of commits to retrieve (default: 10)
        starting_after: SHA of commit to start after (get older commits), or None for most recent

    Returns:
        Dictionary containing:
        - commits (list): Array of commit objects with:
            - sha (str): Git commit hash
            - message (str): Commit message
            - timestamp (str): ISO format timestamp
        - total_commits (int): Total number of commits in history
        - has_more (bool): True if more commits exist beyond this page
    """
    if not manager or not logger:
        raise RuntimeError("Tools not initialized. Call setup_tools() first.")

    logger.info(f"Tool called: get_context_history (limit={limit})")

    if limit <= 0:
        raise ValueError("limit must be positive")

    result = await asyncio.to_thread(manager.get_history, limit, starting_after)
    logger.info(f"Retrieved {len(result['commits'])} commits")

    return result


@mcp.tool()
async def get_snapshot(commit_sha: str) -> dict[str, str]:
    """Retrieve the context content from a specific historical commit.

    Use this tool after exploring history to recall specific past context states.
    This allows you to access historical information without modifying the current
    context. The snapshot is read-only and does not change your working context.

    You can use information from historical snapshots to:
    - Recall facts or details that were removed during compression
    - Compare current context with past states
    - Restore important information that was accidentally removed

    To find commit SHAs, use get_context_history() first to browse the commit log.

    Args:
        commit_sha: Git commit SHA hash to retrieve (from get_context_history)

    Returns:
        Dictionary containing:
        - content (str): Context file content at that commit
        - commit_message (str): Commit message for that change
        - timestamp (str): ISO format timestamp when commit was made
    """
    if not manager or not logger:
        raise RuntimeError("Tools not initialized. Call setup_tools() first.")

    logger.info(f"Tool called: get_snapshot (sha={commit_sha[:8]})")

    if not commit_sha or len(commit_sha) < 7:
        raise ValueError("commit_sha must be at least 7 characters")
    if not all(c in "0123456789abcdefABCDEF" for c in commit_sha):
        raise ValueError("commit_sha must be a valid hexadecimal hash")

    result = await asyncio.to_thread(manager.get_snapshot, commit_sha)
    logger.info(f"Retrieved snapshot from {commit_sha[:8]}")

    return result
