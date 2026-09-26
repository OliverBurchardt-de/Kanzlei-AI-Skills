#!/usr/bin/env python3
"""Validiert DATEV-EXTF-Kopfsatz und Belegtransfer-ZIP.

Aufruf:
    python validate_datev_package.py --csv stapel.csv --zip belege.zip
"""

from __future__ import annotations
import argparse
import csv
import re
import sys
import uuid
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

NS = "http://xml.datev.de/bedi/tps/document/v04.0"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
BEDI_RE = re.compile(r'^BEDI "([0-9a-fA-F-]{36})"$')
DATE8_RE = re.compile(r"^\d{8}$")
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")


def validate_csv(path: Path) -> tuple[list[str], set[str]]:
    errors: list[str] = []
    guids: set[str] = set()

    with path.open("r", encoding="cp1252", newline="") as f:
        rows = list(csv.reader(f, delimiter=";", quotechar='"'))

    if len(rows) < 3:
        return ["CSV enthält keinen vollständigen Kopfsatz und keine Buchung."], guids

    header, columns, data = rows[0], rows[1], rows[2:]

    if len(header) != 31:
        errors.append(f"EXTF-Kopfsatz hat {len(header)} statt 31 Felder.")
        return errors, guids

    expected = {
        0: "EXTF",
        1: "700",
        2: "21",
        3: "Buchungsstapel",
    }
    for idx, value in expected.items():
        if header[idx] != value:
            errors.append(f"Kopfsatz Feld {idx+1}: {header[idx]!r} statt {value!r}.")

    if not header[10]:
        errors.append("Beraternummer in Feld 11 fehlt.")
    if not header[11]:
        errors.append("Mandantennummer in Feld 12 fehlt.")
    if not DATE8_RE.fullmatch(header[12]):
        errors.append("Wirtschaftsjahresbeginn in Feld 13 ist ungültig.")
    if not header[13].isdigit():
        errors.append("Sachkontenlänge in Feld 14 ist ungültig.")
    if not DATE8_RE.fullmatch(header[14]):
        errors.append("Datum von in Feld 15 ist ungültig.")
    if not DATE8_RE.fullmatch(header[15]):
        errors.append("Datum bis in Feld 16 ist ungültig.")
    if DATE8_RE.fullmatch(header[14] or "") and DATE8_RE.fullmatch(header[15] or ""):
        if header[14] > header[15]:
            errors.append("Datum von ist größer als Datum bis.")

    try:
        link_idx = columns.index("Beleglink")
    except ValueError:
        errors.append("Spalte Beleglink fehlt.")
        return errors, guids

    for row_no, row in enumerate(data, start=3):
        if len(row) != len(columns):
            errors.append(
                f"Zeile {row_no} hat {len(row)} statt {len(columns)} Felder."
            )
            continue
        link = row[link_idx]
        if not link:
            continue
        match = BEDI_RE.fullmatch(link)
        if not match:
            errors.append(f"Zeile {row_no}: ungültiger Beleglink {link!r}.")
            continue
        try:
            guid = str(uuid.UUID(match.group(1)))
            guids.add(guid)
        except ValueError:
            errors.append(f"Zeile {row_no}: ungültige UUID.")

    return errors, guids


def validate_zip(path: Path) -> tuple[list[str], set[str]]:
    errors: list[str] = []
    guids: set[str] = set()

    with zipfile.ZipFile(path) as z:
        bad = z.testzip()
        if bad:
            errors.append(f"ZIP-CRC-Fehler in {bad}.")
        names = z.namelist()
        if "document.xml" not in names:
            return ["document.xml fehlt im ZIP-Stammverzeichnis."], guids
        if any("/" in name.strip("/") for name in names):
            errors.append("ZIP enthält Unterordner.")

        try:
            root = ET.fromstring(z.read("document.xml"))
        except ET.ParseError as exc:
            return [f"document.xml ist nicht wohlgeformt: {exc}"], guids

        if root.tag != f"{{{NS}}}archive":
            errors.append(f"Falsches Root-Element: {root.tag}.")
        if root.attrib.get("version") != "4.0":
            errors.append("archive@version ist nicht 4.0.")

        date_el = root.find(f"{{{NS}}}header/{{{NS}}}date")
        if date_el is None or not TIMESTAMP_RE.fullmatch(date_el.text or ""):
            errors.append("Header-Zeitstempel ist nicht YYYY-MM-DDTHH:MM:SS.")

        for doc in root.findall(f"{{{NS}}}content/{{{NS}}}document"):
            raw_guid = doc.attrib.get("guid", "")
            try:
                guid = str(uuid.UUID(raw_guid))
            except ValueError:
                errors.append(f"Ungültige document-GUID {raw_guid!r}.")
                continue
            if guid in guids:
                errors.append(f"Doppelte GUID {guid}.")
            guids.add(guid)

            ext = doc.find(f"{{{NS}}}extension")
            if ext is None:
                errors.append(f"Dokument {guid}: extension fehlt.")
                continue
            if ext.attrib.get(f"{{{XSI}}}type") != "File":
                errors.append(f"Dokument {guid}: xsi:type ist nicht File.")
            filename = ext.attrib.get("name", "")
            if not filename:
                errors.append(f"Dokument {guid}: Dateiname fehlt.")
            elif filename not in names:
                errors.append(f"Dokument {guid}: Datei {filename!r} fehlt im ZIP.")

    return errors, guids


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--zip", dest="zip_path", type=Path, required=True)
    args = parser.parse_args()

    errors_csv, csv_guids = validate_csv(args.csv)
    errors_zip, zip_guids = validate_zip(args.zip_path)
    errors = errors_csv + errors_zip

    missing_in_xml = csv_guids - zip_guids
    missing_in_csv = zip_guids - csv_guids
    if missing_in_xml:
        errors.append("CSV-GUIDs fehlen in XML: " + ", ".join(sorted(missing_in_xml)))
    if missing_in_csv:
        errors.append("XML-GUIDs fehlen in CSV: " + ", ".join(sorted(missing_in_csv)))

    if errors:
        print("VALIDIERUNG FEHLGESCHLAGEN")
        for error in errors:
            print("- " + error)
        return 1

    print("VALIDIERUNG ERFOLGREICH")
    print(f"- GUIDs: {len(csv_guids)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
