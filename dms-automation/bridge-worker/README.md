# DMS-Bridge-Worker

Legt Dokumente aus der SharePoint-Übergabebibliothek `/sites/DMS-Uebergabe` automatisch im DATEV DMS ab. Referenzimplementierung in Python — zugleich die ausführbare Spezifikation für eine mögliche Umsetzung durch den Klardaten-Anbieter oder einen Nachbau in anderer Technologie.

## Funktionsweise

Ein Lauf (One-Shot, vom Task Scheduler alle 5 Minuten gestartet):

1. **Lock** setzen — parallele Läufe werden übersprungen (Exit-Code 3).
2. **Preflight** — `GET /dms/v2/info` gegen DATEVconnect; nicht erreichbar → Abbruch ohne Statusänderungen (Exit-Code 1).
3. **Delta-Query** gegen die Bibliothek (Microsoft Graph) — nur Änderungen seit dem letzten Lauf; der `deltaLink` liegt im SQLite-Ledger.
4. Je **Sidecar-Datei** (`<Datei>.dms.json`, Kontrakt: `schemas/uebergabe.schema.json`):
   - Sidecar validieren, Dokumenttyp gegen `mapping.yaml` auflösen,
   - Binärdatei daneben suchen (fehlt sie bei `binary_delivery: manual`, wartet der Worker),
   - SHA-256 der Datei gegen das Sidecar prüfen,
   - Mandantennummer über `/master-data/v1/clients` in die Mandanten-GUID auflösen,
   - `POST /dms/v2/document-files` → `POST /dms/v2/documents` (im selben Lauf — DATEV verwirft nicht zugeordnete Uploads nach 24 h),
   - Revisionsvermerk per `dispatcher-information`,
   - SharePoint-Spalten zurückschreiben: `StatusDMS=Abgelegt`, `DMSDokumentNr`, `DMSDokumentGUID`, `VerarbeitetAm`, `VerarbeiteterHash` (+ gespiegelte Metadaten).
5. **Fortschreibung**: Meldet die Delta-Query ein bereits abgelegtes Item mit neuem Hash, wird je `update_strategy` verfahren:
   - `version` (Default): neue Datei-Revision am bestehenden DMS-Dokument (`PUT …/structure-items/{id}` mit `revision_comment`); lehnt die API das ab, automatischer Fallback auf `new_document`.
   - `new_document`: neues Dokument mit Beschreibungszusatz „Aktualisierung, ersetzt Dokument …“.
   - Es wird **niemals gelöscht** (GoBD).
6. Fachliche Fehler (unbekannter Dokumenttyp, Mandant nicht eindeutig, Hash-Abweichung, DMS-Ablehnung) → `StatusDMS=Fehler` + `FehlerText` am Item; das Item bleibt liegen, bis es geändert wird. Transportfehler (Graph nicht erreichbar) werden im nächsten Lauf erneut versucht, ohne den Status anzufassen.

Jede API-Interaktion und jede Entscheidung landet im JSONL-Auditlog (`logs/dms_bridge_YYYY-MM-DD.jsonl`, Aufbewahrung 10 Jahre, nur anhängend).

## Installation (Windows-Host im ASP mit Netzzugang zu DATEVconnect und Graph)

```powershell
# 1. Python 3.11+ oder die PyInstaller-EXE verwenden (siehe unten)
py -m venv C:\dms-bridge\venv
C:\dms-bridge\venv\Scripts\pip install -r requirements.txt

# 2. Konfiguration
copy config.example.yaml C:\dms-bridge\config.yaml   # anpassen
copy mapping.example.yaml C:\dms-bridge\mapping.yaml # IDs gegen /dms/v2/domains prüfen!

# 3. Geheimnisse im Windows Credential Manager hinterlegen (Ziel "dms-bridge"):
#    - dms-bridge/graph                (Client Secret der Entra-App)
#    - dms-bridge/datevconnect-user     (DATEVconnect-Benutzer)
#    - dms-bridge/datevconnect-password
#    Alternativ (nur Test): Umgebungsvariablen DMS_BRIDGE_GRAPH_SECRET,
#    DMS_BRIDGE_DATEV_USER, DMS_BRIDGE_DATEV_PASSWORD

# 4. Probelauf
C:\dms-bridge\venv\Scripts\python -m dms_bridge.main C:\dms-bridge\config.yaml

# 5. Geplante Aufgabe (alle 5 Minuten, Service-Konto ohne Anmeldung)
schtasks /Create /TN "DMS-Bridge" /SC MINUTE /MO 5 /RU <SERVICEKONTO> /RP * ^
  /TR "C:\dms-bridge\venv\Scripts\python.exe -m dms_bridge.main C:\dms-bridge\config.yaml"
```

### PyInstaller-Build (falls der ASP keine Python-Installation erlaubt)

```powershell
pip install pyinstaller
pyinstaller --onefile --name dms-bridge --add-data "schemas;schemas" -p . dms_bridge/main.py
# Ergebnis: dist\dms-bridge.exe; Aufruf: dms-bridge.exe C:\dms-bridge\config.yaml
```

## Tests

```bash
pip install -r requirements.txt pytest
python -m pytest tests/ -q
```

`tests/test_mapper.py` prüft den Metadaten-Kontrakt und den Payload-Aufbau gegen die Pflichtfelder der OpenAPI 2.3.1; `tests/test_contract.py` die DATEVconnect-Aufrufe (gemockt, ohne Netz).

## Betrieb

- **Fehlersichtung**: SharePoint-Ansicht „Fehler“ (Filter `StatusDMS=Fehler`) täglich prüfen; `FehlerText` nennt die Ursache. Nach Korrektur (z. B. Sidecar berichtigt) verarbeitet der nächste Lauf das Item automatisch neu.
- **Exit-Codes**: 0 = ok, 1 = Lauf abgebrochen (Config/Auth/DATEVconnect), 3 = übersprungen (Lock). Der Task Scheduler kann auf Exit-Code 1 eine Benachrichtigung setzen.
- **Idempotenz**: Ein bereits abgelegter Stand (Item + SHA-256) wird nie doppelt abgelegt — auch nach Ledger-Verlust entsteht kein Datenverlust, nur ggf. ein Duplikat; darum das Ledger (`dms_bridge_state.sqlite3`) mitsichern.
