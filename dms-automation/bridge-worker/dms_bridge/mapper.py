"""Sidecar + mapping.yaml -> validiertes Payload für POST /dms/v2/documents.

Reine Funktionen ohne I/O – dieses Modul ist zugleich die ausführbare
Spezifikation des Metadaten-Kontrakts (uebergabe.schema.json) und damit die
Referenz für eine mögliche Klardaten-Write-Implementierung.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "uebergabe.schema.json"


class ContractError(ValueError):
    """Sidecar verletzt den Metadaten-Kontrakt oder das Mapping."""


def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_sidecar(sidecar: dict[str, Any], schema: dict[str, Any] | None = None) -> None:
    try:
        jsonschema.validate(sidecar, schema or load_schema())
    except jsonschema.ValidationError as exc:
        raise ContractError(f"Sidecar ungültig: {exc.message}") from exc


def resolve_mapping(sidecar: dict[str, Any], mapping: dict[str, Any]) -> dict[str, Any]:
    """Ermittelt das DMS-Ziel (class/domain/folder/register/state/update_strategy)."""
    dokumenttyp = sidecar["dokumenttyp"]
    typen = mapping.get("dokumenttypen", {})
    if dokumenttyp not in typen:
        raise ContractError(f"Unbekannter Dokumenttyp '{dokumenttyp}' (nicht in mapping.yaml)")
    target = {**mapping.get("defaults", {}), **typen[dokumenttyp]}
    missing = [k for k in ("class", "domain", "folder", "register", "state") if k not in target]
    if missing:
        raise ContractError(f"Mapping für '{dokumenttyp}' unvollständig, es fehlt: {missing}")
    return target


def build_document_payload(
    sidecar: dict[str, Any],
    target: dict[str, Any],
    correspondence_partner_guid: str,
    document_file_id: int,
    dms_user_guid: str,
) -> dict[str, Any]:
    """Baut das Payload für POST /documents.

    Pflichtfelder laut OpenAPI 2.3.1: class, correspondence_partner_guid,
    structure_items; zusätzlich werden description, domain, state und user
    gesetzt (von der Desktop-Anwendung erwartet, siehe Konzept).
    """
    structure_item = {
        "counter": 1,
        "type": 1,  # 1 = Datei
        "name": sidecar["datei_name"],
        "parent_counter": 0,
        "creation_date": sidecar["erstellt_am"],
        "last_modification_date": sidecar["erstellt_am"],
        "document_file_id": document_file_id,
    }
    payload: dict[str, Any] = {
        "class": {"id": target["class"]},
        "correspondence_partner_guid": correspondence_partner_guid,
        "description": sidecar["beschreibung"],
        "domain": {"id": target["domain"]},
        "folder": {"id": target["folder"]},
        "register": {"id": target["register"]},
        "state": {"id": target["state"]},
        "user": {"id": dms_user_guid},
        "year": sidecar["jahr"],
        "application": sidecar["quelle_skill"],
        "structure_items": [structure_item],
    }
    if sidecar.get("monat"):
        payload["month"] = sidecar["monat"]
    if sidecar.get("stichworte"):
        payload["keywords"] = sidecar["stichworte"]
    return payload


def sidecar_name_for(file_name: str) -> str:
    return f"{file_name}.dms.json"


def is_sidecar(name: str) -> bool:
    return name.endswith(".dms.json")


def binary_name_for(sidecar_name: str) -> str:
    return sidecar_name[: -len(".dms.json")]
