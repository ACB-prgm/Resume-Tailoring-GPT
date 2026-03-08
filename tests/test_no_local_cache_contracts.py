from __future__ import annotations

from pathlib import Path
import unittest


class SessionMemoryContractsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_uat_contains_session_status_block(self) -> None:
        text = (self.repo_root / "knowledge_files/UATGuardrails.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("MEMORY STATUS", text)
        self.assertIn("corpus_uploaded", text)
        self.assertIn("corpus_source", text)
        self.assertIn("last_uploaded", text)
        self.assertIn("last_exported", text)

    def test_docs_do_not_contain_legacy_action_flow_terms(self) -> None:
        files = [
            "knowledge_files/InitializationGuidelines.md",
            "knowledge_files/OnboardingGuidelines.md",
            "knowledge_files/UATGuardrails.md",
            "knowledge_files/CareerCorpusFormat.md",
            "instructions.txt",
        ]
        combined = "\n".join(
            (self.repo_root / rel).read_text(encoding="utf-8") for rel in files
        ).lower()
        forbidden = [
            "getgit",
            "creategit",
            "updatebranchref",
            "career-corpus-memory",
            "preferences.md",
            "careercorpus/",
        ]
        for term in forbidden:
            self.assertNotIn(term, combined, term)


if __name__ == "__main__":
    unittest.main()
