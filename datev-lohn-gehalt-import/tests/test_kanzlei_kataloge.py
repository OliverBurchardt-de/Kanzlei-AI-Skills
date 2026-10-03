import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("zw", ROOT / "scripts/zeitwirtschaft.py")
zw = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(zw)


class CatalogueTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "examples/zeitwirtschaft.json").read_text(encoding="utf-8"))

    def test_advisor_default_and_conflict(self):
        del self.data["beraternummer"]
        normalized, txt, _ = zw.render(self.data)
        self.assertEqual(normalized["beraternummer"], "413885")
        self.assertTrue(txt.startswith(b"413885;"))
        self.data["beraternummer"] = "128588"
        with self.assertRaisesRegex(ValueError, "Kanzleivorgabe"):
            zw.render(self.data)

    def test_valid_umlaut_key_and_unknown_key(self):
        self.data["datensaetze"] = [{"personalnummer": "00002", "kalendertag": "13",
                                    "ausfallschluessel": "EÜ", "quelle": "Synthetisches Schlüsselbeispiel"}]
        _, txt, _ = zw.render(self.data)
        self.assertIn(";EÜ;".encode("cp1252"), txt)
        self.data["datensaetze"][0]["ausfallschluessel"] = "ZZ"
        with self.assertRaisesRegex(ValueError, "DATEV-Katalog"):
            zw.render(self.data)

    def test_expired_absence_key(self):
        self.data["datensaetze"] = [{"personalnummer": "00002", "kalendertag": "13",
                                    "ausfallschluessel": "KS", "stunden": "4.00", "quelle": "Synthetischer Altfall"}]
        with self.assertRaisesRegex(ValueError, "nicht mehr erfassbar"):
            zw.render(self.data)
        self.data["abrechnungsmonat"] = "2021-03"
        zw.render(self.data)

    def test_baulohn_version_annotation_preserved(self):
        self.data["datensaetze"] = self.data["datensaetze"][:1]
        self.data["datensaetze"][0]["lohnart"] = "8380"
        with self.assertRaisesRegex(ValueError, "datev_version"):
            zw.render(self.data)
        self.data["datev_version"] = "16.0"
        with self.assertRaisesRegex(ValueError, "erst ab LuG 16.1"):
            zw.render(self.data)
        self.data["datev_version"] = "16.1"
        _, txt, _ = zw.render(self.data)
        self.assertIn(b";8380;", txt)

    def test_individual_wage_requires_source_and_checks_unit(self):
        self.data["datensaetze"] = self.data["datensaetze"][:1]
        self.data["datensaetze"][0].update(lohnart="1001", wert="10.00", werteinheit="stunden")
        with self.assertRaisesRegex(ValueError, "Nachweis aus dem Mandanten"):
            zw.render(self.data)
        self.data["mandanten_lohnarten"] = {"1001": {"bezeichnung": "Individuell", "werteinheit": "stunden"}}
        with self.assertRaisesRegex(ValueError, "Quellnachweis"):
            zw.render(self.data)
        self.data["mandanten_lohnarten"]["1001"]["quelle"] = "Synthetisch: geprüfte Zuordnung"
        zw.render(self.data)
        self.data["datensaetze"][0]["werteinheit"] = "betrag"
        with self.assertRaisesRegex(ValueError, "widerspricht"):
            zw.render(self.data)

    def test_ambiguous_individual_wage_ids(self):
        entry = {"bezeichnung": "Individuell", "quelle": "Synthetisch"}
        self.data["mandanten_lohnarten"] = {"001": entry, "1": copy.deepcopy(entry)}
        with self.assertRaisesRegex(ValueError, "Mehrdeutige"):
            zw.render(self.data)


if __name__ == "__main__":
    unittest.main()
