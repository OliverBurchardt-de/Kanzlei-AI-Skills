from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(SCRIPTS))


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


build_module = load_script("build_mt940", "build-mt940.py")
validate_module = load_script("validate_mt940", "validate-mt940.py")
from mt940_common import MT940Error, normalize_manifest, output_filename  # noqa: E402


def add_pdf_source_evidence(data: dict) -> dict:
    for number, tx in enumerate(data["transactions"], 1):
        words = tx["description"].split()
        split_at = len(words) // 2
        visible_lines = (
            [" ".join(words[:split_at]), " ".join(words[split_at:])]
            if len(words) >= 8
            else [tx["description"]]
        )
        tx.setdefault("source_page", 1 + ((number - 1) // 10))
        tx.setdefault("source_description_lines", visible_lines)
        tx.setdefault("source_text_verified", True)
    return data


def reference_day() -> dict:
    data = json.loads((FIXTURES / "reference-day.json").read_text(encoding="utf-8"))
    return add_pdf_source_evidence(data)


def full_july_manifest() -> dict:
    data = reference_day()
    data.update(
        {
            "statement_end": "2026-07-31",
            "closing_balance_date": "2026-07-31",
            "closing_balance": "33444.84",
            "field86_mode": "datev_verified:automated-test-profile",
            "output_scope": "full",
        }
    )
    data["source_evidence"].update(
        {
            "statement_end": "2026-07-31",
            "closing_balance_date": "2026-07-31",
            "closing_balance": "33444.84",
        }
    )
    transactions = data["transactions"]
    for number in range(7, 64):
        day = 2 + ((number - 7) // 2)
        transactions.append(
            {
                "value_date": f"2026-07-{day:02d}",
                "booking_date": f"2026-07-{day:02d}",
                "amount": "-100.00",
                "code": "NMSC",
                "customer_reference": f"REF{number:04d}",
                "description": f"Juli-Umsatz {number:04d} mit eindeutiger Referenz REF{number:04d}",
            }
        )
    transactions.append(
        {
            "value_date": "2026-07-31",
            "booking_date": "2026-07-31",
            "amount": "-39793.40",
            "code": "NTRF",
            "customer_reference": "REF0064",
            "description": "Abschlussumsatz Juli Referenz REF0064",
        }
    )
    return add_pdf_source_evidence(data)


class MT940Tests(unittest.TestCase):
    profile_dir = FIXTURES / "profiles"

    def write_and_validate(self, data: dict) -> tuple[Path, dict]:
        normalized = normalize_manifest(data, self.profile_dir)
        payload, _ = build_module.build(data, self.profile_dir)
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / output_filename(normalized)
        path.write_bytes(payload)
        return path, validate_module.validate(path, data, self.profile_dir)

    def test_complete_july_statement(self):
        data = full_july_manifest()
        path, result = self.write_and_validate(data)
        text = path.read_bytes().decode("cp1252")
        self.assertIn(":20:MT26073152432107\r\n", text)
        self.assertIn(":25:DE43300501101009524321\r\n", text)
        self.assertIn(":28C:00007/001\r\n", text)
        self.assertIn(":60F:C260630EUR83077,77\r\n", text)
        self.assertIn(":62F:C260731EUR33444,84\r\n", text)
        self.assertEqual(result["transactions"], 64)
        self.assertEqual(result["transaction_total"], "-49632.93")

    def test_reference_day_probe_file(self):
        data = reference_day()
        path, result = self.write_and_validate(data)
        self.assertEqual(path.name, "MT940 Test DE43300501101009524321 01.07.2026.sta")
        self.assertEqual(result["transactions"], 6)
        self.assertEqual(result["opening"], "83077.77")
        self.assertEqual(result["transaction_total"], "-4139.53")
        self.assertEqual(result["closing"], "78938.24")

    def test_wrong_opening_balance_date_fails_source_check(self):
        data = reference_day()
        data["opening_balance_date"] = "2026-07-01"
        with self.assertRaises(MT940Error) as raised:
            normalize_manifest(data, self.profile_dir)
        self.assertEqual(raised.exception.exit_code, 2)
        self.assertIn("source evidence", str(raised.exception))

    def test_hard_coded_statement_number_fails(self):
        data = reference_day()
        normalized = normalize_manifest(data, self.profile_dir)
        payload, _ = build_module.build(data, self.profile_dir)
        payload = payload.replace(b":28C:00007/001", b":28C:00001/001")
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / output_filename(normalized)
            path.write_bytes(payload)
            with self.assertRaises(MT940Error) as raised:
                validate_module.validate(path, data, self.profile_dir)
        self.assertEqual(raised.exception.exit_code, 3)

    def test_duplicate_fingerprint_returns_status_five(self):
        data = reference_day()
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            manifest_path = directory / "manifest.json"
            manifest_path.write_text(json.dumps(data), encoding="utf-8")
            output = directory / output_filename(normalize_manifest(data, self.profile_dir))
            build_module.write_artifacts(
                data, manifest_path, output, profile_dir=self.profile_dir
            )
            with self.assertRaises(MT940Error) as raised:
                build_module.write_artifacts(
                    data, manifest_path, output, profile_dir=self.profile_dir
                )
        self.assertEqual(raised.exception.exit_code, 5)

    def test_field86_roundtrip_preserves_allianz_text(self):
        data = reference_day()
        path, result = self.write_and_validate(data)
        metric = result["field86"][0]
        self.assertTrue(metric["roundtrip_match"])
        self.assertFalse(metric["truncated"])
        text = path.read_bytes().decode("cp1252")
        for fragment in ("Allianz", "AG", "AS-", "SA01A000000095207172"):
            self.assertIn(fragment, text)

    def test_field86_loss_is_detected(self):
        data = reference_day()
        normalized = normalize_manifest(data, self.profile_dir)
        payload, _ = build_module.build(data, self.profile_dir)
        payload = payload.replace(b"Allianz", b"XXXXXXX", 1)
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / output_filename(normalized)
            path.write_bytes(payload)
            with self.assertRaises(MT940Error):
                validate_module.validate(path, data, self.profile_dir)

    def test_unverified_pdf_cannot_create_full_month(self):
        data = full_july_manifest()
        data["field86_mode"] = "unverified"
        with self.assertRaises(MT940Error) as raised:
            build_module.build(data, self.profile_dir)
        self.assertEqual(raised.exception.exit_code, 4)

    def test_datev_legacy_dates_are_not_migrated(self):
        data = reference_day()
        data["period_start"] = data.pop("statement_start")
        data["period_end"] = data.pop("statement_end")
        data.pop("opening_balance_date")
        data.pop("closing_balance_date")
        with self.assertRaises(MT940Error) as raised:
            normalize_manifest(data, self.profile_dir)
        self.assertEqual(raised.exception.exit_code, 2)

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




    def test_pdf_requires_visually_verified_source_lines(self):
        data = reference_day()
        data["transactions"][0].pop("source_description_lines")
        with self.assertRaises(MT940Error) as raised:
            normalize_manifest(data, self.profile_dir)
        self.assertEqual(raised.exception.exit_code, 2)
        self.assertIn("source_description_lines", str(raised.exception))

    def test_pdf_description_must_match_visible_source_lines(self):
        data = reference_day()
        data["transactions"][0]["description"] = "Falscher Anfang und falsches Ende"
        with self.assertRaises(MT940Error) as raised:
            normalize_manifest(data, self.profile_dir)
        self.assertEqual(raised.exception.exit_code, 2)
        self.assertIn("differs from", str(raised.exception))

    def test_pdf_source_match_is_reported_with_text_edges(self):
        data = reference_day()
        _, result = self.write_and_validate(data)
        metric = result["field86"][0]
        self.assertEqual(metric["source_page"], 1)
        self.assertGreaterEqual(metric["source_line_count"], 2)
        self.assertTrue(metric["source_to_manifest_match"])
        self.assertTrue(metric["source_text_start"].startswith("Allianz"))
        self.assertTrue(metric["source_text_end"].endswith("SA01A000000095207172"))

    def test_native_field86_lines_are_preserved_exactly(self):
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
                    "native_field86_lines": [
                        ":86:?00ORIGINAL?20Unver?ndert",
                        "Fortsetzung aus der Bankdatei",
                    ],
                }
            ],
        }
        path, result = self.write_and_validate(data)
        text = path.read_bytes().decode("cp1252")
        self.assertIn(":86:?00ORIGINAL?20Unver?ndert\r\n", text)
        self.assertEqual(result["transactions"], 1)

if __name__ == "__main__":
    unittest.main()
