"""Git-based context management."""

from dataclasses import dataclass
from datetime import datetime
from types import TracebackType

from git import Repo
from git.exc import InvalidGitRepositoryError

from gnote.config_manager import ConfigManager
from gnote.logger import BranchLogger


@dataclass(frozen=True)
class CommitInfo:
    """Type for commit information."""

    sha: str
    message: str
    timestamp: str


@dataclass(frozen=True)
class History:
    """Type for history."""

    commits: list[CommitInfo]
    total_commits: int
    has_more: bool


@dataclass(frozen=True)
class Snapshot:
    """Type for snapshot."""

    content: str
    commit_message: str
    timestamp: str


@dataclass(frozen=True)
class Search:
    """Type for search."""

    commits: list[CommitInfo]
    total_matches: int


class GitNoteManager:
    """Manages note file within a Git repository.

    Can be used as a note manager for proper resource cleanup:
        with GitNoteManager("branch") as manager:
            manager.write_note("content", "message")
    """

    def __init__(self, branch: str) -> None:
        """Initialize Git note manager.

        Args:
            branch: Branch to operate on (required).

        Raises:
            RuntimeError: If repository initialization fails
        """
        self.branch = branch
        self.logger = BranchLogger(self.branch)

        self.repo_path = ConfigManager.REPO_PATH
        self.note_file = ConfigManager.CONTEXT_FILE
        self.note_file_path = self.repo_path / self.note_file

        self.repo = self._initialize_repo()

        if branch not in [ref.name for ref in self.repo.heads]:
            self._create_branch_from_main(branch)

        self.logger.info(f"Initialized GitNoteManager for branch: {self.branch}")

    def __enter__(self) -> "GitNoteManager":
        """Note manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Note manager exit - cleanup resources."""
        self.logger.close()

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
            self.logger.info(f"Opened existing repository at {self.repo_path}")
        except InvalidGitRepositoryError:
            self.logger.info(f"Initializing new repository at {self.repo_path}")
            try:
                repo = Repo.init(self.repo_path)
                self.logger.info("Repository initialized")

                config = repo.config_writer()
                try:
                    config.set_value("user", "name", "gnote-agent")
                    config.set_value("user", "email", "agent@gnote.local")
                    self.logger.info("Git config set: user.name and user.email")
                finally:
                    config.release()

                if not self.note_file_path.exists():
                    self.note_file_path.touch()
                    self.logger.info(f"Created note file: {self.note_file}")

                repo.index.add([self.note_file])
                repo.index.commit("Initialize gnote note")
                self.logger.info("Initial commit created")
            except Exception as e:
                self.logger.error(f"Failed to initialize repository: {e}")
                raise RuntimeError(f"Failed to initialize repository: {e}") from e

        return repo

    def _create_branch_from_main(self, branch: str) -> None:
        """Create a new branch from main or current branch.

        Args:
            branch: Name of branch to create
        """
        if "main" in [ref.name for ref in self.repo.heads]:
            source = self.repo.heads["main"]
            self.logger.info(f"Creating branch '{branch}' from 'main'")
        else:
            source = self.repo.active_branch
            self.logger.info(f"Creating branch '{branch}' from '{source.name}'")

        self.repo.create_head(branch, source)
        self.logger.info(f"Branch '{branch}' created")

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
            branch_name = repo.active_branch.name
            return branch_name
        except (InvalidGitRepositoryError, Exception) as e:
            msg = f"Failed to get active branch: {e}"
            raise RuntimeError(msg) from e

    def get_current_branch(self) -> str:
        """Get current active branch name.

        Returns:
            Current branch name
        """
        return self.branch

    def read_note(self) -> str:
        """Read current note content from branch HEAD.

        Returns:
            Content of note file as string

        Raises:
            RuntimeError: If reading note fails
        """
        try:
            self.logger.info(f"Reading note from branch '{self.branch}'")
            commit = self.repo.heads[self.branch].commit
            blob = commit.tree / self.note_file
            content = blob.data_stream.read().decode("utf-8")
            self.logger.info(f"Read {len(content)} characters from note")
            return content
        except Exception as e:
            self.logger.error(f"Failed to read note: {e}")
            raise RuntimeError(f"Failed to read note from branch '{self.branch}': {e}") from e

    def write_note(self, content: str, message: str) -> str:
        """Write new content to note file and commit.

        Args:
            content: New note content
            message: Commit message

        Returns:
            Git commit SHA hash

        Raises:
            RuntimeError: If Git commit fails
        """
        try:
            self.logger.info(f"Writing note: {message}")
            parent = self.repo.heads[self.branch].commit

            self.note_file_path.write_text(content, encoding="utf-8")

            self.repo.index.reset(commit=parent)
            self.repo.index.add([self.note_file])
            new_commit = self.repo.index.commit(message, parent_commits=[parent], head=False)

            self.repo.heads[self.branch].commit = new_commit

            self.logger.info(f"Committed: {new_commit.hexsha[:8]}")
            return new_commit.hexsha
        except Exception as e:
            self.logger.error(f"Failed to write note: {e}")
            raise RuntimeError(f"Failed to write note: {e}") from e

    def append_note(self, text: str, message: str) -> str:
        """Append text to note file and commit.

        Args:
            text: Text to append
            message: Commit message

        Returns:
            Git commit SHA hash
        """
        self.logger.info(f"Appending to note: {message}")
        current = self.read_note()

        separator = "\n" if current and not current.endswith("\n") else ""
        new_content = current + separator + text

        return self.write_note(new_content, message)

    def get_history(self, limit: int = 10, starting_after: str | None = None) -> History:
        """Get commit history for branch.

        Args:
            limit: Number of commits to retrieve
            starting_after: SHA of commit to start after, or None for most recent

        Returns:
            History with commits list, total_commits, has_more flag

        Raises:
            RuntimeError: If getting history fails
        """
        self.logger.info(
            f"Getting history for branch '{self.branch}' "
            f"(limit={limit}, starting_after={starting_after})"
        )
        total = sum(1 for _ in self.repo.iter_commits(self.branch))

        if starting_after:
            start = self.repo.commit(starting_after)
            if start.parents:
                commits_iter = self.repo.iter_commits(start.parents[0], max_count=limit)
            else:
                return History(commits=[], total_commits=total, has_more=False)
        else:
            commits_iter = self.repo.iter_commits(self.branch, max_count=limit)

        commits: list[CommitInfo] = []
        for c in commits_iter:
            msg = c.message
            commit_message = str(msg).strip()
            commits.append(
                CommitInfo(
                    sha=c.hexsha,
                    message=commit_message,
                    timestamp=datetime.fromtimestamp(c.committed_date).isoformat(),
                )
            )

        has_more = False
        if commits:
            last = self.repo.commit(commits[-1].sha)
            has_more = len(last.parents) > 0

        self.logger.info(f"Retrieved {len(commits)} commits (total={total}, has_more={has_more})")
        return History(commits=commits, total_commits=total, has_more=has_more)

    def get_snapshot(self, commit_sha: str) -> Snapshot:
        """Get note content from specific commit.

        Args:
            commit_sha: Git commit SHA to retrieve

        Returns:
            Snapshot with content, commit_message, and timestamp

        Raises:
            RuntimeError: If commit doesn't exist or file not found
        """
        try:
            self.logger.info(f"Getting snapshot for commit {commit_sha[:8]}")
            commit = self.repo.commit(commit_sha)
            blob = commit.tree / self.note_file
            content: str = blob.data_stream.read().decode("utf-8")
            commit_message: str = str(commit.message).strip()
            timestamp: str = datetime.fromtimestamp(commit.committed_date).isoformat()

            self.logger.info(f"Retrieved snapshot: {len(content)} characters")
            return Snapshot(
                content=content,
                commit_message=commit_message,
                timestamp=timestamp,
            )
        except Exception as e:
            self.logger.error(f"Failed to get snapshot: {e}")
            raise RuntimeError(f"Failed to get snapshot for commit {commit_sha}: {e}") from e

    def search_history(self, keywords: list[str], limit: int = 100) -> Search:
        """Search commit history for keywords in messages or content.

        Searches through commit history and returns commits where any keyword
        matches either the commit message or the note content.

        Args:
            keywords: List of keywords to search for (case-insensitive)
            limit: Maximum number of commits to search (default: 100)

        Returns:
            Search with matching commits and total count

        Raises:
            RuntimeError: If search fails
        """
        try:
            self.logger.info(f"Searching history for keywords: {keywords} (limit={limit})")

            if not keywords:
                return Search(commits=[], total_matches=0)

            normalized_keywords = [kw.lower() for kw in keywords]

            matching_commits: list[CommitInfo] = []
            searched_count = 0

            for commit in self.repo.iter_commits(self.branch):
                if searched_count >= limit:
                    break
                searched_count += 1

                commit_message = str(commit.message).strip()

                try:
                    blob = commit.tree / self.note_file
                    content = blob.data_stream.read().decode("utf-8")
                except Exception:
                    continue

                search_text = (commit_message + "\n" + content).lower()
                if any(keyword in search_text for keyword in normalized_keywords):
                    matching_commits.append(
                        CommitInfo(
                            sha=commit.hexsha,
                            message=commit_message,
                            timestamp=datetime.fromtimestamp(commit.committed_date).isoformat(),
                        )
                    )

            self.logger.info(
                f"Found {len(matching_commits)} matches out of {searched_count} commits searched"
            )
            return Search(
                commits=matching_commits,
                total_matches=len(matching_commits),
            )
        except Exception as e:
            self.logger.error(f"Failed to search history: {e}")
            raise RuntimeError(f"Failed to search history: {e}") from e

    @classmethod
    def list_branches(cls) -> list[str]:
        """List all branch names.

        Returns:
            List of branch names

        Raises:
            RuntimeError: If repository doesn't exist
        """
        repo_path = ConfigManager.REPO_PATH
        try:
            repo = Repo(repo_path)
            branches = [ref.name for ref in repo.heads]
            return branches
        except (InvalidGitRepositoryError, Exception) as e:
            raise RuntimeError(f"Failed to list branches: {e}") from e

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
        if name in GitNoteManager.list_branches():
            raise ValueError(f"Branch '{name}' already exists")

        if from_branch:
            if from_branch not in GitNoteManager.list_branches():
                raise ValueError(f"Source branch '{from_branch}' does not exist")
            source = self.repo.heads[from_branch]
        else:
            source = self.repo.heads[self.branch]

        self.repo.create_head(name, source)
        self.logger.info(f"Created branch: {name}")
        return name

    @classmethod
    def checkout_branch(cls, name: str) -> None:
        """Checkout a branch in the Git repository.

        This is a class method that changes the active branch in the Git repo.
        It does not require a manager instance since it only affects Git state.

        Args:
            name: Branch name to checkout

        Raises:
            ValueError: If branch doesn't exist
            RuntimeError: If repository doesn't exist or checkout fails
        """
        repo_path = ConfigManager.REPO_PATH
        try:
            repo = Repo(repo_path)
            if name not in [ref.name for ref in repo.heads]:
                raise ValueError(f"Branch '{name}' does not exist")
            repo.heads[name].checkout()
        except (InvalidGitRepositoryError, Exception) as e:
            raise RuntimeError(f"Failed to checkout branch: {e}") from e
