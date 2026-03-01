from __future__ import annotations

import unittest

from knowledge_files import intent_context_router_surface as router_surface
from knowledge_files.intent_context_router_core import Intent, RuntimeState


class IntentContextRouterContractsTests(unittest.TestCase):
    def test_surface_exports(self) -> None:
        expected = [
            "Intent",
            "RuntimeState",
            "ContextAtom",
            "ContextPack",
            "resolve_intent",
            "build_context",
        ]
        self.assertEqual(router_surface.__all__, expected)
        self.assertTrue(getattr(router_surface.Intent, "__gpt_surface__", False))
        self.assertTrue(getattr(router_surface.RuntimeState, "__gpt_surface__", False))
        self.assertTrue(getattr(router_surface.ContextAtom, "__gpt_surface__", False))
        self.assertTrue(getattr(router_surface.ContextPack, "__gpt_surface__", False))
        self.assertTrue(getattr(router_surface.resolve_intent, "__gpt_surface__", False))
        self.assertTrue(getattr(router_surface.build_context, "__gpt_surface__", False))

    def test_deterministic_ordering(self) -> None:
        state = RuntimeState(
            repo_exists=True,
            runtime_initialized=True,
            corpus_exists=True,
            corpus_loaded=True,
            corpus_valid=True,
            user_requested_memory_status=True,
        )
        first = router_surface.build_context(Intent.MEMORY_STATUS, state)
        second = router_surface.build_context(Intent.MEMORY_STATUS, state)
        self.assertEqual([atom.id for atom in first.atoms], [atom.id for atom in second.atoms])
        self.assertEqual(first.rendered_context, second.rendered_context)

    def test_restrictive_conflict_resolution(self) -> None:
        state = RuntimeState(
            repo_exists=True,
            runtime_initialized=True,
            corpus_exists=True,
            corpus_loaded=True,
            corpus_valid=True,
            user_requested_memory_status=True,
        )
        pack = router_surface.build_context(Intent.MEMORY_STATUS, state)
        atom_ids = [atom.id for atom in pack.atoms]

        self.assertIn("memory_status.state_block", atom_ids)
        self.assertNotIn("persist.status_visibility", atom_ids)
        self.assertNotIn("state.memory_status_only_when_relevant", atom_ids)
        self.assertIn("persist.status_visibility", pack.diagnostics["filtered_ids"]["conflict"])

    def test_intent_resolution_priority(self) -> None:
        intent = router_surface.resolve_intent("export pdf and save to memory")
        self.assertEqual(intent, Intent.PDF_EXPORT)

    def test_shadow_diagnostics_present(self) -> None:
        state = RuntimeState()
        pack = router_surface.build_context(Intent.JD_ANALYSIS, state)
        shadow = pack.diagnostics.get("shadow", {})
        self.assertIn("legacy_reference_pack", shadow)
        self.assertIn("selected_source_refs", shadow)
        self.assertIn("overlap", shadow)


if __name__ == "__main__":
    unittest.main()
