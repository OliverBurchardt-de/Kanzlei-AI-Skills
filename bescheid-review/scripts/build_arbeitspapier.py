"""Erzeugt das einheitliche Bescheidreview-Arbeitspapier (Burchardt & Kollegen).

Aufruf:
    python build_arbeitspapier.py <daten.json> <ausgabe.xlsx>

Die Datenstruktur (JSON) ist am Ende dieser Datei dokumentiert (BEISPIEL_JSON).
Das Skript garantiert ein identisches Layout fuer jeden Review: gleiche Blaetter,
Spalten, Farben (Kanzlei-Gold #F7B234), Schweregrad-Formatierung, Dropdowns.
Nach dem Erzeugen zwingend recalc.py des xlsx-Skills laufen lassen.
"""
import json
import math
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

GOLD, GREY, INPUT = "F7B234", "F2F2F2", "FFF7E6"
FILL = {
    "A": PatternFill("solid", start_color="FFC7CE"),
    "B": PatternFill("solid", start_color="FFEB9C"),
    "C": PatternFill("solid", start_color="D9D9D9"),
}
SGFONT = {
    "A": Font(color="9C0006", bold=True, size=10),
    "B": Font(color="9C6500", bold=True, size=10),
    "C": Font(bold=True, size=10),
}
HFILL = PatternFill("solid", start_color=GOLD)
FRISTFILL = PatternFill("solid", start_color="FFC7CE")
AMPFILL = {"GRUEN": "C6EFCE", "GELB": "FFEB9C", "ROT": "FFC7CE"}
AMPFONT = {"GRUEN": "006100", "GELB": "9C6500", "ROT": "9C0006"}
thin = Side(style="thin", color="BFBFBF")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
F10, F10B = Font(size=10), Font(size=10, bold=True)
FRED = Font(size=10, bold=True, color="9C0006")
WRAP = Alignment(wrap_text=True, vertical="top")
TOP = Alignment(vertical="top")
NUM = '#,##0.00;[Red](#,##0.00);"-"'

ZEILE_PX = 13.5   # Punkthöhe je Textzeile bei Calibri 10
CHARS_JE_BREITE = 0.92  # sichtbare Zeichen je Excel-Breiteneinheit (konservativ)


def zeilen_hoehe(text_breite_paare, min_h=20.0, max_h=380.0):
    """Schätzt die nötige Zeilenhöhe aus (text, spaltenbreite)-Paaren.

    Für jede umbruchfähige Zelle der Zeile wird die Zeilenzahl geschätzt
    (explizite Umbrüche + Umbruch nach Spaltenbreite); die höchste Zelle
    bestimmt die Zeilenhöhe. Konservativ gerechnet, damit nie Text
    abgeschnitten wird — lieber 1 Zeile Luft als 1 Zeile verdeckt.
    """
    zeilen = 1
    for text, breite in text_breite_paare:
        if text is None:
            continue
        s = str(text)
        cpl = max(8, int(breite * CHARS_JE_BREITE))
        z = sum(max(1, math.ceil(len(seg) / cpl)) for seg in s.split("\n"))
        zeilen = max(zeilen, z)
    return min(max_h, max(min_h, zeilen * ZEILE_PX + 6))

RP_COLS = [
    ("Nr.", 8), ("Schweregrad", 12), ("Kategorie", 16),
    ("Bescheid / Position", 26), ("Betrag (EUR)", 14), ("Frist", 12),
    ("Feststellung", 50), ("Erforderliche Maßnahme", 50),
    ("Antwort Sachbearbeiter", 34), ("Nachweis / Ablage", 18),
    ("Status", 13), ("Prüfvermerk Partner", 18),
]
AB_COLS = [
    ("Position", 38), ("Lt. Berechnung (EUR)", 18), ("Lt. Bescheid (EUR)", 18),
    ("Differenz (EUR)", 16), ("Ursache", 40), ("siehe Punkt", 12),
]
NB_COLS = [
    ("Art", 20), ("Bescheid", 22), ("Fundstelle", 16), ("Inhalt", 48),
    ("Rechtsfolge / Bedeutung", 44), ("Frist", 12), ("siehe Punkt", 12),
]


def kopf(ws, titel, meta):
    ws["A1"] = "Burchardt & Kollegen — Wirtschaftsprüfer · Steuerberater"
    ws["A1"].font = Font(size=12, bold=True)
    ws["A2"] = "Bescheidreview-Arbeitspapier: " + titel
    ws["A2"].font = Font(size=11, bold=True)
    ws["A3"] = (f"Mandant: {meta['mandant']} · StNr. {meta['steuernummer']} · "
                f"{meta['steuerarten_vz']}")
    ws["A3"].font = Font(size=9, italic=True)
    ws["A4"] = f"EINSPRUCHSFRIST: {meta['einspruchsfrist_kurz']}"
    ws["A4"].font = Font(size=10, bold=True, color="9C0006")
    ws["A5"] = f"Review erstellt: {meta['review_datum']} (Claude / Skill bescheid-review)"
    ws["A5"].font = Font(size=9, italic=True, color="808080")


def ampelbanner(ws, row, meta, breit="B", textbreite=120):
    amp = meta.get("ampel", "GELB")
    ws.merge_cells(f"A{row}:{breit}{row}")
    txt = "ERGEBNIS " + amp.replace("GRUEN", "GRÜN") + ": " + meta.get("ampel_text", "")
    c = ws.cell(row, 1, txt)
    c.fill = PatternFill("solid", start_color=AMPFILL[amp])
    c.font = Font(size=12, bold=True, color=AMPFONT[amp])
    c.alignment = Alignment(wrap_text=True, vertical="center")
    # Schrift 12 statt 10 → Höhe je Zeile hochskalieren (12/10)
    ws.row_dimensions[row].height = zeilen_hoehe(
        [(txt, textbreite)], min_h=34.0) * 1.2


def tabellenkopf(ws, row, cols):
    for i, (name, w) in enumerate(cols, 1):
        c = ws.cell(row, i, name)
        c.font, c.fill, c.border = Font(bold=True, size=10), HFILL, BORDER
        c.alignment = Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[row].height = 28  # einheitliche Kopfzeile, 2-zeilig lesbar


def main(datenpfad, ausgabe):
    with open(datenpfad, encoding="utf-8") as f:
        d = json.load(f)
    meta, punkte = d["meta"], d["punkte"]
    wb = Workbook()

    # ---------------- Deckblatt ----------------
    ws = wb.active
    ws.title = "Deckblatt"
    kopf(ws, "Deckblatt", meta)
    ampelbanner(ws, 6, meta)
    zeilen = [
        ("Mandant", meta["mandant"]),
        ("Mandantennummer", meta["mandanten_nr"]),
        ("Steuernummer / Finanzamt", f"{meta['steuernummer']} · {meta['finanzamt']}"),
        ("Bescheide", meta["bescheide"]),
        ("Bescheidfamilie (abgefragt)", meta["bescheidfamilie"]),
        ("Fristenblock (nachrichtlich)", meta["fristenblock"]),
        ("Hinweis Posteingang", meta["hinweis_posteingang"]),
        ("Vorbehalt der Nachprüfung (§ 164 AO)", meta["vdn"]),
        ("Vorläufigkeit (§ 165 AO)", meta["vorlaeufigkeit"]),
        ("Ergebnis / Fälligkeit", meta["ergebnis"]),
        ("Zahlungsweg", meta.get("zahlungsweg", "—")),
        ("Verwendete Dokumente", meta["dokumente"]),
        ("Ersteller Review", "Claude (Skill bescheid-review)"),
        ("Sachbearbeiter", ""), ("Abgearbeitet am", ""),
        ("Frist mit Fristenprogramm abgeglichen am", ""),
        ("Freigabe Partner am", ""),
    ]
    r = 8
    for k, v in zeilen:
        ws.cell(r, 1, k).font = F10B
        ws.cell(r, 1).fill = PatternFill("solid", start_color=GREY)
        ws.cell(r, 1).alignment = WRAP
        c = ws.cell(r, 2, v)
        c.font, c.alignment = F10, WRAP
        if k == "Fristenblock (nachrichtlich)":
            c.font = FRED
            ws.cell(r, 1).font = FRED
        for col in (1, 2):
            ws.cell(r, col).border = BORDER
        # Höhe an den tatsächlichen Text anpassen (Spalte A 34 / B 100 breit)
        ws.row_dimensions[r].height = zeilen_hoehe([(k, 34), (v, 100)])
        r += 1
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 100

    # To-Do-Checkliste kompakt auf dem Deckblatt — der Sachbearbeiter sieht
    # ohne Blättern, was zu tun ist (Details: Blatt Arbeitsanweisung)
    r += 1
    c = ws.cell(r, 1, "TO-DO-CHECKLISTE (abhaken — Details und Erledigt-Spalte: Blatt Arbeitsanweisung)")
    ws.merge_cells(f"A{r}:B{r}")
    c.font = Font(size=10, bold=True)
    c.fill = HFILL
    c.border = BORDER
    ws.cell(r, 2).border = BORDER
    ws.row_dimensions[r].height = 20
    for j, a in enumerate(d.get("arbeitsanweisung", [])):
        r += 1
        zeile = f"☐  {j+1}. {a['aufgabe']}"
        zusatz = " · ".join(x for x in (
            f"Frist {a['frist']}" if a.get("frist") else "",
            a.get("zustaendig", "")) if x)
        if zusatz:
            zeile += f"   [{zusatz}]"
        ws.merge_cells(f"A{r}:B{r}")
        c = ws.cell(r, 1, zeile)
        c.font, c.alignment, c.border = F10, WRAP, BORDER
        ws.cell(r, 2).border = BORDER
        if a.get("frist"):
            c.font = FRED
        # Merge-Breite = Spalte A + B (34 + 100)
        ws.row_dimensions[r].height = zeilen_hoehe([(zeile, 134)])

    # ---------------- Arbeitsanweisung ----------------
    ws = wb.create_sheet("Arbeitsanweisung", 1)
    kopf(ws, "Arbeitsanweisung", meta)
    ampelbanner(ws, 6, meta, breit="E")
    AA_COLS = [("Nr.", 6), ("☐", 5), ("Aufgabe", 78), ("Frist", 13),
               ("Zuständig", 12), ("Erledigt am", 13)]
    HR = 8
    tabellenkopf(ws, HR, AA_COLS)
    for j, a in enumerate(d.get("arbeitsanweisung", [])):
        r = HR + 1 + j
        vals = [j + 1, "☐", a["aufgabe"], a.get("frist", ""),
                a.get("zustaendig", "SB"), ""]
        for i, v in enumerate(vals, 1):
            c = ws.cell(r, i, v)
            c.border, c.font = BORDER, F10
            c.alignment = WRAP if i == 3 else TOP
        ws.cell(r, 1).font = F10B
        ws.cell(r, 2).font = Font(size=12)  # Checkbox gut sichtbar
        ws.cell(r, 2).alignment = Alignment(horizontal="center", vertical="top")
        if a.get("frist"):
            fz = ws.cell(r, 4)
            fz.fill, fz.font = FRISTFILL, FRED
        ws.cell(r, 6).fill = PatternFill("solid", start_color=INPUT)
        ws.row_dimensions[r].height = zeilen_hoehe([(a["aufgabe"], 78)],
                                                   min_h=24.0)
    ws.freeze_panes = f"A{HR+1}"

    # ---------------- Reviewpunkte ----------------
    ws = wb.create_sheet("Reviewpunkte")
    kopf(ws, "Reviewpunkte", meta)
    HR = 7
    tabellenkopf(ws, HR, RP_COLS)
    ordnung = {"A": 0, "B": 1, "C": 2}
    punkte = sorted(punkte, key=lambda p: (
        ordnung[p["schweregrad"]],
        p.get("frist") or "9999-12-31",      # Fristsachen zuerst (ISO-Datum sortiert)
        -(p.get("betrag") or 0)))
    for j, p in enumerate(punkte):
        r = HR + 1 + j
        vals = [f"R-{j+1:03d}", p["schweregrad"], p["kategorie"],
                p["bescheid_position"], p.get("betrag"),
                p.get("frist_anzeige", ""), p["feststellung"], p["massnahme"],
                "", "", "offen", ""]
        for i, v in enumerate(vals, 1):
            c = ws.cell(r, i, v)
            c.border, c.font = BORDER, F10
            # Alle Textspalten umbrechen (3 Kategorie, 4 Position, 7-9 Texte)
            c.alignment = WRAP if i in (3, 4, 7, 8, 9) else TOP
            if i == 5:
                c.number_format = NUM
        sg = ws.cell(r, 2)
        sg.fill, sg.font = FILL[p["schweregrad"]], SGFONT[p["schweregrad"]]
        sg.alignment = Alignment(horizontal="center", vertical="top")
        if p.get("frist_anzeige"):
            fz = ws.cell(r, 6)
            fz.fill, fz.font = FRISTFILL, FRED
        ws.cell(r, 9).fill = PatternFill("solid", start_color=INPUT)
        # Höhe aus den beiden Langtextspalten (Breite je 50) + Position (26)
        ws.row_dimensions[r].height = zeilen_hoehe(
            [(p["feststellung"], 50), (p["massnahme"], 50),
             (p["bescheid_position"], 26)], min_h=30.0)
    last = HR + len(punkte)
    dv1 = DataValidation(type="list", formula1='"A,B,C"', allow_blank=False)
    dv2 = DataValidation(type="list",
                         formula1='"offen,in Klärung,geklärt,kein Handlungsbedarf"',
                         allow_blank=False)
    ws.add_data_validation(dv1)
    ws.add_data_validation(dv2)
    dv1.add(f"B{HR+1}:B{last}")
    dv2.add(f"K{HR+1}:K{last}")
    ws.auto_filter.ref = f"A{HR}:L{last}"
    ws.freeze_panes = f"A{HR+1}"

    # ---------------- Summary ----------------
    ws = wb.create_sheet("Summary", 2)
    kopf(ws, "Summary", meta)
    ws["A7"] = "Reviewpunkte nach Schweregrad"
    ws["A7"].font = F10B
    beschr = {"A": "Kritisch — Frist/Fehler, sofort klären",
              "B": "Wesentlich — vor Ablage klären/dokumentieren", "C": "Hinweis"}
    for i, sg in enumerate("ABC"):
        r = 8 + i
        ws.cell(r, 1, sg).font = SGFONT[sg]
        ws.cell(r, 1).fill = FILL[sg]
        ws.cell(r, 2, f'=COUNTIF(Reviewpunkte!B:B,A{r})').font = F10B
        ws.cell(r, 3, beschr[sg]).font = F10
        for col in (1, 2, 3):
            ws.cell(r, col).border = BORDER
    ws.cell(11, 1, "Gesamt").font = F10B
    ws.cell(11, 2, "=SUM(B8:B10)").font = F10B
    for col in (1, 2):
        ws.cell(11, col).border = BORDER
    ws["A13"] = "Top-Punkte"
    ws["A13"].font = F10B
    r = 14
    for t in d["top_punkte"]:
        ws.cell(r, 1, t["nr"]).font = F10B
        c = ws.cell(r, 2, t["text"])
        c.font, c.alignment = F10, WRAP
        for col in (1, 2):
            ws.cell(r, col).border = BORDER
        ws.row_dimensions[r].height = zeilen_hoehe([(t["text"], 90)])
        r += 1
    ge = "Gesamteinschätzung: " + d["gesamteinschaetzung"]
    ws.merge_cells(f"A{r+1}:D{r+1}")
    c = ws.cell(r + 1, 1, ge)
    c.font, c.alignment = F10, WRAP
    for col in range(1, 5):  # Rahmen um die gesamte Merge-Zeile
        ws.cell(r + 1, col).border = BORDER
    # Merge-Breite = Summe der Spalten A-D (16+90+45+15)
    ws.row_dimensions[r + 1].height = zeilen_hoehe([(ge, 160)], min_h=40.0)
    ws.column_dimensions["A"].width = 16
    ws.column_dimensions["B"].width = 90
    ws.column_dimensions["C"].width = 45
    ws.column_dimensions["D"].width = 15

    # ---------------- Abgleich (Soll-Ist) ----------------
    ws = wb.create_sheet("Abgleich", 3)
    kopf(ws, "Abgleich Berechnung ↔ Bescheid", meta)
    r = 7
    for block in d["abgleich"]:
        ws.cell(r, 1, block["titel"]).font = Font(size=11, bold=True)
        ws.row_dimensions[r].height = 22
        r += 1
        tabellenkopf(ws, r, AB_COLS)
        for z in block["zeilen"]:
            r += 1
            c = ws.cell(r, 1, z["position"])
            c.font, c.alignment = F10, WRAP
            for col, val in ((2, z.get("soll")), (3, z.get("ist"))):
                c = ws.cell(r, col, val)
                c.number_format, c.font = NUM, F10
                c.alignment = TOP
            # Differenz als Excel-Formel, damit der Sachbearbeiter sie
            # nachvollziehen und bei Korrekturen live sehen kann
            c = ws.cell(r, 4, f"=C{r}-B{r}")
            c.number_format = NUM
            c.font = FRED if z.get("abweichung") else F10
            c.alignment = TOP
            c = ws.cell(r, 5, z.get("ursache", "—"))
            c.font, c.alignment = F10, WRAP
            ws.cell(r, 6, z.get("punkt", "—")).font = F10
            ws.cell(r, 6).alignment = TOP
            for col in range(1, 7):
                ws.cell(r, col).border = BORDER
            ws.row_dimensions[r].height = zeilen_hoehe(
                [(z["position"], 38), (z.get("ursache", ""), 40)])
        r += 2

    # ---------------- Nebenbestimmungen & Fristen ----------------
    ws = wb.create_sheet("Nebenbestimmungen")
    kopf(ws, "Nebenbestimmungen & Fristen", meta)
    HR = 7
    tabellenkopf(ws, HR, NB_COLS)
    for j, n in enumerate(d["nebenbestimmungen"]):
        r = HR + 1 + j
        vals = [n["art"], n["bescheid"], n.get("fundstelle", ""), n["inhalt"],
                n["bedeutung"], n.get("frist", ""), n.get("punkt", "—")]
        for i, v in enumerate(vals, 1):
            c = ws.cell(r, i, v)
            c.border, c.font = BORDER, F10
            # Alle Textspalten umbrechen, damit nichts abgeschnitten wird
            c.alignment = WRAP if i in (1, 2, 4, 5) else TOP
        if n.get("frist"):
            fz = ws.cell(r, 6)
            fz.fill, fz.font = FRISTFILL, FRED
        ws.row_dimensions[r].height = zeilen_hoehe(
            [(n["inhalt"], 48), (n["bedeutung"], 44),
             (n["art"], 20), (n["bescheid"], 22)], min_h=24.0)
    ws.auto_filter.ref = f"A{HR}:G{HR+len(d['nebenbestimmungen'])}"
    ws.freeze_panes = f"A{HR+1}"

    # ---------------- Druck-Layout (alle Blätter einheitlich) ----------------
    for ws in wb.worksheets:
        ws.page_setup.orientation = "landscape"   # Querformat
        ws.page_setup.fitToWidth = 1              # gesamte Breite auf eine Seite
        ws.page_setup.fitToHeight = 0             # Höhe darf umbrechen
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.print_options.gridLines = False

    wb.save(ausgabe)
    print(f"Arbeitspapier gespeichert: {ausgabe} ({len(punkte)} Punkte)")


BEISPIEL_JSON = r"""
{
  "meta": {
    "mandant": "Mustermann GmbH, Dortmund",
    "mandanten_nr": "10234",
    "steuernummer": "317/5555/1234",
    "finanzamt": "FA Dortmund-West",
    "steuerarten_vz": "KSt + GewSt-Messbetrag 2025",
    "bescheide": "KSt 2025 v. 10.07.2026 (Erstbescheid, VdN); GewSt-Messbescheid 2025 v. 10.07.2026",
    "bescheidfamilie": "Abgefragt am 06.07.2026: Feststellung § 27 II KStG liegt vor (geprüft); GewSt-Bescheid Gemeinde steht noch aus (R-005 Wiedervorlage); Zerlegung: nicht einschlägig (eine Betriebsstätte); Verlustfeststellung: nicht einschlägig.",
    "fristenblock": "Bescheiddatum 10.07.2026 → fiktive Bekanntgabe 14.07.2026 (§ 122 II AO, 4 Tage) → Einspruchsfrist rechnerisch bis Montag, 17.08.2026 (§ 355, § 108 III AO) — nachrichtlich, Fristenprogramm führend",
    "einspruchsfrist_kurz": "rechnerisch 17.08.2026 (Mo) — nachrichtlich, Fristenprogramm führend",
    "hinweis_posteingang": "Berechnung unterstellt Postaufgabe am Bescheiddatum. Tatsächlichen Posteingang (Eingangsstempel/ELSTER-Abruf) abgleichen; nachrichtlich — Fristenprogramm der Kanzlei ist führend.",
    "vdn": "JA — Bescheid steht unter Vorbehalt der Nachprüfung (§ 164 AO), bleibt vollumfänglich änderbar.",
    "vorlaeufigkeit": "Teilweise vorläufig (§ 165 AO) — 2 Punkte, siehe Blatt Nebenbestimmungen.",
    "ergebnis": "Nachzahlung KSt 4.312,00 EUR, fällig 17.08.2026.",
    "zahlungsweg": "EINZUG DURCH FA — Lastschrift-Aussage im Bescheid (S. 1 unten): Abbuchung am 17.08.2026, Mandant über Kontodeckung informieren. [Alternative ohne Lastschrift-Aussage: 'SELBSTÜBERWEISUNG ERFORDERLICH — keine Lastschrift-Aussage im Bescheid. Mandant muss 4.312,00 EUR bis Mo, 17.08.2026 überweisen an IBAN DEXX... , Verwendungszweck 317/5555/1234. Säumniszuschläge 1 %/Monat (§ 240 AO). Geldeingang überwacht der Mandant, nicht die Kanzlei.']",
    "dokumente": "KSt-Bescheid 2025 (PDF); GewSt-Messbescheid 2025 (PDF); DATEV-Steuerberechnung v. 02.05.2026",
    "review_datum": "06.07.2026",
    "ampel": "ROT",
    "ampel_text": "Bescheid passt NICHT — FA weicht um 4.312,00 EUR zu Lasten ab; Einspruchsentscheidung bis 17.08.2026 erforderlich."
  },
  "arbeitsanweisung": [
    {"aufgabe": "MANUELL: Adressierung/Bekanntgabe gegen Stammdaten und Vollmachtsdatenbank prüfen (richtiger Mandant, Empfangsvollmacht greift?).", "zustaendig": "SB"},
    {"aufgabe": "MANUELL: Tatsächlichen Posteingang feststellen (Eingangsstempel/ELSTER-Abruf) und Frist 17.08.2026 in der Fristen-App verifizieren (R-001).", "frist": "07.07.2026", "zustaendig": "SB"},
    {"aufgabe": "MANUELL: SEPA-Mandatslage in den DATEV-Stammdaten gegenprüfen — Bescheid enthält keine Lastschrift-Aussage (R-003).", "zustaendig": "SB"},
    {"aufgabe": "Sachverhalt vGA mit Partner besprechen; Einspruchsentscheidung einholen (R-001). Einspruch bis spätestens 10.08.2026 versenden — Fristablauf 17.08.2026.", "frist": "20.07.2026", "zustaendig": "Partner"},
    {"aufgabe": "Mandantenanschreiben (Zahlungsaufforderung + Einspruchsempfehlung) versenden (R-003).", "frist": "10.07.2026", "zustaendig": "SB"},
    {"aufgabe": "Nach Erledigung aller Punkte: Fall ablegen, Status im Arbeitspapier pflegen.", "zustaendig": "SB"}
  ],
  "punkte": [
    {"schweregrad": "A", "kategorie": "Abweichung",
     "bescheid_position": "KSt 2025 / nicht abziehbare BA",
     "betrag": 4312.0, "frist": "2026-08-17", "frist_anzeige": "17.08.2026",
     "feststellung": "FA hat ... (Erläuterung S. 2: '...'). Differenz 4.312,00 EUR zu Lasten.",
     "massnahme": "Einspruch gegen den KSt-Bescheid 2025 bis 17.08.2026 einlegen; AdV über 4.312,00 EUR nach § 361 AO beantragen; Frist mit Fristenprogramm abgleichen."}
  ],
  "top_punkte": [{"nr": "R-001", "text": "Einzeiler"}],
  "gesamteinschaetzung": "3-5 Sätze, keine Bestandskraft-/Freigabeaussage.",
  "abgleich": [
    {"titel": "Körperschaftsteuer 2025",
     "zeilen": [
       {"position": "zu versteuerndes Einkommen", "soll": 100000.0,
        "ist": 128746.0, "abweichung": true,
        "ursache": "(a) FA-Abweichung lt. Erläuterung S. 2 — vGA Geschäftsführervergütung",
        "punkt": "R-001"},
       {"position": "KSt 15 %", "soll": 15000.0, "ist": 19312.0,
        "abweichung": true, "ursache": "Folge der zvE-Abweichung", "punkt": "R-001"}
     ]}
  ],
  "nebenbestimmungen": [
    {"art": "VdN § 164 AO", "bescheid": "KSt 2025", "fundstelle": "S. 1",
     "inhalt": "Festsetzung unter Vorbehalt der Nachprüfung",
     "bedeutung": "Bescheid bleibt vollumfänglich änderbar; Wiedervorlage bis Aufhebung/Festsetzungsverjährung.",
     "punkt": "R-004"},
    {"art": "Nachreichung", "bescheid": "KSt 2025", "fundstelle": "S. 3",
     "inhalt": "Darlehensvertrag Gesellschafter bis 15.09.2026 vorlegen",
     "bedeutung": "Bei Nichtvorlage droht Änderung zu Lasten.",
     "frist": "15.09.2026", "punkt": "R-002"}
  ]
}
"""

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
