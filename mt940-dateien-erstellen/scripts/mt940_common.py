#!/usr/bin/env python3
"""Shared validation and formatting helpers for deterministic MT940 files."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


IBAN_RE = re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}$")
CODE_RE = re.compile(r"^N[A-Z0-9]{3}$")
UNDERFIELD_RE = re.compile(r"\?(\d{2})")
FIELD86_TEXT_CAPACITY = 61 + 5 * 65
PROFILE_DIR = Path(__file__).resolve().parent.parent / "profiles"


class MT940Error(ValueError):
    """A classified error whose code is also used by the command-line tools."""

    def __init__(self, message: str, exit_code: int = 3) -> None:
        super().__init__(message)
        self.exit_code = exit_code


@dataclass(frozen=True)
class Field86Result:
    lines: list[str]
    source_description_length: int
    encoded_description_length: int
    roundtrip_match: bool
    truncated: bool
    canonical_description: str


def valid_iban(value: str) -> bool:
    if not isinstance(value, str) or not IBAN_RE.fullmatch(value):
        return False
    rearranged = value[4:] + value[:4]
    numeric = "".join(str(ord(char) - 55) if char.isalpha() else char for char in rearranged)
    remainder = 0
    for char in numeric:
        remainder = (remainder * 10 + int(char)) % 97
    return remainder == 1


def parse_date(value: object, field: str, *, code: int = 2) -> date:
    try:
        return date.fromisoformat(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise MT940Error(f"{field} must use YYYY-MM-DD: {value!r}", code) from exc


def parse_money(value: object, field: str, *, code: int = 2) -> Decimal:
    if not isinstance(value, str) or not re.fullmatch(r"-?[0-9]+\.[0-9]{2}", value):
        raise MT940Error(
            f"{field} must be a decimal string with two digits: {value!r}", code
        )
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise MT940Error(f"Invalid money in {field}: {value!r}", code) from exc


def dc(value: Decimal) -> str:
    return "C" if value >= 0 else "D"


def mt_amount(value: Decimal) -> str:
    return f"{abs(value):.2f}".replace(".", ",")


def canonical_description(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MT940Error("Every transaction needs a description", 2)
    canonical = re.sub(r"\s+", " ", value).strip()
    try:
        canonical.encode("cp1252", errors="strict")
    except UnicodeEncodeError as exc:
        raise MT940Error(
            f"Description contains a character not representable in Windows-1252: {exc}",
            3,
        ) from exc
    return canonical




def verified_pdf_description(
    tx: dict[str, Any], transaction_number: int
) -> tuple[str, int, int]:
    page = tx.get("source_page")
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        raise MT940Error(
            f"PDF transaction {transaction_number} requires a positive source_page", 2
        )
    lines = tx.get("source_description_lines")
    if (
        not isinstance(lines, list)
        or not lines
        or not all(isinstance(line, str) and line.strip() for line in lines)
    ):
        raise MT940Error(
            f"PDF transaction {transaction_number} requires exact, non-empty "
            "source_description_lines in visible order",
            2,
        )
    if tx.get("source_text_verified") is not True:
        raise MT940Error(
            f"PDF transaction {transaction_number} requires source_text_verified=true "
            "after visual comparison with the rendered page",
            2,
        )
    source_text = canonical_description(" ".join(lines))
    if "description" in tx:
        manifest_text = canonical_description(tx["description"])
        if manifest_text != source_text:
            raise MT940Error(
                f"PDF transaction {transaction_number} description differs from the "
                "visually verified source_description_lines",
                2,
            )
    return source_text, page, len(lines)
def normalize_reference(value: object, fallback: str) -> str:
    if value is None or value == "":
        return fallback
    if not isinstance(value, str):
        raise MT940Error(f"Reference must be text: {value!r}", 2)
    normalized = re.sub(r"[^A-Z0-9]", "", value.upper())[:16]
    if not normalized:
        raise MT940Error(f"Reference contains no alphanumeric characters: {value!r}", 2)
    return normalized


def _split_losslessly(text: str) -> list[str]:
    chunks: list[str] = []
    position = 0
    for width in (61, 65, 65, 65, 65, 65):
        if position >= len(text):
            break
        cut = min(width, len(text) - position)
        if position and text[position] == ":":
            raise MT940Error(
                "A lossless :86: continuation would start with ':'; clarify or rephrase the source text",
                3,
            )
        if position + cut < len(text) and text[position + cut] == ":" and cut > 1:
            cut -= 1
        chunks.append(text[position : position + cut])
        position += cut
    if position != len(text):
        raise MT940Error(
            f"Description has {len(text)} characters but lossless :86: capacity is "
            f"{FIELD86_TEXT_CAPACITY}; create a clarification case instead of truncating",
            2,
        )
    return chunks


def field86_result(value: object) -> Field86Result:
    canonical = canonical_description(value)
    chunks = _split_losslessly(canonical)
    lines = [":86:" + chunks[0], *chunks[1:]]
    reconstructed = lines[0][4:] + "".join(lines[1:])
    result = Field86Result(
        lines=lines,
        source_description_length=len(canonical),
        encoded_description_length=len(reconstructed),
        roundtrip_match=reconstructed == canonical,
        truncated=False,
        canonical_description=canonical,
    )
    if not result.roundtrip_match:
        raise MT940Error("Loss detected during :86: roundtrip", 3)
    return result




def native_field86_result(value: object) -> Field86Result:
    if not isinstance(value, list) or not value or len(value) > 6:
        raise MT940Error(
            "native mode requires one to six exact native_field86_lines per transaction",
            2,
        )
    if not all(isinstance(line, str) for line in value):
        raise MT940Error("native_field86_lines must contain text lines", 2)
    lines = list(value)
    if not lines[0].startswith(":86:"):
        raise MT940Error("The first native :86: line must start with ':86:'", 3)
    if any(line.startswith(":") for line in lines[1:]):
        raise MT940Error("A native :86: continuation must not start with ':'", 3)
    for line in lines:
        if len(line) > 65:
            raise MT940Error("A native :86: line exceeds 65 characters", 3)
        try:
            line.encode("cp1252", errors="strict")
        except UnicodeEncodeError as exc:
            raise MT940Error(
                f"A native :86: line is not representable in Windows-1252: {exc}", 3
            ) from exc
    reconstructed = lines[0][4:] + "".join(lines[1:])
    return Field86Result(
        lines=lines,
        source_description_length=len(reconstructed),
        encoded_description_length=len(reconstructed),
        roundtrip_match=True,
        truncated=False,
        canonical_description=reconstructed,
    )
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


def _positive_int(value: object, field: str, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
        raise MT940Error(f"{field} must be an integer from 1 to {maximum}: {value!r}", 2)
    return value


def load_profile(mode: str, profile_dir: Path | None = None) -> dict[str, Any] | None:
    if not mode.startswith("datev_verified:"):
        return None
    name = mode.split(":", 1)[1]
    if not re.fullmatch(r"[a-z0-9-]+", name):
        raise MT940Error(f"Invalid DATEV profile name: {name!r}", 4)
    path = (profile_dir or PROFILE_DIR) / f"{name}.json"
    if not path.is_file():
        raise MT940Error(f"DATEV profile fixture not found: {path}", 4)
    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MT940Error(f"Cannot read DATEV profile fixture {path}: {exc}", 4) from exc
    checks = profile.get("probe_import", {}).get("checks", {})
    required_checks = (
        "opening_balance_correct",
        "test_closing_balance_correct",
        "transaction_count_and_signs_correct",
        "description_complete",
        "no_visible_control_characters",
    )
    if (
        profile.get("profile_name") != name
        or profile.get("probe_import", {}).get("result") != "successful"
        or not all(checks.get(item) is True for item in required_checks)
        or profile.get("probe_import", {}).get("test_transactions_deleted") is not True
    ):
        raise MT940Error(
            f"DATEV profile {name!r} lacks a successful, cleaned-up probe import", 4
        )
    return profile


def _check_source_evidence(data: dict[str, Any], normalized: dict[str, Any]) -> None:
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
    for field, expected in comparisons.items():
        if field in evidence and evidence[field] != expected:
            raise MT940Error(
                f"Manifest {field}={expected!r} differs from source evidence "
                f"{evidence[field]!r}",
                2,
            )


def normalize_manifest(
    data: dict[str, Any], profile_dir: Path | None = None
) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise MT940Error("Manifest root must be an object", 2)
    normalized = dict(data)
    iban = data.get("iban", "")
    if not valid_iban(iban):
        raise MT940Error(f"Invalid IBAN syntax: {iban!r}", 2)
    currency = data.get("currency", "EUR")
    if currency != "EUR":
        raise MT940Error("This skill currently supports EUR only", 2)

    target = str(data.get("target_system", "GENERIC")).upper()
    datev = target == "DATEV"
    if datev:
        required_dates = (
            "statement_start",
            "statement_end",
            "opening_balance_date",
            "closing_balance_date",
        )
        missing = [field for field in required_dates if not data.get(field)]
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
    allowed_modes = {"native", "generic_unstructured", "unverified"}
    if field86_mode not in allowed_modes and not field86_mode.startswith("datev_verified:"):
        raise MT940Error(f"Unsupported field86_mode: {field86_mode!r}", 4)
    profile = load_profile(field86_mode, profile_dir)
    output_scope = str(data.get("output_scope", "full"))
    source_type = str(data.get("source_type", "structured_list")).lower()
    reconstructed_source = source_type in {"pdf", "image", "manual", "manual_list"}
    if datev and reconstructed_source and profile is None and output_scope != "test":
        raise MT940Error(
            "DATEV profile is not verified; only a one-day probe-import test file is allowed",
            4,
        )
    if output_scope not in {"full", "test"}:
        raise MT940Error("output_scope must be 'full' or 'test'", 2)

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
            raise MT940Error(
                f"Transaction {index} booking_date lies outside the statement period", 2
            )
        if not statement_start <= value_date <= statement_end:
            if tx.get("value_date_source_confirmed") is not True or index not in value_exceptions:
                raise MT940Error(
                    f"Transaction {index} value_date lies outside the statement period without "
                    "source confirmation and an explicit review-report exception",
                    2,
                )
        amount = parse_money(tx.get("amount"), f"transactions[{index}].amount")
        if amount == 0:
            raise MT940Error(f"Transaction {index} has a zero amount", 2)
        code = tx.get("code", "NMSC")
        if not isinstance(code, str) or not CODE_RE.fullmatch(code):
            raise MT940Error(f"Transaction {index} has invalid code {code!r}", 2)
        source_page: int | None = None
        source_line_count: int | None = None
        source_to_manifest_match: bool | None = None
        if field86_mode == "native":
            description_result = native_field86_result(tx.get("native_field86_lines"))
            if "description" in tx and tx["description"] != description_result.canonical_description:
                raise MT940Error(
                    f"Transaction {index} description differs from exact native :86: lines", 2
                )
            source_line_count = len(tx["native_field86_lines"])
            source_to_manifest_match = True
        elif source_type in {"pdf", "image"}:
            source_text, source_page, source_line_count = verified_pdf_description(tx, index)
            description_result = field86_result(source_text)
            source_to_manifest_match = True
        else:
            description_result = field86_result(tx.get("description"))
        customer_reference = normalize_reference(tx.get("customer_reference"), "NONREF")
        bank_reference = normalize_reference(tx.get("bank_reference"), f"{index:09d}")
        if bank_reference in bank_references:
            raise MT940Error(
                f"Transaction {index} has duplicate bank_reference {bank_reference!r}", 2
            )
        bank_references.add(bank_reference)
        if previous_booking_date and booking_date < previous_booking_date:
            raise MT940Error(f"Transactions are not in chronological source order at item {index}", 2)
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
                "_field86": description_result,
                "_source_page": source_page,
                "_source_line_count": source_line_count,
                "_source_to_manifest_match": source_to_manifest_match,
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
        if not any(tx["_field86"].source_description_length > 61 for tx in normalized_transactions):
            raise MT940Error("A DATEV test file must contain at least one long description", 4)

    normalized.update(
        {
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
            "_output_scope": output_scope,
            "_transactions": normalized_transactions,
        }
    )
    _check_source_evidence(data, normalized)
    return normalized


def canonical_fingerprint_payload(data: dict[str, Any]) -> dict[str, Any]:
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
        "transactions": [
            {
                "value_date": tx["_value_date"].isoformat(),
                "booking_date": tx["_booking_date"].isoformat(),
                "amount": f"{tx['_amount']:.2f}",
                "code": tx["_code"],
                "customer_reference": tx["_customer_reference"],
                "bank_reference": tx["_bank_reference"],
                "description": tx["_field86"].canonical_description,
            }
            for tx in data["_transactions"]
        ],
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
    return lines


def contains_unexpected_controls(text: str) -> bool:
    return any(unicodedata.category(char) == "Cc" for char in text)


def profile_allowed_underfields(data: dict[str, Any]) -> set[str]:
    profile = data.get("_profile")
    return set(profile.get("allowed_underfields", [])) if profile else set()


def underfields(text: str) -> set[str]:
    return set(UNDERFIELD_RE.findall(text))


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
    return [
        {
            "transaction_number": tx["_transaction_number"],
            "source_description_length": tx["_field86"].source_description_length,
            "source_page": tx["_source_page"],
            "source_line_count": tx["_source_line_count"],
            "source_to_manifest_match": tx["_source_to_manifest_match"],
            "source_text_start": tx["_field86"].canonical_description[:40],
            "source_text_end": tx["_field86"].canonical_description[-40:],
            "encoded_description_length": tx["_field86"].encoded_description_length,
            "roundtrip_match": tx["_field86"].roundtrip_match,
            "truncated": tx["_field86"].truncated,
        }
        for tx in data["_transactions"]
    ]
