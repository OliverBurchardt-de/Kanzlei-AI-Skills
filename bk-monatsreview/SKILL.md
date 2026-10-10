---
name: bk-monatsreview
description: >
  Fachlicher Monatsreview einer bereits final gebuchten Finanzbuchhaltung bei
  Burchardt & Kollegen. Verwenden, wenn ein abgeschlossener Buchungsmonat auf
  offensichtliche Buchungsfehler, fehlende Pflichtbuchungen, unzulässige
  Kontensalden, ungeklärte Interimsposten, schnell erkennbare
  OPOS-Auszifferungen und buchungsrelevante GuV-Auffälligkeiten geprüft werden
  soll. Nicht verwenden zur Erstellung der laufenden Buchhaltung, für die
  UStVA-Prüfung, den Jahresabschluss-Review, eine betriebswirtschaftliche
  Beratung, Anlagenzugangsprüfung, Wertberichtigung oder Bescheidprüfung.
---

# B&K Monatsreview – Produktivversion 1.2

## 1. Rolle und Ziel

Dieser Skill ist der unabhängige Verifier nach Abschluss der laufenden
Buchhaltung. Er prüft, ob der Buchungsmonat fachlich plausibel und sauber
abgeschlossen ist. Er ersetzt weder den Mitarbeiterreview während der Buchung
noch eine betriebswirtschaftliche Analyse.

Der Auftrag zum Monatsreview bedeutet grundsätzlich, dass die Buchhaltung
inklusive Bank final gebucht ist. Keine zusätzliche Bestätigung verlangen.
Gibt es deutliche Gegenanzeichen, den Review abbrechen und den Nutzer um Prüfung
des Abschlussstatus bitten.

## 2. Verbindliche Ausschlüsse

Nicht Gegenstand dieses Skills sind:

- UStVA-, Vorsteuer- und Umsatzsteuerverprobung sowie sonstige Steuerkonten,
- Rechnungsabgrenzungen als Jahresabschlussthema,
- Anlagenzugänge und Aktivierungsprüfung,
- Wertberichtigungen,
- Bestandsveränderungen und Materialeinsatz als eigenes Prüfmodul,
- betriebswirtschaftliche Beratung, Margen- oder Rentabilitätsanalyse,
- vollständige forensische OPOS-Rekonstruktion,
- Prüfung oder Pflege fehlender Zahlungsziele in Debitoren-/Kreditorenstammdaten.

Lohnsteuer- und Sozialversicherungskonten bleiben trotz des Ausschlusses
sonstiger Steuerkonten Bestandteil des Lohnmoduls.

## 3. Datenquellen und Ablauf

1. Mandant über Mandantennummer eindeutig bestimmen und DATEV-Namen bestätigen.
2. Mandantendatei vollständig lesen. Pflichtangaben siehe
   `referenz/Mandantendatei.md`. Ist sie nicht auffindbar, alle davon
   abhängigen Prüfpunkte als `NICHT_PRUEFBAR` kennzeichnen, die unabhängigen
   Prüfungen aber fortsetzen. Ein Gesamturteil `GRUEN` ist dann ausgeschlossen.
3. Pflichtunterlagen des Prüfmonats sichten.
4. DATEV Accounting ausschließlich über den Riecken-Connector nach
   `referenz/Riecken Abruf.md` abrufen; den Connector nur lesend verwenden.
5. Kontonummern ausschließlich nach
   `referenz/Kontonummernregel.md` umrechnen.
6. Prüfmodule M1 bis M5 abarbeiten.
7. Alle Geldrechnungen deterministisch mit den Skripten aus `skripte/`
   durchführen; Geldbeträge nie mit binären Gleitkommazahlen rechnen.
8. Sichere Korrekturen nur als Umbuchungen vorbereiten. Keine Generalumkehr.
9. Ergebnis mit der Vorlage
   `assets/Monatsreview Arbeitspapier.xlsx` dokumentieren.

## 4. Abbruch bei erkennbar unfertiger Buchhaltung

Nur bei mehreren deutlichen Indikatoren abbrechen, insbesondere:

- Bankkonten fehlen offensichtlich oder enthalten nur Bruchteile der üblichen
  Buchungen,
- typische laufende Buchungen fehlen vollständig,
- Lohnunterlagen liegen vor, aber die Lohnbuchung fehlt,
- mehrere zentrale Abstimmkonten zeigen unbearbeitete Zwischenstände,
- der Buchungszeitraum endet erkennbar vor Monatsultimo.

Meldung sinngemäß:

> Nach der vorliegenden Datenlage ist die Buchhaltung für den Prüfmonat
> vermutlich noch nicht final abgeschlossen. Bitte prüfen Sie den
> Abschlussstatus und starten Sie den Monatsreview anschließend erneut.

## 5. Prüfmodule

### M1 Lohnkonten

Regeln: `referenz/M1 Lohnkonten.md`.

Immer prüfen: 1740, 1741 und 1742. Bei ausdrücklich in der Mandantendatei
bestätigtem Schätzverfahren zusätzlich 1759. Maßgeblich ist der fachlich
richtige Saldo zum Monatsultimo, nicht eine pauschale Nullregel.

### M2 Bankauffälligkeiten und Interimskonten

Regeln: `referenz/M2 Bank und Interim.md`.

Bankkonten nicht gegen externe Banksalden abstimmen. Nur auffällige Buchungen
untersuchen. 1360 und 1590 nach den eigenen strengen Regeln prüfen. Die
1590-Prüfung ist zweistufig: Erstprüfung, Mitarbeiter-Nachbearbeitung und
anschließender frischer Abruf über den Riecken-Connector nach erneutem
Anstoß.

### M3 OPOS

Regeln: `referenz/M3 OPOS.md`.

Nur schnell und mit hoher Sicherheit erkennbare Auszifferungen,
naheliegende Kombinationen und Fehlzuordnungen suchen. Keine vollständige
Rekonstruktion. Auszifferungsliste strikt von Umbuchungs-/Ausbuchungsvorschlägen
trennen.

### M4 GuV-Plausibilität

Regeln: `referenz/M4 GuV.md`.

Nur buchungsrelevante Plausibilität prüfen: fehlende AfA oder Personalkosten,
fehlende wiederkehrende Aufwendungen, unzulässige Saldenrichtungen und
wesentliche ungewöhnliche Buchungen. Keine betriebswirtschaftliche Analyse.

### M5 Bilanzkonten-Plausibilität

Regeln: `referenz/M5 Bilanzkonten.md`.

Prüfung klar definierter Risikofelder: 1295, Kassen, ARAP/PRAP, Darlehen,
Privatkonten und Gesellschafter-Verrechnungskonten.

## 6. Wesentlichkeit

Allgemeine Wesentlichkeit:

> 1 % des absoluten kumulierten Vorsteuerergebnisses, mindestens 250 EUR.

Eine Veränderung ist nur dann als wesentlich auffällig zu behandeln, wenn sie
die Wesentlichkeitsgrenze überschreitet und mehr als 50 % vom üblichen
Monatswert abweicht. Der übliche Monatswert ist der Durchschnitt der letzten
drei tatsächlich bebuchten Monate. Ein Konto gilt als regelmäßig, wenn es in
mindestens drei der letzten vier Monate bebucht wurde.

Unabhängig von der Wesentlichkeit prüfen:

- vollständig fehlende typische Buchungen wie AfA, Personalkosten oder Miete,
- negative Kassenbestände,
- ARAP/PRAP auf falscher Saldenseite,
- zwingende Lohnkontenabgleiche,
- ausdrücklich definierte Nullkonten.

## 7. Ampel und Prüfbarkeit

- `GRUEN`: Prüfung durchgeführt und ohne Beanstandung.
- `GELB`: plausibler Klärungsbedarf, Verdachtsmoment oder dokumentierbare
  Ausnahme.
- `ROT`: klarer Fehler, unzulässiger Zustand oder zwingender Korrekturbedarf.
- `NICHT_PRUEFBAR`: erforderliche Quelle fehlt oder ist nicht auswertbar.

In jeder bearbeitbaren Ergebnistabelle steht die Ampel in Spalte A. Die letzte
Spalte heißt `Kommentar` und bleibt für die fachliche Abarbeitung editierbar.

Jeder Befund enthält mindestens Ampel, Modul, Prüfpunkt, Konto, Soll, Ist,
Differenz, Quelle, Grund, Maßnahme, Bearbeitungsstatus und Kommentar.

## 8. Korrekturen

- Nur sichere und eindeutig begründete Umbuchungen in einen DATEV-Stapel.
- Keine Generalumkehr.
- Grundsätzlich ohne Steuerschlüssel.
- Bei ausnahmsweise betroffenen Automatikkonten darf Buchungsschlüssel 40 zur
  Aufhebung der Automatik verwendet werden.
- Unsichere Fälle bleiben außerhalb des Stapels als Klärungshinweis.
- Eine Auszifferung ist keine Buchung und gehört ausschließlich in die
  Auszifferungsliste.
- Der Skill importiert oder überträgt keine Buchungen in DATEV. Ein erzeugter
  DATEV-Stapel ist ausschließlich ein Vorschlag zur fachlichen Freigabe und
  anschließenden manuellen Verarbeitung außerhalb dieses Skills. Die
  schreibenden Werkzeuge des Riecken-Connectors werden nicht aufgerufen.

## 9. Ausgabe

Ergebnisstruktur:

1. Fehler und zwingender Korrekturbedarf,
2. Prüf- und Klärungshinweise,
3. direkt umsetzbare Maßnahmen,
4. kurz bestätigte unauffällige Prüfbereiche.

Ausgaben:

- ausgefülltes Excel-Arbeitspapier,
- kurze Chat-Zusammenfassung,
- Auszifferungsliste als eigenes Tabellenblatt,
- versandfertige 1590-Beleganforderung nach abgeschlossener Schlusskontrolle,
- bei sicheren Fällen separater DATEV-Buchungsstapel.

Die verbindliche Spaltenfolge und die Trennung der Ergebnislisten stehen in
`referenz/Ergebnisformat.md`.

## 10. Technische Regeln

- Kontonummern immer als Strings behandeln.
- Sachkontenlänge ausschließlich aus den über den Riecken-Connector gelesenen
  Mandantendaten des konkreten Wirtschaftsjahres verwenden; nicht raten.
- Geldbeträge mit `Decimal` und centgenauer Rundung rechnen.
- Vor Ausgabe die Kopfzeilen der Excel-Vorlage, die Ampelzählung, Formelfehler
  und die visuelle Darstellung aller Tabellenblätter prüfen.
- Vor produktiver Freigabe ausführen:

```bash
python -m unittest discover -s tests -p "test*.py"
```

## 11. Versionsbasis und Regressionstest

Die Produktivversion 1.0 bleibt die fachliche und technische
Ausgangsbasis für die weitere Entwicklung. Jede spätere Änderung wird als neue
Version dokumentiert und gegen diese Basis regressionsgeprüft.

Vor einer neuen Produktivversion mindestens einen bereits final gebuchten Monat
mit vollständiger Mandantendatei und den erforderlichen Lohnunterlagen prüfen.
Prüfergebnisse, Auszifferungsliste und einen gegebenenfalls erzeugten
Vorschlagsstapel fachlich und technisch gegen DATEV kontrollieren, ohne ihn
durch den Skill zu importieren oder zu übertragen. Zusätzlich den vorhandenen
Regressionstest ohne vollständige Mandantendatei ausführen, damit
`NICHT_PRUEFBAR` nicht zu geratenen Aussagen führt. Das Protokoll
`assets/Freigabeprotokoll.md` verwenden.

Version 1.2 ersetzt den bisherigen ressourcenbasierten DATEV-MCP-Zugang durch
den Riecken-Connector (`referenz/Riecken Abruf.md`). Die fachlichen Prüfregeln
M1 bis M5 sind unverändert.
