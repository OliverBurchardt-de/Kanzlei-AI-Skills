# OPOS gegen den letzten Buchhaltungsstand abstimmen

## Zwei Zeitbezüge verbindlich trennen

Ermittle den letzten tatsächlich verfügbaren verarbeiteten Buchhaltungsstand aus DATEV, einschließlich vorhandener Folgejahre. Dokumentiere Jahres-ID, Buchungen bis, Abrufzeit, Stapelstand und Vollständigkeit; das heutige Datum ist kein Beweis für aktuelle Buchführung. Noch nicht verarbeitete Stapel nicht als gebucht behandeln.

1. **Aktueller Abgleich:** Debitoren- und Kreditoren-OPOS gegen Buchhaltung mit demselben Datenstand und zeitlichen Umfang prüfen.
2. **Abschlussstichtag und Fortschreibung:** Zum Abschlussstichtag offene Posten separat nachweisen und deren Ausgleich bis zum letzten verfügbaren Buchhaltungsstand verfolgen. Neue Folgejahresrechnungen, Zahlungen, Teilzahlungen, Gutschriften und Umbuchungen getrennt halten. Die 31-Tage-Frist des Geldtransit-Moduls begrenzt diesen OPOS-Abgleich nicht.

Ein Datumsfilter wie `due_before` auf heute offenen Posten stellt keinen historischen OPOS-Bestand her: später bezahlte Rechnungen fehlen dann. Ausgeglichene Posten mit `status=all` beziehungsweise `status=cleared` einbeziehen; ein Stichtagsbestand ist daraus nur rekonstruierbar, wenn je Posten Belegdatum und Ausgleich nachvollziehbar geliefert werden. Ohne historische OPOS-Auswertung oder vollständige rekonstruierbare Posten einschließlich später ausgeglichener Posten den Stichtagsvergleich `NICHT_PRUEFBAR` ausweisen. Aktuellen Abgleich trotzdem durchführen; fehlenden historischen Nachweis nicht durch ihn ersetzen.

## Vollständige Bestände und Identitäten

Offene Posten mit `datev_get_open_items` je Seite (`side=receivable`, `side=payable`) und `fiscal_year` über den Riecken-Connector lesen. Jede Position ist ein OPOS-Posten (Konto + Belegfeld 1); `totals.open_sum` ist der fertige Saldo der DATEV-OPOS-Liste und wird nicht selbst nachgerechnet. `limit` so setzen, dass alle Posten geliefert werden; bei Abschneidung nach dem vollständigen Personenkonten-Inventar aus `datev_search_business_partners` je `business_partner` disjunkt partitionieren; alle Teilabrufe protokollieren. Positive wie negative offene Salden lesen, nicht nur Forderungen größer null. Einzelbuchungen des Personenkontos (`datev_get_account_postings`) nur zur Erklärung und Rekonstruktion; nie zusätzlich zur Summe des Connectors zählen.

Alle im OPOS-Bestand **oder** in der Buchhaltung vorhandenen Personenkonten aufnehmen, einschließlich Saldo null mit offenen Gegenposten. Für aktuelle OPOS nicht unbesehen mehrere Wirtschaftsjahre addieren: Vorträge und mitgeführte Posten würden doppelt gezählt. Jahresübergänge mit Herkunfts-ID und Vortragsnachweis verbinden.

Abgleichsschlüssel: Mandant, Seite, Wirtschaftsjahr/Datenstand, Personenkonto, Währung sowie belastbare Beleg-/Postenidentität. Postenidentität ist Konto plus Belegfeld 1, wie vom Connector geliefert; Belegfeld 1 ist insbesondere bei Kreditoren kein universeller Rechnungsschlüssel. Fehlende Identität oder Mehrdeutigkeit offen ausweisen, nicht gleiche Beträge automatisch paaren.

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
