# Verbindliche Prüflogik

Diese Prüfungen gelten ausschließlich für die definierten Aufräumarbeiten. Ein unauffälliges Modul ist keine Aussage über den vollständigen Jahresabschluss.

## 0. Startklarheits-Matrix und Kontenabdeckung

Die Matrix nach `STARTKLARHEITS_CHECKLISTE.md` ist der führende Arbeitsplan.

1. Alle im Zieljahr bebuchten oder am Stichtag nicht auf null stehenden Bilanzkonten inventarisieren.
2. Jedes Konto genau einem Checklisteneintrag zuordnen.
3. Die verbindlichen Kernthemen auch bei Nullsaldo oder `NICHT_ANWENDBAR` dokumentieren.
4. Je Eintrag `zero_expectation`, Stichtagssaldo, Nachweise, `work_lane`, `blocks_start` und nächsten Schritt festhalten.
5. Ein nicht zugeordnetes Konto oder ein offener Eintrag mit `blocks_start: true` verhindert `STARTKLAR_FUER_ABSCHLUSSBEARBEITUNG`.

## 1. Debitoren, Kreditoren und OPOS

### Inventar

Zum Abschlussstichtag getrennt ausgeben:

1. Debitorenstamm: Konto, Name, relevante Stammdaten und OPOS-Saldo.
2. Kreditorenstamm: Konto, Name, relevante Stammdaten und OPOS-Saldo.
3. Alle logischen offenen Debitorenposten.
4. Alle logischen offenen Kreditorenposten.

Verdichtete OPOS sind maßgeblich. Komponenten dienen nur zur Erklärung. Jede Liste nennt Stichtag, Währung, Rechnungsdatum, Fälligkeit, Belegfeld, offenen Betrag und Altersklasse.

### Auszifferungskandidaten

Eine Auszifferung ist keine Buchung. Nur innerhalb desselben Personenkontos und derselben Währung suchen. Priorität:

1. Eindeutige Gegenposten mit identischem Belegfeld und centgenauer Summe null.
2. Eindeutige betragsgleiche Rechnung und Zahlung/Gutschrift mit belastbarem zeitlichem und textlichem Zusammenhang.
3. Eindeutige Kombination aus höchstens fünf Komponenten mit centgenauer Summe null.

`AUSZIFFERBAR` nur, wenn genau eine plausible Kombination existiert und kein Teilposten bereits einem anderen Kandidaten zugeordnet ist. Andernfalls `FACHLICH_ZU_KLAEREN`.

Nie automatisch:

- über verschiedene Personenkonten verrechnen,
- Debitor und Kreditor desselben Geschäftspartners verrechnen,
- Restdifferenzen ausbuchen,
- Wertberichtigungen bilden,
- eine Zahlung allein wegen Betragsgleichheit zuordnen, wenn mehrere Lösungen bestehen.

## 2. Geldtransit

Funktionales Konto live auflösen:

| Kontenrahmen | Regelmäßiges Konto | Funktion |
|---|---:|---|
| SKR03 | 1360 | Geldtransit |
| SKR04 | 1460 | Geldtransit |

Prüfung:

1. Saldo zum Abschlussstichtag ermitteln.
2. Alle offenen Komponenten des Saldos auf Einzelbuchungsebene erklären.
3. Soweit verfügbar, die ersten 31 Tage des Folgejahres auf eindeutige Gegenbuchungen prüfen.
4. Saldo null: `AUF_NULL`.
5. Eindeutig dokumentierter Banklaufzeitunterschied: `ABGESTIMMT` mit Gegenbuchung und Datum als Nachweis (`evidence_refs`); nicht automatisch umbuchen.
6. Ungeklärter oder dauerhaft stehengebliebener Betrag: `FACHLICH_ZU_KLAEREN` mit konkreter Mitarbeiteraufgabe.

## 3. Durchlaufende Posten

Funktionales Konto live auflösen:

| Kontenrahmen | Regelmäßiges Konto | Aufwand Kleinbetragsregel |
|---|---:|---:|
| SKR03 | 1590 | 4980 Sonstiger Betriebsbedarf |
| SKR04 | 1370 | 6850 Sonstiger Betriebsbedarf |

Das Konto vollständig bis auf Einzelbuchungsebene lesen. Einzelbeträge nicht saldieren, um die 100-EUR-Grenze zu prüfen.

### Absoluter Einzelbetrag unter 100 EUR

- `BUCHUNGSVORSCHLAG` vom funktionalen Konto `Durchlaufende Posten` auf `Sonstiger Betriebsbedarf`.
- Bruttobetrag, kein Vorsteuerabzug, kein Steuerschlüssel.
- Soll/Haben und Gegenkonto aus der Ursprungsbuchung erhalten.
- Zielkonto im live gelesenen Kontenplan bestätigen.
- Betrag genau 100 EUR nicht einschließen.

### Einzelbetrag ab 100 EUR

Nicht automatisch auf Aufwand buchen. Je Posten dokumentieren: Zahlungsrichtung, Partner, Vorgang, Datum, Betrag, Alter, Gegenkonto, Buchungstext, vorhandener Beleg/Registerbezug, Beanstandung und nächsten Schritt.

## 4. ARAP/PRAP und Register

### Bilanz

ARAP und PRAP nach Kontenfunktion, nicht nach einer geratenen Kontonummer bestimmen.

- ARAP: Ausgabe vor dem Stichtag, Aufwand für eine bestimmte Zeit nach dem Stichtag.
- PRAP: Einnahme vor dem Stichtag, Ertrag für eine bestimmte Zeit nach dem Stichtag.
- Aufwand/Ertrag vor dem Stichtag mit Zahlung danach ist kein ARAP/PRAP-Fall. Solche antizipativen Fälle getrennt als sonstige Forderung/Verbindlichkeit beziehungsweise Rückstellung prüfen.

Für jeden Registereintrag und jede DATEV-Buchung abgleichen:

- Abgrenzungs-ID, Typ, Geschäftspartner und Beschreibung,
- Ursprungsbeleg und Belegfeld,
- Leistungsbeginn/-ende,
- ursprünglicher abzugrenzender Betrag,
- Buchungen und Auflösungen des Zieljahrs,
- Soll-Restbetrag und DATEV-Istsaldo am Stichtag,
- Konten und Saldenseite.

Abweichungskategorien:

1. Registereintrag ohne DATEV-Buchung.
2. DATEV-Buchung ohne Registereintrag.
3. falscher Betrag oder Zeitraum.
4. fehlende, doppelte oder zu frühe Auflösung.
5. vollständig aufgelöster Altfall noch offen.
6. falsche Saldenseite oder falsche Abgrenzungsart.
7. doppelter Registereintrag.

Eine unbestätigte interne Kleinbetragsgrenze nicht als Gesetz darstellen und nicht zur automatischen Eliminierung eines Falls verwenden.

### EÜR: Zu-/Abfluss und Fälligkeit

Bei Gewinnermittlung nach § 4 Abs. 3 EStG grundsätzlich keine ARAP-/PRAP-Prüfung wie bei Bilanzierenden durchführen. Stattdessen:

1. Zahlungsdatum und wirtschaftliche Zugehörigkeit getrennt erfassen.
2. Regelmäßig wiederkehrende Einnahmen/Ausgaben im Zehn-Tages-Zeitraum gesondert prüfen.
3. Für die Ausnahme müssen Zahlung und Fälligkeit innerhalb des Zehn-Tages-Zeitraums liegen; die aktuelle amtliche Regel und Sonderfälle prüfen.
4. Sonderregeln, insbesondere für langfristige Nutzungsüberlassung, Anlagevermögen und durchlaufende Posten, getrennt kennzeichnen.

Fälligkeit ist damit ein eigenes Prüffeld und darf nicht aus Buchungsdatum oder Leistungszeitraum geraten werden.

## 5. Lohnkonten zum Abschlussstichtag

Die Konten nach Funktion im Live-Kontenplan auflösen. Bei Standardkontenrahmen regelmäßig:

| Funktion | SKR03 | SKR04 | Null-/Nachweisregel |
|---|---:|---:|---|
| Verbindlichkeiten aus Lohn und Gehalt | 1740 | 3720 | Bei vielen Mandanten null; andernfalls offene Nettolöhne centgenau durch Lohnjournal/Buchungsbeleg und Zahlung erklären. |
| Verbindlichkeiten aus Lohn- und Kirchensteuer | 1741 | 3730 | Nicht pauschal null; gegen offene Lohnsteueranmeldung, Lohnjournal und Zahlung abstimmen. |
| Verbindlichkeiten im Rahmen der sozialen Sicherheit | 1742 | 3740 | Nicht-Schätzmandanten grundsätzlich null, sofern keine dokumentierte Ausnahme; Schätzmandanten nach Restbetragslogik. |
| Voraussichtliche Beitragsschuld | 1759 | 3759 | Nur bei Schätzverfahren; nach Zahlung grundsätzlich null, Rest centgenau erklären. |
| Lohn- und Gehaltsverrechnung | 1755 | 3790 | `MUSS_NULL`; Differenzen zeilenweise klären. |

Zusätzlich verwendete Lohnkonten aus Kontenplan und Mandantenprofil ergänzen. Fehlen Lohnjournal, Buchungsbeleg, Anmeldung oder Beitragsnachweis für einen betroffenen Abgleich, `UNTERLAGE_FEHLT` statt einer Saldoaussage ausgeben.

## 6. Weitere Abschlussvorbereitungsbereiche

### Bank, Kasse und Zahlungsdienstleister

- Alle im Mandantenprofil oder Kontenplan geführten Bestände erfassen.
- Bank gegen Stichtagskontoauszug, Kasse gegen Kassenbuch und Zahlungsdienstleister gegen Anbieterabrechnung abstimmen.
- Negative Kassenbestände sind `ZU_BEREINIGEN` und Startblocker.
- Keine allgemeine Banktransaktionsanalyse durchführen.

### Steuerkonten

- Konten nach Kontenzweck gruppieren und gegen bereits vorliegende Anmeldungen, Bescheide, Zahlungen und Steuerkontoauszüge abstimmen.
- Nur die buchhalterische Übereinstimmung der vorhandenen Unterlagen prüfen; keine Steuer neu berechnen und keine Erklärung erstellen.

### Bedingte Themen

Anlagen, Vorräte, Darlehen, Rückstellungen, Gesellschafter-/Privatkonten, Anzahlungen, Kautionen, Gutscheine und weitere Abstimmkonten nur aufnehmen, wenn ein einschlägiges Konto, Register, Vorjahreshinweis oder eine Mandantenbesonderheit vorhanden ist. In dieser Stufe Unterlagen und Salden vorbereiten; Bilanzierung, Bewertung und rechtliche Würdigung an `handoff_to_annual_close` übergeben.
