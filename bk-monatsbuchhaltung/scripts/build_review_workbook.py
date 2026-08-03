from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation


NAVY = "183B56"
BLUE = "2F75B5"
PALE_BLUE = "D9EAF7"
GREEN = "C6E0B4"
YELLOW = "FFE699"
RED = "F4CCCC"
LIGHT = "F5F7FA"
WHITE = "FFFFFF"
THIN = Side(style="thin", color="D6DEE5")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--qa-dir", type=Path)
    return parser.parse_args()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def amount(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = re.sub(r"\s+", "", str(value))
    if not text:
        return None
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def document_field_1(doc: dict[str, Any]) -> str:
    for line in doc.get("bookings", []):
        if clean(line.get("document_field_1")):
            return clean(line["document_field_1"])
    return clean(doc.get("invoice_number")) or f"ERSATZ-{doc.get('transaction_id', '')}"


BATCH_FILE_STEMS = {
    "Grün": "Buchungsstapel",
    "Gelb": "Klaerungsposten_1",
    "Rot": "Klaerungsposten_2",
}


def booking_batch_filename(
    doc: dict[str, Any], run: dict[str, Any]
) -> str:
    if doc.get("processing_status") != "Buchungszeile erzeugt":
        return "Kein Buchungsstapel"
    light = clean(doc.get("traffic_light"))
    stem = BATCH_FILE_STEMS.get(light)
    period = clean(doc.get("period")) or clean(run.get("buchungsmonat"))
    if not stem or not period:
        return "Nicht bestimmbar"
    return f"EXTF_{stem}_{period}.csv"


def compact_posting(doc: dict[str, Any]) -> str:
    if doc.get("processing_status") != "Buchungszeile erzeugt":
        return clean(doc.get("processing_status")) or "Keine Buchungszeile"
    rows: list[str] = []
    for line in doc.get("bookings", []):
        value = amount(line.get("amount"))
        value_text = (
            f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            if value is not None else clean(line.get("amount"))
        )
        account = " ".join(filter(None, [
            clean(line.get("account")), clean(line.get("account_name"))
        ]))
        contra = " ".join(filter(None, [
            clean(line.get("contra_account")), clean(line.get("contra_account_name"))
        ]))
        rows.append(
            f"{value_text} {doc.get('currency', 'EUR')} {line.get('debit_credit', '')}"
            f" | {account} an {contra} | BU {line.get('bu_key') or '–'}"
            f" | BF1 {line.get('document_field_1') or document_field_1(doc)}"
        )
    return "\n".join(rows)


def apply_header(ws, row: int, start: int, end: int) -> None:
    for cell in ws.iter_cols(min_col=start, max_col=end, min_row=row, max_row=row):
        item = cell[0]
        item.fill = PatternFill("solid", fgColor=BLUE)
        item.font = Font(color=WHITE, bold=True)
        item.alignment = Alignment(vertical="center", wrap_text=True)
        item.border = Border(bottom=THIN)


def set_widths(ws, widths: list[float]) -> None:
    for index, width in enumerate(widths, start=1):
        ws.column_dimensions[ws.cell(1, index).column_letter].width = width


def traffic_format(ws, end_row: int) -> None:
    if end_row < 2:
        return
    for value, color in (("Grün", GREEN), ("Gelb", YELLOW), ("Rot", RED)):
        ws.conditional_formatting.add(
            f"A2:A{end_row}",
            FormulaRule(
                formula=[f'$A2="{value}"'],
                fill=PatternFill("solid", fgColor=color),
                font=Font(bold=True),
            ),
        )


def add_title(ws, title: str, end_column: int) -> None:
    ws.insert_rows(1, 2)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=end_column)
    cell = ws.cell(1, 1, title)
    cell.fill = PatternFill("solid", fgColor=NAVY)
    cell.font = Font(color=WHITE, bold=True, size=16)
    cell.alignment = Alignment(vertical="center")
    ws.row_dimensions[1].height = 30
    ws.sheet_view.showGridLines = False


def build(data: dict[str, Any], output: Path) -> None:
    run = data["run"]
    order = {"Rot": 0, "Gelb": 1, "Grün": 2, None: 9, "": 9}
    docs = sorted(
        data.get("documents", []),
        key=lambda doc: (
            order.get(doc.get("traffic_light"), 9),
            str(doc.get("period", "")),
            str(doc.get("recognized_date", "")),
            str(doc.get("transaction_id", "")),
        ),
    )
    cases: dict[str, dict[str, Any]] = {}
    for case in data.get("clarification_cases", []):
        for transaction_id in case.get("transaction_ids", []):
            cases.setdefault(str(transaction_id), case)

    wb = Workbook()
    wb.remove(wb.active)
    guide = wb.create_sheet("Anleitung")
    summary = wb.create_sheet("Übersicht")
    review = wb.create_sheet("Belegprüfung")
    bookings = wb.create_sheet("Buchungszeilen")
    notes = wb.create_sheet("Mandanten-Hinweise")
    masters = wb.create_sheet("Stammdatenänderungen")

    guide_rows = [
        ["Schritt / Feld", "Bedeutung"],
        ["1. Belegprüfung", "Zuerst Rot, dann Gelb bearbeiten. Direkt rechts neben der Ampel steht der vollständige DATEV-Buchungsstapel. Grün ist bereits plausibel kontiert."],
        ["2. Buchungszeilen", "Direkt rechts neben der Ampel steht der DATEV-Buchungsstapel; danach Konten, BU-Schlüssel, Belegfeld 1, Buchungstext und Periode nachvollziehen."],
        ["3. Rücklaufstatus", "Für jeden roten und gelben Vorgang einen Abschlussstatus wählen: unverändert übernommen, geändert oder nicht übernommen. Offen ist kein Abschlussstatus."],
        ["4. Mitarbeiter-Ergebnis", "Bei geändert oder nicht übernommen ist die endgültige Behandlung als Mitarbeiter-Ergebnis Pflicht."],
        ["Grün", "Vollständig und plausibel; keine offene fachliche Frage."],
        ["Gelb", "Importierbar; eine fachliche Kontrolle bleibt offen."],
        ["Rot", "Aktive DATEV-Bearbeitung; das Belegdatum ist im Klärungsposten bewusst leer."],
        ["Zahlungsavise", "Nicht buchen. Das gesonderte Belegtransfer_Avise-ZIP in DATEV Unternehmen online hochladen."],
        ["DATEV-Import", "1. Stammdaten, 2. reguläre Belegtransfer-ZIPs, 3. Avis-ZIPs, 4. Buchungs- und Abgrenzungsstapel."],
    ]
    for row in guide_rows:
        guide.append(row)
    apply_header(guide, 1, 1, 2)
    for row in range(2, guide.max_row + 1):
        guide.cell(row, 1).font = Font(bold=True)
        guide.cell(row, 2).alignment = Alignment(wrap_text=True, vertical="top")
        guide.row_dimensions[row].height = 34
    for row, color in ((6, GREEN), (7, YELLOW), (8, RED)):
        guide.cell(row, 1).fill = PatternFill("solid", fgColor=color)
    set_widths(guide, [25, 90])
    guide.freeze_panes = "A2"
    add_title(guide, f"Buchungsprüfung {run['mandantennummer']} – {run['buchungsmonat']}", 8)

    summary.append(["Kennzahl", "Gesamt", "Grün", "Gelb", "Rot"])
    summary.append(["Belege", len(docs)] + [
        sum(1 for doc in docs if doc.get("traffic_light") == value)
        for value in ("Grün", "Gelb", "Rot")
    ])
    summary.append(["Belegsumme", sum(amount(doc.get("total_amount")) or 0 for doc in docs)] + [
        sum((amount(doc.get("total_amount")) or 0) for doc in docs if doc.get("traffic_light") == value)
        for value in ("Grün", "Gelb", "Rot")
    ])
    summary.append(["Buchungszeilen", sum(len(doc.get("bookings", [])) for doc in docs)] + [
        sum(len(doc.get("bookings", [])) for doc in docs if doc.get("traffic_light") == value)
        for value in ("Grün", "Gelb", "Rot")
    ])
    summary.append([])
    summary.append(["Kontrollpunkt", "Ergebnis"])
    controls = [
        ("Vorperiodenbelege", sum(1 for doc in docs if str(doc.get("period", "")) < run["buchungsmonat"])),
        ("Zukunftsbelege", sum(1 for doc in docs if str(doc.get("period", "")) > run["buchungsmonat"])),
        ("Sichere Dubletten", sum(1 for doc in docs if doc.get("processing_status") == "sichere Dublette – nicht erneut gebucht")),
        ("Zahlungsavise", sum(1 for doc in docs if doc.get("payment_advice"))),
        ("Nicht buchungsrelevant", sum(1 for doc in docs if doc.get("processing_status") == "nicht buchungsrelevant")),
        ("Offene Klärfälle", len(data.get("clarification_cases", []))),
        ("Neue/geänderte Stammdaten", len(data.get("master_records", []))),
        ("Mandanten-Hinweise", len(data.get("client_notes", []))),
        ("Vollständigkeitskontrolle", "VOLLSTÄNDIG"),
    ]
    for item in controls:
        summary.append(list(item))
    apply_header(summary, 1, 1, 5)
    apply_header(summary, 6, 1, 2)
    for row in range(2, 5):
        for col in range(2, 6):
            summary.cell(row, col).number_format = '#,##0.00' if row == 3 else '#,##0'
    set_widths(summary, [34, 20, 16, 16, 16])
    summary.freeze_panes = "A2"
    add_title(summary, f"Übersicht {run['mandantennummer']} – {run['buchungsmonat']}", 5)

    review_headers = [
        "Ampel-Einstufung", "Buchungsstapel", "Vorgangs-ID", "Belegdatum", "Geschäftspartner",
        "Belegfeld 1", "Betrag", "Währung", "Buchungsperiode", "Kontierung",
        "Ableitung", "Prüfergebnis / Ampelbegrgründung".replace("begrgründung", "begründung"),
        "Offener Punkt / nächster Schritt", "Bearbeitungsstatus", "Mitarbeiter-Ergebnis",
    ]
    review.append(review_headers)
    for doc in docs:
        case = cases.get(str(doc.get("transaction_id", "")), {})
        next_step = " – ".join(dict.fromkeys(filter(None, [
            clean(case.get("recommendation")), clean(case.get("decision_needed"))
        ])))
        if not next_step:
            if doc.get("payment_advice"):
                next_step = "Gesondertes Avis-ZIP in DATEV Unternehmen online hochladen."
            elif doc.get("processing_status") == "sichere Dublette – nicht erneut gebucht":
                next_step = "Keine erneute Buchung."
            elif doc.get("processing_status") == "nicht buchungsrelevant":
                next_step = "Keine Buchung."
            elif doc.get("traffic_light") == "Grün":
                next_step = "Keine weitere Bearbeitung."
        review.append([
            doc.get("traffic_light") or "",
            booking_batch_filename(doc, run),
            doc.get("transaction_id") or "",
            datetime.strptime(doc["recognized_date"], "%Y-%m-%d") if doc.get("recognized_date") else None,
            doc.get("partner") or "",
            document_field_1(doc),
            amount(doc.get("total_amount")),
            doc.get("currency") or "",
            doc.get("period") or "",
            compact_posting(doc),
            clean(doc.get("derivation")),
            re.sub(r"^(Grün|Gelb|Rot)\s*:\s*", "", clean(doc.get("reason")), flags=re.I),
            next_step,
            "offen" if doc.get("traffic_light") in {"Gelb", "Rot"} else "",
            "",
        ])
    apply_header(review, 1, 1, 15)
    review.freeze_panes = "C2"
    review.auto_filter.ref = review.dimensions
    set_widths(review, [18, 38, 14, 14, 27, 22, 14, 10, 16, 58, 52, 48, 48, 27, 48])
    for row in range(2, review.max_row + 1):
        review.cell(row, 4).number_format = "dd.mm.yyyy"
        review.cell(row, 7).number_format = '#,##0.00'
        for col in range(10, 16):
            review.cell(row, col).alignment = Alignment(wrap_text=True, vertical="top")
        review.row_dimensions[row].height = 52
    traffic_format(review, review.max_row)
    status_validation = DataValidation(
        type="list",
        formula1='"offen,unverändert übernommen,geändert,nicht übernommen"',
    )
    review.add_data_validation(status_validation)
    status_validation.add(f"N2:N{max(2, review.max_row)}")
    review.conditional_formatting.add(
        f"O2:O{max(2, review.max_row)}",
        FormulaRule(
            formula=['AND(OR($N2="geändert",$N2="nicht übernommen"),$O2="")'],
            fill=PatternFill("solid", fgColor=RED),
            font=Font(color="9C0006", bold=True),
        ),
    )

    booking_headers = [
        "Ampel-Einstufung", "Buchungsstapel", "Vorgangs-ID", "Betrag", "Soll/Haben", "Konto",
        "Kontobezeichnung", "Gegenkonto", "Gegenkontobezeichnung",
        "BU-Schlüssel", "Erkanntes Belegdatum", "Belegfeld 1",
        "Buchungstext", "Buchungsperiode",
    ]
    bookings.append(booking_headers)
    for doc in docs:
        for line in doc.get("bookings", []):
            bookings.append([
                doc.get("traffic_light") or "", booking_batch_filename(doc, run),
                doc.get("transaction_id") or "", amount(line.get("amount")), line.get("debit_credit") or "",
                str(line.get("account") or ""), line.get("account_name") or "",
                str(line.get("contra_account") or ""), line.get("contra_account_name") or "",
                line.get("bu_key") or "",
                datetime.strptime(doc["recognized_date"], "%Y-%m-%d") if doc.get("recognized_date") else None,
                line.get("document_field_1") or document_field_1(doc),
                line.get("booking_text") or "", doc.get("period") or "",
            ])
    apply_header(bookings, 1, 1, 14)
    bookings.freeze_panes = "C2"
    bookings.auto_filter.ref = bookings.dimensions
    set_widths(bookings, [18, 38, 14, 14, 12, 12, 26, 14, 28, 13, 19, 23, 42, 16])
    for row in range(2, bookings.max_row + 1):
        bookings.cell(row, 4).number_format = '#,##0.00'
        bookings.cell(row, 11).number_format = "dd.mm.yyyy"
        bookings.cell(row, 13).alignment = Alignment(wrap_text=True)
    traffic_format(bookings, bookings.max_row)

    notes.append(["Vorgangs-ID", "Geschäftspartner", "Hinweis", "Empfohlenes Vorgehen"])
    for item in data.get("client_notes", []):
        notes.append([
            item.get("transaction_id") or "", item.get("partner") or "",
            item.get("note") or "", item.get("suggested_action") or "",
        ])
    apply_header(notes, 1, 1, 4)
    notes.freeze_panes = "A2"
    notes.auto_filter.ref = notes.dimensions
    set_widths(notes, [14, 28, 58, 58])
    for row in range(2, notes.max_row + 1):
        notes.cell(row, 3).alignment = Alignment(wrap_text=True)
        notes.cell(row, 4).alignment = Alignment(wrap_text=True)

    masters.append([
        "Aktion", "Konto", "Typ", "Name", "USt-ID", "Bankverbindungen",
        "Vollständiger Datensatz", "Hinweis",
    ])
    for record in data.get("master_records", []):
        banks = "; ".join(filter(None, [
            " / ".join(filter(None, [clean(bank.get("iban")), clean(bank.get("bic")), clean(bank.get("bank_name"))]))
            for bank in record.get("banks", [])
        ]))
        complete = record.get("action") == "Neuanlage" or record.get("full_current_record_available") is True
        masters.append([
            record.get("action") or "", str(record.get("account") or ""),
            record.get("account_type") or "", record.get("name") or "",
            record.get("vat_id") or "", banks, "JA" if complete else "NEIN",
            "" if complete else "Vollständigen aktuellen Datensatz manuell pflegen.",
        ])
    apply_header(masters, 1, 1, 8)
    masters.freeze_panes = "A2"
    masters.auto_filter.ref = masters.dimensions
    set_widths(masters, [16, 14, 14, 34, 20, 60, 22, 50])
    for row in range(2, masters.max_row + 1):
        masters.cell(row, 6).alignment = Alignment(wrap_text=True)
        masters.cell(row, 8).alignment = Alignment(wrap_text=True)

    output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output)


def main() -> int:
    args = parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    build(data, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
