"""CLI commands for gctx."""

import argparse
import json
import sys

from pydantic import ValidationError

from gctx.config import GctxConfig
from gctx.config_manager import ConfigManager
from gctx.git_manager import GitContextManager


def cmd_init(args: argparse.Namespace) -> None:
    """Initialize gctx structure.

    CLI: gctx init <branch>
    """
    branch: str = args.branch

    ConfigManager.GCTX_HOME.mkdir(parents=True, exist_ok=True)
    (ConfigManager.GCTX_HOME / "configs").mkdir(exist_ok=True)
    (ConfigManager.GCTX_HOME / "logs").mkdir(exist_ok=True)
    (ConfigManager.GCTX_HOME / "vectors").mkdir(exist_ok=True)

    ConfigManager.initialize_default()

    try:
        GitContextManager(branch)
        GitContextManager.checkout_branch(branch)
        print("✓ gctx initialized at ~/.gctx")
        print("  - Repository created at ~/.gctx/repo")
        print(f"  - Default config created at ~/.gctx/{ConfigManager.GLOBAL_CONFIG_FILE}")
        print(f"  - Active branch: {branch}")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_config_show(args: argparse.Namespace) -> None:
    """Show configuration for current branch.

    CLI: gctx config
    """
    try:
        branch = GitContextManager.get_active_branch()
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
        key: str = args.key
        raw_value: str = args.value

        branch = GitContextManager.get_active_branch()
        current_config = ConfigManager.load_for_branch(branch)
        overrides = ConfigManager.get_branch_override(branch)

        if key not in GctxConfig.model_fields:
            valid_keys = ", ".join(GctxConfig.model_fields.keys())
            print(f"✗ Unknown config key: {key}", file=sys.stderr)
            print(f"  Valid keys: {valid_keys}", file=sys.stderr)
            sys.exit(1)

        field_info = GctxConfig.model_fields[key]
        parsed_value: str | int

        try:
            if field_info.annotation is int:
                parsed_value = int(raw_value)
            else:
                parsed_value = raw_value

            test_config_data = current_config.model_dump()
            test_config_data[key] = parsed_value
            GctxConfig(**test_config_data)

        except ValidationError as e:
            errors = e.errors()
            for error in errors:
                if key in str(error["loc"]):
                    print(f"✗ Invalid value for {key}: {error['msg']}", file=sys.stderr)
                    sys.exit(1)
            raise
        except ValueError as e:
            print(f"✗ Invalid value for {key}: {e}", file=sys.stderr)
            sys.exit(1)

        overrides[key] = parsed_value
        ConfigManager.save_branch_override(branch, overrides)
        print(f"✓ Set {key}={parsed_value} for branch '{branch}'")

    except Exception as e:
        print(f"✗ Failed to set config: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_branch_show(args: argparse.Namespace) -> None:
    """Show current branch.

    CLI: gctx branch
    """
    try:
        branch = GitContextManager.get_active_branch()
        print(branch)
    except Exception as e:
        print(f"✗ Failed to get current branch: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_branch_list(args: argparse.Namespace) -> None:
    """List all branches.

    CLI: gctx branch list
    """
    try:
        current = GitContextManager.get_active_branch()
        branches = GitContextManager.list_branches()

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
        name: str = args.name
        from_branch: str | None = args.from_branch

        current = GitContextManager.get_active_branch()
        with GitContextManager(current) as manager:
            sha = manager.create_branch(name, from_branch)
            print(f"✓ Created branch '{name}' at {sha[:8]}")

    except Exception as e:
        print(f"✗ Failed to create branch: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_branch_checkout(args: argparse.Namespace) -> None:
    """Checkout branch.

    CLI: gctx branch checkout <name>
    """
    try:
        name: str = args.name

        GitContextManager.checkout_branch(name)
        print(f"✓ Switched to branch '{name}'")

    except Exception as e:
        print(f"✗ Failed to checkout branch: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_read(args: argparse.Namespace) -> None:
    """Read current context.

    CLI: gctx read
    """
    try:
        branch = GitContextManager.get_active_branch()
        with GitContextManager(branch) as manager:
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
        message: str = args.message
        content_arg: str | None = args.content

        branch = GitContextManager.get_active_branch()
        with GitContextManager(branch) as manager:
            if content_arg:
                content = content_arg
            else:
                print("Enter new context (Ctrl+D or Ctrl+Z to finish):")
                content = sys.stdin.read()

            sha = manager.write_context(content, message)
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
        message: str = args.message
        text_arg: str | None = args.text

        branch = GitContextManager.get_active_branch()
        with GitContextManager(branch) as manager:
            if text_arg:
                text = text_arg
            else:
                print("Enter text to append (Ctrl+D or Ctrl+Z to finish):")
                text = sys.stdin.read()

            sha = manager.append_context(text, message)
            print(f"✓ Appended to context: {sha[:8]}")

    except Exception as e:
        print(f"✗ Failed to append to context: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_history(args: argparse.Namespace) -> None:
    """Show commit history.

    CLI: gctx history [--limit N] [--starting-after SHA]
    """
    try:
        limit: int = args.limit
        starting_after: str | None = args.starting_after

        branch = GitContextManager.get_active_branch()
        with GitContextManager(branch) as manager:
            result = manager.get_history(limit, starting_after)

            print(f"# History ({len(result.commits)} of {result.total_commits} commits)")
            print()

            for commit in result.commits:
                sha_short = commit.sha[:8]
                print(f"{sha_short} - {commit.timestamp}")
                print(f"  {commit.message}")
                print()

            if result.has_more:
                last_sha = result.commits[-1].sha
                print(f"# More commits available. Use: --starting-after {last_sha}")

    except Exception as e:
        print(f"✗ Failed to get history: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_snapshot(args: argparse.Namespace) -> None:
    """Show snapshot of context at specific commit.

    CLI: gctx snapshot <sha>
    """
    try:
        sha: str = args.sha

        branch = GitContextManager.get_active_branch()
        with GitContextManager(branch) as manager:
            snapshot = manager.get_snapshot(sha)

            print(f"# Snapshot: {sha}")
            print(f"# Message: {snapshot.commit_message}")
            print(f"# Time: {snapshot.timestamp}")
            print()
            print(snapshot.content)

    except Exception as e:
        print(f"✗ Failed to get snapshot: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_search(args: argparse.Namespace) -> None:
    """Search commit history by keywords.

    CLI: gctx search <keyword> [keyword...] [--limit N]
    """
    try:
        keywords: list[str] = args.keywords
        limit: int = args.limit

        branch = GitContextManager.get_active_branch()
        with GitContextManager(branch) as manager:
            result = manager.search_history(keywords, limit)

            print(f"# Searched {limit} commits for: {', '.join(keywords)}")
            print(f"# Found {result.total_matches} matches")
            print()

            for commit in result.commits:
                sha_short = commit.sha[:8]
                print(f"{sha_short} - {commit.timestamp}")
                print(f"  {commit.message}")
                print()

    except Exception as e:
        print(f"✗ Failed to search history: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate gctx setup.

    CLI: gctx validate
    """
    errors = []

    if not ConfigManager.GCTX_HOME.exists():
        errors.append("~/.gctx directory does not exist. Run 'gctx init' first.")
    else:
        print("✓ ~/.gctx directory exists")

        config_path = ConfigManager.GCTX_HOME / ConfigManager.GLOBAL_CONFIG_FILE
        if not config_path.exists():
            errors.append(f"~/.gctx/{ConfigManager.GLOBAL_CONFIG_FILE} does not exist")
        else:
            print(f"✓ ~/.gctx/{ConfigManager.GLOBAL_CONFIG_FILE} exists")
            try:
                with config_path.open() as f:
                    json.load(f)
                print(f"✓ {ConfigManager.GLOBAL_CONFIG_FILE} is valid JSON")
            except json.JSONDecodeError:
                errors.append(f"~/.gctx/{ConfigManager.GLOBAL_CONFIG_FILE} is not valid JSON")

        if not ConfigManager.REPO_PATH.exists():
            errors.append("~/.gctx/repo does not exist")
        else:
            print("✓ ~/.gctx/repo exists")
            try:
                branch = GitContextManager.get_active_branch()
                print(f"✓ Current branch: {branch}")
            except Exception as e:
                errors.append(f"Git repository error: {e}")

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

    parser_init = subparsers.add_parser("init", help="Initialize gctx")
    parser_init.add_argument("branch", help="Initial branch name")
    parser_init.set_defaults(func=cmd_init)

    parser_config = subparsers.add_parser("config", help="Manage configuration")
    config_subparsers = parser_config.add_subparsers(dest="config_command")

    parser_config.set_defaults(func=cmd_config_show)

    parser_config_set = config_subparsers.add_parser("set", help="Set config value")
    parser_config_set.add_argument("key", help="Config key (token_approach, token_limit)")
    parser_config_set.add_argument("value", help="Config value")
    parser_config_set.set_defaults(func=cmd_config_set)

    parser_branch = subparsers.add_parser("branch", help="Manage branches")
    branch_subparsers = parser_branch.add_subparsers(dest="branch_command")

    parser_branch.set_defaults(func=cmd_branch_show)

    parser_branch_list = branch_subparsers.add_parser("list", help="List all branches")
    parser_branch_list.set_defaults(func=cmd_branch_list)

    parser_branch_create = branch_subparsers.add_parser("create", help="Create new branch")
    parser_branch_create.add_argument("name", help="Branch name")
    parser_branch_create.add_argument(
        "--from", dest="from_branch", help="Source branch (default: current)"
    )
    parser_branch_create.set_defaults(func=cmd_branch_create)

    parser_branch_checkout = branch_subparsers.add_parser("checkout", help="Checkout branch")
    parser_branch_checkout.add_argument("name", help="Branch name")
    parser_branch_checkout.set_defaults(func=cmd_branch_checkout)

    parser_read = subparsers.add_parser("read", help="Read current context")
    parser_read.set_defaults(func=cmd_read)

    parser_update = subparsers.add_parser("update", help="Update context")
    parser_update.add_argument("message", help="Commit message")
    parser_update.add_argument("--content", help="New content (or use stdin)")
    parser_update.set_defaults(func=cmd_update)

    parser_append = subparsers.add_parser("append", help="Append to context")
    parser_append.add_argument("message", help="Commit message")
    parser_append.add_argument("--text", help="Text to append (or use stdin)")
    parser_append.set_defaults(func=cmd_append)

    parser_history = subparsers.add_parser("history", help="Show commit history")
    parser_history.add_argument("--limit", type=int, default=10, help="Number of commits")
    parser_history.add_argument("--starting-after", help="Start after this commit SHA")
    parser_history.set_defaults(func=cmd_history)

    parser_snapshot = subparsers.add_parser("snapshot", help="Show snapshot at commit")
    parser_snapshot.add_argument("sha", help="Commit SHA")
    parser_snapshot.set_defaults(func=cmd_snapshot)

    parser_search = subparsers.add_parser("search", help="Search commit history")
    parser_search.add_argument("keywords", nargs="+", help="Keywords to search for")
    parser_search.add_argument("--limit", type=int, default=100, help="Max commits to search")
    parser_search.set_defaults(func=cmd_search)

    parser_validate = subparsers.add_parser("validate", help="Validate gctx setup")
    parser_validate.set_defaults(func=cmd_validate)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
