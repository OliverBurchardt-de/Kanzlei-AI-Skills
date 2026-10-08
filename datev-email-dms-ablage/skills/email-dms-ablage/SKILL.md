---
name: email-dms-ablage
description: Immer bei Aufträgen zur Ablage, Archivierung oder Verarbeitung von ein- und ausgehenden E-Mails in DATEV DMS über Riecken mCO verwenden. Pflicht: Original-EML samt Anhängen, Ablage-Knigge, Abkürzungen, Status und Rücklesekontrolle.
---

# E-Mail-Ablage DATEV-DMS — verbindlicher Standard

## Aktivierung
**Bei jeder beauftragten E-Mail-Ablage** (Ein- und Ausgang, einzelne Nachrichten oder ganze Korrespondenz) diesen Workflow automatisch anwenden. Der Skill ist eine Anweisung, kein neuer EML-Export-Connector. Eine Plugin-Installation allein gewährleistet keine globale Ausführung außerhalb zugänglicher ChatGPT-Workflows.

## Quellen und Reihenfolge
1. Inhalt und Kontext aus freigegebenem Microsoft Outlook-Connector holen. Exakte Nachricht und Anhänge ermitteln; Eingang und Ausgang getrennt berücksichtigen.
2. Vollständiges **Original-EML (RFC 5322/MIME)** einschließlich der technischen Header, Nachrichtentext, HTML, eingebetteten und regulären Anhänge über einen tatsächlich verfügbaren, freigegebenen Exportweg erhalten. Kein rekonstruiertes EML aus Ausschnitten; keine TXT-, PDF- oder HTML-Datei als EML ausgeben. Keine frei erfundenen technischen Header.
3. Wenn der freigegebene Outlook-Connector keinen vollständigen MIME-Export liefert: **nicht als Ersatz TXT ablegen**; technische Blockade transparent melden. Original in Outlook erhalten, nicht löschen. Ein zulässiger Exportweg muss ergänzt werden. Unvollständiges EML nur bei separater ausdrücklicher Freigabe als solche kennzeichnen, niemals als Original.
4. DATEV-Mandant anhand Nachrichtentext, Absender, bisheriger Korrespondenz, Mandantenstammdaten bestimmen. Verwechslungen zwischen Privat, Praxis, GmbH usw. vermeiden. Bei mehreren möglichen Mandanten: erst eindeutig zuordnen.
5. Art/Thema/Inhalt semantisch bestimmen. Den **gesamten** Knigge in `references/ablage-knigge.csv` nach `Bezeichnung` und `Ergaenzung` durchsuchen; `references/abkuerzungen.csv` interpretiert Präfixe (`BaM`, `BvM`, `BaFA`, `BvFA` usw.). Auch die Richtung beachten: `Ba`=an, `Bv`=von. Passenden `KniggeId`, `Dokumentklasse`, `Bereich`, `Ordner`, `Register`, `Status` ermitteln. Die Einträge sind konkrete Zuordnungsregeln, keine pauschale Sortierung nach Absender. Spezialregel geht vor Generik. Bei fehlender eindeutiger Übereinstimmung nicht willkürlich eine Kategorie wählen; einschlägige generische Knigge-Regel nur dann einsetzen, wenn sachlich zutreffend.
6. Die in der Excel-Referenz enthaltenen IDs sind **Hinweise**, nicht blind als aktuelle API-IDs benutzen. Mit `datev_lookup_dms_structure({type:'structure',domain:...})` den aktuellen Ablagebaum abfragen und korrekte `domain_id`, `folder_id`, `register_id` verwenden. `KniggeId` selbst wird vom DMS-Connector ggf. nicht unterstützt: **nicht** an ein nicht unterstütztes Feld übergeben; semantisch passende Ordner-/Register-ID setzen.
7. Für abgeschlossene Korrespondenz Bearbeitungsstatus ausdrücklich `erledigt`, für noch zu bearbeitende Unterlagen ausdrücklich `offen` setzen. Bei widersprechender Knigge-Vorgabe aktuellen Bearbeitungszustand prüfen; besondere vom Nutzer benannte Statusvorgabe hat Vorrang. Eingangs- und Ausgangsnachricht getrennt als Original-EML ablegen; Betreff, Richtung, Datum, Name in Titel.
8. Den freigegebenen Riecken mCO DMS-Connector `datev_prepare_document_filing` für die tatsächliche EML-Datei verwenden. Nutzeraussage zur Ablage ist Auftrag und Freigabe; ggf. notwendige Plan-Ausführung nur unter vorhandener ausdrücklicher Freigabe. Falls technisch keine Dateiquelle existiert, nicht so tun, als sei archiviert.
9. Nach `datev_execute_change_plan` **jede** zurückgegebene Dokument-ID mit `datev_get_document` erneut öffnen. Mandant/Korrespondenzpartner, Bereich/Ordner/Register (soweit aus API auslesbar), Dateiendung `EML`, dokumentierte Anhänge, Status `offen`/`erledigt`, Jahr und Monat prüfen. Wenn die API Ablageordner nicht ausgibt: mit gezielter DMS-Suche/Strukturdaten verifizieren; fehlende Prüfung ausdrücklich kennzeichnen.
10. Erst **nach nachweislich vollständiger und richtiger Ablage** und ausschließlich bei expliziter Löschanweisung Outlook-Eingang in `deleteditems` verschieben. Ausgangsnachrichten nur auf ausdrückliche Weisung löschen. Bei Teilfehlern Original unbedingt erhalten.

## Qualitätsgrenzen
- Niemals behaupten, vollständige EML archiviert zu haben, wenn nur Text extrahiert wurde.
- Keine TXT-Fallbacks, keine stillen Anhangauslassungen, keine generische Default-Ablage statt der Knigge-Regel.
- Bei Auftrag zur gemeinsamen Ablage immer beide E-Mails **separat** protokollieren: Original-EML vorhanden, Anhänge enthalten, Zuordnung mit KniggeId, tatsächlicher DMS-Ordner/Register, Status, Dokument-ID und Rückleseergebnis.
- Bereits unzulänglich abgelegte TXT-Kopien erst nach kontrollierter Original-EML-Ablage und separater Löschfreigabe ersetzen/löschen.

## Referenzdateien
`references/ablage-knigge.csv`: Übertragung des Tabellenblatts `Knigge` aus der Datei `Ablage-Knigge(1).xlsx` inklusive Zuordnung und Metadaten.
`references/abkuerzungen.csv`: zweite Tabelle `Abkürzungen`.  Beides als Originalregelbestand beibehalten und bei Änderung der Kanzleistruktur versionieren.
