# DATEV-Logik 1742 und 1759 bei Schätzmandanten

Diese Referenz übernimmt die für den Skill relevanten Aussagen aus der vom
Nutzer bereitgestellten Fachrecherche.

## Funktion der Konten

- 1742 ist das Konto der tatsächlichen Sozialversicherungsverbindlichkeit aus
  der Bruttolohnverbuchung.
- 1759 ist das Konto der voraussichtlichen Beitragsschuld und das Zahlungskonto
  der Schätzung.

## Typische Buchungslogik

1. Schätzbetrag: 1742 an 1759
2. Zahlung der Schätzung: 1759 an Bank beziehungsweise an das in der
   Mandantendatei dokumentierte Zahlungskonto
3. endgültige Lohnabrechnung: tatsächliche SV-Verbindlichkeit auf 1742

## Sollzustand zum Monatsultimo

- 1759 soll nach Zahlung grundsätzlich null sein.
- 1742 zeigt nach der endgültigen Abrechnung die Restschuld oder bei
  Überzahlung eine Forderung.

## Kontrollquellen

- Beitragsnachweise
- Buchungsbeleg/Buchungsbericht
- Lohnjournal
- vorhandene DATEV-Auswertungen zur Restbetragslogik

Abweichende Personenkontenlösungen je Krankenkasse müssen in der
Mandantendatei dokumentiert sein.
