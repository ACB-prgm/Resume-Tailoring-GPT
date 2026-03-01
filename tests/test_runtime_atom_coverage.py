from __future__ import annotations

import unittest

from knowledge_files.context_atoms_core import get_all_atoms


class RuntimeAtomCoverageTests(unittest.TestCase):
    """Test suite for runtime atom coverage."""
    def test_required_policy_domains_present(self) -> None:
        """Test that required policy domains present."""
        atoms = get_all_atoms()
        tags = {tag for atom in atoms for tag in atom.tags}

        required_domains = {
            "memory",
            "persist",
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
        """Test that registry contains all intent coverage."""
        atoms = get_all_atoms()
        intents = {intent for atom in atoms for intent in atom.intents}
        expected = {
            "INTENT_CONVERSATION_ONLY",
            "INTENT_FAILURE_RECOVERY",
            "INTENT_PDF_EXPORT",
            "INTENT_MEMORY_PERSIST_UPDATE",
            "INTENT_ONBOARDING_IMPORT_REPAIR",
            "INTENT_RESUME_DRAFTING",
            "INTENT_JD_ANALYSIS",
            "INTENT_MEMORY_STATUS",
            "INTENT_INITIALIZATION_OR_SETUP",
        }
        self.assertEqual(intents, expected)


if __name__ == "__main__":
    unittest.main()
