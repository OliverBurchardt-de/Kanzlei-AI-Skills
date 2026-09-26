# Korpus

Was als Stimmprobe taugt, was nicht, und wie der Bestand erweitert wird.

## Der Grundsatz

Ein Humanizer, der mit maschinell erzeugten Texten kalibriert wird, lernt,
seinen eigenen Durchschnitt zu reproduzieren. Deshalb gilt hier die
umgekehrte Regel zu allem sonstigen Datensammeln:

> **Wenige belegte Eigentexte schlagen viele gemischte.** Ein einziger
> unbearbeiteter Text des Autors ist als Stimmprobe mehr wert als zwanzig
> gemeinsam mit einem Modell entstandene.

Deshalb liegen in `korpus/` fünf Texte und nicht 55.

## Der Bestand

### `korpus/fachtext/` — deutscher Fachtext

| Datei | Quelle | Stufe |
|---|---|---|
| `2026-05-13-restnutzungsdauer.md` | Blog 2910, zugleich Referenzartikel in `bk-blogartikel` | A |
| `2026-08-25-familienheim.md` | Blog 3194 | A (unbestätigt) |
| `2026-08-28-praxis-im-eigenen-haus.md` | Blog 3222 | A (unbestätigt) |

### `korpus/fiktion/` — englische Belletristik

| Datei | Quelle | Stufe |
|---|---|---|
| `tonprobe-bikini-kapitel-09.md` | *Three Weeks in a Bikini*, Tonprobe v3 | A |
| `a-life-between-names-kapitel-35.md` | veröffentlichte Fassung, Kapitel 35 | A |

Beide Ausschnitte enden vor den expliziten Passagen. Für die Sprache
reicht das; wo eine explizite Szene überarbeitet wird, gilt die Regel zur
direkten Sprache aus `STIMME-FIKTION.md`, Zug 7.

## Die Stufen

- **Stufe A — Kanon.** Überwiegend oder vollständig Eigentext. Maßstab für
  Ton und Niveau. Bei Widerspruch zwischen zwei A-Texten entscheidet der
  jüngere.
- **Stufe B — brauchbar für Struktur.** Gemeinsam mit einem Modell
  entstanden. Zeigt Aufbau und Fachtiefe, nicht die Stimme.
- **Stufe C — ausdrücklich kein Maßstab.** Siehe unten.

## Wie die Auswahl zustande kam, und was daran offen ist

Am 26.09.2026 wurden alle 55 veröffentlichten Blogbeiträge maschinell
ausgewertet: Satzrhythmus, Anteil der Ich-Form, Dichte der Füllformeln.
Die drei Fachtexte oben fielen dabei zusammen auf: kein einziger Treffer
aus der Floskelliste, Streuung der Satzlängen bei 9,0 bis 9,4,
erkennbare Ich-Form mit begründeter Meinung.

Am anderen Ende standen Beiträge mit bis zu 10 Floskeltreffern je 1000
Wörter, gleichförmigem Satzrhythmus und ohne jede Ich-Form. Einer davon
ist in `MESSWERTE.md` als Gegenprobe dokumentiert.

**Hier ist eine Annahme im Spiel, und sie ist nicht bestätigt.** Aus
Messwerten folgt, dass ein Text *nicht* wie eine Schablone gebaut ist. Es
folgt daraus **nicht**, dass Oliver Burchardt ihn selbst geschrieben hat.
Für `2026-05-13-restnutzungsdauer.md` ist die Herkunft über
`bk-blogartikel/references/REFERENZARTIKEL.md` belegt; für die beiden
anderen beruht die Einstufung allein auf der Messung.

**Was zu tun ist:** Die Einstufung der beiden unbestätigten Texte gehört
von Oliver bestätigt oder korrigiert. Bis dahin steht sie im Kopf der
jeweiligen Datei als `herkunft: unbestaetigt`. Fällt einer der beiden
weg, verliert der Fachtext-Maßstab ein Drittel seiner Grundlage, und die
Referenzwerte in `slop_scan.py` sind neu zu erheben.

## Was nicht in den Kanon gehört

**Die frühen Kapitel von *A Life Between Names*.** Die `AGENTS.md` des
Buchrepositorys nennt die „unmittelbare persönliche Stimme" dieses Buches
als Referenz, und für Kapitel 35 trifft das zu. Kapitel 1 trägt sie nicht:
gedeutete Redebegleitsätze („her voice a mixture of excitement and a faint
tremor of unease"), Haltungsangaben statt Handlung („with a thoughtful
expression"), eine Streuung der Satzlängen von 11,0 gegenüber 17,2 in
Kapitel 35.

Das ist keine Kritik am Buch, sondern eine Aussage über seine Eignung als
Stimmprobe. **Wer „den Ton von *A Life Between Names*" sagt, meint
Kapitel 35 und nicht das Buch als ganzes.**

**Die Blogbeiträge bis etwa 2024.** Sie duzen den Leser und stehen näher
am Ratgeberton. Das ist ein gewachsenes Register und kein Fehler, aber
nicht der aktuelle Maßstab. Dazu `STIMME-FACHTEXT.md`, letzter Abschnitt.

**Die Beiträge mit hoher Floskeldichte.** Sie taugen als Gegenprobe beim
Prüfen des Skripts und sonst zu nichts.

**Die Musterartikel 1 bis 3 in `bk-blogartikel/references/examples/`.**
Gemeinsam mit einem Modell entstanden, Stufe B. Artikel 3 ist dort
ausdrücklich als Testfall und nicht als Vorlage gekennzeichnet.

## Den Korpus erweitern

### Was hinzugehört

Ein Text kommt in den Kanon, wenn er **überwiegend unbearbeitet vom Autor
stammt**. Auch und gerade dann, wenn er kurz ist. Länge hilft der Messung,
Echtheit hilft dem Ton, und von beidem ist Echtheit das knappere Gut.

Nicht hinzu gehören Texte, die ein Modell geschrieben und ein Mensch
freigegeben hat. Freigabe ist keine Urheberschaft.

### Blogbeiträge nachladen

Der Novamira-Zugang zur WordPress-Installation liefert die Beiträge
sauber. Ausgeführt wird das über die Fähigkeit `novamira/execute-php`:

```php
function bk_clean($c){
  $c = preg_replace('/\[\/?[a-z_]+[^\]]*\]/u', "\n", $c);   // Enfold-Shortcodes
  $c = preg_replace('/<h([1-6])[^>]*>/u', "\n\n## ", $c);
  $c = preg_replace('/<\/p>|<br\s*\/?>/u', "\n\n", $c);
  $c = wp_strip_all_tags($c);
  $c = html_entity_decode($c, ENT_QUOTES|ENT_HTML5, 'UTF-8');
  return trim(preg_replace('/\n{3,}/u', "\n\n", $c));
}
$p = get_post(3194);
return ['title' => $p->post_title, 'text' => bk_clean($p->post_content)];
```

Die Shortcode-Zeile ist nötig: Das Theme ist ein Enfold-Kind, und die
Beitragsinhalte stecken voller `[av_…]`-Blöcke, die jede Messung
verfälschen.

Neue Dateien bekommen denselben Kopf wie die vorhandenen, mit `stufe` und
`herkunft`. Ohne diese beiden Angaben wird ein Text nicht aufgenommen.

### Danach messen

Jede Aufnahme in den Kanon verschiebt die Referenzwerte. Nach einer
Erweiterung:

```bash
python3 scripts/slop_scan.py korpus/fachtext/*.md --profil fachtext --json
```

Ergeben sich Werte außerhalb der Spannen in `slop_scan.py`, wird
entschieden: Entweder der neue Text erweitert die Spanne — dann wird sie in
`REFERENZ` und in `MESSWERTE.md` nachgeführt —, oder er gehört nicht in
den Kanon. Stillschweigend bleiben die Werte nicht stehen.

## Serienprüfung

Der Korpus dient nicht nur der Kalibrierung, sondern auch der Frage, ob
sich ein Autor selbst zur Schablone wird. Vergleiche einen neuen Text mit
den letzten verfügbaren Arbeiten:

- gleicher Einstiegstyp;
- gleiche Formeln in den Zwischenüberschriften;
- gleiche Zahl und Position der Beispiele;
- wiederkehrender Rollenwechsel;
- identische Schlussform;
- wiederholte Signatursätze („Mein Rat hier", „Die eigentliche Gefahr",
  „Meine drei Kernbotschaften").

Stimmen mehrere Punkte überein, wird die Dramaturgie geändert, nicht der
Satzbau. Ein Zug aus dem Repertoire, der in jedem Text an derselben Stelle
steht, ist ein Muster wie jedes andere — nur eines, das niemand
beanstandet, weil es vom Autor selbst stammt.

## Verhältnis zu `bk-blogartikel`

Der Skill `bk-blogartikel` enthält mit `Blogartikel/references/HUMANIZER-DE.md`
und `Blogartikel/references/STILPROFIL.md` eine ältere, auf Blogartikel zugeschnittene
Fassung dieses Stoffes. Beide Fassungen sind derzeit **inhaltlich
verträglich, aber getrennt gepflegt.** Das geht eine Weile gut und
divergiert dann.

Empfehlung: `bk-blogartikel` verweist in Schritt 7 seiner Redaktionsprüfung
auf `bk-humanizer` und behält allein, was blogspezifisch ist —
Evidenzprotokoll, Artikeltypen, CMS-Handoff, Veröffentlichungssperren.
Diese Änderung ist hier **nicht** vorgenommen worden, weil sie über den
Auftrag hinausgeht und ein funktionierender Skill dabei angefasst wird.
Sie sollte aber bald kommen.
