"""Different synthetic bank format to exercise bank-specific field assignment."""

from mt940_common import field86_result


def encode_field86(transaction):
    fields = transaction["source_fields"]
    if set(fields) != {"counterparty"}:
        raise ValueError("Exactly counterparty is required in this test variant")
    return field86_result("?20" + transaction["description"] + "?32" + fields["counterparty"]).lines


def decode_field86(lines):
    text = lines[0][4:] + "".join(lines[1:])
    if not text.startswith("?20") or text.count("?32") != 1:
        raise ValueError("Unexpected field order for this synthetic bank")
    description, counterparty = text[3:].split("?32")
    return {"description": description, "source_fields": {"counterparty": counterparty}}
