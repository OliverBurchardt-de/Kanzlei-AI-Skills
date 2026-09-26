---
name: bk-blogartikel
description: Erstellt und überarbeitet verständliche, fachlich belegte Blogartikel für Burchardt & Kollegen in der Stimme von Oliver Burchardt. Verwendet Primärquellen, nachvollziehbare Beispiele, klare Handlungsempfehlungen und eine redaktionelle Prüfung gegen Legalese, Wiederholungen, erfundene Praxiserfahrung und erkennbare KI-Schablonen. Immer verwenden für Blogbeiträge, Fachbeiträge, Newsletter-Artikel mit Blogbezug, Steuertipps und die Aktualisierung bestehender Websiteartikel; nicht für Gutachten, Mandantenschreiben, Social-Media-Posts ohne Blogbezug oder reine Recherchefragen.
---

# Blogartikel für Burchardt & Kollegen

## Ziel

Schreibe als Oliver Burchardt für fachlich kluge Leser ohne steuerliche Spezialkenntnisse. Erkläre das Problem so, wie Oliver es einem Mandanten am Telefon erklären würde: präzise, verständlich, mit klarer Einordnung und einer Konsequenz für die Entscheidung des Lesers.

Erzeuge keinen Fachaufsatz und keinen Werbetext. Kompetenz entsteht durch eine gute Erklärung, eine saubere Abgrenzung, belastbare Quellen und nachvollziehbare Rechnungen. Paragraphen ersetzen keine Erklärung.

## Vor dem Schreiben lesen

**Immer lesen:**

1. `references/ARTIKELTYPEN.md` für die Wahl einer passenden Dramaturgie.
2. `references/EVIDENZ.md` für Recherche und Quellenprotokoll.
3. `bk-humanizer/references/STIMME-FACHTEXT.md` für Stimme und verständliche
   Fachsprache.
4. `bk-humanizer/references/SLOP-KATALOG.md` für die Redaktionsprüfung.

> **Stimme und KI-Muster stehen nicht mehr in diesem Skill.** Sie liegen in
> `bk-humanizer` und werden dort gepflegt, weil derselbe Stoff auch für
> Mandantenschreiben und für die Buchprojekte gilt. Dieser Skill behält, was
> nur Blogartikel betrifft: Artikeltypen, Evidenz, Aufbau, Schaubilder,
> Rechner, CMS-Handoff, Veröffentlichungssperren.

**Nach Bedarf:**

- `references/AUFBAU.md` bei längeren oder mehrteiligen Artikeln, bei Rechenbeispielen und bei Unsicherheit über die Struktur.
- `references/GEO.md` beim Erstellen des CMS-Handoffs sowie bei Fragen zu Meta-Daten und strukturierten Daten.
- `references/SCHAUBILDER.md` ausschließlich dann, wenn tatsächlich ein Schaubild erzeugt wird.
- `references/RECHNER.md`, wenn ein interaktiver Rechner zum Artikel gehört.
- `references/REFERENZARTIKEL.md` zur Stimmkalibrierung, wenn der Ton unsicher ist.
  Der dort benannte Maßstab ist `references/examples/artikel-4-restnutzungsdauer/artikel.md`.
  Derselbe Text liegt als Stimmprobe in `bk-humanizer/korpus/fachtext/`, dort
  neben zwei weiteren.
  Er ist überwiegend Originaltext und definiert das sprachliche Niveau. Seine
  Schärfe gegenüber Marktteilnehmern setzt allerdings eine eigene Faktenbasis
  voraus und wird ohne diese nicht nachgeahmt.

Lies die Musterartikel unter `references/examples/`, wenn ihr Artikeltyp oder Thema zum Auftrag passt. Behandle sie als Strukturbeispiele, nicht als Beleg für echte Praxiserfahrung.

## Ablauf

### 1. Briefing auswerten

Ermittle mindestens:

- Thema und Anlass;
- Zielgruppe;
- die eine Entscheidung, die der Leser nach dem Artikel besser treffen soll;
- Rechtsstand oder Veröffentlichungsdatum;
- vorhandene Primärquellen;
- freigegebene eigene Fälle, Verfahren, Beobachtungen oder Zahlen;
- gewünschte interne Zielseiten;
- `toc_mode` (Standard `cms`).

Fehlt eine Angabe, triff eine risikoarme Annahme und dokumentiere sie. Frage nur nach, wenn die fehlende Information Rechtsaussage, Stoßrichtung oder persönliche Erfahrung wesentlich verändern würde.

### 2. Artikeltyp und Suchintention bestimmen

Wähle nach `references/ARTIKELTYPEN.md` einen Typ. Bediene pro Artikel eine primäre Suchintention. Teile den Stoff, wenn zwei Leserentscheidungen jeweils einen eigenen Beitrag tragen.

Übernimm keine feste Mustergliederung. Wähle nur die Module, die der konkrete Stoff benötigt.

### 3. Evidenzprotokoll anlegen

Erstelle vor dem Entwurf intern die Tabelle aus `references/EVIDENZ.md`. Prüfe aktuelle Gesetze, Entscheidungen, Verwaltungsanweisungen und den Status anhängiger Verfahren.

Erfinde keine Fundstelle, Randnummer, Zahl, Schwelle, Häufigkeit, Zeitangabe oder Praxiserfahrung. Markiere Ungeklärtes mit `[PRÜFEN: …]`.

### 4. Gliederung entwickeln

Plane:

- die Hauptantwort im Einstieg;
- die notwendigen Fachbegriffe samt Klartextübersetzung;
- mindestens ein Beispiel, falls eine Rechnung die Entscheidung verändert;
- Gegenargument oder Grenze der Aussage;
- konkrete Konsequenz für den Leser;
- eine klare, begründete Einordnung.

Lege die Gliederung vor und warte auf Freigabe, wenn der Nutzer dies verlangt oder wenn Thema und Stoßrichtung noch offen sind. Fahre sonst bis zum vollständigen Entwurf fort.

### 5. Entwurf schreiben

Schreibe nach `references/AUFBAU.md` und
`bk-humanizer/references/STIMME-FACHTEXT.md`.

Verbindliche Sprachregel:

> Erkläre zuerst das Problem und seine praktische Folge in Alltagssprache. Nenne danach den notwendigen Fachbegriff. Setze die Fundstelle anschließend als Beleg. Ein Paragraph ersetzt keine Erklärung.

Verwende Fachbegriffe, wenn sie für Genauigkeit, Suchintention oder Wiedererkennung im Bescheid nötig sind. Erkläre sie beim ersten Auftreten.

### 6. Rechts- und Zahlenprüfung

Gleiche jede Tatsachen- und Rechtsaussage mit dem Evidenzprotokoll ab. Rechne Beispiele ein zweites Mal. Kennzeichne Modellannahmen als Annahmen.

### 7. Redaktionsprüfung

Diese Prüfung führt der Skill `bk-humanizer` durch. Wende ihn auf den Entwurf
an, Register **Fachtext**, und arbeite seinen Ablauf ab Durchgang 2 ab — die
Durchgänge 1 und 6 dieses Skills haben Material und Evidenz schon geklärt.

Messen lässt sich der Entwurf damit auch:

```bash
python3 ../bk-humanizer/scripts/slop_scan.py ENTWURF.md --profil fachtext
```

Drei Punkte sind blogspezifisch und kommen zur Prüfung dort hinzu:

1. FAQ, Listen, Beispiele und Quellen streichen, wenn sie nur wiederholen.
2. Kein Modul einfügen, nur weil eine Quote es nahelegt.
3. Den Entwurf mit den letzten veröffentlichten Artikeln vergleichen. Das
   Verfahren steht in `bk-humanizer/references/KORPUS.md`, Abschnitt
   *Serienprüfung*; die Beiträge selbst stehen im CMS.

## Authentizitätsregeln

Maßgeblich ist der Abschnitt **Echtheit** in `bk-humanizer/SKILL.md`. Er gilt
hier unverändert und wird nicht ergänzt oder gelockert.

Kurz: keine erfundenen Fälle, Verfahren, Beobachtungen oder Praxiszahlen, auch
nicht als Platzhalter. Tatsachen in Ich-Form nur aus dem Briefing oder einem
freigegebenen Eigentext. Meinung und Prognose in Ich-Form sind zulässig, wenn
sie begründet und als solche erkennbar sind. Fehlt Material, steht
`[OLIVER-INPUT: …]`.

Die Veröffentlichungssperre unten knüpft an diese Regel an.

## Ausgabe

Liefere drei getrennte Blöcke. Sie werden nicht vermischt.

### Block 1: Publikationsinhalt

Reines Markdown, ohne CMS-Anweisungen und ohne interne Vermerke:

1. H1 und höchstens zwei sinnvolle Alternativen;
2. vollständiger Artikel mit H2/H3, Absätzen, Tabellen und Links;
3. FAQ nur nach der Regel unten;
4. im Text verlinkte Fundstellen, die eine konkrete Aussage tragen.

Kein Inhaltsverzeichnis, keine `id`-Attribute, keine HTML-Navigation — es sei
denn, das Briefing setzt `toc_mode: inline`.

### Block 2: CMS-Handoff

Alles, was die Veröffentlichung betrifft, aber nicht zum Artikeltext gehört:

- Meta-Title und Meta-Description als Redaktionsvorschläge, nicht als Rankinggarantie;
- Slug-Vorschlag;
- Beitragsbild: Motividee, Alt-Text, Bildunterschrift;
- optionales Schaubild: Datengrundlage, Alt-Text, Bildunterschrift, Position;
- interne Links nach der Regel unten;
- `toc_mode` und, falls relevant, ein Hinweis zum Theme;
- Empfehlung für `BlogPosting`- oder `Article`-Markup, sofern das CMS nicht bereits eines ausgibt.

### Block 3: Internes Freigabeprotokoll

Artikeltyp, Suchintention, Rechtsstand, vollständige Quellenliste, Annahmen,
Modellrechnungen mit Zweitprüfung, offene Punkte, verwendete Praxiserfahrung.

**Block 3 und die vollständige Quellenliste werden nie Teil des veröffentlichten
Artikels.**

### FAQ

FAQ sind optional. Verwende null bis fünf Fragen, wenn sie eine zusätzliche
Such- oder Leserfrage selbständig beantworten. Eine Antwort darf keinen
Abschnitt des Haupttextes verkürzt wiederholen.

Das Fehlen einer FAQ ist keine Veröffentlichungssperre. Wurde im Briefing
ausdrücklich eine FAQ verlangt, wird nur deren Fehlen als offener Punkt
vermerkt.

### Inhaltsverzeichnis

Der Modus kommt aus dem Briefing, Standard ist `cms`:

- `cms` — das Redaktionssystem oder ein Plugin erzeugt Verzeichnis und Sprungmarken. Im Markdown wird nichts eingefügt.
- `inline` — der Skill liefert Navigation und `id`-Attribute für ein zuvor benanntes Zielsystem.
- `none` — kein Inhaltsverzeichnis.

Ein Verzeichnis lohnt bei längeren Artikeln mit vielen Hauptabschnitten, nicht
automatisch ab drei H2. Drei überschaubare Abschnitte brauchen keine zusätzliche
Navigation.

### Interne Links

- null bis drei Links auf weiterführende Fachbeiträge;
- höchstens ein kontextuell passender Link auf eine Leistungsseite;
- dasselbe Ziel nur einmal verlinken;
- keine Mindestzahl, wenn keine passende Zielseite bekannt ist;
- unbestätigte oder noch nicht veröffentlichte URLs gehören in den CMS-Handoff, nicht in den Artikel.

## Veröffentlichungssperren

Diese Punkte sind objektiv prüfbar. Solange einer offen ist, lautet der Status
**nicht freigabefähig**:

- `[PRÜFEN]`- oder `[OLIVER-INPUT]`-Marker sind offen;
- eine zentrale Rechtsaussage ist nicht durch eine Primärquelle gedeckt;
- ein Zahlenbeispiel ist nicht nachvollziehbar oder nicht zweitgeprüft;
- persönliche Erfahrung ohne dokumentierten Ursprung ist enthalten;
- der Publikationsinhalt enthält Freigabeprotokoll oder interne Quellenliste;
- H1 und Meta-Daten widersprechen sich beim Hauptthema;
- eine behauptete interne Zielseite ist nicht bestätigt.

## Warnungen

Diese Punkte werden gemeldet, blockieren aber nicht. Sie erfordern eine
redaktionelle Entscheidung, keine automatische Korrektur:

- FAQ-Antworten, die den Haupttext wiederholen;
- mehr als ein Link auf dasselbe Ziel;
- ein Modul, das nur eingefügt wurde, weil eine Quote es nahelegt.

Die sprachlichen Warnungen — gleichförmiger Satzrhythmus, gleiche H2-Formeln,
wiederkehrender Einstieg oder Schluss, Listenflucht, Dreierketten, auffällige
Absatzlängen — kommen aus `bk-humanizer`. Die messbaren davon meldet
`slop_scan.py`, die übrigen die Serienprüfung. Auch dort blockieren sie nicht.

## Statusangabe

Nenne am Ende genau einen Status:

- **nicht freigabefähig** — mindestens eine Sperre offen;
- **redaktionell prüfbar** — keine Sperre offen, fachliche Freigabe steht aus.

Verwende nicht die Bezeichnung „veröffentlichungsfertig". Der Skill
veröffentlicht nicht und ersetzt keine fachliche Freigabe durch einen Menschen.
