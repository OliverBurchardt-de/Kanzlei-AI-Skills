from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import build_package
from test_datev_contract import write_pdf


def source_item(path: Path, source_id: str) -> dict:
    raw = path.read_bytes()
    return {
        "source_id": source_id,
        "source_path": str(path),
        "size_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "readability": "readable",
    }


def transaction(transaction_id: str, period: str = "2026-07") -> dict:
    return {
        "transaction_id": transaction_id,
        "document_type": "Rechnung",
        "partner": "Test GmbH",
        "recognized_date": f"{period}-15",
        "total_amount": "119.00",
        "currency": "EUR",
        "period": period,
        "processing_status": "Buchungszeile erzeugt",
        "traffic_light": "Grün",
        "derivation": "Eindeutige Testkontierung",
        "reason": "Kontierung, Betrag und Umsatzsteuer sind eindeutig.",
        "business_purpose_status": "betrieblich",
        "input_tax_treatment": "volle_vorsteuer",
        "entity_assessment": {
            "legal_entity": "Test GmbH",
            "addressee": "Test GmbH",
            "relevance": "in_scope",
        },
        "duplicate_checks": {
            "file_hash_current_upload": {"checked": True, "result": "no_hit", "reference": ""},
            "logical_document_current_upload": {"checked": True, "result": "no_hit", "reference": ""},
            "datev_live": {"checked": True, "result": "no_hit", "reference": ""},
        },
        "prior_booking_check": {
            "checked": True,
            "result": "kein_treffer",
            "references": [],
        },
        "bookings": [
            {
                "amount": "119.00",
                "debit_credit": "S",
                "account": "4900",
                "account_name": "Aufwand",
                "contra_account": "70001",
                "contra_account_name": "Test GmbH",
                "bu_key": "401",
                "document_field_1": transaction_id,
                "booking_text": "Testbuchung",
            }
        ],
    }


def normalized_data(source_files: list[dict], transactions: list[dict], mappings: list[dict]) -> dict:
    return build_package.normalize_input_model({
        "run": {"buchungsmonat": "2026-07", "mandantennummer": "12345"},
        "scope": {
            "target_periods": ["2026-06", "2026-07"],
            "include_prior_periods": False,
            "include_future_periods": False,
            "job_mode": "belegbuchhaltung",
        },
        "mandantenprofil": {
            "status": "existing",
            "source_status": "found",
            "approval_status": "approved",
            "evidence": [],
        },
        "source_files": source_files,
        "transactions": transactions,
        "transaction_sources": mappings,
    })


def test_profile_first_run() -> None:
    data = {
        "run": {"provisional_profile_verified": True},
        "mandantenprofil": {
            "status": "provisional_first_run",
            "source_status": "confirmed_not_found",
            "approval_status": "pending",
            "evidence": ["DATEV live"],
        },
        "provisional_profile": {
            "content_markdown": "# Mandantenprofil\n\nVorläufige Regel.",
            "sources": ["DATEV live", "Nutzerangabe"],
            "provisional_rules": ["Vorläufige Regel"],
            "sharepoint_write_approved": False,
        },
    }
    build_package.validate_profile_contract(data)
    summary = build_package._confirmed_not_found_evidence(
        {
            "status": "not_found",
            "source_url": "https://example.test/profile.md",
            "file_name": "13481.md",
            "retrieved_via": "sharepoint.direct",
            "checked_at": "2026-08-11T10:00:00+02:00",
            "not_found_code": "itemNotFound",
            "site_verified": True,
            "library_verified": True,
            "direct_lookup_attempts": 2,
        },
        expected_url="https://example.test/profile.md",
        expected_name="13481.md",
        label="Mandantenprofil",
    )
    assert summary["status"] == "not_found"
    try:
        build_package._confirmed_not_found_evidence(
            {"status": "connector_error"},
            expected_url="https://example.test/profile.md",
            expected_name="13481.md",
            label="Mandantenprofil",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Connectorfehler darf keinen Erstlauf freigeben")


def test_scope_and_payment() -> None:
    may = transaction("V-MAI", "2026-05")
    may.update({
        "processing_status": "außerhalb Auftragszeitraum",
        "traffic_light": None,
        "bookings": [],
        "exclusion_reason": "außerhalb Auftragszeitraum",
    })
    data = {
        "scope": {
            "target_periods": ["2026-06", "2026-07"],
            "include_prior_periods": False,
            "include_future_periods": False,
            "job_mode": "belegbuchhaltung",
        },
        "documents": [may, transaction("V-JULI")],
    }
    assert build_package.validate_scope(data) == []
    may["processing_status"] = "Buchungszeile erzeugt"
    assert any("außerhalb" in item for item in build_package.validate_scope(data))

    green = transaction("V-GRUEN")
    payment_data = {
        "payment_reconciliation": {
            "statement_type": "credit_card",
            "status": "missing",
            "periods": ["2026-07"],
            "affects_document_traffic_light": False,
            "handoff_required": True,
            "note": "Kreditkartenabrechnung fehlt",
        },
        "documents": [green],
    }
    assert build_package.validate_payment_reconciliation(payment_data) == []
    green["traffic_light"] = "Rot"
    green["reason"] = "Kreditkartenabrechnung fehlt"
    assert any("ausschließlich" in item for item in build_package.validate_payment_reconciliation(payment_data))


def test_source_transaction_transfer(temp: Path) -> None:
    invoice = write_pdf(temp / "invoice.pdf", "invoice")
    email = temp / "email.txt"
    email.write_text("email", encoding="utf-8")
    data = normalized_data(
        [source_item(invoice, "S1"), source_item(email, "S2")],
        [transaction("V1")],
        [
            {"transaction_id": "V1", "source_id": "S1", "role": "primary_invoice"},
            {"transaction_id": "V1", "source_id": "S2", "role": "supporting_document"},
        ],
    )
    assert len(data["documents"][0]["source_paths"]) == 2
    packages, index = build_package.prepare_document_transfer(data)
    # v1.4.1 Belegdateiregel: nur der Buchungsbeleg (eine PDF) geht nach DATEV; die Begleit-E-Mail nicht als eigener Beleg.
    assert sum(len(item["documents"]) for item in packages) == 1
    assert sum(1 for item in index if item.get("included")) == 1
    assert "Begleitdokument" in next(item for item in index if item["source_id"] == "S2")["reason"]

    # v1.4.1 Belegdateiregel: eine Sammeldatei darf nicht mehrere Buchungsbelege tragen.
    bundle = write_pdf(temp / "bundle.pdf", "three logical receipts")
    transactions = [transaction(f"V{number}") for number in range(1, 4)]
    mappings = [
        {"transaction_id": item["transaction_id"], "source_id": "S3", "role": "primary_invoice"}
        for item in transactions
    ]
    shared = normalized_data([source_item(bundle, "S3")], transactions, mappings)
    assert any("Sammeldatei" in item for item in build_package.validate_document_file_rule(shared))
    try:
        build_package.prepare_document_transfer(shared)
    except ValueError as exc:
        assert "Sammeldatei" in str(exc)
    else:
        raise AssertionError("Sammeldatei mit drei Buchungsbelegen wurde übertragen")
    # Korrektes Modell: Original als bundle_original, je Vorgang eine abgeleitete PDF.
    derived = [write_pdf(temp / f"V{number}.pdf", f"receipt {number}") for number in range(1, 4)]
    sources = [source_item(bundle, "S3")] + [
        {**source_item(path, f"D{number}"), "derived_from": {"source_ids": ["S3"], "method": "split", "pages": f"{number}-{number}"}}
        for number, path in enumerate(derived, start=1)
    ]
    mappings = [
        {"transaction_id": f"V{number}", "source_id": "S3", "role": "bundle_original"} for number in range(1, 4)
    ] + [
        {"transaction_id": f"V{number}", "source_id": f"D{number}", "role": "primary_invoice"} for number in range(1, 4)
    ]
    split_data = normalized_data(sources, [transaction(f"V{number}") for number in range(1, 4)], mappings)
    assert build_package.validate_input_inventory(split_data) == []
    assert build_package.validate_document_file_rule(split_data) == []
    packages, index = build_package.prepare_document_transfer(split_data)
    assert sum(len(item["documents"]) for item in packages) == 3
    assert sum(1 for item in index if item.get("included")) == 3
    assert next(item for item in index if item["source_id"] == "S3")["included"] is False
    guids = {item.get("document_guid") for item in split_data["documents"]}
    assert len(guids) == 3


def test_activity_and_handoff() -> None:
    doc = transaction("V1")
    doc["handoff_required"] = True
    data = {
        "_normalized_source_model": "canonical",
        "run": {"requested_entities": ["You Nie", "You Lie"]},
        "documents": [doc],
        "activity_report": {
            "datev_import_status": "Importpaket erstellt – noch nicht in DATEV importiert",
            "sources_used": ["hochgeladene Belege", "DATEV live"],
            "named_entities": [
                {"name": "You Nie", "variants": ["You Nie"], "findings": 1, "final_status": "Rechnung gebucht"},
                {"name": "You Lie", "variants": ["You Lie"], "findings": 0, "final_status": "keine Fundstelle"},
            ],
        },
        "handoffs": [
            {
                "source_ids": ["S1"],
                "transaction_ids": ["V1"],
                "period": "2026-07",
                "target_process": "Bankbuchhaltung / MT940",
                "reason": "Kontoauszug separat verarbeiten",
            }
        ],
    }
    assert build_package.validate_activity_and_handoffs(data) == []
    data["activity_report"]["named_entities"].pop()
    assert any("You Lie" in item for item in build_package.validate_activity_and_handoffs(data))


def test_entity_exclusion_and_kasse_boundary() -> None:
    run = {
        "vat_config": {"input_tax_deduction": "voll"},
        "account_config": {
            "private_expense": "4655",
            "clarification": "1590",
            "asset_accounts": ["0480"],
        },
    }
    booking = transaction("V-BUCHUNG")
    booking["source_path"] = "booking.pdf"
    assert build_package.validate_documents({
        "_normalized_source_model": "canonical",
        "run": run,
        "documents": [booking],
        "clarification_cases": [],
    }) == []

    payroll = transaction("V-LOHN")
    payroll.update({
        "source_path": "payroll.pdf",
        "document_type": "Lohnabrechnung",
        "processing_status": "nicht buchungsrelevant",
        "traffic_light": None,
        "bookings": [],
        "business_purpose_status": "unklar",
        "exclusion_reason": "Lohnunterlage – Übergabe an Lohnbuchhaltung",
        "handoff_required": True,
    })
    payroll.pop("duplicate_checks")
    payroll.pop("prior_booking_check")
    assert build_package.validate_documents({
        "_normalized_source_model": "canonical",
        "run": run,
        "documents": [payroll],
        "clarification_cases": [],
    }) == []

    scope = {
        "scope": {
            "target_periods": ["2026-07"],
            "include_prior_periods": False,
            "include_future_periods": False,
            "job_mode": "kassenbelegpaket",
        },
        "documents": [],
    }
    assert any("Kasse" in item for item in build_package.validate_scope(scope))

def main() -> None:
    test_profile_first_run()
    test_scope_and_payment()
    with tempfile.TemporaryDirectory(prefix="bk_v110_contract_") as temp_name:
        test_source_transaction_transfer(Path(temp_name))
    test_activity_and_handoff()
    print("v1.1 product feedback contract: OK")


if __name__ == "__main__":
    main()
