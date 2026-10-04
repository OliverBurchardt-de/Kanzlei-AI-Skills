---
name: bk-humanizer
description: Macht Texte menschlich klingend und trifft die Schreibstimme von Oliver Burchardt – für deutsche Fachtexte (Blogartikel, Mandantenschreiben, Fachbeiträge, Newsletter) ebenso wie für englischsprachige Belletristik (Romankapitel, Szenen, Tonproben). Der Skill entfernt erkennbare KI-Muster und ersetzt sie durch konkrete Formulierungszüge aus einem gemessenen Korpus echter Eigentexte, statt nur Floskeln zu streichen. Immer verwenden, wenn ein Text überarbeitet, entschwurbelt, „menschlicher", „weniger nach KI", natürlicher, schärfer oder „mehr nach mir" klingen soll; wenn gefragt wird, ob ein Entwurf nach KI klingt; wenn ein Kapitel, eine Szene oder ein Artikel lektoriert werden soll; und ebenso beim Neuschreiben, wenn der Text von Anfang an in Olivers Stimme stehen soll. Auch verwenden bei Formulierungen wie „lies das nochmal gegen", „klingt das nach mir", „nimm den KI-Sound raus", „Lektorat", „Feinschliff", „Stilprüfung". Nicht verwenden für reine Sachrecherche, Berechnungen oder Übersetzungen ohne Stilauftrag.
---

# Humanizer und Stimme Oliver Burchardt

## Wozu dieser Skill da ist

Sprachmodelle schreiben den statistischen Durchschnitt. Das Ergebnis ist
grammatisch sauber, thematisch zutreffend und vollkommen austauschbar.
Dieser Skill schließt die Lücke zwischen korrekt und eigen.

Die entscheidende Einsicht steht am Anfang, weil sie über Erfolg oder
Misserfolg jeder Überarbeitung entscheidet:

> **Streichen allein erzeugt keinen Ton.** Wer nur Floskeln entfernt,
> bekommt einen kürzeren Durchschnittstext. Jede gestrichene Stelle wird
> entweder durch einen konkreten Zug aus dem Repertoire ersetzt oder ganz
> gelöscht. Eine Lücke, die nichts füllt, war nie ein Problem.

## Register bestimmen

Bevor irgendetwas geschrieben oder geändert wird, steht fest, in welchem
Register der Text liegt. Die beiden Register teilen den Slop-Katalog, aber
sonst nichts: Satzbau, Anrede, Rhythmus und die erlaubten Züge sind
verschieden.

| Register | Was darunter fällt | Vergleichsmaßstab | Stimmdatei |
|---|---|---|---|
| **Fachtext** | Blogartikel, Mandantenschreiben, Fachbeiträge, Newsletter, Sachbuchkapitel. Deutsch, Leser wird gesiezt. | `fachtext` | `references/STIMME-FACHTEXT.md` |
| **Fiktion** | Romankapitel, Szenen, Tonproben. Englisch, Ich-Erzählung. | `fiktion-knapp` oder `fiktion-kaskade` | `references/STIMME-FIKTION.md` |

Innerhalb der Fiktion gibt es zwei Tonlagen, und sie sind nicht
austauschbar. `fiktion-knapp` ist der Dialogton aus *Three Weeks in a
Bikini*: kurze Sätze, Handlung statt Innenschau, keine Gedankenstriche.
`fiktion-kaskade` ist der Erzählton aus *A Life Between Names*, Kapitel 35:
lange, geschachtelte Sätze mit Einschüben, dazwischen eine kurze
Feststellung. Welche Tonlage gilt, sagt das Projekt; im Zweifel nachfragen,
statt zu mischen.

## Vor der Arbeit lesen

**Immer:**

1. `references/SLOP-KATALOG.md` — die Muster und was an ihre Stelle tritt.
2. Die Stimmdatei des Registers aus der Tabelle oben.

**Nach Bedarf:**

- `references/KORPUS.md`, wenn unklar ist, welcher Beispieltext als
  Maßstab taugt, oder wenn der Korpus erweitert werden soll. Die Datei sagt
  auch, welche Texte ausdrücklich **kein** Maßstab sind.
- `references/MESSWERTE.md`, wenn eine Kennzahl aus `slop_scan.py`
  eingeordnet werden muss.
- `references/VOICE-METHODE.md`, wenn der Auftrag ausdrücklich die
  VOICE-Methode nennt oder wenn ein Text von Grund auf neu entsteht.
- `references/BEISPIEL.md`, wenn unklar ist, wie weit ein Eingriff gehen
  soll. Ein Fachtext vor und nach dem Ablauf, mit Messung und Begründung
  jedes Eingriffs.
- `references/QUELLEN.md`, wenn belegt werden soll, woher ein Muster
  stammt, oder wenn jemand wissen will, wie belastbar der Katalog ist.
- `references/PFLEGE.md` — **verbindlich, sobald eine der Stimmdateien
  geändert wird.** Die Regeln liegen als erzeugte Kopien auch im Skill
  `bk-blogartikel` und im Buchrepository. Wer die Quelle ändert und den
  Abgleich überspringt, hinterlässt drei Fassungen derselben Regel.
- Die Dateien in `korpus/`, wenn der Ton unsicher ist. Ein echter Text
  kalibriert schneller als jede Regelliste.

## Ablauf

Der Ablauf gilt für die Überarbeitung eines vorhandenen Entwurfs. Beim
Neuschreiben entfallen die Durchgänge 3 und 4; an ihre Stelle tritt
`references/VOICE-METHODE.md`.

### 1. Material klären, bevor irgendetwas formuliert wird

Der häufigste Grund, warum ein Text nach Maschine klingt, ist nicht der
Stil. Es ist das Fehlen von Material, das nur dieser Autor hat. Ein Text
ohne eigene Beobachtung, ohne eigene Zahl, ohne eigenen Fall lässt sich
nicht menschlich schreiben, sondern nur menschlich anstreichen.

Prüfe deshalb zuerst, was im Entwurf aus erster Hand stammt: eigene
Verfahren, eigene Mandate, eigene Zahlen, eigene Qualifikation, eine
begründete eigene Meinung.

Fehlt das und würde der Text es tragen, frage danach, statt es zu
erfinden. Eine Frage nach der anderen, konkret:

> Schreibe noch nichts. Frage mich zu diesem Thema aus: jeweils eine Frage
> danach, was ich selbst gesehen, entschieden, erlebt oder für falsch
> gehalten habe. Hake nach, wenn meine Antwort allgemein bleibt. Höre auf,
> wenn du fünf Einzelheiten hast, die nur aus meiner Arbeit stammen können.

Wenn keine Antwort kommt, gilt die Grenze aus dem Abschnitt
**Echtheit** weiter unten.

### 2. Inhalt vor Ton

Markiere und streiche zuerst, was keine Information trägt:

- Sätze, die den vorigen Satz wiederholen;
- Beispiele, die nur die Regel noch einmal sagen;
- Absätze, die sich auf eine Überschrift beschränken;
- Fundstellen, die keine Aussage stützen;
- FAQ-Antworten, die einen Abschnitt verkürzt wiederholen;
- in der Fiktion: Nachsätze, die zusammenfassen, was die Szene gerade
  gezeigt hat.

Das lohnt sich zuerst, weil jede dieser Stellen sonst im nächsten
Durchgang stilistisch poliert würde, obwohl sie ersatzlos verschwinden
sollte.

### 3. Slop-Durchgang

Arbeite `references/SLOP-KATALOG.md` durch. Der Katalog nennt zu jedem
Muster, woran man es erkennt und was an seine Stelle tritt.

### 4. Stimm-Durchgang

Jetzt erst die Stimme. Nimm die Züge aus der Stimmdatei des Registers und
setze sie dort ein, wo Durchgang 3 eine Lücke hinterlassen hat. Das
Repertoire ist keine Liste von Phrasen zum Einsetzen, sondern eine Liste
von Bewegungen: das Urteil vor die Begründung ziehen, den Gegeneinwand
ernst nehmen, die Zahl statt des Adjektivs, den Angriff der Gegenseite zu
Ende denken.

Setze nicht alle Züge in einen Text. Zwei bis vier tragende Bewegungen
reichen. Ein Text, in dem jeder Absatz einen Signaturzug enthält, ist
wieder eine Schablone, nur eine andere.

### 5. Messen

```bash
python3 scripts/slop_scan.py ENTWURF.md --profil fachtext
python3 scripts/slop_scan.py KAPITEL.md --profil fiktion-knapp
```

Das Skript misst Satzrhythmus, Absatzrhythmus, Füllformeln,
Gedankenstriche, Dreierketten, Negativparallelen und — in der Fiktion —
gedeutete Redebegleitsätze und Filterverben. Es vergleicht gegen die
Werte des Korpus.

**Die Ausgabe ist eine Liste von Stellen zum Nachsehen, keine Mängelliste
zum Abarbeiten.** Ein verständlicher Absatz wird nicht umgebaut, weil eine
Zahl ausschlägt. Umgekehrt: Das Skript sieht nur Oberfläche. Ein Text kann
jede Kennzahl treffen und trotzdem nichts zu sagen haben. Was es
nachweislich **nicht** erkennt, steht in `references/MESSWERTE.md`.

### 6. Laut lesen

Zum Schluss der Durchgang, für den es kein Skript gibt und keinen geben
wird. Lies den Text Satz für Satz und frage bei jedem: Zwingt er mich zum
nächsten?

Für den Fachtext gibt es dafür eine brauchbare Probe: **Würde Oliver diesen
Satz einem Mandanten am Telefon so sagen?** Am Telefon gibt es keinen
Nominalstil, keine Paragraphenkette und keine Floskel, weil der andere sonst
nachfragt. Was man laut nicht sagen würde, schreibt man auch nicht.

In der Belletristik lautet die Probe anders: Lies die Dialoge laut. Hört man,
wer spricht, ohne den Begleitsatz?

Konkrete Prüfungen:

- Steht am Anfang eine Behauptung, die jemand bestreiten könnte, oder eine
  Aufwärmrunde?
- Wird irgendwo etwas auf dem Spiel stehen — Geld, eine Frist, eine
  Entscheidung, in der Fiktion eine Figur, die etwas verlieren kann?
- Gibt es eine Stelle, an der die Leserin den Satz nicht vorhersagen kann?
- Wäre der Text schwächer, wenn der Name des Autors darunter fehlte? Wenn
  nicht, fehlt er auch darin.

### 7. Abschlussfragen

Sechs Fragen, die vor der Abgabe alle mit Ja beantwortet sein müssen. Steht
irgendwo ein Nein, geht der Text noch einmal in den betroffenen Durchgang
zurück.

1. Versteht ein kluger Laie die praktische Folge?
2. Bleiben die notwendigen Fachbegriffe erhalten und erklärt?
3. Trägt jeder Absatz eine neue Information?
4. Ist jede Zahl belegt oder als Modellannahme markiert?
5. Ist jede Praxisaussage freigegeben?
6. Klingt der Text wie ein eigener Text zu diesem Problem und nicht wie die
   nächste Ausgabe derselben Vorlage?

Frage 6 lässt sich allein am Text nicht beantworten. Sie braucht den
Vergleich mit den letzten Arbeiten; das Verfahren steht in `KORPUS.md`,
Abschnitt *Serienprüfung*.

In der Belletristik treten an die Stelle von 4 und 5 zwei andere Fragen:
Bleiben die Regeln des Buches eingehalten, und nimmt diese Szene einer
späteren nichts weg?

## Echtheit

Diese Grenze ist nicht verhandelbar, weil ihre Verletzung den Autor
angreifbar macht und nicht nur den Text.

- Erfinde keine eigenen Fälle, Mandate, Verfahren, Beobachtungen oder
  Praxiszahlen. Auch nicht als Platzhalter, auch nicht „nur als Beispiel".
- Eine Tatsachenaussage in der Ich-Form ist zulässig, wenn sie aus dem
  Auftrag oder aus einem freigegebenen Eigentext stammt. Sonst nicht.
- Eine **Meinung** in der Ich-Form ist zulässig, wenn sie begründet und als
  Bewertung erkennbar ist. „Diese Empfehlung halte ich für falsch" ist eine
  Meinung. „Wir haben gerade zwei Fälle" ist eine Tatsache.
- Eine **Prognose** ist zulässig, wenn die Unsicherheit mitsteht.
- Fehlt gewünschtes Material, setze `[OLIVER-INPUT: konkrete Beobachtung
  oder Fall ergänzen]` oder formuliere neutral. Melde den Marker.
- Simuliere Menschlichkeit nicht durch erzwungenen Humor, absichtliche
  Fehler, gespielte Unsicherheit oder Umgangssprache, die nicht zu Oliver
  passt. Das fällt schneller auf als jede Floskel.

Die Schärfe, mit der der Referenzartikel zur Restnutzungsdauer über
Marktteilnehmer urteilt, ruht auf eigenen Verfahren, einem eigenen
Bewerterlehrgang und einem Interview in der Fachpresse. **Ohne eine solche
Grundlage wird dieser Ton nicht nachgeahmt.** Wer ohne eigene Fälle über
Geschäftsmodelle urteilt, wirkt nicht souverän, sondern anmaßend. Die
Meinung bezieht sich dann auf die Regelung, nicht auf Personen.

## Sprachregeln, die immer gelten

- Kein Gendern. Keine Sternchen, Doppelpunkte, Binnen-I,
  Partizipkonstruktionen. Die männliche Form oder eine sachliche
  Umformulierung. Eine Mandantin wird als Mandantin angeschrieben, sonst
  gilt die allgemeine Form.
- Kein Konjunktiv als Höflichkeitspolster. „Wir zeigen", nicht „wir möchten
  Ihnen zeigen". „Wir stellen dar", nicht „wir möchten darstellen".
- Beträge einheitlich als `300.000 EUR`.
- Normen kompakt: `§ 32d Abs. 2 EStG`.
- Keine werbliche Schlussfloskel, kein „Zögern Sie nicht".

## Ausgabe

Liefere zwei getrennte Blöcke, die nicht vermischt werden.

**Block 1 — der Text.** Nur der überarbeitete Text, ohne Anmerkungen,
ohne Marker außer offenen `[OLIVER-INPUT: …]`.

**Block 2 — das Protokoll.** Kurz und nachprüfbar:

1. Register und Vergleichsmaßstab;
2. die drei bis fünf wichtigsten Eingriffe, je mit vorher/nachher in einer
   Zeile und dem Grund;
3. die Züge aus dem Repertoire, die eingesetzt wurden;
4. die Ausgabe von `slop_scan.py` und was davon bewusst stehen bleibt;
5. offene `[OLIVER-INPUT]`-Marker;
6. was auffiel, aber nicht geändert wurde, weil es eine Entscheidung des
   Autors ist.

Punkt 6 wird nicht weggelassen. Ein Lektor, der nur meldet, was er selbst
schon behoben hat, verschweigt die Fälle, in denen er sich nicht sicher war.

## Wenn du eine Regel änderst

Die Regeln dieses Skills liegen nicht nur hier. `SLOP-KATALOG.md` und
`STIMME-FACHTEXT.md` liegen als erzeugte Kopie im Skill `bk-blogartikel`,
`SLOP-KATALOG.md` und `STIMME-FIKTION.md` im Buchrepository
`special-interest`. Das ist nötig, weil ein installierter Skill seine
Nachbarn nicht verlässlich sieht und das Buchrepository gar kein Skill ist.

**Hast du eine der drei Stimmdateien geändert, gehören diese drei Schritte
zur Änderung und nicht zu einem späteren Aufräumen:**

```bash
python3 scripts/sync_stimme.py           # Kopien schreiben
python3 scripts/sync_stimme.py --check   # muss 0 zurückgeben
```

Und dann der Schritt, der am leichtesten untergeht:

> **Sage Oliver ausdrücklich, dass `bk-humanizer` und `bk-blogartikel` neu
> installiert werden müssen, und dass die Änderung bis dahin nicht wirkt.**
> Die Installation zieht nicht von allein nach. Dieser Hinweis wird auch bei
> einer kleinen Änderung nicht weggelassen, weil die Lücke zwischen Repo und
> Installation sonst unbemerkt wächst.

Liefere dazu die neuen `.skill`-Pakete mit, damit die Installation ein Klick
bleibt:

```bash
python3 ~/.claude/skills/synced/*/skill-creator/scripts/package_skill.py bk-humanizer
```

Den Rest — welche Datei wohin geht, was bei einer von Hand geänderten Kopie
zu tun ist, warum es Kopien überhaupt gibt — regelt `references/PFLEGE.md`.
Lies die Datei, bevor du eine Stimmdatei anfasst.

## Was dieser Skill nicht tut

- Er prüft keine Rechtsaussagen und keine Fundstellen. Für Blogartikel
  bleibt dafür der Skill `bk-blogartikel` zuständig, der Evidenzprotokoll
  und Freigabeprotokoll führt.
- Er prüft keine Kontinuität in laufenden Romanprojekten. Dafür gilt die
  `AGENTS.md` des jeweiligen Buchrepositorys, die Story Bible und der
  dokumentierte Arbeitsstand.
- Er erklärt einen Text nicht für veröffentlichungsfertig. Er ersetzt keine
  fachliche und keine menschliche Freigabe.
