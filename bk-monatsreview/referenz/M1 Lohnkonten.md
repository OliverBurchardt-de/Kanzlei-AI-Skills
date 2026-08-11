# M1 Lohnkonten

## Pflichtunterlagen

- Buchungsbeleg oder Buchungsbericht des Prüfmonats
- Lohnjournal des Prüfmonats
- bei Schätzmandanten: Beitragsnachweise
- ergänzend, wenn vorhanden: Restbetragsrechnung oder „KK SV-Werte – gesamt“

Fehlt eine Pflichtunterlage, ist der betroffene Prüfschritt
`NICHT_PRUEFBAR`.

## Prüfzeitpunkt

Geprüft wird ausschließlich der fachlich richtige Saldo zum Monatsultimo. Der
Folgemonat wird nicht benötigt, um einen Saldo des Prüfmonats zu rechtfertigen.

## Kontenlogik

### 1740 – Verbindlichkeiten aus Lohn und Gehalt

Bei den meisten Mandanten am Monatsultimo null. Die konkrete Regel steht in der
Mandantendatei. Ein abweichender zulässiger Saldo muss dort erklärt sein.

### 1741 – Lohnsteuer

Am Monatsultimo regelmäßig Saldo in Höhe der noch offenen Lohnsteueranmeldung,
da die Zahlung im Folgemonat erfolgt. Gegen Lohnjournal und Buchungsbeleg
centgenau abstimmen.

### 1742 – Sozialversicherung

Bei Nicht-Schätzmandanten grundsätzlich null, soweit die Mandantendatei keine
dokumentierte Ausnahme enthält.

Bei Schätzmandanten zeigt 1742 nach finaler Lohnabrechnung die Restschuld oder
bei Überzahlung eine Forderung.

### 1759 – Voraussichtliche Beitragsschuld

Nur prüfen, wenn die Mandantendatei ausdrücklich `Schätzverfahren: ja` enthält.
Die Schätzung wird auf 1759 geführt und die Zahlung gegen 1759 gebucht. Nach der
Zahlung soll 1759 grundsätzlich null sein. Ein Restsaldo ist zu erklären und in
der Regel zu korrigieren.

Die fachliche Detaillogik ergibt sich aus
`DATEV Logik 1742 1759.md`.

## Weitere Prüfungen

- Lohnbuchung des Monats vorhanden
- 1755 nach Verbuchung des Lohnbelegs ausgeglichen
- Buchungsbeleg zeilenweise gegen die FIBU prüfen
- Lohnjournal gegen 1741 und 1742 prüfen
- Abschlagszahlungen bei Verwendung von 1530 nicht fälschlich auf 1740 buchen
- 1748/1750 nicht über mehrere Monate nur auflaufen lassen

## Status

- fehlende Lohnbuchung, klare Falschkontierung oder unzulässiger Saldo: ROT
- dokumentierbare Ausnahme oder auflaufender Nebenbestand: GELB
- centgenauer Abgleich und passende Monatsultimo-Logik: GRUEN
