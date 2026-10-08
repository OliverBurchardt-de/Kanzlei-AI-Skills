# Eingabeschema für `build_package.py` (v1.4)

Der Agent erstellt eine UTF-8-JSON-Datei. Technische GUIDs, Paketnamen und Dateinamen erzeugt ausschließlich der Generator. Neue Läufe verwenden das normalisierte Modell `source_files` → `transaction_sources` → `transactions`. Das v1.0-Modell `input_inventory`/`documents` bleibt ausschließlich zur Rückwärtskompatibilität lesbar.

Bei Parallelverarbeitung ist `merged_draft.json` nur ein Konsolidierungsentwurf. Solange `_parallel_review.global_reconciliation_required` nicht ausdrücklich `false` ist, weist `build_package.py` die Datei ab. `person_account_proposals` müssen vor dem Paketbau global abgeglichen und gegebenenfalls in vollständige `master_records` überführt werden.

## `run`

Pflichtfelder:

- `beraternummer`, `mandantennummer`, `buchungsmonat`, `wirtschaftsjahr_beginn`
- `sachkontenlaenge`, `sachkontenrahmen`, `waehrung`, `accounting_method`
- `datev_connection_verified: true`
- bei vorhandenem Profil `mandantenprofil_verified: true`, beim kontrollierten Erstlauf stattdessen `provisional_profile_verified: true`
- `kostenstellenpflicht`: `true` oder `false` aus dem Mandantenprofil
- `cost_center_config`, sobald das Mandantenprofil Kostenstellen nennt oder DATEV live ein aktives Kostenrechnungssystem meldet; bei `kostenstellenpflicht: true` zwingend (sonst Preflight-Abbruch „unkonfigurierte Pflichtkostenstelle“)
- optional `batch_config` für im Profil freigeschaltete getrennte Buchungsvorläufe
- `mandantenprofil_evidence`, bei Bilanz `abgrenzungsregister_evidence`, `datev_live_evidence`
- `vat_config`, `account_config`, `person_account_ranges`
- optional `requested_entities`: alle vom Nutzer ausdrücklich genannten Personen oder Geschäftspartner

Kontonummern müssen zur Sachkontenlänge passen; Personenkonten haben eine Stelle mehr. `account_config.asset_accounts` ist vollständig, duplikatfrei und enthält das GWG-Konto.

`datev_live_evidence` enthält Kerndaten, geprüfte Stammdaten/Vorbuchungen, `validated_accounts`, `validated_bu_keys`, höchste Debitoren-/Kreditorennummer, Abrufzeitpunkt, `used_person_accounts` sowie `connector: "Riecken"` und je Prüfung das verwendete Werkzeug (`retrieved_via`). Sammel-/CPD-Konten sind unzulässig. Bei vorhandener `cost_center_config` zusätzlich `cost_system_active: true` und `validated_cost_centers` (Liste der live in DATEV nachgewiesenen KOST1-Nummern, siehe Abschnitt DATEV-Anbindung).

## DATEV-Anbindung (Riecken-Connector)

Die Anbindung an DATEV erfolgt ausschließlich über den Riecken-DATEV-Connector (MCP-Server `Riecken`, Werkzeuge mit Präfix `datev_`). Der Connector wird nur lesend verwendet; die Übergabe an DATEV bleibt das EXTF-Importpaket mit Belegtransfer-ZIPs. Die schreibenden Funktionen `datev_add_posting`, `datev_prepare_posting_batch`, `datev_prepare_business_partner`, `datev_prepare_document_filing` und `datev_execute_change_plan` werden in diesem Skill nicht aufgerufen.

| Prüfung | Riecken-Werkzeug | Nachweisfeld |
|---|---|---|
| Erreichbarkeit | `datev_health_check` (`master-data` und `accounting`) | `datev_connection_verified: true`, `retrieved_via.health` |
| Mandant und Kerndaten (Berater-/Mandantennummer, Wirtschaftsjahr, Kontenrahmen, Sachkontenlänge) | `datev_search_clients` (Mandantennummer), `datev_get_client_dossier`; Wirtschaftsjahr zusätzlich über `datev_suggest_posting` mit Belegdatum | `beraternummer`, `mandantennummer`, `wirtschaftsjahr_beginn`, `sachkontenrahmen`, `sachkontenlaenge`, `retrieved_via.core` |
| Personenkonten, Stammdaten, höchste Nummer je Bereich | `datev_search_business_partners` (`role` debitor/creditor), `datev_suggest_posting` (nächste freie Kontonummer) | `used_person_accounts`, `highest_creditor_account`, `highest_debtor_account`, `master_data_checked`, `master_data_records_found`, `retrieved_via.master_data` |
| Vorbuchungen und DATEV-Dublettenprüfung | `datev_get_account_postings` (Personenkonto und Aufwands-/Erlöskonto, Belegzeitraum), `datev_get_accounting_statistics` | `prior_bookings_checked`, `prior_booking_records_found`, `duplicate_checks.datev_live`, `retrieved_via.prior_bookings` |
| Sachkonten | `datev_get_account_balances` (`account_number` oder Bereich), `datev_suggest_posting` (Kontenplan-Kandidaten) | `validated_accounts`, `retrieved_via.accounts` |
| BU-Schlüssel | `datev_suggest_posting` (Steuerschlüssel zum Konto) | `validated_bu_keys`, `retrieved_via.bu_keys` |
| Kostenstellen | KOST1/KOST2 aus `datev_get_account_postings` (Vorbuchungen) und `datev_get_asset_inventory`; der Connector bietet keinen eigenen Kostenstellenkatalog | `cost_system_active`, `validated_cost_centers`, `retrieved_via.cost_centers` |

Beispiel:

```json
"datev_live_evidence": {
  "source": "DATEV live",
  "connector": "Riecken",
  "retrieved_at": "2026-10-07T10:00:00+02:00",
  "retrieved_via": {
    "health": "datev_health_check",
    "core": "datev_get_client_dossier",
    "master_data": "datev_search_business_partners",
    "prior_bookings": "datev_get_account_postings",
    "accounts": "datev_get_account_balances",
    "bu_keys": "datev_suggest_posting",
    "cost_centers": "datev_get_account_postings"
  }
}
```

Regeln:

- Jeder Wert in `datev_live_evidence` stammt aus einem Riecken-Abruf dieses Laufs. Werte aus Erinnerung, früheren Läufen oder anderen DATEV-Zugängen sind unzulässig. `connector: "Riecken"` und `retrieved_via` mit einem `datev_*`-Werkzeug für `health`, `core`, `master_data`, `prior_bookings`, `accounts` und `bu_keys` sind Pflicht; der Generator bricht den Paketbau sonst ab, der Validator prüft dasselbe im Laufmanifest.
- Liefert der Connector einen Kernwert nicht, ist das ein technischer Preflight-Blocker; das Mandantenprofil ersetzt den Live-Abruf nicht.
- Eine im Profil genannte Kostenstelle, die über den Connector in keiner Vorbuchung und keinem Anlagegut nachweisbar ist, gilt nicht als live validiert. Der Vorgang wird Rot mit offenem `kost1` und Klärungsfall „Kostenstelle in DATEV anlegen/bestätigen“ (Abschnitt Kostenstellen, Regel 6).
- `datev_get_account_balances` nur mit `account_number` oder einem Kontenbereich aufrufen; `confirmed_full_list` bleibt in diesem Skill ungenutzt.

## Kostenstellen

```json
"kostenstellenpflicht": true,
"cost_center_config": {
  "kost_system": 1,
  "kost1_required": true,
  "kost2_required": false,
  "kost1_allowed": {
    "1000": "Praxis",
    "2000": "Labor",
    "9999": "Sammelkostenstelle/-träger"
  },
  "kost2_allowed": {},
  "rules_source": "Mandantenprofil 13481, Abschnitt Kostenstellenregeln"
}
```

Prüfregeln des Generators:

1. Keine `cost_center_config`: `kost1`/`kost2` müssen leer sein.
2. `cost_center_config` vorhanden, `kostenstellenpflicht: false`: ableitbare Kostenstelle setzen; nicht ableitbar bleibt leer ohne Ampelwirkung.
3. `kostenstellenpflicht: true` ohne vollständige `cost_center_config`: Abbruch im Preflight („unkonfigurierte Pflichtkostenstelle“); `kost1_required` muss dann `true` sein.
4. `kostenstellenpflicht: true`, Grün: `kost1` gefüllt und in `kost1_allowed`; `kost2` entsprechend bei `kost2_required: true`.
5. `kostenstellenpflicht: true`, Rot: `kost1` darf leer bleiben, wenn es in `open_fields` begründet ist. Ein bekannter Wert wird nie gelöscht.
6. Jeder gefüllte Wert muss in `kost1_allowed`/`kost2_allowed` und in `validated_cost_centers` stehen; eine unbekannte Kostenstelle ist ein Generatorfehler, eine live fehlende Kostenstelle ist nur als Rot mit offenem `kost1` und Klärungsfall „Kostenstelle in DATEV anlegen“ zulässig.
7. Die Ableitung der Kostenstelle wird je Vorgang in `derivation` begründet.

## Getrennte Buchungsvorläufe

```json
"batch_config": {
  "separate_batches": {
    "eigenbelege": {
      "label": "Eigenbelege Labor",
      "required_kost1": "2000",
      "required_contra_account": "800010"
    }
  }
}
```

Je Vorgang optional `batch_type` mit `standard` (Default) oder einem konfigurierten Schlüssel. Ein `batch_type` ohne Konfiguration ist ein Generatorfehler. Stapeltypen bestehen aus Kleinbuchstaben und Ziffern; der Dateisuffix ist der Schlüssel mit großem Anfangsbuchstaben (`eigenbelege` → `_Eigenbelege`). `label` (höchstens 30 Zeichen) wird Stapelbezeichnung in Header-Feld 17.

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

`readability`: `readable`, `partially_readable`, `image_only` (Scan ohne Textebene, über das Belegbild auswertbar), `unreadable` oder `not_checked`. Gleicher SHA-256 innerhalb eines Uploads ist nur als ausdrücklich zugeordnete `duplicate_copy` zulässig.

### Abgeleitete Belegdateien (Belegdateiregel: ein Buchungsbeleg = genau eine eigene PDF-Datei)

Jeder gebuchte Vorgang besitzt genau eine `primary_invoice`-Quelle, und diese ist eine PDF-Datei, die für keinen weiteren Vorgang Primärbeleg ist. Mit `scripts/beleg_pdf.py` aufgeteilte, zusammengeführte oder umgewandelte PDFs sind eigene Einträge in `source_files` mit `derived_from`; sie liegen in einem Arbeitsordner außerhalb des Eingabeordners:

```json
{
  "source_id": "D0001",
  "source_path": "…/work/V0001.pdf",
  "size_bytes": 23456,
  "sha256": "…64 hex…",
  "readability": "image_only",
  "derived_from": {"source_ids": ["S0001"], "method": "split", "pages": "1-2", "tool": "scripts/beleg_pdf.py"}
}
```

`method` ist `split` (Sammel-PDF, Pflichtangabe `pages`), `merge` (mindestens zwei Originale desselben Belegs) oder `convert` (Bilddatei). Eine per `merge` oder `convert` erzeugte PDF ist genau einem Vorgang zugeordnet, und ihre Originale dürfen keinem anderen Vorgang zugeordnet sein: Jeder Beleg wird genau ein eigenes Dokument, niemals werden mehrere Belege zu einer Datei zusammengefasst. Das Original bleibt inventarisiert und wird je betroffenem Vorgang mit der Rolle `bundle_original` (split) beziehungsweise `converted_original` (merge/convert) zugeordnet; es wird nicht in den Belegtransfer übernommen. Ableitungen werden nicht verkettet. Der Generator weist Sammeldateien mit mehreren Buchungsbelegen, Nicht-PDF-Buchungsbelege und auf mehrere Dateien verteilte Buchungsbelege zurück.

## `transactions` und `transaction_sources`

Ein logischer Vorgang besitzt eine eigene `transaction_id`. Eine Datei kann mehrere Vorgänge belegen; ein Vorgang kann mehrere Quellen besitzen.

```json
"transaction_sources": [
  {"transaction_id": "V0001", "source_id": "S0001", "role": "primary_invoice"},
  {"transaction_id": "V0001", "source_id": "S0002", "role": "supporting_document"}
]
```

Rollen: `primary_invoice`, `supporting_document`, `payment_notice`, `cover_sheet`, `duplicate_copy`, `bundle_original`, `converted_original`. Deckblätter, Dublettenkopien und Originale abgeleiteter PDFs werden nicht zusätzlich übertragen. Jede Quelldatei wird höchstens einmal in den DATEV-Belegtransfer aufgenommen; ein Buchungsbeleg ist genau eine eigene PDF-Datei (`primary_invoice` genau einmal je gebuchtem Vorgang und je Datei). Mehrere Buchungszeilen desselben Vorgangs verweisen auf dieselbe übertragene Quelle. Begleitdokumente (`supporting_document`) werden nicht als eigener DATEV-Beleg übertragen (sie hätten keinen Buchungs-Beleglink); zum Belegbild gehörende Seiten werden per `merge` in die Beleg-PDF aufgenommen, sonst bleiben sie inventarisierte Arbeitsunterlage mit Endstatus.

Pflichtfelder je `transactions[]`:

- `transaction_id`, `document_type`, `partner`, `recognized_date`, `total_amount`, `currency`, `period`
- `processing_status`, `traffic_light`, `derivation`, `reason`, `business_purpose_status`, `bookings`
- optional `batch_type` (`standard` oder ein in `batch_config` konfigurierter Stapeltyp)
- `entity_assessment`; bei buchungsrelevanten oder als Dublette behandelten Vorgängen zusätzlich `duplicate_checks`

Zulässige Endstatus (jede Eingabedatei und jeder Vorgang erhält genau einen):

- `Buchungszeile erzeugt` (regulär verarbeitet, Grün oder konkret fachlich ungeklärt Rot)
- `sichere Dublette – nicht erneut gebucht`
- `nicht buchungsrelevant` (einschließlich Aussteuerung an einen anderen Mandanten/Rechtsträger mit `handoff_required`)
- `außerhalb Auftragszeitraum`
- `technisch nicht auswertbar` (nur nach dokumentiertem Auswertungsversuch)

Ampel `Grün` oder `Rot` nur bei `Buchungszeile erzeugt`; sonst `null`.

### Rot-Grund (`red_reason`) und Auswertungsversuche (`evaluation_attempts`)

Jeder rote Vorgang trägt einen maschinenlesbaren Rot-Grund:

```json
"red_reason": {
  "code": "konto_unklar",
  "verification_attempted": "Belegbild, Mandantenprofil, DATEV-Vorbuchungen des Kreditors und Kontenrahmen geprüft; Leistungsart nicht erkennbar.",
  "next_check": "Leistungsbeschreibung beim Mandanten anfordern."
}
```

Zulässige `code`-Werte: `fehlende_belegangabe`, `steuer_unklar`, `rechtstraeger_unklar`, `personenkonto_unklar` (nur mit `partner_check`), `datev_dublette_unklar` (nur mit möglichem DATEV-Treffer), `konto_unklar`, `anlage_gwg_spezialregel` (nur mit `asset_booking: true`), `technisch_unlesbar` (nur mit `evaluation_attempts` einschließlich Belegbildprüfung), `spezialregel_sonstige`. `reason` darf nicht allein auf fehlende OCR oder Textebene verweisen.

`personenkonto_unklar` erfordert den dokumentierten Riecken-Partnerabgleich; ein fehlender oder neuer Kreditor ist kein Rot-Grund, sondern eine Neuanlage in `master_records`:

```json
"red_reason": {
  "code": "personenkonto_unklar",
  "partner_check": {
    "tool": "datev_search_business_partners",
    "query": "Müller Bau",
    "result": "ambiguous",
    "detail": "Zwei Einzelkreditoren 70012 Müller Bau GmbH und 70058 Müller Bauservice; Beleg nennt weder Rechtsform noch USt-ID."
  },
  "verification_attempted": "Belegbild, Mandantenprofil, DATEV-Stammdaten beider Treffer und Vorbuchungen geprüft.",
  "next_check": "USt-ID oder IBAN beim Mandanten erfragen."
}
```

`result` ist `ambiguous` oder `identity_unclear` (jeweils mit `detail`) oder `error` (nur zusammen mit einem `technical_incidents`-Eintrag, der den Vorgang in `affected_transaction_ids` führt). `no_match` wird zurückgewiesen. Der Generator sperrt außerdem jede Rot-Begründung, die lediglich „Kreditor/Debitor/Lieferant fehlt, nicht angelegt oder neu“ nennt, ohne eine Identitätsunklarheit zu beschreiben.

`evaluation_attempts` dokumentiert den tatsächlichen Auswertungsversuch bei `technisch_unlesbar` und beim Status `technisch nicht auswertbar`:

```json
"processing_status": "technisch nicht auswertbar",
"traffic_light": null,
"exclusion_reason": "Datei ist eine passwortgeschützte PDF; Belegbild nicht darstellbar.",
"evaluation_attempts": [
  {"method": "textebene", "result": "keine Textebene"},
  {"method": "belegbild", "result": "Seiten nicht renderbar (verschlüsselt)"},
  {"method": "wiederholung", "result": "zweiter Leseversuch identisch fehlgeschlagen"}
]
```

`method` ist `textebene`, `ocr`, `belegbild`, `alternativer_leseweg` oder `wiederholung`; ein Eintrag mit `belegbild` ist Pflicht.

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

Ergebnisse: `no_hit`, `possible_duplicate`, `secure_duplicate`. Treffer enthalten eine Referenz. Sichere Dublette wird nicht erneut gebucht; mögliche Dublette wird Rot mit allen bekannten Angaben behandelt. `prior_booking_check` bleibt als DATEV-Kompatibilitätsfeld bestehen.

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

Eine Buchungszeile enthält `amount`, `debit_credit`, `account`, `account_name`, `contra_account`, `contra_account_name`, `bu_key`, `document_field_1`, `booking_text` sowie bei konfigurierten Kostenstellen `kost1` und optional `kost2` (Text, höchstens 36 Zeichen, DATEV-Zeichensatz). Rote Zeilen werden im Klärungsstapel `EXTF_Klaerungsposten_<JJJJ-MM>.csv` exportiert, grüne im Buchungsstapel; die Zuordnung ergibt sich allein aus `traffic_light`, ein Feld zur manuellen Stapelwahl ist ausdrücklich nicht vorgesehen. Im Klärungsstapel bleibt das DATEV-Belegdatum immer leer; `recognized_date` bleibt trotzdem Pflicht, soweit sicher erkannt. `bu_key` ist intern leer oder dreistellig, zum Beispiel `511`; eine führende Null entsteht erst beim Export. Bekannte Referenzen für Belegfeld 1 erhalten; unbekannte Referenzen bei Rot dokumentiert leer lassen. Anlagen/GWG erfordern `asset_booking: true`, Rot und ein grundsätzlich leeres Anlagenkontofeld. Je betroffener Zeile `asset_account_field: "account"` oder `"contra_account"` setzen. Der Generator weist direkte Anlagenkonten und Ersatzbuchungen zurück.

Bei Rot enthält jede Buchungszeile `open_fields` als Objekt aus exakt offenem Feld und konkreter Begründung, zum Beispiel:

```json
"account": null,
"asset_account_field": "account",
"open_fields": {"account": "Anlagenzugang zuerst in der Anlagenvorerfassung anlegen; fachlicher Vorschlag 0480 GWG."}
```

Erlaubte Feldnamen: `amount`, `debit_credit`, `currency`, `exchange_rate`, `base_amount`, `account`, `contra_account`, `bu_key`, `recognized_date`, `document_field_1`, `kost1`, `kost2`, `service_date`, `tax_period_date`. `kost1`/`kost2` sind nur bei vorhandener `cost_center_config` zulässig. `currency` und `recognized_date` stehen am Vorgang, die übrigen Werte an der Buchungszeile. Ein offenes Feld ist `null` oder leer; ein bekannt ausgefüllter Wert darf nicht zugleich als offen deklariert werden. Grün hat keine offenen Felder. Ein fachlich korrekt leeres BU-Feld benötigt keine Unsicherheitsbegründung. Rote Fälle mit vollständig bekannten Feldern benötigen weiterhin einen konkreten Klärungsfall, aber keine künstliche Leerstelle.

Jeder rote Vorgang benötigt `requires_clarification: true` und genau einen Klärungsfall mit `booking_risk`. Die Prüfungsdatei zeigt die konkreten offenen Felder, das Risiko und die Mitarbeiterentscheidung. Buchungstexte bleiben sachliche Beleg-/Leistungsbeschreibungen.

Bei Zahlungsavis: `payment_advice: true`, Status `nicht buchungsrelevant`, keine Ampel, keine Buchungen. Es entsteht ein separates Avis-Belegtransfer-ZIP.

## Klärungsquote und Zweitprüfung (`clarification_review`)

Der Generator berechnet N, R und Q aus den Vorgängen (`scripts/clarification_rate.py`). Der Agent dokumentiert die Zweitprüfung und die Ursachenprüfung:

```json
"clarification_review": {
  "checked_at": "2026-10-08T10:00:00+02:00",
  "cause_analysis": {"konto_unklar": "Fünf Lieferanten ohne Leistungsbeschreibung; keine systematische Fehleinstufung."},
  "second_review": {
    "performed": true,
    "performed_at": "2026-10-08T11:30:00+02:00",
    "basis": ["belegbild", "mandantenprofil", "datev_bestand", "buchungsregeln"],
    "reviewed_transaction_ids": ["V0003", "V0007"],
    "corrections": [
      {"transaction_id": "V0003", "from": "Rot", "to": "Grün", "reason": "Konto 4930 aus DATEV-Vorbuchung des Kreditors eindeutig; Belegbild bestätigt Leistungsart."}
    ],
    "before": {"N": 100, "R": 25}
  }
}
```

Bei `Q > 20 %` (vor Zweitprüfung) muss `performed: true` sein und `reviewed_transaction_ids` alle roten Vorgänge vor der Zweitprüfung umfassen (verbleibende rote plus korrigierte). `corrections[].to` ist `Grün`, `Rot` oder `ausgeschlossen` (nach Zweitprüfung als sichere Dublette oder nicht buchungsrelevant erkannt); jede Korrektur braucht eine konkrete Begründung, und der Vorgang muss im Lauf-JSON den korrigierten Zustand tragen. `before` ist optional und muss mit den Korrekturen konsistent sein. Bei `10 % < Q ≤ 20 %` ist `cause_analysis` je vorkommendem Rot-Code Pflicht; eine Kategorie mit mindestens der Hälfte von mindestens fünf Rot-Fällen erfordert sie immer.

## Technische Einzelfehler (`technical_incidents`)

Ein Zugriffsausfall auf ein Register, einen Geschäftspartner oder einen Beleg blockiert nur die betroffene Teilentscheidung:

```json
"technical_incidents": [
  {
    "incident_id": "T001",
    "system": "DATEV",
    "scope": "datev_search_business_partners für Lieferant Muster GmbH",
    "error": "Timeout nach 30 s",
    "retries": 2,
    "alternative_path": "datev_get_account_postings auf Kreditorenbereich versucht; ebenfalls Timeout",
    "affected_transaction_ids": ["V0042"],
    "deferred_decision": "Personenkonto für Muster GmbH",
    "next_step": "Partnerabfrage nach Wiederherstellung des Connectors wiederholen",
    "resolved": false
  }
]
```

`system` ist `DATEV`, `SharePoint`, `OCR`, `Belegbild`, `Register` oder `sonstige`. Von einem ungelösten Fehler betroffene Vorgänge dürfen nicht Grün sein (begründet Rot, zum Beispiel `personenkonto_unklar`, oder zurückgestellt). Ungelöste Einträge führen zu `run_completion.status = "nicht vollständig abgeschlossen"` mit dem offenen Punkt im Laufmanifest.

## Abgrenzungsregister: Abrufergebnis (nur Bilanz)

Das Register ist keine Pflichtquelle; nur der einmalige Abruf am exakten Ziel wird dokumentiert. Leer oder nicht vorhanden ist normal:

```json
"abgrenzungsregister_evidence": {
  "status": "not_found",
  "source_url": "<accrual_url aus sharepoint_target.py>",
  "file_name": "12861.md",
  "retrieved_via": "microsoft_sharepoint.fetch",
  "checked_at": "2026-10-08T09:00:00+02:00"
}
```

`status` ist `found` (dann wie beim Mandantenprofil mit `file_uri`, `sha256` und Inhalt; der Inhalt darf leer sein), `empty` oder `not_found` (nur die vier Felder oben) oder `access_error` (unten). Bei EÜR entfällt `abgrenzungsregister_evidence`; `accrual_register`, `accrual_candidates` und `accrual_releases` müssen bei EÜR leer sein.

## Abgrenzungsregister: Abruffehler

```json
"abgrenzungsregister_evidence": {
  "status": "access_error",
  "source_url": "<accrual_url aus sharepoint_target.py>",
  "file_name": "12861.md",
  "retrieved_via": "microsoft_sharepoint.fetch",
  "checked_at": "2026-10-08T09:00:00+02:00",
  "http_status": 403,
  "error_code": "accessDenied",
  "direct_lookup_attempts": 2
}
```

Ein `access_error` ist kein Nullstand: keine `carried_forward`-Einträge erfinden, keine Auflösungen bestehender Registereinträge buchen; neue Abgrenzungen dieses Laufs regulär verarbeiten. 404/`itemNotFound` ist kein `access_error`, sondern `status: "not_found"`; umgekehrt darf ein 401/403 nicht als `not_found` deklariert werden.

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

`clarification_cases[]`: `case_id`, `transaction_ids`, `topic`, `facts`, `booking_risk`, `provisional_treatment`, `recommendation`, `decision_needed`, `traffic_light`, `target`, `proposed_change`, `employee_result`.

`profile_suggestions[]` enthält ausschließlich dauerhaft wiederverwendbare mandantenspezifische Regeln. Allgemeine Ausschluss-, DATEV- und Dokumentregeln bleiben global.

`accrual_register`, `accrual_candidates` und `accrual_releases` folgen der Registerlogik. `threshold_amount` liegt über 800 EUR. Bei neuen Abgrenzungen bleiben Ursprungsrechnung und erste Auflösung vollständig nachgewiesen.

## DATEV-Testimport und Grenzen der internen Prüfung

Vor einem produktiven Import das Paket in einem dafür freigegebenen DATEV-Testbestand testen. Prüfen, ob unvollständige rote Zeilen als bearbeitungsbedürftig übernommen werden oder ob DATEV Zeilen beziehungsweise den gesamten Stapel zurückweist. Den tatsächlich getesteten Dateistand über SHA-256 nachweisen; Ergebnis, DATEV-Version, Testbestand und genaue Meldungen dokumentieren. Bei fehlendem Zugang Status `pending` und `DATEV-Testimport ausstehend` ausweisen; keinen Erfolg behaupten. Die Paketübergabe mit internem `valid=true` bleibt zulässig, ohne damit DATEV-Importfähigkeit zu bestätigen.

Optionales Lauf-JSON-Feld `datev_test_import`: `status` ist `pending`, `confirmed` oder `rejected`. Bei ausgeführtem Test sind `tested_at`, `datev_version`, `test_client`, `evidence_reference`, `result_detail`, `tested_files` und `carry_over_result` Pflicht. `tested_files` ordnet jeder tatsächlich erzeugten EXTF-Datei, also auch jedem Klärungsstapel und jeder Teilungsdatei, den SHA-256 des getesteten Inhalts zu. `carry_over_result` hält je gefährdetem Feld (`account`, `contra_account`, `bu_key`, `recognized_date`, `document_field_1`) das beobachtete Verhalten fest: `carried`, `not_carried` oder `not_tested`. `confirmed` bedeutet: Alle Zeilen wurden übernommen und rote Zeilen sind bearbeitungsbedürftig; `rejected` protokolliert insbesondere eine Zurückweisung des gesamten Stapels. Ein Nachweis für andere Dateiinhalte bestätigt das aktuelle Paket nicht. Ein ergebnisloser oder nicht ausgeführter Test bleibt `pending`.

Weist DATEV den gesamten Stapel zurück, Fehler und betroffene Felder offen melden; keine Ersatzbuchung, kein Entfernen roter Fälle und keine Teilung über die Sortierregel hinaus. Einen lokalen Strukturtest niemals als DATEV-Testimport ausgeben.

Quelle: [DATEV-Schnittstellenvorgaben und Testimport](https://developer.datev.de/de/product-detail/accounting-extf-files/2.0/documentation/interface-requirements-file).

Einen tatsächlichen Testimportnachweis nach dem Test mit `python scripts/validate_package.py --package <Paketordner> --datev-test-import <Nachweis.json>` prüfen. Bei passendem Dateistand wird er unter `03_Technische_Protokolle/DATEV_Testimport.json` gespeichert und bei Folgeprüfungen berücksichtigt.
