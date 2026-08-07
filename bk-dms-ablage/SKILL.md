---
name: bk-dms-ablage
description: Legt fertige Kanzlei-Dokumente (Bescheidreview-Arbeitspapiere, Abschluss-Reviews, FIBU-Prüfprotokolle u. a.) mit Metadaten-Begleitdatei in der SharePoint-Übergabebibliothek DMS_Uebergabe ab, aus der die DMS-Bridge sie automatisch im DATEV DMS des Mandanten ablegt. Verwenden, wenn ein erzeugtes Dokument "ins DMS", "ins BMS", "in die DATEV-Akte" oder "zum Mandanten ablegen" soll oder ein Review-Skill seine Ausgabe archivieren will. Nicht für DUO-Belegtransfer (bk-datev-export) und nicht für die Wissensbibliothek /sites/Wissen.
---

# BK DMS-Ablage v1.0.0

Übergibt ein fertiges Dokument an die automatische DATEV-DMS-Ablage. Der Skill lädt **nie direkt ins DMS** — er legt Datei + Metadaten-Begleitdatei (Sidecar) in die Übergabebibliothek; die DMS-Bridge (siehe `dms-automation/` im Kanzlei-Repo) erledigt die Ablage und schreibt das Ergebnis an das SharePoint-Item zurück.

## Voraussetzungen

- Microsoft-365-Connector mit SharePoint-Upload verfügbar (`sharepoint_upload_file`).
- Die fünf Pflichtangaben sind bekannt oder werden **vor** dem Upload beim Nutzer erfragt:
  1. **Mandantennummer** (genau 5 Ziffern — niemals raten, niemals aus dem Mandantennamen ableiten),
  2. **Jahr** (VZ/Wirtschaftsjahr),
  3. **Dokumenttyp** (nur Schlüssel aus `references/METADATEN_KONTRAKT.md`),
  4. **Beschreibung** (max. 255 Zeichen, aussagekräftig für die DMS-Suche),
  5. **Quell-Skill** (z. B. `bescheid-review`; bei manueller Nutzung `manuell`).

## Ablauf

1. **Sidecar bauen und Lane bestimmen:**
   ```bash
   python scripts/build_uebergabe_meta.py <datei> --mandant <NNNNN> --jahr <JJJJ> \
     --dokumenttyp <schluessel> --beschreibung "<text>" --quelle-skill <skill> \
     [--monat <M>] [--stichworte "<a, b>"]
   ```
   Das Skript validiert gegen das Schema, berechnet SHA-256 und entscheidet die Lane: `upload` (≤ 900 KiB) oder `manual` (größer — der M365-Connector kann max. 1 MiB hochladen).

2. **Zielpfad bestimmen — ausschließlich per Skript, niemals suchen:**
   ```bash
   python scripts/sharepoint_target.py --mandant <NNNNN> --jahr <JJJJ> --datei <name>
   ```
   Ziel ist immer `DMS_Uebergabe/<Mandantennummer>/<Jahr>/` auf `/sites/DMS-Uebergabe`. Pfade mit Fragmenten aus `forbidden_path_fragments` (u. a. `/sites/Wissen`, `Mandantenbesonderheiten`, `OneDrive`) sind verboten. Existiert der Ordner noch nicht, per `sharepoint_create_folder` anlegen (erst Mandant, dann Jahr).

3. **Upload in fester Reihenfolge:**
   - Lane `upload`: **erst die Binärdatei, dann das Sidecar** hochladen (die Bridge triggert auf das Sidecar und erwartet die Datei bereits daneben).
   - Lane `manual`: **nur das Sidecar** hochladen und dem Nutzer wörtlich mitteilen, in welchen Ordner er die Datei manuell legen muss (Link aus `folder_path`); die Bridge wartet bis zu 72 h und prüft die SHA-256.
   - Fortschreibung (gleiches Dokument, neuer Stand, z. B. Bescheidreview derselben Bescheidfamilie): **denselben Dateinamen** und `conflictBehavior=replace` verwenden — nie `rename`, sonst entsteht im DMS eine Dublette statt einer Revision.

4. **Rückmeldung an den Nutzer:** Nach dem Upload sinngemäß bestätigen: „Dokument und Metadaten in der Übergabebibliothek abgelegt (`<Pfad>`). Die DMS-Ablage erfolgt automatisch innerhalb weniger Minuten; Status und DMS-Dokumentnummer erscheinen am Dokument in der Bibliothek (Spalte StatusDMS).“
   - **Niemals behaupten**, das Dokument sei bereits im DMS, SharePoint-Spalten seien gesetzt oder ein Status stehe fest — das erledigt allein die Bridge.
   - Auf Wunsch später den Status prüfen: Item per `sharepoint_search`/Ordnerpfad aufrufen und die Spalten `StatusDMS`/`FehlerText` wiedergeben; bei `Fehler` den `FehlerText` erklären und die Korrektur (meist Sidecar berichtigen und erneut hochladen) anbieten.

## Harte Regeln

- Mandantennummer nur 5-stellig numerisch; bei Unsicherheit nachfragen, nie aus Namen/Steuernummern ableiten.
- Nur Dokumenttypen aus dem Katalog; unbekannter Typ = Rückfrage, nicht raten (die Bridge lehnt unbekannte Typen ab).
- Keine Uploads außerhalb von `DMS_Uebergabe/<Mandant>/<Jahr>/`.
- Sidecar-Inhalte nie von Hand schreiben — immer `build_uebergabe_meta.py` verwenden (Schema + Hash).
- Dieser Skill löscht nichts und überschreibt nur bei bewusster Fortschreibung (replace).

## Referenzen

- `references/METADATEN_KONTRAKT.md` — Felder, Dokumenttyp-Katalog, Statusmaschine
- `references/uebergabe.schema.json` — maschinenlesbarer Kontrakt (Version 1.0)
