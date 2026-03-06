from __future__ import annotations

from pathlib import Path
import unittest


class NoLocalCacheContractsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_memory_state_model_has_no_loaded_booleans(self) -> None:
        text = (self.repo_root / "knowledge_files/MemoryStateModel.md").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("corpus_loaded", text)
        self.assertNotIn("preferences_loaded", text)
        self.assertIn("last_remote_read_utc", text)

    def test_docs_do_not_require_local_mirror(self) -> None:
        files = [
            "knowledge_files/MemoryPersistenceGuidelines.md",
            "knowledge_files/InitializationGuidelines.md",
            "knowledge_files/OnboardingGuidelines.md",
            "knowledge_files/UATGuardrails.md",
        ]
        combined = "\n".join(
            (self.repo_root / rel).read_text(encoding="utf-8") for rel in files
        )
        self.assertNotIn("Local mirror path prefix", combined)
        self.assertNotIn("mirror changed section files locally", combined)
        self.assertNotIn("mirror updated corpus files under", combined)
        self.assertNotIn("stage approved sections locally", combined)
        self.assertIn("GitHub section files", combined)

    def test_direct_section_contract_present(self) -> None:
        text = (self.repo_root / "knowledge_files/MemoryPersistenceGuidelines.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Read and write section files directly", text)


if __name__ == "__main__":
    unittest.main()
