from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("vergleiche_baseline", ROOT / "scripts" / "vergleiche_baseline.py")
modul = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(modul)

BASELINE = ROOT / "baseline" / "tools.json"


class BaselineTest(unittest.TestCase):
    def test_baseline_ist_gueltig_und_vollstaendig(self) -> None:
        daten = json.loads(BASELINE.read_text(encoding="utf-8"))
        namen = [werkzeug["name"] for werkzeug in daten["tools"]]
        self.assertEqual(len(namen), len(set(namen)))
        self.assertGreaterEqual(len(namen), 32)
        for name in namen:
            self.assertTrue(name.startswith("mcp__Riecken__datev_"), name)
        for pflicht in ("datev_search_clients", "datev_get_account_balances", "datev_get_account_postings",
                        "datev_get_open_items", "datev_get_client_dossier", "datev_prepare_document_filing"):
            self.assertIn(f"mcp__Riecken__{pflicht}", namen)

    def test_identische_dateien_ergeben_keine_aenderung(self) -> None:
        baseline = modul._lade(BASELINE)
        ergebnis = modul.vergleiche(baseline, baseline)
        self.assertFalse(ergebnis["aenderungen"])
        self.assertIn("Keine Änderungen", modul.bericht_markdown(ergebnis, baseline, "2026-10-10"))

    def test_erkennt_neue_entfernte_und_geaenderte_werkzeuge(self) -> None:
        baseline = modul._lade(BASELINE)
        aktuell = copy.deepcopy(baseline)
        entfernt = aktuell.pop("datev_get_bwa")
        aktuell["datev_prepare_letter"] = {
            "name": "mcp__Riecken__datev_prepare_letter",
            "description": "Rendert einen Brief.",
            "parameters": {"properties": {"client_id": {"type": "string"}}, "required": ["client_id"], "type": "object"},
        }
        aktuell["datev_get_open_items"]["parameters"]["properties"]["currency"] = {"type": ["string", "null"]}
        aktuell["datev_get_open_items"]["parameters"]["properties"]["status"]["enum"] = ["open", "cleared", "all", "disputed", None]
        aktuell["datev_get_account_balances"]["parameters"]["required"] = ["client_id", "fiscal_year"]
        aktuell["datev_search_clients"]["description"] += " Neu: auch Suche nach Steuernummer."
        ergebnis = modul.vergleiche(baseline, aktuell)
        self.assertTrue(ergebnis["aenderungen"])
        self.assertEqual(ergebnis["neu"], ["datev_prepare_letter"])
        self.assertEqual(ergebnis["entfernt"], ["datev_get_bwa"])
        self.assertIn("neuer Parameter `currency`", ergebnis["geaendert"]["datev_get_open_items"])
        self.assertTrue(any("Werteliste von `status`" in b for b in ergebnis["geaendert"]["datev_get_open_items"]))
        self.assertIn("`fiscal_year` ist jetzt Pflicht", ergebnis["geaendert"]["datev_get_account_balances"])
        self.assertIn("Beschreibung geändert", ergebnis["geaendert"]["datev_search_clients"])
        bericht = modul.bericht_markdown(ergebnis, aktuell, "2026-10-17")
        self.assertIn("## Neue Werkzeuge", bericht)
        self.assertIn("datev_prepare_letter", bericht)
        self.assertIn("## Entfernte Werkzeuge", bericht)
        self.assertIsNotNone(entfernt)

    def test_kommandozeile_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as ordner:
            aktuell_pfad = Path(ordner) / "aktuell.json"
            daten = json.loads(BASELINE.read_text(encoding="utf-8"))
            aktuell_pfad.write_text(json.dumps(daten), encoding="utf-8")
            self.assertEqual(modul.main(["--baseline", str(BASELINE), "--aktuell", str(aktuell_pfad), "--datum", "2026-10-10"]), 0)
            daten["tools"].append({"name": "mcp__Riecken__datev_workflow", "description": "x", "parameters": {"properties": {}, "type": "object"}})
            aktuell_pfad.write_text(json.dumps(daten), encoding="utf-8")
            bericht = Path(ordner) / "bericht.md"
            self.assertEqual(modul.main(["--baseline", str(BASELINE), "--aktuell", str(aktuell_pfad), "--bericht", str(bericht), "--datum", "2026-10-10"]), 1)
            self.assertIn("datev_workflow", bericht.read_text(encoding="utf-8"))
            self.assertEqual(modul.main(["--baseline", str(BASELINE), "--aktuell", str(Path(ordner) / "fehlt.json")]), 2)


if __name__ == "__main__":
    unittest.main()
