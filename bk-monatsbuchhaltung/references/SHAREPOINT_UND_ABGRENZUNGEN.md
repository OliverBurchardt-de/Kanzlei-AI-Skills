# SharePoint und Abgrenzungen

## Zentrale Ablagekonfiguration

Für die derzeitige Kanzleiablage gelten:

- Hostname: `burchardtkollegen.sharepoint.com`
- Site: `/sites/Wissen`
- Dokumentbibliothek: `Mandantenbesonderheiten`
- Profilordner: `Mandantenprofile`
- Registerordner: `Abgrenzungsregister`

Aus der Mandantennummer deterministisch genau diese Ziele bilden:

- Bibliothekspfad `Mandantenprofile/<Mandantennummer>.md`
- Bibliothekspfad `Abgrenzungsregister/<Mandantennummer>.md`

Beispiel für Mandant 12861:

- Hostname: `burchardtkollegen.sharepoint.com`
- Site-Pfad: `/sites/Wissen`
- Dokumentbibliothek/Drive: `Mandantenbesonderheiten`
- Ordner: `Mandantenprofile`
- exakter Dateiname: `12861.md`

`Mandantenprofile` und `Abgrenzungsregister` sind Ordner innerhalb der Dokumentbibliothek `Mandantenbesonderheiten`, keine eigenständigen Bibliotheken.

## Verbindlicher direkter Abruf

Mandantenprofil zwingend in dieser Reihenfolge abrufen:

1. `scripts/sharepoint_target.py --mandant <Mandantennummer>` ausführen. URL und Pfad nicht selbst herleiten.
2. Die ausgegebene `profile_url` unverändert als erste SharePoint- oder Dateizugriffsaktion direkt abrufen. Der konkrete Connectorname darf je Oberfläche variieren; allgemeine Suche, DMS und lokale Ersatzdateien sind unzulässig.
3. Den Treffer nur akzeptieren, wenn `title` oder `file_name` exakt `<Mandantennummer>.md` lautet, `file_uri` vorhanden ist und `web_link` beziehungsweise `display_url` mit `profile_url` beginnt. Die zurückgegebene Rohdatei als UTF-8 lesen. `content: null` ist bei `.md` erwartbar und kein Anlass für eine andere Suche.
4. Nur wenn der exakte Abruf einen technischen Fehler oder `NOT_FOUND` zurückgibt, Host `/sites/Wissen` und Drive `Mandantenbesonderheiten` zur Fehlerdiagnose direkt validieren. Dabei niemals andere Sites, persönliche OneDrive-Bereiche oder die Standardbibliothek `Dokumente` durchsuchen.
5. Nach erfolgreicher Site-/Drive-Diagnose genau dieselbe exakte URL einmal erneut abrufen. Keine Stichwort-, Volltext- oder semantische Suche einschieben.

Für das Abgrenzungsregister gilt derselbe direkte Abruf mit dem Ordner `Abgrenzungsregister`. Anders als beim Mandantenprofil ist ein nach erfolgreicher Site-/Bibliotheksprüfung und wiederholtem Direktabruf eindeutig bestätigtes `itemNotFound` zulässig: Es bedeutet `Erstlauf ohne vorhandenes Register` und stoppt die Belegverarbeitung nicht.

Unzulässig sind:

- jeder allgemeine SharePoint- oder OneDrive-Suchschritt vor dem direkten Abruf der exakten URL,
- allgemeine SharePoint-Volltextsuche nach Mandantennummer oder Dateinamen,
- semantische Suche,
- Aufruf von persönlichen OneDrive-/`Kanzlei`-/`Mandanten`-Pfaden,
- Suche auf der Site „Burchardt & Kollegen“, im allgemeinen Teamspace, in `Documents`, `Dokumente`, `Teams Wiki Data` oder in einer anderen Bibliothek,
- Anforderung eines SharePoint-Links vom Benutzer, solange die fest hinterlegte exakte URL noch nicht direkt abgerufen wurde,
- Ableitung „Datei fehlt“ aus einer erfolglosen Stichwortsuche oder einer leeren Markdown-Textextraktion,
- Ausweichen auf einen lokalen Spiegel außerhalb eines ausdrücklich benannten lokalen Testmodus.

Ein Ergebnis aus `Kanzlei/Mandanten/<Mandant>` ist immer das Ergebnis eines falschen Abrufwegs. Es verwerfen, den Preflight nicht damit bewerten und den verbindlichen Direktabruf mit der vom Skript ausgegebenen `profile_url` ausführen.

## Fehlerklassifikation

`Mandantenprofil eindeutig nicht vorhanden` darf nur festgestellt werden, wenn:

- die exakte URL `.../Mandantenprofile/<Mandantennummer>.md` zuerst direkt abgerufen wurde,
- die Site `/sites/Wissen` anschließend erfolgreich aufgelöst wurde,
- die Bibliothek `Mandantenbesonderheiten` einschließlich ihrer `web_url` anschließend erfolgreich aufgelöst wurde und
- der wiederholte direkte Abruf genau derselben exakten URL eindeutig `itemNotFound` beziehungsweise `NOT_FOUND` zurückgibt.

Ein 404 beim bloßen Browsen von `folder_path="Mandantenprofile"` ohne die Identität des Drives `Mandantenbesonderheiten` ist kein Nachweis für eine fehlende Datei; dieser Aufruf kann gegen die Standardbibliothek laufen.

Kann Site, Bibliothek, Drive-URL oder exakte Datei-URL nicht eindeutig aufgelöst werden, lautet das Ergebnis `technischer SharePoint-Abruffehler`. Daraus darf weder geschlossen werden, dass das Mandantenprofil fehlt, noch dass kein Abgrenzungsregister besteht. Der Lauf stoppt, weil ein vorhandener Registerbestand sonst übergangen werden könnte. Keine Neuanlage und keine Profiländerung vorschlagen.

Wird die Datei eindeutig gefunden, aber die zurückgegebene Rohdatei kann nicht als UTF-8 gelesen werden, lautet das Ergebnis `technischer SharePoint-Lesefehler`. Eine leere Textextraktion allein ist ausdrücklich kein Lesefehler. Auch dann darf nicht behauptet werden, das Profil fehle.

## Mandantenprofil

Profil ausschließlich am exakt aufgelösten SharePoint-Ziel laden. Das Profil enthält nur mandantenspezifische Regeln, keine globalen DATEV-Felddefinitionen.

Wenn der SharePoint-Connector für eine Markdown-Datei keinen extrahierten Text liefert, dieselbe eindeutig gefundene Datei als Rohdatei herunterladen und UTF-8 lesen. Das ist der vorgesehene Fallback und kein fachlicher Fehler.

### Kontrollierter Erstlauf ohne vorhandenes Profil

Ein technischer Connector-, Datei- oder UTF-8-Lesefehler blockiert weiterhin. Nur wenn Site und Bibliothek erfolgreich bestätigt wurden und der zweite direkte Abruf der exakten Profil-URL erneut eindeutig `itemNotFound` liefert, ist `provisional_first_run` zulässig.

Vor der Belegverarbeitung ein vollständiges vorläufiges Profil aus der bestehenden Profilvorlage erstellen. Ausschließlich live gelesene DATEV-Daten, ausdrückliche Nutzerangaben und belastbare Belegmerkmale verwenden. Jede abgeleitete Regel als vorläufig kennzeichnen und ihre Quelle nennen. Im Paket sichtbar ausweisen: `Mandantenprofil-Status: vorläufig – Freigabe ausstehend`.

Das vollständige vorläufige Profil in `02_Buchungspruefung/Mandantenprofil_Vorschlag.md` ausgeben. Niemals während des Laufs nach SharePoint schreiben. Erst nach ausdrücklicher Freigabe darf es am exakt bestimmten Profilziel angelegt werden.

Während des Beleglaufs keine Rückfragen zu möglichen neuen Besonderheiten stellen und ein vorhandenes Profil nicht ändern. Wiederverwendbare mandantenspezifische Erkenntnisse in `02_Buchungspruefung/Mandantenprofil_Vorschlag.md` sammeln. Je Vorschlag Zielabschnitt, exakten Regeltext, Begründung und betroffene Vorgangs-IDs angeben. Einmalige Belegkorrekturen und globale Regeln nicht für das Mandantenprofil vorschlagen.

## Abgrenzungsregister

Bei Bilanzierenden das Register monatlich am exakt gebildeten SharePoint-Ziel laden und als Markdown fortschreiben. Fehlt es bei einem erstmaligen Lauf nachweislich, ohne Unterbrechung weiterarbeiten. Nur wenn mindestens eine klare neue Abgrenzung entsteht, im `Abgrenzungsregister_Vorschlag.md` die Neuanlage am exakten Ziel verlangen und den vollständigen Übernahmebestand ausgeben. Werden keine Abgrenzungen erkannt, keine leere Registerdatei verlangen. Bei Einnahmenüberschussrechnern ist kein Abgrenzungsregister erforderlich.

Pro offenem Fall führen: Abgrenzungs-ID, ARAP/PRAP, Geschäftspartner, Beschreibung, Aufwands-/Ertragskonto, ARAP-/PRAP-Konto, Belegfeld 1, Leistungsbeginn/-ende, ursprünglicher Nettobetrag, Monatsbetrag, nächste Periode und Restbetrag.

Vor jeder Abgrenzungsprüfung den betrieblichen Anlass beurteilen. Eindeutig private Ausgaben, insbesondere Sport- und Freizeitdauerkarten, auf Konto `4655` buchen und nicht in das Abgrenzungsregister aufnehmen.

Vor einer Neuaufnahme die einheitliche Kleinbetragsregel prüfen. Bei einem maßgeblichen Betrag bis einschließlich 800 EUR den vollständigen Aufwand oder Ertrag im Buchungsmonat erfassen und keinen Vorschlag, Registereintrag oder Abgrenzungsstapel erzeugen. Der ursprüngliche Gesamtbetrag ist maßgeblich, nicht Monatsanteil oder Restbetrag.

Klare neue Abgrenzungen über 800 EUR automatisch in den Übernahmebestand des vollständigen `Abgrenzungsregister_Vorschlag.md` aufnehmen. Fällige klare Auflösungen automatisch in den Buchungsstapel der jeweiligen Buchungsperiode übernehmen (niemals in den Klärungsstapel), Restbetrag fortschreiben und vollständig aufgelöste Einträge aus dem Vorschlag entfernen.

Mehrdeutige neue Abgrenzungen oder zweifelhafte Auflösungen nicht erfragen und den Lauf nicht anhalten. Eine konkrete Empfehlung bilden, den Fall in `Klaerungsfaelle.md` aufnehmen und im Registervorschlag getrennt unter `Klärung offen – noch nicht übernehmen` ausweisen. Diese Kandidaten noch nicht in den Übernahmebestand einrechnen.

## Abschlussübergabe und Schreiben

Während des Laufs weder Mandantenprofil noch Abgrenzungsregister nach SharePoint schreiben. Zuerst alle Belege, Stapel, Prüfliste, `Klaerungsfaelle.md`, `Abgrenzungsregister_Vorschlag.md` und `Mandantenprofil_Vorschlag.md` vollständig erzeugen.

Erst danach darf optional angeboten werden, bestätigte SharePoint-Vorschläge zu übernehmen. Offene Klärungsfälle werden nicht abgefragt, sondern ausschließlich in der bearbeitbaren Klärungsdatei übergeben. Die vollständige DATEV-Paketerstellung ist von keiner Antwort abhängig. Nach ausdrücklicher Zustimmung nur die bestätigten Änderungen an die exakt bestimmten SharePoint-Ziele schreiben.