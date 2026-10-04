# Technischer Aufbau und unterstützter Bankpfad

## Geltungsbereich

Die folgenden Regeln beschreiben den unterstützten technischen Ausschnitt. Bei fehlendem Bankmodell dienen sie als Ausgangspunkt für eine Rekonstruktion, die nach vollständigem Quellabgleich zum neuen Referenzmodell wird. Vorhandene native Bankmodelle genau anwenden. Lernablauf, Ersatzregeln und Quellenprüfung stehen in [bankreferenzmodelle.md](bankreferenzmodelle.md).

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

Originale Saldendaten erhalten. Fehlen sie bei Rekonstruktion, dokumentierte technische Periodenregeln mit `derived_fields` anwenden; der Quellprüfnachweis bleibt null. `opening_balance_date` gehört zu `:60F:`, `closing_balance_date` zu `:62F:`. Zeitraum und Saldendatum getrennt ausweisen.

Die Option `statement_reference_rule: deterministic_mt` hat folgenden technischen Aufbau:

```text
MT + JJMMTT des Auszugsendes + letzte 6 IBAN-Zeichen + zweistellige Auszugsnummer
```

Diese Regel bei Rekonstruktion als technische Exportreferenz dokumentieren. Bei `source` die vorhandene `statement_reference` übernehmen. Identische Referenzen verhindern keinen DATEV-Doppelimport.

## Buchungsfeld

Unterstützter Parserausschnitt:

```text
:61:<JJMMTT Valuta><MMTT Buchung><C oder D><Betrag><Nxxx Code><Kundenreferenz>//<Bankreferenz>
```

Der volle Buchungsdatumswert bleibt im Quellprüfbericht; in diesem Feld wird nur `MMTT` geschrieben. Abweichende Valutadaten und Jahreswechsel gegen die Quelle und den belegten Bankpfad prüfen.

Referenzbehandlung im Modell dokumentieren und vorhandene Referenzen vollständig im Text erhalten. Fehlende Referenzen bei Rekonstruktion als NONREF bzw. technische Sequenz kennzeichnen. Originale Codes erhalten; fehlt ein angezeigter Code, NMSC nur über die dokumentierte Rekonstruktionsregel einsetzen. Eine fehlende separate Valuta darf als technische Ableitung den Buchungstag verwenden; sichtbare Valutaabweichungen erhalten.

Stornosyntax, andere Kontokennungen, zusätzliche Felder oder längere native Referenzen verlangen eine Erweiterung des Bankpfads. Ein original vorhandener Wert darf nicht wegen der Werkzeuggrenze verändert werden.

## Buchungsinformation

Für neue Rekonstruktionen vollständigen Text unstrukturiert und verlustfrei schreiben und unabhängig zurücklesen. Der bank-/quellenbezogene Decoder gibt alle benannten `source_fields` aus dem tatsächlichen Text zurück. Native strukturierte Varianten nach ihrem vorhandenen Modell lesen. Rekonstruktionen mit `field86_mode: reconstructed` und eigener Referenzbasis speichern.

Die technische Textaufteilung kann für die Rekonstruktion gemeinsam verwendet werden:

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

Ein fehlender Quellnachweis oder eine Abweichung sperrt Auslieferung und Modellbestätigung. Nach Korrektur neu erzeugen und vollständig prüfen. Nach erfolgreichem Lernlauf `source_verified` speichern und die Rekonstruktion mit `delivery_approved: true` ausliefern. Technische Ableitungen sind keine bestätigten Originalwerte. Die tatsächliche DATEV-Prüfung separat mit `datev_import_verified` ausweisen. Eine ausdrücklich erzeugte Testdatei bleibt eine Testdatei.

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

Für native Varianten Originaldatei oder Bankdokumentation heranziehen. Rekonstruktionen anhand der Formatgrundlage erzeugen und das neue Modell durch den vollständigen Quelle/MT940-Abgleich bestätigen:

- [DATEV: Import von MT940-Swift-Dateien, Dokument 1030312](https://wissensplattform.apps.datev.de/help/document/1030312)
- [DATEV: elektronische Bankkontoumsätze, Dokument 1036444](https://wissensplattform.apps.datev.de/help/document/1036444)
- [SWIFT: Message Reference Guide Category 9](https://www2.swift.com/knowledgecentre/rest/v1/publications/us9m_20190719/2.0/us9m_20190719.pdf)
