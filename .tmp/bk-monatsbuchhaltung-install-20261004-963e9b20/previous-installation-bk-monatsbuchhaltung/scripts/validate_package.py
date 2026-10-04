from __future__ import annotations

import argparse
import calendar
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

from datev_io import BOOKING_FIELDS, MASTER_FIELDS, fiscal_year_start, month_bounds
from sharepoint_target import build_targets


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
        "Ampel-Einstufung", "Buchungsstapel", "Vorgangs-ID", "Belegdatum",
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
    "Mandanten-Hinweise", "Stammdatenänderungen",
}
FORBIDDEN_VISIBLE_REVIEW_HEADERS = {
    "Belegdatei", "Quelldatei", "Originaldateiname", "Importfähig",
}
FORBIDDEN_DATEV_FOLDERS = {
    "01_Buchungsstapel", "02_Stammdaten", "03_Belegtransfer",
    "06_Abgrenzungsstapel", "01_Buchungsstapel_Gruen",
    "02_Buchungsstapel_Gelb", "03_Buchungsstapel_Rot", "04_Stammdaten",
}


EXPECTED_SKILL_VERSION = "0.3.8"
EXPECTED_OUTPUT_CONTRACT = "single-datev-import-folder-v2"


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


def validate_review_workbook(path: Path) -> list[str]:
    errors: list[str] = []
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

            for sheet_name, expected in EXPECTED_REVIEW_HEADERS.items():
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


def validate_datev_import_layout(package_root: Path) -> list[str]:
    errors: list[str] = []
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

    check_sharepoint(
        evidence.get("mandantenprofil"),
        str(targets["profile_url"]),
        f"{client_number}.md",
        "Mandantenprofil",
    )
    def check_accrual_register(item: object) -> None:
        if isinstance(item, dict) and item.get("status") == "not_found":
            if item.get("source_url") != str(targets["accrual_url"]):
                errors.append("Abgrenzungsregister-Nichtvorhanden-Nachweis verwendet nicht die exakte URL.")
            if item.get("file_name") != f"{client_number}.md":
                errors.append("Abgrenzungsregister-Dateiname stimmt nicht.")
            if not item.get("retrieved_via") or not item.get("checked_at"):
                errors.append("Abgrenzungsregister-Nichtvorhanden-Nachweis ist unvollständig.")
            if item.get("not_found_code") != "itemNotFound":
                errors.append("Abgrenzungsregister wurde nicht eindeutig als itemNotFound bestätigt.")
            if item.get("site_verified") is not True or item.get("library_verified") is not True:
                errors.append("Site/Bibliothek für das Abgrenzungsregister wurden nicht bestätigt.")
            if not isinstance(item.get("direct_lookup_attempts"), int) or item["direct_lookup_attempts"] < 2:
                errors.append("Abgrenzungsregister wurde nicht zweimal direkt geprüft.")
            return
        check_sharepoint(
            item,
            str(targets["accrual_url"]),
            f"{client_number}.md",
            "Abgrenzungsregister",
        )
    if contract.get("accounting_method") == "Bilanz":
        check_accrual_register(evidence.get("abgrenzungsregister"))
    if contract.get("accounting_method") not in {"Bilanz", "EÜR"}:
        errors.append("Rechnungslegungsart im Laufmanifest ist ungültig.")
    if contract.get("kostenstellenpflicht") is not False:
        errors.append("Kostenstellenprüfung ist nicht ausdrücklich mit false bestätigt.")
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
        period_match = re.search(r"_([0-9]{4}-[0-9]{2})[.]csv$", path.name)
        if not period_match:
            errors.append(f"{path.name}: Buchungsperiode fehlt im Dateinamen")
            file_period = ""
        else:
            file_period = period_match.group(1)
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
        expected_label = (
            "Buchungsstapel"
            if path.name.startswith("EXTF_Buchungsstapel_")
            else "Klärungsposten"
            if path.name.startswith("EXTF_Klaerungsposten_")
            else None
        )
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

    requires_beleglink = (
        category == "21" and not path.name.startswith("EXTF_Abgrenzungen_")
    )
    configured_asset_accounts = {
        str(value)
        for value in (manifest or {}).get("run_contract", {})
        .get("account_config", {})
        .get("asset_accounts", [])
    }
    for row_no, line in enumerate(lines[2:], start=3):
        fields = split_extf(line)
        if len(fields) != len(expected):
            errors.append(
                f"{path.name}, Zeile {row_no}: {len(fields)} statt "
                f"{len(expected)} Felder"
            )
            continue
        if category == "21":
            if not re.fullmatch(r"(?!0{1,10},00)\d{1,10},\d{2}", fields[0]):
                errors.append(f"{path.name}, Zeile {row_no}: Umsatz ist ungültig")
            if fields[1] not in {"S", "H"}:
                errors.append(f"{path.name}, Zeile {row_no}: Soll/Haben ist ungültig")
            if not re.fullmatch(r"[A-Z]{3}", fields[2]):
                errors.append(f"{path.name}, Zeile {row_no}: Währung ist ungültig")
            if fields[2] != header[21]:
                if not re.fullmatch(r"[1-9]\d{0,3},\d{2,6}", fields[3]):
                    errors.append(f"{path.name}, Zeile {row_no}: Fremdwährungskurs fehlt")
                if not re.fullmatch(r"(?!0{1,10},00)\d{1,10},\d{2}", fields[4]):
                    errors.append(f"{path.name}, Zeile {row_no}: Basisumsatz fehlt")
                if fields[5] != header[21]:
                    errors.append(f"{path.name}, Zeile {row_no}: Basiswährung ist falsch")
            if not re.fullmatch(r"(?!0{1,9}$)\d{1,9}", fields[6]):
                errors.append(f"{path.name}, Zeile {row_no}: Konto ist ungültig")
            if not re.fullmatch(r"(?!0{1,9}$)\d{1,9}", fields[7]):
                errors.append(f"{path.name}, Zeile {row_no}: Gegenkonto ist ungültig")
            bu_key = fields[8]
            if bu_key and not re.fullmatch(r"\d{4}", bu_key):
                errors.append(
                    f"{path.name}, Zeile {row_no}: BU-Schlüssel ist nicht "
                    f"vierstellig DATEV-konform: {bu_key}"
                )
            is_red_file = path.name.startswith("EXTF_Klaerungsposten_2_")
            is_asset_line = bool(
                configured_asset_accounts.intersection({fields[6], fields[7]})
            )
            if is_asset_line and not is_red_file:
                errors.append(
                    f"{path.name}, Zeile {row_no}: Anlagenkonto darf nur im "
                    "roten Klärungsposten stehen"
                )
            if is_asset_line and fields[9]:
                errors.append(
                    f"{path.name}, Zeile {row_no}: Anlagenkonto erfordert ein "
                    "leeres DATEV-Belegdatum"
                )
            if is_red_file:
                if fields[9]:
                    errors.append(
                        f"{path.name}, Zeile {row_no}: Rot muss absichtlich "
                        "ein leeres Belegdatum enthalten"
                    )
            elif not re.fullmatch(r"\d{4}", fields[9]):
                errors.append(f"{path.name}, Zeile {row_no}: Belegdatum fehlt/ist ungültig")
            elif file_period:
                if not _valid_date(
                    f"{fields[9][:2]}{fields[9][2:]}{file_period[:4]}",
                    "%d%m%Y",
                ) or fields[9][2:] != file_period[5:7]:
                    errors.append(
                        f"{path.name}, Zeile {row_no}: Belegdatum passt nicht zur Periode"
                    )
            if not re.fullmatch(r"[A-Za-z0-9_$&%*+\-/]{1,36}", fields[10]):
                errors.append(f"{path.name}, Zeile {row_no}: Belegfeld 1 ist ungültig")
            if any(fields[index] for index in (36, 37, 38)):
                errors.append(f"{path.name}, Zeile {row_no}: KOST-Felder müssen leer sein")
            if bool(fields[114]) != bool(fields[115]):
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
                r"PRUEFUNG\s+ERFORDERLICH|PRÜFEN|PRUEFEN)\b",
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
            match = re.search(r"_([0-9]{4}-[0-9]{2})[.]csv$", file.name)
            if match:
                booking_periods.add(match.group(1))
    for (kind, period_value), numbers in sorted(sequences.items()):
        if numbers != set(range(1, max(numbers) + 1)):
            errors.append(f"{kind}/{period_value}: Paketnummern müssen lückenlos bei 001 beginnen.")
        if kind == "booking" and period_value not in booking_periods:
            errors.append(f"{period_value}: Belegtransfer vorhanden, aber Buchungsstapel fehlt.")
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
        if not isinstance(inventory, list):
            errors.append("Technisches input_inventory fehlt im Laufmanifest")
        elif inventory_count != len(inventory) or uploaded_count != len(inventory):
            errors.append("Eingabeinventar und hochgeladene Dateianzahl stimmen nicht überein")
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
            "Ausgabevertrag single-datev-import-folder-v2 fehlt im Laufmanifest"
        )

    expected_import_order = [
        "EXTF_Debitoren_Kreditoren.csv (falls vorhanden)",
        "Belegtransfer_*.zip und Belegtransfer_Avise_*.zip",
        "EXTF Kategorie 21: Buchungs-, Klärungs- und Abgrenzungsstapel",
    ]
    if manifest.get("datev_import_order") != expected_import_order:
        errors.append("Verbindliche DATEV-Importreihenfolge fehlt im Laufmanifest")
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
    ]
    for path in required_work_files:
        if not path.is_file():
            errors.append(f"Arbeitsdatei fehlt: {path.name}")

    errors.extend(validate_datev_import_layout(args.package))
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
        errors.extend(validate_review_workbook(workbooks[0]))

    csv_files = sorted(args.package.rglob("EXTF_*.csv"))
    if not csv_files:
        errors.append("Keine EXTF-Datei gefunden")
    booking_links: set[str] = set()
    for path in csv_files:
        csv_errors, links = validate_csv(path, manifest)
        errors.extend(csv_errors)
        booking_links.update(links)

    transfer_dir = args.package / "01_DATEV_Import"
    transfer_errors, document_guids, booking_document_guids, transfer_count, advice_package_count = validate_document_packages(
        transfer_dir
    )
    errors.extend(transfer_errors)
    errors.extend(validate_transfer_period_separation(args.package))
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

    report = {
        "package": str(args.package),
        "checked_extf_files": len(csv_files),
        "checked_belegtransfer_packages": transfer_count,
        "checked_advice_packages": advice_package_count,
        "checked_document_guids": len(document_guids),
        "checked_booking_links": len(booking_links),
        "xsd": "Document_v060.xsd + Document_types_v060.xsd",
        "valid": not errors,
        "errors": errors,
    }
    target = args.package / "03_Technische_Protokolle" / "Validierungsbericht.json"
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