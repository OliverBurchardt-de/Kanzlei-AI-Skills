#!/usr/bin/env python3
"""Vergleicht den aktuellen Leistungsumfang des Riecken-Connectors mit der Baseline.

Aufruf:
    python vergleiche_baseline.py --baseline baseline/tools.json --aktuell aktuell.json \
        [--bericht bericht.md]

Beide Dateien tragen unter "tools" eine Liste von Werkzeugschemata, wie ToolSearch
sie liefert (Felder name, description, parameters). Der Vergleich meldet neue,
entfernte und geänderte Werkzeuge. Als Änderung gelten eine geänderte Beschreibung,
neue oder entfernte Parameter, geänderte Pflichtparameter, geänderte Enum-Werte und
geänderte Parametertypen oder -beschreibungen.

Exit-Code 0: keine Änderungen. Exit-Code 1: Änderungen gefunden. Exit-Code 2: Fehler.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _kurzname(name: str) -> str:
    return name.split("__")[-1]


def _lade(pfad: Path) -> dict[str, dict[str, Any]]:
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    werkzeuge = daten["tools"] if isinstance(daten, dict) else daten
    ergebnis: dict[str, dict[str, Any]] = {}
    for werkzeug in werkzeuge:
        name = _kurzname(werkzeug["name"])
        if name in ergebnis:
            raise ValueError(f"Werkzeug {name} ist doppelt in {pfad}.")
        ergebnis[name] = werkzeug
    return ergebnis


def _parameter(werkzeug: dict[str, Any]) -> dict[str, Any]:
    return (werkzeug.get("parameters") or {}).get("properties") or {}


def _pflicht(werkzeug: dict[str, Any]) -> set[str]:
    return set((werkzeug.get("parameters") or {}).get("required") or [])


def _enum(schema: dict[str, Any]) -> list[Any]:
    return [wert for wert in schema.get("enum") or [] if wert is not None]


def vergleiche_werkzeug(alt: dict[str, Any], neu: dict[str, Any]) -> list[str]:
    befunde: list[str] = []
    if (alt.get("description") or "") != (neu.get("description") or ""):
        befunde.append("Beschreibung geändert")
    alt_param, neu_param = _parameter(alt), _parameter(neu)
    for name in sorted(set(neu_param) - set(alt_param)):
        befunde.append(f"neuer Parameter `{name}`")
    for name in sorted(set(alt_param) - set(neu_param)):
        befunde.append(f"Parameter `{name}` entfernt")
    for name in sorted(set(alt_param) & set(neu_param)):
        a, n = alt_param[name], neu_param[name]
        if a.get("type") != n.get("type"):
            befunde.append(f"Typ von `{name}` geändert: {a.get('type')} -> {n.get('type')}")
        if _enum(a) != _enum(n):
            befunde.append(f"Werteliste von `{name}` geändert: {_enum(a)} -> {_enum(n)}")
        if (a.get("description") or "") != (n.get("description") or ""):
            befunde.append(f"Beschreibung von `{name}` geändert")
    alt_pflicht, neu_pflicht = _pflicht(alt), _pflicht(neu)
    for name in sorted(neu_pflicht - alt_pflicht):
        befunde.append(f"`{name}` ist jetzt Pflicht")
    for name in sorted(alt_pflicht - neu_pflicht):
        befunde.append(f"`{name}` ist nicht mehr Pflicht")
    return befunde


def vergleiche(baseline: dict[str, dict[str, Any]], aktuell: dict[str, dict[str, Any]]) -> dict[str, Any]:
    neu = sorted(set(aktuell) - set(baseline))
    entfernt = sorted(set(baseline) - set(aktuell))
    geaendert: dict[str, list[str]] = {}
    for name in sorted(set(baseline) & set(aktuell)):
        befunde = vergleiche_werkzeug(baseline[name], aktuell[name])
        if befunde:
            geaendert[name] = befunde
    return {
        "neu": neu,
        "entfernt": entfernt,
        "geaendert": geaendert,
        "anzahl_baseline": len(baseline),
        "anzahl_aktuell": len(aktuell),
        "aenderungen": bool(neu or entfernt or geaendert),
    }


def bericht_markdown(ergebnis: dict[str, Any], aktuell: dict[str, dict[str, Any]], datum: str) -> str:
    zeilen = [f"# Riecken-Connector: Vergleich mit der Baseline ({datum})", ""]
    zeilen.append(
        f"Werkzeuge in der Baseline: {ergebnis['anzahl_baseline']}, aktuell: {ergebnis['anzahl_aktuell']}."
    )
    zeilen.append("")
    if not ergebnis["aenderungen"]:
        zeilen.append("Keine Änderungen im Leistungsumfang festgestellt.")
        return "\n".join(zeilen) + "\n"
    if ergebnis["neu"]:
        zeilen.append("## Neue Werkzeuge")
        zeilen.append("")
        for name in ergebnis["neu"]:
            beschreibung = (aktuell[name].get("description") or "").strip()
            pflicht = ", ".join(sorted(_pflicht(aktuell[name]))) or "keine"
            zeilen.append(f"- `{name}` (Pflichtparameter: {pflicht}): {beschreibung}")
        zeilen.append("")
    if ergebnis["entfernt"]:
        zeilen.append("## Entfernte Werkzeuge")
        zeilen.append("")
        for name in ergebnis["entfernt"]:
            zeilen.append(f"- `{name}`")
        zeilen.append("")
    if ergebnis["geaendert"]:
        zeilen.append("## Geänderte Werkzeuge")
        zeilen.append("")
        for name, befunde in ergebnis["geaendert"].items():
            zeilen.append(f"- `{name}`: " + "; ".join(befunde))
        zeilen.append("")
    return "\n".join(zeilen) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--aktuell", required=True, type=Path)
    parser.add_argument("--bericht", type=Path, help="Markdown-Bericht hierhin schreiben")
    parser.add_argument("--datum", default=None, help="Datum für die Berichtsüberschrift (JJJJ-MM-TT)")
    args = parser.parse_args(argv)
    try:
        baseline = _lade(args.baseline)
        aktuell = _lade(args.aktuell)
    except (OSError, ValueError, KeyError) as fehler:
        print(f"Fehler beim Laden: {fehler}", file=sys.stderr)
        return 2
    ergebnis = vergleiche(baseline, aktuell)
    from datetime import date

    datum = args.datum or date.today().isoformat()
    text = bericht_markdown(ergebnis, aktuell, datum)
    if args.bericht:
        args.bericht.parent.mkdir(parents=True, exist_ok=True)
        args.bericht.write_text(text, encoding="utf-8")
    print(text)
    return 1 if ergebnis["aenderungen"] else 0


if __name__ == "__main__":
    sys.exit(main())
