"""
Utilities for strict JSON-schema validation of persistent memory files.

This module is designed for the GPT export/memory pipeline so writes to
`career_corpus.json` and `preferences.json` can be validated deterministically
before any GitHub upsert call is made.
"""

from __future__ import annotations

import base64
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parent
CAREER_CORPUS_SCHEMA_PATH = REPO_ROOT / "career_corpus.schema.json"
PREFERENCES_SCHEMA_PATH = REPO_ROOT / "preferences.schema.json"


def _load_json_file(path: Path) -> Dict[str, Any]:
    """Read a JSON file from disk and return a parsed object."""
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected top-level object in {path}, got {type(data).__name__}")
    return data


def _load_validator(schema_path: Path) -> Draft202012Validator:
    """Build a Draft 2020-12 validator from a schema file."""
    schema = _load_json_file(schema_path)
    return Draft202012Validator(schema)


def _format_errors(errors: List[Any]) -> List[str]:
    """Normalize jsonschema errors into compact, stable strings."""
    formatted: List[str] = []
    for err in sorted(errors, key=lambda e: list(e.path)):
        location = ".".join(str(p) for p in err.path) or "<root>"
        formatted.append(f"{location}: {err.message}")
    return formatted


def validate_json_document(
    document: Dict[str, Any], schema_path: Path
) -> Tuple[bool, List[str]]:
    """
    Validate a document against the schema at `schema_path`.

    Returns:
        (is_valid, errors)
        - is_valid: True only when the document fully conforms to schema.
        - errors: human-readable validation error list (empty when valid).
    """
    validator = _load_validator(schema_path)
    errors = list(validator.iter_errors(document))
    if errors:
        return False, _format_errors(errors)
    return True, []


def validate_career_corpus(corpus: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate `career_corpus.json` payloads.

    Use before any persistence write attempt.
    """
    return validate_json_document(corpus, CAREER_CORPUS_SCHEMA_PATH)


def validate_preferences(preferences: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate `preferences.json` payloads.

    Use before any persistence write attempt.
    """
    return validate_json_document(preferences, PREFERENCES_SCHEMA_PATH)


def merge_minimal_patch(
    existing: Dict[str, Any], patch: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Apply a minimal nested patch to an existing document.

    Rules:
    - dict + dict: recursively merge keys
    - scalar/list replacement: patch value replaces existing value

    This preserves untouched keys and only updates provided paths.
    """
    merged = deepcopy(existing)
    for key, patch_value in patch.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(patch_value, dict)
        ):
            merged[key] = merge_minimal_patch(merged[key], patch_value)
        else:
            merged[key] = deepcopy(patch_value)
    return merged


def apply_patch_and_validate(
    existing: Dict[str, Any],
    patch: Dict[str, Any],
    schema_path: Path,
) -> Tuple[bool, Dict[str, Any], List[str]]:
    """
    Merge `patch` into `existing`, then validate the full result.

    Returns:
        (is_valid, merged_document, errors)
    """
    merged = merge_minimal_patch(existing, patch)
    valid, errors = validate_json_document(merged, schema_path)
    return valid, merged, errors


def validate_career_patch(
    existing_corpus: Dict[str, Any], patch: Dict[str, Any]
) -> Tuple[bool, Dict[str, Any], List[str]]:
    """Patch and validate a career corpus update in one call."""
    return apply_patch_and_validate(existing_corpus, patch, CAREER_CORPUS_SCHEMA_PATH)


def validate_preferences_patch(
    existing_preferences: Dict[str, Any], patch: Dict[str, Any]
) -> Tuple[bool, Dict[str, Any], List[str]]:
    """Patch and validate a preferences update in one call."""
    return apply_patch_and_validate(
        existing_preferences, patch, PREFERENCES_SCHEMA_PATH
    )


def canonical_json_text(json_obj: Dict[str, Any]) -> str:
    """Return deterministic JSON text for hashing/comparison."""
    return json.dumps(
        json_obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_json_sha256(json_obj: Dict[str, Any]) -> str:
    """Return SHA-256 hex digest of deterministic JSON text."""
    return hashlib.sha256(canonical_json_text(json_obj).encode("utf-8")).hexdigest()


def diagnose_payload_integrity(text: str) -> Dict[str, Any]:
    """
    Provide quick integrity diagnostics for UTF-8 payloads.

    This is useful before transport calls to detect truncation/mutation.
    """
    encoded = text.encode("utf-8")
    return {
        "char_len": len(text),
        "byte_len": len(encoded),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "contains_non_ascii": any(ord(c) > 127 for c in text),
        "newline_count": text.count("\n"),
    }


def verify_remote_matches_local(
    local_text: str,
    remote_text: str,
) -> Tuple[bool, Optional[str]]:
    """
    Verify remote JSON text matches local JSON text after canonicalization.

    Returns:
        (ok, error)
    """
    try:
        local_obj = json.loads(local_text)
        remote_obj = json.loads(remote_text)
    except Exception as exc:
        return False, f"JSON parse failed during verification: {exc}"

    local_canonical = canonical_json_text(local_obj)
    remote_canonical = canonical_json_text(remote_obj)
    if local_canonical == remote_canonical:
        return True, None

    local_hash = hashlib.sha256(local_canonical.encode("utf-8")).hexdigest()
    remote_hash = hashlib.sha256(remote_canonical.encode("utf-8")).hexdigest()
    return False, f"Canonical mismatch: local={local_hash} remote={remote_hash}"


def encode_base64_utf8(text: str) -> str:
    """
    Encode UTF-8 text as a base64 ASCII string.

    Use this for GitHub contents API `content` fields.
    """
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def decode_base64_utf8(content_b64: str) -> str:
    """
    Decode a base64 ASCII string back to UTF-8 text.

    Raises:
        ValueError: when the payload is not valid base64/UTF-8.
    """
    try:
        raw = base64.b64decode(content_b64.encode("ascii"), validate=True)
        return raw.decode("utf-8")
    except Exception as exc:  # pragma: no cover - precise exception type not required here.
        raise ValueError(f"Invalid base64 UTF-8 payload: {exc}") from exc


def build_upsert_payload(
    message: str,
    json_obj: Dict[str, Any],
    sha: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a GitHub contents API upsert payload from a JSON object.

    The JSON is canonicalized (sorted keys + compact separators) before base64
    encoding so repeated writes are deterministic.
    """
    json_text = json.dumps(json_obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    payload: Dict[str, Any] = {
        "message": message,
        "content": encode_base64_utf8(json_text),
    }
    if sha:
        payload["sha"] = sha
    return payload


def verify_base64_roundtrip(json_obj: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Verify JSON -> base64 -> JSON roundtrip consistency.

    Returns:
        (ok, error)
        - ok: True when the object survives roundtrip exactly.
        - error: human-readable reason when verification fails.
    """
    try:
        canonical = json.dumps(
            json_obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        encoded = encode_base64_utf8(canonical)
        decoded = decode_base64_utf8(encoded)
        decoded_obj = json.loads(decoded)
        if decoded_obj != json_obj:
            return False, "Roundtrip mismatch after base64 encode/decode."
        return True, None
    except Exception as exc:  # pragma: no cover - surfaced to caller as string
        return False, str(exc)


def assert_validated_before_write(validated: bool, context: str = "") -> None:
    """
    Raise a hard error if a write is attempted without a successful validation gate.

    This function is a process guard used by instructions/workflows before GitHub upserts.
    """
    if not validated:
        suffix = f" ({context})" if context else ""
        raise RuntimeError(f"Validation gate failed before write{suffix}.")


def assert_sections_explicitly_approved(
    approved_sections: Dict[str, Any],
    target_sections: List[str],
) -> None:
    """
    Enforce section-level explicit approvals before persistence.

    `approved_sections` may be:
    - {"education": True, "profile": {"approved": True, ...}}
    """
    if not target_sections:
        raise RuntimeError("target_sections cannot be empty for guarded writes.")

    missing: List[str] = []
    for section in target_sections:
        value = approved_sections.get(section)
        is_approved = False
        if isinstance(value, bool):
            is_approved = value
        elif isinstance(value, dict):
            is_approved = bool(value.get("approved"))
        if not is_approved:
            missing.append(section)

    if missing:
        raise RuntimeError(f"Missing explicit approvals for sections: {', '.join(sorted(missing))}.")


def assert_validation_claim_allowed(validated_ran: bool, validation_ok: bool) -> None:
    """Block invalid `validated=true` claims."""
    if not validated_ran:
        raise RuntimeError("Cannot claim validated=true because validator did not run.")
    if not validation_ok:
        raise RuntimeError("Cannot claim validated=true because validation did not pass.")


def assert_persist_claim_allowed(push_ok: bool, verify_ok: bool) -> None:
    """Block invalid `persisted=true` claims."""
    if not push_ok:
        raise RuntimeError("Cannot claim persisted=true because push did not succeed.")
    if not verify_ok:
        raise RuntimeError("Cannot claim persisted=true because verification did not pass.")


def assert_citations_from_current_turn(
    citation_markers: List[str],
    current_turn_markers: List[str],
) -> None:
    """
    Require citation markers to come from evidence retrieval in the current turn.
    """
    if not citation_markers:
        return
    allowed = set(current_turn_markers)
    invalid = sorted(marker for marker in citation_markers if marker not in allowed)
    if invalid:
        raise RuntimeError(
            "Citation markers are not from current-turn evidence: " + ", ".join(invalid)
        )


def compute_onboarding_complete(
    approved_sections: Dict[str, Any],
    validated: bool,
    persisted: bool,
    required_sections: Optional[List[str]] = None,
) -> bool:
    """
    True only when required sections are approved and validation/persistence passed.
    """
    if not validated or not persisted:
        return False
    needed = required_sections or [
        "profile",
        "experience",
        "projects",
        "skills",
        "certifications",
        "education",
        "metadata",
    ]
    for section in needed:
        value = approved_sections.get(section)
        approved = (isinstance(value, bool) and value) or (
            isinstance(value, dict) and bool(value.get("approved"))
        )
        if not approved:
            return False
    return True


def assert_scaffolding_confirmation_allowed(
    create_scaffold: bool,
    user_confirmed: bool,
) -> None:
    """Require explicit confirmation before creating empty scaffold sections."""
    if create_scaffold and not user_confirmed:
        raise RuntimeError("Scaffold creation requires explicit user confirmation.")
