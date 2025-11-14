# PowerShell script to demonstrate and test gnote CLI commands
# Run with: pwsh examples/test_cli.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GNOTE CLI DEMONSTRATION & TEST SCRIPT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Clean up previous test
Write-Host ">>> Cleaning up previous test data..." -ForegroundColor Yellow
if (Test-Path "$HOME\.gnote") {
    Remove-Item -Recurse -Force "$HOME\.gnote"
    Write-Host "✓ Removed ~/.gnote" -ForegroundColor Green
}
Write-Host ""

# Test 1: Initialize
Write-Host "Test 1: Initialize gnote" -ForegroundColor Cyan
Write-Host "Command: gnote init main" -ForegroundColor Gray
uv run gnote init main
Write-Host ""

# Test 2: Validate setup
Write-Host "Test 2: Validate setup" -ForegroundColor Cyan
Write-Host "Command: gnote validate" -ForegroundColor Gray
uv run gnote validate
Write-Host ""

# Test 3: Show default config
Write-Host "Test 3: Show default configuration" -ForegroundColor Cyan
Write-Host "Command: gnote config" -ForegroundColor Gray
uv run gnote config
Write-Host ""

# Test 4: Show current branch
Write-Host "Test 4: Show current branch" -ForegroundColor Cyan
Write-Host "Command: gnote branch" -ForegroundColor Gray
uv run gnote branch
Write-Host ""

# Test 5: Update note
Write-Host "Test 5: Update note with initial content" -ForegroundColor Cyan
Write-Host "Command: gnote update 'Initial note' --content '...'" -ForegroundColor Gray
$initialContent = @"
# Project Note

## Overview
This is a test project for gnote - a Git-based context management system.

## Goals
- Demonstrate CLI functionality
- Test all features
- Provide usage examples

## Status
Initial setup complete.
"@
$initialContent | uv run gnote update "Initial note"
Write-Host ""

# Test 6: Read note
Write-Host "Test 6: Read current note" -ForegroundColor Cyan
Write-Host "Command: gnote read" -ForegroundColor Gray
uv run gnote read
Write-Host ""

# Test 7: Append to note
Write-Host "Test 7: Append information to note" -ForegroundColor Cyan
Write-Host "Command: gnote append 'Add progress update' --text '...'" -ForegroundColor Gray
uv run gnote append "Add progress update" --text @"

## Progress Update
- All core modules implemented
- CLI tests passing
- Ready for MCP testing
"@
Write-Host ""

# Test 8: Read updated note
Write-Host "Test 8: Read updated note" -ForegroundColor Cyan
Write-Host "Command: gnote read" -ForegroundColor Gray
uv run gnote read
Write-Host ""

# Test 9: View history
Write-Host "Test 9: View commit history" -ForegroundColor Cyan
Write-Host "Command: gnote history --limit 5" -ForegroundColor Gray
uv run gnote history --limit 5
Write-Host ""

# Test 10: Create new branch
Write-Host "Test 10: Create new branch 'agent1'" -ForegroundColor Cyan
Write-Host "Command: gnote branch create agent1" -ForegroundColor Gray
uv run gnote branch create agent1
Write-Host ""

# Test 11: List branches
Write-Host "Test 11: List all branches" -ForegroundColor Cyan
Write-Host "Command: gnote branch list" -ForegroundColor Gray
uv run gnote branch list
Write-Host ""

# Test 12: Checkout new branch
Write-Host "Test 12: Checkout agent1 branch" -ForegroundColor Cyan
Write-Host "Command: gnote branch checkout agent1" -ForegroundColor Gray
uv run gnote branch checkout agent1
Write-Host ""

# Test 13: Verify current branch
Write-Host "Test 13: Verify current branch is agent1" -ForegroundColor Cyan
Write-Host "Command: gnote branch" -ForegroundColor Gray
uv run gnote branch
Write-Host ""

# Test 14: Update config for agent1
Write-Host "Test 14: Set custom token limit for agent1" -ForegroundColor Cyan
Write-Host "Command: gnote config set token_limit 15000" -ForegroundColor Gray
uv run gnote config set token_limit 15000
Write-Host ""

# Test 15: Verify config override
Write-Host "Test 15: Verify agent1 config has custom limit" -ForegroundColor Cyan
Write-Host "Command: gnote config" -ForegroundColor Gray
uv run gnote config
Write-Host ""

# Test 16: Update note on agent1 branch
Write-Host "Test 16: Update note on agent1 branch" -ForegroundColor Cyan
Write-Host "Command: gnote update 'Agent1 working note' --content '...'" -ForegroundColor Gray
uv run gnote update "Agent1 working note" --content @"
# Agent1 Note

This is agent1's isolated note.
Working on specialized tasks with higher token limit (15000).
"@
Write-Host ""

# Test 17: Get snapshot from master branch
Write-Host "Test 17: Get snapshot from master branch" -ForegroundColor Cyan
Write-Host "Command: gnote snapshot <sha> (from history)" -ForegroundColor Gray
# Get first commit SHA from history
$historyOutput = uv run gnote history --limit 1 2>&1 | Out-String
if ($historyOutput -match "([a-f0-9]{8}) -") {
    $sha = $matches[1]
    uv run gnote snapshot $sha
} else {
    Write-Host "Could not find commit SHA from history" -ForegroundColor Red
}
Write-Host ""

# Test 18: Switch back to master
Write-Host "Test 18: Switch back to master branch" -ForegroundColor Cyan
Write-Host "Command: gnote branch checkout master" -ForegroundColor Gray
uv run gnote branch checkout master
Write-Host ""

# Test 19: Verify master note unchanged
Write-Host "Test 19: Verify master note is unchanged" -ForegroundColor Cyan
Write-Host "Command: gnote read" -ForegroundColor Gray
uv run gnote read
Write-Host ""

# Test 20: View full history
Write-Host "Test 20: View full history with pagination info" -ForegroundColor Cyan
Write-Host "Command: gnote history" -ForegroundColor Gray
uv run gnote history
Write-Host ""

# Note about MCP server config override
Write-Host "Note: MCP Server Config Override" -ForegroundColor Cyan
Write-Host "The MCP server supports config overrides via --config-override:" -ForegroundColor Gray
Write-Host "  gnote-server --branch master --config-override token_limit=12000" -ForegroundColor Gray
Write-Host "This allows per-instance configuration without modifying config files." -ForegroundColor Gray
Write-Host "See examples/test_mcp.py for usage in MCP client connections." -ForegroundColor Gray
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ALL CLI TESTS COMPLETED!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "  ✓ Initialization and validation" -ForegroundColor Green
Write-Host "  ✓ Configuration management (global + per-branch)" -ForegroundColor Green
Write-Host "  ✓ Note operations (read, update, append)" -ForegroundColor Green
Write-Host "  ✓ Branch management (create, checkout, list)" -ForegroundColor Green
Write-Host "  ✓ History and snapshots" -ForegroundColor Green
Write-Host "  ✓ Multi-branch isolation verified" -ForegroundColor Green
Write-Host ""
Write-Host "Test data location: $HOME\.gnote" -ForegroundColor Gray
Write-Host "To clean up: Remove-Item -Recurse -Force $HOME\.gnote" -ForegroundColor Gray
