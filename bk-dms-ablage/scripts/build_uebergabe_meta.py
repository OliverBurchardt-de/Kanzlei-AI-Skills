"""Erzeugt und validiert die Metadaten-Begleitdatei (<Datei>.dms.json).

Aufruf:
    python build_uebergabe_meta.py <datei> --mandant 10002 --jahr 2025 \
        --dokumenttyp bescheidreview_arbeitspapier \
        --beschreibung "Bescheidreview KSt 2025" --quelle-skill bescheid-review \
        [--monat 3] [--stichworte "Bescheid, KSt"] [--update-von-dms-guid <GUID>]

Schreibt <datei>.dms.json neben die Datei und gibt das Ergebnis (inkl.
upload_lane) als JSON auf stdout aus. Die Schema-Validierung erfolgt gegen
schemas/uebergabe.schema.json (Kopie des zentralen Kontrakts aus
dms-automation/bridge-worker/schemas/) sofern jsonschema installiert ist.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

CONTRACT_VERSION = "1.0"
DIRECT_UPLOAD_MAX_BYTES = 900 * 1024  # M365-Connector-Limit 1 MiB, Sicherheitsmarge

SCHEMA_CANDIDATES = [
    Path(__file__).resolve().parent.parent / "references" / "uebergabe.schema.json",
    Path(__file__).resolve().parents[2] / "dms-automation" / "bridge-worker" / "schemas" / "uebergabe.schema.json",
]


def build_sidecar(file_path: Path, args: argparse.Namespace) -> dict:
    if not re.fullmatch(r"\d{5}", args.mandant):
        raise ValueError("Die Mandantennummer muss genau fünf Ziffern enthalten.")
    data = file_path.read_bytes()
    sidecar = {
        "contract_version": CONTRACT_VERSION,
        "mandanten_nr": args.mandant,
        "jahr": args.jahr,
        "monat": args.monat,
        "dokumenttyp": args.dokumenttyp,
        "beschreibung": args.beschreibung[:255],
        "stichworte": args.stichworte,
        "datei_name": file_path.name,
        "sha256": hashlib.sha256(data).hexdigest(),
        "datei_groesse_bytes": len(data),
        "quelle_skill": args.quelle_skill,
        "erstellt_am": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "binary_delivery": "upload" if len(data) <= DIRECT_UPLOAD_MAX_BYTES else "manual",
        "update_von_dms_guid": args.update_von_dms_guid,
    }
    return sidecar


def validate(sidecar: dict) -> str:
    for schema_path in SCHEMA_CANDIDATES:
        if schema_path.exists():
            try:
                import jsonschema
            except ImportError:
                return "uebersprungen (jsonschema nicht installiert)"
            jsonschema.validate(sidecar, json.loads(schema_path.read_text(encoding="utf-8")))
            return f"ok ({schema_path.name})"
    return "uebersprungen (Schema nicht gefunden)"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("datei")
    parser.add_argument("--mandant", required=True)
    parser.add_argument("--jahr", required=True, type=int)
    parser.add_argument("--dokumenttyp", required=True)
    parser.add_argument("--beschreibung", required=True)
    parser.add_argument("--quelle-skill", required=True)
    parser.add_argument("--monat", type=int, default=None)
    parser.add_argument("--stichworte", default=None)
    parser.add_argument("--update-von-dms-guid", default=None)
    args = parser.parse_args()

    file_path = Path(args.datei)
    if not file_path.is_file():
        print(f"FEHLER: Datei nicht gefunden: {file_path}", file=sys.stderr)
        return 1

    sidecar = build_sidecar(file_path, args)
    validation = validate(sidecar)

    sidecar_path = file_path.with_name(f"{file_path.name}.dms.json")
    sidecar_path.write_text(
        json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "sidecar_path": str(sidecar_path),
                "schema_validierung": validation,
                "upload_lane": sidecar["binary_delivery"],
                "datei_groesse_bytes": sidecar["datei_groesse_bytes"],
                "sha256": sidecar["sha256"],
                "hinweis": (
                    "Datei und Sidecar hochladen (erst Datei, dann Sidecar)."
                    if sidecar["binary_delivery"] == "upload"
                    else "Datei ist zu groß für den Direktupload: NUR das Sidecar hochladen "
                    "und den Nutzer bitten, die Datei manuell in denselben Ordner zu legen."
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
