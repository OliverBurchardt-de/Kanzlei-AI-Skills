#!/usr/bin/env python3
"""Portable DATEV LuG time-data renderer; Python 3.10+, standard library only."""

import argparse
import calendar
from collections import Counter, defaultdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys


FIELDS = (
    ("personalnummer", "Personalnummer"),
    ("kalendertag", "Kalendertag"),
    ("ausfallschluessel", "Ausfallschlüssel"),
    ("lohnart", "Lohnartennummer"),
    ("stunden", "Stundenanzahl"),
    ("tage", "Tagesanzahl"),
    ("wert", "Wert"),
    ("faktor", "Abweichender Faktor"),
    ("lohnveraenderung", "Abweichende Lohnveränderung"),
    ("kostenstelle", "Kostenstellennummer"),
    ("kostentraeger", "Kostenträger"),
    ("bemerkung", "Bemerkung"),
)
RANGES = {
    "stunden": ("0.01", "24.00"), "tage": ("0.01", "1.00"),
    "wert": ("-9999999.99", "9999999.99"),
    "faktor": ("-999.99", "999.99"), "lohnveraenderung": ("0.01", "999.99"),
}
TOP_KEYS = {
    "schema_version", "beraternummer", "mandantennummer", "abrechnungsmonat",
    "personalnummer_typ", "datev_version", "korrekturmodus", "korrekturnachweis",
    "zuordnungsnachweis", "mandanten_lohnarten", "datensaetze",
}
UNITS = {"betrag", "stunden", "tage", "kilometer", "sonstiges"}
SKILL_ROOT = Path(__file__).resolve().parents[1]


def catalogues():
    result = {}
    for name in ("ausfallschluessel", "standardlohnarten", "baulohnarten"):
        content = json.loads((SKILL_ROOT / "references" / "kataloge" / (name + ".json")).read_text(encoding="utf-8"))
        result[name] = {entry["code"]: entry for entry in content["eintraege"]}
    return result


def version_tuple(value):
    require(isinstance(value, str) and re.fullmatch(r"[0-9]+\.[0-9]+(?:\.[0-9]+)?", value),
            "Numerische datev_version benötigt, z. B. 16.1")
    parts = tuple(map(int, value.split(".")))
    return parts + (0,) * (3 - len(parts))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value, label, low, high, width):
    require(isinstance(value, str) and re.fullmatch(r"[0-9]{1,%d}" % width, value),
            f"{label}: Ziffern als String mit höchstens {width} Stellen erwartet")
    require(low <= int(value) <= high, f"{label}: außerhalb {low} bis {high}")


def field_text(value, label):
    if value is None:
        return ""
    require(isinstance(value, str), f"{label}: String oder null erwartet")
    require(not any(c == ";" or ord(c) < 32 or 127 <= ord(c) < 160 for c in value),
            f"{label}: Semikolon oder Steuerzeichen im Feld")
    return value


def decimal_text(value, label, bounds):
    if not value:
        return ""
    require(re.fullmatch(r"-?[0-9]+(?:\.[0-9]{1,2})?", value),
            f"{label}: Dezimalstring mit Punkt, ohne Tausendertrennzeichen, max. 2 Nachkommastellen")
    val = Decimal(value)
    require(Decimal(bounds[0]) <= val <= Decimal(bounds[1]), f"{label}: außerhalb {bounds}")
    return format(val.quantize(Decimal("0.01")), "f")


def validate(data):
    require(isinstance(data, dict), "JSON-Wurzel muss ein Objekt sein")
    require(not set(data) - TOP_KEYS, f"Unbekannte Kopffelder: {set(data) - TOP_KEYS}")
    require(data.get("schema_version") == "1.0", "schema_version muss 1.0 sein")
    configured_advisor = json.loads((SKILL_ROOT / "config" / "kanzlei.json").read_text(encoding="utf-8"))["beraternummer"]
    data = {"beraternummer": configured_advisor, **data}
    number(data["beraternummer"], "Beraternummer", 1000, 9999999, 7)
    require(data["beraternummer"] == configured_advisor,
            f"Beraternummer weicht von der Kanzleivorgabe {configured_advisor} ab")
    catalogs = catalogues()
    wages = {**catalogs["standardlohnarten"], **catalogs["baulohnarten"]}
    client_wages = data.get("mandanten_lohnarten", {})
    require(isinstance(client_wages, dict), "mandanten_lohnarten muss ein Objekt sein")
    for code, entry in client_wages.items():
        number(code, "Mandantenlohnart", 1, 9999, 4)
        require(isinstance(entry, dict) and not set(entry) - {"bezeichnung", "quelle", "werteinheit"},
                f"Mandantenlohnart {code}: unbekannte Felder oder kein Objekt")
        require(all(isinstance(entry.get(k), str) and entry[k].strip() for k in ("bezeichnung", "quelle")),
                f"Mandantenlohnart {code}: Bezeichnung und Quellnachweis benötigt")
        require("werteinheit" not in entry or (isinstance(entry["werteinheit"], str) and entry["werteinheit"] in UNITS),
                f"Mandantenlohnart {code}: ungültige werteinheit")
    canonical_client_wages = {str(int(code)): entry for code, entry in client_wages.items()}
    require(len(canonical_client_wages) == len(client_wages), "Mehrdeutige Mandantenlohnartnummern")
    number(data.get("mandantennummer"), "Mandantennummer", 1, 99999, 5)
    month = data.get("abrechnungsmonat")
    require(isinstance(month, str) and re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", month),
            "abrechnungsmonat muss YYYY-MM sein")
    year, mon = map(int, month.split("-"))
    require(1 <= year <= 9999, "Ungültiges Jahr")
    last_day = calendar.monthrange(year, mon)[1]
    require(data.get("personalnummer_typ") in ("datev", "betrieblich"),
            "personalnummer_typ muss datev oder betrieblich sein")
    mode = data.get("korrekturmodus")
    require(mode in ("original", "monat_differenz", "kalender_vollmonat"),
            "korrekturmodus fehlt oder ist ungültig")
    for key in ("zuordnungsnachweis",):
        require(isinstance(data.get(key), str) and data[key].strip(), f"{key} fehlt")
    for key in ("datev_version", "korrekturnachweis"):
        require(key not in data or isinstance(data[key], str), f"{key} muss ein String sein")
    if mode != "original":
        require(data.get("korrekturnachweis", "").strip(), "Korrektur benötigt korrekturnachweis")
    rows = data.get("datensaetze")
    require(isinstance(rows, list) and rows, "datensaetze muss eine nichtleere Liste sein")
    normalized, daily = [], defaultdict(lambda: [Decimal(0), Decimal(0)])
    for index, row in enumerate(rows, 1):
        prefix = f"Datensatz {index}"
        require(isinstance(row, dict), f"{prefix}: Objekt erwartet")
        allowed = {k for k, _ in FIELDS} | {"quelle", "werteinheit"}
        require(not set(row) - allowed, f"{prefix}: unbekannte Felder {set(row) - allowed}")
        require(isinstance(row.get("quelle"), str) and row["quelle"].strip(), f"{prefix}: quelle fehlt")
        r = {key: field_text(row.get(key), f"{prefix}/{key}") for key, _ in FIELDS}
        require(r["personalnummer"].strip(), f"{prefix}: Personalnummer fehlt")
        if data["personalnummer_typ"] == "datev":
            number(r["personalnummer"], f"{prefix}/Personalnummer", 1, 99999, 5)
        for key, bounds in RANGES.items():
            r[key] = decimal_text(r[key], f"{prefix}/{key}", bounds)
        if r["lohnart"]:
            number(r["lohnart"], f"{prefix}/Lohnart", 1, 9999, 4)
            require(not 6000 <= int(r["lohnart"]) <= 7999, f"{prefix}: Lohnart 6000-7999 nicht zulässig")
            wage_code = str(int(r["lohnart"]))
            require(wage_code in wages or wage_code in canonical_client_wages,
                    f"{prefix}: Lohnart {wage_code} fehlt im Standardkatalog; Nachweis aus dem Mandanten benötigt")
            minimum = wages.get(wage_code, {}).get("ab_lug_version")
            if minimum:
                require(version_tuple(data.get("datev_version")) >= version_tuple(minimum),
                        f"{prefix}: Lohnart {wage_code} erst ab LuG {minimum}")
        for key, length in (("kostenstelle", 8), ("kostentraeger", 8), ("bemerkung", 30)):
            require(len(r[key]) <= length, f"{prefix}/{key}: maximal {length} Zeichen")
        if r["ausfallschluessel"]:
            absence = catalogs["ausfallschluessel"].get(r["ausfallschluessel"])
            require(absence is not None, f"{prefix}: Ausfallschlüssel nicht im DATEV-Katalog")
            require(month <= absence.get("erfassbar_bis", "9999-12"),
                    f"{prefix}: Ausfallschlüssel {r['ausfallschluessel']} im Abrechnungsmonat nicht mehr erfassbar")
            number(r["kalendertag"], f"{prefix}/Kalendertag", 1, last_day, 2)
            require(not r["wert"], f"{prefix}: Monatsfeld Wert in Kalenderzeile")
            require(row.get("werteinheit") in (None, ""), f"{prefix}: werteinheit nur für Monatszeilen")
            require(mode != "monat_differenz", f"{prefix}: Kalenderzeile im Modus monat_differenz")
            if r["ausfallschluessel"] == "U" and r["tage"]:
                require(r["tage"] in ("0.50", "1.00"), f"{prefix}: Urlaub nur halbe/ganze Tage")
            if r["faktor"] or r["lohnveraenderung"]:
                require(r["lohnart"], f"{prefix}: Faktor/Lohnveränderung ohne Lohnart")
            person = str(int(r["personalnummer"])) if data["personalnummer_typ"] == "datev" else r["personalnummer"]
            totals = daily[(person, int(r["kalendertag"]))]
            totals[0] += Decimal(r["stunden"] or "0")
            totals[1] += Decimal(r["tage"] or "0")
            require(totals[0] <= 24 and totals[1] <= 1,
                    f"{prefix}: Tagessumme über 24 Stunden oder 1 Tag")
        else:
            require(not any(r[k] for k in ("kalendertag", "stunden", "tage")),
                    f"{prefix}: Kalenderfelder ohne Ausfallschlüssel")
            require(r["wert"] and r["lohnart"], f"{prefix}: Monatszeile benötigt Wert und Lohnart")
            require(isinstance(row.get("werteinheit"), str) and row["werteinheit"] in UNITS, f"{prefix}: werteinheit fehlt/ungültig")
            require(mode != "kalender_vollmonat", f"{prefix}: Monatszeile im Modus kalender_vollmonat")
            if row["werteinheit"] == "stunden":
                require(abs(Decimal(r["wert"])) <= 744, f"{prefix}: Monatsstunden außerhalb -744 bis 744")
            known_unit = canonical_client_wages.get(str(int(r["lohnart"])), {}).get("werteinheit")
            require(not known_unit or known_unit == row["werteinheit"],
                    f"{prefix}: werteinheit widerspricht der belegten Mandantenlohnart")
            r["werteinheit"] = row["werteinheit"]
        r["quelle"] = row["quelle"]
        normalized.append(r)
    return {**data, "datensaetze": normalized}


def render(data, encoding="cp1252"):
    require(encoding in ("cp1252", "ascii"), "Exportprofil unterstützt cp1252 oder ascii")
    data = validate(data)
    year, mon = data["abrechnungsmonat"].split("-")
    header = [data["beraternummer"], data["mandantennummer"], f"{mon}/{year}"]
    if data["personalnummer_typ"] == "betrieblich":
        header.append("x")
    lines = [";".join(header)]
    for row in data["datensaetze"]:
        lines.append(";".join(row[k].replace(".", ",") if k in RANGES else row[k] for k, _ in FIELDS))
    ini = ["[Allgemein]", f"Feldanzahl = {len(FIELDS)}", "Feldtrennzeichen = Strichpunkt",
           "Satztrennzeichen = Enter/Return", "Zahlenkomma = ,", "Datumstrennzeichen = /",
           "", "[Feldinhalt]"]
    ini += [f"Feld{i} = {label}" for i, (_, label) in enumerate(FIELDS, 1)]
    # INI labels include umlauts even when the data is pure ASCII; keep INI in cp1252.
    return data, ("\r\n".join(lines) + "\r\n").encode(encoding, errors="strict"), ("\r\n".join(ini) + "\r\n").encode("cp1252")


def reject_duplicate_keys(pairs):
    obj = {}
    for key, value in pairs:
        require(key not in obj, f"Doppelter JSON-Schlüssel: {key}")
        obj[key] = value
    return obj


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true", help="Nur technisch prüfen, keine Dateien schreiben")
    parser.add_argument("--encoding", choices=("cp1252", "ascii"), default="cp1252")
    args = parser.parse_args(argv)
    if not args.check and args.output is None:
        parser.error("--output ist ohne --check erforderlich")
    try:
        raw = args.input.read_bytes()
        data, txt, ini = render(json.loads(raw.decode("utf-8-sig"), object_pairs_hook=reject_duplicate_keys), args.encoding)
        rows = data["datensaetze"]
        monthly = [r for r in rows if not r["ausfallschluessel"]]
        sums = defaultdict(Decimal)
        for r in monthly:
            sums[(r["lohnart"], r["werteinheit"])] += Decimal(r["wert"])
        counts = Counter(tuple(r[k] for k, _ in FIELDS) for r in rows)
        report = {
            "technische_pruefung": "bestanden", "datev_probeimport": "nicht durchgeführt",
            "profil": "zeitwirtschaft-12-felder-v1.1", "beraternummer": data["beraternummer"], "datencodierung": args.encoding,
            "ini_codierung": "cp1252", "zeilenende": "CRLF", "datenfelder": 12,
            "datensaetze": len(rows), "monatszeilen": len(monthly), "kalenderzeilen": len(rows)-len(monthly),
            "korrekturmodus": data["korrekturmodus"],
            "identische_datenzeilen_zusaetzlich": sum(n-1 for n in counts.values()),
            "monatssummen": [{"lohnart": la, "einheit": unit, "summe": str(value)} for (la, unit), value in sorted(sums.items())],
            "sha256": {"eingabe_json": hashlib.sha256(raw).hexdigest(), "txt": hashlib.sha256(txt).hexdigest(), "ini": hashlib.sha256(ini).hexdigest()},
            "noch_fachlich_zu_pruefen": [
                "Vollständigkeit und Richtigkeit gegenüber sämtlichen Quelldaten",
                "Personalnummernzuordnung, Zielstammdaten und ggf. Länge betrieblicher Personalnummern",
                "Fachliche Lohnartfunktionen, individuelle Grenzen und Änderungen seit den hinterlegten Katalogständen",
                "Schlüsselspezifische Feldkombinationen, Arbeitstage, Sollzeiten und Fehlzeitenvollständigkeit",
                "Korrekturdifferenzen bzw. vollständiger Korrekturkalender; Wiederholungsimport",
                "Eingerichtete Codepage und Interpretation als Dezimalstunden im Zielsystem",
            ],
        }
        if not args.check:
            stem = f"LuG_{data['beraternummer']}_{data['mandantennummer']}_{data['abrechnungsmonat']}"
            args.output.mkdir(parents=True, exist_ok=False)
            (args.output / f"{stem}.txt").write_bytes(txt)
            (args.output / "Zeitwirtschaft_12_Felder.ini").write_bytes(ini)
            (args.output / "daten.normalisiert.json").write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
            (args.output / "pruefbericht.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, UnicodeError) as exc:
        print(f"FEHLER: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
