"""Bank-specific regression tests; the stored reference is never regenerated."""
import copy
import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from bank_routing import model
BANK=ROOT/"banks"/"dortmunder-volksbank"

class VolksbankTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((BANK/"reference-input.json").read_text(encoding="utf-8"))
        self.expected=json.loads((BANK/"reference-expected.json").read_text(encoding="utf-8"))
        self.ref=(BANK/"reference.sta").read_bytes()
        self.m=model(self.data)

    def test_stored_reference_independent_semantics(self):
        self.assertEqual(self.m.DECODER.parse(self.ref),self.expected)
        self.assertEqual(hashlib.sha256(self.ref).hexdigest(),"403eabadf2a84ade1cfd5f0f626ce596bbcda675f28ace3395e24210349512c0")

    def test_new_generation_all_fields(self):
        payload,report=self.m.build(self.data)
        self.assertEqual(self.m.DECODER.parse(payload),self.expected)
        self.assertEqual(report["transaction_count"],8)
        self.assertEqual(report["month_counts"],{"2025-02":2,"2025-03":6})
        self.assertEqual(report["datev_import_status"],"not_verified")

    def test_original_statement_numbers_in_one_file(self):
        payload,_=self.m.build(self.data)
        self.assertEqual(payload.count(b":28C:"),2)
        self.assertIn(b":28C:00002/001",payload)

    def test_gvc_required(self):
        with self.assertRaises(ValueError):
            self.m.DECODER.parse(self.ref.replace(b":86:051?",b":86:?"))

    def test_wrong_counterparty_subfields_detected(self):
        mutated=self.ref.replace(b"?32Muster Beteiligung",b"?30Muster Beteiligung")
        with self.assertRaises(ValueError):
            self.m.validate(self.data,mutated)

    def test_cut_text_detected_even_with_same_balances(self):
        with self.assertRaises(ValueError):
            self.m.validate(self.data,self.ref.replace(b"DEMO-REF-Z",b"DEMO"))

    def test_missing_february_rejected(self):
        self.data["statements"]=self.data["statements"][1:]
        with self.assertRaises(ValueError):
            self.m.build(self.data)

    def test_missing_transaction_rejected(self):
        self.data["statements"][1]["transactions"].pop(2)
        with self.assertRaises(ValueError):
            self.m.build(self.data)

    def test_independent_month_count(self):
        self.data["source_month_counts"]["2025-02"]=0
        with self.assertRaises(ValueError):
            self.m.build(self.data)

    def test_control_debit_credit_totals(self):
        self.data["source_inventory"][1]["debits"]="1.00"
        with self.assertRaises(ValueError):
            self.m.build(self.data)

    def test_unknown_bank_no_fallback(self):
        self.data["bank"]["name"]="Andere Volksbank eG"
        with self.assertRaises(ValueError):
            self.m.build(self.data)

    def test_unknown_profile_no_fallback(self):
        self.data["profile_id"]="andere-bank"
        with self.assertRaises(ValueError):
            model(self.data)

    def test_old_profile_blocked(self):
        self.data["profile_id"]="dortmunder-volksbank-v1"
        with self.assertRaises(ValueError):
            model(self.data)

    def test_cp1252_v2_profile_blocked(self):
        self.data["profile_id"]="dortmunder-volksbank-pdf-2025-v2"
        with self.assertRaises(ValueError):
            model(self.data)

    def test_complete_synthetic_year_in_one_file(self):
        import calendar
        from decimal import Decimal
        template = copy.deepcopy(self.data["statements"][0]["transactions"])
        self.data["statements"] = []
        self.data["source_inventory"] = []
        self.data["source_month_counts"] = {}
        opening = {"date": "2025-01-01", "amount": "0.00"}
        for month in range(1, 13):
            end = f"2025-{month:02d}-{calendar.monthrange(2025, month)[1]}"
            txs = copy.deepcopy(template)
            for tx in txs:
                tx["booking_date"] = tx["value_date"] = end
            closing = {"date": end, "amount": str(Decimal(opening["amount"]) + Decimal("2282.20"))}
            self.data["statements"].append({"number": month, "opening": opening.copy(), "closing": closing.copy(), "transactions": txs})
            self.data["source_inventory"].append({"number": month, "count": 2, "debits": "17.80", "credits": "2300.00", "opening": opening.copy(), "closing": closing.copy()})
            self.data["source_month_counts"][end[:7]] = 2
            opening = closing
        payload, report = self.m.build(self.data)
        self.assertEqual(payload.count(b":28C:"), 12)
        self.assertEqual(report["transaction_count"], 24)
        self.assertEqual(report["month_counts"]["2025-02"], 2)
        self.assertEqual(report["closing"]["amount"], "27386.40")

    def test_synthetic_reference_is_not_import_approval(self):
        payload, report = self.m.build(self.data)
        self.assertEqual(payload, self.ref)
        self.assertEqual(report["datev_import_status"], "not_verified")
        self.assertEqual(report["bank_model_import_status"], "not_verified")
        self.assertIsNone(report["acceptance_evidence"])

    def test_wrong_encoding_recreates_datev_error_and_is_rejected(self):
        wrong=self.ref.decode("cp850").encode("cp1252")
        self.assertIn("beschrõnkt",wrong.decode("cp850"))
        with self.assertRaises(ValueError):
            self.m.validate(self.data,wrong)

    def test_invalid_date_not_normalized(self):
        self.data["statements"][0]["transactions"][1]["value_date"]="2025-02-30"
        with self.assertRaises(ValueError):
            self.m.build(self.data)

    def test_unconfirmed_original_date_change_rejected(self):
        self.data["statements"][0]["transactions"][1]["source_value_date"]="2025-02-30"
        with self.assertRaises(ValueError):
            self.m.build(self.data)

    def test_confirmed_date_change_keeps_provenance(self):
        tx=self.data["statements"][0]["transactions"][1]
        tx["source_value_date"]="2025-02-30"
        tx["value_date_correction"]={"confirmed":True,"authority":"synthetic test instruction","reason":"fixture only"}
        self.m.build(self.data)
        self.assertEqual(tx["source_value_date"],"2025-02-30")

    def test_long_name_not_truncated(self):
        self.data["statements"][1]["transactions"][2]["counterparty"]="A"*55
        with self.assertRaises(ValueError):
            self.m.build(self.data)

    def test_long_purpose_not_truncated(self):
        self.data["statements"][1]["transactions"][2]["purpose"]="A"*271
        with self.assertRaises(ValueError):
            self.m.build(self.data)

    def test_umlauts_and_physical_encoding(self):
        payload,_=self.m.build(self.data)
        self.assertIn("beschränkt".encode("cp850"),payload)
        self.assertNotIn(b"\xef\xbb\xbf",payload)
        self.assertNotIn(b"\n",payload.replace(b"\r\n",b""))
        self.assertTrue(all(len(x)<=65 for x in payload.split(b"\r\n")))

    def test_delimiter_in_source_rejected(self):
        self.data["statements"][1]["transactions"][2]["purpose"]="Text ?20 literal"
        with self.assertRaises(ValueError):
            self.m.build(self.data)

    def test_pdf_requires_visual_confirmation(self):
        self.data["source_kind"]="pdf"
        with self.assertRaises(ValueError):
            self.m.build(self.data)

    def test_source_line_join_without_inserted_space(self):
        tx=copy.deepcopy(self.data["statements"][1]["transactions"][0])
        tx.update(counterparty="Beispiel",purpose="SecureGo",source_page=1,
                  source_reviewed=True,source_lines=["Beispiel","Sec","ureGo"],source_joiners=[" ",""])
        self.m.check_source(tx,"pdf")
        tx["source_joiners"]=[" "," "]
        with self.assertRaises(ValueError):
            self.m.check_source(tx,"pdf")

    def test_no_fictitious_fee_counterparty(self):
        decoded=self.m.DECODER.parse(self.ref)
        self.assertEqual(decoded[0]["transactions"][1]["counterparty"],"")
        self.assertEqual(decoded[0]["transactions"][1]["type"],"Abschluss lt. Anlage 1")

    def test_value_date_independent_from_booking(self):
        self.data["statements"][1]["transactions"][4]["value_date"]="2025-04-01"
        payload,_=self.m.build(self.data)
        last=self.m.DECODER.parse(payload)[1]["transactions"][4]
        self.assertEqual(last["booking_date"],"2025-03-24")
        self.assertEqual(last["value_date"],"2025-04-01")

    def test_lf_only_reference_rejected(self):
        with self.assertRaises(ValueError):
            self.m.DECODER.parse(self.ref.replace(b"\r\n",b"\n"))

    def test_gvc_sign_mismatch_rejected(self):
        self.data["statements"][0]["transactions"][0]["gvc"]="020"
        with self.assertRaises(ValueError):
            self.m.build(self.data)

    def pdf_fixture(self):
        self.data["source_kind"]="pdf"
        for s,control in zip(self.data["statements"],self.data["source_inventory"]):
            control.update(source_file="synthetic.pdf",source_file_sha256="0"*64,
                           page_count=2,reviewed_pages=[1,2])
            for tx in s["transactions"]:
                lines=[v for v in (tx["counterparty"],tx["purpose"]) if v]
                tx.update(source_reviewed=True,source_page=1,source_lines=lines,
                          source_joiners=[" "]*max(0,len(lines)-1))

    def test_all_pages_and_continuation_transactions(self):
        self.pdf_fixture()
        self.data["statements"][1]["transactions"][-1]["source_page"]=2
        payload,report=self.m.build(self.data)
        self.assertEqual(report["transaction_count"],8)
        self.assertEqual(report["transaction_audit"][-1]["source_page"],2)

    def test_unreviewed_page_rejected(self):
        self.pdf_fixture()
        self.data["source_inventory"][1]["reviewed_pages"]=[1]
        with self.assertRaises(ValueError):
            self.m.build(self.data)

    def test_transaction_outside_page_inventory_rejected(self):
        self.pdf_fixture()
        self.data["statements"][1]["transactions"][0]["source_page"]=3
        with self.assertRaises(ValueError):
            self.m.build(self.data)

    def test_control_totals_catch_balanced_missing_pair(self):
        # Removing a debit and credit of equal value preserves the balance,
        # but must still fail source count/control totals.
        pair=copy.deepcopy(self.data["statements"][1]["transactions"][:1])*2
        pair[0]=copy.deepcopy(pair[0])
        pair[0].update(amount="100.00",gvc="051",type="Überweisungsgutschr.")
        pair[1]=copy.deepcopy(pair[1])
        pair[1].update(amount="-100.00")
        self.data["statements"][1]["transactions"][0:0]=pair
        with self.assertRaises(ValueError):
            self.m.build(self.data)

if __name__=="__main__":
    unittest.main()
