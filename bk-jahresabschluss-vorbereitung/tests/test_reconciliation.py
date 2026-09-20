"""Synthetic acceptance cases; these tests do not perform a live DATEV review."""
from copy import deepcopy
import unittest

from test_skill_scripts import (
    valid_data, set_two_area_opening, set_reconciled_opos,
    validate_review_data,
)


def reference_12500():
    data = valid_data()
    set_two_area_opening(data)
    data["mandant"].update(number="12500", name="Referenzfall aus Anweisung, kein Live-Nachweis")
    data["target_fiscal_year"].update(id="20250101", start="2025-01-01", end="2025-12-31")
    data["prior_fiscal_year"].update(id="20240101", start="2024-01-01", end="2024-12-31")
    for source in data["sources"]:
        source["fiscal_year_id"] = "20240101" if source["fiscal_year_id"] == "20250101" else "20250101"
    hgb, tax = data["opening_balance_review"]["areas"]
    hgb["account_comparisons"] = [{
        "prior_account": "TEST-VORTRAG", "opening_account": "TEST-VORTRAG",
        "prior_balance": "4608.54", "opening_balance": "-70949.63",
        "currency": "EUR", "group_id": "ERGEBNIS",
    }]
    data["sources"].append({
        "id": "FINALE-JA", "kind": "upload", "uri": "test://finale-ja",
        "retrieved_at": "2026-09-20T12:00:00+02:00", "complete": True,
        "accounting_area_id": "handelsrecht", "fiscal_year_id": "20240101",
        "document_role": "finale_ja_susa",
    })
    hgb["groups"] = [{
        "id": "ERGEBNIS", "kind": "ergebnisvortrag", "currency": "EUR",
        "reason": "Vortragsbrücke aus dem vorgegebenen Referenzfall.",
        "source_refs": ["FINALE-JA"], "bridge_source_ref": "FINALE-JA",
        "bridge_amount": "-75558.17", "next_action": "Keine.",
    }]
    data["sources"].append({
        "id": "ABSCHREIBUNGEN-TEILMENGE", "kind": "upload",
        "uri": "test://teilmenge-2024-06-bis-12", "retrieved_at": "2026-09-20T12:00:00+02:00",
        "complete": False, "accounting_area_id": "steuerrecht",
        "fiscal_year_id": "20240101", "proof_kind": "partial",
        "supplied_example": {
            "account": "4831", "contra_account": "9000",
            "commercial_law": "2882.00", "tax_law": "2882.00",
        },
    })
    tax.update(
        status="TEILNACHWEIS", evidence_extent="teilweise",
        prior_close_source_ref="ABSCHREIBUNGEN-TEILMENGE", current_opening_source_ref=None,
        prior_close_final=False, comparison_complete=False, compared_account_count=0,
        account_comparisons=[], partial_source_refs=["ABSCHREIBUNGEN-TEILMENGE"],
        next_action="Vollständige steuerliche Schluss- und Eröffnungswerte herleiten.",
    )
    row = next(r for r in data["preparation_checklist"] if r["topic_id"] == "eroeffnungsbilanz")
    row.update(status="TEILNACHWEIS", work_lane="UNTERLAGE_ANFORDERN", blocks_start=True)
    return data


class OpeningEvidenceTests(unittest.TestCase):
    def errors(self, data):
        return validate_review_data.validate_review_data(data)

    def test_reference_12500_hgb_bridge_and_tax_partial_are_valid_draft(self):
        data = reference_12500()
        self.assertEqual(self.errors(data), [])
        self.assertEqual([a["status"] for a in data["opening_balance_review"]["areas"]],
                         ["ABGESTIMMT", "TEILNACHWEIS"])

    def test_reference_partial_never_allows_start_ready(self):
        data = reference_12500()
        set_reconciled_opos(data)
        data["overall_status"] = "STARTKLAR_FUER_ABSCHLUSSBEARBEITUNG"
        self.assertTrue(any("Eröffnungsbilanz" in e for e in self.errors(data)))

    def test_identical_tax_subset_cannot_be_promoted_to_full(self):
        data = reference_12500()
        tax = data["opening_balance_review"]["areas"][1]
        tax.update(status="ABGESTIMMT", evidence_extent="vollstaendig", comparison_complete=True)
        self.assertTrue(any("Bereichsnachweis" in e or "vollständig" in e for e in self.errors(data)))

    def test_running_susa_profit_is_not_final_bridge_evidence(self):
        data = reference_12500()
        next(s for s in data["sources"] if s["id"] == "FINALE-JA")["document_role"] = "laufende_susa"
        self.assertTrue(any("Ergebnisbrücke" in e for e in self.errors(data)))

    def test_one_cent_wrong_profit_bridge_is_rejected(self):
        data = reference_12500()
        data["opening_balance_review"]["areas"][0]["groups"][0]["bridge_amount"] = "-75558.16"
        self.assertTrue(any("abweichenden Kontenbeträgen" in e for e in self.errors(data)))

    def test_complete_separate_evidence_can_close_both_areas(self):
        data = valid_data()
        set_two_area_opening(data)
        set_reconciled_opos(data)
        data["overall_status"] = "STARTKLAR_FUER_ABSCHLUSSBEARBEITUNG"
        self.assertEqual(self.errors(data), [])

    def test_tax_line_cannot_be_removed_from_inventory(self):
        data = valid_data()
        set_two_area_opening(data)
        data["opening_balance_review"]["expected_areas"] = ["handelsrecht"]
        data["opening_balance_review"]["areas"].pop()
        self.assertTrue(any("getrennte Prüflinien" in e for e in self.errors(data)))

    def test_shared_susa_cannot_be_labelled_as_area_evidence(self):
        data = valid_data()
        set_two_area_opening(data)
        data["sources"][1]["proof_kind"] = "shared_susa"
        self.assertTrue(any("Gemeinsame SuSa" in e for e in self.errors(data)))

    def test_derived_area_needs_complete_layers(self):
        data = valid_data()
        set_two_area_opening(data)
        data["sources"][1].update(proof_kind="derived_area", layers_complete=False)
        self.assertTrue(any("Wertschicht" in e for e in self.errors(data)))

    def test_unapproved_group_type_is_rejected(self):
        data = reference_12500()
        data["opening_balance_review"]["areas"][0]["groups"][0]["kind"] = "aehnliche_kontonamen"
        self.assertTrue(any("Unzulässige Prüfgruppe" in e for e in self.errors(data)))

    def test_complete_derived_area_accepts_independent_same_year_sources(self):
        data = valid_data()
        set_two_area_opening(data)
        source = data["sources"][3]
        component = deepcopy(source)
        component.update(id="RAW-TAX", proof_kind="raw_layer")
        data["sources"].append(component)
        source.update(proof_kind="derived_area", layers_complete=True,
                      base_semantics="Grundbuchhaltung ohne Steueranpassungen plus vollständige Wertschicht.",
                      derivation_source_refs=["RAW-TAX"])
        self.assertEqual(self.errors(data), [])
        component["fiscal_year_id"] = "19990101"
        self.assertTrue(any("Herleitungsquelle" in e for e in self.errors(data)))

    def test_derived_area_cannot_cite_itself(self):
        data = valid_data()
        set_two_area_opening(data)
        source = data["sources"][3]
        source.update(proof_kind="derived_area", layers_complete=True,
                      base_semantics="Behauptete Wertschicht", derivation_source_refs=[source["id"]])
        self.assertTrue(any("unabhängige Roh" in e for e in self.errors(data)))

    def test_documented_vat_reclassification_keeps_individual_differences(self):
        data = valid_data()
        set_two_area_opening(data)
        area = data["opening_balance_review"]["areas"][0]
        area["account_comparisons"] = [
            {"prior_account": "TEST-U1", "opening_account": "TEST-U1", "prior_balance": "-100.00", "opening_balance": "0.00", "currency": "EUR", "group_id": "UST"},
            {"prior_account": "TEST-U2", "opening_account": "TEST-U2", "prior_balance": "0.00", "opening_balance": "-100.00", "currency": "EUR", "group_id": "UST"},
        ]
        area["compared_account_count"] = 2
        area["groups"] = [{"id": "UST", "kind": "umsatzsteuer", "currency": "EUR",
                          "source_refs": ["handelsrecht-VORJAHR"], "reason": "Belegte Umgliederung", "next_action": "Keine."}]
        self.assertEqual(self.errors(data), [])
        area["groups"] = []
        self.assertTrue(any("Prüfgruppe" in e for e in self.errors(data)))

    def test_account_cannot_be_counted_twice_in_groups(self):
        data = reference_12500()
        area = data["opening_balance_review"]["areas"][0]
        area["account_comparisons"].append(deepcopy(area["account_comparisons"][0]))
        area["compared_account_count"] = 2
        self.assertTrue(any("Doppelte Kontenzuordnung" in e for e in self.errors(data)))


class OposReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.data = valid_data()
        set_reconciled_opos(self.data)
        self.row = self.data["open_items"]["reconciliation"][0]

    def errors(self):
        return validate_review_data.validate_review_data(self.data)

    def test_complete_empty_sides_are_explicitly_reconciled(self):
        self.assertEqual(self.errors(), [])

    def test_signed_credit_balance_reconciles(self):
        row = self.data["open_items"]["reconciliation"][2]
        row["expected_accounts"] = ["70001|EUR"]
        row["account_comparisons"] = [{"account": "70001", "currency": "EUR", "opos_balance": "-88.00", "ledger_balance": "-88.00"}]
        self.assertEqual(self.errors(), [])

    def test_equal_grand_total_does_not_hide_account_differences(self):
        self.row["expected_accounts"] = ["10001|EUR", "10002|EUR"]
        self.row["account_comparisons"] = [
            {"account": "10001", "currency": "EUR", "opos_balance": "101.00", "ledger_balance": "100.00"},
            {"account": "10002", "currency": "EUR", "opos_balance": "99.00", "ledger_balance": "100.00"},
        ]
        self.assertEqual(sum("Kontendifferenz" in e for e in self.errors()), 2)

    def test_historical_date_filter_does_not_prove_historical_open_items(self):
        self.data["open_items"]["reconciliation"][1]["historical_method"] = "date_filter_on_current"
        self.assertTrue(any("historischer Nachweis" in e for e in self.errors()))

    def test_mismatched_cutoffs_are_not_reconciled(self):
        self.row["ledger_as_of"] = "2027-01-31"
        self.assertTrue(any("unterschiedliche Stichtage" in e for e in self.errors()))

    def test_source_snapshot_drift_is_rejected(self):
        self.data["sources"][0]["snapshot_id"] = "OTHER"
        self.assertTrue(any("gleichen Datenstand" in e for e in self.errors()))

    def test_truncated_source_is_not_complete(self):
        self.data["sources"][0]["complete"] = False
        self.assertTrue(any("unvollständig" in e for e in self.errors()))

    def test_missing_person_account_is_not_silently_zero(self):
        self.row["expected_accounts"] = ["10001|EUR"]
        self.assertTrue(any("Kontenabdeckung" in e for e in self.errors()))

    def test_missing_creditor_side_is_rejected(self):
        self.data["open_items"]["reconciliation"].pop()
        self.assertTrue(any("beide Seiten" in e for e in self.errors()))

    def test_control_account_difference_blocks_reconciled_status(self):
        self.row["control_differences"] = [{"account": "TEST-SAMMEL", "amount": "0.01"}]
        self.assertTrue(any("control_differences" in e for e in self.errors()))

    def test_partial_item_matching_is_not_reconciled(self):
        self.row["item_check_complete"] = False
        self.assertTrue(any("item_check_complete" in e for e in self.errors()))


if __name__ == "__main__":
    unittest.main()
