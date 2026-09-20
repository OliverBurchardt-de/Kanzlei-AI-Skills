# DATEV-MCP und SharePoint

## DATEV-Klardaten-MCP

Vor jeder fachlichen Abfrage zuerst `datev_describe` für das Modul oder die konkrete Ressourcen-URI aufrufen. Ressourcen, Filterfelder und ID-Formate nicht aus Beispielen ableiten.

### Verbindliche ID-Kette

1. `datev://accounting/clients` ohne erfundene IDs auflisten.
2. Mandantennummer und DATEV-Bezeichnung eindeutig zum `clientId`-GUID binden.
3. `datev://accounting/fiscal_years` mit `clientId` auflisten.
4. Ziel- und Vorwirtschaftsjahr anhand der tatsächlich gelieferten Zeiträume auswählen.
5. `fiscalYearId` im Format des gelieferten DATEV-Werts verwenden; niemals konstruieren.
6. `account_length` aus dem konkreten Wirtschaftsjahr übernehmen und für die Gewinnermittlungsart `taxation_method` mit abrufen.

### Benötigte Ressourcen

- `datev://accounting/general_ledger_accounts`: Live-Kontenplan und Kontenfunktionen.
- `datev://accounting/accounting_sums_and_balances`: Salden und Monatsbewegungen; vollständig paginieren und Soll/Haben-Richtung berücksichtigen.
- Für die Eröffnungsbilanzprüfung beide Prüflinien nach [EROEFFNUNGSBILANZ.md](EROEFFNUNGSBILANZ.md) führen. Die SuSa-Ressource dokumentiert keinen Bereichsparameter. Deshalb Stapel beider Jahre vollständig auf `accounting_reason` auswerten, zugehörige Buchungssätze lesen und bereichsbezogene Schluss-/Eröffnungswerte direkt belegen oder vollständig herleiten. Gemeinsame SuSa und identische Teilmengen sind kein vollständiger Steuernachweis.
- `datev://accounting/account_postings`: Einzelbuchungen für Geldtransit, durchlaufende Posten, ARAP/PRAP und Vorjahresanalyse. Mit technischem Konto und Datum eingrenzen; diese Ressource nicht mit `top`/`skip` aufrufen.
- `datev://accounting/debitors` und `datev://accounting/creditors`: Personenkontenstämme vollständig paginieren.
- `datev://accounting/condensed_accounts_receivable` und `datev://accounting/condensed_accounts_payable`: bevorzugte logische OPOS-Sicht.
- `datev://accounting/accounts_receivable` und `datev://accounting/accounts_payable`: Komponenten nur für die Detailprüfung eines Kandidaten. Einzelzeilen nicht als separate Rechnungen zählen.
- `datev://accounting/accounting_sequences_processed` und `datev://accounting/accounting_records`: für die Eröffnungsbilanz in beiden Jahren verpflichtend; Stapel und stapelbezogene Datensätze vollständig paginieren. Die am 20.09.2026 beschriebenen Ressourcen besitzen keinen `filter`-Parameter; `accounting_reason` aus den gelieferten Daten auswerten, keinen Filter erfinden. Zurückgelieferte Stapel-IDs verwenden.
- `datev://accounting/stocktakings`: nur bei vorhandenem Anlagen-/Inventurthema den Nebenbuchstatus für die Vorbereitung lesen.
- `datev://payroll/financial_accounting`: bei Lohnmandanten ergänzende lohnrelevante Fibu-Daten lesen. Payroll-Client-ID und `referenceDate` nach der aktuellen Ressourcenbeschreibung getrennt auflösen; Accounting-IDs nicht wiederverwenden.
- `datev://dms/documents` und `datev://dms/structure_items`: nur einen für einen konkreten Checklistenpunkt benötigten Nachweis auffinden oder dessen Metadaten sichern. Keine globale DMS-Belegvollständigkeitsprüfung durchführen.

### Filter- und Mengenregeln

- Für OPOS sind typischerweise `account_number`, `document_field1`, `date`, `due_date`, `open_balance_of_item` und `is_cleared` zulässige Filter; die jeweils aktuelle Beschreibung ist maßgeblich.
- Für gewöhnliche OPOS-Berichte die verdichteten Ressourcen verwenden. Komponenten erst nach Auswahl eines logischen Falls lesen.
- `document_field1` mit der dafür beschriebenen Abfrageform verwenden; nicht unzulässig mit Paging kombinieren.
- Alle paginierbaren Ressourcen bis zum Ende lesen. Verdichtete OPOS unterstützen nach aktueller Ressourcenbeschreibung kein `top`/`skip`; ein zulässig gefiltertes Ergebnis vollständig verwenden. Teilergebnisse nie als Vollbestand bezeichnen.
- OPOS nach [OPOS_ABGLEICH.md](OPOS_ABGLEICH.md) gegen den belegten Fibu-Endsaldo abstimmen. SuSa-Monatswerte sind Bewegungen. `date` ist kein zugesicherter historischer OPOS-Stichtagsparameter; heutige offene Posten nicht als damaligen Gesamtbestand ausgeben.
- Technische Kontonummern anhand `account_length` bilden. Sachkonten und Personenkonten als Strings behandeln.
- Eine MCP-Warnung über veraltete Toolbeschreibungen bedeutet `MCP_CLIENT_REFRESH_ERFORDERLICH`. Vor Pilot und Produktion Integration aktualisieren oder neu verbinden und den Ressourcenkatalog erneut beschreiben lassen.

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

- Ressourcen-URI,
- Bereichskennung (`accounting_area_id`) bei Eröffnungsbilanzquellen und Kennzeichnung, auf welcher Grundlage diese bestimmt wurde,
- Client-GUID und Wirtschaftsjahr-ID,
- `select`, `filter`, `top` und `skip`, soweit verwendet,
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
