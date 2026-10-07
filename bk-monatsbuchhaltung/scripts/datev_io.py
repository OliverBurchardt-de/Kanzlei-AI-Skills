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


OPEN_FIELD_INDEXES = {
    "amount": 0, "debit_credit": 1, "currency": 2,
    "exchange_rate": 3, "base_amount": 4, "account": 6,
    "contra_account": 7, "bu_key": 8, "recognized_date": 9,
    "document_field_1": 10, "kost1": 36, "kost2": 37,
    "service_date": 114, "tax_period_date": 115,
}

# Felder, die DATEV beim Import nachweislich (Konto) oder vorsorglich aus der
# Vorzeile übernimmt, wenn sie leer sind. Spaltenindex 0-basiert.
# Nach dem DATEV-Test (SKILL v1.4, Testplan) auf die tatsächlich geschleppten
# Felder reduzieren.
CARRY_FIELDS = {
    "account": 6, "contra_account": 7, "bu_key": 8,
    "recognized_date": 9, "document_field_1": 10,
}
CARRY_FIELD_LABELS = {
    "account": "Konto", "contra_account": "Gegenkonto", "bu_key": "BU-Schlüssel",
    "recognized_date": "Belegdatum", "document_field_1": "Belegfeld 1",
}
STANDARD_BATCH_TYPE = "standard"
DATEV_IMPORT_ORDER = [
    "EXTF_Debitoren_Kreditoren.csv (falls vorhanden)",
    "reguläre Belegtransfer_*.zip",
    "Belegtransfer_Avise_*.zip in DUO",
    "EXTF_Buchungsstapel_<JJJJ-MM>.csv je Periode, danach konfigurierte Stapeltypen derselben Periode (z. B. _Eigenbelege)",
    "EXTF_Klaerungsposten_<JJJJ-MM>.csv (und ggf. _02 usw.) als eigener Importvorgang",
]
CARRY_RESULTS = {"carried", "not_carried", "not_tested"}

# Lesbare Bezeichnungen der Buchungsfelder für Prüfungsdatei und Klärungsfälle.
FIELD_LABELS = {
    "amount": "Betrag", "debit_credit": "Soll/Haben", "currency": "Währung",
    "exchange_rate": "Kurs", "base_amount": "Betrag in Euro", "account": "Sachkonto",
    "contra_account": "Gegenkonto", "bu_key": "Steuerschlüssel",
    "recognized_date": "Belegdatum", "document_field_1": "Belegnummer",
    "kost1": "Kostenstelle", "kost2": "Kostenstelle 2",
    "service_date": "Leistungsdatum", "tax_period_date": "Steuerperiode",
}

# Technische Bezeichner, die in für Mitarbeiter sichtbaren Texten nichts verloren haben.
TECHNICAL_TOKEN_PATTERN = re.compile(
    r"(?<![\w/])(?:contra_account|account|open_fields|bu_key|document_field_1|kost1|kost2|"
    r"recognized_date|asset_account_field|traffic_light|booking_text|batch_type|"
    r"processing_status|transaction_id|source_id|BF1|BU-Key|Riecken|Rieken|Riken|"
    r"Connector|Konnektor|MCP|datev_[a-z_]+|JSON|null|None)(?![\w/])",
    re.IGNORECASE,
)

# Pauschale Begründungen, die nicht aus dem Beleg abgeleitet sind.
GENERIC_REASONS = {
    "kontierung prüfen", "kontierung offen", "kontierung unklar", "prüfung erforderlich",
    "fachliche prüfung erforderlich", "bitte prüfen", "prüfen", "unklar", "offen",
    "klärung erforderlich", "klärungsfall", "zu klären", "rot", "grün", "beleg prüfen",
    "offene fachliche entscheidung", "fachliche unsicherheit", "mitarbeiter prüfen",
    "manuell prüfen", "offene entscheidung", "klärungsbedarf",
}


def _normalized_phrase(text: str) -> str:
    return re.sub(r"[\s.:;!,–-]+$", "", clean_text(text).casefold())


def plain_language_issues(text: Any, label: str, *, min_length: int = 0,
                          reject_generic: bool = False) -> list[str]:
    """Texts for employees: no technical identifiers, no boilerplate, derived from the document."""
    issues: list[str] = []
    value = clean_text(text)
    if min_length and len(value) < min_length:
        issues.append(f"{label}: zu knapp ({len(value)} Zeichen); aus dem Beleg konkret begründen")
    tokens = sorted({match.group(0) for match in TECHNICAL_TOKEN_PATTERN.finditer(value)})
    if tokens:
        issues.append(f"{label}: technische Bezeichner sind unzulässig: " + ", ".join(tokens))
    if reject_generic and _normalized_phrase(value) in GENERIC_REASONS:
        issues.append(f"{label}: pauschale Begründung „{value}“; es muss aus dem Beleg hervorgehen, warum")
    return issues


def single_task_issues(text: Any, label: str = "Nächster Schritt") -> list[str]:
    """Exactly one task in one plain sentence for the employee."""
    issues: list[str] = []
    value = clean_text(text)
    if not value:
        return [f"{label}: fehlt; genau eine Aufgabe für den Mitarbeiter nennen"]
    if len(value) > 240:
        issues.append(f"{label}: länger als 240 Zeichen; auf eine Aufgabe kürzen")
    sentences = [part for part in re.split(r"(?<=[.!?])\s+", value) if part.strip()]
    if len(sentences) > 1 or " – " in value or ";" in value or re.search(r"\b\d\.\s", value):
        issues.append(f"{label}: enthält mehr als eine Aufgabe; genau einen Satz mit einer Aufgabe nennen")
    issues.extend(plain_language_issues(value, label))
    return issues
BATCH_KIND_BOOKING = "buchung"
BATCH_KIND_CLARIFICATION = "klaerung"
CLARIFICATION_LABEL = "Klärungsposten"
BOOKING_LABEL = "Buchungsstapel"


def _cell_text(value: Any) -> str:
    return "" if value is None else str(value)


def carry_empty_fields(row: list[Any]) -> frozenset[str]:
    """Names of the carry-endangered fields that are empty in this export row."""
    return frozenset(
        name for name, index in CARRY_FIELDS.items()
        if not _cell_text(row[index]).strip()
    )


def carry_sort_key(row: list[Any], transaction_id: str = "", line: int = 0) -> tuple:
    """Rows with more empty endangered fields first, then stable by transaction and line."""
    return (-len(carry_empty_fields(row)), str(transaction_id), int(line))


def carry_order_violations(rows: Iterable[list[Any]], first_row_number: int = 3) -> list[str]:
    """Report every endangered field that is empty behind a filled row.

    DATEV would fill such an empty field with the value of the preceding row.
    Row numbers are CSV line numbers (header = 1, field names = 2).
    """
    violations: list[str] = []
    last_filled: dict[str, int | None] = {name: None for name in CARRY_FIELDS}
    for offset, row in enumerate(rows):
        number = first_row_number + offset
        for name, index in CARRY_FIELDS.items():
            if _cell_text(row[index]).strip():
                last_filled[name] = number
            elif last_filled[name] is not None:
                violations.append(
                    f"{CARRY_FIELD_LABELS[name]}: Zeile {number} ist leer hinter "
                    f"gefüllter Zeile {last_filled[name]}"
                )
    return violations


def batch_type_suffix(batch_type: str) -> str:
    """File name suffix of a configured separate batch type (``eigenbelege`` → ``Eigenbelege``)."""
    text = clean_text(batch_type)
    if text == STANDARD_BATCH_TYPE or not text:
        return ""
    return text[:1].upper() + text[1:]


def batch_file_name(period: str, kind: str, batch_type: str = STANDARD_BATCH_TYPE,
                    part: int = 1) -> str:
    if kind == BATCH_KIND_CLARIFICATION:
        stem = f"EXTF_Klaerungsposten_{period}"
    elif kind == BATCH_KIND_BOOKING:
        stem = f"EXTF_Buchungsstapel_{period}"
    else:
        raise ValueError(f"Unbekannte Stapelart: {kind}")
    suffix = batch_type_suffix(batch_type)
    if suffix:
        stem = f"{stem}_{suffix}"
    if part > 1:
        if kind != BATCH_KIND_CLARIFICATION:
            raise ValueError("Nur der Klärungsstapel darf geteilt werden.")
        stem = f"{stem}_{part:02d}"
    return f"{stem}.csv"


def batch_label(kind: str, batch_type: str, run: dict[str, Any] | None = None) -> str:
    configured = ""
    if batch_type != STANDARD_BATCH_TYPE:
        separate = ((run or {}).get("batch_config") or {}).get("separate_batches") or {}
        configured = clean_text((separate.get(batch_type) or {}).get("label", ""))
        if not configured:
            raise ValueError(f"Stapeltyp {batch_type} ist nicht in batch_config konfiguriert.")
    if kind == BATCH_KIND_CLARIFICATION:
        return clean_text(f"{CLARIFICATION_LABEL} {configured}".strip(), 30)
    return clean_text(configured or BOOKING_LABEL, 30)


BATCH_FILE_PATTERN = re.compile(
    r"^EXTF_(Buchungsstapel|Klaerungsposten)_(\d{4}-\d{2})(?:_([A-Z][a-z0-9]*))?(?:_(\d{2}))?\.csv$"
)


def parse_batch_file_name(name: str) -> dict[str, Any] | None:
    """Split a Kategorie-21 file name into kind, period, batch type suffix and part."""
    match = BATCH_FILE_PATTERN.fullmatch(name)
    if not match:
        return None
    kind = BATCH_KIND_BOOKING if match.group(1) == "Buchungsstapel" else BATCH_KIND_CLARIFICATION
    suffix = match.group(3) or ""
    part = int(match.group(4)) if match.group(4) else 1
    return {
        "kind": kind, "period": match.group(2), "suffix": suffix,
        "batch_type": (suffix[:1].lower() + suffix[1:]) if suffix else STANDARD_BATCH_TYPE,
        "part": part,
    }


def accrual_document(release: dict[str, Any], run: dict[str, Any], number: int) -> dict[str, Any]:
    period = release["period"]
    year, month = (int(value) for value in period.split("-"))
    return {
        "transaction_id": f"ABGRENZUNG-{release['accrual_id']}-{number}",
        "period": period, "traffic_light": "Grün",
        "processing_status": "Buchungszeile erzeugt",
        "recognized_date": release.get("booking_date") or f"{period}-{calendar.monthrange(year, month)[1]:02d}",
        "invoice_number": release["document_field_1"],
        "currency": release.get("currency", run.get("waehrung", "EUR")),
        "reason": "Fällige Abgrenzungsauflösung", "bookings": [release],
    }


def validate_open_fields(document: dict[str, Any], booking: dict[str, Any],
                         run: dict[str, Any] | None = None) -> dict[str, str]:
    """Only documented, genuinely absent fields may remain open in red rows."""
    light = document.get("traffic_light")
    if light not in {"Grün", "Rot"}:
        raise ValueError("Ampel muss Grün oder Rot sein; Gelb ist nicht zulässig.")
    opened = booking.get("open_fields", {})
    if not isinstance(opened, dict):
        raise ValueError("open_fields muss ein Objekt aus Feld und Begründung sein.")
    if opened and light != "Rot":
        raise ValueError("Offene Buchungsfelder erfordern Rot.")
    cost_config = (run or {}).get("cost_center_config")
    for field, reason in opened.items():
        if field not in OPEN_FIELD_INDEXES or not clean_text(reason):
            raise ValueError(f"Ungültiges offenes Feld oder fehlende Begründung: {field}")
        if field in {"kost1", "kost2"} and not isinstance(cost_config, dict):
            raise ValueError(f"Offenes Feld {field} ohne cost_center_config ist unzulässig.")
        value = document.get(field) if field in {"currency", "recognized_date"} else booking.get(field)
        if field == "document_field_1":
            value = value or document.get("invoice_number")
        if value not in (None, ""):
            raise ValueError(f"Bekannter Wert darf nicht als offen deklariert werden: {field}")
    configured = (run or {}).get("account_config", {})
    assets = {clean_text(value) for value in configured.get("asset_accounts", [])}
    forbidden = assets | {"1590", clean_text(configured.get("clarification"))}
    for field in ("account", "contra_account"):
        account = clean_text(booking.get(field))
        if account and account in forbidden:
            raise ValueError(f"Direkte Anlagen- oder Ersatzbuchung auf Klärungskonto unzulässig: {account}")
    if document.get("asset_booking") is True:
        side = booking.get("asset_account_field")
        if light != "Rot" or side not in {"account", "contra_account"} or side not in opened:
            raise ValueError("Anlagenzugang erfordert Rot und ein dokumentiertes leeres Anlagenkontofeld (asset_account_field).")
    return opened


def cost_center_values(
    document: dict[str, Any],
    booking: dict[str, Any],
    run: dict[str, Any] | None,
    opened: dict[str, str],
) -> tuple[str | None, str | None]:
    """KOST1/KOST2 for EXTF fields 37/38 according to the client's cost center profile."""
    run = run or {}
    config = run.get("cost_center_config")
    required = run.get("kostenstellenpflicht") is True
    tid = document.get("transaction_id", "")
    kost1 = clean_text(booking.get("kost1", ""), 36)
    kost2 = clean_text(booking.get("kost2", ""), 36)
    if not isinstance(config, dict):
        if kost1 or kost2:
            raise ValueError(f"{tid}: Kostenstellen ohne cost_center_config sind unzulässig.")
        if required:
            raise ValueError("Abbruch: unkonfigurierte Pflichtkostenstelle; cost_center_config fehlt.")
        return None, None
    allowed1 = {clean_text(key) for key in (config.get("kost1_allowed") or {})}
    allowed2 = {clean_text(key) for key in (config.get("kost2_allowed") or {})}
    kost2_required = config.get("kost2_required") is True
    if kost1 and kost1 not in allowed1:
        raise ValueError(f"{tid}: Kostenstelle {kost1} ist nicht in kost1_allowed konfiguriert.")
    if kost2 and kost2 not in allowed2:
        raise ValueError(f"{tid}: Kostenstelle {kost2} ist nicht in kost2_allowed konfiguriert.")
    if required and not kost1 and "kost1" not in opened:
        raise ValueError(f"{tid}: kost1 fehlt ohne dokumentierte Unsicherheit.")
    if required and kost2_required and not kost2 and "kost2" not in opened:
        raise ValueError(f"{tid}: kost2 fehlt ohne dokumentierte Unsicherheit.")
    return (kost1 or None), (kost2 or None)


def booking_row(
    document: dict[str, Any],
    booking: dict[str, Any],
    run: dict[str, Any] | None = None,
) -> list[Any]:
    row: list[Any] = [None] * 125
    opened = validate_open_fields(document, booking, run)

    def supplied(field: str, value: Any, formatter):
        if value in (None, ""):
            if field in opened:
                return None
            raise ValueError(f"{document['transaction_id']}: {field} fehlt ohne dokumentierte Unsicherheit.")
        return formatter(value)

    if booking.get("debit_credit") not in {"S", "H"} and "debit_credit" not in opened:
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
    )
    if not doc_field and "document_field_1" not in opened:
        raise ValueError(f"Belegfeld 1 fehlt: {document['transaction_id']}")
    row[0] = supplied("amount", booking.get("amount"), decimal_raw)
    row[1] = booking.get("debit_credit") or None
    currency = clean_text(document.get("currency")).upper()
    base_currency = clean_text(
        (run or {}).get("waehrung", document.get("base_currency", currency))
    ).upper()
    if not re.fullmatch(r"[A-Z]{3}", currency) and "currency" not in opened:
        raise ValueError(f"Ungültiges Währungskennzeichen: {currency}")
    if not re.fullmatch(r"[A-Z]{3}", base_currency):
        raise ValueError(f"Ungültige Basiswährung: {base_currency}")
    row[2] = currency
    if currency and currency != base_currency:
        missing_currency_fields = [
            key for key in ("exchange_rate", "base_amount")
            if booking.get(key) in (None, "") and key not in opened
        ]
        if missing_currency_fields:
            raise ValueError(
                f"Fremdwährungsbuchung {document['transaction_id']} ohne "
                f"{', '.join(missing_currency_fields)}"
            )
        row[3] = supplied("exchange_rate", booking.get("exchange_rate"), exchange_rate_raw)
        row[4] = supplied("base_amount", booking.get("base_amount"), decimal_raw)
        row[5] = base_currency
    row[6] = supplied("account", booking.get("account"), lambda value: digits_raw(value, "Konto"))
    row[7] = supplied("contra_account", booking.get("contra_account"), lambda value: digits_raw(value, "Gegenkonto"))
    row[8] = extf_bu_key
    recognized_date = supplied("recognized_date", document.get("recognized_date"), ddmm_raw)
    # Pflichtleerung: jede Zeile des Klärungsstapels wird ohne Belegdatum
    # exportiert, damit DATEV sie zwingend als fehlerhaft kennzeichnet. Das
    # sicher erkannte Datum bleibt im Lauf-JSON, Manifest und in der Prüfungsdatei.
    row[9] = None if document.get("traffic_light") == "Rot" else recognized_date
    row[10] = doc_field
    row[36], row[37] = cost_center_values(document, booking, run, opened)
    text = clean_text(booking.get("booking_text", ""), 60)
    warning_pattern = re.compile(
        r"\b(?:ACHTUNG|PRÜFUNG\s+ERFORDERLICH|"
        r"PRUEFUNG\s+ERFORDERLICH|PRÜFEN|PRUEFEN|VORSCHLAG|"
        r"ANLAGENVORERFASSUNG|KONTIERUNGSVORSCHLAG|"
        r"BITTE|KLÄREN|KLAEREN|NUTZUNGSDAUER)\b",
        re.IGNORECASE,
    )
    if warning_pattern.search(text):
        raise ValueError("Arbeitsanweisung oder Kontierungsvorschlag im Buchungstext; ausschließlich in der Prüfungsdatei dokumentieren.")
    if not text:
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
    if bool(service_date) != bool(tax_period_date) and not (
        "service_date" in opened or "tax_period_date" in opened
    ):
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
