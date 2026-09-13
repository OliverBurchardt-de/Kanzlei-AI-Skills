#!/usr/bin/env python3
"""Rebuild the supplied DATEV catalogues. Build only: requires pdfplumber and pypdf."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

SOURCES = (
    ("9222265_Tabelle der Ausfallschlüssel.pdf", "2025-12-30", "ausfallschluessel"),
    ("9226266_Tabelle der DATEV-Standardlohnarten.pdf", "2026-06-11", "standardlohnarten"),
    ("9225689_Tabelle der DATEV-Standardlohnarten für Baulohn.pdf", "2026-08-06", "baulohnarten"),
)


def records_from_tables(tables, kind):
    records = []
    for table in tables:
        for row in table["rows"]:
            if kind == "ausfallschluessel":
                if row[0] == "Ausfallschlüssel":
                    continue
                code = (row[0] or "").split("\n")[0]
                if len(row) != 7 or not 1 <= len(code) <= 2 or not code.isalnum():
                    raise ValueError(f"Unklare Ausfallschlüsselzeile auf Seite {table['page']}: {row}")
                record = {
                    "code": code, "bezeichnung": row[1], "festbezugskuerzung": row[2],
                    "anspruch_lohnzahlung": row[3], "anwesenheitsstunden": row[4],
                    "unterbrechungstatbestand": row[5], "fehlzeit_unbezahlt": row[6],
                }
                until = re.search(r"einschließlich\s*([0-9]{2})/([0-9]{4})", row[0])
                if until:
                    record["erfassbar_bis"] = f"{until[2]}-{until[1]}"
            else:
                # PDF layout contains a decorative two-cell box in addition to the table.
                if len(row) != 15 or row[0] == "Thema":
                    continue
                cell = re.sub(r"\s+", "", row[1] or "")
                match = re.fullmatch(r"([0-9]{4})(?:\[neuabVersion([0-9]+\.[0-9]+)\])?", cell)
                if not match:
                    raise ValueError(f"Unklare Lohnartnummer auf Seite {table['page']}: {row}")
                record = {"code": match[1], "thema": row[0], "bezeichnung": row[2],
                          "lohnartenkern": re.sub(r"\s+", "", row[3] or ""),
                          "faktorschluessel": re.sub(r"\s+", "", row[4] or "")}
                if match[2]:
                    record["ab_lug_version"] = match[2]
            record.update(pdf_seite=table["page"], originalzellen=row)
            records.append(record)
    duplicates = [k for k, n in Counter(r["code"] for r in records).items() if n > 1]
    if duplicates or not records:
        raise ValueError(f"Leerer Katalog oder doppelte Schlüssel: {duplicates}")
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tables-cache", type=Path, help="Vorher mit pdfplumber extrahierte Tabellen für dieselben Originaldateien")
    args = parser.parse_args()
    from pypdf import PdfReader
    args.output.mkdir(parents=True, exist_ok=True)
    for name, date, kind in SOURCES:
        source = args.source_dir / name
        reader = PdfReader(source)
        text = "\n\n".join(f"=== PDF-SEITE {i+1} ===\n" + (page.extract_text(extraction_mode="layout") or "") for i, page in enumerate(reader.pages))
        cache = args.tables_cache / (name + ".tables.json") if args.tables_cache else None
        if cache:
            tables = json.loads(cache.read_text(encoding="utf-8"))
        else:
            import pdfplumber
            with pdfplumber.open(source) as pdf:
                tables = [{"page": i+1, "rows": table} for i, page in enumerate(pdf.pages) for table in page.extract_tables()]
        records = records_from_tables(tables, kind)
        catalogue = {"dokument": name, "dokumentstand": date, "pdf_seiten": len(reader.pages),
                     "quelle_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                     "anzahl": len(records), "eintraege": records}
        (args.output/name).write_bytes(source.read_bytes())
        (args.output/Path(name).with_suffix(".txt")).write_text(text, encoding="utf-8")
        (args.output/(kind+".json")).write_text(json.dumps(catalogue, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        print(f"{kind}: {len(records)} eindeutige Schlüssel; {len(reader.pages)} PDF-Seiten", flush=True)


if __name__ == "__main__":
    main()
