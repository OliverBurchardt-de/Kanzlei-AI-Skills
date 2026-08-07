"""GoBD-taugliches Auditlog: eine JSONL-Zeile pro Ereignis, tagesweise Dateien.

Jede Zeile enthält Zeitstempel (UTC, ISO 8601), Ereignistyp und frei wählbare
Kontextfelder. Die Dateien werden nie überschrieben, nur angehängt; Rotation
erfolgt allein über den Dateinamen (ein File pro Kalendertag).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


class AuditLog:
    def __init__(self, log_dir: str | os.PathLike[str]) -> None:
        self._dir = Path(log_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _file_for_today(self) -> Path:
        return self._dir / f"dms_bridge_{datetime.now(timezone.utc):%Y-%m-%d}.jsonl"

    def event(self, event_type: str, **context: object) -> None:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "event": event_type,
            **context,
        }
        line = json.dumps(record, ensure_ascii=False, default=str)
        with self._file_for_today().open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def api_call(self, system: str, method: str, url: str, status: int | None, **context: object) -> None:
        self.event("api_call", system=system, method=method, url=url, status=status, **context)
