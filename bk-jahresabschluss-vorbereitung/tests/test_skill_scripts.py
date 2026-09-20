from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Modul kann nicht geladen werden: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sharepoint_target = load_module("sharepoint_target", ROOT / "scripts" / "sharepoint_target.py")
validate_review_data = load_module("validate_review_data", ROOT / "scripts" / "validate_review_data.py")


CORE_TOPICS = (
    "quellen_datenstand",
    "eroeffnungsbilanz",
    "bilanzkonten_abdeckung",
    "opos_debitoren",
    "opos_kreditoren",
    "bank_kasse",
    "geldtransit",
    "durchlaufende_posten",
    "lohnkonten",
    "steuerkonten",
    "abgrenzungen",
    "vorjahr_rollforward",
)


def checklist_item(topic_id: str) -> dict:
    return {
        "id": f"CHK-{topic_id.upper()}",
        "module": "startklarheit",
        "topic_id": topic_id,
        "status": "NICHT_ANWENDBAR",
        "description": f"Struktureller Testeintrag für {topic_id}",
        "account_numbers": [],
        "account_purpose": "",
        "balance": None,
        "currency": "",
        "zero_expectation": "KEINE_NULLERWARTUNG",
        "source_refs": [],
        "evidence_refs": [],
        "work_lane": "ERLEDIGT",
        "blocks_start": False,
        "next_action": "Keine.",
        "reviewer_comment": "",
    }


def valid_data() -> dict:
    data = {
        "schema_version": "0.5.0",
        "execution_status": "preparation_only",
        "overall_status": "ENTWURF",
        "mandant": {"number": "12345", "datev_client_id": "guid", "name": "Test"},
        "target_fiscal_year": {
            "id": "20260101",
            "start": "2026-01-01",
            "end": "2026-12-31",
            "account_length": 4,
            "accounting_method": "bilanz",
        },
        "prior_fiscal_year": {"id": "20250101", "start": "2025-01-01", "end": "2025-12-31"},
        "sources": [],
        "opening_balance_review": {
            "area_inventory_status": "NICHT_PRUEFBAR",
            "area_inventory_source_refs": [],
            "expected_areas": [],
            "areas": [],
        },
        "account_inventory": {"debitors": [], "creditors": [], "balance_sheet_accounts": []},
        "open_items": {"receivable": [], "payable": [], "clearing_candidates": []},
        "preparation_checklist": [checklist_item(topic) for topic in CORE_TOPICS],
        "findings": [],
        "posting_proposals": [],
        "prior_year_closing_entries": [],
        "handoff_to_annual_close": [],
        "employee_tasks": [],
        "gates": [],
    }
    opening_row = next(row for row in data["preparation_checklist"] if row["topic_id"] == "eroeffnungsbilanz")
    opening_row.update(
        {
            "status": "NICHT_PRUEFBAR",
            "work_lane": "UNTERLAGE_ANFORDERN",
            "blocks_start": True,
            "next_action": "Bereichsinventar und bereichsspezifische Auswertungen anfordern.",
        }
    )
    data["open_items"]["reconciliation"] = [
        {"side": side, "basis": basis, "status": "NICHT_PRUEFBAR", "next_action": "Vollständigen Abgleich beschaffen."}
        for side in ("receivable", "payable") for basis in ("current", "closing")
    ]
    for row in data["preparation_checklist"]:
        if row["topic_id"] in {"opos_debitoren", "opos_kreditoren"}:
            row.update(status="NICHT_PRUEFBAR", work_lane="UNTERLAGE_ANFORDERN", blocks_start=True)
    return data


def add_opening_source(data: dict, source_id: str, area_id: str | None, year_id: str) -> None:
    source = {
        "id": source_id,
        "kind": "upload",
        "uri": f"test://{source_id}",
        "retrieved_at": "2026-09-20T12:00:00+02:00",
        "complete": True,
        "fiscal_year_id": year_id,
        "proof_kind": "direct_area",
    }
    if area_id is not None:
        source["accounting_area_id"] = area_id
    data["sources"].append(source)


def reconciled_area(area_id: str) -> dict:
    return {
        "area_id": area_id,
        "status": "ABGESTIMMT",
        "evidence_extent": "vollstaendig",
        "prior_close_source_ref": f"{area_id}-VORJAHR",
        "current_opening_source_ref": f"{area_id}-EB",
        "prior_close_final": True,
        "comparison_complete": True,
        "compared_account_count": 1,
        "account_comparisons": [
            {
                "prior_account": "1200",
                "opening_account": "1200",
                "prior_balance": "100.00",
                "opening_balance": "100.00",
                "currency": "EUR",
            }
        ],
        "differences": [],
        "unmapped_accounts": [],
        "next_action": "Keine.",
    }


def set_two_area_opening(data: dict) -> None:
    add_opening_source(data, "BEREICHE", None, "20260101")
    for area_id in ("handelsrecht", "steuerrecht"):
        add_opening_source(data, f"{area_id}-VORJAHR", area_id, "20250101")
        add_opening_source(data, f"{area_id}-EB", area_id, "20260101")
    data["opening_balance_review"] = {
        "area_inventory_status": "BEKANNT",
        "area_inventory_source_refs": ["BEREICHE"],
        "expected_areas": ["handelsrecht", "steuerrecht"],
        "areas": [reconciled_area("handelsrecht"), reconciled_area("steuerrecht")],
    }
    opening_row = next(row for row in data["preparation_checklist"] if row["topic_id"] == "eroeffnungsbilanz")
    opening_row.update(
        {
            "status": "ABGESTIMMT",
            "source_refs": ["BEREICHE"],
            "evidence_refs": ["BEREICHE", "handelsrecht-EB", "steuerrecht-EB"],
            "work_lane": "ERLEDIGT",
            "blocks_start": False,
            "next_action": "Keine.",
        }
    )


def set_reconciled_opos(data: dict) -> None:
    for row in data["open_items"]["reconciliation"]:
        as_of = data["target_fiscal_year"]["end"] if row["basis"] == "closing" else "2027-02-28"
        snapshot_id = f"TEST-{row['side']}-{row['basis']}"
        refs = []
        for role in ("opos", "personenkonten", "sammelkonten"):
            source_id = f"{snapshot_id}-{role}"
            refs.append(source_id)
            data["sources"].append({"id": source_id, "kind": "upload", "uri": f"test://{source_id}", "retrieved_at": "2027-03-01T10:00:00+01:00", "complete": True, "as_of": as_of, "snapshot_id": snapshot_id, "side": row["side"], "reconciliation_role": role})
        row.update(status="ABGESTIMMT", complete=True, snapshot_consistent=True, item_check_complete=True, control_check_complete=True, opos_as_of=as_of, ledger_as_of=as_of, snapshot_id=snapshot_id, source_refs=refs, historical_method="historical_export", unresolved_items=[], control_differences=[], expected_accounts=[], account_comparisons=[])
    for row in data["preparation_checklist"]:
        if row["topic_id"] in {"opos_debitoren", "opos_kreditoren"}:
            refs = data["open_items"]["reconciliation"][0 if row["topic_id"] == "opos_debitoren" else 2]["source_refs"]
            row.update(status="ABGESTIMMT", evidence_refs=refs, source_refs=refs, work_lane="ERLEDIGT", blocks_start=False)


def small_amount_proposal(amount: str = "99.99", tax_key: str = "") -> dict:
    return {
        "id": "P-1",
        "module": "durchlaufende_posten",
        "status": "BUCHUNGSVORSCHLAG",
        "description": "Kleinbetrag umbuchen",
        "next_action": "fachlich freigeben",
        "reviewer_comment": "",
        "source_refs": ["DATEV-1"],
        "amount": amount,
        "currency": "EUR",
        "date": "2026-12-31",
        "account": "4980",
        "contra_account": "1590",
        "debit_credit": "S",
        "document_field1": "K-1",
        "posting_text": "Sonstiger Betriebsbedarf",
        "tax_key": tax_key,
        "reason": "Kanzleiregel",
        "confidence": "sicher",
        "approved": False,
        "rule_id": "K-1590-LT100",
        "functional_source_account": "1590",
        "functional_target_account": "4980",
        "account_mapping_source": "DATEV-1",
        "source_posting_id": "POSTING-1",
    }


def add_datev_source(data: dict) -> None:
    data["sources"].append(
        {
            "id": "DATEV-1",
            "kind": "datev",
            "uri": "datev://accounting/account_postings",
            "retrieved_at": "2026-08-23T12:00:00+02:00",
            "complete": True,
        }
    )


def set_payroll_check(data: dict, *, account: str, balance: str, status: str, zero_expectation: str, with_evidence: bool) -> None:
    row = next(row for row in data["preparation_checklist"] if row["topic_id"] == "lohnkonten")
    row.update(
        {
            "status": status,
            "description": f"Lohnkonto {account} abgestimmt",
            "account_numbers": [account],
            "account_purpose": "Lohnabstimmung",
            "balance": balance,
            "currency": "EUR",
            "zero_expectation": zero_expectation,
            "source_refs": ["DATEV-1"],
            "evidence_refs": ["DATEV-1"] if with_evidence else [],
            "work_lane": "ERLEDIGT",
        }
    )
    data["account_inventory"]["balance_sheet_accounts"].append(
        {
            "account": account,
            "caption": "Lohnkonto",
            "purpose": "payroll_liability",
            "balance": balance,
            "currency": "EUR",
            "checklist_item_id": row["id"],
        }
    )


class SharePointTargetTests(unittest.TestCase):
    def test_exact_targets(self) -> None:
        result = sharepoint_target.build_targets("12861")
        self.assertTrue(result["profile_url"].endswith("/Mandantenprofile/12861.md"))
        self.assertTrue(result["accrual_url"].endswith("/Abgrenzungsregister/12861.md"))
        self.assertEqual(result["review_sheet_status"], "nicht_konfiguriert")

    def test_invalid_client_number(self) -> None:
        with self.assertRaises(ValueError):
            sharepoint_target.build_targets("1286")


class ReviewValidationTests(unittest.TestCase):
    def test_valid_minimum(self) -> None:
        self.assertEqual(validate_review_data.validate_review_data(valid_data()), [])

    def test_two_reconciled_opening_areas_allow_ready(self) -> None:
        data = valid_data()
        set_two_area_opening(data)
        set_reconciled_opos(data)
        data["overall_status"] = "STARTKLAR_FUER_ABSCHLUSSBEARBEITUNG"
        self.assertEqual(validate_review_data.validate_review_data(data), [])

    def test_missing_tax_area_is_rejected_even_if_checklist_says_reconciled(self) -> None:
        data = valid_data()
        set_two_area_opening(data)
        data["opening_balance_review"]["areas"].pop()
        errors = validate_review_data.validate_review_data(data)
        self.assertTrue(any("Eröffnungsbilanzbereiche fehlen" in error for error in errors))
        self.assertTrue(any("nicht ABGESTIMMT" in error for error in errors))

    def test_tax_area_cannot_use_trade_area_source(self) -> None:
        data = valid_data()
        set_two_area_opening(data)
        data["opening_balance_review"]["areas"][1]["current_opening_source_ref"] = "handelsrecht-EB"
        errors = validate_review_data.validate_review_data(data)
        self.assertTrue(any("passende Bereichskennung" in error for error in errors))

    def test_reconciled_area_rejects_account_difference(self) -> None:
        data = valid_data()
        set_two_area_opening(data)
        data["opening_balance_review"]["areas"][0]["account_comparisons"][0]["opening_balance"] = "99.99"
        errors = validate_review_data.validate_review_data(data)
        self.assertTrue(any("abweichenden Kontenbeträgen" in error for error in errors))

    def test_opening_source_from_wrong_year_is_rejected(self) -> None:
        data = valid_data()
        set_two_area_opening(data)
        source = next(source for source in data["sources"] if source["id"] == "steuerrecht-EB")
        source["fiscal_year_id"] = "20250101"
        errors = validate_review_data.validate_review_data(data)
        self.assertTrue(any("passenden Wirtschaftsjahr" in error for error in errors))

    def test_euer_has_no_opening_balance_area(self) -> None:
        data = valid_data()
        data["target_fiscal_year"]["accounting_method"] = "euer"
        data["opening_balance_review"]["area_inventory_status"] = "NICHT_ANWENDBAR"
        opening_row = next(row for row in data["preparation_checklist"] if row["topic_id"] == "eroeffnungsbilanz")
        opening_row.update({"status": "NICHT_ANWENDBAR", "work_lane": "ERLEDIGT", "blocks_start": False})
        self.assertEqual(validate_review_data.validate_review_data(data), [])

    def test_ready_rejects_unknown_area_inventory(self) -> None:
        data = valid_data()
        data["overall_status"] = "STARTKLAR_FUER_ABSCHLUSSBEARBEITUNG"
        errors = validate_review_data.validate_review_data(data)
        self.assertTrue(any("abgestimmte Eröffnungsbilanz" in error for error in errors))

    def test_unresolved_tax_area_blocks_start(self) -> None:
        data = valid_data()
        set_two_area_opening(data)
        data["opening_balance_review"]["areas"][1].update(
            {"status": "NICHT_PRUEFBAR", "current_opening_source_ref": None, "comparison_complete": False}
        )
        data["overall_status"] = "STARTKLAR_FUER_ABSCHLUSSBEARBEITUNG"
        errors = validate_review_data.validate_review_data(data)
        self.assertTrue(any("Fehlende Eröffnungsbilanz-Bereichsabdeckung" in error for error in errors))
        self.assertTrue(any("STARTKLAR verlangt die abgestimmte Eröffnungsbilanz" in error for error in errors))

    def test_small_amount_rule_rejects_100_eur(self) -> None:
        data = valid_data()
        add_datev_source(data)
        data["posting_proposals"].append(small_amount_proposal(amount="100.00"))
        errors = validate_review_data.validate_review_data(data)
        self.assertTrue(any("abs(Betrag) < 100.00" in error for error in errors))

    def test_small_amount_rule_accepts_99_99_without_tax(self) -> None:
        data = valid_data()
        add_datev_source(data)
        data["posting_proposals"].append(small_amount_proposal())
        self.assertEqual(validate_review_data.validate_review_data(data), [])

    def test_small_amount_rule_rejects_tax_key(self) -> None:
        data = valid_data()
        add_datev_source(data)
        data["posting_proposals"].append(small_amount_proposal(tax_key="9"))
        errors = validate_review_data.validate_review_data(data)
        self.assertTrue(any("leeren tax_key" in error for error in errors))

    def test_unknown_source_reference_is_rejected(self) -> None:
        data = valid_data()
        data["posting_proposals"].append(small_amount_proposal())
        errors = validate_review_data.validate_review_data(data)
        self.assertTrue(any("unbekannte Quelle" in error for error in errors))

    def test_small_amount_rule_requires_live_account_mapping(self) -> None:
        data = valid_data()
        add_datev_source(data)
        proposal = small_amount_proposal()
        proposal["account_mapping_source"] = ""
        data["posting_proposals"].append(proposal)
        errors = validate_review_data.validate_review_data(data)
        self.assertTrue(any("Live-Kontenplanprüfung" in error for error in errors))

    def test_missing_prior_year_requires_gate(self) -> None:
        data = valid_data()
        data["prior_fiscal_year"] = None
        errors = validate_review_data.validate_review_data(data)
        self.assertTrue(any("Vorjahr" in error for error in errors))

    def test_missing_core_checklist_topic_is_rejected(self) -> None:
        data = valid_data()
        data["preparation_checklist"] = [
            row for row in data["preparation_checklist"] if row["topic_id"] != "lohnkonten"
        ]
        errors = validate_review_data.validate_review_data(data)
        self.assertTrue(any("lohnkonten" in error for error in errors))

    def test_nonzero_payroll_balance_requires_evidence(self) -> None:
        data = valid_data()
        add_datev_source(data)
        set_payroll_check(
            data,
            account="1741",
            balance="123.45",
            status="ABGESTIMMT",
            zero_expectation="NULL_ODER_NACHWEIS",
            with_evidence=False,
        )
        errors = validate_review_data.validate_review_data(data)
        self.assertTrue(any("evidence_refs" in error for error in errors))

    def test_nonzero_payroll_balance_with_evidence_is_valid(self) -> None:
        data = valid_data()
        add_datev_source(data)
        set_payroll_check(
            data,
            account="1741",
            balance="123.45",
            status="ABGESTIMMT",
            zero_expectation="NULL_ODER_NACHWEIS",
            with_evidence=True,
        )
        self.assertEqual(validate_review_data.validate_review_data(data), [])

    def test_must_zero_payroll_clearing_rejects_residual_balance(self) -> None:
        data = valid_data()
        add_datev_source(data)
        set_payroll_check(
            data,
            account="1755",
            balance="1.00",
            status="ABGESTIMMT",
            zero_expectation="MUSS_NULL",
            with_evidence=True,
        )
        errors = validate_review_data.validate_review_data(data)
        self.assertTrue(any("MUSS_NULL" in error for error in errors))

    def test_zero_status_requires_explicit_zero_balance(self) -> None:
        data = valid_data()
        payroll = next(row for row in data["preparation_checklist"] if row["topic_id"] == "lohnkonten")
        payroll.update(
            {
                "status": "AUF_NULL",
                "work_lane": "ERLEDIGT",
                "zero_expectation": "MUSS_NULL",
            }
        )
        errors = validate_review_data.validate_review_data(data)
        self.assertTrue(any("AUF_NULL verlangt balance 0.00" in error for error in errors))

    def test_unclassified_balance_sheet_account_is_rejected(self) -> None:
        data = valid_data()
        data["account_inventory"]["balance_sheet_accounts"].append(
            {
                "account": "1740",
                "caption": "Verbindlichkeiten aus Lohn und Gehalt",
                "purpose": "payroll_net_liability",
                "balance": "0.00",
                "currency": "EUR",
                "checklist_item_id": "CHK-UNBEKANNT",
            }
        )
        errors = validate_review_data.validate_review_data(data)
        self.assertTrue(any("checklist_item_id" in error for error in errors))

    def test_start_ready_rejects_open_start_blocker(self) -> None:
        data = valid_data()
        data["overall_status"] = "STARTKLAR_FUER_ABSCHLUSSBEARBEITUNG"
        blocker = data["preparation_checklist"][0]
        blocker.update(
            {
                "status": "ZU_BEREINIGEN",
                "work_lane": "VOR_START_BEREINIGEN",
                "blocks_start": True,
                "next_action": "Saldo aufklären.",
            }
        )
        errors = validate_review_data.validate_review_data(data)
        self.assertTrue(any("offenen Startblockern" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
