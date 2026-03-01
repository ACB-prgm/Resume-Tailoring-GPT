from __future__ import annotations

import unittest

from knowledge_files.career_corpus_sync_surface import CareerCorpusSync
from knowledge_files.memory_validation_surface import (
    assert_notes_content_only,
    assert_persist_claim_allowed,
    assert_sections_explicitly_approved,
    assert_validated_before_write,
    assert_validation_claim_allowed,
    should_emit_memory_status,
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
            assert_sections_explicitly_approved(approved, ["education", "profile"])

    def test_validation_gate_enforcement(self) -> None:
        assert_validated_before_write(True)
        with self.assertRaises(RuntimeError):
            assert_validated_before_write(False, context="push")

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

    def test_status_emission_policy(self) -> None:
        prev = {"repo_exists": True, "corpus_exists": True}
        same = {"repo_exists": True, "corpus_exists": True}
        changed = {"repo_exists": True, "corpus_exists": False}

        self.assertFalse(
            should_emit_memory_status(prev, same, requested=False, failed=False, policy="on_change")
        )
        self.assertTrue(
            should_emit_memory_status(prev, changed, requested=False, failed=False, policy="on_change")
        )
        self.assertFalse(
            should_emit_memory_status(prev, changed, requested=False, failed=False, policy="on_request")
        )
        self.assertTrue(
            should_emit_memory_status(prev, same, requested=True, failed=False, policy="on_request")
        )
        self.assertTrue(
            should_emit_memory_status(prev, same, requested=False, failed=True, policy="on_change")
        )
        self.assertTrue(
            should_emit_memory_status(prev, same, requested=False, failed=False, policy="always")
        )

    def test_notes_policy_guard(self) -> None:
        assert_notes_content_only(
            {
                "profile": {"notes": "Graduated with honors"},
                "experience": [{"notes": "Received employee award"}],
            }
        )
        with self.assertRaises(RuntimeError):
            assert_notes_content_only(
                {
                    "profile": {"notes": "Source: CareerCorpus.txt uploaded during onboarding."},
                }
            )


if __name__ == "__main__":
    unittest.main()
