# Pflichtangaben der Mandantendatei

Der Skill liest die Mandantendatei vor jedem Review. Fehlende Angaben werden
nicht geraten.

## Lohn

- Lohnmandant: ja/nein
- Schätzverfahren Sozialversicherung: ja/nein
- erwarteter Monatsultimo-Zustand Konto 1740
- besondere zulässige Abweichungen Konto 1742
- gegebenenfalls Krankenkassen-Personenkonten statt Sammelkonto 1759
- Abschlagszahlungen Lohn: ja/nein und verwendetes Konto
- bAV-/VWL-Zahlungsrhythmus, soweit für 1748/1750 relevant

## Zahlungsweg

- Bankkonten vollständig betrieblich oder gemischt privat/betrieblich
- bei gemischten Konten: verwendete Privat-, Einlagen- und Entnahmekonten

## OPOS

- Mandantenhinweise zu offenen Debitoren aktiv: ja/nein

Nur manuell aktivieren, wenn der OPOS-Bestand zuvor grundlegend bereinigt und
freigegeben wurde. Vorhandene individuelle Zahlungsziele aus den DATEV-
Personenkonten dürfen berücksichtigt werden. Die Vollständigkeit dieser
Stammdaten wird in diesem Skill nicht geprüft.

## Darlehen

Je Darlehen, soweit bekannt:

- Darlehenskonto
- Kreditgeber
- Tilgungsrhythmus monatlich/quartalsweise/endfällig/tilgungsfrei
- reguläre Tilgung
- Zinsrhythmus
- tilgungsfreie Zeiträume
- Informationsquelle
- Status: bestätigt oder automatisch ermittelt und noch zu bestätigen

Der Skill darf diese Angaben aus Verträgen, Tilgungsplänen und Buchungsverläufen
vorbefüllen. Automatisch abgeleitete Angaben bleiben bis zur Bestätigung
vorläufig.

## Abweichende Konten

Nur vom Standard abweichende Konten oder Kontenfunktionen dokumentieren,
insbesondere abweichende Kassen-, Privat- oder Gesellschafterkonten. Die
technische DATEV-Kontonummernlogik gehört nicht in die Mandantendatei.
