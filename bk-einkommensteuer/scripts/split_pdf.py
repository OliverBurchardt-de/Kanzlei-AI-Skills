#!/usr/bin/env python3
"""Split an unsigned PDF into traceable upload files for DATEV Meine Steuern."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from pathlib import Path

from pypdf import PdfReader, PdfWriter


MANIFEST_FIELDS = [
    "upload_id",
    "upload_filename",
    "beleg_id_original",
    "original_filename",
    "original_sha256",
    "page_from",
    "page_to",
    "person",
    "topic",
    "object_id",
    "upload_sha256",
    "page_count",
    "status",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_token(value: object, fallback: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Za-z0-9_-]+", "-", text).strip("-_")
    return text[:60] or fallback


def has_signature(reader: PdfReader) -> bool:
    fields = reader.get_fields() or {}
    return any(str(field.get("/FT", "")) == "/Sig" for field in fields.values())


def load_spec(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("Split specification must be a non-empty JSON array")
    required = {"upload_id", "beleg_id", "year", "topic", "page_from", "page_to"}
    seen_ids: set[str] = set()
    used_pages: set[int] = set()
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Spec row {index} must be an object")
        missing = required - set(item)
        if missing:
            raise ValueError(f"Spec row {index} misses: {sorted(missing)}")
        upload_id = str(item["upload_id"]).strip()
        if upload_id in seen_ids:
            raise ValueError(f"Duplicate upload_id: {upload_id}")
        seen_ids.add(upload_id)
        page_from = int(item["page_from"])
        page_to = int(item["page_to"])
        if page_from < 1 or page_to < page_from:
            raise ValueError(f"Invalid page range in {upload_id}: {page_from}-{page_to}")
        current_pages = set(range(page_from, page_to + 1))
        overlap = used_pages & current_pages
        if overlap:
            raise ValueError(f"Page reuse is not allowed; {upload_id} overlaps pages {sorted(overlap)}")
        used_pages.update(current_pages)
    return data


def output_name(item: dict) -> str:
    upload_id = safe_token(item["upload_id"], "UPL")
    year = safe_token(item["year"], "VZ")
    topic = safe_token(item["topic"], "Thema")
    object_id = safe_token(item.get("object_id"), "ohne-Objekt")
    return f"{upload_id}_{year}_{topic}_{object_id}.pdf"


def split_pdf(input_pdf: Path, spec_path: Path, output_dir: Path) -> list[dict]:
    input_pdf = input_pdf.resolve()
    spec_path = spec_path.resolve()
    output_dir = output_dir.resolve()
    if input_pdf.suffix.lower() != ".pdf":
        raise ValueError("Input must be a PDF")
    if not input_pdf.is_file():
        raise FileNotFoundError(input_pdf)
    if output_dir == input_pdf.parent:
        raise ValueError("Output directory must differ from the original directory")

    items = load_spec(spec_path)
    reader = PdfReader(str(input_pdf), strict=False)
    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs are not split automatically")
    if has_signature(reader):
        raise ValueError("Digitally signed PDFs are not split automatically")

    total_pages = len(reader.pages)
    original_hash = sha256(input_pdf)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []
    planned_names: set[str] = set()

    for item in items:
        page_from = int(item["page_from"])
        page_to = int(item["page_to"])
        if page_to > total_pages:
            raise ValueError(
                f"Page range {page_from}-{page_to} exceeds {total_pages} pages in {input_pdf.name}"
            )
        filename = output_name(item)
        lowered = filename.casefold()
        if lowered in planned_names:
            raise ValueError(f"Filename collision: {filename}")
        planned_names.add(lowered)
        target = output_dir / filename
        if target.exists():
            raise FileExistsError(f"Refusing to overwrite: {target}")

        writer = PdfWriter()
        for page_number in range(page_from - 1, page_to):
            writer.add_page(reader.pages[page_number])
        with target.open("xb") as stream:
            writer.write(stream)

        reopened = PdfReader(str(target), strict=False)
        expected_pages = page_to - page_from + 1
        if len(reopened.pages) != expected_pages:
            raise RuntimeError(f"Page validation failed for {target.name}")

        manifest.append(
            {
                "upload_id": str(item["upload_id"]),
                "upload_filename": filename,
                "beleg_id_original": str(item["beleg_id"]),
                "original_filename": input_pdf.name,
                "original_sha256": original_hash,
                "page_from": page_from,
                "page_to": page_to,
                "person": str(item.get("person", "")),
                "topic": str(item["topic"]),
                "object_id": str(item.get("object_id", "")),
                "upload_sha256": sha256(target),
                "page_count": expected_pages,
                "status": "bereit",
            }
        )

    json_path = output_dir / "uploadmanifest.json"
    csv_path = output_dir / "uploadmanifest.csv"
    if json_path.exists() or csv_path.exists():
        raise FileExistsError("Refusing to overwrite an existing upload manifest")
    json_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=MANIFEST_FIELDS, delimiter=";")
        writer.writeheader()
        writer.writerows(manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    manifest = split_pdf(args.input, args.spec, args.output_dir)
    print(json.dumps({"created": len(manifest), "output_dir": str(args.output_dir.resolve())}))


if __name__ == "__main__":
    main()
