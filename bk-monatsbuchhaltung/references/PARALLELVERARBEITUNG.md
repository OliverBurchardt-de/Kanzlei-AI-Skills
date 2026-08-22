# Mehragenten- und Kontrollverarbeitung großer Belegmengen

Diese Referenz gilt bei großen oder beziehungsreichen Belegmengen und verfügbaren Subagents. Ihr Zweck ist die bessere Kontexttrennung, Vollständigkeit und unabhängige Kontrolle. Geschwindigkeit und eine feste Zahl von Agents sind keine Qualitätsziele. Preflight, globale Fachentscheidungen und Paketbau bleiben beim Hauptagenten.

## 1. Zentraler Start

Der Hauptagent schließt zuerst den vollständigen Preflight ab und erzeugt danach die Inventur und Batchdateien:

```text
python scripts/prepare_parallel_batches.py \
  --input-dir <eingabeordner> \
  --output-dir <arbeitsordner> \
  --context-file <verifizierter-arbeitskontext.json> \
  --batch-size 100
```

Ausgabeordner und Arbeitskontext müssen außerhalb des Eingabeordners liegen, damit sie niemals als Beleg inventarisiert werden. Der Arbeitskontext ist ein nicht leeres JSON-Objekt mit den unten genannten, bereits verifizierten Preflight-Daten. Das Skript bindet dessen Fingerprint an Inventur, Batchdateien und Ergebnisse. Es erfasst fachliche Dateien in stabiler Pfadreihenfolge, berechnet Größe und SHA-256, schätzt den Arbeitsaufwand aus PDF-Seitenmarkern, OCR-typischen Bildformaten und Dateigröße, hält identische Inhalte in demselben Batch und erzeugt:

- `inventory.json`: vollständige zentrale Inventur, Hashgruppen und Batchzuordnung.
- `batch_NNN_input.json`: ausschließlich die Quellen des jeweiligen Batches, reservierte ID-Präfixe und globale Hashhinweise.

Offensichtlich zusammengehörige, aber nicht hashidentische Dateien vor der Delegation prüfen und nötigenfalls gemeinsam einem Batch zuordnen. Der Hauptagent darf die Zuordnung in `inventory.json` und den Batchdateien nur konsistent ändern; keine Quelle darf fehlen oder doppelt zugewiesen sein.

Die Zahl der erzeugten oder gleichzeitig bearbeiteten Batches ist fachlich nicht fest begrenzt. Die Laufzeitumgebung bestimmt die verfügbare Parallelität; übrige Batches werden nacheinander bearbeitet. Die Batchgröße begrenzt den Kontext eines Analyseauftrags; innerhalb dieser Grenze wird nach geschätztem Arbeitsaufwand verteilt. Nur eine unteilbare Gruppe hashidentischer Dateien darf die Grenze ausnahmsweise überschreiten. Ohne verfügbare Subagents normal sequentiell weiterarbeiten und dieselben Integritätsprüfungen beibehalten.

## 2. Unveränderlicher Arbeitskontext

Alle Subagents erhalten denselben vom Hauptagenten geprüften Kontext:

- Mandant, Zielperioden und Rechtsträger,
- Mandantenprofil und Umsatzsteuerlogik,
- Kontenrahmen, Sachkontenlänge und erlaubte Konten,
- vorhandene Einzelpersonenkonten und gesperrte Sammel-/CPD-Konten,
- DATEV-Vorbuchungen und Ergebnis der live geprüften Dublettensuche,
- Bilanz-/EÜR-Status und gegebenenfalls Abgrenzungsregister.

Subagents dürfen diesen Kontext nicht neu abrufen oder verändern. Fehlende technische Pflichtdaten melden sie als Batchfehler; fachliche Unsicherheiten behandeln sie nach den normalen Ampel- und Klärungsregeln.

## 3. Auftrag je Subagent

Ein Subagent verarbeitet ausschließlich `allowed_source_ids` seiner `batch_NNN_input.json`. Er darf Dateien aus anderen Batches nur anhand der mitgelieferten Hashhinweise als mögliche Beziehung nennen, nicht als verarbeitet ausweisen.

Jeder Subagent schreibt genau eine eigene Datei `batch_NNN_result.json`. Er verändert weder `inventory.json` noch andere Batchdateien oder Ergebnisse. Zulässige Ergebnisstruktur:

```json
{
  "schema_version": "1.2",
  "batch_id": "B001",
  "inventory_fingerprint": "...",
  "transactions": [],
  "transaction_sources": [],
  "clarification_cases": [],
  "handoffs": [],
  "profile_suggestions": [],
  "accrual_candidates": [],
  "person_account_proposals": [],
  "batch_notes": []
}
```

Vorgangs-IDs beginnen mit dem reservierten Präfix aus `id_namespace.transaction_prefix`, Klärungsfall-IDs mit `id_namespace.clarification_prefix`, Abgrenzungs-IDs mit `id_namespace.accrual_prefix` und Profilvorschlags-IDs mit `id_namespace.profile_suggestion_prefix`. Jede erlaubte Quelle muss mindestens einem Vorgang zugeordnet sein. Ein Vorgang und alle darauf verweisenden Vorschläge dürfen nur Quellen und Vorgänge aus demselben Batch besitzen.

`person_account_proposals` enthält nur Vorschläge für noch nicht eindeutig vorhandene Geschäftspartner:

```json
{
  "partner": "Beispiel GmbH",
  "account_type": "creditor",
  "vat_id": "DE123456789",
  "banks": [],
  "transaction_ids": ["B001-V000001"]
}
```

Subagents dürfen:

- vorhandene, im gemeinsamen Kontext eindeutig bestätigte Einzelpersonenkonten verwenden,
- Kontierungs-, USt- und Ampelvorschläge erstellen,
- Klärungsfälle und Übergaben ihres Batches formulieren.

Subagents dürfen nicht:

- neue Personenkontonummern endgültig vergeben,
- `master_records` erzeugen,
- gemeinsame Dateien verändern,
- DATEV-/SharePoint-Daten erneut abrufen oder schreiben,
- `build_package.py` oder `validate_package.py` ausführen,
- ein Teilpaket als importfähig oder vollständig bezeichnen.

## 4. Deterministische Zusammenführung

Nach Vorliegen aller Ergebnisse erzeugt der Hauptagent einen konsolidierten Entwurf:

```text
python scripts/merge_parallel_results.py \
  --inventory <arbeitsordner>/inventory.json \
  --base-run <basis-lauf.json> \
  --results-dir <arbeitsordner> \
  --output <arbeitsordner>/merged_draft.json
```

`base-run` enthält die globalen Laufdaten wie `run`, `scope`, Mandantenprofil, Zahlungsabstimmung und DATEV-Nachweise, aber keine Batch-Transaktionen. Zusätzlich muss `_parallel_context_fingerprint` exakt dem `shared_context_fingerprint` aus `inventory.json` entsprechen; dadurch kann kein Ergebnis mit der Basisdatei eines anderen Mandanten oder Preflight-Stands vermischt werden. Das Merge-Skript:

- verlangt genau ein Ergebnis pro Batch,
- gleicht Arbeitskontext-Fingerprint von Inventur, Batchergebnissen und `base-run` ab,
- prüft Batch- und ID-Grenzen,
- übernimmt die zentrale `source_files`-Inventur,
- verhindert doppelte Vorgangs-, Quellen- und Klärungsfall-IDs,
- verlangt eine Vorgangszuordnung für jede Quelle,
- kennzeichnet identische Hashes und logische Dublettenkandidaten,
- konsolidiert Personenkontenvorschläge nach Geschäftspartner und Kontotyp.

Ein erfolgreicher Merge ist noch kein freigabefähiges Lauf-JSON. `_parallel_review.global_reconciliation_required` bleibt `true`, bis der Hauptagent die Schlussprüfung vorgenommen hat.

## 5. Verbindliche Schlussprüfung

Der Hauptagent prüft und entscheidet anschließend global:

1. identische und logische Dubletten über alle Batches,
2. Rechnungen mit Begleitdateien oder mehrere Vorgänge in einer Datei,
3. einheitliche Geschäftspartnerbezeichnungen und vorhandene Einzelkonten,
4. neue Personenkonten fortlaufend ab der live geprüften Höchstnummer,
5. Kollisionen und Zusammenlegung von Klärungsfällen,
6. Abgrenzungen, Übergaben und periodenübergreifende Sachverhalte,
7. alle verwendeten Konten und BU-Schlüssel erneut gegen DATEV live.

Erst danach `person_account_proposals` in vollständige `master_records` überführen, `_parallel_review.global_reconciliation_required` auf `false` setzen und das endgültige Lauf-JSON nach `EINGABESCHEMA.md` erstellen. `build_package.py` mit diesem finalen Lauf-JSON ausführen.

## 6. Unabhängige Integritätskontrolle

Einen verfügbaren Subagent, der keinen der zu prüfenden Batches analysiert hat, als Nur-Lese-Prüfer einsetzen. Er erhält Inventur, konsolidiertes Lauf-JSON, Merge-Hinweise und nach dem Paketbau Belegindex und Validierungsbericht. Er prüft mindestens:

1. jede fachliche `source_id` ist vollständig inventarisiert und mindestens einem Endstatus zugeordnet,
2. identische Hashes, gleiche Rechnungsmerkmale und DATEV-Live-Treffer sind global widerspruchsfrei behandelt,
3. Rechnung, Begleitdateien, Deckblätter, Kopien und Sammeldateien sind zu den richtigen logischen Vorgängen verbunden,
4. Geschäftspartner und neue Personenkonten sind global eindeutig und kollisionsfrei,
5. alle Merge-Hinweise sind entschieden und keine Batchentscheidung wurde ungeprüft übernommen,
6. jede übertragene Quelle besitzt genau die erwartete Beleg-GUID, keine GUID kommt mehrfach vor und jede Buchungsverknüpfung zeigt auf eine vorhandene GUID.

Der Prüfer verändert keine Dateien. Bei einem Finding korrigiert der Hauptagent zentral und wiederholt Paketbau, `validate_package.py` und die unabhängige Prüfung. Eine feste Zahl von Agents, kürzere Laufzeit oder geringere Tokenkosten sind kein Abnahmekriterium.
