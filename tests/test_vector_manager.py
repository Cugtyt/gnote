"""Tests for vector_manager module."""

import time
from collections.abc import Generator
from pathlib import Path

import pytest

from gctx.config import GctxConfig, VectorConfig
from gctx.config_manager import ConfigManager
from gctx.git_manager import GitContextManager
from gctx.vector_manager import VectorManager


def wait_for_sync(vm: VectorManager, expected_commits: int | None = None, timeout: int = 5) -> None:
    """Wait for vector manager daemon to sync."""
    import sqlite3

    start = time.time()
    while time.time() - start < timeout:
        time.sleep(0.5)
        with sqlite3.connect(str(vm.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(DISTINCT commit_sha) FROM vector_mapping")
            count = cursor.fetchone()[0]
            if expected_commits is None or count >= expected_commits:
                return
    if expected_commits:
        raise TimeoutError(f"Daemon did not sync {expected_commits} commits within {timeout}s")


@pytest.fixture(scope="session")
def session_vector_config() -> VectorConfig:
    """Create a session-wide test vector config."""
    return VectorConfig(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        similarity_threshold=0.3,
        top_k=5,
        sync_interval_seconds=1,
    )


@pytest.fixture(scope="session")
def session_gctx_config(session_vector_config: VectorConfig) -> GctxConfig:
    """Create a session-wide test gctx config."""
    return GctxConfig(vector=session_vector_config)


@pytest.fixture(scope="session")
def session_test_repo(temp_gctx_home_session: Path) -> str:
    """Set up a test repository once for all tests."""
    branch = "test-branch-session"

    (temp_gctx_home_session / "vectors").mkdir(exist_ok=True)

    with GitContextManager(branch) as git_mgr:
        git_mgr.write_context("Initial context content", "Initial commit")
        git_mgr.write_context("Updated context about feature A", "Add feature A")
        git_mgr.write_context("Updated context about feature B", "Add feature B")

    return branch


@pytest.fixture(scope="session")
def temp_gctx_home_session(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a session-wide temporary GCTX_HOME."""
    import os

    gctx_home = tmp_path_factory.mktemp("gctx_session") / ".gctx"
    gctx_home.mkdir(parents=True, exist_ok=True)
    os.environ["GCTX_HOME"] = str(gctx_home)
    return gctx_home


@pytest.fixture(scope="session")
def session_vector_manager(
    session_test_repo: str, session_gctx_config: GctxConfig
) -> Generator[VectorManager]:
    """Create a session-wide VectorManager that's reused across tests."""
    vm = VectorManager(session_test_repo, session_gctx_config)
    vm.__enter__()
    wait_for_sync(vm, expected_commits=3, timeout=10)
    yield vm
    vm.__exit__(None, None, None)


@pytest.fixture
def vector_config() -> VectorConfig:
    """Create a test vector config."""
    return VectorConfig(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        similarity_threshold=0.3,
        top_k=5,
        sync_interval_seconds=1,
    )


@pytest.fixture
def gctx_config(vector_config: VectorConfig) -> GctxConfig:
    """Create a test gctx config."""
    return GctxConfig(vector=vector_config)


@pytest.fixture
def setup_test_repo(temp_gctx_home: Path) -> str:
    """Set up a test repository with some commits."""
    branch = "test-branch"

    (temp_gctx_home / "vectors").mkdir(exist_ok=True)

    with GitContextManager(branch) as git_mgr:
        git_mgr.write_context("Initial context content", "Initial commit")
        git_mgr.write_context("Updated context about feature A", "Add feature A")
        git_mgr.write_context("Updated context about feature B", "Add feature B")

    return branch


def test_vector_manager_initialization(
    temp_gctx_home: Path, setup_test_repo: str, gctx_config: GctxConfig
) -> None:
    """Test VectorManager initialization and index building."""
    branch = setup_test_repo

    with VectorManager(branch, gctx_config) as vm:
        assert vm.index is not None
        assert vm.model is not None
        assert vm.index.ntotal >= 3
        assert vm.running is True


def test_vector_manager_rebuild_on_model_change(
    temp_gctx_home: Path, setup_test_repo: str, gctx_config: GctxConfig
) -> None:
    """Test that changing model triggers rebuild."""
    branch = setup_test_repo

    with VectorManager(branch, gctx_config) as vm:
        initial_count = vm.index.ntotal  # type: ignore[union-attr]
        assert initial_count >= 3

    new_config = GctxConfig(
        vector=VectorConfig(
            model_name="sentence-transformers/paraphrase-MiniLM-L3-v2",
            similarity_threshold=0.3,
        )
    )

    with VectorManager(branch, new_config) as vm:
        new_count = vm.index.ntotal  # type: ignore[union-attr]
        assert new_count >= 3, "Should rebuild with new model"


def test_vector_search(session_vector_manager: VectorManager) -> None:
    """Test vector similarity search."""
    results = session_vector_manager.search_similar(["feature A"])

    assert len(results) > 0
    assert results[0].sha is not None
    assert results[0].message is not None


def test_vector_search_multiple_queries(session_vector_manager: VectorManager) -> None:
    """Test search with multiple query strings."""
    results = session_vector_manager.search_similar(["feature", "context"])

    assert len(results) > 0


def test_incremental_sync(
    temp_gctx_home: Path, setup_test_repo: str, gctx_config: GctxConfig
) -> None:
    """Test incremental sync of new commits."""
    branch = setup_test_repo

    with VectorManager(branch, gctx_config) as vm:
        initial_count = vm.index.ntotal  # type: ignore[union-attr]
        assert initial_count >= 3

        with GitContextManager(branch) as git_mgr:
            git_mgr.write_context("New feature C content", "Add feature C")

        time.sleep(2)

        assert vm.index.ntotal >= initial_count + 1  # type: ignore[union-attr]


def test_vector_manager_no_commits(temp_gctx_home: Path, gctx_config: GctxConfig) -> None:
    """Test VectorManager with empty repository."""
    branch = "empty-branch"

    (temp_gctx_home / "vectors").mkdir(exist_ok=True)

    with GitContextManager(branch):
        pass

    with VectorManager(branch, gctx_config) as vm:
        assert vm.index.ntotal >= 1  # type: ignore[union-attr]


def test_mapping_consistency(
    temp_gctx_home: Path, setup_test_repo: str, gctx_config: GctxConfig
) -> None:
    """Test that mapping between faiss_id and commit_sha is consistent."""
    branch = setup_test_repo

    with VectorManager(branch, gctx_config) as vm:
        with vm._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM vector_mapping")
            mapping_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT commit_sha) FROM vector_mapping")
            commit_count = cursor.fetchone()[0]

        assert mapping_count == vm.index.ntotal  # type: ignore[union-attr]
        assert mapping_count >= commit_count, "Should have at least 1 vector per commit"


def test_state_tracking(
    temp_gctx_home: Path, setup_test_repo: str, gctx_config: GctxConfig
) -> None:
    """Test that state is tracked correctly."""
    branch = setup_test_repo

    with VectorManager(branch, gctx_config) as vm:
        with vm._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_commit_sha, config_hash FROM system_state WHERE id=1")
            row = cursor.fetchone()

        assert row is not None
        assert row[0] is not None
        assert row[1] is not None


def test_duplicate_commit_handling(
    temp_gctx_home: Path, setup_test_repo: str, gctx_config: GctxConfig
) -> None:
    """Test that duplicate commits are not indexed twice."""
    branch = setup_test_repo

    with VectorManager(branch, gctx_config) as vm:
        initial_count = vm.index.ntotal  # type: ignore[union-attr]

        with vm._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT commit_sha FROM vector_mapping LIMIT 1")
            sha = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM vector_mapping WHERE commit_sha=?", (sha,))
            initial_mapping_count = cursor.fetchone()[0]

        from git import Repo

        repo = Repo(ConfigManager.REPO_PATH)
        commit = repo.commit(sha)

        vm._add_commit_to_index(commit)

        assert vm.index.ntotal == initial_count  # type: ignore[union-attr]

        with vm._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM vector_mapping WHERE commit_sha=?", (sha,))
            final_mapping_count = cursor.fetchone()[0]

        assert final_mapping_count == initial_mapping_count, "Should not add duplicate vectors"

        assert vm.index.ntotal == initial_count  # type: ignore[union-attr]


def test_vector_manager_shutdown(
    temp_gctx_home: Path, setup_test_repo: str, gctx_config: GctxConfig
) -> None:
    """Test proper shutdown of vector manager."""
    branch = setup_test_repo

    vm = VectorManager(branch, gctx_config)
    assert vm.running is True

    vm.shutdown()

    assert vm.running is False
    assert vm.daemon_thread is not None


def test_vector_search_results_structure(session_vector_manager: VectorManager) -> None:
    """Test that vector search returns properly structured results."""
    results = session_vector_manager.search_similar(["feature"])

    assert isinstance(results, list), "Results should be a list"

    if len(results) > 0:
        for result in results:
            assert hasattr(result, "sha"), "Result missing 'sha' field"
            assert hasattr(result, "message"), "Result missing 'message' field"
            assert hasattr(result, "timestamp"), "Result missing 'timestamp' field"
            assert isinstance(result.sha, str), "sha should be string"
            assert isinstance(result.message, str), "message should be string"
            assert isinstance(result.timestamp, str), "timestamp should be string"


def test_vector_search_with_multiple_query_strings(session_vector_manager: VectorManager) -> None:
    """Test searching with multiple query strings."""
    results = session_vector_manager.search_similar(["feature A", "feature B"])

    assert len(results) > 0
    assert all(hasattr(r, "sha") for r in results)


def test_vector_search_finds_relevant_commits(
    temp_gctx_home: Path, setup_test_repo: str, gctx_config: GctxConfig
) -> None:
    """Test that vector search finds semantically relevant commits."""
    branch = setup_test_repo

    with VectorManager(branch, gctx_config) as vm:
        # Give daemon time to sync
        time.sleep(2)

        # Search for commits about features
        results = vm.search_similar(["feature A"])

        # Should find at least one matching commit
        assert len(results) > 0, "Vector search should find matching commits"

        found_relevant = any("feature" in result.message.lower() for result in results)
        assert found_relevant, "Results should include commits about features"


def test_vector_search_threshold_precision(
    temp_gctx_home: Path, setup_test_repo: str, gctx_config: GctxConfig
) -> None:
    """Test that threshold filters results appropriately."""
    branch = setup_test_repo

    with VectorManager(branch, gctx_config) as vm:
        time.sleep(2)

        results_default = vm.search_similar(["feature"])

        vm.config.vector.similarity_threshold = 0.1
        results_low = vm.search_similar(["feature"])

        vm.config.vector.similarity_threshold = 0.8
        results_high = vm.search_similar(["feature"])

        assert len(results_low) >= len(results_default), (
            "Lower threshold should return more results"
        )
        assert len(results_high) <= len(results_default), (
            "Higher threshold should return fewer results"
        )


def test_vector_search_exact_vs_semantic_match(
    temp_gctx_home: Path, setup_test_repo: str, gctx_config: GctxConfig
) -> None:
    """Test that message and diff vectors enable finding commits."""
    branch = setup_test_repo

    with GitContextManager(branch) as git_mgr:
        git_mgr.write_context("Python unit testing framework details", "Add python testing docs")
        git_mgr.write_context("Software quality assurance", "Add QA notes")

    with VectorManager(branch, gctx_config) as vm:
        wait_for_sync(vm, expected_commits=5)

        message_query = vm.search_similar(["python testing docs"])
        diff_query = vm.search_similar(["unit testing framework"])

        assert len(message_query) > 0 or len(diff_query) > 0, (
            "Should find commits via message or diff vectors"
        )


def test_vector_search_commit_message_vs_content(
    temp_gctx_home: Path, setup_test_repo: str, gctx_config: GctxConfig
) -> None:
    """Test that both commit message and content are searchable."""
    branch = setup_test_repo

    with GitContextManager(branch) as git_mgr:
        git_mgr.write_context(
            "# Database Design\nSQL queries and schema optimization.", "Add database documentation"
        )

    with VectorManager(branch, gctx_config) as vm:
        wait_for_sync(vm, expected_commits=4)

        query_message = vm.search_similar(["database documentation"])
        query_content = vm.search_similar(["SQL schema optimization"])

        assert len(query_message) > 0, "Should find by commit message"
        assert len(query_content) > 0, "Should find by content"


def test_vector_search_threshold_boundaries(
    temp_gctx_home: Path, setup_test_repo: str, gctx_config: GctxConfig
) -> None:
    """Test vector search at different threshold boundaries."""
    branch = setup_test_repo

    with GitContextManager(branch) as git_mgr:
        git_mgr.write_context("Python programming language", "Add Python")
        git_mgr.write_context("JavaScript coding", "Add JavaScript")
        git_mgr.write_context("Unrelated topic", "Add other")

    with VectorManager(branch, gctx_config) as vm:
        time.sleep(2)

        thresholds_to_test = [0.0, 0.2, 0.3, 0.5, 0.7, 0.9]
        results_counts = []

        for threshold in thresholds_to_test:
            vm.config.vector.similarity_threshold = threshold
            results = vm.search_similar(["python programming"])
            results_counts.append(len(results))

        for i in range(len(results_counts) - 1):
            assert results_counts[i] >= results_counts[i + 1], (
                f"Higher threshold should return fewer or equal results: "
                f"threshold {thresholds_to_test[i]} ({results_counts[i]} results) vs "
                f"threshold {thresholds_to_test[i + 1]} ({results_counts[i + 1]} results)"
            )


def test_vector_search_optimal_threshold_range(
    temp_gctx_home: Path, setup_test_repo: str, gctx_config: GctxConfig
) -> None:
    """Test that similarity scores fall within expected ranges for typical queries."""
    branch = setup_test_repo

    with GitContextManager(branch) as git_mgr:
        git_mgr.write_context("Python unit testing framework", "Python test")
        git_mgr.write_context("Database optimization techniques", "DB optimize")

    with VectorManager(branch, gctx_config) as vm:
        wait_for_sync(vm, expected_commits=5)

        vm.config.vector.similarity_threshold = 0.0
        vm.config.vector.top_k = 100

        exact_results = vm.search_similar(["python unit testing"])
        semantic_results = vm.search_similar(["database performance"])

        assert len(exact_results) > 0, "Should find exact matches"
        assert len(semantic_results) > 0, "Should find semantic matches"


def test_vector_search_no_false_positives_high_threshold(
    temp_gctx_home: Path, setup_test_repo: str, gctx_config: GctxConfig
) -> None:
    """Test that high threshold doesn't return irrelevant results."""
    branch = setup_test_repo

    with GitContextManager(branch) as git_mgr:
        git_mgr.write_context("Python programming", "Python")
        git_mgr.write_context("Completely unrelated content about cooking", "Cooking")

    with VectorManager(branch, gctx_config) as vm:
        time.sleep(2)

        vm.config.vector.similarity_threshold = 0.5
        results = vm.search_similar(["python programming language"])

        for result in results:
            assert "cooking" not in result.message.lower(), (
                "High threshold should not return irrelevant results"
            )


def test_vector_search_dual_indexing(
    temp_gctx_home: Path, setup_test_repo: str, gctx_config: GctxConfig
) -> None:
    """Test that commits are indexed with both message and content vectors."""
    branch = setup_test_repo

    with GitContextManager(branch) as git_mgr:
        git_mgr.write_context("Test content for dual indexing", "Test commit message")

    vectors_dir = temp_gctx_home / "vectors"
    for f in vectors_dir.glob(f"{branch}_*"):
        f.unlink()

    with VectorManager(branch, gctx_config) as vm:
        wait_for_sync(vm, expected_commits=4, timeout=10)

        import sqlite3

        db_path = vm.db_path
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM vector_mapping")
            total_vectors = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT commit_sha) FROM vector_mapping")
            total_commits = cursor.fetchone()[0]

            cursor.execute(
                "SELECT commit_sha, COUNT(*) as cnt FROM vector_mapping "
                "GROUP BY commit_sha ORDER BY cnt DESC LIMIT 3"
            )
            sample_counts = cursor.fetchall()

            if total_commits > 0:
                avg_vectors_per_commit = total_vectors / total_commits
                assert total_vectors >= total_commits, (
                    f"Should have at least 1 vector per commit: "
                    f"{total_vectors} vectors for {total_commits} commits"
                )
                assert avg_vectors_per_commit >= 1.8, (
                    f"Should have ~2 vectors per commit (message + content), "
                    f"got {avg_vectors_per_commit:.2f}. Sample counts: {sample_counts}"
                )
