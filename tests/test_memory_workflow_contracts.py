from __future__ import annotations

import unittest

from knowledge_files.career_corpus_sync import CareerCorpusSync
from knowledge_files.memory_validation import (
    assert_citations_from_current_turn,
    assert_persist_claim_allowed,
    assert_scaffolding_confirmation_allowed,
    assert_sections_explicitly_approved,
    assert_validation_claim_allowed,
    compute_onboarding_complete,
)


class MemoryWorkflowContractsTests(unittest.TestCase):
    def test_repo_bootstrap_idempotency_sequence(self) -> None:
        calls = []
        state = {"repo_exists": False}

        def get_repo() -> dict:
            calls.append("get")
            if state["repo_exists"]:
                return {"default_branch": "main"}
            return {"status_code": 404}

        def create_repo(payload: dict) -> dict:
            calls.append("create")
            self.assertEqual(payload["name"], "career-corpus-memory")
            state["repo_exists"] = True
            return {"status_code": 201}

        result = CareerCorpusSync.bootstrap_memory_repo(get_repo, create_repo, turn_state={})
        self.assertTrue(result["ok"])
        self.assertTrue(result["created"])
        self.assertEqual(result["sequence"], ["get", "create", "get_confirm"])
        self.assertEqual(calls, ["get", "create", "get"])

    def test_duplicate_create_prevention(self) -> None:
        def get_repo() -> dict:
            return {"status_code": 404}

        def create_repo(_: dict) -> dict:
            return {"status_code": 201}

        with self.assertRaises(RuntimeError):
            CareerCorpusSync.bootstrap_memory_repo(
                get_repo,
                create_repo,
                turn_state={"repo_create_attempted_this_turn": True},
            )

    def test_approval_gate_enforcement(self) -> None:
        approved = {"education": {"approved": True}}
        assert_sections_explicitly_approved(approved, ["education"])

        with self.assertRaises(RuntimeError):
            assert_sections_explicitly_approved(approved, ["education", "skills"])

    def test_scaffolding_prompt_gate(self) -> None:
        with self.assertRaises(RuntimeError):
            assert_scaffolding_confirmation_allowed(create_scaffold=True, user_confirmed=False)
        assert_scaffolding_confirmation_allowed(create_scaffold=False, user_confirmed=False)

    def test_validation_claim_integrity(self) -> None:
        with self.assertRaises(RuntimeError):
            assert_validation_claim_allowed(validated_ran=False, validation_ok=True)
        with self.assertRaises(RuntimeError):
            assert_validation_claim_allowed(validated_ran=True, validation_ok=False)
        assert_validation_claim_allowed(validated_ran=True, validation_ok=True)

    def test_persistence_claim_integrity(self) -> None:
        with self.assertRaises(RuntimeError):
            assert_persist_claim_allowed(push_ok=False, verify_ok=True)
        with self.assertRaises(RuntimeError):
            assert_persist_claim_allowed(push_ok=True, verify_ok=False)
        assert_persist_claim_allowed(push_ok=True, verify_ok=True)

    def test_onboarding_completion_state(self) -> None:
        partial = {
            "profile": {"approved": True},
            "summary_facts": {"approved": True},
        }
        self.assertFalse(compute_onboarding_complete(partial, validated=True, persisted=True))

        full = {
            "profile": {"approved": True},
            "summary_facts": {"approved": True},
            "experience": {"approved": True},
            "projects": {"approved": True},
            "skills": {"approved": True},
            "certifications": {"approved": True},
            "education": {"approved": True},
            "metadata": {"approved": True},
        }
        self.assertTrue(compute_onboarding_complete(full, validated=True, persisted=True))

    def test_citation_contract(self) -> None:
        assert_citations_from_current_turn(["marker_a"], ["marker_a", "marker_b"])
        with self.assertRaises(RuntimeError):
            assert_citations_from_current_turn(["marker_old"], ["marker_new"])


if __name__ == "__main__":
    unittest.main()
