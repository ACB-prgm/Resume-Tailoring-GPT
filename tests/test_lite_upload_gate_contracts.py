from __future__ import annotations

from pathlib import Path
import unittest


class LiteUploadGateContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_instructions_hard_gate_jd_and_resume_without_upload(self) -> None:
        text = (self.repo_root / "instructions.txt").read_text(encoding="utf-8")
        self.assertIn("Do not perform `jd_analysis` or `resume_drafting` until `career_corpus.md` is uploaded", text)
        self.assertIn("If corpus is missing, ask for upload and stop that workflow.", text)

    def test_jd_guidelines_define_preflight_gate(self) -> None:
        text = (self.repo_root / "knowledge_files/JDAnalysisGuidelines.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Preflight gate (required)", text)
        self.assertIn("If missing, request upload and stop.", text)

    def test_resume_guidelines_define_preflight_gate(self) -> None:
        text = (self.repo_root / "knowledge_files/ResumeBuildingGuidelines.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Preflight gate (required)", text)
        self.assertIn("If missing, request upload and stop.", text)


if __name__ == "__main__":
    unittest.main()
