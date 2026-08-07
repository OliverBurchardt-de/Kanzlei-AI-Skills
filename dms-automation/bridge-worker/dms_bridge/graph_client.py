"""Microsoft-Graph-Zugriff auf die Übergabebibliothek.

Auth: MSAL Client-Credentials-Flow, App-Registrierung mit Sites.Selected
(nur auf /sites/DMS-Uebergabe berechtigt, siehe BIBLIOTHEK_SPEZIFIKATION.md).

Änderungserkennung: Drive-Delta-Query. Der deltaLink wird zwischen den Läufen
im SQLite-Ledger persistiert; der erste Lauf liefert den Vollbestand.
"""

from __future__ import annotations

from typing import Any, Iterator

import msal
import requests

GRAPH = "https://graph.microsoft.com/v1.0"


class GraphError(RuntimeError):
    pass


class GraphClient:
    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        hostname: str,
        site_path: str,
        library: str,
        audit=None,
    ) -> None:
        self._app = msal.ConfidentialClientApplication(
            client_id,
            client_credential=client_secret,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
        )
        self._hostname = hostname
        self._site_path = site_path
        self._library = library
        self._audit = audit
        self._session = requests.Session()
        self._drive_id: str | None = None
        self._site_id: str | None = None

    # -- Grundbausteine ----------------------------------------------------

    def _token(self) -> str:
        result = self._app.acquire_token_for_client(
            scopes=["https://graph.microsoft.com/.default"]
        )
        if "access_token" not in result:
            raise GraphError(f"Tokenbezug fehlgeschlagen: {result.get('error_description')}")
        return result["access_token"]

    def _request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._token()}"
        response = self._session.request(method, url, headers=headers, timeout=120, **kwargs)
        if self._audit:
            self._audit.api_call("graph", method, url, response.status_code)
        if response.status_code >= 400:
            raise GraphError(f"Graph {method} {url} -> {response.status_code}: {response.text[:500]}")
        return response

    # -- Site/Drive-Auflösung ---------------------------------------------

    def resolve_drive(self) -> str:
        if self._drive_id:
            return self._drive_id
        site = self._request(
            "GET", f"{GRAPH}/sites/{self._hostname}:{self._site_path}"
        ).json()
        self._site_id = site["id"]
        drives = self._request("GET", f"{GRAPH}/sites/{self._site_id}/drives").json()
        for drive in drives.get("value", []):
            if drive.get("name") == self._library:
                self._drive_id = drive["id"]
                return self._drive_id
        raise GraphError(f"Bibliothek '{self._library}' nicht gefunden auf {self._site_path}")

    # -- Delta-Query -------------------------------------------------------

    def iter_changes(self, delta_link: str | None) -> tuple[list[dict[str, Any]], str]:
        """Liefert (geänderte driveItems, neuer deltaLink)."""
        drive_id = self.resolve_drive()
        url = delta_link or f"{GRAPH}/drives/{drive_id}/root/delta"
        items: list[dict[str, Any]] = []
        while True:
            page = self._request("GET", url).json()
            items.extend(page.get("value", []))
            if "@odata.nextLink" in page:
                url = page["@odata.nextLink"]
                continue
            return items, page["@odata.deltaLink"]

    # -- Dateien -----------------------------------------------------------

    def download(self, item_id: str) -> bytes:
        drive_id = self.resolve_drive()
        return self._request(
            "GET", f"{GRAPH}/drives/{drive_id}/items/{item_id}/content"
        ).content

    def get_item(self, item_id: str) -> dict[str, Any]:
        drive_id = self.resolve_drive()
        return self._request("GET", f"{GRAPH}/drives/{drive_id}/items/{item_id}").json()

    def get_child(self, parent_id: str, name: str) -> dict[str, Any] | None:
        drive_id = self.resolve_drive()
        children = self._request(
            "GET", f"{GRAPH}/drives/{drive_id}/items/{parent_id}/children?$top=999"
        ).json()
        for child in children.get("value", []):
            if child.get("name") == name:
                return child
        return None

    # -- Spalten-Writeback -------------------------------------------------

    def update_columns(self, item_id: str, fields: dict[str, Any]) -> None:
        """Spiegelt Sidecar-Werte/Status in die Listenspalten des Items."""
        drive_id = self.resolve_drive()
        self._request(
            "PATCH",
            f"{GRAPH}/drives/{drive_id}/items/{item_id}/listItem/fields",
            json=fields,
        )
