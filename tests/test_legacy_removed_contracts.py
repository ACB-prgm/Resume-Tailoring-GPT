from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from knowledge_files.career_corpus_store_core import CareerCorpusStore
from knowledge_files.career_corpus_sync_core import CareerCorpusSync
import knowledge_files.memory_validation_core as validation_core


class LegacyRemovedContractsTests(unittest.TestCase):
    """Test suite for legacy removed contracts."""
    def test_sync_legacy_pull_path_removed(self) -> None:
        """Test that sync legacy pull path removed."""
        self.assertFalse(hasattr(CareerCorpusSync, "_pull_legacy_single_file"))
        self.assertFalse(hasattr(CareerCorpusSync, "_normalize_read_response"))

    def test_store_summary_facts_migration_removed(self) -> None:
        """Test that store summary facts migration removed."""
        self.assertFalse(hasattr(CareerCorpusStore, "_migrate_legacy_summary_facts"))

    def test_store_remote_sha_alias_removed(self) -> None:
        """Test that store remote sha alias removed."""
        with tempfile.TemporaryDirectory() as tmp:
            corpus_path = Path(tmp) / "career_corpus.json"
            meta_path = Path(tmp) / "career_corpus.meta.json"
            corpus_path.write_text("{}", encoding="utf-8")
            store = CareerCorpusStore(path=corpus_path, meta_path=meta_path, validate_on_load=False)
            status = store.status()
            self.assertIn("remote_file_sha", status)
            self.assertNotIn("remote_sha", status)

    def test_validation_legacy_base64_helpers_removed(self) -> None:
        """Test that validation legacy base64 helpers removed."""
        self.assertFalse(hasattr(validation_core, "build_upsert_payload"))
        self.assertFalse(hasattr(validation_core, "verify_base64_roundtrip"))
        self.assertFalse(hasattr(validation_core, "encode_base64_utf8"))
        self.assertFalse(hasattr(validation_core, "decode_base64_utf8"))


if __name__ == "__main__":
    unittest.main()
