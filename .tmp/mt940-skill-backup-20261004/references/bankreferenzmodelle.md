# Bankreferenzmodelle und Quellprüfung

## Ein Modell pro Bank und Variante

`profiles/<bank>-<variante>.json` gehört genau zu einer Bankidentität und einer belegten Exportvariante. Bankidentität mit BIC, BLZ oder eindeutiger Anbieterkennung in der Referenz dokumentieren; `bank_id` ist deren stabiler interner Schlüssel. Bei Zweifeln an der Identität die Quelle klären. Ein Modell einer anderen Sparkasse, einer Bankengruppe oder eines anderen Kartenanbieters nicht wegen ähnlicher Texte übernehmen.

Bei jeder Bearbeitung Modell suchen, lesen und anwenden. Fehlt es, [unverified-example.json](../profiles/unverified-example.json) als Entwurf für die konkrete Bank kopieren und bekannte Werte eintragen. Offene Zuordnungen als `null` und in `open_questions` festhalten. Eine fehlende Referenz ist ein Klärungsfall; der Entwurf muss trotzdem angelegt werden. Ein gespeicherter Entwurf allein erlaubt keine Formatannahmen.

Erst aus einer Originalbankdatei, bankeigenen Formatbeschreibung oder bestätigten bankbezogenen Testausgabe die tatsächliche Syntax und Feldbedeutung übernehmen. Bank-/Quellenidentität, Datum und genaue Fundstelle der Referenz speichern. Die sichtbare PDF allein belegt ihren Text, aber keine unsichtbare MT940-Unterfeldsyntax. Beispielwerte nie als reale Salden oder Buchungen übernehmen.

`status: draft` bedeutet: noch nicht für produktive Verwendung bestätigt. Nach belegter Modellprüfung und bei DATEV nach dokumentiertem, anschließend bereinigtem Probeimport auf `verified` setzen. Regeln nicht still ändern: neue `profile_version` vergeben; bei anderem Exportweg/Format eine neue `source_variant` und gegebenenfalls ein neues Profil anlegen.

## Modellinhalt

Der Generator verlangt:

- `profile_name`: identisch mit dem JSON-Dateinamen ohne Endung;
- `bank_id`, `bank_name`, `source_variant`, `profile_version`, `source_types`;
- `status`: `draft` oder `verified`;
- `reference_basis`: `kind` (`native_bank_file`, `bank_documentation` oder `confirmed_test`), `reference` mit überprüfbarer Fundstelle und `verified_against_reference: true` erst nach Prüfung;
- `field_mappings`: belegte Bedeutung, Quelle und Ziel jedes Auszugs-/Umsatzfelds, einschließlich der benannten Zusatzfelder;
- `statement_reference_rule`: `source` zur unveränderten Übernahme oder `deterministic_mt` ausschließlich als ausdrücklich belegte Modellregel;
- `reference_rules`: je Kunden- und Bankreferenz die ausdrücklich dokumentierte Behandlung;
- `charset`, `line_endings`, `allowed_underfields` und Quelle/Ziel-Beispiele unter `examples`;
- für rekonstruierten Text `adapter` und dessen `adapter_sha256`;
- bei DATEV `probe_import` mit Datum, Ergebnis, sämtlichen Prüfpunkten und bestätigter Löschung der Testumsätze.

Pflichtschlüssel in `field_mappings`: `statement_reference`, `iban`, `statement_number`, `sequence_number`, `opening_balance_date`, `opening_balance`, `closing_balance_date`, `closing_balance`, `currency`, `value_date`, `booking_date`, `amount`, `code`, `customer_reference`, `bank_reference`, `description`. Für jeden Schlüssel Herkunft, technische Transformation und Ziel angeben, nicht nur eine Zielfeldnummer. Fehlende Quellwerte und ihre zulässige Behandlung ausdrücklich dokumentieren.

Die derzeitigen Skripte unterstützen einen begrenzten MT940-Ausschnitt: EUR, IBAN als `:25:`, `:60F:`/`:62F:`, Soll/Haben ohne zusätzliche Stornokennzeichen und kurze Referenzen in `:61:`. Das ist eine technische Begrenzung des Werkzeugs, **kein universelles Bankmodell**. Falls die Bankreferenz andere Felder oder Grenzen verlangt, Modell und technischen Bankpfad erweitern und verifizieren. Die Bankvariante nicht in das vorhandene Schema pressen. Bei nativen Quellen alle unterstützten Felder unverändert übernehmen; eine Quelle mit nicht unterstützter Syntax sperren, bis ein geeigneter Bankpfad vorhanden ist.

Unterstützte Referenzregeln:

| Regel | Anwendung |
| --- | --- |
| `exact` | Vorhandenen Wert unverändert übernehmen, bei nicht darstellbarem Wert abbrechen. |
| `upper_alnum_16` | Nur wenn das Bankmodell diese Transformation belegt: Großbuchstaben/Alphanumerik und 16 Zeichen. Vollständigen Originalwert zusätzlich in `:86:` erhalten. |
| `source_or_sequence_9` | Nur für die Bankreferenz und nur als belegte Modellregel: vorhandene kurze Referenz unverändert, sonst neunstellige technische Sequenz. Niemals als originale Bankreferenz ausgeben. |

Fehlende Kundenreferenz nur mit ausdrücklich modelliertem `missing_customer_reference: NONREF` behandeln. Kein globaler `NMSC`-Standardcode: Code aus der Quelle oder der dokumentierten Zuordnung ihrer Buchungsart erfassen. Im Quellprüfbericht Originalbezeichnung und Modellregel nachvollziehbar machen.

## Bankeigener Textadapter

Der Adapter liegt neben seinem Profil. Sein Dateiname darf keine Pfadkomponenten enthalten. Vor dem Eintragen des SHA-256 die Funktionen anhand der Referenzbeispiele prüfen:

```python
def encode_field86(transaction):
    # Nur die belegten Regeln DIESER Bankvariante verwenden.
    # transaction enthält description und gegebenenfalls source_fields.
    return [":86:...", "..."]

def decode_field86(lines):
    # Tatsächliche Zeilen unabhängig von encode_field86 lesen.
    # Nicht durch erneutes Erzeugen oder Rückgabe der Eingabequelle prüfen.
    return {"description": "vollständiger Nutztext", "source_fields": {}}
```

Benannte Informationen wie Gegenpartei, IBAN, EREF und MREF müssen bei Bedarf einzeln unter `source_fields` zurückgegeben werden. Bedeutung und Reihenfolge aus der Bankreferenz übernehmen. Ein erlaubtes `?32` ohne dokumentierte Bedeutung reicht nicht. Ein einfacher Textadapter ist nur zulässig, wenn **diese Bankvariante** tatsächlich unstrukturierten Text verwendet. Keine zentrale Standarddatei für unbekannte Banken erstellen.

Referenzbeispiele müssen sowohl vollständige Quellfelder als auch die erwarteten physischen MT940-Felder und deren dekodierte Bedeutung enthalten. Schreiben und Lesen jeweils gegen diese Beispiele prüfen; ein selbstkonsistenter Rundlauf beweist keine richtige Zuordnung. Lange Texte, Umlaute, Referenzenden und gegebenenfalls mehrere Buchungsarten abdecken, soweit in der Referenz vorhanden.

Unter `tests/fixtures/profiles/` liegen ausschließlich synthetische Softwaretestmodelle. Die Beispiele `?20`/`?32` sind keine Bankregeln. `test_fixture_only: true` darf nie entfernt werden, um ein Produktionsprofil vorzutäuschen. Der Loader sperrt diese Modelle außerhalb des Testordners, und der Validator erteilt ihnen keine Produktionsfreigabe.

## Manifest

Zusätzlich zu den Quelldaten ausdrücklich eintragen:

```json
{
  "bank_id": "bankidentitaet-aus-der-quelle",
  "bank_profile": "bankidentitaet-exportvariante",
  "profile_version": 1,
  "source_variant": "exportvariante-aus-der-referenz",
  "source_type": "pdf",
  "target_system": "DATEV",
  "field86_mode": "bank_profile",
  "output_scope": "test"
}
```

Dies ist ein Ausschnitt, kein ausführbares Manifest. Zeitraum, Auszugs-/Sequenznummer, IBAN, Währung, Salden und Umsätze müssen separat vollständig vorliegen. Die Modellbezeichnungen stammen aus dem tatsächlich angelegten Profil. Fehlende Modellkennungen nicht aus ähnlichen Dateinamen ableiten.

## Getrennter Quellprüfbericht

`source-review.json` vor der Freigabe **aus der Originalquelle** erfassen oder unabhängig gegen diese prüfen. Der Generator erstellt ihn bewusst nicht. Beispielstruktur, keine echten Bankwerte:

```json
{
  "bank_id": "bankidentitaet-aus-der-quelle",
  "bank_profile": "bankidentitaet-exportvariante",
  "profile_version": 1,
  "source_variant": "exportvariante-aus-der-referenz",
  "reviewed_against_original": true,
  "review_method": "visual_original",
  "source_files": [
    {"id": "auszug", "path": "original.pdf", "sha256": "SHA-256-der-unveraenderten-Quelldatei"}
  ],
  "iban": "IBAN-aus-der-Quelle",
  "currency": "EUR",
  "statement_start": "2026-07-01",
  "statement_end": "2026-07-01",
  "statement_number": 7,
  "sequence_number": 1,
  "opening_balance_date": "2026-06-30",
  "opening_balance": "100.00",
  "closing_balance_date": "2026-07-01",
  "closing_balance": "75.00",
  "transactions": [
    {
      "source_file": "auszug",
      "source_locator": "Seite 1, Buchungsblock 1, Zeilen 12 bis 15",
      "value_date": "2026-07-01",
      "booking_date": "2026-07-01",
      "amount": "-25.00",
      "code": "NTRF",
      "customer_reference": "REF0001",
      "bank_reference": null,
      "description": "Vollständiger sichtbarer Buchungstext mit Referenz REF0001",
      "source_fields": {}
    }
  ]
}
```

Alle Feldwerte und Codes sind anhand der realen Quelle und ihrer Bankregel zu ersetzen. `bank_reference: null` bezeichnet einen tatsächlich fehlenden Quellwert und ist nur bei belegter Fehlwertregel zulässig. Die Fundstellen dürfen sich nicht wiederholen. Bei mehreren Seiten im Locator den gesamten Block angeben. Relative Originaldateipfade beziehen sich auf den Ordner des Quellprüfberichts.

`visual_original` ist für PDF/Bild Pflicht. `native_field_extraction` ist für nachvollziehbare Extraktion aus einer elektronischen Originaldatei vorgesehen. Bei `native` die tatsächlichen `native_field86_lines` und deren vollständigen Text sowie `statement_reference` auch im Quellprüfbericht speichern. Alle weiteren übernommenen Informationen einzeln als `source_fields` erfassen und im Bankmodell zuordnen.

Die Software kann nicht beweisen, dass eine als geprüft markierte Abschrift tatsächlich visuell geprüft wurde. Die ursprüngliche Datei erneut öffnen und mit der Abschrift vergleichen; den Nachweis nicht bloß durch Setzen eines Bool-Werts herstellen. Dateihashes sichern die Identität, nicht die Richtigkeit der Abschrift. Bei unleserlichem Text die Freigabe sperren.

## Abnahme

```bash
python scripts/build-mt940.py manifest.json
python scripts/validate-mt940.py "MT940 <IBAN> <Zeitraum>.sta" manifest.json --source-review source-review.json
```

Bei abweichendem Modellordner beide Aufrufe mit demselben `--profile-dir` ausführen. Für ein neues Modell außerdem die bankbezogenen Referenzbeispiele prüfen. Der Quellprüfbericht dient dem vollständigen Feldvergleich, der DATEV-Probeimport der tatsächlichen Interpretation in DATEV.

Im Bericht je Feld Quelle, Manifest, tatsächlichen MT940-Wert und Vergleich speichern. Für modellbedingte technische Transformationen den Originalwert und das transformierte Ergebnis getrennt ausweisen. Auszugszeitraum und Modellkennungen werden mit dem Quellprüfbericht als Metadaten abgeglichen; der Zeitraum besitzt kein eigenes MT940-Feld. `:61:` kodiert den Buchungstag als `MMTT`; dessen vollständiges Jahr bleibt im geprüften Quellnachweis.

`delivery_approved: true` verlangt eine vollständige Quellenprüfung, bestandene Struktur-/Saldenprüfung und ein für den Umfang geeignetes echtes Modell. Ein Testlauf bleibt `delivery_approved: false` und kann ausschließlich als ausdrücklich gekennzeichnete Testdatei übergeben werden. Nach jeder Änderung erneut prüfen. Alte Erfolgsberichte bei Fehlern nicht weiterverwenden.
