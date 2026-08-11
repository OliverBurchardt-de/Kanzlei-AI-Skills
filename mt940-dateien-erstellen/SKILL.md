---
name: mt940-dateien-erstellen
description: Erstellt, prüft und erläutert MT940-Swift-Dateien aus PDF-Kontoauszügen oder strukturierten Umsatzlisten. Verwenden, wenn Konto- oder Kreditkartenumsätze für DATEV als MT940/STA aufbereitet, bestehende MT940-Dateien technisch validiert, Salden und Buchungszahlen abgestimmt oder Mitarbeitern Aufbau und Prüfschritte des Formats erklärt werden sollen.
---

# MT940-Dateien erstellen

Aus Quelldokumenten nachvollziehbare MT940-Dateien erzeugen. Keine Buchung, kein Datum und keinen Saldo erfinden. Eine Datei erst nach vollständiger Saldenabstimmung ausgeben.

## Arbeitsmodus bestimmen

- **Erstellen:** Kontoauszüge oder Umsatzlisten in eine `.sta`-Datei umwandeln.
- **Prüfen:** Vorhandene MT940-Datei technisch und rechnerisch validieren.
- **Erklären:** Den technischen Aufbau für Mitarbeiter anhand von [technischer-aufbau.md](references/technischer-aufbau.md) erläutern.

Bei PDFs zuerst die PDF-Skill-Anweisungen lesen, alle Seiten rendern und visuell prüfen. Textextraktion nur zusammen mit der visuellen Kontrolle verwenden.

## Erstellungsworkflow

### 1. Quelldaten sichern

Je Konto getrennt erfassen:

- Kontoinhaber und IBAN
- ausgewiesener Abfrage- oder Auszugszeitraum
- Anfangs- und Endsaldo mit Vorzeichen und Währung
- jede Buchung mit Betrag, Soll/Haben, Valutadatum, Buchungsdatum und Verwendungszweck
- Reihenfolge der Buchungen

Aus jedem Konto eine eigene MT940-Datei erzeugen. Kreditkartenkonten nicht mit dem Zahlkonto vermischen.

### 2. Vollständigkeit prüfen

Vor der Erzeugung zwingend rechnen:

`Anfangssaldo + Summe aller vorzeichenbehafteten Buchungen = Endsaldo`

Zusätzlich prüfen:

- Zahl der erkannten Buchungen gegen die sichtbaren Buchungen
- frühestes und spätestes Valuta- und Buchungsdatum
- Rücklastschriften, Gutschriften und Gebühren mit korrektem Vorzeichen
- Seitenwechsel auf abgeschnittene oder doppelt erfasste Buchungen
- Auszugsfilter gegen den im Dateinamen genannten Zeitraum

Bei einer Differenz nicht runden, keine Ausgleichsbuchung erzeugen und keine MT940-Datei freigeben. Den konkreten Klärungsfall nennen.

### 3. Manifest erstellen

Ein UTF-8-JSON nach diesem Schema anlegen:

```json
{
  "iban": "DE89370400440532013000",
  "account_name": "Beispiel Geschäftskonto",
  "period_start": "2025-01-01",
  "period_end": "2025-12-31",
  "opening_balance": "100.00",
  "closing_balance": "125.00",
  "currency": "EUR",
  "transactions": [
    {
      "value_date": "2025-01-02",
      "booking_date": "2025-01-02",
      "amount": "-25.00",
      "code": "NMSC",
      "customer_reference": "RECHNUNG4711",
      "description": "Beispielzahlung Rechnung 4711"
    },
    {
      "value_date": "2025-01-03",
      "booking_date": "2025-01-03",
      "amount": "50.00",
      "code": "NTRF",
      "description": "Beispielgutschrift"
    }
  ]
}
```

Beträge als Dezimalstrings mit Punkt und genau zwei Nachkommastellen speichern. Belastungen negativ, Gutschriften positiv erfassen. Transaktionen chronologisch nach Buchungsdatum anordnen; bei gleichem Buchungsdatum die nachvollziehbare Quellreihenfolge beibehalten.

Übliche Codes:

| Sachverhalt | Code |
| --- | --- |
| Überweisung/Gutschrift | `NTRF` |
| Lastschrift | `NDDT` |
| Gebühren/Abschluss | `NCHG` |
| Kartenzahlung oder nicht sicher klassifizierbar | `NMSC` |

Keine spezifischere Klassifizierung vortäuschen, wenn der Auszug sie nicht hergibt.

Eine im Auszug vorhandene `EREF`, `MREF`, Rechnungsnummer oder sonstige belastbare Referenz zusätzlich als `customer_reference` erfassen. Optional `bank_reference` verwenden, wenn eine gesonderte Bankreferenz sichtbar ist. Die Skripte normalisieren diese Werte auf höchstens 16 alphanumerische Zeichen; die vollständige Referenz außerdem im Verwendungszweck erhalten. Nur bei tatsächlich fehlender Referenz `NONREF` verwenden.

### 4. Datei deterministisch erzeugen

```bash
python3 scripts/build-mt940.py manifest.json
```

Ohne Ausgabepfad erzeugt das Skript:

`MT940 <IBAN> <TT.MM.JJJJ> bis <TT.MM.JJJJ>.sta`

Keine Unterstriche in Dateinamen verwenden. Die Datei in Windows-1252 mit CRLF-Zeilenumbrüchen schreiben.

### 5. Unabhängig validieren

```bash
python3 scripts/validate-mt940.py "MT940 <IBAN> <Zeitraum>.sta"
```

Nur ausgeben, wenn beide Skripte erfolgreich enden und zusätzlich der Abgleich gegen die Quelldokumente abgeschlossen ist.

## Technische Pflichtregeln

- Pflichtfolge: `:20:`, `:25:`, `:28C:`, `:60F:`, je Buchung `:61:` und unmittelbar danach `:86:`, abschließend `:62F:`.
- In `:25:` die IBAN des ausgewerteten Kontos führen.
- In `:60F:` den ausgewiesenen Anfangssaldo und in `:62F:` den Endsaldo führen.
- `C` für positiven Saldo/Betrag und `D` für negativen Saldo/Betrag verwenden.
- `:61:` mit Valuta, Buchungsdatum, Betrag, sachgerechtem Buchungscode und vorhandener Quellreferenz belegen; `NONREF` nur verwenden, wenn die Quelle keine belastbare Referenz enthält.
- `:86:` auf höchstens sechs Zeilen und 390 Zeichen einschließlich Tag begrenzen; keine Fortsetzungszeile mit Doppelpunkt beginnen lassen.
- Jede physische Zeile auf höchstens 65 Zeichen begrenzen.
- Den Auszugszeitraum, nicht nur den Zeitraum mit tatsächlicher Kontobewegung, im Dateinamen nennen.

Die vollständige Feldbeschreibung und ein anonymisiertes Muster stehen in [technischer-aufbau.md](references/technischer-aufbau.md).

## Abbruch- und Klärungsfälle

Keine fertige Datei erzeugen, wenn mindestens einer dieser Fälle vorliegt:

- Anfangs- oder Endsaldo fehlt.
- Saldenrechnung geht nicht centgenau auf.
- Betrag, Vorzeichen oder Buchungsdatum einer Buchung ist nicht sicher lesbar.
- Seiten oder Monate fehlen, obwohl der angegebene Zeitraum Vollständigkeit behauptet.
- Mehrere Konten sind nicht eindeutig voneinander trennbar.
- Der Auszug enthält nur vorgemerkte, nicht endgültig gebuchte Umsätze.

Unklare Positionen tabellarisch mit Seite, sichtbarem Text und benötigter Klärung ausgeben.

## Übergabe

Je Konto die `.sta`-Datei sowie eine kurze Prüfzusammenfassung liefern:

- IBAN und Zeitraum
- Anzahl der Buchungen
- Anfangssaldo, Buchungssumme und Endsaldo
- frühestes/spätestes Valuta- und Buchungsdatum
- Ergebnis der technischen Validierung
- Hinweis, ob ein tatsächlicher DATEV-Probeimport durchgeführt wurde

Ohne DATEV-Probeimport niemals behaupten, der Import sei praktisch erfolgreich gewesen. Stattdessen „technisch und rechnerisch geprüft; DATEV-Probeimport nicht durchgeführt“ angeben.
