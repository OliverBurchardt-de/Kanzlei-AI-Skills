# Metadaten-Kontrakt der DMS-Übergabe (Version 1.0)

Führende Definition: `uebergabe.schema.json` (Kopie des zentralen Kontrakts aus `dms-automation/bridge-worker/schemas/`; bei Änderungen beide Stellen synchron halten — die Bridge validiert gegen ihre Kopie).

## Prinzip

Pro Dokument werden **zwei Dateien** in die Übergabebibliothek gelegt:

```
<Mandantennummer>/<Jahr>/<Datei>            z. B. 10002/2025/Bescheidreview_Bemelmans_KSt_2025_2026-08-07.xlsx
<Mandantennummer>/<Jahr>/<Datei>.dms.json   Metadaten-Begleitdatei (Sidecar)
```

Die Bridge verarbeitet **nur vollständige Paare**. Das Sidecar ist die Quelle der Wahrheit; SharePoint-Spalten werden von der Bridge gespiegelt und dürfen vom Agenten nie als gesetzt behauptet werden.

## Felder

| Feld | Pflicht | Inhalt |
|---|---|---|
| `contract_version` | ja | konstant `"1.0"` |
| `mandanten_nr` | ja | 5-stellige DATEV-Mandantennummer als String, z. B. `"10002"` |
| `jahr` | ja | Veranlagungszeitraum/Wirtschaftsjahr, Integer 2000–2099 |
| `monat` | nein | 1–12 oder `null` (Monatsbuchhaltung) |
| `dokumenttyp` | ja | Schlüssel aus dem Dokumenttyp-Katalog (unten) |
| `beschreibung` | ja | DMS-Beschreibung, max. 255 Zeichen, aussagekräftig |
| `stichworte` | nein | kommagetrennt, max. 255 Zeichen, oder `null` |
| `datei_name` | ja | exakt der Name der Binärdatei inkl. Endung |
| `sha256` | ja | SHA-256 der Binärdatei, lowercase hex |
| `datei_groesse_bytes` | ja | Dateigröße in Bytes |
| `quelle_skill` | ja | erzeugender Skill, z. B. `bescheid-review` |
| `erstellt_am` | ja | ISO 8601 mit Zeitzonen-Offset |
| `binary_delivery` | ja | `upload` (Datei liegt daneben) oder `manual` (Datei > 900 KiB, kommt manuell) |
| `update_von_dms_guid` | nein | GUID eines fortzuschreibenden DMS-Dokuments oder `null` (Normalfall: die Bridge erkennt Fortschreibungen selbst über den Dateipfad) |

## Dokumenttyp-Katalog (muss mit `mapping.yaml` der Bridge übereinstimmen)

| Schlüssel | Inhalt | DMS-Ziel (Bereich Mandanten) |
|---|---|---|
| `bescheidreview_arbeitspapier` | Bescheidreview-Excel aus bescheid-review | Steuerakte / Steuerbescheide |
| `abschlussreview_arbeitspapier` | Review-Excel aus abschluss-review | Jahresabschluss / Arbeitspapiere zum Jahresabschluss |
| `fibu_pruefprotokoll` | Prüfprotokoll/Buchungsprüfung aus bk-monatsbuchhaltung | Finanzbuchhaltung / Arbeitspapiere FiBu |
| `fibu_klaerungsfaelle` | Klärungsfälle-Dokumentation | Finanzbuchhaltung / Unterlagen zur Mandantenabstimmung |
| `jahresabschluss_dokument` | sonstige JA-Dokumente | Jahresabschluss / Mandanteninformationen |
| `steuerakte_korrespondenz` | Korrespondenz mit Steuerbezug | Steuerakte / Korrespondenz |

Neue Dokumenttypen: erst in `dms-automation/bridge-worker/mapping.example.yaml` (und der produktiven `mapping.yaml`) ergänzen, dann hier und in der SharePoint-Auswahlspalte nachziehen.

## Statusmaschine (nur die Bridge schreibt Status)

`Neu` (Upload) → `InVerarbeitung` → `Abgelegt` (mit `DMSDokumentNr`, `DMSDokumentGUID`, `VerarbeitetAm`, `VerarbeiteterHash`) oder `Fehler` (mit `FehlerText`; nach Korrektur von Datei/Sidecar verarbeitet der nächste Lauf das Item erneut).
