"""Einen Beleg anhand seiner GUID aus einem Belegtransfer-ZIP entfernen (SKILL.md Abschnitt 5).

Entfernt die Belegdatei und den zugehörigen ``document``-Eintrag in ``document.xml``,
packt das ZIP neu, führt ``testzip`` aus und legt das Original unter
``03_Technische_Protokolle/ersetzt/`` ab (Standard: neben ``01_DATEV_Import``,
abweichend über ``--replaced-dir``).
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

DOCUMENT_NAMESPACE = "http://xml.datev.de/bedi/tps/document/v06.0"
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--zip", required=True, type=Path, help="Belegtransfer-ZIP in 01_DATEV_Import")
    parser.add_argument("--guid", required=True, help="Beleg-GUID aus document.xml")
    parser.add_argument("--reason", default="", help="Grund der Entfernung (für das Protokoll)")
    parser.add_argument("--replaced-dir", type=Path, help="Ablage des Originals; Standard: ../03_Technische_Protokolle/ersetzt")
    return parser.parse_args()


def remove_document(archive: Path, guid: str, replaced_dir: Path | None = None, reason: str = "") -> dict:
    guid = guid.strip().upper()
    if not archive.is_file():
        raise ValueError(f"{archive}: Datei nicht gefunden.")
    replaced_dir = replaced_dir or (archive.parent.parent / "03_Technische_Protokolle" / "ersetzt")
    replaced_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive) as bundle:
        names = bundle.namelist()
        if "document.xml" not in names:
            raise ValueError(f"{archive.name}: document.xml fehlt.")
        xml_bytes = bundle.read("document.xml")
        contents = {name: bundle.read(name) for name in names if name != "document.xml"}

    ET.register_namespace("", DOCUMENT_NAMESPACE)
    ET.register_namespace("xsi", XSI_NAMESPACE)
    root = ET.fromstring(xml_bytes)
    removed_file = None
    for content in root.iter(f"{{{DOCUMENT_NAMESPACE}}}content"):
        for document in list(content):
            if str(document.get("guid", "")).upper() != guid:
                continue
            for extension in document:
                if extension.get("name"):
                    removed_file = str(extension.get("name"))
            content.remove(document)
    if removed_file is None:
        raise ValueError(f"{archive.name}: GUID {guid} nicht in document.xml.")
    if removed_file not in contents:
        raise ValueError(f"{archive.name}: Belegdatei {removed_file} fehlt im ZIP.")
    remaining = [doc for doc in root.iter(f"{{{DOCUMENT_NAMESPACE}}}document")]
    if not remaining:
        raise ValueError(f"{archive.name}: Nach der Entfernung bliebe kein Beleg übrig; das ZIP stattdessen ganz zurückziehen.")
    del contents[removed_file]
    ET.indent(root, space="  ")
    new_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True, short_empty_elements=True)

    original = replaced_dir / archive.name
    if original.exists():
        stem, suffix = archive.stem, archive.suffix
        counter = 2
        while (replaced_dir / f"{stem}_{counter:02d}{suffix}").exists():
            counter += 1
        original = replaced_dir / f"{stem}_{counter:02d}{suffix}"
    shutil.move(str(archive), str(original))

    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr("document.xml", new_xml)
        for name, payload in contents.items():
            bundle.writestr(name, payload)
    with zipfile.ZipFile(archive) as bundle:
        bad = bundle.testzip()
        if bad is not None:
            raise ValueError(f"{archive.name}: testzip meldet beschädigten Eintrag {bad}.")
        remaining_names = bundle.namelist()
    if removed_file in remaining_names:
        raise ValueError(f"{archive.name}: Belegdatei {removed_file} ist noch enthalten.")
    log = {
        "zip": archive.name, "guid": guid, "removed_file": removed_file, "reason": reason,
        "original_moved_to": str(original), "remaining_documents": len(remaining), "testzip": "ok",
    }
    (replaced_dir / f"{archive.stem}_entfernt_{guid}.json").write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    return log


def main() -> int:
    args = parse_args()
    try:
        print(json.dumps(remove_document(args.zip, args.guid, args.replaced_dir, args.reason), ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:  # pragma: no cover - CLI-Fehlerpfad
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
