"""MCP server entry point for gctx."""

import argparse

from gctx.logger import get_logger
from gctx.tools import setup_tools


def main() -> None:
    """Start MCP server for a specific branch.

    CLI: gctx-server --branch <name>
    """
    parser = argparse.ArgumentParser(description="gctx MCP server - Git-based context management")
    parser.add_argument(
        "--branch",
        required=True,
        help="Branch name to operate on",
    )
    args = parser.parse_args()

    logger = get_logger(args.branch)
    logger.info("=" * 60)
    logger.info(f"Starting gctx-server on branch: {args.branch}")

    try:
        mcp_server = setup_tools(args.branch)
        logger.info("MCP server initialized successfully")

        mcp_server.run()

    except Exception as e:
        logger.error(f"Server failed to start: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
