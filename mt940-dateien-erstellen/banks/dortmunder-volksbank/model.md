# Dortmunder Volksbank: Kontokorrent-EUR-PDF 2025

## Geltung und Status

Nur Dortmunder Volksbank eG, BLZ 44160014, BIC GENODEM1DOR, beobachtete
Kontokorrent-EUR-PDF-Vorlage 2025. Nicht auf andere Volksbanken oder native Exporte
übertragen. Modell-ID: `dortmunder-volksbank-pdf-2025-v3`.

Rekonstruktionsmodell, kein natives Volksbank-MT940-Muster. Diese öffentliche
Fassung enthält ausschließlich frei erfundene Testdaten in `reference-input.json`,
`reference-expected.json` und `reference.sta`. Keine echten Mandanten, Konten,
Beträge, Rechnungsreferenzen oder Originaldatei-Hashes sind als Beispiele enthalten.
Die synthetische Referenz wurde technisch geprüft, aber nicht in DATEV abgenommen.
Die private Praxisbestätigung einer echten Datei wird nicht auf diese Referenz übertragen.

## Bankeigene Quellenlesung

PDF-Merkmale: Banküberschrift, Kontokorrent/EUR-Konto, IBAN/BIC, Auszug Nr. n/Jahr,
Blatt x von y und Spalten `Bu-Tag | Wert | Vorgang | Betrag H/S`.

- Alle Blätter erfassen. `Übertrag auf/von Blatt` ist kein Umsatz; auf der nächsten
  Seite weiterzählen. Gebührenanlagen erläutern bereits gebuchte Abschlüsse.
- Dateiname/Druckdatum nicht mit Buchungsmonat gleichsetzen. Der im Juli
  gespeicherte Juni-Auszug gehört nach seinem Inhalt zum Juni.
- Vorgang aus der Kopfzeile; darunter vollständigen Namen und Zweck lesen.
  Mehrzeilige Namen nicht auf die erste Zeile begrenzen.
- `Abschluss lt. Anlage 1` als eigene Belastung erfassen, Anlage nicht doppelt.
  Ohne Gegenpartei keinen erfundenen Empfänger einsetzen.
- Herkunftszeilen bewahren. Je Zeilengrenze Leerzeichen oder direkte Verbindung
  festlegen: `Sec`+`ureGo`, `IBA`+`N:`, geteilte IBAN/BIC direkt verbinden.
  Keine globale Wortverklebung. Ligaturen/OCR-Lücken am gerenderten PDF prüfen.
- Automatische Extraktion darf `source_reviewed` nicht setzen.
- Buchungstag und Valuta getrennt bewahren, auch über Monatsenden.
  Unmögliche Quelldaten nicht still korrigieren: belegte Korrektur mit
  Ursprung, Grund und Bestätigungsart dokumentieren, sonst Klärungsfall.
- Ein nur hergeleitetes Anfangssaldodatum nicht als gedruckten Wert behaupten.

## Feldbelegung dieser Rekonstruktion

`:86:` beginnt mit dreistelligem GVC, danach `?00` für den Vorgang,
`?20`–`?29` für den Zweck und `?32`/`?33` für den Namen.
Je Unterfeld höchstens 27 Zeichen. Keine Fortsetzung in erfundene Nachbarfelder.

IBAN/BIC und Referenzen vollständig im originalnahen Zweck belassen.
`?30`/`?31` nicht zweckentfremden; ihre native Dortmunder Belegung ist ohne
Originalexport nicht belegt. Keine EREF/MREF/Bankreferenz erfinden.
`:61:` benutzt `NONREF` bei fehlender Originalreferenz; die technische
Buchungs-ID bleibt im Bericht.

GVC je Umsatz in `classification_basis` begründen: 051 Gutschrift,
020 Überweisungsauftrag, 118 Echtzeitüberweisung, 805 Abschluss.
835 nur für ausdrücklich geprüfte sonstige Fälle (Entgelt/Auslagen,
Geschäftsanteilbelastung oder girocard), deren nativer GVC im PDF fehlt.
Das sind technische Zuordnungen, keine behaupteten nativen Bankcodes.
Unbekannte Fälle nicht automatisch als 835 einstufen.

Keine Kürzung langer Namen/Zwecke. Modellgrenzen: Name 54, Zweck 270 Zeichen;
höchstens sechs physische Zeilen zu je 65 Zeichen einschließlich `:86:`.
Überschreitungen erfordern eine belegte bankeigene Erweiterung.
OEM/CP850, CRLF, kein BOM. Umlaute erhalten, nicht transliterieren oder löschen.
Der konkrete DATEV-Rückexport zeigte bei Windows-1252 reproduzierbar
`ä` → `õ` und `ü` → `³`. Die CP850-Fassung wurde anschließend vom Nutzer bestätigt.
Diese Kodierung nicht auf andere Banken oder ungeprüfte Importwege übertragen.

Eine Gesamtdatei enthält mehrere vollständige Auszugsblöcke
`:20: :25: :28C: :60F: (:61: :86:)* :62F: -`.
Originalnummern und Salden bewahren. `:20:` ist eine technische Referenz,
keine behauptete Bankreferenz. Kein künstlicher Jahresauszug.

## Schema und Ausführung

`reference-input.json` beschreibt die vollständige Eingabe.
`reference.sta` ist die feste Byte-Referenz.
`reference-expected.json` enthält unabhängig festgelegte decodierte Sollwerte.
`encode.py` und `decode.py` sind bankeigene, voneinander unabhängige Programme.
Der öffentliche Prüfer meldet den DATEV-Importstatus immer als `not_verified`.
Eine spätere Praxisabnahme gehört zur konkreten erzeugten Datei und wird außerhalb
des öffentlichen Repositorys dokumentiert.

Bei PDF-Eingaben je Umsatz zusätzlich `source_page`, `source_lines`,
`source_joiners` (je Grenze nur `""` oder `" "`) und
`source_reviewed: true` nach Sichtprüfung erfassen.
Verbundene Zeilen müssen exakt Name und Zweck wiedergeben; bei reinem Abschluss
ohne Detailzeilen ist die Liste leer, der Vorgang bleibt vollständig in `?00`.
Kontrollzählung und Kontrollsummen je Auszug sowie Monatsanzahl aus der Quelle
festhalten. Pflichtangaben nicht aus der Ausgabe rückwärts als bestätigt setzen.
Bei PDF-Quellen in jedem Eintrag der `source_inventory` außerdem
`source_file`, `source_file_sha256`, `page_count` und `reviewed_pages`
(sämtliche Seitennummern von 1 bis zur letzten Seite) erfassen.

```bash
python3 scripts/build-mt940.py banks/dortmunder-volksbank/reference-input.json /tmp/Volksbank-Referenz.sta
python3 scripts/validate-mt940.py banks/dortmunder-volksbank/reference-input.json /tmp/Volksbank-Referenz.sta
python3 -m unittest discover -s tests -v
```

Die Referenz niemals während eines Tests überschreiben. DATEV-Status bleibt
unabhängig vom Ergebnis technischer Tests.

## Fehlerbilder und Quellen

v1 ist gesperrt: fehlender GVC und falsche Feldrollen können sichtbares `?20`
und abgeschnittene Texte verursachen. v2 ist wegen der beim beobachteten Importweg
falsch gelesenen CP1252-Kodierung gesperrt.
Beschädigte Doppeleinträge mit GVC 000 und von DATEV erzeugte Lückenpositionen
mit GVC 079 können sich saldieren. Ein richtiger Endsaldo allein belegt daher
keine Vollständigkeit oder Dublettenfreiheit. DATEV-Lückenpositionen niemals als
Quellumsätze übernehmen. Eine neue Datei entfernt keine bestehenden Fehlimporte;
keine weiteren Ausgleichsumsätze erfinden.

Banklayoutquelle: geprüfte Kontokorrent-EUR-PDFs dieser Bankvariante.
Mandantenbelege und die private Praxisabnahme werden nicht veröffentlicht.
Native Bankcodes bleiben unbekannt.

[Omikron-Formatspezifikation, 11/2003, S. 8–9 und 12–15](https://www.national-bank.de/fileadmin/user_upload/Service/Electronic_Banking_Center/swift_mt940.pdf)
belegt GVC-Präfix, Feldrollen und klassische Codes, nicht die DATEV-Abnahme.
[UniCredit-GVC-Liste](https://www.hypovereinsbank.de/content/dam/hypovereinsbank/unternehmen/pdf/Downloadcenter/SEPA-Geschaeftsvorfallcodes-Rueckgabecodes-de.pdf)
belegt den technischen Code 118, nicht die native Dortmunder Zuordnung.
[Atruvia-Exportanleitung](https://atruvia.scene7.com/is/content/atruvia/OnlineBanking%20Ums%C3%A4tze%20exportieren%20%28MT940%2C%20CSV%20oder%20PDF%29pdf)
beschreibt einen Beschaffungsweg; daraus wurde kein Originalexport abgeleitet.
