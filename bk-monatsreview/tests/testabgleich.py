import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "skripte"))
from abgleich import abgleich, geld, summe


class AbgleichTests(unittest.TestCase):
    def test_deutsches_zahlenformat(self):
        self.assertEqual(geld("1.234,56 €"), Decimal("1234.56"))

    def test_decimal_rundung(self):
        self.assertEqual(summe(["2.675"]), Decimal("2.68"))
        self.assertEqual(summe(["1.005"]), Decimal("1.01"))

    def test_status(self):
        self.assertEqual(abgleich("ok", 1, 1)["ampel"], "GRUEN")
        self.assertEqual(abgleich("rot", 1, 2)["ampel"], "ROT")
        self.assertEqual(abgleich("gelb", status="GELB")["ampel"], "GELB")
        self.assertEqual(abgleich("fehlt")["ampel"], "NICHT_PRUEFBAR")


if __name__ == "__main__":
    unittest.main()
