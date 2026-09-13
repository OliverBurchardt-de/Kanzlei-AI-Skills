# Nutzung in anderen KIs und Programmen

Der gesamte Ordner `datev-lohn-gehalt-import` kann unverändert kopiert oder als ZIP weitergegeben werden. Er enthält die Arbeitsanweisung, die unveränderte Schnittstellen-PDF und drei DATEV-Tabellen, Textauszüge, strukturierte Kataloge, ein offenes JSON-Schema und einen Python-Konverter. Externe KI-Dienste oder Zugangsschlüssel sind für das Skript nicht erforderlich.

## KI mit Skill-Unterstützung

Den vollständigen Ordner in das von der jeweiligen Anwendung vorgesehene Skill-Verzeichnis übernehmen. Einstieg ist `SKILL.md`; relative Verweise müssen erhalten bleiben. `agents/openai.yaml` ist optionale Codex-Anzeigekonfiguration und kann von anderen Programmen ignoriert werden. Das ZIP wird nicht automatisch in jeden KI-Dienst installiert.

## KI ohne Skill-Unterstützung

ZIP entpacken und `SKILL.md`, die fachlich relevante Referenz und die Original-PDF zusammen mit den Quelldaten bereitstellen. Wenn die KI Python ausführen kann, den vollständigen Ordner einschließlich `scripts/`, `config/` und `references/kataloge/` bereitstellen. Geeigneter Auftrag:

> Verwende SKILL.md und die beigefügten Referenzen, um meine Daten für DATEV Lohn und Gehalt aufzubereiten. Bestimme den Importweg, belege die Zuordnungen und liefere Importdateien, neutrales JSON und offene Punkte. Beachte, dass die beiliegende PDF die Zeitwirtschaft und keine vollständige Stammdaten-Schnittstelle beschreibt.

Eine KI ohne Codeausführung kann das neutrale JSON und die Zuordnung vorbereiten. Die tatsächlich kodierten TXT-/INI-Dateien anschließend mit dem Python-Skript erzeugen; Text im Chat belegt keine Codepage und keine Zeilenenden.

## Andere Programme / Kommandozeile

Voraussetzung für den TXT-/INI-Export: Python 3.10 oder neuer, nur Standardbibliothek. Der optionale Neuaufbau der Kataloge aus PDFs benötigt zusätzlich pdfplumber und pypdf. Auf Windows ggf. `py -3` statt `python`; auf macOS/Linux ggf. `python3`. Alle folgenden Pfade beziehen sich auf den entpackten Skill-Ordner.

```text
python scripts/zeitwirtschaft.py examples/zeitwirtschaft.json --output ausgabe-beispiel
python scripts/zeitwirtschaft.py daten.json --check
python scripts/zeitwirtschaft.py daten.json --output ausgabe
python -m unittest discover -s tests -v
```

Der Export schreibt in einen neuen, noch nicht bestehenden Ausgabeordner, damit frühere Lieferungen erhalten bleiben. Bei Strukturfehlern endet das Programm mit Exit-Code 2 und erzeugt keine Lieferung. `--check` schreibt keine Dateien. Alle fachlichen Prüfungen aus `SKILL.md` bleiben zusätzlich erforderlich.

Die Datendatei verwendet das dokumentierte lokale Windows-1252-Profil; `--encoding ascii` ist ebenfalls möglich. ASCII lehnt Umlaute in Datensätzen ab. Die INI bleibt wegen der deutschen Feldbezeichnungen in Windows-1252. Andere Codepages müssen mit der tatsächlichen Zielkonfiguration abgeglichen und bewusst implementiert werden.

## Kanzleivorgabe und Datenbeschaffung

Die Beraternummer ist **413885**. Sie steht in `config/kanzlei.json`, wird bei fehlender Angabe im Eingabe-JSON automatisch eingesetzt und gegen abweichende Angaben abgesichert. Stammdaten bezieht die ausführende KI über den [dokumentierten MCP-Leseweg](references/stammdaten-per-mcp.md); der lokale Exporthelfer selbst enthält weder MCP-Zugangsdaten noch einen Onlineversand.

Der aktuelle Umfang endet bei TXT, INI und Prüfbericht. Die Online-API wird erst in einem späteren Schritt umgesetzt.

## Neutrales Datenmodell

`schemas/zeitwirtschaft.schema.json` beschreibt den Datenvertrag. Ein Fremdprogramm kann JSON direkt erzeugen und denselben Konverter nutzen. Das JSON ist ein Austauschmodell dieses Pakets, keine unmittelbar in DATEV importierbare Datei.

- IDs, Tagesnummern und Dezimalwerte sind Strings, z. B. `"00001"`, `"14"`, `"7.50"`.
- Optionale leere Felder weglassen oder als `""`/`null` angeben. Das normalisierte Ausgabe-JSON verwendet `""`.
- Monatszeilen benötigen `werteinheit`: `betrag`, `stunden`, `tage`, `kilometer` oder `sonstiges`; die fachliche Einheit muss aus der Lohnartzuordnung belegt sein. Kalenderzeilen verwenden die benannten Stunden-/Tagesfelder.
- Jede Zeile hat `quelle` (z. B. `Zeiten.xlsx, Tabelle September, Zeile 8`). Zusätzliche Herkunftsdaten können in einem gesonderten Zuordnungsbericht stehen.
- `korrekturmodus` bezeichnet `original`, `monat_differenz` oder `kalender_vollmonat`. Bei Korrekturen ist `korrekturnachweis` erforderlich; er dokumentiert die Vergleichs- bzw. Vollständigkeitsgrundlage. Das Skript berechnet oder bestätigt diese Grundlage nicht selbst.
- `mandanten_lohnarten` enthält bei Bedarf belegte individuelle bzw. weitere Lohnarten aus dem Zielmandanten. Aufbau und Kataloggrenzen stehen in [Kataloge](references/kataloge.md).
- `zuordnungsnachweis` nennt die fachliche Grundlage für Personalnummern/Lohnarten/Schlüssel, z. B. einen geprüften Export des Zielmandanten. Er ersetzt die Prüfung nicht.

Ausgabe: DATEV-TXT, passende INI, normalisiertes UTF-8-JSON und technischer Prüfbericht mit Prüfsummen. Der Prüfbericht nennt ausdrücklich die noch nicht automatisch geprüften Bereiche. Eine erfolgreiche technische Prüfung ist kein Nachweis des DATEV-Imports.

Die Beispieldaten sind synthetisch und dienen nur zum Ausprobieren. Original-PDF und DATEV-Marken verbleiben bei ihren Rechteinhabern; dieses Paket behauptet keine DATEV-Zertifizierung.
