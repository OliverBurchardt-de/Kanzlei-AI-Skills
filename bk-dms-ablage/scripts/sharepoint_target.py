"""Deterministische Zielpfade in der DMS-Übergabebibliothek.

Muster übernommen aus bk-monatsbuchhaltung/scripts/sharepoint_target.py:
Ziele werden ausschließlich aus Mandantennummer + Jahr gebildet, niemals
gesucht oder geraten.
"""

from __future__ import annotations

import argparse
import json
import re

HOSTNAME = "burchardtkollegen.sharepoint.com"
SITE_PATH = "/sites/DMS-Uebergabe"
LIBRARY = "DMS_Uebergabe"
BASE_URL = f"https://{HOSTNAME}{SITE_PATH}/{LIBRARY}"


def build_targets(client_number: str, year: int, file_name: str) -> dict[str, object]:
    if not re.fullmatch(r"\d{5}", client_number):
        raise ValueError("Die Mandantennummer muss genau fünf Ziffern enthalten.")
    if not 2000 <= year <= 2099:
        raise ValueError("Das Jahr muss vierstellig zwischen 2000 und 2099 liegen.")
    if "/" in file_name or "\\" in file_name:
        raise ValueError("Der Dateiname darf keine Pfadtrenner enthalten.")
    folder = f"{client_number}/{year}"
    return {
        "hostname": HOSTNAME,
        "site_path": SITE_PATH,
        "library": LIBRARY,
        "folder_path": folder,
        "file_url": f"{BASE_URL}/{folder}/{file_name}",
        "sidecar_url": f"{BASE_URL}/{folder}/{file_name}.dms.json",
        "forbidden_path_fragments": [
            "Kanzlei/Mandanten",
            "Kanzlei\\Mandanten",
            "Documents",
            "Dokumente",
            "OneDrive",
            "Mandantenbesonderheiten",
            "/sites/Wissen",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mandant", required=True)
    parser.add_argument("--jahr", required=True, type=int)
    parser.add_argument("--datei", required=True)
    args = parser.parse_args()
    print(json.dumps(build_targets(args.mandant, args.jahr, args.datei), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
