#!/usr/bin/env python3
"""Validate an MT940 file field by field against its reviewed source manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from mt940_common import (
    MT940Error,
    contains_unexpected_controls,
    expected_lines,
    fingerprint,
    normalize_manifest,
    output_filename,
    profile_allowed_underfields,
    sidecar_filename,
    transaction_metrics,
    underfields,
)
from source_check import compare_source, read_source_review


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


def validate(path: Path, manifest: dict[str, Any], profile_dir: Path | None = None,
             source_review_path: Path | None = None) -> dict[str, Any]:
    review = read_source_review(source_review_path)
    normalized = normalize_manifest(manifest, profile_dir)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise MT940Error(f"Cannot read MT940 file: {exc}", 2) from exc
    if not raw.endswith(b"\r\n"):
        raise MT940Error("File must end with CRLF", 3)
    if b"\n" in raw.replace(b"\r\n", b"") or b"\r" in raw.replace(b"\r\n", b""):
        raise MT940Error("Only CRLF line endings are allowed", 3)
    try:
        text = raw.decode("cp1252", errors="strict")
    except UnicodeDecodeError as exc:
        raise MT940Error(f"File is not valid Windows-1252: {exc}", 3) from exc
    lines = text.split("\r\n")[:-1]
    if not lines:
        raise MT940Error("File is empty", 3)
    for number, line in enumerate(lines, 1):
        if contains_unexpected_controls(line):
            raise MT940Error(f"Line {number} contains an unexpected control character", 3)
        if len(line) > 65:
            raise MT940Error(f"Line {number} exceeds 65 characters", 3)

    if len(lines) < 5:
        raise MT940Error("File is incomplete", 3)
    field20 = FIELD20_RE.fullmatch(lines[0])
    if not field20:
        raise MT940Error(":20: is missing, empty, or longer than 16 characters", 3)
    field28 = FIELD28_RE.fullmatch(lines[2])
    if not field28:
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
        actual_line = lines[mismatch - 1] if mismatch <= len(lines) else "<missing>"
        expected_line = expected[mismatch - 1] if mismatch <= len(expected) else "<none>"
        raise MT940Error(
            f"Field-wise manifest mismatch at line {mismatch}: "
            f"actual={actual_line!r}, expected={expected_line!r}",
            3,
        )

    groups = _field86_groups(lines)
    if len(groups) != len(normalized["_transactions"]):
        raise MT940Error("The numbers of :61:, :86:, and source transactions differ", 3)
    mode = normalized["_field86_mode"]
    allowed = profile_allowed_underfields(normalized)
    for number, (group, tx) in enumerate(zip(groups, normalized["_transactions"]), 1):
        reconstructed = group[0][4:] + "".join(group[1:])
        source = tx["_field86"].canonical_description
        decoded = reconstructed if mode == "native" else normalized["_profile"]["_adapter"].decode_field86(group)["description"]
        if decoded != source:
            raise MT940Error(f"Transaction {number} failed the :86: roundtrip", 3)
        found_underfields = underfields(reconstructed)
        if not found_underfields <= allowed:
            raise MT940Error(
                f"Transaction {number} uses underfields not allowed by the DATEV profile",
                3,
            )

    source_check = compare_source(lines, manifest, normalized, review)
    probe_verified = normalized["_profile"].get("status") == "verified" and mode != "native"
    production_ready = normalized["_output_scope"] == "full" and (
        normalized["_target_system"] != "DATEV" or mode == "native" or probe_verified
    ) and not normalized["_profile"].get("test_fixture_only", False)

    result = {
        "status": "source_fields_technically_and_arithmetically_valid",
        "delivery_approved": production_ready,
        "mt940_sha256": hashlib.sha256(raw).hexdigest(),
        "bank_model": {key: manifest[key] for key in ("bank_id", "source_variant", "bank_profile", "profile_version")},
        "bank_model_sha256": normalized["_profile"]["_model_sha256"],
        "source_check": source_check,
        "exit_code": 0,
        "iban": normalized["iban"],
        "statement_number": normalized["_statement_number"],
        "sequence_number": normalized["_sequence_number"],
        "transactions": len(normalized["_transactions"]),
        "opening": f"{normalized['_opening']:.2f}",
        "transaction_total": f"{normalized['_transaction_total']:.2f}",
        "closing": f"{normalized['_closing']:.2f}",
        "currency": normalized.get("currency", "EUR"),
        "fingerprint_sha256": fingerprint(normalized),
        "field86": transaction_metrics(normalized),
        "datev_practical_test": (
            "documented in verified profile"
            if probe_verified and not normalized["_profile"].get("test_fixture_only", False)
            else "not confirmed by a probe import"
        ),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--profile-dir", type=Path)
    parser.add_argument("--source-review", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report_path = args.report or default_report_path(args.file)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        normalized = normalize_manifest(manifest, args.profile_dir)
        report_path = args.report or args.file.parent / sidecar_filename(normalized)
        result = validate(args.file, manifest, args.profile_dir, args.source_review)
        report_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    except MT940Error as exc:
        write_failure_report(report_path, exc)
        print(f"status=error\nexit_code={exc.exit_code}\nmessage={exc}", file=sys.stderr)
        raise SystemExit(exc.exit_code) from exc
    except (OSError, json.JSONDecodeError) as exc:
        write_failure_report(report_path, MT940Error(str(exc), 2))
        print(f"status=error\nexit_code=2\nmessage={exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    for key in (
        "status",
        "transactions",
        "opening",
        "transaction_total",
        "closing",
        "fingerprint_sha256",
        "datev_practical_test",
    ):
        print(f"{key}={result[key]}")
    print(f"report={report_path}")


def write_failure_report(path: Path, error: MT940Error) -> None:
    """Replace a stale success report, including readable field mismatches."""
    report = {"status": "delivery_blocked", "delivery_approved": False,
              "exit_code": error.exit_code, "error": str(error), "source_check": error.details}
    try:
        previous = json.loads(path.read_text(encoding="utf-8"))
        digest = previous.get("fingerprint_sha256")
        if isinstance(digest, str) and re.fullmatch(r"[a-f0-9]{64}", digest):
            report["fingerprint_sha256"] = digest
    except (OSError, json.JSONDecodeError, AttributeError):
        pass
    try:
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"Cannot save blocked report {path}: {exc}; do not reuse an earlier report", file=sys.stderr)


def default_report_path(path: Path) -> Path:
    test = re.fullmatch(r"MT940 Test ([A-Z0-9]+) (\d{2}\.\d{2}\.\d{4})", path.stem)
    if test:
        iban, day = test.groups()
        return path.parent / f"MT940 Prüfung {iban} {day} bis {day}.json"
    return path.parent / ("MT940 Prüfung " + path.stem.removeprefix("MT940 ") + ".json")


if __name__ == "__main__":
    main()
