---
name: bk-jahresabschluss-vorbereitung
description: Bereitet Jahresabschlüsse buchhalterisch vor, prüft Eröffnungswerte getrennt nach Handels- und Steuerrecht und stimmt Debitoren-/Kreditoren-OPOS mit dem aktuellen Buchhaltungsstand ab. Liest DATEV und die Mandantenbesonderheiten in SharePoint, dokumentiert Kontenabstimmungen und Startblocker. Verwenden auch für eine einzelne Eröffnungsbilanzprüfung mit Excel-Arbeitspapier; kein vollständiger Jahresabschlussreview oder DATEV-Import.
---

# B&K Abschlussvorbereitung – Startklarheit v0.6.0

## Ziel und Grenze

Arbeite die buchhalterischen Vorarbeiten und Pflichtnachweise ab, die vorhanden sein müssen, damit der zuständige Mitarbeiter sinnvoll mit dem Jahresabschluss beginnen kann. Der Skill beurteilt Startklarheit für die Abschlussbearbeitung, nicht Abschlussreife, Vollständigkeit oder Richtigkeit des Jahresabschlusses.

- DATEV, OPOS und SharePoint während der Vorbereitung nur lesen.
- Keine Auszifferung ausführen, keinen Buchungsstapel importieren und keine SharePoint-Datei ändern.
- Keine Buchungsstapel erstellen oder übertragen und keine DMS-Ablage ausführen. Lokale Arbeitspapiere und klar gekennzeichnete Vorschläge sind möglich.
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
7. [references/EROEFFNUNGSBILANZ.md](references/EROEFFNUNGSBILANZ.md)
8. [references/OPOS_ABGLEICH.md](references/OPOS_ABGLEICH.md)

Bei einem Auftrag nur zur Eröffnungsbilanzprüfung die Schritte 1–3 sowie deren Arbeitspapier ausführen; keine vollständige Startklarheit bestätigen. Die fachlichen Regeln bleiben dieselben.

## Statusmodell

- `IM_VORBEREITUNGSSCOPE_UNAUFFAELLIG`: der eng begrenzte Vorbereitungspunkt wurde ohne Befund abgearbeitet; keine Aussage zum Gesamtabschluss.
- `AUF_NULL`: ein Checklistenkonto steht centgenau auf null.
- `ABGESTIMMT`: ein zulässiger Saldo ist mit der maßgeblichen Unterlage oder einem Register centgenau erklärt.
- `TEILNACHWEIS`: ein Bereich oder eine Teilmenge ist belegt, die vollständige Stichtagsherleitung oder Abstimmung fehlt; kein erledigter Prüfpunkt.
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

1. Mandantennummer aus dem Auftrag verwenden und über den Riecken-Connector mit `datev_search_clients` zur Mandanten-`id` (UUID) auflösen. Bei keinem oder mehreren Treffern nicht raten. DATEV wird ausschließlich über den Riecken-Connector nach [references/MCP_UND_SHAREPOINT.md](references/MCP_UND_SHAREPOINT.md) gelesen.
2. Kerndaten mit `datev_get_client_dossier` lesen: Kontenrahmen, Sachkontenlänge, Beginn des Wirtschaftsjahres, Rechtsform. Das Zielwirtschaftsjahr aus dem Auftrag als `fiscal_year` binden; nicht aus dem aktuellen Kalenderjahr ableiten und den Standardwert „laufendes Wirtschaftsjahr“ nicht stillschweigend verwenden.
3. Existenz und Buchungsstand des Zieljahrs mit `datev_get_accounting_statistics` nachweisen. Beginn, Ende, `fiscal_year`, Sachkontenlänge und Gewinnermittlungsart dokumentieren. Die Gewinnermittlungsart aus dem Mandantenprofil und, soweit geliefert, aus dem Dossier bestimmen; der Connector liefert kein eigenes Feld dafür. Ein abweichendes Wirtschaftsjahr als solches behandeln. Die Buchhaltung muss für diese Vorstufe noch nicht insgesamt abschlussreif sein; den Datenstand mit Abrufzeitpunkt ausweisen.
4. Das unmittelbar vorhergehende Wirtschaftsjahr als Vergleichsjahr bestimmen und ebenfalls mit `datev_get_accounting_statistics` nachweisen. Liefert der Connector dafür keine Daten, die Vorjahresanalyse `NICHT_PRUEFBAR` kennzeichnen und die übrigen Module fortsetzen.
5. Die aktuelle Werkzeugbeschreibung des Connectors ist maßgeblich; Parameter und Feldnamen nicht erfinden. Bei Verbindungs- oder Berechtigungsproblemen zuerst `datev_health_check` aufrufen. Einen technischen Fehler des Connectors als Pilotgate protokollieren; daraus keinen DATEV-Datenfehler ableiten.

### 2. Pflichtquellen direkt lesen

1. `scripts/sharepoint_target.py --mandant <Nummer>` ausführen.
2. Mandantenprofil und bei bilanzierenden Mandanten das Abgrenzungsregister an den ausgegebenen exakten SharePoint-URLs direkt abrufen. Die Bibliothek ist `https://burchardtkollegen.sharepoint.com/sites/Wissen/Mandantenbesonderheiten`. Profilinhalt vor fachlichen Schlussfolgerungen lesen und einschlägige Besonderheiten mit Quelle den Prüfpunkten zuordnen. Keine allgemeine Suche vor dem Direktabruf.
3. Über den Riecken-Connector vollständig und mit dem richtigen `fiscal_year` abrufen: Summen- und Saldenliste einschließlich Kontenplan beider Jahre (`datev_get_account_balances`, nach Bestätigung des Nutzers mit `confirmed_full_list=true`), Einzelbuchungen der Prüfkonten (`datev_get_account_postings`), Debitoren und Kreditoren (`datev_search_business_partners`) sowie offene Posten beider Seiten (`datev_get_open_items`).
4. Jede Quelle mit stabilem Bezeichner, Abrufzeitpunkt, Werkzeug und Parametern beziehungsweise URL, Zeitraum und – bei Dateien – Datei-ID und SHA-256 im Reviewdatensatz nachweisen.
5. Fehlt nur die Review-Sheet-Vorlage, alle Prüfungen durchführen und `Vorbereitungsdaten.json` erzeugen. Das definierte Excel-Arbeitspapier zur Eröffnungsbilanz ist unabhängig davon zu erstellen; es ersetzt die noch ausstehende Kanzlei-Gesamtvorlage nicht.

### 3. Eröffnungsbilanz je Rechnungslegungsbereich prüfen

1. Handelsrecht und Steuerrecht als zwei eigenständige Prüflinien führen. Der Riecken-Connector liefert keine bereichsgetrennten Buchungsstapel; eine Bereichskennung (`accounting_reason`) ist nur im Anlagenverzeichnis (`datev_get_asset_inventory`) verfügbar. Das Bereichsinventar für Vor- und Zieljahr deshalb aus Anlagenverzeichnis je Bewertungsbereich, DMS-Nachweisen und Mandantenprofil aufbauen und offen dokumentieren. Ein fehlender DMS-Titel beweist keinen fehlenden Steuerrechtsbereich.
2. Vollständige Schluss- und Eröffnungswerte je Prüflinie beschaffen oder aus belegter Grundbuchhaltung und vollständiger Wertschicht herleiten. Eine gemeinsame SuSa allein genügt nicht. Unvollständige Herleitung als `TEILNACHWEIS` oder `NICHT_PRUEFBAR` ausweisen und den Start sperren.
3. Nach [references/EROEFFNUNGSBILANZ.md](references/EROEFFNUNGSBILANZ.md) zuerst kontengleich prüfen, nur belegte zulässige Gruppen und finale Ergebnisbrücken verwenden und das Excel-Arbeitspapier erstellen. Keine Ansatz- oder Bewertungsentscheidung treffen.
4. Bei EÜR das Thema nur mit begründeter Gewinnermittlungsart `NICHT_ANWENDBAR` setzen. Bei Erstjahr/Neugründung die Eröffnungswerte gegen die maßgeblichen Gründungs-/Übernahmeunterlagen prüfen lassen; fehlendes Vorjahr bedeutet nicht automatisch einen Nullvortrag.

### 4. Vollständige Startklarheits-Matrix aufbauen

1. Alle im Zieljahr bebuchten oder am Stichtag nicht auf null stehenden Bilanzkonten aus Summen und Salden und Live-Kontenplan inventarisieren.
2. Die Kernthemen aus [references/STARTKLARHEITS_CHECKLISTE.md](references/STARTKLARHEITS_CHECKLISTE.md) auch bei Nullsaldo aufnehmen.
3. Jedes inventarisierte Bilanzkonto genau einem Checklisteneintrag zuordnen. Ein unklassifiziertes Konto ist `ZU_BEREINIGEN` und blockiert den Start.
4. Je Eintrag Nullerwartung, Stichtagssaldo, Nachweis, Arbeitsspur, Startblocker und nächsten Schritt dokumentieren.
5. Belege nur prüfen, soweit sie einen konkreten Checklisten-Saldo oder ein Register erklären. Keine globale Belegvollständigkeits- oder Datenanomalieprüfung starten.

### 5. Fachmodule abarbeiten

Die Regeln aus [references/PRUEFLOGIK.md](references/PRUEFLOGIK.md) vollständig anwenden:

1. Debitoren, Kreditoren und alle offenen Posten inventarisieren und nach [references/OPOS_ABGLEICH.md](references/OPOS_ABGLEICH.md) je Seite, Personenkonto und Währung mit dem letzten verfügbaren Buchhaltungsstand abstimmen. Historischen Abschlussstichtag und aktuellen Ausgleichsstand getrennt ausweisen; spätere Zahlungen nachvollziehen.
2. Eindeutige Auszifferungskandidaten ermitteln und von Umbuchungs-, Ausbuchungs- und Bewertungsfällen trennen.
3. Geldtransit funktional prüfen: SKR03 regelmäßig 1360, SKR04 regelmäßig 1460; immer am live gelesenen Kontenplan bestätigen.
4. Durchlaufende Posten funktional prüfen: SKR03 regelmäßig 1590, SKR04 regelmäßig 1370; immer am live gelesenen Kontenplan bestätigen.
5. Die bestätigte Kanzleiregel für Einzelbuchungen unter 100 EUR anwenden.
6. ARAP/PRAP-Buchungen vollständig mit dem SharePoint-Abgrenzungsregister abstimmen. Transitorische und antizipative Abgrenzungen nicht vermischen.
7. Bei EÜR statt ARAP/PRAP die Zu-/Abfluss- und Fälligkeitsprüfung nach der Fachreferenz ausführen.
8. Lohnkonten einzeln prüfen: SKR03 regelmäßig 1740, 1741, 1742, 1755 und bei Schätzverfahren 1759; SKR04 regelmäßig 3720, 3730, 3740, 3790 und bei Schätzverfahren 3759. Keine pauschale Nullregel über alle Konten anwenden.
9. Bank-, Kassen-, Steuer-, Darlehens-, Anlagen-, Vorrats-, Rückstellungs-, Gesellschafter- und sonstige Abstimmkonten nur in der Vorbereitungstiefe der Startklarheits-Checkliste bearbeiten.

### 6. Vorjahrshinweise und Übergabegrenze

1. Abschlussnahe Buchungen des Vorjahres anhand Buchungsdatum, Konto, Gegenkonto, Belegfeld und Buchungstext aus `datev_get_account_postings` der betroffenen Konten als Orientierung zusammenstellen. Eine Buchung nicht allein wegen des Datums als Abschlussbuchung klassifizieren.
2. Je Vorjahresbuchung nur festhalten: damalige Buchung, verfügbare Quelle und konkreter Hinweis für den Mitarbeiter, was im Zieljahr geprüft oder neu berechnet werden könnte.
3. Vorjahresbeträge nie fortschreiben oder als aktuell notwendige Abschlussbuchung darstellen.
4. Andere Abschlussbereiche nach [references/VORBEREITUNGSABGRENZUNG.md](references/VORBEREITUNGSABGRENZUNG.md) nicht reviewen. Ergibt sich aus den bereits gelesenen Quellen ein offensichtlicher Hinweis, ihn ohne Vertiefung nach `handoff_to_annual_close` übergeben.

### 7. Reviewdaten und Mitarbeiterübergabe

1. Den kanonischen Datensatz nach [references/REVIEWDATEN.md](references/REVIEWDATEN.md) als `Vorbereitungsdaten.json` erstellen.
2. Vor Übergabe ausführen:

```text
python scripts/validate_review_data.py Vorbereitungsdaten.json
```

3. Zusätzlich `Mitarbeiterhinweise.md` erzeugen. Antwortorientiert formulieren:
   - Was im Vorjahr gebucht wurde.
   - Was davon im Zieljahr erneut zu prüfen oder zu berechnen ist.
   - Welche OPOS eindeutig auszifferbar sind.
   - Ob Debitoren- und Kreditoren-OPOS zu Personenkonten und zugeordneten Sammelkonten passen, welcher Buchhaltungsstand verglichen wurde und welche Differenzen oder späteren Ausgleiche bestehen.
   - Welche 1360-/1590- beziehungsweise SKR04-Fälle zu bearbeiten sind.
   - Ob 1740/1741/1742 beziehungsweise die funktionalen SKR04-Konten auf null stehen oder durch welchen Nachweis der Saldo erklärt ist.
   - Welche weiteren Checklistenpunkte vor dem Start zu bereinigen oder mit Unterlagen zu belegen sind.
   - Welche Registerabweichungen offen sind.
   - Welche Eröffnungsbilanzbereiche nachgewiesen und abgestimmt sind, welche Quelle je Bereich fehlt und welche Differenz vor dem Start bereinigt werden muss.
   - Welche außerhalb des Vorbereitungsscopes liegenden Punkte lediglich an die spätere Abschlussbearbeitung übergeben wurden.
4. Buchungsvorschläge, Auszifferungen und reine Klärungen in getrennten Tabellen ausgeben. Jeder Eintrag benötigt konkrete Quelldaten und einen nächsten Schritt.
5. Nach Erhalt der Review-Sheet-Vorlage nur eine Arbeitskopie befüllen. Bestehende Formeln, Validierungen, ausgeblendete Bereiche und Formatierungen erhalten; die Feldzuordnung zuerst gegen die Vorlage testen.
6. `STARTKLAR_FUER_ABSCHLUSSBEARBEITUNG` nur ausweisen, wenn jedes Kernthema vorhanden ist, alle Bilanzkonten klassifiziert sind, Handelsrecht und Steuerrecht jeweils abgestimmt oder fachlich nachgewiesen nicht anwendbar sind, beide OPOS-Seiten aktuell und zum Abschlussstichtag abgestimmt sind und kein offener Eintrag `blocks_start: true` trägt. Bei nachgewiesener EÜR entfällt das Eröffnungsbilanzmodul. Die eigentlichen Abschlussentscheidungen dürfen weiterhin unter `IM_ABSCHLUSS_PRUEFEN` offen sein.

## Abschlussformulierung

Bis zur Produktivfreigabe immer sichtbar ausweisen:

`Startklarheits-Checkliste für die Abschlussbearbeitung erstellt – kein Review des vollständigen Jahresabschlusses; keine Buchung oder Auszifferung in DATEV ausgeführt.`

Bei der Eröffnungsbilanzprüfung stattdessen den konkreten Prüfungsumfang benennen. Knapp ausgeben: Ergebnis Handelsrecht; Ergebnis Steuerrecht mit `vollständig`, `teilweise` oder `nicht prüfbar`; wesentliche offene Punkte; begründetes Konfidenzniveau; präzise Quellenangaben und Link zum Excel-Arbeitspapier. Ein lokaler Test ist keine fachliche Pilotfreigabe.
