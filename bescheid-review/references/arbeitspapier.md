# Spezifikation Excel-Arbeitspapier (Bescheid-Review)

**Verbindliche Layout-Quelle ist `scripts/build_arbeitspapier.py`** — das Skript
erzeugt Blätter, Spalten, Farben und Dropdowns immer identisch. Diese Datei
beschreibt Ziel-Layout und Qualitätsregeln; bei Abweichungen gilt das Skript.
Layoutänderungen erfolgen NUR im Skript, nie ad hoc.

Es wird GENAU EIN Arbeitspapier je Bescheidfamilie erzeugt (alle Bescheide der
Familie in denselben Blättern; Abgleich je Bescheid ein Abschnitt). Bei
Nachreichungen wird dieses Papier fortgeschrieben, kein zweites erstellt.

Dateiname: `Bescheidreview_[Mandantenname]_[Steuerart-Familie]_[VZ]_[JJJJ-MM-TT].xlsx`
Vorher zwingend `/mnt/skills/public/xlsx/SKILL.md` lesen und dessen Vorgaben
(openpyxl, Formatierung, keine kaputten Formeln) befolgen.

## Corporate Design
- Identisch zum abschluss-review-Arbeitspapier: Akzentfarbe Kanzlei-Gold
  `#F7B234` (Kopfzeilen-Füllung), Schrift Calibri 10, Überschriften fett,
  Autofilter, Fensterfixierung, Zeilenumbruch in ALLEN Textspalten.
- **Zeilenhöhen sind dynamisch**: Das Skript berechnet die Höhe jeder Zeile
  aus dem tatsächlichen Textumfang (Funktion `zeilen_hoehe`), konservativ
  gerundet — es darf NIE Text abgeschnitten sein und keine Zeile unnötig
  aufgebläht. Fixe Zeilenhöhen sind verboten.
- **Druck-Layout**: Alle Blätter Querformat, "an Seitenbreite anpassen"
  (fitToWidth=1), Höhe darf umbrechen. Ein Blatt muss ohne horizontales
  Zerreißen ausdruckbar sein.
- Kopfbereich jedes Blatts: "Burchardt & Kollegen", Mandant, Steuerart(en) + VZ,
  Einspruchsfrist (rechnerisch, nachrichtlich) — sie steht auf jedem Blatt im
  Kopf als Zweitkontrolle; führend bleibt das Fristenprogramm der Kanzlei.

## Blattstruktur

### Blatt 1 — "Deckblatt"
Mandant, Steuernummer, Finanzamt, Bescheid(e) mit Typ/Datum/Erst- oder
Änderungsbescheid/Korrekturnorm, **Bescheidfamilie**: welche zugehörigen
Bescheide abgefragt wurden und mit welchem Ergebnis (liegt vor / kommt noch →
Wiedervorlage-Punkt / nicht einschlägig), **Fristenblock (nachrichtlich)**:
Bescheiddatum → fiktive Bekanntgabe → rechnerisches Einspruchsfristende
(Datum + Wochentag) + Hinweis "nachrichtlich — Fristenprogramm der Kanzlei
ist führend", **Statusblock**: VdN ja/nein, vorläufig
ja/nein (Anzahl Punkte), Ergebnis (Nachzahlung/Erstattung EUR, Fälligkeit),
**Zahlungsweg** (Einzug durch FA mit Abbuchungsdatum ODER Selbstüberweisung
mit Betrag/Frist/Bankverbindung/Verwendungszweck — Feld `meta.zahlungsweg`),
verwendete Dokumente, Felder für Sachbearbeiter / abgearbeitet am / Freigabe
Partner am / Frist mit Fristenprogramm abgeglichen am.

### Blatt 1a — Ergebnisblock (auf dem Deckblatt, Zeile 6)
Farbig hinterlegtes Ampel-Urteil (GRÜN/GELB/ROT) mit Klartext-Satz
("Bescheid passt …"). Farben: GRÜN #C6EFCE/#006100, GELB #FFEB9C/#9C6500,
ROT #FFC7CE/#9C0006.

### Blatt 1b — To-Do-Checkliste (auf dem Deckblatt, unter dem Statusblock)
Kompakte Fassung der kompletten Arbeitsanweisung, jeder Punkt mit ☐ voran,
Frist und Zuständigkeit in eckigen Klammern, Fristpunkte rot. Der
Sachbearbeiter sieht auf dem ersten Blatt ohne Blättern, was zu tun ist;
abgehakt und mit Erledigt-Datum versehen wird auf Blatt "Arbeitsanweisung".
Manuelle Prüfpunkte (Präfix "MANUELL:") stehen am Anfang der Liste.

### Blatt 2 — "Arbeitsanweisung"
Nummerierte Abarbeitungsliste aus SKILL.md Schritt 6, mit Ampelbanner im Kopf.
Spalten: Nr. | ☐ (Checkbox-Spalte) | Aufgabe (imperativ, ein Arbeitsgang,
Punktverweis; manuelle Prüfpunkte mit Präfix "MANUELL:") | Frist
(rot hinterlegt, wenn gesetzt) | Zuständig (SB/Partner/Mandant) | Erledigt am
(Eingabefeld, hell). Letzte Zeile immer der Abschluss (Ablage/Wiedervorlage).

### Blatt 3 — "Summary"
Anzahl Reviewpunkte je Schweregrad (A/B/C, per Formel gezählt), Top-5-Punkte,
Gesamteinschätzung in 3–5 Sätzen (Feststellungen, KEINE Freigabe-/
Bestandskraftaussage).

### Blatt 4 — "Abgleich" (Soll-Ist bzw. Einspruchs-Erfolgskontrolle)
Je Bescheid ein Abschnitt. Bei Änderungsbescheiden nach eigenem Einspruch trägt
der Abschnitt den Titel "Einspruchs-Erfolgskontrolle": Spalte "Lt. Berechnung"
= begehrtes Ergebnis lt. Einspruch, Spalte "Lt. Bescheid" = Änderungsbescheid,
Wert des Vorbescheids und Ergebnisklasse (voll/teilweise/nicht erreicht/
Verböserung) in der Ursache-Spalte. Spalten:

| Spalte | Inhalt |
|---|---|
| Position | z.B. "Einkünfte § 21 EStG", "Hinzurechnung § 8 Nr. 1 GewStG" |
| Lt. Berechnung (EUR) | Soll-Wert der Kanzlei |
| Lt. Bescheid (EUR) | Ist-Wert |
| Differenz (EUR) | **Excel-Formel** (Bescheid − Berechnung), rot bei ≠ 0 |
| Ursache | (a) FA-Abweichung lt. Erläuterung / (b) mutmaßl. FA-Fehler / (c) mutmaßl. eigener Fehler / (d) Rechtsstand |
| siehe Punkt | Reviewpunkt-Nr. oder "—" |

Nur echte Vergleichszeilen aufnehmen; identische Werte werden mitgeführt
(Differenz 0,00 belegt den vollständigen Abgleich). Fehlt die eigene Berechnung,
enthält das Blatt nur die Bescheidwerte plus Hinweiszeile "Soll-Werte fehlen —
siehe Punkt R-001".

### Blatt 5 — "Reviewpunkte" (Haupttabelle, Abarbeitungslogik)
Spalten (genau diese, in dieser Reihenfolge):

| Spalte | Inhalt |
|---|---|
| Nr. | R-001, R-002 … |
| Schweregrad | A / B / C (Dropdown; A rot, B orange, C grau) |
| Kategorie | Frist, Abweichung, Nebenbestimmung, Nachreichung, Formal, Konsistenz, Zahlung, Eigenkontrolle |
| Bescheid / Position | welcher Bescheid, welche Position/Fundstelle |
| Betrag (EUR) | betroffener Betrag/Differenz, leer wenn nicht anwendbar |
| Frist | Datum, wenn fristgebunden (rot formatiert), sonst leer |
| Feststellung | Fakten mit Fundstelle (Seite/Abschnitt des Bescheids, Zitatkern) |
| Erforderliche Maßnahme | imperativ, konkret, in einem Arbeitsschritt ausführbar; bei Einsprüchen: gegen welchen Bescheid (§ 351 Abs. 2 AO!) |
| Antwort Sachbearbeiter | leer (Eingabefeld, hell hinterlegt) |
| Nachweis / Ablage | leer (DMS-Verweis) |
| Status | Dropdown: offen / in Klärung / geklärt / kein Handlungsbedarf |
| Prüfvermerk Partner | leer |

Sortierung: Schweregrad A → B → C; innerhalb A zuerst Fristsachen (nächstes
Fristdatum zuerst), sonst nach Betrag absteigend.

### Blatt 6 — "Nebenbestimmungen & Fristen"
Vollständige Liste ALLER Befunde aus Prüfkatalog Teil C — auch derer ohne
Handlungsbedarf (Vollständigkeitsnachweis des Reviews). Spalten: Art (VdN /
Vorläufigkeit / Nachreichung / Abweichungsbegründung / Nebenleistung / Zahlung /
Sonstiges), Bescheid, Fundstelle, Inhalt (sinngemäß), Rechtsfolge/Bedeutung,
Frist (falls vorhanden), siehe Punkt.

## Qualitätsregeln für Punktformulierungen
- Feststellung = beobachtbare Fakten mit Zahl und Fundstelle im Bescheid.
- Vermutungen ausdrücklich kennzeichnen ("mutmaßlich", "Indiz für").
- Maßnahme = imperativ, konkret, fristbewusst ("Einspruch gegen den
  ESt-Bescheid 2025 bis 18.08.2026 einlegen; zur Fristwahrung zunächst ohne
  Begründung, Begründung zu Position X nachreichen; AdV über 4.312,00 EUR
  nach § 361 AO beantragen." statt "Einspruch prüfen").
- Jede fristgebundene Maßnahme trägt das Fristdatum in der Frist-Spalte UND
  den Hinweis "mit dem Fristenprogramm abgleichen". In der Arbeitsanweisung
  gilt die Vorfristen-Regel (SKILL.md Schritt 6): interner Erledigungstermin
  mit Sicherheitspuffer vor dem gesetzlichen Fristablauf.
- Keine Doppelungen: Abgleichsdifferenz, zugehörige FA-Begründung und
  Einspruchsempfehlung bilden EINEN Punkt.
- Zielgröße: 5–20 Punkte je Bescheidpaket; ein unauffälliger Bescheid darf auch
  nur 3 Punkte haben (Frist, VdN-Status, Ablagehinweis) — künstliches Aufblähen
  vermeiden.
