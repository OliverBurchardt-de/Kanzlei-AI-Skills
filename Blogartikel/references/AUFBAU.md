# Aufbau, Beispiele und Länge

## Vom Leserproblem ausgehen

Definiere vor dem Schreiben einen Satz:

> Nach dem Artikel kann der Leser entscheiden, ob …

Jeder Hauptabschnitt muss zu dieser Entscheidung beitragen.

## Mögliche Module

Wähle nur passende Module und variiere ihre Reihenfolge:

- Anlass und Hauptantwort;
- konkreter Ausgangsfall;
- notwendige Begriffe;
- Rechenweg;
- Gegenposition oder Ausnahme;
- Folgen für Vertrag, Erklärung oder Einspruch;
- persönliche Einordnung;
- Handlungsschritte;
- Fazit;
- zusätzliche Leserfragen.

Nicht jeder Artikel braucht alle Module.

## Einstieg

Beantworte früh:

- Worum geht es?
- Wen betrifft es?
- Was ist die wichtigste Folge?

Beginne nicht mit einer Lexikondefinition. Wenn ein aktueller Anlass fehlt, darf ein konkreter Fall oder eine typische Fehlentscheidung den Einstieg tragen.

## Beispiele

Verwende mindestens ein vollständig nachvollziehbares Beispiel, wenn Zahlen die Entscheidung verändern.

Ein gutes Beispiel nennt:

- handelnde Personen und wirtschaftlichen Zweck;
- Ausgangswerte;
- Rechenschritte;
- Ergebnis;
- Modellannahmen und bewusst ausgeblendete Faktoren;
- den Unterschied zwischen Erwartung und steuerlicher Folge.

Ein zweites Beispiel ist nur sinnvoll, wenn es einen anderen Mechanismus zeigt, etwa einen anderen Freibetrag oder eine andere Einkunftsart.

Erfinde keine Praxisfälle. Nenne konstruierte Zahlen ausdrücklich „vereinfachtes Beispiel“ oder „Modellrechnung“.

## Fundstellen im Text

Eine Fundstelle soll belegen, nicht beeindrucken.

- Nenne die Leitentscheidung bei der ersten zentralen Aussage.
- Verlinke möglichst die Primärquelle.
- Wiederhole das Aktenzeichen nicht in jedem Abschnitt.
- Verschiebe Parallelfundstellen und vollständige Normketten in das interne
  Freigabeprotokoll.

**Kein Quellenverzeichnis im veröffentlichten Artikel.** Eine Liste mit
Aktenzeichen am Textende richtet sich an den prüfenden Kollegen, nicht an den
Mandanten. Sie wiederholt Fundstellen, die im Fließtext bereits verlinkt sind,
und beendet den Artikel mit einer Sammlung blauer Links statt mit einer Aussage.

Die tragende Entscheidung wird an der Stelle verlinkt, an der sie gebraucht
wird. Alles Weitere gehört ausschließlich in das interne Protokoll.

## Schluss

Der Schluss beantwortet die Leserentscheidung. Er darf zusammenfassen, wenn er zusätzlich gewichtet. Eine nummerierte Dreierform ist möglich, aber nicht Standard.

## Inhaltsverzeichnis

Der Modus steht im Briefing, Standard ist `cms`. Die Regeln dazu stehen in
`SKILL.md`.

Ein Verzeichnis lohnt bei längeren Artikeln mit vielen Hauptabschnitten. Drei
überschaubare Abschnitte brauchen keine zusätzliche Navigation.

Bei `toc_mode: inline` gilt: nur H2 listen, Wortlaut der Überschrift unverändert
übernehmen, semantisch ein `nav` mit `aria-labelledby`, kein JavaScript. Der
Abstand des Sprungziels zum fixierten Header ist eine Theme-Einstellung und
gehört in den CMS-Handoff, nicht in den Artikel.


## Vertikaler Rhythmus

Die Abstände tragen die Gliederung. Ein Artikel mit richtigen Überschriften und
falschen Abständen liest sich wie ein Fließtext ohne Struktur.

**Grundregel: viel Luft über einer Überschrift, wenig darunter.**

Die Überschrift gehört zu dem Text, der ihr folgt, nicht zu dem, der ihr
vorausgeht. Steht der Abstand unter der Überschrift, wirkt sie wie ein
abgetrennter Titel und der Leser verliert die Zuordnung.

Als Orientierung im Verhältnis zur Textgröße:

| Element | Abstand oben | Abstand unten |
|---|---|---|
| H2 | etwa 2,5 bis 3 Zeilen | etwa 0,5 Zeilen |
| H3 | etwa 1,5 bis 2 Zeilen | etwa 0,4 Zeilen |
| Absatz | 0 | etwa 1 Zeile |
| Tabelle, Bild, Verzeichnis | etwa 1,2 Zeilen | etwa 1,2 Zeilen |

Weitere Regeln:

- Absätze bekommen ihren Abstand ausschließlich nach unten. Wer oben und unten
  setzt, erzeugt je nach Browser doppelte oder eingeklappte Abstände.
- Die erste Überschrift eines Beitrags braucht oben keinen zusätzlichen Abstand.
- Tabellen steuern ihren Abstand über den umgebenden Wrapper, nicht selbst.
- Auf schmalen Displays werden Überschriftengrößen und Abstände reduziert, das
  Verhältnis oben zu unten bleibt gleich.

Diese Werte betreffen die Darstellung im Redaktionssystem, nicht den
Artikeltext. Sie gehören in den CMS-Handoff und werden dort einmalig als
Theme-Einstellung umgesetzt, nicht bei jedem Artikel neu geprüft.

## FAQ

FAQ sind optional. Verwende null bis fünf Fragen, die über den Haupttext hinausgehen oder eine wichtige Randfrage selbständig beantworten.

Streiche eine FAQ, wenn ihre Antwort nur einen früheren Absatz wiederholt. Formuliere die erste Antwortzeile direkt und verständlich.

## Länge

Nutze diese Bereiche als Orientierung:

| Format | Orientierung |
|---|---:|
| Kurzmeldung | 600–1.000 Wörter |
| Standardartikel | 1.200–2.000 Wörter |
| Grundlagenartikel | 1.800–3.000 Wörter |

Die Suchintention und Informationsdichte entscheiden. Es gibt keine Mindestlänge für SEO oder generative Suche.

## Wiederholungsprüfung

Markiere für jeden Absatz seine neue Information. Zwei Absätze mit derselben Information werden zusammengeführt. Wiederhole eine Kernaussage nur, wenn der neue Kontext ihre Bedeutung verändert.


## Reihenfolge am Artikelanfang

Verbindlich:

1. Titel als H1 aus dem Redaktionssystem
2. Einstieg, zwei bis vier Absätze
3. Inhaltsverzeichnis, sofern `toc_mode: inline` gesetzt ist
4. erste H2

Alle Bilddateien werden als WebP geliefert: Fotos verlustbehaftet mit Qualität
82, Schaubilder verlustfrei. Die Vorgaben dazu stehen in `SCHAUBILDER.md`.

Das Beitragsbild wird immer gesetzt, weil es Übersichtsseite und Vorschau beim
Teilen steuert. Ein zusätzliches Bild im Fließtext ist optional und lohnt nur,
wenn es etwas zeigt, das der Text nicht leisten kann — bei Rechenthemen eher
eine Grafik als ein Foto.

Kein Bild zwischen Titel und Einstieg. Der Einstieg entscheidet, ob weitergelesen
wird.

## FAQ

FAQ sind optional, null bis fünf Fragen.

Eine Frage gehört nur dann in den Block, wenn sie eine Such- oder Leserfrage
selbständig beantwortet, die der Haupttext nicht abdeckt. Eine Antwort, die
einen Abschnitt verkürzt wiederholt, wird gestrichen.

Der erste Satz beantwortet die Frage. Jede Antwort steht für sich, ohne
Rückbezug auf den Artikeltext. Fragen werden so formuliert, wie ein Mandant sie
stellt.

Das Fehlen einer FAQ ist kein Mangel.


## Links auf Leistungsseiten

Höchstens ein Link je Artikel, und nur dort, wo der Leser gerade eine Frage
entwickelt, die die Zielseite beantwortet. Nicht am Textende als Angebot.

Der Ankertext beschreibt das Ziel: „steuerliche Beratung rund um Immobilien",
nicht „hier" oder „unsere Leistungen". Suchmaschinen werten den Ankertext als
Hinweis auf den Inhalt der Zielseite.

Passt kein Thema, wird kein Link gesetzt. Ein Themensprung zur Leistungsseite
wirkt werblich und widerspricht der Regel, dass Artikel ohne Verkaufsschluss
enden.
