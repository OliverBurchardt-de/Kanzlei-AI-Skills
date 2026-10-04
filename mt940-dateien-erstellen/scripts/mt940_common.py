#!/usr/bin/env python3
"""Shared validation and formatting helpers for deterministic MT940 files."""

from __future__ import annotations

import hashlib
import importlib.util
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

    def __init__(self, message: str, exit_code: int = 3, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.details = details or {}


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
                "A lossless :86: continuation would start with ':'; review the bank's splitting rule without rewriting the source",
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
    if data["_profile"]["statement_reference_rule"] == "source":
        reference = data.get("statement_reference")
        if not isinstance(reference, str) or not 1 <= len(reference) <= 16 or contains_unexpected_controls(reference):
            raise MT940Error("Model requires the exact source statement_reference (1..16 characters)", 2)
        return reference
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


def load_profile(data: dict[str, Any], profile_dir: Path | None = None) -> dict[str, Any]:
    name = data.get("bank_profile", "")
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9-]+", name):
        raise MT940Error("A bank-specific bank_profile is required; no generic fallback", 4)
    path = (profile_dir or PROFILE_DIR) / f"{name}.json"
    if not path.is_file():
        raise MT940Error(f"Bank model missing: create {path} from this bank's references first", 4)
    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MT940Error(f"Cannot read DATEV profile fixture {path}: {exc}", 4) from exc
    if not isinstance(profile, dict) or profile.get("profile_name") != name:
        raise MT940Error("Bank profile name does not match its filename", 4)
    if profile.get("template_only") is True:
        raise MT940Error("A blank template is not a bank reference model", 4)
    profile["_model_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    for field in ("bank_id", "source_variant", "profile_version"):
        if not data.get(field) or data[field] != profile.get(field):
            raise MT940Error(f"Bank model mismatch in {field}; another bank/variant/version is forbidden", 4)
    if not profile.get("bank_name") or profile.get("status") not in {"draft", "source_verified", "verified"}:
        raise MT940Error("Bank model requires bank_name and draft/source_verified/verified status", 4)
    if data.get("source_type") not in profile.get("source_types", []):
        raise MT940Error("Bank model does not cover this source_type", 4)
    basis = profile.get("reference_basis", {})
    reconstruction = isinstance(basis, dict) and basis.get("kind") == "source_reconstruction"
    learning = reconstruction and profile.get("status") == "draft"
    if profile.get("status") == "source_verified" and not reconstruction:
        raise MT940Error("source_verified status requires a source_reconstruction model", 4)
    if not isinstance(basis, dict) or (not learning and basis.get("verified_against_reference") is not True) or not basis.get("reference"):
        raise MT940Error("Bank model has no reviewed bank-specific reference basis", 4)
    if basis.get("kind") not in {"native_bank_file", "bank_documentation", "confirmed_test", "source_reconstruction"}:
        raise MT940Error("Bank model needs a bank reference or source-checked reconstruction", 4)
    if reconstruction:
        if data.get("field86_mode") != "reconstructed" or data.get("source_type") == "native_mt940":
            raise MT940Error("Reconstruction model requires reconstructed mode and a non-native source", 4)
        if profile.get("field86_structure") != "unstructured" or not isinstance(profile.get("reconstruction_rules"), dict):
            raise MT940Error("Reconstruction model must document text structure and missing-value rules", 4)
        if not learning:
            evidence_path = Path(basis["reference"])
            if not evidence_path.is_absolute():
                evidence_path = path.parent / evidence_path
            try:
                evidence_bytes = evidence_path.read_bytes()
                evidence = json.loads(evidence_bytes)
            except (OSError, ValueError) as exc:
                raise MT940Error("Source-checked model reference evidence is unavailable", 4) from exc
            if hashlib.sha256(evidence_bytes).hexdigest() != basis.get("reference_sha256") or evidence.get("exit_code") != 0 or evidence.get("source_check", {}).get("source_to_mt940_match") is not True:
                raise MT940Error("Source-checked model reference evidence failed integrity/field checks", 4)
            if evidence.get("bank_model") != {key:data[key] for key in ("bank_id","source_variant","bank_profile","profile_version")}:
                raise MT940Error("Source-checked evidence belongs to another bank/variant/version", 4)
    mappings = profile.get("field_mappings", {})
    required_mappings = {"statement_reference", "iban", "statement_number", "sequence_number",
                         "opening_balance_date", "opening_balance", "closing_balance_date",
                         "closing_balance", "currency", "value_date", "booking_date", "amount",
                         "code", "customer_reference", "bank_reference", "description"}
    if not isinstance(mappings, dict) or not required_mappings <= mappings.keys() or not all(isinstance(mappings[key], str) and mappings[key].strip() for key in required_mappings):
        raise MT940Error("Bank model lacks explicit field_mappings for statement/transaction fields", 4)
    if profile.get("charset") != "Windows-1252" or profile.get("line_endings") != "CRLF":
        raise MT940Error("This generator supports only explicitly modeled Windows-1252/CRLF", 4)
    if profile.get("statement_reference_rule") not in {"source", "deterministic_mt"}:
        raise MT940Error("Bank model must explicitly define statement_reference_rule", 4)
    rules = profile.get("reference_rules", {})
    if not isinstance(rules, dict) or rules.get("customer_reference") not in {"exact", "upper_alnum_16"}:
        raise MT940Error("Bank model must define customer_reference handling", 4)
    if rules.get("bank_reference") not in {"exact", "upper_alnum_16", "source_or_sequence_9"}:
        raise MT940Error("Bank model must define bank_reference handling", 4)
    if not isinstance(profile.get("examples"), list) or (not profile["examples"] and not learning):
        raise MT940Error("Bank model requires source/output reference examples", 4)
    if profile.get("test_fixture_only") is True and path.parent.resolve() != (
        Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "profiles"
    ).resolve():
        raise MT940Error("Synthetic test models cannot be used as production profiles", 4)
    mode = data.get("field86_mode")
    if mode not in {"native", "bank_profile", "reconstructed", f"datev_verified:{name}"}:
        raise MT940Error("Use native, bank_profile or explicit reconstructed mode", 4)
    if mode == "reconstructed" and not reconstruction:
        raise MT940Error("Reconstructed mode requires a source_reconstruction model", 4)
    if mode == "native" and data.get("source_type") != "native_mt940":
        raise MT940Error("native mode requires a native_mt940 source", 4)
    if mode == "native" and (profile["statement_reference_rule"] != "source"
                             or rules != {"customer_reference": "exact", "bank_reference": "exact"}):
        raise MT940Error("Native models must preserve source references exactly", 4)
    if mode != "native" and not reconstruction and profile["status"] == "draft" and data.get("output_scope") != "test":
        raise MT940Error("A draft bank model may produce only a clearly labeled test file", 4)
    adapter = profile.get("adapter")
    if mode != "native" or adapter:
        if not isinstance(adapter, str) or not re.fullmatch(r"[a-z0-9-]+\.py", adapter):
            raise MT940Error("Bank model requires its own encode/decode adapter; no default adapter", 4)
        adapter_path = path.parent / adapter
        if not adapter_path.is_file() or hashlib.sha256(adapter_path.read_bytes()).hexdigest() != profile.get("adapter_sha256"):
            raise MT940Error("Bank adapter missing/changed; review and version the model first", 4)
        spec = importlib.util.spec_from_file_location(f"bank_{name.replace('-', '_')}", adapter_path)
        if spec is None or spec.loader is None:
            raise MT940Error("Cannot load bank adapter", 4)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            raise MT940Error(f"Cannot load bank adapter: {exc}", 4) from exc
        if not all(callable(getattr(module, method, None)) for method in ("encode_field86", "decode_field86")):
            raise MT940Error("Bank adapter needs encode_field86 and independent decode_field86", 4)
        profile["_adapter"] = module
    if mode.startswith("datev_verified:") or (str(data.get("target_system", "")).upper() == "DATEV"
                                             and mode not in {"native", "reconstructed"} and data.get("output_scope", "full") != "test") or (mode == "reconstructed" and profile["status"] == "verified"):
        require_probe_import(profile)
    for example in profile["examples"]:
        if not isinstance(example, dict) or not isinstance(example.get("source_transaction"), dict):
            raise MT940Error("Each bank reference example needs its original source_transaction", 4)
        lines = example.get("mt940")
        if not isinstance(lines, list) or len(lines) < 2 or not isinstance(lines[0], str) or not lines[0].startswith(":61:"):
            raise MT940Error("Each bank reference example needs complete :61:/:86: lines", 4)
        if mode != "native" and bank_field86_result(example["source_transaction"], profile).lines != lines[1:]:
            raise MT940Error("Bank adapter differs from its fixed reference example", 4)
        if mode == "native" and native_field86_result(example["source_transaction"].get("native_field86_lines")).lines != lines[1:]:
            raise MT940Error("Native bank reference example does not preserve original lines", 4)
    return profile


def require_probe_import(profile: dict[str, Any]) -> None:
    checks = profile.get("probe_import", {}).get("checks", {})
    required_checks = (
        "opening_balance_correct",
        "test_closing_balance_correct",
        "transaction_count_and_signs_correct",
        "description_complete",
        "no_visible_control_characters",
        "all_source_fields_correct",
    )
    if (
        profile.get("status") != "verified"
        or not profile.get("probe_import", {}).get("date")
        or profile.get("probe_import", {}).get("result") != "successful"
        or not all(checks.get(item) is True for item in required_checks)
        or profile.get("probe_import", {}).get("test_transactions_deleted") is not True
    ):
        raise MT940Error(
            f"Bank model {profile['profile_name']!r} lacks a successful, cleaned-up probe import", 4
        )


def modeled_reference(value: object, field: str, profile: dict[str, Any], number: int) -> str:
    rule = profile["reference_rules"][field]
    if rule == "source_or_sequence_9" and not value:
        return f"{number:09d}"
    if field == "customer_reference" and not value:
        if profile.get("missing_customer_reference") != "NONREF":
            raise MT940Error("Missing customer reference has no bank-specific modeled fallback", 2)
        return "NONREF"
    if rule == "upper_alnum_16":
        return normalize_reference(value, "NONREF")
    if not isinstance(value, str) or not re.fullmatch(r"[^/\r\n\x00-\x1f]{1,16}", value):
        raise MT940Error(f"{field} cannot be represented exactly; no silent reference rewrite", 2)
    try:
        value.encode("cp1252", errors="strict")
    except UnicodeEncodeError as exc:
        raise MT940Error(f"{field} is not representable in Windows-1252", 3) from exc
    return value


def bank_field86_result(tx: dict[str, Any], profile: dict[str, Any]) -> Field86Result:
    source = canonical_description(tx.get("description"))
    try:
        encoded = profile["_adapter"].encode_field86(tx)
        physical = native_field86_result(encoded)
        decoded = profile["_adapter"].decode_field86(physical.lines)
    except MT940Error:
        raise
    except Exception as exc:
        raise MT940Error(f"Bank adapter failed: {exc}", 3) from exc
    if not isinstance(decoded, dict) or decoded.get("description") != source:
        raise MT940Error("Bank model :86: decode differs from the complete source description", 3)
    if decoded.get("source_fields", {}) != tx.get("source_fields", {}):
        raise MT940Error("Bank model :86: decode loses or swaps named source fields", 3)
    if profile.get("field86_structure") != "unstructured" and underfields(physical.canonical_description) - set(profile.get("allowed_underfields", [])):
        raise MT940Error("Bank adapter emitted underfields outside its reference model", 3)
    return Field86Result(physical.lines, len(source), physical.encoded_description_length,
                         True, False, source)


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

    target = str(data.get("target_system", "")).upper()
    if target not in {"DATEV", "GENERIC"}:
        raise MT940Error("target_system must explicitly be DATEV or GENERIC", 2)
    required_dates = ("statement_start", "statement_end", "opening_balance_date", "closing_balance_date")
    missing = [field for field in required_dates if not data.get(field)]
    if missing:
        raise MT940Error("Bank manifests require separate statement and balance dates; missing: "
                         + ", ".join(missing), 2)
    if "sequence_number" not in data:
        raise MT940Error("Bank manifests must explicitly store sequence_number", 2)
    statement_start_value = data.get("statement_start")
    statement_end_value = data.get("statement_end")
    opening_date_value = data.get("opening_balance_date")
    closing_date_value = data.get("closing_balance_date")
    statement_number = _positive_int(data.get("statement_number"), "statement_number", 99999)
    sequence_number = _positive_int(data.get("sequence_number"), "sequence_number", 999)

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

    field86_mode = str(data.get("field86_mode", ""))
    allowed_modes = {"native", "bank_profile", "reconstructed"}
    if field86_mode not in allowed_modes and not field86_mode.startswith("datev_verified:"):
        raise MT940Error(f"Unsupported field86_mode: {field86_mode!r}", 4)
    profile = load_profile(data, profile_dir)
    output_scope = str(data.get("output_scope", "full"))
    source_type = str(data.get("source_type", "structured_list")).lower()
    if output_scope not in {"full", "test"}:
        raise MT940Error("output_scope must be 'full' or 'test'", 2)

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
        code = tx.get("code")
        if not isinstance(code, str) or not CODE_RE.fullmatch(code):
            raise MT940Error(f"Transaction {index} has invalid code {code!r}", 2)
        source_page: int | None = None
        source_line_count: int | None = None
        source_to_manifest_match: bool | None = None
        if field86_mode == "native":
            if tx.get("source_fields") and "_adapter" not in profile:
                raise MT940Error("Native named fields require the bank model's decoder; preserve the raw lines", 4)
            description_result = native_field86_result(tx.get("native_field86_lines"))
            if "description" in tx and tx["description"] != description_result.canonical_description:
                raise MT940Error(
                    f"Transaction {index} description differs from exact native :86: lines", 2
                )
            source_line_count = len(tx["native_field86_lines"])
            source_to_manifest_match = True
        elif source_type in {"pdf", "image"}:
            source_text, source_page, source_line_count = verified_pdf_description(tx, index)
            tx["description"] = source_text
            description_result = bank_field86_result(tx, profile)
            source_to_manifest_match = True
        else:
            description_result = bank_field86_result(tx, profile)
        customer_reference = modeled_reference(tx.get("customer_reference"), "customer_reference", profile, index)
        bank_reference = modeled_reference(tx.get("bank_reference"), "bank_reference", profile, index)
        if field86_mode != "native":
            for key, converted in (("customer_reference", customer_reference), ("bank_reference", bank_reference)):
                raw_reference = tx.get(key)
                if raw_reference and converted != raw_reference and raw_reference not in description_result.canonical_description:
                    raise MT940Error(f"Transaction {index}: transformed {key} must also remain complete in :86:", 2)
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
                "_source_fields": tx.get("source_fields", {}),
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
                "source_fields": tx["_source_fields"],
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
