from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import validate_package
from sharepoint_target import build_targets


def main() -> None:
    targets = build_targets("12861")
    manifest = {
        "beraternummer": 29098,
        "mandant": 12861,
        "run_contract": {
            "scope": {
                "target_periods": ["2026-07"],
                "include_prior_periods": False,
                "include_future_periods": False,
                "job_mode": "belegbuchhaltung",
            },
            "mandantenprofil": {
                "status": "existing",
                "source_status": "found",
                "approval_status": "approved",
                "evidence": [],
            },
            "wirtschaftsjahr_beginn": "2026-01-01",
            "sachkontenlaenge": 4,
            "sachkontenrahmen": "03",
            "accounting_method": "Bilanz",
            "kostenstellenpflicht": False,
            "vat_config": {},
            "account_config": {
                "gwg": "0480",
                "asset_accounts": ["0480"],
            },
            "person_account_ranges": {},
        },
        "preflight_evidence": {
            "mandantenprofil": {
                "source_url": str(targets["profile_url"]),
                "file_name": "12861.md",
                "file_uri": "sharepoint://12861-profile",
                "retrieved_via": "microsoft_sharepoint.fetch",
                "sha256": "a" * 64,
                "raw_evidence": "content_utf8",
            },
            "abgrenzungsregister": {
                "status": "not_found",
                "source_url": str(targets["accrual_url"]),
                "file_name": "12861.md",
                "retrieved_via": "microsoft_sharepoint.fetch",
                "checked_at": "2026-07-28T09:00:00+02:00",
                "not_found_code": "itemNotFound",
                "site_verified": True,
                "library_verified": True,
                "direct_lookup_attempts": 2,
            },
            "datev": {
                "source": "DATEV live",
                "retrieved_at": "2026-07-28T09:00:00+02:00",
                "validated_accounts": ["0480"],
                "validated_bu_keys": [],
                "used_person_accounts": [],
                "highest_creditor_account": 70000,
                "highest_debtor_account": 10000,
                "beraternummer": 29098,
                "mandantennummer": 12861,
                "wirtschaftsjahr_beginn": "2026-01-01",
                "sachkontenlaenge": 4,
                "sachkontenrahmen": "03",
                "master_data_checked": True,
                "master_data_records_found": 0,
                "prior_bookings_checked": True,
                "prior_booking_records_found": 0,
            },
        },
    }
    errors = validate_package._validate_preflight_manifest(manifest)
    assert errors == [], errors
    print("accrual register manifest contract: OK")


if __name__ == "__main__":
    main()
