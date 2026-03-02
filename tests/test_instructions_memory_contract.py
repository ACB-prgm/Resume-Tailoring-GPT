from __future__ import annotations

from pathlib import Path
import unittest


class InstructionsMemoryContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]
        self.text = (self.repo_root / "instructions.txt").read_text(encoding="utf-8")

    def test_instructions_define_section_file_read_and_write_flows(self) -> None:
        required_terms = [
            "Direct Memory Read Flow",
            "getAuthenticatedUser",
            "getMemoryRepo",
            "getBranchRef",
            "getGitCommit",
            "getGitTree(recursive=1)",
            "getGitBlob",
            "Direct Memory Write Flow (Section Scoped + Preferences)",
            "createGitBlob",
            "createGitTree",
            "createGitCommit",
            "updateBranchRef",
            "CareerCorpus/profile.md",
            "CareerCorpus/experience.md",
            "CareerCorpus/projects.md",
            "CareerCorpus/certifications.md",
            "CareerCorpus/education.md",
            "preferences.md",
            "/mnt/data/preferences.md",
            "Do not write empty section files",
            "Skills` inside `profile.md`",
            "/mnt/data/CareerCorpusFormat.md",
            "user explicitly states a personal preference",
            "GitHub memory is opt-out (default-on)",
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
