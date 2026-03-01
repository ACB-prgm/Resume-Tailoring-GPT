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
        pack = build_context(Intent.JD_ANALYSIS, state)
        self.assertTrue(pack.block_current_intent)
        self.assertEqual(
            [route.value for route in pack.required_routes],
            [
                "INTENT_INITIALIZATION_OR_SETUP",
                "INTENT_MEMORY_STATUS",
                "INTENT_ONBOARDING_IMPORT_REPAIR",
            ],
        )
        self.assertEqual(pack.atoms, [])
        self.assertIn("INTENT BLOCKED: INTENT_JD_ANALYSIS", pack.rendered_context)
        self.assertIn("build_context(INTENT_JD_ANALYSIS, state)", pack.rendered_context)

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
        pack = build_context(Intent.RESUME_DRAFTING, state)
        self.assertEqual(pack.required_routes, [Intent.JD_ANALYSIS])

    def test_export_without_approved_markdown_is_blocked(self) -> None:
        """Test that export without approved markdown is blocked."""
        state = RuntimeState(
            repo_exists=True,
            runtime_initialized=True,
            approved_markdown_ready=False,
        )
        pack = build_context(Intent.PDF_EXPORT, state)
        self.assertTrue(pack.block_current_intent)
        self.assertEqual(pack.required_routes, [Intent.RESUME_DRAFTING])

    def test_persist_without_initialization_is_blocked(self) -> None:
        """Test that persist without initialization is blocked."""
        state = RuntimeState(
            repo_exists=False,
            runtime_initialized=False,
            corpus_exists=False,
            corpus_loaded=False,
            corpus_valid=False,
        )
        pack = build_context(Intent.MEMORY_PERSIST_UPDATE, state)
        self.assertTrue(pack.block_current_intent)
        self.assertEqual(
            pack.required_routes,
            [
                Intent.INITIALIZATION_OR_SETUP,
                Intent.MEMORY_STATUS,
                Intent.ONBOARDING_IMPORT_REPAIR,
            ],
        )


if __name__ == "__main__":
    unittest.main()
