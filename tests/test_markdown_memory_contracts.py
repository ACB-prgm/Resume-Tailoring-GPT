from __future__ import annotations

from pathlib import Path
import unittest


class MarkdownMemoryContractsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_runtime_stack_modules_removed(self) -> None:
        removed = [
            "knowledge_files/career_corpus_store_surface.py",
            "knowledge_files/career_corpus_store_core.py",
            "knowledge_files/career_corpus_sync_surface.py",
            "knowledge_files/career_corpus_sync_core.py",
            "knowledge_files/memory_validation_surface.py",
            "knowledge_files/memory_validation_core.py",
            "knowledge_files/career_corpus.schema.json",
        ]
        for rel in removed:
            self.assertFalse((self.repo_root / rel).exists(), rel)

    def test_memory_persistence_guide_uses_section_files(self) -> None:
        text = (self.repo_root / "knowledge_files/MemoryPersistenceGuidelines.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("CareerCorpus/profile.md", text)
        self.assertIn("CareerCorpus/experience.md", text)
        self.assertIn("CareerCorpus/projects.md", text)
        self.assertIn("CareerCorpus/certifications.md", text)
        self.assertIn("CareerCorpus/education.md", text)
        self.assertIn("preferences.md", text)
        self.assertIn("Do not save empty section files", text)
        self.assertIn("Skills` must be inside `profile.md`", text)
        self.assertNotIn("CareerCorpus/corpus.md", text)
        self.assertNotIn("CareerCorpus/metadata.md", text)

    def test_onboarding_uses_section_files(self) -> None:
        text = (self.repo_root / "knowledge_files/OnboardingGuidelines.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("one file per non-empty section", text)
        self.assertIn("Skills are always part of Profile", text)
        self.assertIn("No Metadata section", text)

    def test_career_corpus_format_exists_and_matches_new_contract(self) -> None:
        path = self.repo_root / "knowledge_files/CareerCorpusFormat.md"
        self.assertTrue(path.exists())
        text = path.read_text(encoding="utf-8")
        self.assertIn("CareerCorpus/profile.md", text)
        self.assertIn("CareerCorpus/experience.md", text)
        self.assertIn("CareerCorpus/projects.md", text)
        self.assertIn("CareerCorpus/certifications.md", text)
        self.assertIn("CareerCorpus/education.md", text)
        self.assertIn("preferences.md", text)
        self.assertIn("Do not save an empty file", text)
        self.assertIn("No `CareerCorpus/metadata.md`", text)
        self.assertNotIn("## Metadata", text)

    def test_initialization_loads_preferences_file_when_present(self) -> None:
        text = (self.repo_root / "knowledge_files/InitializationGuidelines.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("preferences.md", text)
        self.assertIn("/mnt/data/preferences.md", text)


if __name__ == "__main__":
    unittest.main()
