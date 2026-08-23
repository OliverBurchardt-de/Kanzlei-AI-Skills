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
    return {
        "schema_version": "0.3.1",
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

    def test_sharepoint_source_requires_protocol_fields(self) -> None:
        data = valid_data()
        data["sources"].append(
            {
                "id": "SP-1",
                "kind": "sharepoint",
                "uri": "https://burchardtkollegen.sharepoint.com/sites/Wissen/Mandantenbesonderheiten/Mandantenprofile/12345.md",
                "retrieved_at": "2026-08-23T12:00:00+02:00",
                "complete": True,
            }
        )
        errors = validate_review_data.validate_review_data(data)
        self.assertTrue(any("file_id" in error for error in errors))
        self.assertTrue(any("sha256" in error for error in errors))

    def test_sharepoint_source_with_protocol_fields_is_valid(self) -> None:
        data = valid_data()
        data["sources"].append(
            {
                "id": "SP-1",
                "kind": "sharepoint",
                "uri": "https://burchardtkollegen.sharepoint.com/sites/Wissen/Mandantenbesonderheiten/Mandantenprofile/12345.md",
                "retrieved_at": "2026-08-23T12:00:00+02:00",
                "complete": True,
                "file_id": "b!abc123",
                "file_name": "12345.md",
                "modified_at": "2026-08-20T09:00:00+02:00",
                "sha256": "a" * 64,
            }
        )
        self.assertEqual(validate_review_data.validate_review_data(data), [])

    def test_proposal_requires_posting_reference(self) -> None:
        data = valid_data()
        add_datev_source(data)
        proposal = small_amount_proposal()
        del proposal["rule_id"]
        del proposal["source_posting_id"]
        proposal["source_refs"] = []
        data["posting_proposals"].append(proposal)
        errors = validate_review_data.validate_review_data(data)
        self.assertTrue(any("source_posting_id oder mindestens eine source_ref" in error for error in errors))

    def test_proposal_rejects_insufficient_confidence(self) -> None:
        data = valid_data()
        add_datev_source(data)
        proposal = small_amount_proposal()
        proposal["confidence"] = "hoch"
        data["posting_proposals"].append(proposal)
        errors = validate_review_data.validate_review_data(data)
        self.assertTrue(any("nicht ausreichend" in error for error in errors))

    def test_small_amount_rule_rejects_empty_target_account(self) -> None:
        data = valid_data()
        add_datev_source(data)
        proposal = small_amount_proposal()
        proposal["functional_target_account"] = ""
        data["posting_proposals"].append(proposal)
        errors = validate_review_data.validate_review_data(data)
        self.assertTrue(any("Zielkonto der Kleinbetragsregel" in error for error in errors))

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
