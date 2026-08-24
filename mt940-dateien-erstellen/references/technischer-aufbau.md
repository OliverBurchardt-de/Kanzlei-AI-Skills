# Technischer Aufbau institutsunabhängiger MT940-Dateien für DATEV

## Inhalt

1. Zielarchitektur
2. Kodierungsvertrag
3. Allgemeine MT940-Felder
4. Kanonisches Umsatzmodell
5. Strukturierter DATEV-Renderer für `:86:`
6. Semantischer Rundlauf
7. DATEV-Zielprofile
8. Fingerprint und Doppelimportsperre
9. Validierung und Freigabe

## 1. Zielarchitektur

Die Verarbeitung besteht aus fünf getrennten Ebenen:

```text
MT940 / CAMT / CSV / PDF / Bild / manuelle Liste
                    ↓
               Quellenleser
                    ↓
        unveränderter Quellnachweis
                    ↓
     kanonisches, institutsneutrales Modell
                    ↓
         DATEV-Zielprofil und Renderer
                    ↓
          MT940-Bytes und Validator
```

Bankname, Logo, Dateiname, IBAN-Präfix, Layoutkoordinaten und institutsspezifische Überschriften dürfen nur dem Quellenleser helfen. Sie dürfen keine Renderer- oder Profilentscheidung auslösen.

Native MT940-Felder können im Modus `native` unverändert erhalten bleiben. Rekonstruierte Quellen verwenden nach der Quellenlesung dasselbe kanonische Modell.

## 2. Kodierungsvertrag

| Verarbeitungsebene | Verbindliche Kodierung |
| --- | --- |
| Quellenlesung und internes Modell | Unicode NFC |
| Manifest, JSON-Sidecar, Markdown-Bericht | UTF-8 ohne BOM |
| DATEV-STA | Windows-1252/CP1252 ohne BOM |
| DATEV-STA-Zeilenenden | ausschließlich CRLF |

Vor dem Rendern jeden Ausgabetext mit `unicodedata.normalize("NFC", text)` normalisieren. Anschließend ausschließlich streng kodieren:

```python
payload = text.encode("cp1252", errors="strict")
```

Nicht darstellbare Zeichen führen zu einem Klärungsfall. Keine stillen Ersatzzeichen, Transliteration oder Ersetzung durch `?`, `+` oder Leerzeichen zulassen.

### Bytevertrag für DATEV

Der Generator und Validator prüfen:

- keine UTF-8-BOM `EF BB BF`
- keine UTF-16-BOM `FF FE` oder `FE FF`
- ausschließlich CRLF `0D 0A`, einschließlich Dateiende
- exakte Übereinstimmung mit den erwarteten CP1252-Bytes
- CP1252-Rücklauf zum erwarteten kanonischen MT940-Text
- keine UTF-8-Mehrbytefolgen für deutsche Sonderzeichen

Beispiel:

```text
Unicode:      Zusatzgebühren
CP1252 ü:     FC
unzulässig:   C3 BC   (UTF-8)
```

Eine bloße CP1252-Dekodierung reicht nicht als Prüfung, weil fast jede Bytefolge als CP1252 interpretierbar ist. Deshalb immer den vollständigen Rohbytevergleich gegen das kanonische Modell durchführen.

## 3. Allgemeine MT940-Felder

| Tag | Bedeutung | Regel |
| --- | --- | --- |
| `:20:` | Auszugsreferenz | deterministisch, höchstens 16 Zeichen |
| `:25:` | Konto | IBAN aus Manifest und Dateiname |
| `:28C:` | Auszugs-/Sequenznummer | fünf-/dreistellig |
| `:60F:` | Anfangssaldo | ausschließlich Anfangssaldatum und -betrag |
| `:61:` | Buchungszeile | Daten, Betrag, SWIFT-Code und Referenzen |
| `:86:` | Buchungsinformation | unmittelbar nach zugehörigem `:61:` |
| `:62F:` | Endsaldo | ausschließlich Endbestandsdatum und -betrag |

### Referenz `:20:`

```text
MT + JJMMTT des Auszugsendes + letzte sechs IBAN-Zeichen + zweistellige Auszugsnummer
```

Die Referenz ist kein Schutz gegen Doppelimporte.

### Auszugsnummer `:28C:`

```text
:28C:<statement_number fünfstellig>/<sequence_number dreistellig>
```

### Saldenfelder

```text
:60F:CJJMMTTEUR1000,00
:62F:CJJMMTTEUR750,00
```

Technische Rechnung:

```text
Anfangssaldo + Summe(C-Buchungen) - Summe(D-Buchungen) = Endsaldo
```

Keine Ausgleichsbuchung zur Kaschierung einer Differenz erzeugen.

## 4. Kanonisches Umsatzmodell

Jeder rekonstruierte Umsatz enthält mindestens:

| Feld | Bedeutung |
| --- | --- |
| `booking_date` | Buchungsdatum |
| `value_date` | Valutadatum |
| `amount` | vorzeichenbehafteter Dezimalstring |
| `currency` | derzeit `EUR` |
| `transaction_category` | institutsneutrale Kategorie |
| `booking_text` | kurzer belegter Buchungstext |
| `purpose` | vollständiger Verwendungszweck |
| `counterparty_name` | belegter Zahlungspartner oder `null` |
| `counterparty_iban` | belegte Gegen-IBAN oder `null` |
| `references` | Referenzen in Quellreihenfolge |
| `raw_source_lines` | unveränderte Originalzeilen |
| `source_page`/`source_location` | Fundstelle |
| `source_text_verified` | bestätigter Quellenabgleich |
| `field_confidence` | Konfidenz je semantischem Feld |

Zulässige Kategorien:

- `fee`
- `transfer`
- `direct_debit`
- `card`
- `cash`
- `interest`
- `other`

Konfidenzen sind `high`, `medium` oder `low`. Eine produktive DATEV-Datei erfordert `high` für Kategorie, Buchungstext, Verwendungszweck und einen vorhandenen Zahlungspartner. Unsichere Trennungen nicht erfinden; belegten Gesamttext im Verwendungszweck erhalten und Testdatei beziehungsweise Klärungsfall ausgeben.

## 5. Strukturierter DATEV-Renderer für `:86:`

Der Modus `datev_structured_v1` ist ein DATEV-Zielmodus, kein Bankprofil.

Logischer Aufbau:

```text
:86:<GVC>?00<Buchungstext>?20<Verwendungszweck>...?31<Gegenkonto>?32<Partner>?33<Partnerfortsetzung>
```

### Unterfeldbelegung

| Unterfeld | Inhalt | Einzelkapazität |
| --- | --- | --- |
| `?00` | Buchungstext | 27 Zeichen |
| `?20` bis `?29` | Verwendungszweck und Referenzen | je 27 Zeichen |
| `?31` | Gegen-IBAN | 34 Zeichen |
| `?32`, `?33` | Zahlungspartner | je 27 Zeichen |

Das konkrete Zielprofil enthält die verbindlichen Längen. Zweck und Referenzen über `?20` bis `?29`, Zahlungspartner über `?32` und `?33` verlustfrei verteilen.

Beim Verteilen:

- keine stille Kürzung
- keine Änderung der Quellreihenfolge
- kein Wort oder Referenzbestandteil an einer Unterfeldgrenze teilen
- Unterfeldkennzeichen nicht beschädigen
- Nutzwerte beim Rücklesen exakt zusammensetzen

Das Fragezeichen ist reserviert. Bei `?` im belegten Nutztext nur mit nachgewiesener zulässiger Behandlung fortfahren; andernfalls Klärungsfall.

### GVC

GVC ausschließlich aus der kanonischen `transaction_category` und der zentralen Tabelle des DATEV-Zielprofils bestimmen. Nur bei hoher Konfidenz einen spezifischen Tabellenwert verwenden. Sonst `835` setzen und `gvc_source: fallback` im Bericht ausweisen.

Nie aus Bankname, Zahlungspartner, Logo oder IBAN ableiten.

### Physische Zeilen

- höchstens 65 Zeichen je physischer Zeile
- `:86:` zählt in der ersten Zeile mit
- erste Nutztextzeile höchstens 61 Zeichen
- höchstens fünf Fortsetzungszeilen mit je 65 Zeichen
- insgesamt höchstens 386 logische Zeichen nach `:86:`
- ausschließlich CRLF

Physische Zeilenumbrüche verändern den logischen Feldinhalt nicht.

## 6. Semantischer Rundlauf

Den strukturierten Text nach der Erzeugung erneut parsen und getrennt vergleichen:

```text
?00            → booking_text
?20 bis ?29    → purpose + references
?31            → counterparty_iban
?32 und ?33    → counterparty_name
GVC            → ermittelter GVC
```

Zusätzlich Reihenfolge, Unterfeldlängen und erlaubte beziehungsweise erforderliche Felder gegen das Zielprofil prüfen. Jede Abweichung mit Status `3` abbrechen.

Der Prüfbericht weist pro Umsatz mindestens aus:

```text
transaction_number
source_page oder source_location
source_line_count
source_to_manifest_match
field86_mode
gvc
gvc_source
underfield_order
semantic_values
low_confidence_fields
roundtrip_match
truncated
```

## 7. DATEV-Zielprofile

Ein Zielprofil enthält mindestens:

- `profile_name`
- `target_system`
- `target_import_path`
- `charset`
- `line_endings`
- erlaubte und erforderliche Unterfelder
- Unterfeldlängen
- GVC-Regeln
- maximale physische Zeilenlänge und `:86:`-Zeilenzahl
- getestete Quellformate
- Datum und Ergebnis des Probeimports
- Prüfergebnisse und Löschung der Testumsätze

Ein `bank_name` ist unzulässig. Das mitgelieferte Profil `datev-mt940-structured-v1` bleibt bis zum echten DATEV-Probeimport unverifiziert.

Modi:

| Modus | Verwendung |
| --- | --- |
| `datev_structured_v1` | technisch geprüfte Testdatei |
| `datev_verified:datev-mt940-structured-v1` | erst nach echtem Probeimport |
| `native` | unveränderte native `:86:`-Syntax |
| `generic_unstructured` | generischer Alt-/Nicht-DATEV-Fall |

Automatisierte Tests dürfen ein ausdrücklich als Testfixture markiertes verifiziertes Profil verwenden. Das ist keine Produktivfreigabe.

## 8. Fingerprint und Doppelimportsperre

SHA-256 über kanonisches JSON bilden aus:

- Konto, Zeitraum, Auszugs-/Sequenznummer
- Anfangs- und Endbestandsdaten und -beträge
- allen Umsätzen in Quellreihenfolge
- Daten, Betrag, Kategorie, Buchungstext, Zweck, Referenzen, Gegenkonto und Zahlungspartner

Hash in JSON-Sidecar speichern, niemals als Bankfeld. Vor jeder Erzeugung Sidecars im Ausgabe- und Arbeitsverzeichnis suchen. Identischen Hash mit Status `5` sperren. Überschreibung nur nach bestätigter Löschung des früheren DATEV-Imports.

## 9. Validierung und Freigabe

Der Validator prüft:

1. separate Auszugs- und Saldendaten
2. jedes `:61:` gegen das kanonische Modell
3. jede strukturierte `:86:`-Semantik
4. GVC und Unterfeldprofil
5. Buchungszahl und chronologische Reihenfolge
6. eindeutige Bankreferenzen
7. centgenaue Saldenrechnung
8. maximale Feld- und Zeilenlängen
9. NFC, CP1252, BOM und CRLF
10. vollständige Rohbytegleichheit
11. Fingerprint und Doppelimportsperre
12. technischen Status getrennt vom DATEV-Praxistest

Der DATEV-Probeimport muss mindestens Sonderzeichen, langen Zahlungspartner und mehrere Referenzen enthalten. Erst nach korrekter Anzeige, dokumentierten Salden/Buchungen und Löschung der Testumsätze das Zielprofil produktiv freigeben.

## Quellen

- DATEV, Formatbeschreibung MT940-SWIFT, Dokument 9226962: https://wissensplattform.apps.datev.de/help/document/9226962
- DATEV, Import von MT940-Swift-Dateien, Dokument 1030312: https://wissensplattform.apps.datev.de/help/document/1030312
- Goldman Sachs, MT940 mit GVC und strukturiertem Feld `:86:`: https://developer.gs.com/docs/services/transaction-banking/mt940-gvc-intro/
- Holvi, MT940 account statements service description: https://holvi-developer.zendesk.com/hc/en-gb/articles/15110599182738-Holvi-SWIFT-MT-940-account-statements-service-description
