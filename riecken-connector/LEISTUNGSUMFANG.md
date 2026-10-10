# Riecken-DATEV-Connector: Leistungsumfang

Stand: 10.10.2026. Quelle: die Werkzeugschemata des MCP-Servers `Riecken`, wie sie in einer Claude-Code-Cloud-Session über ToolSearch geladen wurden. Maschinenlesbare Fassung: [baseline/tools.json](baseline/tools.json). Vergleichsskript: [scripts/vergleiche_baseline.py](scripts/vergleiche_baseline.py). Prüfablauf: [PRUEFANLEITUNG.md](PRUEFANLEITUNG.md).

Alle Werkzeuge tragen den Präfix `datev_`. Eine Mandantennummer wird in `client_id` automatisch zur UUID aufgelöst. Kontonummern werden in normaler Schreibweise übergeben; die technische Auffüllung übernimmt der Server. Schreibende Vorgänge sind zweistufig: `datev_prepare_*` erzeugt einen Change-Plan mit `diff`, `change_plan_id` und `confirmation_token`; erst `datev_execute_change_plan` schreibt nach DATEV.

## 1. Werkzeuge nach Bereich (32 in dieser Verbindung freigeschaltet)

### A. Mandanten und Kanzlei (lesend, Anwendung `master-data`)

| Werkzeug | Leistung | Pflichtparameter |
|---|---|---|
| `datev_search_clients` | Mandantensuche nach Name (unscharf), Mandantennummer, UUID, Telefon, E-Mail oder E-Mail-Domain; liefert `id` für Folgeaufrufe | `search` |
| `datev_get_client_dossier` | Vollständiges Dossier: Kerndaten, Adressat mit Adressen, Kontaktdaten, Bankverbindungen, Beziehungen (Gesellschafter, gesetzliche Vertreter, Angehörige), Zuständigkeiten, Kategorien, Gruppen; `relationships_error` signalisiert nicht abrufbare Beziehungen | `client_id` |
| `datev_search_employees` | Kanzlei-Mitarbeiter mit Details; Filter Name, Personalnummer, Status | keine |
| `datev_search_responsibilities` | Zuständigkeiten je Mandant, je Mitarbeiter oder je Zuständigkeitsbereich | keine |
| `datev_lookup_reference_data` | DATEV-Kataloge: Rechtsformen, Länder, Banken, Finanzämter, Zuständigkeitsbereiche, Beziehungstypen, Mandantenkategorien, Mandantengruppen | `type` |
| `datev_health_check` | Erreichbarkeit der DATEV-API je Anwendung (`master-data`, `accounting`, `dms`, `order-management`) | keine |

### B. Stammdaten schreibend (Change-Plan)

| Werkzeug | Leistung | Pflichtparameter |
|---|---|---|
| `datev_prepare_client_update` | Mandanten- und Adressatenstammdaten ändern: Name, Adressen, Kontaktdaten, Bankverbindungen, Mandantenfelder; Unterobjekte werden vollständig überschrieben | `client_id`, `patch` |
| `datev_prepare_business_partner` | Debitor oder Kreditor anlegen mit Adresse, USt-IdNr., IBAN/BIC, Kurzname, Wunschkontonummer; Dublettenprüfung nach Name | `client_id`, `role`, `name` |
| `datev_execute_change_plan` | Führt einen Change-Plan aus und überschreibt Daten in DATEV | `change_plan_id`, `confirmation_token` |
| `datev_cancel_change_plan` | Verwirft einen Change-Plan | `change_plan_id` |

### C. Rechnungswesen lesend (Anwendung `accounting`)

| Werkzeug | Leistung | Pflichtparameter |
|---|---|---|
| `datev_get_account_balances` | Summen- und Saldenliste je Konto: EB-Wert, Soll/Haben kumuliert, Jahressaldo, Monatssalden. Einzelkonto oder Kontenbereich; komplette Liste nur mit `confirmed_full_list=true` nach Nutzerbestätigung; `limit` Standard 20 | `client_id` |
| `datev_get_account_postings` | Kontoblatt eines Kontos: Datum, Betrag, Soll/Haben, Gegenkonto, Belegfeld, Buchungstext, Steuerschlüssel, KOST1/KOST2; Summen über alle Treffer; `limit` Standard 30, neueste zuerst | `client_id`, `account_number` |
| `datev_get_open_items` | Offene Posten je Seite (`receivable`/`payable`): Fälligkeit, Verzugstage, Mahnstufe, Sperren, Zahlungsträger; `status` open/cleared/all; `totals.open_sum` ist der fertige OPOS-Saldo | `client_id`, `side` |
| `datev_get_bwa` | BWA (kurzfristige Erfolgsrechnung) für das laufende Wirtschaftsjahr oder einen Monatsbereich; Kontendetails je Zeile optional; Ergebnisse werden zwischengespeichert, `refresh` erzwingt aktuelle Zahlen, `pending` bedeutet Hintergrundberechnung | `client_id` |
| `datev_get_accounting_statistics` | Buchungssätze je Monat im Wirtschaftsjahr (Primanota und Journal): „Wird gebucht?“, „Bis wann ist gebucht?“ | `client_id` |
| `datev_get_asset_inventory` | Anlagenverzeichnis: Inventarnummer, Bezeichnung, Sachkonto, Anschaffungsdatum, Nutzungsdauer, Standort, Seriennummer, Kostenstelle; Bewertungsbereich wählbar (`steuerrecht`, `handelsrecht`, `kalkulatorisch`, `ifrs`); keine AfA oder Buchwerte | `client_id` |
| `datev_get_cost_centers` | Kostenstellenstammdaten KOST1/KOST2: Nummer, Bezeichnung, Bebuchbarkeit, Verantwortlicher; optional Kostensätze | `client_id` |
| `datev_search_business_partners` | Debitoren und Kreditoren eines Mandanten nach Name oder Kontonummer, Rolle wählbar | `client_id` |
| `datev_suggest_posting` | Kontierungsvorschlag in einem Aufruf: Wirtschaftsjahr-Check, Personenkonto oder nächste freie Nummer, bisherige Kontierung des Partners, Lerndatei, Kontokandidaten, Steuerschlüssel, bei Belegbilderservice Belegtypen | `client_id` |

### D. Buchen (Zwischenspeicher und Stapel)

| Werkzeug | Leistung | Pflichtparameter |
|---|---|---|
| `datev_add_posting` | Buchungssätze in den Zwischenspeicher aufnehmen, einzeln oder bis 100 je Aufruf; Sofortprüfung von Belegdatum, Konten, Steuerschlüssel; Beleg nur über `document_guid` eines bereits in Unternehmen online liegenden Belegs; Belegdateien aus dem Chat sind auf dieser Verbindung nicht möglich | `client_id` |
| `datev_list_postings` | Zwischengespeicherte Buchungen je Mandant und Monat mit Summen und IDs | keine |
| `datev_remove_posting` | Zwischengespeicherte Buchungen entfernen, einzeln oder alle | keine |
| `datev_prepare_posting_batch` | Aus dem Zwischenspeicher einen Change-Plan mit je einem Buchungsstapel pro Monat bilden; Stapelname bis 30 Zeichen; Ausführung postet die Stapel nicht festgeschrieben | `client_id` |

### E. Dokumentenmanagement lesend (Anwendung `dms`)

| Werkzeug | Leistung | Pflichtparameter |
|---|---|---|
| `datev_search_documents` | Dokumentsuche nach Mandant, Jahr, Status, Stichwort, Ablage, Ordner, Register, Änderungszeitraum; Cache mit `archive=true` umgehbar | keine |
| `datev_get_document` | Metadaten eines Dokuments und seine Dateien und Ordner (Struktur-Elemente) | `document_id` |
| `datev_read_document` | Inhalt extrahieren: PDF (Text oder OCR), Bilder (OCR), DOCX, XLSX, Text, E-Mails (EML/MSG) mit Kopfdaten, Text und Anhangsliste; auch Dateien eines Upload-Links | keine, aber `document_id` oder `upload_id` |
| `datev_document_status_overview` | Aggregierter Bearbeitungsstand: Anzahl je Status und Dokumentklasse, Posteingang, ausgecheckte Dokumente | keine |
| `datev_lookup_dms_structure` | Ablagestruktur Ablagen, Ordner, Register mit IDs sowie Bearbeitungsstatus-Katalog | keine |
| `datev_create_download_link` | Öffentlicher Download-Link für ein Dokument oder einen Anhang, bis 4 Stunden gültig; Inhalte laufen nicht durch das Modell | `document_id` |

### F. Dokumentenmanagement schreibend (Change-Plan)

| Werkzeug | Leistung | Pflichtparameter |
|---|---|---|
| `datev_prepare_document_filing` | Neues Dokument ablegen: Datei über native Übergabe, Chat-Anhang, Upload-Link, `attachment_ref` oder Base64 (nur sehr kleine Dateien); ohne Datei kommt ein Upload-Link; Metadaten Beschreibung, Klasse, Ablageort, Status, Jahr, Monat, Belegdatum, Belegnummer, Betrag, Schlagworte, Notiz | `client`, `description` |
| `datev_prepare_document_update` | Metadaten eines Dokuments ändern: Beschreibung, Schlagworte, Notiz, Status, Klasse, Jahr/Monat, Belegfelder, Ablageort | `document_id`, `patch` |
| `datev_prepare_document_file` | Datei eines Dokuments ersetzen (`create_revision`) oder zusätzliche Datei anhängen (`add_file`); nur vollwertiges DATEV DMS | `document_id`, `action` |

## 2. Laut Serveranweisung vorhandene, in dieser Verbindung nicht freigeschaltete Werkzeuge

Die Anweisung des MCP-Servers nennt weitere Werkzeuge mit dem Zusatz „falls verfügbar“. Sie fehlen in der Werkzeugliste dieser Verbindung und sind damit berechtigungsabhängig:

- `datev_prepare_personalakte_upload` und `datev_upload_status`: Dokumente in die DATEV Personalakte, Statusabfrage von Uploads.
- `datev_prepare_duo_upload`: Belegbilder nach Unternehmen online übertragen; die daraus entstehende `document_guid` wird in `datev_add_posting` referenziert.
- `datev_prepare_letter`: Mandantenbrief als DIN-5008-PDF mit Briefpapier rendern, Vorschau-Link, Change-Plan.
- `datev_workflow`: Workflow-Katalog mit `next_step`-Steuerung.

Erscheint eines dieser Werkzeuge in einer späteren Prüfung, ist das eine Erweiterung des Leistungsumfangs und nach [PRUEFANLEITUNG.md](PRUEFANLEITUNG.md) zu behandeln.

## 3. Nutzung in den Skills dieses Repositories (Stand 10.10.2026)

| Werkzeug | Monatsbuchhaltung | Monatsreview | Abschlussvorbereitung | Gesellschafterbeschluss | E-Mail-DMS-Ablage |
|---|---|---|---|---|---|
| `datev_health_check` | x | x | x | x | |
| `datev_search_clients` | x | x | x | x | x |
| `datev_get_client_dossier` | x | x | x | x | |
| `datev_lookup_reference_data` | | | | x | |
| `datev_get_account_balances` | x | x | x | x | |
| `datev_get_account_postings` | x | x | x | | |
| `datev_get_open_items` | | x | x | | |
| `datev_get_accounting_statistics` | x | x | x | x | |
| `datev_get_asset_inventory` | x | | x | | |
| `datev_get_cost_centers` | | | x | | |
| `datev_search_business_partners` | x | | x | | |
| `datev_suggest_posting` | x | | | | |
| `datev_add_posting`, `datev_list_postings`, `datev_prepare_posting_batch` | x (nur Abschnitt 5) | | | | |
| `datev_prepare_business_partner` | x (nur Abschnitt 5) | | | | |
| `datev_execute_change_plan`, `datev_cancel_change_plan` | x | | | | x |
| `datev_search_documents`, `datev_get_document`, `datev_read_document` | | | x (nur Einzelnachweis) | gesperrt | x |
| `datev_lookup_dms_structure` | | | | gesperrt | x |
| `datev_prepare_document_filing` | | | | | x |
| `datev_create_download_link` | | | | | x |

Von keinem Skill genutzt: `datev_get_bwa`, `datev_document_status_overview`, `datev_search_employees`, `datev_search_responsibilities`, `datev_prepare_client_update`, `datev_prepare_document_update`, `datev_prepare_document_file`, `datev_remove_posting`.

## 4. Befunde aus der Bestandsaufnahme vom 10.10.2026

1. **Kostenstellenkatalog vorhanden, Skill verneint ihn.** `bk-monatsbuchhaltung/references/EINGABESCHEMA.md` sagt, der Connector biete keinen eigenen Kostenstellenkatalog, und leitet Kostenstellen aus Vorbuchungen und Anlagenverzeichnis ab. `datev_get_cost_centers` liefert den Katalog direkt. Empfehlung: Kostenstellenvalidierung in der Monatsbuchhaltung auf `datev_get_cost_centers` umstellen (neue Skill-Version mit Generator- und Validatoranpassung erforderlich).
2. **BWA ungenutzt.** `datev_get_bwa` eignet sich für die GuV-Plausibilität (M4) im Monatsreview als zweite Sicht neben der Summen- und Saldenliste. Zu beachten: Zwischenspeicher mit Stand `cache.cached_at`, `refresh` nur bei Bedarf.
3. **Dokumentstatus ungenutzt.** `datev_prepare_document_update` könnte in der E-Mail-DMS-Ablage den Bearbeitungsstatus nachträglich setzen; `datev_document_status_overview` eignet sich für eine Posteingangsübersicht je Mandant.
4. **DUO-Belegupload nicht freigeschaltet.** Die Monatsbuchhaltung weist DUO-Belegtransfer-ZIPs zum manuellen Upload aus; `datev_prepare_duo_upload` würde das automatisieren, ist aber in dieser Verbindung nicht verfügbar. Freischaltung beim Anbieter klären.
5. **Vollständige SuSa nur mit Bestätigung.** `datev_get_account_balances` liefert die komplette Liste nur nach ausdrücklicher Bestätigung des Nutzers. Monatsreview, Abschlussvorbereitung und Gesellschafterbeschluss holen diese Bestätigung zu Beginn ein; ohne sie laufen die Skills nicht vollständig.
6. **Keine Wirtschaftsjahresliste, keine Gewinnermittlungsart, keine Buchungsstapel mit Bereichskennung.** Diese Daten des früheren Zugangs liefert der Connector nicht. Die Skills binden das Wirtschaftsjahr aus dem Auftrag, weisen es über `datev_get_accounting_statistics` nach und führen die Steuerrechts-Prüflinie über Anlagenverzeichnis, DMS-Nachweis oder Überleitung.
