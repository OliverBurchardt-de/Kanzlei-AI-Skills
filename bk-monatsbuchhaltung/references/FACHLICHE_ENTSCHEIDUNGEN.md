# Verbindliche fachliche Entscheidungen

## 1. Scope und Vollständigkeit

Verarbeitet werden ausschließlich die bereitgestellten Dateien innerhalb des ausdrücklich beauftragten Modus `belegbuchhaltung`. Bank, Kasse, Lohn, Zahlungsverkehr, OPOS-Ausgleich, Abstimmungen und Monatsabschluss bleiben außerhalb des Skills; insbesondere erzeugt der Skill niemals Kassenbuchungen. Jede Quelldatei wird genau einmal inventarisiert und jedem logischen Vorgang wird genau ein Endstatus zugeordnet: regulär verarbeitet (Grün oder konkret fachlich ungeklärt Rot), sichere Dublette, nicht buchungsrelevant, Aussteuerung an einen anderen Mandanten/Rechtsträger, außerhalb Auftragszeitraum oder nach dokumentiertem Auswertungsversuch technisch nicht auswertbar. Kein buchungsrelevanter Vorgang darf fehlen. Ein Auftrag ist ein Auftrag zur vollständigen Abarbeitung bis zum Abschluss-Gate (SKILL.md, Laufregel Durchführungspflicht); Inventur, Stichproben, Vorprüfungen oder Zwischenberichte sind kein Endpunkt, technische Einzelfehler werden lokal behandelt.

## 2. Ausgabe und Stapel

Alle DATEV-Dateien liegen unmittelbar in `01_DATEV_Import/`. Es gibt keine Unterordner für Ampeln, Perioden, Stammdaten oder Stapel. Je Buchungsmonat gibt es einen Buchungsstapel `EXTF_Buchungsstapel_<JJJJ-MM>.csv` mit allen grünen Buchungszeilen und fälligen Abgrenzungsauflösungen sowie, nur bei roten Vorgängen, einen Klärungsstapel `EXTF_Klaerungsposten_<JJJJ-MM>.csv` mit ausschließlich roten Buchungszeilen. Verschiedene Buchungsmonate bleiben getrennt. Alle Zeilen eines Vorgangs gehören in denselben Stapel (belegweit schlechteste Ampel). Keine Ersatzkonten. Im Klärungsstapel bleibt das DATEV-Belegdatum in jeder Zeile leer (Pflichtleerung); das erkannte Datum bleibt in Lauf-JSON, Manifest und Prüfungsdatei erhalten. In jedem Stapel gilt die Sortierregel gegen das Schleppen leerer Felder: Zeilen mit leerem gefährdetem Feld stehen vor Zeilen mit gefülltem Feld; ist das nicht erfüllbar, wird nur der Klärungsstapel in `_02` usw. geteilt. Ein im Mandantenprofil konfigurierter getrennter Vorlauf (`batch_config`, zum Beispiel Eigenbelege) erhält je Periode eine eigene Datei `EXTF_Buchungsstapel_<JJJJ-MM>_<Stapeltyp>.csv`.

- Grün: vollständige, belastbare Buchung ohne offene Entscheidung.
- Rot: konkrete fachliche oder prozessbedingte Bearbeitung erforderlich; alle sicheren Angaben erhalten, nur konkret ungeklärte Felder dokumentiert leer lassen. Gelb entfällt.

Sichtbare DATEV-Dateinamen und Buchungstexte enthalten keine Ampelfarben oder Warnungen.

## 3. Perioden als harte Auftragsgrenze

`scope.target_periods` begrenzt den Lauf. Frühere oder spätere Vorgänge werden vollständig inventarisiert, erhalten aber `außerhalb Auftragszeitraum` und keine Buchungszeile. Ein Nachtrags- oder Zukunftsstapel entsteht nur bei `include_prior_periods: true` beziehungsweise `include_future_periods: true`. Ein fehlendes Datum innerhalb des Auftrags führt zu Rot und leerem DATEV-Datum, nicht zum Weglassen.

## 3a. Rechtsträger, Dokumentart und globale Ausschlüsse

Je Dokument zwingend zuerst Rechtsträger/Adressat, dann Dokumentart und erst danach Buchungsrelevanz, Geschäftspartner, Konto und Umsatzsteuer prüfen.

- Lohnabrechnungen, Lohnsteuerlisten und Sozialversicherungsnachweise nicht buchen; an die Lohnbuchhaltung übergeben.
- Persönliche Bescheide, Privatkonten und Inkasso gegen eine Privatperson nicht einer GmbH zuordnen.
- Mahnungen/Zahlungserinnerungen ohne Originalrechnung oder sicheren Abgleich nicht als neuen Aufwand buchen.
- Anhörungsbogen ohne endgültige Geldbuße oder Zahlungsanspruch noch nicht buchen.
- Deckblätter zu einzeln gebuchten Originalen nicht zusätzlich buchen; Abweichungen als Avis oder Klärung dokumentieren.
- Kontoauszüge nur inventarisieren und an den Bankprozess übergeben.

Jeder Ausschluss weist Rechtsträger, Dokumentart und konkreten Grund aus. Diese Regeln sind global und dürfen nicht in ein Mandantenprofil verschoben werden.

## 3b. Quelldatei und logischer Vorgang

`source_files`, `transactions` und `transaction_sources` strikt trennen. Eine Rechnung plus Begleit-E-Mail ist ein Vorgang mit zwei Quellen. Eine hochgeladene Sammeldatei kann mehrere Vorgänge belegen; sie wird dann vor dem Paketbau mit `scripts/beleg_pdf.py split` je Vorgang in eine eigene PDF getrennt. **Belegdateiregel: Jeder Buchungsbeleg ist im DATEV-Belegtransfer genau eine eigene PDF-Datei.** Niemals zwei Buchungsbelege in einer übertragenen Datei sammeln, niemals einen Buchungsbeleg auf zwei übertragene Dateien verteilen (Teildateien desselben Belegs mit `merge` zusammenführen), Bild- oder Textbelege mit `convert` in eine PDF überführen. `merge` fasst niemals mehrere Belege zusammen: Jeder Beleg wird genau ein eigenes Dokument. Abgeleitete PDFs sind eigene Quellen mit `derived_from`; das Original bleibt inventarisiert (`bundle_original`/`converted_original`) und wird nicht übertragen. Jede physische Quelldatei höchstens einmal in den Belegtransfer aufnehmen; mehrere Buchungszeilen desselben Vorgangs verweisen auf denselben DATEV-Beleg. Deckblätter, Dublettenkopien und Begleitdokumente nicht als eigenen DATEV-Beleg übertragen; zum Belegbild gehörende Begleitseiten in die Beleg-PDF zusammenführen.

## 4. Belegfeld 1

Belegfeld 1 enthält eine sicher erkannte externe Referenz. Fehlt eine belastbare Referenz, bleibt es bei Rot mit Begründung in `open_fields` leer; keine erfundene Rechnungsnummer. Vorrang hat die Rechnungs-/Gutschriftsnummer, danach eine andere stabile externe Referenz. Keine gesonderte Begründung nötig.

## 5. Durchlauf ohne Zwischenfragen

Nach dem technischen Preflight wird nicht unterbrochen. Fachliche Unsicherheit wird mit sämtlichen sicheren Angaben und konkret offenen Feldern in den Klärungsstapel des Monats exportiert und genau einmal als Klärungsfall dokumentiert; jeder rote Vorgang trägt einen maschinenlesbaren Rot-Grund (`red_reason`) mit durchgeführtem Prüfversuch und nächstem Prüfschritt. Rot ist nur bei konkreter Unsicherheit zulässig: Ein Scan ohne Textebene, ein neuer Kreditor oder ein ungeprüfter Dublettenverdacht sind für sich allein kein Rot-Grund. Mitarbeitername ist mandantenseitig fest zugeordnet; die Excel-Datei braucht nur Bearbeitungsstatus und Mitarbeiter-Ergebnis.

## 6. Betrieblicher Anlass

Eindeutig private Ausgaben werden brutto, ohne Vorsteuer und ohne Entnahme-/Verrechnungskonto auf das im Mandantenprofil konfigurierte Privatkonto gebucht. Unklarer Anlass ist Rot; ungesicherte Kontierung bleibt offen. Mandantenseitige Hinweise können unabhängig davon erstellt werden.

## 7. Umsatzsteuer

Die USt-Behandlung kommt aus `vat_config`, nicht aus Branche oder Rechtsform. Zu unterscheiden sind Ausgangsumsätze (`steuerpflichtig`, `steuerfrei`, `gemischt`) und Vorsteuerabzug (`voll`, `keiner`, `anteilig`).

- Kein Vorsteuerabzug: inländische Eingangsrechnung grundsätzlich brutto und BU leer.
- Gemischte Tätigkeit: direkte Zuordnung vor Quote. Allgemeinkosten nur mit profilierter Quote; unklare Zuordnung Rot.
- §13b, innergemeinschaftliche und sonstige Auslandsfälle bleiben gesonderte Steuerfälle.

Details stehen in `UMSATZSTEUER_UND_BEWIRTUNG.md`.

## 8. Bewirtung

Eine automatisierte 70/30-Aufteilung erfolgt nur bei vollständig prüfbarem Rechnungs- und Bewirtungsnachweis. Trinkgeld folgt der 70/30-Aufteilung, ohne Vorsteuer. Unvollständige oder unklare Bewirtungsnachweise bleiben buchungsrelevant und werden Rot mit sicheren Angaben und offenen Feldern im Klärungsstapel exportiert; keine Ersatzbuchung auf 1590 oder andere Zwischenkonten. Eindeutig private Bewirtung folgt der Privatregel.

## 9. Stammdaten

Neue Debitoren/Kreditoren werden automatisch in `EXTF_Debitoren_Kreditoren.csv` angelegt. Keine Freigabe vor Paketbau.

- Es werden ausschließlich eindeutig einem konkreten Geschäftspartner zugeordnete Einzeldebitoren und Einzelkreditoren verwendet.
- Sammeldebitoren, Sammelkreditoren und CPD-Konten dürfen weder neu angelegt noch bebucht werden. Das gilt auch für bereits vorhandene oder historisch bebuchte DATEV-Konten.
- Inhaltliche Sammelkonten sind unabhängig von ihrer technischen DATEV-Kennzeichnung gesperrt. Dazu zählen insbesondere Kontonamen, die mit `Diverse`, `Div.` oder `CPD` beginnen, sowie Bezeichnungen wie `Sammeldebitor`, `Sammelkreditor` oder `Sammelkonto`. Groß-/Kleinschreibung und Satzzeichen ändern die Einstufung nicht; damit sind z. B. `Diverse u.`, `Diverse a.`, `Div.` und `CPD` gesperrt.
- Frühere Buchungen auf einem gesperrten Konto dürfen nur als historischer Treffer dokumentiert, niemals als Kontierungsvorlage übernommen werden.
- Fehlt ein eindeutig passendes Einzelpersonenkonto, ist zwingend ein neues Einzelkonto anzulegen. Ein fehlender oder neuer Kreditor/Debitor ist deshalb nie ein Rot-Grund; Rot mit `personenkonto_unklar` nur bei dokumentiert nicht auflösbarer Geschäftspartneridentität (`red_reason.partner_check`).
- Kontonummer: höchste vorhandene Nummer im konfigurierten Bereich plus eins; Lücken nie wiederverwenden.
- Kreditor: Name, USt-ID (höchstens eine) und bis zu zehn Bankverbindungen; geänderte Bankverbindung als Mandanten-Hinweis.
- Debitor: mindestens Name.
- Änderung vorhandener Stammdaten nur als vollständiger aktueller Datensatz.

## 10. Dreistufige Dublettenprüfung

Jeden Nicht-Avis-Vorgang auf drei Ebenen prüfen und Treffergrund sowie Referenz dokumentieren:

1. identischer Datei-SHA-256 im aktuellen Upload,
2. dasselbe logische Dokument im aktuellen Upload anhand Geschäftspartner, Rechnungsnummer, Datum und Betrag,
3. bereits vorhandene Buchung in DATEV live, abgerufen über den Riecken-DATEV-Connector (`datev_get_account_postings`).

Sichere Dublette nicht erneut buchen. Mögliche Dublette Rot exportieren; ein sicher bekanntes Datum und alle weiteren sicheren Werte bleiben erhalten. Das Dublettenrisiko und die Entscheidung stehen in der Prüfungsdatei. Identische Dateien nur einmal übertragen; weitere Kopien als `duplicate_copy` ausschließen.

## 11. Zahlungsavise und Zahlungsabstimmung

Zahlungsavise werden nicht gebucht. Sie erhalten keine Ampel und keine EXTF-Zeile. Der Generator erstellt separate DUO-Belegtransfer-ZIPs `Belegtransfer_Avise_...` mit `document.xml` und ohne Belegtyp.

Fehlende Konto-/Kreditkartenabrechnungen, Zahlungsnachweise, Kartenumsätze oder Kursdifferenzen verändern die Ampel einer fachlich eindeutigen Rechnung nicht. Zahlungs- und Kreditkartenabstimmung separat in `payment_reconciliation` dokumentieren und gegebenenfalls an den Folgeprozess übergeben. Rot ist nur wegen Kontierung, Betrag, Geschäftspartner, Periode, Umsatzsteuer, betrieblichem Anlass, Anlagenbehandlung oder Dublette zulässig.

## 12. Abgrenzungen

Nur bei Bilanz, nur geschäftsjahresübergreifend und nur über 800 EUR maßgeblichem Betrag. Unter/gleich 800 EUR vollständig im Buchungsmonat. Umsatzsteuer wird, soweit abziehbar, im Ursprungsmonat gezogen; Auflösungen betreffen nur den abzugrenzenden Nettobetrag. Ganze Monate, letzte Rate mit Rundungsdifferenz. Rechnung und erste Auflösung müssen beide gebucht werden.

## 13. Anlagen/GWG

Wirtschaftlich zusammengehörige Bestandteile gemeinsam beurteilen. Anlagevermögen und GWG sind stets Rot mit `asset_booking: true`. Das betroffene Sachkontenfeld bleibt grundsätzlich leer, auch wenn das passende Anlagenkonto eindeutig ist; je Zeile `asset_account_field` und `open_fields` erfassen. Bekannte Personenkonten, Beträge, Daten und Belegverknüpfungen erhalten. Die Prüfungsdatei weist den Mitarbeiter konkret zur Anlage in der Anlagenvorerfassung an, damit Anlagenbuchführung und Finanzbuchhaltung verknüpft entstehen. Vorschläge zu GWG, Anlagenkonto und Nutzungsdauer ausschließlich dort dokumentieren. Keine direkte Anlagenkontenbuchung, Abschreibung oder Sammelposten. Anlagenzugänge landen als Rot im Klärungsstapel des Monats.

## 14. Prüfungsdatei und Abschlussnachweis

Zentrales Blatt ist `Belegprüfung`: Ampel vorne und als feste Zellfüllung in der richtigen Farbe hinterlegt, unmittelbar danach der vollständige EXTF-Dateiname des Buchungsstapels, eine Zeile je logischem Vorgang, danach Datum, Partner, Belegfeld 1, Betrag, Periode, Kontierung, Ableitung, konkrete Ampelbegründung, nächster Schritt und editierbare Mitarbeiterfelder. Dasselbe gilt für die Ampel im Blatt `Buchungszeilen`. Keine Quelldateinamen, GUIDs, Links oder Spalte „Importfähig“.

`Taetigkeitsnachweis.md` nennt Auftrag und tatsächliche Perioden, Quelldateien, logische Vorgänge, Buchungszeilen, Ampel-/Statuszahlen, alle ausdrücklich genannten Personen/Geschäftspartner samt Suchvarianten, Fundstellen und Endstatus sowie die verwendeten Datenquellen. Ein technisch gültiges Paket heißt `Importpaket erstellt – noch nicht in DATEV importiert`; `in DATEV importiert` ist nur mit Nachweis zulässig. Zusätzlich stets `fachlicher Prüfprotokoll-Rücklauf ausstehend` ausweisen.

`Uebergabeliste.md` führt jede ausgeschlossene Folgearbeit mit Quelle, Vorgang, Periode, Zielprozess und Grund. Eine Übergabe an den Kassenprozess ist keine Kassenbuchung.

## 15. Mandanten-Hinweise

Stichprobe geeigneter inländischer Rechnungen auf Pflichtangaben. Ausländische Rechnungen nicht in diese §14-Stichprobe aufnehmen. Auffällige Bankänderungen und sonstige Mehrwert-Hinweise ebenfalls hier dokumentieren.

## 16. Kostenstellen

- Kostenstellen kommen ausschließlich aus dem Mandantenprofil (`cost_center_config`) und werden live gegen DATEV validiert (`validated_cost_centers`, über den Riecken-Connector aus Vorbuchungen und Anlagenverzeichnis). Eine Kostenstelle wird immer bebucht, wenn sie eingerichtet ist und sich aus Beleg oder Profil ableiten lässt; die Ableitung steht je Vorgang in `derivation`.
- Die Kostenstellenpflicht (`kostenstellenpflicht`) entscheidet nur, was bei fehlender Ableitung geschieht: Pflicht bedeutet Rot mit offenem `kost1`; ohne Pflicht bleibt das Feld leer ohne Ampelwirkung und die Prüfungsdatei weist die Zeile als „ohne Kostenstelle“ aus.
- Gemischte Rechnungen werden in getrennte Buchungszeilen je Kostenstelle aufgeteilt.
- Die Kostenstelle steuert keine Umsatzsteuer automatisch. Vorsteuerbehandlung und KOST1 werden gemeinsam aus Beleginhalt und Profil abgeleitet und müssen zueinander passen. Ein Widerspruch (zum Beispiel eine Kostenstelle ohne Vorsteuerabzug mit vollem Vorsteuerabzug) ist Rot.
- Eine unsichere Zuordnung zwischen Kostenstellen ist Rot mit offenem `kost1`; keine Ersatzkostenstelle, insbesondere keine Sammelkostenstelle als Verlegenheitslösung.
- Eine im Profil genannte, aber live in DATEV nicht vorhandene Kostenstelle wird nicht exportiert; der Vorgang ist Rot mit offenem `kost1` und Klärungsfall „Kostenstelle in DATEV anlegen“.
- Jede gefüllte Kostenstelle muss in `kost1_allowed` beziehungsweise `kost2_allowed` stehen; eine unbekannte Kostenstelle ist ein Generatorfehler.
- Mandantenspezifische Zuordnungen (welche Kostenstelle mit welcher Vorsteuer und welchem Erlöskonto) gehören ausschließlich in das Mandantenprofil, nicht in diese Referenz.

## 17. Getrennte Buchungsvorläufe

Nur wenn das Mandantenprofil unter `batch_config.separate_batches` einen Stapeltyp freischaltet (zum Beispiel `eigenbelege` für Eigenrechnungen eines Labors), erhalten Vorgänge mit `batch_type: <Stapeltyp>` je Periode einen eigenen Vorlauf `EXTF_Buchungsstapel_<JJJJ-MM>_<Stapeltyp>.csv` mit der konfigurierten Stapelbezeichnung. Jede Zeile trägt die vorgeschriebene Kostenstelle (`required_kost1`) und das vorgeschriebene Gegenkonto (`required_contra_account`); Abweichungen und ein `batch_type` ohne Konfiguration sind Generatorfehler. Rote Vorgänge eines Stapeltyps landen in `EXTF_Klaerungsposten_<JJJJ-MM>_<Stapeltyp>.csv`. Der Eigenbeleg-Stapel wird nach dem Standardstapel derselben Periode importiert.

## 18. Klärungsquote und Zweitprüfung

Vor dem Paketbau und erneut vor der Abschlussmeldung wird die Klärungsquote `Q = 100 × R / N` nach `VALIDIERUNG.md`, Abschnitt `Klärungsquote und Zweitprüfung`, berechnet: `N` sind die einmalig gezählten buchungsrelevanten Vorgänge, `R` die roten Vorgänge. Bis 10 % normale Vollständigkeitskontrolle, über 10 bis 20 % dokumentierte Ursachenprüfung je Rot-Kategorie, über 20 % verpflichtende vollständige Zweitprüfung aller roten Vorgänge anhand Belegbild, Mandantenprofil, DATEV-Bestand und Buchungsregeln. Die Quote ist ein Qualitätsindikator und kein Zielwert; sie wird nie durch Schätzungen, Ersatzkonten oder Umstufungen gesenkt, eine hohe Quote löst Nacharbeit und keinen Abbruch aus, berechtigt rote Fälle bleiben Rot und werden als fachlich offen ausgewiesen. Der Nachweis steht in `Klaerungsquote_Nachweis.md`, im Registerblatt `Klärungsquote` der Prüfungs-Excel, im Laufmanifest und im Validierungsbericht.
