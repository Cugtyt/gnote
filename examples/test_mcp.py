"""Test script for gctx MCP tools.

This script demonstrates how to use the MCP tools programmatically
without running the full MCP server.

Run with: uv run python examples/test_mcp.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import gctx
sys.path.insert(0, str(Path(__file__).parent.parent))

from gctx.tools import setup_tools


async def test_mcp_tools() -> None:
    """Test all MCP tools with a demo workflow."""
    print("=" * 60)
    print("GCTX MCP TOOLS TEST")
    print("=" * 60)
    print()

    # Setup tools for master branch
    print(">>> Setting up MCP tools for branch: master")
    setup_tools("master")
    print("✓ MCP tools initialized")
    print()

    # Import the tools after setup
    from gctx.tools import (
        append_to_context,
        get_context_history,
        get_snapshot,
        read_context,
        update_context,
    )

    # Test 1: Read context
    print("Test 1: Read current context")
    print("-" * 40)
    result = await read_context()
    print(f"Content length: {len(result['content'])} characters")
    print(f"Token count: {result['token_count']}")
    print(f"Token limit: {result['token_limit']}")
    print(f"Token pressure: {result['token_pressure_percentage']:.2%}")
    print()

    # Test 2: Update context
    print("Test 2: Update context with new content")
    print("-" * 40)
    new_content = """# MCP Test Context

## Test Information
This context was created by the MCP test script.

## Features Tested
- read_context
- update_context
- append_to_context
- get_context_history
- get_snapshot

## Timestamp
Testing MCP tools functionality.
"""
    result = await update_context(new_content, "MCP test: Initial context")
    print(f"✓ Update successful: {result['success']}")
    print(f"Commit SHA: {result['commit_sha'][:8]}")
    print(f"New token count: {result['new_token_count']}")
    print(f"Token delta: {result['token_delta']:+d}")
    print(f"Token pressure: {result['token_pressure_percentage']:.2%}")
    print()

    # Test 3: Append to context
    print("Test 3: Append additional information")
    print("-" * 40)
    append_text = """
## Additional Data
- MCP server tested successfully
- All tools functioning correctly
- Token counting working as expected
"""
    result = await append_to_context(append_text, "MCP test: Add status update")
    print(f"✓ Append successful: {result['success']}")
    print(f"Commit SHA: {result['commit_sha'][:8]}")
    print(f"New token count: {result['new_token_count']}")
    print(f"Token delta: {result['token_delta']:+d}")
    print(f"Token pressure: {result['token_pressure_percentage']:.2%}")
    print()

    # Test 4: Read updated context
    print("Test 4: Read updated context")
    print("-" * 40)
    result = await read_context()
    print("Current content:")
    print("-" * 40)
    print(result["content"])
    print("-" * 40)
    print(f"Token count: {result['token_count']}")
    print(f"Token pressure: {result['token_pressure_percentage']:.2%}")
    print()

    # Test 5: Get context history
    print("Test 5: Get context history (last 5 commits)")
    print("-" * 40)
    result = await get_context_history(limit=5)
    print(f"Total commits: {result['total_commits']}")
    print(f"Showing: {len(result['commits'])} commits")
    print(f"Has more: {result['has_more']}")
    print()
    print("Commit history:")
    for commit in result["commits"]:
        sha_short = commit["sha"][:8]
        print(f"  {sha_short} - {commit['timestamp']}")
        print(f"    {commit['message']}")
    print()

    # Test 6: Get snapshot
    print("Test 6: Get snapshot from specific commit")
    print("-" * 40)
    if result["commits"]:
        # Get the first commit (most recent)
        commit_sha = result["commits"][0]["sha"]
        snapshot = await get_snapshot(commit_sha)
        print(f"Snapshot SHA: {commit_sha[:8]}")
        print(f"Commit message: {snapshot['commit_message']}")
        print(f"Timestamp: {snapshot['timestamp']}")
        print()
        print("Snapshot content (first 200 chars):")
        print("-" * 40)
        content = snapshot["content"]
        preview = content[:200] + "..." if len(content) > 200 else content
        print(preview)
        print()

    # Test 7: Test pagination
    print("Test 7: Test history pagination")
    print("-" * 40)
    result_page1 = await get_context_history(limit=2)
    print(f"Page 1: {len(result_page1['commits'])} commits")
    for commit in result_page1["commits"]:
        print(f"  {commit['sha'][:8]} - {commit['message']}")

    if result_page1["has_more"]:
        last_sha = result_page1["commits"][-1]["sha"]
        result_page2 = await get_context_history(limit=2, starting_after=last_sha)
        print(f"Page 2: {len(result_page2['commits'])} commits")
        for commit in result_page2["commits"]:
            print(f"  {commit['sha'][:8]} - {commit['message']}")
    print()

    # Test 8: Simulate compression workflow
    print("Test 8: Simulate token pressure and compression")
    print("-" * 40)

    # Add more content to increase token pressure
    large_text = "\n## Large Data Section\n" + "- Data point\n" * 100
    result = await append_to_context(large_text, "MCP test: Add large data")
    print("After adding data:")
    print(f"  Token count: {result['new_token_count']}")
    print(f"  Token pressure: {result['token_pressure_percentage']:.2%}")

    # Check if we need to compress (example: > 50% pressure)
    if result["token_pressure_percentage"] > 0.5:
        print("  ⚠️  Token pressure > 50%, compression recommended")

        # Simulate compression
        compressed = """# MCP Test Context (Compressed)

## Summary
All MCP tools tested successfully. Context compressed to reduce token usage.

## Test Results
✓ All 5 MCP tools working correctly
✓ Token counting accurate
✓ History and snapshots functional
"""
        result = await update_context(compressed, "MCP test: Compress context")
        print("After compression:")
        print(f"  Token count: {result['new_token_count']}")
        print(f"  Token delta: {result['token_delta']:+d}")
        print(f"  Token pressure: {result['token_pressure_percentage']:.2%}")
        print("  ✓ Compression successful")
    else:
        print("  ✓ Token pressure acceptable, no compression needed")
    print()

    # Summary
    print("=" * 60)
    print("ALL MCP TOOLS TESTS COMPLETED!")
    print("=" * 60)
    print()
    print("Summary:")
    print("  ✓ read_context() - Working")
    print("  ✓ update_context() - Working")
    print("  ✓ append_to_context() - Working")
    print("  ✓ get_context_history() - Working")
    print("  ✓ get_snapshot() - Working")
    print("  ✓ Token pressure monitoring - Working")
    print("  ✓ Compression workflow - Demonstrated")
    print()


def main() -> None:
    """Main entry point."""
    try:
        asyncio.run(test_mcp_tools())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Test failed with error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
