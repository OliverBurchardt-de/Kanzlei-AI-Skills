#!/usr/bin/env python3
"""Institution-independent canonical model and deterministic MT940 rendering."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


IBAN_RE = re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}$")
CODE_RE = re.compile(r"^N[A-Z0-9]{3}$")
UNDERFIELD_RE = re.compile(r"\?(\d{2})")
PROFILE_DIR = Path(__file__).resolve().parent.parent / "profiles"
FIELD86_TEXT_CAPACITY = 61 + 5 * 65
TARGET_PROFILE_NAME = "datev-mt940-structured-v1"
STRUCTURED_MODES = {"datev_structured_v1"}
RECONSTRUCTED_SOURCE_TYPES = {
    "pdf",
    "image",
    "csv",
    "manual",
    "manual_list",
    "structured_list",
    "camt",
}
TRANSACTION_CATEGORIES = {
    "fee",
    "transfer",
    "direct_debit",
    "card",
    "cash",
    "interest",
    "other",
}
SWIFT_CODE_BY_CATEGORY = {
    "fee": "NCHG",
    "transfer": "NTRF",
    "direct_debit": "NDDT",
    "card": "NMSC",
    "cash": "NMSC",
    "interest": "NMSC",
    "other": "NMSC",
}
CONFIDENCE_VALUES = {"high", "medium", "low"}
GERMAN_SPECIAL_CHARACTERS = "äöüÄÖÜß"
UTF8_GERMAN_SEQUENCES = {
    character.encode("utf-8") for character in GERMAN_SPECIAL_CHARACTERS
}
BOMS = (b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff")


class MT940Error(ValueError):
    """A classified error whose code is also used by the command-line tools."""

    def __init__(self, message: str, exit_code: int = 3) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def read_json_utf8_no_bom(path: Path, label: str) -> dict[str, Any]:
    """Read a JSON object using strict UTF-8 and reject every Unicode BOM."""

    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise MT940Error(f"Cannot read {label} {path}: {exc}", 2) from exc
    if raw.startswith(BOMS):
        raise MT940Error(f"{label} must be UTF-8 without BOM: {path}", 2)
    try:
        value = json.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MT940Error(f"Cannot read {label} {path}: {exc}", 2) from exc
    if not isinstance(value, dict):
        raise MT940Error(f"{label} must contain a JSON object: {path}", 2)
    return value


@dataclass(frozen=True)
class Field86Result:
    lines: list[str]
    source_description_length: int
    encoded_description_length: int
    roundtrip_match: bool
    truncated: bool
    canonical_description: str
    mode: str = "generic_unstructured"
    gvc: str | None = None
    underfield_order: tuple[str, ...] = ()
    semantic_values: dict[str, str] = field(default_factory=dict)


def nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def canonical_text(
    value: object,
    field_name: str,
    *,
    required: bool = True,
    cp1252_required: bool = True,
) -> str:
    if value is None and not required:
        return ""
    if not isinstance(value, str):
        raise MT940Error(f"{field_name} must be text", 2)
    canonical = re.sub(r"\s+", " ", nfc(value)).strip()
    if required and not canonical:
        raise MT940Error(f"{field_name} must not be empty", 2)
    if cp1252_required:
        try:
            canonical.encode("cp1252", errors="strict")
        except UnicodeEncodeError as exc:
            raise MT940Error(
                f"{field_name} contains a character not representable in Windows-1252: {exc}",
                3,
            ) from exc
    return canonical


def canonical_description(value: object) -> str:
    """Backward-compatible alias used by generic manifests."""

    return canonical_text(value, "description")


def valid_iban(value: str) -> bool:
    if not isinstance(value, str) or not IBAN_RE.fullmatch(value):
        return False
    rearranged = value[4:] + value[:4]
    numeric = "".join(str(ord(char) - 55) if char.isalpha() else char for char in rearranged)
    remainder = 0
    for char in numeric:
        remainder = (remainder * 10 + int(char)) % 97
    return remainder == 1


def parse_date(value: object, field_name: str, *, code: int = 2) -> date:
    try:
        return date.fromisoformat(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise MT940Error(f"{field_name} must use YYYY-MM-DD: {value!r}", code) from exc


def parse_money(value: object, field_name: str, *, code: int = 2) -> Decimal:
    if not isinstance(value, str) or not re.fullmatch(r"-?[0-9]+\.[0-9]{2}", value):
        raise MT940Error(
            f"{field_name} must be a decimal string with two digits: {value!r}", code
        )
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise MT940Error(f"Invalid money in {field_name}: {value!r}", code) from exc


def dc(value: Decimal) -> str:
    return "C" if value >= 0 else "D"


def mt_amount(value: Decimal) -> str:
    return f"{abs(value):.2f}".replace(".", ",")


def normalize_reference(value: object, fallback: str) -> str:
    if value is None or value == "":
        return fallback
    if not isinstance(value, str):
        raise MT940Error(f"Reference must be text: {value!r}", 2)
    normalized = re.sub(r"[^A-Z0-9]", "", nfc(value).upper())[:16]
    if not normalized:
        raise MT940Error(f"Reference contains no alphanumeric characters: {value!r}", 2)
    return normalized


def _positive_int(value: object, field_name: str, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
        raise MT940Error(
            f"{field_name} must be an integer from 1 to {maximum}: {value!r}", 2
        )
    return value


def _physical_field86_lines(logical_text: str) -> list[str]:
    chunks: list[str] = []
    position = 0
    for width in (61, 65, 65, 65, 65, 65):
        if position >= len(logical_text):
            break
        cut = min(position + width, len(logical_text))
        if cut < len(logical_text):
            if logical_text[cut - 1] == "?":
                cut -= 1
            elif cut >= 2 and logical_text[cut - 2] == "?" and logical_text[cut - 1].isdigit():
                cut -= 2
        if cut <= position:
            raise MT940Error("Cannot split :86: without damaging an underfield marker", 3)
        chunks.append(logical_text[position:cut])
        position = cut
    if position != len(logical_text):
        raise MT940Error(
            f":86: needs {len(logical_text)} characters but physical capacity is "
            f"{FIELD86_TEXT_CAPACITY}; do not truncate",
            2,
        )
    lines = [":86:" + chunks[0], *chunks[1:]] if chunks else [":86:"]
    if lines[0][4:] + "".join(lines[1:]) != logical_text:
        raise MT940Error("Loss detected during physical :86: roundtrip", 3)
    return lines


def field86_result(value: object) -> Field86Result:
    canonical = canonical_description(value)
    lines = _physical_field86_lines(canonical)
    reconstructed = lines[0][4:] + "".join(lines[1:])
    return Field86Result(
        lines=lines,
        source_description_length=len(canonical),
        encoded_description_length=len(reconstructed),
        roundtrip_match=reconstructed == canonical,
        truncated=False,
        canonical_description=canonical,
    )


def native_field86_result(value: object) -> Field86Result:
    if not isinstance(value, list) or not value or len(value) > 6:
        raise MT940Error(
            "native mode requires one to six exact native_field86_lines per transaction",
            2,
        )
    if not all(isinstance(line, str) for line in value):
        raise MT940Error("native_field86_lines must contain text lines", 2)
    lines = [nfc(line) for line in value]
    if not lines[0].startswith(":86:"):
        raise MT940Error("The first native :86: line must start with ':86:'", 3)
    if any(line.startswith(":") for line in lines[1:]):
        raise MT940Error("A native :86: continuation must not start with ':'", 3)
    for line in lines:
        if len(line) > 65:
            raise MT940Error("A native :86: line exceeds 65 characters", 3)
        canonical_text(line, "native_field86_line")
    reconstructed = lines[0][4:] + "".join(lines[1:])
    return Field86Result(
        lines=lines,
        source_description_length=len(reconstructed),
        encoded_description_length=len(reconstructed),
        roundtrip_match=True,
        truncated=False,
        canonical_description=reconstructed,
        mode="native",
    )


def _split_semantic_value(text: str, codes: list[str], capacity: int) -> list[tuple[str, str]]:
    remaining = text
    result: list[tuple[str, str]] = []
    for code in codes:
        if not remaining:
            break
        if len(remaining) <= capacity:
            chunk = remaining
        else:
            split_at = remaining.rfind(" ", 0, capacity + 1)
            if split_at < 0:
                raise MT940Error(
                    f"Value contains an indivisible word or reference longer than {capacity} "
                    f"characters: {remaining[: capacity + 12]!r}",
                    2,
                )
            chunk = remaining[: split_at + 1]
        result.append((code, chunk))
        remaining = remaining[len(chunk) :]
    if remaining:
        raise MT940Error(
            f"Value exceeds the lossless capacity of underfields {codes[0]}-{codes[-1]}",
            2,
        )
    if "".join(value for _, value in result) != text:
        raise MT940Error("Semantic underfield split is not lossless", 3)
    return result


def _profile_subfield_length(profile: dict[str, Any], code: str) -> int:
    lengths = profile.get("subfield_lengths", {})
    value = lengths.get(code)
    if not isinstance(value, int) or value < 1:
        raise MT940Error(f"Target profile lacks a valid length for ?{code}", 4)
    return value


def determine_gvc(tx: dict[str, Any], profile: dict[str, Any]) -> tuple[str, str]:
    rules = profile.get("gvc_rules", {})
    default = str(rules.get("default", "835"))
    category_map = rules.get("category_map", {})
    confidence = tx["_field_confidence"].get("transaction_category", "low")
    mapped = category_map.get(tx["_transaction_category"])
    if confidence == "high" and isinstance(mapped, str) and re.fullmatch(r"\d{3}", mapped):
        return mapped, "category_map"
    if not re.fullmatch(r"\d{3}", default):
        raise MT940Error("Target profile default GVC must contain three digits", 4)
    return default, "fallback"


def build_datev_structured_field86(
    tx: dict[str, Any], profile: dict[str, Any]
) -> Field86Result:
    booking_text = tx["_booking_text"]
    purpose_references = tx["_purpose_references"]
    counterparty_iban = tx["_counterparty_iban"] or ""
    counterparty_name = tx["_counterparty_name"] or ""
    semantic_texts = (booking_text, purpose_references, counterparty_iban, counterparty_name)
    if any("?" in value for value in semantic_texts):
        raise MT940Error(
            "Question mark is reserved in structured :86:; clarify the source instead of replacing it",
            2,
        )

    fields: list[tuple[str, str]] = []
    booking_capacity = _profile_subfield_length(profile, "00")
    if len(booking_text) > booking_capacity:
        raise MT940Error(
            f"booking_text exceeds ?00 capacity of {booking_capacity} characters", 2
        )
    fields.append(("00", booking_text))
    fields.extend(
        _split_semantic_value(
            purpose_references,
            [f"{number:02d}" for number in range(20, 30)],
            _profile_subfield_length(profile, "20"),
        )
    )
    if counterparty_iban:
        capacity = _profile_subfield_length(profile, "31")
        if len(counterparty_iban) > capacity:
            raise MT940Error(f"counterparty_iban exceeds ?31 capacity of {capacity}", 2)
        fields.append(("31", counterparty_iban))
    if counterparty_name:
        fields.extend(
            _split_semantic_value(
                counterparty_name,
                ["32", "33"],
                _profile_subfield_length(profile, "32"),
            )
        )

    allowed = set(profile.get("allowed_underfields", []))
    required = set(profile.get("required_underfields", []))
    order = tuple(code for code, _ in fields)
    if not set(order) <= allowed or not required <= set(order):
        raise MT940Error("Structured :86: fields violate the DATEV target profile", 4)
    gvc, gvc_source = determine_gvc(tx, profile)
    logical = gvc + "".join(f"?{code}{value}" for code, value in fields)
    lines = _physical_field86_lines(logical)
    parsed = parse_datev_structured_field86(lines)
    expected_semantics = {
        "booking_text": booking_text,
        "purpose_references": purpose_references,
        "counterparty_iban": counterparty_iban,
        "counterparty_name": counterparty_name,
    }
    if parsed["gvc"] != gvc or parsed["semantic_values"] != expected_semantics:
        raise MT940Error("Structured :86: semantic roundtrip failed", 3)
    tx["_gvc_source"] = gvc_source
    return Field86Result(
        lines=lines,
        source_description_length=sum(len(value) for value in semantic_texts),
        encoded_description_length=len(logical),
        roundtrip_match=True,
        truncated=False,
        canonical_description=logical,
        mode="datev_structured_v1",
        gvc=gvc,
        underfield_order=order,
        semantic_values=expected_semantics,
    )


def parse_datev_structured_field86(lines: list[str]) -> dict[str, Any]:
    if not lines or not lines[0].startswith(":86:"):
        raise MT940Error("Structured field must begin with :86:", 3)
    logical = lines[0][4:] + "".join(lines[1:])
    if not re.match(r"^\d{3}\?", logical):
        raise MT940Error("Structured :86: must begin with a three-digit GVC", 3)
    gvc = logical[:3]
    payload = logical[3:]
    markers = list(re.finditer(r"\?(\d{2})", payload))
    if not markers or markers[0].start() != 0:
        raise MT940Error("Structured :86: lacks a leading underfield marker", 3)
    fields: list[tuple[str, str]] = []
    for index, marker in enumerate(markers):
        start = marker.end()
        end = markers[index + 1].start() if index + 1 < len(markers) else len(payload)
        value = payload[start:end]
        if not value:
            raise MT940Error(f"Structured underfield ?{marker.group(1)} is empty", 3)
        fields.append((marker.group(1), value))
    order = tuple(code for code, _ in fields)
    if len(order) != len(set(order)):
        raise MT940Error("Structured :86: contains duplicate underfields", 3)
    values = dict(fields)
    purpose = "".join(value for code, value in fields if "20" <= code <= "29")
    counterparty = "".join(values.get(code, "") for code in ("32", "33"))
    return {
        "gvc": gvc,
        "underfield_order": order,
        "fields": values,
        "semantic_values": {
            "booking_text": values.get("00", ""),
            "purpose_references": purpose,
            "counterparty_iban": values.get("31", ""),
            "counterparty_name": counterparty,
        },
    }


def load_target_profile(
    profile_name: str,
    profile_dir: Path | None = None,
    *,
    require_verified: bool,
) -> dict[str, Any]:
    if not re.fullmatch(r"[a-z0-9-]+", profile_name):
        raise MT940Error(f"Invalid DATEV target profile name: {profile_name!r}", 4)
    path = (profile_dir or PROFILE_DIR) / f"{profile_name}.json"
    if not path.is_file():
        raise MT940Error(f"DATEV target profile not found: {path}", 4)
    try:
        profile = read_json_utf8_no_bom(path, "DATEV target profile")
    except MT940Error as exc:
        raise MT940Error(str(exc), 4) from exc
    if "bank_name" in profile:
        raise MT940Error("DATEV target profiles must not depend on bank_name", 4)
    if (
        profile.get("profile_name") != profile_name
        or profile.get("target_system") != "DATEV"
        or str(profile.get("charset", "")).upper() not in {"WINDOWS-1252", "CP1252"}
        or profile.get("line_endings") != "CRLF"
    ):
        raise MT940Error(f"Invalid DATEV target profile contract: {profile_name}", 4)
    if require_verified:
        probe = profile.get("probe_import", {})
        checks = probe.get("checks", {})
        required_checks = (
            "opening_balance_correct",
            "test_closing_balance_correct",
            "transaction_count_and_signs_correct",
            "special_characters_complete",
            "counterparty_complete",
            "references_complete",
            "no_visible_underfield_markers",
        )
        if (
            probe.get("result") != "successful"
            or not all(checks.get(item) is True for item in required_checks)
            or probe.get("test_transactions_deleted") is not True
        ):
            raise MT940Error(
                f"DATEV target profile {profile_name!r} is not practically verified", 4
            )
    return profile


def _source_evidence(
    tx: dict[str, Any], transaction_number: int, source_type: str
) -> tuple[list[str], int | None, str | None]:
    raw_lines = tx.get("raw_source_lines")
    if (
        not isinstance(raw_lines, list)
        or not raw_lines
        or not all(isinstance(line, str) and line.strip() for line in raw_lines)
    ):
        raise MT940Error(
            f"Transaction {transaction_number} requires non-empty raw_source_lines", 2
        )
    normalized_lines = [nfc(line) for line in raw_lines]
    if tx.get("source_text_verified") is not True:
        raise MT940Error(
            f"Transaction {transaction_number} requires source_text_verified=true", 2
        )
    page: int | None = None
    location: str | None = None
    if source_type in {"pdf", "image"}:
        page_value = tx.get("source_page")
        if isinstance(page_value, bool) or not isinstance(page_value, int) or page_value < 1:
            raise MT940Error(
                f"Transaction {transaction_number} requires a positive source_page", 2
            )
        page = page_value
    else:
        location = canonical_text(
            tx.get("source_location"),
            f"transactions[{transaction_number}].source_location",
            cp1252_required=False,
        )
    return normalized_lines, page, location


def _canonical_references(value: object, transaction_number: int) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise MT940Error(f"Transaction {transaction_number} references must be a text list", 2)
    references = [
        canonical_text(item, f"transactions[{transaction_number}].references")
        for item in value
    ]
    if len(references) != len(set(references)):
        raise MT940Error(f"Transaction {transaction_number} contains duplicate references", 2)
    return references


def _canonical_confidence(value: object, transaction_number: int) -> dict[str, str]:
    required = ("transaction_category", "booking_text", "purpose", "counterparty_name")
    if not isinstance(value, dict):
        raise MT940Error(
            f"Transaction {transaction_number} field_confidence must be an object", 2
        )
    result: dict[str, str] = {}
    for key in required:
        confidence = value.get(key)
        if confidence not in CONFIDENCE_VALUES:
            raise MT940Error(
                f"Transaction {transaction_number} confidence for {key} must be "
                "high, medium, or low",
                2,
            )
        result[key] = confidence
    return result


def _canonical_transaction(
    tx: dict[str, Any],
    transaction_number: int,
    source_type: str,
    currency: str,
    profile: dict[str, Any],
    output_scope: str,
) -> dict[str, Any]:
    raw_lines, source_page, source_location = _source_evidence(
        tx, transaction_number, source_type
    )
    category = tx.get("transaction_category")
    if category not in TRANSACTION_CATEGORIES:
        raise MT940Error(
            f"Transaction {transaction_number} has unsupported transaction_category {category!r}",
            2,
        )
    tx_currency = tx.get("currency")
    if tx_currency != currency:
        raise MT940Error(
            f"Transaction {transaction_number} currency differs from statement currency", 2
        )
    booking_text = canonical_text(
        tx.get("booking_text"), f"transactions[{transaction_number}].booking_text"
    )
    purpose = canonical_text(
        tx.get("purpose"), f"transactions[{transaction_number}].purpose"
    )
    counterparty_name_value = tx.get("counterparty_name")
    counterparty_name = (
        canonical_text(
            counterparty_name_value,
            f"transactions[{transaction_number}].counterparty_name",
        )
        if counterparty_name_value is not None
        else None
    )
    counterparty_iban_value = tx.get("counterparty_iban")
    if counterparty_iban_value is not None:
        counterparty_iban = canonical_text(
            counterparty_iban_value,
            f"transactions[{transaction_number}].counterparty_iban",
        ).upper()
        if not valid_iban(counterparty_iban):
            raise MT940Error(
                f"Transaction {transaction_number} has invalid counterparty_iban", 2
            )
    else:
        counterparty_iban = None
    references = _canonical_references(tx.get("references"), transaction_number)
    confidence = _canonical_confidence(tx.get("field_confidence"), transaction_number)
    low_confidence_fields = [
        key
        for key in ("transaction_category", "booking_text", "purpose", "counterparty_name")
        if confidence[key] != "high"
    ]
    if output_scope == "full" and low_confidence_fields:
        raise MT940Error(
            f"Transaction {transaction_number} has non-high confidence fields; only a test "
            f"file is allowed: {', '.join(low_confidence_fields)}",
            4,
        )
    purpose_references = purpose + (" " + " ".join(references) if references else "")
    result = dict(tx)
    result.update(
        {
            "_transaction_category": category,
            "_booking_text": booking_text,
            "_purpose": purpose,
            "_references": references,
            "_purpose_references": purpose_references,
            "_counterparty_name": counterparty_name,
            "_counterparty_iban": counterparty_iban,
            "_raw_source_lines": raw_lines,
            "_source_page": source_page,
            "_source_location": source_location,
            "_source_line_count": len(raw_lines),
            "_source_to_manifest_match": True,
            "_field_confidence": confidence,
            "_low_confidence_fields": low_confidence_fields,
        }
    )
    result["_field86"] = build_datev_structured_field86(result, profile)
    return result


def statement_reference(data: dict[str, Any]) -> str:
    number = int(data["_statement_number"])
    reference = (
        f"MT{data['_statement_end']:%y%m%d}{data['iban'][-6:]}{number % 100:02d}"
    )
    if len(reference) > 16:
        raise MT940Error(f"Generated :20: reference is too long: {reference}", 3)
    return reference


def entry_line(tx: dict[str, Any]) -> str:
    return (
        f":61:{tx['_value_date']:%y%m%d}{tx['_booking_date']:%m%d}"
        f"{dc(tx['_amount'])}{mt_amount(tx['_amount'])}{tx['_code']}"
        f"{tx['_customer_reference']}//{tx['_bank_reference']}"
    )


def balance_line(tag: str, balance_date: date, value: Decimal, currency: str) -> str:
    return f":{tag}:{dc(value)}{balance_date:%y%m%d}{currency}{mt_amount(value)}"


def _check_statement_source_evidence(data: dict[str, Any], normalized: dict[str, Any]) -> None:
    evidence = data.get("source_evidence")
    if evidence is None:
        return
    if not isinstance(evidence, dict):
        raise MT940Error("source_evidence must be an object", 2)
    comparisons = {
        "statement_start": normalized["_statement_start"].isoformat(),
        "statement_end": normalized["_statement_end"].isoformat(),
        "opening_balance_date": normalized["_opening_balance_date"].isoformat(),
        "closing_balance_date": normalized["_closing_balance_date"].isoformat(),
        "opening_balance": f"{normalized['_opening']:.2f}",
        "closing_balance": f"{normalized['_closing']:.2f}",
        "statement_number": normalized["_statement_number"],
    }
    for field_name, expected in comparisons.items():
        if field_name in evidence and evidence[field_name] != expected:
            raise MT940Error(
                f"Manifest {field_name}={expected!r} differs from source evidence "
                f"{evidence[field_name]!r}",
                2,
            )


def normalize_manifest(
    data: dict[str, Any], profile_dir: Path | None = None
) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise MT940Error("Manifest root must be an object", 2)
    normalized = dict(data)
    iban = str(data.get("iban", "")).upper()
    if not valid_iban(iban):
        raise MT940Error(f"Invalid IBAN syntax: {iban!r}", 2)
    currency = data.get("currency", "EUR")
    if currency != "EUR":
        raise MT940Error("This skill currently supports EUR only", 2)

    target = str(data.get("target_system", "GENERIC")).upper()
    datev = target == "DATEV"
    if datev:
        date_fields = (
            "statement_start",
            "statement_end",
            "opening_balance_date",
            "closing_balance_date",
        )
        missing = [field_name for field_name in date_fields if not data.get(field_name)]
        if missing:
            raise MT940Error(
                "DATEV manifests require separate statement and balance dates; missing: "
                + ", ".join(missing),
                2,
            )
        if "sequence_number" not in data:
            raise MT940Error("DATEV manifests must explicitly store sequence_number", 2)
        statement_start_value = data.get("statement_start")
        statement_end_value = data.get("statement_end")
        opening_date_value = data.get("opening_balance_date")
        closing_date_value = data.get("closing_balance_date")
        statement_number = _positive_int(data.get("statement_number"), "statement_number", 99999)
        sequence_number = _positive_int(data.get("sequence_number"), "sequence_number", 999)
    else:
        statement_start_value = data.get("statement_start", data.get("period_start"))
        statement_end_value = data.get("statement_end", data.get("period_end"))
        opening_date_value = data.get("opening_balance_date", statement_start_value)
        closing_date_value = data.get("closing_balance_date", statement_end_value)
        statement_number = _positive_int(data.get("statement_number", 1), "statement_number", 99999)
        sequence_number = _positive_int(data.get("sequence_number", 1), "sequence_number", 999)

    statement_start = parse_date(statement_start_value, "statement_start")
    statement_end = parse_date(statement_end_value, "statement_end")
    opening_balance_date = parse_date(opening_date_value, "opening_balance_date")
    closing_balance_date = parse_date(closing_date_value, "closing_balance_date")
    if statement_start > statement_end:
        raise MT940Error("statement_start must not be after statement_end", 2)
    opening = parse_money(data.get("opening_balance"), "opening_balance")
    closing = parse_money(data.get("closing_balance"), "closing_balance")
    transactions = data.get("transactions")
    if not isinstance(transactions, list):
        raise MT940Error("transactions must be a list", 2)

    field86_mode = str(data.get("field86_mode", "generic_unstructured"))
    allowed_modes = {"native", "generic_unstructured", "unverified", *STRUCTURED_MODES}
    verified_mode = field86_mode.startswith("datev_verified:")
    if field86_mode not in allowed_modes and not verified_mode:
        raise MT940Error(f"Unsupported field86_mode: {field86_mode!r}", 4)
    output_scope = str(data.get("output_scope", "full"))
    if output_scope not in {"full", "test"}:
        raise MT940Error("output_scope must be 'full' or 'test'", 2)
    source_type = str(data.get("source_type", "structured_list")).lower()
    structured_mode = field86_mode in STRUCTURED_MODES or verified_mode
    profile: dict[str, Any] | None = None
    target_profile_name: str | None = None
    if field86_mode in STRUCTURED_MODES:
        target_profile_name = str(data.get("target_profile", TARGET_PROFILE_NAME))
        profile = load_target_profile(
            target_profile_name, profile_dir, require_verified=False
        )
        if output_scope != "test":
            raise MT940Error(
                "Unverified DATEV target profile permits only a test file", 4
            )
    elif verified_mode:
        target_profile_name = field86_mode.split(":", 1)[1]
        profile = load_target_profile(
            target_profile_name, profile_dir, require_verified=True
        )
    if datev and source_type in RECONSTRUCTED_SOURCE_TYPES and not structured_mode:
        raise MT940Error(
            "Reconstructed DATEV sources require the institution-independent structured renderer",
            4,
        )

    previous_booking_date: date | None = None
    bank_references: set[str] = set()
    total = Decimal("0.00")
    normalized_transactions: list[dict[str, Any]] = []
    value_exceptions = set(data.get("review_report", {}).get("value_date_exceptions", []))
    for index, original_tx in enumerate(transactions, 1):
        if not isinstance(original_tx, dict):
            raise MT940Error(f"Transaction {index} must be an object", 2)
        tx = dict(original_tx)
        value_date = parse_date(tx.get("value_date"), f"transactions[{index}].value_date")
        booking_date = parse_date(tx.get("booking_date"), f"transactions[{index}].booking_date")
        if not statement_start <= booking_date <= statement_end:
            raise MT940Error(f"Transaction {index} booking_date is outside the statement", 2)
        if not statement_start <= value_date <= statement_end:
            if tx.get("value_date_source_confirmed") is not True or index not in value_exceptions:
                raise MT940Error(
                    f"Transaction {index} value_date is outside the statement without "
                    "source confirmation and a review-report exception",
                    2,
                )
        amount = parse_money(tx.get("amount"), f"transactions[{index}].amount")
        if amount == 0:
            raise MT940Error(f"Transaction {index} has a zero amount", 2)

        if structured_mode:
            assert profile is not None
            tx = _canonical_transaction(
                tx, index, source_type, currency, profile, output_scope
            )
            code = SWIFT_CODE_BY_CATEGORY[tx["_transaction_category"]]
            customer_fallback = tx["_references"][0] if tx["_references"] else "NONREF"
            customer_reference = normalize_reference(
                tx.get("customer_reference"), normalize_reference(customer_fallback, "NONREF")
            )
            source_page = tx["_source_page"]
            source_location = tx["_source_location"]
        elif field86_mode == "native":
            tx["_field86"] = native_field86_result(tx.get("native_field86_lines"))
            code = tx.get("code", "NMSC")
            customer_reference = normalize_reference(tx.get("customer_reference"), "NONREF")
            source_page = None
            source_location = canonical_text(
                tx.get("source_location", "native MT940"),
                f"transactions[{index}].source_location",
                cp1252_required=False,
            )
            tx.update(
                {
                    "_source_line_count": len(tx["native_field86_lines"]),
                    "_source_to_manifest_match": True,
                    "_low_confidence_fields": [],
                }
            )
        else:
            tx["_field86"] = field86_result(tx.get("description"))
            code = tx.get("code", "NMSC")
            customer_reference = normalize_reference(tx.get("customer_reference"), "NONREF")
            source_page = None
            source_location = None
            tx.update(
                {
                    "_source_line_count": None,
                    "_source_to_manifest_match": None,
                    "_low_confidence_fields": [],
                }
            )
        if not isinstance(code, str) or not CODE_RE.fullmatch(code):
            raise MT940Error(f"Transaction {index} has invalid code {code!r}", 2)
        bank_reference = normalize_reference(tx.get("bank_reference"), f"{index:09d}")
        if bank_reference in bank_references:
            raise MT940Error(
                f"Transaction {index} has duplicate bank_reference {bank_reference!r}", 2
            )
        bank_references.add(bank_reference)
        if previous_booking_date and booking_date < previous_booking_date:
            raise MT940Error(
                f"Transactions are not in chronological source order at item {index}", 2
            )
        previous_booking_date = booking_date
        total += amount
        tx.update(
            {
                "_transaction_number": index,
                "_value_date": value_date,
                "_booking_date": booking_date,
                "_amount": amount,
                "_code": code,
                "_customer_reference": customer_reference,
                "_bank_reference": bank_reference,
                "_source_page": source_page,
                "_source_location": source_location,
            }
        )
        normalized_transactions.append(tx)

    if opening + total != closing:
        raise MT940Error(
            f"Balance mismatch: {opening:.2f} + {total:.2f} != {closing:.2f}", 2
        )
    if output_scope == "test":
        booking_days = {tx["_booking_date"] for tx in normalized_transactions}
        if statement_start != statement_end or len(booking_days) > 1:
            raise MT940Error("A DATEV test file may cover at most one booking day", 4)

    normalized.update(
        {
            "iban": iban,
            "_target_system": target,
            "_statement_start": statement_start,
            "_statement_end": statement_end,
            "_opening_balance_date": opening_balance_date,
            "_closing_balance_date": closing_balance_date,
            "_opening": opening,
            "_closing": closing,
            "_transaction_total": total,
            "_statement_number": statement_number,
            "_sequence_number": sequence_number,
            "_field86_mode": field86_mode,
            "_profile": profile,
            "_target_profile_name": target_profile_name,
            "_output_scope": output_scope,
            "_source_type": source_type,
            "_transactions": normalized_transactions,
        }
    )
    _check_statement_source_evidence(data, normalized)
    return normalized


def canonical_fingerprint_payload(data: dict[str, Any]) -> dict[str, Any]:
    transactions: list[dict[str, Any]] = []
    for tx in data["_transactions"]:
        item: dict[str, Any] = {
            "value_date": tx["_value_date"].isoformat(),
            "booking_date": tx["_booking_date"].isoformat(),
            "amount": f"{tx['_amount']:.2f}",
            "code": tx["_code"],
            "customer_reference": tx["_customer_reference"],
            "bank_reference": tx["_bank_reference"],
        }
        if "_transaction_category" in tx:
            item.update(
                {
                    "transaction_category": tx["_transaction_category"],
                    "booking_text": tx["_booking_text"],
                    "purpose": tx["_purpose"],
                    "references": tx["_references"],
                    "counterparty_name": tx["_counterparty_name"],
                    "counterparty_iban": tx["_counterparty_iban"],
                }
            )
        else:
            item["description"] = tx["_field86"].canonical_description
        transactions.append(item)
    return {
        "iban": data["iban"],
        "statement_number": data["_statement_number"],
        "sequence_number": data["_sequence_number"],
        "statement_start": data["_statement_start"].isoformat(),
        "statement_end": data["_statement_end"].isoformat(),
        "opening_balance_date": data["_opening_balance_date"].isoformat(),
        "opening_balance": f"{data['_opening']:.2f}",
        "closing_balance_date": data["_closing_balance_date"].isoformat(),
        "closing_balance": f"{data['_closing']:.2f}",
        "transactions": transactions,
    }


def fingerprint(data: dict[str, Any]) -> str:
    serialized = json.dumps(
        canonical_fingerprint_payload(data),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def expected_lines(data: dict[str, Any]) -> list[str]:
    lines = [
        f":20:{statement_reference(data)}",
        f":25:{data['iban']}",
        f":28C:{data['_statement_number']:05d}/{data['_sequence_number']:03d}",
        balance_line(
            "60F", data["_opening_balance_date"], data["_opening"], data.get("currency", "EUR")
        ),
    ]
    for tx in data["_transactions"]:
        lines.append(entry_line(tx))
        lines.extend(tx["_field86"].lines)
    lines.append(
        balance_line(
            "62F", data["_closing_balance_date"], data["_closing"], data.get("currency", "EUR")
        )
    )
    for line in lines:
        if len(line) > 65:
            raise MT940Error(f"Generated line exceeds 65 characters: {line!r}", 3)
        if nfc(line) != line:
            raise MT940Error("Generated line is not Unicode NFC", 3)
    return lines


def contains_unexpected_controls(text: str) -> bool:
    return any(unicodedata.category(character) == "Cc" for character in text)


def underfields(text: str) -> set[str]:
    return set(UNDERFIELD_RE.findall(text))


def expected_payload(data: dict[str, Any], lines: list[str] | None = None) -> bytes:
    rendered_lines = lines or expected_lines(data)
    text = "\r\n".join(rendered_lines) + "\r\n"
    try:
        payload = text.encode("cp1252", errors="strict")
    except UnicodeEncodeError as exc:
        raise MT940Error(f"MT940 output is not representable in Windows-1252: {exc}", 3) from exc
    if payload.startswith(BOMS):
        raise MT940Error("DATEV STA output must not contain a BOM", 3)
    if data["_target_system"] == "DATEV":
        for sequence in UTF8_GERMAN_SEQUENCES:
            if sequence in payload:
                raise MT940Error(
                    "DATEV STA contains a UTF-8 multibyte sequence for a German character",
                    3,
                )
    if payload.decode("cp1252", errors="strict") != text:
        raise MT940Error("CP1252 byte roundtrip failed", 3)
    return payload


def reject_invalid_datev_bytes(raw: bytes) -> None:
    if raw.startswith(BOMS):
        raise MT940Error("DATEV STA must not contain a UTF BOM", 3)
    for sequence in UTF8_GERMAN_SEQUENCES:
        if sequence in raw:
            raise MT940Error(
                "DATEV STA contains a UTF-8 multibyte sequence for a German character",
                3,
            )
    if not raw.endswith(b"\r\n"):
        raise MT940Error("DATEV STA must end with CRLF", 3)
    if b"\n" in raw.replace(b"\r\n", b"") or b"\r" in raw.replace(b"\r\n", b""):
        raise MT940Error("DATEV STA may contain only CRLF line endings", 3)


def sidecar_filename(data: dict[str, Any]) -> str:
    return (
        f"MT940 Prüfung {data['iban']} {data['_statement_start']:%d.%m.%Y} "
        f"bis {data['_statement_end']:%d.%m.%Y}.json"
    )


def output_filename(data: dict[str, Any]) -> str:
    if data["_output_scope"] == "test":
        return f"MT940 Test {data['iban']} {data['_statement_start']:%d.%m.%Y}.sta"
    return (
        f"MT940 {data['iban']} {data['_statement_start']:%d.%m.%Y} "
        f"bis {data['_statement_end']:%d.%m.%Y}.sta"
    )


def transaction_metrics(data: dict[str, Any]) -> list[dict[str, Any]]:
    metrics: list[dict[str, Any]] = []
    for tx in data["_transactions"]:
        result = tx["_field86"]
        item: dict[str, Any] = {
            "transaction_number": tx["_transaction_number"],
            "source_page": tx.get("_source_page"),
            "source_location": tx.get("_source_location"),
            "source_line_count": tx.get("_source_line_count"),
            "source_to_manifest_match": tx.get("_source_to_manifest_match"),
            "source_description_length": result.source_description_length,
            "encoded_description_length": result.encoded_description_length,
            "roundtrip_match": result.roundtrip_match,
            "truncated": result.truncated,
            "field86_mode": result.mode,
            "gvc": result.gvc,
            "gvc_source": tx.get("_gvc_source"),
            "underfield_order": list(result.underfield_order),
            "semantic_values": result.semantic_values,
            "low_confidence_fields": tx.get("_low_confidence_fields", []),
        }
        metrics.append(item)
    return metrics
