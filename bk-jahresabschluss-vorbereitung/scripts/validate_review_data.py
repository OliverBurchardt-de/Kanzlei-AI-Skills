from __future__ import annotations

import argparse
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
from typing import Any


ALLOWED_STATUSES = {
    "IM_VORBEREITUNGSSCOPE_UNAUFFAELLIG",
    "AUF_NULL",
    "ABGESTIMMT",
    "ZU_BEREINIGEN",
    "UNTERLAGE_FEHLT",
    "NICHT_ANWENDBAR",
    "AUSZIFFERBAR",
    "BUCHUNGSVORSCHLAG",
    "FACHLICH_ZU_KLAEREN",
    "NICHT_PRUEFBAR",
    "BLOCKIERT",
}

ROW_COLLECTIONS = (
    "preparation_checklist",
    "findings",
    "posting_proposals",
    "prior_year_closing_entries",
    "handoff_to_annual_close",
    "employee_tasks",
    "gates",
)

CORE_TOPICS = {
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
}

ZERO_EXPECTATIONS = {"MUSS_NULL", "NULL_ODER_NACHWEIS", "KEINE_NULLERWARTUNG"}
WORK_LANES = {"ERLEDIGT", "VOR_START_BEREINIGEN", "UNTERLAGE_ANFORDERN", "IM_ABSCHLUSS_PRUEFEN"}
RESOLVED_CHECKLIST_STATUSES = {"AUF_NULL", "ABGESTIMMT", "NICHT_ANWENDBAR", "IM_VORBEREITUNGSSCOPE_UNAUFFAELLIG"}

PROPOSAL_STRING_FIELDS = (
    "currency",
    "date",
    "account",
    "contra_account",
    "debit_credit",
    "document_field1",
    "posting_text",
    "tax_key",
    "reason",
    "confidence",
)


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def parse_iso_date(value: Any, path: str, errors: list[str]) -> date | None:
    if not isinstance(value, str):
        errors.append(f"{path} muss ein ISO-Datumsstring sein.")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append(f"{path} ist kein gültiges ISO-Datum: {value!r}")
        return None


def parse_money(value: Any, path: str, errors: list[str]) -> Decimal | None:
    if not isinstance(value, str) or not re.fullmatch(r"-?\d+\.\d{2}", value):
        errors.append(f"{path} muss ein Dezimalstring mit zwei Nachkommastellen sein.")
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        errors.append(f"{path} ist kein gültiger Geldbetrag.")
        return None


def validate_common_row(row: Any, path: str, errors: list[str], ids: set[str]) -> None:
    if not isinstance(row, dict):
        errors.append(f"{path} muss ein Objekt sein.")
        return
    row_id = row.get("id")
    require(isinstance(row_id, str) and bool(row_id.strip()), f"{path}.id fehlt.", errors)
    if isinstance(row_id, str) and row_id:
        require(row_id not in ids, f"Doppelte id: {row_id}", errors)
        ids.add(row_id)
    require(isinstance(row.get("module"), str) and bool(row["module"].strip()), f"{path}.module fehlt.", errors)
    require(row.get("status") in ALLOWED_STATUSES, f"{path}.status ist unzulässig.", errors)
    require(isinstance(row.get("description"), str) and bool(row["description"].strip()), f"{path}.description fehlt.", errors)
    require(isinstance(row.get("next_action"), str), f"{path}.next_action fehlt.", errors)
    require("reviewer_comment" in row and isinstance(row.get("reviewer_comment"), str), f"{path}.reviewer_comment fehlt.", errors)
    source_refs = row.get("source_refs", [])
    require(isinstance(source_refs, list) and all(isinstance(ref, str) for ref in source_refs), f"{path}.source_refs muss eine Stringliste sein.", errors)


def validate_review_data(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["Wurzel muss ein JSON-Objekt sein."]

    require(data.get("schema_version") == "0.3.1", "schema_version muss 0.3.1 sein.", errors)
    require(data.get("execution_status") == "preparation_only", "execution_status muss preparation_only sein.", errors)
    require(data.get("overall_status") in {"ENTWURF", "VORBEREITUNG_OFFEN", "STARTKLAR_FUER_ABSCHLUSSBEARBEITUNG", "BLOCKIERT"}, "overall_status ist unzulässig.", errors)

    mandant = data.get("mandant")
    require(isinstance(mandant, dict), "mandant fehlt.", errors)
    if isinstance(mandant, dict):
        require(bool(re.fullmatch(r"\d{5}", str(mandant.get("number", "")))), "mandant.number muss fünfstellig sein.", errors)
        require(isinstance(mandant.get("datev_client_id"), str) and bool(mandant["datev_client_id"]), "mandant.datev_client_id fehlt.", errors)
        require(isinstance(mandant.get("name"), str) and bool(mandant["name"].strip()), "mandant.name fehlt.", errors)

    target = data.get("target_fiscal_year")
    require(isinstance(target, dict), "target_fiscal_year fehlt.", errors)
    target_start = target_end = None
    if isinstance(target, dict):
        require(isinstance(target.get("id"), str) and bool(target["id"]), "target_fiscal_year.id fehlt.", errors)
        target_start = parse_iso_date(target.get("start"), "target_fiscal_year.start", errors)
        target_end = parse_iso_date(target.get("end"), "target_fiscal_year.end", errors)
        if target_start and target_end:
            require(target_start <= target_end, "Zielwirtschaftsjahr hat einen ungültigen Zeitraum.", errors)
        require(isinstance(target.get("account_length"), int) and target["account_length"] > 0, "target_fiscal_year.account_length fehlt.", errors)
        require(target.get("accounting_method") in {"bilanz", "euer", "unbekannt"}, "target_fiscal_year.accounting_method ist unzulässig.", errors)

    prior = data.get("prior_fiscal_year")
    if prior is not None:
        require(isinstance(prior, dict), "prior_fiscal_year muss Objekt oder null sein.", errors)
        if isinstance(prior, dict):
            require(isinstance(prior.get("id"), str) and bool(prior["id"]), "prior_fiscal_year.id fehlt.", errors)
            prior_start = parse_iso_date(prior.get("start"), "prior_fiscal_year.start", errors)
            prior_end = parse_iso_date(prior.get("end"), "prior_fiscal_year.end", errors)
            if prior_start and prior_end:
                require(prior_start <= prior_end, "Vorwirtschaftsjahr hat einen ungültigen Zeitraum.", errors)
            if prior_end and target_start:
                require(prior_end + timedelta(days=1) == target_start, "Vor- und Zielwirtschaftsjahr schließen nicht unmittelbar aneinander an.", errors)

    for key in ("sources", "preparation_checklist", "findings", "posting_proposals", "prior_year_closing_entries", "handoff_to_annual_close", "employee_tasks", "gates"):
        require(isinstance(data.get(key), list), f"{key} muss eine Liste sein.", errors)
    account_inventory = data.get("account_inventory")
    require(isinstance(account_inventory, dict), "account_inventory fehlt.", errors)
    if isinstance(account_inventory, dict):
        require(isinstance(account_inventory.get("debitors"), list), "account_inventory.debitors muss eine Liste sein.", errors)
        require(isinstance(account_inventory.get("creditors"), list), "account_inventory.creditors muss eine Liste sein.", errors)
        require(isinstance(account_inventory.get("balance_sheet_accounts"), list), "account_inventory.balance_sheet_accounts muss eine Liste sein.", errors)
    open_items = data.get("open_items")
    require(isinstance(open_items, dict), "open_items fehlt.", errors)
    if isinstance(open_items, dict):
        for key in ("receivable", "payable", "clearing_candidates"):
            require(isinstance(open_items.get(key), list), f"open_items.{key} muss eine Liste sein.", errors)

    source_ids: set[str] = set()
    sources = data.get("sources", [])
    if isinstance(sources, list):
        for index, source in enumerate(sources):
            path = f"sources[{index}]"
            if not isinstance(source, dict):
                errors.append(f"{path} muss ein Objekt sein.")
                continue
            source_id = source.get("id")
            require(isinstance(source_id, str) and bool(source_id), f"{path}.id fehlt.", errors)
            if isinstance(source_id, str) and source_id:
                require(source_id not in source_ids, f"Doppelte Quellen-id: {source_id}", errors)
                source_ids.add(source_id)
            require(source.get("kind") in {"datev", "sharepoint", "upload", "calculation"}, f"{path}.kind ist unzulässig.", errors)
            require(isinstance(source.get("uri"), str) and bool(source["uri"]), f"{path}.uri fehlt.", errors)
            require(isinstance(source.get("retrieved_at"), str) and bool(source["retrieved_at"]), f"{path}.retrieved_at fehlt.", errors)
            require(isinstance(source.get("complete"), bool), f"{path}.complete muss boolesch sein.", errors)
            if source.get("kind") == "sharepoint":
                for field in ("file_id", "file_name", "modified_at"):
                    require(isinstance(source.get(field), str) and bool(source.get(field)), f"{path}.{field} ist für SharePoint-Quellen erforderlich.", errors)
                require(isinstance(source.get("sha256"), str) and bool(re.fullmatch(r"[0-9a-fA-F]{64}", source.get("sha256") or "")), f"{path}.sha256 muss ein 64-stelliger Hex-Wert sein.", errors)

    ids: set[str] = set()
    for collection in ROW_COLLECTIONS:
        rows = data.get(collection, [])
        if isinstance(rows, list):
            for index, row in enumerate(rows):
                validate_common_row(row, f"{collection}[{index}]", errors, ids)

    checklist = data.get("preparation_checklist", [])
    checklist_ids: set[str] = set()
    checklist_topics: set[str] = set()
    if isinstance(checklist, list):
        for index, row in enumerate(checklist):
            path = f"preparation_checklist[{index}]"
            if not isinstance(row, dict):
                continue
            row_id = row.get("id")
            if isinstance(row_id, str) and row_id:
                checklist_ids.add(row_id)
            topic_id = row.get("topic_id")
            require(isinstance(topic_id, str) and bool(topic_id.strip()), f"{path}.topic_id fehlt.", errors)
            if isinstance(topic_id, str) and topic_id:
                checklist_topics.add(topic_id)
            require(isinstance(row.get("account_numbers"), list) and all(isinstance(account, str) for account in row.get("account_numbers", [])), f"{path}.account_numbers muss eine Stringliste sein.", errors)
            require(isinstance(row.get("account_purpose"), str), f"{path}.account_purpose fehlt.", errors)
            balance = row.get("balance")
            parsed_balance = None
            if balance is not None:
                parsed_balance = parse_money(balance, f"{path}.balance", errors)
            currency = row.get("currency")
            require(isinstance(currency, str) and (currency == "" or bool(re.fullmatch(r"[A-Z]{3}", currency))), f"{path}.currency muss leer oder ein dreistelliger ISO-Code sein.", errors)
            if balance is not None:
                require(isinstance(currency, str) and bool(re.fullmatch(r"[A-Z]{3}", currency)), f"{path}.currency ist bei einem Kontosaldo erforderlich.", errors)
            require(row.get("zero_expectation") in ZERO_EXPECTATIONS, f"{path}.zero_expectation ist unzulässig.", errors)
            evidence_refs = row.get("evidence_refs")
            require(isinstance(evidence_refs, list) and all(isinstance(ref, str) for ref in evidence_refs), f"{path}.evidence_refs muss eine Stringliste sein.", errors)
            require(row.get("work_lane") in WORK_LANES, f"{path}.work_lane ist unzulässig.", errors)
            require(isinstance(row.get("blocks_start"), bool), f"{path}.blocks_start muss boolesch sein.", errors)
            if row.get("status") == "AUF_NULL":
                require(parsed_balance == Decimal("0.00"), f"{path}: AUF_NULL verlangt balance 0.00.", errors)
            if row.get("status") == "ABGESTIMMT":
                if parsed_balance is not None and row.get("zero_expectation") == "MUSS_NULL":
                    require(parsed_balance == Decimal("0.00"), f"{path}: MUSS_NULL darf nicht mit einem Restsaldo abgestimmt werden.", errors)
                if parsed_balance is None or parsed_balance != Decimal("0.00"):
                    require(bool(evidence_refs), f"{path}: ABGESTIMMT mit Restsaldo oder ohne Kontosaldo benötigt evidence_refs.", errors)
            if row.get("work_lane") == "ERLEDIGT":
                require(row.get("status") in RESOLVED_CHECKLIST_STATUSES, f"{path}: ERLEDIGT verlangt einen erledigten Status.", errors)
            if row.get("work_lane") in {"VOR_START_BEREINIGEN", "UNTERLAGE_ANFORDERN"}:
                require(row.get("blocks_start") is True, f"{path}: Die Arbeitsspur vor Start muss blocks_start=true setzen.", errors)

    missing_topics = sorted(CORE_TOPICS - checklist_topics)
    require(not missing_topics, f"Pflicht-Themen der Startklarheits-Checkliste fehlen: {', '.join(missing_topics)}", errors)

    if isinstance(account_inventory, dict) and isinstance(account_inventory.get("balance_sheet_accounts"), list):
        account_numbers: set[str] = set()
        for index, account_row in enumerate(account_inventory["balance_sheet_accounts"]):
            path = f"account_inventory.balance_sheet_accounts[{index}]"
            if not isinstance(account_row, dict):
                errors.append(f"{path} muss ein Objekt sein.")
                continue
            account = account_row.get("account")
            require(isinstance(account, str) and bool(account), f"{path}.account fehlt.", errors)
            if isinstance(account, str) and account:
                require(account not in account_numbers, f"Doppeltes Bilanzkonto im Inventar: {account}", errors)
                account_numbers.add(account)
            require(isinstance(account_row.get("caption"), str) and bool(account_row.get("caption")), f"{path}.caption fehlt.", errors)
            require(isinstance(account_row.get("purpose"), str) and bool(account_row.get("purpose")), f"{path}.purpose fehlt.", errors)
            parse_money(account_row.get("balance"), f"{path}.balance", errors)
            require(isinstance(account_row.get("currency"), str) and bool(re.fullmatch(r"[A-Z]{3}", account_row.get("currency", ""))), f"{path}.currency muss ein dreistelliger ISO-Code sein.", errors)
            checklist_item_id = account_row.get("checklist_item_id")
            require(isinstance(checklist_item_id, str) and checklist_item_id in checklist_ids, f"{path}.checklist_item_id verweist nicht auf einen Checklisteneintrag.", errors)

    if isinstance(open_items, dict) and isinstance(open_items.get("clearing_candidates"), list):
        for index, row in enumerate(open_items["clearing_candidates"]):
            validate_common_row(row, f"open_items.clearing_candidates[{index}]", errors, ids)

    for collection in (*ROW_COLLECTIONS,):
        rows = data.get(collection, [])
        if not isinstance(rows, list):
            continue
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            for source_ref in row.get("source_refs", []):
                require(source_ref in source_ids, f"{collection}[{index}] verweist auf unbekannte Quelle {source_ref!r}.", errors)
            if collection == "preparation_checklist":
                for evidence_ref in row.get("evidence_refs", []):
                    require(evidence_ref in source_ids, f"{collection}[{index}] verweist auf unbekannten Nachweis {evidence_ref!r}.", errors)
    if isinstance(open_items, dict) and isinstance(open_items.get("clearing_candidates"), list):
        for index, row in enumerate(open_items["clearing_candidates"]):
            if not isinstance(row, dict):
                continue
            for source_ref in row.get("source_refs", []):
                require(source_ref in source_ids, f"open_items.clearing_candidates[{index}] verweist auf unbekannte Quelle {source_ref!r}.", errors)

    proposals = data.get("posting_proposals", [])
    if isinstance(proposals, list):
        for index, row in enumerate(proposals):
            if not isinstance(row, dict):
                continue
            path = f"posting_proposals[{index}]"
            amount = parse_money(row.get("amount"), f"{path}.amount", errors)
            require(row.get("approved") is False, f"{path}.approved muss false sein.", errors)
            for field in PROPOSAL_STRING_FIELDS:
                require(isinstance(row.get(field), str) and (field in {"document_field1", "tax_key"} or bool(row.get(field))), f"{path}.{field} muss ein gültiger String sein.", errors)
            parse_iso_date(row.get("date"), f"{path}.date", errors)
            require(isinstance(row.get("currency"), str) and bool(re.fullmatch(r"[A-Z]{3}", row.get("currency", ""))), f"{path}.currency muss ein dreistelliger ISO-Code sein.", errors)
            require(row.get("debit_credit") in {"S", "H"}, f"{path}.debit_credit muss S oder H sein.", errors)
            require(row.get("confidence") == "sicher", f"{path}.confidence ist für einen Buchungsvorschlag nicht ausreichend.", errors)
            source_refs = row.get("source_refs", [])
            has_posting_ref = isinstance(row.get("source_posting_id"), str) and bool(row.get("source_posting_id"))
            has_source_ref = isinstance(source_refs, list) and bool(source_refs)
            require(has_posting_ref or has_source_ref, f"{path}: Buchungsvorschlag benötigt source_posting_id oder mindestens eine source_ref.", errors)
            if row.get("rule_id") == "K-1590-LT100":
                if amount is not None:
                    require(abs(amount) < Decimal("100.00"), f"{path}: K-1590-LT100 verlangt abs(Betrag) < 100.00.", errors)
                require(row.get("tax_key") == "", f"{path}: Kleinbetragsregel verlangt leeren tax_key.", errors)
                require(isinstance(row.get("functional_source_account"), str) and bool(row.get("functional_source_account")), f"{path}: Quellkonto der Kleinbetragsregel ist nicht bestätigt.", errors)
                require(isinstance(row.get("functional_target_account"), str) and bool(row.get("functional_target_account")), f"{path}: Zielkonto der Kleinbetragsregel ist nicht bestätigt.", errors)
                require(isinstance(row.get("account_mapping_source"), str) and bool(row.get("account_mapping_source")), f"{path}: Nachweis der Live-Kontenplanprüfung fehlt.", errors)
                require(isinstance(row.get("source_posting_id"), str) and bool(row.get("source_posting_id")), f"{path}: source_posting_id fehlt.", errors)

    if prior is None:
        gates = data.get("gates", [])
        has_prior_gate = isinstance(gates, list) and any(
            isinstance(row, dict)
            and row.get("status") == "NICHT_PRUEFBAR"
            and row.get("module") == "vorjahr"
            for row in gates
        )
        require(has_prior_gate, "Bei fehlendem Vorjahr ist ein NICHT_PRUEFBAR-Gate für module=vorjahr erforderlich.", errors)

    if data.get("overall_status") == "STARTKLAR_FUER_ABSCHLUSSBEARBEITUNG" and isinstance(checklist, list):
        open_blockers = [
            row.get("id", f"Zeile {index}")
            for index, row in enumerate(checklist)
            if isinstance(row, dict)
            and row.get("blocks_start") is True
            and row.get("status") not in RESOLVED_CHECKLIST_STATUSES
        ]
        require(not open_blockers, f"STARTKLAR ist mit offenen Startblockern unzulässig: {', '.join(open_blockers)}", errors)

    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    errors = validate_review_data(data)
    if errors:
        for error in errors:
            print(f"FEHLER: {error}")
        raise SystemExit(1)
    print("Vorbereitungsdaten gültig: preparation_only | schema_version 0.3.1")


if __name__ == "__main__":
    main()
