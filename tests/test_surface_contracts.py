from __future__ import annotations

import unittest

from knowledge_files import career_corpus_store_surface as store_surface
from knowledge_files import career_corpus_sync_surface as sync_surface
from knowledge_files import memory_validation_surface as validation_surface


class SurfaceContractTests(unittest.TestCase):
    def test_store_surface_exports(self) -> None:
        self.assertEqual(store_surface.__all__, ["CareerCorpusStore"])
        cls = store_surface.CareerCorpusStore
        self.assertTrue(getattr(cls, "__gpt_surface__", False))
        expected_methods = [
            "__init__",
            "load",
            "save",
            "status",
            "snapshot",
            "get",
            "set",
            "update",
            "replace_corpus",
            "build_split_documents",
            "index_referenced_paths",
            "assemble_from_split_documents",
            "list_experiences",
            "upsert_experience",
        ]
        for name in expected_methods:
            self.assertTrue(getattr(getattr(cls, name), "__gpt_surface__", False), name)

    def test_sync_surface_exports(self) -> None:
        self.assertEqual(sync_surface.__all__, ["CareerCorpusSync"])
        cls = sync_surface.CareerCorpusSync
        self.assertTrue(getattr(cls, "__gpt_surface__", False))
        expected_methods = [
            "__init__",
            "bootstrap_memory_repo",
            "pull",
            "pull_if_stale_before_write",
            "push",
            "persist_memory_changes",
        ]
        for name in expected_methods:
            self.assertTrue(getattr(getattr(cls, name), "__gpt_surface__", False), name)

    def test_validation_surface_exports(self) -> None:
        expected = [
            "validate_career_corpus",
            "validate_preferences",
            "validate_career_patch",
            "validate_preferences_patch",
            "assert_validated_before_write",
            "assert_sections_explicitly_approved",
            "assert_validation_claim_allowed",
            "assert_persist_claim_allowed",
            "assert_notes_content_only",
            "should_emit_memory_status",
            "canonical_json_text",
            "canonical_json_sha256",
            "diagnose_payload_integrity",
        ]
        self.assertEqual(validation_surface.__all__, expected)
        for name in expected:
            self.assertTrue(getattr(getattr(validation_surface, name), "__gpt_surface__", False), name)


if __name__ == "__main__":
    unittest.main()
