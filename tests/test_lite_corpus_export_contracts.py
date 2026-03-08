from __future__ import annotations

from pathlib import Path
import unittest


class LiteCorpusExportContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_instructions_define_downloadable_corpus_output(self) -> None:
        text = (self.repo_root / "instructions.txt").read_text(encoding="utf-8")
        self.assertIn("return updated downloadable `career_corpus.md`", text)
        self.assertIn("Claim save success only after updated `career_corpus.md` has been generated", text)

    def test_onboarding_finalize_outputs_downloadable_corpus(self) -> None:
        text = (self.repo_root / "knowledge_files/OnboardingGuidelines.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Generate and present downloadable `career_corpus.md`", text)
        self.assertIn("State completion only after export succeeds.", text)


if __name__ == "__main__":
    unittest.main()
