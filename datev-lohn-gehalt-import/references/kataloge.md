# DATEV-Kataloge für die Dateierstellung

Die vom Nutzer bereitgestellten Originale sind zusammen mit Textauszügen und strukturierten JSON-Katalogen in `references/kataloge/` enthalten:

| Katalog | Dokumentstand | JSON |
| --- | --- | --- |
| Ausfallschlüssel, DATEV 9222265 | 30.12.2025 | [ausfallschluessel.json](kataloge/ausfallschluessel.json) |
| Standardlohnarten, DATEV 9226266 | 11.06.2026 | [standardlohnarten.json](kataloge/standardlohnarten.json) |
| Baulohnarten, DATEV 9225689 | 06.08.2026 | [baulohnarten.json](kataloge/baulohnarten.json) |

Jeder Eintrag enthält den Schlüssel, die Bezeichnung, PDF-Seite und unveränderte Originalzellen. Der Katalogkopf nennt die Quell-PDF, deren SHA-256 und die Anzahl der Einträge. Zeilenumbrüche in Textzellen sind bewusst erhalten; sie können mitten im Wort liegen. Bei einer fachlichen Unklarheit die zugehörige PDF-Seite lesen, nicht aus getrennten Textfragmenten eine neue Bezeichnung erfinden.

Die numerischen Schlüssel werden aus ihrer Tabellenspalte rekonstruiert. In der Baulohn-PDF ist beispielsweise `8000` auf zwei Zeilen verteilt. Die neuen Lohnarten 8380-8384 tragen zusätzlich den Hinweis **ab Version 16.1**; er ist als eigene Eigenschaft erhalten. Der Konverter verlangt bei diesen Lohnarten eine entsprechende `datev_version`.

Ausfallschlüssel werden gegen den Katalog geprüft, einschließlich **EÜ**. Die Einträge KS, KT und KV sind ausdrücklich nur bis einschließlich März 2021 erfassbar. Andere historische Gültigkeitsgrenzen sind nicht vollständig in diesen Momentaufnahmen beschrieben. Für historische Korrekturen die damals gültigen Zuordnungen zusätzlich aus dem Mandanten bzw. der passenden Dokumentation prüfen.

## Anwendung auf einen Mandanten

Die Standardtabellen beschreiben Funktionen und Merkmale; sie ersetzen nicht die Lohnartenkonfiguration im Zielmandanten. Den Mandantenkatalog nach [MCP-Ablauf](stammdaten-per-mcp.md) lesen. Individuelle bzw. sonstige im statischen Katalog nicht enthaltene Lohnarten als `mandanten_lohnarten` im Eingabe-JSON mit Bezeichnung und genauer Quelle dokumentieren. Nur die tatsächlich benötigten Einträge mitgeben; keine Mandantenbestände im Skill installieren.

```json
{
  "mandanten_lohnarten": {
    "1001": {
      "bezeichnung": "Individuelle Lohnart laut Zielmandant",
      "werteinheit": "stunden",
      "quelle": "Tatsächliche Payroll-Ressource oder Mandantendokument, Stichtag und Eintrag"
    }
  }
}
```

Dies ist ein Strukturbeispiel, kein verwendbarer Nachweis. Die Angaben aus dem realen Mandanten übernehmen. Ist eine Lohnart individuell angepasst, hat die belegte Mandantenzuordnung Vorrang. Die Mitgliedschaft im Katalog allein sagt nicht, dass eine Lohnart für jeden Mitarbeiter, jede Erfassungsart oder eine manuelle Buchung zulässig ist. Automatisch berechnete Lohnarten nicht allein aufgrund ihrer Existenz als zusätzliche Bewegung erzeugen.

Der Helfer prüft Schlüsselmitgliedschaft, ausdrücklich dokumentierte zeitliche bzw. Versionsgrenzen und eine ggf. belegte Einheit individueller Lohnarten. Die Auswirkungen auf Steuer/SV, Fehlzeiten, Sollzeiten und zulässige Feldkombinationen bleiben Teil der fachlichen Zuordnung anhand von Schnittstellenbeschreibung, Katalog und Zielmandant.

## Kataloge aktualisieren

Die fertigen JSON-Kataloge benötigen beim Export keine Zusatzbibliothek. Ein erneuter Aufbau aus denselben PDF-Tabellen verwendet `scripts/build_catalogs.py` mit `pdfplumber` und `pypdf`. Bei neuen Dokumentständen zunächst Dateinamen/Stand im Skript aktualisieren und geänderte Tabellenspalten bzw. Hinweise prüfen; kein altes Standdatum auf eine neue PDF übertragen.

```text
python scripts/build_catalogs.py ordner-mit-original-pdfs --output references/kataloge
```

Danach Quellprüfsummen, unklare Zeilen, Dubletten, Anzahlen, Quellenverweise und die fachlich geänderten Einträge prüfen. PDF-Originale nicht mit einer neu erzeugten Tabelle überschreiben.
