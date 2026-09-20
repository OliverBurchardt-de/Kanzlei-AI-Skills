"""Independent reader for the Dortmunder Volksbank reconstruction model only."""
import re
from datetime import date
from decimal import Decimal

def fail(message):
    raise ValueError(message)

def read_date(text):
    return date(2000 + int(text[:2]), int(text[2:4]), int(text[4:6])).isoformat()

def money(sign, text):
    value = Decimal(text.replace(",", "."))
    return format(value if sign == "C" else -value, ".2f")

def field86(lines):
    if not 1 <= len(lines) <= 6 or any(len(x) > 65 for x in lines):
        fail("Invalid :86: physical length")
    value = lines[0][4:] + "".join(lines[1:])
    if not re.match(r"\d{3}\?00", value):
        fail("Missing three-digit GVC or ?00")
    gvc, rest = value[:3], value[3:]
    if gvc not in {"020", "051", "118", "805", "835"}:
        fail("Unsupported GVC for this bank model")
    parts = re.findall(r"\?(\d{2})([^?]*)", rest)
    if "".join("?" + k + v for k, v in parts) != rest:
        fail("Malformed subfields")
    keys = [k for k, _ in parts]
    allowed = ["00"] + [str(n) for n in range(20,30)] + ["32", "33"]
    if len(keys) != len(set(keys)) or any(k not in allowed for k in keys):
        fail("Duplicate or wrong subfield roles")
    if keys != sorted(keys):
        fail("Wrong subfield order")
    fields = dict(parts)
    if any(not v or len(v) > 27 for v in fields.values()):
        fail("Empty/overlong subfield")
    purpose_keys = [k for k in keys if 20 <= int(k) <= 29]
    if purpose_keys != [str(n) for n in range(20,20+len(purpose_keys))]:
        fail("Purpose subfield gap")
    if "33" in fields and "32" not in fields:
        fail("Counterparty continuation without beginning")
    return {"gvc":gvc, "type":fields["00"],
            "purpose":"".join(fields[k] for k in purpose_keys),
            "counterparty":fields.get("32","")+fields.get("33","")}

def parse(payload):
    if payload.startswith(b"\xef\xbb\xbf") or not payload.endswith(b"\r\n"):
        fail("BOM or missing final CRLF")
    if b"\n" in payload.replace(b"\r\n",b"") or b"\r" in payload.replace(b"\r\n",b""):
        fail("CRLF required")
    text = payload.decode("cp850", errors="strict")
    if any(ord(c)<32 for c in text.replace("\r\n","")):
        fail("Control character")
    lines = text.split("\r\n")[:-1]
    if any(not x or len(x)>65 for x in lines):
        fail("Empty/overlong physical line")
    index = 0
    statements = []
    def take(tag):
        nonlocal index
        if index >= len(lines) or not lines[index].startswith(tag):
            fail("Expected "+tag)
        value = lines[index][len(tag):]
        index += 1
        return value
    def balance(tag):
        value = take(tag)
        match = re.fullmatch(r"([CD])(\d{6})EUR(\d+,\d{2})",value)
        if not match:
            fail("Malformed balance")
        sign, day, amount = match.groups()
        return {"date":read_date(day),"amount":money(sign,amount)}
    while index < len(lines):
        reference = take(":20:")
        if not re.fullmatch(r"[A-Z0-9]{1,16}", reference):
            fail("Invalid statement reference")
        iban = take(":25:")
        number = take(":28C:")
        if not re.fullmatch(r"\d{5}/001",number):
            fail("Invalid statement number/sequence")
        opening = balance(":60F:")
        transactions = []
        while index<len(lines) and lines[index].startswith(":61:"):
            entry = take(":61:")
            match = re.fullmatch(r"(\d{6})(\d{4})([CD])(\d+,\d{2})(N[A-Z]{3})([^/]{1,16})",entry)
            if not match:
                fail("Malformed :61:")
            vd, md, sign, amt, code, customer = match.groups()
            value_date = read_date(vd)
            # Booking year belongs to the statement, not automatically to valuta.
            year = int(reference[2:6]) if re.fullmatch(r"DV\d{4}\d{5}",reference) else int(opening["date"][:4])
            candidates = []
            for candidate_year in (year-1,year,year+1):
                try:
                    candidate = date(candidate_year,int(md[:2]),int(md[2:]))
                    candidates.append(candidate)
                except ValueError:
                    pass
            if not candidates:
                fail("Invalid booking date")
            booking = min(candidates,key=lambda d:abs((d-date.fromisoformat(value_date)).days))
            group = [":86:"+take(":86:")]
            while index<len(lines) and not lines[index].startswith(":") and lines[index]!="-":
                group.append(lines[index])
                index+=1
            detail=field86(group)
            detail.update({"booking_date":booking.isoformat(),"value_date":value_date,
                           "amount":money(sign,amt),"code":code,"customer_reference":customer})
            transactions.append(detail)
        closing = balance(":62F:")
        if index>=len(lines) or lines[index]!="-":
            fail("Missing statement terminator")
        index+=1
        if Decimal(opening["amount"])+sum((Decimal(t["amount"]) for t in transactions),Decimal(0)) != Decimal(closing["amount"]):
            fail("Balance mismatch")
        if statements and (statements[-1]["closing"]!=opening or statements[-1]["iban"]!=iban):
            fail("Broken account/balance chain")
        statements.append({"reference":reference,"iban":iban,"number":int(number[:5]),
                           "opening":opening,"closing":closing,"transactions":transactions})
    if not statements:
        fail("Empty file")
    return statements
