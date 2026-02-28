"""GPT-facing validation surface for memory workflows."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

try:
    from memory_validation_core import (
        assert_notes_content_only as _assert_notes_content_only,
        assert_persist_claim_allowed as _assert_persist_claim_allowed,
        assert_sections_explicitly_approved as _assert_sections_explicitly_approved,
        assert_validated_before_write as _assert_validated_before_write,
        assert_validation_claim_allowed as _assert_validation_claim_allowed,
        canonical_json_sha256 as _canonical_json_sha256,
        canonical_json_text as _canonical_json_text,
        diagnose_payload_integrity as _diagnose_payload_integrity,
        should_emit_memory_status as _should_emit_memory_status,
        validate_career_corpus as _validate_career_corpus,
        validate_career_patch as _validate_career_patch,
    )
except ImportError:
    from knowledge_files.memory_validation_core import (  # type: ignore
        assert_notes_content_only as _assert_notes_content_only,
        assert_persist_claim_allowed as _assert_persist_claim_allowed,
        assert_sections_explicitly_approved as _assert_sections_explicitly_approved,
        assert_validated_before_write as _assert_validated_before_write,
        assert_validation_claim_allowed as _assert_validation_claim_allowed,
        canonical_json_sha256 as _canonical_json_sha256,
        canonical_json_text as _canonical_json_text,
        diagnose_payload_integrity as _diagnose_payload_integrity,
        should_emit_memory_status as _should_emit_memory_status,
        validate_career_corpus as _validate_career_corpus,
        validate_career_patch as _validate_career_patch,
    )


__all__ = [
    "validate_career_corpus",
    "validate_career_patch",
    "assert_validated_before_write",
    "assert_sections_explicitly_approved",
    "assert_validation_claim_allowed",
    "assert_persist_claim_allowed",
    "assert_notes_content_only",
    "should_emit_memory_status",
    "canonical_json_text",
    "canonical_json_sha256",
    "diagnose_payload_integrity",
]


def gpt_surface(obj: Any) -> Any:
    """When to use: mark a callable as GPT-facing surface API."""
    obj.__gpt_layer__ = "surface"
    obj.__gpt_surface__ = True
    return obj


def gpt_core(obj: Any) -> Any:
    """When to use: mark a callable as internal core API."""
    obj.__gpt_layer__ = "core"
    obj.__gpt_core__ = True
    return obj


@gpt_surface
def validate_career_corpus(corpus: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """When to use: validate full career corpus before write/use. Inputs: corpus object. Outputs: (is_valid, errors)."""
    return _validate_career_corpus(corpus)


@gpt_surface
def validate_career_patch(
    existing_corpus: Dict[str, Any], patch: Dict[str, Any]
) -> Tuple[bool, Dict[str, Any], List[str]]:
    """When to use: validate a partial corpus change against schema. Inputs: existing corpus + patch. Outputs: (is_valid, merged_doc, errors)."""
    return _validate_career_patch(existing_corpus, patch)


@gpt_surface
def assert_validated_before_write(validated: bool, context: str = "") -> None:
    """When to use: hard-stop writes if validation did not pass. Inputs: validation flag + optional context. Outputs: none (raises on violation)."""
    _assert_validated_before_write(validated, context)


@gpt_surface
def assert_sections_explicitly_approved(
    approved_sections: Dict[str, Any],
    target_sections: List[str],
) -> None:
    """When to use: enforce explicit user approval for section-scoped writes. Inputs: approvals map + target sections. Outputs: none (raises on violation)."""
    _assert_sections_explicitly_approved(approved_sections, target_sections)


@gpt_surface
def assert_validation_claim_allowed(validated_ran: bool, validation_ok: bool) -> None:
    """When to use: enforce truthful validated-state reporting. Inputs: validation execution/pass flags. Outputs: none (raises on violation)."""
    _assert_validation_claim_allowed(validated_ran, validation_ok)


@gpt_surface
def assert_persist_claim_allowed(push_ok: bool, verify_ok: bool) -> None:
    """When to use: enforce truthful persisted-state reporting. Inputs: push success + verification flags. Outputs: none (raises on violation)."""
    _assert_persist_claim_allowed(push_ok, verify_ok)


@gpt_surface
def assert_notes_content_only(document: Dict[str, Any]) -> None:
    """When to use: reject process/provenance text in notes fields. Inputs: full document object. Outputs: none (raises on violation)."""
    _assert_notes_content_only(document)


@gpt_surface
def should_emit_memory_status(
    previous_state: Optional[Dict[str, Any]],
    current_state: Optional[Dict[str, Any]],
    requested: bool,
    failed: bool,
    policy: Optional[str] = "on_change",
) -> bool:
    """When to use: decide if memory status should be shown to user. Inputs: previous/current state and policy flags. Outputs: boolean."""
    return _should_emit_memory_status(previous_state, current_state, requested, failed, policy)


@gpt_surface
def canonical_json_text(json_obj: Dict[str, Any]) -> str:
    """When to use: produce deterministic JSON text for compare/hash operations. Inputs: JSON object. Outputs: canonical JSON string."""
    return _canonical_json_text(json_obj)


@gpt_surface
def canonical_json_sha256(json_obj: Dict[str, Any]) -> str:
    """When to use: compute deterministic JSON hash for integrity checks. Inputs: JSON object. Outputs: SHA-256 hex digest."""
    return _canonical_json_sha256(json_obj)


@gpt_surface
def diagnose_payload_integrity(text: str) -> Dict[str, Any]:
    """When to use: inspect UTF-8 payload integrity before transport. Inputs: payload text. Outputs: diagnostics object."""
    return _diagnose_payload_integrity(text)
