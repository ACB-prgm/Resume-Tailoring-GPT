from __future__ import annotations

import unittest

from knowledge_files.intent_context_router_core import Intent, RuntimeState, build_context


class IntentPreconditionRoutingTests(unittest.TestCase):
    """Test suite for intent precondition routing."""
    def test_jd_first_without_corpus_routes_chain(self) -> None:
        """Test that jd first without corpus routes chain."""
        state = RuntimeState(
            repo_exists=False,
            runtime_initialized=False,
            corpus_exists=False,
            corpus_loaded=False,
            corpus_valid=False,
        )
        pack = build_context(Intent.JD_ANALYSIS, state, verbose=True)
        self.assertFalse(pack.block_current_intent)
        self.assertEqual(pack.intent, Intent.INITIALIZATION_OR_SETUP)
        self.assertEqual(pack.rerouted_to, [Intent.INITIALIZATION_OR_SETUP])

    def test_resume_without_jd_routes_to_jd(self) -> None:
        """Test that resume without jd routes to jd."""
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

    def test_export_without_approved_markdown_is_blocked(self) -> None:
        """Test that export without approved markdown is blocked."""
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

    def test_persist_without_initialization_is_blocked(self) -> None:
        """Test that persist without initialization is blocked."""
        state = RuntimeState(
            repo_exists=False,
            runtime_initialized=False,
            corpus_exists=False,
            corpus_loaded=False,
            corpus_valid=False,
        )
        pack = build_context(Intent.MEMORY_PERSIST_UPDATE, state, verbose=True)
        self.assertFalse(pack.block_current_intent)
        self.assertEqual(pack.intent, Intent.INITIALIZATION_OR_SETUP)
        self.assertEqual(pack.rerouted_to, [Intent.INITIALIZATION_OR_SETUP])


if __name__ == "__main__":
    unittest.main()
