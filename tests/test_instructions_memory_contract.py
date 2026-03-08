from __future__ import annotations

from pathlib import Path
import unittest


class InstructionsMemoryContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]
        self.text = (self.repo_root / "instructions.txt").read_text(encoding="utf-8")

    def test_instructions_define_lite_memory_contracts(self) -> None:
        required_terms = [
            "Intent Matrix",
            "memory_persist_update",
            "onboarding_import_repair",
            "$Ref: `/mnt/data/OnboardingGuidelines.md`",
            "$Ref: `/mnt/data/CareerCorpusFormat.md`",
            "$Ref: `/mnt/data/UATGuardrails.md`",
            "career_corpus.md",
            "Do not perform `jd_analysis` or `resume_drafting` until `career_corpus.md` is uploaded",
            "If corpus is missing, ask for upload and stop that workflow.",
            "Never claim remote persistence or background save success.",
            "Claim save success only after updated `career_corpus.md` has been generated and presented for download.",
        ]
        for term in required_terms:
            self.assertIn(term, self.text, term)

    def test_instructions_remove_legacy_action_language(self) -> None:
        forbidden_terms = [
            "github tool call",
            "getGitBlob",
            "createGitBlob",
            "updateBranchRef",
            "career-corpus-memory",
            "CareerCorpus/",
            "preferences.md",
            "MemoryPersistenceGuidelines.md",
            "MemoryStateModel.md",
        ]
        for term in forbidden_terms:
            self.assertNotIn(term, self.text, term)


if __name__ == "__main__":
    unittest.main()
