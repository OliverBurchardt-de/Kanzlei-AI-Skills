from __future__ import annotations

import calendar
import re
import unicodedata
import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable


class Raw(str):
    """Value written without DATEV text quotes."""


class Quoted(str):
    """DATEV text value, including an explicitly quoted empty value."""


BOOKING_FIELDS = [
    "Umsatz (ohne Soll/Haben-Kz)", "Soll/Haben-Kennzeichen", "WKZ Umsatz",
    "Kurs", "Basis-Umsatz", "WKZ Basis-Umsatz", "Konto",
    "Gegenkonto (ohne BU-Schlüssel)", "BU-Schlüssel", "Belegdatum",
    "Belegfeld 1", "Belegfeld 2", "Skonto", "Buchungstext", "Postensperre",
    "Diverse Adressnummer", "Geschäftspartnerbank", "Sachverhalt",
    "Zinssperre", "Beleglink",
]
for _i in range(1, 9):
    BOOKING_FIELDS.extend([f"Beleginfo - Art {_i}", f"Beleginfo - Inhalt {_i}"])
BOOKING_FIELDS.extend([
    "KOST1 - Kostenstelle", "KOST2 - Kostenstelle", "Kost-Menge",
    "EU-Land u. UStID (Bestimmung)", "EU-Steuersatz (Bestimmung)",
    "Abw. Versteuerungsart", "Sachverhalt L+L", "Funktionsergänzung L+L",
    "BU 49 Hauptfunktionstyp", "BU 49 Hauptfunktionsnummer",
    "BU 49 Funktionsergänzung",
])
for _i in range(1, 21):
    BOOKING_FIELDS.extend([
        f"Zusatzinformation - Art {_i}",
        f"Zusatzinformation- Inhalt {_i}",
    ])
BOOKING_FIELDS.extend([
    "Stück", "Gewicht", "Zahlweise", "Forderungsart", "Veranlagungsjahr",
    "Zugeordnete Fälligkeit", "Skontotyp", "Auftragsnummer", "Buchungstyp",
    "USt-Schlüssel (Anzahlungen)", "EU-Land (Anzahlungen)",
    "Sachverhalt L+L (Anzahlungen)", "EU-Steuersatz (Anzahlungen)",
    "Erlöskonto (Anzahlungen)", "Herkunft-Kz", "Buchungs GUID", "KOST-Datum",
    "SEPA-Mandatsreferenz", "Skontosperre", "Gesellschaftername",
    "Beteiligtennummer", "Identifikationsnummer", "Zeichnernummer",
    "Postensperre bis", "Bezeichnung SoBil-Sachverhalt",
    "Kennzeichen SoBil-Buchung", "Festschreibung", "Leistungsdatum",
    "Datum Zuord. Steuerperiode", "Fälligkeit", "Generalumkehr (GU)",
    "Steuersatz", "Land", "Abrechnungsreferenz",
    "BVV-Position", "EU-Land u. UStID (Ursprung)",
    "EU-Steuersatz (Ursprung)", "Abw. Skontokonto",
])
assert len(BOOKING_FIELDS) == 125


MASTER_FIELDS = [
    "Konto", "Name (Adressatentyp Unternehmen)", "Unternehmensgegenstand",
    "Name (Adressatentyp natürl. Person)", "Vorname (Adressatentyp natürl. Person)",
    "Name (Adressatentyp keine Angabe)", "Adressatentyp", "Kurzbezeichnung",
    "EU-Land", "EU-UStID", "Anrede", "Titel / Akad. Grad", "Adelstitel",
    "Namensvorsatz", "Adressart", "Straße", "Postfach", "Postleitzahl", "Ort",
    "Land", "Versandzusatz", "Adresszusatz", "Abweichende Anrede",
    "Abw. Zustellbezeichnung 1", "Abw. Zustellbezeichnung 2",
    "Kennz. Korrespondenzadresse", "Adresse Gültig von", "Adresse Gültig bis",
    "Telefon", "Bemerkung (Telefon)", "Telefon Geschäftsleitung",
    "Bemerkung (Telefon GL)", "E-Mail", "Bemerkung (E-Mail)", "Internet",
    "Bemerkung (Internet)", "Fax", "Bemerkung (Fax)", "Sonstige",
    "Bemerkung (Sonstige)",
]


def _bank_fields(number: int) -> list[str]:
    return [
        f"Bankleitzahl {number}", f"Bankbezeichnung {number}",
        f"Bankkonto-Nummer {number}", f"Länderkennzeichen {number}",
        f"IBAN-Nr. {number}", "Leerfeld", f"SWIFT-Code {number}",
        f"Abw. Kontoinhaber {number}", f"Kennz. Hauptbankverb. {number}",
        f"Bankverb. {number} Gültig von", f"Bankverb. {number} Gültig bis",
    ]


for _i in range(1, 6):
    MASTER_FIELDS.extend(_bank_fields(_i))
MASTER_FIELDS.extend([
    "Leerfeld", "Briefanrede", "Grußformel", "Kundennummer", "Steuernummer",
    "Sprache", "Ansprechpartner", "Vertreter", "Sachbearbeiter", "Diverse-Konto",
    "Ausgabeziel", "Währungssteuerung", "Kreditlimit (Debitor)",
    "Zahlungsbedingung", "Fälligkeit in Tagen (Debitor)",
    "Skonto in Prozent (Debitor)", "Kreditoren-Ziel 1 (Tage)",
    "Kreditoren-Skonto 1 (%)", "Kreditoren-Ziel 2 (Tage)",
    "Kreditoren-Skonto 2 (%)", "Kreditoren-Ziel 3 Brutto (Tage)",
    "Kreditoren-Ziel 4 (Tage)", "Kreditoren-Skonto 4 (%)",
    "Kreditoren-Ziel 5 (Tage)", "Kreditoren-Skonto 5 (%)", "Mahnung",
    "Kontoauszug", "Mahntext 1", "Mahntext 2", "Mahntext 3",
    "Kontoauszugstest", "Mahnlimit Betrag", "Mahnlimit %",
    "Zinsberechnung", "Mahnzinssatz 1", "Mahnzinssatz 2", "Mahnzinssatz 3",
    "Lastschrift", "Leerfeld", "Mandantenbank", "Zahlungsträger",
])
MASTER_FIELDS.extend([f"Indiv. Feld {_i}" for _i in range(1, 16)])
MASTER_FIELDS.extend([
    "Abweichende Anrede (Rechnungsadresse)",
    "Adressart (Rechnungsadresse)", "Straße (Rechnungsadresse)",
    "Postfach (Rechnungsadresse)", "Postleitzahl (Rechnungsadresse)",
    "Ort (Rechnungsadresse)", "Land (Rechnungsadresse)",
    "Versandzusatz (Rechnungsadresse)", "Adresszusatz (Rechnungsadresse)",
    "Abw. Zustellbezeichnung 1 (Rechnungsadresse)",
    "Abw. Zustellbezeichnung 2 (Rechnungsadresse)",
    "Adresse Gültig von (Rechnungsadresse)",
    "Adresse Gültig bis (Rechnungsadresse)",
])
for _i in range(6, 11):
    MASTER_FIELDS.extend(_bank_fields(_i))
MASTER_FIELDS.extend([
    "Nummer Fremdsystem", "Insolvent",
])
MASTER_FIELDS.extend([f"SEPA-Mandatsreferenz {_i}" for _i in range(1, 11)])
MASTER_FIELDS.extend([
    "Verknüpftes OPOS-Konto", "Mahnsperre bis", "Lastschriftsperre bis",
    "Zahlungssperre bis", "Gebührenberechnung", "Mahngebühr 1",
    "Mahngebühr 2", "Mahngebühr 3", "Pauschalenberechnung",
    "Verzugspauschale 1", "Verzugspauschale 2", "Verzugspauschale 3",
    "Alternativer Suchname", "Status",
    "Anschrift manuell geändert (Korrespondenzadresse)",
    "Anschrift individuell (Korrespondenzadresse)",
    "Anschrift manuell geändert (Rechnungsadresse)",
    "Anschrift individuell (Rechnungsadresse)", "Fristberechnung bei Debitor",
    "Mahnfrist 1", "Mahnfrist 2", "Mahnfrist 3", "Letzte Frist",
])
assert len(MASTER_FIELDS) == 254

HEADER_TEXT_FIELDS = {1,4,8,9,10,17,18,22,24,27,30,31}
BOOKING_TEXT_FIELDS = {2,3,9,11,12,14,16,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,40,42,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,91,95,96,98,102,103,105,107,109,110,112,118,120,121,123}
MASTER_TEXT_FIELDS = {2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,52,53,54,55,56,57,58,59,60,63,64,65,66,67,68,69,70,71,74,75,76,77,78,79,80,81,82,85,86,87,88,89,90,91,92,93,96,97,98,99,100,102,103,104,133,134,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,154,155,156,157,158,159,160,161,162,165,166,167,168,169,170,171,172,173,176,177,178,179,180,181,182,183,184,187,188,189,190,191,192,193,194,195,198,199,200,201,202,203,204,205,206,209,210,211,212,213,214,215,216,217,220,222,223,224,225,226,227,228,229,230,231,244,247,249}


def clean_text(value: Any, max_length: int | None = None) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"[\x00-\x1f\x7f]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if max_length:
        text = text[:max_length]
    return text


def normalize_document_field(value: Any) -> str:
    text = clean_text(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^A-Za-z0-9_$&%*+\-/]", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:36]


def ascii_filename(value: str, fallback: str = "beleg") -> str:
    path = Path(value)
    stem = unicodedata.normalize("NFKD", path.stem)
    stem = "".join(ch for ch in stem if not unicodedata.combining(ch))
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._")
    return f"{stem or fallback}{path.suffix.lower()}"


def decimal_value(value: Any) -> Decimal:
    try:
        result = Decimal(str(value).replace(".", "").replace(",", ".")) if (
            isinstance(value, str) and "," in value
        ) else Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Ungültiger Geldwert: {value}") from exc
    if result <= 0:
        raise ValueError(f"Betrag muss positiv sein: {value}")
    return result.quantize(Decimal("0.01"))


def decimal_raw(value: Any) -> Raw:
    return Raw(format(decimal_value(value), "f").replace(".", ","))


def parse_positive_decimal(value: Any, field: str) -> Decimal:
    text = str(value).strip().replace(" ", "")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        result = Decimal(text)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Ungültiger Wert für {field}: {value}") from exc
    if result <= 0:
        raise ValueError(f"{field} muss positiv sein: {value}")
    return result


def exchange_rate_raw(value: Any) -> Raw:
    rate = parse_positive_decimal(value, "Kurs")
    normalized = format(rate, "f")
    if "." not in normalized:
        normalized += ".00"
    else:
        integer, fraction = normalized.split(".", 1)
        fraction = fraction.rstrip("0").ljust(2, "0")[:6]
        normalized = f"{integer}.{fraction}"
    return Raw(normalized.replace(".", ","))


def digits_raw(value: Any, field: str) -> Raw:
    text = clean_text(value)
    if not text.isdigit():
        raise ValueError(f"{field} muss numerisch sein: {value}")
    return Raw(text)


def ddmm_raw(iso_date: str | None) -> Raw | None:
    if not iso_date:
        return None
    try:
        date_value = datetime.strptime(iso_date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"Ungültiges Kalenderdatum: {iso_date}") from exc
    return Raw(date_value.strftime("%d%m"))


def ddmmyyyy_raw(iso_date: str | None, field: str) -> Raw | None:
    if not iso_date:
        return None
    try:
        date_value = datetime.strptime(str(iso_date), "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"Ungültiges Kalenderdatum für {field}: {iso_date}") from exc
    return Raw(date_value.strftime("%d%m%Y"))


def month_bounds(period: str) -> tuple[str, str]:
    try:
        year, month = (int(part) for part in period.split("-"))
        last = calendar.monthrange(year, month)[1]
    except Exception as exc:
        raise ValueError(f"Ungültige Buchungsperiode: {period}") from exc
    return f"{year:04d}{month:02d}01", f"{year:04d}{month:02d}{last:02d}"


def fiscal_year_start(reference_start: str, period: str) -> str:
    try:
        reference = datetime.strptime(reference_start, "%Y-%m-%d").date()
        period_start = datetime.strptime(f"{period}-01", "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(
            f"Ungültiger Wirtschaftsjahresbeginn oder Periode: "
            f"{reference_start}, {period}"
        ) from exc
    candidate = date(period_start.year, reference.month, reference.day)
    if period_start < candidate:
        candidate = date(period_start.year - 1, reference.month, reference.day)
    return candidate.strftime("%Y%m%d")


def _serialize(value: Any) -> str:
    if isinstance(value, Quoted):
        return f'"{clean_text(value).replace(chr(34), chr(34) * 2)}"'
    if value is None:
        return ""
    if isinstance(value, Raw):
        return str(value)
    if isinstance(value, (int, Decimal)):
        return str(value).replace(".", ",")
    text = clean_text(value).replace('"', '""')
    return f'"{text}"'


def write_extf(path: Path, header: Iterable[Any], fields: list[str],
               rows: Iterable[list[Any]]) -> None:
    encoded_header = [
        Quoted("") if index in HEADER_TEXT_FIELDS and value in (None, "") else value
        for index, value in enumerate(header, start=1)
    ]
    row_text_fields = BOOKING_TEXT_FIELDS if len(fields) == 125 else MASTER_TEXT_FIELDS
    lines = [
        ";".join(_serialize(v) for v in encoded_header),
        ";".join(fields),
    ]
    for row in rows:
        if len(row) != len(fields):
            raise ValueError(
                f"Falsche Feldanzahl für {path.name}: {len(row)} statt {len(fields)}"
            )
        encoded_row = [
            Quoted("") if index in row_text_fields and value in (None, "") else value
            for index, value in enumerate(row, start=1)
        ]
        lines.append(";".join(_serialize(v) for v in encoded_row))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(("\r\n".join(lines) + "\r\n").encode("cp1252", errors="strict"))


def extf_header(run: dict[str, Any], *, category: int, format_name: str,
                version: int, label: str = "", period: str | None = None) -> list[Any]:
    created = datetime.now().strftime("%Y%m%d%H%M%S%f")[:17]
    date_from, date_to = ("", "")
    if period:
        date_from, date_to = month_bounds(period)
    movement = category == 21
    wj_start = (
        fiscal_year_start(str(run["wirtschaftsjahr_beginn"]), period)
        if period else str(run["wirtschaftsjahr_beginn"]).replace("-", "")
    )
    dictation = clean_text(run.get("diktatkuerzel", "BK")).upper()
    if movement and not re.fullmatch(r"(?:[A-Z]{2}){1,2}", dictation):
        raise ValueError(
            "Diktatkürzel muss aus zwei oder vier Großbuchstaben bestehen."
        )
    return [
        "EXTF", 700, category, format_name, version, Raw(created), None,
        "RE", "", "", int(run["beraternummer"]), int(run["mandantennummer"]),
        Raw(wj_start),
        int(run["sachkontenlaenge"]),
        Raw(date_from) if date_from else None,
        Raw(date_to) if date_to else None,
        clean_text(label, 30) if movement else "",
        dictation if movement else "",
        1 if movement else None,
        0 if movement else None,
        0 if movement else None,
        run.get("waehrung", "EUR") if movement else None,
        None, "", None, None, str(run.get("sachkontenrahmen", "")),
        None, None, "", "",
    ]


def booking_row(
    document: dict[str, Any],
    booking: dict[str, Any],
    run: dict[str, Any] | None = None,
) -> list[Any]:
    row: list[Any] = [None] * 125
    traffic = document["traffic_light"]
    if booking.get("debit_credit") not in {"S", "H"}:
        raise ValueError(f"Ungültiges Soll/Haben bei {document['transaction_id']}")
    bu_key = clean_text(booking.get("bu_key", ""))
    if re.fullmatch(r"0\d{3}", bu_key):
        bu_key = bu_key[1:]
    if bu_key and not re.fullmatch(r"\d{3}", bu_key):
        raise ValueError(
            f"BU-Schlüssel muss fachlich dreistellig sein: {bu_key}"
        )
    extf_bu_key = f"0{bu_key}" if bu_key else ""
    doc_field = normalize_document_field(
        booking.get("document_field_1") or document.get("invoice_number")
        or f"ERSATZ-{document['transaction_id']}"
    )
    if not doc_field:
        raise ValueError(f"Belegfeld 1 fehlt: {document['transaction_id']}")
    row[0] = decimal_raw(booking["amount"])
    row[1] = booking["debit_credit"]
    currency = clean_text(document.get("currency", "EUR")).upper()
    base_currency = clean_text(
        (run or {}).get("waehrung", document.get("base_currency", currency))
    ).upper()
    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise ValueError(f"Ungültiges Währungskennzeichen: {currency}")
    if not re.fullmatch(r"[A-Z]{3}", base_currency):
        raise ValueError(f"Ungültige Basiswährung: {base_currency}")
    row[2] = currency
    if currency != base_currency:
        missing_currency_fields = [
            key for key in ("exchange_rate", "base_amount")
            if booking.get(key) in (None, "")
        ]
        if missing_currency_fields:
            raise ValueError(
                f"Fremdwährungsbuchung {document['transaction_id']} ohne "
                f"{', '.join(missing_currency_fields)}"
            )
        row[3] = exchange_rate_raw(booking["exchange_rate"])
        row[4] = decimal_raw(booking["base_amount"])
        row[5] = base_currency
    row[6] = digits_raw(booking["account"], "Konto")
    row[7] = digits_raw(booking["contra_account"], "Gegenkonto")
    row[8] = extf_bu_key
    configured_asset_accounts = {
        clean_text(value)
        for value in (run or {}).get("account_config", {}).get("asset_accounts", [])
    }
    booking_accounts = {
        clean_text(booking.get("account", "")),
        clean_text(booking.get("contra_account", "")),
    }
    is_asset_booking = (
        document.get("asset_booking") is True
        or bool(configured_asset_accounts.intersection(booking_accounts))
    )
    if is_asset_booking and traffic != "Rot":
        raise ValueError(
            f"Anlagenbuchung {document['transaction_id']} muss Rot sein; "
            "das DATEV-Belegdatum muss leer bleiben."
        )
    row[9] = (
        None
        if traffic == "Rot" or is_asset_booking
        else ddmm_raw(document.get("recognized_date"))
    )
    row[10] = doc_field
    text = clean_text(booking.get("booking_text", ""), 60)
    warning_pattern = re.compile(
        r"\b(?:ACHTUNG|PRÜFUNG\s+ERFORDERLICH|"
        r"PRUEFUNG\s+ERFORDERLICH|PRÜFEN|PRUEFEN)\b",
        re.IGNORECASE,
    )
    if not text or warning_pattern.search(text):
        partner = clean_text(document.get("partner", ""), 25)
        subject = clean_text(
            booking.get("account_name") or document.get("document_type") or "Beleg",
            30,
        )
        text = clean_text(f"{partner} {subject}".strip() or "Belegbuchung", 60)
    row[13] = text
    document_guid = clean_text(document.get("document_guid", ""))
    if document_guid:
        try:
            parsed_guid = uuid.UUID(document_guid)
        except ValueError as exc:
            raise ValueError(
                f"Ungültige Beleg-GUID bei {document['transaction_id']}: "
                f"{document_guid}"
            ) from exc
        row[19] = f'BEDI "{str(parsed_guid).upper()}"'
    service_date = booking.get("service_date")
    tax_period_date = booking.get("tax_period_date")
    if service_date and not tax_period_date:
        raise ValueError(
            f"Leistungsdatum bei {document['transaction_id']} erfordert "
            "Datum Zuord. Steuerperiode."
        )
    row[114] = ddmmyyyy_raw(service_date, "Leistungsdatum")
    row[115] = ddmmyyyy_raw(tax_period_date, "Datum Zuord. Steuerperiode")
    return row


def master_row(record: dict[str, Any]) -> list[Any]:
    banks = record.get("banks", [])
    if len(banks) > 10:
        raise ValueError(f"Mehr als zehn Banken bei Konto {record.get('account')}")
    if record.get("action") != "Neuanlage" and not record.get(
        "full_current_record_available"
    ):
        raise ValueError(
            f"Teiländerung eines Stammdatensatzes unzulässig: {record.get('account')}"
        )
    account_type = clean_text(record.get("account_type", "")).lower()
    if account_type not in {"kreditor", "debitor"}:
        raise ValueError(
            f"account_type muss Kreditor oder Debitor sein: "
            f"{record.get('account_type')}"
        )
    name = clean_text(record.get("name", ""), 50)
    if not name:
        raise ValueError(f"Name fehlt bei Konto {record.get('account')}")
    primary_banks = sum(bool(bank.get("is_primary")) for bank in banks)
    if primary_banks > 1:
        raise ValueError(
            f"Mehr als eine Hauptbankverbindung bei Konto {record.get('account')}"
        )
    seen_ibans: set[str] = set()
    row: list[Any] = [None] * 254
    row[0] = digits_raw(record["account"], "Personenkonto")
    row[1] = name
    row[6] = Raw("2")
    row[7] = clean_text(record.get("short_name") or name, 15)
    vat = clean_text(record.get("vat_id", "")).replace(" ", "").upper()
    eu_country = clean_text(record.get("eu_country", "")).upper()
    if vat and len(vat) >= 3 and vat[:2].isalpha():
        eu_country = eu_country or vat[:2]
        vat = vat[2:]
    if vat and (len(vat) > 13 or not re.fullmatch(r"[A-Z0-9]+", vat)):
        raise ValueError(f"Ungültige EU-UStID bei Konto {record.get('account')}")
    if eu_country and not re.fullmatch(r"[A-Z]{2}", eu_country):
        raise ValueError(f"Ungültiges EU-Land bei Konto {record.get('account')}")
    row[8] = eu_country
    row[9] = vat
    street = clean_text(record.get("street", ""), 36)
    row[14] = clean_text(
        record.get("address_type") or ("STR" if street else ""), 3
    )
    row[15] = street
    row[17] = clean_text(record.get("postal_code", ""), 10)
    row[18] = clean_text(record.get("city", ""), 30)
    row[19] = clean_text(record.get("country", ""), 2)
    row[28] = clean_text(record.get("phone", ""), 30)
    row[32] = clean_text(record.get("email", ""), 60)
    starts = [40, 51, 62, 73, 84, 164, 175, 186, 197, 208]
    for bank, start in zip(banks, starts):
        iban = clean_text(bank.get("iban", "")).replace(" ", "").upper()
        if iban:
            if not re.fullmatch(r"[A-Z]{2}[A-Z0-9]{13,32}", iban):
                raise ValueError(
                    f"Ungültige IBAN bei Konto {record.get('account')}: {iban}"
                )
            if iban in seen_ibans:
                raise ValueError(
                    f"Doppelte IBAN bei Konto {record.get('account')}: {iban}"
                )
            seen_ibans.add(iban)
        row[start] = clean_text(bank.get("bank_code", ""), 8)
        row[start + 1] = clean_text(bank.get("bank_name", ""), 30)
        row[start + 2] = clean_text(bank.get("account_number", ""), 10)
        row[start + 3] = clean_text(bank.get("country") or iban[:2], 2)
        row[start + 4] = iban
        row[start + 6] = clean_text(bank.get("bic", ""), 11)
        row[start + 7] = clean_text(bank.get("account_holder", ""), 70)
        row[start + 8] = Raw("1") if bank.get("is_primary") else None
        row[start + 9] = ddmmyyyy_raw(
            bank.get("valid_from"), f"Bank {start} gültig von"
        )
        row[start + 10] = ddmmyyyy_raw(
            bank.get("valid_to"), f"Bank {start} gültig bis"
        )
    return row
