# gnote - Git-based Context Management for LLM Agents

**gnote** is a simplified Git-based context and memory management system for LLM agents using the Model Context Protocol (MCP). It provides tools for reading, updating, and navigating note history with token pressure monitoring.

## Features

- 🔄 **Git-based versioning** - Every note change is a Git commit with full history
- 🌿 **Multi-agent branching** - Different agents work on isolated branches with their own configs
- 📊 **Token pressure monitoring** - Track token usage against configurable limits
- 🔧 **Dual interface** - Both CLI and MCP server for flexible integration
- 📝 **Per-branch logging** - Separate logs for each branch in `~/.gnote/logs/`
- ⚙️ **Simple configuration** - Global defaults with per-branch overrides

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd gnote

# Install with uv
uv sync
uv pip install -e .
```

## Quick Start

```bash
# Initialize gnote with a branch name
uv run gnote init main

# Add some note
echo "Project started" | uv run gnote update "Initial note"

# Read note
uv run gnote read

# Append more information
uv run gnote append "New findings" --text "Found interesting pattern"

# View history
uv run gnote history

# Create a new branch for another agent
uv run gnote branch create agent1
uv run gnote branch checkout agent1
```

## Examples & Testing

We provide comprehensive test scripts to help you understand and verify gnote functionality:

### Test MCP Tools
```bash
# Run MCP tools test (Python)
uv run python examples/test_mcp.py
```

This script demonstrates all 5 MCP tools with a complete workflow including token pressure monitoring and compression simulation.

### Test CLI Commands
```bash
# Run CLI test (PowerShell)
pwsh examples/test_cli.ps1
```

This script walks through all 20 CLI commands with colored output showing initialization, configuration, note operations, branch management, and multi-branch isolation.

See [`examples/README.md`](examples/README.md) for detailed documentation.

## Architecture

### Directory Structure

```
~/.gnote/
├── global.config.json   # Global default configuration
├── repo/                # Git repository
│   └── note          # Note file (tracked by Git)
├── configs/             # Per-branch configuration overrides
│   ├── master.json
│   └── agent1.json
└── logs/               # Per-branch log files
    ├── master.log
    └── agent1.log
```

### Configuration

Global configuration (`~/.gnote/global.config.json`):
```json
{
  "token_approach": "chardiv4",
  "token_limit": 8000
}
```

Per-branch overrides (`~/.gnote/configs/<branch>.json`):
```json
{
  "token_limit": 12000
}
```

Branch configs override global settings. The `token_approach` currently supports only `chardiv4` (characters divided by 4).

## CLI Commands

### Initialization
```bash
gnote init <branch>           # Initialize gnote structure with initial branch
gnote validate                # Validate setup
```

### Configuration
```bash
gnote config                  # Show current branch config
gnote config set <key> <value>  # Set config for current branch
```

Example:
```bash
gnote config set token_limit 12000
```

### Branch Management
```bash
gnote branch                  # Show current branch
gnote branch list             # List all branches
gnote branch create <name> [--from <branch>]  # Create new branch
gnote branch checkout <name>  # Switch to branch
```

### Note Operations
```bash
gnote read                    # Read current note
gnote update <message> [--content <text>]  # Update note
gnote append <message> [--text <text>]     # Append to note
gnote history [--limit N] [--starting-after SHA]  # View history
gnote snapshot <sha>          # View note at specific commit
gnote search <keyword...> [--limit N]      # Search history by keywords
```

Examples:
```bash
# Update with content flag
gnote update "Compress note" --content "New compressed version"

# Update from stdin
echo "New content" | gnote update "Updated via stdin"

# Append with text flag
gnote append "Add findings" --text "New discovery: pattern X"

# Append from stdin
echo "More info" | gnote append "More information"
```

## MCP Server

Start the MCP server for a specific branch:

```bash
gnote-server --branch master
```

**Override configuration:**
```bash
# Override token limit for this server instance
gnote-server --branch master --token-limit 12000
## MCP Server

Start the MCP server for a specific branch:

```bash
gnote-server --branch master
```

**Override configuration:**
```bash
gnote-server --branch master --config-override token_limit=12000
gnote-server --branch master --config-override token_limit=12000 token_approach=chardiv4
```

The `--config-override` flag accepts `key=value` pairs to override any configuration without modifying config files.

### VS Code Integration

To use gnote as an MCP server in VS Code with GitHub Copilot, configure it in your workspace's `.vscode/mcp.json`:

**Basic configuration:**
```json
{
  "servers": {
    "gnote-server": {
      "type": "stdio",
      "command": "path/to/python.exe",
      "args": ["-m", "gnote.server", "--branch", "vscode"]
    }
  },
  "inputs": []
}
```

**With config overrides:**
```json
{
  "servers": {
    "gnote-server": {
      "type": "stdio",
      "command": "path/to/python.exe",
      "args": [
        "-m", "gnote.server",
        "--branch", "vscode",
        "--config-override", "token_limit=12000"
      ]
    }
  },
  "inputs": []
}
```

**Setup steps:**

1. **Create the MCP configuration file:**
   ```bash
   # In your project root
   mkdir -p .vscode
   # Create .vscode/mcp.json with the content above
   ```

2. **Update the Python path:**
   - If using a virtual environment: `path/to/your/.venv/Scripts/python.exe` (Windows) or `path/to/your/.venv/bin/python` (Linux/Mac)
   - If using system Python: Use the full path to your Python executable
   - Example for this project: `C:\\MyProjects\\gnote\\.venv\\Scripts\\python.exe`

3. **Choose your branch:**
   - Change `--branch vscode` to use a different branch
   - Each branch has isolated note and configuration

4. **Optional config overrides:**
   - Add `--config-override` with `key=value` pairs to customize settings
   - Available keys: `token_limit`, `token_approach`

5. **Restart VS Code** to load the MCP server

Once configured, GitHub Copilot will have access to these tools:
- `mcp_gnote-server_read_note` - Read current note
- `mcp_gnote-server_update_note` - Replace note
- `mcp_gnote-server_append_to_note` - Append to note
- `mcp_gnote-server_get_note_history` - View history
- `mcp_gnote-server_get_snapshot` - Get historical note
- `mcp_gnote-server_search_note_history` - Search history by keywords

And this resource:
- `gnote://usage-guide` - Usage guide for gnote tools

**Tip:** Use different branches for different projects or coding sessions to keep note isolated.

The server exposes the following MCP tools and resources:

### MCP Resource

#### `gnote://usage-guide`
Provides comprehensive usage guidelines for gnote context management tools. MCP clients can read this resource to understand how to effectively use gnote for note management across sessions.

### MCP Tools

#### `read_note()`
Read current note with token metrics.

**Returns:**
```json
{
  "success": true,
  "content": "...",
  "token_count": 1250,
  "token_limit": 8000,
  "token_pressure_percentage": 0.1563,
  "error": ""
}
```

#### `update_note(new_note: str, commit_message: str)`
Replace note with new content.

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

#### `append_to_note(text: str, commit_message: str)`
Append text to note.

**Returns:**
```json
{
  "success": true,
  "commit_sha": "def456...",
  "new_token_count": 1650,
  "token_delta": 400,
  "token_pressure_percentage": 0.2063,
  "error": ""
}
```

#### `get_note_history(limit: int = 10, starting_after: str | None = None)`
Get paginated commit history.

**Returns:**
```json
{
  "success": true,
  "commits": [
    {
      "sha": "abc123...",
      "message": "Compress note",
      "timestamp": "2025-11-08T12:00:00"
    }
  ],
  "total_commits": 50,
  "has_more": true,
  "error": ""
}
```

#### `get_snapshot(commit_sha: str)`
Retrieve note from a specific commit.

**Returns:**
```json
{
  "success": true,
  "content": "...",
  "commit_message": "...",
  "timestamp": "2025-11-08T12:00:00",
  "error": ""
}
```

#### `search_note_history(keywords: list[str], limit: int = 100)`
Search commit history for keywords in messages or content.

**Returns:**
```json
{
  "success": true,
  "commits": [
    {
      "sha": "abc123...",
      "message": "Add python implementation",
      "timestamp": "2025-11-08T12:00:00"
    }
  ],
  "total_matches": 5,
  "error": ""
}
```

## Token Counting

gnote uses a simple `chardiv4` approach: `token_count = len(text) // 4`

Token pressure is calculated as: `token_count / token_limit`

The agent decides when to compress based on the pressure percentage - no automatic warnings.

## Logging

All operations are logged to `~/.gnote/logs/<branch>.log`:

```
2025-11-08 12:00:00 - gnote.master - INFO - Setting up MCP tools for branch: master
2025-11-08 12:00:05 - gnote.master - INFO - Tool called: read_note
2025-11-08 12:00:05 - gnote.master - INFO - Read note: 1250 tokens
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
gnote/
├── gnote/
│   ├── __init__.py
│   ├── config.py           # Pydantic config model
│   ├── config_manager.py   # Config file operations
│   ├── git_manager.py      # Git operations
│   ├── token_counter.py    # Token counting
│   ├── logger.py           # Per-branch logging
│   ├── mcp.py              # MCP tools
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
