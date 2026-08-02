from __future__ import annotations

import importlib.util
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


SCRIPT_DIR = Path(__file__).resolve().parent


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Modul kann nicht geladen werden: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_package = _load_module("build_package", SCRIPT_DIR / "build_package.py")
validate_package = _load_module("validate_package", SCRIPT_DIR / "validate_package.py")


def _write_transfer(path: Path, xml_bytes: bytes) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("document.xml", xml_bytes)
        archive.writestr("beleg.tif", b"II*\x00")


def main() -> None:
    xml_bytes = build_package._document_xml(
        [{"document_guid": "01234567-89ab-cdef-0123-456789abcdef", "document_filename": "beleg.tif"}]
    )
    root = ET.fromstring(xml_bytes)
    document = next(element for element in root.iter() if element.tag.endswith("document"))
    extension = next(element for element in root.iter() if element.tag.endswith("extension"))

    assert document.attrib == {
        "guid": "01234567-89ab-cdef-0123-456789abcdef",
        "processID": "1",
    }
    assert extension.attrib["name"] == "beleg.tif"
    assert extension.attrib["{http://www.w3.org/2001/XMLSchema-instance}type"] == "File"
    assert b"accountsPayableLedger" not in xml_bytes

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        valid_path = temp_path / "Belegtransfer_12371_2026-06_001.zip"
        _write_transfer(valid_path, xml_bytes)
        errors, document_guids, booking_guids, count, advice_count = validate_package.validate_document_packages(temp_path)
        assert errors == [], errors
        assert count == 1
        assert advice_count == 0
        assert booking_guids == document_guids
        assert len(document_guids) == 1

        document.set("type", "accountsPayableLedger")
        invalid_path = temp_path / "Belegtransfer_12371_2026-06_002.zip"
        _write_transfer(invalid_path, ET.tostring(root, encoding="utf-8", xml_declaration=True))
        errors, document_guids, booking_guids, count, advice_count = validate_package.validate_document_packages(temp_path)
        assert count == 2
        assert len(document_guids) == 1
        assert any("accountsPayableLedger" in error for error in errors), errors
        assert any("type-Attribut" in error for error in errors), errors

    print("document.xml contract test: OK")


if __name__ == "__main__":
    main()
