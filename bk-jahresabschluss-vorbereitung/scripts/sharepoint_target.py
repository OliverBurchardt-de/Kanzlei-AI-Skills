from __future__ import annotations

import argparse
import json
import re


HOSTNAME = "burchardtkollegen.sharepoint.com"
SITE_PATH = "/sites/Wissen"
LIBRARY = "Mandantenbesonderheiten"
BASE_URL = f"https://{HOSTNAME}{SITE_PATH}/{LIBRARY}"


def build_targets(client_number: str) -> dict[str, object]:
    if not re.fullmatch(r"\d{5}", client_number):
        raise ValueError("Die Mandantennummer muss genau fünf Ziffern enthalten.")
    return {
        "hostname": HOSTNAME,
        "site_path": SITE_PATH,
        "library": LIBRARY,
        "profile_url": f"{BASE_URL}/Mandantenprofile/{client_number}.md",
        "accrual_url": f"{BASE_URL}/Abgrenzungsregister/{client_number}.md",
        "review_sheet_url": None,
        "review_sheet_status": "nicht_konfiguriert",
        "fetch_raw_file": True,
        "forbidden_path_fragments": [
            "Kanzlei/Mandanten",
            "Kanzlei\\Mandanten",
            "Documents",
            "Dokumente",
            "OneDrive",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mandant", required=True)
    args = parser.parse_args()
    print(json.dumps(build_targets(args.mandant), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

