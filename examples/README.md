# Examples Directory

This directory contains test and demonstration scripts for gnote.

## Files

### `test_cli.ps1`
PowerShell script that demonstrates and tests all CLI commands.

**Usage:**
```powershell
pwsh examples/test_cli.ps1
```

**What it tests:**
- Initialization and validation
- Configuration management (global and per-branch)
- Note operations (read, update, append)
- Branch management (create, checkout, list)
- History and snapshots
- Multi-branch isolation

**Output:** Complete walkthrough of CLI functionality with colored output.

### `test_mcp.py`
Python script that tests all MCP tools programmatically.

**Usage:**
```bash
uv run python examples/test_mcp.py
```

**What it tests:**
- `read_note()` - Read current note with metrics
- `update_note()` - Replace note content
- `append_to_note()` - Append to note
- `get_note_history()` - Retrieve commit history with pagination
- `get_snapshot()` - Get historical notes
- Token pressure monitoring workflow
- Compression simulation

**Output:** Detailed test results showing all MCP tools in action.

## Running the Tests

### CLI Test
```powershell
# Run CLI test (PowerShell)
pwsh examples/test_cli.ps1

# The script will:
# 1. Clean up any previous test data
# 2. Initialize gnote
# 3. Run through all CLI commands
# 4. Show results with colored output
```

### MCP Test
```bash
# Run MCP test (Python)
uv run python examples/test_mcp.py

# The script will:
# 1. Setup MCP tools for master branch
# 2. Test all 5 MCP tools
# 3. Demonstrate token pressure workflow
# 4. Show compression example
```

## Test Data

Both scripts use the `~/.gnote` directory for test data.

**To clean up after testing:**
```powershell
# Windows/PowerShell
Remove-Item -Recurse -Force ~/.gnote

# Linux/macOS
rm -rf ~/.gnote
```

## Expected Output

### CLI Test
- Creates test note with multi-line content
- Shows commit history
- Demonstrates branch isolation
- Verifies configuration overrides
- All operations should succeed with ✓ marks

### MCP Test
- Shows token counts and pressure percentages
- Demonstrates pagination in history
- Simulates compression workflow
- All tools should return expected data structures

## Notes

- Both tests are safe to run multiple times
- CLI test automatically cleans up before starting
- MCP test uses the existing `~/.gnote` or creates new
- All test operations are logged to `~/.gnote/logs/master.log`

## Troubleshooting

If tests fail:
1. Ensure gnote is installed: `uv pip install -e .`
2. Check dependencies: `uv sync`
3. Verify setup: `uv run gnote validate`
4. Check logs: `cat ~/.gnote/logs/master.log`
