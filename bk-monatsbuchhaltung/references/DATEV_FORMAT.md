# DATEV-Format

## Verbindliche Versionen

- Header-Version: `700`
- Buchungsstapel: Kategorie `21`, Format `Buchungsstapel`, Version `13`, 125 Felder
- Debitoren/Kreditoren: Kategorie `16`, Format `Debitoren/Kreditoren`, Version `5`, 254 Felder
- Trennzeichen: Semikolon
- Zeilenende: CRLF
- Standardausgabe: Codepage 1252

Quellen:

- https://developer.datev.de/de/file-format/details/datev-format/format-description/header
- https://developer.datev.de/de/file-format/details/datev-format/format-description/booking-batch
- https://developer.datev.de/de/file-format/details/datev-format/format-description/debitorskreditors
- https://developer.datev.de/de/file-format/details/datev-format/character-set
- https://developer.datev.de/de/file-format/details/datev-format/changelog

## Header

Der EXTF-Header enthält 31 Felder. Pflichtwerte aus Live-DATEV-Daten übernehmen. Für Bewegungsdaten `Datum von`, `Datum bis`, Bezeichnung, Diktatkürzel, Buchungstyp, Rechnungslegungszweck, Festschreibung und Währung füllen. Stammdaten lassen Bewegungsdatenfelder leer.

## Buchungsstapel

Die interne Ampelfarbe wird niemals in DATEV-Dateiname oder Stapelbezeichnung ausgegeben. Je Buchungsmonat `EXTF_Buchungsstapel_<JJJJ-MM>.csv` mit Stapelbezeichnung `Buchungsstapel` (Grün und fällige Abgrenzungsauflösungen) und bei roten Vorgängen `EXTF_Klaerungsposten_<JJJJ-MM>.csv` mit Stapelbezeichnung `Klärungsposten`; der Header ist ansonsten identisch (Kategorie 21, Version 13, Datum von/bis des Monats, Festschreibung 0). Konfigurierte Stapeltypen erhalten den Suffix `_<Stapeltyp>` und die Bezeichnung aus `batch_config`; geteilte Klärungsstapel den Suffix `_02` ff. Keine Abgrenzungs-CSV-Dateien.

Vollständige 125-Feld-Folge ausgeben. Wesentliche Felder:

1. Umsatz, positiv und ohne Soll/Haben
2. Soll/Haben `S` oder `H`
3. Währung
7. Konto
8. Gegenkonto ohne BU-Schlüssel
9. BU-Schlüssel: technisch leer oder exakt vier Ziffern. Der fachlich dreistellige Schlüssel wird im EXTF-Export mit genau einer führenden Null ausgegeben, z. B. `401` → `0401`.
10. Sicher erkanntes Belegdatum `TTMM` im Buchungsstapel; im Klärungsstapel immer leer (Pflichtleerung, siehe `VALIDIERUNG.md`)
11. Bekannte Belegreferenz in Belegfeld 1, maximal 36 Zeichen; bei Rot nur bei unbekannter Referenz dokumentiert leer
14. Buchungstext, maximal 60 Zeichen; ausschließlich normaler fachlicher Text ohne interne Warn- oder Prüfhinweise
37–39. KOST1/KOST2 nur bei konfigurierten Kostenstellen (`cost_center_config`) nach Profil; Feld 39 (Kost-Menge) immer leer
115. Leistungsdatum, soweit technisch/fachlich erforderlich

### Feldübernahme beim Import

Befund vom 07.10.2026 (Mandant 12191, Stapel 08-2026/0004): DATEV hat jedes leere Kontofeld (Feld 7) mit dem Konto der vorhergehenden Zeile gefüllt; fünf rote Zeilen erschienen als vollständige, unauffällige Buchungen. Deshalb gilt die Sortierregel gegen das Schleppen leerer Felder und die Pflichtleerung des Belegdatums im Klärungsstapel (`VALIDIERUNG.md`). Ob DATEV auch Gegenkonto, BU-Schlüssel, Belegdatum oder Belegfeld 1 übernimmt, ist nicht geprüft; das Ergebnis des DATEV-Tests wird als `carry_over_result` im Testimportnachweis festgehalten.

## Debitoren/Kreditoren

Vollständige 254-Feld-Folge ausgeben. Kontonummer und Name füllen; weitere vorhandene Werte übernehmen. Es existieren zehn Bankgruppen:

- Bank 1: Felder 41–51
- Bank 2: Felder 52–62
- Bank 3: Felder 63–73
- Bank 4: Felder 74–84
- Bank 5: Felder 85–95
- Bank 6: Felder 165–175
- Bank 7: Felder 176–186
- Bank 8: Felder 187–197
- Bank 9: Felder 198–208
- Bank 10: Felder 209–219

Je Gruppe stehen unter anderem Bankleitzahl, Bankbezeichnung, Kontonummer, Länderkennzeichen, IBAN, SWIFT/BIC, abweichender Kontoinhaber, Hauptbankkennzeichen und Gültigkeitsdaten zur Verfügung.

## Belegtransfer

DATEV XML-Schnittstelle online Version 6.0 und die im Skill gebündelten aktuellen `Document_v060.xsd` und `Document_types_v060.xsd` verwenden:

- https://developer.datev.de/de/file-format/details/datev-xml-interface-online/getting-started-
- https://developer.datev.de/de/file-format/details/datev-xml-interface-online/format-specification-/administrative-data-file
- https://developer.datev.de/de/file-format/details/datev-xml-interface-online/xsdminusfiles

`01_DATEV_Import/` enthält neben den EXTF-Importdateien keine losen Belege, sondern ein oder mehrere eigenständige DATEV-Document-Packages:

```text
Belegtransfer_<Mandant>_<JJJJ-MM>_<NNN>.zip
├── document.xml
├── <technischer ASCII-Belegname 1>
└── <technischer ASCII-Belegname n>
```

Verbindliche Regeln:

- `document.xml` heißt exakt so, liegt genau einmal direkt im ZIP-Stamm und verwendet Namespace `http://xml.datev.de/bedi/tps/document/v06.0`, Version `6.0` und UTF-8.
- Belegdateien liegen ebenfalls direkt im ZIP-Stamm; Unterordner sind unzulässig.
- Jeder Buchungsbeleg ist genau eine eigene PDF-Datei im Paket (Belegdateiregel): keine Sammel-PDF mit mehreren Buchungsbelegen, kein auf mehrere Dateien verteilter Buchungsbeleg, keine Bild- oder Textdatei als Buchungsbeleg; Sammel-PDFs werden vorher mit `scripts/beleg_pdf.py split` getrennt, Teildateien mit `merge` zusammengeführt, Bilder mit `convert` umgewandelt. Zahlungsavise dürfen weitere zulässige Dateitypen haben; Begleitdokumente werden nicht als eigener DATEV-Beleg übertragen, sondern bei Bedarf in die Beleg-PDF zusammengeführt.
- Jede Belegdatei erhält in `document.xml` genau ein `document` mit RFC-4122-GUID, `processID="1"` und einer `extension xsi:type="File"` mit identischem Dateinamen. Das optionale `document`-Attribut `type` wird in diesem Skill weggelassen; falls es in einem fremden Paket vorhanden ist, sind ausschließlich `1` für Rechnungseingang oder `2` für Rechnungsausgang zulässig.
- `accountsPayableLedger` niemals als Wert des `document`-Attributs `type` oder als Extension in diesen Belegbildpaketen verwenden. Es bezeichnet den gesonderten Import strukturierter Rechnungseingangsdaten und gehört nicht zum hier verwendeten File-only-Belegtransfer mit anschließendem EXTF-Buchungsstapel.
- Dieselbe GUID wird in jeder zugehörigen EXTF-Buchungszeile in Feld 20 `Beleglink` als `BEDI "GUID"` ausgegeben.
- Belegtransfer-Pakete werden anhand der unkomprimierten Größe bei ungefähr 100 MB oder spätestens 4.999 Dokumenten geteilt. Absolute Paketgrenze: 465 MB; Einzeldateigrenze: 20 MB.
- Jedes Belegtransfer-Paket enthält ausschließlich Belege genau einer Belegperiode. Der Zeitraum im Dateinamen ist die tatsächliche Belegperiode, nicht pauschal der angeforderte Buchungsmonat.
- Ausdrücklich über `scope` freigegebene Vorjahresbelege werden je Belegperiode in ein eigenes Uploadpaket `Belegtransfer_<Mandant>_<Belegperiode>_<NNN>.zip` ausgesteuert und niemals mit Belegen einer anderen Periode gemischt. Die laufende Paketnummer beginnt je Periode bei `001`.
- Der technische Belegindex gehört ausschließlich nach `03_Technische_Protokolle/` und niemals in das DATEV-Document-Package.
- Belegbilder zuerst nach DATEV Unternehmen online übertragen, danach die EXTF-Buchungsstapel einlesen.

Ohne erfolgreiche XSD-, ZIP- und GUID-Konsistenzprüfung ist das Paket nicht importfreigegeben.

## Pilotpflicht

Feldschema und Generator technisch validieren, anschließend echte Importdateien in einem Pilotmandanten prüfen. Eine vom Nutzer bereitgestellte erfolgreiche DATEV-Export-/Importdatei dient als Golden Sample für Headerkonventionen, vollständige Stammdatensätze und mehrere Banken.
