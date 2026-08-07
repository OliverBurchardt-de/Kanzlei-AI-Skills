# Einrichtungs-Checkliste SharePoint + Entra (manuell oder per PnP)

## A. Site anlegen (SharePoint-Admin)

- [ ] Teamsite **ohne** M365-Gruppe anlegen: Name `DMS-Uebergabe`, URL `/sites/DMS-Uebergabe`, Sprache Deutsch.
- [ ] Externes Teilen für die Site deaktivieren.
- [ ] Mitgliederpflege: Kanzlei-Mitarbeitergruppe als „Mitglieder“ (Beitragen), Administratoren als „Besitzer“.

## B. Bibliothek provisionieren

Entweder PnP (empfohlen, reproduzierbar):

```powershell
Install-Module PnP.PowerShell -Scope CurrentUser
Connect-PnPOnline -Url "https://burchardtkollegen.sharepoint.com/sites/DMS-Uebergabe" -Interactive
Invoke-PnPSiteTemplate -Path .\DMS_Uebergabe.pnp.xml
```

Oder manuell gemäß `../BIBLIOTHEK_SPEZIFIKATION.md`:

- [ ] Bibliothek `DMS_Uebergabe` anlegen, Versionierung aktiv (50 Hauptversionen).
- [ ] Spalten anlegen: Mandantennummer, Jahr, Dokumenttyp (Auswahl), Beschreibung, QuelleSkill, StatusDMS (Auswahl, Default `Neu`), FehlerText, DMSDokumentNr, DMSDokumentGUID, VerarbeitetAm, VerarbeiteterHash.
- [ ] Ansichten `Offen`, `Fehler`, `Abgelegt` anlegen (Filter siehe Spezifikation).
- [ ] Spalten **nicht** als Pflichtfelder markieren (sonst blockieren Uploads ohne Eigenschaften).

## C. Entra-App „DMS-Bridge“ (Entra-Admin)

- [ ] App-Registrierung `DMS-Bridge` anlegen (kein Redirect-URI nötig).
- [ ] API-Berechtigung: Microsoft Graph → Anwendung → `Sites.Selected` → Admin-Zustimmung erteilen.
- [ ] Client Secret erzeugen (Laufzeit 12–24 Monate; Ablauf im Kalender vermerken!).
- [ ] Der App Schreibzugriff **nur** auf die Site geben (als SharePoint-Admin mit `Sites.FullControl.All`-berechtigtem Kontext bzw. PnP):

```powershell
# PnP-Variante
Grant-PnPAzureADAppSitePermission -AppId "<CLIENT-ID>" -DisplayName "DMS-Bridge" `
  -Site "https://burchardtkollegen.sharepoint.com/sites/DMS-Uebergabe" -Permissions Write
```

- [ ] Tenant-ID, Client-ID in `config.yaml` des Workers eintragen; Secret in den Windows Credential Manager des Worker-Hosts (`dms-bridge/graph`).

## D. Funktionsprobe (vor dem ersten Worker-Lauf)

- [ ] Als Mitarbeiter eine Testdatei in `10002/2025/` hochladen — Upload ohne Pflichtfeld-Dialog möglich?
- [ ] Mit dem App-Token per Graph `GET /sites/{host}:/sites/DMS-Uebergabe` und `GET .../drives` — Bibliothek sichtbar?
- [ ] `PATCH .../listItem/fields` auf das Testitem (StatusDMS=Neu) — Schreibrecht bestätigt?
- [ ] Testdatei wieder entfernen.
