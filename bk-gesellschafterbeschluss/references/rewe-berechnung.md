# Berechnung aus Kanzlei-ReWe

Diese Anleitung vollständig anwenden, wenn die Schnittstelle keine fertige Bilanzsumme und kein fertiges Jahresergebnis liefert.

## 1. Datenbasis sichern

1. Mandant über `datev://accounting/clients` mit der Mandantennummer auflösen.
2. Geschäftsjahr ausschließlich über `datev://accounting/fiscal_years` ermitteln. Keine ID aus dem Kalenderjahr ableiten.
3. Kontenlänge und Währung des Geschäftsjahres festhalten.
4. `datev://accounting/accounting_sums_and_balances` vollständig mit `top` und `skip` abrufen. Bis zum Ende weiterblättern.
5. Nur Daten des ausgewählten Geschäftsjahres verwenden.
6. Keine Ressource unter `datev://dms/*` aufrufen.
7. Bei einem vorübergehenden Verbindungsfehler den Accounting-Abruf bis zu dreimal wiederholen und erforderlichenfalls die Seitengröße verkleinern. Bleibt der vollständige Abruf unmöglich, stoppen; niemals ins DMS ausweichen.

## 2. Salden richtig lesen

- Für den Stichtagssaldo `balance` zusammen mit `balance_debit_credit_identifier` verwenden.
- Rechenkonvention: Soll `S` positiv, Haben `H` negativ.
- Monatswerte sind Bewegungen und nicht der Stichtagssaldo. Sie nicht anstelle von `balance` verwenden.
- Beträge nie ohne Soll-/Haben-Kennzeichen addieren.
- Sachkonten von Debitoren und Kreditoren anhand der Kontenlänge trennen.
- Personenkonten für die HGB-seitengerechte Aufteilung verwenden: Debitoren mit Sollsaldo sind Forderungen, Debitoren mit Habensaldo sind auf der Passivseite umzugliedern; Kreditoren mit Habensaldo sind Verbindlichkeiten, Kreditoren mit Sollsaldo sind auf der Aktivseite umzugliedern.
- Die Summe der vorzeichenbehafteten Personenkontensalden mit dem jeweiligen Forderungs- oder Verbindlichkeitssammelkonto abstimmen.
- Sammelkonto und Personenkonten niemals vollständig nebeneinander addieren. Entweder die Personenkonten anstelle des Sammelkontos verwenden oder das Sammelkonto nur um die belegte Seitenumgliederung korrigieren.
- Vortrags- und technische Konten, insbesondere 9000, 9008 und 9009 im SKR03, nicht als Bilanzposition oder GuV-Position addieren.

## 3. Jahresergebnis berechnen

1. Die Sachkonten anhand des beim Mandanten verwendeten Kontenrahmens und der Kontenzwecke in Bilanz- und GuV-Konten einordnen.
2. Eigene oder ungewöhnlich beschriftete Konten nicht allein anhand der Kontenklasse erzwingen. Kontenbeschriftung, Kontenzweck und bei Bedarf die Buchungen des aktuellen Geschäftsjahres prüfen.
3. Für alle GuV-Sachkonten rechnen:

   `Jahresergebnis = Summe annual_value_credit - Summe annual_value_debit`

4. Bilanzkonten, Personenkonten sowie Vortrags- und statistische Konten ausschließen.
5. Positives Ergebnis als Jahresüberschuss, negatives Ergebnis als Jahresfehlbetrag und null als ausgeglichenes Jahresergebnis behandeln.

Kontrollrechnung: Das Ergebnis zusätzlich aus den vorzeichenbehafteten GuV-Endsalden bestimmen. Beide Wege müssen auf Cent genau übereinstimmen. Bei Abweichung die Kontenzuordnung prüfen.

## 4. Bilanzsumme berechnen

1. Bilanz-Sachkonten sowie die für die Seitentrennung erforderlichen Debitoren- und Kreditorensalden verwenden. Personenkonten nicht doppelt neben den Sammelkonten addieren.
2. Jedes Bilanzkonto nach dem Kanzlei-ReWe-Kontenzweck beziehungsweise dem verwendeten Kontenrahmen einer HGB-Bilanzposition zuordnen.
3. Innerhalb jeder HGB-Position Soll- und Habensalden vorzeichenrichtig saldieren. Nicht sämtliche Sollsalden brutto addieren.
4. Wertberichtigungskonten auf der Aktivseite, etwa eine Pauschalwertberichtigung zu Forderungen, mit ihrem Habensaldo abziehen.
5. Debitoren- und Kreditorensalden nach Soll und Haben trennen. Kreditorische Debitoren und debitorische Kreditoren auf die richtige Bilanzseite umgliedern; die Sammelkonten entsprechend ersetzen oder korrigieren.
6. Zusammengehörige Steuerkonten, insbesondere Umsatzsteuer- und Vorsteuerkonten, entsprechend ihrer HGB-Zuordnung saldieren. Konten mit eigenständiger HGB-Zuordnung nicht unbesehen in eine Gesamtsaldierung einbeziehen.
7. Die Aktivpositionen nach Saldierung und Seitenumgliederung addieren. Diese Summe ist die Bilanzsumme.
8. Die Passivseite unabhängig aufbauen. Prüfen, ob das laufende Jahresergebnis bereits auf ein Eigenkapitalkonto abgeschlossen wurde; das Ergebnis niemals doppelt einbeziehen.

## 5. Pflichtkontrollen

- Vollständigkeit: Alle Seiten der Summen und Salden sind eingelesen.
- Geschäftsjahr: Mandant, Beginn und Ende des Wirtschaftsjahres stimmen mit dem Auftrag überein.
- GuV: Ergebnis aus Jahresverkehrszahlen und Ergebnis aus GuV-Endsalden stimmen auf Cent überein.
- Bilanz: Aktiv- und Passivseite stimmen einschließlich des noch nicht abgeschlossenen Jahresergebnisses auf Cent überein.
- Doppelzählung: Personenkonten, Sammelkonten und Vortragskonten wurden nicht doppelt erfasst.
- Abweichung: Bei einer Differenz zuerst Kontenzuordnung, Soll/Haben-Richtung, USt-Saldierung und Abschlussbuchungen prüfen. Nur bei nicht auflösbarer Differenz stoppen und den Nutzer gezielt informieren.

Die Berechnung ist zulässig und ausdrücklich vorgesehen. Das Fehlen fertiger Berichtszeilen in der Schnittstelle ist kein Abbruchgrund.
