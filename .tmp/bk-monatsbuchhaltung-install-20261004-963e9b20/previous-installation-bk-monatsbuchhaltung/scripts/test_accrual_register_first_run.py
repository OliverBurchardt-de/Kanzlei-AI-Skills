from __future__ import annotations

import sys
import tempfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import build_package


def write_and_read(temp: Path, data: dict) -> str:
    review = temp / build_package.FOLDERS["review"]
    review.mkdir(parents=True, exist_ok=True)
    build_package.write_accrual_register(temp, data)
    return (review / "Abgrenzungsregister_Vorschlag.md").read_text(
        encoding="utf-8"
    )


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="bk_accrual_first_run_") as name:
        temp = Path(name)
        base = {
            "run": {
                "_preflight_summary": {
                    "abgrenzungsregister": {
                        "status": "not_found",
                        "first_run_without_register": True,
                    }
                }
            },
            "accrual_register": [],
            "accrual_candidates": [],
        }

        empty_text = write_and_read(temp, base)
        assert "Status: Keine Neuanlage erforderlich." in empty_text
        assert "Keine offenen Rechnungsabgrenzungen" in empty_text

        with_accrual = {
            **base,
            "accrual_register": [
                {
                    "accrual_id": "ARAP-2026-001",
                    "type": "ARAP",
                    "partner": "Testversicherung",
                    "description": "Jahresversicherung",
                    "release_account": "4360",
                    "accrual_account": "0980",
                    "document_field_1": "RE-100",
                    "service_start": "2026-07-01",
                    "service_end": "2027-06-30",
                    "original_net": "1200.00",
                    "monthly_release": "100.00",
                    "next_release_period": "2026-07",
                    "remaining_amount": "1100.00",
                }
            ],
        }
        required_text = write_and_read(temp, with_accrual)
        assert "Status: Neuanlage erforderlich." in required_text
        assert "Testversicherung" in required_text

    print("accrual register first-run contract: OK")


if __name__ == "__main__":
    main()
