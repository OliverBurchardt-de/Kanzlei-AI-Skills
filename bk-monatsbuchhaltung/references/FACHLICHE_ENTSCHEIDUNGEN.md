# Verbindliche fachliche Entscheidungen

## 1. Scope und Vollständigkeit

Verarbeitet werden ausschließlich die bereitgestellten Belege. Bank, Kasse, Lohn, Zahlungsverkehr, OPOS-Ausgleich, Abstimmungen und Monatsabschluss bleiben außerhalb des Skills. Jede inventarisierte Datei erhält genau einen Endstatus. Kein buchungsrelevanter Beleg darf fehlen.

## 2. Ausgabe und Stapel

Alle DATEV-Dateien liegen unmittelbar in `01_DATEV_Import/`. Es gibt keine Unterordner für Ampeln, Perioden, Stammdaten oder Stapel. Die Zahl der Stapel ist variabel. Unterschiedliche Ampeln und Belegperioden bleiben unterschiedliche Dateien.

- Grün: fachlich eindeutig.
- Gelb: plausibler Vorschlag mit prüfbarer Unsicherheit.
- Rot: Bearbeitung in DATEV erforderlich; nur das Belegdatum der Zeile bleibt leer.

Sichtbare DATEV-Dateinamen und Buchungstexte enthalten keine Ampelfarben oder Warnungen.

## 3. Perioden

Das Belegdatum bestimmt die Periode. Frühere Monate und Vorjahre erhalten eigene Buchungsstapel und eigene reguläre Belegtransfer-ZIPs. Ein fehlendes Datum führt zu Rot und leerem DATEV-Datum, nicht zum Weglassen.

## 4. Belegfeld 1

Jede Buchungszeile erhält Belegfeld 1. Vorrang hat die Rechnungs-/Gutschriftsnummer, danach eine andere stabile externe Referenz. Keine gesonderte Begründung nötig.

## 5. Durchlauf ohne Zwischenfragen

Nach dem technischen Preflight wird nicht unterbrochen. Fachliche Unsicherheit wird provisorisch gebucht und genau einmal als Klärungsfall dokumentiert. Mitarbeitername ist mandantenseitig fest zugeordnet; die Excel-Datei braucht nur Bearbeitungsstatus und Mitarbeiter-Ergebnis.

## 6. Betrieblicher Anlass

Eindeutig private Ausgaben werden brutto, ohne Vorsteuer und ohne Entnahme-/Verrechnungskonto auf das im Mandantenprofil konfigurierte Privatkonto gebucht. Unklarer Anlass ist Gelb oder Rot. Mandantenseitige Hinweise können unabhängig davon erstellt werden.

## 7. Umsatzsteuer

Die USt-Behandlung kommt aus `vat_config`, nicht aus Branche oder Rechtsform. Zu unterscheiden sind Ausgangsumsätze (`steuerpflichtig`, `steuerfrei`, `gemischt`) und Vorsteuerabzug (`voll`, `keiner`, `anteilig`).

- Kein Vorsteuerabzug: inländische Eingangsrechnung grundsätzlich brutto und BU leer.
- Gemischte Tätigkeit: direkte Zuordnung vor Quote. Allgemeinkosten nur mit profilierter Quote; unklare Zuordnung Rot.
- §13b, innergemeinschaftliche und sonstige Auslandsfälle bleiben gesonderte Steuerfälle.

Details stehen in `UMSATZSTEUER_UND_BEWIRTUNG.md`.

## 8. Bewirtung

Eine automatisierte 70/30-Aufteilung erfolgt nur bei vollständig prüfbarem Rechnungs- und Bewirtungsnachweis. Trinkgeld folgt der 70/30-Aufteilung, ohne Vorsteuer. Unvollständige oder unklare Bewirtungsnachweise bleiben buchungsrelevant und werden Rot auf das konfigurierte Klärungskonto gebucht. Eindeutig private Bewirtung folgt der Privatregel.

## 9. Stammdaten

Neue Debitoren/Kreditoren werden automatisch in `EXTF_Debitoren_Kreditoren.csv` angelegt. Keine Freigabe vor Paketbau.

- Es werden ausschließlich eindeutig einem konkreten Geschäftspartner zugeordnete Einzeldebitoren und Einzelkreditoren verwendet.
- Sammeldebitoren, Sammelkreditoren und CPD-Konten dürfen weder neu angelegt noch bebucht werden. Das gilt auch für bereits vorhandene oder historisch bebuchte DATEV-Konten.
- Inhaltliche Sammelkonten sind unabhängig von ihrer technischen DATEV-Kennzeichnung gesperrt. Dazu zählen insbesondere Kontonamen, die mit `Diverse`, `Div.` oder `CPD` beginnen, sowie Bezeichnungen wie `Sammeldebitor`, `Sammelkreditor` oder `Sammelkonto`. Groß-/Kleinschreibung und Satzzeichen ändern die Einstufung nicht; damit sind z. B. `Diverse u.`, `Diverse a.`, `Div.` und `CPD` gesperrt.
- Frühere Buchungen auf einem gesperrten Konto dürfen nur als historischer Treffer dokumentiert, niemals als Kontierungsvorlage übernommen werden.
- Fehlt ein eindeutig passendes Einzelpersonenkonto, ist zwingend ein neues Einzelkonto anzulegen.
- Kontonummer: höchste vorhandene Nummer im konfigurierten Bereich plus eins; Lücken nie wiederverwenden.
- Kreditor: Name, USt-ID (höchstens eine) und bis zu zehn Bankverbindungen; geänderte Bankverbindung als Mandanten-Hinweis.
- Debitor: mindestens Name.
- Änderung vorhandener Stammdaten nur als vollständiger aktueller Datensatz.

## 10. DATEV-Dublettenprüfung

Jeder Nicht-Avis-Beleg erhält `prior_booking_check`. Sichere Dublette: nicht erneut buchen. Mögliche Dublette: Rot mit leerem DATEV-Datum buchen. Ein identischer technischer Datei-Hash darf nicht zweimal als Buchungsbeleg exportiert werden.

## 11. Zahlungsavise

Zahlungsavise werden vorerst nicht gebucht und nicht in die fachliche Avis-/Factoringlogik einbezogen. Sie erhalten keine Ampel und keine EXTF-Zeile. Der Generator erstellt separate DUO-Belegtransfer-ZIPs `Belegtransfer_Avise_...` mit `document.xml` und ohne Belegtyp. Zusätzlich können Arbeitskopien in `04_Zahlungsavise/` liegen.

## 12. Abgrenzungen

Nur bei Bilanz, nur geschäftsjahresübergreifend und nur über 800 EUR maßgeblichem Betrag. Unter/gleich 800 EUR vollständig im Buchungsmonat. Umsatzsteuer wird, soweit abziehbar, im Ursprungsmonat gezogen; Auflösungen betreffen nur den abzugrenzenden Nettobetrag. Ganze Monate, letzte Rate mit Rundungsdifferenz. Rechnung und erste Auflösung müssen beide gebucht werden.

## 13. Anlagen/GWG

Wirtschaftlich zusammengehörige Bestandteile werden gemeinsam beurteilt. Bis 800 EUR maßgebliche Anschaffungskosten auf das konfigurierte GWG-Konto, darüber Einzelanlagekonto. Jede Buchungszeile, deren Konto oder Gegenkonto in `account_config.asset_accounts` steht, ist eine Anlagenbuchung: `asset_booking: true`, Ampel Rot und DATEV-Belegdatum zwingend leer. Das gilt auch bei einem vollständig und korrekt ausgelesenen Beleg, damit DATEV die automatische Anlagenerfassung bzw. erforderliche Bearbeitung auslöst. Keine Abschreibung und kein Sammelposten.

## 14. Prüfungsdatei

Zentrales Blatt ist `Belegprüfung`: Ampel vorne und farbig, unmittelbar danach der vollständige EXTF-Dateiname des Buchungsstapels, eine Zeile je Beleg, danach Datum, Partner, Belegfeld 1, Betrag, Periode, Kontierung, Ableitung, konkrete Ampelbegründung, nächster Schritt und editierbare Mitarbeiterfelder. Im Blatt `Buchungszeilen` steht der Buchungsstapel ebenfalls an zweiter Stelle. Keine Quelldateinamen, GUIDs, Links oder Spalte „Importfähig“.

## 15. Mandanten-Hinweise

Stichprobe geeigneter inländischer Rechnungen auf Pflichtangaben. Ausländische Rechnungen nicht in diese §14-Stichprobe aufnehmen. Auffällige Bankänderungen und sonstige Mehrwert-Hinweise ebenfalls hier dokumentieren.
