#!/usr/bin/env python3
"""SVG-Schaubild nach WebP rendern, mit vorgeschalteter Breitenpruefung.

Gehoert zu references/SCHAUBILDER.md.

Abhaengigkeiten:
    pip install cairosvg pillow

Aufruf:
    python3 svg_nach_webp.py schaubild-name.svg
    python3 svg_nach_webp.py schaubild-name.svg --breite 1200
"""
import argparse
import pathlib
import re
import sys


# Georgia: mittlere Zeichenbreite als Anteil der Schriftgroesse.
# Erfahrungswert aus der Praxis, bewusst konservativ angesetzt.
BREITE_NORMAL = 0.52
BREITE_FETT = 0.56
MINDESTLUFT = 20  # px Abstand zum Rand, unter dem gewarnt wird


def textbreite(text: str, groesse: float, fett: bool = False) -> float:
    return len(text) * groesse * (BREITE_FETT if fett else BREITE_NORMAL)


def pruefe_texte(svg: str) -> list[str]:
    """Grobpruefung: laeuft ein Text ueber den rechten Rand der Leinwand?

    Erkennt keine Kollisionen innerhalb von Kaesten - dafuer ist die
    Kontrolle beim Bauen zustaendig. Faengt aber den haeufigsten Fehler ab.
    """
    vb = svg.split('viewBox="')[1].split('"')[0].split()
    leinwand = float(vb[2])
    warnungen = []

    muster = re.compile(
        r'<text[^>]*\bx="([\d.]+)"[^>]*?font-size="([\d.]+)"([^>]*)>([^<]*)</text>')
    for treffer in muster.finditer(svg):
        x = float(treffer.group(1))
        groesse = float(treffer.group(2))
        attribute = treffer.group(3)
        inhalt = treffer.group(4).strip()
        if not inhalt:
            continue
        if 'text-anchor="end"' in attribute or 'text-anchor="middle"' in attribute:
            continue  # rechtsbuendig oder zentriert: Startpunkt ist nicht der Anfang
        fett = 'font-weight="bold"' in attribute
        ende = x + textbreite(inhalt, groesse, fett)
        if ende > leinwand - MINDESTLUFT:
            warnungen.append(
                f'  "{inhalt[:48]}" endet bei {ende:.0f}, Leinwand {leinwand:.0f}')
    return warnungen


def rendern(pfad: pathlib.Path, breite: int) -> pathlib.Path:
    try:
        import cairosvg
        from PIL import Image
    except ImportError as fehler:
        sys.exit(f'Fehlende Abhaengigkeit: {fehler}\n'
                 'Installation: pip install cairosvg pillow')

    svg = pfad.read_text(encoding='utf-8')

    warnungen = pruefe_texte(svg)
    if warnungen:
        print('WARNUNG - Text laeuft moeglicherweise ueber den Rand:')
        print('\n'.join(warnungen))
        print()

    # Hoehe aus dem Seitenverhaeltnis, nicht schaetzen - sonst verzerrt das Bild
    vb = svg.split('viewBox="')[1].split('"')[0].split()
    hoehe = round(breite * float(vb[3]) / float(vb[2]))

    tmp = pfad.with_suffix('.tmp.png')
    cairosvg.svg2png(url=str(pfad), write_to=str(tmp),
                     output_width=breite, output_height=hoehe,
                     background_color='white')

    ziel = pfad.with_suffix('.webp')
    # Verlustfrei: bei Grafiken mit Text und Flaechen nicht groesser als lossy,
    # aber ohne Artefakte an den Buchstabenkanten.
    Image.open(tmp).convert('RGB').save(ziel, 'WEBP', lossless=True, method=6)
    tmp.unlink()

    kb = ziel.stat().st_size / 1024
    print(f'{ziel.name}  {breite}x{hoehe}  {kb:.1f} KB')
    return ziel


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('svg', type=pathlib.Path)
    parser.add_argument('--breite', type=int, default=1760,
                        help='Ausgabebreite in Pixel (Standard 1760)')
    args = parser.parse_args()

    if not args.svg.exists():
        sys.exit(f'Nicht gefunden: {args.svg}')
    rendern(args.svg, args.breite)
