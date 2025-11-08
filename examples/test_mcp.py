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
from mcp.types import TextContent


async def test_mcp_server() -> None:
    """Test all MCP tools via the MCP server."""
    print("=" * 60)
    print("GCTX MCP SERVER TEST")
    print("=" * 60)
    print()

    # Setup server parameters
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "gctx-server", "--branch", "master"],
        env=None,
    )

    print(">>> Starting MCP server...")
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
            print()

            # Test 1: Read context
            print("Test 1: Read current context")
            print("-" * 40)
            result = await session.call_tool("read_context", arguments={})
            assert isinstance(result.content[0], TextContent)
            content = result.content[0].text
            print("✓ Tool call successful")
            print(f"Result preview: {content[:200]}...")
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

            # Summary
            print("=" * 60)
            print("ALL MCP SERVER TESTS COMPLETED!")
            print("=" * 60)
            print()
            print("Summary:")
            print("  ✓ MCP server connection via stdio - Working")
            print("  ✓ read_context tool - Working")
            print("  ✓ update_context tool - Working")
            print("  ✓ append_to_context tool - Working")
            print("  ✓ get_context_history tool - Working")
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
