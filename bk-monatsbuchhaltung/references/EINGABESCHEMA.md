# Eingabeschema für `build_package.py` (v1.2)

Der Agent erstellt eine UTF-8-JSON-Datei. Technische GUIDs, Paketnamen und Dateinamen erzeugt ausschließlich der Generator. Neue Läufe verwenden das normalisierte Modell `source_files` → `transaction_sources` → `transactions`. Das v1.0-Modell `input_inventory`/`documents` bleibt ausschließlich zur Rückwärtskompatibilität lesbar.

Bei Parallelverarbeitung ist `merged_draft.json` nur ein Konsolidierungsentwurf. Solange `_parallel_review.global_reconciliation_required` nicht ausdrücklich `false` ist, weist `build_package.py` die Datei ab. `person_account_proposals` müssen vor dem Paketbau global abgeglichen und gegebenenfalls in vollständige `master_records` überführt werden.

## `run`

Pflichtfelder:

- `beraternummer`, `mandantennummer`, `buchungsmonat`, `wirtschaftsjahr_beginn`
- `sachkontenlaenge`, `sachkontenrahmen`, `waehrung`, `accounting_method`
- `datev_connection_verified: true`
- bei vorhandenem Profil `mandantenprofil_verified: true`, beim kontrollierten Erstlauf stattdessen `provisional_profile_verified: true`
- `kostenstellenpflicht: false`
- `mandantenprofil_evidence`, bei Bilanz `abgrenzungsregister_evidence`, `datev_live_evidence`
- `vat_config`, `account_config`, `person_account_ranges`
- optional `requested_entities`: alle vom Nutzer ausdrücklich genannten Personen oder Geschäftspartner

Kontonummern müssen zur Sachkontenlänge passen; Personenkonten haben eine Stelle mehr. `account_config.asset_accounts` ist vollständig, duplikatfrei und enthält das GWG-Konto.

`datev_live_evidence` enthält Kerndaten, geprüfte Stammdaten/Vorbuchungen, `validated_accounts`, `validated_bu_keys`, höchste Debitoren-/Kreditorennummer, Abrufzeitpunkt und `used_person_accounts`. Sammel-/CPD-Konten sind unzulässig.

## Mandantenprofil

Vorhandenes Profil:

```json
"mandantenprofil": {
  "status": "existing",
  "source_status": "found",
  "approval_status": "approved",
  "evidence": []
}
```

Kontrollierter Erstlauf nach zweimaligem direktem `itemNotFound`:

```json
"mandantenprofil": {
  "status": "provisional_first_run",
  "source_status": "confirmed_not_found",
  "approval_status": "pending",
  "evidence": []
},
"provisional_profile": {
  "content_markdown": "# Mandantenprofil …",
  "sources": ["DATEV live …", "Nutzerangabe …", "Belegmerkmal …"],
  "provisional_rules": [],
  "sharepoint_write_approved": false
}
```

Der Nichtvorhanden-Nachweis enthält die exakte URL und den exakten Dateinamen, `retrieved_via`, `checked_at`, `not_found_code: "itemNotFound"`, `site_verified: true`, `library_verified: true` und `direct_lookup_attempts: 2`. Ein Connector-/Lesefehler ist niemals `confirmed_not_found` und blockiert weiterhin. Das vorläufige Profil wird vollständig im Paket ausgegeben, aber erst nach ausdrücklicher Freigabe nach SharePoint geschrieben.

## `scope`

```json
"scope": {
  "target_periods": ["2026-06", "2026-07"],
  "include_prior_periods": false,
  "include_future_periods": false,
  "job_mode": "belegbuchhaltung"
}
```

Nur `job_mode: "belegbuchhaltung"` ist zulässig. Bank, Kasse, Lohn, Zahlungsverkehr, OPOS-Ausgleich, Abstimmung und Monatsabschluss bleiben ausgeschlossen. Belege außerhalb der Zielperioden erhalten `processing_status: "außerhalb Auftragszeitraum"`, keine Ampel und keine Buchungszeile. Sie bleiben vollständig inventarisiert.

## `source_files`

Jede physische Datei genau einmal:

```json
"source_files": [
  {
    "source_id": "S0001",
    "source_path": "…/rechnung.pdf",
    "size_bytes": 12345,
    "sha256": "…64 hex…",
    "readability": "readable"
  }
]
```

`readability`: `readable`, `partially_readable`, `unreadable` oder `not_checked`. Gleicher SHA-256 innerhalb eines Uploads ist nur als ausdrücklich zugeordnete `duplicate_copy` zulässig.

## `transactions` und `transaction_sources`

Ein logischer Vorgang besitzt eine eigene `transaction_id`. Eine Datei kann mehrere Vorgänge belegen; ein Vorgang kann mehrere Quellen besitzen.

```json
"transaction_sources": [
  {"transaction_id": "V0001", "source_id": "S0001", "role": "primary_invoice"},
  {"transaction_id": "V0001", "source_id": "S0002", "role": "supporting_document"}
]
```

Rollen: `primary_invoice`, `supporting_document`, `payment_notice`, `cover_sheet`, `duplicate_copy`. Deckblätter und Dublettenkopien werden nicht zusätzlich übertragen. Jede Quelldatei wird höchstens einmal in den DATEV-Belegtransfer aufgenommen; mehrere Buchungen dürfen auf dieselbe übertragene Quelle verweisen.

Pflichtfelder je `transactions[]`:

- `transaction_id`, `document_type`, `partner`, `recognized_date`, `total_amount`, `currency`, `period`
- `processing_status`, `traffic_light`, `derivation`, `reason`, `business_purpose_status`, `bookings`
- `entity_assessment`; bei buchungsrelevanten oder als Dublette behandelten Vorgängen zusätzlich `duplicate_checks`

Zulässige Status:

- `Buchungszeile erzeugt`
- `sichere Dublette – nicht erneut gebucht`
- `nicht buchungsrelevant`
- `außerhalb Auftragszeitraum`

Ampel `Grün`, `Gelb` oder `Rot` nur bei `Buchungszeile erzeugt`; sonst `null`.

## Rechtsträger, Dokumentart und Ausschluss

Vor Kontierung und Umsatzsteuer:

```json
"entity_assessment": {
  "legal_entity": "Muster GmbH",
  "addressee": "Muster GmbH",
  "relevance": "in_scope|foreign_entity|personal|unclear"
}
```

Bei jedem nicht gebuchten Vorgang ist `exclusion_reason` Pflicht. Wenn Folgearbeit erforderlich ist, zusätzlich `handoff_required: true` und ein passender Eintrag in `handoffs`.

Globale Ausschlüsse: Lohn-/Sozialversicherungsunterlagen, private Bescheide oder Inkasso gegen Privatpersonen, Mahnungen ohne Original oder sicheren Abgleich, Anhörungsbögen ohne endgültigen Anspruch, Deckblätter zu einzeln gebuchten Originalen und Kontoauszüge. Diese Regeln gehören nicht in Mandantenprofile.

## Dreistufige Dublettenprüfung

```json
"duplicate_checks": {
  "file_hash_current_upload": {"checked": true, "result": "no_hit", "reference": ""},
  "logical_document_current_upload": {"checked": true, "result": "no_hit", "reference": ""},
  "datev_live": {"checked": true, "result": "no_hit", "reference": ""}
}
```

Ergebnisse: `no_hit`, `possible_duplicate`, `secure_duplicate`. Treffer enthalten eine Referenz. Sichere Dublette wird nicht erneut gebucht; mögliche Dublette wird Rot mit leerem DATEV-Belegdatum behandelt. `prior_booking_check` bleibt als DATEV-Kompatibilitätsfeld bestehen.

## Belegampel und Zahlungsabstimmung

Rot ist nur bei einer Unsicherheit des Belegs zulässig: Kontierung, Betrag, Geschäftspartner, Periode, Umsatzsteuer, betrieblicher Anlass, Anlagenbehandlung oder Dublette. Fehlende Konto-/Kreditkartenabrechnung, Zahlungsnachweis, Kartenumsatz oder Kursdifferenz verändern die Belegampel nicht.

```json
"payment_reconciliation": {
  "statement_type": "credit_card",
  "status": "present|missing|not_expected|not_checked",
  "periods": ["2026-06", "2026-07"],
  "affects_document_traffic_light": false,
  "handoff_required": true,
  "note": "…"
}
```

Ein Lauf wird abgelehnt, wenn Rot ausschließlich mit fehlender Zahlungs- oder Kartenabstimmung begründet wird.

## Buchungszeilen

Eine Buchungszeile enthält `amount`, `debit_credit`, `account`, `account_name`, `contra_account`, `contra_account_name`, `bu_key`, `document_field_1`, `booking_text`. `bu_key` ist intern leer oder dreistellig, zum Beispiel `511`; eine führende Null entsteht erst beim Export. Belegfeld 1 ist immer gefüllt. Anlagenkonten erfordern `asset_booking: true`, Ampel Rot und leeres DATEV-Belegdatum.

Bei Zahlungsavis: `payment_advice: true`, Status `nicht buchungsrelevant`, keine Ampel, keine Buchungen. Es entsteht ein separates Avis-Belegtransfer-ZIP.

## Tätigkeitsnachweis

```json
"activity_report": {
  "datev_import_status": "Importpaket erstellt – noch nicht in DATEV importiert",
  "sources_used": ["hochgeladene Belege", "DATEV live", "Mandantenprofil"],
  "named_entities": [
    {
      "name": "You Nie",
      "variants": ["You Nie", "You Lie"],
      "findings": 3,
      "final_status": "2 Lohnunterlagen ausgeschlossen; 1 Rechnung gebucht"
    }
  ]
}
```

Jeder Name aus `run.requested_entities` benötigt Fundstellenzahl, Varianten und Endstatus. `in DATEV importiert` ist nur mit `import_evidence` zulässig. Der Generator selbst meldet stets getrennt den Fachstatus `fachlicher Prüfprotokoll-Rücklauf ausstehend`.

## `handoffs`

```json
"handoffs": [
  {
    "source_ids": ["S0007"],
    "transaction_ids": ["V0006"],
    "period": "2026-07",
    "target_process": "Bankbuchhaltung / MT940",
    "reason": "Kontoauszug ist kein Belegbuchungsvorgang"
  }
]
```

Typische Ziele: Bank-/Kreditkartenprozess, Lohnbuchhaltung, DUO-Avispaket, Rückgabe/Korrektur Rechtsträger oder ein separater Kassenprozess. Eine Übergabe an einen Kassenprozess erzeugt ausdrücklich keine Kassenbuchung in diesem Skill.

## Stammdaten, Klärungen und Abgrenzungen

`master_records[]`: `action`, `account`, `account_type`, `name`, `full_current_record_available`, `banks`; bei Kreditoren soweit vorhanden `vat_id`. Keine Sammel-/CPD-Konten.

`clarification_cases[]`: `case_id`, `transaction_ids`, `topic`, `facts`, `provisional_treatment`, `recommendation`, `decision_needed`, `traffic_light`, `target`, `proposed_change`, `employee_result`.

`profile_suggestions[]` enthält ausschließlich dauerhaft wiederverwendbare mandantenspezifische Regeln. Allgemeine Ausschluss-, DATEV- und Dokumentregeln bleiben global.

`accrual_register`, `accrual_candidates` und `accrual_releases` folgen der Registerlogik. `threshold_amount` liegt über 800 EUR. Bei neuen Abgrenzungen bleiben Ursprungsrechnung und erste Auflösung vollständig nachgewiesen.
