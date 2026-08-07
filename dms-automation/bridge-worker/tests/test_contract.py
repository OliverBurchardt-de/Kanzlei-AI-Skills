"""Kontrakt-Tests gegen die DATEVconnect-Aufrufe (gemockt, kein Netz)."""

from __future__ import annotations

from unittest import mock

import pytest

from dms_bridge.datev_client import DatevClient, DatevError


def _client() -> DatevClient:
    return DatevClient("https://localhost:58452/datev/api", "user", "pass")


def _response(json_body=None, status=200):
    resp = mock.Mock()
    resp.status_code = status
    resp.json.return_value = json_body
    resp.text = str(json_body)
    return resp


def test_resolve_client_guid_eindeutig():
    client = _client()
    with mock.patch.object(client, "_request") as req:
        req.return_value = _response([{"number": 10002, "id": "guid-10002"}])
        assert client.resolve_client_guid("10002") == "guid-10002"
        req.assert_called_once_with(
            "GET", "/master-data/v1/clients", params={"filter": "number eq 10002"}
        )


@pytest.mark.parametrize(
    "treffer",
    [
        [],
        [{"number": 10002, "id": "a"}, {"number": 10002, "id": "b"}],
    ],
)
def test_resolve_client_guid_nicht_eindeutig(treffer):
    client = _client()
    with mock.patch.object(client, "_request") as req:
        req.return_value = _response(treffer)
        with pytest.raises(DatevError):
            client.resolve_client_guid("10002")


def test_upload_file_nutzt_octet_stream_und_liefert_id():
    client = _client()
    with mock.patch.object(client, "_request") as req:
        req.return_value = _response({"id": 1489})
        assert client.upload_file(b"PDF") == 1489
        _, kwargs = req.call_args
        assert kwargs["headers"]["Content-Type"] == "application/octet-stream"
        assert kwargs["data"] == b"PDF"


def test_update_structure_item_sendet_pflichtfelder():
    client = _client()
    with mock.patch.object(client, "_request") as req:
        req.return_value = _response(None, 204)
        client.update_structure_item(
            "doc-guid", 976058, 1489, "a.xlsx", "2026-08-07T10:00:00+02:00", "Kommentar"
        )
        _, kwargs = req.call_args
        body = kwargs["json"]
        # Pflicht laut StructureItemUpdate (OpenAPI 2.3.1): id + document_file_id
        assert body["id"] == 976058
        assert body["document_file_id"] == 1489
        assert body["revision_comment"] == "Kommentar"


def test_dispatcher_information_wird_gekuerzt():
    client = _client()
    with mock.patch.object(client, "_request") as req:
        req.return_value = _response(None, 204)
        client.add_dispatcher_information("doc-guid", "x" * 400)
        _, kwargs = req.call_args
        assert len(kwargs["json"]["description"]) == 255


def test_http_fehler_wird_zu_datev_error():
    client = _client()
    session_response = mock.Mock()
    session_response.status_code = 400
    session_response.text = "Bad Request"
    with mock.patch.object(client._session, "request", return_value=session_response):
        with pytest.raises(DatevError):
            client.info()
