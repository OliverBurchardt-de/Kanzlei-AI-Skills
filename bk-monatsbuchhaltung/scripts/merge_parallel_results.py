#!/usr/bin/env python3
"""Validate and merge isolated subagent results into one reconciliation draft."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.2"
MERGED_LIST_FIELDS = (
    "transactions",
    "transaction_sources",
    "clarification_cases",
    "handoffs",
    "profile_suggestions",
    "accrual_candidates",
    "technical_incidents",
)
FORBIDDEN_RESULT_FIELDS = {"source_files", "master_records", "run", "scope"}
SOURCE_ROLES = {
    "primary_invoice",
    "supporting_document",
    "payment_notice",
    "cover_sheet",
    "duplicate_copy",
    "bundle_original",
    "converted_original",
}


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"JSON kann nicht gelesen werden: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"JSON-Wurzel muss ein Objekt sein: {path}")
    return payload


def inventory_fingerprint(
    sources: list[dict[str, Any]], shared_context_fingerprint: str
) -> str:
    import hashlib

    digest = hashlib.sha256()
    digest.update(shared_context_fingerprint.encode("ascii"))
    digest.update(b"\n")
    for source in sources:
        digest.update(str(source.get("source_id", "")).encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(source.get("sha256", "")).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def normalized_text(value: Any) -> str:
    normalized = unicodedata.normalize("NFKC", str(value)).casefold()
    return "".join(character for character in normalized if character.isalnum())


def normalized_amount(value: Any) -> str:
    try:
        return format(Decimal(str(value).replace(",", ".")).normalize(), "f")
    except (InvalidOperation, ValueError):
        return ""


def document_reference(transaction: dict[str, Any]) -> str:
    direct = str(transaction.get("document_field_1", "")).strip()
    if direct:
        return direct
    bookings = transaction.get("bookings", [])
    if isinstance(bookings, list):
        for booking in bookings:
            if isinstance(booking, dict) and str(booking.get("document_field_1", "")).strip():
                return str(booking["document_field_1"]).strip()
    return ""


def logical_duplicate_candidates(transactions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    signatures: dict[tuple[str, str, str, str], list[str]] = defaultdict(list)
    for transaction in transactions:
        signature = (
            normalized_text(transaction.get("partner", "")),
            normalized_text(document_reference(transaction)),
            str(transaction.get("recognized_date", "")).strip(),
            normalized_amount(transaction.get("total_amount", "")),
        )
        if all(signature):
            signatures[signature].append(str(transaction.get("transaction_id", "")))
    return [
        {
            "partner_key": signature[0],
            "document_reference_key": signature[1],
            "recognized_date": signature[2],
            "total_amount": signature[3],
            "transaction_ids": transaction_ids,
        }
        for signature, transaction_ids in sorted(signatures.items())
        if len(transaction_ids) > 1
    ]


def consolidate_person_proposals(
    proposals: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    conflicts: list[dict[str, Any]] = []
    for proposal in proposals:
        partner = str(proposal.get("partner", "")).strip()
        account_type = str(proposal.get("account_type", "")).strip().casefold()
        if not partner or account_type not in {"debtor", "creditor"}:
            raise ValueError("Personenkontenvorschlag benötigt partner und account_type debtor|creditor")
        key = (normalized_text(partner), account_type)
        current = grouped.get(key)
        transaction_ids = sorted({str(value) for value in proposal.get("transaction_ids", [])})
        vat_id = str(proposal.get("vat_id", "")).strip()
        banks = proposal.get("banks", [])
        if not isinstance(banks, list):
            raise ValueError(f"Personenkontenvorschlag {partner}: banks muss eine Liste sein")
        if current is None:
            current = dict(proposal)
            current["partner"] = partner
            current["account_type"] = account_type
            current["transaction_ids"] = transaction_ids
            current["banks"] = banks
            grouped[key] = current
            continue
        current["transaction_ids"] = sorted(
            set(current.get("transaction_ids", [])) | set(transaction_ids)
        )
        current_vat = str(current.get("vat_id", "")).strip()
        if current_vat and vat_id and current_vat != vat_id:
            conflicts.append(
                {
                    "partner": partner,
                    "account_type": account_type,
                    "field": "vat_id",
                    "values": sorted({current_vat, vat_id}),
                }
            )
        elif vat_id and not current_vat:
            current["vat_id"] = vat_id
        bank_keys = {json.dumps(item, ensure_ascii=False, sort_keys=True) for item in current["banks"]}
        for bank in banks:
            key_text = json.dumps(bank, ensure_ascii=False, sort_keys=True)
            if key_text not in bank_keys:
                current["banks"].append(bank)
                bank_keys.add(key_text)
    return [grouped[key] for key in sorted(grouped)], conflicts


def validate_result(
    result: dict[str, Any], batch: dict[str, Any]
) -> tuple[dict[str, list[Any]], list[dict[str, Any]], list[Any]]:
    batch_id = str(batch["batch_id"])
    if result.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"{batch_id}: schema_version muss {SCHEMA_VERSION} sein")
    if result.get("batch_id") != batch_id:
        raise ValueError(f"{batch_id}: Ergebnis enthält falsche batch_id")
    if result.get("inventory_fingerprint") != batch.get("inventory_fingerprint"):
        raise ValueError(f"{batch_id}: Ergebnis gehört nicht zur aktuellen Inventur")
    forbidden = sorted(FORBIDDEN_RESULT_FIELDS & set(result))
    if forbidden:
        raise ValueError(f"{batch_id}: unzulässige Ergebnisfelder: {', '.join(forbidden)}")
    for field in (*MERGED_LIST_FIELDS, "person_account_proposals", "batch_notes"):
        if not isinstance(result.get(field, []), list):
            raise ValueError(f"{batch_id}: {field} muss eine Liste sein")

    allowed_sources = {str(value) for value in batch["source_ids"]}
    transaction_prefix = f"{batch_id}-V"
    clarification_prefix = f"{batch_id}-K"
    accrual_prefix = f"{batch_id}-A"
    profile_prefix = f"{batch_id}-P"
    transactions = result.get("transactions", [])
    transaction_ids: set[str] = set()
    for transaction in transactions:
        if not isinstance(transaction, dict):
            raise ValueError(f"{batch_id}: transaction ist kein Objekt")
        transaction_id = str(transaction.get("transaction_id", ""))
        if not re.fullmatch(re.escape(transaction_prefix) + r"\d{6}", transaction_id):
            raise ValueError(f"{batch_id}: ungültige Vorgangs-ID {transaction_id}")
        if transaction_id in transaction_ids:
            raise ValueError(f"{batch_id}: doppelte Vorgangs-ID {transaction_id}")
        transaction_ids.add(transaction_id)

    covered_sources: set[str] = set()
    mappings_seen: set[tuple[str, str, str]] = set()
    for mapping in result.get("transaction_sources", []):
        if not isinstance(mapping, dict):
            raise ValueError(f"{batch_id}: transaction_source ist kein Objekt")
        transaction_id = str(mapping.get("transaction_id", ""))
        source_id = str(mapping.get("source_id", ""))
        role = str(mapping.get("role", ""))
        if transaction_id not in transaction_ids:
            raise ValueError(f"{batch_id}: Zuordnung verweist auf unbekannten Vorgang {transaction_id}")
        if source_id not in allowed_sources:
            raise ValueError(f"{batch_id}: Zuordnung greift auf fremde Quelle {source_id} zu")
        if role not in SOURCE_ROLES:
            raise ValueError(f"{batch_id}: ungültige Dokumentrolle {role}")
        key = (transaction_id, source_id, role)
        if key in mappings_seen:
            raise ValueError(f"{batch_id}: doppelte Quellenzuordnung {key}")
        mappings_seen.add(key)
        covered_sources.add(source_id)
    mapped_transactions = {transaction_id for transaction_id, _, _ in mappings_seen}
    missing_transaction_sources = sorted(transaction_ids - mapped_transactions)
    if missing_transaction_sources:
        raise ValueError(
            f"{batch_id}: Vorgänge ohne Quellenzuordnung: {', '.join(missing_transaction_sources)}"
        )
    missing_sources = sorted(allowed_sources - covered_sources)
    if missing_sources:
        raise ValueError(f"{batch_id}: Quellen ohne Vorgangszuordnung: {', '.join(missing_sources)}")

    clarification_ids: set[str] = set()
    for case in result.get("clarification_cases", []):
        if not isinstance(case, dict):
            raise ValueError(f"{batch_id}: clarification_case ist kein Objekt")
        case_id = str(case.get("case_id", ""))
        if not re.fullmatch(re.escape(clarification_prefix) + r"\d{6}", case_id):
            raise ValueError(f"{batch_id}: ungültige Klärungsfall-ID {case_id}")
        if case_id in clarification_ids:
            raise ValueError(f"{batch_id}: doppelte Klärungsfall-ID {case_id}")
        clarification_ids.add(case_id)
        unknown = {str(value) for value in case.get("transaction_ids", [])} - transaction_ids
        if unknown:
            raise ValueError(f"{batch_id}: Klärungsfall verweist auf fremde Vorgänge: {sorted(unknown)}")

    for handoff in result.get("handoffs", []):
        if not isinstance(handoff, dict):
            raise ValueError(f"{batch_id}: handoff ist kein Objekt")
        if {str(value) for value in handoff.get("source_ids", [])} - allowed_sources:
            raise ValueError(f"{batch_id}: Übergabe enthält fremde Quelle")
        if {str(value) for value in handoff.get("transaction_ids", [])} - transaction_ids:
            raise ValueError(f"{batch_id}: Übergabe enthält fremden Vorgang")

    accrual_ids: set[str] = set()
    for candidate in result.get("accrual_candidates", []):
        if not isinstance(candidate, dict):
            raise ValueError(f"{batch_id}: accrual_candidate ist kein Objekt")
        accrual_id = str(candidate.get("accrual_id", ""))
        if not re.fullmatch(re.escape(accrual_prefix) + r"\d{6}", accrual_id):
            raise ValueError(f"{batch_id}: ungültige Abgrenzungs-ID {accrual_id}")
        if accrual_id in accrual_ids:
            raise ValueError(f"{batch_id}: doppelte Abgrenzungs-ID {accrual_id}")
        accrual_ids.add(accrual_id)
        if {str(value) for value in candidate.get("transaction_ids", [])} - transaction_ids:
            raise ValueError(f"{batch_id}: Abgrenzung enthält fremden Vorgang")

    suggestion_ids: set[str] = set()
    for suggestion in result.get("profile_suggestions", []):
        if not isinstance(suggestion, dict):
            raise ValueError(f"{batch_id}: profile_suggestion ist kein Objekt")
        suggestion_id = str(suggestion.get("suggestion_id", ""))
        if not re.fullmatch(re.escape(profile_prefix) + r"\d{6}", suggestion_id):
            raise ValueError(f"{batch_id}: ungültige Profilvorschlags-ID {suggestion_id}")
        if suggestion_id in suggestion_ids:
            raise ValueError(f"{batch_id}: doppelte Profilvorschlags-ID {suggestion_id}")
        suggestion_ids.add(suggestion_id)
        if {str(value) for value in suggestion.get("transaction_ids", [])} - transaction_ids:
            raise ValueError(f"{batch_id}: Profilvorschlag enthält fremden Vorgang")

    proposals = result.get("person_account_proposals", [])
    for proposal in proposals:
        if not isinstance(proposal, dict):
            raise ValueError(f"{batch_id}: person_account_proposal ist kein Objekt")
        if {str(value) for value in proposal.get("transaction_ids", [])} - transaction_ids:
            raise ValueError(f"{batch_id}: Personenkontenvorschlag enthält fremden Vorgang")
        if "account" in proposal:
            raise ValueError(f"{batch_id}: Subagent darf keine neue Kontonummer vergeben")
    return (
        {field: list(result.get(field, [])) for field in MERGED_LIST_FIELDS},
        list(proposals),
        list(result.get("batch_notes", [])),
    )


def merge(inventory_path: Path, base_run_path: Path, results_dir: Path) -> dict[str, Any]:
    inventory = read_json(inventory_path)
    base_run = read_json(base_run_path)
    if inventory.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"Inventur schema_version muss {SCHEMA_VERSION} sein")
    for field in (*MERGED_LIST_FIELDS, "source_files", "master_records"):
        if field == "technical_incidents":
            continue  # Preflight-Fehler des Hauptagenten dürfen im base-run stehen
        if field in base_run and base_run[field]:
            raise ValueError(f"base-run darf keine vorbefüllte Liste {field} enthalten")
    batches = inventory.get("batches")
    sources = inventory.get("source_files")
    if not isinstance(batches, list) or not batches or not isinstance(sources, list):
        raise ValueError("Inventur enthält keine vollständigen Batches/source_files")
    source_ids = [str(source.get("source_id", "")) for source in sources]
    if any(not source_id for source_id in source_ids) or len(source_ids) != len(set(source_ids)):
        raise ValueError("Inventur enthält fehlende oder doppelte source_ids")
    shared_context_fingerprint = str(inventory.get("shared_context_fingerprint", ""))
    if not re.fullmatch(r"[0-9a-f]{64}", shared_context_fingerprint):
        raise ValueError("Inventur enthält keinen gültigen Arbeitskontext-Fingerprint")
    if base_run.get("_parallel_context_fingerprint") != shared_context_fingerprint:
        raise ValueError(
            "base-run gehört nicht zum verifizierten Arbeitskontext der Inventur"
        )
    declared_fingerprint = str(inventory.get("inventory_fingerprint", ""))
    if inventory_fingerprint(sources, shared_context_fingerprint) != declared_fingerprint:
        raise ValueError("Inventur-Fingerprint stimmt nicht mit source_files überein")
    assigned_sources: list[str] = []
    source_batches: dict[str, str] = {}
    for batch in batches:
        batch_id = str(batch.get("batch_id", ""))
        batch["inventory_fingerprint"] = declared_fingerprint
        for source_id in batch.get("source_ids", []):
            source_text = str(source_id)
            assigned_sources.append(source_text)
            source_batches[source_text] = batch_id
    if len(assigned_sources) != len(set(assigned_sources)) or set(assigned_sources) != set(source_ids):
        raise ValueError("Batchzuordnung muss jede Inventurquelle genau einmal enthalten")
    for source in sources:
        source_id = str(source["source_id"])
        if str(source.get("batch_id", "")) != source_batches[source_id]:
            raise ValueError(f"{source_id}: batch_id widerspricht der zentralen Batchzuordnung")
    for group in inventory.get("duplicate_hash_groups", []):
        group_batches = {source_batches.get(str(value)) for value in group.get("source_ids", [])}
        if len(group_batches) > 1:
            raise ValueError("Identische Hashgruppe wurde auf mehrere Batches verteilt")
    expected_ids = {str(batch.get("batch_id", "")) for batch in batches}
    result_files = sorted(results_dir.glob("batch_*_result.json"))
    results_by_id: dict[str, dict[str, Any]] = {}
    for path in result_files:
        result = read_json(path)
        batch_id = str(result.get("batch_id", ""))
        if batch_id in results_by_id:
            raise ValueError(f"Mehrere Ergebnisdateien für {batch_id}")
        results_by_id[batch_id] = result
    missing = sorted(expected_ids - set(results_by_id))
    extra = sorted(set(results_by_id) - expected_ids)
    if missing or extra:
        details = []
        if missing:
            details.append("fehlend: " + ", ".join(missing))
        if extra:
            details.append("unbekannt: " + ", ".join(extra))
        raise ValueError("Batch-Ergebnisse unvollständig (" + "; ".join(details) + ")")

    merged_lists: dict[str, list[Any]] = {field: [] for field in MERGED_LIST_FIELDS}
    all_proposals: list[dict[str, Any]] = []
    batch_notes: list[dict[str, Any]] = []
    seen_transactions: set[str] = set()
    seen_cases: set[str] = set()
    for batch in sorted(batches, key=lambda item: str(item["batch_id"])):
        batch_id = str(batch["batch_id"])
        lists, proposals, notes = validate_result(results_by_id[batch_id], batch)
        for transaction in lists["transactions"]:
            transaction_id = str(transaction["transaction_id"])
            if transaction_id in seen_transactions:
                raise ValueError(f"Globale doppelte Vorgangs-ID {transaction_id}")
            seen_transactions.add(transaction_id)
        for case in lists["clarification_cases"]:
            case_id = str(case["case_id"])
            if case_id in seen_cases:
                raise ValueError(f"Globale doppelte Klärungsfall-ID {case_id}")
            seen_cases.add(case_id)
        for field in MERGED_LIST_FIELDS:
            merged_lists[field].extend(lists[field])
        all_proposals.extend(proposals)
        batch_notes.extend({"batch_id": batch_id, "note": note} for note in notes)

    consolidated_proposals, proposal_conflicts = consolidate_person_proposals(all_proposals)
    merged = dict(base_run)
    merged["source_files"] = sources
    merged.update(merged_lists)
    merged["technical_incidents"] = list(base_run.get("technical_incidents", []) or []) + merged_lists["technical_incidents"]
    merged["person_account_proposals"] = consolidated_proposals
    merged["_parallel_review"] = {
        "schema_version": SCHEMA_VERSION,
        "inventory_fingerprint": inventory.get("inventory_fingerprint"),
        "shared_context_fingerprint": inventory.get("shared_context_fingerprint"),
        "completed_batches": sorted(expected_ids),
        "global_reconciliation_required": True,
        "duplicate_hash_groups": inventory.get("duplicate_hash_groups", []),
        "logical_duplicate_candidates": logical_duplicate_candidates(
            merged_lists["transactions"]
        ),
        "person_account_conflicts": proposal_conflicts,
        "batch_notes": batch_notes,
    }
    return merged


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--base-run", required=True, type=Path)
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        merged = merge(args.inventory, args.base_run, args.results_dir)
        write_json(args.output, merged)
    except (OSError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    print(
        f"Parallel-Ergebnisse zusammengeführt: {len(merged['transactions'])} Vorgänge; "
        "globale fachliche Konsolidierung erforderlich"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
