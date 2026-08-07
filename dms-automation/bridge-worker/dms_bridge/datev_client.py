"""DATEVconnect-Zugriff: Master-Data (Mandanten-GUID) und DMS-Schreibpfad.

Ablauf je Dokument (vgl. OpenAPI document management 2.3.1):
  1. POST /dms/v2/document-files   (application/octet-stream) -> document_file_id
  2. POST /dms/v2/documents        (Metadaten + structure_items) -> Dokument-GUID
     Beide Schritte laufen im selben Worker-Lauf: nicht zugeordnete Datei-Uploads
     werden von DATEV nach 24 h verworfen.
  3. POST /dms/v2/documents/{id}/dispatcher-information  (Revisionsvermerk)

Fortschreibung (update_strategy 'version'):
  PUT /dms/v2/documents/{id}/structure-items/{structure_item_id}
  mit neuem document_file_id + revision_comment.
"""

from __future__ import annotations

from typing import Any

import requests


class DatevError(RuntimeError):
    """Technischer oder fachlicher Fehler der DATEVconnect-API."""


class DatevClient:
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        verify_tls: bool = True,
        audit=None,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.auth = (username, password)
        self._session.verify = verify_tls
        self._audit = audit

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = f"{self._base}{path}"
        response = self._session.request(method, url, timeout=300, **kwargs)
        if self._audit:
            self._audit.api_call("datevconnect", method, url, response.status_code)
        if response.status_code >= 400:
            raise DatevError(f"{method} {path} -> {response.status_code}: {response.text[:500]}")
        return response

    # -- Preflight ---------------------------------------------------------

    def info(self) -> dict[str, Any]:
        """DMS-Version/-Typ; scheitert früh, wenn DATEVconnect nicht erreichbar ist."""
        return self._request("GET", "/dms/v2/info").json()

    # -- Mandanten-Auflösung ----------------------------------------------

    def resolve_client_guid(self, mandanten_nr: str) -> str:
        """Fünfstellige Mandantennummer -> correspondence_partner_guid.

        Eindeutigkeit ist Pflicht: kein Treffer oder mehrere Treffer sind
        fachliche Fehler (Status 'Fehler' am SharePoint-Item), niemals raten.
        """
        response = self._request(
            "GET",
            "/master-data/v1/clients",
            params={"filter": f"number eq {int(mandanten_nr)}"},
        ).json()
        matches = [c for c in response if str(c.get("number")) == str(int(mandanten_nr))]
        if len(matches) != 1:
            raise DatevError(
                f"Mandantennummer {mandanten_nr}: {len(matches)} Treffer in master-data/clients"
            )
        return matches[0]["id"]

    # -- DMS-Schreibpfad ---------------------------------------------------

    def upload_file(self, data: bytes) -> int:
        response = self._request(
            "POST",
            "/dms/v2/document-files",
            data=data,
            headers={"Content-Type": "application/octet-stream"},
        ).json()
        return int(response["id"])

    def create_document(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/dms/v2/documents", json=payload).json()

    def get_structure_items(self, document_guid: str) -> list[dict[str, Any]]:
        return self._request(
            "GET", f"/dms/v2/documents/{document_guid}/structure-items"
        ).json()

    def update_structure_item(
        self,
        document_guid: str,
        structure_item_id: int,
        document_file_id: int,
        name: str,
        modification_date: str,
        revision_comment: str,
    ) -> None:
        self._request(
            "PUT",
            f"/dms/v2/documents/{document_guid}/structure-items/{structure_item_id}",
            json={
                "id": structure_item_id,
                "document_file_id": document_file_id,
                "name": name,
                "last_modification_date": modification_date,
                "revision_comment": revision_comment[:255],
            },
        )

    def add_dispatcher_information(self, document_guid: str, description: str) -> None:
        """Revisionshistorien-Eintrag ("Nach Online gesendet")."""
        self._request(
            "POST",
            f"/dms/v2/documents/{document_guid}/dispatcher-information",
            json={"name": "DMS-Bridge", "application": "DMS-Bridge", "description": description[:255]},
        )
