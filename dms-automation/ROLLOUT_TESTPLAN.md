# Rollout- und Testplan: SharePoint → DATEV DMS

## Phase 0 — Voraussetzungen (Koordination, ~1–3 Wochen Vorlauf)

| # | Aufgabe | Verantwortlich | Status |
|---|---|---|---|
| 0.1 | ASP-Ticket: Host, geplante Aufgabe, ausgehendes HTTPS, DATEVconnect-Endpunkt + Zertifikat (Fragenkatalog: KONZEPT.md §7) | O. Burchardt / IT | ☐ |
| 0.2 | DATEVconnect-Service-Benutzer mit DMS-Schreibrecht; Lizenz klären | O. Burchardt / DATEV | ☐ |
| 0.3 | Testmandant im DATEV DMS anlegen (z. B. 19999 „Testmandant KI“) | Kanzlei | ☐ |
| 0.4 | Site + Bibliothek + Entra-App gemäß `sharepoint/provisioning/setup_checkliste.md` | IT | ☐ |
| 0.5 | Worker auf ASP-Host installieren (`bridge-worker/README.md`), `mapping.yaml` gegen `GET /dms/v2/domains` + `/documentstates` der Ziel-Instanz verifizieren | IT | ☐ |
| 0.6 | Fachliche Freigabe der Register-/Status-Zuordnung je Dokumenttyp (`mapping.example.yaml`) | O. Burchardt | ☐ |
| 0.7 | Parallel: Anfrage an Klardaten zu Schreib-Endpunkten (KONZEPT.md §3 Variante c) | O. Burchardt | ☐ |

## Phase 1 — Pilot: Bescheidreview, 1 Testmandant (~1 Woche)

Alle Tests gegen den **Testmandanten**; Worker läuft zunächst manuell (kein Zeitplan).

### Happy Path
- [ ] T1: Agent legt Bescheidreview-Workbook + Sidecar über `bk-dms-ablage` in `19999/2025/` ab → Worker-Lauf → Dokument im DMS unter Mandanten/Steuerakte/Steuerbescheide, Jahr 2025, Status „offen“, Beschreibung korrekt, Datei öffnet fehlerfrei.
- [ ] T2: SharePoint-Writeback: `StatusDMS=Abgelegt`, `DMSDokumentNr` + `DMSDokumentGUID` gefüllt, gespiegelte Metadatenspalten korrekt.
- [ ] T3: DMS-Revisionshistorie enthält den `dispatcher-information`-Eintrag („Nach Online gesendet“).

### Idempotenz und Fortschreibung
- [ ] T4: Zweiter Worker-Lauf ohne Änderungen → kein Duplikat, Auditlog `already_processed`.
- [ ] T5: Fortschreibung: gleiches Workbook mit neuem Inhalt erneut hochladen (replace) → **Testpunkt E5:** neue Datei-Revision am selben DMS-Dokument (Strategie `version`); prüfen, ob die DMS-Version das akzeptiert. Falls API-Ablehnung: automatischer Fallback `new_document` mit Beschreibungszusatz — Ergebnis dokumentieren und Strategie in `mapping.yaml` fixieren.
- [ ] T6: Ledger-Verlust simulieren (SQLite umbenennen) → nächster Lauf erzeugt kontrolliert ein neues Dokument, kein Absturz, Auditlog nachvollziehbar.

### Fehlerpfade
- [ ] T7: Sidecar mit unbekanntem `dokumenttyp` → `StatusDMS=Fehler` + aussagekräftiger `FehlerText`; nach Korrektur des Sidecars wird das Item im Folgelauf verarbeitet.
- [ ] T8: Nicht existente Mandantennummer → `Fehler` („0 Treffer“).
- [ ] T9: Manipulierte Datei (Hash-Abweichung zum Sidecar) → `Fehler`, keine DMS-Ablage.
- [ ] T10: Binärdatei fehlt bei `binary_delivery: upload` → `Fehler`; bei `manual` → Item bleibt `Neu`, nach manuellem Upload der Datei erfolgt Ablage.
- [ ] T11: DATEVconnect nicht erreichbar (Preflight) → Lauf bricht ab (Exit 1), **kein** Item wird auf `Fehler` gesetzt; nächster Lauf arbeitet normal.
- [ ] T12: 24-h-Purge: `document-files`-Upload und `documents`-Anlage erfolgen im selben Lauf (Auditlog-Zeitstempel prüfen).

### Sonderfälle
- [ ] T13: Datei > 900 KiB → Skill wählt Manuell-Lane, Nutzerhinweis mit Zielordner; Ablauf wie T10b.
- [ ] T14: Property-Templates: prüfen, ob das Kanzlei-DMS Templates erzwingt und ob gesetzte Metadaten unverändert ankommen (E6).
- [ ] T15: Parallelität: zwei Worker-Starts gleichzeitig → zweiter Lauf endet sofort mit Exit 3 (Lock).

**Abnahmekriterium Phase 1:** T1–T12 bestanden; T5-Ergebnis dokumentiert; Auditlog vollständig.

## Phase 2 — Ausweitung (~2 Wochen)

- [ ] Dokumenttypen `abschlussreview_arbeitspapier`, `fibu_pruefprotokoll`, `fibu_klaerungsfaelle` mit je einem echten Mandanten pilotieren (Register-Zuordnung fachlich abnehmen).
- [ ] Worker auf Zeitplan (alle 5 Min) stellen.
- [ ] Team-Schulung: Übergabebibliothek, Statusspalten, Fehler-Ansicht, Manuell-Lane.
- [ ] Skill-Rollout: aktualisierte `bescheid-review`/`abschluss-review` (mit Pflichtfeld Mandantennummer) und `bk-dms-ablage` in die installierte Skill-Umgebung übernehmen.

## Phase 3 — Betrieb

- [ ] Runbook: tägliche Sichtung der Ansicht „Fehler“ (Verantwortlicher benennen); wöchentlicher Blick ins Auditlog.
- [ ] Task-Scheduler-Alarm auf Exit-Code 1 (Lauf abgebrochen).
- [ ] Secret-Rotation: Kalendereintrag vor Ablauf des Entra-Client-Secrets.
- [ ] Aufbewahrungsrichtlinie der Bibliothek aktivieren (12 Monate nach Ablage).
- [ ] Review nach 3 Monaten: Fehlerquote, Latenz, offene Klardaten-Anfrage (Ablösung des Workers gemäß KONZEPT.md §3).
