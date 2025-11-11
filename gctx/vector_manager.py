"""Vector search manager with FAISS indexing and background sync."""

import hashlib
import sqlite3
import threading
import time
from datetime import datetime

import faiss
from git import Repo
from git.objects.commit import Commit
from sentence_transformers import SentenceTransformer

from gctx.config import GctxConfig
from gctx.config_manager import ConfigManager
from gctx.git_manager import CommitInfo
from gctx.logger import BranchLogger


class VectorManager:
    """Manages vector embeddings and similarity search for commits."""

    def __init__(self, branch: str, config: GctxConfig) -> None:
        self.branch = branch
        self.config = config
        self.logger = BranchLogger(self.branch)

        self.vectors_dir = ConfigManager.GCTX_HOME / "vectors"
        self.vectors_dir.mkdir(exist_ok=True)

        self.index_path = self.vectors_dir / f"{branch}_hnsw.index"
        self.db_path = self.vectors_dir / f"{branch}_metadata.db"

        self.repo_path = ConfigManager.REPO_PATH
        self.context_file = ConfigManager.CONTEXT_FILE

        self.model = None
        self.index = None
        self.running = False
        self.daemon_thread = None

        self._init_db()

        if self._check_rebuild_needed():
            self._full_rebuild()
        else:
            self._load_existing()

        self._start_daemon()

    def _get_db_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    def _init_db(self) -> None:
        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='vector_mapping'"
            )
            result = cursor.fetchone()

            if result:
                schema_sql = result[0]
                if "faiss_id" not in schema_sql:
                    self.logger.info("Old schema detected, dropping tables to rebuild")
                    cursor.execute("DROP TABLE IF EXISTS vector_mapping")
                    cursor.execute("DROP TABLE IF EXISTS system_state")
                    conn.commit()

                    if self.index_path.exists():
                        self.index_path.unlink()
                        self.logger.info("Deleted old index file")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vector_mapping (
                    faiss_id INTEGER PRIMARY KEY,
                    commit_sha TEXT NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sha ON vector_mapping(commit_sha)")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    last_commit_sha TEXT,
                    config_hash TEXT,
                    last_sync_timestamp INTEGER
                )
            """)

            cursor.execute("SELECT COUNT(*) FROM system_state")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO system_state (id, last_commit_sha, config_hash) "
                    "VALUES (1, NULL, NULL)"
                )

            conn.commit()

    def _check_rebuild_needed(self) -> bool:
        if not self.index_path.exists():
            self.logger.info("No index file, rebuild needed")
            return True

        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT config_hash FROM system_state WHERE id=1")
            row = cursor.fetchone()

            current_hash = self._compute_config_hash()
            if not row or row[0] != current_hash:
                self.logger.info("Config changed, rebuild needed")
                return True

        return False

    def _compute_config_hash(self) -> str:
        return hashlib.sha256(self.config.vector.model_name.encode()).hexdigest()

    def _full_rebuild(self) -> None:
        self.logger.info(f"Starting full rebuild for branch {self.branch}")

        self.model = SentenceTransformer(self.config.vector.model_name)
        dimension = self.model.get_sentence_embedding_dimension()

        self.index = faiss.IndexHNSWFlat(dimension, 32)  # type: ignore[attr-defined]

        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM vector_mapping")
            conn.commit()

        repo = Repo(self.repo_path)
        commits = list(repo.iter_commits(self.branch))

        self.logger.info(f"Indexing {len(commits)} commits...")

        for i, commit in enumerate(commits):
            try:
                self._add_commit_to_index(commit)

                if (i + 1) % 100 == 0:
                    self.logger.info(f"Indexed {i + 1}/{len(commits)} commits")
            except Exception as e:
                self.logger.error(f"Failed to index commit {commit.hexsha}: {e}")
                raise

        faiss.write_index(self.index, str(self.index_path))  # type: ignore[attr-defined]

        # Get the HEAD of the specific branch we're indexing
        branch_head_sha = repo.heads[self.branch].commit.hexsha
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE system_state
                   SET last_commit_sha=?, config_hash=?, last_sync_timestamp=?
                   WHERE id=1""",
                (branch_head_sha, self._compute_config_hash(), int(time.time())),
            )
            conn.commit()

        self.logger.info(f"Rebuild complete: {self.index.ntotal} vectors indexed")  # type: ignore[union-attr]

    def _load_existing(self) -> None:
        self.logger.info(f"Loading existing index for branch {self.branch}")

        self.model = SentenceTransformer(self.config.vector.model_name)
        self.index = faiss.read_index(str(self.index_path))  # type: ignore[attr-defined]

        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM vector_mapping")
            count = cursor.fetchone()[0]

        self.logger.info(f"Loaded {self.index.ntotal} vectors, {count} mappings")  # type: ignore[union-attr]

    def _add_commit_to_index(self, commit: Commit) -> None:
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM vector_mapping WHERE commit_sha=?", (commit.hexsha,)
            )
            count = cursor.fetchone()[0]

            if count >= 2:
                self.logger.debug(f"Commit {commit.hexsha} already indexed")
                return

            if count == 1:
                self.logger.warning(f"Partial index found for {commit.hexsha}, reindexing")
                cursor.execute("DELETE FROM vector_mapping WHERE commit_sha=?", (commit.hexsha,))

            message_embedding = self.model.encode(commit.message, convert_to_numpy=True)  # type: ignore[union-attr]
            message_embedding = message_embedding.reshape(1, -1).astype("float32")
            faiss.normalize_L2(message_embedding)  # type: ignore[attr-defined]

            message_faiss_id = self.index.ntotal  # type: ignore[union-attr]
            self.index.add(message_embedding)  # type: ignore[union-attr]

            cursor.execute(
                "INSERT INTO vector_mapping (faiss_id, commit_sha) VALUES (?, ?)",
                (message_faiss_id, commit.hexsha),
            )

            try:
                if commit.parents:
                    parent = commit.parents[0]
                    diff_text = parent.diff(commit, create_patch=True, paths=[self.context_file])
                    if diff_text:
                        diffs = []
                        for d in diff_text:
                            if d.diff:
                                content = d.diff
                                if isinstance(content, bytes):
                                    content = content.decode("utf-8")
                                diffs.append(content)
                        diff_content = "\n".join(diffs)
                    else:
                        diff_content = ""
                else:
                    blob = commit.tree / self.context_file
                    diff_content = blob.data_stream.read().decode("utf-8")

                if diff_content:
                    diff_embedding = self.model.encode(diff_content, convert_to_numpy=True)  # type: ignore[union-attr]
                    diff_embedding = diff_embedding.reshape(1, -1).astype("float32")
                    faiss.normalize_L2(diff_embedding)  # type: ignore[attr-defined]

                    diff_faiss_id = self.index.ntotal  # type: ignore[union-attr]
                    self.index.add(diff_embedding)  # type: ignore[union-attr]

                    cursor.execute(
                        "INSERT INTO vector_mapping (faiss_id, commit_sha) VALUES (?, ?)",
                        (diff_faiss_id, commit.hexsha),
                    )

                    self.logger.info(
                        f"Indexed commit {commit.hexsha[:8]}: "
                        f"message + diff ({len(diff_content)} chars)"
                    )
                else:
                    self.logger.info(f"Indexed commit {commit.hexsha[:8]}: message only (no diff)")
            except Exception as e:
                self.logger.warning(
                    f"Failed to add diff vector for {commit.hexsha[:8]}: {type(e).__name__}: {e}"
                )

            conn.commit()

    def _start_daemon(self) -> None:
        self.running = True
        self.daemon_thread = threading.Thread(target=self._daemon_loop, daemon=True)
        self.daemon_thread.start()
        self.logger.info("Vector daemon started")

    def _daemon_loop(self) -> None:
        while self.running:
            try:
                time.sleep(self.config.vector.sync_interval_seconds)
                self._incremental_sync()
            except Exception as e:
                self.logger.error(f"Daemon sync error: {e}")
                self.running = False
                raise

    def _incremental_sync(self) -> None:
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_commit_sha FROM system_state WHERE id=1")
            row = cursor.fetchone()
            last_sha = row[0] if row else None

        if last_sha is None:
            self.logger.info("No last_commit_sha, triggering full rebuild")
            self._full_rebuild()
            return

        repo = Repo(self.repo_path)
        new_commits = []

        for commit in repo.iter_commits(self.branch):
            if commit.hexsha == last_sha:
                break
            new_commits.append(commit)

        if not new_commits:
            self.logger.debug("No new commits to sync")
            return

        self.logger.info(f"Incremental sync: {len(new_commits)} new commits")

        for commit in reversed(new_commits):
            try:
                self._add_commit_to_index(commit)
            except Exception as e:
                self.logger.error(f"Failed to index {commit.hexsha}: {e}")
                raise

        faiss.write_index(self.index, str(self.index_path))  # type: ignore[attr-defined]

        # Get the HEAD of the specific branch we're indexing
        branch_head_sha = repo.heads[self.branch].commit.hexsha
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE system_state
                   SET last_commit_sha=?, last_sync_timestamp=?
                   WHERE id=1""",
                (branch_head_sha, int(time.time())),
            )
            conn.commit()

        self.logger.info(f"Sync complete: {self.index.ntotal} total vectors")  # type: ignore[union-attr]

    def search_similar(self, query_texts: list[str]) -> list[CommitInfo]:
        k = self.config.vector.top_k
        threshold = self.config.vector.similarity_threshold

        all_results = {}

        for query_text in query_texts:
            query_embedding = self.model.encode(query_text, convert_to_numpy=True)  # type: ignore[union-attr]
            query_embedding = query_embedding.reshape(1, -1).astype("float32")
            faiss.normalize_L2(query_embedding)  # type: ignore[attr-defined]

            distances, indices = self.index.search(query_embedding, k)  # type: ignore[union-attr]

            similarities = 1 - (distances[0] ** 2 / 2)

            valid_indices = [int(idx) for idx in indices[0] if idx >= 0]

            if not valid_indices:
                continue

            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                placeholders = ",".join("?" * len(valid_indices))
                cursor.execute(
                    "SELECT faiss_id, commit_sha FROM vector_mapping "
                    f"WHERE faiss_id IN ({placeholders})",
                    valid_indices,
                )
                id_to_sha = dict(cursor.fetchall())

            for idx, sim in zip(indices[0], similarities, strict=True):
                if sim >= threshold and idx in id_to_sha:
                    sha = id_to_sha[idx]

                    if sha not in all_results or sim > all_results[sha][1]:
                        commit_info = self._get_commit_info(sha)
                        all_results[sha] = (commit_info, sim)

        sorted_results = sorted(all_results.values(), key=lambda x: x[1], reverse=True)
        return [info for info, _ in sorted_results[:k]]

    def _get_commit_info(self, sha: str) -> CommitInfo:
        repo = Repo(self.repo_path)
        commit = repo.commit(sha)
        return CommitInfo(
            sha=commit.hexsha,
            message=str(commit.message).strip(),
            timestamp=datetime.fromtimestamp(commit.committed_date).isoformat(),
        )

    def shutdown(self) -> None:
        self.logger.info("Shutting down vector manager")
        self.running = False

        if self.daemon_thread:
            self.daemon_thread.join(timeout=5)

        self.logger.close()

    def __enter__(self) -> "VectorManager":
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.shutdown()
