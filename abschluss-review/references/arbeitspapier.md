# Spezifikation Excel-Arbeitspapier

**Verbindliche Layout-Quelle ist `scripts/build_arbeitspapier.py`** — das Skript
erzeugt Blätter, Spalten, Farben und Dropdowns immer identisch. Diese Datei
beschreibt das Ziel-Layout und die Qualitätsregeln für die Inhalte; bei
Abweichungen gilt das Skript. Layoutänderungen erfolgen NUR im Skript, nie ad hoc.

Dateiname: `Review_[Mandantenname]_[WJ]_[JJJJ-MM-TT].xlsx`
Vorher zwingend `/mnt/skills/public/xlsx/SKILL.md` lesen und dessen Vorgaben
(openpyxl, Formatierung, keine kaputten Formeln) befolgen.

## Corporate Design
- Akzentfarbe Kanzlei-Gold: `#F7B234` (Kopfzeilen-Füllung), Schrift dort schwarz.
- Schrift: Calibri 10, Überschriften 12–14 fett.
- Kopfbereich jedes Blatts: Kanzleiname "Burchardt & Kollegen", Mandant,
  Wirtschaftsjahr, Abschlussart (BILANZ oder EÜR — groß und unübersehbar),
  Erstellungsdatum des Reviews.
- Autofilter auf der Reviewpunkte-Tabelle, Fensterfixierung unter der Kopfzeile,
  sinnvolle Spaltenbreiten, Zeilenumbruch in Textspalten.

## Blattstruktur

### Blatt 1 — "Deckblatt"
Mandant, Mandanten-Nr., Rechtsform, Branche, Wirtschaftsjahr/Stichtag,
**Abschlussart (EÜR/Bilanz)**, verwendete Dokumente (mit Druckdatum/Status),
Wesentlichkeit mit Herleitung, Nichtaufgriffsgrenze, Ersteller (Claude-Review),
Felder für: Sachbearbeiter, abgeschlossen am, Freigabe Partner am.

### Blatt 2 — "Summary"
- Anzahl Reviewpunkte je Schweregrad (A/B/C) als kleine Tabelle.
- Die Top-5-Punkte (höchster Schweregrad/Betrag) mit Nr. und Einzeiler.
- Gesamteinschätzung in 3–5 Sätzen (Feststellungen, keine Freigabeaussage).

### Blatt 3 — "Reviewpunkte" (Haupttabelle)
Spalten (genau diese, in dieser Reihenfolge):

| Spalte | Inhalt |
|---|---|
| Nr. | fortlaufend, Format R-001, R-002 … |
| Schweregrad | A / B / C (Datenüberprüfung/Dropdown; A rot, B orange, C grau hinterlegt) |
| Kategorie | z.B. Vorjahresvergleich, Steuerlich, Buchung, Abgrenzung, Kennzahl, Formal, Privat |
| Konto/Position | SKR-Konto + Bezeichnung bzw. Abschlussposition |
| Betrag GJ (EUR) | Zahlenformat #.##0,00 |
| Betrag VJ (EUR) | dito, leer wenn nicht anwendbar |
| Feststellung | Was wurde festgestellt (Fakten, mit Fundstelle: Blatt/Datum/Betrag) |
| Erforderliche Maßnahme | Konkrete Handlungsanweisung: welcher Beleg, welche Frage, welcher Nachweis |
| Antwort Sachbearbeiter | leer (Eingabefeld, hell hinterlegt) |
| Nachweis/Ablage | leer (Verweis auf Beleg/DMS) |
| Status | Dropdown: offen / in Klärung / geklärt / kein Handlungsbedarf; Standard "offen" |
| Prüfvermerk Partner | leer |

Sortierung: Schweregrad A → B → C, innerhalb dessen nach Betrag absteigend.

### Blatt 4 — "Kennzahlen"
Kennzahlentabelle GJ/VJ/Veränderung gemäß Prüfkatalog Teil D, inkl. Hinweis auf
Annualisierung bei Rumpfzeiträumen. Auffällige Werte farblich markieren und mit
der zugehörigen Reviewpunkt-Nr. verknüpfen (Spalte "siehe Punkt").

### Blatt 5 — "Buchungsauffälligkeiten" (nur wenn Teil E Punkte ergab)
Detailliste: Konto, Datum, Betrag, S/H, Gegenkonto, Auffälligkeitstyp,
Verweis auf Reviewpunkt-Nr. (jede Zeile hängt an einem Punkt aus Blatt 3;
dieses Blatt ist die Fundstellen-Dokumentation, nicht eine zweite Punkteliste).

## Qualitätsregeln für Punktformulierungen
- Feststellung = beobachtbare Fakten mit Zahlen und Fundstelle.
- Vermutungen ausdrücklich als solche kennzeichnen ("möglicherweise", "Indiz für").
- Maßnahme = imperativ, konkret, in einem Arbeitsschritt ausführbar
  ("Beleg zur Buchung vom 28.05. über 3.784,20 EUR (Konto 3106, Gegenkonto 1200,
  Beleg 042-2026) ziehen und prüfen, ob Freistellungsbescheinigung § 48b EStG
  des Subunternehmers vorliegt.").
- Keine Doppelungen: verwandte Feststellungen zu einem Punkt bündeln.
- Zielgröße: 10–30 Punkte je Abschluss; deutlich mehr nur bei entsprechend
  problematischem Abschluss.
