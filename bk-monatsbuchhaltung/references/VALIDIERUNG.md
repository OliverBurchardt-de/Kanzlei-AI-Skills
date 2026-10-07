# Validierung

## Strukturell blockierend

Kein importfreigegebenes Paket bei fehlender bestätigter DATEV-Verbindung, fehlendem oder nicht verifiziertem vorhandenen/vorläufigen Mandantenprofil, verpflichtender Kostenstelle, fehlenden Header-Kerndaten, falscher EXTF-Kategorie/-Version, falscher Feldanzahl, verschobenen Spalten, nicht positiver Buchungssumme, ungültigem Soll/Haben, ungültigem Konto/Gegenkonto, fehlendem Belegfeld 1, mehr als zehn Banken oder Teiländerung eines vorhandenen Stammdatensatzes.

Nur fehlende DATEV-Verbindung, technischer SharePoint-Abruf-/Lesefehler, ein nach erfolgreicher direkter Ordnerauflistung tatsächlich fehlendes Mandantenprofil oder verpflichtende Kostenstellenverarbeitung beenden den Lauf im Preflight. Ein nachweislich nicht vorhandenes Abgrenzungsregister beendet den Lauf ausdrücklich nicht. Eine erfolglose Volltext- oder Stichwortsuche darf niemals als fehlendes Mandantenprofil gewertet werden. Später erkannte strukturelle Fehler werden protokolliert und kennzeichnen das Paket als nicht importfreigegeben; sie lösen keine fachliche Zwischenfrage aus.

Neue Kreditoren und Debitoren, ihre automatisch fortlaufenden Kontonummern sowie provisorische Kreditorennamen sind niemals ein Stop- oder Freigabegrund. Prüfen, dass keine Freigabeeigenschaft erwartet wird, jede technisch mögliche Neuanlage in `EXTF_Debitoren_Kreditoren.csv` enthalten ist und bei unklarer Geschäftspartneridentität kein Name oder Personenkonto erfunden wird; das betroffene Personenkontofeld bleibt bei Rot dokumentiert offen. Meldet das Laufmanifest mindestens einen `master_records`-Datensatz, muss `01_DATEV_Import/EXTF_Debitoren_Kreditoren.csv` vorhanden sein, Kategorie 16 und Formatversion 5 tragen und exakt dieselbe Zahl an Datenzeilen enthalten. Eine separate Anlage zählt nicht als Stammdatenimport.

Für jedes verwendete bestehende Personenkonto muss `datev_live_evidence.used_person_accounts` Kontonummer, Typ und live gelesenen Namen enthalten. Generatorisch sperren:

- jeden Stammdatensatz und jedes verwendete bestehende Personenkonto mit einer Sammel-/CPD-Bezeichnung,
- insbesondere Namen, die normalisiert mit `Diverse`, `Div.` oder `CPD` beginnen,
- Bezeichnungen mit `Sammeldebitor`, `Sammelkreditor` oder `Sammelkonto`,
- Buchungszeilen, deren Personenkontoname nicht mit dem live nachgewiesenen bzw. neu angelegten Einzelkonto übereinstimmt.

Ein in früheren Buchungen verwendetes gesperrtes Konto bleibt gesperrt. Historische Nutzung ist kein Positivnachweis. In diesem Fall muss eine Neuanlage mit höchster vorhandener Nummer plus eins erfolgen.

## Technischer Quellen-Preflight

Ein Wahrheitsfeld allein ist kein Quellenbeleg. Vor dem Paketbau müssen für ein vorhandenes Mandantenprofil die exakte SharePoint-URL, Dateiname, `file_uri`, der tatsächlich verwendete Abrufweg, der gelesene UTF-8-Inhalt und dessen SHA-256 vorliegen. Bei einem kontrollierten Erstlauf tritt nach erfolgreicher Site-/Bibliotheksprüfung und zwei direkten `itemNotFound`-Treffern der verifizierte Nichtvorhanden-Nachweis sowie das vollständige vorläufige Profil an diese Stelle. Bei Bilanz gilt dies auch für ein vorhandenes Abgrenzungsregister. Ist das Register nachweislich noch nicht angelegt, tritt an die Stelle des Inhaltsnachweises ein verifizierter `not_found`-Nachweis mit zweimaligem exaktem Direktabruf nach erfolgreicher Site- und Bibliotheksprüfung; dies blockiert den Lauf nicht. Zusätzlich muss `datev_live_evidence` Abrufzeitpunkt, mit dem Lauf übereinstimmende Berater-/Mandantennummer, Wirtschaftsjahr, Kontenlänge und Kontenrahmen, die tatsächlich verwendeten validierten Konten und BU-Schlüssel, beide höchsten Personenkontonummern sowie die bestätigte Prüfung vorhandener Stammdaten und früherer Buchungen mit jeweiliger Trefferzahl enthalten. Der Generator weist jede Buchung auf nicht bestätigten Konten oder mit nicht bestätigtem BU-Schlüssel sowie jede nicht lückenlose Neuanlage zurück.

## SharePoint-Preflight

- Vor jedem SharePoint- oder Dateizugriff `scripts/sharepoint_target.py --mandant <Mandantennummer>` ausführen und ausschließlich die ausgegebene `profile_url` verwenden.
- Als erste Zugriffsaktion die exakte `profile_url` direkt über den in der jeweiligen Oberfläche verfügbaren SharePoint-Abrufweg laden. Keine lokale Ersatzdatei, semantische Suche oder DMS-Datei vorschalten.
- Den Treffer nur bestätigen, wenn `title` oder `file_name` exakt `<Mandantennummer>.md` lautet, `file_uri` vorhanden ist und `web_link` beziehungsweise `display_url` mit `profile_url` beginnt.
- Bei gefundenem Item die Markdown-Rohdatei als UTF-8 lesen; `content: null` beziehungsweise eine leere Textextraktion nicht als Fehler behandeln.
- Jedes Ergebnis aus `Kanzlei/Mandanten`, persönlichem OneDrive, `Documents` oder `Dokumente` als falschen Abrufweg verwerfen; daraus weder Profilinhalt noch `Profil fehlt` ableiten.
- Host `/sites/Wissen` und Drive `Mandantenbesonderheiten` nur nach technischem Fehler oder `NOT_FOUND` zur Diagnose validieren und anschließend dieselbe exakte URL erneut abrufen.
- Keine semantische Suche, allgemeine Volltextsuche, persönliche OneDrive-Suche oder Suche im allgemeinen Teamspace/`Documents`/`Dokumente`/`Teams Wiki Data` für Markdown-Profile verwenden.
- Den Benutzer nicht nach einem SharePoint-Link fragen, solange die fest hinterlegte exakte URL nicht direkt abgerufen und technisch diagnostiziert wurde.
- `Profil fehlt` nur zulassen, wenn sowohl der erste als auch der nach erfolgreicher Site-/Drive-Diagnose wiederholte direkte Abruf derselben exakten Datei-URL eindeutig `itemNotFound`/`NOT_FOUND` liefert.
- Einen 404-Fehler beim drive-unspezifischen Browsen von `folder_path="Mandantenprofile"` nicht als fehlendes Profil werten; dieser Aufruf kann die Standardbibliothek treffen.
- Nicht auflösbare Site, Bibliothek, Drive-URL, exakte Datei-URL oder Rohdatei als technischen Abruf-/Lesefehler klassifizieren; keine Profilneuanlage vorschlagen.

## Beabsichtigte rote Zeilenfehler

Rot bleibt im gemeinsamen Monatsstapel. Nur konkret dokumentierte offene Felder dürfen leer sein; bekannte Werte bleiben erhalten. Header, Kategorie 21, Formatversion 13 und 125-Feld-Struktur bleiben verbindlich. Jede rote Zeile über Vorgangs-ID, Datei, CSV-Zeilennummer, `open_fields` und exportierte Werte im Manifest nachweisen. Die Prüfung bestätigt den internen Exportvertrag, nicht die DATEV-Importfähigkeit unvollständiger Pflichtfelder.

## Fachliche Prüfungen

- Echte Kalenderdaten prüfen.
- Buchungsperiode aus erkanntem Belegdatum ableiten.
- Jede Buchungsperiode als genau eine gemeinsame CSV-Datei unmittelbar in dem einzigen Ordner `01_DATEV_Import/` ausgeben. Alle Stammdaten-, Buchungs-, Abgrenzungs- und Belegtransferdateien liegen dort gemeinsam; Unterordner und getrennte DATEV-/Ampelordner sind blockierend. Den gemeinsamen Monatsstapel vollständig durch die strukturelle EXTF-Prüfung laufen lassen. DATEV-Dateiname und Stapelbezeichnung dürfen keine Ampelfarbe enthalten. DATEV-Stapel und Dateiname heißen `Buchungsstapel`; getrennte Klärungs-/Abgrenzungsdateien sind unzulässig. Nur ausdrücklich über `scope` freigegebene Vorjahresperioden verarbeiten und niemals mit dem laufenden Buchungsmonat mischen.
- Belegweit schlechteste Farbe durchsetzen.
- Bei Rot alle sicher bekannten Angaben erhalten; ausschließlich begründete `open_fields` offen lassen.
- Bekannte Belegreferenz in Belegfeld 1 setzen; unbekannte Referenz bei Rot dokumentiert leer lassen und auf 36 zulässige Zeichen normalisieren.
- Buchungstext auf 60 Zeichen normalisieren und interne Warn- oder Prüfhinweise vollständig ausschließen. Das gilt für Grün und Rot.
- BU-Schlüssel im Lauf-JSON und in Excel fachlich leer oder genau dreistellig führen. Vierstellige Eingaben mit genau einer führenden Null intern auf drei Stellen normalisieren; zweistellige und sonstige Formate zurückweisen. Im technischen EXTF-Feld 9 den Schlüssel exakt vierstellig mit führender Null ausgeben und validieren.
- Nur live bestätigte Konten und Steuerschlüssel verwenden.
- Vollständigkeitsgleichung auf Dateiebene und Exportebene prüfen. Jeder Beleg mit Status `Buchungszeile erzeugt` muss mindestens eine tatsächlich exportierte DATEV-Buchungszeile besitzen.
- Neu erkannte Abgrenzungen über `transaction_ids` mit ihren Ursprungsrechnungen verknüpfen. Ursprungsrechnung zwingend gegen Kreditor/Debitor auf ARAP/PRAP buchen; Registereintrag und Auflösungsstapel ersetzen diese Rechnungsbuchung nicht.
- Für jede neue Abgrenzung die erste Auflösungsbuchung im gemeinsamen Monatsstapel nachweisen.
- Sichere Dublette nicht erneut buchen oder übertragen.
- Zahlungsavis nicht buchen; als eigenes DUO-Belegtransfer-ZIP mit `document.xml` vollständig aussteuern und zusätzlich als Arbeitskopie ablegen.
- Betrieblichen Anlass vor Kontierung, Anlagenprüfung und Abgrenzungsprüfung dokumentieren.
- Bei eindeutig privater Ausgabe Bruttobetrag auf Konto `4655` gegen den Kreditor buchen, BU-Schlüssel leer lassen und keinen Vorsteuerabzug oder Abgrenzung erzeugen.
- Für private Ausgaben keine Entnahme-, Gesellschafter- oder Verrechnungskonten verwenden.
- Sport- und Freizeitdauerkarten als privat und nicht abzugrenzen behandeln.
- Bei unklarem betrieblichen Anlass Rot und eine konkrete Begründung setzen.
- Konto und Gegenkonto gegen `account_config.asset_accounts` prüfen. Jede direkte Anlagenkontenbuchung blockiert das Paket. Anlagen/GWG stattdessen Rot mit `asset_booking: true`, `asset_account_field` und dokumentiert leerem Anlagenkontofeld exportieren; sicheres Datum erhalten.
- Fällige Abgrenzungsauflösung im gemeinsamen Monatsstapel.
- Die einheitliche 800-Euro-Regel vor jeder Abgrenzung prüfen: `threshold_amount` muss für neue ARAP-/PRAP-Fälle über 800 EUR liegen.
- Bei einem maßgeblichen Betrag bis einschließlich 800 EUR vollständigen Aufwand oder Ertrag im Buchungsmonat erfassen und keinen Abgrenzungsvorschlag, Registereintrag oder Abgrenzungsstapel zulassen.
- Für die Grenze die gesamte Ausgabe oder Einnahme prüfen, nicht Monatsanteil oder Restbetrag; bei vollem Vorsteuerabzug netto, sonst einschließlich nicht abziehbarer Umsatzsteuer.
- Klare neue Abgrenzungen über 800 EUR und klare Auflösungen ohne Rückfrage verarbeiten.

## Durchlauf und Klärungsdateien

- Nach bestandenem Preflight keine fachlichen Zwischenfragen zulassen.
- Sämtliche Dateien vollständig analysieren und alle fachlichen Entscheidungen in den Klärungsunterlagen dokumentieren; keine Freigabe- oder Abschlussfrage für Klärungsfälle stellen.
- `02_Buchungspruefung/Klaerungsfaelle.md` immer erzeugen, auch wenn keine Klärungsfälle bestehen.
- Jeden Beleg mit `requires_clarification: true` genau einem Klärfall zuordnen; mehrere Zeilen desselben Belegs nicht doppelt aufführen.
- Jeder Klärfall muss Tatsachen, sichere Angaben, konkrete offene Felder, `booking_risk`, konkrete Empfehlung, Entscheidungspunkt, Ampel Rot, Ziel, vorgeschlagene Änderung und ein editierbares Mitarbeiterfeld enthalten.
- Jeder Beleg muss eine knappe fachliche Ableitung seiner Buchung oder sonstigen Behandlung enthalten. Strukturierte Werte werden in der kompakten Kontierung gezeigt und nicht in langen Standardtexten wiederholt.
- In `Belegprüfung` und `Buchungszeilen` muss `Ampel-Einstufung` jeweils die erste, fixierte und farblich formatierte Spalte sein. `Buchungsstapel` muss jeweils als zweite, ebenfalls fixierte Spalte den vollständigen tatsächlich erzeugten EXTF-Dateinamen enthalten. Rot erhält rote und Grün grüne Füllung; Gelb ist unzulässig. Sichtbare Spalten `Belegdatei`, `Quelldatei`, `Originaldateiname`, Pfad oder `Importfähig` sind unzulässig; technische Quelldateiangaben verbleiben ausschließlich im Lauf-JSON und Belegindex.
- Jeder gebuchte Beleg muss eine konkrete Ampelbegründung besitzen; auch Grün darf nicht leer sein. Kontierung, Ableitung, Ampelbegründung und nächster Schritt sind in `Belegprüfung` sichtbar.
- Offene Klärfälle dürfen Prüfliste, Buchungsstapel, Belegtransfer oder Gesamtpaket nicht blockieren.
- `02_Buchungspruefung/Abgrenzungsregister_Vorschlag.md` immer vollständig erzeugen. Ungeklärte Kandidaten getrennt unter `Klärung offen – noch nicht übernehmen` ausweisen und nicht in den Übernahmebestand einrechnen. War im Preflight kein Register vorhanden, bei einem nicht leeren Übernahmebestand klar `Neuanlage erforderlich` ausweisen; bei leerem Übernahmebestand `keine Neuanlage erforderlich` ausweisen.
- `02_Buchungspruefung/Mandantenprofil_Vorschlag.md` immer erzeugen. Nur dauerhaft wiederverwendbare mandantenspezifische Regeln vorschlagen.
- SharePoint während des Laufs nicht ändern. Nach Übergabe aller Dateien höchstens optional die Übernahme bestätigter SharePoint-Vorschläge anbieten; die DATEV-Paketerstellung und Klärungsfälle dürfen davon nicht abhängen.
- Während des Buchhaltungslaufs keine Skill-Datei, Referenz, Skript, Metadatei, Installation oder ZIP verändern und den `skill-creator` nicht verwenden.
- Einmalige Fälle der Klärungsdatei, mandantenspezifisch wiederverwendbare Regeln dem Mandantenprofil-Vorschlag und globale Verbesserungsmöglichkeiten ausschließlich einer internen Themenliste zuordnen.
- Möglichen Skill-Änderungsbedarf erst nach vollständiger Paketerstellung kurz nennen und einmal fragen, ob separate Änderungsvorschläge gewünscht sind.
- Auch nach Zustimmung nur eine Vorschlagsdatei erstellen; keine Skill-Änderung ohne weiteren ausdrücklichen Auftrag umsetzen.

## Zeichen und Dateien

- EXTF in Codepage 1252 mit CRLF erzeugen.
- Steuerzeichen entfernen.
- Technische Belegdateinamen ASCII-normalisieren.
- Datei-Hash mit SHA-256 bilden.
- `01_DATEV_Import/` darf nur DATEV-Importdateien `EXTF_*.csv` und DATEV-Document-Packages `Belegtransfer_*.zip`, keine losen Belege, keinen `Belegindex.json` und keine Unterordner enthalten. Jede `EXTF_*.csv` und jedes `Belegtransfer_*.zip` muss unmittelbar in diesem Ordner liegen.
- Jedes Document-Package muss genau eine `document.xml` und alle dort referenzierten Belege ohne Unterordner enthalten.
- Jedes `document` muss `processID="1"` tragen. Das Attribut `type` muss vollständig fehlen, damit DATEV den Beleg in diesem Workflow als „Ohne Belegtyp“ übernimmt. Auch die schemaformal möglichen Werte `1` und `2` sind für diesen Skill zurückzuweisen. Den Text `accountsPayableLedger` in einem File-only-Belegtransfer-ZIP blockierend zurückweisen.
- Jedes Document-Package darf nur Belege genau einer Buchungsperiode enthalten. Der Belegindex muss für jedes enthaltene Dokument dieselbe Periode wie der Paketname ausweisen.
- Für jede ausdrücklich über `scope` freigegebene Vorjahresperiode mindestens ein eigenes `Belegtransfer_<Mandant>_<Belegperiode>_<NNN>.zip` verlangen; eine Mischung mit laufenden oder anderen Perioden ist blockierend.
- `document.xml` gegen `Document_v060.xsd` und `Document_types_v060.xsd` validieren.
- Jede GUID aus `document.xml` muss als `BEDI "GUID"` in Feld 20 mindestens einer zugehörigen EXTF-Buchungszeile vorkommen; jeder EXTF-Beleglink muss im Belegtransfer vorhanden sein.
- Größenlimits prüfen: Einzeldatei höchstens 20 MB, Paket höchstens 465 MB; bei ungefähr 100 MB teilen.
- Belegtransfer erst nach erfolgreicher ZIP-, XSD- und GUID-Konsistenzprüfung als DATEV-importbereit kennzeichnen.

Die technische Validierung ersetzt keinen DATEV-Pilot.## DATEV-Testimport und Grenzen der internen Prüfung

Vor einem produktiven Import das Paket in einem dafür freigegebenen DATEV-Testbestand testen. Prüfen, ob unvollständige rote Zeilen als bearbeitungsbedürftig übernommen werden oder ob DATEV Zeilen beziehungsweise den gesamten Stapel zurückweist. Den tatsächlich getesteten Dateistand über SHA-256 nachweisen; Ergebnis, DATEV-Version, Testbestand und genaue Meldungen dokumentieren. Bei fehlendem Zugang Status `pending` und `DATEV-Testimport ausstehend` ausweisen; keinen Erfolg behaupten. Die Paketübergabe mit internem `valid=true` bleibt zulässig, ohne damit DATEV-Importfähigkeit zu bestätigen.

Optionales Lauf-JSON-Feld `datev_test_import`: `status` ist `pending`, `confirmed` oder `rejected`. Bei ausgeführtem Test sind `tested_at`, `datev_version`, `test_client`, `evidence_reference`, `result_detail` und `tested_files` Pflicht. `tested_files` ordnet jedem tatsächlich erzeugten EXTF-Dateinamen den SHA-256 des getesteten Inhalts zu. `confirmed` bedeutet: Alle Zeilen wurden übernommen und rote Zeilen sind bearbeitungsbedürftig; `rejected` protokolliert insbesondere eine Zurückweisung des gesamten Stapels. Ein Nachweis für andere Dateiinhalte bestätigt das aktuelle Paket nicht. Ein ergebnisloser oder nicht ausgeführter Test bleibt `pending`.

Weist DATEV den gesamten Stapel zurück, Fehler und betroffene Felder offen melden; keine Ersatzbuchung, kein Entfernen roter Fälle und kein eigenmächtiges Aufteilen des Monatsstapels. Einen lokalen Strukturtest niemals als DATEV-Testimport ausgeben.

Quelle: [DATEV-Schnittstellenvorgaben und Testimport](https://developer.datev.de/de/product-detail/accounting-extf-files/2.0/documentation/interface-requirements-file).

Einen tatsächlichen Testimportnachweis nach dem Test mit `python scripts/validate_package.py --package <Paketordner> --datev-test-import <Nachweis.json>` prüfen. Bei passendem Dateistand wird er unter `03_Technische_Protokolle/DATEV_Testimport.json` gespeichert und bei Folgeprüfungen berücksichtigt.
