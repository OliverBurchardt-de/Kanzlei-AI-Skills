#!/usr/bin/env python3
"""Belegdateiregel: ein Buchungsbeleg = genau eine eigene PDF-Datei.

Werkzeug für den Agenten, um vor dem Paketbau die Belegdateien so herzurichten,
dass jeder buchungsrelevante Vorgang als genau eine PDF-Datei in den
DATEV-Belegtransfer geht:

    info     Seitenzahl, Textebene je Seite und SHA-256 einer PDF ermitteln
    split    Sammel-PDF in je eine PDF pro Vorgang trennen (Seitenbereiche)
    merge    Auf mehrere Dateien verteiltes Belegbild zu einer PDF zusammenführen
    convert  Bilddatei (JPG/PNG/TIF/BMP/GIF) in eine PDF umwandeln

Beispiele:

    python scripts/beleg_pdf.py info --input scan.pdf
    python scripts/beleg_pdf.py split --input sammel.pdf --output-dir work/ \
        --range V0001:1-2 --range V0002:3 --range V0003:4-5
    python scripts/beleg_pdf.py merge --input seite1.pdf --input seite2.pdf --output work/V0004.pdf
    python scripts/beleg_pdf.py convert --input quittung.jpg --output work/V0005.pdf

Jedes Ergebnis wird als JSON ausgegeben (Pfad, SHA-256, Größe, Seiten) und ist
im Lauf-JSON als eigener `source_files`-Eintrag mit `derived_from` zu führen.
Abgeleitete Dateien niemals in den Eingabeordner schreiben.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

try:  # pypdf ist der bevorzugte Weg; poppler-utils dienen als Ersatz.
    from pypdf import PdfReader, PdfWriter
except ImportError:  # pragma: no cover - abhängig von der Laufzeitumgebung
    PdfReader = None  # type: ignore[assignment]
    PdfWriter = None  # type: ignore[assignment]

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif"}
RANGE_PATTERN = re.compile(r"^(?P<label>[^:]+):(?P<start>\d+)(?:-(?P<end>\d+))?$")


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_pdf(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(5) == b"%PDF-"
    except OSError:
        return False


def _require_pdf(path: Path) -> None:
    if not path.is_file():
        raise ValueError(f"Datei fehlt: {path}")
    if not is_pdf(path):
        raise ValueError(f"Keine PDF-Datei (fehlender %PDF-Header): {path}")


def _result(path: Path, **extra: Any) -> dict[str, Any]:
    item: dict[str, Any] = {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": sha256_of(path),
    }
    item.update(extra)
    return item


def _page_count_cli(path: Path) -> int:
    pdfinfo = shutil.which("pdfinfo")
    if not pdfinfo:
        raise ValueError("Weder pypdf noch pdfinfo verfügbar; Seitenzahl nicht ermittelbar.")
    output = subprocess.run([pdfinfo, str(path)], capture_output=True, text=True, check=True).stdout
    match = re.search(r"^Pages:\s+(\d+)", output, re.MULTILINE)
    if not match:
        raise ValueError(f"pdfinfo liefert keine Seitenzahl für {path}")
    return int(match.group(1))


def info(path: Path) -> dict[str, Any]:
    _require_pdf(path)
    pages: list[dict[str, Any]] = []
    if PdfReader is not None:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception as exc:  # pragma: no cover
                raise ValueError(f"PDF ist verschlüsselt und nicht lesbar: {path} ({exc})") from exc
        for number, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception:  # pragma: no cover - defekte Seite
                text = ""
            pages.append({"page": number, "text_chars": len(text.strip()), "has_text_layer": bool(text.strip())})
        page_count = len(reader.pages)
    else:  # pragma: no cover
        page_count = _page_count_cli(path)
        pages = [{"page": number, "text_chars": None, "has_text_layer": None} for number in range(1, page_count + 1)]
    text_pages = sum(1 for page in pages if page["has_text_layer"])
    if text_pages == 0:
        readability = "image_only"
    elif text_pages < page_count:
        readability = "partially_readable"
    else:
        readability = "readable"
    return _result(
        path,
        page_count=page_count,
        pages=pages,
        suggested_readability=readability,
        note=(
            "Keine Textebene: Beleg über das Belegbild auswerten; fehlende OCR allein ist kein Rot-Grund."
            if readability == "image_only" else ""
        ),
    )


def parse_ranges(values: list[str], page_count: int) -> list[tuple[str, int, int]]:
    ranges: list[tuple[str, int, int]] = []
    seen: set[int] = set()
    for raw in values:
        match = RANGE_PATTERN.match(raw.strip())
        if not match:
            raise ValueError(f"Ungültiger Seitenbereich {raw!r}; erwartet <Vorgang>:<von>[-<bis>]")
        label = match.group("label").strip()
        start = int(match.group("start"))
        end = int(match.group("end") or start)
        if start < 1 or end < start or end > page_count:
            raise ValueError(f"Seitenbereich {raw!r} liegt außerhalb von 1-{page_count}")
        overlap = seen.intersection(range(start, end + 1))
        if overlap:
            raise ValueError(f"Seitenbereich {raw!r} überschneidet sich mit einem anderen Vorgang (Seiten {sorted(overlap)})")
        seen.update(range(start, end + 1))
        ranges.append((label, start, end))
    if not ranges:
        raise ValueError("Mindestens ein Seitenbereich (--range) ist erforderlich.")
    return ranges


def _safe_name(label: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", label).strip("_")
    return cleaned or "beleg"


def split(path: Path, output_dir: Path, ranges: list[str]) -> list[dict[str, Any]]:
    _require_pdf(path)
    output_dir.mkdir(parents=True, exist_ok=True)
    if output_dir.resolve() == path.resolve().parent:
        raise ValueError("Abgeleitete PDFs nicht neben der Originaldatei im Eingabeordner ablegen; eigenen Arbeitsordner verwenden.")
    results: list[dict[str, Any]] = []
    if PdfReader is not None:
        reader = PdfReader(str(path))
        page_count = len(reader.pages)
        parsed = parse_ranges(ranges, page_count)
        for label, start, end in parsed:
            writer = PdfWriter()
            for number in range(start - 1, end):
                writer.add_page(reader.pages[number])
            target = output_dir / f"{_safe_name(label)}.pdf"
            with target.open("wb") as handle:
                writer.write(handle)
            results.append(_result(target, label=label, pages=f"{start}-{end}", derived_from=str(path), method="split"))
    else:  # pragma: no cover - poppler-Ersatzweg
        pdfseparate = shutil.which("pdfseparate")
        pdfunite = shutil.which("pdfunite")
        if not pdfseparate or not pdfunite:
            raise ValueError("Weder pypdf noch poppler-utils (pdfseparate/pdfunite) verfügbar.")
        page_count = _page_count_cli(path)
        parsed = parse_ranges(ranges, page_count)
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            subprocess.run([pdfseparate, str(path), str(temp / "p-%d.pdf")], check=True)
            for label, start, end in parsed:
                target = output_dir / f"{_safe_name(label)}.pdf"
                parts = [str(temp / f"p-{number}.pdf") for number in range(start, end + 1)]
                if len(parts) == 1:
                    shutil.copyfile(parts[0], target)
                else:
                    subprocess.run([pdfunite, *parts, str(target)], check=True)
                results.append(_result(target, label=label, pages=f"{start}-{end}", derived_from=str(path), method="split"))
    return results


def merge(inputs: list[Path], output: Path) -> dict[str, Any]:
    if len(inputs) < 2:
        raise ValueError("merge erfordert mindestens zwei Eingabedateien.")
    for item in inputs:
        _require_pdf(item)
    output.parent.mkdir(parents=True, exist_ok=True)
    if PdfWriter is not None:
        writer = PdfWriter()
        for item in inputs:
            for page in PdfReader(str(item)).pages:
                writer.add_page(page)
        with output.open("wb") as handle:
            writer.write(handle)
    else:  # pragma: no cover
        pdfunite = shutil.which("pdfunite")
        if not pdfunite:
            raise ValueError("Weder pypdf noch pdfunite verfügbar.")
        subprocess.run([pdfunite, *[str(item) for item in inputs], str(output)], check=True)
    return _result(output, derived_from=[str(item) for item in inputs], method="merge")


def convert(path: Path, output: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"Datei fehlt: {path}")
    if path.suffix.lower() not in IMAGE_EXTENSIONS:
        raise ValueError(f"convert unterstützt nur Bilddateien {sorted(IMAGE_EXTENSIONS)}: {path}")
    try:
        from PIL import Image, ImageSequence
    except ImportError as exc:  # pragma: no cover
        raise ValueError("Pillow ist nicht verfügbar; Bild kann nicht in PDF umgewandelt werden.") from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(path) as image:
        frames = [frame.convert("RGB") for frame in ImageSequence.Iterator(image)]
    if not frames:
        raise ValueError(f"Bilddatei enthält keine Seite: {path}")
    first, rest = frames[0], frames[1:]
    first.save(output, "PDF", save_all=bool(rest), append_images=rest, resolution=200.0)
    return _result(output, derived_from=str(path), method="convert", page_count=len(frames))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p_info = sub.add_parser("info")
    p_info.add_argument("--input", required=True, type=Path)
    p_split = sub.add_parser("split")
    p_split.add_argument("--input", required=True, type=Path)
    p_split.add_argument("--output-dir", required=True, type=Path)
    p_split.add_argument("--range", action="append", default=[], help="<Vorgang>:<von>[-<bis>], mehrfach")
    p_merge = sub.add_parser("merge")
    p_merge.add_argument("--input", action="append", required=True, type=Path)
    p_merge.add_argument("--output", required=True, type=Path)
    p_convert = sub.add_parser("convert")
    p_convert.add_argument("--input", required=True, type=Path)
    p_convert.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "info":
            payload: Any = info(args.input)
        elif args.command == "split":
            payload = split(args.input, args.output_dir, args.range)
        elif args.command == "merge":
            payload = merge(args.input, args.output)
        else:
            payload = convert(args.input, args.output)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
