# Pflege: wie eine Änderung an der Stimme weitergegeben wird

Diese Datei regelt, was nach jeder Änderung an den Stimmdateien zu tun ist.
**Wer eine Regel ändert, führt diesen Ablauf aus.** Sonst arbeiten die
Kopien, der Blog-Skill und die Buchprojekte weiter mit der alten Fassung,
und niemand merkt es, weil nichts sichtbar bricht.

## Warum es Kopien gibt

Ein installierter Skill sieht seine Nachbarn nicht verlässlich. Ein Verweis
von `bk-blogartikel` auf `bk-humanizer/references/…` greift nur, wenn beide
Skills installiert sind und das Modell vom richtigen Verzeichnis aus sucht.
Fehlt einer, bricht der Verweis still. Das Buchrepository `special-interest`
ist gar kein Skill und sieht ohnehin nichts.

Die Anweisungen müssen also mitreisen. Zwei Handfassungen derselben Regel
laufen aber auseinander, und das ist in diesem Repo schon einmal passiert:
Die Liste der verbotenen Leerformeln hatte an einer Stelle acht Einträge und
an der anderen elf.

Deshalb gilt:

> **Es gibt genau eine Quelle: `bk-humanizer/references/`.** Alles andere ist
> eine erzeugte Kopie, die `scripts/sync_stimme.py` schreibt. Jede Kopie
> trägt im Kopf den Hinweis, dass sie nicht bearbeitet wird, und die
> Prüfsumme ihrer Quelle.

## Was wohin geht

| Ziel | Pfad | Dateien |
|---|---|---|
| Skill `bk-blogartikel` | `Blogartikel/references/stimme/` | `SLOP-KATALOG.md`, `STIMME-FACHTEXT.md` |
| Repository `special-interest` | `special-interest/Stimme/` | `SLOP-KATALOG.md`, `STIMME-FIKTION.md` |

Jedes Ziel bekommt nur, was es braucht. Der Blog braucht die Belletristik
nicht, die Bücher nicht den Fachtext. Wer alles überall verteilt, schafft
nur mehr Stellen, die veralten.

`SKILL.md`, `MESSWERTE.md`, `KORPUS.md`, `QUELLEN.md`, `VOICE-METHODE.md`,
`BEISPIEL.md` und der Korpus werden **nicht** kopiert. Sie beschreiben den
Skill selbst, nicht die Regeln, nach denen geschrieben wird.

## Der Ablauf bei jeder Änderung

Fünf Schritte. Der fünfte wird am häufigsten vergessen und ist der, ohne den
die ganze Arbeit nicht ankommt.

**1. Nur die Quelle bearbeiten.**

```
bk-humanizer/references/SLOP-KATALOG.md
bk-humanizer/references/STIMME-FACHTEXT.md
bk-humanizer/references/STIMME-FIKTION.md
```

Eine Änderung in einer Kopie geht beim nächsten Lauf verloren.

**2. Kopien schreiben.**

```bash
python3 bk-humanizer/scripts/sync_stimme.py
```

Ist das Buchrepository in dieser Sitzung nicht geklont, meldet das Skript das
Ziel als übersprungen. Das ist kein Fehler, aber die Kopie dort ist dann
veraltet und muss nachgezogen werden, sobald das Repository verfügbar ist.

**3. Prüfen.**

```bash
python3 bk-humanizer/scripts/sync_stimme.py --check
```

Rückgabewert 1 heißt: Eine Kopie weicht ab. Das passiert auch dann, wenn
jemand eine Kopie von Hand angefasst hat — genau dafür ist die Prüfung da.

**4. Messen, wenn der Korpus oder eine Schwelle betroffen ist.**

```bash
python3 bk-humanizer/scripts/slop_scan.py bk-humanizer/korpus/fachtext/*.md --profil fachtext
```

Der Kanon muss weiter null Befunde der Stufe *Hinsehen* erzeugen. Schlägt er
an, ist entweder die Schwelle falsch gesetzt oder der neue Text gehört nicht
in den Kanon. Dazu `KORPUS.md` und `MESSWERTE.md`.

**5. Betroffene Skills neu installieren — und daran erinnern.**

Das Repo ist die maßgebliche Quelle. Die **Installation zieht nicht von
allein nach.** Nach jeder Änderung an den Stimmdateien arbeitet die
installierte Fassung weiter mit dem alten Stand, bis sie ersetzt wird.

Neu zu installieren sind:

- `bk-humanizer` — immer, wenn sich eine seiner Dateien geändert hat;
- `bk-blogartikel` — immer, wenn sich `SLOP-KATALOG.md` oder
  `STIMME-FACHTEXT.md` geändert hat, weil seine Kopien davon abhängen.

Für `special-interest` entfällt das: Dort liegen die Dateien im Repository
und werden beim Arbeiten gelesen, nicht installiert.

> **An den Nutzer:** Nach einem Lauf von `sync_stimme.py` wird Oliver
> ausdrücklich darauf hingewiesen, dass `bk-humanizer` und `bk-blogartikel`
> neu installiert werden müssen, und dass die Änderung bis dahin nicht
> wirkt. Dieser Hinweis wird nicht weggelassen, auch nicht bei einer kleinen
> Änderung, weil die Lücke zwischen Repo und Installation sonst unbemerkt
> wächst. Das Neuinstallieren selbst kann der Skill nicht übernehmen; siehe
> unten.

## Was der Skill nicht selbst kann

Die installierten Skills liegen im Container unter
`~/.claude/skills/synced/`. Dieses Verzeichnis ist eine Kopie, die **von**
claude.ai heruntergeladen wird; es gibt keinen Rückweg. Ein Schreibzugriff
dort gilt nur für die laufende Sitzung und ist mit dem Container verloren.

Es gibt auch kein Werkzeug, mit dem ein Skill in das Konto hochgeladen wird.
Der einzige Weg führt über eine `.skill`-Datei: Sie wird erzeugt mit

```bash
python3 ~/.claude/skills/synced/*/skill-creator/scripts/package_skill.py <ordner>
```

und dem Nutzer bereitgestellt. Auf der Dateikarte erscheint **Save skill**;
dieser Klick installiert. Ein Klick, aber ein menschlicher.

Wer also eine Regel ändert, liefert am Ende die neuen `.skill`-Dateien mit
und sagt, welche davon installiert werden müssen.

## Wenn eine Kopie abweicht

`--check` meldet eine Abweichung in zwei Fällen, und sie werden verschieden
behandelt.

**Die Kopie ist veraltet.** Jemand hat die Quelle geändert und den Lauf
vergessen. Lösung: Schritt 2 und 3.

**Die Kopie wurde von Hand bearbeitet.** Dann steckt in ihr eine Änderung,
die in der Quelle fehlt. **Nicht einfach überschreiben.** Erst ansehen, was
dort steht, die Änderung in die Quelle übernehmen, wenn sie richtig ist, und
dann den Lauf ausführen. Sonst ist Arbeit weg.

Erkennbar ist der zweite Fall daran, dass die Prüfsumme im Kopf der Kopie zu
ihrem eigenen Inhalt nicht passt, oder daran, dass der Kopf ganz fehlt.
