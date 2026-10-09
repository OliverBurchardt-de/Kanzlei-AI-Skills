# Verbindliche fachliche Entscheidungen

## 1. Scope und Vollständigkeit

Verarbeitet werden ausschließlich die bereitgestellten Dateien innerhalb des ausdrücklich beauftragten Modus `belegbuchhaltung`. Bank, Kasse, Lohn, Zahlungsverkehr, OPOS-Ausgleich, Abstimmungen und Monatsabschluss bleiben außerhalb des Skills; insbesondere erzeugt der Skill niemals Kassenbuchungen. Jede Quelldatei wird genau einmal inventarisiert und jedem logischen Vorgang wird genau ein Endstatus zugeordnet: regulär verarbeitet (Grün oder konkret fachlich ungeklärt Rot), sichere Dublette, nicht buchungsrelevant, Aussteuerung an einen anderen Mandanten/Rechtsträger, außerhalb Auftragszeitraum oder nach dokumentiertem Auswertungsversuch technisch nicht auswertbar. Kein buchungsrelevanter Vorgang darf fehlen. Ein Auftrag ist ein Auftrag zur vollständigen Abarbeitung bis zum Abschluss-Gate (SKILL.md, Laufregel Durchführungspflicht); Inventur, Stichproben, Vorprüfungen oder Zwischenberichte sind kein Endpunkt, technische Einzelfehler werden lokal behandelt.

## 2. Ausgabe und Stapel

Alle DATEV-Dateien liegen unmittelbar in `01_DATEV_Import/`. Es gibt keine Unterordner für Ampeln, Perioden, Stammdaten oder Stapel. Je Buchungsmonat gibt es einen Buchungsstapel `EXTF_Buchungsstapel_<JJJJ-MM>.csv` mit allen grünen Buchungszeilen und fälligen Abgrenzungsauflösungen sowie, nur bei roten Vorgängen, einen Klärungsstapel `EXTF_Klaerungsposten_<JJJJ-MM>.csv` mit ausschließlich roten Buchungszeilen. Verschiedene Buchungsmonate bleiben getrennt. Alle Zeilen eines Vorgangs gehören in denselben Stapel (belegweit schlechteste Ampel). Alle Buchungsstapel werden übertragen, sowohl die mit Klärungen als auch die ohne Klärung; der Klärungsstapel wird in DATEV importiert und dort bearbeitet, nur seine Festschreibung erfolgt nach der Bearbeitung. Keine Ersatzkonten. Für die nachgelagerte Übertragung über den Riecken-Connector gilt `SKILL.md` Abschnitt 5; dort werden rote Vorgänge über das Klärungskonto aus dem Mandantenprofil gebucht. Das EXTF-Paket selbst bleibt ohne Ersatzkonten. Im Klärungsstapel bleibt das DATEV-Belegdatum in jeder Zeile leer (Pflichtleerung); das erkannte Datum bleibt in Lauf-JSON, Manifest und Prüfungsdatei erhalten. In jedem Stapel gilt die Sortierregel gegen das Schleppen leerer Felder: Zeilen mit leerem gefährdetem Feld stehen vor Zeilen mit gefülltem Feld; ist das nicht erfüllbar, wird nur der Klärungsstapel in `_02` usw. geteilt. Ein im Mandantenprofil konfigurierter getrennter Vorlauf (`batch_config`, zum Beispiel Eigenbelege) erhält je Periode eine eigene Datei `EXTF_Buchungsstapel_<JJJJ-MM>_<Stapeltyp>.csv`.

- Grün: vollständige, belastbare Buchung ohne offene Entscheidung.
- Rot: konkrete fachliche oder prozessbedingte Bearbeitung erforderlich, weil aus dem Beleg selbst eine konkrete Frage offenbleibt; alle sicheren Angaben erhalten, nur konkret ungeklärte Felder dokumentiert leer lassen. Gelb entfällt. Eine fehlende Standardzuordnung, Profilregel, Vorbuchung oder ein fehlendes Buchungsmuster ist nie ein Klärungsgrund (Abschnitt 18).

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

Zentrales Blatt ist `Belegprüfung`: Ampel vorne und als feste Zellfüllung in der richtigen Farbe hinterlegt, unmittelbar danach der vollständige EXTF-Dateiname des jeweiligen Stapels, eine Zeile je logischem Vorgang, danach Datum laut Beleg, Partner, Belegfeld 1, Betrag, Periode und die Klartextspalten `Beleg zeigt`, `Buchung`, `Daraus folgt`, `Warum Rot oder Grün?`, `Nächster Schritt` sowie die editierbaren Mitarbeiterfelder. Dasselbe gilt für die Ampel im Blatt `Buchungszeilen`. Keine Quelldateinamen, GUIDs, Links oder Spalte „Importfähig“. Die Klartextspalten sind für Mitarbeiter ohne Buchhaltungskürzel lesbar (Abschnitt 20).

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

## 19. Riecken-Übertragung und Klärungskonto

Gilt nur für die nachgelagerte Übertragung nach DATEV über den Riecken-Connector auf ausdrücklichen Auftrag nach der Paketübergabe (`SKILL.md` Abschnitt 5). Der Buchhaltungslauf und das EXTF-Paket bleiben unverändert.

1. **Klärungskonto:** Rote Vorgänge werden bei der Riecken-Übertragung auf das Klärungskonto aus dem Mandantenprofil (`klaerungskonto`) gebucht. Kanzleistandard ist `159900 Klärungskonto Buchhaltung` (vierstellig 1599). Es ist ein reines Arbeitskonto; am Ende der Klärung hat es den Saldo 0.
2. **Kein bereits belegtes Konto:** Das Klärungskonto darf für keinen anderen Zweck bebucht sein. Belegte Konten (Beispiele bei 12371: 1590 `159000 Durchlaufende Posten`, 1591 `159100 Sammelzahlung MCC`) scheiden aus; vor der ersten Verwendung live prüfen und die Existenz vom Nutzer bestätigen lassen.
3. **Zwei Stapel je Monat:** Grüne Zeilen gehen in den Riecken-Stapel `Eingangsrechnungen`, rote in den Riecken-Stapel `Rechnungen Nachlauf`; beide als getrennte Change-Pläne. Der Name des roten Riecken-Stapels ist bewusst neutral, weil die Stapelbezeichnung in DATEV sichtbar bleibt (etwa bei einer Betriebsprüfung); `Klärungsposten` oder ein anderer Hinweis auf Klärung oder Prüfung ist als Riecken-Stapelname unzulässig. Die EXTF-Datei `EXTF_Klaerungsposten_<JJJJ-MM>.csv` des Pakets bleibt davon unberührt.
4. **Klärungsinformation im Buchungstext:** Muster `KLÄR <Vorgangs-ID> <offenes Thema> <Zielkonto oder Alternativen>`, höchstens 60 Zeichen. Der Mitarbeiter findet über den verknüpften Beleg und die Vorgangs-ID alles Weitere in Prüfungsdatei und `Klaerungsfaelle.md`.
5. **Kein 1-Cent-Platzhalter:** Eine Rechnung ohne sicheren Betrag wird nicht gebucht; sie fehlt, bis die vollständige Rechnung vorliegt. Keine Schätzung, kein Platzhalterbetrag.
6. **Anlagevermögen:** Riecken kann keine Anlagegüter anlegen (`datev_get_asset_inventory` ist nur lesend). Anlagenfälle laufen über das Klärungskonto; das vorgeschlagene Zielkonto steht im Buchungstext. Der Mitarbeiter legt das Anlagegut in der Anlagenbuchführung an und bucht um.
7. **Nutzerentscheidungen:** Nicht übertragbare Fälle (beide Kontoseiten offen, Betrag oder Datum unsicher) werden dem Nutzer vorgelegt. Seine Entscheidung (nicht buchen, Beleg belassen oder entfernen) wird mit Name und Datum in Statusdatei und Prüfungs-Excel dokumentiert.
8. **Prüfungs-Excel:** Wird nach der Übertragung auf den Riecken-Stand gebracht und dem Nutzer immer als eigene Datei übergeben.

## 20. Begründung aus dem Beleg

Die Entscheidung über jeden Vorgang wird aus dem Belegbild getroffen und so aufgeschrieben, dass ein Mitarbeiter ohne Rückfrage versteht, warum. Der Riecken-Connector liefert Stammdaten, Vorbuchungen und den Übertragungsweg; er ersetzt weder das Lesen des Belegs noch die Begründung. „Über den Connector nichts gefunden“ oder „in DATEV kein Treffer“ ist nie der Grund für Rot oder Grün; Live-Daten dürfen nur als Zusatzfakt genannt werden („Muster Juli: Telefonkosten auf 492000“).

Je Vorgang vier Klartexte:

1. **Beleg zeigt** (`document_summary`): was auf dem Beleg steht. Aussteller, Adressat, Leistung oder Artikel, Datum und Uhrzeit, Ort, Betrag, Umsatzsteuer, Zahlungsweg. Beispiel: „Kassenbon des WOK point in Hasbergen vom 11.08.2026, 11:43 Uhr, vier Gerichte zum Mitnehmen, 47,00 EUR bar bezahlt, 7 % Umsatzsteuer.“
2. **Daraus folgt** (`derivation`): wie Buchung oder Ausschluss aus dem Beleg und dem Mandantenprofil folgen. Beispiel: „Hasbergen liegt am Privatwohnort, rund 60 km von der Praxis; auf dem Bon stehen weder Teilnehmer noch Anlass.“
3. **Warum Rot oder Grün?** (`reason`): der konkrete Grund, bei Rot zusätzlich das Risiko und welches Feld offen bleibt. Beispiel Rot: „Ohne Anlass und Teilnehmer ist nicht erkennbar, ob es sich um private Verpflegung oder um eine Bewirtung handelt.“ Beispiel Grün: „Rechnung an die Praxis, Leistung Softwarewartung, Betrag und Datum eindeutig, wiederkehrend wie im Vormonat.“
4. **Nächster Schritt** (`next_step`, bei Rot Pflicht): genau eine Aufgabe in einem Satz. Beispiel: „Beim Mandanten nach dem Anlass des Essens und den Teilnehmern fragen.“ Keine Aufzählung von Alternativen, keine zweite Aufgabe, keine Kontonummernwahl als Aufgabe; was aus der Antwort folgt, steht unter „Warum Rot oder Grün?“.

**Rot nur bei einer konkreten offenen Frage aus dem Beleg.** Ein Lauf darf nicht pauschal auf Rot schalten, weil eine technische Standardzuordnung fehlt, das Mandantenprofil keine Regel nennt, keine Vorbuchung oder kein Buchungsmuster vorliegt oder der Lieferant neu ist. In diesen Fällen wird der einzelne Beleg fachlich ausgewertet: Wer stellt aus, an wen ist er adressiert, welche Leistung, welcher Ort, welcher Betrag, welche Umsatzsteuer, welcher Zahlungsweg. Ergibt diese Auswertung eine eindeutige Buchung, ist der Vorgang Grün, auch ohne Profilregel; das Profil erhält dann einen Vorschlag. Rot bleibt nur, wenn der Beleg selbst eine Frage offenlässt, die der Mitarbeiter oder Mandant beantworten muss, zum Beispiel fehlender Anlass einer Bewirtung, nicht erkennbare Leistung, privater oder betrieblicher Zweck, möglicher Doppelbeleg. Diese Frage steht wörtlich unter „Warum Rot oder Grün?“. Begründungen wie „keine Standardzuordnung“, „keine Profilregel“, „kein Buchungsmuster“, „keine Vorbuchung“, „kein Treffer“ oder „neuer Lieferant“ weist der Generator bei Rot zurück; der Validator prüft dieselbe Regel in der Prüfungsdatei. Befund aus Mandant 12191, August 2026: 75 Zeilen standen als Klärungsposten, weil der Lauf bei fehlender Standardzuordnung pauschal Rot gesetzt hatte; nach fachlicher Neubewertung blieben fünf echte Klärungsfälle.

Regeln für alle vier Texte, für Ausschlussgründe, offene Felder und Klärungsfälle:

- Alltagssprache. Keine Feldnamen (`account`, `open_fields`, `kost1`), keine Kürzel (`BU`, `BF1`), keine Werkzeug- oder Connectornamen, kein JSON-Vokabular. Konten heißen „Sachkonto“, „Gegenkonto“, „Kreditor“, „Debitor“; der BU-Schlüssel heißt „Steuerschlüssel“; Belegfeld 1 heißt „Belegnummer“.
- Konkret statt pauschal. „Kontierung prüfen“, „Kontierung offen“, „Prüfung erforderlich“ oder „unklar“ ohne Belegbezug weist der Generator zurück. Jede Begründung nennt die Belegtatsache, aus der sie folgt.
- Vollständig aus dem Beleg. Ein Grund, der sich nicht aus Belegbild, Mandantenprofil oder einer benannten Vorbuchung ergibt, ist keine Begründung.
- Konten dürfen genannt werden, wenn sie der Buchung dienen („Sachkonto 498000 Praxisbedarf“), aber nicht als Entscheidungsalternative im nächsten Schritt.
