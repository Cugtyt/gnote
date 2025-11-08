"""MCP server entry point for gctx."""

import argparse

from gctx.config import GctxConfig
from gctx.config_manager import ConfigManager
from gctx.logger import BranchLogger
from gctx.mcp import setup_mcp


def main() -> None:
    """Start MCP server for a specific branch.

    CLI: gctx-server --branch <name> [--config-override key=value ...]
    """
    parser = argparse.ArgumentParser(
        description="gctx MCP server - Git-based context management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Config Override Examples:
  --config-override token_limit=12000
  --config-override token_approach=chardiv4 token_limit=10000
        """,
    )
    parser.add_argument(
        "--branch",
        required=True,
        help="Branch name to operate on",
    )
    parser.add_argument(
        "--config-override",
        nargs="+",
        metavar="KEY=VALUE",
        help="Override config values (e.g., token_limit=12000)",
    )
    args = parser.parse_args()

    with BranchLogger(args.branch) as logger:
        logger.info("=" * 60)
        logger.info(f"Starting gctx-server on branch: {args.branch}")

        config = ConfigManager.load_for_branch(args.branch)

        if args.config_override:
            overrides = {}
            for override in args.config_override:
                if "=" not in override:
                    logger.error(f"Invalid override format: {override} (expected key=value)")
                    raise ValueError(f"Invalid override format: {override}")
                key, value = override.split("=", 1)
                key = key.strip()
                value = value.strip()

                if key == "token_limit":
                    overrides[key] = int(value)
                elif key == "token_approach":
                    overrides[key] = value
                else:
                    logger.warning(f"Unknown config key: {key}")
                    continue

            config = GctxConfig(**{**config.model_dump(), **overrides})
            logger.info(f"Config overrides applied: {overrides}")

        logger.info(f"Active config: {config.model_dump_json()}")

        try:
            mcp_server = setup_mcp(args.branch, config_override=config)
            logger.info("MCP server initialized successfully")

            mcp_server.run()

        except Exception as e:
            logger.error(f"Server failed to start: {e}")
            raise


if __name__ == "__main__":
    main()
