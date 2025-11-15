"""MCP server entry point for gnote."""

import argparse

from gnote.config import GnoteConfig
from gnote.config_manager import ConfigManager
from gnote.logger import BranchLogger
from gnote.mcp import setup_mcp


def main() -> None:
    """Start MCP server for a specific branch.

    CLI: gnote-server --branch <name> [--config-override key=value ...]
    """
    parser = argparse.ArgumentParser(
        description="gnote MCP server - Git-based context management",
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
        "--enable-guidance-tool",
        action="store_true",
        help="Enable the guidance tool for LLM instruction visibility",
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
        logger.info(f"Starting gnote-server on branch: {args.branch}")

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

            config = GnoteConfig(**{**config.model_dump(), **overrides})
            logger.info(f"Config overrides applied: {overrides}")

        logger.info(f"Active config: {config.model_dump_json()}")

        try:
            mcp_server = setup_mcp(
                args.branch,
                config_override=config,
                enable_guidance_tool=args.enable_guidance_tool,
            )
            logger.info("MCP server initialized successfully")
            logger.info("Starting MCP server (press Ctrl+C to stop)")

            mcp_server.run()

        except KeyboardInterrupt:
            logger.info("Received shutdown signal, stopping server...")
        except Exception as e:
            logger.error(f"MCP server crashed: {e}")
            raise
        finally:
            logger.info("gnote-server stopped")
            logger.info("=" * 60)


if __name__ == "__main__":
    main()
