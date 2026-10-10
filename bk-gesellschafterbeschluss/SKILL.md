---
name: bk-gesellschafterbeschluss
description: Erstellt unterschriftsreife Gesellschafterbeschlüsse zur Feststellung eines handelsrechtlichen Jahresabschlusses, zur Entlastung der Geschäftsführung und zur Ergebnisverwendung. Verwenden, wenn für einen Mandanten ein Gesellschaftsversammlungsbeschluss beziehungsweise Feststellungs- und Ergebnisverwendungsbeschluss als Word-Dokument erstellt oder geprüft werden soll. Ermittelt Bilanzsumme und Jahresüberschuss, Jahresfehlbetrag oder Nullergebnis ausschließlich aus Kanzlei-ReWe-Daten und darf sie aus vollständigen Kontensalden selbst berechnen. Unterscheidet Vortrag, Voll- oder Teilausschüttung und Ausschüttung aus Gewinnvortrag.
---

# BK Gesellschafterbeschluss

## Ziel

Aus den aktuellen Kanzlei-ReWe-Daten und Mandantenstammdaten einen formal sauberen, unterschriftsreifen Gesellschafterbeschluss als DOCX erstellen. Bilanzsumme und Jahresergebnis bei Bedarf kontrolliert aus den Kontensalden berechnen. Niemals ungeklärte, veraltete oder aus einer unzulässigen Quelle stammende Zahlen übernehmen.

## Pflichtablauf

### 1. Abschlusswerte ausschließlich aus Kanzlei-ReWe ermitteln

1. Mandant und Geschäftsjahr in Kanzlei-ReWe eindeutig auflösen. Der Zugriff auf Kanzlei-ReWe erfolgt ausschließlich über den Riecken-DATEV-Connector (MCP-Server `Riecken`, Werkzeuge mit Präfix `datev_`); kein anderer DATEV-Zugang wird verwendet, auch wenn er in der Umgebung verfügbar ist. Der Connector wird nur lesend verwendet; schreibende Werkzeuge (`datev_add_posting`, `datev_prepare_*`, `datev_execute_change_plan`) werden nicht aufgerufen.
2. Mandant mit `datev_search_clients` über die Mandantennummer auflösen und die gelieferte `id` (UUID) verwenden; bei keinem oder mehreren Treffern nicht raten. Das Geschäftsjahr aus dem Auftrag als `fiscal_year` (zum Beispiel `"2025"`) binden, nicht aus dem Kalenderjahr ableiten und den Standardwert „laufendes Wirtschaftsjahr“ nicht stillschweigend verwenden. Mit `datev_get_accounting_statistics` nachweisen, dass das Geschäftsjahr bebucht ist.
3. Die vollständigen Summen und Salden mit `datev_get_account_balances` abrufen. Der Beschluss benötigt alle Konten: dem Nutzer zu Beginn einmal mitteilen, dass die komplette Summen- und Saldenliste gelesen wird, seine Bestätigung einholen und danach mit `confirmed_full_list=true` und ausreichend hohem `limit` abrufen. Die gelieferte Kontenzahl gegen die gemeldete Gesamtzahl prüfen; bei Abschneidung in Kontenbereichen (`account_from`/`account_to`) nachladen. Für die Berechnung je Konto Kontonummer, Bezeichnung, EB-Wert, kumulierte Soll- und Habenwerte sowie den Jahressaldo mit Soll-/Haben-Kennzeichen verwenden; die Feldnamen aus der tatsächlichen Antwort des Connectors übernehmen.
4. Gibt die Schnittstelle Bilanzsumme und Jahresergebnis nicht als fertige Felder zurück, diese Werte selbst aus den Kanzlei-ReWe-Daten berechnen. Dazu [references/rewe-berechnung.md](references/rewe-berechnung.md) vollständig lesen und anwenden.
5. Die ermittelte Ergebnisart festhalten: Jahresüberschuss, Jahresfehlbetrag oder Nullergebnis.
6. Die Quelle intern mit `Kanzlei-ReWe`, Mandantennummer, Geschäftsjahr, Abrufdatum und `berechnet aus Summen und Salden` dokumentieren.

Für Bilanzsumme und Jahresergebnis gilt daneben eine absolute DMS-Sperre:

- Niemals die DMS-Werkzeuge des Riecken-Connectors aufrufen, insbesondere nicht `datev_search_documents`, `datev_get_document`, `datev_read_document` oder `datev_lookup_dms_structure`.
- Das DMS weder durchsuchen noch öffnen, herunterladen oder auswerten. Insbesondere keine dort gespeicherten Jahresabschlüsse, früheren Gesellschafterbeschlüsse oder sonstigen Dokumente als Quelle oder Gegenprobe verwenden.
- Keine Vorjahreswerte aus einem DMS-Dokument übernehmen. Auch ein Dokument mit passendem Namen kann ein anderes Geschäftsjahr oder einen überholten Bearbeitungsstand enthalten.
- Vom Nutzer genannte oder in einem Dokument sichtbare Beträge sind nur Hinweise und ersetzen die Ermittlung aus den Kanzlei-ReWe-Daten nicht.
- Ist Kanzlei-ReWe nicht erreichbar oder fehlt das Geschäftsjahr, anhalten. Keine Zahlen aus dem DMS oder einer anderen Quelle ersatzweise übernehmen.

### 2. Stammdaten ermitteln

Die Quellensperre aus Schritt 1 betrifft die Abschlusswerte. Firma, Sitz, Gesellschafter und Geschäftsführung über den Riecken-Connector ermitteln:

1. Die in Schritt 1 ermittelte Mandanten-`id` verwenden.
2. `datev_get_client_dossier` mit `include_addressees=true` und `include_relationships=true` lesen.
3. Exakte Firma, Rechtsform, Satzungssitz/Ort und aktuelle Anschrift aus den Adressatenstammdaten übernehmen. Rechtsformschlüssel bei Bedarf mit `datev_lookup_reference_data` (`type=legal_forms`) auflösen.
4. Aktuelle Gesellschafter und gesetzliche Vertreter aus den Beziehungen des Dossiers ermitteln. Enthält die Antwort `relationships_error`, konnten die Beziehungen nicht abgerufen werden; das dem Nutzer nennen und nicht als „keine Gesellschafter“ werten.
5. Beteiligungsquote oder Alleingesellschafterstellung nur behaupten, wenn sie zuverlässig belegt ist. Andernfalls neutral von „den Gesellschaftern“ sprechen oder nachfragen.

Ohne vollständige Stammdaten nach exakter Firma, Sitz, Gesellschaftern und Geschäftsführung fragen. Registerdaten nur ergänzen, wenn sie aktuell belegt sind.

### 3. Ergebnisart bestimmen

Den Jahresergebnisbetrag als vorzeichenbehaftete Zahl erfassen:

- positiv: **Jahresüberschuss**;
- negativ: **Jahresfehlbetrag**, im Dokument als positiver Absolutbetrag ausweisen;
- null: **ausgeglichenes Jahresergebnis**.

Die verbindlichen Formulierungen aus [references/beschlusslogik.md](references/beschlusslogik.md) verwenden.

### 4. Ergebnisverwendung zwingend abfragen

Diese Frage niemals überspringen, auch wenn ein Vorjahresbeschluss vorliegt.

Bei Jahresüberschuss fragen:

1. auf neue Rechnung vortragen;
2. vollständig ausschütten;
3. teilweise ausschütten und Rest vortragen.

Bei Jahresfehlbetrag fragen:

1. Jahresfehlbetrag auf neue Rechnung vortragen;
2. zusätzlich Ausschüttung aus vorhandenem Gewinnvortrag beabsichtigt.

Bei Nullergebnis fragen, ob keine Ergebnisverwendung oder eine Ausschüttung aus Gewinnvortrag beschlossen werden soll.

Bei jeder Ausschüttung zusätzlich klären:

- Bruttoausschüttungsbetrag;
- Quelle: laufender Jahresüberschuss oder Gewinnvortrag;
- Fälligkeit/Auszahlungstag;
- Auszahlung oder Verrechnung mit einem Gesellschafterkonto;
- bei Teilausschüttung: Behandlung des Restbetrags.

Eine Ausschüttung aus dem laufenden Ergebnis bei Jahresfehlbetrag sperren. Eine Ausschüttung aus Gewinnvortrag nur nach ausdrücklicher Bestätigung erstellen; verfügbare Rücklagen, Verlustvorträge, Kapitalerhaltung und gesellschaftsvertragliche Vorgaben nicht unterstellen.

Wenn eine interaktive Auswahl verfügbar ist, zuerst eine kurze Auswahlfrage zur Ergebnisverwendung stellen. Detailfragen erst nach Auswahl „Ausschüttung“ stellen.

### 5. Weitere Beschlussparameter klären

- Entlastung der Geschäftsführung standardmäßig vorsehen, aber bei entgegenstehenden Angaben nachfragen.
- Beschlussdatum erfragen oder eine offene Datumszeile verwenden.
- Bei mehreren Geschäftsführern oder Besonderheiten klären, ob die Entlastung gemeinsam oder einzeln erfolgt.
- Abweichende Satzungsregeln, streitige Beschlussfassungen, nicht vollständig bekannte Gesellschafter oder Ausschüttungen trotz Verlusten als Klärungsfall behandeln.

### 6. Dokument erzeugen

Die Eingaben in eine JSON-Datei nach [references/eingabeschema.md](references/eingabeschema.md) übertragen und ausführen:

```bash
"$CODEX_PRIMARY_RUNTIME_PYTHON" scripts/erstelle_beschluss.py \
  --input /absoluter/pfad/eingaben.json \
  --output "/absoluter/pfad/Gesellschafterbeschluss Firma Jahr.docx"
```

Dateinamen ohne Unterstriche bilden. Das Dokument enthält regelmäßig:

1. Feststellung des Jahresabschlusses mit Bilanzsumme und richtiger Ergebnisbezeichnung;
2. Entlastung der Geschäftsführung;
3. beschlossene Ergebnisverwendung;
4. Ort, Datum und Unterschriftszeile.

### 7. Qualitätsprüfung und Übergabe

- Den Documents-Skill für DOCX-Erstellung und Renderprüfung verwenden.
- Das DOCX rendern und jede Seite visuell prüfen.
- Kontrollieren: Firma, Ort, Geschäftsjahr, Bilanzsumme, Ergebnisart, Betrag, Ergebnisverwendung, Nummerierung, Datumszeile und Unterschriftsfeld.
- Nach verbliebenen Platzhaltermarkierungen und alten Vorjahresbeträgen suchen.
- Nur die finale DOCX-Datei ausgeben; PDF nur auf ausdrücklichen Wunsch.
- In der Übergabe `Kanzlei-ReWe`, Mandantennummer, Geschäftsjahr, Abrufdatum und den Rechenstatus `aus Summen und Salden berechnet` als Quelle der Abschlusswerte sowie die Stammdatenquelle und das Konfidenzniveau nennen.

## Stop-Regeln

Keinen finalen Beschluss erstellen bei:

- nicht verfügbarem Kanzlei-ReWe-Zugriff über den Riecken-Connector (bei Verbindungsproblemen zuerst `datev_health_check`);
- nicht eindeutig aufgelöstem Mandanten oder Geschäftsjahr;
- unvollständiger Summen- und Saldenliste (gelieferte Kontenzahl kleiner als Gesamtzahl);
- nicht auflösbarer Kontenzuordnung oder verbleibender Bilanzdifferenz nach der Kontrollrechnung;
- unklarer Abgrenzung zwischen Handels- und Steuerbilanzdaten in Kanzlei-ReWe;
- unbekannter Ergebnisverwendung;
- Ausschüttung ohne Betrag oder Fälligkeit;
- nicht belastbar ermittelter Firma oder Sitz;
- unklarer Ergebnisart.

## Version

Version 1.1.0: Kanzlei-ReWe- und Stammdatenzugriff ausschließlich über den Riecken-Connector. Beschlusslogik, Eingabeschema und Dokumentenerzeugung unverändert.
