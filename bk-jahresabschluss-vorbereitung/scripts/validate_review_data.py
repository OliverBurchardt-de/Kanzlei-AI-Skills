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
    "TEILNACHWEIS",
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
}

ZERO_EXPECTATIONS = {"MUSS_NULL", "NULL_ODER_NACHWEIS", "KEINE_NULLERWARTUNG"}
WORK_LANES = {"ERLEDIGT", "VOR_START_BEREINIGEN", "UNTERLAGE_ANFORDERN", "IM_ABSCHLUSS_PRUEFEN"}
RESOLVED_CHECKLIST_STATUSES = {"AUF_NULL", "ABGESTIMMT", "NICHT_ANWENDBAR", "IM_VORBEREITUNGSSCOPE_UNAUFFAELLIG"}
OPENING_AREA_STATUSES = {"ABGESTIMMT", "TEILNACHWEIS", "FACHLICH_ZU_KLAEREN", "ZU_BEREINIGEN", "NICHT_PRUEFBAR", "NICHT_ANWENDBAR"}
OPENING_RESOLVED = {"ABGESTIMMT", "NICHT_ANWENDBAR"}
TOLERANCE = Decimal("0.005")
AREA_INVENTORY_STATUSES = {"BEKANNT", "NICHT_PRUEFBAR", "NICHT_ANWENDBAR"}

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


def checked_refs(value: Any, sources: dict, path: str, errors: list[str], *, complete: bool = False) -> list[dict]:
    require(isinstance(value, list) and bool(value), f"{path}: Quellen erforderlich.", errors)
    result = []
    if isinstance(value, list):
        for ref in value:
            source = sources.get(ref) if isinstance(ref, str) else None
            require(source is not None, f"{path}: unbekannte Quelle {ref!r}.", errors)
            if source is not None:
                result.append(source)
                if complete:
                    require(source.get("complete") is True, f"{path}: Quelle {ref!r} unvollständig.", errors)
    return result


def validate_opening_comparisons(area: dict, sources: dict, path: str, errors: list[str]) -> bool:
    comparisons = area.get("account_comparisons")
    require(isinstance(comparisons, list), f"{path}.account_comparisons muss eine Liste sein.", errors)
    if not isinstance(comparisons, list):
        return True
    require(area.get("compared_account_count") == len(comparisons), f"{path}.compared_account_count passt nicht zu account_comparisons.", errors)
    groups = area.get("groups", [])
    require(isinstance(groups, list), f"{path}.groups muss eine Liste sein.", errors)
    group_map = {}
    for group in groups if isinstance(groups, list) else []:
        if not isinstance(group, dict):
            errors.append(f"{path}.groups: Objekt erforderlich.")
            continue
        group_id = group.get("id")
        if not isinstance(group_id, str) or not group_id:
            errors.append(f"{path}.groups: id fehlt.")
            continue
        require(group_id not in group_map, f"{path}: Doppelte Prüfgruppe {group_id}.", errors)
        require(group.get("kind") in {"darlehen_gesellschafter", "umsatzsteuer", "ergebnisvortrag"}, f"{path}: Unzulässige Prüfgruppe.", errors)
        require(bool(group.get("reason")) and bool(group.get("next_action")), f"{path}: Gruppenbegründung/nächster Schritt fehlt.", errors)
        checked_refs(group.get("source_refs"), sources, f"{path}.groups.{group_id}", errors, complete=True)
        adjustment = Decimal("0.00")
        if group.get("kind") == "ergebnisvortrag":
            adjustment = parse_money(group.get("bridge_amount"), f"{path}.bridge_amount", errors)
            source = sources.get(group.get("bridge_source_ref"))
            require(isinstance(source, dict) and source.get("document_role") in {"finale_ja_susa", "festgestellter_abschluss", "abschlussbuchung"} and source.get("complete") is True and source.get("accounting_area_id") == area.get("area_id"), f"{path}: Ergebnisbrücke benötigt finale, bereichsgleiche Abschlussquelle.", errors)
            prior_source = sources.get(area.get("prior_close_source_ref"), {})
            if isinstance(source, dict):
                require(source.get("fiscal_year_id") == prior_source.get("fiscal_year_id"), f"{path}: Ergebnisbrücke gehört nicht zum Vorjahr.", errors)
        else:
            require(group.get("bridge_amount", "0.00") == "0.00", f"{path}: Umgliederungsgruppe darf keine Ergebnisbrücke enthalten.", errors)
        group_map[group_id] = {"adjustment": adjustment, "rows": [], "currency": group.get("currency")}
    seen_prior, seen_opening = set(), set()
    mismatch = False
    for index, comparison in enumerate(comparisons):
        row_path = f"{path}.account_comparisons[{index}]"
        if not isinstance(comparison, dict):
            errors.append(f"{row_path} muss ein Objekt sein.")
            continue
        currency = comparison.get("currency")
        require(isinstance(currency, str) and bool(re.fullmatch(r"[A-Z]{3}", currency)), f"{row_path}.currency muss ein ISO-Code sein.", errors)
        for field, seen in (("prior_account", seen_prior), ("opening_account", seen_opening)):
            account = comparison.get(field)
            require(isinstance(account, str) and bool(account), f"{row_path}.{field} fehlt.", errors)
            if isinstance(account, str) and isinstance(currency, str):
                key = (account, currency)
                require(key not in seen, f"{row_path}: Doppelte Kontenzuordnung.", errors)
                seen.add(key)
        prior_balance = parse_money(comparison.get("prior_balance"), f"{row_path}.prior_balance", errors)
        opening_balance = parse_money(comparison.get("opening_balance"), f"{row_path}.opening_balance", errors)
        group_id = comparison.get("group_id")
        group = group_map.get(group_id) if isinstance(group_id, str) else None
        if group_id is not None:
            require(group is not None, f"{row_path}: unbekannte Prüfgruppe.", errors)
        if group is not None:
            require(currency == group["currency"], f"{row_path}: Gruppenwährung weicht ab.", errors)
            group["rows"].append((prior_balance, opening_balance))
        elif prior_balance is not None and opening_balance is not None:
            mismatch |= abs(opening_balance - prior_balance) > TOLERANCE
        if comparison.get("prior_account") != comparison.get("opening_account"):
            require(comparison.get("mapping_source_ref") in sources, f"{row_path}: Kontenwechsel benötigt mapping_source_ref.", errors)
    for group_id, group in group_map.items():
        require(bool(group["rows"]), f"{path}: Leere Prüfgruppe {group_id}.", errors)
        if group["adjustment"] is None or any(a is None or b is None for a, b in group["rows"]):
            mismatch = True
        else:
            difference = sum((b - a for a, b in group["rows"]), Decimal("0")) - group["adjustment"]
            mismatch |= abs(difference) > TOLERANCE
    return mismatch


def validate_opos_reconciliation(data: dict, sources: dict, errors: list[str]) -> None:
    open_items = data.get("open_items", {})
    if not isinstance(open_items, dict):
        return
    rows = open_items.get("reconciliation")
    require(isinstance(rows, list), "open_items.reconciliation muss eine Liste sein.", errors)
    if not isinstance(rows, list):
        return
    seen, resolved = set(), {}
    for index, row in enumerate(rows):
        path = f"open_items.reconciliation[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{path} muss ein Objekt sein.")
            continue
        side, basis = row.get("side"), row.get("basis")
        if side not in {"receivable", "payable"} or basis not in {"current", "closing"}:
            errors.append(f"{path}: Seite/Zeitbezug unzulässig.")
            continue
        key = (side, basis)
        require(key not in seen, f"{path}: Doppelter OPOS-Abgleich.", errors)
        seen.add(key)
        status = row.get("status")
        require(status in OPENING_AREA_STATUSES - {"NICHT_ANWENDBAR"}, f"{path}.status ist unzulässig.", errors)
        require(isinstance(row.get("next_action"), str) and bool(row.get("next_action")), f"{path}.next_action fehlt.", errors)
        resolved[key] = status == "ABGESTIMMT"
        if status != "ABGESTIMMT":
            continue
        for flag in ("complete", "snapshot_consistent", "item_check_complete", "control_check_complete"):
            require(row.get(flag) is True, f"{path}.{flag} muss für ABGESTIMMT true sein.", errors)
        opos_date = parse_iso_date(row.get("opos_as_of"), f"{path}.opos_as_of", errors)
        ledger_date = parse_iso_date(row.get("ledger_as_of"), f"{path}.ledger_as_of", errors)
        require(opos_date == ledger_date, f"{path}: OPOS und Fibu haben unterschiedliche Stichtage.", errors)
        if basis == "closing":
            require(row.get("opos_as_of") == data.get("target_fiscal_year", {}).get("end"), f"{path}: Abschlussstichtag weicht ab.", errors)
            require(row.get("historical_method") in {"historical_export", "full_reconstruction"}, f"{path}: Datumsfilter auf aktuelle OPOS ist kein historischer Nachweis.", errors)
        refs = checked_refs(row.get("source_refs"), sources, path, errors, complete=True)
        require({"opos", "personenkonten", "sammelkonten"} <= {s.get("reconciliation_role") for s in refs}, f"{path}: Quellen für alle drei OPOS-Ebenen erforderlich.", errors)
        snapshot_id = row.get("snapshot_id")
        require(isinstance(snapshot_id, str) and bool(snapshot_id), f"{path}.snapshot_id fehlt.", errors)
        for source in refs:
            require(source.get("as_of") == row.get("opos_as_of") and source.get("snapshot_id") == snapshot_id and source.get("side") == side, f"{path}: Quelle gehört nicht zum gleichen Datenstand/zur gleichen Seite.", errors)
        for field in ("unresolved_items", "control_differences"):
            require(row.get(field) == [], f"{path}: ABGESTIMMT trotz offener {field} unzulässig.", errors)
        comparisons = row.get("account_comparisons")
        expected = row.get("expected_accounts")
        require(isinstance(expected, list) and all(isinstance(k, str) for k in expected), f"{path}.expected_accounts fehlt.", errors)
        require(isinstance(comparisons, list), f"{path}.account_comparisons fehlt.", errors)
        accounts = set()
        for comparison in comparisons if isinstance(comparisons, list) else []:
            if not isinstance(comparison, dict):
                errors.append(f"{path}: Kontenabgleich muss Objekt sein.")
                continue
            account, currency = comparison.get("account"), comparison.get("currency")
            require(isinstance(account, str) and bool(account) and isinstance(currency, str) and bool(re.fullmatch(r"[A-Z]{3}", currency)), f"{path}: Konto/Währung fehlt.", errors)
            account_key = f"{account}|{currency}"
            require(account_key not in accounts, f"{path}: Doppelter OPOS-Kontenabgleich.", errors)
            accounts.add(account_key)
            opos = parse_money(comparison.get("opos_balance"), f"{path}.opos_balance", errors)
            ledger = parse_money(comparison.get("ledger_balance"), f"{path}.ledger_balance", errors)
            if opos is not None and ledger is not None:
                require(abs(opos - ledger) <= TOLERANCE, f"{path}: OPOS-Kontendifferenz darf nicht durch Gesamtsumme verdeckt werden.", errors)
        if isinstance(expected, list) and all(isinstance(k, str) for k in expected):
            require(len(expected) == len(set(expected)) and set(expected) == accounts, f"{path}: OPOS-Kontenabdeckung unvollständig.", errors)
    require(seen == {(s, b) for s in ("receivable", "payable") for b in ("current", "closing")}, "OPOS-Abgleich benötigt beide Seiten aktuell und zum Abschlussstichtag.", errors)
    checklist = data.get("preparation_checklist", [])
    for side, topic in (("receivable", "opos_debitoren"), ("payable", "opos_kreditoren")):
        if not all(resolved.get((side, basis)) for basis in ("current", "closing")):
            for row in checklist if isinstance(checklist, list) else []:
                if isinstance(row, dict) and row.get("topic_id") == topic:
                    require(row.get("blocks_start") is True and row.get("status") not in RESOLVED_CHECKLIST_STATUSES, f"{topic}: Offener OPOS-Abgleich muss den Start blockieren.", errors)


def validate_review_data(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["Wurzel muss ein JSON-Objekt sein."]

    require(data.get("schema_version") == "0.5.0", "schema_version muss 0.5.0 sein.", errors)
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
    sources_by_id: dict[str, dict[str, Any]] = {}
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
                sources_by_id[source_id] = source
            require(source.get("kind") in {"datev", "dms", "sharepoint", "upload", "calculation"}, f"{path}.kind ist unzulässig.", errors)
            require(isinstance(source.get("uri"), str) and bool(source["uri"]), f"{path}.uri fehlt.", errors)
            if source.get("kind") == "datev" and isinstance(source.get("uri"), str):
                require(
                    source["uri"].startswith("riecken:datev_"),
                    f"{path}.uri: DATEV-Quellen stammen ausschließlich aus dem Riecken-Connector (riecken:datev_<werkzeug>...).",
                    errors,
                )
            require(isinstance(source.get("retrieved_at"), str) and bool(source["retrieved_at"]), f"{path}.retrieved_at fehlt.", errors)
            require(isinstance(source.get("complete"), bool), f"{path}.complete muss boolesch sein.", errors)

    opening = data.get("opening_balance_review")
    require(isinstance(opening, dict), "opening_balance_review fehlt.", errors)
    opening_status = None
    expected_areas: set[str] = set()
    opening_area_statuses: dict[str, str] = {}
    if isinstance(opening, dict):
        opening_status = opening.get("area_inventory_status")
        require(opening_status in AREA_INVENTORY_STATUSES, "opening_balance_review.area_inventory_status ist unzulässig.", errors)
        inventory_refs = opening.get("area_inventory_source_refs")
        require(isinstance(inventory_refs, list) and all(isinstance(ref, str) for ref in inventory_refs), "opening_balance_review.area_inventory_source_refs muss eine Stringliste sein.", errors)
        if isinstance(inventory_refs, list):
            for ref in inventory_refs:
                source = sources_by_id.get(ref)
                require(source is not None, f"opening_balance_review verweist auf unbekannte Bereichsinventarquelle {ref!r}.", errors)
                if source is not None:
                    require(source.get("complete") is True, f"Bereichsinventarquelle {ref!r} ist nicht vollständig.", errors)
        area_ids = opening.get("expected_areas")
        require(isinstance(area_ids, list) and all(isinstance(area, str) and bool(area.strip()) for area in area_ids), "opening_balance_review.expected_areas muss eine Liste nichtleerer Bereichskennungen sein.", errors)
        if isinstance(area_ids, list):
            valid_ids = [area for area in area_ids if isinstance(area, str) and area.strip()]
            require(len(valid_ids) == len(set(valid_ids)), "Doppelte Kennung in opening_balance_review.expected_areas.", errors)
            expected_areas = set(valid_ids)
        opening_areas = opening.get("areas")
        require(isinstance(opening_areas, list), "opening_balance_review.areas muss eine Liste sein.", errors)
        if opening_status == "BEKANNT":
            require(bool(expected_areas), "Bekanntes Bereichsinventar muss mindestens einen Bereich nennen.", errors)
            require(bool(inventory_refs), "Bekanntes Bereichsinventar benötigt eine Quelle.", errors)
            require({"handelsrecht", "steuerrecht"} <= expected_areas, "Handelsrecht und Steuerrecht müssen als getrennte Prüflinien sichtbar sein.", errors)
        else:
            require(not expected_areas and opening_areas == [], "Ohne bekanntes Bereichsinventar dürfen keine geprüften Bereiche behauptet werden.", errors)
        if isinstance(target, dict):
            method = target.get("accounting_method")
            if method == "bilanz":
                require(opening_status != "NICHT_ANWENDBAR", "Bei Bilanzierung ist die Eröffnungsbilanzprüfung nicht pauschal unanwendbar.", errors)
            if method == "euer":
                require(opening_status == "NICHT_ANWENDBAR", "Bei EÜR muss opening_balance_review NICHT_ANWENDBAR sein.", errors)
        if isinstance(opening_areas, list):
            seen_areas: set[str] = set()
            for index, area in enumerate(opening_areas):
                path = f"opening_balance_review.areas[{index}]"
                if not isinstance(area, dict):
                    errors.append(f"{path} muss ein Objekt sein.")
                    continue
                area_id = area.get("area_id")
                require(isinstance(area_id, str) and bool(area_id.strip()), f"{path}.area_id fehlt.", errors)
                if isinstance(area_id, str) and area_id:
                    require(area_id not in seen_areas, f"Doppelter Eröffnungsbilanzbereich: {area_id}", errors)
                    seen_areas.add(area_id)
                    require(area_id in expected_areas, f"{path}.area_id steht nicht im Bereichsinventar.", errors)
                status = area.get("status")
                require(status in OPENING_AREA_STATUSES, f"{path}.status ist unzulässig.", errors)
                if isinstance(area_id, str) and isinstance(status, str):
                    opening_area_statuses[area_id] = status
                for field in ("prior_close_source_ref", "current_opening_source_ref"):
                    ref = area.get(field)
                    require(ref is None or (isinstance(ref, str) and bool(ref)), f"{path}.{field} muss Quellen-ID oder null sein.", errors)
                    if isinstance(ref, str) and ref:
                        source = sources_by_id.get(ref)
                        require(source is not None, f"{path}.{field} verweist auf unbekannte Quelle {ref!r}.", errors)
                        if source is not None:
                            require(source.get("accounting_area_id") == area_id, f"{path}.{field} hat keine passende Bereichskennung.", errors)
                            if status == "ABGESTIMMT":
                                require(source.get("complete") is True, f"{path}.{field} ist nicht vollständig.", errors)
                                proof_kind = source.get("proof_kind")
                                require(proof_kind in {"direct_area", "derived_area"}, f"{path}.{field}: Gemeinsame SuSa/Teilmenge ist kein vollständiger Bereichsnachweis.", errors)
                                if proof_kind == "derived_area":
                                    require(source.get("layers_complete") is True and bool(source.get("base_semantics")), f"{path}.{field}: Vollständige Wertschicht und Basissemantik erforderlich.", errors)
                                    components = checked_refs(source.get("derivation_source_refs"), sources_by_id, f"{path}.{field}.derivation", errors, complete=True)
                                    for component in components:
                                        require(component.get("id") != ref and component.get("proof_kind") != "derived_area", f"{path}.{field}: Herleitung muss auf unabhängige Roh-/Überleitungsquellen zurückführen.", errors)
                                        require(component.get("fiscal_year_id") == source.get("fiscal_year_id"), f"{path}.{field}: Herleitungsquelle gehört nicht zum passenden Wirtschaftsjahr.", errors)
                            expected_year_id = prior.get("id") if field == "prior_close_source_ref" and isinstance(prior, dict) else target.get("id") if isinstance(target, dict) else None
                            require(source.get("fiscal_year_id") == expected_year_id, f"{path}.{field} gehört nicht zum passenden Wirtschaftsjahr.", errors)
                require(isinstance(area.get("prior_close_final"), bool), f"{path}.prior_close_final muss boolesch sein.", errors)
                require(isinstance(area.get("comparison_complete"), bool), f"{path}.comparison_complete muss boolesch sein.", errors)
                count = area.get("compared_account_count")
                require(isinstance(count, int) and not isinstance(count, bool) and count >= 0, f"{path}.compared_account_count muss eine nichtnegative Ganzzahl sein.", errors)
                comparison_differences = validate_opening_comparisons(area, sources_by_id, path, errors)
                for field in ("differences", "unmapped_accounts"):
                    require(isinstance(area.get(field), list), f"{path}.{field} muss eine Liste sein.", errors)
                require(isinstance(area.get("next_action"), str) and bool(area.get("next_action").strip()), f"{path}.next_action fehlt.", errors)
                require(area.get("evidence_extent") in {"vollstaendig", "teilweise", "nicht_pruefbar", "nicht_anwendbar"}, f"{path}.evidence_extent fehlt.", errors)
                if status == "TEILNACHWEIS":
                    require(area.get("evidence_extent") == "teilweise" and area.get("comparison_complete") is False, f"{path}: TEILNACHWEIS darf keinen vollständigen Abgleich behaupten.", errors)
                    checked_refs(area.get("partial_source_refs"), sources_by_id, f"{path}.partial_source_refs", errors)
                if status == "NICHT_ANWENDBAR":
                    require(area.get("evidence_extent") == "nicht_anwendbar", f"{path}: Nichtanwendbarkeit falsch eingeordnet.", errors)
                    checked_refs(area.get("non_applicability_source_refs"), sources_by_id, f"{path}.non_applicability", errors, complete=True)
                if status == "ABGESTIMMT":
                    require(area.get("evidence_extent") == "vollstaendig", f"{path}: ABGESTIMMT benötigt vollständigen Bereichsnachweis.", errors)
                    require(prior is not None, f"{path}: Ohne Vorjahr kein automatischer Schlussbilanzabgleich.", errors)
                    require(bool(area.get("prior_close_source_ref")) and bool(area.get("current_opening_source_ref")), f"{path}: ABGESTIMMT benötigt beide Bereichsquellen.", errors)
                    require(area.get("prior_close_final") is True, f"{path}: ABGESTIMMT benötigt endgültigen Vorjahresstand.", errors)
                    require(area.get("comparison_complete") is True and isinstance(count, int) and count > 0, f"{path}: ABGESTIMMT benötigt vollständigen Kontenvergleich.", errors)
                    require(area.get("differences") == [] and area.get("unmapped_accounts") == [], f"{path}: ABGESTIMMT ist mit offenen Differenzen oder Konten unmöglich.", errors)
                    require(not comparison_differences, f"{path}: ABGESTIMMT ist mit abweichenden Kontenbeträgen unmöglich.", errors)
            require(seen_areas == expected_areas, f"Eröffnungsbilanzbereiche fehlen oder sind zusätzlich: erwartet {sorted(expected_areas)}, vorhanden {sorted(seen_areas)}.", errors)

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
    opening_checklist_rows = [row for row in checklist if isinstance(row, dict) and row.get("topic_id") == "eroeffnungsbilanz"] if isinstance(checklist, list) else []
    require(len(opening_checklist_rows) == 1, "Genau ein Checklisteneintrag für eroeffnungsbilanz ist erforderlich.", errors)
    if len(opening_checklist_rows) == 1 and isinstance(target, dict):
        opening_row = opening_checklist_rows[0]
        if target.get("accounting_method") == "bilanz":
            require(opening_row.get("status") != "NICHT_ANWENDBAR", "Eröffnungsbilanz ist bei Bilanzierung nicht pauschal NICHT_ANWENDBAR.", errors)
            if opening_status != "BEKANNT" or any(status not in OPENING_RESOLVED for status in opening_area_statuses.values()) or set(opening_area_statuses) != expected_areas:
                require(opening_row.get("blocks_start") is True, "Fehlende Eröffnungsbilanz-Bereichsabdeckung muss den Start blockieren.", errors)
                require(opening_row.get("status") != "ABGESTIMMT", "Eröffnungsbilanz darf bei fehlender Bereichsabdeckung nicht ABGESTIMMT sein.", errors)
        elif target.get("accounting_method") == "euer":
            require(opening_row.get("status") == "NICHT_ANWENDBAR", "EÜR-Eröffnungsbilanz muss NICHT_ANWENDBAR sein.", errors)

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
            require(row.get("confidence") in {"sicher", "hoch"}, f"{path}.confidence ist für einen Buchungsvorschlag nicht ausreichend.", errors)
            if row.get("rule_id") == "K-1590-LT100":
                if amount is not None:
                    require(abs(amount) < Decimal("100.00"), f"{path}: K-1590-LT100 verlangt abs(Betrag) < 100.00.", errors)
                require(row.get("tax_key") == "", f"{path}: Kleinbetragsregel verlangt leeren tax_key.", errors)
                require(row.get("functional_source_account") in {"1590", "1370"} or bool(row.get("functional_source_account")), f"{path}: Quellkonto der Kleinbetragsregel ist nicht bestätigt.", errors)
                require(row.get("functional_target_account") in {"4980", "6850"} or bool(row.get("functional_target_account")), f"{path}: Zielkonto der Kleinbetragsregel ist nicht bestätigt.", errors)
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
        require(isinstance(target, dict) and target.get("accounting_method") in {"bilanz", "euer"}, "STARTKLAR verlangt eine bestätigte Gewinnermittlungsart.", errors)
        open_blockers = [
            row.get("id", f"Zeile {index}")
            for index, row in enumerate(checklist)
            if isinstance(row, dict)
            and row.get("blocks_start") is True
            and row.get("status") not in RESOLVED_CHECKLIST_STATUSES
        ]
        require(not open_blockers, f"STARTKLAR ist mit offenen Startblockern unzulässig: {', '.join(open_blockers)}", errors)
        if isinstance(target, dict) and target.get("accounting_method") == "bilanz":
            require(opening_status == "BEKANNT" and bool(expected_areas) and set(opening_area_statuses) == expected_areas and all(status in OPENING_RESOLVED for status in opening_area_statuses.values()), "STARTKLAR verlangt die abgestimmte Eröffnungsbilanz aller vorhandenen Bereiche.", errors)
            require(len(opening_checklist_rows) == 1 and opening_checklist_rows[0].get("status") == "ABGESTIMMT", "STARTKLAR verlangt einen abgestimmten Eröffnungsbilanz-Checklisteneintrag.", errors)

    validate_opos_reconciliation(data, sources_by_id, errors)
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
    print("Vorbereitungsdaten gültig: preparation_only | schema_version 0.5.0")


if __name__ == "__main__":
    main()
