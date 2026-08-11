#!/usr/bin/env python3
"""Build deterministic MT940/STA output and a fingerprint sidecar."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from mt940_common import (
    MT940Error,
    expected_lines,
    fingerprint,
    normalize_manifest,
    output_filename,
    sidecar_filename,
    transaction_metrics,
)


def build(data: dict[str, Any], profile_dir: Path | None = None) -> tuple[bytes, dict[str, Any]]:
    normalized = normalize_manifest(data, profile_dir)
    lines = expected_lines(normalized)
    payload = ("\r\n".join(lines) + "\r\n").encode("cp1252", errors="strict")
    reconstructed = payload.decode("cp1252").split("\r\n")[:-1]
    if reconstructed != lines:
        raise MT940Error("Generated file failed the full-file roundtrip check", 3)
    report = {
        "schema_version": 1,
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
        "field86_mode": normalized["_field86_mode"],
        "output_scope": normalized["_output_scope"],
        "technical_validation": "generation checks passed; independent validation pending",
        "datev_probe_import": (
            "documented in verified profile"
            if normalized.get("_profile")
            else "not verified; test import required"
        ),
        "transactions": transaction_metrics(normalized),
    }
    return payload, report


def find_duplicate_fingerprint(
    fingerprint_sha256: str, directories: list[Path], intended_sidecar: Path
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
        report["fingerprint_sha256"], [output_path.parent, Path.cwd()], sidecar_path
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
    report.update(
        {
            "manifest": str(manifest_path),
            "mt940_file": str(output_path),
        }
    )
    sidecar_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return output_path, sidecar_path, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path, nargs="?")
    parser.add_argument("--profile-dir", type=Path)
    parser.add_argument("--allow-duplicate", action="store_true")
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
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
    print("status=generated")


if __name__ == "__main__":
    main()
