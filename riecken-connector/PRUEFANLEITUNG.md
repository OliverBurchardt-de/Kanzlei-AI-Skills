# Wöchentliche Prüfung des Riecken-Connectors

Diese Anleitung führt die Routine „Riecken-Connector Wochenprüfung“ aus. Ziel: feststellen, ob sich der Leistungsumfang des Riecken-DATEV-Connectors (MCP-Server `Riecken`) gegenüber der Baseline geändert hat, Erweiterungen in die Skills einarbeiten und den Auftraggeber informieren.

## 1. Vorbereitung

1. Repository `OliverBurchardt-de/Kanzlei-AI-Skills` auf `origin/main` aktualisieren. Für Änderungen einen Branch `riecken-update/JJJJ-MM-TT` von `origin/main` anlegen. Niemals direkt auf `main` pushen.
2. Prüfen, ob der MCP-Server `Riecken` verbunden ist: Die Werkzeugliste der Session enthält Namen mit Präfix `mcp__Riecken__`. Fehlen sie vollständig oder meldet der Server einen Verbindungsfehler, ist das **kein** Wegfall von Werkzeugen. Dann: Prüfung abbrechen, keine Baseline ändern, den Auftraggeber mit dem Fehlertext informieren.
3. `datev_health_check` ohne Parameter aufrufen und das Ergebnis protokollieren. Darüber hinaus keine fachlichen Abrufe (keine Mandantendaten lesen, nichts schreiben).

## 2. Aktuellen Leistungsumfang erfassen

1. Alle Werkzeugnamen mit Präfix `mcp__Riecken__` aus der Werkzeugliste der Session sammeln. Zusätzlich ToolSearch mit `Riecken datev` und großem `max_results` ausführen, damit neue Werkzeuge nicht übersehen werden.
2. Für jedes Werkzeug das Schema über ToolSearch `select:<name>,...` laden.
3. Die Schemata wörtlich (Felder `name`, `description`, `parameters`) in eine Datei `aktuell.json` im Scratchpad schreiben, im selben Aufbau wie `riecken-connector/baseline/tools.json` (`{"tools": [...]}`). Nichts kürzen, nichts umformulieren.
4. Vergleich ausführen:

```bash
python riecken-connector/scripts/vergleiche_baseline.py \
  --baseline riecken-connector/baseline/tools.json \
  --aktuell <scratchpad>/aktuell.json \
  --bericht riecken-connector/berichte/JJJJ-MM-TT.md
```

Exit-Code 0: keine Änderungen. Exit-Code 1: Änderungen. Exit-Code 2: technischer Fehler.

## 3. Keine Änderungen

Kein Commit, kein Branch. Kurz zusammenfassen: Datum, Anzahl Werkzeuge, Ergebnis des Health-Checks, „keine Änderungen im Leistungsumfang“. Den Bericht aus Schritt 2.4 nicht ins Repository übernehmen.

## 4. Änderungen gefunden

### 4.1 Einordnen

Jede Änderung einer der Kategorien zuordnen:

- **Neues Werkzeug**: Für jeden Skill in [LEISTUNGSUMFANG.md](LEISTUNGSUMFANG.md) Abschnitt 3 prüfen, ob das Werkzeug einen bestehenden Arbeitsschritt verbessert (genauer, vollständiger, weniger Aufrufe) oder eine dort dokumentierte Lücke schließt (Abschnitt 4). Nur dann einarbeiten.
- **Entferntes Werkzeug**: Jeden Skill, der es nutzt, auf einen Ersatz umstellen. Gibt es keinen Ersatz, den betroffenen Schritt als `NICHT_PRUEFBAR` beziehungsweise als manuellen Schritt ausweisen und das im Bericht hervorheben.
- **Geänderter Parameter, Pflichtparameter oder Werteliste**: Alle Skill-Texte, die das Werkzeug mit Parametern nennen, anpassen.
- **Nur Beschreibung geändert**: Lesen, ob sich das Verhalten geändert hat (Limits, Standardwerte, Bestätigungspflichten, Grenzen). Verhaltensänderungen wie Parameteränderungen behandeln; reine Umformulierungen nur im Bericht nennen.

### 4.2 Einarbeiten

Für jeden betroffenen Skill:

1. Betroffene `SKILL.md` und Referenzdateien ändern. Fachliche Prüfregeln nicht verändern; nur Datenzugriff, Werkzeugnamen, Parameter und daraus folgende Grenzen.
2. Versionsnummer anheben (Patch-Stelle bei reinen Werkzeugänderungen, Minor-Stelle bei neuem Funktionsumfang) an allen Stellen, an denen die Version steht (Titel, Startnachweis, `plugin.json`, Paketvertrag in Skripten, README).
3. Vorhandene Tests des Skills ausführen (`python -m unittest discover -s tests -p "test*.py"` im Skill-Ordner; bei `bk-monatsbuchhaltung` zusätzlich `validate_package.py` nach den dortigen Vorgaben). Rote Tests beheben, nicht abschalten.
4. Installationspaket neu bauen: `zip -r outputs/<skill>-v<version>.zip <skill-ordner> -x "*/__pycache__/*" "*.pyc"`; bei `bk-monatsbuchhaltung` stattdessen `scripts/build_package.py` verwenden. README-Eintrag mit neuem Paketlink und Vorversion ergänzen.
5. Kein Live-Lauf gegen Mandantendaten. Im README-Eintrag und im Bericht ausdrücklich „kein Live-Test“ vermerken, wenn keiner stattgefunden hat.

Grenzen: Niemals schreibende Riecken-Werkzeuge in einen Skill aufnehmen, der bisher nur lesend arbeitet. Niemals die DMS-Sperre des Gesellschafterbeschlusses oder die Nur-Lesen-Regel des Monatsreviews und der Abschlussvorbereitung aufheben. Bei Zweifel die Änderung nur im Bericht vorschlagen und nicht umsetzen.

### 4.3 Baseline und Dokumentation fortschreiben

1. `riecken-connector/baseline/tools.json` durch `aktuell.json` ersetzen und `erfasst_am` setzen.
2. [LEISTUNGSUMFANG.md](LEISTUNGSUMFANG.md) aktualisieren: Tabellen in Abschnitt 1, Liste nicht freigeschalteter Werkzeuge in Abschnitt 2, Nutzungsmatrix in Abschnitt 3, Befunde in Abschnitt 4, Stand im Kopf.
3. Bericht `riecken-connector/berichte/JJJJ-MM-TT.md` ergänzen um: Liste der Änderungen, je Skill die vorgenommene Anpassung und neue Version, bewusst nicht umgesetzte Punkte mit Grund, Hinweis „kein Live-Test“.
4. Alle Tests ausführen, auch `riecken-connector/tests`.

### 4.4 Übergeben

1. Auf dem Branch `riecken-update/JJJJ-MM-TT` committen und mit `git push -u origin <branch>` pushen. Nicht nach `main` mergen, keinen Pull Request ohne Auftrag eröffnen.
2. Den Auftraggeber informieren. Die Mitteilung enthält: dass es Änderungen gab, welche Änderungen (Werkzeug, Art der Änderung), welche Skills auf welche Version gehoben wurden, wo die Installationspakete liegen, der Branch-Name, offene Punkte, Konfidenz und getroffene Annahmen. Deutsch, ohne Gendern, keine Konjunktivfloskeln.

## 5. Sprach- und Formregeln

Deutsch. Keine Gendersternchen, Binnen-I oder Partizipkonstruktionen. Aussagen direkt formulieren. Konfidenzniveau und Annahmen immer nennen. Keine Vermutungen über das Verhalten eines Werkzeugs als Tatsache ausgeben; was nicht aus dem Schema oder einem Aufruf hervorgeht, als Annahme kennzeichnen.
