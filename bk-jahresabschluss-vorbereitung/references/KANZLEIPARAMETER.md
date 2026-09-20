# Kanzleiparameter und Freigabestatus

## Bestätigt

### Durchlaufende Posten unter 100 EUR

Die Regel gilt für den absoluten Betrag jeder einzelnen Buchung, nicht für einen saldierten Tages-, Partner- oder Kontobetrag:

- `abs(Einzelbuchung) < 100,00 EUR`: nicht auf dem funktionalen Konto `Durchlaufende Posten` belassen.
- Bruttobetrag ohne Vorsteuerabzug und ohne Steuerschlüssel auf `Sonstiger Betriebsbedarf` umbuchen.
- SKR03 regelmäßig: `1590` auf `4980`.
- SKR04 regelmäßig: `1370` auf `6850`.
- Betrag genau `100,00 EUR` fällt nicht unter diese Kleinbetragsregel.
- Soll/Haben und Gegenkonto aus der Ursprungsbuchung ableiten; niemals raten.
- Zielkonto und Kontenfunktion im konkreten DATEV-Wirtschaftsjahr live bestätigen. Bei Branchen- oder Individualkontenrahmen nach Kontenfunktion auflösen und bei Mehrdeutigkeit keinen Buchungsvorschlag erzeugen.

Diese Regel ist eine Kanzleiregel, keine gesetzliche Betragsgrenze.

### Schutzgrenzen

- Die vorgeschaltete Abschlussvorbereitung ist lesend und erzeugt nur Vorschläge.
- Sie ist kein Review des vollständigen Jahresabschlusses und bestätigt keine Abschlussreife.
- OPOS nicht automatisch ausziffern.
- Buchungen nicht automatisch nach DATEV importieren.
- Mandantenprofil, Abgrenzungsregister und Review-Sheet nicht ohne gesonderte Freigabe überschreiben.
- Keine allgemeine Datenanalyse durchführen. Belege und Einzelbuchungen nur insoweit vertiefen, wie ein konkreter Checklisten-Saldo, OPOS oder Registerpunkt erklärt werden muss.

### Lohnkonten aus dem freigegebenen Monatsprozess

Die Abschlussvorbereitung übernimmt die bereits verwendete fachliche Monatsultimo-Logik und wendet sie auf den Abschlussstichtag an:

- SKR03 regelmäßig 1740, 1741, 1742 und 1755 immer prüfen; bei bestätigtem Schätzverfahren zusätzlich 1759.
- SKR04 funktional regelmäßig 3720, 3730, 3740 und 3790; bei bestätigtem Schätzverfahren zusätzlich 3759.
- 1740/3720 ist bei vielen Mandanten null. Eine zulässige Abweichung muss durch Mandantenprofil, Lohnjournal und Zahlung erklärt sein.
- 1741/3730 ist nicht pauschal null, sondern entspricht regelmäßig der noch offenen Lohnsteueranmeldung des letzten Abrechnungsmonats.
- 1742/3740 ist bei Nicht-Schätzmandanten grundsätzlich null, sofern keine dokumentierte Ausnahme besteht. Bei Schätzmandanten kann die endgültige Abrechnung eine Restschuld oder Forderung ergeben.
- 1755/3790 muss nach vollständiger Lohnverbuchung null sein.
- 1759/3759 ist nur bei bestätigtem Schätzverfahren relevant und soll nach Zahlung der Schätzung grundsätzlich null sein.

Konten und Kontenfunktionen im konkreten DATEV-Kontenplan live bestätigen. Branchen- oder Individualkonten nicht auf Standardnummern zwingen.

## Aus dem vorhandenen Monatsprozess übernommen

Die SharePoint-Ablage ist derzeit konfiguriert als:

- Site: `https://burchardtkollegen.sharepoint.com/sites/Wissen`
- Bibliothek: `Mandantenbesonderheiten`
- Mandantenprofil: `Mandantenprofile/<Mandantennummer>.md`
- Abgrenzungsregister: `Abgrenzungsregister/<Mandantennummer>.md`

Diese Ablage ist auch für die Abschlussvorbereitung verbindlich. Die eigenständige Bibliothek wurde am 20.09.2026 live bestätigt; einzelne Mandantenprofile werden erst mit eindeutigem Mandanten direkt gelesen. Ein gleichnamiger Ordner unter `Freigegebene Dokumente` ist kein Ersatz.

### Eröffnungsbilanz und OPOS

Handelsrecht und Steuerrecht getrennt nachweisen. Standardtoleranz für EUR-Abgleiche: `0.005 EUR`, keine Wesentlichkeitsgrenze. Eigenständiges Eröffnungsbilanz-Arbeitspapier nach `EROEFFNUNGSBILANZ.md` erstellen. OPOS beider Seiten zusätzlich zum historischen Abschlussstichtag gegen den letzten verfügbaren Buchhaltungsstand abstimmen; die 31-Tage-Frist des Geldtransits gilt dafür nicht.

## Noch zu entscheiden

Die folgenden Punkte blockieren den Entwurf nicht, aber die Produktivfreigabe:

1. Review-Sheet-Datei, Blattnamen, Tabellenköpfe, Formeln und Zielablage.
2. Ob die im Monatsbuchhaltungsprozess verwendete Abgrenzungs-Kleinbetragsgrenze von 800 EUR auch für diese Vorbereitungsstufe gilt. Bis zur Bestätigung nur Registerabgleich durchführen; keine neue Abgrenzung allein aufgrund dieser Grenze verwerfen.
3. Maximale Größe eindeutiger OPOS-Kombinationen. Entwurfsstandard: höchstens fünf Komponenten innerhalb desselben Personenkontos und nur bei eindeutig genau einer Lösung.
4. Zeitraum im Folgejahr zur Erklärung von Geldtransit und Stichtagsbuchungen. Entwurfsstandard: 31 Kalendertage, sofern das Folgejahr in DATEV verfügbar ist.
5. Ob und wo ein freigegebenes Review-Sheet sowie Mitarbeiterergebnisse auf SharePoint abgelegt werden dürfen.
6. Welche Rechtsformen, Gewinnermittlungsarten und Branchenkontenrahmen im Pilot enthalten sind.
7. Welche Stichtagsunterlagen je Mandantengruppe zwingend als Startblocker gelten; bis dahin gelten die Kernthemen aus `STARTKLARHEITS_CHECKLISTE.md`.
