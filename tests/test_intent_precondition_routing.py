from __future__ import annotations

import unittest

from knowledge_files.intent_context_router_core import Intent, RuntimeState, build_context


class IntentPreconditionRoutingTests(unittest.TestCase):
    def test_jd_first_without_corpus_routes_chain(self) -> None:
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
                "intent_initialization_or_setup",
                "intent_memory_status",
                "intent_onboarding_import_repair",
            ],
        )

    def test_resume_without_jd_routes_to_jd(self) -> None:
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
        state = RuntimeState(
            repo_exists=True,
            runtime_initialized=True,
            approved_markdown_ready=False,
        )
        pack = build_context(Intent.PDF_EXPORT, state)
        self.assertTrue(pack.block_current_intent)
        self.assertEqual(pack.required_routes, [Intent.RESUME_DRAFTING])

    def test_persist_without_initialization_is_blocked(self) -> None:
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
