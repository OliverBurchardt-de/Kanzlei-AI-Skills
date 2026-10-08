"""Regressionstests Änderungsauftrag v1.4.1.

1. Anti-Abbruch (150 Eingaben, 120 Bild-PDFs, jedes Dokument mit beweisbarem Endstatus)
2. Einzelner SharePoint-/DATEV-Fehler blockiert nicht den übrigen Belegbestand
3. Fehlendes, leeres und nicht abrufbares (HTTP 403) Abgrenzungsregister
4. Klärungsquote N=100, R=25 → Zweitprüfung → N=100, R=15
5. Unverändert hohe Klärungsquote bleibt fachlich offen, kein künstliches Grün, kein Abbruch
6. Mehrfachzeilen und Dubletten in der Zählweise
7. Scan ohne Textebene ist nicht allein wegen fehlender OCR Rot
8. Vollständigkeits-Gate: nur Inventar oder nur Prüfungs-Excel ist kein Abschluss
9. Versionstest 1.4.1, kein Verweis auf 1.4.2
10. Belegdateiregel: ein Buchungsbeleg = genau eine eigene PDF-Datei
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from openpyxl import load_workbook

import beleg_pdf
import build_package
import clarification_rate
import validate_package
from sharepoint_target import build_targets
from test_datev_contract import evidence, red_reason, second_review, write_pdf
from test_v140_contract import PACKAGE_DIR, PERIOD, Scenario, csv_rows, extf_names, make_run, red_booking, run_validator


SKILL_ROOT = SCRIPT_DIR.parent
VERSION = "1.4.1"


def source_entry(path: Path, source_id: str, **extra) -> dict:
    raw = path.read_bytes()
    item = {
        "source_id": source_id, "source_path": str(path), "size_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(), "readability": "readable",
    }
    item.update(extra)
    return item


def write_run(scenario: Scenario, name: str, mutate=None) -> Path:
    data = copy.deepcopy(scenario.data())
    if mutate:
        mutate(data)
    path = scenario.root / f"{name}.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def build(scenario: Scenario, name: str, mutate=None) -> tuple[subprocess.CompletedProcess, Path]:
    input_path = write_run(scenario, name, mutate)
    result = subprocess.run(
        [sys.executable, str(Path(build_package.__file__)), "--input", str(input_path), "--output", str(scenario.root / name)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return result, scenario.root / name / PACKAGE_DIR


def build_ok(scenario: Scenario, name: str, mutate=None) -> tuple[Path, dict, dict]:
    result, package = build(scenario, name, mutate)
    assert result.returncode == 0, result.stderr + result.stdout
    manifest = json.loads((package / "03_Technische_Protokolle" / "Laufmanifest.json").read_text(encoding="utf-8"))
    report = json.loads((package / "03_Technische_Protokolle" / "Validierungsbericht.json").read_text(encoding="utf-8"))
    assert report["valid"], report["errors"]
    return package, manifest, report


def build_fails(scenario: Scenario, name: str, fragment: str, mutate=None) -> None:
    result, _ = build(scenario, name, mutate)
    assert result.returncode != 0, f"{name}: Lauf wurde fälschlich akzeptiert"
    assert fragment in result.stderr, f"{name}: erwartete Meldung {fragment!r} fehlt in: {result.stderr}"


def load_fails(scenario: Scenario, name: str, fragment: str, mutate=None) -> None:
    try:
        build_package.load_input(write_run(scenario, name, mutate))
    except ValueError as exc:
        assert fragment in str(exc), f"{name}: {exc}"
    else:
        raise AssertionError(f"{name}: Fehler {fragment!r} wurde nicht erkannt")


def unreadable_doc(doc: dict, attempts: list[dict] | None) -> None:
    doc.update({
        "processing_status": "technisch nicht auswertbar", "traffic_light": None, "bookings": [],
        "exclusion_reason": "PDF ist passwortgeschützt; Belegbild nicht darstellbar.",
    })
    doc.pop("requires_clarification", None)
    if attempts is not None:
        doc["evaluation_attempts"] = attempts


FULL_ATTEMPTS = [
    {"method": "textebene", "result": "keine Textebene"},
    {"method": "belegbild", "result": "Seiten nicht renderbar (verschlüsselt)"},
    {"method": "wiederholung", "result": "zweiter Leseversuch identisch fehlgeschlagen"},
]


# 1. Anti-Abbruch -------------------------------------------------------------

def test_anti_abort(root: Path) -> None:
    scenario = Scenario(root, make_run(root))
    for number in range(1, 151):
        doc = scenario.add("Grün")
        if number <= 120:
            # Bild-PDF ohne Textebene: über das Belegbild ausgewertet, regulär Grün.
            scenario.sources[-1]["readability"] = "image_only"
            doc["derivation"] = "Belegbild ausgewertet (kein OCR-Text); 119 EUR, 4900 gegen 70001, BU 401."
    package, manifest, report = build_ok(scenario, "complete")
    assert manifest["quelldateien"] == 150 and manifest["hochgeladene_dateien"] == 150
    assert manifest["status"]["Buchungszeile erzeugt"] == 150 and manifest["vollstaendig"] is True
    assert manifest["unzugeordnete_dateien"] == []
    assert manifest["run_completion"]["status"] == "vollständig abgeschlossen"
    assert report["completion_gate"]["passed"] is True
    index = json.loads((package / "03_Technische_Protokolle" / "Belegindex.json").read_text(encoding="utf-8"))
    assert sum(1 for item in index if item["included"]) == 150
    assert len(csv_rows(package / "01_DATEV_Import" / f"EXTF_Buchungsstapel_{PERIOD}.csv")) == 150
    assert sum(1 for item in scenario.sources if item["readability"] == "image_only") == 120

    # Nur Inventar bzw. nur sieben Beispielbelege: der Generator weist den Lauf zurück.
    def only_seven(data: dict) -> None:
        keep = {doc["transaction_id"] for doc in data["transactions"][:7]}
        data["transactions"] = [doc for doc in data["transactions"] if doc["transaction_id"] in keep]
        data["transaction_sources"] = [item for item in data["transaction_sources"] if item["transaction_id"] in keep]
    build_fails(scenario, "seven", "keinem Vorgang zugeordnet", only_seven)

    def inventory_only(data: dict) -> None:
        data["transactions"] = []
        data["transaction_sources"] = []
    build_fails(scenario, "inventory", "keinem Vorgang zugeordnet", inventory_only)

    # Fehlender OCR-Text ist kein Endpunkt und kein Rot-Grund.
    def ocr_red(data: dict) -> None:
        doc = data["transactions"][0]
        doc.update({"traffic_light": "Rot", "requires_clarification": True, "reason": "Scan ohne Textebene, OCR fehlgeschlagen.", "red_reason": red_reason("konto_unklar")})
        doc["bookings"][0].update({"account": None, "open_fields": {"account": "Konto unklar."}})
        data["clarification_cases"].append({
            "case_id": "K-OCR", "transaction_ids": [doc["transaction_id"]], "topic": "OCR", "facts": "x",
            "booking_risk": "x", "provisional_treatment": "x", "recommendation": "x", "decision_needed": "x",
            "traffic_light": "Rot", "target": "Prüfungsdatei", "proposed_change": "x", "employee_result": "",
        })
        data["clarification_review"] = second_review([doc["transaction_id"]])
    build_fails(scenario, "ocr", "nicht allein mit fehlender OCR", ocr_red)


# 2. Einzelner technischer Fehler --------------------------------------------

def test_single_failure_continues(root: Path) -> None:
    scenario = Scenario(root, make_run(root))
    for _ in range(80):
        scenario.add("Grün")
    affected = scenario.add(
        "Rot", reason="Personenkonto wegen DATEV-Timeout nicht bestätigt; Kreditor offen.",
        bookings=[red_booking(contra_account=None, contra_account_name=None, open_fields={"contra_account": "Partnerabfrage in DATEV fehlgeschlagen; Personenkonto offen."})],
        red_reason=red_reason("personenkonto_unklar", partner_check={
            "tool": "datev_search_business_partners", "query": "DATEV Test GmbH", "result": "error",
            "detail": "Timeout; Partnerabgleich nicht abschließbar.",
        }),
    )
    incident = {
        "incident_id": "T001", "system": "DATEV", "scope": "datev_search_business_partners für DATEV Test GmbH",
        "error": "Timeout nach 30 s", "retries": 2, "alternative_path": "datev_get_account_postings auf Kreditorenbereich versucht; ebenfalls Timeout",
        "affected_transaction_ids": [affected["transaction_id"]], "deferred_decision": "Personenkonto für DATEV Test GmbH",
        "next_step": "Partnerabfrage nach Wiederherstellung des Connectors wiederholen", "resolved": False,
    }
    def with_incident(data: dict) -> None:
        data["technical_incidents"] = [incident]
    package, manifest, report = build_ok(scenario, "incident", with_incident)
    assert manifest["status"]["Buchungszeile erzeugt"] == 81 and manifest["ampel"]["Grün"] == 80
    assert len(csv_rows(package / "01_DATEV_Import" / f"EXTF_Buchungsstapel_{PERIOD}.csv")) == 80
    assert len(csv_rows(package / "01_DATEV_Import" / f"EXTF_Klaerungsposten_{PERIOD}.csv")) == 1
    assert manifest["run_completion"]["status"] == "nicht vollständig abgeschlossen"
    assert any("T001" in item["item"] for item in manifest["run_completion"]["open_items"])
    assert report["valid"] is True and report["completion_gate"]["passed"] is False
    activity = (package / "02_Buchungspruefung" / "Taetigkeitsnachweis.md").read_text(encoding="utf-8")
    assert "nicht vollständig abgeschlossen" in activity and "T001" in activity
    # Betroffener Vorgang darf nicht Grün sein; Wiederholung muss dokumentiert sein.
    def green_affected(data: dict) -> None:
        data["technical_incidents"] = [{**incident, "affected_transaction_ids": ["V0001"]}]
    build_fails(scenario, "green-affected", "darf nicht Grün sein", green_affected)
    def no_retry(data: dict) -> None:
        data["technical_incidents"] = [{**incident, "retries": 0}]
    build_fails(scenario, "no-retry", "zulässige Wiederholung", no_retry)


# 3. Abgrenzungsregister --------------------------------------------------------

def bilanz_run(root: Path) -> dict:
    run = make_run(root)
    run["accounting_method"] = "Bilanz"
    return run


def test_accrual_register_states(root: Path) -> None:
    targets = build_targets("12861")
    url = str(targets["accrual_url"])
    base_not_found = {
        "status": "not_found", "source_url": url, "file_name": "12861.md", "retrieved_via": "microsoft_sharepoint.fetch",
        "checked_at": "2026-10-08T09:00:00+02:00", "not_found_code": "itemNotFound", "site_verified": True,
        "library_verified": True, "direct_lookup_attempts": 2,
    }
    # a) nicht angelegt
    (root / "missing").mkdir()
    missing = Scenario(root / "missing", bilanz_run(root / "missing"))
    missing.run["abgrenzungsregister_evidence"] = base_not_found
    missing.add("Grün")
    package, manifest, report = build_ok(missing, "missing")
    text = (package / "02_Buchungspruefung" / "Abgrenzungsregister_Vorschlag.md").read_text(encoding="utf-8")
    assert "Keine Neuanlage erforderlich" in text and report["completion_gate"]["passed"]
    # b) vorhanden, aber leer
    (root / "empty").mkdir()
    empty_register = root / "empty" / "register.md"
    empty_register.write_text("# Abgrenzungsregister 12861\n\n(keine offenen Fälle)\n", encoding="utf-8")
    empty = Scenario(root / "empty", bilanz_run(root / "empty"))
    empty.run["abgrenzungsregister_evidence"] = {**evidence(empty_register, url), "file_name": "12861.md"}
    empty.add("Grün")
    _, manifest, report = build_ok(empty, "empty")
    assert manifest["preflight_evidence"]["abgrenzungsregister"]["sha256"] and report["completion_gate"]["passed"]
    # c) HTTP 403: kein Nullstand, Buchhaltung läuft weiter, Abgrenzungsentscheidung zurückgestellt
    (root / "forbidden").mkdir()
    forbidden = Scenario(root / "forbidden", bilanz_run(root / "forbidden"))
    forbidden.run["abgrenzungsregister_evidence"] = {
        "status": "access_error", "source_url": url, "file_name": "12861.md", "retrieved_via": "microsoft_sharepoint.fetch",
        "checked_at": "2026-10-08T09:00:00+02:00", "http_status": 403, "error_code": "accessDenied", "direct_lookup_attempts": 2,
    }
    forbidden.add("Grün")
    forbidden.add("Grün")
    package, manifest, report = build_ok(forbidden, "forbidden")
    summary = manifest["preflight_evidence"]["abgrenzungsregister"]
    assert summary["status"] == "access_error" and "kein Nullstand" in summary["register_state"]
    text = (package / "02_Buchungspruefung" / "Abgrenzungsregister_Vorschlag.md").read_text(encoding="utf-8")
    assert "Register nicht abrufbar – kein Nullstand angenommen" in text and "403" in text
    assert manifest["status"]["Buchungszeile erzeugt"] == 2 and extf_names(package) == [f"EXTF_Buchungsstapel_{PERIOD}.csv"]
    assert manifest["run_completion"]["status"] == "nicht vollständig abgeschlossen"
    assert any("Abgrenzungsregister nicht abrufbar" in item["item"] for item in manifest["run_completion"]["open_items"])
    assert report["valid"] and report["completion_gate"]["passed"] is False
    # d) 403 darf nicht als bestätigtes Nichtvorhandensein getarnt werden; 404 ist kein access_error.
    load_fails(forbidden, "fake-not-found", "Abrufproblem",
               lambda data: data["run"].__setitem__("abgrenzungsregister_evidence", {**base_not_found, "error_code": "accessDenied"}))
    # Leeres Register mit minimalem Abrufnachweis: normal, kein weiterer Nachweis nötig.
    (root / "minimal").mkdir()
    minimal = Scenario(root / "minimal", bilanz_run(root / "minimal"))
    minimal.run["abgrenzungsregister_evidence"] = {
        "status": "empty", "source_url": url, "file_name": "12861.md",
        "retrieved_via": "microsoft_sharepoint.fetch", "checked_at": "2026-10-08T09:00:00+02:00",
    }
    minimal.add("Grün")
    _, manifest, report = build_ok(minimal, "minimal")
    assert manifest["preflight_evidence"]["abgrenzungsregister"]["status"] == "not_found" and report["completion_gate"]["passed"]
    # Leere Registerdatei mit Inhalt "" ist ebenfalls zulässig.
    (root / "blank").mkdir()
    blank_file = root / "blank" / "register.md"
    blank_file.write_text("", encoding="utf-8")
    blank = Scenario(root / "blank", bilanz_run(root / "blank"))
    blank.run["abgrenzungsregister_evidence"] = {**evidence(blank_file, url), "file_name": "12861.md"}
    blank.add("Grün")
    build_ok(blank, "blank")
    # EÜR: kein Register, Abgrenzungen unzulässig.
    (root / "euer").mkdir()
    euer = Scenario(root / "euer", make_run(root / "euer"))
    euer.add("Grün")
    euer.run.pop("abgrenzungsregister_evidence", None)
    _, manifest, _ = build_ok(euer, "euer")
    assert manifest["preflight_evidence"]["abgrenzungsregister"]["status"] == "not_applicable"
    text = (root / "euer" / "euer" / PACKAGE_DIR / "02_Buchungspruefung" / "Abgrenzungsregister_Vorschlag.md").read_text(encoding="utf-8")
    assert "Einnahmenüberschussrechnung" in text
    load_fails(euer, "euer-accrual", "bei Einnahmenüberschussrechnung (EÜR) sind Rechnungsabgrenzungen unzulässig",
               lambda data: data.__setitem__("accrual_releases", [{**data["transactions"][0]["bookings"][0], "accrual_id": "A1", "period": PERIOD, "booking_date": "2025-12-31"}]))
    load_fails(forbidden, "fake-access", "kein Abrufproblem",
               lambda data: data["run"]["abgrenzungsregister_evidence"].__setitem__("http_status", 404))
    load_fails(forbidden, "single-attempt", "mindestens zwei Direktabrufe",
               lambda data: data["run"]["abgrenzungsregister_evidence"].__setitem__("direct_lookup_attempts", 1))


# 4./5. Klärungsquote ------------------------------------------------------------

def quota_scenario(root: Path, green: int, red: int) -> Scenario:
    scenario = Scenario(root, make_run(root))
    for _ in range(green):
        scenario.add("Grün")
    for _ in range(red):
        scenario.add("Rot", reason="Kontierung offen; Leistungsart nicht erkennbar.",
                     bookings=[red_booking(account=None, open_fields={"account": "Leistungsart aus Beleg nicht erkennbar."})])
    return scenario


def test_clarification_rate_second_review(root: Path) -> None:
    scenario = quota_scenario(root, 85, 15)
    red_ids = [doc["transaction_id"] for doc in scenario.docs if doc["traffic_light"] == "Rot"]
    corrected = [doc["transaction_id"] for doc in scenario.docs[:10]]  # nach Belegprüfung auf Grün korrigiert
    corrections = [
        {"transaction_id": tid, "from": "Rot", "to": "Grün", "reason": f"{tid}: Konto aus DATEV-Vorbuchung des Kreditors eindeutig; Belegbild bestätigt Leistungsart."}
        for tid in corrected
    ]
    def with_review(data: dict) -> None:
        review = second_review(red_ids + corrected, corrections, cause={"konto_unklar": "15 Lieferanten ohne Leistungsbeschreibung; keine systematische Fehleinstufung."})
        review["second_review"]["before"] = {"N": 100, "R": 25}
        data["clarification_review"] = review
    package, manifest, report = build_ok(scenario, "quota", with_review)
    rate = manifest["clarification_rate"]
    assert (rate["before"]["N"], rate["before"]["R"], rate["before"]["Q"]) == (100, 25, 25.0)
    assert (rate["after"]["N"], rate["after"]["R"], rate["after"]["Q"]) == (100, 15, 15.0)
    assert rate["before"]["stage"] == "zweitpruefung" and rate["after"]["stage"] == "ursachenpruefung"
    assert rate["second_review_required"] and rate["second_review_performed"] and rate["reviewed_cases"] == 25
    assert len(rate["corrected_to_green"]) == 10 and rate["remaining_red"] == 15
    assert rate["result"] == "fachlich kontrolliert"
    text = (package / "02_Buchungspruefung" / "Klaerungsquote_Nachweis.md").read_text(encoding="utf-8")
    assert "| N (buchungsrelevante Vorgänge) | 100 | 100 |" in text
    assert "| R (rote Vorgänge) | 25 | 15 |" in text and "25,0 %" in text and "15,0 %" in text
    assert "Konto aus DATEV-Vorbuchung" in text and "Konto unklar" in text and "Prüfdatum" in text
    assert report["clarification_rate"]["before"]["Q"] == 25.0 and report["clarification_rate"]["Q"] == 15.0
    workbook = load_workbook(next((package / "02_Buchungspruefung").glob("*.xlsx")))
    sheet_text = " ".join(str(cell.value) for row in workbook["Klärungsquote"] for cell in row)
    assert "25.0 %" in sheet_text and "15.0 %" in sheet_text and "Konto unklar" in sheet_text
    workbook.close()
    assert len(csv_rows(package / "01_DATEV_Import" / f"EXTF_Klaerungsposten_{PERIOD}.csv")) == 15

    # Ohne Zweitprüfung bei Q = 25 %: Nacharbeit verlangt, kein Paket.
    def no_review(data: dict) -> None:
        data["clarification_review"] = {"second_review": {"performed": False, "corrections": corrections}}
    build_fails(scenario, "no-review", "Zweitprüfung aller 25 roten Vorgänge ist Pflicht", no_review)
    def partial_review(data: dict) -> None:
        review = second_review(red_ids[3:] + corrected, corrections, cause={"konto_unklar": "x"})
        data["clarification_review"] = review
    build_fails(scenario, "partial-review", "Zweitprüfung unvollständig", partial_review)
    def wrong_before(data: dict) -> None:
        review = second_review(red_ids + corrected, corrections, cause={"konto_unklar": "x"})
        review["second_review"]["before"] = {"N": 100, "R": 30}
        data["clarification_review"] = review
    build_fails(scenario, "wrong-before", "widerspricht den dokumentierten Korrekturen", wrong_before)
    def unjustified(data: dict) -> None:
        review = second_review(red_ids + corrected, [{**item, "reason": ""} for item in corrections], cause={"konto_unklar": "x"})
        data["clarification_review"] = review
    build_fails(scenario, "unjustified", "ohne konkrete fachliche Begründung", unjustified)
    # CLI-Prüfung vor dem Paketbau.
    cli = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "clarification_rate.py"), "--input", str(scenario.root / "quota.json")],
        capture_output=True, text=True, encoding="utf-8",
    )
    assert cli.returncode == 0 and '"Q": 25.0' in cli.stdout and '"Q": 15.0' in cli.stdout, cli.stderr
    # Validator erkennt manipulierte Nachweise.
    tampered = copy.deepcopy(manifest)
    tampered["clarification_rate"]["after"]["R"] = 5
    assert any("Exportnachweis ergibt" in item for item in validate_package.validate_clarification_rate(package, tampered)[0])
    tampered = copy.deepcopy(manifest)
    tampered["clarification_rate"]["second_review_performed"] = False
    assert any("Zweitprüfung" in item for item in validate_package.validate_clarification_rate(package, tampered)[0])


def test_high_rate_stays_open(root: Path) -> None:
    scenario = quota_scenario(root, 70, 30)
    red_ids = [doc["transaction_id"] for doc in scenario.docs if doc["traffic_light"] == "Rot"]
    def with_review(data: dict) -> None:
        data["clarification_review"] = second_review(red_ids, [], cause={"konto_unklar": "30 Rechnungen ohne Leistungsbeschreibung eines neuen Lieferanten; Belegbild, Profil, DATEV-Bestand und Regeln erneut geprüft; berechtigt Rot."})
    package, manifest, report = build_ok(scenario, "high", with_review)
    rate = manifest["clarification_rate"]
    assert rate["before"]["Q"] == 30.0 and rate["after"]["Q"] == 30.0 and rate["after"]["stage"] == "zweitpruefung"
    assert rate["second_review_performed"] and rate["reviewed_cases"] == 30 and rate["corrected_to_green"] == []
    assert rate["professionally_open"] is True and rate["result"] == "fachlich kontrolliert"
    assert manifest["ampel"]["Rot"] == 30 and len(csv_rows(package / "01_DATEV_Import" / f"EXTF_Klaerungsposten_{PERIOD}.csv")) == 30
    text = (package / "02_Buchungspruefung" / "Klaerungsquote_Nachweis.md").read_text(encoding="utf-8")
    assert "fachlich offen" in text and "berechtigt rote Fälle bleiben Rot" in text
    assert report["valid"] and report["completion_gate"]["passed"] is True
    assert rate["systematic_categories"][0]["code"] == "konto_unklar"
    # Dieselbe Quote ohne Ursachenprüfung der auffällig häufigen Kategorie: Nacharbeit, kein Abbruch.
    def without_cause(data: dict) -> None:
        data["clarification_review"] = second_review(red_ids, [])
    build_fails(scenario, "no-cause", "ungewöhnlich häufig", without_cause)


# 6. Mehrfachzeilen und Dubletten -------------------------------------------------

def test_multiline_and_duplicates(root: Path) -> None:
    scenario = Scenario(root, make_run(root))
    scenario.add("Grün")
    scenario.add("Grün")
    scenario.add("Rot", reason="Kontierung offen.", bookings=[
        red_booking(amount="29.75", account=None, open_fields={"account": "Kontierung offen."}) for _ in range(4)
    ])
    duplicate = scenario.add("Grün")
    duplicate.update({
        "processing_status": "sichere Dublette – nicht erneut gebucht", "traffic_light": None, "bookings": [],
        "exclusion_reason": "Rechnung RE-1 bereits in DATEV gebucht (BU 2025-12/0007).",
        "prior_booking_check": {"checked": True, "result": "sichere_dublette", "references": ["BU 2025-12/0007"]},
    })
    duplicate["duplicate_checks"]["datev_live"] = {"checked": True, "result": "secure_duplicate", "reference": "BU 2025-12/0007"}
    data = build_package.load_input(write_run(scenario, "count"))
    summary, errors = clarification_rate.compute_clarification_rate(data)
    assert errors == [], errors
    assert (summary["after"]["N"], summary["after"]["R"], summary["after"]["Q"]) == (3, 1, 33.3)
    assert summary["counts"]["rote_buchungszeilen"] == 4 and summary["counts"]["rote_vorgaenge"] == 1
    assert summary["counts"]["sichere_dubletten"] == 1 and summary["counts"]["bereits_in_datev_vorhanden"] == 1
    package, manifest, _ = build_ok(scenario, "count-package")
    assert manifest["clarification_rate"]["after"]["R"] == 1 and manifest["booking_batches"][1]["rows"] == 4
    index = json.loads((package / "03_Technische_Protokolle" / "Belegindex.json").read_text(encoding="utf-8"))
    assert next(item for item in index if "V0004" in item["transaction_ids"])["included"] is False


# 7. Scan ohne Textebene ---------------------------------------------------------

def test_scan_without_text_layer(root: Path) -> None:
    scenario = Scenario(root, make_run(root))
    scenario.add("Grün", derivation="Belegbild ausgewertet: Rechnung lesbar, 119 EUR, 4900 gegen 70001.")
    scenario.sources[-1]["readability"] = "image_only"
    assert scenario.document_errors("scan-green") == []
    build_ok(scenario, "scan-green")
    # technisch_unlesbar nur mit dokumentierter Belegbildprüfung
    red = scenario.add("Rot", reason="Betrag auf dem Belegbild unlesbar.", total_amount=None,
                       bookings=[red_booking(amount=None, open_fields={"amount": "Betrag auf dem Belegbild unlesbar."})],
                       red_reason=red_reason("technisch_unlesbar"))
    scenario.sources[-1]["readability"] = "partially_readable"
    assert any("evaluation_attempts" in item for item in scenario.document_errors("scan-red-missing"))
    red["evaluation_attempts"] = [{"method": "textebene", "result": "keine Textebene"}]
    assert any("Belegbildprüfung" in item for item in scenario.document_errors("scan-red-ocr-only"))
    red["evaluation_attempts"] = [{"method": "textebene", "result": "keine Textebene"}, {"method": "belegbild", "result": "Betrag verschmiert, Rest lesbar"}]
    assert scenario.document_errors("scan-red-ok") == []
    # Status technisch nicht auswertbar: nur nach dokumentiertem Versuch, zählt nicht zu N.
    broken = scenario.add("Grün")
    unreadable_doc(broken, None)
    assert any("evaluation_attempts" in item for item in scenario.document_errors("unreadable-missing"))
    unreadable_doc(broken, FULL_ATTEMPTS)
    assert scenario.document_errors("unreadable-ok") == []
    package, manifest, report = build_ok(scenario, "unreadable")
    assert manifest["status"]["technisch nicht auswertbar"] == 1
    assert manifest["clarification_rate"]["after"]["N"] == 2 and manifest["clarification_rate"]["counts"]["technisch_nicht_auswertbar"] == 1
    workbook = load_workbook(next((package / "02_Buchungspruefung").glob("*.xlsx")))
    rows = {row[2].value: row for row in list(workbook["Belegprüfung"].rows)[1:]}
    assert "Technisch nicht auswertbar" in str(rows[broken["transaction_id"]][12].value)
    workbook.close()
    assert report["completion_gate"]["passed"]


# 8. Vollständigkeits-Gate --------------------------------------------------------

def test_completeness_gate(root: Path) -> None:
    scenario = Scenario(root, make_run(root))
    scenario.add("Grün")
    scenario.add("Rot", reason="Kontierung offen.", bookings=[red_booking(account=None, open_fields={"account": "Kontierung offen."})])
    package, manifest, report = build_ok(scenario, "full")
    assert report["completion_gate"]["passed"] is True
    inventory_only = root / "inventory-only" / PACKAGE_DIR
    shutil.copytree(package / "03_Technische_Protokolle", inventory_only / "03_Technische_Protokolle")
    report = run_validator(inventory_only)
    assert report["valid"] is False and report["completion_gate"]["passed"] is False
    assert any("Pflichtdatei fehlt" in item for item in report["errors"]) and any("EXTF" in item for item in report["errors"])
    excel_only = root / "excel-only" / PACKAGE_DIR
    (excel_only / "02_Buchungspruefung").mkdir(parents=True)
    shutil.copy2(next((package / "02_Buchungspruefung").glob("*.xlsx")), excel_only / "02_Buchungspruefung")
    report = run_validator(excel_only)
    assert report["valid"] is False and "Laufmanifest fehlt" in report["errors"]
    partial = root / "partial" / PACKAGE_DIR
    shutil.copytree(package, partial)
    (partial / "02_Buchungspruefung" / "Klaerungsquote_Nachweis.md").unlink()
    report = run_validator(partial)
    assert any("Klaerungsquote_Nachweis.md" in item for item in report["errors"])
    # Abschluss-Gate darf keine DATEV-Übertragung behaupten.
    claimed = root / "claimed" / PACKAGE_DIR
    shutil.copytree(package, claimed)
    manifest_path = claimed / "03_Technische_Protokolle" / "Laufmanifest.json"
    tampered = json.loads(manifest_path.read_text(encoding="utf-8"))
    tampered["run_completion"]["datev_import_claimed"] = True
    manifest_path.write_text(json.dumps(tampered, ensure_ascii=False), encoding="utf-8")
    assert any("DATEV-Übertragung" in item for item in run_validator(claimed)["errors"])


# 9. Version -----------------------------------------------------------------------

def test_version(root: Path) -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert f"# BK Monatsbuchhaltung v{VERSION}" in skill and f"Startnachweis: bk-monatsbuchhaltung v{VERSION}" in skill
    assert f"Version `{VERSION}`" in skill
    assert f"BK Monatsbuchhaltung v{VERSION}" in (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
    assert build_package.SKILL_VERSION == VERSION and validate_package.EXPECTED_SKILL_VERSION == VERSION
    for path in [SKILL_ROOT / "SKILL.md", SKILL_ROOT / "agents" / "openai.yaml", *sorted((SKILL_ROOT / "references").glob("*.md")),
                 SCRIPT_DIR / "build_package.py", SCRIPT_DIR / "validate_package.py", SCRIPT_DIR / "datev_io.py"]:
        assert "1.4.2" not in path.read_text(encoding="utf-8"), f"{path.name} verweist auf 1.4.2"
    for manifest_path in (SKILL_ROOT.parent / ".codex-plugin" / "plugin.json", SKILL_ROOT / ".codex-plugin" / "plugin.json"):
        if manifest_path.is_file():
            assert json.loads(manifest_path.read_text(encoding="utf-8")).get("version") == VERSION
    scenario = Scenario(root, make_run(root))
    scenario.add("Grün")
    _, manifest, report = build_ok(scenario, "version")
    assert manifest["skill_version"] == VERSION and report["skill_version_expected"] == VERSION


# 10. Belegdateiregel ---------------------------------------------------------------

def multi_page_pdf(path: Path, pages: int) -> Path:
    from pypdf import PdfWriter
    writer = PdfWriter()
    for number in range(pages):
        # Unterschiedliche Seitengrößen, damit abgeleitete Einzelseiten verschiedene SHA-256 erhalten.
        writer.add_blank_page(width=595 + number, height=842)
    with path.open("wb") as handle:
        writer.write(handle)
    return path


def test_document_file_rule(root: Path) -> None:
    # a) Sammel-PDF mit drei Buchungsbelegen wird zurückgewiesen.
    (root / "bundle").mkdir()
    scenario = Scenario(root / "bundle", make_run(root / "bundle"))
    for _ in range(3):
        scenario.add("Grün")
    input_dir = root / "bundle" / "input"
    input_dir.mkdir()
    bundle = multi_page_pdf(input_dir / "sammel.pdf", 3)
    scenario.sources = [source_entry(bundle, "S1")]
    scenario.mappings = [{"transaction_id": doc["transaction_id"], "source_id": "S1", "role": "primary_invoice"} for doc in scenario.docs]
    build_fails(scenario, "bundle", "Sammeldatei enthält mehrere Buchungsbelege")
    # b) Aufteilung mit beleg_pdf.py: je Vorgang eine eigene PDF, Original als bundle_original.
    work = root / "bundle" / "work"
    parts = beleg_pdf.split(bundle, work, [f"{doc['transaction_id']}:{number}" for number, doc in enumerate(scenario.docs, start=1)])
    assert [item["pages"] for item in parts] == ["1-1", "2-2", "3-3"]
    scenario.sources = [source_entry(bundle, "S1")] + [
        source_entry(Path(item["path"]), f"D{number}", readability="image_only",
                     derived_from={"source_ids": ["S1"], "method": "split", "pages": item["pages"], "tool": "scripts/beleg_pdf.py"})
        for number, item in enumerate(parts, start=1)
    ]
    scenario.mappings = [
        {"transaction_id": doc["transaction_id"], "source_id": "S1", "role": "bundle_original"} for doc in scenario.docs
    ] + [
        {"transaction_id": doc["transaction_id"], "source_id": f"D{number}", "role": "primary_invoice"}
        for number, doc in enumerate(scenario.docs, start=1)
    ]
    package, manifest, report = build_ok(scenario, "split")
    assert manifest["hochgeladene_dateien"] == 1 and manifest["abgeleitete_belegdateien"] == 3 and manifest["quelldateien"] == 4
    assert manifest["document_file_rule"] == "ein Buchungsbeleg = genau eine eigene PDF-Datei"
    index = json.loads((package / "03_Technische_Protokolle" / "Belegindex.json").read_text(encoding="utf-8"))
    original = next(item for item in index if item["source_id"] == "S1")
    assert original["included"] is False and "Original" in original["reason"]
    included = [item for item in index if item["included"]]
    assert len(included) == 3 and all(len(item["primary_transaction_ids"]) == 1 for item in included)
    assert all(item["technical_filename"].endswith(".pdf") and item["derived_from"]["method"] == "split" for item in included)
    import zipfile
    with zipfile.ZipFile(next((package / "01_DATEV_Import").glob("Belegtransfer_*.zip"))) as archive:
        names = [name for name in archive.namelist() if name != "document.xml"]
        assert len(names) == 3 and all(name.endswith(".pdf") for name in names)
    assert report["document_file_rule"] and report["valid"]
    # Original ohne abgeleitete PDF oder abgeleitete PDF ohne Original: Generatorfehler.
    def orphan_original(data: dict) -> None:
        data["source_files"] = [item for item in data["source_files"] if item["source_id"] != "D1"]
        data["transaction_sources"] = [item for item in data["transaction_sources"] if item["source_id"] != "D1"]
    build_fails(scenario, "orphan", "ohne eigene PDF-Datei", orphan_original)
    # Validator: manipulierter Belegindex mit zwei Primärbelegen in einer Datei.
    tampered_index = copy.deepcopy(index)
    next(item for item in tampered_index if item["included"])["primary_transaction_ids"] = ["V0001", "V0002"]
    tampered_dir = root / "bundle" / "tampered" / PACKAGE_DIR
    shutil.copytree(package, tampered_dir)
    (tampered_dir / "03_Technische_Protokolle" / "Belegindex.json").write_text(json.dumps(tampered_index), encoding="utf-8")
    errors = validate_package.validate_document_file_rule(tampered_dir, manifest)
    assert any("mehrere Buchungsbelege" in item for item in errors), errors

    # c) Ein Beleg auf zwei Dateien verteilt: zusammenführen.
    (root / "spread").mkdir()
    spread = Scenario(root / "spread", make_run(root / "spread"))
    spread.add("Grün")
    page2 = write_pdf(root / "spread" / "seite2.pdf", "Seite 2")
    spread.sources.append(source_entry(page2, "S2"))
    spread.mappings.append({"transaction_id": "V0001", "source_id": "S2", "role": "primary_invoice"})
    build_fails(spread, "spread", "auf mehrere Dateien verteilt")
    first = Path(spread.sources[0]["source_path"])
    merged = beleg_pdf.merge([multi_page_pdf(root / "spread" / "s1.pdf", 1), multi_page_pdf(root / "spread" / "s2.pdf", 1)], root / "spread" / "work" / "V0001.pdf")
    spread.sources = [source_entry(first, "S1"), source_entry(page2, "S2"),
                      source_entry(Path(merged["path"]), "D1", derived_from={"source_ids": ["S1", "S2"], "method": "merge"})]
    spread.mappings = [
        {"transaction_id": "V0001", "source_id": "S1", "role": "converted_original"},
        {"transaction_id": "V0001", "source_id": "S2", "role": "converted_original"},
        {"transaction_id": "V0001", "source_id": "D1", "role": "primary_invoice"},
    ]
    _, manifest, _ = build_ok(spread, "merged")
    assert manifest["abgeleitete_belegdateien"] == 1 and manifest["hochgeladene_dateien"] == 2

    # d) Bild- oder Textbeleg als Buchungsbeleg: erst nach Umwandlung in PDF zulässig.
    (root / "image").mkdir()
    image = Scenario(root / "image", make_run(root / "image"))
    image.add("Grün")
    from PIL import Image
    jpg = root / "image" / "quittung.jpg"
    Image.new("RGB", (300, 200), "white").save(jpg)
    image.sources = [source_entry(jpg, "S1")]
    image.mappings = [{"transaction_id": "V0001", "source_id": "S1", "role": "primary_invoice"}]
    build_fails(image, "jpg", "keine PDF-Datei")
    converted = beleg_pdf.convert(jpg, root / "image" / "work" / "V0001.pdf")
    image.sources = [source_entry(jpg, "S1"), source_entry(Path(converted["path"]), "D1", derived_from={"source_ids": ["S1"], "method": "convert"})]
    image.mappings = [
        {"transaction_id": "V0001", "source_id": "S1", "role": "converted_original"},
        {"transaction_id": "V0001", "source_id": "D1", "role": "primary_invoice"},
    ]
    build_ok(image, "converted")
    txt = root / "image" / "beleg.txt"
    txt.write_text("Textbeleg", encoding="utf-8")
    image.sources = [source_entry(txt, "S1")]
    image.mappings = [{"transaction_id": "V0001", "source_id": "S1", "role": "primary_invoice"}]
    build_fails(image, "txt", "keine PDF-Datei")
    # Begleitdokumente dürfen eigene Nicht-PDF-Dateien bleiben.
    (root / "support").mkdir()
    support = Scenario(root / "support", make_run(root / "support"))
    support.add("Grün")
    mail = root / "support" / "mail.txt"
    mail.write_text("Begleit-E-Mail", encoding="utf-8")
    support.sources.append(source_entry(mail, "S2"))
    support.mappings.append({"transaction_id": "V0001", "source_id": "S2", "role": "supporting_document"})
    package, manifest, _ = build_ok(support, "support")
    assert manifest["quelldateien"] == 2
    index = json.loads((package / "03_Technische_Protokolle" / "Belegindex.json").read_text(encoding="utf-8"))
    assert next(item for item in index if item["source_id"] == "S2")["included"] is False
    assert sum(1 for item in index if item["included"]) == 1
    # info: Textebene je Seite.
    info = beleg_pdf.info(bundle)
    assert info["page_count"] == 3 and info["suggested_readability"] == "image_only" and "Belegbild" in info["note"]


# 11. Nachschärfungen: Riecken-Pflicht und "Kreditor fehlt" ist kein Rot-Grund --------

def test_riecken_and_creditor_rule(root: Path) -> None:
    # Riecken-Connector ist Pflicht.
    (root / "connector").mkdir()
    other = Scenario(root / "connector", make_run(root / "connector"))
    other.add("Grün")
    load_fails(other, "other-connector", "Riecken-Connector",
               lambda data: data["run"]["datev_live_evidence"].__setitem__("connector", "Klardaten"))
    load_fails(other, "no-connector", "Riecken-Connector",
               lambda data: data["run"]["datev_live_evidence"].pop("connector"))
    load_fails(other, "no-tool", "retrieved_via nennt kein Riecken-Werkzeug",
               lambda data: data["run"]["datev_live_evidence"]["retrieved_via"].__setitem__("prior_bookings", "Erinnerung aus Vorlauf"))
    _, manifest, _ = build_ok(other, "riecken")
    assert manifest["preflight_evidence"]["datev"]["connector"] == "Riecken"
    tampered = copy.deepcopy(manifest)
    tampered["preflight_evidence"]["datev"]["connector"] = "anderer Zugang"
    assert any("Riecken" in item for item in validate_package._validate_preflight_manifest(tampered))

    # "Kreditor fehlt" ist kein Rot-Grund.
    (root / "creditor").mkdir()
    scenario = Scenario(root / "creditor", make_run(root / "creditor"))
    scenario.add("Grün")
    red = scenario.add("Rot", reason="Kreditor fehlt in DATEV.",
                       bookings=[red_booking(contra_account=None, contra_account_name=None, open_fields={"contra_account": "Kreditor nicht angelegt."})],
                       red_reason=red_reason("personenkonto_unklar"))
    errors = scenario.document_errors("creditor-missing")
    assert any("kein Rot-Grund" in item for item in errors), errors
    assert any("partner_check" in item for item in errors), errors
    # no_match bedeutet Neuanlage, nicht Rot.
    red["reason"] = "Geschäftspartner laut Beleg eindeutig, Personenkonto offen."
    red["bookings"][0]["open_fields"] = {"contra_account": "Personenkonto offen."}
    red["red_reason"] = red_reason("personenkonto_unklar", partner_check={"tool": "datev_search_business_partners", "query": "Neu GmbH", "result": "no_match"})
    assert any("Neuanlage" in item for item in scenario.document_errors("creditor-no-match"))
    # Auch ein anderer Code rettet eine "Kreditor fehlt"-Begründung nicht.
    red["reason"] = "Lieferant nicht angelegt."
    red["red_reason"] = red_reason("konto_unklar")
    assert any("kein Rot-Grund" in item for item in scenario.document_errors("creditor-other-code"))
    # Zulässig: dokumentierte Mehrdeutigkeit der Geschäftspartneridentität.
    red["reason"] = "Geschäftspartneridentität nicht eindeutig: zwei Einzelkreditoren Müller Bau."
    red["red_reason"] = red_reason("personenkonto_unklar", partner_check={
        "tool": "datev_search_business_partners", "query": "Müller Bau", "result": "ambiguous",
        "detail": "70012 Müller Bau GmbH und 70058 Müller Bauservice; Beleg ohne Rechtsform und USt-ID.",
    })
    assert scenario.document_errors("creditor-ambiguous") == []
    build_ok(scenario, "creditor-ok")
    # error nur mit technical_incidents-Eintrag.
    red["red_reason"]["partner_check"].update({"result": "error"})
    assert any("technical_incidents" in item for item in scenario.document_errors("creditor-error"))

    # Jeder Beleg ein eigenes Dokument: merge darf keine zwei Belege zusammenfassen.
    (root / "twobelege").mkdir()
    two = Scenario(root / "twobelege", make_run(root / "twobelege"))
    two.add("Grün")
    two.add("Grün")
    a = multi_page_pdf(root / "twobelege" / "a.pdf", 1)
    b = multi_page_pdf(root / "twobelege" / "b.pdf", 2)
    merged = beleg_pdf.merge([a, b], root / "twobelege" / "work" / "beide.pdf")
    two.sources = [source_entry(a, "S1"), source_entry(b, "S2"),
                   source_entry(Path(merged["path"]), "D1", derived_from={"source_ids": ["S1", "S2"], "method": "merge"})]
    two.mappings = [
        {"transaction_id": "V0001", "source_id": "S1", "role": "converted_original"},
        {"transaction_id": "V0002", "source_id": "S2", "role": "converted_original"},
        {"transaction_id": "V0001", "source_id": "D1", "role": "primary_invoice"},
        {"transaction_id": "V0002", "source_id": "D1", "role": "primary_invoice"},
    ]
    build_fails(two, "two-in-one", "niemals mehrere Belege zu einer Datei")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="bk_v141_") as name:
        root = Path(name)
        for case in (
            test_anti_abort, test_single_failure_continues, test_accrual_register_states,
            test_clarification_rate_second_review, test_high_rate_stays_open, test_multiline_and_duplicates,
            test_scan_without_text_layer, test_completeness_gate, test_version, test_document_file_rule,
            test_riecken_and_creditor_rule,
        ):
            case_root = root / case.__name__
            case_root.mkdir()
            case(case_root)
    print("v1.4.1 Durchführungspflicht, Klärungsquote, Abgrenzungsregister, Belegdateiregel und Version: OK")


if __name__ == "__main__":
    main()
