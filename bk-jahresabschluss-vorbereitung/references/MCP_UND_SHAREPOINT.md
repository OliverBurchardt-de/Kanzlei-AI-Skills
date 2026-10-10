# DATEV-MCP und SharePoint

## DATEV-Zugang über den Riecken-Connector

Die Anbindung an DATEV erfolgt ausschließlich über den Riecken-DATEV-Connector (MCP-Server `Riecken`, Werkzeuge mit Präfix `datev_`). Kein anderer DATEV-Zugang und kein anderer DATEV-MCP-Server wird verwendet, auch wenn er in der Umgebung verfügbar ist. Dieser Skill verwendet den Connector ausschließlich lesend; die schreibenden Werkzeuge (`datev_add_posting`, `datev_prepare_posting_batch`, `datev_prepare_business_partner`, `datev_prepare_document_filing`, `datev_prepare_client_update`, `datev_execute_change_plan`) werden nicht aufgerufen.

Die aktuelle Werkzeugbeschreibung des Connectors ist maßgeblich. Parameter, Feldnamen und Filter nicht aus Beispielen oder früheren Läufen ableiten.

### Verbindliche Bindungskette

1. `datev_search_clients` mit der Mandantennummer aufrufen; Mandantennummer und DATEV-Bezeichnung eindeutig zur gelieferten `id` (UUID) binden. Bei keinem oder mehreren Treffern nicht raten.
2. `datev_get_client_dossier` lesen: Kontenrahmen, Sachkontenlänge, Beginn des Wirtschaftsjahres, Rechtsform, Zuständigkeiten. Fehlt die Sachkontenlänge, ist jede Kontenprüfung `NICHT_PRUEFBAR`.
3. Ziel- und Vorwirtschaftsjahr als `fiscal_year` (zum Beispiel `"2025"` und `"2024"`) aus dem Auftrag binden; nicht aus dem Kalenderjahr ableiten und den Standardwert „laufendes Wirtschaftsjahr“ nicht stillschweigend verwenden. Jahresgrenzen aus dem Beginn des Wirtschaftsjahres im Dossier ableiten; abweichende Wirtschaftsjahre als solche behandeln.
4. Existenz und Buchungsstand beider Jahre mit `datev_get_accounting_statistics` je `fiscal_year` nachweisen (gebuchte Buchungssätze je Monat). Daraus den letzten verfügbaren Buchhaltungsstand bestimmen.
5. Die Gewinnermittlungsart aus dem Mandantenprofil in SharePoint und, soweit geliefert, aus dem Dossier bestimmen. Der Connector liefert kein eigenes Feld dafür. Bleibt sie offen: `FACHLICH_ZU_KLAEREN`; das Eröffnungsbilanzmodul nicht als `NICHT_ANWENDBAR` setzen.

### Benötigte Werkzeuge

- `datev_get_account_balances`: Summen- und Saldenliste je Konto mit EB-Wert, kumulierten Soll-/Habenwerten, Jahressaldo und Monatssalden; zugleich der Live-Kontenplan mit Kontenbezeichnungen. Die Vorbereitung benötigt die vollständige Liste beider Jahre: zu Beginn des Laufs einmal die Bestätigung des Nutzers für die komplette Liste einholen und danach mit `confirmed_full_list=true` und ausreichend hohem `limit` abrufen. Gelieferte Kontenzahl gegen die Gesamtzahl prüfen; bei Abschneidung in Kontenbereichen (`account_from`/`account_to`) nachladen. Soll/Haben-Richtung beachten; Monatswerte sind Bewegungen.
- `datev_get_account_postings`: Einzelbuchungen eines Kontos mit Datum, Betrag, Soll/Haben, Gegenkonto, Belegfeld, Buchungstext, Steuerschlüssel und Kostenstellen. Für Geldtransit, durchlaufende Posten, ARAP/PRAP, Abschlussbuchungen des Vorjahrs und Vorjahresanalyse mit `account_number`, `date_from`, `date_to` und `fiscal_year` eingrenzen. `limit` so setzen, dass alle Buchungen des Zeitraums geliefert werden; die mitgelieferten Summen gelten über alle Treffer.
- `datev_search_business_partners` (`role` `debitor`/`creditor`): Personenkontenstämme; mit `limit` vollständig lesen, bis das Inventar vollständig ist.
- `datev_get_open_items` (`side=receivable`/`side=payable`): offene Posten je Seite. Jede Position ist ein OPOS-Posten (Konto + Belegfeld 1); `totals.open_sum` ist der fertige Saldo der DATEV-OPOS-Liste. Mit `status=all` oder `status=cleared` auch ausgeglichene Posten lesen, soweit für die Fortschreibung nach [OPOS_ABGLEICH.md](OPOS_ABGLEICH.md) erforderlich. Für die Eröffnungsbilanzprüfung beide Prüflinien nach [EROEFFNUNGSBILANZ.md](EROEFFNUNGSBILANZ.md) führen.
- `datev_get_asset_inventory` (`accounting_reason` `handelsrecht`/`steuerrecht`): einzige bereichsgetrennte Quelle des Connectors; für das Bereichsinventar der Eröffnungsbilanz und bei Anlagen-/Inventurthemen lesen. Enthält keine Abschreibungen oder Buchwerte.
- `datev_get_cost_centers`: nur bei Kostenstellenthemen eines Checklistenpunkts.
- `datev_search_documents`, `datev_get_document`, `datev_read_document`: nur einen für einen konkreten Checklistenpunkt benötigten Nachweis auffinden oder dessen Metadaten sichern. Keine globale DMS-Belegvollständigkeitsprüfung durchführen.
- `datev_health_check` (`accounting`, bei Bedarf `dms`): bei Verbindungs- oder Berechtigungsproblemen zuerst aufrufen.

Der Connector liefert keine Buchungsstapel, keine stapelbezogenen Buchungsdatensätze und keine Bereichskennung außerhalb des Anlagenverzeichnisses. Die Steuerrechts-Prüflinie wird deshalb nach [EROEFFNUNGSBILANZ.md](EROEFFNUNGSBILANZ.md) aus Anlagenverzeichnis, DMS-Nachweis oder vollständiger Überleitung geführt; fehlende Nachweise als `TEILNACHWEIS` oder `NICHT_PRUEFBAR` ausweisen, nicht raten.

### Mengen- und Vollständigkeitsregeln

- Jeder Abruf ist durch `limit` begrenzt. Gelieferte Anzahl immer gegen die gemeldete Gesamtzahl beziehungsweise Trefferzahl prüfen. Teilergebnisse nie als Vollbestand bezeichnen; bei Abschneidung disjunkt nachladen und alle Teilabrufe protokollieren.
- Für OPOS die Summen des Connectors verwenden; Einzelpositionen nicht als separate Rechnungen zählen, wenn sie zum selben Posten (Konto + Belegfeld 1) gehören.
- OPOS nach [OPOS_ABGLEICH.md](OPOS_ABGLEICH.md) gegen den belegten Fibu-Endsaldo abstimmen. `due_before` ist kein historischer Stichtagsparameter; heutige offene Posten nicht als damaligen Gesamtbestand ausgeben.
- Kontonummern dem Connector in normaler Schreibweise übergeben; die technische Auffüllung übernimmt der Server. Sachkonten und Personenkonten als Strings behandeln; die Sachkontenlänge aus dem Dossier verwenden.
- Ein technischer Fehler oder eine Berechtigungsmeldung des Connectors bedeutet `CONNECTOR_PRUEFUNG_ERFORDERLICH`: `datev_health_check` ausführen, Fehler protokollieren, abhängige Prüfpunkte `NICHT_PRUEFBAR`; daraus keinen DATEV-Datenfehler ableiten.

## SharePoint-Direktabruf

Die Ziele ausschließlich mit `scripts/sharepoint_target.py` bilden. Der Connectorname kann variieren; maßgeblich ist der exakte URL-Abruf.

Verbindliche Bibliothek: `https://burchardtkollegen.sharepoint.com/sites/Wissen/Mandantenbesonderheiten`. Am 20.09.2026 über `list_site_drives` live gefunden. `list_folder_items(folder_path="Mandantenbesonderheiten")` lieferte dagegen einen gleichnamigen Ordner unter `Freigegebene Dokumente`; dieser ist nicht die Zielbibliothek. Rückgabe-URL/Drive stets prüfen, Pfade nicht anhand des Namens gleichsetzen.

1. Zuerst `profile_url` direkt abrufen.
2. Bei Bilanz anschließend `accrual_url` direkt abrufen.
3. Nur Treffer akzeptieren, deren Dateiname exakt `<Mandantennummer>.md` lautet und deren Web-/Anzeige-URL zum ausgegebenen Ziel passt.
4. Wenn Markdown-Text nicht extrahiert wird, dieselbe gefundene Datei als Rohdatei laden und UTF-8 lesen.
5. Ein allgemeiner Suchtreffer, eine leere Suche oder ein Zugriff auf `Dokumente`, `Documents`, OneDrive oder `Kanzlei/Mandanten` beweist nicht, dass die Zieldatei fehlt.
6. Bei technischem Abruffehler den abhängigen Prüfpunkt `NICHT_PRUEFBAR` ausweisen. Kein leeres Ersatzregister anlegen und keine bestehende Datei überschreiben.
7. Profilinhalt vor den fachlichen Ergebnissen lesen; relevante Kontenzuordnungen, Lohnverfahren, Abgrenzungen und offene Besonderheiten mit Fundstelle übernehmen. Widersprüche zu DATEV sichtbar klären, nie unbemerkt überschreiben. Bei fehlender Mandantennummer nur Bibliothek validieren; keine beliebige Mandantendatei wählen.

## Quellenprotokoll

Je DATEV-Abruf mindestens festhalten:

- Werkzeug des Riecken-Connectors; im Reviewdatensatz als `uri` in der Form `riecken:<werkzeug>?<parameter>`, zum Beispiel `riecken:datev_get_account_postings?account_number=1590&fiscal_year=2025`,
- Bereichskennung (`accounting_reason`) bei Eröffnungsbilanzquellen und Kennzeichnung, auf welcher Grundlage diese bestimmt wurde,
- Mandanten-`id` (UUID) und `fiscal_year`,
- `account_number`, `account_from`/`account_to`, `date_from`/`date_to`, `side`, `status`, `limit` und `confirmed_full_list`, soweit verwendet,
- Abrufzeitpunkt,
- Buchungsstand und Sperr-/Festschreibestatus, soweit geliefert; sonst `unbekannt`,
- Anzahl gelesener Datensätze und Vollständigkeitsstatus.

Je SharePoint-Datei mindestens festhalten:

- exakte URL,
- Datei-/Dokument-ID,
- Dateiname,
- Änderungszeitpunkt,
- SHA-256 der gelesenen Rohdatei,
- Lesestatus.
