"""Regressionstests v1.5.1: Begründung aus dem Beleg in Klartext (übernommen aus dem Branch claude/friendly-franklin-tsti28, dort als v1.5.0)."""
from __future__ import annotations

import copy
import sys
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from openpyxl import load_workbook

import build_package
import datev_io
import validate_package
from test_v140_contract import PERIOD, Scenario, make_run, red_booking


def expect_issue(errors: list[str], fragment: str, label: str) -> None:
    assert any(fragment in item for item in errors), f"{label}: {fragment!r} nicht gemeldet; Meldungen: {errors}"


def test_plain_language_helpers() -> None:
    assert datev_io.plain_language_issues("Rechnung über 47,00 EUR, bar bezahlt in Hasbergen.", "x") == []
    issues = datev_io.plain_language_issues("account: 492000 oder privat; siehe open_fields", "x")
    assert issues and "account" in issues[0] and "open_fields" in issues[0]
    assert datev_io.plain_language_issues("Über Riecken nichts gefunden.", "x")
    assert datev_io.plain_language_issues("Kontierung prüfen", "x", reject_generic=True)
    assert datev_io.plain_language_issues("Kontierung offen.", "x", reject_generic=True)
    assert datev_io.single_task_issues("Beim Mandanten fragen, ob der Kaffee für die Praxis ist.") == []
    assert datev_io.single_task_issues("Mandanten fragen. Danach Sachkonto festlegen.")
    assert datev_io.single_task_issues("Rechnung anfordern – Sachkonto festlegen")
    assert datev_io.single_task_issues("")
    assert datev_io.single_task_issues("1. Rechnung anfordern 2. buchen")
    assert datev_io.missing_mapping_issues("Für diesen Lieferanten gibt es keine Standardzuordnung im Profil.", "x")
    assert datev_io.missing_mapping_issues("Neuer Lieferant, bisher nicht gebucht.", "x")
    assert datev_io.missing_mapping_issues("Ohne Anlass ist nicht erkennbar, ob privat oder Bewirtung.", "x") == []


def test_generator_rules(root: Path) -> None:
    base = Scenario(root, make_run(root))
    base.add("Grün")
    base.add("Rot", reason="Abholung von vier Gerichten, bar bezahlt, Dienstag 11:43 in Hasbergen rund 60 km von der Praxis; kein Bewirtungsnachweis, keine Teilnehmer, kein Anlass.",
             next_step="Beim Mandanten nach dem Anlass des Essens fragen.",
             bookings=[red_booking(account=None, open_fields={"account": "Ohne Anlass ist nicht entscheidbar, ob privat oder Bewirtung mit Nachweis."})])
    assert base.document_errors("ok") == []

    # Technischer Bezeichner in der Begründung.
    broken = copy.deepcopy(base)
    broken.docs[1]["reason"] = "account: Betrieblicher Anlass nicht belegt; 180100 oder 465000 je nach Nachweis."
    expect_issue(broken.document_errors("token"), "technische Bezeichner", "Feldname in reason")
    # Pauschale Begründung.
    broken = copy.deepcopy(base)
    broken.docs[1]["reason"] = "Kontierung prüfen."
    expect_issue(broken.document_errors("generic"), "pauschale Begründung", "generische reason")
    # Connector als Begründung.
    broken = copy.deepcopy(base)
    broken.docs[1]["reason"] = "Über den Riecken-Connector wurde zu diesem Lieferanten keine Vorbuchung gefunden."
    expect_issue(broken.document_errors("connector"), "technische Bezeichner", "Connector in reason")
    # Fehlende Standardzuordnung ist kein Klärungsgrund.
    broken = copy.deepcopy(base)
    broken.docs[1]["reason"] = "Für den Lieferanten WOK point gibt es keine Standardzuordnung im Mandantenprofil."
    expect_issue(broken.document_errors("mapping"), "kein zulässiger Klärungsgrund", "Standardzuordnung als Rot-Grund")
    broken = copy.deepcopy(base)
    broken.docs[1]["bookings"][0]["open_fields"] = {"account": "Kein Buchungsmuster für diesen Lieferanten vorhanden."}
    expect_issue(broken.document_errors("mapping-open"), "kein zulässiger Klärungsgrund", "Buchungsmuster in offenem Feld")
    broken = copy.deepcopy(base)
    broken.cases[0]["facts"] = "Lieferant ist neu, keine Vorbuchung in DATEV."
    expect_issue(build_package.validate_clarifications(broken.load("mapping-case")), "kein zulässiger Klärungsgrund", "Vorbuchung in Klärungsfall")
    # Beleg zeigt fehlt.
    broken = copy.deepcopy(base)
    broken.docs[0]["document_summary"] = ""
    expect_issue(broken.document_errors("summary"), "Beleg zeigt", "document_summary fehlt")
    # Nächster Schritt fehlt oder enthält zwei Aufgaben.
    broken = copy.deepcopy(base)
    broken.docs[1].pop("next_step")
    expect_issue(broken.document_errors("nostep"), "Nächster Schritt: fehlt", "next_step fehlt")
    broken = copy.deepcopy(base)
    broken.docs[1]["next_step"] = "Beim Mandanten nach dem Anlass fragen. Danach das Sachkonto festlegen."
    expect_issue(broken.document_errors("twosteps"), "mehr als eine Aufgabe", "zwei Aufgaben")
    broken = copy.deepcopy(base)
    broken.docs[1]["next_step"] = "Mandanten fragen – Sachkonto festlegen"
    expect_issue(broken.document_errors("dash"), "mehr als eine Aufgabe", "Gedankenstrich-Kette")
    # Offene Felder und Klärungsfälle ebenfalls in Klartext.
    broken = copy.deepcopy(base)
    broken.docs[1]["bookings"][0]["open_fields"] = {"account": "account offen, siehe JSON."}
    expect_issue(broken.document_errors("openfield"), "Begründung offenes Feld", "technischer Text in open_fields")
    broken = copy.deepcopy(base)
    broken.cases[0]["topic"] = "contra_account"
    data = broken.load("case")
    expect_issue(build_package.validate_clarifications(data), "Thema: technische Bezeichner", "Klärungsfall-Thema")
    # Grün braucht keinen nächsten Schritt; Ausschlüsse brauchen Klartext.
    excluded = copy.deepcopy(base)
    doc = excluded.add("Grün")
    doc.update({"processing_status": "nicht buchungsrelevant", "traffic_light": None, "bookings": [],
                "exclusion_reason": "Kontoauszug der Bank; wird im Bankprozess verarbeitet.", "handoff_required": False})
    doc.pop("prior_booking_check", None)
    assert excluded.document_errors("excluded") == []
    doc["exclusion_reason"] = "siehe processing_status"
    expect_issue(excluded.document_errors("excluded-token"), "Ausschlussgrund", "technischer Ausschlussgrund")


def test_workbook(root: Path) -> None:
    scenario = Scenario(root, make_run(root))
    scenario.add("Grün")
    scenario.add(
        "Rot",
        partner="WOK point, Hong Wen, Hasbergen",
        document_summary="Kassenbon des WOK point in Hasbergen vom 11.08.2026, 11:43 Uhr, vier Gerichte zum Mitnehmen, 47,00 EUR bar bezahlt, 7 % Umsatzsteuer.",
        derivation="Hasbergen liegt am Privatwohnort, rund 60 km von der Praxis; auf dem Bon stehen weder Teilnehmer noch Anlass.",
        reason="Ohne Anlass und Teilnehmer ist nicht erkennbar, ob es sich um private Verpflegung oder um eine Bewirtung handelt.",
        next_step="Beim Mandanten nach dem Anlass des Essens und den Teilnehmern fragen.",
        bookings=[red_booking(account=None, open_fields={"account": "Je nach Anlass privat oder Bewirtung mit Nachweis; ohne Antwort nicht entscheidbar."})],
    )
    scenario.cases[-1]["booking_risk"] = "Private Verpflegung würde als Betriebsausgabe gebucht."
    package, manifest, report = scenario.build("workbook")
    assert report["valid"], report["errors"]
    workbook = load_workbook(next((package / "02_Buchungspruefung").glob("*.xlsx")))
    rows = list(workbook["Belegprüfung"].rows)
    headers = [cell.value for cell in rows[0]]
    assert headers[9:14] == ["Beleg zeigt", "Buchung", "Daraus folgt", "Warum Rot oder Grün?", "Nächster Schritt"], headers
    by_id = {row[2].value: {headers[i]: row[i].value for i in range(len(headers))} for row in rows[1:]}
    red = by_id["V0002"]
    assert red["Beleg zeigt"].startswith("Kassenbon des WOK point")
    assert red["Buchung"].startswith("119,00 EUR: Soll Sachkonto noch offen, Haben 70001 DATEV Test GmbH")
    assert "Steuerschlüssel 401" in red["Buchung"] and "offen: Sachkonto" in red["Buchung"]
    assert "BU " not in red["Buchung"] and "BF1" not in red["Buchung"]
    assert red["Warum Rot oder Grün?"].startswith("Ohne Anlass und Teilnehmer")
    assert "Risiko: Private Verpflegung" in red["Warum Rot oder Grün?"]
    assert "Offen bleibt: Sachkonto:" in red["Warum Rot oder Grün?"]
    assert red["Nächster Schritt"] == "Beim Mandanten nach dem Anlass des Essens und den Teilnehmern fragen."
    assert red["Bearbeitungsstatus"] == "offen"
    green = by_id["V0001"]
    assert green["Buchung"].startswith("119,00 EUR: Soll 4900 Betriebsbedarf, Haben 70001 DATEV Test GmbH; Steuerschlüssel 401; Belegnummer RE-1")
    assert green["Nächster Schritt"] == "Keine weitere Bearbeitung."
    for row in rows[1:]:
        for cell in row[9:14]:
            assert datev_io.plain_language_issues(cell.value, "Zelle") == [], cell.value
    guide = " ".join(str(cell.value) for row in workbook["Anleitung"] for cell in row)
    assert "genau eine Aufgabe" in guide and "Beleg zeigt" in guide
    workbook.close()
    clarification = (package / "02_Buchungspruefung" / "Klaerungsfaelle.md").read_text(encoding="utf-8")
    assert "Nächster Schritt" in clarification and "Beim Mandanten nach dem Anlass" in clarification
    # Validator weist technische Texte in der Prüfungsdatei zurück.
    assert validate_package.validate_review_workbook(next((package / "02_Buchungspruefung").glob("*.xlsx")), manifest) == []
    tampered = root / "tampered.xlsx"
    wb = load_workbook(next((package / "02_Buchungspruefung").glob("*.xlsx")))
    ws = wb["Belegprüfung"]
    ws.cell(3, headers.index("Nächster Schritt") + 1).value = "account: 180100 oder 465000 festlegen"
    wb.save(tampered)
    errors = validate_package.validate_review_workbook(tampered, manifest)
    assert any("technische Bezeichner" in item for item in errors), errors
    wb = load_workbook(next((package / "02_Buchungspruefung").glob("*.xlsx")))
    ws = wb["Belegprüfung"]
    for row in range(2, ws.max_row + 1):
        if ws.cell(row, 1).value == "Rot":
            ws.cell(row, headers.index("Warum Rot oder Grün?") + 1).value = "Keine Standardzuordnung im Profil hinterlegt."
    wb.save(tampered)
    errors = validate_package.validate_review_workbook(tampered, manifest)
    assert any("kein zulässiger Klärungsgrund" in item for item in errors), errors


def main() -> None:
    test_plain_language_helpers()
    with tempfile.TemporaryDirectory(prefix="bk_v151_") as name:
        root = Path(name)
        for case in (test_generator_rules, test_workbook):
            case_root = root / case.__name__
            case_root.mkdir()
            case(case_root)
    print("v1.5.1 Begründung aus dem Beleg, Klartextspalten, Generator- und Validatorregeln: OK")


if __name__ == "__main__":
    main()
