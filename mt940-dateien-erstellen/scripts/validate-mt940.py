#!/usr/bin/env python3
"""Validate structural and balance rules of an MT940/STA file."""

from __future__ import annotations

import argparse
import re
from decimal import Decimal
from pathlib import Path


BALANCE_RE = re.compile(r"^:(60F|62F):([CD])(\d{6})([A-Z]{3})([0-9]+,[0-9]{2})$")
ENTRY_RE = re.compile(
    r"^:61:(\d{6})(\d{4})([CD])([0-9]+,[0-9]{2})(N[A-Z0-9]{3})"
    r"(.{1,16})(?://(.{1,16}))?$"
)


def amount(sign: str, value: str) -> Decimal:
    result = Decimal(value.replace(",", "."))
    return result if sign == "C" else -result


def validate(path: Path) -> dict:
    raw = path.read_bytes()
    if not raw.endswith(b"\r\n"):
        raise ValueError("File must end with CRLF")
    if b"\n" in raw.replace(b"\r\n", b""):
        raise ValueError("Bare LF line ending found")
    text = raw.decode("cp1252", errors="strict")
    lines = text.split("\r\n")[:-1]
    if not lines:
        raise ValueError("File is empty")
    for number, line in enumerate(lines, 1):
        if len(line) > 65:
            raise ValueError(f"Line {number} exceeds 65 characters")

    expected_start = (":20:", ":25:", ":28C:", ":60F:")
    for index, prefix in enumerate(expected_start):
        if index >= len(lines) or not lines[index].startswith(prefix):
            raise ValueError(f"Expected {prefix} at line {index + 1}")
    if not lines[-1].startswith(":62F:"):
        raise ValueError("Last field must be :62F:")

    opening_match = BALANCE_RE.fullmatch(lines[3])
    closing_match = BALANCE_RE.fullmatch(lines[-1])
    if not opening_match or not closing_match:
        raise ValueError("Invalid opening or closing balance field")
    if opening_match.group(4) != closing_match.group(4):
        raise ValueError("Opening and closing currencies differ")

    opening = amount(opening_match.group(2), opening_match.group(5))
    closing = amount(closing_match.group(2), closing_match.group(5))
    transaction_total = Decimal("0.00")
    transaction_count = 0

    i = 4
    while i < len(lines) - 1:
        entry = ENTRY_RE.fullmatch(lines[i])
        if not entry:
            raise ValueError(f"Expected valid :61: field at line {i + 1}")
        transaction_total += amount(entry.group(3), entry.group(4))
        transaction_count += 1
        i += 1
        if i >= len(lines) - 1 or not lines[i].startswith(":86:"):
            raise ValueError(f"Transaction {transaction_count} lacks immediate :86: field")
        i += 1
        continuation_count = 0
        while i < len(lines) - 1 and not lines[i].startswith(":61:"):
            if lines[i].startswith(":"):
                raise ValueError(f"Unexpected tag at line {i + 1}")
            continuation_count += 1
            if continuation_count > 5:
                raise ValueError(f"Transaction {transaction_count} exceeds six :86: lines")
            i += 1

    if opening + transaction_total != closing:
        raise ValueError(
            f"Balance mismatch: {opening:.2f} + {transaction_total:.2f} != {closing:.2f}"
        )
    return {
        "transactions": transaction_count,
        "opening": opening,
        "transaction_total": transaction_total,
        "closing": closing,
        "currency": opening_match.group(4),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    result = validate(args.file)
    for key, value in result.items():
        print(f"{key}={value}")
    print("status=valid")


if __name__ == "__main__":
    main()

