from __future__ import annotations

import unittest

from knowledge_files.intent_context_router_core import Intent, RuntimeState, build_context


class ContextAtomPredicatesTests(unittest.TestCase):
    """Test suite for context atom predicates."""
    def test_jd_requires_preflight_when_state_missing(self) -> None:
        """Test that jd requires preflight when state missing."""
        pack = build_context(Intent.JD_ANALYSIS, RuntimeState())
        self.assertTrue(pack.block_current_intent)
        self.assertEqual(pack.atoms, [])
        self.assertTrue(pack.diagnostics.get("blocked_mode"))
        self.assertEqual(
            pack.required_routes,
            [
                Intent.INITIALIZATION_OR_SETUP,
                Intent.MEMORY_STATUS,
                Intent.ONBOARDING_IMPORT_REPAIR,
            ],
        )

    def test_jd_unblocked_when_corpus_ready(self) -> None:
        """Test that jd unblocked when corpus ready."""
        state = RuntimeState(
            repo_exists=True,
            runtime_initialized=True,
            corpus_exists=True,
            corpus_loaded=True,
            corpus_valid=True,
        )
        pack = build_context(Intent.JD_ANALYSIS, state)
        self.assertFalse(pack.block_current_intent)
        self.assertEqual(pack.required_routes, [])

    def test_resume_requires_jd_when_missing(self) -> None:
        """Test that resume requires jd when missing."""
        state = RuntimeState(
            repo_exists=True,
            runtime_initialized=True,
            corpus_exists=True,
            corpus_loaded=True,
            corpus_valid=True,
            last_jd_analysis_present=False,
        )
        pack = build_context(Intent.RESUME_DRAFTING, state)
        self.assertTrue(pack.block_current_intent)
        self.assertEqual(pack.required_routes, [Intent.JD_ANALYSIS])

    def test_pdf_requires_approved_markdown(self) -> None:
        """Test that pdf requires approved markdown."""
        state = RuntimeState(approved_markdown_ready=False)
        pack = build_context(Intent.PDF_EXPORT, state)
        self.assertTrue(pack.block_current_intent)
        self.assertEqual(pack.required_routes, [Intent.RESUME_DRAFTING])


if __name__ == "__main__":
    unittest.main()
