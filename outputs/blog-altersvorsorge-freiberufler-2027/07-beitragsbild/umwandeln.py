"""Beitragsbild auf Hausformat bringen: 1600 x 900, WebP verlustbehaftet, Qualität 82, ohne Metadaten.

Aufruf: python3 umwandeln.py quelle.png ziel.webp
Zuschnitt mittig auf 16:9, dann Verkleinerung mit Lanczos.
"""
import sys
from PIL import Image

quelle, ziel = sys.argv[1], sys.argv[2]
im = Image.open(quelle).convert("RGB")
b, h = im.size
soll = 16 / 9
if b / h > soll:
    nb = round(h * soll)
    links = (b - nb) // 2
    im = im.crop((links, 0, links + nb, h))
elif b / h < soll:
    nh = round(b / soll)
    oben = (h - nh) // 2
    im = im.crop((0, oben, b, oben + nh))
im = im.resize((1600, 900), Image.Resampling.LANCZOS)
im.save(ziel, "WEBP", quality=82, method=6)
print(ziel, im.size)
