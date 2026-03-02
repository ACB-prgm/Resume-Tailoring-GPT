from __future__ import annotations

from pathlib import Path
import unittest


class InstructionsMemoryContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]
        self.text = (self.repo_root / "instructions.txt").read_text(encoding="utf-8")

    def test_instructions_define_direct_read_and_write_flows(self) -> None:
        required_terms = [
            "Direct Memory Read Flow",
            "getAuthenticatedUser",
            "getMemoryRepo",
            "getBranchRef",
            "getGitCommit",
            "getGitTree(recursive=1)",
            "getGitBlob",
            "Direct Memory Write Flow",
            "createGitBlob",
            "createGitTree",
            "createGitCommit",
            "updateBranchRef",
            "CareerCorpus/corpus.md",
            "/mnt/data/CareerCorpus/corpus.md",
            "/mnt/data/CareerCorpusFormat.md",
            "Update only the targeted section blocks",
        ]
        for term in required_terms:
            self.assertIn(term, self.text, term)

    def test_instructions_remove_legacy_runtime_stack_references(self) -> None:
        forbidden_terms = [
            "career_corpus_store_surface.py",
            "career_corpus_sync_surface.py",
            "memory_validation_surface.py",
            "career_corpus.schema.json",
            "build_split_documents",
            "assemble_from_split_documents",
            "corpus_index.json",
            "validated=true",
        ]
        for term in forbidden_terms:
            self.assertNotIn(term, self.text, term)


if __name__ == "__main__":
    unittest.main()
