# -*- coding: utf-8 -*-
"""Verlustfreie DATEV-Kontonummernkonvertierung."""
from __future__ import annotations


def padding(sachkontenlaenge: int) -> int:
    if not 4 <= sachkontenlaenge <= 8:
        raise ValueError("Sachkontenlaenge muss zwischen 4 und 8 liegen")
    return 8 - sachkontenlaenge


def _nur_ziffern(kontonummer) -> str:
    s = str(kontonummer).strip()
    if not s or not s.isdigit():
        raise ValueError(f"Ungueltige Kontonummer: {kontonummer}")
    return s


def anzeige(technisch, sachkontenlaenge: int, art: str = "auto") -> str:
    """Technische Kontonummer verlustfrei in die Anzeigenummer umwandeln.

    `art` ist `sachkonto`, `personenkonto` oder `auto`. Für kritische Fälle ist
    die explizite Art vorzuziehen. Sachkonten werden links auf die bekannte
    Sachkontenlänge aufgefüllt, damit etwa 0980 erhalten bleibt.
    """
    p = padding(sachkontenlaenge)
    s = _nur_ziffern(technisch)
    if p and not s.endswith("0" * p):
        raise ValueError("Technische Kontonummer passt nicht zur Sachkontenlaenge")
    core = s[:-p] if p else s
    core = core or "0"

    if art == "auto":
        # Personenkonten beginnen nicht mit 0 und haben nach Entfernen des
        # Paddings regelmäßig eine Stelle mehr als Sachkonten.
        art = "personenkonto" if len(core) > sachkontenlaenge else "sachkonto"

    if art == "sachkonto":
        if len(core) > sachkontenlaenge:
            raise ValueError("Technische Nummer ist kein Sachkonto dieser Laenge")
        return core.zfill(sachkontenlaenge)
    if art == "personenkonto":
        if len(core) > sachkontenlaenge + 1:
            raise ValueError("Technische Nummer ist kein Personenkonto dieser Laenge")
        return core.zfill(sachkontenlaenge + 1)
    raise ValueError("art muss sachkonto, personenkonto oder auto sein")


def technisch(anzeigenummer, sachkontenlaenge: int) -> str:
    s = _nur_ziffern(anzeigenummer)
    if len(s) not in (sachkontenlaenge, sachkontenlaenge + 1):
        raise ValueError("Anzeigenummer passt nicht zur Sachkontenlaenge")
    return s + ("0" * padding(sachkontenlaenge))


def klassifiziere(anzeigenummer, sachkontenlaenge: int) -> str:
    s = _nur_ziffern(anzeigenummer)
    if len(s) == sachkontenlaenge:
        return "sachkonto"
    if len(s) == sachkontenlaenge + 1:
        if s[0] in "123456":
            return "debitor"
        if s[0] in "789":
            return "kreditor"
    raise ValueError("Kontonummer passt nicht zur Sachkontenlaenge")


if __name__ == "__main__":
    assert anzeige("9800000", 4, "sachkonto") == "0980"
    assert anzeige("9000000", 4, "sachkonto") == "0900"
    assert anzeige("15900000", 4, "sachkonto") == "1590"
    assert anzeige("701470000", 4, "personenkonto") == "70147"
    assert technisch("0980", 4) == "09800000"
    assert technisch("70147", 4) == "701470000"
    assert klassifiziere("0980", 4) == "sachkonto"
    assert klassifiziere("10002", 4) == "debitor"
    assert klassifiziere("70147", 4) == "kreditor"
    print("konto.py: alle Selbsttests OK")
