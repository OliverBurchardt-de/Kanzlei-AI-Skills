#!/usr/bin/env python3
"""sync_stimme.py — verteilt die Stimmdateien an die Orte, die sie brauchen.

## Warum es dieses Skript gibt

Ein installierter Skill sieht seine Nachbarn nicht verlaesslich. Steht in
`bk-blogartikel` ein Verweis auf `bk-humanizer/references/...`, greift der nur,
wenn beide Skills installiert sind und das Modell vom richtigen Verzeichnis aus
sucht. Fehlt einer, bricht der Verweis still. Dasselbe gilt fuer das
Buchrepository, das gar kein Skill ist.

Die Anweisungen muessen also mitreisen. Zwei Handfassungen derselben Regel
laufen aber auseinander — genau das hat dieses Repo schon einmal erlebt, als
die Liste der verbotenen Leerformeln an einer Stelle acht und an der anderen
elf Eintraege hatte.

Der Ausweg ist die **erzeugte** Kopie. Es gibt genau eine Quelle, naemlich
`bk-humanizer/references/`. Dieses Skript schreibt die Kopien, versieht jede
mit einem Kopf, der das Bearbeiten verbietet, und kann jederzeit pruefen, ob
eine Kopie veraltet oder von Hand angefasst worden ist.

## Aufruf

    python3 sync_stimme.py            # Kopien schreiben
    python3 sync_stimme.py --check    # nur pruefen, Rueckgabe 1 bei Abweichung
    python3 sync_stimme.py --ziel blog

`--check` gehoert vor jede Freigabe und in jede Pruefschleife.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

# Wurzel des Skills (dieses Skript liegt in scripts/)
SKILL = Path(__file__).resolve().parent.parent
QUELLE = SKILL / "references"
REPO = SKILL.parent

# ---------------------------------------------------------------------------
# Ziele
#
# Jedes Ziel bekommt nur, was es braucht. Der Blog braucht die Belletristik
# nicht, das Buchrepository nicht den Fachtext. Wer alles verteilt, erzeugt
# nur mehr Stellen, die veralten koennen.
# ---------------------------------------------------------------------------

ZIELE = {
    "blog": {
        "pfad": REPO / "Blogartikel" / "references" / "stimme",
        "dateien": ["SLOP-KATALOG.md", "STIMME-FACHTEXT.md"],
        "zweck": "Skill bk-blogartikel, Register Fachtext",
    },
    "buch": {
        # Das Buchrepository liegt neben diesem. Fehlt es, wird das Ziel
        # uebersprungen und gemeldet, nicht als Fehler behandelt.
        "pfad": REPO.parent / "special-interest" / "Stimme",
        "dateien": ["SLOP-KATALOG.md", "STIMME-FIKTION.md"],
        "zweck": "Repository special-interest, Register Fiktion",
    },
}

KOPF = """<!-- ERZEUGTE KOPIE — NICHT HIER BEARBEITEN.

Quelle:  bk-humanizer/references/{name}
Zweck:   {zweck}
Pruefsumme der Quelle: {hash}

Diese Datei wird von bk-humanizer/scripts/sync_stimme.py geschrieben. Eine
Aenderung hier geht beim naechsten Lauf verloren und laesst die Fassungen
auseinanderlaufen.

Soll sich eine Regel aendern:
  1. bk-humanizer/references/{name} bearbeiten
  2. python3 bk-humanizer/scripts/sync_stimme.py
  3. python3 bk-humanizer/scripts/sync_stimme.py --check
  4. beides in einem Commit

Danach muessen die betroffenen Skills neu installiert werden, sonst arbeitet
die Installation weiter mit der alten Fassung. Siehe
bk-humanizer/references/PFLEGE.md.
-->

"""


def pruefsumme(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def kopf_bauen(name: str, zweck: str, quelltext: str) -> str:
    return KOPF.format(name=name, zweck=zweck, hash=pruefsumme(quelltext))


def erwarteter_inhalt(name: str, zweck: str) -> str | None:
    q = QUELLE / name
    if not q.is_file():
        return None
    t = q.read_text(encoding="utf-8")
    return kopf_bauen(name, zweck, t) + t


def lauf(zielnamen: list[str], nur_pruefen: bool) -> int:
    abweichungen = 0
    uebersprungen = []

    for zn in zielnamen:
        ziel = ZIELE[zn]
        ordner: Path = ziel["pfad"]

        # Beim Buchrepository ist die Abwesenheit ein normaler Zustand: Es ist
        # ein eigenes Repository und in vielen Sitzungen gar nicht geklont.
        if not ordner.parent.exists():
            uebersprungen.append(f"{zn}: {ordner.parent} nicht vorhanden")
            continue

        for name in ziel["dateien"]:
            soll = erwarteter_inhalt(name, ziel["zweck"])
            if soll is None:
                print(f"  FEHLER  Quelle fehlt: references/{name}", file=sys.stderr)
                abweichungen += 1
                continue

            datei = ordner / name
            ist = datei.read_text(encoding="utf-8") if datei.is_file() else None

            if ist == soll:
                print(f"  gleich  {datei.relative_to(REPO.parent)}")
                continue

            abweichungen += 1
            if nur_pruefen:
                grund = "fehlt" if ist is None else "veraltet oder von Hand geaendert"
                print(f"  ABWEICHUNG  {datei.relative_to(REPO.parent)} — {grund}")
            else:
                ordner.mkdir(parents=True, exist_ok=True)
                datei.write_text(soll, encoding="utf-8")
                print(f"  geschrieben  {datei.relative_to(REPO.parent)}")

    for u in uebersprungen:
        print(f"  uebersprungen  {u}")

    if nur_pruefen:
        if abweichungen:
            print(f"\n{abweichungen} Abweichung(en). "
                  "sync_stimme.py ohne --check ausfuehren und mitcommitten.")
            return 1
        print("\nAlle Kopien stimmen mit der Quelle ueberein.")
        return 0

    if abweichungen:
        print(f"\n{abweichungen} Datei(en) geschrieben. Jetzt --check laufen "
              "lassen und die betroffenen Skills neu installieren "
              "(references/PFLEGE.md).")
    else:
        print("\nNichts zu tun, alle Kopien waren aktuell.")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description="Verteilt die Stimmdateien aus bk-humanizer an Blog und Buchrepository.")
    p.add_argument("--ziel", choices=list(ZIELE) + ["alle"], default="alle")
    p.add_argument("--check", action="store_true",
                   help="nur pruefen, nichts schreiben; Rueckgabe 1 bei Abweichung")
    a = p.parse_args()

    ziele = list(ZIELE) if a.ziel == "alle" else [a.ziel]
    print(f"{'Pruefe' if a.check else 'Schreibe'} Ziele: {', '.join(ziele)}\n")
    return lauf(ziele, a.check)


if __name__ == "__main__":
    sys.exit(main())
