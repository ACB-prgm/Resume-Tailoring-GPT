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
        self.assertIn("Use GitHub section files as the active working source", text)
        self.assertIn("Read and write section files directly by intent", text)
        self.assertNotIn("CareerCorpus/corpus.md", text)
        self.assertNotIn("CareerCorpus/metadata.md", text)

    def test_onboarding_uses_section_files(self) -> None:
        text = (self.repo_root / "knowledge_files/OnboardingGuidelines.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("one file per non-empty section", text)
        self.assertIn("Skills are always part of Profile", text)
        self.assertIn("No Metadata section", text)
        self.assertIn("memory is opt-out", text)
        self.assertIn("Default approval behavior is section-by-section review", text)
        self.assertIn("full corpus at once", text)
        self.assertIn("write the complete corpus draft to canvas", text)
        self.assertIn("Push once only after final approval", text)
        self.assertIn("canvas/session draft", text)

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

    def test_initialization_uses_remote_readiness_process(self) -> None:
        text = (self.repo_root / "knowledge_files/InitializationGuidelines.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("remote repo/account readiness and file discovery", text)
        self.assertIn("Read and write section files directly by intent/context", text)
        self.assertNotIn("mirror to /mnt/data/preferences.md", text)


if __name__ == "__main__":
    unittest.main()
