# Routine „Riecken-Connector Wochenprüfung“

Angelegt am 10.10.2026 (Routine-ID `trig_019Us1MhorHJDnytg3ugeVc1`), Zeitplan montags 06:59 Uhr Europe/Berlin (`CRON_TZ=Europe/Berlin 59 6 * * 1`), jede Ausführung in einer neuen Session, Benachrichtigung per Push und E-Mail.

**Einschränkung:** Die aus der Session heraus angelegte Routine speichert keinen Connector. Ohne den Riecken-Connector findet die gestartete Session keine `mcp__Riecken__`-Werkzeuge und meldet nach Schritt 3 des Prompts einen Verbindungsfehler statt eines Prüfergebnisses. Abhilfe: Die Routine in der Routinen-Oberfläche von claude.ai öffnen und den Connector „Riecken“ hinzufügen, oder sie dort mit dem folgenden Prompt und dem Connector neu anlegen und die bestehende Routine löschen.

## Prompt

```text
Wöchentliche Prüfung des Riecken-DATEV-Connectors (MCP-Server „Riecken“, Werkzeuge mit Präfix mcp__Riecken__datev_) für die Kanzlei Burchardt & Kollegen. Auftraggeber: Oliver Burchardt. Antworte auf Deutsch, ohne Gendern, ohne Konjunktivfloskeln, mit Konfidenzniveau und ausdrücklich genannten Annahmen.

Aufgabe: Feststellen, ob sich der Leistungsumfang des Connectors gegenüber der gespeicherten Baseline geändert hat. Bei Änderungen: die Erweiterungen in die betroffenen Skills einarbeiten, Baseline und Dokumentation fortschreiben und den Auftraggeber informieren, welche Änderungen es gab und welche Skills auf welche Version gehoben wurden.

Vorgehen:
1. Repository OliverBurchardt-de/Kanzlei-AI-Skills verwenden (im Arbeitsverzeichnis vorhanden oder klonen). origin/main holen. Fehlt der Ordner riecken-connector/ auf main, stattdessen den Branch claude/laughing-bardeen-o7paio auschecken; dort liegt die erste Fassung.
2. riecken-connector/PRUEFANLEITUNG.md vollständig lesen und exakt danach vorgehen. Kurzfassung: Werkzeugliste der Session nach mcp__Riecken__ durchsuchen, zusätzlich ToolSearch „Riecken datev“ mit großem max_results; alle Schemata über ToolSearch select laden; wörtlich als {"tools": [...]} in eine Datei aktuell.json im Scratchpad schreiben; python riecken-connector/scripts/vergleiche_baseline.py --baseline riecken-connector/baseline/tools.json --aktuell <pfad>/aktuell.json --bericht riecken-connector/berichte/<JJJJ-MM-TT>.md ausführen.
3. Sind keine mcp__Riecken__-Werkzeuge vorhanden oder meldet der Server einen Verbindungsfehler, ist das kein Wegfall von Werkzeugen: abbrechen, nichts ändern, den Fehler melden und darauf hinweisen, dass der Riecken-Connector für diese Routine verbunden sein muss.
4. Exit-Code 0 (keine Änderungen): nichts committen. Abschließend kurz melden: Datum, Anzahl Werkzeuge, Ergebnis von datev_health_check, keine Änderungen.
5. Exit-Code 1 (Änderungen): nach PRUEFANLEITUNG.md Abschnitt 4 vorgehen. Branch riecken-update/<JJJJ-MM-TT> von der aktuellen Basis anlegen; betroffene Skills anpassen (nur Datenzugriff, Werkzeugnamen, Parameter und daraus folgende Grenzen, keine fachlichen Prüfregeln), Versionen anheben, Tests ausführen, Installationspakete in outputs/ neu bauen, README ergänzen, baseline/tools.json und LEISTUNGSUMFANG.md fortschreiben, Bericht ergänzen. Committen und mit git push -u origin <branch> pushen. Nicht nach main mergen, keinen Pull Request eröffnen. Niemals schreibende Riecken-Werkzeuge in bisher nur lesende Skills aufnehmen; die DMS-Sperre des Gesellschafterbeschlusses nicht aufheben. Außer datev_health_check keine fachlichen Riecken-Abrufe und keine schreibenden Aufrufe.
6. Abschlussmeldung bei Änderungen: dass es Änderungen gab; welche (Werkzeug, Art der Änderung); welche Skills auf welche Version gehoben wurden; Pfade der neuen Installationspakete; Branch-Name; bewusst nicht umgesetzte Punkte mit Grund; Hinweis „kein Live-Test“; Konfidenz und Annahmen.
```
