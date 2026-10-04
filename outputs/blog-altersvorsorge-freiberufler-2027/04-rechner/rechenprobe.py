"""Referenzrechnung zum Förderrechner Altersvorsorge 2027.

Unabhängig vom JavaScript des Rechners geschrieben. Dient als Rechenprobe:
gleiche Eingaben müssen im Rechner und hier dieselben Ergebnisse liefern.

Rechtsgrundlagen (Stand 04.10.2026):
- Zulagen und Sonderausgabenabzug: Altersvorsorgereformgesetz, BGBl. 2026 I Nr. 156
- Einkommensteuertarif: § 32a EStG in der für 2026 geltenden Fassung
  (der Tarif 2027 liegt nur als Regierungsentwurf vom 02.09.2026 vor)
"""
import math

MIN_EIGENBEITRAG = 120
GRENZE_STUFE_1 = 360
GEFOERDERT_MAX = 1800
KIND_MAX = 300
ABGELTUNGSTEUER = 0.25        # ohne Soli und Kirchensteuer
TEILFREISTELLUNG = 0.30       # Aktienfonds, § 20 Abs. 1 InvStG
INFLATION = 0.02
SZENARIEN = (0.02, 0.04, 0.06)


def est_grundtarif_2026(zve: float) -> int:
    x = math.floor(zve)
    if x <= 12348:
        st = 0.0
    elif x <= 17799:
        y = (x - 12348) / 10000
        st = (914.51 * y + 1400) * y
    elif x <= 69878:
        z = (x - 17799) / 10000
        st = (173.10 * z + 2397) * z + 1034.87
    elif x <= 277825:
        st = 0.42 * x - 11135.63
    else:
        st = 0.45 * x - 19470.38
    return math.floor(st)


def est(zve: float, splitting: bool) -> int:
    if splitting:
        return 2 * est_grundtarif_2026(math.floor(zve / 2))
    return est_grundtarif_2026(zve)


def zulagen(e: float, kinder: int):
    if e < MIN_EIGENBEITRAG:
        return 0.0, 0.0
    grund = 0.5 * min(e, GRENZE_STUFE_1) + 0.25 * max(min(e, GEFOERDERT_MAX) - GRENZE_STUFE_1, 0)
    kind = kinder * min(e, KIND_MAX)
    return grund, kind


def foerderung(e, kinder, zve, splitting):
    grund, kind = zulagen(e, kinder)
    z = grund + kind
    abzug = min(e, GEFOERDERT_MAX) + z
    entlastung = est(zve, splitting) - est(max(zve - abzug, 0), splitting)
    zusatz = max(0.0, entlastung - z)
    gesamt = z + zusatz
    zufluss = e + z
    netto = e - zusatz
    quote = gesamt / zufluss if zufluss > 0 else 0.0
    return dict(grund=grund, kind=kind, zulagen=z, abzug=abzug, entlastung=entlastung,
                zusatz=zusatz, gesamt=gesamt, zufluss=zufluss, netto=netto, quote=quote)


def rentenfaktor(r, n):
    return n if r == 0 else ((1 + r) ** n - 1) / r


def projektion(f, jahre, steuer_alter):
    rows = []
    for r in SZENARIEN:
        k = f["zufluss"] * rentenfaktor(r, jahre)
        steuer = k * steuer_alter
        av_netto = k - steuer
        frei = f["netto"] * rentenfaktor(r, jahre)
        gewinn = max(frei - f["netto"] * jahre, 0)
        frei_steuer = gewinn * (1 - TEILFREISTELLUNG) * ABGELTUNGSTEUER
        frei_netto = frei - frei_steuer
        rows.append(dict(r=r, kapital=k, steuer=steuer, av_netto=av_netto,
                         frei_netto=frei_netto, diff=av_netto - frei_netto,
                         real=k / (1 + INFLATION) ** jahre))
    return rows


def fall(name, e, kinder, zve, splitting, jahre, steuer_alter):
    f = foerderung(e, kinder, zve, splitting)
    p = projektion(f, jahre, steuer_alter)
    print(f"\n=== {name} ===")
    print(f"Eingaben: Eigenbeitrag {e} | Kinder {kinder} | zvE {zve} | "
          f"{'Splitting' if splitting else 'Grundtarif'} | {jahre} Jahre | Steuer im Alter {steuer_alter:.0%}")
    for k in ("grund", "kind", "zulagen", "abzug", "entlastung", "zusatz", "gesamt", "zufluss", "netto"):
        print(f"  {k:<11} {f[k]:>12,.2f}")
    print(f"  {'quote':<11} {f['quote']:>12.2%}")
    print(f"  Eigener Nettoaufwand über {jahre} Jahre: {f['netto'] * jahre:,.2f}")
    for row in p:
        print(f"  r={row['r']:.0%}: Kapital {row['kapital']:>11,.0f} | Steuer {row['steuer']:>10,.0f} | "
              f"nach Steuer {row['av_netto']:>11,.0f} | freies Depot {row['frei_netto']:>11,.0f} | "
              f"Diff {row['diff']:>+10,.0f} | real {row['real']:>10,.0f}")
    return f, p


if __name__ == "__main__":
    # Tarifkontrolle an den Zonengrenzen (Stetigkeit)
    for x in (12348, 12349, 17799, 17800, 69878, 69879, 277825, 277826):
        print(x, est_grundtarif_2026(x))

    fall("A Ärztin, ledig, ohne Kind, 1.800 EUR", 1800, 0, 90000, False, 25, 0.30)
    fall("B Familie, 2 Kinder, 300 EUR, Splitting", 300, 2, 150000, True, 25, 0.30)
    fall("C Grenzfall: 100 EUR Eigenbeitrag (unter Mindestbeitrag)", 100, 1, 40000, False, 20, 0.25)
    fall("D Berufseinsteiger, geringes Einkommen, 1.800 EUR", 1800, 0, 22000, False, 35, 0.30)
    fall("E Ärztin, Steuer im Alter 42 % (gleicher Satz)", 1800, 0, 90000, False, 25, 0.42)
    fall("F ungünstig: geringes Einkommen heute, 42 % im Alter", 1800, 0, 22000, False, 35, 0.42)
    fall("G Spitzensteuersatz, 1.800, 1 Kind", 1800, 1, 320000, False, 20, 0.42)
    fall("H Briefing-Kontrolle: 1 Kind, 300 EUR, zvE 0", 300, 1, 0, False, 25, 0.0)
