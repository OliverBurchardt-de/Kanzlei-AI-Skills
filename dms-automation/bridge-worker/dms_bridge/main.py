"""One-Shot-Lauf des DMS-Bridge-Workers (Einstieg für den Task Scheduler).

Ablauf je Lauf:
  1. Lockfile setzen (parallele Läufe verhindern), Konfiguration + Mapping laden.
  2. DATEVconnect-Preflight (GET /dms/v2/info).
  3. Graph-Delta abrufen (nur Änderungen seit letztem Lauf).
  4. Je vollständigem Paar (Binärdatei + Sidecar): validieren, Mandanten-GUID
     auflösen, Datei hochladen, Dokument anlegen bzw. fortschreiben,
     SharePoint-Spalten zurückschreiben, Ledger fortschreiben.
  5. deltaLink persistieren, Lock freigeben.

Fachliche Fehler führen zu StatusDMS='Fehler' + FehlerText am Item; das Item
bleibt liegen und wird erst nach einer Änderung (Delta) erneut verarbeitet.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import CONTRACT_VERSION
from .datev_client import DatevClient, DatevError
from .graph_client import GraphClient, GraphError
from .log import AuditLog
from .mapper import (
    ContractError,
    binary_name_for,
    build_document_payload,
    is_sidecar,
    load_schema,
    resolve_mapping,
    validate_sidecar,
)
from .state import State


def _secret(credential_name: str, env_var: str) -> str:
    """Geheimnis aus dem Windows Credential Manager (keyring), sonst Umgebung."""
    try:
        import keyring

        value = keyring.get_password("dms-bridge", credential_name)
        if value:
            return value
    except Exception:
        pass
    value = os.environ.get(env_var)
    if not value:
        raise RuntimeError(
            f"Geheimnis fehlt: Credential-Manager-Eintrag 'dms-bridge/{credential_name}' "
            f"oder Umgebungsvariable {env_var}"
        )
    return value


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Bridge:
    def __init__(self, config: dict, audit: AuditLog) -> None:
        self.config = config
        self.audit = audit
        sp = config["sharepoint"]
        dc = config["datevconnect"]
        self.graph = GraphClient(
            tenant_id=sp["tenant_id"],
            client_id=sp["client_id"],
            client_secret=_secret("graph", "DMS_BRIDGE_GRAPH_SECRET"),
            hostname=sp["hostname"],
            site_path=sp["site_path"],
            library=sp["library"],
            audit=audit,
        )
        self.datev = DatevClient(
            base_url=dc["base_url"],
            username=_secret("datevconnect-user", "DMS_BRIDGE_DATEV_USER"),
            password=_secret("datevconnect-password", "DMS_BRIDGE_DATEV_PASSWORD"),
            verify_tls=dc.get("verify_tls", True),
            audit=audit,
        )
        self.dms_user_guid = dc["dms_user_guid"]
        worker = config["worker"]
        self.mapping = yaml.safe_load(Path(worker["mapping_file"]).read_text(encoding="utf-8"))
        self.schema = load_schema()
        self.state = State(worker["state_db"])
        self.max_items = int(worker.get("max_items_per_run", 50))

    # -- Hilfen ------------------------------------------------------------

    def _fail_item(self, item_id: str, message: str) -> None:
        self.audit.event("item_failed", item_id=item_id, error=message)
        self.graph.update_columns(item_id, {"StatusDMS": "Fehler", "FehlerText": message[:1000]})

    def _mirror_columns(self, item_id: str, sidecar: dict) -> None:
        self.graph.update_columns(
            item_id,
            {
                "Mandantennummer": sidecar["mandanten_nr"],
                "Jahr": str(sidecar["jahr"]),
                "Dokumenttyp": sidecar["dokumenttyp"],
                "Beschreibung": sidecar["beschreibung"],
                "QuelleSkill": sidecar["quelle_skill"],
            },
        )

    # -- Kernverarbeitung --------------------------------------------------

    def process_pair(self, sidecar_item: dict) -> None:
        sidecar_id = sidecar_item["id"]
        parent_id = sidecar_item["parentReference"]["id"]
        sidecar_raw = self.graph.download(sidecar_id)
        try:
            sidecar = json.loads(sidecar_raw.decode("utf-8"))
            validate_sidecar(sidecar, self.schema)
            if sidecar["contract_version"] != CONTRACT_VERSION:
                raise ContractError(
                    f"contract_version {sidecar['contract_version']} wird nicht unterstützt"
                )
            target = resolve_mapping(sidecar, self.mapping)
        except (json.JSONDecodeError, ContractError) as exc:
            self._fail_item(sidecar_id, str(exc))
            return

        expected_name = binary_name_for(sidecar_item["name"])
        if expected_name != sidecar["datei_name"]:
            self._fail_item(
                sidecar_id,
                f"Sidecar-Name passt nicht zur Binärdatei: erwartet '{sidecar['datei_name']}'",
            )
            return

        binary_item = self.graph.get_child(parent_id, sidecar["datei_name"])
        if binary_item is None:
            if sidecar["binary_delivery"] == "manual":
                self.audit.event(
                    "awaiting_manual_binary", sidecar_id=sidecar_id, name=sidecar["datei_name"]
                )
                return  # Manuell-Lane: Binärdatei kommt später, Item bleibt 'Neu'
            self._fail_item(sidecar_id, f"Binärdatei '{sidecar['datei_name']}' fehlt neben dem Sidecar")
            return

        binary_id = binary_item["id"]
        self._mirror_columns(binary_id, sidecar)
        self.graph.update_columns(binary_id, {"StatusDMS": "InVerarbeitung", "FehlerText": ""})

        data = self.graph.download(binary_id)
        actual_sha = hashlib.sha256(data).hexdigest()
        if actual_sha != sidecar["sha256"]:
            self._fail_item(
                binary_id,
                f"sha256 weicht ab (Sidecar {sidecar['sha256'][:12]}…, Datei {actual_sha[:12]}…) – "
                "Datei oder Sidecar wurde nachträglich verändert",
            )
            return

        item_path = f"{sidecar_item['parentReference'].get('path', '')}/{sidecar['datei_name']}"
        entry = self.state.get(binary_id)
        if entry and entry.sha256 == actual_sha and entry.dms_guid:
            # Idempotenz: identischer Stand wurde bereits abgelegt.
            self.audit.event("already_processed", item_id=binary_id, dms_guid=entry.dms_guid)
            self._writeback_success(binary_id, entry.dms_guid, entry.dms_number, actual_sha)
            return

        try:
            if entry and entry.dms_guid and sidecar.get("update_von_dms_guid") in (None, entry.dms_guid):
                dms_guid, dms_number = self._update_document(
                    entry.dms_guid, sidecar, target, data, known_number=entry.dms_number
                )
            elif sidecar.get("update_von_dms_guid"):
                dms_guid, dms_number = self._update_document(
                    sidecar["update_von_dms_guid"], sidecar, target, data
                )
            else:
                dms_guid, dms_number = self._create_document(sidecar, target, data)
        except (DatevError, ContractError) as exc:
            self._fail_item(binary_id, str(exc))
            return

        self.state.record_success(binary_id, item_path, actual_sha, dms_guid, dms_number, _now())
        self._writeback_success(binary_id, dms_guid, dms_number, actual_sha)
        self.audit.event(
            "document_filed",
            item_id=binary_id,
            path=item_path,
            dms_guid=dms_guid,
            dms_number=dms_number,
            sha256=actual_sha,
            mandant=sidecar["mandanten_nr"],
            dokumenttyp=sidecar["dokumenttyp"],
        )

    def _create_document(self, sidecar: dict, target: dict, data: bytes) -> tuple[str, int | None]:
        guid = self.datev.resolve_client_guid(sidecar["mandanten_nr"])
        file_id = self.datev.upload_file(data)
        payload = build_document_payload(sidecar, target, guid, file_id, self.dms_user_guid)
        document = self.datev.create_document(payload)
        self.datev.add_dispatcher_information(
            document["id"],
            f"Automatische Ablage durch DMS-Bridge ({sidecar['quelle_skill']}), "
            f"sha256 {sidecar['sha256'][:12]}…",
        )
        return document["id"], document.get("number")

    def _update_document(
        self,
        dms_guid: str,
        sidecar: dict,
        target: dict,
        data: bytes,
        known_number: int | None = None,
    ) -> tuple[str, int | None]:
        """Fortschreibung: neue Datei-Revision am bestehenden Dokument.

        Fällt bei Ablehnung durch die API auf 'new_document' zurück (niemals
        löschen, siehe Konzept E5).
        """
        strategy = target.get("update_strategy", "version")
        if strategy == "version":
            try:
                items = self.datev.get_structure_items(dms_guid)
                files = [i for i in items if i.get("type") == 1]
                if len(files) != 1:
                    raise DatevError(f"Erwartet genau 1 Datei-structure_item, gefunden {len(files)}")
                file_id = self.datev.upload_file(data)
                self.datev.update_structure_item(
                    dms_guid,
                    files[0]["id"],
                    file_id,
                    sidecar["datei_name"],
                    sidecar["erstellt_am"],
                    f"Aktualisierung durch DMS-Bridge ({sidecar['quelle_skill']}), "
                    f"neuer Stand sha256 {sidecar['sha256'][:12]}…",
                )
                self.datev.add_dispatcher_information(
                    dms_guid,
                    f"Fortschreibung durch DMS-Bridge, sha256 {sidecar['sha256'][:12]}…",
                )
                return dms_guid, known_number
            except DatevError as exc:
                self.audit.event("version_update_rejected", dms_guid=dms_guid, error=str(exc))
        # Fallback bzw. konfigurierte Strategie 'new_document'
        updated = dict(sidecar)
        updated["beschreibung"] = (
            f"{sidecar['beschreibung']} (Aktualisierung, ersetzt Dokument {dms_guid})"[:255]
        )
        return self._create_document(updated, target, data)

    def _writeback_success(
        self, item_id: str, dms_guid: str, dms_number: int | None, sha256: str
    ) -> None:
        self.graph.update_columns(
            item_id,
            {
                "StatusDMS": "Abgelegt",
                "FehlerText": "",
                "DMSDokumentGUID": dms_guid,
                "DMSDokumentNr": str(dms_number) if dms_number is not None else "",
                "VerarbeitetAm": _now(),
                "VerarbeiteterHash": sha256,
            },
        )

    # -- Lauf --------------------------------------------------------------

    def run(self) -> int:
        info = self.datev.info()
        self.audit.event("run_started", dms_info=info)
        changes, delta_link = self.graph.iter_changes(self.state.get_delta_link())
        sidecars = [
            item
            for item in changes
            if "file" in item and is_sidecar(item.get("name", "")) and "deleted" not in item
        ]
        self.audit.event("delta_received", changes=len(changes), sidecars=len(sidecars))
        for sidecar_item in sidecars[: self.max_items]:
            try:
                self.process_pair(sidecar_item)
            except GraphError as exc:
                # Transportfehler: Item nicht als 'Fehler' markieren, nächster Lauf versucht es erneut.
                self.audit.event("transient_error", item_id=sidecar_item.get("id"), error=str(exc))
        self.state.set_delta_link(delta_link)
        self.audit.event("run_finished")
        return 0


def main() -> int:
    config_path = Path(sys.argv[1] if len(sys.argv) > 1 else "config.yaml")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    worker = config["worker"]
    audit = AuditLog(worker.get("log_dir", "logs"))

    lock = Path(worker.get("lock_file", "dms_bridge.lock"))
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        audit.event("run_skipped_locked", lock=str(lock))
        return 3
    try:
        os.write(fd, _now().encode())
        os.close(fd)
        bridge = Bridge(config, audit)
        try:
            return bridge.run()
        finally:
            bridge.state.close()
    except Exception as exc:  # Startfehler (Config, Auth, DATEVconnect nicht erreichbar)
        audit.event("run_aborted", error=str(exc))
        return 1
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
