---
name: bk-jahresabschluss-vorbereitung
description: Bereitet den Start der eigentlichen Jahresabschlussbearbeitung vor: bindet DATEV und SharePoint mandantengenau, deckt alle bebuchten oder nicht auf null stehenden Bilanzkonten ab und arbeitet eine verbindliche Konten- und Themencheckliste einschließlich OPOS, Bank/Kasse, 1360/1590, Lohnkonten 1740/1741/1742, Steuerabstimmung, ARAP/PRAP und Vorjahrshinweisen ab. Verwenden für buchhalterische Startklarheit und Vorarbeiten, nicht für allgemeine Datenanalyse, einen vollständigen Jahresabschlussreview, endgültige Bilanzierung, Steuererklärungen oder automatischen DATEV-Import.
---

# B&K Abschlussvorbereitung – Startklarheit v0.3.0

## Ziel und Grenze

Arbeite die buchhalterischen Vorarbeiten und Pflichtnachweise ab, die vorhanden sein müssen, damit der zuständige Mitarbeiter sinnvoll mit dem Jahresabschluss beginnen kann. Der Skill beurteilt Startklarheit für die Abschlussbearbeitung, nicht Abschlussreife, Vollständigkeit oder Richtigkeit des Jahresabschlusses.

- DATEV, OPOS und SharePoint während der Vorbereitung nur lesen.
- Keine Auszifferung ausführen, keinen Buchungsstapel importieren und keine SharePoint-Datei ändern.
- Schreibende Schritte erst in einem getrennten Arbeitsgang nach ausdrücklicher Freigabe des exakten Ziels und Inhalts.
- Unsichere Beträge, Konten, Gegenkonten, Steuerschlüssel, Perioden oder Rechtsfolgen nicht raten. Als `NICHT_PRUEFBAR` oder `FACHLICH_ZU_KLAEREN` ausweisen.
- Nicht zum Vorbereitungsscope gehörende Auffälligkeiten nur als Übergabepunkt sammeln. Nicht untersuchen, bewerten oder als erledigt bestätigen.
- Keine allgemeine Datenanalyse durchführen. Insbesondere keine Rechnungsnummernlücken, generische Doppelbuchungssuche oder allgemeine Gegenkonto-Anomalien prüfen.
- Das Ergebnis bleibt `ENTWURF`, bis die Review-Sheet-Vorlage eingebunden, die Kanzleiparameter bestätigt und ein Pilotmandat fachlich freigegeben wurde.

## Vor jedem Lauf lesen

1. [references/KANZLEIPARAMETER.md](references/KANZLEIPARAMETER.md)
2. [references/MCP_UND_SHAREPOINT.md](references/MCP_UND_SHAREPOINT.md)
3. [references/PRUEFLOGIK.md](references/PRUEFLOGIK.md)
4. [references/STARTKLARHEITS_CHECKLISTE.md](references/STARTKLARHEITS_CHECKLISTE.md)
5. [references/VORBEREITUNGSABGRENZUNG.md](references/VORBEREITUNGSABGRENZUNG.md)
6. [references/REVIEWDATEN.md](references/REVIEWDATEN.md)

## Statusmodell

- `IM_VORBEREITUNGSSCOPE_UNAUFFAELLIG`: der eng begrenzte Vorbereitungspunkt wurde ohne Befund abgearbeitet; keine Aussage zum Gesamtabschluss.
- `AUF_NULL`: ein Checklistenkonto steht centgenau auf null.
- `ABGESTIMMT`: ein zulässiger Saldo ist mit der maßgeblichen Unterlage oder einem Register centgenau erklärt.
- `ZU_BEREINIGEN`: vor Beginn der Abschlussbearbeitung ist eine konkrete Aufräumhandlung erforderlich.
- `UNTERLAGE_FEHLT`: der für die Vorbereitung erforderliche Nachweis muss angefordert werden.
- `NICHT_ANWENDBAR`: das Thema trifft nach nachgewiesener Mandanten- und Kontenlage nicht zu.
- `AUSZIFFERBAR`: eindeutiger technischer Auszifferungskandidat; noch nicht ausgeziffert.
- `BUCHUNGSVORSCHLAG`: fachlich und rechnerisch sicherer Vorschlag; noch nicht gebucht.
- `FACHLICH_ZU_KLAEREN`: Bewertung oder Kanzleientscheidung erforderlich.
- `NICHT_PRUEFBAR`: Pflichtquelle fehlt, ist technisch nicht erreichbar oder nicht eindeutig.
- `BLOCKIERT`: Mandant oder Zielwirtschaftsjahr ist nicht eindeutig; keine DATEV-abhängige Gesamtbeurteilung zulässig.

## Ablauf

### 1. Mandant und Wirtschaftsjahr eindeutig binden

1. Mandantennummer aus dem Auftrag verwenden und über DATEV `datev://accounting/clients` zum Client-GUID auflösen. Bei keinem oder mehreren Treffern nicht raten.
2. Die verfügbaren Wirtschaftsjahre mit dem Client-GUID abrufen. Das Zielwirtschaftsjahr nicht aus dem aktuellen Kalenderjahr ableiten und keine `fiscalYearId` konstruieren.
3. Beginn, Ende, `fiscalYearId`, Sachkontenlänge und `taxation_method` des Zieljahrs dokumentieren. Daraus und aus dem Mandantenprofil die Gewinnermittlungsart bestimmen. Ein abweichendes Wirtschaftsjahr als solches behandeln. Die Buchhaltung muss für diese Vorstufe noch nicht insgesamt abschlussreif sein; den Datenstand mit Abrufzeitpunkt ausweisen.
4. Das unmittelbar vorhergehende DATEV-Wirtschaftsjahr als Vergleichsjahr bestimmen. Fehlt es, die Vorjahresanalyse `NICHT_PRUEFBAR` kennzeichnen und die übrigen Module fortsetzen.
5. Vor DATEV-Abfragen die jeweilige Ressource mit `datev_describe` beschreiben lassen. Einen Hinweis auf veraltete MCP-Toolbeschreibungen als technisches Pilotgate protokollieren; daraus keinen DATEV-Datenfehler ableiten.

### 2. Pflichtquellen direkt lesen

1. `scripts/sharepoint_target.py --mandant <Nummer>` ausführen.
2. Mandantenprofil und bei bilanzierenden Mandanten das Abgrenzungsregister an den ausgegebenen exakten SharePoint-URLs direkt abrufen. Keine allgemeine Suche vor dem Direktabruf.
3. DATEV-Kontenplan, Summen und Salden, Einzelbuchungen, Debitoren, Kreditoren sowie verdichtete OPOS vollständig und mit den richtigen Jahres-IDs abrufen.
4. Jede Quelle mit stabilem Bezeichner, Abrufzeitpunkt, URI/URL, Filter, Zeitraum und – bei Dateien – Datei-ID und SHA-256 im Reviewdatensatz nachweisen.
5. Fehlt nur die Review-Sheet-Vorlage, alle Prüfungen durchführen und `Vorbereitungsdaten.json` erzeugen. Keine eigene Excel-Struktur als vermeintliche Endvorlage erfinden.

### 3. Vollständige Startklarheits-Matrix aufbauen

1. Alle im Zieljahr bebuchten oder am Stichtag nicht auf null stehenden Bilanzkonten aus Summen und Salden und Live-Kontenplan inventarisieren.
2. Die Kernthemen aus [references/STARTKLARHEITS_CHECKLISTE.md](references/STARTKLARHEITS_CHECKLISTE.md) auch bei Nullsaldo aufnehmen.
3. Jedes inventarisierte Bilanzkonto genau einem Checklisteneintrag zuordnen. Ein unklassifiziertes Konto ist `ZU_BEREINIGEN` und blockiert den Start.
4. Je Eintrag Nullerwartung, Stichtagssaldo, Nachweis, Arbeitsspur, Startblocker und nächsten Schritt dokumentieren.
5. Belege nur prüfen, soweit sie einen konkreten Checklisten-Saldo oder ein Register erklären. Keine globale Belegvollständigkeits- oder Datenanomalieprüfung starten.

### 4. Fachmodule abarbeiten

Die Regeln aus [references/PRUEFLOGIK.md](references/PRUEFLOGIK.md) vollständig anwenden:

1. Debitoren, Kreditoren und alle offenen Posten zum Stichtag inventarisieren.
2. Eindeutige Auszifferungskandidaten ermitteln und von Umbuchungs-, Ausbuchungs- und Bewertungsfällen trennen.
3. Geldtransit funktional prüfen: SKR03 regelmäßig 1360, SKR04 regelmäßig 1460; immer am live gelesenen Kontenplan bestätigen.
4. Durchlaufende Posten funktional prüfen: SKR03 regelmäßig 1590, SKR04 regelmäßig 1370; immer am live gelesenen Kontenplan bestätigen.
5. Die bestätigte Kanzleiregel für Einzelbuchungen unter 100 EUR anwenden.
6. ARAP/PRAP-Buchungen vollständig mit dem SharePoint-Abgrenzungsregister abstimmen. Transitorische und antizipative Abgrenzungen nicht vermischen.
7. Bei EÜR statt ARAP/PRAP die Zu-/Abfluss- und Fälligkeitsprüfung nach der Fachreferenz ausführen.
8. Lohnkonten einzeln prüfen: SKR03 regelmäßig 1740, 1741, 1742, 1755 und bei Schätzverfahren 1759; SKR04 regelmäßig 3720, 3730, 3740, 3790 und bei Schätzverfahren 3759. Keine pauschale Nullregel über alle Konten anwenden.
9. Bank-, Kassen-, Steuer-, Darlehens-, Anlagen-, Vorrats-, Rückstellungs-, Gesellschafter- und sonstige Abstimmkonten nur in der Vorbereitungstiefe der Startklarheits-Checkliste bearbeiten.

### 5. Vorjahrshinweise und Übergabegrenze

1. Abschlussnahe Buchungen des Vorjahres anhand DATEV-Sequenz, Buchungsdatum, Konten, Buchungstext und `accounting_reason` als Orientierung zusammenstellen. Eine Buchung nicht allein wegen des Datums als Abschlussbuchung klassifizieren.
2. Je Vorjahresbuchung nur festhalten: damalige Buchung, verfügbare Quelle und konkreter Hinweis für den Mitarbeiter, was im Zieljahr geprüft oder neu berechnet werden könnte.
3. Vorjahresbeträge nie fortschreiben oder als aktuell notwendige Abschlussbuchung darstellen.
4. Andere Abschlussbereiche nach [references/VORBEREITUNGSABGRENZUNG.md](references/VORBEREITUNGSABGRENZUNG.md) nicht reviewen. Ergibt sich aus den bereits gelesenen Quellen ein offensichtlicher Hinweis, ihn ohne Vertiefung nach `handoff_to_annual_close` übergeben.

### 6. Reviewdaten und Mitarbeiterübergabe

1. Den kanonischen Datensatz nach [references/REVIEWDATEN.md](references/REVIEWDATEN.md) als `Vorbereitungsdaten.json` erstellen.
2. Vor Übergabe ausführen:

```text
python scripts/validate_review_data.py Vorbereitungsdaten.json
```

3. Zusätzlich `Mitarbeiterhinweise.md` erzeugen. Antwortorientiert formulieren:
   - Was im Vorjahr gebucht wurde.
   - Was davon im Zieljahr erneut zu prüfen oder zu berechnen ist.
   - Welche OPOS eindeutig auszifferbar sind.
   - Welche 1360-/1590- beziehungsweise SKR04-Fälle zu bearbeiten sind.
   - Ob 1740/1741/1742 beziehungsweise die funktionalen SKR04-Konten auf null stehen oder durch welchen Nachweis der Saldo erklärt ist.
   - Welche weiteren Checklistenpunkte vor dem Start zu bereinigen oder mit Unterlagen zu belegen sind.
   - Welche Registerabweichungen offen sind.
   - Welche außerhalb des Vorbereitungsscopes liegenden Punkte lediglich an die spätere Abschlussbearbeitung übergeben wurden.
4. Buchungsvorschläge, Auszifferungen und reine Klärungen in getrennten Tabellen ausgeben. Jeder Eintrag benötigt konkrete Quelldaten und einen nächsten Schritt.
5. Nach Erhalt der Review-Sheet-Vorlage nur eine Arbeitskopie befüllen. Bestehende Formeln, Validierungen, ausgeblendete Bereiche und Formatierungen erhalten; die Feldzuordnung zuerst gegen die Vorlage testen.
6. `STARTKLAR_FUER_ABSCHLUSSBEARBEITUNG` nur ausweisen, wenn jedes Kernthema vorhanden ist, alle Bilanzkonten klassifiziert sind und kein offener Eintrag `blocks_start: true` trägt. Die eigentlichen Abschlussentscheidungen dürfen weiterhin unter `IM_ABSCHLUSS_PRUEFEN` offen sein.

## Abschlussformulierung

Bis zur Produktivfreigabe immer sichtbar ausweisen:

`Startklarheits-Checkliste für die Abschlussbearbeitung erstellt – kein Review des vollständigen Jahresabschlusses; keine Buchung oder Auszifferung in DATEV ausgeführt.`
