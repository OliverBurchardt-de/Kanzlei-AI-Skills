# Eingabeschema für `build_package.py`

Der Agent erstellt eine UTF-8-JSON-Datei. Technische GUIDs, Paketnamen und Dateinamen erzeugt ausschließlich der Generator.

## `run`

Pflichtfelder:

- `beraternummer`, `mandantennummer`, `buchungsmonat`, `wirtschaftsjahr_beginn`
- `sachkontenlaenge`, `sachkontenrahmen`, `waehrung`, `accounting_method`
- `datev_connection_verified: true`, `mandantenprofil_verified: true`
- `kostenstellenpflicht: false`
- SharePoint-Nachweise und `datev_live_evidence`
- `vat_config`
- `account_config`
- `person_account_ranges`

Beispiel:

```json
{
  "vat_config": {
    "sales_treatment": "gemischt",
    "input_tax_deduction": "anteilig",
    "default_domestic_input_treatment": "anteilige_vorsteuer",
    "general_cost_input_tax_rate": 45.5,
    "special_rules": []
  },
  "account_config": {
    "private_expense": "4655",
    "gwg": "0480",
    "clarification": "1590",
    "hospitality_deductible": "4650",
    "hospitality_nondeductible": "4654",
    "asset_accounts": ["0480", "0500", "0670"]
  },
  "person_account_ranges": {
    "debitor": {"start": "10000", "end": "69999"},
    "kreditor": {"start": "70000", "end": "99999"}
  }
}
```

Kontonummern müssen zur Sachkontenlänge passen; Personenkonten haben eine Stelle mehr. `account_config.asset_accounts` ist eine vollständige, duplikatfreie Liste der für den Mandanten verwendbaren Anlagenkonten und enthält zwingend das GWG-Konto.

SharePoint-Nachweise für vorhandene Dateien enthalten `source_url`, `file_name`, `file_uri`, `retrieved_via`, `sha256` sowie entweder `raw_file_path` oder `content_utf8`. `retrieved_via` benennt den tatsächlich verwendeten Connector/Abrufweg; er ist nicht auf einen Produktnamen festgelegt. Das Mandantenprofil ist immer eine vorhandene Pflichtdatei. Bei Bilanz darf ein noch nicht vorhandenes Abgrenzungsregister stattdessen durch `status: "not_found"`, exakte `source_url`, exakten `file_name`, `retrieved_via`, ISO-Zeitpunkt `checked_at`, `not_found_code: "itemNotFound"`, `site_verified: true`, `library_verified: true` und `direct_lookup_attempts: 2` nachgewiesen werden. Ein technischer Abruffehler ist nicht mit `not_found` gleichzusetzen.

`datev_live_evidence` enthält Kerndaten, geprüfte Stammdaten/Vorbuchungen, `validated_accounts`, `validated_bu_keys` (darf leer sein, wenn kein BU verwendet wird), höchste Debitoren-/Kreditorennummer innerhalb der konfigurierten Bereiche, Abrufzeitpunkt und `used_person_accounts`.

`used_person_accounts` ist eine Liste aller im Lauf tatsächlich verwendeten bereits vorhandenen Personenkonten:

```json
[
  {
    "account": "70015",
    "account_type": "kreditor",
    "name": "Musterlieferant GmbH"
  }
]
```

Für neu in `master_records` angelegte Konten ist kein zusätzlicher Eintrag nötig. Für jedes verwendete bestehende Personenkonto ist der live aus DATEV gelesene Name Pflicht. Technisch oder inhaltlich als Sammel-/CPD-Konto erkennbare Namen sind unzulässig. Gesperrt sind insbesondere Namen, die mit `Diverse`, `Div.` oder `CPD` beginnen, sowie `Sammeldebitor`, `Sammelkreditor` und `Sammelkonto`.

## `input_inventory`

Nicht leere Liste aller bereitgestellten Dateien mit `source_path`, `size_bytes` und `sha256`. Sie muss 1:1 den `documents[].source_path` entsprechen.

## `documents`

Pflichtfelder:

`transaction_id`, `source_path`, `document_type`, `partner`, `recognized_date`, `total_amount`, `currency`, `period`, `processing_status`, `traffic_light`, `derivation`, `reason`, `business_purpose_status`, `bookings`.

Zulässige Status:

- `Buchungszeile erzeugt`
- `sichere Dublette – nicht erneut gebucht`
- `nicht buchungsrelevant`

Ampel `Grün`, `Gelb` oder `Rot` nur bei `Buchungszeile erzeugt`; sonst `null`.

Jeder Nicht-Avis-Beleg benötigt:

```json
"prior_booking_check": {
  "checked": true,
  "result": "kein_treffer",
  "references": []
}
```

Zulässige Ergebnisse: `kein_treffer`, `moegliche_dublette`, `sichere_dublette`.

Jeder gebuchte Beleg benötigt `input_tax_treatment`: `volle_vorsteuer`, `keine_vorsteuer`, `anteilige_vorsteuer` oder `sonderfall`. Bei anteiliger Vorsteuer zusätzlich `input_tax_rate`.

OCR-Auswertung optional als:

```json
"extraction": {
  "mode": "text_layer",
  "quality": "hoch",
  "uncertain_fields": []
}
```

Bei Zahlungsavis: `payment_advice: true`, Status `nicht buchungsrelevant`, `traffic_light: null`, leere `bookings`. Der Generator nimmt es dennoch in ein separates DUO-Belegtransfer-ZIP auf.

Bewirtung:

```json
"hospitality": {
  "detected": true,
  "status": "vollstaendig",
  "machine_receipt_complete": true,
  "hospitality_record_complete": true,
  "participants_present": true,
  "business_occasion_present": true
}
```

`status`: `vollstaendig`, `klaerung`, `privat`.

Eine Buchungszeile enthält `amount`, `debit_credit`, `account`, `account_name`, `contra_account`, `contra_account_name`, `bu_key`, `document_field_1`, `booking_text`. `bu_key` intern leer oder dreistellig; Export vierstellig mit führender Null. Belegfeld 1 ist immer gefüllt. Sobald Konto oder Gegenkonto in `account_config.asset_accounts` enthalten ist, muss das Dokument `asset_booking: true` und Ampel `Rot` tragen; der Generator exportiert das DATEV-Belegdatum leer.

## Stammdaten

`master_records[]`: `action` (`Neuanlage`/`Änderung`), `account`, `account_type` (`kreditor`/`debitor`), `name`, `full_current_record_available`, `banks`. Kreditor zusätzlich, soweit vorhanden, `vat_id`; maximal zehn Bankverbindungen. Änderungen nur als vollständiger aktueller Datensatz.

Der Name eines Stammdatensatzes darf keine Sammel-/CPD-Bezeichnung sein. Wird für einen Geschäftspartner kein zulässiges bestehendes Einzelkonto gefunden, muss `master_records[]` eine Neuanlage mit der nächsten fortlaufenden Nummer enthalten.

## Klärungen und Vorschläge

`clarification_cases[]`: `case_id`, `transaction_ids`, `topic`, `facts`, `provisional_treatment`, `recommendation`, `decision_needed`, `traffic_light`, `target`, `proposed_change`, `employee_result`.

`profile_suggestions[]` enthält nur dauerhaft wiederverwendbare mandantenspezifische Regeln. Allgemeine Skill-Änderungen gehören nicht in den Buchhaltungslauf.

## Abgrenzungen

`accrual_register`, `accrual_candidates` und `accrual_releases` folgen der bestehenden Registerlogik. `threshold_amount` muss über 800 EUR liegen. Bei neuen Abgrenzungen muss die Ursprungsrechnung gebucht und die erste Auflösung erzeugt sein. War das Register im Preflight nachweislich nicht vorhanden, fordert der Registervorschlag seine Neuanlage nur bei mindestens einer klaren neuen Abgrenzung; ohne erkannte Abgrenzung bleibt die Neuanlage entbehrlich.
