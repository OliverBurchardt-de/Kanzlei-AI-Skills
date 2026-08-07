"""SQLite-Ledger des Workers.

Zweck:
  * Idempotenz: ein bereits abgelegter Stand (SharePoint-Item + sha256) wird nie
    erneut ins DMS geschrieben.
  * Fortschreibungs-Erkennung: gleiches Item, vorhandene DMS-GUID, neuer sha256.
  * Persistenz des Graph-deltaLink zwischen den Läufen.

Der Ledger ist Betriebszustand, kein Archiv – die revisionssichere Historie
liegt im JSONL-Auditlog und im DMS selbst.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS ledger (
    item_id        TEXT PRIMARY KEY,   -- Graph driveItem-Id der Binärdatei
    item_path      TEXT NOT NULL,      -- Pfad in der Bibliothek (für Menschen/Diagnose)
    sha256         TEXT NOT NULL,      -- zuletzt erfolgreich abgelegter Stand
    dms_guid       TEXT,               -- GUID des DMS-Dokuments
    dms_number     INTEGER,            -- DMS-Dokumentnummer
    revision       INTEGER NOT NULL DEFAULT 1,
    processed_at   TEXT NOT NULL       -- ISO 8601 UTC
);
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


@dataclass
class LedgerEntry:
    item_id: str
    item_path: str
    sha256: str
    dms_guid: str | None
    dms_number: int | None
    revision: int
    processed_at: str


class State:
    def __init__(self, db_path: str | Path) -> None:
        self._conn = sqlite3.connect(str(db_path))
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # -- deltaLink ---------------------------------------------------------

    def get_delta_link(self) -> str | None:
        row = self._conn.execute(
            "SELECT value FROM meta WHERE key = 'delta_link'"
        ).fetchone()
        return row[0] if row else None

    def set_delta_link(self, link: str) -> None:
        self._conn.execute(
            "INSERT INTO meta (key, value) VALUES ('delta_link', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (link,),
        )
        self._conn.commit()

    # -- Ledger ------------------------------------------------------------

    def get(self, item_id: str) -> LedgerEntry | None:
        row = self._conn.execute(
            "SELECT item_id, item_path, sha256, dms_guid, dms_number, revision, processed_at "
            "FROM ledger WHERE item_id = ?",
            (item_id,),
        ).fetchone()
        return LedgerEntry(*row) if row else None

    def record_success(
        self,
        item_id: str,
        item_path: str,
        sha256: str,
        dms_guid: str,
        dms_number: int | None,
        processed_at: str,
    ) -> None:
        existing = self.get(item_id)
        revision = existing.revision + 1 if existing else 1
        self._conn.execute(
            "INSERT INTO ledger (item_id, item_path, sha256, dms_guid, dms_number, revision, processed_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(item_id) DO UPDATE SET "
            "  item_path = excluded.item_path, sha256 = excluded.sha256, "
            "  dms_guid = excluded.dms_guid, dms_number = excluded.dms_number, "
            "  revision = excluded.revision, processed_at = excluded.processed_at",
            (item_id, item_path, sha256, dms_guid, dms_number, revision, processed_at),
        )
        self._conn.commit()
