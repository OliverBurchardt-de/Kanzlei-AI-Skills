from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
SOURCE_FIXTURES = FIXTURES / "sources"
PROFILE_FIXTURES = FIXTURES / "profiles"
sys.path.insert(0, str(SCRIPTS))


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


build_module = load_script("build_mt940", "build-mt940.py")
validate_module = load_script("validate_mt940", "validate-mt940.py")
from mt940_common import (  # noqa: E402
    MT940Error,
    canonical_text,
    fingerprint,
    normalize_manifest,
    output_filename,
    parse_datev_structured_field86,
    read_json_utf8_no_bom,
)


def load_source(name: str) -> dict:
    return json.loads((SOURCE_FIXTURES / name).read_text(encoding="utf-8"))


def base_manifest(
    transactions: list[dict],
    source_type: str,
    *,
    field86_mode: str = "datev_verified:datev-mt940-structured-v1",
    output_scope: str = "full",
) -> dict:
    opening = Decimal("1000.00")
    total = sum((Decimal(tx["amount"]) for tx in transactions), Decimal("0.00"))
    closing = opening + total
    return {
        "iban": "DE89370400440532013000",
        "account_name": "Anonymisiertes Geschäftskonto",
        "statement_start": "2026-08-03",
        "statement_end": "2026-08-03",
        "opening_balance_date": "2026-08-02",
        "opening_balance": f"{opening:.2f}",
        "closing_balance_date": "2026-08-03",
        "closing_balance": f"{closing:.2f}",
        "statement_number": 8,
        "sequence_number": 1,
        "currency": "EUR",
        "source_type": source_type,
        "target_system": "DATEV",
        "field86_mode": field86_mode,
        "target_profile": "datev-mt940-structured-v1",
        "output_scope": output_scope,
        "source_evidence": {
            "statement_start": "2026-08-03",
            "statement_end": "2026-08-03",
            "opening_balance_date": "2026-08-02",
            "opening_balance": f"{opening:.2f}",
            "closing_balance_date": "2026-08-03",
            "closing_balance": f"{closing:.2f}",
            "statement_number": 8
        },
        "transactions": copy.deepcopy(transactions),
    }


class MT940Tests(unittest.TestCase):
    profile_dir = PROFILE_FIXTURES

    def fixture_manifest(self, name: str, **kwargs) -> dict:
        fixture = load_source(name)
        return base_manifest([fixture["transaction"]], fixture["source_type"], **kwargs)

    def write_and_validate(self, data: dict) -> tuple[Path, dict, bytes, dict]:
        normalized = normalize_manifest(data, self.profile_dir)
        payload, build_report = build_module.build(data, self.profile_dir)
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / output_filename(normalized)
        path.write_bytes(payload)
        validation = validate_module.validate(path, data, self.profile_dir)
        return path, validation, payload, build_report

    def test_cp1252_special_character_contract(self):
        data = self.fixture_manifest("fintech-pdf.json")
        _, validation, payload, report = self.write_and_validate(data)
        self.assertFalse(payload.startswith(b"\xef\xbb\xbf"))
        self.assertIn(b"\xfc", payload)
        self.assertNotIn(b"\xc3\xbc", payload)
        self.assertIn("Zusatzgebühren", payload.decode("cp1252"))
        self.assertEqual(report["output_charset"], "Windows-1252")
        self.assertTrue(validation["byte_roundtrip_match"])

    def test_manifest_utf8_bom_is_rejected(self):
        data = self.fixture_manifest("fintech-pdf.json")
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "manifest.json"
            path.write_bytes(
                b"\xef\xbb\xbf" + json.dumps(data, ensure_ascii=False).encode("utf-8")
            )
            with self.assertRaises(MT940Error) as raised:
                read_json_utf8_no_bom(path, "manifest")
        self.assertEqual(raised.exception.exit_code, 2)
        self.assertIn("without BOM", str(raised.exception))

    def test_complete_german_character_set(self):
        fixture = load_source("camt-entry.json")
        tx = fixture["transaction"]
        tx["purpose"] = "Müller Straße Überweisung Gebühren Änderung Öffentliche Zahlung"
        tx["raw_source_lines"] = [tx["purpose"], tx["counterparty_name"]]
        data = base_manifest([tx], fixture["source_type"])
        _, _, payload, _ = self.write_and_validate(data)
        normalized = normalize_manifest(data, self.profile_dir)
        field = normalized["_transactions"][0]["_field86"]
        parsed = parse_datev_structured_field86(field.lines)
        decoded = parsed["semantic_values"]["purpose_references"]
        for value in (
            "Müller",
            "Straße",
            "Überweisung",
            "Gebühren",
            "Änderung",
            "Öffentliche Zahlung",
        ):
            self.assertIn(value, decoded)

    def test_utf8_encoded_datev_file_is_rejected(self):
        data = self.fixture_manifest("fintech-pdf.json")
        normalized = normalize_manifest(data, self.profile_dir)
        payload, _ = build_module.build(data, self.profile_dir)
        utf8_payload = payload.decode("cp1252").encode("utf-8")
        self.assertIn(b"\xc3\xbc", utf8_payload)
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / output_filename(normalized)
            path.write_bytes(utf8_payload)
            with self.assertRaises(MT940Error) as raised:
                validate_module.validate(path, data, self.profile_dir)
        self.assertEqual(raised.exception.exit_code, 3)
        self.assertIn("UTF-8 multibyte", str(raised.exception))

    def test_skill_texts_have_no_known_encoding_damage(self):
        patterns = (
            "\ufffd",
            "Ãƒ",
            "Ã‚",
            "F?r",
            "?bernehmen",
            "zur?ck",
            "pr?fen",
            "ausschlie?lich",
            "Unver?ndert",
        )
        files = [ROOT / "SKILL.md", ROOT / "references" / "technischer-aufbau.md"]
        files.extend((ROOT / "profiles").glob("*.json"))
        for path in files:
            text = path.read_text(encoding="utf-8")
            for pattern in patterns:
                self.assertNotIn(pattern, text, f"{pattern!r} found in {path}")

    def test_qonto_fee_uses_structured_semantics(self):
        data = self.fixture_manifest("fintech-pdf.json")
        normalized = normalize_manifest(data, self.profile_dir)
        field = normalized["_transactions"][0]["_field86"]
        parsed = parse_datev_structured_field86(field.lines)
        self.assertEqual(parsed["semantic_values"]["booking_text"], "Entgelt")
        self.assertEqual(
            parsed["semantic_values"]["purpose_references"],
            "Abonnement / Zusatzgebühren",
        )
        self.assertEqual(parsed["semantic_values"]["counterparty_name"], "Qonto")
        self.assertEqual(parsed["underfield_order"][0:2], ("00", "20"))

    def test_iwg_name_and_both_references_roundtrip(self):
        data = self.fixture_manifest("structured-csv.json")
        normalized = normalize_manifest(data, self.profile_dir)
        field = normalized["_transactions"][0]["_field86"]
        parsed = parse_datev_structured_field86(field.lines)
        purpose = parsed["semantic_values"]["purpose_references"]
        self.assertEqual(parsed["semantic_values"]["counterparty_name"], "IWG Deutschland GmbH")
        self.assertIn("8240-26-522INV", purpose)
        self.assertIn("8240-26-431INV", purpose)

    def test_four_source_types_use_same_canonical_schema_and_renderer(self):
        required_keys = {
            "_transaction_category",
            "_booking_text",
            "_purpose",
            "_references",
            "_counterparty_name",
            "_counterparty_iban",
            "_raw_source_lines",
            "_field_confidence",
            "_field86",
        }
        for fixture_name in (
            "classic-pdf.json",
            "fintech-pdf.json",
            "structured-csv.json",
            "camt-entry.json",
        ):
            data = self.fixture_manifest(fixture_name)
            normalized = normalize_manifest(data, self.profile_dir)
            tx = normalized["_transactions"][0]
            self.assertTrue(required_keys <= set(tx))
            self.assertEqual(tx["_field86"].mode, "datev_structured_v1")
        application_text = "\n".join(
            path.read_text(encoding="utf-8") for path in SCRIPTS.glob("*.py")
        ).lower()
        for forbidden in ("sparkasse", "qonto", "iwg"):
            self.assertNotIn(forbidden, application_text)
        for profile_path in (
            ROOT / "profiles" / "datev-mt940-structured-v1.json",
            self.profile_dir / "datev-mt940-structured-v1.json",
        ):
            self.assertNotIn("bank_name", json.loads(profile_path.read_text(encoding="utf-8")))

    def test_low_confidence_blocks_productive_output(self):
        data = self.fixture_manifest("fintech-pdf.json")
        data["transactions"][0]["field_confidence"]["counterparty_name"] = "low"
        with self.assertRaises(MT940Error) as raised:
            normalize_manifest(data, self.profile_dir)
        self.assertEqual(raised.exception.exit_code, 4)
        data["field86_mode"] = "datev_structured_v1"
        data["output_scope"] = "test"
        normalized = normalize_manifest(data, self.profile_dir)
        self.assertIn(
            "counterparty_name", normalized["_transactions"][0]["_low_confidence_fields"]
        )

    def test_reserved_question_mark_requires_clarification(self):
        data = self.fixture_manifest("fintech-pdf.json")
        data["transactions"][0]["purpose"] = "Abonnement? Zusatzgebühren"
        with self.assertRaises(MT940Error) as raised:
            normalize_manifest(data, self.profile_dir)
        self.assertEqual(raised.exception.exit_code, 2)

    def test_indivisible_reference_is_not_silently_split(self):
        data = self.fixture_manifest("structured-csv.json")
        data["transactions"][0]["references"] = ["R" * 28]
        with self.assertRaises(MT940Error) as raised:
            normalize_manifest(data, self.profile_dir)
        self.assertEqual(raised.exception.exit_code, 2)

    def test_structured_field_lines_and_semantic_roundtrip(self):
        data = self.fixture_manifest("structured-csv.json")
        path, validation, payload, _ = self.write_and_validate(data)
        self.assertTrue(all(len(line) <= 65 for line in payload.decode("cp1252").splitlines()))
        self.assertTrue(all(item["roundtrip_match"] for item in validation["field86"]))
        self.assertEqual(path.read_bytes(), payload)

    def test_nfc_normalization_is_central(self):
        decomposed = "Mu\u0308ller"
        self.assertEqual(canonical_text(decomposed, "test"), "Müller")
        data = self.fixture_manifest("camt-entry.json")
        data["transactions"][0]["counterparty_name"] = decomposed
        normalized = normalize_manifest(data, self.profile_dir)
        self.assertEqual(normalized["_transactions"][0]["_counterparty_name"], "Müller")

    def test_balance_mismatch_remains_blocked(self):
        data = self.fixture_manifest("classic-pdf.json")
        data["closing_balance"] = "0.00"
        with self.assertRaises(MT940Error) as raised:
            normalize_manifest(data, self.profile_dir)
        self.assertEqual(raised.exception.exit_code, 2)

    def test_separate_balance_dates_are_rendered_exactly(self):
        data = self.fixture_manifest("classic-pdf.json")
        _, _, payload, _ = self.write_and_validate(data)
        text = payload.decode("cp1252")
        self.assertIn(":60F:C260802EUR1000,00\r\n", text)
        self.assertIn(":62F:D260803EUR200,00\r\n", text)

    def test_chronological_source_order_remains_required(self):
        fixture = load_source("fintech-pdf.json")
        first = fixture["transaction"]
        second = copy.deepcopy(first)
        first["booking_date"] = first["value_date"] = "2026-08-04"
        second["booking_date"] = second["value_date"] = "2026-08-03"
        data = base_manifest([first, second], fixture["source_type"])
        data["statement_end"] = data["closing_balance_date"] = "2026-08-04"
        data["source_evidence"]["statement_end"] = "2026-08-04"
        data["source_evidence"]["closing_balance_date"] = "2026-08-04"
        with self.assertRaises(MT940Error):
            normalize_manifest(data, self.profile_dir)

    def test_duplicate_bank_reference_remains_blocked(self):
        fixture = load_source("fintech-pdf.json")
        first = fixture["transaction"]
        second = copy.deepcopy(first)
        first["bank_reference"] = second["bank_reference"] = "SAME"
        data = base_manifest([first, second], fixture["source_type"])
        with self.assertRaises(MT940Error) as raised:
            normalize_manifest(data, self.profile_dir)
        self.assertEqual(raised.exception.exit_code, 2)

    def test_fingerprint_and_duplicate_import_gate_remain_active(self):
        data = self.fixture_manifest("fintech-pdf.json")
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            manifest_path = directory / "manifest.json"
            manifest_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            normalized = normalize_manifest(data, self.profile_dir)
            output = directory / output_filename(normalized)
            _, _, report = build_module.write_artifacts(
                data, manifest_path, output, profile_dir=self.profile_dir
            )
            self.assertEqual(report["fingerprint_sha256"], fingerprint(normalized))
            with self.assertRaises(MT940Error) as raised:
                build_module.write_artifacts(
                    data, manifest_path, output, profile_dir=self.profile_dir
                )
            self.assertEqual(raised.exception.exit_code, 5)

    def test_duplicate_override_requires_deletion_confirmation(self):
        data = self.fixture_manifest("fintech-pdf.json")
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            manifest_path = directory / "manifest.json"
            manifest_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            output = directory / output_filename(normalize_manifest(data, self.profile_dir))
            build_module.write_artifacts(data, manifest_path, output, profile_dir=self.profile_dir)
            with self.assertRaises(MT940Error):
                build_module.write_artifacts(
                    data,
                    manifest_path,
                    output,
                    profile_dir=self.profile_dir,
                    allow_duplicate=True,
                )
            data["previous_datev_import_removed_confirmed"] = True
            build_module.write_artifacts(
                data,
                manifest_path,
                output,
                profile_dir=self.profile_dir,
                allow_duplicate=True,
            )

    def test_unverified_target_profile_allows_only_test_output(self):
        data = self.fixture_manifest(
            "fintech-pdf.json", field86_mode="datev_structured_v1", output_scope="full"
        )
        with self.assertRaises(MT940Error) as raised:
            normalize_manifest(data, self.profile_dir)
        self.assertEqual(raised.exception.exit_code, 4)

    def test_production_target_profile_is_not_falsely_verified(self):
        data = self.fixture_manifest("fintech-pdf.json")
        with self.assertRaises(MT940Error) as raised:
            normalize_manifest(data, ROOT / "profiles")
        self.assertEqual(raised.exception.exit_code, 4)

    def test_sidecar_reports_encoding_and_target_profile(self):
        data = self.fixture_manifest("fintech-pdf.json")
        _, validation, _, report = self.write_and_validate(data)
        for result in (report, validation):
            self.assertEqual(result["output_charset"], "Windows-1252")
            self.assertEqual(result["bom"], "none")
            self.assertEqual(result["line_endings"], "CRLF")
            self.assertTrue(result["byte_roundtrip_match"])
            self.assertEqual(
                result["target_profile_version"], "datev-mt940-structured-v1"
            )

    def test_legacy_generic_manifest_remains_supported(self):
        data = {
            "iban": "DE89370400440532013000",
            "period_start": "2025-01-01",
            "period_end": "2025-01-31",
            "opening_balance": "100.00",
            "closing_balance": "125.00",
            "currency": "EUR",
            "transactions": [
                {
                    "value_date": "2025-01-02",
                    "booking_date": "2025-01-02",
                    "amount": "25.00",
                    "description": "Legacy generic transaction",
                }
            ],
        }
        payload, report = build_module.build(data)
        self.assertIn(b":28C:00001/001\r\n", payload)
        self.assertEqual(report["transaction_total"], "25.00")

    def test_native_field86_lines_remain_supported(self):
        data = {
            "iban": "DE89370400440532013000",
            "statement_start": "2025-01-01",
            "statement_end": "2025-01-31",
            "opening_balance_date": "2024-12-31",
            "opening_balance": "100.00",
            "closing_balance_date": "2025-01-31",
            "closing_balance": "75.00",
            "statement_number": 1,
            "sequence_number": 1,
            "currency": "EUR",
            "source_type": "native_mt940",
            "target_system": "DATEV",
            "field86_mode": "native",
            "transactions": [
                {
                    "value_date": "2025-01-02",
                    "booking_date": "2025-01-02",
                    "amount": "-25.00",
                    "code": "NMSC",
                    "source_location": "native statement 1 entry 1",
                    "native_field86_lines": [
                        ":86:?00ORIGINAL?20Unverändert",
                        "Fortsetzung aus der Bankdatei",
                    ],
                }
            ],
        }
        path, result, _, _ = self.write_and_validate(data)
        text = path.read_bytes().decode("cp1252")
        self.assertIn(":86:?00ORIGINAL?20Unverändert\r\n", text)
        self.assertEqual(result["transactions"], 1)


if __name__ == "__main__":
    unittest.main()
