from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from openpyxl import load_workbook

import build_package
import datev_io
import validate_package
from sharepoint_target import build_targets
from test_datev_contract import booking_document, evidence


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="bk_v130_") as name:
        root = Path(name)
        profile = root / "12861.md"
        profile.write_text("# Synthetisches Testprofil\nEÜR, keine Kostenstellen.\n", encoding="utf-8")
        run = {
            "beraternummer": 29098, "mandantennummer": 12861,
            "buchungsmonat": "2025-12", "wirtschaftsjahr_beginn": "2025-01-01",
            "sachkontenlaenge": 4, "sachkontenrahmen": "03", "waehrung": "EUR",
            "accounting_method": "EÜR", "kostenstellenpflicht": False,
            "datev_connection_verified": True, "mandantenprofil_verified": True,
            "vat_config": {"sales_treatment": "steuerpflichtig", "input_tax_deduction": "voll", "default_domestic_input_treatment": "volle_vorsteuer"},
            "account_config": {"private_expense": "4655", "gwg": "0480", "asset_accounts": ["0480", "0500"]},
            "person_account_ranges": {"debitor": {"start": "10000", "end": "69999"}, "kreditor": {"start": "70000", "end": "99999"}},
            "mandantenprofil_evidence": evidence(profile, str(build_targets("12861")["profile_url"])),
        }
        run["datev_live_evidence"] = {
            **{key: run[key] for key in ("beraternummer", "mandantennummer", "wirtschaftsjahr_beginn", "sachkontenlaenge", "sachkontenrahmen")},
            "source": "DATEV live", "retrieved_at": "2026-10-07T10:00:00+02:00",
            "validated_accounts": ["4900", "4655", "70001"], "validated_bu_keys": ["401"],
            "highest_creditor_account": 70001, "highest_debtor_account": 10000,
            "used_person_accounts": [{"account": "70001", "account_type": "kreditor", "name": "DATEV Test GmbH"}],
            "master_data_checked": True, "master_data_records_found": 1,
            "prior_bookings_checked": True, "prior_booking_records_found": 0,
        }
        docs, sources, mappings, cases = [], [], [], []
        fields = [None, "account", "recognized_date", "bu_key", "amount", "document_field_1", "contra_account", "exchange_rate"]
        for number, field in enumerate(fields, start=1):
            source = root / f"beleg{number}.txt"
            source.write_text(f"Synthetischer Beleg {number}", encoding="utf-8")
            doc = booking_document(source, "Rot" if field else "Grün")
            doc["transaction_id"] = f"V{number:04d}"
            doc["entity_assessment"] = {"legal_entity": "Test", "addressee": "Test", "relevance": "in_scope"}
            doc["duplicate_checks"] = {key: {"checked": True, "result": "no_hit", "reference": ""} for key in ("file_hash_current_upload", "logical_document_current_upload", "datev_live")}
            if field:
                line = doc["bookings"][0]
                line["open_fields"] = {field: f"{field} muss anhand des Originalbelegs geklärt werden."}
                if field == "recognized_date":
                    doc[field] = None
                else:
                    line[field] = None
                if field == "account":
                    doc["asset_booking"] = True
                    line["asset_account_field"] = "account"
                    line["open_fields"][field] = "Anlagenzugang zuerst in der Anlagenvorerfassung anlegen; Vorschlag GWG."
                if field == "amount":
                    doc["total_amount"] = None
                if field == "document_field_1":
                    doc["invoice_number"] = None
                if field == "contra_account":
                    line["contra_account_name"] = None
                if field == "exchange_rate":
                    doc["currency"] = "USD"
                    line["base_amount"] = "109.48"
                doc["reason"] = f"Offene Angabe: {field}."
                cases.append({
                    "case_id": f"K{number}", "transaction_ids": [doc["transaction_id"]],
                    "topic": field, "facts": "Sichere Angaben im Buchungsstapel erhalten.",
                    "booking_risk": "Ohne Klärung kann die Buchung fachlich falsch sein.",
                    "provisional_treatment": "Bekannte Angaben exportiert, konkretes Feld offen.",
                    "recommendation": "Originalbeleg prüfen; Anlagenzugänge über Anlagenvorerfassung bearbeiten.",
                    "decision_needed": "Offenes Feld vervollständigen.", "traffic_light": "Rot",
                    "target": "Prüfungsdatei", "proposed_change": "Feld klären", "employee_result": "",
                })
            docs.append(doc)
            source_id = f"S{number}"
            sources.append({"source_id": source_id, "source_path": str(source), "size_bytes": source.stat().st_size, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "readability": "readable"})
            mappings.append({"transaction_id": doc["transaction_id"], "source_id": source_id, "role": "primary_invoice"})

        # Invalid states must fail before creating a package.
        for field, value in (("account", "0480"), ("account", "1590"), ("account", "4900")):
            bad = copy.deepcopy(docs[1])
            bad["bookings"][0][field] = value
            try:
                datev_io.booking_row(bad, bad["bookings"][0], run)
            except ValueError:
                pass
            else:
                raise AssertionError(f"Verbotener Zustand wurde exportiert: {field}={value}")
        yellow = copy.deepcopy(docs[0]); yellow["traffic_light"] = "Gelb"
        try:
            datev_io.booking_row(yellow, yellow["bookings"][0], run)
        except ValueError:
            pass
        else:
            raise AssertionError("Gelb wurde akzeptiert")
        instructional = copy.deepcopy(docs[0])
        instructional["bookings"][0]["booking_text"] = "Vorschlag Konto 0480; Anlagenvorerfassung"
        try:
            datev_io.booking_row(instructional, instructional["bookings"][0], run)
        except ValueError:
            pass
        else:
            raise AssertionError("Arbeitsanweisung wurde in den Buchungstext exportiert")

        data = {
            "run": run, "scope": {"target_periods": ["2025-12"], "job_mode": "belegbuchhaltung", "include_prior_periods": False, "include_future_periods": False},
            "source_files": sources, "transactions": docs, "transaction_sources": mappings,
            "clarification_cases": cases, "master_records": [],
            "activity_report": {"datev_import_status": "Importpaket erstellt – noch nicht in DATEV importiert", "sources_used": ["Synthetische Testbelege"], "named_entities": []},
        }
        input_path = root / "lauf.json"
        input_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        result = subprocess.run([sys.executable, str(Path(build_package.__file__)), "--input", str(input_path), "--output", str(root / "package")], capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert result.returncode == 0, result.stderr + result.stdout
        package = root / "package" / "12861_2025-12"
        import_files = list((package / "01_DATEV_Import").glob("EXTF_*.csv"))
        assert [path.name for path in import_files] == ["EXTF_Buchungsstapel_2025-12.csv"]
        rows = [validate_package.split_extf(line) for line in import_files[0].read_text(encoding="cp1252").splitlines()[2:]]
        assert len(rows) == len(docs)
        assert all(row[9] == "1512" for number, row in enumerate(rows) if number != 2)
        assert rows[2][9] == ""
        assert rows[1][6] == "" and rows[1][7] == "70001"
        assert rows[3][8] == "" and rows[3][6] == "4900"
        assert rows[4][0] == "" and rows[4][7] == "70001"
        report = json.loads((package / "03_Technische_Protokolle" / "Validierungsbericht.json").read_text(encoding="utf-8"))
        assert report["valid"] and report["datev_test_import_status"] == "pending"
        assert not report["datev_import_compatibility_confirmed"]
        workbook = load_workbook(next((package / "02_Buchungspruefung").glob("*.xlsx")))
        assert all(row[1].value == import_files[0].name for row in list(workbook["Belegprüfung"].rows)[1:])
        assert all(row[0].value in {"Grün", "Rot"} for row in list(workbook["Belegprüfung"].rows)[1:])
        assert "Anlagenvorerfassung" in " ".join(str(cell.value) for row in workbook["Belegprüfung"] for cell in row)
        workbook.close()
        manifest = json.loads((package / "03_Technische_Protokolle" / "Laufmanifest.json").read_text(encoding="utf-8"))
        manifest["booking_trace"][1]["traffic_light"] = "Grün"
        assert validate_package.validate_csv(import_files[0], manifest)[0]
        assert validate_package.validate_test_import({"status": "confirmed"}, import_files)

        # Accrual releases join the same month; they cannot create another CSV.
        accrual_root = root / "accrual"
        (accrual_root / "01_DATEV_Import").mkdir(parents=True)
        release = {**docs[0]["bookings"][0], "accrual_id": "A1", "period": "2025-12", "booking_date": "2025-12-31"}
        trace = build_package.write_booking_batches(accrual_root, {"run": run, "documents": [docs[0]], "accrual_releases": [release]})
        assert len(list((accrual_root / "01_DATEV_Import").glob("*.csv"))) == 1
        assert len(trace) == 2 and trace[1]["kind"] == "accrual"
    print("v1.3 export, open fields, asset workflow, workbook and import-evidence tests: OK")


if __name__ == "__main__":
    main()
