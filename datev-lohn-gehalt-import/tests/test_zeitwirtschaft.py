import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("zeitwirtschaft", ROOT / "scripts/zeitwirtschaft.py")
zw = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(zw)


class TimeImportTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "examples/zeitwirtschaft.json").read_text(encoding="utf-8"))

    def rejected(self, data):
        with self.assertRaises(ValueError):
            zw.render(data)

    def test_bytes_and_format_agree(self):
        data, txt, ini = zw.render(self.data)
        self.assertTrue(txt.startswith(b"413885;10000;09/2026\r\n"))
        self.assertIn(b"2500,00", txt)
        self.assertIn("Mustervergütung".encode("cp1252"), txt)
        self.assertNotIn(b"\xc3\xbc", txt)
        for payload in (txt, ini):
            self.assertTrue(payload.endswith(b"\r\n"))
            self.assertNotIn(b"\n", payload.replace(b"\r\n", b""))
            self.assertFalse(payload.startswith(b"\xef\xbb\xbf"))
        lines = txt.decode("cp1252").splitlines()
        self.assertEqual(len(lines[0].split(";")), 3)
        self.assertTrue(all(len(line.split(";")) == 12 for line in lines[1:]))
        self.assertIn(b"Feldanzahl = 12\r\n", ini)
        self.assertIn(b"Feld12 = Bemerkung", ini)
        self.assertEqual(lines[1].split(";")[0], "00001")
        self.assertEqual(data["datensaetze"][1]["lohnart"], "")

    def test_business_identifier_header(self):
        self.data["personalnummer_typ"] = "betrieblich"
        self.data["datensaetze"][0]["personalnummer"] = "AB12345678"
        _, txt, _ = zw.render(self.data)
        self.assertTrue(txt.startswith(b"413885;10000;09/2026;x\r\nAB12345678;"))
        self.data["personalnummer_typ"] = "datev"
        self.rejected(self.data)

    def test_invalid_fields_and_ranges(self):
        cases = [("lohnart", "6000"), ("lohnart", "07999"), ("wert", "10000000.00"),
                 ("wert", "1,50"), ("wert", "7:30"), ("wert", "1.001"), ("wert", "NaN"),
                 ("wert", 12.5), ("kostenstelle", "123456789"), ("bemerkung", "a;b"),
                 ("bemerkung", "a\nb"), ("personalnummer", "100000"), ("personalnummer", "0"),
                 ("werteinheit", ["stunden"])]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                bad = copy.deepcopy(self.data)
                bad["datensaetze"][0][field] = value
                self.rejected(bad)

    def test_exact_decimals_and_negative_correction(self):
        self.data["datensaetze"] = self.data["datensaetze"][:1]
        self.data["datensaetze"][0]["wert"] = "-0.01"
        self.data["korrekturmodus"] = "monat_differenz"
        self.rejected(self.data)
        self.data["korrekturnachweis"] = "Belegter Originalwert 2500.01, neuer Wert 2500.00"
        _, txt, _ = zw.render(self.data)
        self.assertIn(b"-0,01", txt)

    def test_calendar_month_confusion(self):
        for index, field, value in [(0, "kalendertag", "1"), (0, "stunden", "2"),
                                    (1, "wert", "50"), (1, "ausfallschluessel", "")]:
            with self.subTest(field=field):
                bad = copy.deepcopy(self.data)
                bad["datensaetze"][index][field] = value
                self.rejected(bad)

    def test_calendar_date_and_vacation(self):
        self.data["abrechnungsmonat"] = "2026-02"
        self.data["datensaetze"][1]["kalendertag"] = "29"
        self.rejected(self.data)
        self.data["abrechnungsmonat"] = "2028-02"
        zw.render(self.data)
        self.data["datensaetze"][1]["tage"] = "0.25"
        self.rejected(self.data)

    def test_daily_total_includes_equivalent_numeric_ids(self):
        row = copy.deepcopy(self.data["datensaetze"][1])
        row["personalnummer"] = "2"
        row["tage"] = "1.00"
        self.data["datensaetze"].append(row)
        self.rejected(self.data)

    def test_missing_and_unknown_values_are_not_silently_dropped(self):
        bad = copy.deepcopy(self.data)
        bad["datensaetze"][0]["adresse"] = "Nicht importierbar"
        self.rejected(bad)
        for field in ("quelle", "werteinheit", "lohnart", "wert"):
            bad = copy.deepcopy(self.data)
            del bad["datensaetze"][0][field]
            self.rejected(bad)
        self.data["beraternummer"] = "999"
        self.rejected(self.data)

    def test_not_representable(self):
        self.data["datensaetze"][0]["bemerkung"] = "Text 🦊"
        with self.assertRaises(UnicodeEncodeError):
            zw.render(self.data)

    def test_zero_month_value_is_not_blank(self):
        self.data["datensaetze"][0]["wert"] = "0"
        _, txt, _ = zw.render(self.data)
        self.assertEqual(txt.decode("cp1252").splitlines()[1].split(";")[6], "0,00")

    def test_hour_wage_limit_and_key_only_calendar(self):
        self.data["datensaetze"][0].update(wert="745", werteinheit="stunden")
        self.rejected(self.data)
        self.data["datensaetze"] = [{"personalnummer": "00002", "kalendertag": "13",
                                    "ausfallschluessel": "K", "quelle": "Synthetisch: arbeitsfreier Krankheitstag"}]
        _, txt, _ = zw.render(self.data)
        self.assertEqual(txt.decode("cp1252").splitlines()[1], "00002;13;K;;;;;;;;;")

    def test_cli_no_partial_output_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, out = Path(tmp)/"in.json", Path(tmp)/"output"
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                path.write_text(json.dumps(self.data), encoding="utf-8")
                self.assertEqual(zw.main([str(path), "--check"]), 0)
                self.assertFalse(out.exists())
                self.assertEqual(zw.main([str(path), "--output", str(out)]), 0)
                self.assertEqual(len(list(out.iterdir())), 4)
                before = {p.name: p.read_bytes() for p in out.iterdir()}
                self.assertEqual(zw.main([str(path), "--output", str(out)]), 2)
                self.assertEqual(before, {p.name: p.read_bytes() for p in out.iterdir()})
                path.write_text('{"schema_version":"1.0","schema_version":"1.1"}', encoding="utf-8")
                self.assertEqual(zw.main([str(path), "--output", str(Path(tmp)/"bad")]), 2)
                self.assertFalse((Path(tmp)/"bad").exists())


if __name__ == "__main__":
    unittest.main()
