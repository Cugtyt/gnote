"""Git-based context management."""

from datetime import datetime
from typing import TypedDict

from git import Repo
from git.exc import InvalidGitRepositoryError

from gctx.config_manager import ConfigManager
from gctx.logger import get_logger


class CommitInfo(TypedDict):
    """Type for commit information."""

    sha: str
    message: str
    timestamp: str


class HistoryResult(TypedDict):
    """Type for history result."""

    commits: list[CommitInfo]
    total_commits: int
    has_more: bool


class GitContextManager:
    """Manages context file within a Git repository."""

    def __init__(self, branch: str) -> None:
        """Initialize Git context manager.

        Args:
            branch: Branch to operate on (required).

        Raises:
            RuntimeError: If repository initialization fails
        """
        self.repo_path = ConfigManager.REPO_PATH
        self.context_file = ConfigManager.CONTEXT_FILE
        self.context_file_path = self.repo_path / self.context_file

        self.repo = self._initialize_repo()

        self.branch = branch
        if branch not in [ref.name for ref in self.repo.heads]:
            self._create_branch_from_main(branch)
        if self.repo.active_branch.name != branch:
            self.repo.heads[branch].checkout()

        self.logger = get_logger(self.branch)
        self.logger.info(f"Initialized GitContextManager for branch: {self.branch}")

    def __del__(self) -> None:
        """Cleanup Git repository resources."""
        if hasattr(self, "repo") and self.repo is not None:
            try:
                self.repo.close()
            except Exception:
                pass

    def _initialize_repo(self) -> Repo:
        """Initialize or open the Git repository.

        Returns:
            Initialized Git repository

        Raises:
            RuntimeError: If repository initialization fails
        """
        self.repo_path.mkdir(parents=True, exist_ok=True)

        try:
            repo = Repo(self.repo_path)
        except InvalidGitRepositoryError:
            try:
                repo = Repo.init(self.repo_path)

                config = repo.config_writer()
                try:
                    config.set_value("user", "name", "gctx-agent")
                    config.set_value("user", "email", "agent@gctx.local")
                finally:
                    config.release()

                if not self.context_file_path.exists():
                    self.context_file_path.touch()

                repo.index.add([self.context_file])
                repo.index.commit("Initialize gctx context")
            except Exception as e:
                raise RuntimeError(f"Failed to initialize repository: {e}") from e

        return repo

    def _create_branch_from_main(self, branch: str) -> None:
        """Create a new branch from main or current branch.

        Args:
            branch: Name of branch to create
        """
        if "main" in [ref.name for ref in self.repo.heads]:
            source = self.repo.heads["main"]
        else:
            source = self.repo.active_branch

        self.repo.create_head(branch, source)

    @staticmethod
    def get_active_branch() -> str:
        """Get the currently active branch name without initializing a manager.

        Returns:
            Active branch name

        Raises:
            RuntimeError: If repository doesn't exist or can't be accessed
        """
        repo_path = ConfigManager.REPO_PATH
        try:
            repo = Repo(repo_path)
            return repo.active_branch.name
        except (InvalidGitRepositoryError, Exception) as e:
            msg = f"Failed to get active branch: {e}"
            raise RuntimeError(msg) from e

    def get_current_branch(self) -> str:
        """Get current active branch name.

        Returns:
            Current branch name
        """
        return self.branch

    def read_context(self) -> str:
        """Read current context content from branch HEAD.

        Returns:
            Content of context file as string

        Raises:
            RuntimeError: If reading context fails
        """
        try:
            commit = self.repo.heads[self.branch].commit
            blob = commit.tree / self.context_file
            content = blob.data_stream.read().decode("utf-8")
            return content
        except Exception as e:
            self.logger.error(f"Failed to read context: {e}")
            raise RuntimeError(f"Failed to read context from branch '{self.branch}': {e}") from e

    def write_context(self, content: str, message: str) -> str:
        """Write new content to context file and commit.

        Args:
            content: New context content
            message: Commit message

        Returns:
            Git commit SHA hash

        Raises:
            RuntimeError: If Git commit fails
        """
        try:
            self.logger.info(f"Writing context: {message}")
            parent = self.repo.heads[self.branch].commit

            # Write to file
            self.context_file_path.write_text(content, encoding="utf-8")

            # Commit to branch
            self.repo.index.reset(commit=parent)
            self.repo.index.add([self.context_file])
            new_commit = self.repo.index.commit(message, parent_commits=[parent], head=False)

            # Update branch ref
            self.repo.heads[self.branch].commit = new_commit

            self.logger.info(f"Committed: {new_commit.hexsha[:8]}")
            return new_commit.hexsha
        except Exception as e:
            self.logger.error(f"Failed to write context: {e}")
            raise RuntimeError(f"Failed to write context: {e}") from e

    def append_context(self, text: str, message: str) -> str:
        """Append text to context file and commit.

        Args:
            text: Text to append
            message: Commit message

        Returns:
            Git commit SHA hash
        """
        self.logger.info(f"Appending to context: {message}")
        current = self.read_context()

        separator = "\n" if current and not current.endswith("\n") else ""
        new_content = current + separator + text

        return self.write_context(new_content, message)

    def get_history(self, limit: int = 10, starting_after: str | None = None) -> HistoryResult:
        """Get commit history for branch.

        Args:
            limit: Number of commits to retrieve
            starting_after: SHA of commit to start after, or None for most recent

        Returns:
            Dictionary with commits list, total_commits, and has_more flag
        """
        total = sum(1 for _ in self.repo.iter_commits(self.branch))

        if starting_after:
            start = self.repo.commit(starting_after)
            if start.parents:
                commits_iter = self.repo.iter_commits(start.parents[0], max_count=limit)
            else:
                return {"commits": [], "total_commits": total, "has_more": False}
        else:
            commits_iter = self.repo.iter_commits(self.branch, max_count=limit)

        commits = []
        for c in commits_iter:
            commits.append(
                {
                    "sha": c.hexsha,
                    "message": c.message.strip(),
                    "timestamp": datetime.fromtimestamp(c.committed_date).isoformat(),
                }
            )

        has_more = False
        if commits:
            last = self.repo.commit(commits[-1]["sha"])
            has_more = len(last.parents) > 0

        return {"commits": commits, "total_commits": total, "has_more": has_more}

    def get_snapshot(self, commit_sha: str) -> dict[str, str]:
        """Get context content from specific commit.

        Args:
            commit_sha: Git commit SHA to retrieve

        Returns:
            Dictionary with content, commit_message, and timestamp

        Raises:
            RuntimeError: If commit doesn't exist or file not found
        """
        try:
            commit = self.repo.commit(commit_sha)
            blob = commit.tree / self.context_file
            content: str = blob.data_stream.read().decode("utf-8")
            commit_message: str = str(commit.message).strip()
            timestamp: str = datetime.fromtimestamp(commit.committed_date).isoformat()

            return {
                "content": content,
                "commit_message": commit_message,
                "timestamp": timestamp,
            }
        except Exception as e:
            raise RuntimeError(f"Failed to get snapshot for commit {commit_sha}: {e}") from e

    def list_branches(self) -> list[str]:
        """List all branch names.

        Returns:
            List of branch names
        """
        return [ref.name for ref in self.repo.heads]

    def create_branch(self, name: str, from_branch: str | None = None) -> str:
        """Create new branch.

        Args:
            name: Name for the new branch
            from_branch: Branch to fork from (default: current branch)

        Returns:
            Name of created branch

        Raises:
            ValueError: If branch already exists
        """
        if name in self.list_branches():
            raise ValueError(f"Branch '{name}' already exists")

        if from_branch:
            if from_branch not in self.list_branches():
                raise ValueError(f"Source branch '{from_branch}' does not exist")
            source = self.repo.heads[from_branch]
        else:
            source = self.repo.heads[self.branch]

        self.repo.create_head(name, source)
        self.logger.info(f"Created branch: {name}")
        return name

    def checkout_branch(self, name: str) -> None:
        """Checkout a branch.

        Args:
            name: Branch name to checkout

        Raises:
            ValueError: If branch doesn't exist
        """
        if name not in self.list_branches():
            raise ValueError(f"Branch '{name}' does not exist")

        self.repo.heads[name].checkout()
        self.branch = name
        self.logger.info(f"Checked out branch: {name}")
