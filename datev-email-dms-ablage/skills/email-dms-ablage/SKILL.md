---
name: email-dms-ablage
description: Immer bei Aufträgen zur Ablage, Archivierung oder Verarbeitung von ein- und ausgehenden E-Mails in DATEV DMS über den Microsoft-Outlook-Connector und Riecken mCO verwenden. Pflicht: Original-EML samt Anhängen, soweit verfügbar; bei ausdrücklicher Nutzerfreigabe auch klar gekennzeichnete rekonstruierte EML. Immer Ablage-Knigge, Status und Rücklesekontrolle beachten. Tatsächliche Dateiübergabe an Riecken mCO und Rücklesekontrolle mit Dokument-ID.
---

# E-Mail-Ablage DATEV-DMS — verbindlicher Standard (v1.2.0)

## Aktivierung
Bei jeder beauftragten E-Mail-Ablage (Eingang und Ausgang, einzelne Nachrichten oder ganze Korrespondenz) diesen Workflow automatisch anwenden. Die Nutzeraussage zur Ablage ist Auftrag und Freigabe für Abruf, Original-EML, Dateiübergabe und Ausführung des Change-Plans. Sie ist keine Freigabe für eine rekonstruierte EML; dafür ist eine ausdrückliche, gesonderte Freigabe des Nutzers erforderlich (Abschnitt 2). Bei eindeutigem Arbeitsauftrag keine weiteren Rückfragen stellen. Rückfrage nur, wenn der Mandant nicht eindeutig bestimmbar ist oder mehrere Knigge-Regeln gleich gut passen. Für die rekonstruierte EML besteht eine stehende Freigabe (Abschnitt 2 Nr. 2); dafür nie nachfragen.

Startnachweis sinngemäß ausgeben und danach selbstständig weiterarbeiten:
`Startnachweis: email-dms-ablage v1.2.0 | Quelle Outlook-Connector | Original-EML vorrangig, Rekonstruktion nur mit Freigabe | Knigge-Zuordnung | Status explizit | Dateiübergabe geprüft | Rücklesekontrolle mit Dokument-ID`

## Werkzeuge
- Outlook: `outlook_email_search` (Nachricht finden), `read_resource` mit `mail:///messages/{id}` (Kopfdaten, HTML-Text, Anhangsliste), `read_resource` mit der Anhang-URI (liefert die Anhangsdatei auf die Festplatte), `outlook_batch_delete_messages` (verschiebt einzelne Nachrichten nach „Gelöschte Elemente“). `outlook_trash_thread` nicht verwenden, es löscht den gesamten Thread.
- Riecken mCO: `datev_search_clients`, `datev_lookup_dms_structure` (`type=structure` mit `domain`, `type=states`), `datev_prepare_document_filing`, `datev_execute_change_plan` mit `application="dms"`, `datev_get_document`, `datev_read_document`.
- Skript: `scripts/build_eml.py` erzeugt aus den Connector-Daten eine RFC-5322/MIME-konforme EML (siehe Abschnitt 2).

## 1. Nachricht abrufen
1. Nachricht über `outlook_email_search` eindeutig bestimmen (Absender, Betreff, Datum). Bei mehreren Treffern die Message-ID und das Datum vergleichen; nie die falsche Nachricht ablegen.
2. Vollständige Nachrichtendaten mit `read_resource` holen: Absender, alle Empfänger (To, Cc, Bcc), Betreff, `sentDateTime`, `receivedDateTime`, `internetMessageId`, `conversationId`, HTML- oder Text-Body, Anhangsliste mit Name, Typ, Größe, `isInline`.
3. Jeden Anhang (regulär und eingebettet) über seine Anhang-URI mit `read_resource` abrufen. Bilder (PNG, JPG, GIF) liefert der Connector als Datei im Werkzeugergebnis-Verzeichnis; sie mit ihrem Originalnamen in ein Arbeitsverzeichnis kopieren. Die vom Connector gemeldete `size` enthält Kodierungs-Overhead und weicht von der Dateigröße ab; das ist keine Abweichung des Inhalts.
   **Bekannte Grenze (Stand 09.10.2026):** Für PDF- und sonstige Dokumentanhänge liefert der Microsoft-365-Connector keine Dateibytes. Bei `application/pdf` kommt nur der extrahierte Text zurück, bei `application/octet-stream` die Antwort „Binary attachment — content cannot be returned inline“. Solche Anhänge können nicht in die EML übernommen werden. Dann: EML mit `--allow-missing` erzeugen, den Anhang in `X-BK-Missing-Attachments`, im DMS-Titel (`[rekonstruierte EML, Anhang fehlt]`) und in der DMS-Notiz mit Name, Typ, Größe und Grund ausweisen, die Nachricht in Outlook erhalten und im Protokoll als unvollständig bezeichnen. Den vom Connector extrahierten Text des Anhangs darf die Notiz als „Inhalt laut Textextraktion“ wiedergeben; er ersetzt den Anhang nicht. Ist der Anhang das eigentliche Dokument (Rechnung, Bescheid, Vertrag), den Nutzer darauf hinweisen, dass die Datei selbst über einen anderen Weg ins DMS muss (z. B. Upload-Link von Riecken im Browser).
4. Eingang und Ausgang getrennt behandeln. Zu einem Thread gehörende Ausgangsnachrichten nur ablegen, wenn der Auftrag sie umfasst.

## 2. EML erzeugen
1. **Vorrang Original-EML.** Vollständiges Original-EML (RFC 5322/MIME) einschließlich technischer Header, Nachrichtentext, HTML sowie eingebetteter und regulärer Anhänge über einen tatsächlich verfügbaren, freigegebenen Exportweg bevorzugen. Liefert der Connector solche Daten, diese unverändert als EML verwenden; dann wird ausschließlich die Original-EML abgelegt. Keine TXT-, PDF- oder HTML-Datei lediglich mit der Endung `.eml` ausgeben. Der Microsoft-365-Connector liefert derzeit keine Original-MIME-Daten, sondern strukturierte Felder.
2. **Ohne Original-MIME: Nutzer informieren, Original erhalten.** Liefert der Connector keinen vollständigen MIME-Export, die Nachricht in Outlook unverändert erhalten und im Protokoll vermerken, dass eine rekonstruierte EML entsteht. Eine allgemeine Ablageanweisung allein genügt als Freigabe nicht; eine Freigabe liegt vor, wenn der Nutzer die Rekonstruktion im Auftrag oder als stehende Regel ausdrücklich zugelassen hat.
   **Stehende Freigabe:** Der Nutzer (Oliver Burchardt) hat am 09.10.2026 die rekonstruierte EML generell freigegeben („Rekonstruierte EML ist freigegeben“). Diese Freigabe gilt für alle Ablagen über den Microsoft-365-Connector, bis sie widerrufen wird. Deshalb **keine Nachfrage je E-Mail**; in der DMS-Notiz und im Protokoll als „stehende Freigabe vom 09.10.2026“ dokumentieren. Nur wenn der Nutzer die Freigabe widerruft oder für einen Auftrag ausdrücklich Original-EML verlangt, gilt Nr. 3.
3. **Ohne Freigabe: Blockade melden, nicht ablegen.** Liegt keine ausdrückliche Freigabe vor, keine rekonstruierte EML erstellen, die technische Blockade transparent melden (Connector, fehlende Exportfunktion) und keine Ablage als Original-EML behaupten. Das ist kein stiller Abbruch, sondern eine Rückmeldung mit der Frage nach Freigabe.
4. **Mit Freigabe: valide MIME-EML rekonstruieren** mit `scripts/build_eml.py`:
   - Eingabe-JSON mit den Feldern aus `read_resource` (Beispiel im Skript-Docstring). Alle tatsächlich verfügbaren Nachrichteninhalte und Anhänge vollständig übernehmen; Anhänge über `--attachments-dir` einbinden, eingebettete Bilder mit `Content-Disposition: inline`.
   - Vorhandene Absender-, Empfänger-, Betreff- und Zeitangaben verwenden (From, To, Cc, Subject, Date aus `sentDateTime`, Message-ID aus `internetMessageId`). Keine nicht bekannten technischen Header oder Message-IDs als Originaldaten ausgeben; das Skript setzt keine Received-, Return-Path-, DKIM- oder sonstigen Transportheader. Fehlt die Message-ID, erzeugt das Skript eine lokale Kennung unter `reconstructed.invalid` und vermerkt das im Header.
   - Das Skript setzt die Header `X-Reconstructed-EML: yes` und `X-BK-EML-Source: reconstructed-from-graph`, listet enthaltene Anhänge in `X-BK-Included-Attachments` und stellt dem Nachrichtentext (Text- und HTML-Teil) den Hinweis „Rekonstruierte EML; keine durch Outlook exportierte Original-MIME-Datei“ voran. Der gelieferte HTML-Inhalt folgt danach unverändert. Ein `text/plain`-Teil wird aus dem HTML abgeleitet und mit `X-BK-Derived` gekennzeichnet.
   - Dateiname und DMS-Titel mit „rekonstruierte EML“ kennzeichnen, z. B. `2026-10-08_AW_Kuendigung_taxmaro_rekonstruierte-EML.eml`.
   - Derselbe Hinweis gehört in die DMS-Notiz, zusammen mit Freigabe des Nutzers (Wortlaut oder Datum), Datenquelle (Microsoft-365-Connector, Nachrichten-ID), enthaltenen Anhängen und nicht verfügbaren Anhängen.
5. EML nach dem Erzeugen lokal prüfen: mit Python `email.parser` (policy `strict`) parsen, Struktur ausgeben, jeden Anhang byteweise mit der Quelldatei vergleichen. Bei Abweichung nicht weiterarbeiten.
6. Fehlt ein Anhang (Abruf nicht möglich), bricht das Skript ab. Nur mit `--allow-missing` weiterarbeiten; die fehlenden Teile stehen dann in `X-BK-Missing-Attachments` und müssen in die DMS-Notiz. Fehlende Anhänge nie ersetzen oder fingieren.
7. Lässt der Übertragungsweg (Abschnitt 3) die vollständige Datei nicht zu, dürfen Anhänge nur mit `--omit-attachments` und `--omit-reason` weggelassen werden. Reihenfolge: zuerst eingebettete Signaturgrafiken ohne Sachinhalt, nie Anhänge mit Sachinhalt (Rechnungen, Verträge, Bescheide). Weggelassene Anhänge stehen in `X-BK-Omitted-Attachments` und müssen in die DMS-Notiz.
8. **Bezeichnung.** Eine rekonstruierte EML darf nie als Original-EML bezeichnet werden. Wurden alle verfügbaren Nachrichtendaten und Anhänge übernommen, darf sie als „inhaltlich vollständig aus den verfügbaren Outlook-Daten rekonstruiert“ bezeichnet werden, nicht als technische Originaldatei. Wurden Anhänge weggelassen oder fehlen sie, ist sie als unvollständig zu bezeichnen.

## 3. Dateiübergabe an Riecken mCO
`datev_prepare_document_filing` nimmt die Datei auf genau einem dieser Wege an, in dieser Reihenfolge prüfen und den ersten technisch funktionierenden Weg verwenden:
1. `file` (native Dateiübergabe des Clients, z. B. Langdock) oder `chat_files` (ChatGPT): nur wenn der Client die Felder selbst befüllt. Nicht von Hand befüllen.
2. `upload_id`: Aufruf ohne Dateiquelle liefert `upload_url` (Browser) und `upload_url_api` (programmatisch). Ist `upload_url_api` aus der Laufzeitumgebung erreichbar, die EML dorthin hochladen und danach mit `upload_id` ablegen. In der Claude-Cloud-Umgebung ist der Host `datev-mcp.riecken.io` durch die Netzwerkrichtlinie gesperrt (HTTP 403 am Proxy); dann ist dieser Weg nur über den Nutzer (Browser-Upload) möglich. Ein Upload-Link ist kein abgeschlossener Ablagevorgang; er wird dem Nutzer wörtlich weitergegeben, und die Ablage läuft erst nach dessen Upload mit `upload_id` weiter.
3. `content_base64` mit `file_name` (Endung `.eml`): die Bytes der lokal erzeugten und geprüften EML Base64-kodiert übergeben. Nachweislich funktionierend bis rund 30 KB (Testlauf 08.10.2026, 30.359 Bytes). Größere Dateien zuerst versuchen; lehnt der Connector ab, nach Abschnitt 2 Nr. 5 verfahren oder den Upload-Link an den Nutzer geben.
Nie Dateiinhalte raten oder erfinden; nur Bytes übergeben, die tatsächlich lokal vorliegen. Die Antwort enthält `upload.size_bytes`; dieser Wert muss der lokalen Dateigröße entsprechen, sonst Change-Plan verwerfen (`datev_cancel_change_plan`).
Existiert kein funktionierender Übertragungsweg, die konkrete Blockade (Tool, Fehlermeldung, Host) dokumentieren und keine Ablage melden.

## 4. Mandant und Ablage-Knigge
1. Mandant über `datev_search_clients` bestimmen (Nummer, Name, E-Mail-Adresse oder Domain). Bei mehreren Kandidaten (Privat, Praxis, GmbH) zuerst eindeutig zuordnen; Nachrichtentext, Absender, bisherige Korrespondenz heranziehen. Mandantennummer und UUID im Protokoll festhalten.
2. Art, Thema und Richtung der Nachricht semantisch bestimmen. Den gesamten Knigge in `references/ablage-knigge.csv` nach `Bezeichnung` und `Ergaenzung` durchsuchen; `references/abkuerzungen.csv` interpretiert die Präfixe (`Ba`=Brief an, `Bv`=Brief von, `BaM`/`BvM` Mandant, `BaFA`/`BvFA` Finanzamt usw.). Passenden `KniggeId`, `Dokumentklasse`, `Bereich`, `Ordner`, `Register`, `Status` ermitteln. Spezialregel vor generischer Regel. Keine pauschale Standardablage, wenn eine konkrete Zuordnungsregel existiert. Fehlt eine eindeutige Übereinstimmung, die sachlich zutreffende generische Regel wählen (z. B. `10041 Sonstige Korrespondenz` für Korrespondenz mit Dritten ohne Spezialregel) und die Entscheidung im Protokoll begründen.
3. Die IDs im Knigge sind Hinweise. Vor jeder Ablage `datev_lookup_dms_structure({type:"structure", domain:"Mandanten"})` aufrufen und die aktuellen `domain_id`, `folder_id`, `register_id` verwenden. In `datev_prepare_document_filing` reicht `register_id`; Ordner und Ablage werden daraus abgeleitet. `KniggeId` nicht an den Connector übergeben; er unterstützt das Feld nicht. KniggeId in `keywords` und `note` dokumentieren.
4. Beschreibung nach Knigge-Muster: `{Knigge-Bezeichnung}: E-Mail von/an {Partner} ({Adresse}) vom {Datum} – {Betreff}`; bei Rekonstruktion mit dem Zusatz `[rekonstruierte EML]`. Betreff, Richtung, Datum, Name und Rekonstruktionsstatus stehen damit im Titel. Jahr und Monat aus dem Versanddatum setzen (`year`, `month`), `receipt_date` auf das Versanddatum.

## 5. Bearbeitungsstatus
Bei jedem Ablageaufruf `state` ausdrücklich setzen, als Name oder ID aus `datev_lookup_dms_structure({type:"states"})`: `erledigt` (ID 6) für abgeschlossene Korrespondenz, `offen` (ID 5) für noch zu bearbeitende Unterlagen. Keine stillschweigende Übernahme eines Standardstatus. Reihenfolge: ausdrückliche Vorgabe des Nutzers, dann tatsächlicher Bearbeitungsstand, dann Knigge-Spalte `Status`.

## 6. DMS-Ablage ausführen
Eingangs- und Ausgangsnachricht getrennt als Original-EML ablegen; bei ausdrücklich freigegebener Rekonstruktion jeweils als klar gekennzeichnete rekonstruierte EML. Für jede E-Mail getrennt:
1. Original-EML verwenden oder, nur mit Freigabe, EML rekonstruieren (Abschnitt 2).
2. Dateiübergabe nach Abschnitt 3.
3. `datev_prepare_document_filing` mit `client`, `description`, `document_class="dokument"`, `register_id`, `state`, `year`, `month`, `receipt_date`, `keywords`, `note` und der Dateiquelle aufrufen. Die `note` enthält: Richtung (Eingang/Ausgang), „Original-EML“ oder „Rekonstruierte EML; keine durch Outlook exportierte Original-MIME-Datei“, bei Rekonstruktion die Freigabe des Nutzers und die Datenquelle, enthaltene Anhänge, weggelassene oder fehlende Anhänge mit Grund, KniggeId, Outlook-Message-ID.
4. Den zurückgegebenen `diff` gegen Mandant, Ablage/Ordner/Register, Status, Jahr/Monat und Dateiname prüfen. `upload.size_bytes` mit der lokalen Dateigröße abgleichen.
5. `datev_execute_change_plan` mit `change_plan_id`, `confirmation_token` und `application="dms"` ausführen. Die Freigabe liegt im Ablageauftrag; eine zusätzliche Bestätigung ist nicht einzuholen, sofern der Nutzer das nicht ausdrücklich verlangt.
6. Die zurückgegebene `documentId` speichern und im Protokoll festhalten.

## 7. Rücklesekontrolle (Pflicht)
Nach jeder Ablage `datev_get_document` mit der tatsächlichen `documentId` aufrufen und prüfen:
- `correspondence_partner_guid` = UUID des Mandanten aus `datev_search_clients`
- `domain`, `folder`, `register` = Knigge-Zuordnung
- `extension` = `EML`
- bei Rekonstruktion: Kennzeichnung „rekonstruierte EML“ in `description`, Dateiname und `note` vorhanden
- `structure_items` enthält die Datei mit Name `.eml` und `size` = lokale Dateigröße
- `state` = `offen` oder `erledigt` wie beauftragt
- `description`, `keywords`, `note` wie übergeben, einschließlich dokumentierter Einschränkungen
- `year`, `month`, `receipt_date`
Zusätzlich `datev_read_document` mit der `document_id` aufrufen, um Kopfdaten und Text aus der gespeicherten Datei zu bestätigen. Meldet Riecken `Der Mail-Parser ist mit einem Fehler geendet.`, ist das kein Ablagefehler, wenn `datev_get_document` die Datei mit korrekter Größe zeigt; die Datei dann über einen zweiten Weg prüfen (z. B. Klardaten `datev_dms_get` mit `datev://dms/document_files` und `datev_prepare_attachment`, Ergebnis byteweise mit der lokalen EML vergleichen) und das Ergebnis protokollieren. Schlägt eine Prüfung fehl, keine Erfolgsmeldung ausgeben, Abweichung benennen.

## 8. Outlook-Löschung
Nur bei ausdrücklicher Löschanweisung des Nutzers:
1. DMS-Ablage vollständig abschließen (Abschnitt 6).
2. Rücklesekontrolle mit der Dokument-ID bestehen (Abschnitt 7).
3. Erst danach die ursprüngliche Nachricht mit `outlook_batch_delete_messages` und ihrer Message-ID nach „Gelöschte Elemente“ verschieben (wiederherstellbar). Ausgangsnachrichten nur auf ausdrückliche Weisung. Ganze Threads nie löschen.
Bei fehlgeschlagener oder unvollständig geprüfter Ablage bleibt die Nachricht in Outlook.

## 9. Verbotene Verhaltensweisen
- Kein stiller Abbruch wegen fehlender Original-MIME-Exportfunktion: Nutzer informieren und Freigabe für die Rekonstruktion einholen.
- Keine rekonstruierte EML ohne ausdrückliche Nutzerfreigabe; eine allgemeine Ablageanweisung genügt nicht. Die stehende Freigabe vom 09.10.2026 erfüllt diese Anforderung; keine wiederholte Nachfrage.
- Keine TXT-, PDF- oder HTML-Datei als angebliche EML.
- Keine erfundenen Original-Header oder Anhänge.
- Keine rekonstruierte EML als Original-EML bezeichnen; Kennzeichnung in Header, Nachrichtentext, Dateiname, DMS-Titel und DMS-Notiz ist Pflicht. In Rückmeldung und Protokoll immer zwischen „Original-EML“ und „rekonstruierte EML“ unterscheiden.
- Keine stillen Anhangauslassungen; weggelassene oder fehlende Teile stehen in Header und Notiz.
- Keine generische Standardablage, wenn eine Knigge-Regel passt.
- Keine Löschung vor bestätigter Ablage und bestandener Rücklesekontrolle.
- Keine Erfolgsmeldung ohne Rücklesekontrolle mit Dokument-ID.
- Kein Upload-Link als „archiviert“ melden.
- Keine unnötigen Rückfragen bei eindeutigem Arbeitsauftrag.

## 10. Protokoll je E-Mail
Am Ende je Nachricht ausgeben: Richtung, Absender/Empfänger, Betreff, Datum, Mandant (Nummer), KniggeId und Regel, Ablage/Ordner/Register, Status, Dateiname und Größe, „Original-EML“ oder „rekonstruierte EML“ (bei Rekonstruktion: Freigabe des Nutzers, Datenquelle, Bezeichnung „inhaltlich vollständig aus den verfügbaren Outlook-Daten rekonstruiert“ oder „unvollständig“), enthaltene, weggelassene und nicht verfügbare Anhänge, Übertragungsweg, DMS-Dokumentnummer und Dokument-ID, Ergebnis der Rücklesekontrolle, Outlook-Löschung ja/nein.

## Referenzdateien
`references/ablage-knigge.csv`: Übertragung des Tabellenblatts `Knigge` aus der Datei `Ablage-Knigge(1).xlsx` inklusive Zuordnung und Metadaten.
`references/abkuerzungen.csv`: zweite Tabelle `Abkürzungen`. Beides als Originalregelbestand beibehalten und bei Änderung der Kanzleistruktur versionieren.
`scripts/build_eml.py`: EML-Erzeugung aus Connector-Daten (Abschnitt 2).
