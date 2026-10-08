"""Records für die Übertragung über den Riecken-Connector (SKILL.md Abschnitt 5).

Eingaben: fertiges Paket (EXTF-Dateien, Belegtransfer-ZIPs mit document.xml,
Laufmanifest), Lauf-JSON und Klärungskonto. Ausgabe: ``riecken_records.json`` mit
Records für ``datev_add_posting`` getrennt nach grün (Stapel Eingangsrechnungen)
und rot (Stapel Klärungsposten über das Klärungskonto) sowie
``nicht_uebertragbar.json`` mit den abgewiesenen Zeilen.

Regeln für rote Zeilen:
- genau eine offene Kontoseite erhält das Klärungskonto; zwei offene Seiten werden abgewiesen,
- ohne sicheren Betrag oder ohne sicheres Datum wird nicht übertragen (kein Platzhalter),
- ein offener BU-Schlüssel bleibt leer,
- Buchungstext ``KLÄR <Vorgangs-ID> <offenes Thema> <Zielkonto oder Alternativen>``, höchstens 60 Zeichen.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from decimal import Decimal
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from datev_io import (  # noqa: E402
    BATCH_KIND_BOOKING,
    BATCH_KIND_CLARIFICATION,
    STANDARD_BATCH_TYPE,
    clean_text,
    parse_batch_file_name,
)
from validate_package import split_extf  # noqa: E402

KLAER_PREFIX = "KLÄR"
MAX_TEXT_LENGTH = 60
MAX_RECORDS_PER_CALL = 100
GREEN_LABEL = "Eingangsrechnungen"
RED_LABEL = "Klärungsposten"
DATEV_FOLDER = "01_DATEV_Import"
LOG_FOLDER = "03_Technische_Protokolle"
PLACEHOLDER_AMOUNTS = {Decimal("0.01")}

REASON_BOTH_SIDES = "beide Kontoseiten offen"
REASON_AMOUNT = "Betrag fehlt oder unsicher"
REASON_DATE = "Belegdatum fehlt oder unsicher"
REASON_TEXT = "KLÄR-Buchungstext länger als 60 Zeichen"
REASON_PLACEHOLDER = "Platzhalterbetrag"

OPEN_FIELD_TOPICS = {
    "account": "Konto offen",
    "contra_account": "Gegenkonto offen",
    "bu_key": "BU offen",
    "kost1": "KOST1 offen",
    "kost2": "KOST2 offen",
    "document_field_1": "Belegnr. offen",
    "currency": "Währung offen",
    "service_date": "Leistungsdatum offen",
    "tax_period_date": "Steuerperiode offen",
    "exchange_rate": "Kurs offen",
    "base_amount": "Basisbetrag offen",
}
RED_REASON_TOPICS = {
    "fehlende_belegangabe": "Belegangabe fehlt",
    "steuer_unklar": "Steuer unklar",
    "rechtstraeger_unklar": "Rechtsträger unklar",
    "personenkonto_unklar": "Personenkonto unklar",
    "datev_dublette_unklar": "Dublette prüfen",
    "konto_unklar": "Konto unklar",
    "anlage_gwg_spezialregel": "Anlage",
    "technisch_unlesbar": "Beleg unlesbar",
    "spezialregel_sonstige": "Sonderfall",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--package", required=True, type=Path, help="Paketordner mit 01_DATEV_Import und 03_Technische_Protokolle")
    parser.add_argument("--input", required=True, type=Path, help="Lauf-JSON des Buchhaltungslaufs")
    parser.add_argument("--clearing-account", required=True, help="Klärungskonto aus dem Mandantenprofil, z. B. 159900 oder 1599")
    parser.add_argument("--clearing-name", default="Klärungskonto Buchhaltung", help="Bezeichnung des Klärungskontos")
    parser.add_argument("--klaer-texte", type=Path, help="JSON: Vorgangs-ID -> KLÄR-Text oder {\"topic\": ..., \"target\": ...}")
    parser.add_argument("--green-label", default=GREEN_LABEL, help="Stapelbezeichnung für grüne Zeilen")
    parser.add_argument("--red-label", default=RED_LABEL, help="Stapelbezeichnung für rote Zeilen")
    parser.add_argument("--output", required=True, type=Path, help="Arbeitsordner für riecken_records.json und nicht_uebertragbar.json")
    return parser.parse_args()


# --- Hilfsfunktionen -------------------------------------------------------------

def extf_amount(value: str) -> Decimal | None:
    text = (value or "").strip()
    if not text:
        return None
    return Decimal(text.replace(".", "").replace(",", "."))


def account_text(value: Any) -> str:
    return re.sub(r"\D", "", str(value or ""))


def extf_rows(path: Path) -> list[list[str]]:
    lines = path.read_text(encoding="cp1252").splitlines()
    return [split_extf(line) for line in lines[2:] if line.strip()]


def beleglink_guid(value: str) -> str | None:
    match = re.search(r'BEDI\s*"?([0-9A-Fa-f-]{36})"?', value or "")
    return match.group(1).upper() if match else None


def document_guids(package: Path) -> dict[str, dict[str, str]]:
    """GUID -> {file, zip} aus allen Belegtransfer-ZIPs des Pakets."""
    result: dict[str, dict[str, str]] = {}
    for archive in sorted((package / DATEV_FOLDER).glob("Belegtransfer_*.zip")):
        with zipfile.ZipFile(archive) as bundle:
            if "document.xml" not in bundle.namelist():
                continue
            root = ET.fromstring(bundle.read("document.xml"))
        for document in root.iter():
            if not document.tag.endswith("}document") and document.tag != "document":
                continue
            guid = str(document.get("guid", "")).upper()
            file_name = ""
            for extension in document:
                if extension.get("name"):
                    file_name = str(extension.get("name"))
            if guid:
                result[guid] = {"file": file_name, "zip": archive.name}
    return result


def manifest_trace(package: Path) -> dict[tuple[str, int], dict[str, Any]]:
    manifest_path = package / LOG_FOLDER / "Laufmanifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {
        (str(item.get("file")), int(item.get("csv_row"))): item
        for item in manifest.get("booking_trace", [])
    }


def manifest_batches(package: Path) -> dict[str, dict[str, Any]]:
    manifest_path = package / LOG_FOLDER / "Laufmanifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {str(item.get("file")): item for item in manifest.get("booking_batches", [])}


def shorten(text: str, limit: int = MAX_TEXT_LENGTH) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip()


def default_topic(document: dict[str, Any], trace: dict[str, Any]) -> str:
    opened = trace.get("open_fields") or {}
    code = str((document.get("red_reason") or {}).get("code", ""))
    if trace.get("asset_booking"):
        return "Anlage"
    parts = [OPEN_FIELD_TOPICS[field] for field in opened if field in OPEN_FIELD_TOPICS]
    if not parts and code in RED_REASON_TOPICS:
        parts = [RED_REASON_TOPICS[code]]
    if not parts:
        parts = ["Klärung offen"]
    return ", ".join(dict.fromkeys(parts))


def default_target(document: dict[str, Any], trace: dict[str, Any], cases: dict[str, dict[str, Any]]) -> str:
    case = cases.get(str(document.get("transaction_id", "")), {})
    for key in ("target_account", "proposed_account", "suggested_account"):
        value = clean_text(document.get(key) or case.get(key))
        if value:
            return f"Ziel {value}"
    if trace.get("asset_booking"):
        return "Ziel Anlagenkonto"
    return ""


def klaer_text(transaction_id: str, topic: str, target: str) -> str:
    """KLÄR-Text bilden; bei Überlänge zuerst das Thema kürzen, nie Kürzel und ID."""
    base = f"{KLAER_PREFIX} {transaction_id}"
    tail = f" {target}".rstrip() if target else ""
    room = MAX_TEXT_LENGTH - len(base) - len(tail) - (1 if topic else 0)
    if room < 0:
        return shorten(f"{base}{tail}")
    topic = shorten(topic, room) if topic else ""
    return re.sub(r"\s+", " ", f"{base} {topic}{tail}").strip()


def resolve_klaer_text(transaction_id: str, document: dict[str, Any], trace: dict[str, Any],
                       cases: dict[str, dict[str, Any]], overrides: dict[str, Any]) -> tuple[str, bool]:
    override = overrides.get(transaction_id)
    if isinstance(override, str):
        text = re.sub(r"\s+", " ", override).strip()
        if not text.startswith(KLAER_PREFIX):
            text = f"{KLAER_PREFIX} {text}"
        return text, True
    if isinstance(override, dict):
        topic = clean_text(override.get("topic")) or default_topic(document, trace)
        target = clean_text(override.get("target")) or default_target(document, trace, cases)
        return klaer_text(transaction_id, topic, target), False
    return klaer_text(transaction_id, default_topic(document, trace), default_target(document, trace, cases)), False


# --- Kernlogik -------------------------------------------------------------------

def record_from_row(row: list[str], trace: dict[str, Any], guids: dict[str, dict[str, str]]) -> dict[str, Any]:
    amount = extf_amount(row[0])
    debit_credit = (row[1] or "S").strip().upper()
    account = account_text(row[6])
    contra = account_text(row[7])
    bu = account_text(row[8])
    guid = beleglink_guid(row[19])
    date = trace.get("recognized_date")
    if not date and row[9].strip():
        # Fallback: Belegdatum TTMM aus dem EXTF plus Periode aus dem Trace
        period = str(trace.get("period") or "")
        if re.fullmatch(r"\d{4}", row[9].strip()) and re.fullmatch(r"\d{4}-\d{2}", period):
            date = f"{period[:4]}-{row[9].strip()[2:]}-{row[9].strip()[:2]}"
    record: dict[str, Any] = {
        "transaction_id": trace.get("transaction_id"),
        "source_file": trace.get("file"),
        "csv_row": trace.get("csv_row"),
        "date": date,
        "amount": float(amount) if amount is not None else None,
        "debit_account": account if debit_credit == "S" else contra,
        "credit_account": contra if debit_credit == "S" else account,
        "document_field1": (row[10] or "").strip() or None,
        "posting_description": (row[13] or "").strip() or None,
        "tax_key": int(bu) if bu else None,
        "kost1": (row[36] or "").strip() or None,
        "kost2": (row[37] or "").strip() or None,
        "document_guid": guid,
    }
    if guid and guid not in guids:
        record["document_guid_warning"] = "GUID nicht in document.xml des Belegtransfers gefunden"
    return {key: value for key, value in record.items() if value is not None}


def process_red(record: dict[str, Any], trace: dict[str, Any], document: dict[str, Any], clearing: str,
                text: str, text_is_override: bool) -> tuple[dict[str, Any] | None, str | None]:
    opened = trace.get("open_fields") or {}
    amount = record.get("amount")
    if "amount" in opened or amount in (None, 0, 0.0):
        return None, REASON_AMOUNT
    if Decimal(str(amount)) in PLACEHOLDER_AMOUNTS:
        return None, REASON_PLACEHOLDER
    if not record.get("date") or "recognized_date" in opened:
        return None, REASON_DATE
    debit = record.get("debit_account", "")
    credit = record.get("credit_account", "")
    if not debit and not credit:
        return None, REASON_BOTH_SIDES
    if not debit:
        record["debit_account"] = clearing
        record["clearing_side"] = "debit"
    elif not credit:
        record["credit_account"] = clearing
        record["clearing_side"] = "credit"
    else:
        record["clearing_side"] = None
    if record["debit_account"] == clearing and record["credit_account"] == clearing:
        return None, REASON_BOTH_SIDES
    if "bu_key" in opened:
        record.pop("tax_key", None)
    if len(text) > MAX_TEXT_LENGTH:
        if text_is_override:
            return None, f"{REASON_TEXT} ({len(text)} Zeichen): {text}"
        text = shorten(text)
    record["posting_description"] = text
    record["klaer_text_length"] = len(text)
    record["original_description"] = trace.get("export_values", [None] * 14)[13] if trace.get("export_values") else None
    return record, None


def build_records(package: Path, data: dict[str, Any], clearing: str, clearing_name: str,
                  overrides: dict[str, Any], green_label: str, red_label: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    clearing = account_text(clearing)
    if not clearing:
        raise ValueError("Klärungskonto muss eine Kontonummer sein.")
    documents = {str(doc.get("transaction_id")): doc for doc in data.get("documents", [])}
    cases: dict[str, dict[str, Any]] = {}
    for case in data.get("clarification_cases", []):
        for tid in case.get("transaction_ids", []):
            cases.setdefault(str(tid), case)
    traces = manifest_trace(package)
    batches = manifest_batches(package)
    guids = document_guids(package)
    run = data.get("run", {})
    configured_clearing = account_text((run.get("account_config") or {}).get("clarification"))
    if configured_clearing and configured_clearing != clearing:
        raise ValueError(
            f"Klärungskonto {clearing} weicht von account_config.clarification ({configured_clearing}) ab."
        )

    sequences: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    extf_files = sorted((package / DATEV_FOLDER).glob("EXTF_*.csv"))
    for path in extf_files:
        parsed = parse_batch_file_name(path.name)
        if not parsed:
            continue
        rows = extf_rows(path)
        batch = batches.get(path.name, {})
        kind = parsed["kind"]
        period = parsed["period"]
        if kind == BATCH_KIND_CLARIFICATION:
            label = red_label
        elif parsed.get("suffix") and batch.get("label"):
            label = str(batch["label"])
        else:
            label = green_label
        extf_total = sum((extf_amount(row[0]) or Decimal("0")) for row in rows)
        records: list[dict[str, Any]] = []
        for offset, row in enumerate(rows, start=3):
            trace = traces.get((path.name, offset))
            if trace is None:
                raise ValueError(f"{path.name} Zeile {offset}: kein Eintrag im Laufmanifest (booking_trace).")
            record = record_from_row(row, trace, guids)
            transaction_id = str(trace.get("transaction_id"))
            if kind == BATCH_KIND_BOOKING:
                if not record.get("date") or record.get("amount") in (None, 0.0) or not record.get("debit_account") or not record.get("credit_account"):
                    raise ValueError(f"{path.name} Zeile {offset}: grüne Zeile unvollständig; grüne Zeilen werden 1:1 übertragen.")
                records.append(record)
                continue
            document = documents.get(transaction_id, {})
            text, is_override = resolve_klaer_text(transaction_id, document, trace, cases, overrides)
            result, reason = process_red(record, trace, document, clearing, text, is_override)
            if result is None:
                rejected.append({
                    "transaction_id": transaction_id, "file": path.name, "csv_row": offset,
                    "period": period, "amount": record.get("amount"), "reason": reason,
                    "open_fields": trace.get("open_fields") or {},
                    "partner": document.get("partner"), "document_guid": record.get("document_guid"),
                    "decision": None, "decided_by": None, "decided_at": None,
                })
                continue
            records.append(result)
        transferable_total = sum(Decimal(str(item["amount"])) for item in records)
        rejected_total = sum(Decimal(str(item["amount"] or 0)) for item in rejected if item["file"] == path.name)
        if transferable_total + rejected_total != extf_total:
            raise ValueError(f"{path.name}: Summenabgleich fehlgeschlagen ({transferable_total} + {rejected_total} != {extf_total}).")
        sequences.append({
            "month": period,
            "description": label,
            "kind": "rot" if kind == BATCH_KIND_CLARIFICATION else "gruen",
            "batch_type": parsed.get("batch_type") or STANDARD_BATCH_TYPE,
            "source_file": path.name,
            "extf_rows": len(rows),
            "extf_total": str(extf_total),
            "record_count": len(records),
            "total_amount": str(transferable_total),
            "not_transferred_count": len(rows) - len(records),
            "not_transferred_total": str(rejected_total),
            "calls": [records[i:i + MAX_RECORDS_PER_CALL] for i in range(0, len(records), MAX_RECORDS_PER_CALL)],
        })
    result = {
        "mandant": run.get("mandantennummer"),
        "clearing_account": {"account": clearing, "name": clearing_name},
        "labels": {"gruen": green_label, "rot": red_label},
        "max_records_per_call": MAX_RECORDS_PER_CALL,
        "records_gruen": [item for item in sequences if item["kind"] == "gruen"],
        "records_rot": [item for item in sequences if item["kind"] == "rot"],
        "master_data_file": "EXTF_Debitoren_Kreditoren.csv" if (package / DATEV_FOLDER / "EXTF_Debitoren_Kreditoren.csv").is_file() else None,
        "transferred_files_expected": [item["source_file"] for item in sequences],
        "preview": [
            {"month": item["month"], "description": item["description"], "record_count": item["record_count"], "total_amount": item["total_amount"]}
            for item in sequences
        ],
    }
    return result, rejected


def main() -> int:
    args = parse_args()
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        overrides = json.loads(args.klaer_texte.read_text(encoding="utf-8")) if args.klaer_texte else {}
        result, rejected = build_records(
            args.package, data, args.clearing_account, args.clearing_name, overrides, args.green_label, args.red_label,
        )
        args.output.mkdir(parents=True, exist_ok=True)
        records_path = args.output / "riecken_records.json"
        rejected_path = args.output / "nicht_uebertragbar.json"
        records_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        rejected_path.write_text(json.dumps(rejected, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({
            "records": str(records_path), "nicht_uebertragbar": str(rejected_path),
            "preview": result["preview"], "nicht_uebertragbar_count": len(rejected),
        }, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:  # pragma: no cover - CLI-Fehlerpfad
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
