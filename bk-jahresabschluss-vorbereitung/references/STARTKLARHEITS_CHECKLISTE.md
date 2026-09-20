# Startklarheits-Checkliste für die Abschlussbearbeitung

## Zweck

Diese Checkliste beantwortet ausschließlich: Welche buchhalterischen Vorarbeiten und Nachweise müssen abgearbeitet sein, damit ein Mitarbeiter sinnvoll mit dem Jahresabschluss beginnen kann?

Sie ist keine allgemeine Datenanalyse. Rechnungsnummernlücken, generische Doppelbuchungssuchen, allgemeine Gegenkonto-Anomalien oder sonstige forensische Prüfungen gehören nicht in diesen Skill.

## Vollständige Kontenabdeckung

1. Aus Summen- und Saldenliste sowie Live-Kontenplan alle im Zieljahr bebuchten oder am Stichtag nicht auf null stehenden Bilanzkonten ermitteln.
2. Die unten genannten Kernthemen auch dann aufnehmen, wenn die dazugehörigen Konten am Stichtag null sind.
3. Jedes ermittelte Bilanzkonto genau einem Checklisteneintrag zuordnen.
4. Ein nicht zugeordnetes Bilanzkonto als `ZU_BEREINIGEN` mit `blocks_start: true` ausweisen. Es darf nicht stillschweigend unter „sonstige Konten“ verschwinden.
5. Kontenbezeichnungen und Kontenzwecke aus dem konkreten DATEV-Wirtschaftsjahr verwenden. Die genannten SKR03-/SKR04-Konten sind Beispiele und müssen live bestätigt werden.

## Null- und Nachweislogik

- `MUSS_NULL`: Ein reines technisches Verrechnungskonto muss nach Abarbeitung null sein. Eine Abweichung ist ein Startblocker.
- `NULL_ODER_NACHWEIS`: Null ist der Regelfall; ein Stichtagssaldo ist nur mit einem konkreten, centgenauen Nachweis zulässig.
- `KEINE_NULLERWARTUNG`: Ein Saldo kann regulär bestehen, muss aber mit der maßgeblichen externen Unterlage oder einem Register abgestimmt sein.

„Abgestimmt“ bedeutet in dieser Vorbereitungsstufe nur, dass Saldo, Quelle und zeitlicher Bezug nachvollziehbar zusammenpassen. Es ist kein Bilanzierungs- oder Bewertungsurteil.

## Verbindliche Kernthemen

| `topic_id` | Thema | Regelmäßige Kontenbeispiele | Erwartung und Vorbereitungsergebnis |
|---|---|---|---|
| `quellen_datenstand` | Datenstand und Pflichtquellen | keine | Mandant, Zieljahr, Kontenplan, Summen und Salden, Einzelbuchungen, OPOS, Mandantenprofil und erforderliche Register sind eindeutig gebunden und mit Abrufstand dokumentiert. |
| `eroeffnungsbilanz` | Eröffnungsbilanz und Bereichsabdeckung | Handelsrecht und Steuerrecht getrennt | Je Prüflinie endgültige Schlusswerte gegen Eröffnungswerte kontengleich, mit zulässigen Gruppen oder final belegter Ergebnisbrücke abstimmen. Unvollständige steuerliche Herleitung ist TEILNACHWEIS und Startblocker. Bei EÜR begründet nicht anwendbar. |
| `bilanzkonten_abdeckung` | Vollständige Kontenabdeckung | alle bebuchten oder nicht auf null stehenden Bilanzkonten | Jedes Konto ist genau einem Thema zugeordnet. Unklassifizierte Konten blockieren den Start. |
| `opos_debitoren` | Debitoren und offene Forderungen | Personenkonten und belegte Sammelkonten | Posten, Personenkontensalden und Sammelkonten zum gleichen letzten Buchhaltungsstand abstimmen; Abschlussstichtag und spätere Ausgleiche separat nachweisen. Differenzen/Quellenlücken blockieren. Auszifferungsvorschläge separat. |
| `opos_kreditoren` | Kreditoren und offene Verbindlichkeiten | Personenkonten und belegte Sammelkonten | Gleicher dreistufiger Abgleich wie Debitoren; keine Verrechnung zwischen Seiten. |
| `bank_kasse` | Banken, Kassen und Zahlungsdienstleister | aus Mandantenprofil und Live-Kontenplan | Stichtagssalden gegen Bankauszug, Kassenbuch beziehungsweise Anbieterabrechnung abstimmen. Kassen dürfen zu keinem Zeitpunkt negativ sein. |
| `geldtransit` | Geldtransit | SKR03 1360, SKR04 1460 | `NULL_ODER_NACHWEIS`: Null oder centgenau erklärter Banklaufzeitunterschied mit Gegenbuchung und Datum. |
| `durchlaufende_posten` | Durchlaufende Posten | SKR03 1590, SKR04 1370 | `NULL_ODER_NACHWEIS`: Jeder Restposten ist einzeln erklärt. Die bestätigte Unter-100-EUR-Regel anwenden. |
| `lohnkonten` | Lohnverbindlichkeiten und Lohnverrechnung | siehe Lohnlogik unten | Konten einzeln gegen Lohnjournal, Buchungsbeleg, Anmeldung, Beitragsnachweis und Zahlung abstimmen. Keine pauschale Nullregel über alle Lohnkonten. |
| `steuerkonten` | Umsatzsteuer- und sonstige Abrechnungskonten | kontenzweckbezogen | Salden gegen bereits vorliegende Anmeldungen, Bescheide, Zahlungen und Steuerkontoauszüge abstimmen. Keine Steuerberechnung oder Steuererklärung erstellen. |
| `abgrenzungen` | ARAP/PRAP beziehungsweise EÜR-Zu-/Abfluss | kontenzweckbezogen | DATEV-Buchungen und SharePoint-Register vollständig gegeneinander abstimmen; Bewertungsfragen an den Abschluss übergeben. |
| `vorjahr_rollforward` | Vorjahresbuchungen und offene Vorjahrespunkte | keine feste Kontonummer | Abschlussnahe Vorjahresbuchungen und offene Arbeitspunkte als Hinweise übertragen, ohne Betrag oder Buchung zu übernehmen. |

## Lohnkonten – verbindliche Einzellogik

| Funktion | SKR03 regelmäßig | SKR04 regelmäßig | Vorbereitung zum Stichtag |
|---|---:|---:|---|
| Verbindlichkeiten aus Lohn und Gehalt | 1740 | 3720 | Bei vielen Mandanten null. Ein Rest muss der noch offenen Nettolohnzahlung entsprechen und durch Lohnjournal/Buchungsbeleg sowie Zahlungsnachweis erklärt sein. Die Mandantenbesonderheit ist maßgeblich. |
| Verbindlichkeiten aus Lohn- und Kirchensteuer | 1741 | 3730 | Nicht pauschal null. Der Saldo entspricht regelmäßig der noch offenen Lohnsteueranmeldung des letzten Abrechnungsmonats und ist centgenau gegen Anmeldung, Lohnjournal und Zahlung abzustimmen. |
| Verbindlichkeiten im Rahmen der sozialen Sicherheit | 1742 | 3740 | Bei Nicht-Schätzmandanten grundsätzlich null, sofern keine dokumentierte Ausnahme besteht. Bei Schätzmandanten kann nach der endgültigen Abrechnung eine Restschuld oder Forderung bestehen. |
| Voraussichtliche Beitragsschuld | 1759 | 3759 | Nur bei bestätigtem Schätzverfahren prüfen. Nach Zahlung der Schätzung grundsätzlich null; Rest gegen Beitragsnachweis und Restbetragslogik erklären. |
| Lohn- und Gehaltsverrechnung | 1755 | 3790 | `MUSS_NULL` nach vollständiger Verbuchung des Lohnbelegs. Jede Differenz zeilenweise aufklären. |

Zusätzlich verwendete Lohnkonten, insbesondere Einbehaltungen, Vermögensbildung, bAV/VWL, Abschläge oder Krankenkassen-Personenkonten, aus Mandantenprofil und Live-Kontenplan ergänzen. Sie dürfen nicht allein deshalb entfallen, weil sie nicht in der Standardtabelle stehen.

## Bedingte Vorbereitungsthemen

Diese Themen aufnehmen, sobald im Kontenplan, Mandantenprofil, Vorjahr oder Datenbestand ein einschlägiges Konto beziehungsweise Register vorhanden ist:

| `topic_id` | Thema | Vorbereitung | Grenze zum eigentlichen Abschluss |
|---|---|---|---|
| `anlagen_nebenbuch` | Anlagenbuchführung | Anlagenkonten, vorhandene Inventare, Zugangs-/Abgangsbelege und Nebenbuchstatus zusammenstellen. | Keine Aktivierungs-, Nutzungsdauer-, AfA- oder Bewertungsentscheidung. |
| `vorrat_inventur` | Vorräte und Inventur | Vorhandensein, Stichtag und Verantwortlichkeit der Inventurunterlagen dokumentieren. | Keine Mengen- oder Vorratsbewertung. |
| `darlehen` | Darlehen | Kontensaldo gegen Saldenbestätigung/Tilgungsplan abstimmen und fehlende Unterlagen anfordern. | Keine Zinsabgrenzung, Restlaufzeit- oder Bewertungsentscheidung abschließend treffen. |
| `rueckstellungen` | Rückstellungen | Vorjahresbestand und vorhandenes Rückstellungsregister als Roll-forward-Liste bereitstellen. | Keine Vollständigkeits- oder Höhenberechnung. |
| `gesellschafter_privat` | Gesellschafter-, Gesellschafts- und Privatkonten | Saldo, Bewegungen, Nachweise und Mandantenbesonderheiten zusammenstellen. | Keine rechtliche oder steuerliche Würdigung. |
| `anzahlungen_kautionen` | Anzahlungen, Kautionen und Gutscheine | Einzelbestand beziehungsweise Register und Belege zusammenstellen. | Keine abschließende Ausweis- oder Bewertungsentscheidung. |
| `sonstige_abstimmkonten` | Weitere Interim-/Verrechnungskonten | Kontenzweck bestimmen und jeden Saldo auflösen oder belegen. | Nicht als generische Datenanalyse auf andere GuV-Konten ausweiten. |

## Arbeitsspuren und Startblocker

Jeder Checklisteneintrag wird genau einer Arbeitsspur zugeordnet:

- `ERLEDIGT`: auf null oder mit zulässigem Nachweis abgestimmt.
- `VOR_START_BEREINIGEN`: technische Bereinigung oder eindeutige Umbuchung ist noch erforderlich; `blocks_start: true`.
- `UNTERLAGE_ANFORDERN`: für die Vorbereitung erforderlicher Nachweis fehlt; regelmäßig `blocks_start: true`.
- `IM_ABSCHLUSS_PRUEFEN`: Unterlagen und Saldo sind vorbereitet, die fachliche Bilanzierungs-/Bewertungsentscheidung gehört in den eigentlichen Abschluss; `blocks_start: false`.

`STARTKLAR_FUER_ABSCHLUSSBEARBEITUNG` ist nur zulässig, wenn alle Kernthemen vorkommen, bei Bilanzierung beide Prüflinien Handelsrecht und Steuerrecht abgestimmt oder fachlich nachgewiesen nicht anwendbar sind, beide OPOS-Seiten aktuell und zum Abschlussstichtag abgestimmt sind, kein Bilanzkonto unklassifiziert ist und kein Checklisteneintrag mit `blocks_start: true` offen bleibt. Dieser Status bestätigt ausdrücklich nicht die Vollständigkeit oder Richtigkeit des Jahresabschlusses.
