from __future__ import annotations

import unittest

from knowledge_files.context_atoms_core import get_all_atoms


class RuntimeAtomCoverageTests(unittest.TestCase):
    def test_required_policy_domains_present(self) -> None:
        atoms = get_all_atoms()
        tags = {tag for atom in atoms for tag in atom.tags}

        required_domains = {
            "headers",
            "canonical_layout",
            "truthfulness",
            "onboarding",
            "jd",
            "resume",
            "pdf",
            "memory_status",
            "initialization",
            "failure",
        }

        missing = sorted(domain for domain in required_domains if domain not in tags)
        self.assertEqual(missing, [])

    def test_registry_contains_all_intent_coverage(self) -> None:
        atoms = get_all_atoms()
        intents = {intent for atom in atoms for intent in atom.intents}
        expected = {
            "intent_conversation_only",
            "intent_failure_recovery",
            "intent_pdf_export",
            "intent_memory_persist_update",
            "intent_onboarding_import_repair",
            "intent_resume_drafting",
            "intent_jd_analysis",
            "intent_memory_status",
            "intent_initialization_or_setup",
        }
        self.assertEqual(intents, expected)


if __name__ == "__main__":
    unittest.main()
