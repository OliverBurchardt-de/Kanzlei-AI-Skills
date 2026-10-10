# M2 Bankauffälligkeiten und Interimskonten

## Bankkonten

Keine Abstimmung gegen einen externen Banksaldo. Nur Verdachtspunkte prüfen:

- Buchungen ohne aussagekräftigen Buchungstext
- ungewöhnlich hohe Barabhebungen oder Bareinzahlungen
- hohe Zahlungen an unbekannte Empfänger
- auffällige Privatbuchungen auf betrieblichen Bankkonten
- mögliche Doppelbuchungen
- größere runde Beträge ohne erkennbaren betrieblichen Zusammenhang

Diese Punkte sind zunächst GELB, außer ein Fehler ist eindeutig.

## Konto 1360 – Geldtransit

Soll am Monatsultimo grundsätzlich null sein. Ein Saldo kann bei einem echten
Banklaufzeitunterschied zulässig sein. Den Folgemonat nicht automatisch prüfen.
Jeder Saldo muss konkret erklärt und dokumentiert werden.

- plausible dokumentierte Ausnahme: GELB
- ungeklärter Saldo: ROT

## Konto 1590 – Durchlaufende Posten

Konto 1590 immer vollständig bis auf die Einzelbuchungsebene auslesen. Für die
Schwelle den absoluten Betrag jeder einzelnen Buchung verwenden; Buchungen
nicht saldieren oder zusammenfassen.

### Kleinbeträge unter 100 EUR

- Ein Einzelbetrag unter 100 EUR darf nicht auf 1590 verbleiben: ROT.
- Jeden solchen Betrag ohne Umsatzsteuer und ohne Buchungsschlüssel von 1590
  auf Konto 4980 (sonstiger betrieblicher Aufwand) umbuchen. Konto 4980 nach
  Kontonummernregel.md auf die Sachkontenlänge des Bestands umrechnen.
- Soll/Haben aus der ursprünglichen Buchung ableiten und nicht raten.
- Als sicheren Umbuchungsvorschlag und gegebenenfalls im DATEV-Vorschlagsstapel
  erfassen. Nicht in die Beleganforderung an den Mandanten aufnehmen.

### Posten ab 100 EUR und fehlende Belege

Jeden auf 1590 verbleibenden Posten ab 100 EUR einzeln in die
1590-Klärungsliste übernehmen. Für jeden Posten anhand der über den
Riecken-Connector gelesenen Einzelbuchungen (`datev_get_account_postings` auf
1590) prüfen und dokumentieren:

- Zahlungsrichtung: Zahlungseingang von oder Zahlungsausgang an,
- Zahlungspartner mit verständlichem Namen, zum Beispiel „Herr Mayer“ oder
  „Herr Müller“,
- erkennbarer Vorgang oder Leistungsbezug,
- Datum, Betrag, Alter, Gegenkonto und vorhandener DATEV-Buchungstext,
- konkrete Beanstandung und versandfertiger Mandantentext zur Nachreichung des
  fehlenden Belegs.

Namen oder Vorgänge nicht erfinden. Reichen Buchungstext, Banktext, Gegenkonto
und weitere DATEV-Daten aus dem Riecken-Abruf nicht zur sicheren Bestimmung
aus, den Posten ROT
kennzeichnen und dem Mitarbeiter die Recherche aufgeben.

Der DATEV-Buchungstext muss Zahlungsrichtung, Zahlungspartner und den fehlenden
Beleg erkennen lassen, zum Beispiel:

> Zahlung von Herrn Mayer – Beleg fehlt

oder:

> Zahlung an Herrn Müller – Beleg fehlt

Den Vorgang ergänzen, wenn er sicher erkennbar ist. Formulierungen wie
„Durchlaufender Posten“, „Zahlung“, „Klärung“ oder bloße Namen ohne
Zahlungsrichtung sind nicht ausreichend.

Der versandfertige Mandantentext muss ohne weitere interne Bearbeitung
verständlich sein, zum Beispiel:

> Zu der Zahlung von Herrn Mayer vom 14.05.2026 über 245,00 EUR fehlt uns der
> Beleg. Bitte reichen Sie den zugehörigen Beleg ein und geben Sie kurz an,
> wofür die Zahlung erfolgte.

- aktueller Posten ab 100 EUR mit vollständigen Angaben: GELB,
- älter als ein Monat: ROT,
- fehlender Zahlungspartner, unklare Zahlungsrichtung oder nichtssagender
  Buchungstext: ROT.

### Mitarbeiter-Nachbearbeitung und verpflichtende Schlusskontrolle

Nach der Erstprüfung dem Mitarbeiter eine konkrete Aufgabenliste ausgeben:

1. alle Einzelbeträge unter 100 EUR ohne Umsatzsteuer von 1590 auf 4980
   umbuchen,
2. für jeden verbleibenden Posten Zahlungsrichtung, Zahlungspartner und Vorgang
   prüfen sowie den DATEV-Buchungstext verständlich ergänzen,
3. die Bearbeitung in der 1590-Klärungsliste dokumentieren und anschließend
   erneut mit folgendem Text anstoßen:

> 1590 ist nachbearbeitet – bitte Schlusskontrolle durchführen.

Den Monatsreview bis zu diesem erneuten Anstoß nicht als abschließend erledigt
kennzeichnen. Nach dem erneuten Anstoß Konto 1590 frisch über den
Riecken-Connector aus DATEV auslesen; nicht auf die alte Liste vertrauen. Dabei
prüfen:

- kein Einzelbetrag unter 100 EUR steht mehr auf 1590,
- jeder verbleibende Posten ab 100 EUR hat Zahlungsrichtung,
  Zahlungspartner und aussagekräftigen Buchungstext,
- jeder verbleibende fehlende Beleg steht genau einmal in der strukturierten,
  versandfertigen Mandantenliste.

Verbleiben Mängel, erneut ROT ausgeben und die offene Aufgabe konkret an den
Mitarbeiter zurückgeben. Erst nach bestandener Schlusskontrolle die
1590-Beleganforderung als versandfertig und den Prüfpunkt als abgeschlossen
kennzeichnen.
