---
name: mt940-dateien-erstellen
description: Erstellt und validiert MT940-/STA-Dateien aus nativen Bankdateien, PDF-Kontoauszügen, Bildern oder strukturierten Umsatzlisten, insbesondere für DATEV. Verwenden, wenn Konto- oder Kreditkartenumsätze als MT940 aufbereitet, bestehende Dateien feldweise gegen Quelldaten geprüft, Salden und Verwendungszwecke abgestimmt, DATEV-Probeimporte vorbereitet oder Mehrfachimporte verhindert werden sollen.
---

# MT940-Dateien erstellen

Aus Quelldaten nachvollziehbare MT940-Dateien erzeugen. Keine Buchung, kein Datum, keinen Saldo und kein DATEV-Profil erfinden. Technische Gültigkeit nie mit einem praktisch erfolgreichen DATEV-Import gleichsetzen.

## Arbeitsmodus bestimmen

- **Erstellen:** Kontoauszug oder Umsatzliste in eine `.sta`-Datei umwandeln.
- **Prüfen:** MT940-Datei feldweise gegen Manifest und Quelle validieren.
- **Erklären:** [technischer-aufbau.md](references/technischer-aufbau.md) lesen und den Aufbau erläutern.

Bei PDFs zuerst die PDF-Skill-Anweisungen lesen, alle Seiten rendern und visuell prüfen. Textextraktion nur zusammen mit der visuellen Kontrolle verwenden.

## Workflow

### 1. Native Bankdatei bevorzugen

Vor einer PDF-Rekonstruktion ausdrücklich nach einer nativen MT940- oder CAMT-Datei fragen. Eine elektronische Originaldatei der Bank bevorzugen. Wenn ausschließlich PDF, Bild oder manuelle Daten verfügbar sind, die Rekonstruktion als solche kennzeichnen.

### 2. Wiederholungsimport sperren

Vor einer korrigierten oder erneut erzeugten Datei fragen:

> Wurde der frühere Import für dieses Konto und diesen Zeitraum aus dem DATEV-Bankbestand gelöscht?

Ein neuer Chat, Dateiname, eine neue `:20:`-Referenz oder eine andere Auszugsnummer bereinigt DATEV nicht. Bei einer bereits vorhandenen Fingerprint-Sidecar-Datei abbrechen. `--allow-duplicate` nur nach bestätigter Löschung und mit `previous_datev_import_removed_confirmed: true` verwenden.

Keine MT940-Ausgleichsbuchung erzeugen, um eine FIBU-Differenz oder einen Mehrfachimport zu verdecken.

### 3. Quelldaten getrennt erfassen

Je Konto erfassen und gegen die sichtbare Quelle prüfen:

- Kontoinhaber und IBAN
- Auszugsbeginn und Auszugsende
- Datum und Betrag des Anfangssaldos
- Datum und Betrag des Endbestands
- Auszugsnummer und Sequenznummer
- jede Buchung in Quellreihenfolge mit Betrag, Vorzeichen, Valuta, Buchungsdatum, Referenz und vollständigem Verwendungszweck

Aus jedem Konto eine eigene Datei erzeugen. Kreditkartenkonto und Zahlkonto nicht vermischen.

### 4. Vollständigkeit centgenau prüfen

Zwingend rechnen:

`Anfangssaldo + Summe aller vorzeichenbehafteten Buchungen = Endsaldo`

Zusätzlich Buchungszahl, Reihenfolge, Datumsgrenzen, Seitenwechsel, Rücklastschriften, Gutschriften und Gebühren prüfen. Bei einer Differenz nicht runden, keine Ausgleichsbuchung erzeugen und keine Datei freigeben.

### 5. Manifest erstellen

Für DATEV ein UTF-8-JSON mit getrennten Auszugs- und Saldendaten verwenden:

```json
{
  "iban": "DE43300501101009524321",
  "account_name": "JS Logistik GmbH - Stadtsparkasse Düsseldorf",
  "statement_start": "2026-07-01",
  "statement_end": "2026-07-31",
  "opening_balance_date": "2026-06-30",
  "opening_balance": "83077.77",
  "closing_balance_date": "2026-07-31",
  "closing_balance": "33444.84",
  "statement_number": 7,
  "sequence_number": 1,
  "currency": "EUR",
  "source_type": "pdf",
  "target_system": "DATEV",
  "field86_mode": "unverified",
  "output_scope": "test",
  "transactions": []
}
```

Für PDF-, Bild- und manuelle Quellen zusätzlich `source_evidence` mit den sichtbaren Datums-, Salden- und Auszugswerten speichern. Der Generator gleicht vorhandene Evidenzfelder gegen das Manifest ab.


#### PDF-Buchungstext als Pflichtnachweis erfassen

F?r **jeden** Umsatz aus PDF oder Bild folgende Felder speichern:

```json
{
  "source_page": 3,
  "source_description_lines": [
    "Allianz Versicherungs-AG Vertrag AS-6170637093,",
    "Kfz-Versicherung ME-LS 2028,",
    "Referenz SA01A000000095207172"
  ],
  "source_text_verified": true,
  "description": "Allianz Versicherungs-AG Vertrag AS-6170637093, Kfz-Versicherung ME-LS 2028, Referenz SA01A000000095207172"
}
```

Dabei zwingend:

- Buchungsblock auf der gerenderten PDF-Seite visuell abgrenzen.
- Alle sichtbaren Zeilen des Buchungstextes in ihrer Reihenfolge wortgetreu nach `source_description_lines` ?bernehmen.
- OCR-/Extraktionstext nur als Arbeitshilfe verwenden und anschlie?end Zeichen f?r Zeichen gegen das Seitenbild pr?fen.
- Namen, Verwendungszweck, IBAN, Mandats-, End-to-End-, Vertrags- und sonstige Referenzen weder umstellen noch zusammenfassen, erg?nzen oder sprachlich ?verbessern?.
- Sichtbare Wiederholungen, Bindestriche, Satzzeichen und Referenzbestandteile erhalten.
- Bei unklarem Anfang oder Ende des Buchungsblocks abbrechen und einen Kl?rungsfall ausgeben.
- `source_text_verified: true` erst nach der visuellen Pr?fung setzen.

Der Generator leitet den `:86:`-Ausgangstext ausschlie?lich aus den sichtbaren `source_description_lines` ab. Ein zus?tzlich gespeichertes `description` muss nach der festgelegten Leerzeichennormalisierung exakt ?bereinstimmen; andernfalls mit Status `2` abbrechen. Damit reicht ein intern stimmiger, aber gegen?ber dem PDF falscher Manifesttext nicht mehr aus.

Pflichtregeln:

- `opening_balance_date` ausschließlich für `:60F:` verwenden.
- `closing_balance_date` ausschließlich für `:62F:` verwenden.
- `statement_start` und `statement_end` für Dateiname, Zeitraumskontrolle und Bericht verwenden.
- Für DATEV keine fehlenden Saldendaten aus dem Auszugszeitraum ableiten.
- `statement_number` und das standardmäßig `1` betragende `sequence_number` ausdrücklich speichern.
- Buchungsdaten innerhalb des Auszugszeitraums halten.
- Abweichende Valutadaten nur bei belegter Quelle zulassen: am Umsatz `value_date_source_confirmed: true` setzen und die Umsatznummer unter `review_report.value_date_exceptions` nennen.
- Geldbeträge als Dezimalstrings mit Punkt und zwei Nachkommastellen speichern; Belastungen negativ, Gutschriften positiv.
- Quellreihenfolge chronologisch beibehalten.

Legacy-Manifeste mit `period_start` und `period_end` nur im generischen Modus verarbeiten. Bei `target_system: DATEV` ohne die vier getrennten Datumsfelder abbrechen; keine vermutete Migration durchführen.

### 6. Modus für `:86:` festlegen

Nur diese Werte verwenden:

- `native`: Syntax unverändert aus einer elektronischen Originaldatei übernehmen.
- `generic_unstructured`: formal generisches MT940 ohne DATEV-Anzeigegarantie.
- `datev_verified:<profilname>`: Profil aus `profiles/<profilname>.json` mit dokumentiert erfolgreichem Probeimport und gelöschten Testumsätzen.
- `unverified`: ausschließlich für eine Testdatei.

Keine Unterfelder wie `?00`, `?10`, `?20` oder `?32` erfinden. Strukturierte Unterfelder nur aus einer nativen Bankdatei oder einem verifizierten Profil übernehmen.

Verwendungszwecke kanonisch auf einfache Leerzeichen normalisieren und in Windows-1252 verlustfrei schreiben. Texte außerhalb der physischen Kapazität von sechs Zeilen als Klärungsfall behandeln; nie still kürzen.

### 7. Unbekanntes DATEV-Profil zuerst testen

Bei PDF, Bild oder manueller Umsatzliste mit Ziel DATEV und ohne verifiziertes Profil nur `output_scope: test` zulassen. Die Testdatei darf höchstens einen Buchungstag enthalten und muss mindestens einen langen Verwendungszweck enthalten.

Vor dem Testimport ausdrücklich bestätigen lassen:

> Für das Bankkonto und den Testzeitraum sind keine bereits importierten Bankkontoumsätze mehr vorhanden.

Für den Referenztag 01.07.2026 gelten:

```text
Anfangssaldo:      83.077,77 EUR
Umsatzsumme:       -4.139,53 EUR
Test-Endsaldo:     78.938,24 EUR
Anzahl Umsätze:             6
```

Der Dateiname lautet ohne Unterstriche:

`MT940 Test DE43300501101009524321 01.07.2026.sta`

Nach dem Probeimport prüfen und dokumentieren:

- Anfangssaldo in DATEV korrekt
- Test-Endsaldo korrekt
- Zahl und Vorzeichen der Umsätze korrekt
- Verwendungszweck vollständig, ohne fehlende Textteile
- keine sichtbaren Steuer- oder Unterfeldkennzeichen

Danach ausdrücklich anweisen:

> Die Testumsätze müssen vor dem Import der vollständigen Monatsdatei wieder aus dem DATEV-Bankbestand gelöscht werden.

Ein verifiziertes Profil erst anlegen, wenn diese Prüfungen und die anschließende Löschung dokumentiert sind. Vorher keine vollständige Monatsdatei erzeugen oder freigeben.

### 8. Datei erzeugen und Fingerprint prüfen

```bash
python scripts/build-mt940.py manifest.json
```

Das Skript erzeugt die `.sta`-Datei und eine JSON-Sidecar-Datei mit SHA-256-Fingerabdruck. Der Fingerabdruck umfasst Konto, Auszugs-/Sequenznummer, Zeitraum, Salden und alle kanonischen Umsätze in Quellreihenfolge. Ihn nie als erfundenes Bankfeld in die MT940-Datei schreiben.

Generische Monatsdatei:

`MT940 <IBAN> <TT.MM.JJJJ> bis <TT.MM.JJJJ>.sta`

Sidecar:

`MT940 Prüfung <IBAN> <TT.MM.JJJJ> bis <TT.MM.JJJJ>.json`

### 9. Unabhängig gegen das Manifest validieren

```bash
python scripts/validate-mt940.py "MT940 <IBAN> <Zeitraum>.sta" manifest.json
```

Der Validator prüft unter anderem `:20:`, IBAN, `:28C:`, beide Saldenfelder, jedes `:61:`/`:86:`-Paar, Reihenfolge, Rundlauf, Zeichensatz, CRLF, Zeilenlängen, Saldenrechnung, Profilregeln und Fingerprint.

Exit-Status:

- `0`: technisch und rechnerisch gültig
- `2`: Quelldaten oder Salden unvollständig
- `3`: Struktur- oder Zeichenfehler
- `4`: DATEV-Profil nicht verifiziert; nur Probeimport zulässig
- `5`: möglicher Doppelimport erkannt

## Freigabe und Übergabe

Je Konto `.sta`, JSON-Sidecar und eine Prüfzusammenfassung liefern:

- IBAN, Auszugsnummer und Zeitraum
- Anfangssaldodatum/-betrag, Buchungszahl/-summe, Endbestandsdatum/-betrag
- frühestes/spätestes Valuta- und Buchungsdatum
- Fingerprint und Ergebnis der technischen Validierung
- je PDF-Umsatz: Seite, Zahl der sichtbaren Quellzeilen, `source_to_manifest_match`, Textanfang, Textende und `roundtrip_match`
- PDF-basierte Datei nur freigeben, wenn f?r jeden Umsatz `source_to_manifest_match: true` und `roundtrip_match: true` ausgewiesen sind
- separater Status des DATEV-Probeimports
- offene Klärungen und Löschbestätigung für Testumsätze

Ohne dokumentierten Probeimport exakt sinngemäß formulieren:

> Technisch und rechnerisch geprüft. Die konkrete Verarbeitung und Anzeige in DATEV ist noch nicht durch einen Probeimport bestätigt. Die Datei ist daher noch nicht für den vollständigen Produktivimport freigegeben.

Ohne Probeimport niemals „DATEV-kompatibel“, „DATEV-geprüft“ oder „erfolgreich importierbar“ behaupten.

Die vollständigen Feldregeln und Profilanforderungen stehen in [technischer-aufbau.md](references/technischer-aufbau.md).
