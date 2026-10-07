from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import uuid
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal, InvalidOperation
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from sharepoint_target import build_targets
from datev_io import (
    BATCH_KIND_BOOKING,
    BATCH_KIND_CLARIFICATION,
    BOOKING_FIELDS,
    CARRY_FIELDS,
    DATEV_IMPORT_ORDER,
    MASTER_FIELDS,
    STANDARD_BATCH_TYPE,
    ascii_filename,
    batch_file_name,
    batch_label,
    batch_type_suffix,
    booking_row,
    carry_empty_fields,
    carry_order_violations,
    carry_sort_key,
    clean_text,
    missing_mapping_issues,
    plain_language_issues,
    single_task_issues,
    extf_header,
    master_row,
    month_bounds,
    write_extf,
    validate_open_fields,
    accrual_document,
)


FOLDERS = {
    "datev": "01_DATEV_Import",
    "review": "02_Buchungspruefung",
    "logs": "03_Technische_Protokolle",
    "advice": "04_Zahlungsavise",
}

SKILL_VERSION = "1.5.0"
OUTPUT_CONTRACT = "monthly-booking-and-clarification-batches-v4"

VALID_STATUSES = {
    "Buchungszeile erzeugt",
    "sichere Dublette – nicht erneut gebucht",
    "nicht buchungsrelevant",
    "außerhalb Auftragszeitraum",
}
VALID_LIGHTS = {"Grün", "Rot"}
SOURCE_ROLES = {
    "primary_invoice",
    "supporting_document",
    "payment_notice",
    "cover_sheet",
    "duplicate_copy",
}
JOB_MODE = "belegbuchhaltung"
ACCRUAL_THRESHOLD = Decimal("800")

DOCUMENT_NAMESPACE = "http://xml.datev.de/bedi/tps/document/v06.0"
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
DOCUMENT_SCHEMA_LOCATION = (
    f"{DOCUMENT_NAMESPACE} Document_v060.xsd"
)
MAX_DOCUMENT_BYTES = 20 * 1024 * 1024
RECOMMENDED_PACKAGE_BYTES = 100 * 1024 * 1024
MAX_PACKAGE_BYTES = 465 * 1024 * 1024
MAX_DOCUMENTS_PER_PACKAGE = 4999
ALLOWED_DOCUMENT_EXTENSIONS = {
    ".pdf", ".xml", ".tif", ".tiff", ".bmp", ".csv", ".doc", ".docx",
    ".gif", ".jpeg", ".jpg", ".ods", ".odt", ".pkcs7", ".png", ".rtf",
    ".txt", ".xls", ".xlsx",
}


def normalized_person_account_name(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]+", " ", str(value).upper()).strip()


def is_collective_person_account_name(value: Any) -> bool:
    normalized = normalized_person_account_name(value)
    if not normalized:
        return False
    tokens = normalized.split()
    first = tokens[0]
    if first in {"DIVERSE", "DIVERS", "DIV", "CPD"}:
        return True
    compact = "".join(tokens)
    return any(
        marker in compact
        for marker in ("SAMMELDEBITOR", "SAMMELKREDITOR", "SAMMELKONTO")
    )


def person_account_type(account: str, run: dict[str, Any]) -> str | None:
    if not account.isdigit():
        return None
    number = int(account)
    for account_type in ("debitor", "kreditor"):
        item = run["person_account_ranges"][account_type]
        if int(item["start"]) <= number <= int(item["end"]):
            return account_type
    return None


def parse_decimal_amount(value: Any) -> Decimal:
    text = str(value).strip().replace(" ", "")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Ungültiger Abgrenzungsbetrag: {value}") from exc


def validate_accrual_thresholds(data: dict[str, Any]) -> None:
    for collection in ("accrual_register", "accrual_candidates"):
        for item in data.get(collection, []):
            accrual_id = item.get("accrual_id", "ohne Abgrenzungs-ID")
            raw_amount = item.get("threshold_amount", item.get("original_net"))
            if raw_amount in (None, ""):
                raise ValueError(
                    f"{accrual_id}: maßgeblicher Betrag für die "
                    "800-Euro-Regel fehlt."
                )
            amount = parse_decimal_amount(raw_amount)
            if amount <= ACCRUAL_THRESHOLD:
                raise ValueError(
                    f"{accrual_id}: Abgrenzung mit {amount} EUR unzulässig; "
                    "Beträge bis einschließlich 800 EUR werden vollständig im "
                    "Buchungsmonat erfasst."
                )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DATEV-Belegbuchhaltungspaket bauen")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--node", default="node")
    return parser.parse_args()


def _normalized_internal_bu_key(value: Any) -> str:
    text = str(value or "").strip()
    if re.fullmatch(r"0\d{3}", text):
        text = text[1:]
    if text and not re.fullmatch(r"\d{3}", text):
        raise ValueError(f"Ungültiger fachlicher BU-Schlüssel: {value}")
    return text



def _validate_sharepoint_evidence(
    evidence: Any,
    *,
    expected_url: str,
    expected_name: str,
    label: str,
) -> dict[str, str]:
    if not isinstance(evidence, dict):
        raise ValueError(f"Abbruch: {label}-Abrufnachweis fehlt.")
    required = {"source_url", "file_name", "file_uri", "retrieved_via", "sha256"}
    missing = sorted(key for key in required if evidence.get(key) in (None, ""))
    if missing:
        raise ValueError(f"Abbruch: {label}-Abrufnachweis unvollständig: " + ", ".join(missing))
    if evidence["source_url"] != expected_url:
        raise ValueError(f"Abbruch: {label} wurde nicht von der verbindlichen exakten SharePoint-URL geladen.")
    if evidence["file_name"] != expected_name:
        raise ValueError(f"Abbruch: {label}-Dateiname ist nicht {expected_name}.")
    digest = str(evidence["sha256"]).lower()
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError(f"Abbruch: {label}-SHA-256 ist ungültig.")
    raw_path = evidence.get("raw_file_path")
    raw_text = evidence.get("content_utf8")
    if raw_path:
        raw_file = Path(str(raw_path))
        if not raw_file.is_file():
            raise ValueError(f"Abbruch: {label}-Rohdatei fehlt: {raw_file}")
        raw_bytes = raw_file.read_bytes()
        try:
            raw_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"Abbruch: {label}-Rohdatei ist nicht UTF-8.") from exc
        evidence_mode = "raw_file"
    elif isinstance(raw_text, str):
        raw_bytes = raw_text.encode("utf-8")
        evidence_mode = "content_utf8"
    else:
        raise ValueError(f"Abbruch: {label}-Abrufnachweis enthält weder raw_file_path noch content_utf8.")
    if hashlib.sha256(raw_bytes).hexdigest() != digest:
        raise ValueError(f"Abbruch: {label}-SHA-256 stimmt nicht mit dem Inhalt überein.")
    if not raw_bytes.strip():
        raise ValueError(f"Abbruch: {label}-Datei ist leer.")
    return {
        "source_url": expected_url,
        "file_name": expected_name,
        "file_uri": str(evidence["file_uri"]),
        "retrieved_via": str(evidence["retrieved_via"]),
        "raw_evidence": str(raw_path) if raw_path else "content_utf8",
        "evidence_mode": evidence_mode,
        "sha256": digest,
    }


def _validate_accrual_register_evidence(
    evidence: Any,
    *,
    expected_url: str,
    expected_name: str,
) -> dict[str, Any]:
    if not isinstance(evidence, dict) or evidence.get("status") != "not_found":
        return _validate_sharepoint_evidence(
            evidence,
            expected_url=expected_url,
            expected_name=expected_name,
            label="Abgrenzungsregister",
        )
    summary = _confirmed_not_found_evidence(
        evidence,
        expected_url=expected_url,
        expected_name=expected_name,
        label="Abgrenzungsregister",
    )
    summary["first_run_without_register"] = True
    return summary


def validate_preflight_evidence(data: dict[str, Any]) -> None:
    run = data["run"]
    client_number = str(run["mandantennummer"]).zfill(5)
    targets = build_targets(client_number)
    profile_contract = data["mandantenprofil"]
    if profile_contract["status"] == "provisional_first_run":
        profile_summary = _confirmed_not_found_evidence(
            run.get("mandantenprofil_evidence"),
            expected_url=str(targets["profile_url"]),
            expected_name=f"{client_number}.md",
            label="Mandantenprofil",
        )
        profile_summary["profile_status"] = "vorläufig – Freigabe ausstehend"
    else:
        profile_summary = _validate_sharepoint_evidence(
            run.get("mandantenprofil_evidence"),
            expected_url=str(targets["profile_url"]),
            expected_name=f"{client_number}.md",
            label="Mandantenprofil",
        )
        profile_summary["profile_status"] = "freigegeben"
    accounting_method = str(run.get("accounting_method", "")).strip()
    if accounting_method not in {"Bilanz", "EÜR"}:
        raise ValueError("Abbruch: accounting_method muss Bilanz oder EÜR sein.")
    accrual_summary = None
    if accounting_method == "Bilanz":
        accrual_summary = _validate_accrual_register_evidence(
            run.get("abgrenzungsregister_evidence"),
            expected_url=str(targets["accrual_url"]),
            expected_name=f"{client_number}.md",
        )
    live = run.get("datev_live_evidence")
    if not isinstance(live, dict):
        raise ValueError("Abbruch: technischer DATEV-Livenachweis fehlt.")
    if live.get("source") != "DATEV live":
        raise ValueError("Abbruch: DATEV-Livenachweis hat eine unzulässige Quelle.")
    for key in (
        "beraternummer", "mandantennummer", "wirtschaftsjahr_beginn",
        "sachkontenlaenge", "sachkontenrahmen",
    ):
        if str(live.get(key, "")) != str(run.get(key, "")):
            raise ValueError(f"Abbruch: DATEV-Livenachweis für {key} stimmt nicht mit dem Lauf überein.")
    for flag, count_key in (
        ("master_data_checked", "master_data_records_found"),
        ("prior_bookings_checked", "prior_booking_records_found"),
    ):
        if live.get(flag) is not True:
            raise ValueError(f"Abbruch: DATEV-Livenachweis {flag}=true fehlt.")
        count = live.get(count_key)
        if not isinstance(count, int) or count < 0:
            raise ValueError(f"Abbruch: DATEV-Livenachweis {count_key} ist ungültig.")
    try:
        datetime.fromisoformat(str(live.get("retrieved_at", "")).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Abbruch: DATEV-Abrufzeitpunkt fehlt oder ist ungültig.") from exc
    valid_accounts = live.get("validated_accounts")
    valid_bu_keys = live.get("validated_bu_keys")
    used_person_accounts = live.get("used_person_accounts")
    if not isinstance(valid_accounts, list) or not valid_accounts:
        raise ValueError("Abbruch: live validierte DATEV-Konten fehlen.")
    if not isinstance(valid_bu_keys, list):
        raise ValueError("Abbruch: live validierte DATEV-BU-Schlüssel fehlen.")
    if not isinstance(used_person_accounts, list):
        raise ValueError(
            "Abbruch: DATEV-Livenachweis used_person_accounts fehlt."
        )
    for evidence_key in ("highest_creditor_account", "highest_debtor_account"):
        value = live.get(evidence_key)
        if value in (None, "") or not str(value).isdigit():
            raise ValueError(f"Abbruch: DATEV-Livenachweis enthält kein gültiges {evidence_key}.")
    account_set = {str(value) for value in valid_accounts}
    if any(
        not re.fullmatch(r"(?!0{1,9}$)\d{1,9}", value)
        for value in account_set
    ):
        raise ValueError("Abbruch: DATEV-Kontennachweis enthält ungültige Konten.")
    cost_center_set: list[str] = []
    cost_system_active = None
    if isinstance(run.get("cost_center_config"), dict):
        if live.get("cost_system_active") is not True:
            raise ValueError(
                "Abbruch: DATEV-Livenachweis cost_system_active=true fehlt, obwohl "
                "Kostenstellen konfiguriert sind."
            )
        live_cost_centers = live.get("validated_cost_centers")
        if not isinstance(live_cost_centers, list):
            raise ValueError("Abbruch: DATEV-Livenachweis validated_cost_centers fehlt.")
        cost_center_set = sorted({clean_text(value) for value in live_cost_centers} - {""})
        cost_system_active = True
    bu_set = {_normalized_internal_bu_key(value) for value in valid_bu_keys}
    if "" in bu_set:
        bu_set.remove("")
    person_account_map: dict[str, dict[str, str]] = {}
    for item in used_person_accounts:
        if not isinstance(item, dict):
            raise ValueError(
                "Abbruch: used_person_accounts enthält keinen Datensatz."
            )
        account = str(item.get("account", ""))
        account_type = str(item.get("account_type", "")).strip().lower()
        name = str(item.get("name", "")).strip()
        expected_type = person_account_type(account, run)
        if expected_type is None or account_type != expected_type:
            raise ValueError(
                f"Abbruch: Personenkontonachweis {account} hat einen "
                "ungültigen Bereich oder Typ."
            )
        if account not in account_set:
            raise ValueError(
                f"Abbruch: Personenkontonachweis {account} ist nicht live "
                "als verwendbares Konto bestätigt."
            )
        if not name:
            raise ValueError(
                f"Abbruch: Personenkontonachweis {account} enthält keinen Namen."
            )
        if is_collective_person_account_name(name):
            raise ValueError(
                f"Abbruch: Personenkonto {account} ({name}) ist ein "
                "unzulässiges Sammel-/CPD-Konto."
            )
        if account in person_account_map:
            raise ValueError(
                f"Abbruch: Personenkontonachweis {account} ist doppelt."
            )
        person_account_map[account] = {
            "account_type": account_type,
            "name": name,
        }
    run["_preflight_summary"] = {
        "mandantenprofil": profile_summary,
        "abgrenzungsregister": accrual_summary,
        "datev": {
            "source": "DATEV live",
            "connector": live.get("connector"),
            "retrieved_via": live.get("retrieved_via"),
            "retrieved_at": str(live["retrieved_at"]),
            "validated_accounts": sorted(account_set),
            "validated_accounts_count": len(account_set),
            "validated_bu_keys": sorted(bu_set),
            "highest_creditor_account": live.get("highest_creditor_account"),
            "highest_debtor_account": live.get("highest_debtor_account"),
            "cost_system_active": cost_system_active,
            "validated_cost_centers": cost_center_set,
            "beraternummer": live.get("beraternummer"),
            "mandantennummer": live.get("mandantennummer"),
            "wirtschaftsjahr_beginn": live.get("wirtschaftsjahr_beginn"),
            "sachkontenlaenge": live.get("sachkontenlaenge"),
            "sachkontenrahmen": live.get("sachkontenrahmen"),
            "master_data_checked": live.get("master_data_checked"),
            "master_data_records_found": live.get("master_data_records_found"),
            "prior_bookings_checked": live.get("prior_bookings_checked"),
            "prior_booking_records_found": live.get("prior_booking_records_found"),
            "used_person_accounts": [
                {
                    "account": account,
                    "account_type": item["account_type"],
                    "name": item["name"],
                }
                for account, item in sorted(person_account_map.items())
            ],
        },
    }
    run["_validated_accounts"] = sorted(account_set)
    run["_validated_bu_keys"] = sorted(bu_set)
    run["_validated_cost_centers"] = cost_center_set
    run["_used_person_accounts"] = person_account_map



def validate_run_values(run: dict[str, Any]) -> None:
    consultant = str(run["beraternummer"])
    client = str(run["mandantennummer"])
    if not re.fullmatch(r"\d{4,7}", consultant) or not 1001 <= int(consultant) <= 9999999:
        raise ValueError("Beraternummer liegt außerhalb des DATEV-Wertebereichs.")
    if not client.isdigit() or not 1 <= int(client) <= 99999:
        raise ValueError("Mandantennummer liegt außerhalb des DATEV-Wertebereichs.")
    try:
        datetime.strptime(str(run["wirtschaftsjahr_beginn"]), "%Y-%m-%d")
        parsed_month = datetime.strptime(str(run["buchungsmonat"]), "%Y-%m")
    except ValueError as exc:
        raise ValueError("Wirtschaftsjahresbeginn oder Buchungsmonat ist ungültig.") from exc
    if parsed_month.strftime("%Y-%m") != str(run["buchungsmonat"]):
        raise ValueError("Buchungsmonat ist nicht kanonisch JJJJ-MM.")
    account_length = int(run["sachkontenlaenge"])
    if account_length not in range(4, 9):
        raise ValueError("Sachkontenlänge muss zwischen 4 und 8 liegen.")
    if not re.fullmatch(r"(?:\d{2}){1,2}", str(run["sachkontenrahmen"])):
        raise ValueError("Sachkontenrahmen muss zwei oder vier Ziffern enthalten.")
    if not re.fullmatch(r"[A-Z]{3}", str(run.get("waehrung", "EUR")).upper()):
        raise ValueError("Basiswährung muss ein dreistelliger ISO-Code sein.")
    if not isinstance(run.get("kostenstellenpflicht"), bool):
        raise ValueError(
            "Abbruch: kostenstellenpflicht muss aus dem Profil ausdrücklich "
            "als true oder false übernommen sein."
        )
    validate_cost_center_config(run)
    validate_batch_config(run)

    vat = run.get("vat_config")
    if not isinstance(vat, dict):
        raise ValueError("Umsatzsteuerkonfiguration vat_config fehlt.")
    if vat.get("sales_treatment") not in {"steuerpflichtig", "steuerfrei", "gemischt"}:
        raise ValueError("vat_config.sales_treatment ist ungültig.")
    if vat.get("input_tax_deduction") not in {"voll", "keiner", "anteilig"}:
        raise ValueError("vat_config.input_tax_deduction ist ungültig.")
    if vat.get("default_domestic_input_treatment") not in {
        "volle_vorsteuer", "keine_vorsteuer", "anteilige_vorsteuer"
    }:
        raise ValueError("vat_config.default_domestic_input_treatment ist ungültig.")

    accounts = run.get("account_config")
    if not isinstance(accounts, dict):
        raise ValueError("Mandantenspezifische account_config fehlt.")
    for key in ("private_expense", "gwg"):
        value = str(accounts.get(key, ""))
        if not value.isdigit() or len(value) != account_length:
            raise ValueError(f"account_config.{key} muss ein gültiges Sachkonto sein.")
    asset_accounts = accounts.get("asset_accounts")
    if not isinstance(asset_accounts, list) or not asset_accounts:
        raise ValueError("account_config.asset_accounts muss alle verwendbaren Anlagenkonten enthalten.")
    normalized_asset_accounts = [str(value) for value in asset_accounts]
    if len(set(normalized_asset_accounts)) != len(normalized_asset_accounts):
        raise ValueError("account_config.asset_accounts enthält doppelte Konten.")
    for value in normalized_asset_accounts:
        if not value.isdigit() or len(value) != account_length:
            raise ValueError("account_config.asset_accounts enthält ein ungültiges Sachkonto.")
    if str(accounts["gwg"]) not in normalized_asset_accounts:
        raise ValueError("Das konfigurierte GWG-Konto muss in asset_accounts enthalten sein.")

    ranges = run.get("person_account_ranges")
    if not isinstance(ranges, dict):
        raise ValueError("person_account_ranges fehlt.")
    expected_person_length = account_length + 1
    for kind in ("debitor", "kreditor"):
        item = ranges.get(kind)
        if not isinstance(item, dict):
            raise ValueError(f"Personenkontenbereich {kind} fehlt.")
        start = str(item.get("start", ""))
        end = str(item.get("end", ""))
        if (
            not start.isdigit() or not end.isdigit()
            or len(start) != expected_person_length
            or len(end) != expected_person_length
            or int(start) > int(end)
        ):
            raise ValueError(f"Personenkontenbereich {kind} ist ungültig.")


def validate_cost_center_config(run: dict[str, Any]) -> None:
    """Cost centers are booked whenever configured; the Pflicht only decides what an empty KOST1 means."""
    required = run.get("kostenstellenpflicht") is True
    config = run.get("cost_center_config")
    if config is None:
        if required:
            raise ValueError(
                "Abbruch: unkonfigurierte Pflichtkostenstelle; kostenstellenpflicht=true "
                "erfordert cost_center_config aus dem Mandantenprofil."
            )
        return
    prefix = "Abbruch: unkonfigurierte Pflichtkostenstelle; " if required else ""
    if not isinstance(config, dict):
        raise ValueError(f"{prefix}cost_center_config muss ein Objekt sein.")
    missing = [
        key for key in ("kost_system", "kost1_required", "kost2_required", "kost1_allowed", "kost2_allowed", "rules_source")
        if key not in config
    ]
    if missing:
        raise ValueError(f"{prefix}cost_center_config unvollständig: " + ", ".join(missing))
    if not isinstance(config.get("kost_system"), int) or config["kost_system"] not in (1, 2):
        raise ValueError(f"{prefix}cost_center_config.kost_system muss 1 oder 2 sein.")
    for key in ("kost1_required", "kost2_required"):
        if not isinstance(config.get(key), bool):
            raise ValueError(f"{prefix}cost_center_config.{key} muss true oder false sein.")
    if required and config["kost1_required"] is not True:
        raise ValueError(f"{prefix}kostenstellenpflicht=true erfordert kost1_required=true.")
    if config["kost1_required"] is True and not required:
        raise ValueError("cost_center_config.kost1_required=true widerspricht kostenstellenpflicht=false.")
    for key in ("kost1_allowed", "kost2_allowed"):
        allowed = config.get(key)
        if not isinstance(allowed, dict):
            raise ValueError(f"{prefix}cost_center_config.{key} muss ein Objekt aus Nummer und Bezeichnung sein.")
        for number, name in allowed.items():
            text = clean_text(number)
            if not text or len(text) > 36 or not re.fullmatch(r"[A-Za-z0-9_$&%*+\-/]+", text):
                raise ValueError(f"{prefix}cost_center_config.{key} enthält eine ungültige Kostenstelle: {number!r}")
            if not clean_text(name):
                raise ValueError(f"{prefix}cost_center_config.{key}: Bezeichnung für {text} fehlt.")
    if not config["kost1_allowed"]:
        raise ValueError(f"{prefix}cost_center_config.kost1_allowed ist leer.")
    if config["kost2_required"] is True and not config["kost2_allowed"]:
        raise ValueError(f"{prefix}kost2_required=true erfordert kost2_allowed.")
    if not clean_text(config.get("rules_source")):
        raise ValueError(f"{prefix}cost_center_config.rules_source fehlt.")


def validate_batch_config(run: dict[str, Any]) -> None:
    config = run.get("batch_config")
    if config is None:
        return
    if not isinstance(config, dict) or not isinstance(config.get("separate_batches"), dict):
        raise ValueError("batch_config.separate_batches muss ein Objekt je Stapeltyp sein.")
    cost_config = run.get("cost_center_config")
    allowed_kost1 = {
        clean_text(key) for key in ((cost_config or {}).get("kost1_allowed") or {})
    } if isinstance(cost_config, dict) else set()
    seen_suffixes: set[str] = set()
    for batch_type, item in config["separate_batches"].items():
        key = str(batch_type)
        if key == STANDARD_BATCH_TYPE or not re.fullmatch(r"[a-z][a-z0-9]*", key):
            raise ValueError(f"batch_config: ungültiger Stapeltyp {key!r} (Kleinbuchstaben/Ziffern, nicht standard).")
        if not isinstance(item, dict):
            raise ValueError(f"batch_config.{key} muss ein Objekt sein.")
        label = clean_text(item.get("label", ""))
        if not label or len(label) > 30:
            raise ValueError(f"batch_config.{key}.label fehlt oder ist länger als 30 Zeichen.")
        suffix = batch_type_suffix(key)
        if suffix in seen_suffixes:
            raise ValueError(f"batch_config: Dateisuffix {suffix} ist doppelt.")
        seen_suffixes.add(suffix)
        required_kost1 = clean_text(item.get("required_kost1", ""))
        if required_kost1:
            if not isinstance(cost_config, dict):
                raise ValueError(f"batch_config.{key}.required_kost1 erfordert cost_center_config.")
            if required_kost1 not in allowed_kost1:
                raise ValueError(f"batch_config.{key}.required_kost1 {required_kost1} ist nicht in kost1_allowed.")
        contra = clean_text(item.get("required_contra_account", ""))
        if contra and not contra.isdigit():
            raise ValueError(f"batch_config.{key}.required_contra_account muss numerisch sein.")


def document_batch_type(document: dict[str, Any]) -> str:
    return clean_text(document.get("batch_type") or STANDARD_BATCH_TYPE)


def validate_live_datev_usage(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    run = data["run"]
    live = run["datev_live_evidence"]
    valid_accounts = set(run.get("_validated_accounts", []))
    valid_bu_keys = set(run.get("_validated_bu_keys", []))
    valid_cost_centers = set(run.get("_validated_cost_centers", []))
    cost_centers_configured = isinstance(run.get("cost_center_config"), dict)
    records = data.get("master_records", [])
    new_accounts: set[str] = set()
    new_account_names: dict[str, str] = {}
    accounts_by_type: dict[str, list[int]] = defaultdict(list)
    seen_master_accounts: set[str] = set()
    forbidden_approval_fields = {
        "approved", "freigegeben", "requires_approval", "approval_required"
    }
    person_length = int(run["sachkontenlaenge"]) + 1
    configured_ranges = run["person_account_ranges"]
    for kind, live_key in (
        ("kreditor", "highest_creditor_account"),
        ("debitor", "highest_debtor_account"),
    ):
        value = live.get(live_key)
        if value not in (None, ""):
            start = int(configured_ranges[kind]["start"])
            end = int(configured_ranges[kind]["end"])
            if not start <= int(value) <= end:
                errors.append(f"{live_key} liegt außerhalb des konfigurierten {kind}-Bereichs")
    for record in records:
        account = str(record.get("account", ""))
        account_type = str(record.get("account_type", "")).strip().lower()
        action = str(record.get("action", ""))
        if action not in {"Neuanlage", "Änderung"}:
            errors.append(f"Stammdatenkonto {account}: ungültige Aktion {action}")
        if account_type not in {"kreditor", "debitor"}:
            errors.append(f"Stammdatenkonto {account}: Typ muss Kreditor oder Debitor sein")
            continue
        if forbidden_approval_fields.intersection(record):
            errors.append(
                f"Stammdatenkonto {account}: Freigabefelder sind unzulässig"
            )
        if account in seen_master_accounts:
            errors.append(f"Doppelter Stammdatensatz für Konto {account}")
        seen_master_accounts.add(account)
        name = str(record.get("name", "")).strip()
        if not name:
            errors.append(f"Stammdatenkonto {account}: Name fehlt")
        elif is_collective_person_account_name(name):
            errors.append(
                f"Stammdatenkonto {account} ({name}) ist ein unzulässiges "
                "Sammel-/CPD-Konto"
            )
        if not account.isdigit() or len(account) != person_length:
            errors.append(
                f"Personenkonto {account}: erwartet werden genau {person_length} Ziffern"
            )
        if action == "Neuanlage":
            new_accounts.add(account)
            new_account_names[account] = name
            if account.isdigit():
                accounts_by_type[account_type].append(int(account))
        elif account not in valid_accounts:
            errors.append(
                f"Änderungskonto {account} ist nicht live in DATEV bestätigt"
            )
    for account_type, values in accounts_by_type.items():
        evidence_key = (
            "highest_creditor_account"
            if account_type == "kreditor"
            else "highest_debtor_account"
        )
        highest = live.get(evidence_key)
        if highest in (None, ""):
            errors.append(
                f"Für neue {account_type.title()}en fehlt {evidence_key}"
            )
            continue
        expected = list(range(int(highest) + 1, int(highest) + 1 + len(values)))
        if sorted(values) != expected:
            errors.append(
                f"Neue {account_type.title()}enkonten müssen lückenlos bei "
                f"{int(highest) + 1} beginnen; erhalten: {sorted(values)}"
            )
    allowed_accounts = valid_accounts | new_accounts
    used_person_accounts = run.get("_used_person_accounts", {})
    for doc in data.get("documents", []):
        tid = str(doc.get("transaction_id", ""))
        for booking in doc.get("bookings", []):
            for field in ("account", "contra_account"):
                account = str(booking.get(field) or "")
                if not account and field in booking.get("open_fields", {}) and doc.get("traffic_light") == "Rot":
                    continue
                if account not in allowed_accounts:
                    errors.append(
                        f"{tid}: {field} {account} ist weder live bestätigt "
                        "noch als Neuanlage enthalten"
                    )
                account_type = person_account_type(account, run)
                if account_type is None:
                    continue
                name_field = (
                    "account_name" if field == "account"
                    else "contra_account_name"
                )
                booking_name = str(booking.get(name_field, "")).strip()
                if is_collective_person_account_name(booking_name):
                    errors.append(
                        f"{tid}: {field} {account} verwendet mit "
                        f"{booking_name} ein unzulässiges Sammel-/CPD-Konto"
                    )
                if account in new_accounts:
                    expected_name = new_account_names.get(account, "")
                else:
                    evidence = used_person_accounts.get(account)
                    if not evidence:
                        errors.append(
                            f"{tid}: verwendetes bestehendes Personenkonto "
                            f"{account} fehlt in datev_live_evidence."
                            "used_person_accounts"
                        )
                        continue
                    expected_name = evidence["name"]
                if (
                    normalized_person_account_name(booking_name)
                    != normalized_person_account_name(expected_name)
                ):
                    errors.append(
                        f"{tid}: {name_field} für Personenkonto {account} "
                        "stimmt nicht mit dem live nachgewiesenen bzw. neu "
                        "angelegten Einzelkonto überein"
                    )
            try:
                key = _normalized_internal_bu_key(booking.get("bu_key", ""))
            except ValueError as exc:
                errors.append(f"{tid}: {exc}")
            else:
                if key and key not in valid_bu_keys:
                    errors.append(
                        f"{tid}: BU-Schlüssel {key} ist nicht live in DATEV bestätigt"
                    )
            kost1 = clean_text(booking.get("kost1", ""))
            if kost1 and cost_centers_configured and kost1 not in valid_cost_centers:
                errors.append(
                    f"{tid}: Kostenstelle {kost1} ist nicht live in DATEV vorhanden; "
                    "nur als Rot mit offenem kost1 und Klärungsfall "
                    "'Kostenstelle in DATEV anlegen' zulässig"
                )
    return errors


def _confirmed_not_found_evidence(
    evidence: Any,
    *,
    expected_url: str,
    expected_name: str,
    label: str,
) -> dict[str, Any]:
    if not isinstance(evidence, dict) or evidence.get("status") != "not_found":
        raise ValueError(f"Abbruch: {label} wurde nicht eindeutig als nicht vorhanden nachgewiesen.")
    required = {
        "source_url", "file_name", "retrieved_via", "checked_at",
        "not_found_code", "site_verified", "library_verified",
        "direct_lookup_attempts",
    }
    missing = sorted(key for key in required if evidence.get(key) in (None, ""))
    if missing:
        raise ValueError(
            f"Abbruch: {label}-not_found-Nachweis unvollständig: "
            + ", ".join(missing)
        )
    if evidence["source_url"] != expected_url or evidence["file_name"] != expected_name:
        raise ValueError(f"Abbruch: {label}-not_found-Nachweis verwendet nicht das verbindliche SharePoint-Ziel.")
    if str(evidence["not_found_code"]).lower() not in {"itemnotfound", "not_found"}:
        raise ValueError(f"Abbruch: {label} wurde nicht als itemNotFound bestätigt.")
    if evidence["site_verified"] is not True or evidence["library_verified"] is not True:
        raise ValueError(f"Abbruch: Site und Bibliothek wurden für {label} nicht bestätigt.")
    attempts = evidence["direct_lookup_attempts"]
    if not isinstance(attempts, int) or attempts < 2:
        raise ValueError(f"Abbruch: {label} muss zweimal direkt als itemNotFound bestätigt sein.")
    try:
        datetime.fromisoformat(str(evidence["checked_at"]).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Abbruch: Abrufzeitpunkt für {label} ist ungültig.") from exc
    return {
        "status": "not_found",
        "source_url": expected_url,
        "file_name": expected_name,
        "retrieved_via": str(evidence["retrieved_via"]),
        "checked_at": str(evidence["checked_at"]),
        "not_found_code": "itemNotFound",
        "site_verified": True,
        "library_verified": True,
        "direct_lookup_attempts": attempts,
    }


def normalize_input_model(data: dict[str, Any]) -> dict[str, Any]:
    """Accept v1.0 input while normalizing the v1.1+ source/transaction model."""
    run = data.setdefault("run", {})
    if not isinstance(data.get("scope"), dict):
        data["scope"] = {
            "target_periods": [str(run.get("buchungsmonat", ""))],
            "include_prior_periods": True,
            "include_future_periods": True,
            "job_mode": JOB_MODE,
            "legacy_default": True,
        }
    if not isinstance(data.get("mandantenprofil"), dict):
        data["mandantenprofil"] = {
            "status": "existing",
            "source_status": "found",
            "approval_status": "approved",
            "evidence": [],
            "legacy_default": True,
        }

    canonical_keys = ("source_files", "transactions", "transaction_sources")
    canonical_present = any(key in data for key in canonical_keys)
    if not canonical_present:
        inventory = data.get("input_inventory", [])
        source_files = []
        path_to_id: dict[str, str] = {}
        for index, item in enumerate(inventory, start=1):
            source_id = str(item.get("source_id") or f"S{index:04d}")
            source_item = dict(item)
            source_item["source_id"] = source_id
            source_item.setdefault("readability", "not_checked")
            source_files.append(source_item)
            path_to_id[str(item.get("source_path", ""))] = source_id
        mappings = []
        for document in data.get("documents", []):
            source_path = str(document.get("source_path", ""))
            source_id = path_to_id.get(source_path)
            if source_id:
                mappings.append({
                    "transaction_id": str(document.get("transaction_id", "")),
                    "source_id": source_id,
                    "role": "payment_notice" if document.get("payment_advice") else "primary_invoice",
                })
        data["source_files"] = source_files
        data["transactions"] = data.get("documents", [])
        data["transaction_sources"] = mappings
        data["_normalized_source_model"] = "legacy"
        return data

    if not all(isinstance(data.get(key), list) for key in canonical_keys):
        raise ValueError(
            "source_files, transactions und transaction_sources müssen gemeinsam als Listen vorliegen."
        )
    sources_by_id: dict[str, dict[str, Any]] = {}
    normalized_inventory: list[dict[str, Any]] = []
    for index, item in enumerate(data["source_files"], start=1):
        if not isinstance(item, dict):
            raise ValueError(f"source_files {index}: Eintrag ist kein Objekt")
        source_id = str(item.get("source_id", "")).strip()
        source_path = str(item.get("source_path", "")).strip()
        if not source_id or source_id in sources_by_id:
            raise ValueError(f"source_files {index}: source_id fehlt oder ist doppelt")
        if not source_path:
            raise ValueError(f"source_files {index}: source_path fehlt")
        normalized = dict(item)
        normalized.setdefault("readability", "not_checked")
        sources_by_id[source_id] = normalized
        normalized_inventory.append(normalized)

    transactions_by_id: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(data["transactions"], start=1):
        if not isinstance(item, dict):
            raise ValueError(f"transactions {index}: Eintrag ist kein Objekt")
        transaction_id = str(item.get("transaction_id", "")).strip()
        if not transaction_id or transaction_id in transactions_by_id:
            raise ValueError(f"transactions {index}: transaction_id fehlt oder ist doppelt")
        transactions_by_id[transaction_id] = dict(item)

    mappings_by_transaction: dict[str, list[dict[str, str]]] = defaultdict(list)
    for index, item in enumerate(data["transaction_sources"], start=1):
        if not isinstance(item, dict):
            raise ValueError(f"transaction_sources {index}: Eintrag ist kein Objekt")
        transaction_id = str(item.get("transaction_id", "")).strip()
        source_id = str(item.get("source_id", "")).strip()
        role = str(item.get("role", "")).strip()
        if transaction_id not in transactions_by_id or source_id not in sources_by_id:
            raise ValueError(f"transaction_sources {index}: unbekannte Vorgangs- oder Quellen-ID")
        if role not in SOURCE_ROLES:
            raise ValueError(f"transaction_sources {index}: ungültige Dokumentrolle {role}")
        mapping = {"transaction_id": transaction_id, "source_id": source_id, "role": role}
        if mapping in mappings_by_transaction[transaction_id]:
            raise ValueError(f"transaction_sources {index}: Zuordnung ist doppelt")
        mappings_by_transaction[transaction_id].append(mapping)

    documents: list[dict[str, Any]] = []
    for transaction_id, document in transactions_by_id.items():
        mappings = mappings_by_transaction.get(transaction_id, [])
        if not mappings:
            raise ValueError(f"{transaction_id}: keine Quelldatei zugeordnet")
        primary = next((item for item in mappings if item["role"] == "primary_invoice"), mappings[0])
        document["source_path"] = sources_by_id[primary["source_id"]]["source_path"]
        document["source_paths"] = [sources_by_id[item["source_id"]]["source_path"] for item in mappings]
        document["source_roles"] = mappings
        documents.append(document)

    data["documents"] = documents
    data["input_inventory"] = normalized_inventory
    data["_normalized_source_model"] = "canonical"
    return data


def validate_profile_contract(data: dict[str, Any]) -> None:
    run = data["run"]
    profile = data.get("mandantenprofil")
    if not isinstance(profile, dict):
        raise ValueError("Mandantenprofil-Vertrag fehlt.")
    status = profile.get("status")
    source_status = profile.get("source_status")
    approval_status = profile.get("approval_status")
    if not isinstance(profile.get("evidence"), list):
        raise ValueError("mandantenprofil.evidence muss eine Liste sein.")
    if status == "existing":
        if source_status != "found" or approval_status != "approved":
            raise ValueError("Vorhandenes Mandantenprofil muss gefunden und freigegeben sein.")
        if run.get("mandantenprofil_verified") is not True:
            raise ValueError("Abbruch: Mandantenprofil ist nicht eindeutig bestätigt.")
        return
    if status != "provisional_first_run":
        raise ValueError("mandantenprofil.status ist ungültig.")
    if source_status != "confirmed_not_found" or approval_status != "pending":
        raise ValueError("Vorläufiges Erstlaufprofil erfordert confirmed_not_found und pending.")
    if run.get("provisional_profile_verified") is not True:
        raise ValueError("Abbruch: vorläufiges Erstlaufprofil ist nicht verifiziert.")
    provisional = data.get("provisional_profile")
    if not isinstance(provisional, dict):
        raise ValueError("Vollständiges vorläufiges Mandantenprofil fehlt.")
    if not str(provisional.get("content_markdown", "")).strip():
        raise ValueError("Vorläufiges Mandantenprofil enthält keinen vollständigen Markdown-Inhalt.")
    if not isinstance(provisional.get("sources"), list) or not provisional["sources"]:
        raise ValueError("Vorläufiges Mandantenprofil enthält keine Quellen.")
    if provisional.get("sharepoint_write_approved") is not False:
        raise ValueError("Vorläufiges Mandantenprofil darf vor Freigabe nicht nach SharePoint geschrieben werden.")

def _canonical_month(value: Any) -> str | None:
    text = str(value or "")
    try:
        parsed = datetime.strptime(text, "%Y-%m")
    except ValueError:
        return None
    return text if parsed.strftime("%Y-%m") == text else None


def validate_scope(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    scope = data.get("scope")
    if not isinstance(scope, dict):
        return ["scope fehlt oder ist kein Objekt"]
    if scope.get("job_mode") != JOB_MODE:
        errors.append(
            "scope.job_mode muss belegbuchhaltung sein; Kasse, Bank, Lohn und sonstige Teilaufträge sind ausgeschlossen"
        )
    periods = scope.get("target_periods")
    if not isinstance(periods, list) or not periods:
        errors.append("scope.target_periods fehlt oder ist leer")
        return errors
    if len(set(map(str, periods))) != len(periods):
        errors.append("scope.target_periods enthält doppelte Perioden")
    canonical = [str(value) for value in periods if _canonical_month(value)]
    if len(canonical) != len(periods):
        errors.append("scope.target_periods enthält eine ungültige Periode")
        return errors
    for flag in ("include_prior_periods", "include_future_periods"):
        if not isinstance(scope.get(flag), bool):
            errors.append(f"scope.{flag} muss true oder false sein")
    if errors:
        return errors
    first_period = min(canonical)
    last_period = max(canonical)
    allowed = set(canonical)
    for document in data.get("documents", []):
        transaction_id = str(document.get("transaction_id", ""))
        period = str(document.get("period", ""))
        in_scope = period in allowed
        if period < first_period and scope["include_prior_periods"]:
            in_scope = True
        if period > last_period and scope["include_future_periods"]:
            in_scope = True
        status = document.get("processing_status")
        if not in_scope and status != "außerhalb Auftragszeitraum":
            errors.append(
                f"{transaction_id}: Periode {period} liegt außerhalb des Auftragszeitraums und muss ausgeschlossen werden"
            )
        if in_scope and status == "außerhalb Auftragszeitraum":
            errors.append(f"{transaction_id}: zulässige Zielperiode ist fälschlich ausgeschlossen")
    return errors


def validate_payment_reconciliation(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    value = data.get("payment_reconciliation")
    if value in (None, []):
        items: list[Any] = []
    elif isinstance(value, dict):
        items = [value]
    elif isinstance(value, list):
        items = value
    else:
        return ["payment_reconciliation muss ein Objekt oder eine Liste sein"]
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            errors.append(f"payment_reconciliation {index}: Eintrag ist kein Objekt")
            continue
        if item.get("status") not in {"present", "missing", "not_expected", "not_checked"}:
            errors.append(f"payment_reconciliation {index}: status ist ungültig")
        if item.get("affects_document_traffic_light") is not False:
            errors.append(
                f"payment_reconciliation {index}: affects_document_traffic_light muss false sein"
            )
        periods = item.get("periods")
        if not isinstance(periods, list) or any(_canonical_month(value) is None for value in periods):
            errors.append(f"payment_reconciliation {index}: periods ist ungültig")
        if not isinstance(item.get("handoff_required"), bool):
            errors.append(f"payment_reconciliation {index}: handoff_required muss boolesch sein")
    payment_terms = (
        "kontoauszug", "kreditkartenabrechnung", "zahlungsnachweis",
        "kartenumsatz", "kursdifferenz", "zahlungsabstimmung",
    )
    substantive_terms = (
        "kontierung", "betrag", "geschäftspartner", "periode",
        "umsatzsteuer", "vorsteuer", "betrieblicher anlass", "anlage", "dublette",
    )
    for document in data.get("documents", []):
        if document.get("traffic_light") != "Rot":
            continue
        reason = str(document.get("reason", "")).casefold()
        if any(term in reason for term in payment_terms) and not any(
            term in reason for term in substantive_terms
        ):
            errors.append(
                f"{document.get('transaction_id', '')}: Rot darf nicht ausschließlich mit fehlender Zahlungs- oder Kartenabstimmung begründet werden"
            )
    return errors

def validate_activity_and_handoffs(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    canonical = data.get("_normalized_source_model") == "canonical"
    report = data.get("activity_report")
    if report is None and not canonical:
        report = {
            "datev_import_status": "Importpaket erstellt – noch nicht in DATEV importiert",
            "named_entities": [],
            "sources_used": [],
            "legacy_default": True,
        }
        data["activity_report"] = report
    if not isinstance(report, dict):
        errors.append("activity_report fehlt oder ist kein Objekt")
        report = {}
    import_status = report.get("datev_import_status")
    allowed_status = {
        "Importpaket erstellt – noch nicht in DATEV importiert",
        "in DATEV importiert",
    }
    if import_status not in allowed_status:
        errors.append("activity_report.datev_import_status ist ungültig")
    if import_status == "in DATEV importiert" and not isinstance(
        report.get("import_evidence"), dict
    ):
        errors.append("Status 'in DATEV importiert' erfordert einen Importnachweis")
    entities = report.get("named_entities")
    if not isinstance(entities, list):
        errors.append("activity_report.named_entities muss eine Liste sein")
        entities = []
    found_names: set[str] = set()
    for index, item in enumerate(entities, start=1):
        if not isinstance(item, dict):
            errors.append(f"activity_report.named_entities {index}: Eintrag ist kein Objekt")
            continue
        name = str(item.get("name", "")).strip()
        if not name or not str(item.get("final_status", "")).strip():
            errors.append(f"activity_report.named_entities {index}: Name oder Endstatus fehlt")
        if not isinstance(item.get("variants", []), list):
            errors.append(f"activity_report.named_entities {index}: variants muss eine Liste sein")
        if not isinstance(item.get("findings"), int) or item.get("findings", -1) < 0:
            errors.append(f"activity_report.named_entities {index}: findings ist ungültig")
        found_names.add(name.casefold())
    for requested in data.get("run", {}).get("requested_entities", []):
        if str(requested).casefold() not in found_names:
            errors.append(f"Angefragte Person/Geschäftspartner ohne Such- und Endstatus: {requested}")
    if canonical and (
        not isinstance(report.get("sources_used"), list)
        or not report.get("sources_used")
    ):
        errors.append("activity_report.sources_used fehlt oder ist leer")

    handoffs = data.get("handoffs", [])
    if not isinstance(handoffs, list):
        return errors + ["handoffs muss eine Liste sein"]
    covered_transactions: set[str] = set()
    for index, item in enumerate(handoffs, start=1):
        if not isinstance(item, dict):
            errors.append(f"handoffs {index}: Eintrag ist kein Objekt")
            continue
        source_ids = item.get("source_ids", [])
        transaction_ids = item.get("transaction_ids", [])
        if not isinstance(source_ids, list) or not isinstance(transaction_ids, list):
            errors.append(f"handoffs {index}: source_ids/transaction_ids müssen Listen sein")
        if not source_ids and not transaction_ids:
            errors.append(f"handoffs {index}: Quelle oder Vorgang fehlt")
        if _canonical_month(item.get("period")) is None:
            errors.append(f"handoffs {index}: Periode ist ungültig")
        if not str(item.get("target_process", "")).strip() or not str(item.get("reason", "")).strip():
            errors.append(f"handoffs {index}: Zielprozess oder Grund fehlt")
        covered_transactions.update(str(value) for value in transaction_ids)
    for document in data.get("documents", []):
        if document.get("handoff_required") is True:
            transaction_id = str(document.get("transaction_id", ""))
            if transaction_id not in covered_transactions:
                errors.append(f"{transaction_id}: erforderliche Übergabe fehlt in handoffs")
    return errors

def load_input(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        raw_data = json.load(handle)
    parallel_review = raw_data.get("_parallel_review")
    if (
        isinstance(parallel_review, dict)
        and parallel_review.get("global_reconciliation_required") is not False
    ):
        raise ValueError(
            "Parallelentwurf ist nicht global konsolidiert; "
            "Paketbau erst nach global_reconciliation_required=false zulässig."
        )
    if (
        isinstance(parallel_review, dict)
        and raw_data.get("person_account_proposals")
    ):
        raise ValueError(
            "Personenkontenvorschläge sind noch nicht final konsolidiert; "
            "vor dem Paketbau in vollständige master_records überführen oder verwerfen."
        )
    data = normalize_input_model(raw_data)
    run = data.get("run", {})
    required = [
        "beraternummer", "mandantennummer", "buchungsmonat",
        "wirtschaftsjahr_beginn", "sachkontenlaenge", "sachkontenrahmen",
    ]
    missing = [key for key in required if run.get(key) in (None, "")]
    if missing:
        raise ValueError(f"Fehlende Laufdaten: {', '.join(missing)}")
    if run.get("datev_connection_verified") is not True:
        raise ValueError("Abbruch: DATEV-Kerndatenverbindung ist nicht bestätigt.")
    validate_profile_contract(data)
    scope_errors = validate_scope(data)
    scope_errors.extend(validate_payment_reconciliation(data))
    scope_errors.extend(validate_activity_and_handoffs(data))
    if scope_errors:
        raise ValueError("\n".join(scope_errors))
    validate_run_values(run)
    validate_preflight_evidence(data)
    live_errors = validate_live_datev_usage(data)
    if live_errors:
        raise ValueError("\n".join(live_errors))
    validate_accrual_thresholds(data)
    return data


def source_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()



def validate_input_inventory(data: dict[str, Any]) -> list[str]:
    """Validate source files independently from their logical transactions."""
    errors: list[str] = []
    inventory = data.get("input_inventory")
    if not isinstance(inventory, list):
        return ["input_inventory/source_files fehlt oder ist keine Liste"]
    if not inventory:
        return ["source_files ist leer; ein Beleglauf ohne Eingabedateien ist unzulässig"]
    canonical = data.get("_normalized_source_model") == "canonical"
    inventory_paths: dict[str, str] = {}
    hash_sources: dict[str, list[str]] = defaultdict(list)
    for index, item in enumerate(inventory, start=1):
        if not isinstance(item, dict):
            errors.append(f"source_files {index}: Eintrag ist kein Objekt")
            continue
        source_id = str(item.get("source_id", f"S{index:04d}"))
        raw_path = str(item.get("source_path", "")).strip()
        if canonical and not str(item.get("source_id", "")).strip():
            errors.append(f"source_files {index}: source_id fehlt")
        if not raw_path:
            errors.append(f"source_files {index}: source_path fehlt")
            continue
        source = Path(raw_path)
        normalized = str(source.resolve()).casefold()
        if normalized in inventory_paths:
            errors.append(f"source_files: Datei mehrfach enthalten: {raw_path}")
            continue
        inventory_paths[normalized] = raw_path
        if item.get("readability") not in {
            "readable", "partially_readable", "unreadable", "not_checked"
        }:
            errors.append(f"source_files {source_id}: readability ist ungültig")
        if not source.is_file():
            errors.append(f"source_files: Datei fehlt: {raw_path}")
            continue
        if item.get("size_bytes") != source.stat().st_size:
            errors.append(f"source_files: Dateigröße stimmt nicht: {raw_path}")
        expected_hash = str(item.get("sha256", "")).lower()
        if not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
            errors.append(f"source_files: ungültiger SHA-256: {raw_path}")
        elif source_hash(source) != expected_hash:
            errors.append(f"source_files: SHA-256 stimmt nicht: {raw_path}")
        else:
            hash_sources[expected_hash].append(source_id)

    referenced_paths: dict[str, str] = {}
    for document in data.get("documents", []):
        paths = document.get("source_paths") or [document.get("source_path", "")]
        for raw in paths:
            raw_path = str(raw).strip()
            if not raw_path:
                continue
            referenced_paths[str(Path(raw_path).resolve()).casefold()] = raw_path
    missing_transactions = sorted(set(inventory_paths) - set(referenced_paths))
    extra_sources = sorted(set(referenced_paths) - set(inventory_paths))
    if missing_transactions:
        errors.append(
            "Inventarisierte Quelldateien sind keinem Vorgang zugeordnet: "
            + ", ".join(inventory_paths[path] for path in missing_transactions)
        )
    if extra_sources:
        errors.append(
            "Vorgänge referenzieren nicht inventarisierte Quelldateien: "
            + ", ".join(referenced_paths[path] for path in extra_sources)
        )

    if canonical:
        mappings = data.get("transaction_sources", [])
        for digest, source_ids in hash_sources.items():
            if len(source_ids) < 2:
                continue
            for duplicate_id in source_ids[1:]:
                roles = {
                    str(item.get("role", ""))
                    for item in mappings
                    if str(item.get("source_id", "")) == duplicate_id
                }
                if roles != {"duplicate_copy"}:
                    errors.append(
                        f"source_files {duplicate_id}: gleicher SHA-256 wie {source_ids[0]}, aber nicht ausschließlich als duplicate_copy gekennzeichnet"
                    )
    return errors



def validate_documents(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_sources: set[str] = set()
    run = data["run"]
    vat = run["vat_config"]
    accounts = run["account_config"]
    configured_asset_accounts = {
        str(value) for value in accounts["asset_accounts"]
    }
    clarification_counts = Counter(
        str(transaction_id)
        for case in data.get("clarification_cases", [])
        for transaction_id in case.get("transaction_ids", [])
    )
    separate_batches = (run.get("batch_config") or {}).get("separate_batches") or {}
    for index, doc in enumerate(data.get("documents", []), start=1):
        tid = str(doc.get("transaction_id", f"Zeile {index}"))
        if tid in seen_ids:
            errors.append(f"Doppelte Vorgangs-ID: {tid}")
        seen_ids.add(tid)
        batch_type = document_batch_type(doc)
        if batch_type != STANDARD_BATCH_TYPE:
            batch_rule = separate_batches.get(batch_type)
            if not isinstance(batch_rule, dict):
                errors.append(
                    f"{tid}: batch_type {batch_type} ohne entsprechende batch_config.separate_batches"
                )
            elif doc.get("processing_status") == "Buchungszeile erzeugt":
                required_kost1 = clean_text(batch_rule.get("required_kost1", ""))
                required_contra = clean_text(batch_rule.get("required_contra_account", ""))
                for line_no, booking in enumerate(doc.get("bookings", []), start=1):
                    if required_kost1 and clean_text(booking.get("kost1", "")) != required_kost1:
                        errors.append(
                            f"{tid}, Zeile {line_no}: Stapeltyp {batch_type} verlangt KOST1 {required_kost1}"
                        )
                    if required_contra and clean_text(booking.get("contra_account", "")) != required_contra:
                        errors.append(
                            f"{tid}, Zeile {line_no}: Stapeltyp {batch_type} verlangt Gegenkonto {required_contra}"
                        )
        source_paths = doc.get("source_paths") or [doc.get("source_path", "")]
        if not any(str(path).strip() for path in source_paths):
            errors.append(f"{tid}: keine Quelldatei zugeordnet")

        if doc.get("business_purpose_status") not in {"betrieblich", "privat", "unklar"}:
            errors.append(f"{tid}: betrieblicher Anlass ist nicht klassifiziert")
        if data.get("_normalized_source_model") == "canonical":
            if not str(doc.get("document_type", "")).strip():
                errors.append(f"{tid}: Dokumentart fehlt")
            entity = doc.get("entity_assessment")
            if not isinstance(entity, dict):
                errors.append(f"{tid}: Rechtsträger-/Adressatenprüfung fehlt")
            else:
                for field in ("legal_entity", "addressee", "relevance"):
                    if not str(entity.get(field, "")).strip():
                        errors.append(f"{tid}: entity_assessment.{field} fehlt")
            if doc.get("processing_status") != "Buchungszeile erzeugt":
                if not str(doc.get("exclusion_reason", "")).strip():
                    errors.append(f"{tid}: konkreter Ausschlussgrund fehlt")
            if doc.get("processing_status") in {
                "Buchungszeile erzeugt",
                "sichere Dublette – nicht erneut gebucht",
            }:
                duplicate_checks = doc.get("duplicate_checks")
                if not isinstance(duplicate_checks, dict):
                    errors.append(f"{tid}: dreistufige Dublettenprüfung fehlt")
                else:
                    for level in (
                        "file_hash_current_upload",
                        "logical_document_current_upload",
                        "datev_live",
                    ):
                        check = duplicate_checks.get(level)
                        if not isinstance(check, dict) or check.get("checked") is not True:
                            errors.append(f"{tid}: Dublettenprüfung {level} fehlt")
                        elif check.get("result") not in {
                            "no_hit", "possible_duplicate", "secure_duplicate"
                        }:
                            errors.append(f"{tid}: Dublettenprüfung {level} hat ungültiges Ergebnis")
                        elif check.get("result") != "no_hit" and not str(check.get("reference", "")).strip():
                            errors.append(f"{tid}: Dublettentreffer {level} enthält keine Referenz")
        try:
            period_valid = datetime.strptime(str(doc.get("period", "")), "%Y-%m").strftime("%Y-%m") == str(doc.get("period", ""))
        except ValueError:
            period_valid = False
        if not period_valid:
            errors.append(f"{tid}: ungültige oder fehlende Belegperiode")
        recognized_date = doc.get("recognized_date")
        if recognized_date:
            try:
                parsed_date = datetime.strptime(str(recognized_date), "%Y-%m-%d")
            except ValueError:
                errors.append(f"{tid}: ungültiges erkanntes Belegdatum")
            else:
                if period_valid and parsed_date.strftime("%Y-%m") != doc.get("period"):
                    errors.append(f"{tid}: Belegperiode stimmt nicht mit Belegdatum überein")
        elif doc.get("processing_status") == "Buchungszeile erzeugt" and doc.get("traffic_light") != "Rot":
            errors.append(f"{tid}: fehlendes Belegdatum erfordert Ampel Rot")

        if not str(doc.get("derivation", "")).strip():
            errors.append(f"{tid}: nachvollziehbare Ableitung der Buchung/Behandlung fehlt")
        if doc.get("processing_status") == "Buchungszeile erzeugt" and not str(doc.get("reason", "")).strip():
            errors.append(f"{tid}: Ampelbegründung fehlt")
        if data.get("_normalized_source_model") == "canonical":
            errors.extend(f"{tid}: {issue}" for issue in plain_language_issues(
                doc.get("document_summary"), "Beleg zeigt (document_summary)", min_length=30))
            errors.extend(f"{tid}: {issue}" for issue in plain_language_issues(
                doc.get("derivation"), "Daraus folgt (derivation)"))
            errors.extend(f"{tid}: {issue}" for issue in plain_language_issues(
                doc.get("exclusion_reason"), "Ausschlussgrund"))
            if doc.get("processing_status") == "Buchungszeile erzeugt":
                errors.extend(f"{tid}: {issue}" for issue in plain_language_issues(
                    doc.get("reason"), "Warum Rot oder Grün (reason)", min_length=30, reject_generic=True))
            if doc.get("traffic_light") == "Rot":
                errors.extend(f"{tid}: {issue}" for issue in single_task_issues(doc.get("next_step")))
                errors.extend(f"{tid}: {issue}" for issue in missing_mapping_issues(doc.get("reason"), "Warum Rot (reason)"))
                for line_no, booking in enumerate(doc.get("bookings", []), start=1):
                    for field, text in (booking.get("open_fields") or {}).items() if isinstance(booking.get("open_fields"), dict) else []:
                        errors.extend(f"{tid}, Zeile {line_no}: {issue}" for issue in missing_mapping_issues(text, f"Begründung offenes Feld {field}"))
            elif str(doc.get("next_step", "") or "").strip():
                errors.extend(f"{tid}: {issue}" for issue in plain_language_issues(doc.get("next_step"), "Nächster Schritt"))
            for line_no, booking in enumerate(doc.get("bookings", []), start=1):
                opened = booking.get("open_fields") or {}
                if isinstance(opened, dict):
                    for field, text in opened.items():
                        errors.extend(
                            f"{tid}, Zeile {line_no}: {issue}" for issue in
                            plain_language_issues(text, f"Begründung offenes Feld {field}", min_length=20)
                        )
        if doc.get("processing_status") not in VALID_STATUSES:
            errors.append(f"{tid}: ungültiger Verarbeitungsstatus")
        if doc.get("processing_status") == "Buchungszeile erzeugt":
            if doc.get("traffic_light") not in VALID_LIGHTS:
                errors.append(f"{tid}: ungültige Ampel")
        elif doc.get("traffic_light") not in (None, ""):
            errors.append(f"{tid}: nicht gebuchte Datei darf keine Ampel tragen")

        is_advice = bool(doc.get("payment_advice"))
        if is_advice:
            if doc.get("processing_status") != "nicht buchungsrelevant":
                errors.append(f"{tid}: Zahlungsavis muss nicht buchungsrelevant sein")
            if doc.get("bookings"):
                errors.append(f"{tid}: Zahlungsavis darf keine Buchungen enthalten")
        elif doc.get("processing_status") in {
            "Buchungszeile erzeugt",
            "sichere Dublette – nicht erneut gebucht",
        }:
            prior = doc.get("prior_booking_check")
            if not isinstance(prior, dict) or prior.get("checked") is not True:
                errors.append(f"{tid}: DATEV-Dublettenprüfung fehlt")
            else:
                result = prior.get("result")
                if result not in {"kein_treffer", "moegliche_dublette", "sichere_dublette"}:
                    errors.append(f"{tid}: Ergebnis der DATEV-Dublettenprüfung ist ungültig")
                if result == "sichere_dublette" and doc.get("processing_status") != "sichere Dublette – nicht erneut gebucht":
                    errors.append(f"{tid}: sichere Dublette darf nicht erneut gebucht werden")
                if result == "moegliche_dublette" and (
                    doc.get("processing_status") != "Buchungszeile erzeugt"
                    or doc.get("traffic_light") != "Rot"
                ):
                    errors.append(f"{tid}: mögliche Dublette muss als roter Klärungsposten gebucht werden")

        if doc.get("processing_status") == "Buchungszeile erzeugt" and not doc.get("bookings"):
            errors.append(f"{tid}: buchungsrelevanter Beleg ohne Buchungszeile")
        if doc.get("processing_status") != "Buchungszeile erzeugt" and doc.get("bookings"):
            errors.append(f"{tid}: Status und vorhandene Buchungen widersprechen sich")

        if doc.get("processing_status") == "Buchungszeile erzeugt":
            if doc.get("traffic_light") == "Rot":
                if doc.get("requires_clarification") is not True:
                    errors.append(f"{tid}: Rot erfordert requires_clarification=true")
                if clarification_counts.get(tid, 0) != 1:
                    errors.append(f"{tid}: Rot muss genau einem Klärungsfall zugeordnet sein")
            if doc.get("traffic_light") == "Grün" and (
                doc.get("requires_clarification") is True or clarification_counts.get(tid, 0)
            ):
                errors.append(f"{tid}: Grün darf keinen Klärfall enthalten")

            if doc.get("business_purpose_status") == "privat":
                for booking in doc.get("bookings", []):
                    used = {str(booking.get("account", "")), str(booking.get("contra_account", ""))}
                    if str(accounts["private_expense"]) not in used:
                        errors.append(f"{tid}: private Ausgabe ist nicht auf das konfigurierte Privatkonto gebucht")
                    if str(booking.get("bu_key", "")).strip():
                        errors.append(f"{tid}: private Ausgabe darf keinen BU-Schlüssel haben")

            treatment = doc.get("input_tax_treatment")
            if treatment not in {"volle_vorsteuer", "keine_vorsteuer", "anteilige_vorsteuer", "sonderfall"}:
                errors.append(f"{tid}: input_tax_treatment fehlt oder ist ungültig")
            used_bu = [
                str(item.get("bu_key", "")).strip()
                for item in doc.get("bookings", [])
                if str(item.get("bu_key", "")).strip()
            ]
            if treatment == "keine_vorsteuer" and used_bu:
                errors.append(f"{tid}: keine Vorsteuer erlaubt, BU-Schlüssel muss leer bleiben")
            if vat["input_tax_deduction"] == "keiner" and treatment in {"volle_vorsteuer", "anteilige_vorsteuer"}:
                errors.append(f"{tid}: Mandant hat keinen Vorsteuerabzug")
            if treatment == "anteilige_vorsteuer":
                try:
                    rate = Decimal(str(doc.get("input_tax_rate")))
                except (InvalidOperation, TypeError):
                    errors.append(f"{tid}: Anteil des Vorsteuerabzugs fehlt")
                else:
                    if not Decimal("0") < rate < Decimal("100"):
                        errors.append(f"{tid}: Vorsteueranteil muss zwischen 0 und 100 liegen")

            hospitality = doc.get("hospitality")
            if isinstance(hospitality, dict) and hospitality.get("detected") is True:
                status = hospitality.get("status")
                if status not in {"vollstaendig", "klaerung", "privat"}:
                    errors.append(f"{tid}: Bewirtungsstatus ist ungültig")
                if status == "vollstaendig":
                    required = ("machine_receipt_complete", "hospitality_record_complete", "participants_present", "business_occasion_present")
                    if not all(hospitality.get(key) is True for key in required):
                        errors.append(f"{tid}: Bewirtungsnachweis ist nicht vollständig")
                    expected = {
                        str(accounts.get("hospitality_deductible", "")),
                        str(accounts.get("hospitality_nondeductible", "")),
                    } - {""}
                    used_accounts = {
                        str(value)
                        for booking in doc.get("bookings", [])
                        for value in (booking.get("account"), booking.get("contra_account"))
                    }
                    if len(expected) != 2 or not expected.issubset(used_accounts):
                        errors.append(f"{tid}: vollständige Bewirtung ist nicht auf 70/30-Konten aufgeteilt")
                elif status == "klaerung":
                    if doc.get("traffic_light") != "Rot":
                        errors.append(f"{tid}: unvollständiger Bewirtungsbeleg muss Rot sein")
                    if not any(item.get("open_fields") for item in doc.get("bookings", [])):
                        errors.append(f"{tid}: unvollständige Bewirtung erfordert konkret dokumentierte offene Buchungsfelder")

            for booking in doc.get("bookings", []):
                try:
                    validate_open_fields(doc, booking, run)
                    booking_row(doc, booking, run)
                except ValueError as exc:
                    errors.append(f"{tid}: {exc}")
            all_amounts_known = all(item.get("amount") not in (None, "") for item in doc.get("bookings", []))
            if doc.get("total_amount") not in (None, "") and all_amounts_known:
                try:
                    total = parse_decimal_amount(doc["total_amount"])
                    booking_total = sum(parse_decimal_amount(item["amount"]) for item in doc.get("bookings", []))
                    if total <= 0 or booking_total != total:
                        errors.append(f"{tid}: Summe der Buchungszeilen stimmt nicht mit Gesamtbetrag überein")
                except (ValueError, TypeError):
                    errors.append(f"{tid}: Gesamt- oder Buchungsbetrag ist ungültig")
            elif doc.get("traffic_light") != "Rot":
                errors.append(f"{tid}: fehlender Gesamt- oder Buchungsbetrag erfordert Rot")
            elif doc.get("total_amount") in (None, "") and all_amounts_known:
                errors.append(f"{tid}: fehlender Gesamtbetrag bei vollständig gefüllten Buchungsbeträgen ist widersprüchlich")

        used_asset_accounts = {
            account
            for item in doc.get("bookings", [])
            for account in (
                str(item.get("account", "")),
                str(item.get("contra_account", "")),
            )
            if account in configured_asset_accounts
        }
        if used_asset_accounts:
            errors.append(f"{tid}: Anlagenkonto darf nicht unmittelbar exportiert werden; Anlagenvorerfassung erforderlich")
    return errors


def validate_accrual_source_documents(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    documents = {
        str(doc.get("transaction_id")): doc
        for doc in data.get("documents", [])
        if doc.get("transaction_id")
    }
    current_period = str(data.get("run", {}).get("buchungsmonat", ""))
    release_periods = {
        (str(item.get("accrual_id")), str(item.get("period")))
        for item in data.get("accrual_releases", [])
        if item.get("accrual_id") and item.get("period")
    }

    def validate_links(item: dict[str, Any], *, require_accrual_account: bool) -> None:
        accrual_id = str(item.get("accrual_id") or "ohne Abgrenzungs-ID")
        transaction_ids = item.get("transaction_ids")
        if not isinstance(transaction_ids, list) or not transaction_ids:
            errors.append(
                f"{accrual_id}: neue Abgrenzung ohne verknüpfte Vorgangs-ID"
            )
            return
        for transaction_id in transaction_ids:
            tid = str(transaction_id)
            document = documents.get(tid)
            if document is None:
                errors.append(
                    f"{accrual_id}: verknüpfter Rechnungsbeleg {tid} fehlt"
                )
                continue
            if document.get("processing_status") != "Buchungszeile erzeugt":
                errors.append(
                    f"{accrual_id}/{tid}: Abgrenzungsrechnung ist nicht als "
                    "buchungsrelevant gekennzeichnet"
                )
                continue
            bookings = document.get("bookings")
            if not isinstance(bookings, list) or not bookings:
                errors.append(
                    f"{accrual_id}/{tid}: Abgrenzungsrechnung besitzt keine "
                    "Rechnungsbuchungszeile"
                )
                continue
            accrual_account = str(item.get("accrual_account") or "")
            if require_accrual_account and accrual_account:
                accounts = {
                    str(value)
                    for booking in bookings
                    for value in (
                        booking.get("account"),
                        booking.get("contra_account"),
                    )
                    if value not in (None, "")
                }
                if accrual_account not in accounts:
                    errors.append(
                        f"{accrual_id}/{tid}: Ursprungsrechnung ist nicht auf "
                        f"das Abgrenzungskonto {accrual_account} gebucht"
                    )

    for item in data.get("accrual_register", []):
        source = item.get("source")
        if source not in {"current_run", "carried_forward"}:
            errors.append(
                f"{item.get('accrual_id', 'ohne Abgrenzungs-ID')}: "
                "source muss current_run oder carried_forward sein"
            )
            continue
        if source == "current_run":
            validate_links(item, require_accrual_account=True)
            accrual_id = str(item.get("accrual_id") or "")
            service_start = str(item.get("service_start") or "")
            try:
                service_start_date = datetime.strptime(
                    service_start, "%Y-%m-%d"
                )
            except ValueError:
                errors.append(
                    f"{accrual_id}: service_start fehlt oder ist ungültig"
                )
                continue
            first_release_period = max(
                current_period, service_start_date.strftime("%Y-%m")
            )
            if (
                accrual_id
                and (accrual_id, first_release_period) not in release_periods
            ):
                errors.append(
                    f"{accrual_id}: erste Auflösungsbuchung für "
                    f"{first_release_period} fehlt"
                )

    for item in data.get("accrual_candidates", []):
        validate_links(item, require_accrual_account=False)

    return errors


def validate_clarifications(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    documents = {doc.get("transaction_id"): doc for doc in data.get("documents", [])}
    covered: set[str] = set()
    seen_cases: set[str] = set()
    required = {
        "case_id", "transaction_ids", "topic", "facts",
        "provisional_treatment", "recommendation", "decision_needed",
        "traffic_light", "target", "proposed_change", "employee_result",
    }
    for case in data.get("clarification_cases", []):
        case_id = case.get("case_id", "ohne Klärfall-ID")
        if case_id in seen_cases:
            errors.append(f"Doppelte Klärfall-ID: {case_id}")
        seen_cases.add(case_id)
        missing = [key for key in required if key not in case]
        if missing:
            errors.append(f"{case_id}: fehlende Klärungsfelder: {', '.join(missing)}")
        if case.get("traffic_light") != "Rot":
            errors.append(f"{case_id}: Klärungsfall muss Rot sein")
        if not str(case.get("booking_risk", "")).strip():
            errors.append(f"{case_id}: konkretes Buchungsrisiko (booking_risk) fehlt")
        if data.get("_normalized_source_model") == "canonical":
            for key, label in (
                ("topic", "Thema"), ("facts", "Tatsachen"), ("booking_risk", "Buchungsrisiko"),
                ("provisional_treatment", "Provisorische Behandlung"), ("recommendation", "Empfehlung"),
                ("decision_needed", "Entscheidung"), ("proposed_change", "Vorgeschlagene Änderung"),
            ):
                errors.extend(f"{case_id}: {issue}" for issue in plain_language_issues(case.get(key), label))
            for key, label in (("facts", "Tatsachen"), ("booking_risk", "Buchungsrisiko")):
                errors.extend(f"{case_id}: {issue}" for issue in missing_mapping_issues(case.get(key), label))
        transaction_ids = case.get("transaction_ids", [])
        if not isinstance(transaction_ids, list) or not transaction_ids:
            errors.append(f"{case_id}: transaction_ids muss eine nicht leere Liste sein")
            continue
        for tid in transaction_ids:
            if tid not in documents:
                errors.append(f"{case_id}: unbekannte Vorgangs-ID {tid}")
            covered.add(tid)
    coverage_counts = Counter(
        str(tid)
        for case in data.get("clarification_cases", [])
        for tid in case.get("transaction_ids", [])
    )
    for tid, doc in documents.items():
        if doc.get("requires_clarification") is True and coverage_counts.get(str(tid), 0) != 1:
            errors.append(
                f"{tid}: Klärungsbedarf muss genau einem Klärfall zugeordnet sein"
            )
    for case in data.get("clarification_cases", []):
        if case.get("employee_result") not in ("", None):
            errors.append(
                f"{case.get('case_id', 'ohne Klärfall-ID')}: "
                "employee_result muss bei Erstellung leer sein"
            )
    return errors
def prepare_output(base: Path, run: dict[str, Any]) -> Path:
    root = base / f"{run['mandantennummer']}_{run['buchungsmonat']}"
    if root.exists() and any(root.iterdir()):
        raise ValueError(f"Zielordner ist nicht leer: {root}")
    root.mkdir(parents=True, exist_ok=True)
    for folder in FOLDERS.values():
        (root / folder).mkdir(exist_ok=True)
    return root


def _assign_carry_parts(
    entries: list[dict[str, Any]], kind: str, group_label: str
) -> tuple[list[list[dict[str, Any]]], list[str]]:
    """Sort rows so that empty endangered fields precede filled ones; split only when unavoidable.

    A valid single order exists exactly when the sets of empty endangered
    fields form a chain under inclusion. Sorting by the number of empty fields
    (descending) then yields that order. Otherwise rows are distributed greedily
    onto further files (``_02``, ``_03`` ...); only the clarification batch may
    be split.
    """
    entries.sort(key=lambda item: carry_sort_key(item["row"], item["transaction_id"], item["line"]))
    violations = carry_order_violations([item["row"] for item in entries])
    if not violations:
        return [entries], []
    if kind != BATCH_KIND_CLARIFICATION:
        raise ValueError(
            f"{group_label}: Sortierregel gegen das Schleppen leerer Felder im Buchungsstapel "
            "nicht erfüllbar: " + "; ".join(violations)
        )
    parts: list[list[dict[str, Any]]] = []
    for item in entries:
        empty = carry_empty_fields(item["row"])
        for part in parts:
            if empty <= carry_empty_fields(part[-1]["row"]):
                part.append(item)
                break
        else:
            parts.append([item])
    reasons = [
        f"{group_label}: Sortierregel ohne Teilung nicht erfüllbar ({'; '.join(violations[:3])}"
        f"{'; …' if len(violations) > 3 else ''}); Klärungsstapel in {len(parts)} Dateien geteilt."
    ]
    return parts, reasons


def write_booking_batches(root: Path, data: dict[str, Any]) -> list[dict[str, Any]]:
    run = data["run"]
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    trace: list[dict[str, Any]] = []

    def add_row(doc: dict[str, Any], booking: dict[str, Any], line_no: int,
                kind: str = "document") -> None:
        period = doc.get("period") or run["buchungsmonat"]
        row = booking_row(doc, booking, run)
        batch_type = STANDARD_BATCH_TYPE if kind == "accrual" else document_batch_type(doc)
        batch_kind = (
            BATCH_KIND_CLARIFICATION
            if kind == "document" and doc["traffic_light"] == "Rot"
            else BATCH_KIND_BOOKING
        )
        entry = {
            "transaction_id": doc["transaction_id"], "line": line_no,
            "traffic_light": doc["traffic_light"], "period": period,
            "kind": kind, "batch_kind": batch_kind, "batch_type": batch_type,
            "open_fields": booking.get("open_fields", {}),
            "asset_booking": doc.get("asset_booking") is True,
            "asset_account_field": booking.get("asset_account_field"),
            "recognized_date": doc.get("recognized_date"),
            "kost1": clean_text(booking.get("kost1", "")) or None,
            "kost2": clean_text(booking.get("kost2", "")) or None,
            "export_values": ["" if value is None else str(value) for value in row],
            "reason": doc.get("reason", ""),
            "row": row,
        }
        groups[(period, batch_type, batch_kind)].append(entry)

    for doc in data.get("documents", []):
        if doc.get("processing_status") != "Buchungszeile erzeugt":
            continue
        for line_no, booking in enumerate(doc.get("bookings", []), start=1):
            add_row(doc, booking, line_no)
    for number, release in enumerate(data.get("accrual_releases", []), start=1):
        synthetic_doc = accrual_document(release, run, number)
        add_row(synthetic_doc, release, number, "accrual")

    batches: list[dict[str, Any]] = []
    split_reasons: list[str] = []
    for (period, batch_type, batch_kind) in sorted(groups):
        entries = groups[(period, batch_type, batch_kind)]
        group_label = batch_file_name(period, batch_kind, batch_type)
        parts, reasons = _assign_carry_parts(entries, batch_kind, group_label)
        split_reasons.extend(reasons)
        label = batch_label(batch_kind, batch_type, run)
        for part_number, part in enumerate(parts, start=1):
            file_name = batch_file_name(period, batch_kind, batch_type, part_number)
            rows = [item["row"] for item in part]
            if len(rows) > 99999:
                raise ValueError(
                    f"{file_name}: DATEV-Grenze von 99.999 Buchungen überschritten; nicht eigenmächtig teilen"
                )
            violations = carry_order_violations(rows)
            if violations:
                raise ValueError(f"{file_name}: Sortierregel verletzt: " + "; ".join(violations))
            for csv_row, item in enumerate(part, start=3):
                item["file"] = file_name
                item["csv_row"] = csv_row
                item["carry_order_ok"] = True
                item["batch_part"] = part_number
            write_extf(
                root / FOLDERS["datev"] / file_name,
                extf_header(
                    run, category=21, format_name="Buchungsstapel", version=13,
                    label=label, period=period
                ),
                BOOKING_FIELDS,
                rows,
            )
            batches.append({
                "file": file_name, "period": period, "batch_type": batch_type,
                "batch_kind": batch_kind, "part": part_number, "parts": len(parts),
                "label": label, "rows": len(rows),
                "transactions": sorted({item["transaction_id"] for item in part}),
                "amount_total": str(sum(
                    Decimal(item["export_values"][0].replace(".", "").replace(",", ".") or "0")
                    for item in part
                )),
            })
    ordered_entries = sorted(
        (item for entries in groups.values() for item in entries),
        key=lambda item: (item["file"], item["csv_row"]),
    )
    trace_keys = (
        "transaction_id", "line", "traffic_light", "period", "file", "csv_row",
        "kind", "batch_kind", "batch_type", "batch_part", "carry_order_ok",
        "open_fields", "asset_booking", "asset_account_field", "recognized_date",
        "kost1", "kost2", "export_values", "reason",
    )
    trace = [{key: item[key] for key in trace_keys} for item in ordered_entries]
    data["_booking_batches"] = batches
    data["_batch_split_reasons"] = split_reasons
    return trace


def write_master_data(root: Path, data: dict[str, Any]) -> None:
    records = data.get("master_records", [])
    if not records:
        return
    rows = [master_row(record) for record in records]
    target = root / FOLDERS["datev"] / "EXTF_Debitoren_Kreditoren.csv"
    write_extf(
        target,
        extf_header(
            data["run"], category=16, format_name="Debitoren/Kreditoren",
            version=5, label="Debitoren Kreditoren"
        ),
        MASTER_FIELDS,
        rows,
    )


def _technical_document_name(
    document: dict[str, Any], source: Path, digest: str, used_names: set[str]
) -> str:
    transaction = ascii_filename(str(document.get("transaction_id", "V")), "V")
    transaction = Path(transaction).stem[:80]
    extension = source.suffix.lower()
    candidate = f"{transaction}_{digest[:12]}{extension}"
    counter = 2
    while candidate.lower() in used_names:
        candidate = f"{transaction}_{digest[:12]}_{counter}{extension}"
        counter += 1
    used_names.add(candidate.lower())
    return candidate



def _prepare_canonical_document_transfer(
    data: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[tuple[dict[str, Any], int]]] = defaultdict(list)
    packages: list[dict[str, Any]] = []
    index: list[dict[str, Any]] = []
    used_names: set[str] = set()
    booked_hashes: dict[str, str] = {}
    mandant = str(data["run"]["mandantennummer"])
    run_period = str(data["run"]["buchungsmonat"])
    documents = {
        str(item.get("transaction_id", "")): item
        for item in data.get("documents", [])
    }
    mappings_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for mapping in data.get("transaction_sources", []):
        mappings_by_source[str(mapping.get("source_id", ""))].append(mapping)

    for source_item in data.get("source_files", []):
        source_id = str(source_item.get("source_id", ""))
        source = Path(str(source_item.get("source_path", "")))
        mappings = mappings_by_source.get(source_id, [])
        linked = [
            (mapping, documents.get(str(mapping.get("transaction_id", ""))))
            for mapping in mappings
        ]
        linked = [(mapping, document) for mapping, document in linked if document]
        transaction_ids = [str(mapping["transaction_id"]) for mapping, _ in linked]
        excluded_roles = {"cover_sheet", "duplicate_copy"}
        transferable = [
            (mapping, document)
            for mapping, document in linked
            if mapping.get("role") not in excluded_roles
            and (
                document.get("processing_status") == "Buchungszeile erzeugt"
                or document.get("payment_advice") is True
            )
        ]
        if not transferable:
            index.append({
                "source_id": source_id,
                "transaction_ids": transaction_ids,
                "included": False,
                "reason": "keine übertragbare Dokumentrolle oder kein buchungsrelevanter Vorgang",
            })
            continue
        booking_links = [
            pair for pair in transferable
            if pair[1].get("processing_status") == "Buchungszeile erzeugt"
        ]
        kind = "booking" if booking_links else "advice"
        preferred = next(
            (pair for pair in transferable if pair[0].get("role") == "primary_invoice"),
            transferable[0],
        )
        primary_document = preferred[1]
        period = str(primary_document.get("period") or run_period)
        try:
            month_bounds(period)
        except ValueError as exc:
            raise ValueError(f"{source_id}: ungültige Belegperiode {period}") from exc
        if not source.is_file():
            raise ValueError(f"{source_id}: Quelldatei für den Belegtransfer fehlt: {source}")
        extension = source.suffix.lower()
        if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
            raise ValueError(f"{source_id}: Dateityp {extension or '(ohne Endung)'} ist für DATEV Belegtransfer nicht zugelassen.")
        file_size = source.stat().st_size
        if file_size <= 0 or file_size > MAX_DOCUMENT_BYTES:
            raise ValueError(f"{source_id}: Belegdatei ist leer oder überschreitet 20 MB.")
        if extension == ".pdf" and source.read_bytes()[:5] != b"%PDF-":
            raise ValueError(f"{source_id}: Datei trägt die Endung .pdf, ist aber keine PDF-Datei.")
        digest = source_hash(source)
        declared_hash = str(source_item.get("sha256", "")).lower()
        if declared_hash and declared_hash != digest:
            raise ValueError(f"{source_id}: hinterlegter Datei-Hash stimmt nicht.")
        if kind == "booking":
            previous = booked_hashes.get(digest)
            if previous:
                raise ValueError(f"{source_id}: identischer Dateiinhalt wurde bereits als {previous} übertragen.")
            booked_hashes[digest] = source_id
        technical_name = _technical_document_name(
            {"transaction_id": source_id}, source, digest, used_names
        )
        guid = uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"bk-monatsbuchhaltung:{kind}:{mandant}:{digest}",
        )
        transfer_item = {
            "source_id": source_id,
            "source_path": str(source),
            "transaction_id": str(primary_document.get("transaction_id", "")),
            "transaction_ids": transaction_ids,
            "content_hash": digest,
            "document_filename": technical_name,
            "document_period": period,
            "document_guid": str(guid).upper(),
            "document_package_kind": kind,
        }
        grouped[(kind, period)].append((transfer_item, file_size))
        for mapping, document in transferable:
            if (
                mapping.get("role") == "primary_invoice"
                or not document.get("document_guid")
            ):
                document.update({
                    "content_hash": digest,
                    "document_filename": technical_name,
                    "document_period": period,
                    "document_guid": str(guid).upper(),
                    "document_package_kind": kind,
                })
            else:
                document.setdefault("supporting_document_guids", []).append(
                    str(guid).upper()
                )
        index.append({
            "source_id": source_id,
            "transaction_ids": transaction_ids,
            "content_hash": digest,
            "document_guid": str(guid).upper(),
            "technical_filename": technical_name,
            "document_period": period,
            "document_package_kind": kind,
            "included": True,
            "target": FOLDERS["datev"],
        })

    for document in data.get("documents", []):
        if (
            document.get("processing_status") == "Buchungszeile erzeugt"
            or document.get("payment_advice") is True
        ) and not document.get("document_guid"):
            raise ValueError(
                f"{document.get('transaction_id', '')}: keine übertragbare Primär- oder Unterstützungsquelle"
            )

    for (kind, period) in sorted(grouped):
        current: list[dict[str, Any]] = []
        current_size = 0
        number = 1
        for transfer_item, file_size in grouped[(kind, period)]:
            if current and (
                current_size + file_size > RECOMMENDED_PACKAGE_BYTES
                or len(current) >= MAX_DOCUMENTS_PER_PACKAGE
            ):
                packages.append({"kind": kind, "period": period, "number": number, "documents": current})
                number += 1
                current = []
                current_size = 0
            current.append(transfer_item)
            current_size += file_size
        if current:
            packages.append({"kind": kind, "period": period, "number": number, "documents": current})

    assignments: dict[str, tuple[str, int, str]] = {}
    for package in packages:
        kind = str(package["kind"])
        period = str(package["period"])
        number = int(package["number"])
        key = f"{kind}:{period}:{number:03d}"
        for transfer_item in package["documents"]:
            transfer_item["document_package_period"] = period
            transfer_item["document_package_number"] = number
            transfer_item["document_package_key"] = key
            assignments[str(transfer_item["source_id"])] = (period, number, key)
    for entry in index:
        assignment = assignments.get(str(entry.get("source_id", "")))
        if assignment:
            period, number, key = assignment
            entry["document_package_period"] = period
            entry["document_package_number"] = number
            entry["document_package_key"] = key
    return packages, index

def prepare_document_transfer(
    data: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if data.get("_normalized_source_model") == "canonical":
        return _prepare_canonical_document_transfer(data)
    grouped: dict[tuple[str, str], list[tuple[dict[str, Any], int]]] = defaultdict(list)
    packages: list[dict[str, Any]] = []
    index: list[dict[str, Any]] = []
    used_names: set[str] = set()
    mandant = str(data["run"]["mandantennummer"])
    run_period = str(data["run"]["buchungsmonat"])
    booked_hashes: dict[str, str] = {}

    for document in data.get("documents", []):
        transaction_id = str(document.get("transaction_id", ""))
        source = Path(document.get("source_path", ""))
        is_booking = document.get("processing_status") == "Buchungszeile erzeugt"
        is_advice = bool(document.get("payment_advice"))
        if not is_booking and not is_advice:
            index.append({"transaction_id": transaction_id, "included": False, "reason": document.get("processing_status")})
            continue
        if not source.is_file():
            raise ValueError(f"{transaction_id}: Quelldatei für den Belegtransfer fehlt: {source}")
        extension = source.suffix.lower()
        if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
            raise ValueError(f"{transaction_id}: Dateityp {extension or '(ohne Endung)'} ist für DATEV Belegtransfer nicht zugelassen.")
        file_size = source.stat().st_size
        if file_size <= 0 or file_size > MAX_DOCUMENT_BYTES:
            raise ValueError(f"{transaction_id}: Belegdatei ist leer oder überschreitet 20 MB.")
        if extension == ".pdf" and source.read_bytes()[:5] != b"%PDF-":
            raise ValueError(f"{transaction_id}: Datei trägt die Endung .pdf, ist aber keine PDF-Datei.")
        digest = source_hash(source)
        if is_booking:
            previous = booked_hashes.get(digest)
            if previous:
                raise ValueError(f"{transaction_id}: identischer Dateiinhalt wurde bereits als {previous} gebucht.")
            booked_hashes[digest] = transaction_id
        declared_hash = str(document.get("content_hash", "")).lower()
        if declared_hash and declared_hash != digest:
            raise ValueError(f"{transaction_id}: hinterlegter Datei-Hash stimmt nicht.")
        technical_name = _technical_document_name(document, source, digest, used_names)
        period = str(document.get("period") or run_period)
        try:
            month_bounds(period)
        except ValueError as exc:
            raise ValueError(f"{transaction_id}: ungültige Belegperiode {period}") from exc
        kind = "advice" if is_advice else "booking"
        guid = uuid.uuid5(uuid.NAMESPACE_URL, f"bk-monatsbuchhaltung:{kind}:{mandant}:{digest}")
        document.update({
            "content_hash": digest,
            "document_filename": technical_name,
            "document_period": period,
            "document_guid": str(guid).upper(),
            "document_package_kind": kind,
        })
        grouped[(kind, period)].append((document, file_size))
        index.append({
            "transaction_id": transaction_id,
            "content_hash": digest,
            "document_guid": document["document_guid"],
            "technical_filename": technical_name,
            "document_period": period,
            "document_package_kind": kind,
            "included": True,
            "target": FOLDERS["datev"],
        })

    assignments: dict[str, tuple[str, int, str]] = {}
    for (kind, period) in sorted(grouped):
        current: list[dict[str, Any]] = []
        current_size = 0
        number = 1
        for document, file_size in grouped[(kind, period)]:
            if current and (current_size + file_size > RECOMMENDED_PACKAGE_BYTES or len(current) >= MAX_DOCUMENTS_PER_PACKAGE):
                packages.append({"kind": kind, "period": period, "number": number, "documents": current})
                number += 1
                current = []
                current_size = 0
            current.append(document)
            current_size += file_size
        if current:
            packages.append({"kind": kind, "period": period, "number": number, "documents": current})

    for package in packages:
        kind = str(package["kind"])
        period = str(package["period"])
        number = int(package["number"])
        key = f"{kind}:{period}:{number:03d}"
        for document in package["documents"]:
            document["document_package_period"] = period
            document["document_package_number"] = number
            document["document_package_key"] = key
            assignments[str(document["transaction_id"])] = (period, number, key)
    for entry in index:
        assignment = assignments.get(str(entry.get("transaction_id", "")))
        if assignment:
            period, number, key = assignment
            entry["document_package_period"] = period
            entry["document_package_number"] = number
            entry["document_package_key"] = key
    return packages, index


def _document_xml(documents: list[dict[str, Any]]) -> bytes:
    ET.register_namespace("", DOCUMENT_NAMESPACE)
    ET.register_namespace("xsi", XSI_NAMESPACE)
    archive = ET.Element(
        f"{{{DOCUMENT_NAMESPACE}}}archive",
        {
            "version": "6.0",
            "generatingSystem": "BK Monatsbuchhaltung",
            f"{{{XSI_NAMESPACE}}}schemaLocation": DOCUMENT_SCHEMA_LOCATION,
        },
    )
    header = ET.SubElement(archive, f"{{{DOCUMENT_NAMESPACE}}}header")
    ET.SubElement(header, f"{{{DOCUMENT_NAMESPACE}}}date").text = (
        datetime.now().replace(microsecond=0).isoformat()
    )
    content = ET.SubElement(archive, f"{{{DOCUMENT_NAMESPACE}}}content")
    for item in documents:
        document = ET.SubElement(
            content,
            f"{{{DOCUMENT_NAMESPACE}}}document",
            {"guid": item["document_guid"], "processID": "1"},
        )
        ET.SubElement(
            document,
            f"{{{DOCUMENT_NAMESPACE}}}extension",
            {
                f"{{{XSI_NAMESPACE}}}type": "File",
                "name": item["document_filename"],
            },
        )
    ET.indent(archive, space="  ")
    return ET.tostring(
        archive,
        encoding="utf-8",
        xml_declaration=True,
        short_empty_elements=True,
    )



def write_belegtransfer_packages(
    root: Path,
    data: dict[str, Any],
    packages: list[dict[str, Any]],
    document_index: list[dict[str, Any]],
) -> None:
    run = data["run"]
    package_names: dict[str, str] = {}
    for package in packages:
        kind = str(package.get("kind", "booking"))
        period = str(package["period"])
        number = int(package["number"])
        documents = package["documents"]
        package_key = f"{kind}:{period}:{number:03d}"
        prefix = "Belegtransfer_Avise" if kind == "advice" else "Belegtransfer"
        package_name = f"{prefix}_{run['mandantennummer']}_{period}_{number:03d}.zip"
        package_names[package_key] = package_name
        target = root / FOLDERS["datev"] / package_name
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, strict_timestamps=False) as bundle:
            bundle.writestr("document.xml", _document_xml(documents))
            for document in documents:
                bundle.write(Path(document["source_path"]), document["document_filename"])
        if target.stat().st_size > MAX_PACKAGE_BYTES:
            raise ValueError(f"{package_name}: DATEV-Höchstgröße von 465 MB überschritten.")
    for entry in document_index:
        key = entry.get("document_package_key")
        if key:
            entry["document_package"] = package_names[str(key)]
    (root / FOLDERS["logs"] / "Belegindex.json").write_text(
        json.dumps(document_index, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def copy_payment_advices(root: Path, data: dict[str, Any]) -> None:
    for document in data.get("documents", []):
        if not document.get("payment_advice"):
            continue
        source = Path(document["source_path"])
        destination = root / FOLDERS["advice"] / document["document_filename"]
        shutil.copy2(source, destination)

def md_cell(value: Any) -> str:
    if isinstance(value, list):
        value = ", ".join(str(item) for item in value)
    return str(value if value is not None else "").replace("|", "/").replace(
        "\n", "<br>"
    )


def write_accrual_register(root: Path, data: dict[str, Any]) -> None:
    header = (
        "| Abgrenzungs-ID | Art | Geschäftspartner | Beschreibung | "
        "Aufwands-/Ertragskonto | ARAP-/PRAP-Konto | Belegfeld 1 | "
        "Leistungsbeginn | Leistungsende | Ursprünglich netto | Monatsbetrag | "
        "Nächste Periode | Restbetrag |"
    )
    divider = "|---|---|---|---|---:|---:|---|---|---|---:|---:|---|---:|"
    register = data.get("accrual_register", [])
    preflight_register = data.get("run", {}).get(
        "_preflight_summary", {}
    ).get("abgrenzungsregister")
    first_run_without_register = (
        isinstance(preflight_register, dict)
        and preflight_register.get("status") == "not_found"
    )
    lines = ["# Vorschlag Abgrenzungsregister", ""]
    if first_run_without_register and register:
        lines.extend([
            "**Status: Neuanlage erforderlich.** Das Register war am "
            "verbindlichen SharePoint-Ziel noch nicht vorhanden und der "
            "Übernahmebestand enthält mindestens eine klare Abgrenzung.",
            "",
        ])
    elif first_run_without_register:
        lines.extend([
            "**Status: Keine Neuanlage erforderlich.** Das Register war am "
            "verbindlichen SharePoint-Ziel noch nicht vorhanden; im "
            "Übernahmebestand wurde keine klare Abgrenzung erkannt.",
            "",
        ])
    lines.extend(["## Übernahmebestand", "", header, divider])
    if not register:
        lines.append("| – | – | Keine offenen Rechnungsabgrenzungen | – | – | – | – | – | – | – | – | – | – |")
    for item in register:
        values = [
            item.get("accrual_id", ""), item.get("type", ""),
            item.get("partner", ""), item.get("description", ""),
            item.get("release_account", ""), item.get("accrual_account", ""),
            item.get("document_field_1", ""), item.get("service_start", ""),
            item.get("service_end", ""), item.get("original_net", ""),
            item.get("monthly_release", ""), item.get("next_release_period", ""),
            item.get("remaining_amount", ""),
        ]
        lines.append("| " + " | ".join(md_cell(value) for value in values) + " |")
    lines.extend([
        "", "## Klärung offen – noch nicht übernehmen", "",
        "| Abgrenzungs-ID | Vorgangs-ID(s) | Geschäftspartner | Beschreibung | "
        "Leistungsbeginn | Leistungsende | Maßgeblicher Betrag | Empfehlung | Entscheidung |",
        "|---|---|---|---|---|---|---:|---|---|",
    ])
    candidates = data.get("accrual_candidates", [])
    if not candidates:
        lines.append("| – | – | Keine offenen Kandidaten | – | – | – | – | – | – |")
    for item in candidates:
        values = [
            item.get("accrual_id", ""), item.get("transaction_ids", []),
            item.get("partner", ""), item.get("description", ""),
            item.get("service_start", ""), item.get("service_end", ""),
            item.get("threshold_amount", item.get("original_net", "")),
            item.get("recommendation", ""), item.get("decision_needed", ""),
        ]
        lines.append("| " + " | ".join(md_cell(value) for value in values) + " |")
    (root / FOLDERS["review"] / "Abgrenzungsregister_Vorschlag.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

def write_clarification_files(root: Path, data: dict[str, Any]) -> None:
    cases = data.get("clarification_cases", [])
    lines = [
        "# Klärungsfälle", "",
        "Alle fachlichen Entscheidungen dieses Laufs sind hier gebündelt. "
        "Die Buchungsverarbeitung wurde deswegen nicht unterbrochen.", "",
        "| Klärfall-ID | Vorgangs-ID(s) | Thema | Beleg zeigt | Warum Rot | Nächster Schritt | "
        "Provisorische Behandlung | Empfehlung | Entscheidung erforderlich | Ziel | Vorgeschlagene Änderung | Ergebnis Mitarbeiter |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    documents = {str(doc.get("transaction_id")): doc for doc in data.get("documents", [])}
    if not cases:
        lines.append("| – | – | Keine fachlichen Klärungsfälle | – | – | – | – | – | – | – | – | – |")
    for case in cases:
        linked = [documents.get(str(tid), {}) for tid in case.get("transaction_ids", [])]
        values = [
            case.get("case_id", ""), case.get("transaction_ids", []),
            case.get("topic", ""),
            " / ".join(dict.fromkeys(filter(None, (str(doc.get("document_summary", "")) for doc in linked)))),
            " – ".join(filter(None, [case.get("facts", ""), case.get("booking_risk", "")])),
            " / ".join(dict.fromkeys(filter(None, (str(doc.get("next_step", "")) for doc in linked)))),
            case.get("provisional_treatment", ""), case.get("recommendation", ""),
            case.get("decision_needed", ""),
            case.get("target", ""), case.get("proposed_change", ""),
            case.get("employee_result", ""),
        ]
        lines.append("| " + " | ".join(md_cell(value) for value in values) + " |")
    review = root / FOLDERS["review"]
    (review / "Klaerungsfaelle.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    suggestions = data.get("profile_suggestions", [])
    provisional = data.get("provisional_profile")
    if data.get("mandantenprofil", {}).get("status") == "provisional_first_run":
        profile = [
            str(provisional.get("content_markdown", "")).rstrip(), "",
            "**Mandantenprofil-Status: vorläufig – Freigabe ausstehend**", "",
            "Dieses vollständige Erstlaufprofil wurde noch nicht nach SharePoint geschrieben.", "",
            "## Quellen des vorläufigen Profils", "",
        ]
        profile.extend(
            [f"- {md_cell(source)}" for source in provisional.get("sources", [])]
        )
        profile.extend([
            "", "## Weitere dauerhafte Vorschläge", "",
            "| Vorschlags-ID | Abschnitt | Vorgeschlagener Regeltext | Begründung | Vorgangs-ID(s) |",
            "|---|---|---|---|---|",
        ])
    else:
        profile = [
            "# Vorschlag Mandantenprofil", "",
            "Nur dauerhaft wiederverwendbare mandantenspezifische Besonderheiten "
            "werden vorgeschlagen.", "",
            "| Vorschlags-ID | Abschnitt | Vorgeschlagener Regeltext | Begründung | Vorgangs-ID(s) |",
            "|---|---|---|---|---|",
        ]
    if not suggestions:
        profile.append("| – | – | Keine Änderung vorgeschlagen | – | – |")
    for item in suggestions:
        values = [
            item.get("suggestion_id", ""), item.get("section", ""),
            item.get("proposed_rule", ""), item.get("reason", ""),
            item.get("transaction_ids", []),
        ]
        profile.append("| " + " | ".join(md_cell(value) for value in values) + " |")
    (review / "Mandantenprofil_Vorschlag.md").write_text(
        "\n".join(profile) + "\n", encoding="utf-8"
    )

def write_activity_and_handoffs(root: Path, data: dict[str, Any]) -> None:
    review = root / FOLDERS["review"]
    documents = data.get("documents", [])
    report = data.get("activity_report", {})
    status_counts = Counter(item.get("processing_status") for item in documents)
    light_counts = Counter(item.get("traffic_light") for item in documents)
    booking_lines = sum(len(item.get("bookings", [])) for item in documents) + len(data.get("accrual_releases", []))
    actual_periods = sorted({
        str(item.get("period", ""))
        for item in documents
        if item.get("processing_status") == "Buchungszeile erzeugt"
    })
    profile_status = (
        "vorläufig – Freigabe ausstehend"
        if data.get("mandantenprofil", {}).get("status") == "provisional_first_run"
        else "freigegeben"
    )
    lines = [
        "# Tätigkeits- und Abdeckungsnachweis",
        "",
        f"- Auftrag: {data.get('scope', {}).get('job_mode', JOB_MODE)}",
        f"- Beauftragte Zielperioden: {', '.join(data.get('scope', {}).get('target_periods', []))}",
        f"- Tatsächlich verarbeitete Buchungsperioden: {', '.join(actual_periods) or 'keine'}",
        f"- Mandantenprofil-Status: {profile_status}",
        f"- Quelldateien: {len(data.get('source_files', []))}",
        f"- Logische Vorgänge: {len(documents)}",
        f"- Buchungszeilen: {booking_lines}",
        f"- Gebuchte Vorgänge: {status_counts.get('Buchungszeile erzeugt', 0)}",
        f"- Grün/Rot: {light_counts.get('Grün', 0)} / {light_counts.get('Rot', 0)}",
        f"- Ausgeschlossen: {sum(1 for item in documents if item.get('processing_status') in {'nicht buchungsrelevant', 'außerhalb Auftragszeitraum'})}",
        f"- Sichere Dubletten: {status_counts.get('sichere Dublette – nicht erneut gebucht', 0)}",
        f"- Bearbeitungsstatus: {report.get('datev_import_status', 'Importpaket erstellt – noch nicht in DATEV importiert')}",
        "- Fachstatus: fachlicher Prüfprotokoll-Rücklauf ausstehend",
        "",
        "## DATEV-Stapel",
        "",
        "| Datei | Stapelbezeichnung | Zeilen | Summe |",
        "|---|---|---:|---:|",
    ]
    for batch in data.get("_booking_batches", []):
        lines.append(f"| {batch['file']} | {batch['label']} | {batch['rows']} | {batch['amount_total']} |")
    if not data.get("_booking_batches"):
        lines.append("| – | – | 0 | 0 |")
    for reason in data.get("_batch_split_reasons", []):
        lines.append(f"\nTeilungsgrund: {reason}")
    lines.extend([
        "",
        "## Verwendete Datenquellen",
        "",
    ])
    sources_used = report.get("sources_used", [])
    lines.extend([f"- {source}" for source in sources_used] or ["- Keine zusätzliche Quellenliste übergeben (Legacy-Lauf)"])
    lines.extend([
        "",
        "## Angefragte Personen und Geschäftspartner",
        "",
        "| Name | Suchvarianten | Fundstellen | Endstatus |",
        "|---|---|---:|---|",
    ])
    entities = report.get("named_entities", [])
    if not entities:
        lines.append("| – | – | 0 | Keine Namen ausdrücklich angefragt |")
    for item in entities:
        lines.append(
            "| " + " | ".join(md_cell(value) for value in (
                item.get("name", ""), item.get("variants", []),
                item.get("findings", 0), item.get("final_status", ""),
            )) + " |"
        )
    (review / "Taetigkeitsnachweis.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    handoff_lines = [
        "# Übergabeliste ausgeschlossener Folgearbeiten", "",
        "Bank, Kasse, Lohn, Zahlungsverkehr, OPOS-Ausgleich, Abstimmungen und Monatsabschluss werden nicht in diesem Skill gebucht.",
        "",
        "| Quellen-ID(s) | Vorgangs-ID(s) | Periode | Zielprozess | Grund |",
        "|---|---|---|---|---|",
    ]
    handoffs = data.get("handoffs", [])
    if not handoffs:
        handoff_lines.append("| – | – | – | Keine Übergabe erforderlich | – |")
    for item in handoffs:
        handoff_lines.append(
            "| " + " | ".join(md_cell(value) for value in (
                item.get("source_ids", []), item.get("transaction_ids", []),
                item.get("period", ""), item.get("target_process", ""),
                item.get("reason", ""),
            )) + " |"
        )
    (review / "Uebergabeliste.md").write_text(
        "\n".join(handoff_lines) + "\n", encoding="utf-8"
    )

def build_review(root: Path, data: dict[str, Any], node: str) -> None:
    review_json = root / FOLDERS["logs"] / "review_input.json"
    sanitized = json.loads(json.dumps(data))
    for key in ("mandantenprofil_evidence", "abgrenzungsregister_evidence"):
        evidence = sanitized.get("run", {}).get(key)
        if isinstance(evidence, dict):
            evidence.pop("content_utf8", None)
            evidence.pop("raw_file_path", None)
    for key in ("_validated_accounts", "_validated_bu_keys", "_validated_cost_centers", "_used_person_accounts"):
        sanitized.get("run", {}).pop(key, None)
    sanitized["booking_trace"] = data.get("_booking_trace", [])
    sanitized["booking_batches"] = data.get("_booking_batches", [])
    review_json.write_text(json.dumps(sanitized, ensure_ascii=False, indent=2), encoding="utf-8")
    script = Path(__file__).with_name("build_review_workbook.py")
    output = root / FOLDERS["review"] / (
        f"Buchungspruefung_{data['run']['mandantennummer']}_{data['run']['buchungsmonat']}.xlsx"
    )
    qa_dir = root / FOLDERS["logs"] / "Excel_Vorschau"
    subprocess.run(
        [sys.executable, str(script), "--input", str(review_json), "--output", str(output), "--qa-dir", str(qa_dir)],
        check=True,
    )


def write_manifest(root: Path, data: dict[str, Any], trace: list[dict[str, Any]],
                   document_index: list[dict[str, Any]]) -> None:
    docs = data.get("documents", [])
    status_counts = Counter(doc.get("processing_status") for doc in docs)
    light_counts = Counter(doc.get("traffic_light") for doc in docs)
    assigned = sum(status_counts.get(status, 0) for status in VALID_STATUSES)
    expected_booking_ids = {
        str(doc.get("transaction_id"))
        for doc in docs
        if doc.get("processing_status") == "Buchungszeile erzeugt"
    }
    exported_booking_ids = {
        str(item.get("transaction_id"))
        for item in trace
        if item.get("transaction_id")
    }
    missing_booking_exports = sorted(
        expected_booking_ids - exported_booking_ids
    )
    complete = assigned == len(docs) and not missing_booking_exports
    manifest = {
        "skill_version": SKILL_VERSION,
        "output_contract": OUTPUT_CONTRACT,
        "pruefprotokoll_ruecklauf_status": "ausstehend",
        "beraternummer": data["run"]["beraternummer"],
        "mandant": data["run"]["mandantennummer"],
        "buchungsmonat": data["run"]["buchungsmonat"],
        "run_contract": {
            "scope": data.get("scope", {}),
            "mandantenprofil": data.get("mandantenprofil", {}),
            "wirtschaftsjahr_beginn": data["run"]["wirtschaftsjahr_beginn"],
            "sachkontenlaenge": data["run"]["sachkontenlaenge"],
            "sachkontenrahmen": data["run"]["sachkontenrahmen"],
            "waehrung": data["run"].get("waehrung", "EUR"),
            "accounting_method": data["run"]["accounting_method"],
            "kostenstellenpflicht": data["run"]["kostenstellenpflicht"],
            "cost_center_config": data["run"].get("cost_center_config"),
            "batch_config": data["run"].get("batch_config"),
            "vat_config": data["run"]["vat_config"],
            "account_config": data["run"]["account_config"],
            "person_account_ranges": data["run"]["person_account_ranges"],
        },
        "hochgeladene_dateien": len(data.get("source_files", [])),
        "quelldateien": len(data.get("source_files", [])),
        "logische_vorgaenge": len(docs),
        "buchungszeilen": len(trace),
        "input_inventory_count": len(data.get("input_inventory", [])),
        "input_inventory": data.get("input_inventory", []),
        "ampel": dict(light_counts),
        "status": dict(status_counts),
        "vollstaendig": complete,
        "buchungsrelevante_belege_ohne_exportzeile": missing_booking_exports,
        "unzugeordnete_dateien": [
            doc.get("transaction_id")
            for doc in docs
            if doc.get("processing_status") not in VALID_STATUSES
        ],
        "master_records": len(data.get("master_records", [])),
        "client_notes": len(data.get("client_notes", [])),
        "accrual_releases": len(data.get("accrual_releases", [])),
        "clarification_cases": len(data.get("clarification_cases", [])),
        "accrual_candidates": len(data.get("accrual_candidates", [])),
        "profile_suggestions": len(data.get("profile_suggestions", [])),
        "activity_report": data.get("activity_report", {}),
        "handoffs": data.get("handoffs", []),
        "payment_reconciliation": data.get("payment_reconciliation", []),
        "booking_trace": trace,
        "booking_batches": data.get("_booking_batches", []),
        "batch_split_reasons": data.get("_batch_split_reasons", []),
        "carry_fields": sorted(CARRY_FIELDS),
        "datev_test_import": data.get("datev_test_import", {"status": "pending"}),
        "document_index": document_index,
        "belegtransfer_status": (
            "DATEV Document-Package v6.0; Buchungsbelege und Avis getrennt, jeweils ZIP mit document.xml"
        ),
        "payment_advice_packages": sum(1 for item in document_index if item.get("document_package_kind") == "advice"),
        "datev_import_order": list(DATEV_IMPORT_ORDER),
        "preflight_evidence": data["run"].get("_preflight_summary", {}),
    }
    (root / FOLDERS["logs"] / "Laufmanifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    summary = [
        "# Technisches Laufprotokoll", "",
        f"- Skill-Version: {SKILL_VERSION}",
        f"- Ausgabevertrag: {OUTPUT_CONTRACT}",
        "- Prüfprotokoll-Rücklauf: ausstehend",
        f"- Vollständigkeit: {'VOLLSTÄNDIG' if complete else 'UNVOLLSTÄNDIG'}",
        f"- Quelldateien: {len(data.get('source_files', []))}",
        f"- Logische Vorgänge: {len(docs)}",
        f"- Buchungszeilen: {len(trace)}",
        f"- Zielperioden: {', '.join(data.get('scope', {}).get('target_periods', []))}",
        f"- Bearbeitungsstatus: {data.get('activity_report', {}).get('datev_import_status', 'Importpaket erstellt – noch nicht in DATEV importiert')}",
        "- Fachstatus: fachlicher Prüfprotokoll-Rücklauf ausstehend",
        f"- Buchungsbelege: {status_counts.get('Buchungszeile erzeugt', 0)}",
        f"- Sichere Dubletten: {status_counts.get('sichere Dublette – nicht erneut gebucht', 0)}",
        f"- Nicht buchungsrelevant: {status_counts.get('nicht buchungsrelevant', 0)}",
        f"- Rote Belege mit konkret dokumentiertem Bearbeitungsbedarf: {light_counts.get('Rot', 0)}",
        "",
        "## DATEV-Stapel",
        "",
        "| Datei | Stapelbezeichnung | Art | Zeilen | Summe |",
        "|---|---|---|---:|---:|",
    ]
    for batch in data.get("_booking_batches", []):
        summary.append(
            f"| {batch['file']} | {batch['label']} | {batch['batch_kind']} | {batch['rows']} | {batch['amount_total']} |"
        )
    if not data.get("_booking_batches"):
        summary.append("| – | – | – | 0 | 0 |")
    summary.append("")
    for reason in data.get("_batch_split_reasons", []):
        summary.append(f"- Teilung: {reason}")
    summary.extend([
        "- Importreihenfolge: " + "; ".join(DATEV_IMPORT_ORDER),
        "",
        "Belegtransfer wurde als DATEV Document-Package mit document.xml erzeugt.",
    ])
    (root / FOLDERS["logs"] / "Laufprotokoll.md").write_text(
        "\n".join(summary) + "\n", encoding="utf-8"
    )


def zip_package(root: Path) -> Path:
    archive = root.with_suffix(".zip")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                bundle.write(path, path.relative_to(root.parent))
    return archive


def main() -> int:
    args = parse_args()
    try:
        data = load_input(args.input)
        errors = validate_input_inventory(data)
        errors.extend(validate_documents(data))
        errors.extend(validate_accrual_source_documents(data))
        errors.extend(validate_clarifications(data))
        if errors:
            raise ValueError("\n".join(errors))
        transfer_packages, document_index = prepare_document_transfer(data)
        root = prepare_output(args.output, data["run"])
        trace = write_booking_batches(root, data)
        data["_booking_trace"] = trace
        write_master_data(root, data)
        write_belegtransfer_packages(
            root, data, transfer_packages, document_index
        )
        copy_payment_advices(root, data)
        write_accrual_register(root, data)
        write_clarification_files(root, data)
        write_activity_and_handoffs(root, data)
        build_review(root, data, args.node)
        write_manifest(root, data, trace, document_index)
        validator = Path(__file__).with_name("validate_package.py")
        subprocess.run(
            [sys.executable, str(validator), "--package", str(root)],
            check=True,
        )
        archive = zip_package(root)
        print(json.dumps({
            "package_directory": str(root),
            "archive": str(archive),
        }, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
