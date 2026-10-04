# Technischer Aufbau und unterstützter Bankpfad

## Geltungsbereich

Die folgenden Regeln beschreiben den derzeit unterstützten technischen Ausschnitt des Werkzeugs. Sie sind **kein bankübergreifendes Referenzmodell**. Vor ihrer Anwendung muss das Modell der konkreten Bankvariante deren Feldzuordnung und Ausgabeform belegen. Modellverwaltung, Textadapter und getrennte Quellenprüfung stehen in [bankreferenzmodelle.md](bankreferenzmodelle.md).

Eine nicht unterstützte Originalsyntax nicht umformen, um sie in diesen Ausschnitt zu zwingen. Den Bankpfad erweitern und anhand echter Referenzen prüfen. Technisch gültige Syntax belegt keine korrekte DATEV-Interpretation.

## Auszugsfelder

| Tag | Unterstützte Form | Quellenprüfung |
| --- | --- | --- |
| `:20:` | höchstens 16 Zeichen; Regel aus dem Bankmodell | Originalreferenz oder ausdrücklich modellierte technische Ableitung |
| `:25:` | IBAN | Originalquelle, Manifest und Dateiname |
| `:28C:` | fünfstellige Auszugs-/dreistellige Sequenznummer | beide Nummern ausdrücklich aus Quelle/Modell |
| `:60F:` | Soll/Haben, Datum, EUR, Dezimalbetrag | Anfangssaldodatum und -betrag |
| `:61:` | Valuta, Buchungstag, Soll/Haben, Betrag, Code, Referenzen | sämtliche Einzelwerte je Quellumsatz |
| `:86:` | unmittelbar nach zugehörigem `:61:` | bankindividuell dekodierter vollständiger Nutztext und Zusatzfelder |
| `:62F:` | Soll/Haben, Datum, EUR, Dezimalbetrag | Endbestandsdatum und -betrag |

Keine fehlenden Daten aus dem Zeitraum ergänzen. `opening_balance_date` gehört ausschließlich zu `:60F:`, `closing_balance_date` zu `:62F:`. `statement_start` und `statement_end` dienen der Zeitraumkontrolle und dem Dateinamen.

Die Option `statement_reference_rule: deterministic_mt` hat folgenden technischen Aufbau:

```text
MT + JJMMTT des Auszugsendes + letzte 6 IBAN-Zeichen + zweistellige Auszugsnummer
```

Diese Regel nur benutzen, wenn sie im Bankmodell ausdrücklich belegt ist. Bei `source` die vorhandene `statement_reference` übernehmen. Identische Referenzen verhindern keinen DATEV-Doppelimport.

## Buchungsfeld

Unterstützter Parserausschnitt:

```text
:61:<JJMMTT Valuta><MMTT Buchung><C oder D><Betrag><Nxxx Code><Kundenreferenz>//<Bankreferenz>
```

Der volle Buchungsdatumswert bleibt im Quellprüfbericht; in diesem Feld wird nur `MMTT` geschrieben. Abweichende Valutadaten und Jahreswechsel gegen die Quelle und den belegten Bankpfad prüfen.

Referenzen nicht global umschreiben. Die Regeln `exact`, `upper_alnum_16` und `source_or_sequence_9` müssen für diese Bankvariante dokumentiert sein. Ursprüngliche Referenzwerte bei einer belegten technischen Kürzung vollständig im Buchungstext erhalten. Der Code muss aus der Quelle oder einer dokumentierten Buchungsartzuordnung stammen; es gibt keinen Standardcode für unbekannte Fälle.

Stornosyntax, andere Kontokennungen, zusätzliche Felder oder längere native Referenzen verlangen eine Erweiterung des Bankpfads. Ein original vorhandener Wert darf nicht wegen der Werkzeuggrenze verändert werden.

## Buchungsinformation

Das Bankmodell bestimmt die tatsächliche Belegung. Ein generischer Textmodus ist gesperrt. Der Bankadapter muss die geschriebenen physischen Zeilen unabhängig wieder lesen und dabei den vollständigen Nutztext sowie alle benannten `source_fields` zurückgeben.

Die technische Textaufteilung darf gemeinsam verwendet werden, **wenn die bankbezogene Referenz sie zulässt**:

- Windows-1252 verlustfrei;
- höchstens sechs physische Zeilen mit höchstens 65 Zeichen;
- erste Textzeile wegen `:86:` höchstens 61 Zeichen;
- maximal 386 Nutzzeichen bei dieser physischen Form, bei strukturierten Feldern weniger wegen der Unterfeldkennzeichen;
- keine Fortsetzungszeile mit `:` am Anfang;
- nur die belegte Leerzeichennormalisierung, keine Wort-/Zeichenänderungen.

Nicht darstellbare oder zu lange Texte als Klärungsfall sperren. Nicht kürzen oder umformulieren. Erforderlichenfalls den belegten Bankpfad erweitern.

Bei PDF/Bild die gesamte Quellenkette prüfen:

```text
Originalseite und abgegrenzter Buchungsblock
→ alle sichtbaren Quellzeilen in Quellreihenfolge
→ unabhängig geprüfter source-review.json
→ Manifest und bankbezogener Encoder
→ geschriebene MT940-Bytes
→ bankbezogener Decoder
→ vollständiger Vergleich mit den geprüften Quellwerten
```

`source_page`, `source_description_lines` und `source_text_verified: true` sind im PDF-/Bildmanifest Pflicht. Ein vorhandenes `description` muss nach Leerzeichennormalisierung exakt mit den sichtbaren Quellzeilen übereinstimmen. Dieser Vergleich ergänzt den unabhängigen Quellvergleich; er ersetzt ihn nicht.

## Feldabnahme und Status

Der Validator verlangt einen separaten Quellprüfbericht mit den Hashes tatsächlich vorhandener Originaldateien. Anschließend liest er Salden und Buchungsfelder aus der geschriebenen MT940 ein. Der Bankdecoder ermittelt Nutztext und Zusatzfelder. Diese Werte werden je Umsatz gegen Quelle und Manifest verglichen.

Erfolgsbericht:

- tatsächlicher MT940-SHA-256, semantischer Fingerprint und ausgewähltes Bankmodell;
- vollständige Feldvergleiche mit Fundstelle, Quellwert, Manifestwert und MT940-Wert;
- Buchungszahl, Salden und Umsatzsumme;
- Textlängen, Textanfang/-ende und Rundlaufergebnisse als zusätzliche Diagnose;
- Quellenprüfergebnis und separater DATEV-Probeimportstatus;
- `delivery_approved` als explizites Freigabefeld.

Ein fehlender Quellnachweis oder eine Abweichung sperrt die Auslieferung. Nach einem fehlgeschlagenen Kommandozeilenlauf steht der Prüfbericht auf `delivery_approved: false`. Eine Testdatei erhält auch bei bestandener Feldprüfung keine Produktionsfreigabe.

## Fingerprint und Dateinamen

SHA-256 über kanonische Kontodaten, Auszugs-/Sequenznummer, Zeitraum, Salden und sämtliche Umsätze mit Daten, Betrag, Code, Referenzen und vollständigem Nutztext bilden. Benannte Zusatzfelder ebenfalls einbeziehen. Der Fingerprint beschreibt die Umsätze unabhängig vom technischen Modell und bleibt deshalb beim Modellwechsel vergleichbar. Bankmodell und Ausgabehash getrennt im Prüfbericht speichern.

Fingerprints nie als Bankfeld schreiben. Sidecars im Ausgabeordner und Arbeitsverzeichnis auf identische Fingerprints prüfen; Wiedererzeugung nur nach dokumentierter Löschung des früheren DATEV-Imports zulassen.

```text
MT940 <IBAN> <TT.MM.JJJJ> bis <TT.MM.JJJJ>.sta
MT940 Test <IBAN> <TT.MM.JJJJ>.sta
MT940 Prüfung <IBAN> <TT.MM.JJJJ> bis <TT.MM.JJJJ>.json
```

Ausgabe mit Windows-1252 und ausschließlich CRLF einschließlich Dateiende. Konto und Zeitraum in Dateiname und Inhalt abstimmen. Genau ein Konto je Datei.

## Referenzunterlagen

Für die bankbezogene Zuordnung zusätzlich die Originaldatei oder Dokumentation dieser Bank heranziehen. Die allgemeinen Unterlagen ersetzen das Bankmodell nicht:

- [DATEV: Import von MT940-Swift-Dateien, Dokument 1030312](https://wissensplattform.apps.datev.de/help/document/1030312)
- [DATEV: elektronische Bankkontoumsätze, Dokument 1036444](https://wissensplattform.apps.datev.de/help/document/1036444)
- [SWIFT: Message Reference Guide Category 9](https://www2.swift.com/knowledgecentre/rest/v1/publications/us9m_20190719/2.0/us9m_20190719.pdf)
