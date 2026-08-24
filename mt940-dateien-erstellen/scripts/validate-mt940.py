#!/usr/bin/env python3
"""Validate MT940 structure, canonical semantics, and exact DATEV CP1252 bytes."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from mt940_common import (
    MT940Error,
    contains_unexpected_controls,
    expected_lines,
    expected_payload,
    fingerprint,
    normalize_manifest,
    output_filename,
    parse_datev_structured_field86,
    read_json_utf8_no_bom,
    reject_invalid_datev_bytes,
    sidecar_filename,
    transaction_metrics,
    underfields,
)


FIELD20_RE = re.compile(r"^:20:(.{1,16})$")
FIELD28_RE = re.compile(r"^:28C:(\d{5})/(\d{3})$")


def _field86_groups(lines: list[str]) -> list[list[str]]:
    groups: list[list[str]] = []
    index = 4
    while index < len(lines) - 1:
        if not lines[index].startswith(":61:"):
            raise MT940Error(f"Expected :61: at physical line {index + 1}", 3)
        index += 1
        if index >= len(lines) - 1 or not lines[index].startswith(":86:"):
            raise MT940Error(f"Transaction {len(groups) + 1} lacks immediate :86:", 3)
        group = [lines[index]]
        index += 1
        while index < len(lines) - 1 and not lines[index].startswith(":61:"):
            if lines[index].startswith(":"):
                raise MT940Error(f"Unexpected tag at physical line {index + 1}", 3)
            group.append(lines[index])
            index += 1
        if len(group) > 6:
            raise MT940Error(f"Transaction {len(groups) + 1} exceeds six :86: lines", 3)
        groups.append(group)
    return groups


def _validate_structured_group(
    number: int,
    group: list[str],
    tx: dict[str, Any],
    profile: dict[str, Any],
) -> None:
    parsed = parse_datev_structured_field86(group)
    expected = tx["_field86"]
    if parsed["gvc"] != expected.gvc:
        raise MT940Error(f"Transaction {number} GVC differs from canonical model", 3)
    if tuple(parsed["underfield_order"]) != expected.underfield_order:
        raise MT940Error(f"Transaction {number} underfield order differs", 3)
    if parsed["semantic_values"] != expected.semantic_values:
        raise MT940Error(
            f"Transaction {number} swaps, truncates, or changes semantic :86: values",
            3,
        )
    allowed = set(profile.get("allowed_underfields", []))
    required = set(profile.get("required_underfields", []))
    found = set(parsed["underfield_order"])
    if not found <= allowed or not required <= found:
        raise MT940Error(f"Transaction {number} violates target-profile underfields", 3)
    lengths = profile.get("subfield_lengths", {})
    for code, value in parsed["fields"].items():
        configured = lengths.get(code, lengths.get("20") if "20" <= code <= "29" else None)
        if not isinstance(configured, int) or len(value) > configured:
            raise MT940Error(f"Transaction {number} field ?{code} exceeds capacity", 3)


def validate(
    path: Path, manifest: dict[str, Any], profile_dir: Path | None = None
) -> dict[str, Any]:
    normalized = normalize_manifest(manifest, profile_dir)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise MT940Error(f"Cannot read MT940 file: {exc}", 2) from exc
    if normalized["_target_system"] == "DATEV":
        reject_invalid_datev_bytes(raw)
    expected_raw = expected_payload(normalized)
    if raw != expected_raw:
        mismatch = next(
            (index for index, pair in enumerate(zip(raw, expected_raw)) if pair[0] != pair[1]),
            min(len(raw), len(expected_raw)),
        )
        actual_byte = raw[mismatch : mismatch + 8].hex(" ").upper()
        expected_byte = expected_raw[mismatch : mismatch + 8].hex(" ").upper()
        raise MT940Error(
            f"Raw bytes differ from canonical CP1252 output at offset {mismatch}: "
            f"actual={actual_byte}, expected={expected_byte}",
            3,
        )
    try:
        text = raw.decode("cp1252", errors="strict")
    except UnicodeDecodeError as exc:
        raise MT940Error(f"File is not valid Windows-1252: {exc}", 3) from exc
    lines = text.split("\r\n")[:-1]
    if not lines:
        raise MT940Error("File is empty", 3)
    for line_number, line in enumerate(lines, 1):
        if len(line) > 65:
            raise MT940Error(f"Line {line_number} exceeds 65 characters", 3)

    if len(lines) < 5:
        raise MT940Error("File is incomplete", 3)
    if not FIELD20_RE.fullmatch(lines[0]):
        raise MT940Error(":20: is missing, empty, or longer than 16 characters", 3)
    if not FIELD28_RE.fullmatch(lines[2]):
        raise MT940Error(":28C: must use five-digit statement/three-digit sequence syntax", 3)
    if not lines[-1].startswith(":62F:"):
        raise MT940Error("Last field must be :62F:", 3)
    actual_iban = lines[1][4:] if lines[1].startswith(":25:") else ""
    if actual_iban != normalized["iban"]:
        raise MT940Error("IBAN differs between manifest and :25:", 3)
    if normalized["iban"] not in path.name:
        raise MT940Error("IBAN differs between manifest and filename", 3)
    expected_name = output_filename(normalized)
    if path.name != expected_name:
        raise MT940Error(f"Unexpected filename; expected {expected_name!r}", 3)

    expected = expected_lines(normalized)
    if lines != expected:
        mismatch = next(
            (i for i, pair in enumerate(zip(lines, expected), 1) if pair[0] != pair[1]),
            min(len(lines), len(expected)) + 1,
        )
        raise MT940Error(f"Field-wise manifest mismatch at line {mismatch}", 3)

    groups = _field86_groups(lines)
    if len(groups) != len(normalized["_transactions"]):
        raise MT940Error("The numbers of :61:, :86:, and source transactions differ", 3)
    structured = normalized["_field86_mode"] == "datev_structured_v1" or normalized[
        "_field86_mode"
    ].startswith("datev_verified:")
    for number, (group, tx) in enumerate(zip(groups, normalized["_transactions"]), 1):
        reconstructed = group[0][4:] + "".join(group[1:])
        expected_field = tx["_field86"]
        if reconstructed != expected_field.canonical_description:
            raise MT940Error(f"Transaction {number} failed the :86: roundtrip", 3)
        if structured:
            assert normalized["_profile"] is not None
            _validate_structured_group(number, group, tx, normalized["_profile"])
        elif normalized["_field86_mode"] in {"generic_unstructured", "unverified"}:
            if underfields(reconstructed):
                raise MT940Error(f"Transaction {number} contains structured underfields", 3)
            if contains_unexpected_controls(reconstructed):
                raise MT940Error(f"Transaction {number} contains a control character", 3)

    result = {
        "status": "technically_and_arithmetically_valid",
        "exit_code": 0,
        "iban": normalized["iban"],
        "statement_number": normalized["_statement_number"],
        "sequence_number": normalized["_sequence_number"],
        "transactions": len(normalized["_transactions"]),
        "opening": f"{normalized['_opening']:.2f}",
        "transaction_total": f"{normalized['_transaction_total']:.2f}",
        "closing": f"{normalized['_closing']:.2f}",
        "currency": normalized.get("currency", "EUR"),
        "output_charset": "Windows-1252",
        "bom": "none",
        "line_endings": "CRLF",
        "byte_roundtrip_match": True,
        "target_profile_version": normalized["_target_profile_name"],
        "fingerprint_sha256": fingerprint(normalized),
        "field86": transaction_metrics(normalized),
        "datev_practical_test": (
            "documented in verified target profile"
            if normalized["_field86_mode"].startswith("datev_verified:")
            else "not confirmed by a probe import"
        ),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--profile-dir", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        manifest = read_json_utf8_no_bom(args.manifest, "manifest")
        result = validate(args.file, manifest, args.profile_dir)
        normalized = normalize_manifest(manifest, args.profile_dir)
        report_path = args.report or args.file.parent / sidecar_filename(normalized)
        report_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except MT940Error as exc:
        print(f"status=error\nexit_code={exc.exit_code}\nmessage={exc}", file=sys.stderr)
        raise SystemExit(exc.exit_code) from exc
    except (OSError, json.JSONDecodeError) as exc:
        print(f"status=error\nexit_code=2\nmessage={exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    for key in (
        "status",
        "transactions",
        "opening",
        "transaction_total",
        "closing",
        "output_charset",
        "byte_roundtrip_match",
        "fingerprint_sha256",
        "datev_practical_test",
    ):
        print(f"{key}={result[key]}")
    print(f"report={report_path}")


if __name__ == "__main__":
    main()
