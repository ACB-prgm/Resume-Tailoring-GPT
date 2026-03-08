from __future__ import annotations

from pathlib import Path
import unittest


class MarkdownMemoryContractsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_legacy_memory_files_removed(self) -> None:
        removed = [
            "github_action_schema.json",
            "knowledge_files/MemoryPersistenceGuidelines.md",
            "knowledge_files/MemoryStateModel.md",
        ]
        for rel in removed:
            self.assertFalse((self.repo_root / rel).exists(), rel)

    def test_onboarding_and_init_use_upload_download_model(self) -> None:
        onboarding = (self.repo_root / "knowledge_files/OnboardingGuidelines.md").read_text(
            encoding="utf-8"
        )
        init = (self.repo_root / "knowledge_files/InitializationGuidelines.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("downloadable `career_corpus.md`", onboarding)
        self.assertIn("section-by-section", onboarding)
        self.assertIn("full corpus", onboarding)
        self.assertIn("request `career_corpus.md` upload", init)
        self.assertNotIn("github", onboarding.lower())
        self.assertNotIn("github", init.lower())
        self.assertNotIn("commit", onboarding.lower())
        self.assertNotIn("push", onboarding.lower())

    def test_career_corpus_format_is_single_file_numbered_sections(self) -> None:
        text = (self.repo_root / "knowledge_files/CareerCorpusFormat.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("single corpus file: `career_corpus.md`", text)
        self.assertIn("1. Profile", text)
        self.assertIn("2. Experience", text)
        self.assertIn("3. Projects", text)
        self.assertIn("4. Certifications", text)
        self.assertIn("5. Education", text)
        self.assertIn("6. Preferences (optional)", text)
        self.assertNotIn("CareerCorpus/", text)
        self.assertNotIn("preferences.md", text)


if __name__ == "__main__":
    unittest.main()
