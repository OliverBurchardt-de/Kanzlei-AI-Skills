import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "skripte"))
from konto import anzeige, klassifiziere, technisch


class KontoTests(unittest.TestCase):
    def test_fuehrende_nullen(self):
        self.assertEqual(anzeige("9800000", 4, "sachkonto"), "0980")
        self.assertEqual(anzeige("9000000", 4, "sachkonto"), "0900")
        self.assertEqual(anzeige("9800000", 4), "0980")

    def test_roundtrip(self):
        for konto in ("0980", "1590", "1200", "70147"):
            art = "personenkonto" if len(konto) == 5 else "sachkonto"
            self.assertEqual(anzeige(technisch(konto, 4), 4, art), konto)

    def test_klassifikation(self):
        self.assertEqual(klassifiziere("0980", 4), "sachkonto")
        self.assertEqual(klassifiziere("10002", 4), "debitor")
        self.assertEqual(klassifiziere("70147", 4), "kreditor")


if __name__ == "__main__":
    unittest.main()
