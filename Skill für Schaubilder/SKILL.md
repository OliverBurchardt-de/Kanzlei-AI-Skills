---
name: bk-schaubilder
description: Erstellt Schaubilder im Design von Burchardt & Kollegen als SVG und WebP - Rechenwege, Gegenüberstellungen und Zeitverläufe für Blogartikel, Mandantenschreiben, Präsentationen und Leistungsseiten. Legt Farben, Schriftgrößen, Maße und Barrierefreiheit verbindlich fest und prüft Textbreiten vor der Ausgabe. Verwenden, wenn eine Grafik, ein Schaubild, eine Visualisierung oder eine Infografik erstellt oder überarbeitet werden soll. Nicht für Fotos, Diagramme aus Rohdaten oder interaktive Rechner.
---

# Schaubilder für Burchardt & Kollegen

## Ziel

Ein Schaubild macht sichtbar, was im Fließtext mühsam zu verfolgen ist: eine Zahl,
die durch mehrere Stufen wandert, oder zwei Ergebnisse aus demselben Sachverhalt.

Es ersetzt keine Erklärung und keine Tabelle. Es zeigt den Mechanismus oder das
Verhältnis — nicht beides und nicht dasselbe wie der Text daneben.

## Ablauf

**1. Prüfen, ob es sich lohnt.** Die Kriterien stehen in
`references/GESTALTUNG.md`. Im Zweifel kein Schaubild: Ein Bild, das wiederholt,
was danebensteht, kostet Ladezeit und bringt nichts.

**2. Aussage festlegen.** Ein Satz, der beschreibt, was der Betrachter mitnehmen
soll. Passt er nicht in einen Satz, ist die Aussage noch nicht klar.

**3. Zahlen sichern.** Jede Zahl im Bild muss belegt sein und mit dem
umgebenden Text übereinstimmen. Vereinfachungen gehören in die Fußnote.

**4. SVG bauen** nach `references/GESTALTUNG.md`. Farben, Schriftgrößen, Maße und
Aufbau sind dort verbindlich festgelegt.

**5. Textbreiten rechnen.** Verbindlicher Schritt, kein optionaler. Die Formel
steht in der Gestaltungsdatei. Mindestens 20 px Luft zu jeder Grenze.

**6. Nach WebP rendern** mit `scripts/svg_nach_webp.py`.

**7. Ausgeben:** WebP-Datei, SVG als Quelldatei, Alt-Text, Bildunterschrift und
ein Vorschlag zur Position.

## Nicht verhandelbar

- **Zahl unter der Beschreibung, nie daneben.** Bei rechtsbündigen Zahlen läuft
  der Beschreibungstext hinein. Häufigster Fehler.
- **Textbreiten vor der Ausgabe prüfen.** Überlappungen fallen im SVG-Quelltext
  nicht auf.
- **Gold trägt nie Information** und steht nie als Text auf Weiß. Kontrast 1,9:1.
- **Farbe allein bedeutet nichts.** Eine hervorgehobene Seite bekommt zusätzlich
  eine stärkere Kante.
- **`title` und `desc` sind Pflicht.** Die Beschreibung enthält jede Zahl, die im
  Bild steht.
- **Keine erfundenen Zahlen.** Ein Schaubild ohne belegte Datengrundlage wird
  nicht gebaut.

## Grenzen

Das Bild aktualisiert sich nicht mit dem Text. Ändert sich eine Zahl, muss es neu
erzeugt werden — deshalb die Beschränkung auf stabile Werte und höchstens zwei
Schaubilder je Dokument.

Zahlen in Grafiken sind für Suchmaschinen unsichtbar und für Screenreader nur
über den Alt-Text erreichbar. Wo Schaubild und Tabelle dieselben Werte tragen,
entfällt das Schaubild.

## Voraussetzungen

`cairosvg` und `Pillow`. Fehlen sie, liefere statt der Datei ein Bildbriefing:
Datengrundlage, gewünschte Aussage, Alt-Text-Entwurf, Bildunterschrift.
