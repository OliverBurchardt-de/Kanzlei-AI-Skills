"""Adapter for this synthetic test bank only; no production bank evidence."""

from mt940_common import field86_result


def encode_field86(transaction):
    if transaction.get("source_fields"):
        raise ValueError("This synthetic bank variant has no named structured fields")
    return field86_result(transaction["description"]).lines


def decode_field86(lines):
    if not lines or not lines[0].startswith(":86:"):
        raise ValueError("Missing :86:")
    return {"description": lines[0][4:] + "".join(lines[1:]), "source_fields": {}}
