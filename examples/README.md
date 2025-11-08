# Examples Directory

This directory contains test and demonstration scripts for gctx.

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
- Context operations (read, update, append)
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
- `read_context()` - Read current context with metrics
- `update_context()` - Replace context content
- `append_to_context()` - Append to context
- `get_context_history()` - Retrieve commit history with pagination
- `get_snapshot()` - Get historical context
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
# 2. Initialize gctx
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

Both scripts use the `~/.gctx` directory for test data.

**To clean up after testing:**
```powershell
# Windows/PowerShell
Remove-Item -Recurse -Force ~/.gctx

# Linux/macOS
rm -rf ~/.gctx
```

## Expected Output

### CLI Test
- Creates test context with multi-line content
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
- MCP test uses the existing `~/.gctx` or creates new
- All test operations are logged to `~/.gctx/logs/master.log`

## Troubleshooting

If tests fail:
1. Ensure gctx is installed: `uv pip install -e .`
2. Check dependencies: `uv sync`
3. Verify setup: `uv run gctx validate`
4. Check logs: `cat ~/.gctx/logs/master.log`
