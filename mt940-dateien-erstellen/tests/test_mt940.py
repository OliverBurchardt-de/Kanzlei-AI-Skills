from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import subprocess
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

    def source_review(self, directory: Path, data: dict) -> Path:
        original = directory / "synthetic-original.json"
        original.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        review = copy.deepcopy(data)
        review.update(reviewed_against_original=True, review_method="visual_original",
                      source_files=[{"id": "original", "path": original.name,
                                     "sha256": hashlib.sha256(original.read_bytes()).hexdigest()}])
        for number, tx in enumerate(review["transactions"], 1):
            tx.update(source_file="original", source_locator=f"page 1 / block {number}")
            tx.setdefault("customer_reference", None)
            tx.setdefault("bank_reference", None)
            if data["field86_mode"] == "native":
                tx["description"] = tx["native_field86_lines"][0][4:] + "".join(tx["native_field86_lines"][1:])
        path = directory / "source-review.json"
        path.write_text(json.dumps(review, ensure_ascii=False), encoding="utf-8")
        return path

    def write_and_validate(self, data: dict, source: dict | None = None) -> tuple[Path, dict]:
        normalized = normalize_manifest(data, self.profile_dir)
        payload, _ = build_module.build(data, self.profile_dir)
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / output_filename(normalized)
        path.write_bytes(payload)
        review = self.source_review(Path(temp_dir.name), source or data)
        return path, validate_module.validate(path, data, self.profile_dir, review)

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
            review = self.source_review(Path(temp_dir), data)
            with self.assertRaises(MT940Error) as raised:
                validate_module.validate(path, data, self.profile_dir, review)
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
            review = self.source_review(Path(temp_dir), data)
            with self.assertRaises(MT940Error):
                validate_module.validate(path, data, self.profile_dir, review)

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

    def test_legacy_generic_manifest_cannot_bypass_bank_model(self):
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
        with self.assertRaises(MT940Error):
            build_module.build(data)




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
            "bank_id": "synthetic-bank",
            "source_variant": "synthetic-native-v1",
            "bank_profile": "native-test-profile",
            "profile_version": 1,
            "statement_reference": "ORIGINAL0001",
            "transactions": [
                {
                    "value_date": "2025-01-02",
                    "booking_date": "2025-01-02",
                    "amount": "-25.00",
                    "code": "NMSC",
                    "customer_reference": "ORIGINALREF",
                    "bank_reference": "BANKREF1",
                    "description": "?00ORIGINAL?20UnverändertFortsetzung aus der Bankdatei",
                    "native_field86_lines": [
                        ":86:?00ORIGINAL?20Unverändert",
                        "Fortsetzung aus der Bankdatei",
                    ],
                }
            ],
        }
        path, result = self.write_and_validate(data)
        text = path.read_bytes().decode("cp1252")
        self.assertIn(":20:ORIGINAL0001\r\n", text)
        self.assertIn(":86:?00ORIGINAL?20Unverändert\r\n", text)
        self.assertEqual(result["transactions"], 1)

    def test_no_bank_model_is_rejected(self):
        data = reference_day()
        data.pop("bank_profile")
        with self.assertRaises(MT940Error) as raised:
            build_module.build(data, self.profile_dir)
        self.assertEqual(raised.exception.exit_code, 4)

    def test_unknown_bank_model_is_rejected(self):
        data = reference_day()
        data["bank_profile"] = "missing-bank"
        with self.assertRaises(MT940Error) as raised:
            build_module.build(data, self.profile_dir)
        self.assertIn("create", str(raised.exception))

    def test_other_bank_variant_and_version_are_rejected(self):
        for field, value in (("bank_id", "other-bank"), ("source_variant", "other-layout"), ("profile_version", 2)):
            with self.subTest(field=field):
                data = reference_day()
                data[field] = value
                with self.assertRaises(MT940Error) as raised:
                    build_module.build(data, self.profile_dir)
                self.assertEqual(raised.exception.exit_code, 4)

    def test_generic_mode_is_rejected_even_with_bank_profile(self):
        data = reference_day()
        data["field86_mode"] = "generic_unstructured"
        data["target_system"] = "GENERIC"
        with self.assertRaises(MT940Error) as raised:
            build_module.build(data, self.profile_dir)
        self.assertEqual(raised.exception.exit_code, 4)

    def test_source_review_is_mandatory(self):
        data = reference_day()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / output_filename(normalize_manifest(data, self.profile_dir))
            path.write_bytes(build_module.build(data, self.profile_dir)[0])
            with self.assertRaises(MT940Error) as raised:
                validate_module.validate(path, data, self.profile_dir)
        self.assertIn("source-review", str(raised.exception))

    def test_coherently_wrong_manifest_and_mt940_fail_original_comparison(self):
        original = reference_day()
        wrong = copy.deepcopy(original)
        wrong["transactions"][0]["description"] = "Allianz falscher Buchungstext Referenz SA01A000000095207172"
        wrong["transactions"][0]["source_description_lines"] = [wrong["transactions"][0]["description"]]
        with self.assertRaises(MT940Error) as raised:
            self.write_and_validate(wrong, original)
        self.assertIn("description", str(raised.exception))

    def test_swapped_texts_with_equal_amounts_fail_original_comparison(self):
        original = reference_day()
        original["transactions"][1]["amount"] = "-700.00"
        original["closing_balance"] = "79038.24"
        original["source_evidence"]["closing_balance"] = "79038.24"
        wrong = copy.deepcopy(original)
        for key in ("description", "source_description_lines", "customer_reference"):
            wrong["transactions"][1][key], wrong["transactions"][2][key] = wrong["transactions"][2][key], wrong["transactions"][1][key]
        with self.assertRaises(MT940Error):
            self.write_and_validate(wrong, original)

    def test_named_fields_are_encoded_and_compared_for_the_selected_bank(self):
        data = reference_day()
        data.update(bank_profile="structured-test-profile", bank_id="synthetic-other-bank",
                    source_variant="synthetic-structured-v1", field86_mode="bank_profile")
        for number, tx in enumerate(data["transactions"], 1):
            tx["source_fields"] = {"counterparty": f"Empfänger {number}"}
        path, result = self.write_and_validate(data)
        self.assertIn(b"?20Allianz", path.read_bytes())
        self.assertIn("?32Empfänger 1", path.read_bytes().decode("cp1252"))
        self.assertTrue(result["source_check"]["source_to_mt940_match"])
        self.assertEqual(result["source_check"]["checked_transaction_count"], 6)

    def test_changed_original_file_hash_blocks_delivery(self):
        data = reference_day()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / output_filename(normalize_manifest(data, self.profile_dir))
            path.write_bytes(build_module.build(data, self.profile_dir)[0])
            review = self.source_review(root, data)
            (root / "synthetic-original.json").write_text("changed", encoding="utf-8")
            with self.assertRaises(MT940Error) as raised:
                validate_module.validate(path, data, self.profile_dir, review)
        self.assertIn("hash mismatch", str(raised.exception))

    def test_synthetic_probe_is_never_reported_as_real_datev_verification(self):
        _, result = self.write_and_validate(full_july_manifest())
        self.assertFalse(result["delivery_approved"])
        self.assertEqual(result["datev_practical_test"], "not confirmed by a probe import")

    def test_wrong_dates_and_amounts_are_rejected_against_original(self):
        original = full_july_manifest()
        for field, value in (("booking_date", "2026-07-02"), ("value_date", "2026-07-02"), ("amount", "-999.00")):
            with self.subTest(field=field):
                wrong = copy.deepcopy(original)
                wrong["transactions"][0][field] = value
                if field == "amount":
                    wrong["closing_balance"] = "33445.84"
                    wrong["source_evidence"]["closing_balance"] = "33445.84"
                with self.assertRaises(MT940Error) as raised:
                    self.write_and_validate(wrong, original)
                self.assertEqual(raised.exception.exit_code, 2)
                self.assertTrue(raised.exception.details["mismatch_count"])

    def test_long_text_is_rejected_without_truncation(self):
        data = reference_day()
        text = "Allianz SA01A000000095207172 " + "A" * 400
        data["transactions"][0].update(description=text, source_description_lines=[text])
        with self.assertRaises(MT940Error) as raised:
            build_module.build(data, self.profile_dir)
        self.assertEqual(raised.exception.exit_code, 2)

    def test_nonrepresentable_character_is_rejected(self):
        data = reference_day()
        text = data["transactions"][0]["description"] + " 😀"
        data["transactions"][0].update(description=text, source_description_lines=[text])
        with self.assertRaises(MT940Error) as raised:
            build_module.build(data, self.profile_dir)
        self.assertEqual(raised.exception.exit_code, 3)

    def test_copied_synthetic_model_is_not_a_production_reference(self):
        data = reference_day()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "automated-test-profile.json").write_bytes((self.profile_dir / "automated-test-profile.json").read_bytes())
            with self.assertRaises(MT940Error) as raised:
                build_module.build(data, root)
        self.assertIn("Synthetic", str(raised.exception))

    def test_missing_code_does_not_fall_back_to_nmsc(self):
        data = reference_day()
        data["transactions"][0].pop("code")
        with self.assertRaises(MT940Error) as raised:
            build_module.build(data, self.profile_dir)
        self.assertIn("code", str(raised.exception))

    def test_repeated_source_locator_is_rejected(self):
        data = reference_day()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / output_filename(normalize_manifest(data, self.profile_dir))
            path.write_bytes(build_module.build(data, self.profile_dir)[0])
            review_path = self.source_review(root, data)
            review = json.loads(review_path.read_text(encoding="utf-8"))
            review["transactions"][1]["source_locator"] = review["transactions"][0]["source_locator"]
            review_path.write_text(json.dumps(review), encoding="utf-8")
            with self.assertRaises(MT940Error) as raised:
                validate_module.validate(path, data, self.profile_dir, review_path)
        self.assertIn("Repeated source locator", str(raised.exception))

    def test_cli_replaces_success_on_failure_and_preserves_duplicate_record(self):
        data = reference_day()
        environment = dict(os.environ, PYTHONUTF8="1")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            path = root / output_filename(normalize_manifest(data, self.profile_dir))
            generated = subprocess.run([sys.executable, str(SCRIPTS / "build-mt940.py"), str(manifest_path),
                str(path), "--profile-dir", str(self.profile_dir)], cwd=root, env=environment, capture_output=True)
            self.assertEqual(generated.returncode, 0, generated.stderr.decode("utf-8"))
            review_path = self.source_review(root, data)
            command = [sys.executable, str(SCRIPTS / "validate-mt940.py"), str(path), str(manifest_path),
                       "--profile-dir", str(self.profile_dir), "--source-review", str(review_path)]
            validated = subprocess.run(command, cwd=root, env=environment, capture_output=True)
            self.assertEqual(validated.returncode, 0, validated.stderr.decode("utf-8"))
            report_path = validate_module.default_report_path(path)
            success = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertTrue(success["source_check"]["source_to_mt940_match"])
            review = json.loads(review_path.read_text(encoding="utf-8"))
            review["transactions"][0]["description"] = "Abweichender Quelltext"
            review_path.write_text(json.dumps(review, ensure_ascii=False), encoding="utf-8")
            failed = subprocess.run(command, cwd=root, env=environment, capture_output=True)
            self.assertEqual(failed.returncode, 2)
            blocked = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertFalse(blocked["delivery_approved"])
            self.assertEqual(blocked["status"], "delivery_blocked")
            self.assertEqual(blocked["source_check"]["mismatch_count"], 1)
            self.assertEqual(blocked["fingerprint_sha256"], success["fingerprint_sha256"])
            manifest_path.write_text("{", encoding="utf-8")
            malformed = subprocess.run(command, cwd=root, env=environment, capture_output=True)
            self.assertEqual(malformed.returncode, 2)
            self.assertFalse(json.loads(report_path.read_text(encoding="utf-8"))["delivery_approved"])

if __name__ == "__main__":
    unittest.main()
