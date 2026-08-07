"""DMS-Bridge: legt Dokumente aus der SharePoint-Übergabebibliothek im DATEV DMS ab.

Module:
    graph_client  – Microsoft Graph (MSAL Client Credentials, Delta-Query, Download, Writeback)
    datev_client  – DATEVconnect DMS-/Master-Data-API (Basic Auth)
    mapper        – Sidecar + mapping.yaml -> validiertes /documents-Payload
    state         – SQLite-Ledger (Idempotenz, deltaLink)
    log           – GoBD-taugliches JSONL-Auditlog
    main          – One-Shot-Lauf (Task-Scheduler-Einstieg)
"""

__version__ = "1.0.0"

CONTRACT_VERSION = "1.0"
