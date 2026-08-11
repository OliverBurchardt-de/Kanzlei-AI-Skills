# Technischer Aufbau einer MT940-Datei

## Zweck und aktueller Status

MT940 ist ein zeilenorientiertes SWIFT-Format für elektronische Kontoauszüge. DATEV beschreibt weiterhin den Import von MT940-Swift-Dateien in Rechnungswesen-Programme. Seit dem 23. November 2025 ist MT940 jedoch kein Standard der Deutschen Kreditwirtschaft mehr; für neue Bankbereitstellungen ist `camt.053` der aktuelle DK-Standard. Wenn der Anwender ausdrücklich MT940 benötigt, nicht stillschweigend auf CAMT wechseln.

## Feldfolge

| Tag | Bedeutung | Pflicht | Regel |
| --- | --- | --- | --- |
| `:20:` | Transaktionsreferenz | ja | höchstens 16 Zeichen, innerhalb der Datei eindeutig |
| `:25:` | Kontoidentifikation | ja | IBAN des ausgewerteten Kontos |
| `:28C:` | Auszugs-/Sequenznummer | ja | beispielsweise `00001/001` |
| `:60F:` | Anfangssaldo | ja | `C`/`D`, Datum `JJMMTT`, Währung, Betrag |
| `:61:` | Buchungszeile | je Umsatz | Valuta, Buchungstag, Soll/Haben, Betrag, Code, Referenz |
| `:86:` | Buchungsinformation | je Umsatz | folgt unmittelbar auf das zugehörige Feld `:61:` |
| `:62F:` | Endsaldo | ja | `C`/`D`, Datum `JJMMTT`, Währung, Betrag |

## Saldenfelder

Schema:

```text
:60F:C250101EUR1986,99
:62F:C251231EUR718,92
```

- `C`: positiver Saldo (Credit)
- `D`: negativer Saldo (Debit)
- `250101`: 1. Januar 2025 im Format `JJMMTT`
- `EUR`: Kontowährung
- `1986,99`: Betrag ohne Tausenderpunkt und mit Dezimalkomma

Der technische Prüfsatz lautet:

```text
Anfangssaldo + Summe(C-Buchungen) - Summe(D-Buchungen) = Endsaldo
```

## Buchungsfeld `:61:`

Beispiel:

```text
:61:2501020102D213,80NMSCRECHNUNG4711//000000001
```

Aufteilung:

| Bestandteil | Beispiel | Bedeutung |
| --- | --- | --- |
| Valutadatum | `250102` | 02.01.2025 |
| Buchungstag | `0102` | 02.01.; das Jahr ergibt sich aus dem Valutadatum |
| Soll/Haben | `D` | Belastung; `C` wäre Gutschrift |
| Betrag | `213,80` | ohne Vorzeichen und Tausenderpunkt |
| Code | `NMSC` | sonstige Buchung/Kartenzahlung |
| Kundenreferenz | `RECHNUNG4711` | vorhandene Quellreferenz, höchstens 16 Zeichen |
| Bankreferenz | `//000000001` | innerhalb der Datei eindeutige laufende Referenz |

Bei einer Stornobuchung nur dann den SWIFT-Reversal-Indikator verwenden, wenn die Quelle die Buchung eindeutig als Storno ausweist. Eine bloße Gutschrift ist nicht automatisch ein Storno.

Vorhandene `EREF`, `MREF`, `REF`, Rechnungs- oder Zahlungsreferenzen vorrangig übernehmen. Für das kurze Referenzfeld nur alphanumerische Zeichen verwenden und auf 16 Zeichen begrenzen. Die vollständige Originalreferenz zusätzlich in `:86:` erhalten. `NONREF` ist nur zulässig, wenn der Auszug keine belastbare Referenz enthält. Eine separate Bankreferenz nach `//` muss innerhalb der Datei eindeutig sein.

## Informationsfeld `:86:`

Das Feld enthält Empfänger/Auftraggeber, Verwendungszweck und vorhandene Referenzen. Dieses Skill-Paket verwendet ein unstrukturiertes Feld, weil bankindividuelle Unterfelder nicht verlässlich aus jedem PDF rekonstruiert werden können.

Regeln:

- insgesamt höchstens 390 Zeichen in höchstens sechs Zeilen
- höchstens 65 Zeichen je physischer Zeile
- die vier Zeichen `:86:` zählen in der ersten Zeile mit
- daher erste Nutztextzeile höchstens 61 Zeichen, folgende Zeilen höchstens 65 Zeichen
- Fortsetzungszeilen dürfen nicht mit `:` beginnen
- relevante Angaben priorisieren: Name, Gegenkonto/IBAN, Verwendungszweck, Rechnungs- oder End-to-End-Referenz
- bei unvermeidbarer Kürzung das Ende nur nach dokumentierter Priorisierung abschneiden

Beispiel:

```text
:86:Beispiel GmbH DE00123456780000000000 Rechnung 4711
Zahlungsreferenz ABC123
```

## Datei- und Zeichensatzregeln

- Dateiendung: `.sta`
- Zeichensatz: Windows-1252
- Zeilenende: CRLF (`0D 0A`)
- maximal 65 Zeichen je Zeile
- Beträge: Dezimalkomma, kein Tausendertrennzeichen
- Datei enthält genau ein Konto; mehrere Konten werden in getrennten Dateien ausgegeben

Dateiname:

```text
MT940 <IBAN> <TT.MM.JJJJ> bis <TT.MM.JJJJ>.sta
```

Der Zeitraum bezeichnet den ausgewiesenen Auszugs-/Filterzeitraum. Das früheste und späteste tatsächliche Buchungs- und Valutadatum zusätzlich in der Prüfzusammenfassung nennen.

## Anonymisiertes vollständiges Muster

```text
:20:MT94020251300
:25:DE89370400440532013000
:28C:00001/001
:60F:C250101EUR100,00
:61:2501020102D25,00NMSCRECHNUNG4711//000000001
:86:Beispielzahlung Rechnung 4711
:61:2501030103C50,00NTRFNONREF//000000002
:86:Beispielgutschrift
:62F:C251231EUR125,00
```

## Mindestprüfung vor Freigabe

1. IBAN im Auszug, Manifest, Feld `:25:` und Dateinamen vergleichen.
2. Anfangs- und Endsaldo mit Vorzeichen vergleichen.
3. Zahl der Quellbuchungen mit der Zahl der `:61:`-Felder vergleichen.
4. Sicherstellen, dass jedes `:61:` genau ein unmittelbar folgendes `:86:` hat.
5. Buchungscodes und Quellreferenzen stichprobenartig gegen den Auszug prüfen.
6. Saldenrechnung centgenau durchführen.
7. Datumsgrenzen und chronologische Reihenfolge prüfen.
8. CRLF, Windows-1252 und Zeilenlängen prüfen.
9. DATEV-Probeimport getrennt dokumentieren; technische Validierung ersetzt keinen Probeimport.

## Quellen

- DATEV, Dokument 1036444, „Elektronische Bankkontoumsätze über Bankprogramm ohne DATEV-Schnittstelle übernehmen“: https://wissensplattform.apps.datev.de/help/document/1036444
- DATEV, Dokument 1030312, Import von MT940-Swift-Dateien: https://wissensplattform.apps.datev.de/help/document/1030312
- SWIFT, Message Reference Guide Category 9, MT 940 Customer Statement: https://www2.swift.com/knowledgecentre/rest/v1/publications/us9m_20190719/2.0/us9m_20190719.pdf
- Deutsche Kreditwirtschaft/EBICS, Format LifeCycle: https://www.ebics.de/de/datenformate/format-lifecycle
