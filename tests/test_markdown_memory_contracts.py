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

    def test_memory_persistence_guide_is_markdown_only(self) -> None:
        text = (self.repo_root / "knowledge_files/MemoryPersistenceGuidelines.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("CareerCorpus/corpus.md", text)
        self.assertIn("/mnt/data/CareerCorpus/corpus.md", text)
        self.assertNotIn("corpus_index.json", text)
        self.assertNotIn("career_corpus.schema.json", text)
        self.assertNotIn("build_split_documents", text)
        self.assertNotIn("assemble_from_split_documents", text)

    def test_onboarding_uses_single_markdown_corpus_file(self) -> None:
        text = (self.repo_root / "knowledge_files/OnboardingGuidelines.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("CareerCorpus/corpus.md", text)
        self.assertIn("/mnt/data/CareerCorpus/corpus.md", text)
        self.assertIn("onboarding completion", text.lower())


if __name__ == "__main__":
    unittest.main()
