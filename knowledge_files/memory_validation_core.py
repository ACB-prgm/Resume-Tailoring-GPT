"""
Utilities for strict JSON-schema validation of persistent memory files.

This module is designed for the GPT export/memory pipeline so writes to
`career_corpus.json` can be validated deterministically
before any GitHub upsert call is made.
"""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parent
CAREER_CORPUS_SCHEMA_PATH = REPO_ROOT / "career_corpus.schema.json"


def gpt_core(obj: Any) -> Any:
    """Gpt core."""
    obj.__gpt_layer__ = "core"
    obj.__gpt_core__ = True
    return obj


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


@gpt_core
def validate_career_corpus(corpus: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate `career_corpus.json` payloads.

    Use before any persistence write attempt.
    """
    return validate_json_document(corpus, CAREER_CORPUS_SCHEMA_PATH)


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


@gpt_core
def validate_career_patch(
    existing_corpus: Dict[str, Any], patch: Dict[str, Any]
) -> Tuple[bool, Dict[str, Any], List[str]]:
    """Patch and validate a career corpus update in one call."""
    return apply_patch_and_validate(existing_corpus, patch, CAREER_CORPUS_SCHEMA_PATH)


@gpt_core
def canonical_json_text(json_obj: Dict[str, Any]) -> str:
    """Return deterministic JSON text for hashing/comparison."""
    return json.dumps(
        json_obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


@gpt_core
def canonical_json_sha256(json_obj: Dict[str, Any]) -> str:
    """Return SHA-256 hex digest of deterministic JSON text."""
    return hashlib.sha256(canonical_json_text(json_obj).encode("utf-8")).hexdigest()


@gpt_core
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


@gpt_core
def assert_validated_before_write(validated: bool, context: str = "") -> None:
    """
    Raise a hard error if a write is attempted without a successful validation gate.

    This function is a process guard used by instructions/workflows before GitHub upserts.
    """
    if not validated:
        suffix = f" ({context})" if context else ""
        raise RuntimeError(f"Validation gate failed before write{suffix}.")


@gpt_core
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


@gpt_core
def assert_validation_claim_allowed(validated_ran: bool, validation_ok: bool) -> None:
    """Block invalid `validated=true` claims."""
    if not validated_ran:
        raise RuntimeError("Cannot claim validated=true because validator did not run.")
    if not validation_ok:
        raise RuntimeError("Cannot claim validated=true because validation did not pass.")


@gpt_core
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


@gpt_core
def assert_notes_content_only(document: Dict[str, Any]) -> None:
    """
    Enforce that `notes` fields contain only content context.

    Reject operational/provenance/process metadata phrases such as upload
    source tracking and Git transport details.
    """
    prohibited = re.compile(
        r"\b(source|uploaded?|upload|onboarding|current chat|from chat|manual import|"
        r"persisted|committed|branch|commit|sha|blob|tree|ref)\b",
        re.IGNORECASE,
    )

    def _walk(node: Any, path: str) -> None:
        """Internal helper to walk."""
        if isinstance(node, dict):
            for key, value in node.items():
                child_path = f"{path}.{key}" if path else key
                if key == "notes":
                    if value is None:
                        continue
                    if not isinstance(value, str):
                        raise RuntimeError(f"Invalid notes type at {child_path}: expected string or null.")
                    text = value.strip()
                    if not text:
                        return
                    if prohibited.search(text):
                        raise RuntimeError(
                            f"Notes at {child_path} contains process/provenance text; keep notes content-only."
                        )
                    continue
                _walk(value, child_path)
            return
        if isinstance(node, list):
            for idx, value in enumerate(node):
                _walk(value, f"{path}[{idx}]")

    _walk(document, "")


@gpt_core
def should_emit_memory_status(
    previous_state: Optional[Dict[str, Any]],
    current_state: Optional[Dict[str, Any]],
    requested: bool,
    failed: bool,
    policy: Optional[str] = "on_change",
) -> bool:
    """
    Determine whether memory status should be shown to the user.

    Policies:
    - on_change (default): emit when state differs, or when requested/failed.
    - on_request: emit only when requested/failed.
    - always: emit every time.
    """
    if requested or failed:
        return True

    effective_policy = policy or "on_change"
    if effective_policy == "always":
        return True
    if effective_policy == "on_request":
        return False
    if effective_policy != "on_change":
        effective_policy = "on_change"

    if previous_state is None:
        return True
    return previous_state != current_state
