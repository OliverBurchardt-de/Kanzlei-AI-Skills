import re
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


SKILL_ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = SKILL_ROOT / "assets" / "Monatsreview Arbeitspapier.xlsx"
MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


EXPECTED_HEADERS = {
    "Prüfergebnisse": [
        "Ampel", "Modul", "Prüfpunkt", "Konto", "Soll", "Ist", "Differenz",
        "Quelle", "Buchungsdatum", "Buchungstext", "Gegenkonto", "Grund",
        "Maßnahme", "Stapelaufnahme", "Bearbeitungsstatus", "Kommentar",
    ],
    "Auszifferungsliste": [
        "Ampel", "Priorität", "Kategorie", "Personenkonto", "Name",
        "Rechnungsnummer", "Rechnungsdatum", "Rechnungsbetrag",
        "Zahlungsdatum", "Zahlungsbetrag", "Gutschrift", "Konkrete Kombination",
        "Begründung", "Bearbeitungsstatus", "Kommentar",
    ],
    "Umbuchungsvorschläge": [
        "Ampel", "Sicher", "Datum", "Konto", "Gegenkonto", "Betrag",
        "Soll/Haben", "Belegfeld 1", "Buchungstext", "Buchungsschlüssel",
        "Grund", "Stapelaufnahme", "Bearbeitungsstatus", "Kommentar",
    ],
    "1590 Klärungsliste": [
        "Ampel", "Datum", "Betrag", "Alter in Monaten", "Konto", "Gegenkonto",
        "Zahlungsrichtung", "Zahlungspartner", "Vorgang/Leistungsbezug",
        "Buchungstext DATEV", "Beanstandung", "Versandfertiger Mandantentext",
        "Bearbeitungsstatus", "Kommentar",
    ],
    "Geprüfte Bereiche": [
        "Ampel", "Modul", "Prüfbereich", "Kurzbegründung", "Quelle", "Kommentar",
    ],
}


def column_index(reference):
    letters = re.match(r"[A-Z]+", reference).group(0)
    result = 0
    for letter in letters:
        result = result * 26 + ord(letter) - 64
    return result - 1


class WorkbookReader:
    def __init__(self, path):
        self.archive = zipfile.ZipFile(path)
        self.shared_strings = self._shared_strings()
        self.sheets = self._sheet_paths()

    def _shared_strings(self):
        try:
            root = ET.fromstring(self.archive.read("xl/sharedStrings.xml"))
        except KeyError:
            return []
        return ["".join(node.text or "" for node in item.iter(f"{{{MAIN_NS}}}t"))
                for item in root.findall(f"{{{MAIN_NS}}}si")]

    def _sheet_paths(self):
        workbook = ET.fromstring(self.archive.read("xl/workbook.xml"))
        rels = ET.fromstring(self.archive.read("xl/_rels/workbook.xml.rels"))
        targets = {rel.attrib["Id"]: rel.attrib["Target"]
                   for rel in rels.findall(f"{{{PKG_REL_NS}}}Relationship")}
        result = {}
        for sheet in workbook.find(f"{{{MAIN_NS}}}sheets"):
            target = targets[sheet.attrib[f"{{{REL_NS}}}id"]].lstrip("/")
            result[sheet.attrib["name"]] = target if target.startswith("xl/") else f"xl/{target}"
        return result

    def xml(self, sheet_name):
        return ET.fromstring(self.archive.read(self.sheets[sheet_name]))

    def first_row(self, sheet_name):
        root = self.xml(sheet_name)
        row = root.find(f".//{{{MAIN_NS}}}row[@r='1']")
        values = {}
        for cell in row.findall(f"{{{MAIN_NS}}}c"):
            index = column_index(cell.attrib["r"])
            if cell.attrib.get("t") == "inlineStr":
                value = "".join(node.text or "" for node in cell.iter(f"{{{MAIN_NS}}}t"))
            else:
                node = cell.find(f"{{{MAIN_NS}}}v")
                value = "" if node is None else node.text
                if cell.attrib.get("t") == "s" and value != "":
                    value = self.shared_strings[int(value)]
            values[index] = value
        return [values.get(index, "") for index in range(max(values) + 1)]


class ArbeitspapierContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader = WorkbookReader(WORKBOOK)

    def test_verbindliche_kopfzeilen(self):
        for sheet_name, expected in EXPECTED_HEADERS.items():
            with self.subTest(sheet=sheet_name):
                self.assertEqual(self.reader.first_row(sheet_name), expected)

    def test_ampel_validierung_und_farblogik(self):
        for sheet_name in EXPECTED_HEADERS:
            with self.subTest(sheet=sheet_name):
                xml = self.reader.xml(sheet_name)
                validations = [node.attrib.get("sqref", "")
                               for node in xml.findall(f".//{{{MAIN_NS}}}dataValidation")]
                conditions = [node.attrib.get("sqref", "")
                              for node in xml.findall(f".//{{{MAIN_NS}}}conditionalFormatting")]
                self.assertTrue(any("A2:A201" in value for value in validations))
                self.assertTrue(any("A2:A201" in value for value in conditions))

    def test_1590_validierungen_sind_spaltengenau(self):
        xml = self.reader.xml("1590 Klärungsliste")
        ranges = {
            node.attrib.get("sqref", "")
            for node in xml.findall(f".//{{{MAIN_NS}}}dataValidation")
        }
        self.assertEqual(ranges, {"A2:A201", "G2:G201", "M2:M201"})

    def test_statuszaehlung_verwendet_vordere_ampel(self):
        xml = self.reader.xml("Übersicht")
        formulas = [node.text or "" for node in xml.findall(f".//{{{MAIN_NS}}}f")]
        for status in ("ROT", "GELB", "GRUEN", "NICHT_PRUEFBAR"):
            self.assertTrue(any("$A$2:$A$500" in formula and status in formula
                                for formula in formulas))

    def test_vorlage_enthaelt_keine_live_test_markierung(self):
        for name in self.reader.archive.namelist():
            if name.endswith(".xml"):
                with self.subTest(part=name):
                    self.assertNotIn(b"Live-Test", self.reader.archive.read(name))

    def test_keine_automatische_datev_uebertragung(self):
        skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            "Der Skill importiert oder überträgt keine Buchungen in DATEV.",
            skill_text,
        )

    def test_1590_kleinbetrag_und_schlusskontrolle(self):
        regel_text = (
            SKILL_ROOT / "referenz" / "M2 Bank und Interim.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Ein Einzelbetrag unter 100 EUR darf nicht", regel_text)
        self.assertIn("auf Konto 4980", regel_text)
        self.assertIn("ohne Umsatzsteuer und ohne Buchungsschlüssel", regel_text)
        self.assertIn(
            "1590 ist nachbearbeitet – bitte Schlusskontrolle durchführen.",
            regel_text,
        )
        self.assertIn("Konto 1590 frisch über den", regel_text)
        self.assertIn("Riecken-Connector aus DATEV auslesen", regel_text)

    def test_datev_zugang_nur_ueber_riecken(self):
        skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        abruf_text = (
            SKILL_ROOT / "referenz" / "Riecken Abruf.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Riecken-Connector", skill_text)
        self.assertIn("datev_search_clients", abruf_text)
        self.assertIn("datev_get_account_balances", abruf_text)
        self.assertIn("datev_get_account_postings", abruf_text)
        for path in SKILL_ROOT.rglob("*.md"):
            if path.name == "Quellenbasis.md":
                continue
            with self.subTest(datei=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("Klardaten", text)
                self.assertNotIn("datev://", text)
                self.assertNotIn("datev_describe", text)


if __name__ == "__main__":
    unittest.main()
