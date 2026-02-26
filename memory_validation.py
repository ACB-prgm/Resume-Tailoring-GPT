"""
Utilities for strict JSON-schema validation of persistent memory files.

This module is designed for the GPT export/memory pipeline so writes to
`career_corpus.json` and `preferences.json` can be validated deterministically
before any GitHub upsert call is made.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Tuple

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parent
SCHEMA_DIR = REPO_ROOT / "schemas"
CAREER_CORPUS_SCHEMA_PATH = SCHEMA_DIR / "career_corpus.schema.json"
PREFERENCES_SCHEMA_PATH = SCHEMA_DIR / "preferences.schema.json"


def _load_json_file(path: Path) -> Dict[str, Any]:
    """Read a JSON file from disk and return a parsed object."""
    import json

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

    Use before any `upsertCareerCorpusJson` write.
    """
    return validate_json_document(corpus, CAREER_CORPUS_SCHEMA_PATH)


def validate_preferences(preferences: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate `preferences.json` payloads.

    Use before any `upsertPreferencesJson` write.
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
