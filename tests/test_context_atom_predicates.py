from __future__ import annotations

import unittest

from knowledge_files.intent_context_router_core import Intent, RuntimeState, build_context


class ContextAtomPredicatesTests(unittest.TestCase):
    """Test suite for context atom predicates."""
    def test_jd_requires_preflight_when_state_missing(self) -> None:
        """Test that jd requires preflight when state missing."""
        pack = build_context(Intent.JD_ANALYSIS, RuntimeState(), verbose=True)
        self.assertFalse(pack.block_current_intent)
        self.assertEqual(pack.intent, Intent.INITIALIZATION_OR_SETUP)
        self.assertEqual(pack.rerouted_to, [Intent.INITIALIZATION_OR_SETUP])

    def test_jd_unblocked_when_corpus_ready(self) -> None:
        """Test that jd unblocked when corpus ready."""
        state = RuntimeState(
            repo_exists=True,
            runtime_initialized=True,
            corpus_exists=True,
            corpus_loaded=True,
            corpus_valid=True,
        )
        pack = build_context(Intent.JD_ANALYSIS, state, verbose=True)
        self.assertFalse(pack.block_current_intent)
        self.assertEqual(pack.required_routes, [])
        self.assertEqual(pack.rerouted_to, [])
        self.assertEqual(pack.intent, Intent.JD_ANALYSIS)

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
        pack = build_context(Intent.RESUME_DRAFTING, state, verbose=True)
        self.assertFalse(pack.block_current_intent)
        self.assertEqual(pack.intent, Intent.JD_ANALYSIS)
        self.assertEqual(pack.rerouted_to, [Intent.JD_ANALYSIS])

    def test_pdf_requires_approved_markdown(self) -> None:
        """Test that pdf requires approved markdown."""
        state = RuntimeState(
            repo_exists=True,
            runtime_initialized=True,
            corpus_exists=True,
            corpus_loaded=True,
            corpus_valid=True,
            last_jd_analysis_present=True,
            approved_markdown_ready=False,
        )
        pack = build_context(Intent.PDF_EXPORT, state, verbose=True)
        self.assertFalse(pack.block_current_intent)
        self.assertEqual(pack.intent, Intent.RESUME_DRAFTING)
        self.assertEqual(pack.rerouted_to, [Intent.RESUME_DRAFTING])


if __name__ == "__main__":
    unittest.main()
