#!/usr/bin/env python3
"""Klärungsquote und Zweitprüfung (VALIDIERUNG.md, Abschnitt "Klärungsquote und Zweitprüfung").

Berechnet aus dem Lauf-JSON (oder dem normalisierten Datenmodell des Generators)
die Kennzahlen N, R und Q, prüft die Schwellenstufen, die verpflichtende
Zweitprüfung und die Vorher-/Nachher-Konsistenz und erzeugt den
Klärungsquoten-Nachweis. Der Check läuft vor dem Paketbau (Generator) und erneut
vor der Abschlussmeldung (Validator).

Aufruf durch den Agenten vor dem Paketbau:

    python scripts/clarification_rate.py --input <lauf.json> [--markdown <datei.md>]

Exit-Code 2, wenn der Nachweis fachlich oder technisch nicht vollständig ist.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from datev_io import (  # noqa: E402
    RED_REASON_CODES,
    STATUS_BOOKED,
    STATUS_NOT_RELEVANT,
    STATUS_OUT_OF_SCOPE,
    STATUS_SECURE_DUPLICATE,
    STATUS_UNREADABLE,
)


THRESHOLD_NORMAL = 10.0
THRESHOLD_SECOND_REVIEW = 20.0
STAGE_LABELS = {
    "nicht_berechenbar": "nicht berechenbar (N = 0)",
    "normal": "Q ≤ 10 %: normale Vollständigkeitskontrolle",
    "ursachenpruefung": "10 % < Q ≤ 20 %: dokumentierte Plausibilitäts- und Ursachenprüfung",
    "zweitpruefung": "Q > 20 %: verpflichtende vollständige Zweitprüfung aller roten Vorgänge",
}
REVIEW_BASIS = {"belegbild", "mandantenprofil", "datev_bestand", "buchungsregeln"}
CORRECTION_TARGETS = {"Grün", "Rot", "ausgeschlossen"}
SYSTEMATIC_SHARE = 0.5
SYSTEMATIC_MIN_CASES = 5


def _documents(data: dict[str, Any]) -> list[dict[str, Any]]:
    documents = data.get("documents")
    if isinstance(documents, list) and documents:
        return documents
    transactions = data.get("transactions")
    return transactions if isinstance(transactions, list) else []


def quota(red: int, total: int) -> float | None:
    if total <= 0:
        return None
    return round(100.0 * red / total, 1)


def stage_for(value: float | None) -> str:
    if value is None:
        return "nicht_berechenbar"
    if value <= THRESHOLD_NORMAL:
        return "normal"
    if value <= THRESHOLD_SECOND_REVIEW:
        return "ursachenpruefung"
    return "zweitpruefung"


def _document_reference(doc: dict[str, Any]) -> str:
    for key in ("invoice_number",):
        if doc.get(key):
            return str(doc[key])
    for booking in doc.get("bookings", []) or []:
        if booking.get("document_field_1"):
            return str(booking["document_field_1"])
    return ""


def compute_clarification_rate(data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Return (summary, errors). The summary is written into manifest, report and Nachweis."""
    errors: list[str] = []
    documents = _documents(data)
    by_id = {str(doc.get("transaction_id", "")): doc for doc in documents}
    booked = [doc for doc in documents if doc.get("processing_status") == STATUS_BOOKED]
    green = [doc for doc in booked if doc.get("traffic_light") == "Grün"]
    red = [doc for doc in booked if doc.get("traffic_light") == "Rot"]
    n_after = len(booked)
    r_after = len(red)

    counts = {
        "gruene_vorgaenge": len(green),
        "rote_vorgaenge": r_after,
        "rote_buchungszeilen": sum(len(doc.get("bookings", []) or []) for doc in red),
        "technisch_nicht_auswertbar": sum(
            1 for doc in documents if doc.get("processing_status") == STATUS_UNREADABLE
        ),
        "sichere_dubletten": sum(
            1 for doc in documents if doc.get("processing_status") == STATUS_SECURE_DUPLICATE
        ),
        "bereits_in_datev_vorhanden": sum(
            1 for doc in documents
            if doc.get("processing_status") == STATUS_SECURE_DUPLICATE
            and (
                ((doc.get("duplicate_checks") or {}).get("datev_live") or {}).get("result") == "secure_duplicate"
                or (doc.get("prior_booking_check") or {}).get("result") == "sichere_dublette"
            )
        ),
        "aussteuerungen": sum(
            1 for doc in documents
            if doc.get("processing_status") == STATUS_NOT_RELEVANT
            and (
                (doc.get("entity_assessment") or {}).get("relevance") in {"foreign_entity", "personal"}
                or doc.get("handoff_required") is True
            )
        ),
        "nicht_buchungsrelevant": sum(
            1 for doc in documents if doc.get("processing_status") == STATUS_NOT_RELEVANT
        ),
        "ausserhalb_auftragszeitraum": sum(
            1 for doc in documents if doc.get("processing_status") == STATUS_OUT_OF_SCOPE
        ),
        "zahlungsavise": sum(1 for doc in documents if doc.get("payment_advice") is True),
    }

    reason_rows: list[dict[str, Any]] = []
    reason_counter: Counter[str] = Counter()
    for doc in red:
        tid = str(doc.get("transaction_id", ""))
        reason = doc.get("red_reason")
        if not isinstance(reason, dict) or reason.get("code") not in RED_REASON_CODES:
            errors.append(f"{tid}: Rot ohne maschinenlesbaren Rot-Grund (red_reason.code)")
            code = "ohne_grund"
        else:
            code = str(reason["code"])
            if not str(reason.get("verification_attempted", "")).strip():
                errors.append(f"{tid}: red_reason.verification_attempted fehlt (durchgeführter Prüfversuch)")
            if not str(reason.get("next_check", "")).strip():
                errors.append(f"{tid}: red_reason.next_check fehlt (nächstmöglicher Prüfschritt)")
        reason_counter[code] += 1
        open_fields = sorted({
            str(field)
            for booking in doc.get("bookings", []) or []
            for field in (booking.get("open_fields") or {})
        })
        reason_rows.append({
            "transaction_id": tid,
            "code": code,
            "label": RED_REASON_CODES.get(code, "ohne Rot-Grund"),
            "open_fields": open_fields,
            "document_reference": _document_reference(doc),
            "partner": str(doc.get("partner") or ""),
            "verification_attempted": str((reason or {}).get("verification_attempted", "")) if isinstance(reason, dict) else "",
            "next_check": str((reason or {}).get("next_check", "")) if isinstance(reason, dict) else "",
        })

    review = data.get("clarification_review")
    if review is None:
        review = {}
    if not isinstance(review, dict):
        errors.append("clarification_review muss ein Objekt sein")
        review = {}
    second = review.get("second_review") or {}
    if not isinstance(second, dict):
        errors.append("clarification_review.second_review muss ein Objekt sein")
        second = {}
    corrections = second.get("corrections") or []
    if not isinstance(corrections, list):
        errors.append("second_review.corrections muss eine Liste sein")
        corrections = []
    corrected_to_green: list[str] = []
    corrected_to_red: list[str] = []
    corrected_out: list[str] = []
    for index, item in enumerate(corrections, start=1):
        if not isinstance(item, dict):
            errors.append(f"second_review.corrections {index}: Eintrag ist kein Objekt")
            continue
        tid = str(item.get("transaction_id", ""))
        target = item.get("to")
        source = item.get("from")
        doc = by_id.get(tid)
        if doc is None:
            errors.append(f"second_review.corrections {index}: unbekannte Vorgangs-ID {tid}")
            continue
        if target not in CORRECTION_TARGETS or source not in {"Rot", "Grün"}:
            errors.append(f"{tid}: Korrektur muss from Rot/Grün und to Grün/Rot/ausgeschlossen nennen")
            continue
        if not str(item.get("reason", "")).strip():
            errors.append(f"{tid}: Korrektur ohne konkrete fachliche Begründung")
        if target == "Grün":
            if doc.get("processing_status") != STATUS_BOOKED or doc.get("traffic_light") != "Grün":
                errors.append(f"{tid}: als Grün korrigiert, aber nicht als grüner Vorgang gebucht")
            corrected_to_green.append(tid)
        elif target == "Rot":
            if doc.get("processing_status") != STATUS_BOOKED or doc.get("traffic_light") != "Rot":
                errors.append(f"{tid}: als Rot korrigiert, aber nicht als roter Vorgang gebucht")
            corrected_to_red.append(tid)
        else:
            if doc.get("processing_status") == STATUS_BOOKED:
                errors.append(f"{tid}: als ausgeschlossen korrigiert, aber weiterhin gebucht")
            corrected_out.append(tid)
    n_before = n_after + len(corrected_out)
    r_before = r_after + len(corrected_to_green) - len(corrected_to_red) + len(corrected_out)
    if r_before < 0 or r_before > n_before:
        errors.append("Vorher-Werte der Zweitprüfung sind nicht konsistent mit den Korrekturen")
        r_before = max(0, min(r_before, n_before))
    declared_before = second.get("before")
    if isinstance(declared_before, dict):
        for key, value in (("N", n_before), ("R", r_before)):
            if declared_before.get(key) is not None and int(declared_before[key]) != value:
                errors.append(
                    f"second_review.before.{key}={declared_before[key]} widerspricht den dokumentierten Korrekturen ({value})"
                )
    q_before = quota(r_before, n_before)
    q_after = quota(r_after, n_after)
    stage_before = stage_for(q_before)
    stage_after = stage_for(q_after)

    red_before_ids = sorted({str(doc.get("transaction_id", "")) for doc in red} | set(corrected_to_green) | set(corrected_out))
    performed = second.get("performed") is True
    reviewed = second.get("reviewed_transaction_ids") or []
    if not isinstance(reviewed, list):
        errors.append("second_review.reviewed_transaction_ids muss eine Liste sein")
        reviewed = []
    reviewed_set = {str(value) for value in reviewed}
    second_review_required = stage_before == "zweitpruefung"
    if second_review_required:
        if not performed:
            errors.append(
                f"Klärungsquote {q_before} % > 20 %: vollständige Zweitprüfung aller {r_before} roten Vorgänge ist Pflicht "
                "(clarification_review.second_review.performed=true); kein Abbruch, zusätzliche Arbeit"
            )
        missing = sorted(set(red_before_ids) - reviewed_set)
        if performed and missing:
            errors.append("Zweitprüfung unvollständig; nicht nachgeprüfte rote Vorgänge: " + ", ".join(missing))
    if performed:
        basis = second.get("basis") or []
        basis_set = {str(value).strip().lower() for value in basis} if isinstance(basis, list) else set()
        missing_basis = sorted(REVIEW_BASIS - basis_set)
        if missing_basis:
            errors.append("Zweitprüfung ohne vollständige Prüfgrundlage (" + ", ".join(missing_basis) + ")")
        if not str(second.get("performed_at", "")).strip():
            errors.append("second_review.performed_at fehlt")
    cause_analysis = review.get("cause_analysis") or {}
    if not isinstance(cause_analysis, dict):
        errors.append("clarification_review.cause_analysis muss ein Objekt je Rot-Kategorie sein")
        cause_analysis = {}
    cause_required = stage_before == "ursachenpruefung" or stage_after == "ursachenpruefung"
    if cause_required:
        for code in sorted(reason_counter):
            if not str(cause_analysis.get(code, "")).strip():
                errors.append(
                    f"10 % < Q ≤ 20 %: dokumentierte Plausibilitäts- und Ursachenprüfung für Rot-Kategorie {code} fehlt (cause_analysis)"
                )
    systematic: list[dict[str, Any]] = []
    if r_after >= SYSTEMATIC_MIN_CASES:
        for code, count in reason_counter.items():
            if count / r_after >= SYSTEMATIC_SHARE:
                note = str(cause_analysis.get(code, "")).strip()
                systematic.append({"code": code, "count": count, "share": round(100.0 * count / r_after, 1), "note": note})
                if not note:
                    errors.append(
                        f"Rot-Kategorie {code} tritt ungewöhnlich häufig auf ({count} von {r_after}); "
                        "Ursache und mögliche systematische Fehleinstufung in cause_analysis prüfen"
                    )

    checked_at = str(second.get("performed_at") or review.get("checked_at") or "").strip()
    summary = {
        "definition": "N = einmalig gezählte buchungsrelevante logische Geschäftsvorfälle; R = rote Vorgänge (Mehrfachzeilen einmal); Q = 100 × R / N",
        "before": {"N": n_before, "R": r_before, "Q": q_before, "stage": stage_before, "stage_label": STAGE_LABELS[stage_before]},
        "after": {"N": n_after, "R": r_after, "Q": q_after, "stage": stage_after, "stage_label": STAGE_LABELS[stage_after]},
        "second_review_required": second_review_required,
        "second_review_performed": performed,
        "reviewed_cases": len(reviewed_set & set(red_before_ids)),
        "reviewed_transaction_ids": sorted(reviewed_set & set(red_before_ids)),
        "corrected_to_green": sorted(corrected_to_green),
        "corrected_to_red": sorted(corrected_to_red),
        "corrected_excluded": sorted(corrected_out),
        "corrections": [item for item in corrections if isinstance(item, dict)],
        "remaining_red": r_after,
        "remaining_red_transaction_ids": sorted(str(doc.get("transaction_id", "")) for doc in red),
        "reason_distribution": {code: reason_counter[code] for code in sorted(reason_counter)},
        "reason_labels": dict(RED_REASON_CODES),
        "red_cases": reason_rows,
        "cause_analysis": {key: str(value) for key, value in cause_analysis.items()},
        "systematic_categories": systematic,
        "counts": counts,
        "checked_at": checked_at or datetime.now().replace(microsecond=0).isoformat(),
        "check_step": "vor Paketbau (Generator); erneut vor Abschlussmeldung (Validator)",
        "quota_is_target_value": False,
        "result": (
            "fachlich kontrolliert"
            if not errors and not (second_review_required and not performed)
            else "nicht fachlich kontrolliert"
        ),
        "professionally_open": r_after > 0,
        "errors": list(errors),
    }
    return summary, errors


def _pct(value: float | None) -> str:
    return "nicht berechenbar" if value is None else f"{value:.1f} %".replace(".", ",")


def render_markdown(summary: dict[str, Any]) -> str:
    before = summary["before"]
    after = summary["after"]
    counts = summary["counts"]
    lines = [
        "# Klärungsquoten-Nachweis",
        "",
        f"- Prüfdatum: {summary['checked_at']}",
        f"- Prüfschritt: {summary['check_step']}",
        f"- Zählweise: {summary['definition']}",
        "- Die Quote ist ein Qualitätsindikator und kein Zielwert; sie wird niemals durch geschätzte Beträge, Ersatzkonten oder unerlaubte Umstufung gesenkt.",
        "",
        "## Kennzahlen vor und nach Zweitprüfung",
        "",
        "| Kennzahl | vor Zweitprüfung | nach Zweitprüfung |",
        "|---|---:|---:|",
        f"| N (buchungsrelevante Vorgänge) | {before['N']} | {after['N']} |",
        f"| R (rote Vorgänge) | {before['R']} | {after['R']} |",
        f"| Q (Klärungsquote) | {_pct(before['Q'])} | {_pct(after['Q'])} |",
        f"| Grenzstufe | {before['stage_label']} | {after['stage_label']} |",
        "",
        f"- Zweitprüfung erforderlich: {'ja' if summary['second_review_required'] else 'nein'}",
        f"- Zweitprüfung durchgeführt: {'ja' if summary['second_review_performed'] else 'nein'}",
        f"- Konkret nachgeprüfte rote Vorgänge: {summary['reviewed_cases']}",
        f"- Fachlich auf Grün korrigiert: {len(summary['corrected_to_green'])}"
        + (" (" + ", ".join(summary['corrected_to_green']) + ")" if summary['corrected_to_green'] else ""),
        f"- Nach Zweitprüfung ausgeschlossen (Dublette/nicht buchungsrelevant): {len(summary['corrected_excluded'])}",
        f"- Verbleibende rote Vorgänge: {summary['remaining_red']}",
        f"- Ergebnis: {summary['result']}" + ("; fachlich offen (berechtigt rote Fälle bleiben Rot)" if summary["professionally_open"] else ""),
        "",
        "## Weitere Zählungen",
        "",
        "| Zählung | Anzahl |",
        "|---|---:|",
        f"| Grüne Vorgänge | {counts['gruene_vorgaenge']} |",
        f"| Rote Vorgänge | {counts['rote_vorgaenge']} |",
        f"| Rote Buchungszeilen (nicht mit roten Fällen verwechseln) | {counts['rote_buchungszeilen']} |",
        f"| Technisch nicht auswertbare Vorgänge | {counts['technisch_nicht_auswertbar']} |",
        f"| Bereits in DATEV vorhandene Vorgänge | {counts['bereits_in_datev_vorhanden']} |",
        f"| Sichere Dubletten | {counts['sichere_dubletten']} |",
        f"| Aussteuerungen (anderer Mandant/Rechtsträger, Übergaben) | {counts['aussteuerungen']} |",
        f"| Nicht buchungsrelevant gesamt | {counts['nicht_buchungsrelevant']} |",
        f"| Außerhalb Auftragszeitraum | {counts['ausserhalb_auftragszeitraum']} |",
        f"| Zahlungsavise | {counts['zahlungsavise']} |",
        "",
        "## Verteilung nach Rot-Gründen",
        "",
        "| Rot-Grund | Anzahl | Ursachen-/Plausibilitätsprüfung |",
        "|---|---:|---|",
    ]
    distribution = summary["reason_distribution"]
    if not distribution:
        lines.append("| – | 0 | keine roten Vorgänge |")
    for code, count in distribution.items():
        label = summary["reason_labels"].get(code, "ohne Rot-Grund")
        note = summary["cause_analysis"].get(code, "")
        lines.append(f"| {label} (`{code}`) | {count} | {note or '–'} |")
    lines.extend(["", "## Korrekturen aus der Zweitprüfung", "", "| Vorgangs-ID | von | nach | Begründung |", "|---|---|---|---|"])
    if not summary["corrections"]:
        lines.append("| – | – | – | keine Umstufung |")
    for item in summary["corrections"]:
        lines.append(
            f"| {item.get('transaction_id', '')} | {item.get('from', '')} | {item.get('to', '')} | "
            f"{str(item.get('reason', '')).replace('|', '/')} |"
        )
    lines.extend([
        "", "## Verbleibende rote Vorgänge mit konkretem offenen Grund", "",
        "| Vorgangs-ID | Rot-Grund | Offene Felder | Belegreferenz | Durchgeführter Prüfversuch | Nächster Prüfschritt |",
        "|---|---|---|---|---|---|",
    ])
    if not summary["red_cases"]:
        lines.append("| – | – | – | – | – | keine roten Vorgänge |")
    for row in summary["red_cases"]:
        lines.append(
            f"| {row['transaction_id']} | {row['label']} (`{row['code']}`) | {', '.join(row['open_fields']) or '–'} | "
            f"{row['document_reference'] or '–'} | {row['verification_attempted'].replace('|', '/') or '–'} | "
            f"{row['next_check'].replace('|', '/') or '–'} |"
        )
    if summary["systematic_categories"]:
        lines.extend(["", "## Auffällig häufige Rot-Kategorien", ""])
        for item in summary["systematic_categories"]:
            lines.append(
                f"- `{item['code']}`: {item['count']} Fälle ({item['share']} %) – Ursache/systematische Fehleinstufung geprüft: {item['note'] or 'FEHLT'}"
            )
    if summary["errors"]:
        lines.extend(["", "## Offene Mängel des Nachweises", ""])
        lines.extend(f"- {error}" for error in summary["errors"])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Klärungsquote und Zweitprüfung prüfen")
    parser.add_argument("--input", required=True, type=Path, help="Lauf-JSON")
    parser.add_argument("--markdown", type=Path, help="Klärungsquoten-Nachweis als Markdown schreiben")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    summary, errors = compute_clarification_rate(data)
    if args.markdown:
        args.markdown.write_text(render_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if errors:
        print("Klärungsquoten-Nachweis unvollständig:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
