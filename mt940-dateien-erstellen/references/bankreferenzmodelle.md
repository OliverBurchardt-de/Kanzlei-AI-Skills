# Bankmodelle lernen und Quellen unabhängig prüfen

## Vorhandenes Modell oder Lernlauf

Ein Modell gehört genau zu `bank_id`, `source_variant`, `profile_version` und einer Quellenart. Bankidentität anhand der Originalquelle bestimmen; Banken und Varianten nicht vermischen. Native Exporte und PDF-Rekonstruktionen als getrennte Varianten führen.

Fehlt ein Modell: Quelle vollständig erfassen, MT940 erzeugen, tatsächlich geschriebene Felder gegen die unabhängig geprüfte Originalquelle vergleichen, Fehler korrigieren und erneut erzeugen. **Erst nach erfolgreichem vollständigem Abgleich ein bestätigtes Modell speichern.** Fehlende Originalexporte oder Bankdokumentation verhindern den Lernlauf nicht.

| Status | Bedeutung |
| --- | --- |
| `draft` | Temporärer Kandidat für den Lernlauf; keine bestätigte Referenz oder Auslieferungsfreigabe |
| `source_verified` | Tatsächliche MT940 vollständig gegen die Originalquelle geprüft; Modell wiederverwendbar |
| `verified` | Zusätzlich tatsächliche DATEV-Anzeige nach erfolgreichem, bereinigtem Probeimport bestätigt |

`reference_basis.kind: source_reconstruction` bezeichnet eine eigene Exportkonvention für diese Bank/Quellenvariante. Sie behauptet keine Nachbildung des nativen Bankformats. Native Dateien, Bankdokumentation und bestätigte Testimporte bleiben weitere Referenzarten. Synthetische Softwaretestmodelle niemals als echte Bankreferenzen ausgeben.

## Quelle und technische Ersatzregeln

Originaldateien unverändert sichern und SHA-256 dokumentieren. `manifest.json` aus der Quelle erfassen; `source-review.json` getrennt gegen das Original prüfen. Quellprüfung nicht aus Manifest, MT940 oder Generatorbericht zurückkopieren. Bei PDF/Bild alle Seiten rendern und sämtliche vollständigen Buchungsblöcke visuell prüfen.

Nicht angezeigte Werte im Quellprüfnachweis ausdrücklich `null` lassen. Im Manifest dürfen folgende dokumentierte technische Regeln fehlende Werte ergänzen:

| Feld | Regel | Ergebnis |
| --- | --- | --- |
| `statement_number` | `technical_statement_one` | Technische Auszugsnummer 1 |
| `sequence_number` | `technical_sequence_one` | Technische Sequenz 1 |
| `opening_balance_date` | `period_start_previous_day` | Vortag des belegten Zeitraumbeginns als technische Saldendatierung |
| `closing_balance_date` | `period_end` | Ende des belegten Zeitraums als technische Saldendatierung |
| `value_date` | `booking_date_when_not_shown` | Technische Ersatzvaluta = Buchungstag, sofern keine separate Valuta angezeigt wird |
| `code` | `nmsc_when_not_shown` | Technischer NMSC-Code, sofern kein Originalcode angezeigt wird |
| Kundenreferenz | `missing_customer_reference: NONREF` | Kennzeichen für fehlende Quellreferenz |
| Bankreferenz | `source_or_sequence_9` | Neunstellige technische Quellsequenz bei fehlender Bankreferenz |

Sichtbare Originalwerte niemals ersetzen. Keine Ersatzregel für Konto, Währung, Buchungsdatum, Betrag, Saldenbetrag oder Text. Unleserliche Quellen, Widersprüche und nicht verlustfrei darstellbare Inhalte als konkrete Klärungsfälle behandeln. Die Periodenregeln bestätigen keine nicht angezeigten originalen Saldendaten.

Jede Ersatzanwendung in `derived_fields` am Auszug oder Umsatz mit `source_value: null`, `rule`, `value` und `reason` protokollieren. Beispiel:

```json
{
  "opening_balance_date": "2025-12-31",
  "derived_fields": {
    "opening_balance_date": {
      "source_value": null,
      "rule": "period_start_previous_day",
      "value": "2025-12-31",
      "reason": "Technische Datierung für den Zeitraum ab 01.01.2026; kein separates Saldendatum angezeigt"
    }
  }
}
```

Der Quellprüfnachweis behält `opening_balance_date: null`. Der Validator berechnet die Ersatzregel erneut aus den unabhängigen Quellwerten und zeigt Originalwert, technische Ableitung und tatsächlichen MT940-Wert getrennt. Die direkte Original/Manifest-Gleichheit bleibt bei Ableitungen ausdrücklich false; die überprüfte Regelgleichheit muss true sein.

## Textadapter

Sämtliche sichtbaren Buchungstextzeilen in Originalreihenfolge einschließlich Gegenpartei, Gegenkonto, EREF, MREF, Gläubiger-ID und Referenzenden erhalten. Nur Leerzeichen und physische Zeilenumbrüche normalisieren; Wörter, Umlaute, Satzzeichen, Wiederholungen und Referenzen nicht kürzen oder verbessern.

Für neue Rekonstruktionen unstrukturierten `:86:`-Text verwenden. `?xx` im Originaltext bleibt wörtlicher Text. Encoder und Decoder getrennt implementieren; der Decoder liest tatsächliche physische Zeilen und erhält weder Quellwerte noch Manifestwerte als Rückgabeschablone.

```python
from mt940_common import field86_result

def encode_field86(transaction):
    return field86_result(transaction["description"]).lines

def decode_field86(lines):
    if not lines or not lines[0].startswith(":86:"):
        raise ValueError("Missing :86:")
    text = lines[0][4:] + "".join(lines[1:])
    return {"description": text, "source_fields": {}}
```

Bei vorhandenen `source_fields` den Decoder um nachvollziehbare bank-/quellenbezogene Extraktionsregeln aus dem tatsächlichen Text erweitern. Alle benannten Felder einzeln vergleichen; diese nicht entfernen, um einen fehlenden Decoder zu umgehen. Physische Grenzen und Zeichensatz einhalten. Falls Text nicht verlustfrei hineinpasst, den geeigneten dokumentierten Bankpfad erweitern oder die konkrete Grenze klären.

## Lernhelfer

Das ausgelesene Manifest benötigt `bank_name`, `bank_id`, `source_variant`, `bank_profile`, `profile_version`, Quellenart, Konto, Zeitraum, Salden und sämtliche Umsätze. Fehlende technische Angaben ausdrücklich `null` lassen. Der Helfer verwendet die oben benannten Regeln oder die ausdrücklich vorgegebenen `reconstruction_rules`.

```bash
python scripts/learn-bank-profile.py manifest.json --source-review source-review.json --adapter bank-textadapter.py --profile-dir profiles --output-dir ausgabe
```

Der Helfer prüft Originaldateihashes, erzeugt Modellkandidat und MT940 temporär und vergleicht anschließend die tatsächlichen Bytes mit dem unabhängigen Quellprüfnachweis. Nach einem Fehler wird kein bestätigtes Modell gespeichert. Ursache anhand der Fundstelle korrigieren und erneut ausführen, bis der vollständige Abgleich besteht. Interne Wiederholungen vor Auslieferung sind keine DATEV-Importe.

Nach Erfolg werden MT940, ergänztes Manifest, vollständiger Prüfbeleg sowie Modell und Adapter gespeichert. Das Modell erhält `source_verified`, `source_reconstruction`, einen Verweis mit Hash auf den Prüfbeleg und feste Quelle/Ziel-Beispiele aus dem erfolgreichen Lauf. Es enthält Feldzuordnungen, Ersatzregeln, Adapterhash und Bank-/Quellenidentität. Die Beispiele belegen die eigene Rekonstruktion, keine behauptete Originalbankdatei. Prüfbelege dauerhaft bei den Arbeitsunterlagen erhalten. Das bestätigte Modell auch im installierten Skill speichern, damit spätere Anfragen es finden.

## Vorhandenes Modell wiederverwenden

Für gelernte Modelle `field86_mode: reconstructed` verwenden. Fehlende technische Werte erneut mit den dokumentierten Regeln aus `reconstruction.fill_missing` ergänzen; Quellprüfung behält Originalwerte/null. Anschließend:

```bash
python scripts/build-mt940.py manifest.json --profile-dir profiles
python scripts/validate-mt940.py "MT940 <IBAN> <Zeitraum>.sta" manifest.json --profile-dir profiles --source-review source-review.json
```

Der Loader prüft zusätzlich Hash und Erfolg des gespeicherten Referenzbelegs. Geänderte Adapter oder Regeln benötigen eine neue Profilversion und eine erneute Quellenprüfung. Native Varianten bleiben `native` und erhalten exakte Originalsyntax; vorhandene bankeigene Strukturmodelle bleiben `bank_profile` mit belegten Unterfeldbedeutungen.

## Quellprüfschema

Pflichtmetadaten: Bank-/Modellkennungen, `reviewed_against_original: true`, `review_method: visual_original` bei PDF/Bild oder `native_field_extraction` bei elektronischen Originalen; `source_files` mit id, unverändertem Pfad und SHA-256; IBAN, Währung, Zeitraum, Auszugs-/Sequenznummer, Saldendaten/-beträge. Technische Fehlwerte bei Rekonstruktion ausdrücklich `null`.

Jeder Umsatz enthält eindeutige `source_file`/`source_locator`, Valuta, Buchungsdatum, vorzeichenbehafteten Dezimalbetrag mit zwei Nachkommastellen, Code, Kunden-/Bankreferenz, vollständige `description` und benannte `source_fields`. PDF/Bild zusätzlich mit `source_page`, sämtlichen exakten `source_description_lines` und `source_text_verified: true` nach tatsächlicher visueller Prüfung. Quellreihenfolge und Seitenwechsel erhalten. Native Quellen zusätzlich mit `native_field86_lines` und originaler `statement_reference` vergleichen.

Relative Originaldateipfade beziehen sich auf den Ordner des Quellprüfnachweises. Fundstellen dürfen sich nicht wiederholen. Dateihashes sichern die Identität, nicht die Richtigkeit der Abschrift.

## DATEV getrennt ausweisen

Der erfolgreiche Quellen-/Technik-/Saldenabgleich genügt für Modellbestätigung und Übergabe der Rekonstruktion. Ohne tatsächlichen DATEV-Probeimport bleibt `datev_import_verified: false`. Dateierstellung allein beauftragt keinen Import oder Löschvorgang. Nach einem beauftragten Probeimport alle tatsächlichen DATEV-Felder und vollständigen Texte prüfen, Testumsätze bereinigen und erst dann `status: verified` samt Prüfpunkten dokumentieren.
