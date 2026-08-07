# SharePoint-Übergabebibliothek: Spezifikation

## Site und Bibliothek

| Element | Wert | Begründung |
|---|---|---|
| Site | `https://burchardtkollegen.sharepoint.com/sites/DMS-Uebergabe` (neu) | Berechtigungstrennung; die Entra-App der Bridge erhält per `Sites.Selected` nur auf diese Site Zugriff. `/sites/Wissen` bleibt reine Wissensbibliothek (lt. bestehender Skill-Doku ausdrücklich kein Dokumentenarchiv). |
| Bibliothek | `DMS_Uebergabe` | eine Bibliothek, keine Unterwebs |
| Ordnerschema | `<Mandantennummer>/<Jahr>/` z. B. `10002/2025/` | deterministisch aus den Sidecar-Feldern ableitbar; `scripts/sharepoint_target.py` im Skill erzeugt die Pfade |
| Versionierung | aktiviert (Hauptversionen, 50 behalten) | Fortschreibungs-Uploads (`replace`) bleiben nachvollziehbar |
| Dateipaare | `<Datei>` + `<Datei>.dms.json` | Sidecar = Metadaten-Kontrakt (siehe `../bridge-worker/schemas/uebergabe.schema.json`) |

## Content Type „DMS-Übergabedokument“

Spalten (interne Namen ohne Umlaute, werden von der Bridge beschrieben):

| Spalte (intern) | Typ | Pflicht | Beschreibung |
|---|---|---|---|
| `Mandantennummer` | Text, Validierung `=AND(LEN([Mandantennummer])=5,ISNUMBER(VALUE([Mandantennummer])))`, indiziert | ja* | 5-stellige DATEV-Mandantennummer |
| `Jahr` | Text (4-stellig) | ja* | Veranlagungszeitraum/Wirtschaftsjahr |
| `Dokumenttyp` | Auswahl (Werte = Schlüssel aus `mapping.yaml`: `bescheidreview_arbeitspapier`, `abschlussreview_arbeitspapier`, `fibu_pruefprotokoll`, `fibu_klaerungsfaelle`, `jahresabschluss_dokument`, `steuerakte_korrespondenz`) | ja* | steuert das DMS-Ziel |
| `Beschreibung` | Text (255) | ja* | DMS-Beschreibung |
| `QuelleSkill` | Text | nein | erzeugender Skill/Workflow |
| `StatusDMS` | Auswahl: `Neu` (Default), `InVerarbeitung`, `Abgelegt`, `Fehler`; indiziert | ja | Statusmaschine, ausschließlich von der Bridge geführt |
| `FehlerText` | mehrzeiliger Text | nein | Ursache bei `Fehler`, von der Bridge gesetzt |
| `DMSDokumentNr` | Text | nein | Writeback: DMS-Dokumentnummer |
| `DMSDokumentGUID` | Text | nein | Writeback: DMS-Dokument-GUID |
| `VerarbeitetAm` | Text (ISO 8601 UTC) | nein | Writeback: Ablagezeitpunkt |
| `VerarbeiteterHash` | Text | nein | Writeback: SHA-256 des abgelegten Standes |

\* „Pflicht“ fachlich: Quelle ist das Sidecar; die Bridge spiegelt die Werte in die Spalten. Die Spalten selbst sind in SharePoint **nicht** als Pflicht konfiguriert, damit der Datei-Upload des Agenten (der keine Spalten setzen kann) nicht blockiert wird und keine „ausstehenden Eigenschaften“ entstehen.

## Ansichten

| Ansicht | Filter/Sortierung | Zweck |
|---|---|---|
| `Offen` | `StatusDMS` ∈ {Neu, InVerarbeitung}, älteste zuerst | was noch nicht im DMS ist |
| `Fehler` | `StatusDMS = Fehler` | tägliche Sichtung (Runbook) |
| `Abgelegt` | `StatusDMS = Abgelegt`, `VerarbeitetAm` absteigend | Nachweis inkl. Dok-Nr. |
| Standard | gruppiert nach `Mandantennummer` | Navigation |

## Berechtigungen

- **Mitarbeiter** (M365-Gruppe Kanzlei): Beitragen (Upload, keine Löschrechte auf fremde Items — Standard „Beitragen ohne Löschen“ via Berechtigungsstufe kopieren, falls gewünscht).
- **Entra-App „DMS-Bridge“**: `Sites.Selected` mit Rolle `write` nur auf diese Site (Zuweisung per Graph, siehe Setup-Checkliste).
- **Claude-Agent (M365-Connector)**: arbeitet im Kontext des angemeldeten Nutzers — keine gesonderte App nötig.
- Kein anonymer Zugriff, kein externes Teilen.

## Aufbewahrung

Die Bibliothek ist **Durchgangsstation**, das Archiv ist das DMS. Empfehlung: Abgelegte Items 12 Monate behalten (Nachvollziehbarkeit/Rückfragen), danach per Aufbewahrungsrichtlinie bereinigen — die Nachweise (Auditlog der Bridge, DMS-Revisionshistorie) bleiben davon unberührt.
