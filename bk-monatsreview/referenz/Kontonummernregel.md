# DATEV-Kontonummernregel

Die Sachkontenlänge wird immer aus den DATEV-Metadaten des konkreten
Wirtschaftsjahres (`account_length`) übernommen. Sie darf nicht geraten werden.

## Technische Abbildung

`Padding = 8 - Sachkontenlänge`

- Sachkonto technisch: Anzeigenummer rechts mit Padding-Nullen ergänzen.
- Personenkonto technisch: dieselbe Padding-Regel; technische Breite regelmäßig
  9 Stellen.

## Rückrechnung

Kontonummern immer als Strings behandeln. DATEV kann führende Nullen in
numerischen JSON-Werten verlieren. Nach Entfernen des rechten Paddings muss ein
Sachkonto links auf die Sachkontenlänge aufgefüllt werden.

Beispiel bei Sachkontenlänge 4:

- technisch `9800000` → Kern `980` → Anzeige `0980`
- technisch `9000000` → Kern `900` → Anzeige `0900`
- technisch `15900000` → Anzeige `1590`
- technisch `701470000` → Personenkonto `70147`

Personenkonten haben in der Anzeige Sachkontenlänge + 1 Stellen. Führende Ziffer
1 bis 6 = Debitor, 7 bis 9 = Kreditor.

Keine heuristische Ermittlung der Sachkontenlänge aus Einzelkonten verwenden.
Bei fehlender Sachkontenlänge ist die Kontenprüfung `NICHT_PRUEFBAR`.
