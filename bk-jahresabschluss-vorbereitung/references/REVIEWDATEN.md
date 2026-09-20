# Kanonischer Vorbereitungsdatensatz

## Zweck

`Vorbereitungsdaten.json` trennt Fachlogik von der noch ausstehenden Excel-Vorlage. Der Datensatz ist die belegte Quelle für das spätere Vorbefüllen des Review-Sheets und für die Mitarbeiterzusammenfassung. Er enthält eine Startklarheits-Checkliste, aber kein Gesamturteil zum Jahresabschluss.

## Pflichtstruktur

Das folgende Beispiel zeigt die Struktur gekürzt. Ein gültiger Lauf enthält anschließend sämtliche unten genannten Pflicht-Themen und die vollständige Bilanzkontenabdeckung.

```json
{
  "schema_version": "0.5.0",
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
  "opening_balance_review": {
    "area_inventory_status": "NICHT_PRUEFBAR",
    "area_inventory_source_refs": [],
    "expected_areas": [],
    "areas": []
  },
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
    "clearing_candidates": [],
    "reconciliation": [],
    "rollforward": []
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

`preparation_checklist` muss mindestens die `topic_id`-Werte `quellen_datenstand`, `eroeffnungsbilanz`, `bilanzkonten_abdeckung`, `opos_debitoren`, `opos_kreditoren`, `bank_kasse`, `geldtransit`, `durchlaufende_posten`, `lohnkonten`, `steuerkonten`, `abgrenzungen` und `vorjahr_rollforward` enthalten. Ein nicht einschlägiges Thema bleibt mit `NICHT_ANWENDBAR` sichtbar; es wird nicht weggelassen. Bei Bilanzierung ist `eroeffnungsbilanz` niemals pauschal `NICHT_ANWENDBAR`; bei unbekannter Bereichslage `NICHT_PRUEFBAR`, `blocks_start: true` und Arbeitsspur `UNTERLAGE_ANFORDERN` setzen.

## Eröffnungsbilanz nach Bereichen

`opening_balance_review` trennt Bereichsinventar und Abgleiche. `area_inventory_status`: `BEKANNT`, `NICHT_PRUEFBAR` oder bei nachgewiesener EÜR `NICHT_ANWENDBAR`. Bei `BEKANNT` vollständige `area_inventory_source_refs`, beide Prüflinien `handelsrecht` und `steuerrecht` in `expected_areas` und genau einen Eintrag in `areas` je Kennung führen; weitere belegte Bereiche ergänzen. Ohne bekanntes Inventar bleiben die Listen leer, der Bilanzfall blockiert und beide Prüflinien werden im Bericht als ungeklärt benannt.

Jeder Bereich benötigt:

- `area_id`, `status`, `evidence_extent` (`vollstaendig`, `teilweise`, `nicht_pruefbar`, `nicht_anwendbar`) und `next_action`;
- `prior_close_source_ref` und `current_opening_source_ref` (Quellen-ID oder null);
- `prior_close_final` und `comparison_complete` als Boolean;
- `compared_account_count`, `account_comparisons`, `groups` (optional), `differences` und `unmapped_accounts`.

Je Kontenvergleich:

```json
{
  "prior_account": "1200",
  "opening_account": "1200",
  "prior_balance": "100.00",
  "opening_balance": "100.00",
  "currency": "EUR"
}
```

Alle Positionen der Vereinigung beider Bestände abdecken; nur in einer vollständigen Quellseite fehlende Konten mit null ansetzen. Soll positiv/Haben negativ. Kontenwechsel benötigen `mapping_source_ref`. Dieselbe Position darf je Währung und Quellseite nur einmal vorkommen. `compared_account_count` muss der Zeilenzahl entsprechen.

Bei Gruppierung je Vergleich `group_id` ergänzen. Eine Gruppe enthält `id`, `kind` (`darlehen_gesellschafter`, `umsatzsteuer`, `ergebnisvortrag`), `currency`, `reason`, `source_refs` und `next_action`. Mitgliedskonten und Gruppensummen entstehen aus den verknüpften Vergleichszeilen und müssen im Arbeitspapier sichtbar sein. Ergebnisvortrag benötigt zusätzlich `bridge_amount` und `bridge_source_ref`; Formel: Summe Eröffnung minus Summe Schluss minus Brückenbetrag. Für andere Gruppen ist kein Brückenbetrag zulässig.

Jede Bereichsquelle trägt `accounting_area_id` und die passende `fiscal_year_id`. Für vollständige Quellen zusätzlich:

- `complete: true`;
- `proof_kind: "direct_area"` für unmittelbar bereichsspezifische Werte oder `"derived_area"` für vollständig hergeleitete Werte;
- bei Herleitung `base_semantics`, `layers_complete: true` und `derivation_source_refs` auf vollständige Roh-/Überleitungsquellen desselben Wirtschaftsjahrs. Die Herleitung selbst mit Konten, Vorzeichen und Schichtzuordnung im Quellenprotokoll ablegen. Mehrstufige Herleitungen bis zu den unabhängigen Roh-/Überleitungsquellen auflösen; keine erneute `derived_area`-Quelle, kein Selbstverweis, keine Doppelzählung;
- bei Ergebnisbrücke `document_role`: `finale_ja_susa`, `festgestellter_abschluss` oder `abschlussbuchung`, jeweils mit passender Prüflinie und Vorjahres-ID.

`ABGESTIMMT` verlangt beide vollständigen Bereichsquellen, `evidence_extent: "vollstaendig"`, finalen Vorjahresstand, vollständigen Kontenvergleich und keine ungeklärte Konten-/Gruppendifferenz. Die feste EUR-Toleranz ist `0.005`; Geldwerte bleiben Cent-Dezimalstrings.

`TEILNACHWEIS` benötigt `evidence_extent: "teilweise"`, `comparison_complete: false`, konkrete `partial_source_refs` und nächsten Schritt. Teilquellen dürfen `complete: false` tragen. Identische Anlagenbuchungs-Teilmengen von 2.882,00 EUR aus dem Referenzfall 12500 sind deshalb zulässig dokumentierbar, aber kein vollständiger Bereichsnachweis. Eine gemeinsame SuSa bekommt weder `direct_area` noch ohne vollständige Herleitung `derived_area`.

Eine einzelne fachlich nicht anwendbare Prüflinie bleibt mit `NICHT_ANWENDBAR`, `evidence_extent: "nicht_anwendbar"` und vollständigen `non_applicability_source_refs` sichtbar. Fehlende Daten sind keine Nichtanwendbarkeit. Bei bekanntem Inventar dürfen ungeprüfte Bereiche nicht weggelassen werden. `STARTKLAR` verlangt für beide Prüflinien einen vollständigen Abgleich oder nachgewiesene Nichtanwendbarkeit.

Im Erstjahr ist eine gesonderte Prüfung gegen Gründungs-/Übernahmeunterlagen erforderlich. Ohne Vorjahr bestätigt dieses Schema keinen automatischen Schluss-zu-EB-Abgleich.

## OPOS-Abgleich und Datenstand

`open_items.reconciliation` enthält genau vier Abgleiche: `side` jeweils `receivable` und `payable`, `basis` jeweils `current` und `closing`. Ein offener Mindesteintrag lautet:

```json
{
  "side": "receivable",
  "basis": "current",
  "status": "NICHT_PRUEFBAR",
  "next_action": "Vollständige OPOS und Personenkonten zum gleichen Buchhaltungsstand abrufen."
}
```

Auch bei offenem Status verfügbare Teilvergleiche, Quellen und Differenzen dokumentieren. Für `ABGESTIMMT` sind zusätzlich verbindlich:

- `opos_as_of` und `ledger_as_of`: gleicher ISO-Stichtag; bei `closing` das Zieljahresende;
- `snapshot_id`: Kennung des nachweislich konsistenten Buchungsstands, kein frei vergebener Ersatz für dessen Prüfung;
- `complete`, `snapshot_consistent`, `item_check_complete`, `control_check_complete`: jeweils true und fachlich nachgewiesen;
- `source_refs`: vollständige Quellen mit `reconciliation_role` für `opos`, `personenkonten`, `sammelkonten`; jede Quelle trägt dieselbe `side`, `snapshot_id` und `as_of`;
- `expected_accounts`: vollständige Vereinigung aus OPOS- und Fibu-Personenkonten als `Konto|Währung`, beispielsweise `10001|EUR`;
- `account_comparisons`: je Konto/Währung `account`, `currency`, `opos_balance`, `ledger_balance` als vorzeichenrichtige Cent-Dezimalstrings;
- `unresolved_items` und `control_differences`: leer; offene Differenzen stattdessen mit Betrag, Quelle und Aufgabe unter einem offenen Status erfassen;
- bei `closing` zusätzlich `historical_method`: `historical_export` oder `full_reconstruction`. Ein Datumsfilter auf aktuelle OPOS ist nicht ausreichend.

Leere Kontenlisten sind nur mit vollständig belegtem Leerbestand zulässig. Eine passende Gesamtsumme ersetzt keinen Konten- und Postenvergleich. Den Sammelkontenabgleich mit Summen und Überleitung in den referenzierten Berechnungsnachweisen ablegen.

Zusätzlich `open_items.rollforward` führen: je Stichtagsposten eindeutige `id`, `side`, `account`, `currency`, Beleg-/Herkunftsreferenz, ursprünglicher offener Betrag, spätere Zahlungen/Gutschriften/Umbuchungen mit Datum und Quellen, aktueller Rest, Status und nächster Schritt. Neue Folgejahresposten separat erfassen. Datenstand und fehlende Zeiträume ausdrücklich nennen.

Die Prüfung validiert Pflichtfelder, Quellenverknüpfungen, Bereichs-/Jahreszuordnung, Beträge, Gruppen und Statussperren. Sie ersetzt nicht die fachliche Kontrolle von Originalbelegen, DATEV-Vollständigkeit, Schichtherleitung oder Excel-Formeln. Solange aktuelle oder historische Abstimmung einer Seite offen bleibt, muss der entsprechende OPOS-Checklisteneintrag `blocks_start: true` tragen.

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
| Eröffnungsbilanz je Handels-/Steuerrechtsbereich | Eröffnungsbilanz/Bereichsstatus |
| Startklarheits-Checkliste und Bilanzkontenabdeckung | Startklarheit/Kontenabstimmung |
| Debitoren/Kreditoren | Kontenübersicht |
| OPOS-Abgleich aktuell/Stichtag, Fortschreibung und Auszifferungskandidaten | OPOS/Abgleich/Fortschreibung/Auszifferung |
| 1360/1460 und 1590/1370 | Interimskonten |
| Lohnkonten und Abstimmnachweise | Lohnabstimmung |
| ARAP/PRAP-Registerabgleich | Abgrenzungen |
| Vorjahres-Abschlussbuchungen | Vorjahr/Roll-forward |
| Hinweise für die Abschlussbearbeitung | Übergabe an Abschlussbearbeitung |
| Aufgaben und Gates | Mitarbeiter/Offene Punkte |
| Buchungsvorschläge | Buchungsvorschläge |

Blattnamen und Spalten sind noch keine verbindlichen Namen. Die reale Vorlage hat Vorrang. Unbekannte Spalten nicht stillschweigend befüllen; die Zuordnung als versionsgebundenes Mapping dokumentieren.

Diese freie Zuordnung betrifft nur das spätere Gesamt-Review-Sheet. Die Blätter des eigenständigen Eröffnungsbilanz-Arbeitspapiers sind in `EROEFFNUNGSBILANZ.md` bereits verbindlich definiert.
