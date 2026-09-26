---
name: bk-datev-export
description: >
  Erstellt und validiert DATEV-EXTF-Buchungsstapel sowie DATEV-Belegtransfer-Pakete
  mit document.xml, PDF-Belegen und BEDI-GUID-Verknüpfung. Der Skill nutzt vor der Erstellung den Klardaten-MCP für mandantenspezifische DATEV-Daten. Verwenden, wenn Buchungen
  für den DATEV-Import erzeugt, korrigiert oder mit Belegen verknüpft werden sollen.
version: 1.1.0
language: de
---

# B&K DATEV Export

## Zweck

Dieser Skill erzeugt technisch konsistente DATEV-Ausgabepakete aus:

- einem oder mehreren Buchungssätzen,
- den zugehörigen Belegdateien,
- Beraternummer, Mandantennummer und Wirtschaftsjahr,
- optionalen Kontierungsmerkmalen wie BU-Schlüssel, KOST1 und Belegfeld.

Der Skill trennt zwei Importwege:

1. **DATEV Belegtransfer:** ZIP mit `document.xml` und Belegdateien.
2. **DATEV Kanzlei-Rechnungswesen:** EXTF-Buchungsstapel als CSV.

Beide Dateien werden über identische GUIDs verknüpft.

---

## Wann der Skill zwingend zu verwenden ist

Verwende diesen Skill bei jeder Aufgabe, die mindestens eines der folgenden Ergebnisse verlangt:

- DATEV-Buchungsstapel,
- EXTF-Datei,
- Belegtransfer-Paket,
- `document.xml`,
- PDF-/Buchungsverknüpfung,
- Korrektur eines DATEV-Parser- oder Importfehlers,
- automatisierte Abschlussbuchungen mit Belegnachweis.

---

## Erforderliche Eingaben

Der Skill benötigt vor der Erzeugung:

```yaml
beraternummer: string
mandantennummer: string
wirtschaftsjahresbeginn: YYYYMMDD
sachkontenlaenge: integer
datum_von: YYYYMMDD
datum_bis: YYYYMMDD
stapelbezeichnung: string
buchungen:
  - betrag: decimal
    soll_haben: S|H
    konto: string
    gegenkonto: string
    belegdatum: DDMM
    buchungstext: string
    beleglink_guid: uuid
belege:
  - dateipfad: string
    dateiname_im_zip: string
    guid: uuid
    belegtyp: 1|2
```

Fehlende Werte dürfen nicht erfunden werden. Insbesondere sind Beraternummer, Mandantennummer, Sachkontenlänge und Wirtschaftsjahr vor der Erstellung zu bestätigen oder aus belastbaren Stammdaten zu beziehen.

---

## Workflow

### Schritt 1 – Fachliche Buchungslogik prüfen

Vor der technischen Dateierstellung:

1. Sollwert und bereits gebuchten Bestand unterscheiden.
2. Nur die erforderliche Differenz buchen.
3. Buchungsrichtung aus der Differenz ableiten.
4. Gegenkonto anhand des Mandantenkontenplans bestimmen.
5. Keine Vollbuchung erzeugen, wenn ein EB- oder Vorjahresbestand vorhanden ist.

### Schritt 2 – GUIDs fest vergeben

- Jeder Beleg erhält genau eine UUID.
- Die GUID wird einmal erzeugt und danach nicht mehr verändert.
- Dieselbe GUID steht:
  - im Attribut `document@ guid` der `document.xml`,
  - im EXTF-Feld `Beleglink` als `BEDI "<GUID>"`.

### Schritt 3 – Belegtransfer-Paket erzeugen

Das ZIP enthält im Stammverzeichnis:

```text
belege.zip
├── document.xml
├── beleg_001.pdf
├── beleg_002.pdf
└── ...
```

Keine Unterordner verwenden, solange diese nicht separat erfolgreich getestet wurden.

### Schritt 4 – EXTF-Buchungsstapel erzeugen

- Kodierung: Windows-1252 / CP1252.
- Trennzeichen: Semikolon.
- Felder vollständig in doppelte Anführungszeichen setzen.
- Dezimaltrennzeichen: Komma.
- Zeilenende: CRLF.
- Der Kopfsatz muss exakt 31 Felder besitzen.
- Die Buchungszeilen müssen zur verwendeten DATEV-Formatversion passen.
- Für produktive Standardstapel ist die bekannte 125-Spalten-Struktur zu verwenden, sofern eine bestehende Kanzleivorlage zugrunde liegt.

### Schritt 5 – Vorabvalidierung

Ein Paket darf erst ausgegeben werden, wenn alle Prüfungen erfolgreich sind:

- ZIP lesbar und ohne CRC-Fehler,
- `document.xml` wohlgeformt,
- Root-Element und Namespace korrekt,
- vollständiger Zeitstempel,
- alle GUIDs formal gültig und eindeutig,
- jeder XML-Dateiname existiert im ZIP,
- jede EXTF-GUID existiert in `document.xml`,
- kein nicht referenzierter Beleg,
- EXTF-Kopfsatz hat 31 Felder,
- `Datum von` ist nicht größer als `Datum bis`,
- Wirtschaftsjahresbeginn, Zeitraum und Belegdatum sind plausibel,
- Berater- und Mandantennummer stehen an den richtigen Feldpositionen.

---

## DATEV-EXTF-Kopfsatz: verbindliche Feldpositionen

| Nr. | Inhalt | Beispiel |
|---:|---|---|
| 1 | Kennung | `EXTF` |
| 2 | Versionsnummer | `700` |
| 3 | Datenkategorie | `21` |
| 4 | Formatname | `Buchungsstapel` |
| 5 | Formatversion | `12` |
| 6 | Erzeugt am | `YYYYMMDDHHMMSSmmm` |
| 7 | Importiert am | leer |
| 8 | Herkunft | leer oder bestätigt |
| 9 | Exportiert von | leer oder bestätigt |
| 10 | Importiert von | leer |
| 11 | Beraternummer | z. B. `413885` |
| 12 | Mandantennummer | z. B. `13402` |
| 13 | Wirtschaftsjahresbeginn | `20250101` |
| 14 | Sachkontenlänge | z. B. `4` |
| 15 | Datum von | `20250101` |
| 16 | Datum bis | `20251231` |
| 17 | Stapelbezeichnung | Text |
| 18 | Diktatkürzel | optional |
| 19 | Buchungstyp | regelmäßig `1` |
| 20 | Rechnungslegungszweck | regelmäßig `0` |
| 21–31 | optionale Vorlauffelder | nur befüllen, wenn bestätigt |

### Kritische Regel

Beraternummer und Mandantennummer dürfen nicht in Feld 10 und 11 stehen. Eine Verschiebung um nur eine Spalte verfälscht alle nachfolgenden Datumsfelder und kann zu `#REW04403` führen.

---

## Beleglink

Der Beleglink lautet exakt:

```text
BEDI "06bcd671-98dd-401f-933a-c01d59242b63"
```

Falsch sind insbesondere:

```text
dateiname.pdf
06bcd671-98dd-401f-933a-c01d59242b63
BEDI 06bcd671-98dd-401f-933a-c01d59242b63
```

---

## Verbindliche `document.xml`

Verwende das Schema v04.0, solange keine andere Version produktiv getestet wurde.

```xml
<?xml version="1.0" encoding="utf-8"?>
<archive xmlns="http://xml.datev.de/bedi/tps/document/v04.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         version="4.0"
         xsi:schemaLocation="http://xml.datev.de/bedi/tps/document/v04.0 document_v040.xsd">
  <header>
    <date>2026-07-22T13:00:00</date>
    <description>Beschreibung des Belegpakets</description>
  </header>
  <content>
    <document processID="1"
              guid="06bcd671-98dd-401f-933a-c01d59242b63"
              type="1">
      <extension xsi:type="File" name="beleg.pdf"/>
    </document>
  </content>
</archive>
```

### Harte XML-Regeln

- Root-Element: `archive`.
- Namespace: `http://xml.datev.de/bedi/tps/document/v04.0`.
- `archive@version`: `4.0`.
- Keine frei erfundenen Attribute wie `generatingSystemVersion`.
- `<date>` enthält `YYYY-MM-DDTHH:MM:SS`, nicht nur ein Datum.
- `extension@name` stimmt exakt mit dem ZIP-Dateinamen überein.
- XML-Sonderzeichen werden durch eine XML-Bibliothek escaped.
- Belegtyp:
  - `1`: Rechnungseingang,
  - `2`: Rechnungsausgang.
  Andere Dokumentarten nur nach separatem Test.

---

## Fehlerdiagnose

### Parserfehler: XML-Daten passen nicht zur Extension

Prüfen:

1. Root-Element ist `archive`, nicht `documentPackage`.
2. Namespace und Schema-Version stimmen.
3. `xsi:type="File"` ist gesetzt.
4. PDF-Dateiname entspricht exakt einem ZIP-Eintrag.
5. Es gibt keine nicht erlaubten Attribute.

### `#REW04403 – Datum von ist größer als Datum bis`

Prüfen:

1. Kopfsatz exakt 31 Felder.
2. Beraternummer in Feld 11.
3. Mandantennummer in Feld 12.
4. WJ-Beginn in Feld 13.
5. Sachkontenlänge in Feld 14.
6. Datum von in Feld 15.
7. Datum bis in Feld 16.
8. Datumsformat jeweils `YYYYMMDD`.

### Beleglink öffnet keinen Beleg

Prüfen:

1. EXTF-Beleglink lautet exakt `BEDI "<GUID>"`.
2. GUID in EXTF und XML stimmen zeichengetreu.
3. Der Belegtransfer wurde vor dem Buchungsstapel erfolgreich verarbeitet.
4. Es wurde nicht nachträglich eine neue GUID erzeugt.

---

---

## Klardaten-MCP / DATEV-Datenbeschaffung

### Grundsatz

Vor der Erstellung eines DATEV-Buchungsstapels soll der Skill den **Klardaten-MCP**
verwenden, sofern der Connector im aktuellen Lauf verfügbar ist. Ziel ist, alle
mandantenspezifischen Werte direkt aus DATEV zu beziehen, statt Standardkonten,
Vorjahreswerte oder Salden zu unterstellen.

Der Klardaten-MCP ist insbesondere zu verwenden für:

- eindeutige Identifikation des Mandanten,
- Ermittlung des verfügbaren Wirtschaftsjahres,
- Abruf des mandantenspezifischen Kontenplans,
- Abruf von Summen- und Saldenlisten,
- Abruf von Kontenblättern und Einzelbuchungen,
- Ermittlung von EB-Salden,
- Prüfung vorhandener Jahresabschlussbuchungen,
- Prüfung von KOST1/KOST2 und weiteren Kontierungsmerkmalen,
- Ermittlung bereits verwendeter Gegenkonten und Buchungsschlüssel,
- Plausibilisierung, ob eine Voll- oder Differenzbuchung erforderlich ist.

### Verbindlicher Abrufablauf

Der Skill arbeitet in dieser Reihenfolge:

1. **Mandant auflösen**
   - Mandant nicht anhand einer vermuteten GUID ansprechen.
   - Zuerst die DATEV-Mandantenliste über Klardaten abrufen.
   - Mandant anhand von Mandantennummer und Firmenname eindeutig identifizieren.
   - Bei mehreren Treffern nicht raten, sondern den Benutzer um Bestätigung bitten.

2. **Wirtschaftsjahr auflösen**
   - Verfügbare Wirtschaftsjahre für den Mandanten abrufen.
   - Das benötigte Wirtschaftsjahr anhand des Bilanzstichtags auswählen.
   - Keine `fiscalYearId` erfinden.

3. **Kontenplan prüfen**
   - Mandantenspezifische Sachkonten und Kontenbezeichnungen abrufen.
   - Soll- und Gegenkonto nicht allein aus einem Standard-SKR ableiten.
   - Bestehende individuelle Kontenbezeichnungen und Kontenlängen berücksichtigen.

4. **Salden und EB-Werte prüfen**
   - Für Bilanz- und Bestandskonten mindestens folgende Werte ermitteln:
     - EB-Saldo,
     - laufender Jahresverkehr,
     - aktueller Saldo,
     - bereits vorhandene Abschlussbuchungen.
   - Wenn eine Summen- und Saldenliste den EB-Saldo nicht separat zeigt, zusätzlich
     Kontenblatt oder Einzelbuchungen abrufen.
   - Ein leeres Monatsfeld darf nicht automatisch als Saldo 0,00 EUR interpretiert werden.

5. **Differenzbuchung berechnen**
   - `Buchungsbetrag = Sollwert zum Stichtag - bereits gebuchter Endbestand`.
   - Positive und negative Differenzen führen zu unterschiedlichen Buchungsrichtungen.
   - Vor der Ausgabe den rechnerischen Endbestand nach Buchung kontrollieren.

6. **Kontierungsmerkmale prüfen**
   - BU-Schlüssel, KOST1, KOST2, Belegfeld und weitere Pflichtfelder anhand der
     bisherigen Mandantenbuchungen oder dokumentierter Kanzleivorgaben bestimmen.
   - Leistungsdatum nicht verwenden, sofern es nicht ausdrücklich freigegeben ist.
   - Umbuchungsschlüssel 900/901 verwenden, wenn die mandantenspezifische
     Kanzleilogik einen Umbuchungsschlüssel verlangt.

### Bevorzugte DATEV-Ressourcen

Je nach verfügbarer Klardaten-Schnittstelle sind bevorzugt zu verwenden:

```text
Mandanten:
- datev://accounting/clients

Wirtschaftsjahre:
- datev://accounting/fiscal_years

Kontenplan:
- datev://accounting/general_ledger_accounts

Summen und Salden:
- datev://accounting/accounting_sums_and_balances

Kontenblätter / Einzelbuchungen:
- datev://accounting/account_postings
- datev://accounting/accounting_records

Verarbeitete Buchungsstapel:
- datev://accounting/accounting_sequences_processed
```

Die tatsächlichen Pflichtparameter und Filter sind vor dem Abruf über die
Klardaten-Beschreibung der jeweiligen Ressource zu prüfen.

### Dokumentation der Datenherkunft

Das Arbeitspapier muss für jeden aus DATEV übernommenen Wert dokumentieren:

- Mandant,
- Wirtschaftsjahr,
- Konto,
- Kontobezeichnung,
- EB-Saldo,
- Saldo vor Abschlussbuchung,
- Datenquelle innerhalb des Klardaten-MCP,
- Abrufdatum,
- gegebenenfalls Filter oder Zeitraum.

Beispiel:

```yaml
datev_nachweis:
  mandant: "Heydo Apparatebau GmbH"
  mandantennummer: "13402"
  wirtschaftsjahr: "2025"
  konto: "3970"
  kontobezeichnung: "Bestand Roh-, Hilfs- und Betriebsstoffe"
  eb_saldo: 168437.12
  saldo_vor_abschluss: 168437.12
  quelle: "Klardaten-MCP / DATEV Kontenblatt"
  abgerufen_am: "2026-07-22"
```

### Verhalten bei nicht verfügbarem Connector

Ist der Klardaten-MCP im aktuellen Lauf nicht verfügbar:

1. Der Skill meldet ausdrücklich, dass keine direkte DATEV-Abfrage möglich war.
2. Er verwendet nur Werte, die der Benutzer oder eine belastbare Mandantenunterlage
   eindeutig bereitgestellt hat.
3. Er kennzeichnet diese Werte im Arbeitspapier als Benutzerangabe oder externe Quelle.
4. Er darf keine EB-Salden, Konten, Gegenkonten oder Buchungsschlüssel schätzen.
5. Fehlen entscheidende Daten, wird kein produktiver Buchungsstapel erstellt.
6. Ein Entwurf darf nur klar als **nicht importfähig / noch zu prüfen** ausgegeben werden.

### Konfliktregel

Weichen Benutzerangabe, Mandantenunterlage und DATEV-Daten voneinander ab:

- DATEV-Daten nicht ungeprüft überschreiben.
- Abweichung im Arbeitspapier darstellen.
- Sachverhalt zur Freigabe vorlegen.
- Produktive Datei erst nach Auflösung des Konflikts erzeugen.

## Ausgabe

Der Skill liefert mindestens:

```text
EXTF_<Mandant>_<Zeitraum>.csv
belege_<Mandant>_<Zeitraum>.zip
Pruefprotokoll_<Mandant>_<Zeitraum>.txt
```

Optional:

```text
Arbeitspapier_<Mandant>_<Zeitraum>.xlsx
Gesamtdokumentation_<Mandant>_<Zeitraum>.pdf
```

Das Prüfprotokoll muss die Feldpositionen des Kopfsatzes, die GUID-Mengen und das Ergebnis jeder technischen Prüfung enthalten.

---

## Sicherheitsregeln

- Niemals Werte, Konten, Beraternummern oder Mandantennummern erfinden.
- Niemals eine technisch nicht getestete XML-Variante als DATEV-kompatibel bezeichnen.
- Frühere fehlerhafte Dateien klar als nicht zu verwenden markieren.
- Produktivimport erst nach Testimport und Sichtprüfung.
- Bei Abweichungen zwischen Kontenplan, Vorjahresbestand und Sollwert Rückfrage oder Prüffall statt Schätzung.
