#!/usr/bin/env python3
"""Build a deterministic MT940/STA file from a reviewed JSON manifest."""

from __future__ import annotations

import argparse
import json
import re
import textwrap
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


IBAN_RE = re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}$")
CODE_RE = re.compile(r"^N[A-Z0-9]{3}$")


def valid_iban(value: str) -> bool:
    if not IBAN_RE.fullmatch(value):
        return False
    rearranged = value[4:] + value[:4]
    numeric = "".join(str(ord(char) - 55) if char.isalpha() else char for char in rearranged)
    remainder = 0
    for char in numeric:
        remainder = (remainder * 10 + int(char)) % 97
    return remainder == 1


def parse_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must use YYYY-MM-DD: {value!r}") from exc


def parse_money(value: str, field: str) -> Decimal:
    if not isinstance(value, str) or not re.fullmatch(r"-?[0-9]+\.[0-9]{2}", value):
        raise ValueError(f"{field} must be a decimal string with two digits: {value!r}")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid money in {field}: {value!r}") from exc


def dc(value: Decimal) -> str:
    return "C" if value >= 0 else "D"


def mt_amount(value: Decimal) -> str:
    return f"{abs(value):.2f}".replace(".", ",")


def clean_description(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Every transaction needs a description")
    value = re.sub(r"\s+", " ", value).strip().replace(":", ";")
    value.encode("cp1252", errors="strict")
    return value


def normalize_reference(value: object, fallback: str) -> str:
    if value is None or value == "":
        return fallback
    if not isinstance(value, str):
        raise ValueError(f"Reference must be text: {value!r}")
    normalized = re.sub(r"[^A-Z0-9]", "", value.upper())[:16]
    if not normalized:
        raise ValueError(f"Reference contains no alphanumeric characters: {value!r}")
    return normalized


def field86_lines(description: str) -> tuple[list[str], bool]:
    description = clean_description(description)
    truncated = len(description) > 386
    rest = description[:386]
    chunks: list[str] = []
    for width in (61, 65, 65, 65, 65, 65):
        if not rest:
            break
        wrapped = textwrap.wrap(
            rest,
            width=width,
            break_long_words=True,
            break_on_hyphens=False,
            replace_whitespace=True,
            drop_whitespace=True,
        )
        chunk = wrapped[0]
        chunks.append(chunk)
        rest = rest[len(chunk) :].lstrip()
    return ([":86:" + chunks[0]] + chunks[1:] if chunks else [":86:"]), truncated


def validate_manifest(data: dict) -> tuple[date, date, Decimal, Decimal, list[dict]]:
    iban = data.get("iban", "")
    if not valid_iban(iban):
        raise ValueError(f"Invalid IBAN syntax: {iban!r}")
    if data.get("currency", "EUR") != "EUR":
        raise ValueError("This skill currently supports EUR only")

    period_start = parse_date(data.get("period_start"), "period_start")
    period_end = parse_date(data.get("period_end"), "period_end")
    if period_start > period_end:
        raise ValueError("period_start must not be after period_end")

    opening = parse_money(data.get("opening_balance"), "opening_balance")
    closing = parse_money(data.get("closing_balance"), "closing_balance")
    transactions = data.get("transactions")
    if not isinstance(transactions, list):
        raise ValueError("transactions must be a list")

    previous_booking_date: date | None = None
    bank_references: set[str] = set()
    total = Decimal("0.00")
    for index, tx in enumerate(transactions, 1):
        if not isinstance(tx, dict):
            raise ValueError(f"Transaction {index} must be an object")
        value_date = parse_date(tx.get("value_date"), f"transactions[{index}].value_date")
        booking_date = parse_date(tx.get("booking_date"), f"transactions[{index}].booking_date")
        amount = parse_money(tx.get("amount"), f"transactions[{index}].amount")
        if amount == 0:
            raise ValueError(f"Transaction {index} has a zero amount")
        code = tx.get("code", "NMSC")
        if not CODE_RE.fullmatch(code):
            raise ValueError(f"Transaction {index} has invalid code {code!r}")
        clean_description(tx.get("description"))
        tx["_customer_reference"] = normalize_reference(
            tx.get("customer_reference"), "NONREF"
        )
        tx["_bank_reference"] = normalize_reference(
            tx.get("bank_reference"), f"{index:09d}"
        )
        if tx["_bank_reference"] in bank_references:
            raise ValueError(
                f"Transaction {index} has duplicate bank_reference "
                f"{tx['_bank_reference']!r}"
            )
        bank_references.add(tx["_bank_reference"])
        if previous_booking_date and booking_date < previous_booking_date:
            raise ValueError(f"Transactions are not chronological at item {index}")
        previous_booking_date = booking_date
        total += amount
        tx["_value_date"] = value_date
        tx["_booking_date"] = booking_date
        tx["_amount"] = amount

    if opening + total != closing:
        raise ValueError(
            f"Balance mismatch: {opening:.2f} + {total:.2f} != {closing:.2f}"
        )
    return period_start, period_end, opening, closing, transactions


def build(data: dict) -> tuple[bytes, int]:
    period_start, period_end, opening, closing, transactions = validate_manifest(data)
    iban = data["iban"]
    reference = f"MT940{period_end:%Y}{iban[-4:]}"[:16]
    lines = [
        f":20:{reference}",
        f":25:{iban}",
        ":28C:00001/001",
        f":60F:{dc(opening)}{period_start:%y%m%d}EUR{mt_amount(opening)}",
    ]
    truncations = 0
    for number, tx in enumerate(transactions, 1):
        amount = tx["_amount"]
        lines.append(
            f":61:{tx['_value_date']:%y%m%d}{tx['_booking_date']:%m%d}"
            f"{dc(amount)}{mt_amount(amount)}{tx.get('code', 'NMSC')}"
            f"{tx['_customer_reference']}//{tx['_bank_reference']}"
        )
        field_lines, truncated = field86_lines(tx["description"])
        truncations += int(truncated)
        lines.extend(field_lines)
    lines.append(f":62F:{dc(closing)}{period_end:%y%m%d}EUR{mt_amount(closing)}")

    for line in lines:
        if len(line) > 65:
            raise ValueError(f"Generated line exceeds 65 characters: {line!r}")
    payload = ("\r\n".join(lines) + "\r\n").encode("cp1252", errors="strict")
    return payload, truncations


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path, nargs="?")
    args = parser.parse_args()

    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    payload, truncations = build(data)
    start = parse_date(data["period_start"], "period_start")
    end = parse_date(data["period_end"], "period_end")
    output = args.output or Path(
        f"MT940 {data['iban']} {start:%d.%m.%Y} bis {end:%d.%m.%Y}.sta"
    )
    output.write_bytes(payload)
    print(f"created={output}")
    print(f"transactions={len(data['transactions'])}")
    print(f"field86_truncations={truncations}")


if __name__ == "__main__":
    main()
