from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict

from career_corpus_store import CareerCorpusStore
from career_corpus_sync import CareerCorpusSync

try:
    from memory_validation import encode_base64_utf8
except ImportError:
    from knowledge_files.memory_validation import encode_base64_utf8  # type: ignore


def make_corpus(with_ids: bool = True) -> Dict[str, Any]:
    exp = {
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
    proj = {
        "name": "ERP Rollout",
        "role": "Lead Analyst",
        "stack": ["SQL", "Power BI"],
        "outcomes": ["Improved reporting accuracy."],
    }
    cert = {
        "name": "Cert A",
        "issuer": "Issuer A",
        "status": "active",
    }
    edu = {
        "degree": "BS",
        "institution": "State U",
        "graduation_year": 2015,
    }
    if with_ids:
        exp["id"] = "exp_existing"
        proj["id"] = "proj_existing"
        cert["id"] = "cert_existing"
        edu["id"] = "edu_existing"

    return {
        "schema_version": "1.0.0",
        "profile": {"full_name": "Test User"},
        "summary_facts": ["Fact 1"],
        "experience": [exp],
        "projects": [proj],
        "skills": {
            "technical": ["Python"],
            "platforms": ["Azure"],
            "methods": ["Agile"],
            "domains": ["Enterprise IT"],
        },
        "certifications": [cert],
        "education": [edu],
        "metadata": {
            "last_updated_utc": "2026-01-01T00:00:00Z",
            "source": "manual_import",
        },
    }


class CareerCorpusMemoryTests(unittest.TestCase):
    def setUp(self) -> None:
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
        self.tempdir.cleanup()

    def _write_corpus(self, with_ids: bool = True) -> Dict[str, Any]:
        corpus = make_corpus(with_ids=with_ids)
        self.corpus_path.write_text(json.dumps(corpus), encoding="utf-8")
        return corpus

    def _store(self) -> CareerCorpusStore:
        return CareerCorpusStore(
            path=self.corpus_path,
            meta_path=self.meta_path,
            schema_path=self.schema_path,
            validate_on_load=True,
            validate_on_save=True,
        )

    def test_load_save_atomicity(self) -> None:
        self._write_corpus(with_ids=True)
        store = self._store()
        store.load()
        store.set(["profile", "full_name"], "Updated User")
        self.assertTrue(store.dirty)
        store.save()
        self.assertFalse(store.dirty)
        reloaded = json.loads(self.corpus_path.read_text(encoding="utf-8"))
        self.assertEqual(reloaded["profile"]["full_name"], "Updated User")
        tmp_path = self.corpus_path.with_name(f".{self.corpus_path.name}.tmp")
        self.assertFalse(tmp_path.exists())

    def test_id_assignment_on_load(self) -> None:
        self._write_corpus(with_ids=False)
        store = self._store()
        loaded = store.load()
        self.assertTrue(store.dirty)
        self.assertIn("id", loaded["experience"][0])
        self.assertIn("id", loaded["projects"][0])
        self.assertIn("id", loaded["certifications"][0])
        self.assertIn("id", loaded["education"][0])

    def test_upsert_experience_semantics(self) -> None:
        self._write_corpus(with_ids=True)
        store = self._store()
        corpus = store.load()
        existing = corpus["experience"][0]

        # Upsert by id should update in place.
        updated = dict(existing)
        updated["outcomes"] = ["Updated outcome"]
        returned_id = store.upsert_experience(updated)
        self.assertEqual(returned_id, existing["id"])
        self.assertEqual(len(store.list_experiences()), 1)
        self.assertEqual(store.list_experiences()[0]["outcomes"], ["Updated outcome"])

        # Upsert by fallback keys should also update in place.
        fallback_update = {
            "employer": existing["employer"],
            "title": existing["title"],
            "start_date": existing["start_date"],
            "end_date": existing["end_date"],
            "location": existing["location"],
            "bullets": ["Changed by fallback"],
            "tools": existing["tools"],
            "outcomes": existing["outcomes"],
            "domain_tags": existing["domain_tags"],
        }
        store.upsert_experience(fallback_update)
        self.assertEqual(len(store.list_experiences()), 1)
        self.assertEqual(store.list_experiences()[0]["bullets"], ["Changed by fallback"])

    def test_pull_noop_when_sha_unchanged(self) -> None:
        corpus = self._write_corpus(with_ids=True)
        store = self._store()
        store.load()
        store.mark_push_success("sha_123")

        read_calls = {"count": 0}

        def read_remote() -> Dict[str, Any]:
            read_calls["count"] += 1
            return {
                "sha": "sha_123",
                "content": encode_base64_utf8(json.dumps(corpus, sort_keys=True)),
            }

        def upsert_remote(_: Dict[str, Any]) -> Dict[str, Any]:
            raise AssertionError("upsert should not be called in pull no-op test")

        sync = CareerCorpusSync(store=store, read_remote=read_remote, upsert_remote=upsert_remote)
        result = sync.pull()
        self.assertTrue(result["ok"])
        self.assertFalse(result["changed"])
        self.assertEqual(result["reason"], "sha_unchanged")
        self.assertEqual(read_calls["count"], 1)

    def test_push_only_when_dirty(self) -> None:
        self._write_corpus(with_ids=True)
        store = self._store()
        store.load()

        upsert_calls = {"count": 0}

        def read_remote() -> Dict[str, Any]:
            return {"status_code": 404}

        def upsert_remote(payload: Dict[str, Any]) -> Dict[str, Any]:
            upsert_calls["count"] += 1
            self.assertIn("content", payload)
            return {"content": {"sha": "sha_new"}}

        sync = CareerCorpusSync(store=store, read_remote=read_remote, upsert_remote=upsert_remote)
        no_push = sync.push("No changes")
        self.assertFalse(no_push["pushed"])
        self.assertEqual(upsert_calls["count"], 0)

        store.set(["profile", "full_name"], "Dirty User")
        pushed = sync.push("Push changes")
        self.assertTrue(pushed["pushed"])
        self.assertEqual(upsert_calls["count"], 1)


if __name__ == "__main__":
    unittest.main()
