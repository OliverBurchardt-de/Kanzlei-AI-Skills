# Kanonischer Vorbereitungsdatensatz

## Zweck

`Vorbereitungsdaten.json` trennt Fachlogik von der noch ausstehenden Excel-Vorlage. Der Datensatz ist die belegte Quelle für das spätere Vorbefüllen des Review-Sheets und für die Mitarbeiterzusammenfassung. Er enthält eine Startklarheits-Checkliste, aber kein Gesamturteil zum Jahresabschluss.

## Pflichtstruktur

Das folgende Beispiel zeigt die Struktur gekürzt. Ein gültiger Lauf enthält anschließend sämtliche unten genannten Pflicht-Themen und die vollständige Bilanzkontenabdeckung.

```json
{
  "schema_version": "0.3.0",
  "execution_status": "preparation_only",
  "overall_status": "ENTWURF",
  "mandant": {
    "number": "12345",
    "datev_client_id": "GUID",
    "name": "Bezeichnung"
  },
  "target_fiscal_year": {
    "id": "20260101",
    "start": "2026-01-01",
    "end": "2026-12-31",
    "account_length": 4,
    "accounting_method": "bilanz"
  },
  "prior_fiscal_year": {
    "id": "20250101",
    "start": "2025-01-01",
    "end": "2025-12-31"
  },
  "sources": [],
  "account_inventory": {
    "debitors": [],
    "creditors": [],
    "balance_sheet_accounts": [
      {
        "account": "1740",
        "caption": "Verbindlichkeiten aus Lohn und Gehalt",
        "purpose": "payroll_net_liability",
        "balance": "0.00",
        "currency": "EUR",
        "checklist_item_id": "CHK-LOHN-1740"
      }
    ]
  },
  "open_items": {
    "receivable": [],
    "payable": [],
    "clearing_candidates": []
  },
  "preparation_checklist": [
    {
      "id": "CHK-LOHN-1740",
      "module": "startklarheit",
      "topic_id": "lohnkonten",
      "status": "AUF_NULL",
      "description": "Konto 1740 steht am Stichtag auf null.",
      "account_numbers": ["1740"],
      "account_purpose": "Verbindlichkeiten aus Lohn und Gehalt",
      "balance": "0.00",
      "currency": "EUR",
      "zero_expectation": "NULL_ODER_NACHWEIS",
      "source_refs": ["DATEV-SUSA"],
      "evidence_refs": [],
      "work_lane": "ERLEDIGT",
      "blocks_start": false,
      "next_action": "Keine.",
      "reviewer_comment": ""
    }
  ],
  "findings": [],
  "posting_proposals": [],
  "prior_year_closing_entries": [],
  "handoff_to_annual_close": [],
  "employee_tasks": [],
  "gates": []
}
```

`prior_fiscal_year` darf `null` sein, wenn DATEV kein Vorjahr bereitstellt. Dann muss ein Gate mit `NICHT_PRUEFBAR` und konkretem Grund vorhanden sein.

`preparation_checklist` muss mindestens die `topic_id`-Werte `quellen_datenstand`, `bilanzkonten_abdeckung`, `opos_debitoren`, `opos_kreditoren`, `bank_kasse`, `geldtransit`, `durchlaufende_posten`, `lohnkonten`, `steuerkonten`, `abgrenzungen` und `vorjahr_rollforward` enthalten. Ein nicht einschlägiges Thema bleibt mit `NICHT_ANWENDBAR` sichtbar; es wird nicht weggelassen.

`handoff_to_annual_close` enthält Hinweise, deren Unterlagen und Salden vorbereitet sind, deren fachliche Bilanzierungs- oder Bewertungsentscheidung aber erst im eigentlichen Abschluss erfolgt.

## Gemeinsame Felder

Jeder Befund, Vorschlag, Kandidat, Checklisteneintrag und jede Aufgabe benötigt:

- eindeutige `id`,
- `module`,
- `status`,
- konkrete `description`,
- mindestens eine `source_ref`, soweit eine Quelle existiert,
- `next_action`,
- `reviewer_comment` als leeres bearbeitbares Feld.

Geldbeträge als Dezimalstrings mit Punkt und zwei Nachkommastellen speichern, zum Beispiel `"99.50"`. Kontonummern, Belegfelder und DATEV-IDs immer als Strings behandeln.

## Startklarheits-Checkliste

Jeder Checklisteneintrag benötigt zusätzlich:

- `topic_id`,
- `account_numbers` als Stringliste,
- `account_purpose`,
- `balance` als Dezimalstring oder `null`,
- `currency` als ISO-Code oder leeren String bei einem reinen Quellenthema,
- `zero_expectation`: `MUSS_NULL`, `NULL_ODER_NACHWEIS` oder `KEINE_NULLERWARTUNG`,
- `evidence_refs` als Liste vorhandener Quellen-IDs,
- `work_lane`: `ERLEDIGT`, `VOR_START_BEREINIGEN`, `UNTERLAGE_ANFORDERN` oder `IM_ABSCHLUSS_PRUEFEN`,
- `blocks_start` als Boolean.

`AUF_NULL` verlangt einen centgenauen Saldo `0.00`. Ein nicht auf null stehender Eintrag mit `ABGESTIMMT` und Null-/Nachweiserwartung benötigt mindestens einen konkreten `evidence_ref`. `STARTKLAR_FUER_ABSCHLUSSBEARBEITUNG` ist unzulässig, solange ein offener Eintrag `blocks_start: true` trägt.

`account_inventory.balance_sheet_accounts` enthält alle im Zieljahr bebuchten oder am Stichtag nicht auf null stehenden Bilanzkonten sowie die trotz Nullsaldo verpflichtend geprüften Kernkonten. Jedes Inventarkonto verweist über `checklist_item_id` auf genau einen vorhandenen Checklisteneintrag.

## Buchungsvorschläge

Zusätzlich erforderlich:

- `amount`, `currency`, `date`, `account`, `contra_account`, `debit_credit`,
- `document_field1`, `posting_text`, `tax_key`,
- `reason`, `confidence`, `approved: false`,
- `source_posting_id` oder ein konkreter Quellennachweis.

Für die 100-EUR-Regel gilt zusätzlich:

- `rule_id: "K-1590-LT100"`,
- absoluter Betrag kleiner `100.00`,
- `tax_key: ""`,
- `functional_source_account` als bestätigtes Konto für durchlaufende Posten,
- `functional_target_account` als bestätigtes Konto für sonstigen Betriebsbedarf,
- `account_mapping_source` als Nachweis der Live-Kontenplanprüfung,
- `source_posting_id` als eindeutiger Bezug zur Ursprungsbuchung,
- Zielkonto `4980` bei SKR03 oder `6850` bei SKR04 beziehungsweise ein dokumentiertes funktionales Individualkonto.

## Spätere Review-Sheet-Zuordnung

Die Vorlage wird nach Erhalt inventarisiert. Vor dem Schreiben festlegen:

| Datengruppe | Zielbereich im Sheet |
|---|---|
| Stammdaten und Jahre | Übersicht/Stammdaten |
| Startklarheits-Checkliste und Bilanzkontenabdeckung | Startklarheit/Kontenabstimmung |
| Debitoren/Kreditoren | Kontenübersicht |
| OPOS und Auszifferungskandidaten | OPOS/Auszifferung |
| 1360/1460 und 1590/1370 | Interimskonten |
| Lohnkonten und Abstimmnachweise | Lohnabstimmung |
| ARAP/PRAP-Registerabgleich | Abgrenzungen |
| Vorjahres-Abschlussbuchungen | Vorjahr/Roll-forward |
| Hinweise für die Abschlussbearbeitung | Übergabe an Abschlussbearbeitung |
| Aufgaben und Gates | Mitarbeiter/Offene Punkte |
| Buchungsvorschläge | Buchungsvorschläge |

Blattnamen und Spalten sind noch keine verbindlichen Namen. Die reale Vorlage hat Vorrang. Unbekannte Spalten nicht stillschweigend befüllen; die Zuordnung als versionsgebundenes Mapping dokumentieren.
