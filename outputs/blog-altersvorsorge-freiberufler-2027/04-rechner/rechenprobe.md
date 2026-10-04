# Rechenprobe Förderrechner Altersvorsorge 2027

Erzeugt mit `rechenprobe.py` (Python, unabhängig vom JavaScript geschrieben). Rechtsstand 04.10.2026, Einkommensteuertarif 2026.

## Ergebnis des Abgleichs

Alle elf Fälle wurden im Browser (Chromium, `vorschau.html`) zweifach gegen Python geprüft: die Rechenfunktionen des Rechners direkt und die angezeigten Werte nach Eingabe über die Formularfelder. Abweichungen: **0** (Toleranz 1e-9 bei der Förderung, 1e-6 bei der Projektion). JavaScript-Fehler: keine.

## Tarifkontrolle an den Zonengrenzen (Grundtarif 2026)

| zvE | ESt |
|---:|---:|
| 12.348 | 0 |
| 12.349 | 0 |
| 17.799 | 1.034 |
| 17.800 | 1.035 |
| 69.878 | 18.213 |
| 69.879 | 18.213 |
| 277.825 | 105.550 |
| 277.826 | 105.551 |

Der Tarif ist an allen Grenzen stetig (69.878 und 69.879 EUR jeweils 18.213 EUR). Eckwerte 12.348 / 69.879 / 277.826 EUR stimmen mit den Angaben zum Regierungsentwurf 2027 überein, die den bisherigen Tarif als Ausgangspunkt nennen.

## Handrechnung Fall A (Zweitprüfung ohne Programm)

- Grundzulage: 0,5 × 360 + 0,25 × (1.800 − 360) = 180 + 360 = 540 EUR
- Abzug: 1.800 + 540 = 2.340 EUR
- ESt(90.000) = ⌊0,42 × 90.000 − 11.135,63⌋ = ⌊26.664,37⌋ = 26.664 EUR
- ESt(87.660) = ⌊0,42 × 87.660 − 11.135,63⌋ = ⌊25.681,57⌋ = 25.681 EUR
- Entlastung 983 EUR; zusätzlich 983 − 540 = 443 EUR; Nettoaufwand 1.800 − 443 = 1.357 EUR
- Rentenfaktor 25 Jahre, 4 %: (1,04^25 − 1) / 0,04 = 41,6459; Kapital 2.340 × 41,6459 = 97.451 EUR
- Freies Depot: 1.357 × 41,6459 = 56.513; Gewinn 56.513 − 33.925 = 22.588; Steuer 22.588 × 0,7 × 0,25 = 3.953; nach Steuer 52.561 EUR
- Vertrag nach 30 % Steuer: 97.451 × 0,7 = 68.216 EUR; Unterschied +15.655 EUR

## Handrechnung Fall B

- Grundzulage 0,5 × 300 = 150 EUR; Kinderzulage 2 × 300 = 600 EUR; Zulagen 750 EUR; Abzug 1.050 EUR
- Splitting: 2 × ESt(75.000) = 2 × ⌊31.500 − 11.135,63⌋ = 2 × 20.364 = 40.728 EUR
- mit Abzug: 2 × ESt(74.475) = 2 × ⌊31.279,50 − 11.135,63⌋ = 2 × 20.143 = 40.286 EUR
- Entlastung 442 EUR < 750 EUR Zulagen → Zulage gewinnt, Förderquote 750 / 1.050 = 71 %

## Kostenbeispiel im Artikel

2.340 EUR jährlich, 25 Jahre, 6 % vor Kosten, Rendite nach Kosten = 6 % − Effektivkosten:

| Effektivkosten | Endkapital |
|---:|---:|
| 0,3 % | 123.088 EUR |
| 1,0 % | 111.681 EUR |
| 1,5 % | 104.283 EUR |

Unterschied 0,3 % gegenüber 1,5 %: 18.805 EUR; gegenüber 1,0 %: 11.406 EUR. Eigener Nettoaufwand der Zahnärztin über 25 Jahre: 33.925 EUR.

Auszahlungsplan 67 bis 85 ohne Verzinsung: 97.451 EUR / 216 Monate = 451 EUR pro Monat vor Steuern.

## Fälle

| Fall | Eingaben | Zulagen | Entlastung | zusätzlich | Nettoaufwand | Quote | Kapital 4 % | Unterschied 2 % / 4 % / 6 % |
|---|---|---:|---:|---:|---:|---:|---:|---|
| A | Zahnärztin, ledig, ohne Kind (Artikelbeispiel): 1.800 EUR, 0 Ki., zvE 90.000, Grundtarif, 25 J., 30 % im Alter | 540,00 | 983 | 443 | 1.357 | 42 % | 97.451 | +10.670 / +15.655 / +22.509 |
| B | Architekt, verheiratet, 2 Kinder (Artikelbeispiel): 300 EUR, 2 Ki., zvE 150.000, Splitting, 25 J., 30 % im Alter | 750,00 | 442 | 0 | 300 | 71 % | 43.728 | +14.302 / +18.990 / +25.434 |
| C | Grenzfall unter Mindestbeitrag: 100 EUR, 1 Ki., zvE 40.000, Grundtarif, 20 J., 25 % im Alter | 0,00 | 32 | 32 | 68 | 32 % | 2.978 | +221 / +325 / +457 |
| D | Geringes Einkommen: 1.800 EUR, 0 Ki., zvE 22.000, Grundtarif, 35 J., 30 % im Alter | 540,00 | 586 | 46 | 1.754 | 25 % | 172.346 | −1.197 / +3.321 / +10.535 |
| E | wie A, 42 % im Alter (Artikel: Einwand): 1.800 EUR, 0 Ki., zvE 90.000, Grundtarif, 25 J., 42 % im Alter | 540,00 | 983 | 443 | 1.357 | 42 % | 97.451 | +1.676 / +3.961 / +7.103 |
| F | wie D, 42 % im Alter (Artikel: Verlustfall): 1.800 EUR, 0 Ki., zvE 22.000, Grundtarif, 35 J., 42 % im Alter | 540,00 | 586 | 46 | 1.754 | 25 % | 172.346 | −15.235 / −17.361 / −20.756 |
| G | Spitzensteuersatz, 1 Kind: 1.800 EUR, 1 Ki., zvE 320.000, Grundtarif, 20 J., 42 % im Alter | 840,00 | 1.188 | 348 | 1.452 | 45 % | 78.614 | +3.016 / +4.843 / +7.179 |
| H | Kontrolle Briefing, kein Einkommen: 300 EUR, 1 Ki., zvE 0, Grundtarif, 25 J., 0 % im Alter | 450,00 | 0 | 0 | 300 | 60 % | 31.234 | +14.783 / +19.615 / +26.257 |
| I | Grenzfall 125 EUR, 3 Kinder: 125 EUR, 3 Ki., zvE 277.000, Splitting, 10 J., 45 % im Alter | 437,50 | 238 | 0 | 125 | 78 % | 6.753 | +2.040 / +2.258 / +2.500 |
| J | Grenzfall Höchstwerte der Felder: 1.799 EUR, 9 Ki., zvE 5.000.000, Grundtarif, 50 J., 0 % im Alter | 3.239,75 | 2.267 | 0 | 1.799 | 64 % | 769.251 | +284.903 / +526.925 / +1.016.279 |
| K | Grenzfall ohne Eigenbeitrag: 0 EUR, 0 Ki., zvE 90.000, Grundtarif, 25 J., 30 % im Alter | 0,00 | 0 | 0 | 0 | 0 % | 0 | +0 / +0 / +0 |

Fall F zeigt den ungünstigen Fall, in dem das freie Depot besser abschneidet; der Rechner sagt das in der Fazitzeile ausdrücklich.
