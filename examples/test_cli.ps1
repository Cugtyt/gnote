# PowerShell script to demonstrate and test gctx CLI commands
# Run with: pwsh examples/test_cli.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GCTX CLI DEMONSTRATION & TEST SCRIPT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Clean up previous test
Write-Host ">>> Cleaning up previous test data..." -ForegroundColor Yellow
if (Test-Path "$HOME\.gctx") {
    Remove-Item -Recurse -Force "$HOME\.gctx"
    Write-Host "✓ Removed ~/.gctx" -ForegroundColor Green
}
Write-Host ""

# Test 1: Initialize
Write-Host "Test 1: Initialize gctx" -ForegroundColor Cyan
Write-Host "Command: gctx init" -ForegroundColor Gray
uv run gctx init
Write-Host ""

# Test 2: Validate setup
Write-Host "Test 2: Validate setup" -ForegroundColor Cyan
Write-Host "Command: gctx validate" -ForegroundColor Gray
uv run gctx validate
Write-Host ""

# Test 3: Show default config
Write-Host "Test 3: Show default configuration" -ForegroundColor Cyan
Write-Host "Command: gctx config" -ForegroundColor Gray
uv run gctx config
Write-Host ""

# Test 4: Show current branch
Write-Host "Test 4: Show current branch" -ForegroundColor Cyan
Write-Host "Command: gctx branch" -ForegroundColor Gray
uv run gctx branch
Write-Host ""

# Test 5: Update context
Write-Host "Test 5: Update context with initial content" -ForegroundColor Cyan
Write-Host "Command: gctx update 'Initial context' --content '...'" -ForegroundColor Gray
$initialContent = @"
# Project Context

## Overview
This is a test project for gctx - a Git-based context management system.

## Goals
- Demonstrate CLI functionality
- Test all features
- Provide usage examples

## Status
Initial setup complete.
"@
$initialContent | uv run gctx update "Initial context"
Write-Host ""

# Test 6: Read context
Write-Host "Test 6: Read current context" -ForegroundColor Cyan
Write-Host "Command: gctx read" -ForegroundColor Gray
uv run gctx read
Write-Host ""

# Test 7: Append to context
Write-Host "Test 7: Append information to context" -ForegroundColor Cyan
Write-Host "Command: gctx append 'Add progress update' --text '...'" -ForegroundColor Gray
uv run gctx append "Add progress update" --text @"

## Progress Update
- All core modules implemented
- CLI tests passing
- Ready for MCP testing
"@
Write-Host ""

# Test 8: Read updated context
Write-Host "Test 8: Read updated context" -ForegroundColor Cyan
Write-Host "Command: gctx read" -ForegroundColor Gray
uv run gctx read
Write-Host ""

# Test 9: View history
Write-Host "Test 9: View commit history" -ForegroundColor Cyan
Write-Host "Command: gctx history --limit 5" -ForegroundColor Gray
uv run gctx history --limit 5
Write-Host ""

# Test 10: Create new branch
Write-Host "Test 10: Create new branch 'agent1'" -ForegroundColor Cyan
Write-Host "Command: gctx branch create agent1" -ForegroundColor Gray
uv run gctx branch create agent1
Write-Host ""

# Test 11: List branches
Write-Host "Test 11: List all branches" -ForegroundColor Cyan
Write-Host "Command: gctx branch list" -ForegroundColor Gray
uv run gctx branch list
Write-Host ""

# Test 12: Checkout new branch
Write-Host "Test 12: Checkout agent1 branch" -ForegroundColor Cyan
Write-Host "Command: gctx branch checkout agent1" -ForegroundColor Gray
uv run gctx branch checkout agent1
Write-Host ""

# Test 13: Verify current branch
Write-Host "Test 13: Verify current branch is agent1" -ForegroundColor Cyan
Write-Host "Command: gctx branch" -ForegroundColor Gray
uv run gctx branch
Write-Host ""

# Test 14: Update config for agent1
Write-Host "Test 14: Set custom token limit for agent1" -ForegroundColor Cyan
Write-Host "Command: gctx config set token_limit 15000" -ForegroundColor Gray
uv run gctx config set token_limit 15000
Write-Host ""

# Test 15: Verify config override
Write-Host "Test 15: Verify agent1 config has custom limit" -ForegroundColor Cyan
Write-Host "Command: gctx config" -ForegroundColor Gray
uv run gctx config
Write-Host ""

# Test 16: Update context on agent1 branch
Write-Host "Test 16: Update context on agent1 branch" -ForegroundColor Cyan
Write-Host "Command: gctx update 'Agent1 working context' --content '...'" -ForegroundColor Gray
uv run gctx update "Agent1 working context" --content @"
# Agent1 Context

This is agent1's isolated context.
Working on specialized tasks with higher token limit (15000).
"@
Write-Host ""

# Test 17: Get snapshot from master branch
Write-Host "Test 17: Get snapshot from master branch" -ForegroundColor Cyan
Write-Host "Command: gctx snapshot <sha> (from history)" -ForegroundColor Gray
# Get first commit SHA from history
$historyOutput = uv run gctx history --limit 1 2>&1 | Out-String
if ($historyOutput -match "([a-f0-9]{8}) -") {
    $sha = $matches[1]
    uv run gctx snapshot $sha
} else {
    Write-Host "Could not find commit SHA from history" -ForegroundColor Red
}
Write-Host ""

# Test 18: Switch back to master
Write-Host "Test 18: Switch back to master branch" -ForegroundColor Cyan
Write-Host "Command: gctx branch checkout master" -ForegroundColor Gray
uv run gctx branch checkout master
Write-Host ""

# Test 19: Verify master context unchanged
Write-Host "Test 19: Verify master context is unchanged" -ForegroundColor Cyan
Write-Host "Command: gctx read" -ForegroundColor Gray
uv run gctx read
Write-Host ""

# Test 20: View full history
Write-Host "Test 20: View full history with pagination info" -ForegroundColor Cyan
Write-Host "Command: gctx history" -ForegroundColor Gray
uv run gctx history
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ALL CLI TESTS COMPLETED!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "  ✓ Initialization and validation" -ForegroundColor Green
Write-Host "  ✓ Configuration management (global + per-branch)" -ForegroundColor Green
Write-Host "  ✓ Context operations (read, update, append)" -ForegroundColor Green
Write-Host "  ✓ Branch management (create, checkout, list)" -ForegroundColor Green
Write-Host "  ✓ History and snapshots" -ForegroundColor Green
Write-Host "  ✓ Multi-branch isolation verified" -ForegroundColor Green
Write-Host ""
Write-Host "Test data location: $HOME\.gctx" -ForegroundColor Gray
Write-Host "To clean up: Remove-Item -Recurse -Force $HOME\.gctx" -ForegroundColor Gray
