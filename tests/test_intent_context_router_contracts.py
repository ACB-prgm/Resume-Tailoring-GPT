from __future__ import annotations

import unittest

from knowledge_files import intent_context_router_surface as router_surface
from knowledge_files.context_atoms_core import get_all_atoms
from knowledge_files.intent_context_router_core import Intent, RuntimeState


class IntentContextRouterContractsTests(unittest.TestCase):
    """Test suite for intent context router contracts."""
    def test_surface_exports(self) -> None:
        """Test that surface exports."""
        expected = [
            "Intent",
            "RuntimeState",
            "ContextAtom",
            "ContextPack",
            "build_context",
        ]
        self.assertEqual(router_surface.__all__, expected)
        self.assertTrue(getattr(router_surface.Intent, "__gpt_surface__", False))
        self.assertTrue(getattr(router_surface.RuntimeState, "__gpt_surface__", False))
        self.assertTrue(getattr(router_surface.ContextAtom, "__gpt_surface__", False))
        self.assertTrue(getattr(router_surface.ContextPack, "__gpt_surface__", False))
        self.assertTrue(getattr(router_surface.build_context, "__gpt_surface__", False))

    def test_deterministic_ordering(self) -> None:
        """Test that deterministic ordering."""
        state = RuntimeState(
            repo_exists=True,
            runtime_initialized=True,
            corpus_exists=True,
            corpus_loaded=True,
            corpus_valid=True,
            user_requested_memory_status=True,
        )
        first = router_surface.build_context(Intent.MEMORY_STATUS, state, verbose=True)
        second = router_surface.build_context(Intent.MEMORY_STATUS, state, verbose=True)
        self.assertEqual([atom.id for atom in first.atoms], [atom.id for atom in second.atoms])
        self.assertEqual(first.rendered_context, second.rendered_context)

    def test_restrictive_conflict_resolution(self) -> None:
        """Test that restrictive conflict resolution."""
        state = RuntimeState(
            repo_exists=True,
            runtime_initialized=True,
            corpus_exists=True,
            corpus_loaded=True,
            corpus_valid=True,
            user_requested_memory_status=True,
        )
        pack = router_surface.build_context(Intent.MEMORY_STATUS, state, verbose=True)
        atom_ids = [atom.id for atom in pack.atoms]

        self.assertIn("memory_status.state_block", atom_ids)
        self.assertNotIn("persist.status_visibility", atom_ids)
        self.assertNotIn("state.memory_status_only_when_relevant", atom_ids)
        self.assertIn("persist.status_visibility", pack.diagnostics["filtered_ids"]["conflict"])

    def test_source_ref_diagnostics_present(self) -> None:
        """Test that source ref diagnostics present."""
        state = RuntimeState()
        pack = router_surface.build_context(Intent.JD_ANALYSIS, state, verbose=True)
        self.assertIn("selected_source_refs", pack.diagnostics)
        self.assertIsInstance(pack.diagnostics["selected_source_refs"], list)

    def test_default_mode_returns_compact_string(self) -> None:
        """Test that default mode returns compact string output."""
        result = router_surface.build_context(Intent.JD_ANALYSIS, RuntimeState())
        self.assertIsInstance(result, str)
        self.assertIn("RENDERED CONTEXT:", result)

    def test_memory_status_format_contract_is_atom_driven(self) -> None:
        """Test that memory status format contract is atom driven."""
        by_id = {atom.id: atom for atom in get_all_atoms()}
        baseline = by_id["memory_status.state_block"].content
        optional = by_id["memory_status.optional_fields"].content

        self.assertIn("MEMORY STATUS", baseline)
        self.assertIn("repo_exists", baseline)
        self.assertIn("corpus_exists", baseline)
        self.assertIn("onboarding_complete", baseline)
        self.assertIn("last_written", baseline)
        self.assertIn("validated", optional)
        self.assertIn("persisted", optional)
        self.assertIn("fallback_used", optional)
        self.assertIn("retry_count", optional)
        self.assertIn("verification", optional)


if __name__ == "__main__":
    unittest.main()
