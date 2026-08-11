# Technischer Aufbau einer MT940-Datei für DATEV

## Zweck und Status

MT940 ist ein zeilenorientiertes SWIFT-Format für elektronische Kontoauszüge. DATEV kann MT940-Swift-Dateien importieren. Eine formal korrekte Datei beweist jedoch weder die richtige DATEV-Anzeige bankindividueller Buchungsinformationen noch einen bereinigten DATEV-Bankbestand.

Seit dem 23. November 2025 ist MT940 kein Standard der Deutschen Kreditwirtschaft mehr; für neue Bankbereitstellungen ist `camt.053` der aktuelle DK-Standard. Wenn der Anwender ausdrücklich MT940 benötigt, nicht stillschweigend auf CAMT wechseln. Eine native Bankdatei trotzdem vor einer PDF-Rekonstruktion bevorzugen.

## Feldfolge

| Tag | Bedeutung | Pflicht | Regel |
| --- | --- | --- | --- |
| `:20:` | auszugsspezifische Referenz | ja | höchstens 16 Zeichen, deterministisch |
| `:25:` | Kontoidentifikation | ja | IBAN aus Manifest und Dateiname |
| `:28C:` | Auszugs-/Sequenznummer | ja | fünf-/dreistellig |
| `:60F:` | Anfangssaldo | ja | ausschließlich Anfangssaldodatum/-betrag |
| `:61:` | Buchungszeile | je Umsatz | exakt gegen Manifest prüfen |
| `:86:` | Buchungsinformation | je Umsatz | unmittelbar nach zugehörigem `:61:` |
| `:62F:` | Endbestand | ja | ausschließlich Endbestandsdatum/-betrag |

## Auszugsreferenz `:20:`

Schema mit maximal 16 Zeichen:

```text
MT + JJMMTT des Auszugsendes + letzte 6 IBAN-Zeichen + zweistellige Auszugsnummer
```

Beispiel:

```text
:20:MT26073152432107
```

Identische Quelldaten erzeugen immer dieselbe Referenz. Keine Zufalls-, Laufzeit- oder Chat-ID verwenden. Die Referenz verhindert keinen DATEV-Doppelimport; dafür Fingerprint und Prozesssperre verwenden.

## Auszugsnummer `:28C:`

```text
:28C:<statement_number fünfstellig>/<sequence_number dreistellig>
```

Beispiel für Auszug 7, Sequenz 1:

```text
:28C:00007/001
```

Keine feste Standardzeile in produktiven DATEV-Ausgaben verwenden.

## Saldenfelder

```text
:60F:C260630EUR83077,77
:62F:C260731EUR33444,84
```

- `C`: positiver Saldo
- `D`: negativer Saldo
- Datum: `JJMMTT`
- Betrag: Dezimalkomma, kein Tausendertrennzeichen

`opening_balance_date` ausschließlich nach `:60F:` und `closing_balance_date` ausschließlich nach `:62F:` übernehmen. Weder Datum noch Betrag des Anfangssaldos aus der ersten Buchung ableiten.

Technische Rechnung:

```text
Anfangssaldo + Summe(C-Buchungen) - Summe(D-Buchungen) = Endsaldo
```

Eine bestehende FIBU-Differenz separat klären. Keine künstliche MT940-Ausgleichsbuchung erzeugen.

## Buchungsfeld `:61:`

Beispiel:

```text
:61:2607010701D100,00NDDTVERTRAG123//000000001
```

| Bestandteil | Beispiel | Bedeutung |
| --- | --- | --- |
| Valutadatum | `260701` | 01.07.2026 |
| Buchungstag | `0701` | 01.07.; Jahr aus Valutadatum |
| Soll/Haben | `D` | Belastung; `C` ist Gutschrift |
| Betrag | `100,00` | ohne Vorzeichen |
| Code | `NDDT` | vierstelliger SWIFT-Code mit `N` |
| Kundenreferenz | `VERTRAG123` | normalisiert auf höchstens 16 Zeichen |
| Bankreferenz | `//000000001` | innerhalb des Auszugs eindeutig |

Vorhandene `EREF`, `MREF`, Rechnungs- oder Zahlungsreferenzen bevorzugen. Die vollständige Referenz zusätzlich im `:86:`-Text erhalten. `NONREF` nur verwenden, wenn die Quelle keine belastbare Referenz enthält.

Jede erzeugte `:61:`-Zeile gegen Valuta, Buchungsdatum, Betrag, Code und Referenzen des Manifests prüfen. Nicht nur die Gesamtsumme vergleichen.

## Informationsfeld `:86:`

### Verlustfreie generische Ausgabe

Kanonische Ausgangsform:

1. führende und nachfolgende Leerzeichen entfernen;
2. interne Folgen beliebiger Leerzeichen auf ein Leerzeichen reduzieren;
3. Windows-1252-Darstellbarkeit prüfen;
4. ohne Zeichenverlust an echten Positionen aufteilen.

Physische Grenzen:

- höchstens sechs Zeilen
- erste Nutztextzeile höchstens 61 Zeichen wegen des Tags `:86:`
- fünf Fortsetzungszeilen mit jeweils höchstens 65 Zeichen
- damit höchstens 386 Nutztextzeichen ohne Überschreitung der Zeilengrenzen
- keine Fortsetzungszeile mit `:` beginnen lassen

Nach dem Schreiben alle Nutztextteile wieder zusammensetzen und exakt mit der kanonischen Quelle vergleichen. Kürzungen nie still durchführen. Zu lange oder nicht darstellbare Texte als Klärungsfall mit Status `2` ausgeben.

Je Umsatz im Bericht speichern:

```text
transaction_number
source_description_length
encoded_description_length
roundtrip_match
truncated
```

### DATEV-Modi

| Modus | Bedeutung | Produktive DATEV-Freigabe |
| --- | --- | --- |
| `native` | Syntax aus elektronischer Originaldatei | nur mit unveränderter Quelle |
| `generic_unstructured` | generisches MT940 | keine Anzeigegarantie |
| `datev_verified:<profil>` | dokumentierter erfolgreicher Test | ja, für genau diese Variante |
| `unverified` | unbekannte PDF-/manuelle Variante | nur eintägige Testdatei |

Keine Unterfelder wie `?00`, `?10`, `?20` oder `?32` erfinden. Im generischen und unverifizierten Modus sind strukturierte Unterfeldkennzeichen unzulässig. In einem verifizierten Profil ausschließlich die dort erlaubten Kennzeichen verwenden.

## DATEV-Profilfixture

Eine Profil-JSON muss mindestens enthalten:

- `profile_name` und `bank_name`
- anonymisierte vollständige `:61:`-/`:86:`-Beispiele
- erwartete DATEV-Anzeige
- Zeichensatz und Zeilenumbrüche
- Datum und Ergebnis des Probeimports
- Prüfergebnisse für Anfangssaldo, Test-Endsaldo, Buchungszahl/Vorzeichen, vollständigen Verwendungszweck und Steuerzeichen
- Bestätigung, dass die Testumsätze anschließend gelöscht wurden
- Liste erlaubter strukturierter Unterfelder

`datev_verified:<profil>` nur akzeptieren, wenn alle Prüfpunkte erfolgreich und die Testumsätze gelöscht sind. Die Datei [unverified-example.json](../profiles/unverified-example.json) ist ausschließlich eine offene Vorlage und kein verifiziertes Profil.

## Technischer Fingerprint

SHA-256 über kanonisches JSON bilden aus:

- IBAN
- Auszugs- und Sequenznummer
- Auszugsbeginn/-ende
- Anfangssaldodatum/-betrag
- Endbestandsdatum/-betrag
- allen Buchungen in Quellreihenfolge mit Daten, Betrag, Code, Referenzen und kanonischem `:86:`-Text

Den Hash in der Prüfzusammenfassung und JSON-Sidecar speichern, niemals als Bankfeld. Vor jeder Erzeugung Sidecars im Ausgabeordner und aktuellen Arbeitsverzeichnis durchsuchen. Identischen Hash mit Status `5` sperren; Überschreibung nur nach dokumentierter Löschung des früheren DATEV-Imports.

## Datei- und Zeichensatzregeln

- Endung `.sta`
- Windows-1252
- ausschließlich CRLF (`0D 0A`), einschließlich Dateiende
- höchstens 65 Zeichen je physischer Zeile
- genau ein Konto je Datei
- keine Unterstriche in den Standarddateinamen

Monatsdatei:

```text
MT940 <IBAN> <TT.MM.JJJJ> bis <TT.MM.JJJJ>.sta
```

Testdatei:

```text
MT940 Test <IBAN> <TT.MM.JJJJ>.sta
```

Sidecar:

```text
MT940 Prüfung <IBAN> <TT.MM.JJJJ> bis <TT.MM.JJJJ>.json
```

## Mindestprüfung

1. `:20:` gegen das Manifest prüfen und Länge auf 16 begrenzen.
2. IBAN in Manifest, `:25:` und Dateiname vergleichen.
3. `:28C:` gegen Auszugs-/Sequenznummer prüfen.
4. `:60F:` und `:62F:` exakt gegen getrennte Saldendaten prüfen.
5. Jedes `:61:` und `:86:` in Quellreihenfolge vergleichen.
6. Zahlen der Quellumsätze, `:61:`- und `:86:`-Felder vergleichen.
7. Referenzen eindeutig halten, soweit die Quelle dies ermöglicht.
8. `:86:`-Rundlauf, Profilunterfelder und Steuerzeichen prüfen.
9. Windows-1252, ausschließlich CRLF, 65 Zeichen und sechs `:86:`-Zeilen prüfen.
10. Saldenrechnung centgenau prüfen.
11. Fingerprint ausweisen und auf Duplikate prüfen.
12. Technischen Status und DATEV-Praxistest getrennt berichten.

## Referenzfall Juli 2026

```text
:25:DE43300501101009524321
:28C:00007/001
:60F:C260630EUR83077,77
:62F:C260731EUR33444,84
transactions = 64
transaction_total = -49632.93
```

Für den Testtag 01.07.2026:

```text
opening = 83077.77
transactions = 6
transaction_total = -4139.53
closing = 78938.24
```

Ein DATEV-Anfangsbestand von `91356.83` lässt sich als `83077.77 + 4139.53 + 4139.53` erklären und ist als Mehrfachimport zu behandeln. Eine bereits bestehende FIBU-Differenz von `0.30` bleibt davon getrennt.

## Quellen

- DATEV, Dokument 1030312, Import von MT940-Swift-Dateien: https://wissensplattform.apps.datev.de/help/document/1030312
- DATEV, Dokument 1036444, elektronische Bankkontoumsätze ohne DATEV-Schnittstelle: https://wissensplattform.apps.datev.de/help/document/1036444
- SWIFT, Message Reference Guide Category 9: https://www2.swift.com/knowledgecentre/rest/v1/publications/us9m_20190719/2.0/us9m_20190719.pdf
- Deutsche Kreditwirtschaft/EBICS, Format LifeCycle: https://www.ebics.de/de/datenformate/format-lifecycle
