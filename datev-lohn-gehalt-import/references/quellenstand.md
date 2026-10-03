# Quellenstand und Prüfung vom 13.09.2026

In `C:/Projekte/Kanzlei-AI-Skills` sowie den untersuchten persönlichen Codex-Skills und lokalen Claude-Plugin-Skills wurde kein vorhandener Skill für DATEV Lohn und Gehalt gefunden. Der Buchhaltungs- und der Monatsreview-Skill behandeln andere Aufgaben. Deshalb wurde `datev-lohn-gehalt-import` neu angelegt.

## Enthaltene Originalquelle

- Vom Nutzer bereitgestellte Datei: `Importschnittstelle.pdf`.
- Tatsächlicher Titel: Zeitwirtschaftsschnittstelle für das Programm Lohn und Gehalt.
- Herausgeber: DATEV eG; Dokumentstand: 13.07.2022; 24 Seiten.
- Größe: 345983 Bytes.
- SHA-256: `8c3cb9c000f357ed9e7c6d3880cd29d5d9a583f1da9ca6a32af734352ee43629`.
- Original unverändert in diesem Ordner; durchsuchbarer UTF-8-Text mit Seitenmarkern ergänzend enthalten. Die Original-PDF bleibt maßgeblich.

Alle Seiten wurden textuell ausgelesen. Header/Feldtabellen auf S. 14-15 und das INI-Muster auf S. 20-21 wurden zusätzlich visuell geprüft. Nicht jede Oberflächenabbildung wurde visuell begutachtet.

## Ergebnis

1. PDF passt zum Import von Zeitwirtschafts-Bewegungsdaten für Monats- und Kalendererfassung.
2. Kein Nachweis einer universellen LuG-Importschnittstelle oder einer vollständigen Stammdatenspezifikation.
3. Widerspruch im Muster: 11 deklarierte Felder auf S. 20, aber 12 Feldzuordnungen auf S. 20-21. Der Export verwendet konsistent 12 Felder gemäß Gleichheitsanforderung auf S. 17.
4. Die numerische 5-Stellen-Grenze gilt für DATEV-Personalnummern. Die alphanumerischen betrieblichen Nummern sind im Muster ausdrücklich durch `x` im Header unterschieden.
5. Keine eindeutige Codepage in der PDF. Windows-1252 ist als Wahl des mitgelieferten Exportprofils gekennzeichnet.
6. Die PDF ersetzt keine aktuelle Prüfung der Ausfallschlüssel, Lohnarten, Zielstammdaten und Korrekturgrundlagen.

## Aktualitätsabgleich

[DATEV Dokument 1080789](https://apps.datev.de/help-center/documents/1080789) ist der Einstieg zu Schnittstellenbeschreibungen. Der [DATEV-Hinweis vom 10.06.2026](https://developer.datev.de/en/news/details/shssmh53tmdmu4qsdu6g4hk0) nennt neue Stammdaten-Satzbeschreibungen für LuG 15.8. Die Datei des Nutzers wurde deshalb nicht als aktuelle Beschreibung aller LuG-Importwege etikettiert. Direkte Downloadversuche der gefundenen DATEV-Links waren nicht erfolgreich; Details in [Stammdaten und Grenzen](stammdaten-und-grenzen.md). Eine neuere Zeitwirtschafts-PDF wurde nicht verifiziert.

Die lokale Prüfung des Helfers verwendet ausschließlich synthetische Beispieldaten. Sie ist kein DATEV-Probeimport. Es wurden keine Mandantendaten in DATEV geschrieben.

Technische Abschlussprüfung: 18 automatisierte Tests bestanden, Skill-Frontmatter und JSON-Schema validiert, Ein-/Ausgabe-JSON gegen das Schema geprüft, relative Verweise und Originalprüfsumme geprüft. Siehe [Prüfprotokoll](validierung.json). Die erzeugten synthetischen [Beispieldateien](../examples/ausgabe/pruefbericht.json) enthalten einen gesonderten technischen Prüfbericht.

## Erweiterung 1.1.0: Dateierstellung

Nutzerfestlegung: Beraternummer 413885; Mandanten-/Personalnummern und individuelle Lohnarten aus dem LuG-Mandanten per MCP lesen. Der aktuelle Umfang endet bei der TXT-/INI-Erstellung. Onlineversand ist zurückgestellt. Die drei nachgereichten DATEV-Tabellen sind mit SHA-256, Originalzellen und Seitenbelegen im [Katalogverzeichnis](kataloge.md) enthalten. Die Klardaten-Payroll-Verträge wurden per datev_describe geprüft; kein konkreter Mandantenabruf oder DATEV-Import wurde durchgeführt.
