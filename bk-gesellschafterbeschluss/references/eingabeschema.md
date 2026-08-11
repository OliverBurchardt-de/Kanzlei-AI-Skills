# Eingabeschema für die Dokumenterstellung

## Pflichtfelder

```json
{
  "company_name": "Muster GmbH",
  "registered_office": "Dortmund",
  "fiscal_year": 2025,
  "balance_total": "2662355.54",
  "annual_result": "511723.10",
  "appropriation": {
    "mode": "carryforward"
  }
}
```

`annual_result` ist vorzeichenbehaftet: positiv für Jahresüberschuss, negativ für Jahresfehlbetrag, null für Nullergebnis.

## Optionale Felder

```json
{
  "discharge_management": true,
  "resolution_date": null,
  "signature_label": "Unterschrift(en) der Gesellschafter",
  "appropriation": {
    "mode": "partial-distribution",
    "distribution_amount": "100000.00",
    "due_date": "30. September 2026",
    "settlement": "payout",
    "custom_settlement_text": null
  }
}
```

## Zulässige Ergebnisverwendungen

- `carryforward`: laufendes Ergebnis auf neue Rechnung vortragen.
- `full-distribution`: positiven Jahresüberschuss vollständig ausschütten.
- `partial-distribution`: positiven Jahresüberschuss teilweise ausschütten, Rest vortragen.
- `retained-earnings-distribution`: laufendes Ergebnis vortragen und zusätzlich aus Gewinnvortrag ausschütten.
- `custom`: vollständig vorgegebener Text in `custom_text`.

Für alle Ausschüttungsmodi sind `distribution_amount` und `due_date` Pflicht. Bei `full-distribution` muss der Betrag dem Jahresüberschuss entsprechen. Bei `partial-distribution` muss er kleiner als der Jahresüberschuss sein.

## Settlement

- `payout`: Auszahlung nach Steuerabzug.
- `shareholder-account`: Verrechnung mit Gesellschafterkonto nach Steuerabzug.
- `custom`: Text aus `custom_settlement_text` verwenden.
- `none`: keine zusätzliche Zahlungsformulierung.

## Beispiel Jahresfehlbetrag

```json
{
  "company_name": "Muster GmbH",
  "registered_office": "Dortmund",
  "fiscal_year": 2025,
  "balance_total": "850000.00",
  "annual_result": "-42500.00",
  "appropriation": {
    "mode": "carryforward"
  }
}
```

Das Skript formuliert automatisch „Jahresfehlbetrag von EUR 42.500,00“ und verwendet kein Minuszeichen im Beschlusstext.
