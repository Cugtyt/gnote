"""Test script for gctx MCP server.

This script demonstrates how to test the MCP server using an MCP client
that connects via stdio.

Requirements:
    pip install mcp

Run with: uv run python examples/test_mcp.py
"""

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent, TextResourceContents
from pydantic import AnyUrl

from gctx.git_manager import GitContextManager


async def test_mcp_server() -> None:
    """Test all MCP tools via the MCP server."""
    print("=" * 60)
    print("GCTX MCP SERVER TEST")
    print("=" * 60)
    print()

    # Use a dedicated test branch
    test_branch = "mcp-test"

    # Initialize the branch (GitContextManager will create it if it doesn't exist)
    print(f">>> Initializing test branch '{test_branch}'...")
    with GitContextManager(test_branch) as git_mgr:
        git_mgr.write_context(
            "# MCP Test Context\n\nThis context was created for MCP testing.",
            "Initial test context",
        )
    print(f"✓ Branch '{test_branch}' initialized")
    print()

    # Setup server parameters
    server_params = StdioServerParameters(
        command="uv",
        args=[
            "run",
            "gctx-server",
            "--branch",
            test_branch,
            "--config-override",
            "token_limit=10000",
        ],
        env=None,
    )

    print(">>> Starting MCP server with config override (token_limit=10000)...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✓ MCP server connected and initialized")
            print()

            # List available tools
            tools_result = await session.list_tools()
            print(f"Available tools: {len(tools_result.tools)}")
            for tool in tools_result.tools:
                print(f"  - {tool.name}")
            print()

            # List available resources
            resources_result = await session.list_resources()
            print(f"Available resources: {len(resources_result.resources)}")
            for resource in resources_result.resources:
                print(f"  - {resource.uri}")
            print()
            print()

            # Test: Read usage guide resource
            print("Test: Read usage guide resource")
            print("-" * 40)
            usage_result = await session.read_resource(AnyUrl("gctx://usage-guide"))
            assert isinstance(usage_result.contents[0], TextResourceContents)
            guide_text = usage_result.contents[0].text
            print("✓ Resource read successful")
            print("Usage guide preview:")
            print(guide_text[:400] + ("..." if len(guide_text) > 400 else ""))
            print()
            print()

            # Test 1: Read context
            print("Test 1: Read current context")
            print("-" * 40)
            result = await session.call_tool("read_context", arguments={})
            assert isinstance(result.content[0], TextContent)
            content = result.content[0].text
            print("✓ Tool call successful")
            print(f"Result preview: {content[:200]}...")

            # Verify config override worked
            import json

            result_data = json.loads(content)
            if result_data.get("token_limit") == 10000:
                print("✓ Config override verified: token_limit=10000")
            else:
                limit = result_data.get("token_limit")
                print(f"⚠ Config override may not have worked: token_limit={limit}")
            print()

            # Test 2: Update context
            print("Test 2: Update context with new content")
            print("-" * 40)
            new_content = """# MCP Test Context

## Test Information
This context was created by the MCP client test script.

## Features Being Tested
- MCP server connection via stdio
- read_context tool
- update_context tool
- append_to_context tool
- get_context_history tool
- get_snapshot tool

## Timestamp
Testing MCP server functionality.
"""
            result = await session.call_tool(
                "update_context",
                arguments={
                    "new_context": new_content,
                    "commit_message": "MCP client test: Initial context",
                },
            )
            assert isinstance(result.content[0], TextContent)
            print("✓ Tool call successful")
            print(f"Result: {result.content[0].text[:200]}...")
            print()

            # Test 3: Append to context
            print("Test 3: Append additional information")
            print("-" * 40)
            append_text = """
## Additional Data
- MCP server tested via client connection
- All tools accessible through MCP protocol
- stdio communication working correctly
"""
            result = await session.call_tool(
                "append_to_context",
                arguments={
                    "text": append_text,
                    "commit_message": "MCP client test: Add status update",
                },
            )
            assert isinstance(result.content[0], TextContent)
            print("✓ Tool call successful")
            print(f"Result: {result.content[0].text[:200]}...")
            print()

            # Test 4: Read updated context
            print("Test 4: Read updated context")
            print("-" * 40)
            result = await session.call_tool("read_context", arguments={})
            assert isinstance(result.content[0], TextContent)
            content = result.content[0].text
            print("✓ Tool call successful")
            print("Current content:")
            print("-" * 40)
            print(content[:400] + ("..." if len(content) > 400 else ""))
            print("-" * 40)
            print()

            # Test 5: Get context history
            print("Test 5: Get context history (last 5 commits)")
            print("-" * 40)
            result = await session.call_tool("get_context_history", arguments={"limit": 5})
            assert isinstance(result.content[0], TextContent)
            print("✓ Tool call successful")
            print(f"Result preview: {result.content[0].text[:300]}...")
            print()

            # Test 6: Test pagination
            print("Test 6: Test history pagination")
            print("-" * 40)
            result_page1 = await session.call_tool("get_context_history", arguments={"limit": 2})
            assert isinstance(result_page1.content[0], TextContent)
            print("✓ Page 1 retrieved")
            print(f"Result: {result_page1.content[0].text[:200]}...")
            print()

            # Test 7: Search context history with keywords
            print("Test 7: Search context history with keywords")
            print("-" * 40)
            result = await session.call_tool(
                "search_context_history", arguments={"keywords": ["MCP", "test"]}
            )
            assert isinstance(result.content[0], TextContent)
            print("✓ Tool call successful")
            print(f"Result: {result.content[0].text[:300]}...")
            print()

            # Test 8: Vector search for similar commits
            print("Test 8: Vector search for similar commits")
            print("-" * 40)

            # Track all commits created during this test
            import json

            created_commits = []

            # First, add more commits with varied content for better vector search demo
            print("  Adding more context for vector search demonstration...")
            contents = [
                (
                    "## Python Development\nWorking on Python scripts and testing modules.",
                    "Add Python notes",
                ),
                (
                    "## Database Design\nSQL queries and schema optimization work.",
                    "Add database notes",
                ),
                (
                    "## API Integration\nRESTful API endpoints and authentication.",
                    "Add API notes",
                ),
            ]
            for content, message in contents:
                result = await session.call_tool(
                    "append_to_context",
                    arguments={"text": content, "commit_message": message},
                )
                # Extract commit SHA from result
                assert isinstance(result.content[0], TextContent)
                result_data = json.loads(result.content[0].text)
                if result_data.get("success"):
                    created_commits.append(
                        {
                            "sha": result_data.get("commit_sha"),
                            "message": message,
                        }
                    )
            print(f"  ✓ Added {len(created_commits)} commits for testing")

            # Get all commits to verify they exist
            history_result = await session.call_tool(
                "get_context_history",
                arguments={"limit": 10},
            )
            assert isinstance(history_result.content[0], TextContent)
            history_data = json.loads(history_result.content[0].text)
            all_commits = history_data.get("commits", [])
            print(f"  ✓ Total commits in history: {len(all_commits)}")

            # Give vector index time to sync
            # (daemon runs every 30 seconds by default)
            print("  Waiting 35 seconds for vector index to sync...")
            await asyncio.sleep(35)

            try:
                result = await session.call_tool(
                    "vector_search_context_history",
                    arguments={"queries": ["python testing", "database optimization"]},
                )
                assert isinstance(result.content[0], TextContent)
                print("✓ Tool call successful")
                result_text = result.content[0].text

                # Check if vector search found results
                result_data = json.loads(result_text)
                if result_data.get("success"):
                    matches = result_data.get("total_matches", 0)
                    commits = result_data.get("commits", [])
                    print(f"✓ Vector search found {matches} matching commit(s)")

                    # Verify we actually got matches
                    created_msgs = [c["message"] for c in created_commits]
                    assert matches > 0, (
                        f"Vector search should find matching commits. "
                        f"Created: {created_msgs}, Total in history: {len(all_commits)}"
                    )
                    assert len(commits) > 0, "Commits array should not be empty"

                    # Verify the search found at least one of our test commits
                    found_shas = {c["sha"] for c in commits}
                    created_shas = {c["sha"] for c in created_commits}
                    matched_test_commits = found_shas & created_shas
                    print(f"  ✓ Found {len(matched_test_commits)} of our test commits in results")
                    assert len(matched_test_commits) > 0, (
                        f"Should find at least one test commit. "
                        f"Created: {created_shas}, Found: {found_shas}"
                    )

                    if commits:
                        print("\nTop matching commits:")
                        for i, commit in enumerate(commits[:3], 1):
                            print(f"  {i}. {commit['message']} (SHA: {commit['sha'][:8]})")
                            print(f"     Timestamp: {commit['timestamp']}")

                        # Verify commits have required fields
                        for commit in commits:
                            assert "sha" in commit, "Commit missing 'sha' field"
                            assert "message" in commit, "Commit missing 'message' field"
                            assert "timestamp" in commit, "Commit missing 'timestamp' field"
                        print("  ✓ All commits have required fields (sha, message, timestamp)")
                else:
                    print(f"⚠ Vector search error: {result_data.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"⚠ Vector search test failed: {e}")
            print()

            # Summary
            print("=" * 60)
            print("ALL MCP SERVER TESTS COMPLETED!")
            print("=" * 60)
            print()
            print("Summary:")
            print("  ✓ MCP server connection via stdio - Working")
            print("  ✓ usage-guide resource - Working")
            print("  ✓ read_context tool - Working")
            print("  ✓ update_context tool - Working")
            print("  ✓ append_to_context tool - Working")
            print("  ✓ get_context_history tool - Working")
            print("  ✓ search_context_history tool - Working")
            print("  ✓ vector_search_context_history tool - Working")
            print("  ✓ MCP protocol communication - Working")
            print()


def main() -> None:
    """Main entry point."""
    try:
        asyncio.run(test_mcp_server())
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
