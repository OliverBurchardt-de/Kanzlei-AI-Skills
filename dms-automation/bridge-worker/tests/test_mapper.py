from __future__ import annotations

import copy

import pytest

from dms_bridge.mapper import (
    ContractError,
    binary_name_for,
    build_document_payload,
    is_sidecar,
    resolve_mapping,
    sidecar_name_for,
    validate_sidecar,
)

GUELTIGES_SIDECAR = {
    "contract_version": "1.0",
    "mandanten_nr": "10002",
    "jahr": 2025,
    "monat": None,
    "dokumenttyp": "bescheidreview_arbeitspapier",
    "beschreibung": "Bescheidreview KSt/GewSt 2025 Bemelmans",
    "stichworte": "Bescheid, KSt, 2025",
    "datei_name": "Bescheidreview_Bemelmans_KSt_2025_2026-08-07.xlsx",
    "sha256": "a" * 64,
    "datei_groesse_bytes": 123456,
    "quelle_skill": "bescheid-review",
    "erstellt_am": "2026-08-07T10:15:00+02:00",
    "binary_delivery": "upload",
    "update_von_dms_guid": None,
}

MAPPING = {
    "defaults": {"class": 1, "domain": 1, "state": 5, "update_strategy": "version"},
    "dokumenttypen": {
        "bescheidreview_arbeitspapier": {"folder": 5, "register": 560},
        "abschlussreview_arbeitspapier": {"folder": 4, "register": 562, "state": 1000},
    },
}


def test_gueltiges_sidecar_passiert_validierung():
    validate_sidecar(copy.deepcopy(GUELTIGES_SIDECAR))


@pytest.mark.parametrize(
    "feld,wert",
    [
        ("mandanten_nr", "1234"),        # nur 4 Ziffern
        ("mandanten_nr", "1234a"),
        ("sha256", "XYZ"),
        ("contract_version", "2.0"),
        ("binary_delivery", "email"),
        ("datei_name", "ohne_endung"),
        ("jahr", 1999),
    ],
)
def test_ungueltige_werte_werden_abgelehnt(feld, wert):
    sidecar = copy.deepcopy(GUELTIGES_SIDECAR)
    sidecar[feld] = wert
    with pytest.raises(ContractError):
        validate_sidecar(sidecar)


def test_fehlendes_pflichtfeld_wird_abgelehnt():
    sidecar = copy.deepcopy(GUELTIGES_SIDECAR)
    del sidecar["beschreibung"]
    with pytest.raises(ContractError):
        validate_sidecar(sidecar)


def test_unbekanntes_feld_wird_abgelehnt():
    sidecar = copy.deepcopy(GUELTIGES_SIDECAR)
    sidecar["frei_erfunden"] = 1
    with pytest.raises(ContractError):
        validate_sidecar(sidecar)


def test_mapping_defaults_und_override():
    target = resolve_mapping(GUELTIGES_SIDECAR, MAPPING)
    assert target == {
        "class": 1,
        "domain": 1,
        "state": 5,
        "update_strategy": "version",
        "folder": 5,
        "register": 560,
    }
    sidecar = {**GUELTIGES_SIDECAR, "dokumenttyp": "abschlussreview_arbeitspapier"}
    assert resolve_mapping(sidecar, MAPPING)["state"] == 1000


def test_unbekannter_dokumenttyp():
    sidecar = {**GUELTIGES_SIDECAR, "dokumenttyp": "gibt_es_nicht"}
    with pytest.raises(ContractError):
        resolve_mapping(sidecar, MAPPING)


def test_payload_enthaelt_pflichtfelder_der_openapi():
    target = resolve_mapping(GUELTIGES_SIDECAR, MAPPING)
    payload = build_document_payload(
        GUELTIGES_SIDECAR, target, "e602ddcb-e479-4cee-b268-e53bbecf6dc9", 1489, "u-guid"
    )
    # Pflicht laut DocumentCreate (OpenAPI 2.3.1): class, correspondence_partner_guid, structure_items
    assert payload["class"] == {"id": 1}
    assert payload["correspondence_partner_guid"] == "e602ddcb-e479-4cee-b268-e53bbecf6dc9"
    assert len(payload["structure_items"]) == 1
    item = payload["structure_items"][0]
    assert item["counter"] == 1
    assert item["type"] == 1
    assert item["document_file_id"] == 1489
    assert item["name"].endswith(".xlsx")
    assert item["creation_date"] and item["last_modification_date"]
    # Vom Worker zusätzlich immer gesetzt:
    assert payload["description"]
    assert payload["domain"] == {"id": 1}
    assert payload["state"] == {"id": 5}
    assert payload["user"] == {"id": "u-guid"}
    assert payload["year"] == 2025
    assert "month" not in payload  # monat war null


def test_payload_optionale_felder():
    sidecar = {**GUELTIGES_SIDECAR, "monat": 3, "stichworte": "FiBu"}
    target = resolve_mapping(sidecar, MAPPING)
    payload = build_document_payload(sidecar, target, "guid", 1, "u")
    assert payload["month"] == 3
    assert payload["keywords"] == "FiBu"


def test_namenskonvention_sidecar():
    assert sidecar_name_for("a.xlsx") == "a.xlsx.dms.json"
    assert is_sidecar("a.xlsx.dms.json")
    assert not is_sidecar("a.xlsx")
    assert binary_name_for("a.xlsx.dms.json") == "a.xlsx"
