"""Observable learning behavior, including independent-source rejection and retry."""
import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from mt940_common import MT940Error, normalize_manifest

spec = importlib.util.spec_from_file_location("learn_bank", SCRIPTS / "learn-bank-profile.py")
learning = importlib.util.module_from_spec(spec)
spec.loader.exec_module(learning)

class LearningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.profiles = self.root / "profiles"
        self.output = self.root / "output"
        self.manifest = self.root / "manifest.json"
        self.review = self.root / "source-review.json"
        self.adapter = self.root / "adapter.py"
        self.adapter.write_text('''from mt940_common import field86_result
def encode_field86(tx):
    return field86_result(tx['description']).lines
def decode_field86(lines):
    return {'description': lines[0][4:] + ''.join(lines[1:]), 'source_fields': {}}
''', encoding="utf-8")
        text = "Überweisung ?20 wörtlicher Text mit Umlauten äöüß und vollständiger Referenz ABC123456789012345678901234567890"
        self.data = {
            "iban":"DE43300501101009524321", "bank_id":"learning-test-bank",
            "bank_name":"Learning test bank", "bank_profile":"learning-test-bank-pdf",
            "profile_version":1, "source_variant":"pdf-list-v1", "source_type":"pdf",
            "target_system":"DATEV", "statement_start":"2026-01-01", "statement_end":"2026-01-31",
            "currency":"EUR", "opening_balance":"100.00", "closing_balance":"75.00",
            "opening_balance_date":None, "closing_balance_date":None,
            "statement_number":None, "sequence_number":None,
            "transactions":[{
                "value_date":None, "booking_date":"2026-01-04", "amount":"-25.00",
                "code":None, "customer_reference":None,"bank_reference":None,
                "description":text, "source_description_lines":[text],
                "source_page":1,"source_text_verified":True,"source_fields":{},
            }],
        }
        original = self.root / "original.json"
        original.write_text(json.dumps(self.data),encoding="utf-8")
        review = copy.deepcopy(self.data)
        review.update(reviewed_against_original=True,review_method="visual_original",
                      source_files=[{"id":"original","path":original.name,
                                     "sha256":hashlib.sha256(original.read_bytes()).hexdigest()}])
        review["transactions"][0].update(source_file="original",source_locator="page 1 / block 1")
        self.review.write_text(json.dumps(review),encoding="utf-8")
        self.manifest.write_text(json.dumps(self.data),encoding="utf-8")

    def learn(self, data=None):
        return learning.learn(data or self.data,self.manifest,self.review,self.adapter,self.profiles,self.output)

    def test_no_native_reference_needed_full_text_and_original_nulls_preserved(self):
        path, report_path, model_path = self.learn()
        report = json.loads(report_path.read_text(encoding="utf-8"))
        model = json.loads(model_path.read_text(encoding="utf-8"))
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        source = json.loads(self.review.read_text(encoding="utf-8"))
        self.assertEqual(model["status"],"source_verified")
        self.assertEqual(model["reference_basis"]["kind"],"source_reconstruction")
        self.assertTrue(report["delivery_approved"])
        self.assertFalse(report["datev_import_verified"])
        self.assertTrue(report["source_check"]["source_to_mt940_match"])
        self.assertEqual(source["opening_balance_date"],None)
        self.assertEqual(source["transactions"][0]["value_date"],None)
        self.assertEqual(manifest["opening_balance_date"],"2025-12-31")
        self.assertEqual(manifest["transactions"][0]["value_date"],"2026-01-04")
        text = path.read_bytes().decode("cp1252")
        self.assertIn("?20 wörtlicher",text)
        fields = report["source_check"]["field_comparisons"]
        desc = next(c for c in fields if c["field"]=="description")
        self.assertEqual(desc["mt940_value"],self.data["transactions"][0]["description"])
        derived = next(c for c in fields if c["field"]=="opening_balance_date")
        self.assertFalse(derived["source_to_manifest_match"])
        self.assertTrue(derived["source_to_effective_manifest_match"])
        normalize_manifest(manifest,self.profiles)  # reusable learned model

    def test_wrong_coherent_description_cannot_promote_then_corrected_retry_succeeds(self):
        wrong = copy.deepcopy(self.data)
        wrong["transactions"][0].update(description="Fehlerhafter Quelltext",source_description_lines=["Fehlerhafter Quelltext"])
        with self.assertRaises(MT940Error) as raised:
            self.learn(wrong)
        self.assertEqual(raised.exception.exit_code,2)
        self.assertFalse(self.profiles.exists())
        self.assertFalse(list(self.output.glob("*.sta")))
        self.assertTrue(self.learn()[2].is_file())

    def test_declared_rule_cannot_override_visible_original_date(self):
        self.learn()
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        source = json.loads(self.review.read_text(encoding="utf-8"))
        source["transactions"][0]["value_date"]="2026-01-05"
        self.review.write_text(json.dumps(source),encoding="utf-8")
        path = next(self.output.glob("*.sta"))
        with self.assertRaises(MT940Error) as raised:
            learning.validator.validate(path,manifest,self.profiles,self.review)
        self.assertIn("existing original",str(raised.exception))

    def test_bad_adapter_cannot_create_model(self):
        self.adapter.write_text("def encode_field86(tx):\n return [':86:lost']\ndef decode_field86(lines):\n return {'description':'lost','source_fields':{}}\n",encoding="utf-8")
        with self.assertRaises(MT940Error):
            self.learn()
        self.assertFalse(self.profiles.exists())

    def test_changed_reference_evidence_blocks_reuse(self):
        self.learn()
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        evidence = next(self.output.glob("*-reference-evidence.json"))
        evidence.write_text('{}',encoding="utf-8")
        with self.assertRaises(MT940Error) as raised:
            normalize_manifest(manifest,self.profiles)
        self.assertEqual(raised.exception.exit_code,4)

    def test_unknown_fallback_cannot_substitute_money(self):
        bad = copy.deepcopy(self.data)
        bad["reconstruction_rules"]={"opening_balance":"invented_balance"}
        with self.assertRaises(MT940Error):
            self.learn(bad)
        self.assertFalse(self.profiles.exists())

if __name__ == "__main__":
    unittest.main()
