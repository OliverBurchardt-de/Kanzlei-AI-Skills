from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import posixpath
import re
import sys
import uuid
import zipfile
import xml.etree.ElementTree as ET
from lxml import etree
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath

from datev_io import (
    BATCH_KIND_BOOKING,
    BATCH_KIND_CLARIFICATION,
    BOOKING_FIELDS,
    CARRY_FIELDS,
    CARRY_RESULTS,
    DATEV_IMPORT_ORDER,
    DOCUMENT_FILE_RULE,
    MASTER_FIELDS,
    OPEN_FIELD_INDEXES,
    RED_REASON_CODES,
    REQUIRED_CONNECTOR,
    REQUIRED_RETRIEVAL_STEPS,
    STANDARD_BATCH_TYPE,
    STATUS_BOOKED,
    STATUS_UNREADABLE,
    TRANSFER_RULE,
    batch_label,
    batch_type_suffix,
    carry_order_violations,
    carry_sort_key,
    clean_text,
    fiscal_year_start,
    month_bounds,
    parse_batch_file_name,
)
from sharepoint_target import build_targets
from clarification_rate import THRESHOLD_NORMAL, THRESHOLD_SECOND_REVIEW, quota, stage_for


DOCUMENT_NAMESPACE = "http://xml.datev.de/bedi/tps/document/v06.0"
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
DOCUMENT_SCHEMA_LOCATION = (
    f"{DOCUMENT_NAMESPACE} Document_v060.xsd"
)
MAX_DOCUMENT_BYTES = 20 * 1024 * 1024
MAX_PACKAGE_BYTES = 465 * 1024 * 1024
MAX_DOCUMENTS_PER_PACKAGE = 4999
BELEGLINK_PATTERN = re.compile(
    r'^BEDI "([0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-'
    r'[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12})"$'
)
XLSX_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
XLSX_DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
XLSX_PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
EXPECTED_REVIEW_HEADERS = {
    "Belegprüfung": [
        "Ampel-Einstufung", "Buchungsstapel", "Vorgangs-ID", "Belegdatum laut Beleg",
        "Geschäftspartner", "Belegfeld 1", "Betrag", "Währung",
        "Buchungsperiode", "Kontierung", "Ableitung",
        "Prüfergebnis / Ampelbegründung",
        "Offener Punkt / nächster Schritt", "Bearbeitungsstatus",
        "Mitarbeiter-Ergebnis",
    ],
    "Buchungszeilen": [
        "Ampel-Einstufung", "Buchungsstapel", "Vorgangs-ID", "Betrag", "Soll/Haben", "Konto",
        "Kontobezeichnung", "Gegenkonto", "Gegenkontobezeichnung",
        "BU-Schlüssel", "Erkanntes Belegdatum", "Belegfeld 1",
        "Buchungstext", "Buchungsperiode",
    ],
    "Mandanten-Hinweise": [
        "Vorgangs-ID", "Geschäftspartner", "Hinweis",
        "Empfohlenes Vorgehen",
    ],
    "Stammdatenänderungen": [
        "Aktion", "Konto", "Typ", "Name", "USt-ID",
        "Bankverbindungen", "Vollständiger Datensatz", "Hinweis",
    ],
}
REQUIRED_REVIEW_SHEETS = {
    "Anleitung", "Übersicht", "Belegprüfung", "Buchungszeilen",
    "Mandanten-Hinweise", "Stammdatenänderungen", "Klärungsquote",
}
FORBIDDEN_VISIBLE_REVIEW_HEADERS = {
    "Belegdatei", "Quelldatei", "Originaldateiname", "Importfähig",
}
FORBIDDEN_DATEV_FOLDERS = {
    "01_Buchungsstapel", "02_Stammdaten", "03_Belegtransfer",
    "06_Abgrenzungsstapel", "01_Buchungsstapel_Gruen",
    "02_Buchungsstapel_Gelb", "03_Buchungsstapel_Rot", "04_Stammdaten",
}


EXPECTED_SKILL_VERSION = "1.4.1"
EXPECTED_OUTPUT_CONTRACT = "monthly-booking-and-clarification-batches-v4"


def manifest_cost_center_config(manifest: dict | None) -> dict | None:
    config = (manifest or {}).get("run_contract", {}).get("cost_center_config")
    return config if isinstance(config, dict) else None


def manifest_separate_batches(manifest: dict | None) -> dict:
    batch_config = (manifest or {}).get("run_contract", {}).get("batch_config")
    if not isinstance(batch_config, dict):
        return {}
    separate = batch_config.get("separate_batches")
    return separate if isinstance(separate, dict) else {}


def expected_review_headers(manifest: dict | None) -> dict[str, list[str]]:
    """Review columns; KOST columns exist only for clients with a cost center profile."""
    headers = {name: list(values) for name, values in EXPECTED_REVIEW_HEADERS.items()}
    config = manifest_cost_center_config(manifest)
    if config:
        review = headers["Belegprüfung"]
        review.insert(review.index("Kontierung") + 1, "KOST1")
        bookings = headers["Buchungszeilen"]
        position = bookings.index("BU-Schlüssel") + 1
        bookings.insert(position, "KOST1")
        if config.get("kost2_required") is True or config.get("kost2_allowed"):
            bookings.insert(position + 1, "KOST2")
    return headers


def normalized_person_account_name(value: object) -> str:
    return re.sub(r"[^A-Z0-9]+", " ", str(value).upper()).strip()


def is_collective_person_account_name(value: object) -> bool:
    normalized = normalized_person_account_name(value)
    if not normalized:
        return False
    tokens = normalized.split()
    if tokens[0] in {"DIVERSE", "DIVERS", "DIV", "CPD"}:
        return True
    compact = "".join(tokens)
    return any(
        marker in compact
        for marker in ("SAMMELDEBITOR", "SAMMELKREDITOR", "SAMMELKONTO")
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Erzeugtes Buchhaltungspaket prüfen")
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--datev-test-import", type=Path, help="Tatsächlichen DATEV-Testimportnachweis für exakt diese EXTF-Dateien prüfen")
    return parser.parse_args()


def split_extf(line: str) -> list[str]:
    fields: list[str] = []
    current: list[str] = []
    quoted = False
    index = 0
    while index < len(line):
        char = line[index]
        if char == '"':
            if quoted and index + 1 < len(line) and line[index + 1] == '"':
                current.append('"')
                index += 2
                continue
            quoted = not quoted
        elif char == ";" and not quoted:
            fields.append("".join(current))
            current = []
        else:
            current.append(char)
        index += 1
    fields.append("".join(current))
    return fields


def excel_column_index(reference: str) -> int:
    match = re.match(r"([A-Z]+)", reference.upper())
    if not match:
        return 0
    result = 0
    for char in match.group(1):
        result = result * 26 + ord(char) - ord("A") + 1
    return result - 1


def xlsx_cell_text(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.get("t", "")
    if cell_type == "inlineStr":
        return "".join(
            node.text or ""
            for node in cell.findall(f".//{{{XLSX_MAIN_NS}}}t")
        )
    value = cell.findtext(f"{{{XLSX_MAIN_NS}}}v", default="")
    if cell_type == "s" and value:
        try:
            return shared_strings[int(value)]
        except (IndexError, ValueError):
            return ""
    return value


def validate_review_workbook(path: Path, manifest: dict | None = None) -> list[str]:
    errors: list[str] = []
    headers_by_sheet = expected_review_headers(manifest)
    try:
        with zipfile.ZipFile(path) as archive:
            shared_strings: list[str] = []
            try:
                shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            except KeyError:
                pass
            else:
                for item in shared_root.findall(f"{{{XLSX_MAIN_NS}}}si"):
                    shared_strings.append("".join(
                        node.text or ""
                        for node in item.findall(f".//{{{XLSX_MAIN_NS}}}t")
                    ))

            styles_root = ET.fromstring(archive.read("xl/styles.xml"))
            fills = styles_root.find(f"{{{XLSX_MAIN_NS}}}fills")
            cell_xfs = styles_root.find(f"{{{XLSX_MAIN_NS}}}cellXfs")
            style_fill_colors: dict[int, str] = {}
            if fills is not None and cell_xfs is not None:
                fill_items = list(fills)
                for style_id, xf in enumerate(cell_xfs):
                    fill_id = int(xf.get("fillId", "0"))
                    if fill_id >= len(fill_items):
                        continue
                    fg = fill_items[fill_id].find(
                        f".//{{{XLSX_MAIN_NS}}}fgColor"
                    )
                    if fg is not None and fg.get("rgb"):
                        style_fill_colors[style_id] = str(fg.get("rgb"))[-6:].upper()

            workbook_root = ET.fromstring(archive.read("xl/workbook.xml"))
            rels_root = ET.fromstring(
                archive.read("xl/_rels/workbook.xml.rels")
            )
            rel_targets = {
                rel.get("Id", ""): rel.get("Target", "")
                for rel in rels_root.findall(f"{{{XLSX_PKG_REL_NS}}}Relationship")
            }
            sheet_targets: dict[str, str] = {}
            for sheet in workbook_root.findall(
                f".//{{{XLSX_MAIN_NS}}}sheet"
            ):
                rel_id = sheet.get(f"{{{XLSX_DOC_REL_NS}}}id", "")
                target = rel_targets.get(rel_id, "").lstrip("/")
                if target and not target.startswith("xl/"):
                    target = posixpath.normpath(posixpath.join("xl", target))
                sheet_targets[sheet.get("name", "")] = target

            actual_sheets = set(sheet_targets)
            if actual_sheets != REQUIRED_REVIEW_SHEETS:
                missing = sorted(REQUIRED_REVIEW_SHEETS - actual_sheets)
                unexpected = sorted(actual_sheets - REQUIRED_REVIEW_SHEETS)
                details = []
                if missing:
                    details.append("fehlen: " + ", ".join(missing))
                if unexpected:
                    details.append("unerwartet: " + ", ".join(unexpected))
                errors.append(f"{path.name}: Tabellenblätter weichen ab ({'; '.join(details)}).")

            for sheet_name, expected in headers_by_sheet.items():
                target = sheet_targets.get(sheet_name)
                if not target:
                    errors.append(
                        f"{path.name}: Tabellenblatt {sheet_name} fehlt."
                    )
                    continue
                sheet_root = ET.fromstring(archive.read(target))
                first_row = sheet_root.find(
                    f".//{{{XLSX_MAIN_NS}}}row[@r='1']"
                )
                if first_row is None:
                    errors.append(
                        f"{path.name}: Kopfzeile in {sheet_name} fehlt."
                    )
                    continue
                values_by_column = {
                    excel_column_index(cell.get("r", "")): xlsx_cell_text(
                        cell, shared_strings
                    )
                    for cell in first_row.findall(f"{{{XLSX_MAIN_NS}}}c")
                }
                max_column = max(values_by_column, default=-1)
                actual = [
                    values_by_column.get(index, "")
                    for index in range(max_column + 1)
                ]
                if actual != expected:
                    errors.append(
                        f"{path.name}: Kopfzeilen in {sheet_name} weichen ab; "
                        f"erwartet sind Ampel-Einstufung an erster und "
                        "Buchungsstapel an zweiter Stelle ohne sichtbaren "
                        "Quelldateinamen oder Importfähig-Spalte."
                    )
                if sheet_name in {"Belegprüfung", "Buchungszeilen"}:
                    expected_colors = {
                        "Grün": "C6E0B4",
                        "Rot": "F4CCCC",
                    }
                    for row in sheet_root.findall(f".//{{{XLSX_MAIN_NS}}}row"):
                        if int(row.get("r", "0")) < 2:
                            continue
                        cell = next(
                            (
                                item for item in row.findall(f"{{{XLSX_MAIN_NS}}}c")
                                if excel_column_index(item.get("r", "")) == 0
                            ),
                            None,
                        )
                        if cell is None:
                            continue
                        value = xlsx_cell_text(cell, shared_strings)
                        if value == "Gelb":
                            errors.append(f"{path.name}: Gelb ist seit Version 1.3 nicht zulässig.")
                        expected_color = expected_colors.get(value)
                        if not expected_color:
                            continue
                        style_id = int(cell.get("s", "0"))
                        if style_fill_colors.get(style_id) != expected_color:
                            errors.append(
                                f"{path.name}: {sheet_name}!{cell.get('r', '')} hat für {value} keine feste korrekte Hintergrundfarbe."
                            )

                forbidden = sorted(
                    FORBIDDEN_VISIBLE_REVIEW_HEADERS.intersection(actual)
                )
                if forbidden:
                    errors.append(
                        f"{path.name}: unzulässige sichtbare Spalten in "
                        f"{sheet_name}: {', '.join(forbidden)}"
                    )
    except (OSError, KeyError, ET.ParseError, zipfile.BadZipFile) as exc:
        errors.append(f"{path.name}: Excel-Struktur nicht prüfbar ({exc})")
    return errors


def validate_datev_import_layout(package_root: Path, manifest: dict | None = None) -> list[str]:
    errors: list[str] = []
    allowed_suffixes = {batch_type_suffix(key) for key in manifest_separate_batches(manifest)}
    datev_dir = package_root / "01_DATEV_Import"
    if not datev_dir.is_dir():
        return ["Gemeinsamer DATEV-Importordner 01_DATEV_Import fehlt."]
    legacy_folders = sorted(
        name for name in FORBIDDEN_DATEV_FOLDERS
        if (package_root / name).exists()
    )
    if legacy_folders:
        errors.append(
            "Getrennte DATEV- oder Ampelordner sind unzulässig; alle "
            "DATEV-Importdateien gehören nach 01_DATEV_Import: "
            + ", ".join(legacy_folders)
        )
    subdirectories = sorted(
        str(path.relative_to(datev_dir))
        for path in datev_dir.rglob("*")
        if path.is_dir()
    )
    if subdirectories:
        errors.append(
            "01_DATEV_Import darf keine Unterordner enthalten: "
            + ", ".join(subdirectories)
        )
    misplaced = []
    for path in package_root.rglob("*"):
        if not path.is_file():
            continue
        is_datev_file = (
            (path.name.startswith("EXTF_") and path.suffix.lower() == ".csv")
            or (
                path.name.startswith("Belegtransfer_")
                and path.suffix.lower() == ".zip"
            )
        )
        if is_datev_file and path.parent != datev_dir:
            misplaced.append(str(path.relative_to(package_root)))
    if misplaced:
        errors.append(
            "DATEV-Importdateien liegen außerhalb von 01_DATEV_Import: "
            + ", ".join(sorted(misplaced))
        )
    for path in datev_dir.glob("EXTF_*.csv"):
        if path.name == "EXTF_Debitoren_Kreditoren.csv":
            continue
        parsed = parse_batch_file_name(path.name)
        if parsed is None:
            errors.append(
                f"{path.name}: Je Monat nur ein Buchungsstapel und ein Klärungsstapel "
                "(mit Teilungsdateien) zulässig."
            )
            continue
        if parsed["kind"] == BATCH_KIND_BOOKING and parsed["part"] > 1:
            errors.append(f"{path.name}: Je Monat nur ein Buchungsstapel je Stapeltyp; nur der Klärungsstapel darf geteilt werden.")
        if parsed["suffix"] and parsed["suffix"] not in allowed_suffixes:
            errors.append(f"{path.name}: Stapelsuffix {parsed['suffix']} stammt nicht aus batch_config.")
    return errors


def _row_values(path: Path) -> list[list[str]]:
    return [split_extf(line) for line in path.read_text(encoding="cp1252").splitlines()[2:]]


def validate_batch_files(package_root: Path, manifest: dict | None = None) -> list[str]:
    """Per period and batch type: one booking batch, gapless clarification parts, justified splits."""
    errors: list[str] = []
    datev_dir = package_root / "01_DATEV_Import"
    if not datev_dir.is_dir():
        return errors
    grouped: dict[tuple[str, str, str], dict[int, Path]] = {}
    for path in sorted(datev_dir.glob("EXTF_*.csv")):
        parsed = parse_batch_file_name(path.name)
        if parsed is None:
            continue
        key = (parsed["period"], parsed["batch_type"], parsed["kind"])
        grouped.setdefault(key, {})
        if parsed["part"] in grouped[key]:
            errors.append(f"{path.name}: Teilungsnummer ist doppelt.")
        grouped[key][parsed["part"]] = path
        try:
            if not _row_values(path):
                errors.append(f"{path.name}: leere EXTF-Datei ist unzulässig; eine Datei ohne Zeilen wird nicht erzeugt.")
        except (OSError, UnicodeDecodeError):
            pass
    for (period, batch_type, kind), parts in sorted(grouped.items()):
        numbers = sorted(parts)
        if numbers != list(range(1, len(numbers) + 1)):
            errors.append(
                f"{kind}/{period}/{batch_type}: Teilungsdateien müssen lückenlos ab _02 folgen; vorhanden: "
                + ", ".join(str(number) for number in numbers)
            )
        if kind == BATCH_KIND_CLARIFICATION and len(numbers) > 1:
            try:
                all_rows = [row for number in numbers for row in _row_values(parts[number])]
            except (OSError, UnicodeDecodeError):
                continue
            all_rows.sort(key=lambda row: carry_sort_key(row))
            if not carry_order_violations(all_rows):
                errors.append(
                    f"{kind}/{period}/{batch_type}: Teilung in {len(numbers)} Dateien ist unzulässig; "
                    "die Sortierregel wäre ohne Teilung erfüllbar."
                )
    if manifest and "booking_trace" in manifest:
        trace_files = {str(item.get("file")) for item in manifest.get("booking_trace", [])}
        actual_files = {path.name for parts in grouped.values() for path in parts.values()}
        for name in sorted(actual_files - trace_files):
            errors.append(f"{name}: EXTF-Datei ohne Exportnachweis im Laufmanifest.")
        for name in sorted(trace_files - actual_files):
            errors.append(f"{name}: Exportnachweis ohne EXTF-Datei.")
    return errors


def _valid_date(value: str, date_format: str) -> bool:
    try:
        datetime.strptime(value, date_format)
    except ValueError:
        return False
    return True



def _validate_preflight_manifest(manifest: dict) -> list[str]:
    errors: list[str] = []
    evidence = manifest.get("preflight_evidence")
    contract = manifest.get("run_contract")
    if not isinstance(evidence, dict):
        return ["Technischer Preflight-Nachweis fehlt im Laufmanifest."]
    if not isinstance(contract, dict):
        return ["DATEV-Laufvertrag fehlt im Laufmanifest."]
    client_number = str(manifest.get("mandant", "")).zfill(5)
    try:
        targets = build_targets(client_number)
    except ValueError as exc:
        return [f"Mandant im Laufmanifest ist ungültig: {exc}"]

    def check_sharepoint(item: object, expected_url: str, expected_name: str, label: str) -> None:
        if not isinstance(item, dict):
            errors.append(f"{label}-Abrufnachweis fehlt im Laufmanifest.")
            return
        if item.get("source_url") != expected_url:
            errors.append(f"{label} stammt nicht von der exakten SharePoint-URL.")
        if item.get("file_name") != expected_name:
            errors.append(f"{label}-Dateiname stimmt nicht.")
        if not item.get("file_uri") or not item.get("retrieved_via"):
            errors.append(f"{label}-Abrufweg oder Datei-ID fehlt.")
        if not re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256", ""))):
            errors.append(f"{label}-SHA-256 fehlt oder ist ungültig.")
        if not item.get("raw_evidence"):
            errors.append(f"{label}-Inhaltsnachweis fehlt.")

    profile_evidence = evidence.get("mandantenprofil")
    profile_contract = contract.get("mandantenprofil", {})
    if (
        isinstance(profile_contract, dict)
        and profile_contract.get("status") == "provisional_first_run"
    ):
        if not isinstance(profile_evidence, dict) or profile_evidence.get("status") != "not_found":
            errors.append("Vorläufiges Mandantenprofil besitzt keinen bestätigten Nichtvorhanden-Nachweis.")
        else:
            if profile_evidence.get("source_url") != str(targets["profile_url"]):
                errors.append("Mandantenprofil-Nichtvorhanden-Nachweis verwendet nicht die exakte URL.")
            if profile_evidence.get("file_name") != f"{client_number}.md":
                errors.append("Mandantenprofil-Dateiname stimmt nicht.")
            if profile_evidence.get("not_found_code") != "itemNotFound":
                errors.append("Mandantenprofil wurde nicht eindeutig als itemNotFound bestätigt.")
            if profile_evidence.get("site_verified") is not True or profile_evidence.get("library_verified") is not True:
                errors.append("Site/Bibliothek für das Mandantenprofil wurden nicht bestätigt.")
            if not isinstance(profile_evidence.get("direct_lookup_attempts"), int) or profile_evidence["direct_lookup_attempts"] < 2:
                errors.append("Mandantenprofil wurde nicht zweimal direkt geprüft.")
    else:
        check_sharepoint(
            profile_evidence,
            str(targets["profile_url"]),
            f"{client_number}.md",
            "Mandantenprofil",
        )
    scope = contract.get("scope")
    if not isinstance(scope, dict) or scope.get("job_mode") != "belegbuchhaltung":
        errors.append("Scope fehlt oder enthält einen unzulässigen Teilauftrag; Kassenbuchung ist ausgeschlossen.")
    elif not isinstance(scope.get("target_periods"), list) or not scope["target_periods"]:
        errors.append("Zielperioden fehlen im Laufvertrag.")
    def check_accrual_register(item: object) -> None:
        if isinstance(item, dict) and item.get("status") == "access_error":
            # Abrufproblem (z. B. HTTP 403): gesondert vermerkt, kein Nullstand, Lauf nicht vollständig abgeschlossen.
            if item.get("source_url") != str(targets["accrual_url"]) or item.get("file_name") != f"{client_number}.md":
                errors.append("Abgrenzungsregister-Abrufproblem verwendet nicht das exakte SharePoint-Ziel.")
            if not item.get("retrieved_via") or not item.get("checked_at"):
                errors.append("Abgrenzungsregister-Abrufproblem ist unvollständig dokumentiert.")
            if item.get("http_status") in (None, "") and not str(item.get("error_code", "")).strip():
                errors.append("Abgrenzungsregister-Abrufproblem ohne HTTP-Status oder Fehlercode.")
            if str(item.get("http_status")) == "404" or str(item.get("error_code", "")).lower() in {"itemnotfound", "not_found"}:
                errors.append("Abgrenzungsregister: itemNotFound ist kein Abrufproblem, sondern ein bestätigter Erstlauf.")
            if not isinstance(item.get("direct_lookup_attempts"), int) or item["direct_lookup_attempts"] < 2:
                errors.append("Abgrenzungsregister-Abrufproblem wurde nicht nach zulässiger Wiederholung dokumentiert.")
            if "kein Nullstand" not in str(item.get("register_state", "")):
                errors.append("Abgrenzungsregister-Abrufproblem darf keinen Nullstand annehmen.")
            completion = manifest.get("run_completion") or {}
            if completion.get("status") != "nicht vollständig abgeschlossen":
                errors.append("Abgrenzungsregister nicht abrufbar: Lauf muss als nicht vollständig abgeschlossen ausgewiesen sein.")
            return
        if isinstance(item, dict) and item.get("status") in {"not_found", "empty"}:
            # Leer oder nicht vorhanden ist ein normaler Zustand; nur der Abruf muss dokumentiert sein.
            if item.get("source_url") != str(targets["accrual_url"]):
                errors.append("Abgrenzungsregister-Abruf verwendet nicht die exakte URL.")
            if item.get("file_name") != f"{client_number}.md":
                errors.append("Abgrenzungsregister-Dateiname stimmt nicht.")
            if not item.get("retrieved_via") or not item.get("checked_at"):
                errors.append("Abgrenzungsregister-Abruf ist unvollständig dokumentiert.")
            return
        check_sharepoint(
            item,
            str(targets["accrual_url"]),
            f"{client_number}.md",
            "Abgrenzungsregister",
        )
    if contract.get("accounting_method") == "Bilanz":
        check_accrual_register(evidence.get("abgrenzungsregister"))
    elif contract.get("accounting_method") == "EÜR":
        if manifest.get("accrual_releases") or any(
            item.get("kind") == "accrual" for item in manifest.get("booking_trace", []) or []
        ):
            errors.append("EÜR: Abgrenzungsauflösungen sind unzulässig; kein Abgrenzungsregister bei Einnahmenüberschussrechnung.")
    if contract.get("accounting_method") not in {"Bilanz", "EÜR"}:
        errors.append("Rechnungslegungsart im Laufmanifest ist ungültig.")
    required = contract.get("kostenstellenpflicht")
    if not isinstance(required, bool):
        errors.append("kostenstellenpflicht muss im Laufvertrag true oder false sein.")
    cost_config = contract.get("cost_center_config")
    if required is True and not isinstance(cost_config, dict):
        errors.append("Unkonfigurierte Pflichtkostenstelle: kostenstellenpflicht=true ohne cost_center_config.")
    if cost_config is not None:
        if not isinstance(cost_config, dict):
            errors.append("cost_center_config im Laufvertrag ist kein Objekt.")
        else:
            for key in ("kost_system", "kost1_required", "kost2_required", "kost1_allowed", "kost2_allowed", "rules_source"):
                if key not in cost_config:
                    errors.append(f"cost_center_config.{key} fehlt im Laufvertrag.")
            if not isinstance(cost_config.get("kost1_allowed"), dict) or not cost_config.get("kost1_allowed"):
                errors.append("cost_center_config.kost1_allowed fehlt oder ist leer.")
            if required is True and cost_config.get("kost1_required") is not True:
                errors.append("kostenstellenpflicht=true erfordert cost_center_config.kost1_required=true.")
    batch_config = contract.get("batch_config")
    if batch_config is not None:
        separate = batch_config.get("separate_batches") if isinstance(batch_config, dict) else None
        if not isinstance(separate, dict):
            errors.append("batch_config.separate_batches im Laufvertrag ist ungültig.")
        else:
            for key, item in separate.items():
                if not re.fullmatch(r"[a-z][a-z0-9]*", str(key)) or str(key) == STANDARD_BATCH_TYPE:
                    errors.append(f"batch_config: ungültiger Stapeltyp {key!r}.")
                if not isinstance(item, dict) or not clean_text(item.get("label", "")):
                    errors.append(f"batch_config.{key}: label fehlt.")
    for key in ("vat_config", "account_config", "person_account_ranges"):
        if not isinstance(contract.get(key), dict):
            errors.append(f"{key} fehlt im Laufvertrag.")
    account_config = contract.get("account_config", {})
    asset_accounts = (
        account_config.get("asset_accounts")
        if isinstance(account_config, dict)
        else None
    )
    if not isinstance(asset_accounts, list) or not asset_accounts:
        errors.append("asset_accounts fehlt im DATEV-Laufvertrag.")
    elif str(account_config.get("gwg", "")) not in {
        str(value) for value in asset_accounts
    }:
        errors.append("GWG-Konto fehlt in asset_accounts des DATEV-Laufvertrags.")

    datev = evidence.get("datev")
    if not isinstance(datev, dict) or datev.get("source") != "DATEV live":
        errors.append("DATEV-Livenachweis fehlt im Laufmanifest.")
    elif not datev.get("retrieved_at"):
        errors.append("DATEV-Livenachweis enthält keinen Abrufzeitpunkt.")
    else:
        if str(datev.get("connector", "")).strip() != REQUIRED_CONNECTOR:
            errors.append(f"DATEV-Livenachweis stammt nicht vom {REQUIRED_CONNECTOR}-Connector.")
        retrieved_via = datev.get("retrieved_via")
        if not isinstance(retrieved_via, dict) or any(
            not str(retrieved_via.get(step, "")).startswith("datev_") for step in REQUIRED_RETRIEVAL_STEPS
        ):
            errors.append("DATEV-Livenachweis nennt nicht für jede Prüfung ein Riecken-Werkzeug (retrieved_via).")
        if not isinstance(datev.get("validated_accounts"), list) or not datev["validated_accounts"]:
            errors.append("DATEV-Livenachweis enthält keine validierten Konten.")
        if not isinstance(datev.get("validated_bu_keys"), list):
            errors.append("DATEV-Livenachweis enthält keine Liste validierter BU-Schlüssel.")
        used_person_accounts = datev.get("used_person_accounts")
        if not isinstance(used_person_accounts, list):
            errors.append(
                "DATEV-Livenachweis enthält keine Liste der verwendeten "
                "Personenkonten."
            )
        else:
            for item in used_person_accounts:
                if not isinstance(item, dict):
                    errors.append("Ungültiger Personenkontonachweis im Laufmanifest.")
                    continue
                account = str(item.get("account", ""))
                name = str(item.get("name", "")).strip()
                if not account.isdigit() or not name:
                    errors.append("Unvollständiger Personenkontonachweis im Laufmanifest.")
                elif is_collective_person_account_name(name):
                    errors.append(
                        f"Personenkonto {account} ({name}) ist ein "
                        "unzulässiges Sammel-/CPD-Konto."
                    )
        for key in ("highest_creditor_account", "highest_debtor_account"):
            if not str(datev.get(key, "")).isdigit():
                errors.append(f"DATEV-Livenachweis enthält kein gültiges {key}.")
        if isinstance(cost_config, dict):
            if datev.get("cost_system_active") is not True:
                errors.append("DATEV-Livenachweis bestätigt kein aktives Kostenrechnungssystem.")
            if not isinstance(datev.get("validated_cost_centers"), list):
                errors.append("DATEV-Livenachweis enthält keine Liste validierter Kostenstellen.")
        expected_core = {
            "beraternummer": manifest.get("beraternummer"),
            "mandantennummer": manifest.get("mandant"),
            "wirtschaftsjahr_beginn": contract.get("wirtschaftsjahr_beginn"),
            "sachkontenlaenge": contract.get("sachkontenlaenge"),
            "sachkontenrahmen": contract.get("sachkontenrahmen"),
        }
        for key, expected in expected_core.items():
            if str(datev.get(key, "")) != str(expected):
                errors.append(f"DATEV-Livenachweis für {key} stimmt nicht mit dem Laufvertrag überein.")
        for flag, count_key in (
            ("master_data_checked", "master_data_records_found"),
            ("prior_bookings_checked", "prior_booking_records_found"),
        ):
            if datev.get(flag) is not True:
                errors.append(f"DATEV-Livenachweis enthält kein {flag}=true.")
            count = datev.get(count_key)
            if not isinstance(count, int) or count < 0:
                errors.append(f"DATEV-Livenachweis enthält kein gültiges {count_key}.")
    return errors


def validate_csv(
    path: Path, manifest: dict | None = None
) -> tuple[list[str], set[str]]:
    errors: list[str] = []
    beleglinks: set[str] = set()
    try:
        raw = path.read_bytes()
        text = raw.decode("cp1252")
    except Exception as exc:
        return [f"{path.name}: nicht als CP1252 lesbar ({exc})"], beleglinks
    if b"\r\n" not in raw:
        errors.append(f"{path.name}: CRLF fehlt")
    lines = text.splitlines()
    if len(lines) < 3:
        return errors + [f"{path.name}: weniger als drei Zeilen"], beleglinks
    header = split_extf(lines[0])
    if len(header) != 31:
        errors.append(f"{path.name}: Header hat {len(header)} statt 31 Felder")
    category = header[2] if len(header) > 4 else ""
    version = header[4] if len(header) > 4 else ""
    expected = (
        BOOKING_FIELDS if category == "21"
        else MASTER_FIELDS if category == "16"
        else []
    )
    expected_version = "13" if category == "21" else "5" if category == "16" else ""
    if len(header) == 31:
        if header[0] != "EXTF" or header[1] != "700":
            errors.append(f"{path.name}: EXTF-Kennzeichen oder Header-Version ungültig")
        expected_format_name = (
            "Buchungsstapel" if category == "21" else "Debitoren/Kreditoren"
        )
        if header[3] != expected_format_name:
            errors.append(f"{path.name}: Formatname {header[3]} ist unzulässig")
        if not re.fullmatch(r"20\d{15}", header[5]):
            errors.append(f"{path.name}: Erzeugt-am-Zeitstempel ist ungültig")
        if not re.fullmatch(r"\d{4,7}", header[10]):
            errors.append(f"{path.name}: Beraternummer im Header ist ungültig")
        if not re.fullmatch(r"\d{1,5}", header[11]):
            errors.append(f"{path.name}: Mandantennummer im Header ist ungültig")
        if not _valid_date(header[12], "%Y%m%d"):
            errors.append(f"{path.name}: Wirtschaftsjahresbeginn ist ungültig")
        if not re.fullmatch(r"[4-8]", header[13]):
            errors.append(f"{path.name}: Sachkontenlänge ist ungültig")
        if header[26] and not re.fullmatch(r"(?:\d{2}){1,2}", header[26]):
            errors.append(f"{path.name}: Sachkontenrahmen ist ungültig")
        if manifest:
            contract = manifest.get("run_contract", {})
            if header[10] != str(manifest.get("beraternummer", "")):
                errors.append(f"{path.name}: Beraternummer weicht vom Laufmanifest ab")
            if header[11] != str(manifest.get("mandant", "")):
                errors.append(f"{path.name}: Mandant weicht vom Laufmanifest ab")
            if header[13] != str(contract.get("sachkontenlaenge", "")):
                errors.append(f"{path.name}: Sachkontenlänge weicht vom Laufmanifest ab")
            if header[26] != str(contract.get("sachkontenrahmen", "")):
                errors.append(f"{path.name}: Sachkontenrahmen weicht vom Laufmanifest ab")
    if not expected:
        errors.append(f"{path.name}: unbekannte Kategorie {category}")
        return errors, beleglinks
    if version != expected_version:
        errors.append(f"{path.name}: Version {version} statt {expected_version}")
    if category == "21":
        visible_batch_text = f"{path.name} {header[16] if len(header) > 16 else ''}"
        parsed_name = parse_batch_file_name(path.name)
        if not parsed_name:
            errors.append(f"{path.name}: Buchungsperiode fehlt im Dateinamen")
            file_period = ""
        else:
            file_period = parsed_name["period"]
            try:
                expected_from, expected_to = month_bounds(file_period)
            except ValueError:
                errors.append(f"{path.name}: ungültige Periode im Dateinamen")
            else:
                if header[14] != expected_from or header[15] != expected_to:
                    errors.append(f"{path.name}: Datum von/bis passt nicht zur Periode")
                if manifest:
                    reference = str(
                        manifest.get("run_contract", {}).get(
                            "wirtschaftsjahr_beginn", ""
                        )
                    )
                    try:
                        expected_wj = fiscal_year_start(reference, file_period)
                    except ValueError as exc:
                        errors.append(f"{path.name}: Wirtschaftsjahr nicht prüfbar ({exc})")
                    else:
                        if header[12] != expected_wj:
                            errors.append(
                                f"{path.name}: WJ-Beginn {header[12]} statt "
                                f"{expected_wj} für Periode {file_period}"
                            )
        if header[18:21] != ["1", "0", "0"]:
            errors.append(f"{path.name}: Buchungstyp/Rechnungszweck/Festschreibung ungültig")
        if not re.fullmatch(r"[A-Z]{3}", header[21]):
            errors.append(f"{path.name}: Header-Währung ist ungültig")
        if not re.fullmatch(r"(?:[A-Z]{2}){1,2}", header[17]):
            errors.append(f"{path.name}: Diktatkürzel ist ungültig")
        expected_label = None
        if parsed_name:
            try:
                expected_label = batch_label(
                    parsed_name["kind"], parsed_name["batch_type"],
                    {"batch_config": (manifest or {}).get("run_contract", {}).get("batch_config")},
                )
            except ValueError as exc:
                errors.append(f"{path.name}: {exc}")
        if expected_label and header[16] != expected_label:
            errors.append(f"{path.name}: Stapelbezeichnung ist nicht {expected_label}")
        if re.search(r"\b(?:GRÜN|GRUEN|GELB|ROT)\b", visible_batch_text, re.IGNORECASE):
            errors.append(
                f"{path.name}: DATEV-Dateiname oder Stapelbezeichnung enthält "
                "eine unzulässige Ampelfarbe."
            )
    if category == "16":
        if manifest:
            expected_wj = str(
                manifest.get("run_contract", {}).get(
                    "wirtschaftsjahr_beginn", ""
                )
            ).replace("-", "")
            if header[12] != expected_wj:
                errors.append(
                    f"{path.name}: WJ-Beginn im Stammdatenheader weicht ab"
                )
        if any(header[index] for index in range(14, 22)):
            errors.append(
                f"{path.name}: Bewegungsdatenfelder 15 bis 22 müssen "
                "im Stammdatenheader leer sein"
            )
    headings = lines[1].split(";")
    if headings != expected:
        errors.append(f"{path.name}: Feldüberschriften/Feldfolge weichen ab")

    requires_beleglink = category == "21"
    file_kind = parsed_name["kind"] if category == "21" and parsed_name else None
    file_batch_type = parsed_name["batch_type"] if category == "21" and parsed_name else STANDARD_BATCH_TYPE
    cost_config = manifest_cost_center_config(manifest)
    cost_required = (manifest or {}).get("run_contract", {}).get("kostenstellenpflicht") is True
    kost1_allowed = {clean_text(key) for key in (cost_config or {}).get("kost1_allowed", {})}
    kost2_allowed = {clean_text(key) for key in (cost_config or {}).get("kost2_allowed", {})}
    batch_rule = manifest_separate_batches(manifest).get(file_batch_type) or {}
    data_rows: list[list[str]] = []
    configured_asset_accounts = {
        str(value)
        for value in (manifest or {}).get("run_contract", {})
        .get("account_config", {})
        .get("asset_accounts", [])
    }
    trace_by_row: dict[int, list[dict]] = {}
    for item in (manifest or {}).get("booking_trace", []):
        if item.get("file") == path.name:
            trace_by_row.setdefault(item.get("csv_row"), []).append(item)
    for row_no, line in enumerate(lines[2:], start=3):
        fields = split_extf(line)
        if len(fields) != len(expected):
            errors.append(
                f"{path.name}, Zeile {row_no}: {len(fields)} statt "
                f"{len(expected)} Felder"
            )
            continue
        if category == "21":
            matching_trace = trace_by_row.get(row_no, [])
            trace = matching_trace[0] if len(matching_trace) == 1 else {}
            opened = trace.get("open_fields", {})
            if not isinstance(opened, dict):
                opened = {}
                errors.append(f"{path.name}, Zeile {row_no}: ungültige offene Felder")
            for key, reason in opened.items():
                if key not in OPEN_FIELD_INDEXES or not str(reason).strip() or trace.get("traffic_light") != "Rot":
                    errors.append(f"{path.name}, Zeile {row_no}: offene Felder erfordern Rot und konkrete Begründungen")
                elif fields[OPEN_FIELD_INDEXES[key]]:
                    errors.append(f"{path.name}, Zeile {row_no}: offenes Feld {key} ist gefüllt")
            if "booking_trace" in (manifest or {}):
                if len(matching_trace) != 1:
                    errors.append(f"{path.name}, Zeile {row_no}: eindeutiger Exportnachweis fehlt")
                elif trace.get("export_values") != fields:
                    errors.append(f"{path.name}, Zeile {row_no}: exportierte Werte weichen vom Exportnachweis ab")
                if trace.get("traffic_light") not in {"Grün", "Rot"}:
                    errors.append(f"{path.name}, Zeile {row_no}: ungültige Ampel")
                if trace:
                    if file_kind == BATCH_KIND_BOOKING and trace.get("traffic_light") == "Rot":
                        errors.append(f"{path.name}, Zeile {row_no}: rote Zeile im Buchungsstapel; gehört in den Klärungsstapel")
                    if file_kind == BATCH_KIND_CLARIFICATION and trace.get("traffic_light") == "Grün":
                        errors.append(f"{path.name}, Zeile {row_no}: grüne Zeile im Klärungsstapel; gehört in den Buchungsstapel")
                    if file_kind == BATCH_KIND_CLARIFICATION and trace.get("kind") == "accrual":
                        errors.append(f"{path.name}, Zeile {row_no}: Abgrenzungsauflösung gehört in den Buchungsstapel")
                    if str(trace.get("batch_type", STANDARD_BATCH_TYPE)) != file_batch_type:
                        errors.append(f"{path.name}, Zeile {row_no}: Stapeltyp im Exportnachweis passt nicht zum Dateinamen")
            data_rows.append(fields)
            def intentionally_blank(key: str) -> bool:
                return key in opened and not fields[OPEN_FIELD_INDEXES[key]] and trace.get("traffic_light") == "Rot"
            requires_beleglink = trace.get("kind") != "accrual"
            if not re.fullmatch(r"(?!0{1,10},00)\d{1,10},\d{2}", fields[0]) and not intentionally_blank("amount"):
                errors.append(f"{path.name}, Zeile {row_no}: Umsatz ist ungültig")
            if fields[1] not in {"S", "H"} and not intentionally_blank("debit_credit"):
                errors.append(f"{path.name}, Zeile {row_no}: Soll/Haben ist ungültig")
            if not re.fullmatch(r"[A-Z]{3}", fields[2]) and not intentionally_blank("currency"):
                errors.append(f"{path.name}, Zeile {row_no}: Währung ist ungültig")
            if fields[2] and fields[2] != header[21]:
                if not re.fullmatch(r"[1-9]\d{0,3},\d{2,6}", fields[3]) and not intentionally_blank("exchange_rate"):
                    errors.append(f"{path.name}, Zeile {row_no}: Fremdwährungskurs fehlt")
                if not re.fullmatch(r"(?!0{1,10},00)\d{1,10},\d{2}", fields[4]) and not intentionally_blank("base_amount"):
                    errors.append(f"{path.name}, Zeile {row_no}: Basisumsatz fehlt")
                if fields[5] != header[21]:
                    errors.append(f"{path.name}, Zeile {row_no}: Basiswährung ist falsch")
            if not re.fullmatch(r"(?!0{1,9}$)\d{1,9}", fields[6]) and not intentionally_blank("account"):
                errors.append(f"{path.name}, Zeile {row_no}: Konto ist ungültig")
            if not re.fullmatch(r"(?!0{1,9}$)\d{1,9}", fields[7]) and not intentionally_blank("contra_account"):
                errors.append(f"{path.name}, Zeile {row_no}: Gegenkonto ist ungültig")
            bu_key = fields[8]
            if bu_key and not re.fullmatch(r"\d{4}", bu_key):
                errors.append(
                    f"{path.name}, Zeile {row_no}: BU-Schlüssel ist nicht "
                    f"vierstellig DATEV-konform: {bu_key}"
                )
            is_asset_line = bool(
                configured_asset_accounts.intersection({fields[6], fields[7]})
            )
            clarification_account = str((manifest or {}).get("run_contract", {}).get("account_config", {}).get("clarification", ""))
            if is_asset_line or {"1590", clarification_account}.intersection({fields[6], fields[7]} - {""}):
                errors.append(f"{path.name}, Zeile {row_no}: Anlagen- oder Ersatzkontierung unzulässig")
            if trace.get("asset_booking"):
                side = trace.get("asset_account_field")
                if side not in {"account", "contra_account"} or not intentionally_blank(side):
                    errors.append(f"{path.name}, Zeile {row_no}: Anlagenkontofeld muss dokumentiert leer bleiben")
            if file_kind == BATCH_KIND_CLARIFICATION:
                if fields[9]:
                    errors.append(f"{path.name}, Zeile {row_no}: Belegdatum muss im Klärungsstapel leer sein (Pflichtleerung)")
            elif not re.fullmatch(r"\d{4}", fields[9]):
                errors.append(f"{path.name}, Zeile {row_no}: Belegdatum fehlt/ist ungültig")
            if fields[9] and file_period:
                if not _valid_date(
                    f"{fields[9][:2]}{fields[9][2:]}{file_period[:4]}",
                    "%d%m%Y",
                ) or fields[9][2:] != file_period[5:7]:
                    errors.append(
                        f"{path.name}, Zeile {row_no}: Belegdatum passt nicht zur Periode"
                    )
            if not re.fullmatch(r"[A-Za-z0-9_$&%*+\-/]{1,36}", fields[10]) and not intentionally_blank("document_field_1"):
                errors.append(f"{path.name}, Zeile {row_no}: Belegfeld 1 ist ungültig")
            if fields[38]:
                errors.append(f"{path.name}, Zeile {row_no}: Kost-Menge (Feld 39) muss leer sein")
            if cost_config is None:
                if fields[36] or fields[37]:
                    errors.append(f"{path.name}, Zeile {row_no}: KOST-Felder müssen ohne cost_center_config leer sein")
            else:
                if fields[36] and fields[36] not in kost1_allowed:
                    errors.append(f"{path.name}, Zeile {row_no}: KOST1 {fields[36]} ist nicht erlaubt")
                if fields[37] and fields[37] not in kost2_allowed:
                    errors.append(f"{path.name}, Zeile {row_no}: KOST2 {fields[37]} ist nicht erlaubt")
                if cost_required and not fields[36] and not intentionally_blank("kost1"):
                    errors.append(f"{path.name}, Zeile {row_no}: KOST1 fehlt bei Kostenstellenpflicht ohne dokumentiert offenes kost1")
                if cost_required and cost_config.get("kost2_required") is True and not fields[37] and not intentionally_blank("kost2"):
                    errors.append(f"{path.name}, Zeile {row_no}: KOST2 fehlt bei Pflicht-KOST2 ohne dokumentiert offenes kost2")
                required_kost1 = clean_text(batch_rule.get("required_kost1", ""))
                if required_kost1 and fields[36] != required_kost1:
                    errors.append(f"{path.name}, Zeile {row_no}: Stapeltyp {file_batch_type} verlangt KOST1 {required_kost1}")
            required_contra = clean_text(batch_rule.get("required_contra_account", ""))
            if required_contra and fields[7] != required_contra:
                errors.append(f"{path.name}, Zeile {row_no}: Stapeltyp {file_batch_type} verlangt Gegenkonto {required_contra}")
            if bool(fields[114]) != bool(fields[115]) and not (intentionally_blank("service_date") or intentionally_blank("tax_period_date")):
                errors.append(
                    f"{path.name}, Zeile {row_no}: Leistungsdatum und "
                    "Steuerperiodendatum müssen gemeinsam gefüllt sein"
                )
            for index, label in ((114, "Leistungsdatum"), (115, "Steuerperiodendatum")):
                if fields[index] and not _valid_date(fields[index], "%d%m%Y"):
                    errors.append(
                        f"{path.name}, Zeile {row_no}: {label} ist ungültig"
                    )
            booking_text = fields[13]
            if not booking_text.strip():
                errors.append(
                    f"{path.name}, Zeile {row_no}: normaler fachlicher "
                    "Buchungstext fehlt."
                )
            if len(booking_text) > 60:
                errors.append(
                    f"{path.name}, Zeile {row_no}: Buchungstext ist länger als 60 Zeichen"
                )
            if re.search(
                r"\b(?:ACHTUNG|PRÜFUNG\s+ERFORDERLICH|"
                r"PRUEFUNG\s+ERFORDERLICH|PRÜFEN|PRUEFEN|VORSCHLAG|"
                r"ANLAGENVORERFASSUNG|KONTIERUNGSVORSCHLAG|"
                r"BITTE|KLÄREN|KLAEREN|NUTZUNGSDAUER)\b",
                booking_text,
                re.IGNORECASE,
            ):
                errors.append(
                    f"{path.name}, Zeile {row_no}: Buchungstext enthält "
                    "einen internen Warn- oder Prüfhinweis."
                )
        if category == "16":
            account = fields[0]
            expected_length = int(header[13]) + 1 if header[13].isdigit() else 0
            if not account.isdigit() or len(account) != expected_length:
                errors.append(
                    f"{path.name}, Zeile {row_no}: Personenkonto muss "
                    f"{expected_length} Ziffern haben"
                )
            if not fields[1] or len(fields[1]) > 50:
                errors.append(f"{path.name}, Zeile {row_no}: Unternehmensname fehlt/ist zu lang")
            if fields[6] != "2":
                errors.append(f"{path.name}, Zeile {row_no}: Adressatentyp muss 2 sein")
            if fields[8] and not re.fullmatch(r"[A-Z]{2}", fields[8]):
                errors.append(f"{path.name}, Zeile {row_no}: EU-Land ist ungültig")
            if len(fields[9]) > 13 or (
                fields[9] and not re.fullmatch(r"[A-Z0-9]+", fields[9])
            ):
                errors.append(f"{path.name}, Zeile {row_no}: EU-UStID ist ungültig")
            primary_count = 0
            for start in (40, 51, 62, 73, 84, 164, 175, 186, 197, 208):
                bank_code = fields[start]
                iban = fields[start + 4]
                primary = fields[start + 8]
                if bank_code == "0":
                    errors.append(
                        f"{path.name}, Zeile {row_no}: Banklöschung per BLZ 0 ist unzulässig"
                    )
                if iban and not re.fullmatch(r"[A-Z]{2}[A-Z0-9]{13,32}", iban):
                    errors.append(f"{path.name}, Zeile {row_no}: IBAN ist ungültig")
                if primary:
                    if primary not in {"0", "1"}:
                        errors.append(
                            f"{path.name}, Zeile {row_no}: Hauptbankkennzeichen ungültig"
                        )
                    if primary == "1":
                        primary_count += 1
                for date_index in (start + 9, start + 10):
                    if fields[date_index] and not _valid_date(
                        fields[date_index], "%d%m%Y"
                    ):
                        errors.append(
                            f"{path.name}, Zeile {row_no}: Bankgültigkeitsdatum ungültig"
                        )
            if primary_count > 1:
                errors.append(
                    f"{path.name}, Zeile {row_no}: mehr als eine Hauptbankverbindung"
                )
        if requires_beleglink:
            match = BELEGLINK_PATTERN.fullmatch(fields[19])
            if not match:
                errors.append(
                    f"{path.name}, Zeile {row_no}: Beleglink fehlt oder ist "
                    "nicht im Format BEDI \"GUID\"."
                )
                continue
            try:
                parsed = uuid.UUID(match.group(1))
            except ValueError:
                errors.append(
                    f"{path.name}, Zeile {row_no}: Beleglink enthält keine "
                    "RFC-4122-GUID."
                )
                continue
            beleglinks.add(str(parsed).upper())
    if category == "21":
        for violation in carry_order_violations(data_rows):
            errors.append(f"{path.name}: Schleppschutz verletzt; {violation}")
    return errors, beleglinks



def _xsd_validate(xml_bytes: bytes, label: str) -> list[str]:
    xsd_dir = Path(__file__).resolve().parents[1] / "assets" / "xsd"
    schema_path = xsd_dir / "Document_v060.xsd"
    types_path = xsd_dir / "Document_types_v060.xsd"
    missing = [path.name for path in (schema_path, types_path) if not path.is_file()]
    if missing:
        return [f"{label}: DATEV-XSD-Prüfdateien fehlen: {', '.join(missing)}"]
    try:
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        schema = etree.XMLSchema(etree.parse(str(schema_path), parser))
        xml_doc = etree.fromstring(xml_bytes, parser)
        schema.assertValid(xml_doc)
    except (etree.XMLSyntaxError, etree.DocumentInvalid, etree.XMLSchemaParseError) as exc:
        return [f"{label}: XSD-Validierung fehlgeschlagen: {exc}"]
    return []



def validate_document_packages(
    package_dir: Path,
) -> tuple[list[str], set[str], set[str], int, int]:
    errors: list[str] = []
    all_guids: set[str] = set()
    booking_guids: set[str] = set()
    archives = sorted(package_dir.glob("Belegtransfer_*.zip"))
    advice_count = 0
    if package_dir.is_dir():
        unexpected = sorted(
            path.name for path in package_dir.iterdir()
            if not path.is_file()
            or not (
                path.name.startswith("Belegtransfer_") and path.suffix == ".zip"
                or path.name.startswith("EXTF_") and path.suffix == ".csv"
            )
        )
        if unexpected:
            errors.append("01_DATEV_Import enthält unzulässige Dateien oder Ordner: " + ", ".join(unexpected))
    for archive in archives:
        is_advice = archive.name.startswith("Belegtransfer_Avise_")
        advice_count += int(is_advice)
        if archive.stat().st_size > MAX_PACKAGE_BYTES:
            errors.append(f"{archive.name}: ZIP-Datei überschreitet 465 MB.")
        if not zipfile.is_zipfile(archive):
            errors.append(f"{archive.name}: keine gültige ZIP-Datei.")
            continue
        try:
            with zipfile.ZipFile(archive, "r") as bundle:
                infos = bundle.infolist()
                names = [item.filename for item in infos]
                nested = [name for name in names if name.endswith("/") or "/" in name or "\\" in name or PurePosixPath(name).name != name]
                if nested:
                    errors.append(f"{archive.name}: Unterordner/Verschachtelung unzulässig: " + ", ".join(nested))
                if names.count("document.xml") != 1:
                    errors.append(f"{archive.name}: document.xml muss exakt einmal enthalten sein.")
                    continue
                oversized = [item.filename for item in infos if item.filename != "document.xml" and item.file_size > MAX_DOCUMENT_BYTES]
                if oversized:
                    errors.append(f"{archive.name}: Einzeldatei über 20 MB: " + ", ".join(oversized))
                xml_bytes = bundle.read("document.xml")
                if b"accountsPayableLedger" in xml_bytes:
                    errors.append(f"{archive.name}: accountsPayableLedger ist unzulässig.")
                errors.extend(_xsd_validate(xml_bytes, archive.name))
                try:
                    root = ET.fromstring(xml_bytes)
                except ET.ParseError as exc:
                    errors.append(f"{archive.name}: document.xml ist ungültig ({exc}).")
                    continue
                q = lambda name: f"{{{DOCUMENT_NAMESPACE}}}{name}"
                if root.tag != q("archive") or root.get("version") != "6.0":
                    errors.append(f"{archive.name}: falsches Rootelement oder falsche Version.")
                    continue
                if root.get(f"{{{XSI_NAMESPACE}}}schemaLocation") != DOCUMENT_SCHEMA_LOCATION:
                    errors.append(f"{archive.name}: falsche xsi:schemaLocation.")
                children = list(root)
                if [item.tag for item in children] != [q("header"), q("content")]:
                    errors.append(f"{archive.name}: Reihenfolge header/content ist falsch.")
                    continue
                header, content = children
                if [item.tag for item in list(header)] != [q("date")]:
                    errors.append(f"{archive.name}: Header muss genau ein date enthalten.")
                documents = list(content)
                if not 1 <= len(documents) <= MAX_DOCUMENTS_PER_PACKAGE:
                    errors.append(f"{archive.name}: unzulässige Zahl document-Elemente.")
                referenced_files: list[str] = []
                for position, document in enumerate(documents, start=1):
                    if document.tag != q("document"):
                        errors.append(f"{archive.name}: unbekanntes Element in content.")
                        continue
                    try:
                        normalized_guid = str(uuid.UUID(document.get("guid", ""))).upper()
                    except ValueError:
                        errors.append(f"{archive.name}: document {position} ohne gültige GUID.")
                        continue
                    if normalized_guid in all_guids:
                        errors.append(f"{archive.name}: GUID {normalized_guid} wird mehrfach verwendet.")
                    all_guids.add(normalized_guid)
                    if not is_advice:
                        booking_guids.add(normalized_guid)
                    if document.get("type") is not None:
                        errors.append(f"{archive.name}: document {position} muss ohne type-Attribut sein.")
                    if document.get("processID") != "1":
                        errors.append(f"{archive.name}: document {position} muss processID=1 haben.")
                    extensions = [item for item in list(document) if item.tag == q("extension")]
                    if len(extensions) != 1:
                        errors.append(f"{archive.name}: document {position} muss genau eine File-extension enthalten.")
                        continue
                    extension = extensions[0]
                    if extension.get(f"{{{XSI_NAMESPACE}}}type") != "File":
                        errors.append(f"{archive.name}: document {position} hat keine File-extension.")
                    filename = extension.get("name", "")
                    if not filename:
                        errors.append(f"{archive.name}: document {position} ohne Dateiname.")
                    else:
                        try:
                            filename.encode("ascii")
                        except UnicodeEncodeError:
                            errors.append(f"{archive.name}: Dateiname ist nicht ASCII: {filename}")
                        referenced_files.append(filename)
                physical_files = [name for name in names if name != "document.xml"]
                for filename in physical_files:
                    if filename.lower().endswith(".pdf") and bundle.read(filename)[:5] != b"%PDF-":
                        errors.append(f"{archive.name}: {filename} ist keine PDF-Datei.")
                if len(referenced_files) != len(set(referenced_files)):
                    errors.append(f"{archive.name}: Belegdatei mehrfach referenziert.")
                missing_files = sorted(set(referenced_files) - set(physical_files))
                unreferenced = sorted(set(physical_files) - set(referenced_files))
                if missing_files:
                    errors.append(f"{archive.name}: referenzierte Dateien fehlen: " + ", ".join(missing_files))
                if unreferenced:
                    errors.append(f"{archive.name}: Dateien ohne XML-Eintrag: " + ", ".join(unreferenced))
        except (OSError, zipfile.BadZipFile) as exc:
            errors.append(f"{archive.name}: ZIP-Prüfung fehlgeschlagen ({exc}).")
    return errors, all_guids, booking_guids, len(archives), advice_count



def validate_transfer_period_separation(package_root: Path) -> list[str]:
    errors: list[str] = []
    transfer_dir = package_root / "01_DATEV_Import"
    index_path = package_root / "03_Technische_Protokolle" / "Belegindex.json"
    if not index_path.is_file():
        return ["Belegindex.json fehlt; Periodentrennung ist nicht prüfbar."]
    try:
        entries = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Belegindex.json ist ungültig ({exc})."]
    periods_by_package: dict[str, set[str]] = {}
    sequences: dict[tuple[str, str], set[int]] = {}
    pattern = re.compile(r"^Belegtransfer_(?:(Avise)_)?[0-9]+_([0-9]{4}-[0-9]{2})_([0-9]{3})[.]zip$")
    for entry in entries:
        if not entry.get("included") or entry.get("target") != "01_DATEV_Import":
            continue
        name = str(entry.get("document_package", ""))
        doc_period = str(entry.get("document_period", ""))
        package_period = str(entry.get("document_package_period", ""))
        kind = str(entry.get("document_package_kind", "booking"))
        if not name or not doc_period or not package_period:
            errors.append(f"{entry.get('transaction_id')}: Paket- oder Periodenzuordnung fehlt.")
            continue
        periods_by_package.setdefault(name, set()).add(doc_period)
        match = pattern.fullmatch(name)
        if not match:
            errors.append(f"{name}: Dateiname enthält keine eindeutige Belegperiode.")
            continue
        filename_kind = "advice" if match.group(1) else "booking"
        filename_period = match.group(2)
        number = int(match.group(3))
        sequences.setdefault((filename_kind, filename_period), set()).add(number)
        if kind != filename_kind or doc_period != package_period or doc_period != filename_period:
            errors.append(f"{entry.get('transaction_id')}: Paketart oder Periode ist widersprüchlich.")
    actual = {path.name for path in transfer_dir.glob("Belegtransfer_*.zip")}
    indexed = set(periods_by_package)
    if actual - indexed:
        errors.append("Belegtransfer-Pakete ohne Index: " + ", ".join(sorted(actual - indexed)))
    if indexed - actual:
        errors.append("Im Index genannte Pakete fehlen: " + ", ".join(sorted(indexed - actual)))
    booking_periods: set[str] = set()
    for pattern_name in ("EXTF_Buchungsstapel_*.csv", "EXTF_Klaerungsposten_*.csv"):
        for file in transfer_dir.glob(pattern_name):
            parsed = parse_batch_file_name(file.name)
            if parsed:
                booking_periods.add(parsed["period"])
    for (kind, period_value), numbers in sorted(sequences.items()):
        if numbers != set(range(1, max(numbers) + 1)):
            errors.append(f"{kind}/{period_value}: Paketnummern müssen lückenlos bei 001 beginnen.")
        if kind == "booking" and period_value not in booking_periods:
            errors.append(f"{period_value}: Belegtransfer vorhanden, aber Buchungsstapel fehlt.")
    return errors


def _trace_lights(manifest: dict) -> dict[str, str]:
    """Belegweit schlechteste Ampel je Vorgang aus dem Exportnachweis (Mehrfachzeilen einmal)."""
    lights: dict[str, str] = {}
    for item in manifest.get("booking_trace", []) or []:
        if item.get("kind") != "document":
            continue
        tid = str(item.get("transaction_id", ""))
        light = str(item.get("traffic_light", ""))
        if light == "Rot" or tid not in lights:
            lights[tid] = light
    return lights


def validate_clarification_rate(package_root: Path, manifest: dict) -> tuple[list[str], dict]:
    """Klärungsquote erneut vor der Abschlussmeldung berechnen und gegen den Nachweis prüfen."""
    errors: list[str] = []
    rate = manifest.get("clarification_rate")
    if not isinstance(rate, dict) or not isinstance(rate.get("after"), dict) or not isinstance(rate.get("before"), dict):
        return ["Klärungsquoten-Zusammenfassung (clarification_rate) fehlt im Laufmanifest."], {}
    lights = _trace_lights(manifest)
    red_ids = sorted(tid for tid, light in lights.items() if light == "Rot")
    n_after = len(lights)
    r_after = len(red_ids)
    q_after = quota(r_after, n_after)
    after = rate["after"]
    before = rate["before"]
    if int(after.get("N", -1)) != n_after or int(after.get("R", -1)) != r_after:
        errors.append(
            f"Klärungsquote: Nachweis nennt N={after.get('N')}, R={after.get('R')}, Exportnachweis ergibt N={n_after}, R={r_after}."
        )
    if after.get("Q") != q_after:
        errors.append(f"Klärungsquote: Q nach Zweitprüfung {after.get('Q')} stimmt nicht mit {q_after} überein.")
    to_green = [str(value) for value in rate.get("corrected_to_green", [])]
    to_red = [str(value) for value in rate.get("corrected_to_red", [])]
    excluded = [str(value) for value in rate.get("corrected_excluded", [])]
    expected_r_before = r_after + len(to_green) - len(to_red) + len(excluded)
    expected_n_before = n_after + len(excluded)
    if int(before.get("R", -1)) != expected_r_before or int(before.get("N", -1)) != expected_n_before:
        errors.append("Klärungsquote: Vorher-Werte widersprechen den dokumentierten Korrekturen der Zweitprüfung.")
    q_before = quota(expected_r_before, expected_n_before)
    stage_before = stage_for(q_before)
    red_before = set(red_ids) | set(to_green) | set(excluded)
    reviewed = {str(value) for value in rate.get("reviewed_transaction_ids", [])}
    if stage_before == "zweitpruefung":
        if rate.get("second_review_performed") is not True:
            errors.append(
                f"Klärungsquote {q_before} % > {THRESHOLD_SECOND_REVIEW:g} %: vollständige Zweitprüfung aller roten Vorgänge fehlt."
            )
        missing = sorted(red_before - reviewed)
        if missing:
            errors.append("Zweitprüfung unvollständig; nicht nachgeprüft: " + ", ".join(missing))
    for tid in to_green:
        if lights.get(tid) != "Grün":
            errors.append(f"Klärungsquote: {tid} als Grün korrigiert, aber nicht grün exportiert.")
    for tid in excluded:
        if tid in lights:
            errors.append(f"Klärungsquote: {tid} als ausgeschlossen korrigiert, aber exportiert.")
    cases = {str(item.get("transaction_id", "")): item for item in rate.get("red_cases", []) if isinstance(item, dict)}
    for tid in red_ids:
        case = cases.get(tid)
        if case is None or case.get("code") not in RED_REASON_CODES:
            errors.append(f"Klärungsquote: roter Vorgang {tid} ohne maschinenlesbaren Rot-Grund im Nachweis.")
    distribution = rate.get("reason_distribution") or {}
    stage_after = stage_for(q_after)
    if stage_before == "ursachenpruefung" or stage_after == "ursachenpruefung":
        cause = rate.get("cause_analysis") or {}
        for code in distribution:
            if not str(cause.get(code, "")).strip():
                errors.append(f"Klärungsquote {THRESHOLD_NORMAL:g}–{THRESHOLD_SECOND_REVIEW:g} %: Ursachenprüfung für Rot-Kategorie {code} fehlt.")
    proof = package_root / "02_Buchungspruefung" / "Klaerungsquote_Nachweis.md"
    if not proof.is_file():
        errors.append("Klärungsquoten-Nachweis fehlt: 02_Buchungspruefung/Klaerungsquote_Nachweis.md")
    else:
        text = proof.read_text(encoding="utf-8")
        for needle in (f"| N (buchungsrelevante Vorgänge) | {expected_n_before} | {n_after} |",
                       f"| R (rote Vorgänge) | {expected_r_before} | {r_after} |"):
            if needle not in text:
                errors.append(f"Klärungsquoten-Nachweis nennt nicht die geprüften Werte ({needle.strip('| ')}).")
    summary = {
        "N": n_after, "R": r_after, "Q": q_after, "stage": stage_after,
        "before": {"N": expected_n_before, "R": expected_r_before, "Q": q_before, "stage": stage_before},
        "second_review_required": stage_before == "zweitpruefung",
        "second_review_performed": rate.get("second_review_performed") is True,
        "reviewed_cases": len(reviewed & red_before),
        "corrected_to_green": len(to_green),
        "remaining_red": r_after,
        "reason_distribution": distribution,
        "professionally_open": r_after > 0,
        "check_step": "erneut vor Abschlussmeldung (Validator)",
    }
    return errors, summary


def validate_document_file_rule(package_root: Path, manifest: dict) -> list[str]:
    """Ein Buchungsbeleg = genau eine eigene PDF-Datei im Belegtransfer."""
    errors: list[str] = []
    index_path = package_root / "03_Technische_Protokolle" / "Belegindex.json"
    if not index_path.is_file():
        return []  # wird bereits von der Periodentrennung gemeldet
    try:
        entries = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    booked = set(_trace_lights(manifest))
    primary_count: dict[str, int] = {}
    pdf_names: dict[str, set[str]] = {}
    for entry in entries:
        if not entry.get("included") or entry.get("document_package_kind") != "booking":
            continue
        primaries = [str(value) for value in entry.get("primary_transaction_ids", []) or []]
        name = str(entry.get("technical_filename", ""))
        if len(primaries) > 1:
            errors.append(f"{name}: Belegdatei trägt mehrere Buchungsbelege ({', '.join(primaries)}); {DOCUMENT_FILE_RULE}.")
        for tid in primaries:
            primary_count[tid] = primary_count.get(tid, 0) + 1
        if primaries and not name.lower().endswith(".pdf"):
            errors.append(f"{name}: Buchungsbeleg ist keine PDF-Datei; {DOCUMENT_FILE_RULE}.")
        if primaries:
            pdf_names.setdefault(str(entry.get("document_package", "")), set()).add(name)
    for tid in sorted(booked):
        count = primary_count.get(tid, 0)
        if count == 0:
            errors.append(f"{tid}: gebuchter Vorgang ohne eigene PDF-Belegdatei im Belegtransfer; {DOCUMENT_FILE_RULE}.")
        elif count > 1:
            errors.append(f"{tid}: Buchungsbeleg ist auf {count} Dateien verteilt; {DOCUMENT_FILE_RULE}.")
    for package_name, names in pdf_names.items():
        archive = package_root / "01_DATEV_Import" / package_name
        if not archive.is_file() or not zipfile.is_zipfile(archive):
            continue
        with zipfile.ZipFile(archive) as bundle:
            for name in sorted(names):
                try:
                    head = bundle.open(name).read(5)
                except KeyError:
                    continue
                if head != b"%PDF-":
                    errors.append(f"{package_name}/{name}: Buchungsbeleg ist keine gültige PDF-Datei.")
    return errors


def validate_import_scope(package_root: Path, manifest: dict) -> list[str]:
    """Alle Buchungsstapel – mit und ohne Klärung – sowie alle Belegtransfer-Pakete sind zu importieren."""
    errors: list[str] = []
    if not manifest:
        return errors
    if manifest.get("transfer_rule") != TRANSFER_RULE:
        errors.append(f"Übertragungsregel fehlt im Laufmanifest ({TRANSFER_RULE}).")
    scope = manifest.get("import_scope")
    if not isinstance(scope, list):
        return errors + ["import_scope fehlt im Laufmanifest; jede DATEV-Datei muss als zu importieren geführt sein."]
    by_file = {str(item.get("file", "")): item for item in scope if isinstance(item, dict)}
    datev_dir = package_root / "01_DATEV_Import"
    if not datev_dir.is_dir():
        return errors
    for path in sorted(datev_dir.iterdir()):
        if not path.is_file():
            continue
        entry = by_file.get(path.name)
        if entry is None or str(entry.get("import", "")).lower() != "ja":
            label = "Klärungsstapel" if path.name.startswith("EXTF_Klaerungsposten_") else "DATEV-Datei"
            errors.append(f"{path.name}: {label} ist nicht als zu importieren geführt; {TRANSFER_RULE}.")
    for name in by_file:
        if not (datev_dir / name).is_file():
            errors.append(f"import_scope nennt eine nicht vorhandene Datei: {name}")
    return errors


def validate_test_import(evidence: dict, files: list[Path]) -> list[str]:
    if not isinstance(evidence, dict) or evidence.get("status") not in {"pending", "confirmed", "rejected"}:
        return ["DATEV-Testimportstatus ist ungültig."]
    if evidence["status"] == "pending":
        return []
    errors = []
    for field in ("tested_at", "datev_version", "test_client", "evidence_reference", "result_detail"):
        if not str(evidence.get(field, "")).strip():
            errors.append(f"DATEV-Testimport: Nachweisfeld {field} fehlt.")
    actual = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    if evidence.get("tested_files") != actual:
        errors.append("DATEV-Testimportnachweis gehört nicht zu exakt diesen EXTF-Dateien (alle erzeugten Buchungs- und Klärungsstapel).")
    carry = evidence.get("carry_over_result")
    if not isinstance(carry, dict):
        errors.append("DATEV-Testimport: carry_over_result je gefährdetem Feld fehlt.")
    else:
        for field in sorted(CARRY_FIELDS):
            if carry.get(field) not in CARRY_RESULTS:
                errors.append(f"DATEV-Testimport: carry_over_result.{field} muss carried, not_carried oder not_tested sein.")
    return errors


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    manifest: dict = {}
    manifest_path = args.package / "03_Technische_Protokolle" / "Laufmanifest.json"
    if not manifest_path.is_file():
        errors.append("Laufmanifest fehlt")
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not manifest.get("vollstaendig"):
            errors.append("Vollständigkeitskontrolle ist nicht aufgegangen")
        inventory = manifest.get("input_inventory")
        inventory_count = manifest.get("input_inventory_count")
        uploaded_count = manifest.get("hochgeladene_dateien")
        derived_count = manifest.get("abgeleitete_belegdateien", 0)
        if not isinstance(inventory, list):
            errors.append("Technisches input_inventory fehlt im Laufmanifest")
        elif (
            inventory_count != len(inventory)
            or not isinstance(uploaded_count, int)
            or not isinstance(derived_count, int)
            or uploaded_count + derived_count != len(inventory)
        ):
            errors.append("Eingabeinventar, hochgeladene und abgeleitete Dateianzahl stimmen nicht überein")
        elif derived_count != sum(1 for item in inventory if isinstance(item, dict) and item.get("derived_from")):
            errors.append("Zahl der abgeleiteten Belegdateien stimmt nicht mit dem Inventar überein")
        else:
            for item in inventory:
                if (
                    not isinstance(item, dict)
                    or not item.get("source_path")
                    or not isinstance(item.get("size_bytes"), int)
                    or not re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256", "")).lower())
                ):
                    errors.append("Eingabeinventar enthält einen unvollständigen Eintrag")
                    break
        missing_booking_exports = manifest.get(
            "buchungsrelevante_belege_ohne_exportzeile", []
        )
        if missing_booking_exports:
            errors.append(
                "Buchungsrelevante Belege ohne exportierte Buchungszeile: "
                + ", ".join(str(value) for value in missing_booking_exports)
            )

    if manifest.get("skill_version") != EXPECTED_SKILL_VERSION:
        errors.append("Falsche oder fehlende Skill-Version im Laufmanifest")
    if manifest.get("output_contract") != EXPECTED_OUTPUT_CONTRACT:
        errors.append(
            f"Ausgabevertrag {EXPECTED_OUTPUT_CONTRACT} fehlt im Laufmanifest"
        )
    if manifest.get("pruefprotokoll_ruecklauf_status") != "ausstehend":
        errors.append("Fachlicher Prüfprotokoll-Rücklaufstatus fehlt im Laufmanifest")

    if manifest.get("datev_import_order") != list(DATEV_IMPORT_ORDER):
        errors.append("Verbindliche DATEV-Importreihenfolge fehlt im Laufmanifest")
    run_completion = manifest.get("run_completion")
    if not isinstance(run_completion, dict) or run_completion.get("status") not in {
        "vollständig abgeschlossen", "nicht vollständig abgeschlossen",
    }:
        errors.append("Abschluss-Gate: run_completion fehlt im Laufmanifest oder hat einen ungültigen Status")
        run_completion = {"status": "nicht vollständig abgeschlossen", "open_items": []}
    if run_completion.get("datev_import_claimed") is True:
        errors.append("Abschluss-Gate: eine DATEV-Übertragung darf nicht behauptet werden")
    if manifest.get("document_file_rule") != DOCUMENT_FILE_RULE:
        errors.append(f"Belegdateiregel fehlt im Laufmanifest ({DOCUMENT_FILE_RULE})")
    if manifest and manifest.get("status", {}).get(STATUS_UNREADABLE):
        # technisch nicht auswertbare Vorgänge sind nur mit dokumentiertem Versuch zulässig (Generatorprüfung);
        # hier nur die Zählung im Nachweis sichern.
        rate_counts = (manifest.get("clarification_rate") or {}).get("counts") or {}
        if rate_counts.get("technisch_nicht_auswertbar") != manifest["status"][STATUS_UNREADABLE]:
            errors.append("Zahl technisch nicht auswertbarer Vorgänge weicht zwischen Status und Klärungsquoten-Nachweis ab")
    errors.extend(_validate_preflight_manifest(manifest))
    expected_master_records = int(manifest.get("master_records", 0))
    master_path = (
        args.package / "01_DATEV_Import" / "EXTF_Debitoren_Kreditoren.csv"
    )
    if expected_master_records:
        if not master_path.is_file():
            errors.append(
                "Stammdatenimport fehlt: Laufmanifest nennt "
                f"{expected_master_records} Datensätze, aber "
                "EXTF_Debitoren_Kreditoren.csv ist nicht vorhanden."
            )
        else:
            try:
                master_lines = master_path.read_text(
                    encoding="cp1252"
                ).splitlines()
                actual_master_records = max(0, len(master_lines) - 2)
            except OSError as exc:
                errors.append(
                    "Stammdatenimport konnte nicht gezählt werden: "
                    f"{exc}"
                )
            else:
                if actual_master_records != expected_master_records:
                    errors.append(
                        "Stammdatenimport unvollständig: Laufmanifest nennt "
                        f"{expected_master_records}, Datei enthält "
                        f"{actual_master_records} Datensätze."
                    )

    required_work_files = [
        args.package / "02_Buchungspruefung" / "Klaerungsfaelle.md",
        args.package / "02_Buchungspruefung" / "Mandantenprofil_Vorschlag.md",
        args.package / "02_Buchungspruefung" / "Abgrenzungsregister_Vorschlag.md",
        args.package / "02_Buchungspruefung" / "Taetigkeitsnachweis.md",
        args.package / "02_Buchungspruefung" / "Uebergabeliste.md",
        args.package / "02_Buchungspruefung" / "Klaerungsquote_Nachweis.md",
        args.package / "03_Technische_Protokolle" / "Belegindex.json",
    ]
    for path in required_work_files:
        if not path.is_file():
            errors.append(f"Vollständigkeits-Gate: Pflichtdatei fehlt: {path.name}")
    rate_errors, rate_summary = validate_clarification_rate(args.package, manifest) if manifest else (["Klärungsquote ohne Laufmanifest nicht prüfbar"], {})
    errors.extend(rate_errors)

    errors.extend(validate_datev_import_layout(args.package, manifest))
    errors.extend(validate_batch_files(args.package, manifest))
    errors.extend(validate_import_scope(args.package, manifest))
    workbooks = sorted(
        (args.package / "02_Buchungspruefung").glob(
            "Buchungspruefung_*.xlsx"
        )
    )
    if len(workbooks) != 1:
        errors.append(
            "Genau eine Excel-Buchungsprüfung wird erwartet; gefunden: "
            f"{len(workbooks)}"
        )
    else:
        errors.extend(validate_review_workbook(workbooks[0], manifest))

    csv_files = sorted(args.package.rglob("EXTF_*.csv"))
    if not csv_files:
        errors.append("Keine EXTF-Datei gefunden")
    booking_links: set[str] = set()
    for path in csv_files:
        csv_errors, links = validate_csv(path, manifest)
        errors.extend(csv_errors)
        booking_links.update(links)
    trace = manifest.get("booking_trace", [])
    expected_rows = {(item.get("file"), item.get("csv_row")) for item in trace}
    actual_rows = {(path.name, number) for path in csv_files if parse_batch_file_name(path.name)
                   for number in range(3, len(path.read_text(encoding="cp1252").splitlines()) + 1)}
    if expected_rows != actual_rows or len(expected_rows) != len(trace):
        errors.append("Exportnachweise und CSV-Zeilen sind nicht vollständig und eindeutig verknüpft.")
    evidence_path = args.package / "03_Technische_Protokolle" / "DATEV_Testimport.json"
    test_import = manifest.get("datev_test_import", {"status": "pending"})
    if args.datev_test_import or evidence_path.is_file():
        test_import = json.loads((args.datev_test_import or evidence_path).read_text(encoding="utf-8"))
    test_import_errors = validate_test_import(test_import, csv_files)
    errors.extend(test_import_errors)
    if args.datev_test_import and not test_import_errors:
        evidence_path.write_text(json.dumps(test_import, ensure_ascii=False, indent=2), encoding="utf-8")

    transfer_dir = args.package / "01_DATEV_Import"
    transfer_errors, document_guids, booking_document_guids, transfer_count, advice_package_count = validate_document_packages(
        transfer_dir
    )
    errors.extend(transfer_errors)
    errors.extend(validate_transfer_period_separation(args.package))
    errors.extend(validate_document_file_rule(args.package, manifest))
    booking_document_count = int(
        manifest.get("status", {}).get("Buchungszeile erzeugt", 0)
    )
    if booking_document_count and transfer_count == 0:
        errors.append(
            "Buchungsbelege vorhanden, aber kein Belegtransfer_*.zip erzeugt."
        )
    links_without_document = sorted(booking_links - booking_document_guids)
    documents_without_link = sorted(booking_document_guids - booking_links)
    if links_without_document:
        errors.append(
            "Beleglinks ohne zugehörige GUID im Belegtransfer: "
            + ", ".join(links_without_document)
        )
    if documents_without_link:
        errors.append(
            "Belege im Belegtransfer ohne zugehörigen Buchungs-Beleglink: "
            + ", ".join(documents_without_link)
        )

    completion_gate = {
        "run_status": run_completion.get("status") if manifest else "nicht vollständig abgeschlossen",
        "open_items": run_completion.get("open_items", []) if manifest else [],
        "validator_valid": not errors,
        "passed": (not errors) and bool(manifest) and run_completion.get("status") == "vollständig abgeschlossen",
        "rule": "erfolgreicher Abschluss nur bei valid=true und ohne zurückgestellte Teilentscheidungen; sonst ausdrücklich nicht vollständig abgeschlossen",
    }
    report = {
        "package": str(args.package),
        "skill_version_expected": EXPECTED_SKILL_VERSION,
        "checked_extf_files": len(csv_files),
        "checked_belegtransfer_packages": transfer_count,
        "checked_advice_packages": advice_package_count,
        "checked_document_guids": len(document_guids),
        "checked_booking_links": len(booking_links),
        "xsd": "Document_v060.xsd + Document_types_v060.xsd",
        "valid": not errors,
        "validation_scope": "interner Exportvertrag; keine Bestätigung vollständiger DATEV-Pflichtfelder",
        "datev_test_import_status": test_import.get("status", "pending"),
        "datev_import_compatibility_confirmed": test_import.get("status") == "confirmed" and not test_import_errors and not errors,
        "intentional_open_fields": [
            {key: item.get(key) for key in ("transaction_id", "file", "csv_row", "open_fields")}
            for item in trace if item.get("open_fields")
        ],
        "booking_batches": manifest.get("booking_batches", []),
        "batch_split_reasons": manifest.get("batch_split_reasons", []),
        "clarification_rate": rate_summary,
        "completion_gate": completion_gate,
        "document_file_rule": DOCUMENT_FILE_RULE,
        "errors": errors,
    }
    target = args.package / "03_Technische_Protokolle" / "Validierungsbericht.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if errors:
        print(json.dumps(report, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
