# gctx - Git-based Context Management for LLM Agents

**gctx** is a simplified Git-based context and memory management system for LLM agents using the Model Context Protocol (MCP). It provides tools for reading, updating, and navigating context history with token pressure monitoring.

## Features

- 🔄 **Git-based versioning** - Every context change is a Git commit with full history
- �� **Multi-agent branching** - Different agents work on isolated branches with their own configs
- 📊 **Token pressure monitoring** - Track token usage against configurable limits
- 🔧 **Dual interface** - Both CLI and MCP server for flexible integration
- 📝 **Per-branch logging** - Separate logs for each branch in `~/.gctx/logs/`
- ⚙️ **Simple configuration** - Global defaults with per-branch overrides

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd gctx

# Install with uv
uv sync
uv pip install -e .
```

## Quick Start

```bash
# Initialize gctx
uv run gctx init

# Add some context
echo "Project started" | uv run gctx update "Initial context"

# Read context
uv run gctx read

# Append more information
uv run gctx append "New findings" --text "Found interesting pattern"

# View history
uv run gctx history

# Create a new branch for another agent
uv run gctx branch create agent1
uv run gctx branch checkout agent1
```

## Architecture

### Directory Structure

```
~/.gctx/
├── config.json          # Global default configuration
├── repo/                # Git repository
│   └── context          # Context file (tracked by Git)
├── configs/             # Per-branch configuration overrides
│   ├── master.json
│   └── agent1.json
└── logs/               # Per-branch log files
    ├── master.log
    └── agent1.log
```

### Configuration

Global configuration (`~/.gctx/config.json`):
```json
{
  "token_approach": "chardiv4",
  "token_limit": 8000
}
```

Per-branch overrides (`~/.gctx/configs/<branch>.json`):
```json
{
  "token_limit": 12000
}
```

Branch configs override global settings. The `token_approach` currently supports only `chardiv4` (characters divided by 4).

## CLI Commands

### Initialization
```bash
gctx init                    # Initialize gctx structure
gctx validate                # Validate setup
```

### Configuration
```bash
gctx config                  # Show current branch config
gctx config set <key> <value>  # Set config for current branch
```

Example:
```bash
gctx config set token_limit 12000
```

### Branch Management
```bash
gctx branch                  # Show current branch
gctx branch list             # List all branches
gctx branch create <name> [--from <branch>]  # Create new branch
gctx branch checkout <name>  # Switch to branch
```

### Context Operations
```bash
gctx read                    # Read current context
gctx update <message> [--content <text>]  # Update context
gctx append <message> [--text <text>]     # Append to context
gctx history [--limit N] [--starting-after SHA]  # View history
gctx snapshot <sha>          # View context at specific commit
```

Examples:
```bash
# Update with content flag
gctx update "Compress context" --content "New compressed version"

# Update from stdin
echo "New content" | gctx update "Updated via stdin"

# Append with text flag
gctx append "Add findings" --text "New discovery: pattern X"

# Append from stdin
echo "More info" | gctx append "More information"
```

## MCP Server

Start the MCP server for a specific branch:

```bash
gctx-server --branch master
```

The server exposes the following MCP tools:

### MCP Tools

#### `read_context()`
Read current context with token metrics.

**Returns:**
```json
{
  "content": "...",
  "token_count": 1250,
  "token_limit": 8000,
  "token_pressure_percentage": 0.1563
}
```

#### `update_context(new_context: str, commit_message: str)`
Replace context with new content.

**Returns:**
```json
{
  "success": true,
  "commit_sha": "abc123...",
  "new_token_count": 800,
  "token_delta": -450,
  "token_pressure_percentage": 0.1000
}
```

#### `append_to_context(text: str, commit_message: str)`
Append text to context.

**Returns:** Same structure as `update_context`

#### `get_context_history(limit: int = 10, starting_after: str | None = None)`
Get paginated commit history.

**Returns:**
```json
{
  "commits": [
    {
      "sha": "abc123...",
      "message": "Compress context",
      "timestamp": "2025-11-08T12:00:00"
    }
  ],
  "total_commits": 50,
  "has_more": true
}
```

#### `get_snapshot(commit_sha: str)`
Retrieve context from a specific commit.

**Returns:**
```json
{
  "content": "...",
  "commit_message": "...",
  "timestamp": "2025-11-08T12:00:00"
}
```

## Token Counting

gctx uses a simple `chardiv4` approach: `token_count = len(text) // 4`

Token pressure is calculated as: `token_count / token_limit`

The agent decides when to compress based on the pressure percentage - no automatic warnings.

## Logging

All operations are logged to `~/.gctx/logs/<branch>.log`:

```
2025-11-08 12:00:00 - gctx.master - INFO - Setting up MCP tools for branch: master
2025-11-08 12:00:05 - gctx.master - INFO - Tool called: read_context
2025-11-08 12:00:05 - gctx.master - INFO - Read context: 1250 tokens
```

## Development

### Run linting
```bash
uv run ruff check .
uv run ruff format .
```

### Run type checking
```bash
uv run ruff check --select ANN .
```

## Project Structure

```
gctx/
├── gctx/
│   ├── __init__.py
│   ├── config.py           # Pydantic config model
│   ├── config_manager.py   # Config file operations
│   ├── git_manager.py      # Git operations
│   ├── token_counter.py    # Token counting
│   ├── logger.py           # Per-branch logging
│   ├── tools.py            # MCP tools
│   ├── server.py           # MCP server entry point
│   └── cli.py              # CLI commands
├── pyproject.toml
└── README.md
```

## Design Philosophy

- **Simplicity**: One token approach (chardiv4), clear configuration, minimal dependencies
- **Git-native**: Leverage Git for versioning, branching, and history
- **Agent-friendly**: Let agents decide when to compress based on token metrics
- **Multi-agent**: Isolated branches allow multiple agents to work independently
- **Observable**: Comprehensive logging for debugging and monitoring

## License

MIT
