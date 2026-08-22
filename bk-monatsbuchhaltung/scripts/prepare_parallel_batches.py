#!/usr/bin/env python3
"""Create a stable source inventory and balanced work batches for subagents."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.2"


PDF_PAGE_MARKER = re.compile(rb"/Type\s*/Page\b")
IMAGE_EXTENSIONS = {".bmp", ".gif", ".jpeg", ".jpg", ".png", ".tif", ".tiff"}
INSTRUCTION_FILENAMES = {
    "agents.md",
    "claude.md",
    "copilot-instructions.md",
    "gemini.md",
    "instruction.md",
    "instructions.md",
    "prompt.md",
    "readme.md",
    "skill.md",
    "system.md",
}


def inspect_file(path: Path) -> tuple[str, int, str]:
    digest = hashlib.sha256()
    page_markers = 0
    overlap = b""
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
            if path.suffix.casefold() == ".pdf":
                searchable = overlap + block
                page_markers += sum(
                    1
                    for match in PDF_PAGE_MARKER.finditer(searchable)
                    if match.end() > len(overlap)
                )
                overlap = searchable[-32:]
    size_units = max(1, math.ceil(path.stat().st_size / (5 * 1024 * 1024)))
    suffix = path.suffix.casefold()
    if suffix == ".pdf":
        work_units = max(1, page_markers, size_units)
        basis = "pdf_page_markers_and_size"
    elif suffix in IMAGE_EXTENSIONS:
        work_units = max(2, size_units)
        basis = "image_ocr_and_size"
    else:
        work_units = size_units
        basis = "file_size"
    return digest.hexdigest(), work_units, basis


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def zip_contains_control_artifact(path: Path) -> bool:
    try:
        with zipfile.ZipFile(path) as archive:
            members = {
                name.replace("\\", "/").strip("/").casefold()
                for name in archive.namelist()
            }
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile):
        return False
    return any(
        member.endswith("/skill.md")
        or member == "skill.md"
        or member.endswith("/.codex-plugin/plugin.json")
        or member == ".codex-plugin/plugin.json"
        or member.endswith("/agents/openai.yaml")
        or member == "agents/openai.yaml"
        for member in members
    )


def control_artifact_reason(relative_path: Path, source_path: Path) -> str | None:
    name = relative_path.name.casefold()
    parts = {part.casefold() for part in relative_path.parts}
    if name in INSTRUCTION_FILENAMES:
        return "Anleitungsdatei"
    if ".codex-plugin" in parts or name == "plugin.json" or (
        relative_path.parent.name.casefold() == "agents" and name == "openai.yaml"
    ):
        return "Plugin-Manifest"
    if relative_path.suffix.casefold() == ".zip":
        if any(marker in name for marker in ("skill", "plugin")):
            return "Skill-/Plugin-ZIP"
        if zip_contains_control_artifact(source_path):
            return "Skill-/Plugin-ZIP anhand ZIP-Inhalt"
    return None


def discover_sources(input_dir: Path, output_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    candidates: list[tuple[str, Path, Path]] = []
    excluded: list[dict[str, str]] = []
    for path in input_dir.rglob("*"):
        if not path.is_file():
            continue
        resolved = path.resolve()
        if is_relative_to(resolved, output_dir):
            continue
        relative = resolved.relative_to(input_dir)
        sort_key = relative.as_posix().casefold()
        candidates.append((sort_key, resolved, relative))

    candidates.sort(key=lambda item: (item[0], item[2].as_posix()))
    sources: list[dict[str, Any]] = []
    for _, path, relative in candidates:
        reason = control_artifact_reason(relative, path)
        if reason:
            excluded.append({"source_path": str(path), "reason": reason})
            continue
        digest, work_units, work_basis = inspect_file(path)
        sources.append(
            {
                "source_id": f"S{len(sources) + 1:06d}",
                "source_path": str(path),
                "relative_path": relative.as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": digest,
                "readability": "not_checked",
                "estimated_work_units": work_units,
                "work_estimate_basis": work_basis,
            }
        )
    return sources, excluded


def assign_batches(
    sources: list[dict[str, Any]], batch_size: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    batch_count = max(1, math.ceil(len(sources) / batch_size))
    batches = [
        {
            "batch_id": f"B{index:03d}",
            "source_files": [],
            "size_bytes": 0,
            "estimated_work_units": 0,
        }
        for index in range(1, batch_count + 1)
    ]
    by_hash: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for source in sources:
        by_hash[str(source["sha256"])].append(source)
    groups = sorted(
        by_hash.values(),
        key=lambda group: (
            -len(group),
            -sum(int(item["estimated_work_units"]) for item in group),
            -sum(int(item["size_bytes"]) for item in group),
            str(group[0]["source_id"]),
        ),
    )
    for group in groups:
        eligible = [
            batch
            for batch in batches
            if len(batch["source_files"]) + len(group) <= batch_size
        ]
        if not eligible:
            if len(group) <= batch_size:
                new_batch = {
                    "batch_id": f"B{len(batches) + 1:03d}",
                    "source_files": [],
                    "size_bytes": 0,
                    "estimated_work_units": 0,
                }
                batches.append(new_batch)
                eligible = [new_batch]
            else:
                eligible = batches
        target = min(
            eligible,
            key=lambda batch: (
                int(batch["estimated_work_units"]),
                int(batch["size_bytes"]),
                len(batch["source_files"]),
                str(batch["batch_id"]),
            ),
        )
        target["source_files"].extend(group)
        target["size_bytes"] += sum(int(item["size_bytes"]) for item in group)
        target["estimated_work_units"] += sum(
            int(item["estimated_work_units"]) for item in group
        )
    for batch in batches:
        batch["source_files"].sort(key=lambda item: str(item["source_id"]))
        for source in batch["source_files"]:
            source["batch_id"] = batch["batch_id"]
    duplicate_groups = [
        {
            "sha256": digest,
            "source_ids": [str(item["source_id"]) for item in group],
        }
        for digest, group in sorted(by_hash.items())
        if len(group) > 1
    ]
    return batches, duplicate_groups


def context_fingerprint(context: dict[str, Any]) -> str:
    serialized = json.dumps(
        context, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def inventory_fingerprint(
    sources: list[dict[str, Any]], shared_context_fingerprint: str
) -> str:
    digest = hashlib.sha256()
    digest.update(shared_context_fingerprint.encode("ascii"))
    digest.update(b"\n")
    for source in sources:
        digest.update(str(source["source_id"]).encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(source["sha256"]).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def prepare(
    input_dir: Path,
    output_dir: Path,
    context_file: Path,
    batch_size: int,
) -> dict[str, Any]:
    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()
    context_file = context_file.resolve()
    if not input_dir.is_dir():
        raise ValueError(f"Eingabeordner fehlt oder ist kein Ordner: {input_dir}")
    if is_relative_to(output_dir, input_dir):
        raise ValueError("Der Ausgabeordner darf nicht im Eingabeordner liegen")
    if is_relative_to(context_file, input_dir):
        raise ValueError("Der Arbeitskontext darf nicht im Eingabeordner liegen")
    if batch_size < 1:
        raise ValueError("--batch-size muss mindestens 1 sein")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError(f"Ausgabeordner ist nicht leer: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        shared_context = json.loads(context_file.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Arbeitskontext kann nicht gelesen werden: {context_file}: {exc}") from exc
    if not isinstance(shared_context, dict) or not shared_context:
        raise ValueError("Arbeitskontext muss ein nicht leeres JSON-Objekt sein")

    sources, excluded = discover_sources(input_dir, output_dir)
    if not sources:
        raise ValueError("Keine fachlichen Eingabedateien gefunden")
    batches, duplicate_groups = assign_batches(sources, batch_size)
    shared_context_fingerprint = context_fingerprint(shared_context)
    fingerprint = inventory_fingerprint(sources, shared_context_fingerprint)
    inventory = {
        "schema_version": SCHEMA_VERSION,
        "input_dir": str(input_dir),
        "inventory_fingerprint": fingerprint,
        "shared_context_fingerprint": shared_context_fingerprint,
        "source_files": sources,
        "excluded_control_artifacts": excluded,
        "duplicate_hash_groups": duplicate_groups,
        "batches": [
            {
                "batch_id": batch["batch_id"],
                "source_ids": [item["source_id"] for item in batch["source_files"]],
                "file_count": len(batch["source_files"]),
                "size_bytes": batch["size_bytes"],
                "estimated_work_units": batch["estimated_work_units"],
            }
            for batch in batches
        ],
    }
    write_json(output_dir / "inventory.json", inventory)
    for batch in batches:
        batch_number = int(str(batch["batch_id"])[1:])
        matching_hashes = [
            group
            for group in duplicate_groups
            if any(
                source_id in {item["source_id"] for item in batch["source_files"]}
                for source_id in group["source_ids"]
            )
        ]
        payload = {
            "schema_version": SCHEMA_VERSION,
            "batch_id": batch["batch_id"],
            "inventory_fingerprint": fingerprint,
            "shared_context_fingerprint": shared_context_fingerprint,
            "shared_context": shared_context,
            "allowed_source_ids": [item["source_id"] for item in batch["source_files"]],
            "source_files": batch["source_files"],
            "duplicate_hash_groups": matching_hashes,
            "id_namespace": {
                "transaction_prefix": f"B{batch_number:03d}-V",
                "clarification_prefix": f"B{batch_number:03d}-K",
                "accrual_prefix": f"B{batch_number:03d}-A",
                "profile_suggestion_prefix": f"B{batch_number:03d}-P",
            },
            "result_file": f"batch_{batch_number:03d}_result.json",
        }
        write_json(output_dir / f"batch_{batch_number:03d}_input.json", payload)
    return inventory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--context-file", required=True, type=Path)
    parser.add_argument("--batch-size", type=int, default=100)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        inventory = prepare(
            args.input_dir,
            args.output_dir,
            args.context_file,
            args.batch_size,
        )
    except (OSError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    print(
        f"Parallel-Inventur erstellt: {len(inventory['source_files'])} Dateien, "
        f"{len(inventory['batches'])} Batches"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
