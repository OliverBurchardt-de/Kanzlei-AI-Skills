---
name: mt940-dateien-erstellen
description: Erstellt und validiert institutsunabhängige MT940-/STA-Dateien aus nativen MT940-, CAMT-, CSV-, PDF-, Bild- oder manuellen Umsatzquellen, insbesondere für DATEV. Verwenden, wenn Bankumsätze in ein kanonisches Modell überführt, strukturierte DATEV-Felder erzeugt, CP1252-Bytes geprüft, Salden abgestimmt, Quelltexte nachgewiesen oder Doppelimporte und ungeprüfte Produktivimporte verhindert werden sollen.
---

# MT940-Dateien erstellen

Aus unterschiedlichen Umsatzquellen nachvollziehbare MT940-Dateien erzeugen. Keine Verarbeitung nach Bankname, Logo, Dateiname, IBAN-Muster oder institutsspezifischem Layout verzweigen. Keine Buchung, keinen Saldo, Zahlungspartner, Verwendungszweck, Referenzwert oder GVC erfinden.

Technische Gültigkeit und tatsächlichen DATEV-Probeimport getrennt ausweisen.

## Architektur einhalten

Die Verarbeitung strikt in fünf Ebenen trennen:

1. **Quellenleser:** Native MT940-, CAMT-, CSV-, PDF-, Bild- oder manuelle Daten lesen. Layoutregeln ausschließlich hier verwenden.
2. **Quellnachweis:** Unveränderte Originalzeilen, Fundstelle und Sichtprüfung speichern.
3. **Kanonisches Umsatzmodell:** Institutsunabhängige fachliche Felder bilden.
4. **DATEV-Renderer:** Das kanonische Modell über ein DATEV-Zielprofil nach MT940 rendern.
5. **Validator:** Inhalt, Salden, Bytes, Feldstruktur, Rundlauf, Fingerprint und Freigabestatus prüfen.

Nach der Quellenlesung für jedes Institut dasselbe kanonische Schema und denselben DATEV-Renderer verwenden.

## Kodierungsvertrag

| Ebene | Kodierung |
| --- | --- |
| internes Textmodell | Unicode NFC |
| Manifest, JSON-Sidecar, Markdown-Bericht | UTF-8 ohne BOM |
| `.sta` mit Ziel DATEV | Windows-1252/CP1252 ohne BOM |
| `.sta`-Zeilenenden | ausschließlich CRLF, einschließlich Dateiende |

Für DATEV niemals eine freie UTF-8-Ausgabeoption anbieten. Vor dem Schreiben alle Ausgabetexte mit NFC normalisieren und streng mit `cp1252`, `errors="strict"` kodieren. Nicht darstellbare Zeichen als Klärungsfall ausgeben; keine Ersetzung durch `?`, `+`, Leerzeichen oder Transliteration zulassen.

Nach dem Schreiben die Rohbytes gegen die erwarteten CP1252-Bytes des kanonischen Modells prüfen. Insbesondere keine UTF-8-BOM, UTF-16-BOM oder UTF-8-Mehrbytefolgen für `ä`, `ö`, `ü`, `Ä`, `Ö`, `Ü` und `ß` akzeptieren.

## Workflow

### 1. Native Quelle bevorzugen

Vor einer PDF-Rekonstruktion nach nativer MT940- oder CAMT-Datei fragen. Wenn nur PDF, Bild, CSV oder manuelle Daten verfügbar sind, die Quelle eindeutig kennzeichnen und alle sichtbaren Inhalte belegen.

Bei PDFs die PDF-Skill-Anweisungen lesen, alle Seiten rendern und visuell prüfen. OCR oder Textextraktion nur als Arbeitshilfe verwenden.

### 2. Wiederholungsimport sperren

Vor einer korrigierten oder erneut erzeugten Datei fragen:

> Wurde der frühere Import für dieses Konto und diesen Zeitraum aus dem DATEV-Bankbestand gelöscht?

Ein neuer Chat, Dateiname, eine neue `:20:`-Referenz oder Auszugsnummer verhindert keinen DATEV-Doppelimport. Identische Fingerprints mit Status `5` sperren. `--allow-duplicate` nur mit `previous_datev_import_removed_confirmed: true` verwenden.

Keine Ausgleichsbuchung erzeugen, um Saldenfehler, FIBU-Differenzen oder Mehrfachimporte zu verdecken.

### 3. Auszugs- und Saldendaten getrennt erfassen

Je Konto erfassen:

- IBAN und Kontobezeichnung
- `statement_start` und `statement_end`
- `opening_balance_date` und `opening_balance`
- `closing_balance_date` und `closing_balance`
- `statement_number` und `sequence_number`
- Währung und Quellformat
- alle Buchungen in Quellreihenfolge

Für DATEV fehlende Saldendaten niemals aus dem Buchungszeitraum ableiten. Centgenau prüfen:

`Anfangssaldo + Summe aller vorzeichenbehafteten Buchungen = Endsaldo`

Bei Differenz abbrechen; nicht runden und keine künstliche Buchung ergänzen.

### 4. Quellnachweis je Umsatz speichern

Für jeden Umsatz den vollständigen unveränderten Quelltext erhalten:

```json
{
  "raw_source_lines": [
    "Entgelt",
    "Abonnement / Zusatzgebühren",
    "Zahlungspartner"
  ],
  "source_page": 1,
  "source_text_verified": true
}
```

Für PDF und Bild `source_page`, für CSV, CAMT, native oder manuelle Quellen `source_location` speichern. `source_text_verified: true` erst nach dem Abgleich mit der Originalquelle setzen. Unklaren Anfang, unklare Folgezeilen oder abgeschnittenes Ende als Klärungsfall ausgeben.

### 5. Kanonisches Umsatzmodell bilden

Für rekonstruierte DATEV-Ausgaben jeden Umsatz mindestens so abbilden:

```json
{
  "booking_date": "2026-07-01",
  "value_date": "2026-07-01",
  "amount": "-70.80",
  "currency": "EUR",
  "transaction_category": "fee",
  "booking_text": "Entgelt",
  "purpose": "Abonnement / Zusatzgebühren",
  "counterparty_name": "Zahlungspartner",
  "counterparty_iban": null,
  "references": [],
  "raw_source_lines": [
    "Entgelt",
    "Abonnement / Zusatzgebühren",
    "Zahlungspartner"
  ],
  "source_page": 1,
  "source_text_verified": true,
  "field_confidence": {
    "transaction_category": "high",
    "booking_text": "high",
    "purpose": "high",
    "counterparty_name": "high"
  }
}
```

Semantische Regeln:

- Zahlungspartner nur bei eindeutiger Quelle übernehmen.
- Verwendungszweck und alle Rechnungs-, Mandats-, End-to-End- und sonstigen Referenzen vollständig in Quellreihenfolge erhalten.
- Namen und Texte nicht sprachlich verbessern, umstellen oder ergänzen.
- Bei unsicherer Trennung den belegten Gesamttext im Verwendungszweck erhalten und die unsichere Einzelzuordnung kennzeichnen.
- Für eine produktive Datei nur `high` bei allen wesentlichen Feldern akzeptieren; sonst ausschließlich Testdatei oder Klärungsfall.
- Layoutkoordinaten und institutsspezifische Überschriften nicht in den DATEV-Renderer übernehmen.

### 6. Institutsunabhängigen DATEV-Renderer verwenden

Für rekonstruierte DATEV-Quellen ausschließlich `datev_structured_v1` beziehungsweise nach erfolgreichem Probeimport `datev_verified:datev-mt940-structured-v1` verwenden.

Strukturierte Belegung:

| Feld | Kanonischer Inhalt |
| --- | --- |
| GVC nach `:86:` | zentrale semantische Zuordnung; bei Unsicherheit `835` |
| `?00` | `booking_text` |
| `?20` bis `?29` | `purpose` und `references` |
| `?31` | belegte Gegen-IBAN, wenn zulässig |
| `?32` und `?33` | vollständiger Zahlungspartner |

Unterfelder verlustfrei und in Profilreihenfolge bilden. Kein Wort und keinen Referenzbestandteil an einer Unterfeldgrenze teilen. Beim Rücklesen Buchungstext, Verwendungszweck/Referenzen, Gegenkonto und Zahlungspartner getrennt gegen das kanonische Modell prüfen.

Das Fragezeichen ist im strukturierten Feld reserviert. Enthält ein belegter Nutztext `?`, ohne nachgewiesene zulässige Behandlung abbrechen; nicht still ersetzen.

GVC nur aus `transaction_category` und einer zentralen Zielprofiltabelle bestimmen. Nie aus Bank- oder Zahlungspartnernamen ableiten. Bei fehlender sicherer Zuordnung `835` verwenden und im Bericht dokumentieren.

### 7. DATEV-Zielprofil und Freigabe beachten

Profile unter `profiles/` sind DATEV-Zielprofile, keine Bankprofile. Das Profil `datev-mt940-structured-v1` enthält Zeichensatz, Importstrecke, Unterfelder, Längen, GVC-Regeln und Probeimportstatus.

- `datev_structured_v1`: nur technisch geprüfte Testdatei mit unverifiziertem Zielprofil.
- `datev_verified:datev-mt940-structured-v1`: vollständige Ausgabe nur nach dokumentiert erfolgreichem Probeimport und gelöschten Testumsätzen.
- `native`: unveränderte native `:86:`-Syntax erhalten.
- `generic_unstructured`: nur generische Nicht-DATEV- oder ausdrücklich unstrukturierte Anwendungsfälle ohne DATEV-Anzeigegarantie.

Unit-Tests verifizieren kein produktives Zielprofil.

### 8. Erzeugen und unabhängig validieren

```bash
python scripts/build-mt940.py manifest.json
python scripts/validate-mt940.py "MT940 <IBAN> <Zeitraum>.sta" manifest.json
```

Der Generator erzeugt `.sta` und UTF-8-Sidecar. Der Validator liest binär, prüft BOM, CRLF, CP1252-Sollbytes, jedes `:61:`/`:86:`-Paar, GVC, Unterfelder, semantischen Rundlauf, Reihenfolge, Salden und Fingerprint.

Exit-Status:

- `0`: technisch und rechnerisch gültig
- `2`: Quelldaten, semantische Felder oder Salden unvollständig
- `3`: Struktur-, Zeichen- oder Bytefehler
- `4`: Zielprofil oder Feldkonfidenz nicht produktiv verifiziert
- `5`: möglicher Doppelimport

## DATEV-Probeimport

Zunächst nur eine Testdatei mit höchstens einem Buchungstag erzeugen. Sie muss mindestens enthalten:

- Gebührenumsatz mit deutschem Sonderzeichen, beispielsweise `Zusatzgebühren`
- langen Zahlungspartner
- mehrere Referenzen in einem Umsatz

Vor dem Testimport bestätigen lassen:

> Für das Bankkonto und den Testzeitraum sind keine bereits importierten Bankkontoumsätze mehr vorhanden.

Im DATEV-Probeimport dokumentieren:

- Anfangs- und Test-Endsaldo
- Zahl und Vorzeichen der Umsätze
- Sonderzeichen ohne `++`, `?` oder Mojibake
- vollständiger Zahlungspartner
- vollständige Referenzen
- keine sichtbaren Unterfeldkennzeichen
- keine vertauschten oder abgeschnittenen Textteile

Danach anweisen:

> Die Testumsätze müssen vor dem Import der vollständigen Datei wieder aus dem DATEV-Bankbestand gelöscht werden.

Erst nach dokumentierter Prüfung und Löschung das Zielprofil als praktisch verifiziert markieren.

## Übergabe

Je Konto `.sta`, JSON-Sidecar und Prüfzusammenfassung liefern. Mindestens ausweisen:

- Zeitraum, Saldendaten, Buchungszahl und Buchungssumme
- Quellformat und Quellnachweis je Umsatz
- semantische Felder und Konfidenzen
- GVC-Quelle und Unterfeldreihenfolge
- `output_charset`, BOM, Zeilenenden und `byte_roundtrip_match`
- SHA-256-Fingerprint und Doppelimportstatus
- technischen Status und separaten DATEV-Praxistest
- offene Klärungen und Löschbestätigung

Ohne erfolgreichen Probeimport formulieren:

> Technisch und rechnerisch geprüft. Die konkrete Verarbeitung und Anzeige in DATEV ist noch nicht durch einen Probeimport bestätigt. Die Datei ist daher noch nicht für den vollständigen Produktivimport freigegeben.

Ohne Probeimport niemals „DATEV-kompatibel“, „DATEV-geprüft“ oder „erfolgreich importierbar“ behaupten.

Technische Details stehen in [technischer-aufbau.md](references/technischer-aufbau.md).
