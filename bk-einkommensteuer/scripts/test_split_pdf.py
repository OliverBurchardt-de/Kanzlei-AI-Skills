#!/usr/bin/env python3
"""Synthetic contract test for split_pdf.py; writes no client data."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from split_pdf import load_spec, split_pdf


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="bk-est-split-") as temp:
        root = Path(temp)
        source_dir = root / "source"
        output_dir = root / "upload"
        source_dir.mkdir()
        source = source_dir / "synthetischer-sammelbeleg.pdf"

        pdf = canvas.Canvas(str(source), pagesize=A4)
        for page_number in range(1, 5):
            pdf.setFont("Helvetica-Bold", 24)
            pdf.drawString(72, 760, f"Synthetischer Sammelbeleg - Seite {page_number}")
            pdf.setFont("Helvetica", 12)
            pdf.drawString(72, 730, "Nur fuer den technischen Skill-Test.")
            pdf.showPage()
        pdf.save()

        spec = [
            {
                "upload_id": "UPL-0001",
                "beleg_id": "BEL-0001",
                "year": 2025,
                "topic": "Anlage-N",
                "person": "Person-1",
                "page_from": 1,
                "page_to": 2,
            },
            {
                "upload_id": "UPL-0002",
                "beleg_id": "BEL-0001",
                "year": 2025,
                "topic": "Anlage-V",
                "object_id": "OBJ-0001",
                "person": "Person-1",
                "page_from": 3,
                "page_to": 4,
            },
        ]
        spec_path = root / "split.json"
        spec_path.write_text(json.dumps(spec), encoding="utf-8")
        manifest = split_pdf(source, spec_path, output_dir)

        assert len(manifest) == 2
        assert source.exists() and len(PdfReader(str(source)).pages) == 4
        assert len(PdfReader(str(output_dir / manifest[0]["upload_filename"])).pages) == 2
        assert len(PdfReader(str(output_dir / manifest[1]["upload_filename"])).pages) == 2
        assert (output_dir / "uploadmanifest.json").is_file()
        assert (output_dir / "uploadmanifest.csv").is_file()
        assert all(row["status"] == "bereit" for row in manifest)

        keep_dir = os.environ.get("BK_EST_TEST_KEEP")
        if keep_dir:
            shutil.copytree(root, Path(keep_dir), dirs_exist_ok=True)

        overlapping = list(spec)
        overlapping[1] = dict(overlapping[1], page_from=2)
        overlap_path = root / "overlap.json"
        overlap_path.write_text(json.dumps(overlapping), encoding="utf-8")
        try:
            load_spec(overlap_path)
        except ValueError as exc:
            assert "Page reuse" in str(exc)
        else:
            raise AssertionError("Overlapping pages were not rejected")

    print("SPLIT_PDF_TEST_OK")


if __name__ == "__main__":
    main()
