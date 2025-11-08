"""CLI commands for gctx."""

import argparse
import json
import sys

from gctx.config_manager import ConfigManager
from gctx.git_manager import GitContextManager


def cmd_init(args: argparse.Namespace) -> None:
    """Initialize gctx structure.

    CLI: gctx init
    """
    # Create directory structure
    ConfigManager.GCTX_HOME.mkdir(parents=True, exist_ok=True)
    (ConfigManager.GCTX_HOME / "configs").mkdir(exist_ok=True)
    (ConfigManager.GCTX_HOME / "logs").mkdir(exist_ok=True)

    # Create default global config
    ConfigManager.initialize_default()

    # Initialize git repo with main branch
    try:
        GitContextManager("main")
        print("✓ gctx initialized at ~/.gctx")
        print("  - Repository created at ~/.gctx/repo")
        print("  - Default config created at ~/.gctx/config.json")
        print("  - Main branch ready")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_config_show(args: argparse.Namespace) -> None:
    """Show configuration for current branch.

    CLI: gctx config
    """
    try:
        manager = GitContextManager()
        branch = manager.get_current_branch()

        config = ConfigManager.load_for_branch(branch)

        print(f"# Configuration for branch: {branch}")
        print(config.model_dump_json(indent=2))

    except Exception as e:
        print(f"✗ Failed to load config: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_config_set(args: argparse.Namespace) -> None:
    """Set configuration value for current branch.

    CLI: gctx config set <key> <value>
    """
    try:
        manager = GitContextManager()
        branch = manager.get_current_branch()

        # Get existing branch overrides
        overrides = ConfigManager.get_branch_override(branch)

        # Parse value based on key
        value: str | int
        if args.key == "token_limit":
            try:
                value = int(args.value)
                if value <= 0:
                    raise ValueError("token_limit must be positive")
            except ValueError as e:
                print(f"✗ Invalid value for token_limit: {e}", file=sys.stderr)
                sys.exit(1)
        elif args.key == "token_approach":
            if args.value != "chardiv4":
                print(
                    "✗ Invalid token_approach. Only 'chardiv4' is supported.",
                    file=sys.stderr,
                )
                sys.exit(1)
            value = args.value
        else:
            print(f"✗ Unknown config key: {args.key}", file=sys.stderr)
            print("  Valid keys: token_approach, token_limit")
            sys.exit(1)

        # Update overrides
        overrides[args.key] = value
        ConfigManager.save_branch_override(branch, overrides)

        print(f"✓ Set {args.key}={value} for branch '{branch}'")

    except Exception as e:
        print(f"✗ Failed to set config: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_branch_show(args: argparse.Namespace) -> None:
    """Show current branch.

    CLI: gctx branch
    """
    try:
        manager = GitContextManager()
        print(manager.get_current_branch())
    except Exception as e:
        print(f"✗ Failed to get current branch: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_branch_list(args: argparse.Namespace) -> None:
    """List all branches.

    CLI: gctx branch list
    """
    try:
        manager = GitContextManager()
        branches = manager.list_branches()
        current = manager.get_current_branch()

        for branch in branches:
            marker = "*" if branch == current else " "
            print(f"{marker} {branch}")

    except Exception as e:
        print(f"✗ Failed to list branches: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_branch_create(args: argparse.Namespace) -> None:
    """Create new branch.

    CLI: gctx branch create <name> [--from <branch>]
    """
    try:
        manager = GitContextManager()
        sha = manager.create_branch(args.name, args.from_branch)
        print(f"✓ Created branch '{args.name}' at {sha[:8]}")

    except Exception as e:
        print(f"✗ Failed to create branch: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_branch_checkout(args: argparse.Namespace) -> None:
    """Checkout branch.

    CLI: gctx branch checkout <name>
    """
    try:
        manager = GitContextManager()
        manager.checkout_branch(args.name)
        print(f"✓ Switched to branch '{args.name}'")

    except Exception as e:
        print(f"✗ Failed to checkout branch: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_read(args: argparse.Namespace) -> None:
    """Read current context.

    CLI: gctx read
    """
    try:
        manager = GitContextManager()
        content = manager.read_context()
        print(content)

    except Exception as e:
        print(f"✗ Failed to read context: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_update(args: argparse.Namespace) -> None:
    """Update context with new content.

    CLI: gctx update <message> --content <text>
          gctx update <message>  (reads from stdin)
    """
    try:
        manager = GitContextManager()

        # Get content from --content flag or stdin
        if args.content:
            content = args.content
        else:
            print("Enter new context (Ctrl+D or Ctrl+Z to finish):")
            content = sys.stdin.read()

        sha = manager.write_context(content, args.message)
        print(f"✓ Updated context: {sha[:8]}")

    except Exception as e:
        print(f"✗ Failed to update context: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_append(args: argparse.Namespace) -> None:
    """Append text to context.

    CLI: gctx append <message> --text <text>
          gctx append <message>  (reads from stdin)
    """
    try:
        manager = GitContextManager()

        # Get text from --text flag or stdin
        if args.text:
            text = args.text
        else:
            print("Enter text to append (Ctrl+D or Ctrl+Z to finish):")
            text = sys.stdin.read()

        sha = manager.append_context(text, args.message)
        print(f"✓ Appended to context: {sha[:8]}")

    except Exception as e:
        print(f"✗ Failed to append to context: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_history(args: argparse.Namespace) -> None:
    """Show commit history.

    CLI: gctx history [--limit N] [--starting-after SHA]
    """
    try:
        manager = GitContextManager()
        result = manager.get_history(args.limit, args.starting_after)

        print(f"# History ({len(result['commits'])} of {result['total_commits']} commits)")
        print()

        for commit in result["commits"]:
            sha_short = commit["sha"][:8]
            print(f"{sha_short} - {commit['timestamp']}")
            print(f"  {commit['message']}")
            print()

        if result["has_more"]:
            last_sha = result["commits"][-1]["sha"]
            print(f"# More commits available. Use: --starting-after {last_sha}")

    except Exception as e:
        print(f"✗ Failed to get history: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_snapshot(args: argparse.Namespace) -> None:
    """Show snapshot of context at specific commit.

    CLI: gctx snapshot <sha>
    """
    try:
        manager = GitContextManager()
        snapshot = manager.get_snapshot(args.sha)

        print(f"# Snapshot: {args.sha}")
        print(f"# Message: {snapshot['commit_message']}")
        print(f"# Time: {snapshot['timestamp']}")
        print()
        print(snapshot["content"])

    except Exception as e:
        print(f"✗ Failed to get snapshot: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate gctx setup.

    CLI: gctx validate
    """
    errors = []

    # Check if gctx home exists
    if not ConfigManager.GCTX_HOME.exists():
        errors.append("~/.gctx directory does not exist. Run 'gctx init' first.")
    else:
        print("✓ ~/.gctx directory exists")

        # Check config
        config_path = ConfigManager.GCTX_HOME / "config.json"
        if not config_path.exists():
            errors.append("~/.gctx/config.json does not exist")
        else:
            print("✓ ~/.gctx/config.json exists")
            try:
                with config_path.open() as f:
                    json.load(f)
                print("✓ config.json is valid JSON")
            except json.JSONDecodeError:
                errors.append("~/.gctx/config.json is not valid JSON")

        # Check repo
        if not ConfigManager.REPO_PATH.exists():
            errors.append("~/.gctx/repo does not exist")
        else:
            print("✓ ~/.gctx/repo exists")
            try:
                manager = GitContextManager()
                branch = manager.get_current_branch()
                print(f"✓ Current branch: {branch}")
            except Exception as e:
                errors.append(f"Git repository error: {e}")

        # Check subdirectories
        for subdir in ["configs", "logs"]:
            path = ConfigManager.GCTX_HOME / subdir
            if not path.exists():
                errors.append(f"~/.gctx/{subdir} does not exist")
            else:
                print(f"✓ ~/.gctx/{subdir} exists")

    if errors:
        print("\n✗ Validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("\n✓ All checks passed!")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="gctx - Git-based context management for LLM agents"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # gctx init
    parser_init = subparsers.add_parser("init", help="Initialize gctx")
    parser_init.set_defaults(func=cmd_init)

    # gctx config
    parser_config = subparsers.add_parser("config", help="Manage configuration")
    config_subparsers = parser_config.add_subparsers(dest="config_command")

    # gctx config (show)
    parser_config.set_defaults(func=cmd_config_show)

    # gctx config set
    parser_config_set = config_subparsers.add_parser("set", help="Set config value")
    parser_config_set.add_argument("key", help="Config key (token_approach, token_limit)")
    parser_config_set.add_argument("value", help="Config value")
    parser_config_set.set_defaults(func=cmd_config_set)

    # gctx branch
    parser_branch = subparsers.add_parser("branch", help="Manage branches")
    branch_subparsers = parser_branch.add_subparsers(dest="branch_command")

    # gctx branch (show)
    parser_branch.set_defaults(func=cmd_branch_show)

    # gctx branch list
    parser_branch_list = branch_subparsers.add_parser("list", help="List all branches")
    parser_branch_list.set_defaults(func=cmd_branch_list)

    # gctx branch create
    parser_branch_create = branch_subparsers.add_parser("create", help="Create new branch")
    parser_branch_create.add_argument("name", help="Branch name")
    parser_branch_create.add_argument(
        "--from", dest="from_branch", help="Source branch (default: current)"
    )
    parser_branch_create.set_defaults(func=cmd_branch_create)

    # gctx branch checkout
    parser_branch_checkout = branch_subparsers.add_parser("checkout", help="Checkout branch")
    parser_branch_checkout.add_argument("name", help="Branch name")
    parser_branch_checkout.set_defaults(func=cmd_branch_checkout)

    # gctx read
    parser_read = subparsers.add_parser("read", help="Read current context")
    parser_read.set_defaults(func=cmd_read)

    # gctx update
    parser_update = subparsers.add_parser("update", help="Update context")
    parser_update.add_argument("message", help="Commit message")
    parser_update.add_argument("--content", help="New content (or use stdin)")
    parser_update.set_defaults(func=cmd_update)

    # gctx append
    parser_append = subparsers.add_parser("append", help="Append to context")
    parser_append.add_argument("message", help="Commit message")
    parser_append.add_argument("--text", help="Text to append (or use stdin)")
    parser_append.set_defaults(func=cmd_append)

    # gctx history
    parser_history = subparsers.add_parser("history", help="Show commit history")
    parser_history.add_argument("--limit", type=int, default=10, help="Number of commits")
    parser_history.add_argument("--starting-after", help="Start after this commit SHA")
    parser_history.set_defaults(func=cmd_history)

    # gctx snapshot
    parser_snapshot = subparsers.add_parser("snapshot", help="Show snapshot at commit")
    parser_snapshot.add_argument("sha", help="Commit SHA")
    parser_snapshot.set_defaults(func=cmd_snapshot)

    # gctx validate
    parser_validate = subparsers.add_parser("validate", help="Validate gctx setup")
    parser_validate.set_defaults(func=cmd_validate)

    # Parse and execute
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
