"""Read actual MT940 fields and compare them with separately reviewed original data.

This module never calls the output generator or derives evidence from its manifest.
PDF transcription still requires an honest visual review of the original pages.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from mt940_common import MT940Error, canonical_description, native_field86_result, parse_date, parse_money


BALANCE_RE = re.compile(r"^:(60F|62F):([CD])(\d{6})([A-Z]{3})(\d+,\d{2})$")
ENTRY_RE = re.compile(r"^:61:(\d{6})(\d{4})([CD])(\d+,\d{2})(N[A-Z0-9]{3})([^/]{1,16})//([^/]{1,16})$")


def read_source_review(path: Path | None, *, allow_reconstruction: bool = False) -> dict[str, Any]:
    if path is None:
        raise MT940Error("Delivery blocked: --source-review is required; manifest roundtrip alone is insufficient", 2)
    try:
        review = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MT940Error(f"Cannot read separate source review: {exc}", 2) from exc
    if not isinstance(review, dict) or review.get("reviewed_against_original") is not True:
        raise MT940Error("Source review must be checked independently against the original", 2)
    if review.get("review_method") not in {"visual_original", "native_field_extraction"}:
        raise MT940Error("Source review requires visual_original or native_field_extraction", 2)
    files = review.get("source_files")
    if not isinstance(files, list) or not files:
        raise MT940Error("Source review requires original source_files with SHA-256", 2)
    ids: set[str] = set()
    for item in files:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"] or item["id"] in ids:
            raise MT940Error("Source file IDs must be non-empty and unique", 2)
        ids.add(item["id"])
        if not isinstance(item.get("path"), str) or not item["path"]:
            raise MT940Error("Original source file path missing", 2)
        original = Path(item["path"])
        if not original.is_absolute():
            original = path.parent / original
        try:
            digest = hashlib.sha256(original.read_bytes()).hexdigest()
        except OSError as exc:
            raise MT940Error(f"Original source file unavailable: {original}", 2) from exc
        if digest != item.get("sha256"):
            raise MT940Error(f"Original source hash mismatch: {original}", 2)
    transactions = review.get("transactions")
    if not isinstance(transactions, list):
        raise MT940Error("Source review transactions must be a list", 2)
    locators: set[tuple[str, str]] = set()
    for field in ("statement_start", "statement_end", "opening_balance_date", "closing_balance_date"):
        if allow_reconstruction and field.endswith("balance_date") and review.get(field) is None:
            continue
        parse_date(review.get(field), f"source_review.{field}")
    for field in ("opening_balance", "closing_balance"):
        parse_money(review.get(field), f"source_review.{field}")
    for number, tx in enumerate(transactions, 1):
        if not isinstance(tx, dict) or tx.get("source_file") not in ids or not isinstance(tx.get("source_locator"), str) or not tx["source_locator"].strip():
            raise MT940Error(f"Source transaction {number} needs source_file and a page/block/row locator", 2)
        locator = (tx["source_file"], tx["source_locator"])
        if locator in locators:
            raise MT940Error(f"Repeated source locator at transaction {number}", 2)
        locators.add(locator)
        for field in ("value_date", "booking_date"):
            if allow_reconstruction and field == "value_date" and tx.get(field) is None:
                continue
            parse_date(tx.get(field), f"source_review.transactions[{number}].{field}")
        parse_money(tx.get("amount"), f"source_review.transactions[{number}].amount")
        if not isinstance(tx.get("description"), str) or not tx["description"]:
            raise MT940Error(f"Source transaction {number} requires its complete description", 2)
        for field in ("customer_reference", "bank_reference"):
            if field not in tx or (tx[field] is not None and not isinstance(tx[field], str)):
                raise MT940Error(f"Source transaction {number} needs explicit {field} (text/null)", 2)
    return review


def parse_actual(lines: list[str], profile: dict[str, Any], native: bool) -> dict[str, Any]:
    """Parse the emitted supported subset, without rebuilding expected output."""
    result: dict[str, Any] = {"statement_reference": lines[0][4:], "iban": lines[1][4:]}
    statement, sequence = lines[2][5:].split("/")
    result.update(statement_number=int(statement), sequence_number=int(sequence))
    for line, prefix in ((lines[3], "opening"), (lines[-1], "closing")):
        match = BALANCE_RE.fullmatch(line)
        if not match:
            raise MT940Error(f"Cannot independently parse balance field: {line!r}", 3)
        _, sign, short_date, currency, amount = match.groups()
        result[f"{prefix}_balance_date"] = short_date
        result[f"{prefix}_balance"] = ("-" if sign == "D" else "") + amount.replace(",", ".")
        if "currency" in result and result["currency"] != currency:
            raise MT940Error("Balance fields use different currencies", 3)
        result["currency"] = currency
    transactions = []
    index = 4
    while index < len(lines) - 1:
        match = ENTRY_RE.fullmatch(lines[index])
        if not match:
            raise MT940Error(f"Cannot independently parse :61: at line {index + 1}", 3)
        value_date, booking_date, sign, amount, code, customer, bank = match.groups()
        index += 1
        group = []
        while index < len(lines) - 1 and not lines[index].startswith(":61:"):
            group.append(lines[index])
            index += 1
        native_field86_result(group)
        if native:
            extra = profile["_adapter"].decode_field86(group).get("source_fields", {}) if "_adapter" in profile else {}
            decoded = {"description": group[0][4:] + "".join(group[1:]), "source_fields": extra}
        else:
            try:
                decoded = profile["_adapter"].decode_field86(group)
            except Exception as exc:
                raise MT940Error(f"Cannot decode actual :86: with bank model: {exc}", 3) from exc
            if not isinstance(decoded, dict) or not isinstance(decoded.get("description"), str):
                raise MT940Error("Bank decoder returned no description", 3)
        transactions.append({"value_date": value_date, "booking_date": booking_date,
                             "amount": ("-" if sign == "D" else "") + amount.replace(",", "."),
                             "code": code, "customer_reference": customer, "bank_reference": bank,
                             "description": decoded["description"], "source_fields": decoded.get("source_fields", {}),
                             "native_field86_lines": group})
    result["transactions"] = transactions
    return result


def compare_source(lines: list[str], manifest: dict[str, Any], normalized: dict[str, Any],
                   review: dict[str, Any]) -> dict[str, Any]:
    profile = normalized["_profile"]
    native = normalized["_field86_mode"] == "native"
    reconstruction = normalized["_field86_mode"] == "reconstructed"
    from reconstruction import effective_source
    if manifest.get("source_type") in {"pdf", "image"} and review["review_method"] != "visual_original":
        raise MT940Error("PDF/image source fields require visual review against original pages", 2)
    actual = parse_actual(lines, profile, native)
    checks = []
    mismatches = []

    def compare(field: str, source: Any, manifest_value: Any, actual_value: Any,
                expected: Any = None, locator: str = "statement", effective: Any = None,
                derivation: Any = None) -> None:
        target = source if expected is None else expected
        effective_value = source if derivation is None else effective
        item = {"field": field, "source_locator": locator, "source_value": source,
                "manifest_value": manifest_value, "mt940_value": actual_value,
                "source_to_manifest_match": source == manifest_value,
                "source_to_effective_manifest_match": effective_value == manifest_value,
                "derivation": derivation,
                "source_to_mt940_match": target == actual_value}
        checks.append(item)
        if effective_value != manifest_value or target != actual_value:
            mismatches.append(item)

    for field in ("bank_id", "source_variant", "profile_version", "bank_profile"):
        if review.get(field) != manifest.get(field):
            raise MT940Error(f"Source review bank/model mismatch: {field}", 4)
    for field in ("statement_start", "statement_end"):
        if review.get(field) != manifest.get(field):
            raise MT940Error(f"Source review period mismatch: {field}", 2)
    for field in ("iban", "statement_number", "sequence_number", "currency",
                  "opening_balance_date", "opening_balance", "closing_balance_date", "closing_balance"):
        if field not in review:
            raise MT940Error(f"Separate source review missing statement field {field}", 2)
        value = review[field]
        effective, derivation = effective_source(field, value, manifest, review, None, profile) if reconstruction else (value, None)
        expected = parse_date(effective, field).strftime("%y%m%d") if field.endswith("_date") else effective
        compare(field, value, manifest.get(field), actual[field], expected, effective=effective, derivation=derivation)
    if profile["statement_reference_rule"] == "source":
        if not review.get("statement_reference"):
            raise MT940Error("Source review missing original statement_reference", 2)
        compare("statement_reference", review["statement_reference"], manifest.get("statement_reference"), actual["statement_reference"])
    else:
        number, _ = effective_source("statement_number", review["statement_number"], manifest, review, None, profile) if reconstruction else (review["statement_number"], None)
        expected = "MT" + review["statement_end"].replace("-", "")[2:] + review["iban"][-6:] + f"{number % 100:02d}"
        if actual["statement_reference"] != expected:
            raise MT940Error("Actual statement reference differs from the bank model rule", 2)
    if len(review["transactions"]) != len(actual["transactions"]) or len(review["transactions"]) != len(manifest["transactions"]):
        raise MT940Error("Transaction count differs between original, manifest and actual MT940", 2)
    for number, (source, tx, parsed) in enumerate(zip(review["transactions"], manifest["transactions"], actual["transactions"]), 1):
        locator = f"transaction {number}: {source['source_file']} / {source['source_locator']}"
        for field in ("value_date", "booking_date", "amount", "code", "customer_reference", "bank_reference", "description"):
            if field not in source:
                raise MT940Error(f"Source review missing {field} at {locator}", 2)
            value = source[field]
            manifest_value = tx.get(field)
            effective, derivation = effective_source(field, value, tx, review, source, profile) if reconstruction else (value, None)
            expected = effective
            if field in {"value_date", "booking_date"}:
                expected = parse_date(effective, field).strftime("%y%m%d" if field == "value_date" else "%m%d")
            elif field in {"customer_reference", "bank_reference"}:
                rule = profile["reference_rules"][field]
                if field == "customer_reference" and not value:
                    expected = profile.get("missing_customer_reference")
                elif rule == "source_or_sequence_9" and not value:
                    expected = f"{number:09d}"
                elif rule == "upper_alnum_16":
                    expected = re.sub(r"[^A-Z0-9]", "", value.upper())[:16]
            elif field == "description" and not native:
                value = canonical_description(value)
                manifest_value = canonical_description(tx.get("description", " ".join(tx.get("source_description_lines", []))))
                expected = value
            elif field == "description" and native and manifest_value is None:
                native_lines = tx.get("native_field86_lines", [])
                manifest_value = native_lines[0][4:] + "".join(native_lines[1:]) if native_lines else None
            compare(field, value, manifest_value, parsed[field], expected, locator, effective, derivation)
        source_fields = source.get("source_fields", {})
        if not isinstance(source_fields, dict):
            raise MT940Error(f"source_fields must be a named object at {locator}", 2)
        if not source_fields.keys() <= profile["field_mappings"].keys():
            raise MT940Error(f"Bank model has no mapping for all named source fields at {locator}", 4)
        compare("source_fields", source_fields, tx.get("source_fields", {}), parsed["source_fields"], locator=locator)
        if native:
            compare("native_field86_lines", source.get("native_field86_lines"), tx.get("native_field86_lines"), parsed["native_field86_lines"], locator=locator)
    if mismatches:
        first = mismatches[0]
        raise MT940Error(f"Source field mismatch at {first['source_locator']}, {first['field']}: "
                         f"source={first['source_value']!r}, manifest={first['manifest_value']!r}, "
                         f"actual_MT940={first['mt940_value']!r}; {len(mismatches)} mismatched fields", 2,
                         {"source_to_mt940_match": False, "mismatch_count": len(mismatches),
                          "field_comparisons": checks})
    return {"source_to_mt940_match": True, "checked_transaction_count": len(actual["transactions"]),
            "source_files": review["source_files"], "review_method": review["review_method"],
            "field_comparisons": checks}
