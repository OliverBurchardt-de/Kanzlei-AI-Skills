from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import build_package
import datev_io
import validate_package
from sharepoint_target import build_targets


def evidence(path: Path, url: str) -> dict:
    raw = path.read_bytes()
    return {
        "source_url": url,
        "file_name": path.name,
        "file_uri": f"sharepoint://{path.name}",
        "retrieved_via": "microsoft_sharepoint.fetch",
        "download_raw_file": True,
        "raw_file_path": str(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


MINIMAL_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]>>endobj\n"
)


def write_pdf(path: Path, text: str = "Testbeleg") -> Path:
    """Synthetische PDF-Belegdatei (Belegdateiregel: ein Buchungsbeleg = eine PDF)."""
    path.write_bytes(MINIMAL_PDF + b"% " + text.encode("utf-8") + b"\ntrailer<</Root 1 0 R>>\n%%EOF\n")
    return path


def red_reason(code: str = "konto_unklar", **extra) -> dict:
    reason = {
        "code": code,
        "verification_attempted": "Belegbild, Mandantenprofil, DATEV-Vorbuchungen und Buchungsregeln geprüft.",
        "next_check": "Originalbeleg beim Mandanten anfordern und offenes Feld klären.",
    }
    reason.update(extra)
    return reason


def second_review(red_ids: list[str], corrections: list[dict] | None = None, cause: dict | None = None) -> dict:
    """Vollständige Zweitprüfung aller roten Vorgänge als Lauf-JSON-Block clarification_review."""
    return {
        "checked_at": "2026-10-08T10:00:00+02:00",
        "cause_analysis": cause or {},
        "second_review": {
            "performed": True,
            "performed_at": "2026-10-08T10:00:00+02:00",
            "basis": ["belegbild", "mandantenprofil", "datev_bestand", "buchungsregeln"],
            "reviewed_transaction_ids": list(red_ids),
            "corrections": corrections or [],
        },
    }


def booking_document(source: Path, light: str = "Grün") -> dict:
    result = {
        "transaction_id": "V0001",
        "source_path": str(source),
        "document_type": "Rechnung",
        "partner": "DATEV Test GmbH",
        "invoice_number": "RE-100",
        "recognized_date": "2025-12-15",
        "total_amount": "119.00",
        "currency": "EUR",
        "period": "2025-12",
        "processing_status": "Buchungszeile erzeugt",
        "traffic_light": light,
        "derivation": "119 EUR, Aufwand 4900 gegen Kreditor 70001, BU 401.",
        "reason": "Betrag, Kontierung und Steuerbehandlung sind eindeutig.",
        "business_purpose_status": "betrieblich",
        "input_tax_treatment": "volle_vorsteuer",
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
                "account_name": "Betriebsbedarf",
                "contra_account": "70001",
                "contra_account_name": "DATEV Test GmbH",
                "bu_key": "401",
                "document_field_1": "RE-100",
                "booking_text": "Betriebsbedarf DATEV Test",
            }
        ],
    }
    if light == "Rot":
        result["requires_clarification"] = True
        result["red_reason"] = red_reason()
    return result


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="bk_datev_contract_") as temp_name:
        temp = Path(temp_name)
        profile_dir = temp / "Mandantenprofile"
        accrual_dir = temp / "Abgrenzungsregister"
        profile_dir.mkdir()
        accrual_dir.mkdir()
        profile = profile_dir / "12861.md"
        accrual = accrual_dir / "12861.md"
        profile.write_text("# Mandantenprofil\nBilanz, keine Kostenstellen.\n", encoding="utf-8")
        accrual.write_text("# Abgrenzungsregister\nKeine offenen Fälle.\n", encoding="utf-8")
        source = write_pdf(temp / "beleg.pdf", "DATEV-Vertragsbeleg")
        targets = build_targets("12861")

        run = {
            "beraternummer": 29098,
            "mandantennummer": 12861,
            "buchungsmonat": "2026-06",
            "wirtschaftsjahr_beginn": "2026-01-01",
            "sachkontenlaenge": 4,
            "sachkontenrahmen": "03",
            "waehrung": "EUR",
            "diktatkuerzel": "BK",
            "accounting_method": "Bilanz",
            "datev_connection_verified": True,
            "mandantenprofil_verified": True,
            "kostenstellenpflicht": False,
            "vat_config": {
                "sales_treatment": "steuerpflichtig",
                "input_tax_deduction": "voll",
                "default_domestic_input_treatment": "volle_vorsteuer",
            },
            "account_config": {
                "private_expense": "4655",
                "gwg": "0480",
                "clarification": "1590",
                "hospitality_deductible": "4650",
                "hospitality_nondeductible": "4654",
                "asset_accounts": ["0480", "0500", "0670"],
            },
            "person_account_ranges": {
                "debitor": {"start": "10000", "end": "69999"},
                "kreditor": {"start": "70000", "end": "99999"},
            },
            "mandantenprofil_evidence": evidence(
                profile, str(targets["profile_url"])
            ),
            "abgrenzungsregister_evidence": evidence(
                accrual, str(targets["accrual_url"])
            ),
            "datev_live_evidence": {
                "source": "DATEV live",
                "connector": "Riecken",
                "retrieved_via": {
                    "health": "datev_health_check", "core": "datev_get_client_dossier",
                    "master_data": "datev_search_business_partners", "prior_bookings": "datev_get_account_postings",
                    "accounts": "datev_get_account_balances", "bu_keys": "datev_suggest_posting",
                },
                "retrieved_at": "2026-07-26T12:00:00+02:00",
                "beraternummer": 29098,
                "mandantennummer": 12861,
                "wirtschaftsjahr_beginn": "2026-01-01",
                "sachkontenlaenge": 4,
                "sachkontenrahmen": "03",
                "validated_accounts": ["4655", "4900"],
                "validated_bu_keys": ["401"],
                "used_person_accounts": [],
                "highest_creditor_account": 70000,
                "highest_debtor_account": 10000,
                "master_data_checked": True,
                "master_data_records_found": 1,
                "prior_bookings_checked": True,
                "prior_booking_records_found": 3,
            },
        }
        master = {
            "action": "Neuanlage",
            "account": "70001",
            "account_type": "Kreditor",
            "name": "DATEV Test GmbH",
            "full_current_record_available": False,
            "vat_id": "DE123456789",
            "banks": [
                {
                    "iban": "DE89370400440532013000",
                    "bic": "COBADEFFXXX",
                    "bank_name": "Commerzbank Test",
                    "is_primary": True,
                    "valid_from": "2026-06-01",
                },
                {
                    "iban": "DE12500105170648489890",
                    "bic": "INGDDEFFXXX",
                    "bank_name": "ING Test",
                    "is_primary": False,
                },
            ],
        }
        data = {
            "run": run,
            "documents": [booking_document(source)],
            "master_records": [master],
            "clarification_cases": [],
            "accrual_register": [],
            "accrual_candidates": [],
            "accrual_releases": [],
        }
        input_path = temp / "lauf.json"
        input_path.write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )
        loaded = build_package.load_input(input_path)
        assert loaded["run"]["_preflight_summary"]["mandantenprofil"]["sha256"]

        parallel_draft = copy.deepcopy(data)
        parallel_draft["_parallel_review"] = {
            "global_reconciliation_required": True
        }
        parallel_draft_path = temp / "parallel_draft.json"
        parallel_draft_path.write_text(
            json.dumps(parallel_draft, ensure_ascii=False), encoding="utf-8"
        )
        try:
            build_package.load_input(parallel_draft_path)
        except ValueError as exc:
            assert "Parallelentwurf ist nicht global konsolidiert" in str(exc)
        else:
            raise AssertionError("Unkonsolidierter Parallelentwurf wurde nicht abgewiesen")

        unresolved_accounts = copy.deepcopy(data)
        unresolved_accounts["_parallel_review"] = {
            "global_reconciliation_required": False
        }
        unresolved_accounts["person_account_proposals"] = [
            {"partner": "Offener Lieferant", "account_type": "creditor"}
        ]
        unresolved_accounts_path = temp / "unresolved_accounts.json"
        unresolved_accounts_path.write_text(
            json.dumps(unresolved_accounts, ensure_ascii=False), encoding="utf-8"
        )
        try:
            build_package.load_input(unresolved_accounts_path)
        except ValueError as exc:
            assert "Personenkontenvorschläge sind noch nicht final konsolidiert" in str(exc)
        else:
            raise AssertionError("Offene Personenkontenvorschläge wurden nicht abgewiesen")


        # Ein nachweislich noch nicht vorhandenes Register ist bei Bilanz ein
        # zulässiger Erstlauf und darf den Paketbau nicht blockieren.
        missing_register = copy.deepcopy(data)
        missing_register["run"]["abgrenzungsregister_evidence"] = {
            "status": "not_found",
            "source_url": str(targets["accrual_url"]),
            "file_name": "12861.md",
            "retrieved_via": "microsoft_sharepoint.fetch",
            "checked_at": "2026-07-28T09:00:00+02:00",
            "not_found_code": "itemNotFound",
            "site_verified": True,
            "library_verified": True,
            "direct_lookup_attempts": 2,
        }
        missing_register_path = temp / "missing-register.json"
        missing_register_path.write_text(
            json.dumps(missing_register, ensure_ascii=False), encoding="utf-8"
        )
        loaded_missing_register = build_package.load_input(missing_register_path)
        register_summary = loaded_missing_register["run"]["_preflight_summary"][
            "abgrenzungsregister"
        ]
        assert register_summary["status"] == "not_found"
        assert register_summary["first_run_without_register"] is True

        # v1.4.1: Das Register ist keine Pflichtquelle. Ein einfacher dokumentierter Abruf
        # (URL, Dateiname, Abrufweg, Zeitpunkt) genügt; kein zweifacher Direktabruf nötig.
        simple_missing_register = copy.deepcopy(missing_register)
        simple_missing_register["run"]["abgrenzungsregister_evidence"] = {
            "status": "not_found",
            "source_url": str(targets["accrual_url"]),
            "file_name": "12861.md",
            "retrieved_via": "microsoft_sharepoint.fetch",
            "checked_at": "2026-07-28T09:00:00+02:00",
        }
        simple_path = temp / "simple-missing-register.json"
        simple_path.write_text(
            json.dumps(simple_missing_register, ensure_ascii=False), encoding="utf-8"
        )
        assert build_package.load_input(simple_path)["run"]["_preflight_summary"]["abgrenzungsregister"]["status"] == "not_found"
        # Ein 403 darf nicht als leeres Register getarnt werden.
        disguised = copy.deepcopy(simple_missing_register)
        disguised["run"]["abgrenzungsregister_evidence"]["http_status"] = 403
        disguised_path = temp / "disguised-register.json"
        disguised_path.write_text(json.dumps(disguised, ensure_ascii=False), encoding="utf-8")
        try:
            build_package.load_input(disguised_path)
        except ValueError as exc:
            assert "Abrufproblem" in str(exc)
        else:
            raise AssertionError("HTTP 403 wurde als leeres Register akzeptiert")
        # Ein nicht geprüftes Register ist bei Bilanz der einzige Fehlerfall.
        unchecked = copy.deepcopy(missing_register)
        unchecked["run"].pop("abgrenzungsregister_evidence")
        unchecked_path = temp / "unchecked-register.json"
        unchecked_path.write_text(json.dumps(unchecked, ensure_ascii=False), encoding="utf-8")
        try:
            build_package.load_input(unchecked_path)
        except ValueError as exc:
            assert "nicht geprüft" in str(exc)
        else:
            raise AssertionError("Ungeprüftes Register wurde akzeptiert")

        missing_profile = copy.deepcopy(data)
        missing_profile["run"].pop("mandantenprofil_evidence")
        missing_profile_path = temp / "missing-profile.json"
        missing_profile_path.write_text(
            json.dumps(missing_profile, ensure_ascii=False), encoding="utf-8"
        )
        try:
            build_package.load_input(missing_profile_path)
        except ValueError as exc:
            assert "Mandantenprofil-Abrufnachweis fehlt" in str(exc)
        else:
            raise AssertionError("Fehlendes Mandantenprofil wurde akzeptiert")

        wrong_profile = copy.deepcopy(data)
        wrong_profile["run"]["mandantenprofil_evidence"]["source_url"] = (
            "https://example.invalid/12861.md"
        )
        wrong_path = temp / "wrong-profile.json"
        wrong_path.write_text(
            json.dumps(wrong_profile, ensure_ascii=False), encoding="utf-8"
        )
        try:
            build_package.load_input(wrong_path)
        except ValueError as exc:
            assert "verbindlichen exakten SharePoint-URL" in str(exc)
        else:
            raise AssertionError("Falsche Profilquelle wurde akzeptiert")

        gap = copy.deepcopy(data)
        gap["master_records"][0]["account"] = "70002"
        gap["documents"][0]["bookings"][0]["contra_account"] = "70002"
        gap_path = temp / "gap.json"
        gap_path.write_text(json.dumps(gap, ensure_ascii=False), encoding="utf-8")
        try:
            build_package.load_input(gap_path)
        except ValueError as exc:
            assert "lückenlos" in str(exc)
        else:
            raise AssertionError("Personenkontenlücke wurde akzeptiert")

        for forbidden_name in (
            "Diverse",
            "Diverse u.",
            "Diverse a.",
            "Div.",
            "CPD",
            "Sammelkreditoren",
            "Sammeldebitor",
        ):
            assert build_package.is_collective_person_account_name(forbidden_name)
        assert not build_package.is_collective_person_account_name(
            "Diversey Deutschland GmbH"
        )
        assert not build_package.is_collective_person_account_name(
            "Musterlieferant GmbH"
        )

        collective_master = copy.deepcopy(data)
        collective_master["master_records"][0]["name"] = "Diverse u."
        collective_master_path = temp / "collective-master.json"
        collective_master_path.write_text(
            json.dumps(collective_master, ensure_ascii=False), encoding="utf-8"
        )
        try:
            build_package.load_input(collective_master_path)
        except ValueError as exc:
            assert "Sammel-/CPD-Konto" in str(exc)
        else:
            raise AssertionError("Sammelkreditor wurde als Neuanlage akzeptiert")

        existing_individual = copy.deepcopy(data)
        existing_individual["master_records"] = []
        existing_individual["documents"][0]["bookings"][0][
            "contra_account"
        ] = "70000"
        existing_individual["documents"][0]["bookings"][0][
            "contra_account_name"
        ] = "Musterlieferant GmbH"
        existing_individual["run"]["datev_live_evidence"][
            "validated_accounts"
        ].append("70000")
        existing_individual["run"]["datev_live_evidence"][
            "used_person_accounts"
        ] = [
            {
                "account": "70000",
                "account_type": "kreditor",
                "name": "Musterlieferant GmbH",
            }
        ]
        existing_individual_path = temp / "existing-individual.json"
        existing_individual_path.write_text(
            json.dumps(existing_individual, ensure_ascii=False), encoding="utf-8"
        )
        build_package.load_input(existing_individual_path)

        existing_collective = copy.deepcopy(existing_individual)
        existing_collective["documents"][0]["bookings"][0][
            "contra_account_name"
        ] = "CPD"
        existing_collective["run"]["datev_live_evidence"][
            "used_person_accounts"
        ][0]["name"] = "CPD"
        existing_collective_path = temp / "existing-collective.json"
        existing_collective_path.write_text(
            json.dumps(existing_collective, ensure_ascii=False), encoding="utf-8"
        )
        try:
            build_package.load_input(existing_collective_path)
        except ValueError as exc:
            assert "Sammel-/CPD-Konto" in str(exc)
        else:
            raise AssertionError("Historisches CPD-Konto wurde akzeptiert")

        missing_person_evidence = copy.deepcopy(existing_individual)
        missing_person_evidence["run"]["datev_live_evidence"][
            "used_person_accounts"
        ] = []
        missing_person_evidence_path = temp / "missing-person-evidence.json"
        missing_person_evidence_path.write_text(
            json.dumps(missing_person_evidence, ensure_ascii=False),
            encoding="utf-8",
        )
        try:
            build_package.load_input(missing_person_evidence_path)
        except ValueError as exc:
            assert "used_person_accounts" in str(exc)
        else:
            raise AssertionError("Personenkonto ohne Namensnachweis wurde akzeptiert")

        manifest = {
            "beraternummer": 29098,
            "mandant": 12861,
            "run_contract": {
                "wirtschaftsjahr_beginn": "2026-01-01",
                "sachkontenlaenge": 4,
                "sachkontenrahmen": "03",
                "waehrung": "EUR",
                "accounting_method": "Bilanz",
                "kostenstellenpflicht": False,
                "vat_config": run["vat_config"],
                "account_config": run["account_config"],
                "person_account_ranges": run["person_account_ranges"],
            },
        }
        document = booking_document(source)
        document["document_guid"] = "01234567-89AB-CDEF-0123-456789ABCDEF"
        booking_path = temp / "EXTF_Buchungsstapel_2025-12.csv"
        datev_io.write_extf(
            booking_path,
            datev_io.extf_header(
                run,
                category=21,
                format_name="Buchungsstapel",
                version=13,
                label="Buchungsstapel",
                period="2025-12",
            ),
            datev_io.BOOKING_FIELDS,
            [datev_io.booking_row(document, document["bookings"][0], run)],
        )
        header = validate_package.split_extf(
            booking_path.read_text(encoding="cp1252").splitlines()[0]
        )
        assert header[12] == "20250101"
        booking_errors, links = validate_package.validate_csv(
            booking_path, manifest
        )
        assert booking_errors == [], booking_errors
        assert len(links) == 1

        booking_lines = booking_path.read_text(encoding="cp1252").splitlines()
        row = validate_package.split_extf(booking_lines[2])
        assert row[8] == "0401"

        # v1.4: Grün im Buchungsstapel, Rot im Klärungsstapel; dort bleibt das
        # DATEV-Belegdatum immer leer (Pflichtleerung), das erkannte Datum steht im Nachweis.
        datev_dir = temp / "01_DATEV_Import"
        datev_dir.mkdir()
        red_doc = booking_document(source, "Rot")
        red_doc["transaction_id"] = "V0002"
        red_doc["document_guid"] = document["document_guid"]
        trace = build_package.write_booking_batches(temp, {"run": run, "documents": [document, red_doc]})
        generated = sorted(path.name for path in datev_dir.glob("EXTF_*.csv"))
        assert generated == ["EXTF_Buchungsstapel_2025-12.csv", "EXTF_Klaerungsposten_2025-12.csv"], generated
        local_manifest = copy.deepcopy(manifest)
        local_manifest["booking_trace"] = trace
        for name in generated:
            batch_errors, _ = validate_package.validate_csv(datev_dir / name, local_manifest)
            assert batch_errors == [], batch_errors
            rows = (datev_dir / name).read_text(encoding="cp1252").splitlines()[2:]
            assert len(rows) == 1
            expected_date = "" if name.startswith("EXTF_Klaerungsposten_") else "1512"
            assert validate_package.split_extf(rows[0])[9] == expected_date
        red_trace = next(item for item in trace if item["transaction_id"] == "V0002")
        assert red_trace["file"] == "EXTF_Klaerungsposten_2025-12.csv"
        assert red_trace["recognized_date"] == "2025-12-15" and red_trace["batch_kind"] == "klaerung"
        assert not any(path.is_dir() for path in datev_dir.iterdir())

        foreign_document = copy.deepcopy(document)
        foreign_document["currency"] = "USD"
        foreign_booking = copy.deepcopy(document["bookings"][0])
        foreign_booking["service_date"] = "2025-12-01"
        foreign_booking["tax_period_date"] = "2025-12-31"
        foreign_booking["exchange_rate"] = "0.920000"
        foreign_booking["base_amount"] = "109.48"
        foreign_row = datev_io.booking_row(
            foreign_document, foreign_booking, run
        )
        assert foreign_row[3] == "0,92"
        assert foreign_row[4] == "109,48"
        assert foreign_row[5] == "EUR"
        assert foreign_row[114] == "01122025"
        assert foreign_row[115] == "31122025"

        missing_conversion = copy.deepcopy(foreign_booking)
        missing_conversion.pop("base_amount")
        try:
            datev_io.booking_row(foreign_document, missing_conversion, run)
        except ValueError as exc:
            assert "Fremdwährungsbuchung" in str(exc)
        else:
            raise AssertionError(
                "Fremdwährungsbuchung ohne Basisbetrag wurde akzeptiert"
            )
        row[8] = "401"
        booking_lines[2] = ";".join(
            f'"{value}"' if index in datev_io.BOOKING_TEXT_FIELDS else value
            for index, value in enumerate(row, start=1)
        )
        invalid_bu = temp / "EXTF_Buchungsstapel_2025-11.csv"
        invalid_bu.write_text(
            "\r\n".join(booking_lines) + "\r\n", encoding="cp1252"
        )
        invalid_errors, _ = validate_package.validate_csv(invalid_bu, manifest)
        assert any("vierstellig DATEV-konform" in item for item in invalid_errors)

        master_path = temp / "EXTF_Debitoren_Kreditoren.csv"
        datev_io.write_extf(
            master_path,
            datev_io.extf_header(
                run,
                category=16,
                format_name="Debitoren/Kreditoren",
                version=5,
            ),
            datev_io.MASTER_FIELDS,
            [datev_io.master_row(master)],
        )
        master_header = validate_package.split_extf(
            master_path.read_text(encoding="cp1252").splitlines()[0]
        )
        assert master_header[14:22] == [""] * 8
        master_row = validate_package.split_extf(
            master_path.read_text(encoding="cp1252").splitlines()[2]
        )
        assert master_row[44] == "DE89370400440532013000"
        assert master_row[55] == "DE12500105170648489890"
        assert master_row[49] == "01062026"
        master_errors, _ = validate_package.validate_csv(master_path, manifest)
        assert master_errors == [], master_errors

        xml_bytes = build_package._document_xml(
            [{
                "document_guid": "01234567-89AB-CDEF-0123-456789ABCDEF",
                "document_filename": "beleg.txt",
            }]
        )
        assert b'processID="1"' in xml_bytes
        assert b' type=' not in xml_bytes
        assert b"accountsPayableLedger" not in xml_bytes

    print("DATEV contract tests: OK")


if __name__ == "__main__":
    main()
