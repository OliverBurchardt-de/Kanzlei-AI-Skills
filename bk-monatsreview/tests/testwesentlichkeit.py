import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "skripte"))
from wesentlichkeit import (
    regelmaessig,
    ueblicher_monatswert,
    wesentliche_abweichung,
    wesentlichkeit,
)


class WesentlichkeitTests(unittest.TestCase):
    def test_schwelle(self):
        self.assertEqual(wesentlichkeit("10000"), Decimal("250.00"))
        self.assertEqual(wesentlichkeit("-50000"), Decimal("500.00"))

    def test_regelmaessigkeit(self):
        self.assertTrue(regelmaessig([100, 100, 0, 100]))
        self.assertFalse(regelmaessig([100, 0, 0, 100]))

    def test_monatswert(self):
        self.assertEqual(ueblicher_monatswert([100, 110, 0, 120]), Decimal("110.00"))

    def test_abweichung(self):
        self.assertTrue(wesentliche_abweichung(2000, 1000, 250))
        self.assertFalse(wesentliche_abweichung(1100, 1000, 250))


if __name__ == "__main__":
    unittest.main()
