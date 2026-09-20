# OPOS gegen den letzten Buchhaltungsstand abstimmen

## Zwei Zeitbezüge verbindlich trennen

Ermittle den letzten tatsächlich verfügbaren verarbeiteten Buchhaltungsstand aus DATEV, einschließlich vorhandener Folgejahre. Dokumentiere Jahres-ID, Buchungen bis, Abrufzeit, Stapelstand und Vollständigkeit; das heutige Datum ist kein Beweis für aktuelle Buchführung. Noch nicht verarbeitete Stapel nicht als gebucht behandeln.

1. **Aktueller Abgleich:** Debitoren- und Kreditoren-OPOS gegen Buchhaltung mit demselben Datenstand und zeitlichen Umfang prüfen.
2. **Abschlussstichtag und Fortschreibung:** Zum Abschlussstichtag offene Posten separat nachweisen und deren Ausgleich bis zum letzten verfügbaren Buchhaltungsstand verfolgen. Neue Folgejahresrechnungen, Zahlungen, Teilzahlungen, Gutschriften und Umbuchungen getrennt halten. Die 31-Tage-Frist des Geldtransit-Moduls begrenzt diesen OPOS-Abgleich nicht.

Ein Filter `date le <Stichtag>` auf heute offenen Posten stellt keinen historischen OPOS-Bestand her: später bezahlte Rechnungen fehlen dann. Ohne historische OPOS-Auswertung oder vollständige rekonstruierbare Komponenten einschließlich später ausgeglichener Posten den Stichtagsvergleich `NICHT_PRUEFBAR` ausweisen. Aktuellen Abgleich trotzdem durchführen; fehlenden historischen Nachweis nicht durch ihn ersetzen.

## Vollständige Bestände und Identitäten

Vor jedem Abruf `datev_describe`. Verdichtete `condensed_accounts_receivable`/`condensed_accounts_payable` verwenden; kein `top`/`skip`. Bei Mengenbegrenzungen nach vollständigem Personenkonten-Inventar disjunkt partitionieren; alle Teilabrufe protokollieren. Positive wie negative offene Salden lesen, nicht nur Forderungen größer null. Komponenten nur zur Erklärung und Rekonstruktion; nie zusätzlich zur verdichteten Summe zählen.

Alle im OPOS-Bestand **oder** in der Buchhaltung vorhandenen Personenkonten aufnehmen, einschließlich Saldo null mit offenen Gegenposten. Für aktuelle OPOS nicht unbesehen mehrere Wirtschaftsjahre addieren: Vorträge und mitgeführte Posten würden doppelt gezählt. Jahresübergänge mit Herkunfts-ID und Vortragsnachweis verbinden.

Abgleichsschlüssel: Mandant, Seite, Wirtschaftsjahr/Datenstand, Personenkonto, Währung sowie belastbare Beleg-/Postenidentität. Debitoren-`open_item_number` nach Ressourcenbeschreibung verwenden; bei Kreditoren ist sie optional und kein universeller Rechnungsschlüssel. Fehlende Identität oder Mehrdeutigkeit offen ausweisen, nicht gleiche Beträge automatisch paaren.

## Abstimmung auf drei Ebenen

1. Je logischem offenen Posten Rechnung, Zahlung/Gutschrift, Teilzahlungen und Restbetrag anhand Personenkontenbuchungen nachvollziehen. Auszifferungsstatus gegen den tatsächlich gebuchten Ausgleich prüfen; ungebuchte Bankbewegungen beweisen keine Verbuchung.
2. Je Personenkonto/Währung Summe der vorzeichenrichtig offenen Posten gegen den belegten Fibu-Endsaldo vergleichen. Monatsverkehrszahlen sind Bewegungen: Endsaldo aus bestätigtem Anfangsbestand plus vollständigen Bewegungen ableiten oder aus eindeutiger Saldenauswertung lesen. Soll positiv/Haben negativ für beide Seiten; keine Betragsaddition ohne Richtung. Fehlende Seite nur bei nachgewiesen vollständigem Inventar als null behandeln.
3. Summe der Personenkonten gegen die aus dem Live-Kontenplan belegten Forderungs-/Verbindlichkeitssammelkonten und deren Buchungen abstimmen. Debitorische Kreditoren, kreditorische Debitoren sowie dokumentierte Ausweis-/Umbuchungsfälle einzeln überleiten. Direkte Sammelkontenbuchungen, fehlende OPOS-Führung, Vorträge und ungeklärte Differenzen ausweisen; keine fiktiven Einzel-OPOS aus Sammelkonten ableiten.

Jede Ebene getrennt beurteilen. Eine passende Gesamtsumme heilt keine gegenläufigen Kontendifferenzen. Keine Verrechnung zwischen Debitoren und Kreditoren, Geschäftspartnern, Währungen oder Rechnungslegungsbereichen. Bei unterschiedlichen Währungen nur belegte Buchwerte und Umrechnungen verwenden.

## Ergebnis und Quellen

Je Seite sowie je Konto/Posten: Vergleichsdatum, Buchhaltungsstand, OPOS-Restbetrag, Fibu-Saldo/Rest, Differenz, Status, Nachweise, Erklärung und nächster Schritt. Toleranz für EUR `0.005`, bei Centbeträgen somit keine Restdifferenz.

Kategorien: `NUR_OPOS`, `NUR_FIBU`, `BETRAGSDIFFERENZ`, `AUSGLEICH_NICHT_ABGEBILDET`, `STICHTAGSVERSCHIEBUNG`, `MEHRDEUTIGE_ZUORDNUNG`, `SAMMELKONTODIFFERENZ`, `QUELLE_UNVOLLSTAENDIG`. Spätere Zahlungen dokumentiert fortschreiben; sie sind für sich kein Stichtagsfehler.

`ABGESTIMMT` erst bei vollständigen Beständen, gleichem Datenstand und belegtem Abgleich aller drei Ebenen. `TEILNACHWEIS` bei begrenzter Abdeckung, `FACHLICH_ZU_KLAEREN` bei offenen Differenzen, `NICHT_PRUEFBAR` bei fehlender Vergleichsgrundlage. Alle offenen Abstimm-/Quellenlücken sind Startblocker. Ein regulär offener, belegter und abgestimmter Posten ist allein wegen seines offenen Betrags kein Startblocker.

Aktuelle und historische Ergebnisse sowie Fortschreibung in `open_items.reconciliation` dokumentieren. Ausgabe: getrennte Debitoren-/Kreditorentabellen und konkrete Mitarbeiteraufgaben. Auszifferungskandidaten nach `PRUEFLOGIK.md` separat ausgeben; nichts ausziffern oder buchen.
