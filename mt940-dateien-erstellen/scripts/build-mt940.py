#!/usr/bin/env python3
"""Build deterministic CP1252 MT940/STA output and a fingerprint sidecar."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from mt940_common import (
    MT940Error,
    expected_lines,
    expected_payload,
    fingerprint,
    normalize_manifest,
    output_filename,
    read_json_utf8_no_bom,
    reject_invalid_datev_bytes,
    sidecar_filename,
    transaction_metrics,
)


def build(data: dict[str, Any], profile_dir: Path | None = None) -> tuple[bytes, dict[str, Any]]:
    normalized = normalize_manifest(data, profile_dir)
    lines = expected_lines(normalized)
    payload = expected_payload(normalized, lines)
    if normalized["_target_system"] == "DATEV":
        reject_invalid_datev_bytes(payload)
    expected_cp1252 = ("\r\n".join(lines) + "\r\n").encode(
        "cp1252", errors="strict"
    )
    if payload != expected_cp1252:
        raise MT940Error("Generated raw bytes differ from canonical CP1252 bytes", 3)
    report = {
        "schema_version": 2,
        "fingerprint_sha256": fingerprint(normalized),
        "iban": normalized["iban"],
        "statement_number": normalized["_statement_number"],
        "sequence_number": normalized["_sequence_number"],
        "statement_start": normalized["_statement_start"].isoformat(),
        "statement_end": normalized["_statement_end"].isoformat(),
        "opening_balance_date": normalized["_opening_balance_date"].isoformat(),
        "opening_balance": f"{normalized['_opening']:.2f}",
        "transaction_count": len(normalized["_transactions"]),
        "transaction_total": f"{normalized['_transaction_total']:.2f}",
        "closing_balance_date": normalized["_closing_balance_date"].isoformat(),
        "closing_balance": f"{normalized['_closing']:.2f}",
        "source_type": normalized["_source_type"],
        "field86_mode": normalized["_field86_mode"],
        "target_profile_version": normalized["_target_profile_name"],
        "output_scope": normalized["_output_scope"],
        "output_charset": "Windows-1252",
        "bom": "none",
        "line_endings": "CRLF",
        "byte_roundtrip_match": True,
        "technical_validation": "generation and byte checks passed; independent validation pending",
        "datev_probe_import": (
            "documented in verified target profile"
            if normalized["_field86_mode"].startswith("datev_verified:")
            else "not verified; only a test import is permitted"
        ),
        "transactions": transaction_metrics(normalized),
    }
    return payload, report


def find_duplicate_fingerprint(
    fingerprint_sha256: str, directories: list[Path]
) -> Path | None:
    seen: set[Path] = set()
    for directory in directories:
        resolved_directory = directory.resolve()
        if resolved_directory in seen or not resolved_directory.is_dir():
            continue
        seen.add(resolved_directory)
        for candidate in resolved_directory.glob("MT940 Prüfung *.json"):
            try:
                content = json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if content.get("fingerprint_sha256") == fingerprint_sha256:
                return candidate
    return None


def write_artifacts(
    data: dict[str, Any],
    manifest_path: Path,
    output: Path | None,
    *,
    profile_dir: Path | None = None,
    allow_duplicate: bool = False,
) -> tuple[Path, Path, dict[str, Any]]:
    normalized = normalize_manifest(data, profile_dir)
    payload, report = build(data, profile_dir)
    output_path = output or Path(output_filename(normalized))
    sidecar_path = output_path.parent / sidecar_filename(normalized)
    duplicate = find_duplicate_fingerprint(
        report["fingerprint_sha256"], [output_path.parent, Path.cwd()]
    )
    if duplicate:
        if not allow_duplicate:
            raise MT940Error(
                f"Possible duplicate import: identical fingerprint already recorded in {duplicate}",
                5,
            )
        if data.get("previous_datev_import_removed_confirmed") is not True:
            raise MT940Error(
                "Duplicate override requires previous_datev_import_removed_confirmed=true; "
                "a new file or :20: reference does not prevent a DATEV duplicate import",
                5,
            )
        report["duplicate_override"] = {
            "previous_record": str(duplicate),
            "previous_datev_import_removed_confirmed": True,
        }
    output_path.write_bytes(payload)
    written = output_path.read_bytes()
    if written != payload:
        raise MT940Error("Written STA bytes differ from the validated payload", 3)
    if normalized["_target_system"] == "DATEV":
        reject_invalid_datev_bytes(written)
    report.update({"manifest": str(manifest_path), "mt940_file": str(output_path)})
    sidecar_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if sidecar_path.read_bytes().startswith(b"\xef\xbb\xbf"):
        raise MT940Error("JSON sidecar must be UTF-8 without BOM", 3)
    return output_path, sidecar_path, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path, nargs="?")
    parser.add_argument("--profile-dir", type=Path)
    parser.add_argument("--allow-duplicate", action="store_true")
    args = parser.parse_args()
    try:
        data = read_json_utf8_no_bom(args.manifest, "manifest")
        output, sidecar, report = write_artifacts(
            data,
            args.manifest,
            args.output,
            profile_dir=args.profile_dir,
            allow_duplicate=args.allow_duplicate,
        )
    except MT940Error as exc:
        print(f"status=error\nexit_code={exc.exit_code}\nmessage={exc}", file=sys.stderr)
        raise SystemExit(exc.exit_code) from exc
    except (OSError, json.JSONDecodeError) as exc:
        print(f"status=error\nexit_code=2\nmessage={exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    print(f"created={output}")
    print(f"sidecar={sidecar}")
    print(f"transactions={report['transaction_count']}")
    print(f"fingerprint_sha256={report['fingerprint_sha256']}")
    print("output_charset=Windows-1252")
    print("byte_roundtrip_match=true")
    print("status=generated")


if __name__ == "__main__":
    main()
