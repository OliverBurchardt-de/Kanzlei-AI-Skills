# Technische Referenz – B&K DATEV Export

## 1. Getrennte Importobjekte

| Objekt | Zielsystem | Format |
|---|---|---|
| Buchungsstapel | DATEV Kanzlei-Rechnungswesen | EXTF-CSV |
| Belegbilder | DATEV Belegtransfer / DUO | ZIP mit `document.xml` |
| Verknüpfung | beide | identische GUID / `BEDI "<GUID>"` |

## 2. EXTF-Dateieigenschaften

```yaml
encoding: cp1252
delimiter: ";"
quotechar: '"'
quoting: all_fields
line_ending: CRLF
decimal_separator: ","
header_field_count: 31
date_format_header: YYYYMMDD
date_format_booking: DDMM
```

## 3. Kopfsatz als Array

```python
header = [
    "EXTF", "700", "21", "Buchungsstapel", "12",
    generated_at,
    "", "", "", "",
    advisor_number,
    client_number,
    fiscal_year_start,
    account_length,
    date_from,
    date_to,
    description,
    "",
    "1",
    "0",
    "", "", "", "", "", "", "", "", "", "", ""
]
assert len(header) == 31
```

## 4. Mindestprüfung des Kopfsatzes

```python
assert header[0] == "EXTF"
assert header[1] == "700"
assert header[2] == "21"
assert header[3] == "Buchungsstapel"
assert header[10] == advisor_number
assert header[11] == client_number
assert re.fullmatch(r"\d{8}", header[12])
assert header[13].isdigit()
assert re.fullmatch(r"\d{8}", header[14])
assert re.fullmatch(r"\d{8}", header[15])
assert header[14] <= header[15]
```

## 5. document.xml – maschinenlesbare Spezifikation

```yaml
package:
  format: zip
  compression: deflate
  flat_structure: true
  required:
    - document.xml
  payload:
    - "*.pdf"

document_xml:
  encoding: UTF-8
  namespace: "http://xml.datev.de/bedi/tps/document/v04.0"
  xsi_namespace: "http://www.w3.org/2001/XMLSchema-instance"
  schema_location: "http://xml.datev.de/bedi/tps/document/v04.0 document_v040.xsd"
  archive_version: "4.0"
  header_date: "YYYY-MM-DDTHH:MM:SS"
  document:
    processID: "1"
    guid: UUID
    type: "1|2"
    extension:
      xsi_type: File
      name_equals_zip_entry: true

booking_csv:
  beleglink: 'BEDI "<GUID>"'
```

## 6. Nicht zulässige Varianten aus festgestellten Fehlern

```text
Root: documentPackage
Nur PDF-Dateiname im Feld Beleglink
Reines Datum in <date>
Beraternummer an Feldposition 10
Mandantennummer an Feldposition 11
Freie Zusatzattribute im archive-Element
Leistungsdatum ohne bestätigte Mandantenlogik
Umbuchungsschlüssel 90 oder 91
```

## 7. Kanzleivorgaben

- Leistungsdatum grundsätzlich nicht verwenden, sofern nicht ausdrücklich für den Mandanten freigegeben.
- Umbuchungen nutzen – soweit ein BU-Schlüssel erforderlich ist – die Kanzleilogik 900/901, nicht 90/91.
- KOST1 muss mandantenspezifisch geprüft werden.
- Beleg-GUID und Dateiname bleiben über den gesamten Prozess unverändert.

## 8. Klardaten-MCP – technische Abruflogik

### 8.1 Identifikatoren niemals erfinden

```text
1. clients abrufen
2. clientId aus Treffer übernehmen
3. fiscal_years mit clientId abrufen
4. fiscalYearId aus Treffer übernehmen
5. Zielressource mit beiden IDs abrufen
```

### 8.2 Saldenabfrage

Für reine Monats- oder Jahresendbestände:

```text
datev://accounting/accounting_sums_and_balances
```

Mindestfelder:

```text
id
account_number
caption
accounting_sums_and_balances_month_values
```

Achtung: Ein fehlender Monatswert ist nicht gleichbedeutend mit einem fehlenden
EB-Saldo. Bei Bestands- und Bilanzkonten ist deshalb zusätzlich das Kontenblatt
beziehungsweise die Einzelbuchung zu prüfen.

### 8.3 Kontenblatt und EB-Prüfung

Bevorzugte Ressourcen:

```text
datev://accounting/account_postings
datev://accounting/accounting_records
```

Mindestprüfung:

```yaml
konto:
  nummer: string
  bezeichnung: string
  eb_saldo: decimal
  jahresverkehr_soll: decimal
  jahresverkehr_haben: decimal
  saldo_vor_abschluss: decimal
  bereits_gebuchte_abschlussbuchungen: list
```

### 8.4 Differenzlogik

```python
differenz = round(sollbestand - saldo_vor_abschluss, 2)

if differenz > 0:
    # Bestand erhöhen
    betrag = differenz
    buchungsrichtung = "Bestandskonto an Bestandsveränderung"
elif differenz < 0:
    # Bestand vermindern
    betrag = abs(differenz)
    buchungsrichtung = "Bestandsveränderung an Bestandskonto"
else:
    # Keine Buchung
    betrag = 0
```

Die konkrete Kontonummer und Kontenrichtung sind mandantenspezifisch anhand des
DATEV-Kontenplans zu bestimmen.

### 8.5 Klardaten-Fehlerfälle

```text
Kein Mandantentreffer:
- Suche mit Mandantennummer und Firmenname wiederholen.
- Keine GUID schätzen.

Mehrere Mandantentreffer:
- Benutzer um Auswahl bitten.

Kein Wirtschaftsjahr:
- Keine Zielressource abfragen.
- Zeitraum prüfen.

SUSA ohne EB:
- Kontenblatt oder Buchungssätze abrufen.

Connector nicht verfügbar:
- Nur Benutzerwerte verwenden.
- Quelle kennzeichnen.
- Produktiven Import stoppen, wenn Pflichtdaten fehlen.
```
