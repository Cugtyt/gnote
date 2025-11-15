"""CLI commands for gnote."""

import argparse
import json
import re
import sys

from pydantic import ValidationError

from gnote.config import GnoteConfig
from gnote.config_manager import ConfigManager
from gnote.git_manager import GitNoteManager


def validate_branch_name(branch: str) -> str:
    if not branch:
        raise ValueError("Branch name cannot be empty")

    if len(branch) > 255:
        raise ValueError("Branch name too long (max 255 characters)")

    if not re.match(r"^[a-zA-Z0-9._/-]+$", branch):
        raise ValueError(
            "Branch name must contain only letters, numbers, dots, "
            "underscores, hyphens, and forward slashes"
        )

    if ".." in branch or branch.startswith("/") or branch.startswith("."):
        raise ValueError("Branch name cannot contain '..' or start with '/' or '.'")

    if branch.lower() in ("head",) and branch != branch.lower():
        raise ValueError(f"Branch name '{branch}' conflicts with reserved Git names")

    return branch


def cmd_init(args: argparse.Namespace) -> None:
    """Initialize gnote structure.

    CLI: gnote init <branch>
    """
    try:
        branch: str = validate_branch_name(args.branch)
    except ValueError as e:
        print(f"✗ Invalid branch name: {e}", file=sys.stderr)
        sys.exit(1)

    ConfigManager.GNOTE_HOME.mkdir(parents=True, exist_ok=True)
    (ConfigManager.GNOTE_HOME / "configs").mkdir(exist_ok=True)
    (ConfigManager.GNOTE_HOME / "logs").mkdir(exist_ok=True)

    ConfigManager.initialize_default()

    try:
        GitNoteManager(branch)
        GitNoteManager.checkout_branch(branch)
        print("✓ gnote initialized at ~/.gnote")
        print("  - Repository created at ~/.gnote/repo")
        print(f"  - Default config created at ~/.gnote/{ConfigManager.GLOBAL_CONFIG_FILE}")
        print(f"  - Active branch: {branch}")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_config_show(args: argparse.Namespace) -> None:
    """Show configuration for current branch.

    CLI: gnote config
    """
    try:
        branch = GitNoteManager.get_active_branch()
        config = ConfigManager.load_for_branch(branch)

        print(f"# Configuration for branch: {branch}")
        print(config.model_dump_json(indent=2))

    except Exception as e:
        print(f"✗ Failed to load config: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_config_set(args: argparse.Namespace) -> None:
    """Set configuration value for current branch.

    CLI: gnote config set <key> <value>
    """
    try:
        key: str = args.key
        raw_value: str = args.value

        branch = GitNoteManager.get_active_branch()
        current_config = ConfigManager.load_for_branch(branch)
        overrides = ConfigManager.get_branch_override(branch)

        if key not in GnoteConfig.model_fields:
            valid_keys = ", ".join(GnoteConfig.model_fields.keys())
            print(f"✗ Unknown config key: {key}", file=sys.stderr)
            print(f"  Valid keys: {valid_keys}", file=sys.stderr)
            sys.exit(1)

        field_info = GnoteConfig.model_fields[key]
        parsed_value: str | int

        try:
            if field_info.annotation is int:
                parsed_value = int(raw_value)
            else:
                parsed_value = raw_value

            test_config_data = current_config.model_dump()
            test_config_data[key] = parsed_value
            GnoteConfig(**test_config_data)

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

    CLI: gnote branch
    """
    try:
        branch = GitNoteManager.get_active_branch()
        print(branch)
    except Exception as e:
        print(f"✗ Failed to get current branch: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_branch_list(args: argparse.Namespace) -> None:
    """List all branches.

    CLI: gnote branch list
    """
    try:
        current = GitNoteManager.get_active_branch()
        branches = GitNoteManager.list_branches()

        for branch in branches:
            marker = "*" if branch == current else " "
            print(f"{marker} {branch}")

    except Exception as e:
        print(f"✗ Failed to list branches: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_branch_create(args: argparse.Namespace) -> None:
    """Create new branch.

    CLI: gnote branch create <name> [--from <branch>]
    """
    try:
        name: str = validate_branch_name(args.name)
        from_branch: str | None = args.from_branch
        if from_branch:
            from_branch = validate_branch_name(from_branch)

        current = GitNoteManager.get_active_branch()
        with GitNoteManager(current) as manager:
            sha = manager.create_branch(name, from_branch)
            print(f"✓ Created branch '{name}' at {sha[:8]}")

    except Exception as e:
        print(f"✗ Failed to create branch: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_branch_checkout(args: argparse.Namespace) -> None:
    """Checkout branch.

    CLI: gnote branch checkout <name>
    """
    try:
        name: str = validate_branch_name(args.name)

        GitNoteManager.checkout_branch(name)
        print(f"✓ Switched to branch '{name}'")

    except Exception as e:
        print(f"✗ Failed to checkout branch: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_read(args: argparse.Namespace) -> None:
    """Read current note.

    CLI: gnote read
    """
    try:
        branch = GitNoteManager.get_active_branch()
        with GitNoteManager(branch) as manager:
            content = manager.read_note()
            print(content)

    except Exception as e:
        print(f"✗ Failed to read note: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_update(args: argparse.Namespace) -> None:
    """Update note with new content.

    CLI: gnote update <message> --content <text>
          gnote update <message>  (reads from stdin)
    """
    try:
        message: str = args.message
        content_arg: str | None = args.content

        branch = GitNoteManager.get_active_branch()
        with GitNoteManager(branch) as manager:
            if content_arg:
                content = content_arg
            else:
                print("Enter new note (Ctrl+D or Ctrl+Z to finish):")
                content = sys.stdin.read()

            sha = manager.write_note(content, message)
            print(f"✓ Updated note: {sha[:8]}")

    except Exception as e:
        print(f"✗ Failed to update note: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_append(args: argparse.Namespace) -> None:
    """Append text to note.

    CLI: gnote append <message> --text <text>
          gnote append <message>  (reads from stdin)
    """
    try:
        message: str = args.message
        text_arg: str | None = args.text

        branch = GitNoteManager.get_active_branch()
        with GitNoteManager(branch) as manager:
            if text_arg:
                text = text_arg
            else:
                print("Enter text to append (Ctrl+D or Ctrl+Z to finish):")
                text = sys.stdin.read()

            sha = manager.append_note(text, message)
            print(f"✓ Appended to note: {sha[:8]}")

    except Exception as e:
        print(f"✗ Failed to append to note: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_history(args: argparse.Namespace) -> None:
    """Show commit history.

    CLI: gnote history [--limit N] [--starting-after SHA]
    """
    try:
        limit: int = args.limit
        starting_after: str | None = args.starting_after

        branch = GitNoteManager.get_active_branch()
        with GitNoteManager(branch) as manager:
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
    """Show snapshot of note at specific commit.

    CLI: gnote snapshot <sha>
    """
    try:
        sha: str = args.sha

        branch = GitNoteManager.get_active_branch()
        with GitNoteManager(branch) as manager:
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

    CLI: gnote search <keyword> [keyword...] [--limit N]
    """
    try:
        keywords: list[str] = args.keywords
        limit: int = args.limit

        branch = GitNoteManager.get_active_branch()
        with GitNoteManager(branch) as manager:
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
    """Validate gnote setup.

    CLI: gnote validate
    """
    errors = []

    if not ConfigManager.GNOTE_HOME.exists():
        errors.append("~/.gnote directory does not exist. Run 'gnote init' first.")
    else:
        print("✓ ~/.gnote directory exists")

        config_path = ConfigManager.GNOTE_HOME / ConfigManager.GLOBAL_CONFIG_FILE
        if not config_path.exists():
            errors.append(f"~/.gnote/{ConfigManager.GLOBAL_CONFIG_FILE} does not exist")
        else:
            print(f"✓ ~/.gnote/{ConfigManager.GLOBAL_CONFIG_FILE} exists")
            try:
                with config_path.open() as f:
                    json.load(f)
                print(f"✓ {ConfigManager.GLOBAL_CONFIG_FILE} is valid JSON")
            except json.JSONDecodeError:
                errors.append(f"~/.gnote/{ConfigManager.GLOBAL_CONFIG_FILE} is not valid JSON")

        if not ConfigManager.REPO_PATH.exists():
            errors.append("~/.gnote/repo does not exist")
        else:
            print("✓ ~/.gnote/repo exists")
            try:
                branch = GitNoteManager.get_active_branch()
                print(f"✓ Current branch: {branch}")
            except Exception as e:
                errors.append(f"Git repository error: {e}")

        for subdir in ["configs", "logs"]:
            path = ConfigManager.GNOTE_HOME / subdir
            if not path.exists():
                errors.append(f"~/.gnote/{subdir} does not exist")
            else:
                print(f"✓ ~/.gnote/{subdir} exists")

    if errors:
        print("\n✗ Validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("\n✓ All checks passed!")


def cmd_repair(args: argparse.Namespace) -> None:
    """Verify and repair gnote repository integrity.

    CLI: gnote repair
    """
    try:
        issues_found = []

        if not ConfigManager.GNOTE_HOME.exists():
            issues_found.append("~/.gnote directory missing")
            ConfigManager.GNOTE_HOME.mkdir(parents=True, exist_ok=True)
            print("✓ Created ~/.gnote directory")

        for subdir in ["configs", "logs"]:
            path = ConfigManager.GNOTE_HOME / subdir
            if not path.exists():
                issues_found.append(f"~/.gnote/{subdir} missing")
                path.mkdir(exist_ok=True)
                print(f"✓ Created ~/.gnote/{subdir}")

        if not ConfigManager.REPO_PATH.exists():
            issues_found.append("Git repository missing")
            print("✗ Git repository not found. Run 'gnote init <branch>' to initialize")
            sys.exit(1)

        try:
            from git import Repo

            repo = Repo(ConfigManager.REPO_PATH)

            repo.git.fsck()
            print("✓ Git repository integrity check passed")

            branches = [ref.name for ref in repo.heads]
            print(f"✓ Found {len(branches)} branches: {', '.join(branches)}")

        except Exception as e:
            issues_found.append(f"Git repository error: {e}")
            print(f"✗ Git repository integrity check failed: {e}")
            print("  Consider backing up ~/.gnote and running 'gnote init' again")
            sys.exit(1)

        if not issues_found:
            print("\n✓ All integrity checks passed!")
        else:
            print(f"\n⚠ Fixed {len(issues_found)} issues")

    except Exception as e:
        print(f"✗ Repair failed: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="gnote - Git-based note management for LLM agents")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    parser_init = subparsers.add_parser("init", help="Initialize gnote")
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

    parser_read = subparsers.add_parser("read", help="Read current note")
    parser_read.set_defaults(func=cmd_read)

    parser_update = subparsers.add_parser("update", help="Update note")
    parser_update.add_argument("message", help="Commit message")
    parser_update.add_argument("--content", help="New content (or use stdin)")
    parser_update.set_defaults(func=cmd_update)

    parser_append = subparsers.add_parser("append", help="Append to note")
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

    parser_validate = subparsers.add_parser("validate", help="Validate gnote setup")
    parser_validate.set_defaults(func=cmd_validate)

    parser_repair = subparsers.add_parser("repair", help="Verify and repair repository")
    parser_repair.set_defaults(func=cmd_repair)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
