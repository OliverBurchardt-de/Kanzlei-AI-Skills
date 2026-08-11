# -*- coding: utf-8 -*-
"""Deterministische Wesentlichkeits- und Vergleichslogik."""
from __future__ import annotations

from decimal import Decimal
from typing import Iterable, Any

from abgleich import geld, summe


def wesentlichkeit(vorsteuerergebnis: Any, mindestbetrag: Any = "250.00") -> Decimal:
    ergebnis = abs(geld(vorsteuerergebnis)) * Decimal("0.01")
    minimum = geld(mindestbetrag)
    return max(ergebnis, minimum).quantize(Decimal("0.01"))


def regelmaessig(letzte_vier_monate: Iterable[Any]) -> bool:
    werte = list(letzte_vier_monate)
    if len(werte) != 4:
        raise ValueError("Es werden genau vier Monatswerte erwartet")
    return sum(1 for wert in werte if geld(wert) != Decimal("0.00")) >= 3


def ueblicher_monatswert(letzte_bebuchte_monate: Iterable[Any]) -> Decimal:
    werte = [geld(w) for w in letzte_bebuchte_monate if geld(w) != Decimal("0.00")]
    if len(werte) < 3:
        raise ValueError("Mindestens drei tatsächlich bebuchte Monate erforderlich")
    letzte_drei = werte[-3:]
    return (summe(letzte_drei) / Decimal("3")).quantize(Decimal("0.01"))


def wesentliche_abweichung(
    aktueller_wert: Any,
    vergleichswert: Any,
    schwelle: Any,
    prozentgrenze: Any = "50",
) -> bool:
    aktuell = geld(aktueller_wert)
    vergleich = geld(vergleichswert)
    grenze = geld(schwelle)
    absolute_abweichung = abs(aktuell - vergleich)
    if absolute_abweichung < grenze:
        return False
    if vergleich == Decimal("0.00"):
        return aktuell != Decimal("0.00")
    prozent = absolute_abweichung / abs(vergleich) * Decimal("100")
    return prozent > Decimal(str(prozentgrenze))


if __name__ == "__main__":
    assert wesentlichkeit("10000") == Decimal("250.00")
    assert wesentlichkeit("50000") == Decimal("500.00")
    assert regelmaessig([100, 100, 0, 100]) is True
    assert ueblicher_monatswert([100, 110, 120]) == Decimal("110.00")
    assert wesentliche_abweichung(2000, 1000, 250) is True
    print("wesentlichkeit.py: alle Selbsttests OK")
