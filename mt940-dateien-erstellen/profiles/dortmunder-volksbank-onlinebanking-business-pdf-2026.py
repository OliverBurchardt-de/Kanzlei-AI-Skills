"""Reconstructed Dortmunder Volksbank Business PDF; no native-bank syntax claim."""
import re
from mt940_common import field86_result

def encode_field86(transaction):
    return field86_result(transaction["description"]).lines

def decode_field86(lines):
    if not lines or not lines[0].startswith(":86:"):
        raise ValueError("Missing :86:")
    text = lines[0][4:] + "".join(lines[1:])
    label = re.match(r"^(.*?) (?=DE\d{20}\b|Abschluss per\b)", text)
    if not label:
        raise ValueError("Booking label boundary not recognized in this source variant")
    fields = {"counterparty_or_booking_label": label.group(1)}
    iban = re.search(r"\b(DE\d{20})\b", text)
    if iban:
        fields["counterparty_iban"] = iban.group(1)
    patterns = {
        "bic_in_description": r"BIC: ([A-Z0-9]+)",
        "end_to_end_reference": r"EREF: (\S+)",
        "mandate_reference": r"MREF: (\S+)",
        "creditor_identifier": r"CRED: (\S+)",
        "reference_in_description": r"\bREF (\S+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            fields[key] = match.group(1)
    return {"description": text, "source_fields": fields}
