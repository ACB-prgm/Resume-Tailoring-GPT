from __future__ import annotations

from pathlib import Path
import unittest


class InstructionsMemoryContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]
        self.text = (self.repo_root / "instructions.txt").read_text(encoding="utf-8")

    def test_instructions_define_routing_and_memory_contracts(self) -> None:
        required_terms = [
            "Reference Trigger Clauses",
            "Intent Matrix",
            "memory_persist_update",
            "onboarding_import_repair",
            "$Ref: `/mnt/data/MemoryPersistenceGuidelines.md`",
            "$Ref: `/mnt/data/OnboardingGuidelines.md`",
            "$Ref: `/mnt/data/CareerCorpusFormat.md`",
            "github tool call",
            "user explicitly states a personal preference",
            "Approval is required before any memory push.",
            "OnboardingGuidelines.md",
            "getGitBlob` and `createGitBlob`: always use `Accept: application/vnd.github.raw`",
            "All other GitHub memory calls that include `Accept`: use `Accept: application/vnd.github+json`",
            "Keep corpus files under `CareerCorpus/` only; only `preferences.md` is allowed at repo root.",
            "Do not write empty section files.",
            "Never claim persisted success unless `updateBranchRef` succeeds.",
        ]
        for term in required_terms:
            self.assertIn(term, self.text, term)

    def test_instructions_remove_aggregate_and_metadata_file_model(self) -> None:
        forbidden_terms = [
            "CareerCorpus/corpus.md",
            "CareerCorpus/metadata.md",
            "career_corpus_store_surface.py",
            "career_corpus_sync_surface.py",
            "memory_validation_surface.py",
            "career_corpus.schema.json",
            "corpus_index.json",
        ]
        for term in forbidden_terms:
            self.assertNotIn(term, self.text, term)


if __name__ == "__main__":
    unittest.main()
