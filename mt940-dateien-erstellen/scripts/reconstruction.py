"""Explicit technical conventions for source-checked reconstructed exports."""
from __future__ import annotations

import copy
from datetime import timedelta
from typing import Any

from mt940_common import MT940Error, parse_date

DEFAULT_RULES = {
    "statement_number": "technical_statement_one",
    "sequence_number": "technical_sequence_one",
    "opening_balance_date": "period_start_previous_day",
    "closing_balance_date": "period_end",
    "value_date": "booking_date_when_not_shown",
    "code": "nmsc_when_not_shown",
}

def derived_value(field: str, rule: str, statement: dict[str, Any],
                  transaction: dict[str, Any] | None = None) -> Any:
    if DEFAULT_RULES.get(field) != rule:
        raise MT940Error(f"Unsupported reconstruction rule for {field}: {rule!r}", 4)
    if field in {"statement_number", "sequence_number"}:
        return 1
    if field == "opening_balance_date":
        return (parse_date(statement.get("statement_start"), "statement_start") - timedelta(days=1)).isoformat()
    if field == "closing_balance_date":
        return parse_date(statement.get("statement_end"), "statement_end").isoformat()
    if field == "value_date":
        return parse_date((transaction or {}).get("booking_date"), "booking_date").isoformat()
    return "NMSC"

def fill_missing(data: dict[str, Any], rules: dict[str, str]) -> dict[str, Any]:
    """Work from extracted manifest values, never from the independent review."""
    result = copy.deepcopy(data)
    for container, keys in [(result, ("statement_number", "sequence_number", "opening_balance_date", "closing_balance_date"))]:
        for field in keys:
            if container.get(field) is None:
                rule = rules.get(field)
                value = derived_value(field, rule, result)
                container[field] = value
                container.setdefault("derived_fields", {})[field] = {
                    "source_value": None, "rule": rule, "value": value,
                    "reason": "Technical reconstruction convention; original value not shown in source",
                }
    for tx in result.get("transactions", []):
        for field in ("value_date", "code"):
            if tx.get(field) is None:
                rule = rules.get(field)
                value = derived_value(field, rule, result, tx)
                tx[field] = value
                tx.setdefault("derived_fields", {})[field] = {
                    "source_value": None, "rule": rule, "value": value,
                    "reason": "Technical reconstruction convention; original value not shown in source",
                }
    return result

def effective_source(field: str, source: Any, manifest_container: dict[str, Any],
                     statement: dict[str, Any], transaction: dict[str, Any] | None,
                     profile: dict[str, Any]) -> tuple[Any, dict[str, Any] | None]:
    """Recompute each declared convention from independently reviewed originals."""
    record = manifest_container.get("derived_fields", {}).get(field)
    if record is None:
        return source, None
    if source is not None or not isinstance(record, dict) or record.get("source_value") is not None:
        raise MT940Error(f"Reconstruction cannot replace an existing original {field}", 2)
    rule = record.get("rule")
    if profile.get("reconstruction_rules", {}).get(field) != rule or not record.get("reason"):
        raise MT940Error(f"Undocumented reconstruction rule for {field}", 4)
    value = derived_value(field, rule, statement, transaction)
    if record.get("value") != value or manifest_container.get(field) != value:
        raise MT940Error(f"Reconstructed {field} differs from its source-based convention", 2)
    return value, record
