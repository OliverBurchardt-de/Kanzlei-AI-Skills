---
name: bk-einkommensteuer
description: Erstellt aus Mandantenbelegen, der Einkommensteuererklärung des Vorjahres, Vorjahresberechnungen und ergänzenden Arbeitspapieren ein nachvollziehbares Arbeitspapier für die deutsche Einkommensteuererklärung, ein seitenbezogen getrenntes Belegpaket und ein Prüf- und Nachforderungsprotokoll. Verwenden, wenn Einkommensteuerunterlagen natürlicher Personen aufgenommen, Anlagen und Formularfeldern zugeordnet, Vermietungsobjekten zugewiesen, mit dem Vorjahr verglichen, für die Bearbeitung vorbereitet oder auf fehlende und unklare Sachverhalte geprüft werden sollen.
---

# BK Einkommensteuer

## Auftrag

Bereite eine deutsche Einkommensteuererklärung fachlich und dokumentarisch vor. Erzeuge keine bloße Belegzusammenfassung, sondern eine lückenlos nachvollziehbare Verbindung zwischen Quelle, Berechnung, steuerlicher Würdigung und vorgeschlagener Eintragung.

Lies vor jeder Bearbeitung [ANFORDERUNGSPROFIL.md](references/ANFORDERUNGSPROFIL.md), [ARBEITSPAPIER_UND_STATUSLOGIK.md](references/ARBEITSPAPIER_UND_STATUSLOGIK.md), [JAHRESLOGIK_UND_ZIELSYSTEM.md](references/JAHRESLOGIK_UND_ZIELSYSTEM.md) und [DATEV_SYSTEMGRENZEN.md](references/DATEV_SYSTEMGRENZEN.md). Lies vor jeder Belegtrennung zusätzlich [BELEGPAKET_MEINE_STEUERN.md](references/BELEGPAKET_MEINE_STEUERN.md).

## Arbeitsgrundsätze

- Erhalte alle Originaldateien unverändert.
- Übernimm keinen Vorjahreswert ohne aktuellen Nachweis oder dokumentierte Begründung.
- Ordne jede vorgeschlagene Eintragung mindestens einer Quelle, Berechnung oder ausdrücklich gekennzeichneten Annahme zu.
- Trenne Belege nur bei eindeutiger Seiten- und Sachverhaltszuordnung. Dokumentiere jede Trennung im Belegmanifest.
- Erfinde keine Beträge, persönlichen Daten, Zeiträume, Nutzungsanteile oder steuerlichen Tatsachen.
- Weise ungeklärte Tatsachen, zweifelhafte Rechtsanwendungen und nicht belegte Annahmen sichtbar zur Prüfung oder Nachforderung aus.
- Verwende veranlagungsjahrbezogene amtliche Formulare, Anleitungen und Feldbezeichnungen. Vermische keine Formularstände verschiedener Jahre.
- Gib keine Erklärung zur Übermittlung frei. Die abschließende fachliche Prüfung und Übermittlung bleiben menschliche Aufgaben.

## Workflow

### 1. Auftrag und Eingangsbestand feststellen

Ermittle Veranlagungsjahr, Personen und Veranlagungsart. Bereite die manuelle Dateneingabe in DATEV Einkommensteuer und den manuellen Belegupload in DATEV Meine Steuern vor. Inventarisiere sämtliche Originaldateien mit stabiler Quellen-ID, Dateiname, Typ, Seitenzahl und erkennbarem Zeitraum.

Prüfe, ob mindestens Vorjahreserklärung, Vorjahresberechnungen und aktuelle Belege vorliegen. Führe fehlende erwartbare Unterlagen nicht still als null, sondern als Nachforderungs- oder Prüffall.

### 2. Vorjahresstruktur aufbauen

Extrahiere die im Vorjahr verwendeten Anlagen, Einkunftsquellen, Vermietungsobjekte, wiederkehrenden Positionen, Berechnungslogiken und offenen Dauersachverhalte. Verwende diese Struktur ausschließlich als Erwartungs- und Plausibilitätsgerüst für das aktuelle Jahr.

### 3. Aktuelle Unterlagen klassifizieren

Ordne Belege Personen, Sachverhalten, Veranlagungszeiträumen und gegebenenfalls eindeutig gekennzeichneten Mietobjekten zu. Halte Mehrfachbezüge und widersprüchliche Kennzeichnungen als Prüffall fest.

### 4. Belege trennen und nachweisen

Erstelle aus gemischten Dateien nur dann einzelne Upload-Dateien, wenn die betroffenen Seiten eindeutig abgrenzbar sind. Bewahre die Originaldatei separat auf. Vergib jeder Ausgabedatei eine eindeutige ID und dokumentiere Originaldatei, Originalseiten, Zielthema, Zielanlage und Prüfsumme oder anderes Integritätsmerkmal im Manifest.

### 5. Beträge ermitteln und Eintragungen vorschlagen

Ermittle je steuerlicher Position den aktuellen Betrag und die zugrunde liegende Berechnung. Führe mindestens Formular oder Anlage, Feldbezeichnung, amtliche Kennziffer oder systembezogenes Zielfeld, Betrag, Rechenweg, Quellen-IDs, Vorjahresvergleich, Bearbeitungsstatus und Erläuterung.

Verwende die Statuswerte:

- „bereit“: vollständig belegt, rechnerisch nachvollziehbar und eindeutig zugeordnet
- „prüfen“: Bearbeitungsansatz vorhanden, aber fachliche oder tatsächliche Kontrolle notwendig
- „nachfordern“: entscheidungserhebliche Information oder Unterlage fehlt
- „nicht verarbeitet“: technisch unlesbar, außerhalb des vereinbarten Umfangs oder nicht sicher zuordenbar

### 6. Plausibilisieren

Stimme Summen mit Einzelbelegen und Nebenrechnungen ab. Vergleiche Anlagen, Einkunftsquellen und wesentliche Beträge mit dem Vorjahr. Erkläre erhebliche Abweichungen, neue oder weggefallene Sachverhalte sowie Belege ohne Eintragungswirkung.

### 7. Ausgabepaket erstellen

Erzeuge gemeinsam:

1. ein Arbeitspapier mit Eintragungen je Mantelbogen oder Anlage,
2. ein Belegregister und ein Upload-Paket der getrennten Belege,
3. ein Prüf- und Nachforderungsprotokoll,
4. eine Vollständigkeits- und Abstimmübersicht.

Liefere das Paket erst als bearbeitungsbereit aus, wenn alle Quellen referenziert, alle Trennungen rückverfolgbar und alle offenen Punkte statusgerecht ausgewiesen sind.

## Noch nicht automatisieren

Automatisiere keine Dateneingabe in DATEV Einkommensteuer, keinen Upload in DATEV Meine Steuern, keine materiell-rechtliche Entscheidung bei mehreren vertretbaren Behandlungen und keine Übermittlung an Finanzverwaltung oder Kanzleisysteme. Behaupte niemals, dass Daten eingegeben, Belege hochgeladen oder Erklärungen übermittelt wurden. Verwende nur für das konkrete Veranlagungsjahr bestätigte Formularfeldzuordnungen; setze andere Zuordnungen auf „prüfen“.

## Ressourcen verwenden

- Verwende [Arbeitspapier_Einkommensteuer_Vorlage.xlsx](assets/Arbeitspapier_Einkommensteuer_Vorlage.xlsx) als leere Ausgangsvorlage. Kopiere sie in den Fall-Arbeitsordner und befülle niemals die im Skill gespeicherte Vorlage mit Mandantendaten.
- Erzeuge die Vorlage nach strukturellen Änderungen mit [build_workpaper.mjs](scripts/build_workpaper.mjs) neu und prüfe Formeln sowie Renderings aller Tabellenblätter.
- Erstelle für eindeutige PDF-Trennungen eine JSON-Datei nach [BELEGTRENNUNG_SCHEMA.json](references/BELEGTRENNUNG_SCHEMA.json) und führe [split_pdf.py](scripts/split_pdf.py) aus.
- Führe nach Änderungen an der Trennlogik [test_split_pdf.py](scripts/test_split_pdf.py) mit ausschließlich synthetischen Daten aus.
- Speichere keine realen Mandantenunterlagen oder erzeugten Fallpakete im Git-Repository.