from __future__ import annotations

import base64
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

from knowledge_files.career_corpus_store_surface import CareerCorpusStore
from knowledge_files.career_corpus_sync_surface import CareerCorpusSync
from knowledge_files.memory_validation_surface import canonical_json_sha256, canonical_json_text


def _encode_base64_utf8(text: str) -> str:
    """Internal helper to encode base64 utf8."""
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def make_corpus() -> Dict[str, Any]:
    """Make corpus."""
    return {
        "schema_version": "1.0.0",
        "profile": {
            "full_name": "Test User",
            "skills": {
                "technical": ["Python"],
                "platforms": ["Azure"],
                "methods": ["Agile"],
                "domains": ["Enterprise IT"],
            },
        },
        "experience": [
            {
                "id": "exp_existing",
                "employer": "Acme Corp",
                "title": "Systems Analyst",
                "start_date": "2020-01",
                "end_date": None,
                "location": "Remote",
                "bullets": ["Built integrations."],
                "tools": ["Python"],
                "outcomes": ["Reduced cycle time."],
                "domain_tags": ["integration"],
            }
        ],
        "projects": [
            {
                "id": "proj_existing",
                "name": "ERP Rollout",
                "role": "Lead Analyst",
                "stack": ["SQL", "Power BI"],
                "outcomes": ["Improved reporting accuracy."],
            }
        ],
        "certifications": [
            {
                "id": "cert_existing",
                "name": "Cert A",
                "issuer": "Issuer A",
                "status": "active",
            }
        ],
        "education": [
            {
                "id": "edu_existing",
                "degree": "BS",
                "institution": "State U",
                "graduation_year": 2015,
            }
        ],
        "metadata": {
            "last_updated_utc": "2026-01-01T00:00:00Z",
            "source": "manual_import",
        },
    }


class FakeGitRepo:
    """Fake Git Repo."""
    def __init__(self, split_docs: Dict[str, Dict[str, Any]]) -> None:
        """Internal helper to init."""
        self.default_branch = "main"
        self.calls = {
            "get_memory_repo": 0,
            "get_branch_ref": 0,
            "get_git_commit": 0,
            "get_git_tree": 0,
            "get_git_blob": 0,
            "create_git_blob": 0,
            "create_git_tree": 0,
            "create_git_commit": 0,
            "update_branch_ref": 0,
        }
        self._blob_counter = 0
        self._tree_counter = 0
        self._commit_counter = 0
        self._blobs: Dict[str, str] = {}
        self._trees: Dict[str, Dict[str, str]] = {}
        self._commits: Dict[str, str] = {}
        self._head_commit: str = ""

        initial_path_map: Dict[str, str] = {}
        for path, doc in split_docs.items():
            sha = self._new_blob(canonical_json_text(doc))
            initial_path_map[path] = sha
        tree_sha = self._new_tree(initial_path_map)
        self._head_commit = self._new_commit(tree_sha)

    def head_path_map(self) -> Dict[str, str]:
        """Head path map."""
        tree_sha = self._commits[self._head_commit]
        return deepcopy(self._trees[tree_sha])

    def get_memory_repo(self) -> Dict[str, Any]:
        """Get memory repo."""
        self.calls["get_memory_repo"] += 1
        return {"default_branch": self.default_branch}

    def get_branch_ref(self, branch: str) -> Dict[str, Any]:
        """Get branch ref."""
        self.calls["get_branch_ref"] += 1
        if branch != self.default_branch:
            return {"status_code": 404}
        return {"object": {"sha": self._head_commit}}

    def get_git_commit(self, commit_sha: str) -> Dict[str, Any]:
        """Get git commit."""
        self.calls["get_git_commit"] += 1
        tree_sha = self._commits.get(commit_sha)
        if not tree_sha:
            return {"status_code": 404}
        return {"tree": {"sha": tree_sha}}

    def get_git_tree(self, tree_sha: str, recursive: bool) -> Dict[str, Any]:
        """Get git tree."""
        self.calls["get_git_tree"] += 1
        path_map = self._trees.get(tree_sha)
        if path_map is None:
            return {"status_code": 404}
        entries = [{"path": p, "type": "blob", "sha": s} for p, s in sorted(path_map.items())]
        return {"sha": tree_sha, "tree": entries, "truncated": False, "recursive": recursive}

    def get_git_blob(self, blob_sha: str) -> Dict[str, Any]:
        """Get git blob."""
        self.calls["get_git_blob"] += 1
        text = self._blobs.get(blob_sha)
        if text is None:
            return {"status_code": 404}
        return {"sha": blob_sha, "encoding": "base64", "content": _encode_base64_utf8(text)}

    def create_git_blob(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create git blob."""
        self.calls["create_git_blob"] += 1
        if payload.get("encoding") != "utf-8":
            return {"status_code": 422}
        content = payload.get("content")
        if not isinstance(content, str):
            return {"status_code": 422}
        sha = self._new_blob(content)
        return {"sha": sha}

    def create_git_tree(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create git tree."""
        self.calls["create_git_tree"] += 1
        base_tree = payload.get("base_tree")
        tree_entries = payload.get("tree")
        if not isinstance(base_tree, str) or not isinstance(tree_entries, list):
            return {"status_code": 422}
        base_map = deepcopy(self._trees.get(base_tree, {}))
        for entry in tree_entries:
            path = entry.get("path")
            sha = entry.get("sha")
            if not isinstance(path, str):
                continue
            if sha is None:
                base_map.pop(path, None)
            elif isinstance(sha, str):
                base_map[path] = sha
            else:
                return {"status_code": 422}
        new_tree_sha = self._new_tree(base_map)
        return {"sha": new_tree_sha}

    def create_git_commit(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create git commit."""
        self.calls["create_git_commit"] += 1
        tree_sha = payload.get("tree")
        if not isinstance(tree_sha, str) or tree_sha not in self._trees:
            return {"status_code": 422}
        new_commit_sha = self._new_commit(tree_sha)
        return {"sha": new_commit_sha}

    def update_branch_ref(self, branch: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update branch ref."""
        self.calls["update_branch_ref"] += 1
        if branch != self.default_branch:
            return {"status_code": 404}
        commit_sha = payload.get("sha")
        if not isinstance(commit_sha, str) or commit_sha not in self._commits:
            return {"status_code": 422}
        self._head_commit = commit_sha
        return {"object": {"sha": commit_sha}}

    def _new_blob(self, content: str) -> str:
        """Internal helper to new blob."""
        self._blob_counter += 1
        sha = f"blob_{self._blob_counter}"
        self._blobs[sha] = content
        return sha

    def _new_tree(self, path_map: Dict[str, str]) -> str:
        """Internal helper to new tree."""
        self._tree_counter += 1
        sha = f"tree_{self._tree_counter}"
        self._trees[sha] = deepcopy(path_map)
        return sha

    def _new_commit(self, tree_sha: str) -> str:
        """Internal helper to new commit."""
        self._commit_counter += 1
        sha = f"commit_{self._commit_counter}"
        self._commits[sha] = tree_sha
        return sha


class CanonicalLayoutContractsTests(unittest.TestCase):
    """Test suite for canonical layout contracts."""
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.corpus_path = root / "career_corpus.json"
        self.meta_path = root / "career_corpus.meta.json"
        self.schema_path = (
            Path(__file__).resolve().parents[1]
            / "knowledge_files"
            / "career_corpus.schema.json"
        )

    def tearDown(self) -> None:
        """Teardown."""
        self.tempdir.cleanup()

    def _write_corpus(self) -> Dict[str, Any]:
        """Internal helper to write corpus."""
        corpus = make_corpus()
        self.corpus_path.write_text(json.dumps(corpus), encoding="utf-8")
        return corpus

    def _store(self) -> CareerCorpusStore:
        """Internal helper to store."""
        return CareerCorpusStore(
            path=self.corpus_path,
            meta_path=self.meta_path,
            schema_path=self.schema_path,
            validate_on_load=True,
            validate_on_save=True,
        )

    def _sync_with_repo(self, store: CareerCorpusStore, repo: FakeGitRepo) -> CareerCorpusSync:
        """Internal helper to sync with repo."""
        return CareerCorpusSync(
            store=store,
            get_memory_repo=repo.get_memory_repo,
            get_branch_ref=repo.get_branch_ref,
            get_git_commit=repo.get_git_commit,
            get_git_tree=repo.get_git_tree,
            get_git_blob=repo.get_git_blob,
            create_git_blob=repo.create_git_blob,
            create_git_tree=repo.create_git_tree,
            create_git_commit=repo.create_git_commit,
            update_branch_ref=repo.update_branch_ref,
            max_retries=1,
        )

    def _build_legacy_root_split_docs(self, corpus: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Internal helper to build legacy root split docs."""
        docs: Dict[str, Dict[str, Any]] = {
            "corpus_profile.json": {"profile": deepcopy(corpus["profile"])},
            "corpus_certifications.json": {"certifications": deepcopy(corpus["certifications"])},
            "corpus_education.json": {"education": deepcopy(corpus["education"])},
            "corpus_metadata.json": {"metadata": deepcopy(corpus["metadata"])},
        }

        experience_files = []
        for exp in corpus.get("experience", []):
            path = f"corpus_experience_{exp['id']}.json"
            docs[path] = {"experience": deepcopy(exp)}
            experience_files.append({"id": exp["id"], "path": path})

        project_files = []
        for proj in corpus.get("projects", []):
            path = f"corpus_project_{proj['id']}.json"
            docs[path] = {"project": deepcopy(proj)}
            project_files.append({"id": proj["id"], "path": path})

        docs["corpus_index.json"] = {
            "format_version": "1.0.0",
            "schema_version": corpus["schema_version"],
            "generated_at_utc": "2026-01-01T00:00:00Z",
            "core_files": {
                "profile": "corpus_profile.json",
                "certifications": "corpus_certifications.json",
                "education": "corpus_education.json",
                "metadata": "corpus_metadata.json",
            },
            "experience_files": experience_files,
            "project_files": project_files,
            "file_hashes": {
                path: canonical_json_sha256(doc)
                for path, doc in docs.items()
                if path != "corpus_index.json"
            },
        }
        return docs

    def test_store_builds_canonical_prefixed_split_paths(self) -> None:
        """Test that store builds canonical prefixed split paths."""
        corpus = self._write_corpus()
        corpus["experience"].append(
            {
                "id": "exp_second",
                "employer": "Second Co",
                "title": "Analyst",
                "start_date": "2021-01",
                "end_date": "2022-01",
                "location": "Remote",
                "bullets": ["Delivered reporting features."],
                "tools": ["SQL"],
                "outcomes": ["Improved visibility."],
                "domain_tags": ["analytics"],
            }
        )
        corpus["projects"].append(
            {
                "id": "proj_second",
                "name": "Data Migration",
                "role": "Engineer",
                "stack": ["Python"],
                "outcomes": ["Migrated legacy data."],
            }
        )
        self.corpus_path.write_text(json.dumps(corpus), encoding="utf-8")

        store = self._store()
        store.load()
        docs = store.build_split_documents()

        self.assertIn(CareerCorpusStore.INDEX_FILE, docs)
        self.assertTrue(all(path.startswith(f"{CareerCorpusStore.REMOTE_DIR}/") for path in docs.keys()))

        experience_paths = [
            path for path in docs.keys() if path.startswith(CareerCorpusStore.EXPERIENCE_FILE_PREFIX)
        ]
        project_paths = [
            path for path in docs.keys() if path.startswith(CareerCorpusStore.PROJECT_FILE_PREFIX)
        ]
        self.assertEqual(len(experience_paths), len(corpus["experience"]))
        self.assertEqual(len(project_paths), len(corpus["projects"]))

    def test_push_rejects_noncanonical_layout_preflight(self) -> None:
        """Test that push rejects noncanonical layout preflight."""
        self._write_corpus()
        store = self._store()
        store.load()
        repo = FakeGitRepo(store.build_split_documents())
        sync = self._sync_with_repo(store, repo)

        baseline = sync.pull(force=True)
        self.assertTrue(baseline["ok"])

        store.set(["profile", "full_name"], "Dirty User")
        original = store._core_store.build_split_documents
        store._core_store.build_split_documents = lambda: {"career_corpus.json": {"bad": True}}  # type: ignore[assignment]
        try:
            result = sync.push("Bad layout")
        finally:
            store._core_store.build_split_documents = original  # type: ignore[assignment]

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "canonical_layout_violation")
        self.assertEqual(repo.calls["create_git_blob"], 0)

    def test_pull_fails_when_only_legacy_root_manifest_exists(self) -> None:
        """Test that pull fails when only legacy root manifest exists."""
        corpus = self._write_corpus()
        store = self._store()
        store.load()

        legacy_docs = self._build_legacy_root_split_docs(corpus)
        repo = FakeGitRepo(legacy_docs)
        sync = self._sync_with_repo(store, repo)

        result = sync.pull(force=True)
        self.assertFalse(result["ok"])
        self.assertEqual(result["error_code"], "canonical_layout_missing")
        self.assertIn(CareerCorpusStore.INDEX_FILE, result["reason"])

    def test_push_writes_only_canonical_directory_paths(self) -> None:
        """Test that push writes only canonical directory paths."""
        self._write_corpus()
        store = self._store()
        store.load()
        repo = FakeGitRepo(store.build_split_documents())
        sync = self._sync_with_repo(store, repo)

        baseline = sync.pull(force=True)
        self.assertTrue(baseline["ok"])

        store.set(["profile", "full_name"], "Updated Name")
        result = sync.push("Canonical path push")
        self.assertTrue(result["ok"])
        self.assertTrue(result["persisted"])

        remote_paths = repo.head_path_map().keys()
        self.assertTrue(all(path.startswith(f"{CareerCorpusStore.REMOTE_DIR}/") for path in remote_paths))

    def test_action_schema_restricts_git_tree_paths_to_canonical_dir(self) -> None:
        """Test that action schema restricts git tree paths to canonical dir."""
        schema_path = Path(__file__).resolve().parents[1] / "github_action_schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        path_schema = (
            schema["components"]["schemas"]["CreateGitTreeRequest"]["properties"]["tree"]["items"]["properties"]["path"]
        )
        self.assertEqual(path_schema["pattern"], "^CareerCorpus\\/.*\\.json$")


if __name__ == "__main__":
    unittest.main()
