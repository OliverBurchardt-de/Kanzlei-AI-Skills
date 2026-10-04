#!/usr/bin/env python3
"""Generate, independently validate, then persist a new source-checked bank model."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import re
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

from mt940_common import MT940Error, normalize_manifest, output_filename, entry_line
from reconstruction import DEFAULT_RULES, fill_missing
from source_check import read_source_review

def script_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

builder = script_module("learning_builder", "build-mt940.py")
validator = script_module("learning_validator", "validate-mt940.py")

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def learn(data, manifest_path, source_review_path, adapter_path, profile_dir, output_dir):
    # Verify original bytes before generation; the review remains untouched.
    review = read_source_review(source_review_path, allow_reconstruction=True)
    name = data.get("bank_profile", "")
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9-]+", name) or not data.get("bank_name"):
        raise MT940Error("Learning requires bank_profile and bank_name from the source", 4)
    adapter_name = name + ".py"
    destination = profile_dir / (name + ".json")
    if destination.exists():
        existing = json.loads(destination.read_text(encoding="utf-8"))
        if existing.get("status") != "draft":
            raise MT940Error("Model already checked; reuse it or select a new variant/version", 4)
        if existing.get("test_fixture_only"):
            raise MT940Error("A synthetic fixture cannot become a real bank model", 4)
    if data.get("source_type") not in {"pdf", "image", "structured_list", "manual"}:
        raise MT940Error("Reconstruction learning requires a statement/list, not native MT940", 4)
    rules = data.get("reconstruction_rules", DEFAULT_RULES)
    candidate = fill_missing(data, rules)
    candidate.update(field86_mode="reconstructed", output_scope="full", generation_allowed=True)
    candidate.pop("preparation_status", None)
    candidate.pop("delivery_approved", None)
    mappings = {
        "statement_reference": "Technical MT + period end + last six IBAN characters + statement number; not an original bank reference -> :20:",
        "iban": "Exact source IBAN -> :25:",
        "statement_number": "Source value or documented technical sequence -> :28C:",
        "sequence_number": "Source value or documented technical sequence -> :28C:",
        "opening_balance_date": "Source date or documented period convention -> :60F:",
        "opening_balance": "Exact signed opening balance -> :60F:",
        "closing_balance_date": "Source date or documented period convention -> :62F:",
        "closing_balance": "Exact signed closing balance -> :62F:",
        "currency": "Exact source currency -> balance fields",
        "value_date": "Source valuta or documented booking-date convention -> :61:",
        "booking_date": "Exact source booking date -> :61: MMDD; full year in review",
        "amount": "Exact source signed amount -> :61:",
        "code": "Source code or documented NMSC technical fallback -> :61:",
        "customer_reference": "Exact short source reference or NONREF when absent; original long reference stays in full text",
        "bank_reference": "Exact short source reference or technical nine-digit transaction index when absent",
        "description": "All visible source text, in original order, losslessly wrapped in unstructured :86:",
    }
    for tx in candidate["transactions"]:
        for key in tx.get("source_fields", {}):
            mappings[key] = "Named original value in full :86: text; independently decoded by this bank/variant adapter"
    profile = {
        "profile_name": name, "bank_name": data["bank_name"],
        **{key:data[key] for key in ("bank_id","source_variant","profile_version")},
        "source_types":[data["source_type"]], "status":"draft",
        "reference_basis": {"kind":"source_reconstruction", "reference":str(source_review_path.resolve()), "verified_against_reference":False},
        "field86_structure":"unstructured", "charset":"Windows-1252", "line_endings":"CRLF",
        "field_mappings":mappings, "statement_reference_rule":"deterministic_mt",
        "reference_rules":{"customer_reference":"exact","bank_reference":"source_or_sequence_9"},
        "missing_customer_reference":"NONREF", "allowed_underfields":[],
        "reconstruction_rules":rules, "adapter":adapter_name, "adapter_sha256":digest(adapter_path),
        "examples":[], "probe_import":{"result":"not_performed","test_transactions_deleted":False},
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mt940-learning-") as directory:
        stage = Path(directory)
        save(stage/(name+".json"), profile)
        shutil.copyfile(adapter_path, stage/adapter_name)
        normalized = normalize_manifest(candidate, stage)
        payload, _ = builder.build(candidate, stage)
        path = stage/output_filename(normalized)
        path.write_bytes(payload)
        checked = validator.validate(path, candidate, stage, source_review_path)
        # A complete original/actual-byte comparison is the promotion gate.
        if not checked["source_check"]["source_to_mt940_match"]:
            raise MT940Error("Source comparison failed; model stays unconfirmed", 2)
        evidence = output_dir/(name+"-reference-evidence.json")
        checked["reference_mt940_sha256"] = digest(path)
        checked["source_review_sha256"] = digest(source_review_path)
        checked["reference_source_review"] = str(source_review_path.resolve())
        save(evidence, checked)
        # Keep fixed source/output examples for every transaction type and long text.
        profile["examples"] = [
            {"source_transaction":copy.deepcopy(tx), "mt940":[entry_line(norm), *norm["_field86"].lines]}
            for tx,norm in zip(candidate["transactions"], normalized["_transactions"])
        ]
        profile["status"] = "source_verified"
        profile["reference_basis"].update(
            reference=str(evidence.resolve()), reference_sha256=digest(evidence),
            verified_against_reference=True, validation_date=data.get("validation_date", date.today().isoformat()),
        )
        save(stage/(name+".json"), profile)
        final_path = output_dir/output_filename(normalize_manifest(candidate, stage))
        # Use the normal duplicate safeguard only for the finished output, not retries.
        builder.write_artifacts(candidate, manifest_path, final_path, profile_dir=stage)
        report = validator.validate(final_path, candidate, stage, source_review_path)
        if not report["delivery_approved"]:
            raise MT940Error("Completed reconstruction was not approved by source validation", 2)
        # Store the reusable model only after generation AND full source validation.
        profile_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(stage/adapter_name, profile_dir/adapter_name)
        save(destination, profile)
        save(manifest_path, candidate)
        normalized = normalize_manifest(candidate, profile_dir)
        report_path = output_dir/validator.sidecar_filename(normalized)
        save(report_path, report)
    return final_path, report_path, destination

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--source-review", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--profile-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = learn(json.loads(args.manifest.read_text(encoding="utf-8")),args.manifest,
                       args.source_review,args.adapter,args.profile_dir,args.output_dir)
        for key,path in zip(("mt940","report","model"),result):
            print(f"{key}={path}")
    except MT940Error as exc:
        print(f"exit_code={exc.exit_code}\nmessage={exc}",file=sys.stderr)
        raise SystemExit(exc.exit_code) from exc
    except (OSError,ValueError,KeyError) as exc:
        print(f"exit_code=2\nmessage={exc}",file=sys.stderr)
        raise SystemExit(2) from exc

if __name__ == "__main__":
    main()
