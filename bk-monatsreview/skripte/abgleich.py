# -*- coding: utf-8 -*-
"""Centgenauer Soll-Ist-Abgleich mit Decimal und vier Statuswerten."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Iterable, Any

CENT = Decimal("0.01")
ERLAUBTE_STATUS = {"GRUEN", "GELB", "ROT", "NICHT_PRUEFBAR"}


def _normalisiere_zahl(wert: Any) -> str:
    if isinstance(wert, Decimal):
        return format(wert, "f")
    if isinstance(wert, bool):
        raise ValueError("Boolescher Wert ist kein Geldbetrag")
    text = str(wert).strip().replace("€", "").replace(" ", "")
    if not text:
        raise ValueError("Leerer Geldbetrag")
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(".", "").replace(",", ".")
    return text


def geld(wert: Any) -> Decimal:
    try:
        return Decimal(_normalisiere_zahl(wert)).quantize(CENT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Ungueltiger Geldbetrag: {wert}") from exc


def summe(betraege: Iterable[Any]) -> Decimal:
    total = Decimal("0")
    for betrag in betraege:
        total += Decimal(_normalisiere_zahl(betrag))
    return total.quantize(CENT, rounding=ROUND_HALF_UP)


def abgleich(
    bezeichnung: str,
    soll: Any = None,
    ist: Any = None,
    pruefschritt: str = "",
    status: str | None = None,
    grund: str = "",
    quelle: str = "",
) -> dict[str, Any]:
    """Erzeugt eine auditierbare Ergebniszeile.

    Ohne ausdrücklichen Status erfolgt ein centgenauer Soll-Ist-Abgleich.
    Fehlende Werte werden als NICHT_PRUEFBAR ausgegeben.
    """
    if status is not None:
        if status not in ERLAUBTE_STATUS:
            raise ValueError(f"Ungueltiger Status: {status}")
        s = geld(soll) if soll is not None else None
        i = geld(ist) if ist is not None else None
        d = (i - s).quantize(CENT) if s is not None and i is not None else None
        return {
            "pruefpunkt": bezeichnung,
            "schritt": pruefschritt,
            "soll": s,
            "ist": i,
            "differenz": d,
            "ampel": status,
            "grund": grund,
            "quelle": quelle,
        }

    if soll is None or ist is None:
        return abgleich(
            bezeichnung,
            soll,
            ist,
            pruefschritt,
            "NICHT_PRUEFBAR",
            grund or "Soll- oder Ist-Wert fehlt",
            quelle,
        )

    s, i = geld(soll), geld(ist)
    d = (i - s).quantize(CENT)
    ok = d == Decimal("0.00")
    return {
        "pruefpunkt": bezeichnung,
        "schritt": pruefschritt,
        "soll": s,
        "ist": i,
        "differenz": d,
        "ampel": "GRUEN" if ok else "ROT",
        "grund": grund or ("centgenau" if ok else f"Abweichung {d:+.2f} EUR"),
        "quelle": quelle,
    }


def bericht(zeilen: Iterable[dict[str, Any]]) -> str:
    out = ["Pruefpunkt | Soll | Ist | Differenz | Status | Grund"]
    for z in zeilen:
        out.append(
            " | ".join(
                [
                    str(z["pruefpunkt"]),
                    "" if z["soll"] is None else str(z["soll"]),
                    "" if z["ist"] is None else str(z["ist"]),
                    "" if z["differenz"] is None else str(z["differenz"]),
                    z["ampel"],
                    z["grund"],
                ]
            )
        )
    return "\n".join(out)


if __name__ == "__main__":
    assert geld("1.234,56 €") == Decimal("1234.56")
    assert summe(["2.675"]) == Decimal("2.68")
    assert summe(["1.005"]) == Decimal("1.01")
    assert abgleich("ok", "10.00", "10.00")["ampel"] == "GRUEN"
    assert abgleich("abweichung", "10.00", "9.99")["ampel"] == "ROT"
    assert abgleich("hinweis", status="GELB", grund="pruefen")["ampel"] == "GELB"
    assert abgleich("fehlt")["ampel"] == "NICHT_PRUEFBAR"
    print("abgleich.py: alle Selbsttests OK")
