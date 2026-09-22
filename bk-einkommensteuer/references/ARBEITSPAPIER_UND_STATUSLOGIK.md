# Arbeitspapier und Statuslogik

## Zweck

Die Excel-Arbeitsmappe als zentrale Übergabe an den fachlichen Bearbeiter verwenden. Keine Zahl darf nur in einer Erläuterung stehen; Beträge, Quellen und Status gehören in strukturierte Zellen.

## Tabellenblätter

- `Steuerfall`: Falldaten, Veranlagungsjahr, Zielsystem und Statusübersicht
- `Eintragungen`: vorgeschlagene Werte je Mantelbogen, Anlage oder Feld
- `Berechnungen`: nachvollziehbare Nebenrechnungen und Aufteilungen
- `Belege`: vollständiges Inventar der Mandantenunterlagen
- `Vermietung`: Objektstammdaten und objektbezogene Aufteilungen
- `Vorjahresabgleich`: fortgeführte, geänderte, weggefallene und neue Sachverhalte
- `Prueffalle`: Annahmen, fachliche Prüfungen und Nachforderungen
- `Uploadmanifest`: getrennte Belege für DATEV Meine Steuern
- `Listen`: zulässige Status- und Auswahlwerte

## Statuswerte

- `bereit`: vollständig belegt, rechnerisch nachvollziehbar und eindeutig zugeordnet
- `prüfen`: Bearbeitungsansatz vorhanden; tatsächliche oder fachliche Freigabe fehlt
- `nachfordern`: entscheidungserhebliche Unterlage oder Angabe fehlt
- `nicht verarbeitet`: technisch unlesbar, nicht sicher zuordenbar oder außerhalb des Umfangs

Der Status `bereit` ersetzt keine abschließende menschliche Freigabe der Steuererklärung.

## Identitäten und Verknüpfungen

Stabile IDs verwenden:

- Eintragungsposition: `POS-0001`
- Berechnung: `BER-0001`
- Beleg: `BEL-0001`
- Mietobjekt: `OBJ-0001`
- Prüffall: `PRF-0001`
- Uploaddatei: `UPL-0001`

Mehrere IDs in einer Zelle durch Semikolon trennen. Keine Verknüpfung ausschließlich über Dateinamen oder Freitext herstellen.

## Beträge und Berechnungen

- Beträge als numerische Werte speichern.
- Aufteilungsquoten als Prozentwerte speichern.
- Abweichungen und einfache Aufteilungen durch sichtbare Formeln berechnen.
- Komplexe Berechnungen in mehrere verständliche Zeilen zerlegen.
- Vorjahresbeträge nie als aktuellen Eingabewert verwenden, sofern kein aktueller Nachweis oder dokumentierter Fortführungsgrund vorliegt.

## Freigabe

Vor Übergabe prüfen:

1. jede Eintragungsposition besitzt Quelle oder dokumentierte Annahme,
2. jede Quelle ist im Belegregister vorhanden,
3. jeder Nachforderungsfall enthält eine konkrete nächste Handlung,
4. jede Belegtrennung ist im Uploadmanifest rückverfolgbar,
5. jede programmspezifische Feldzuordnung ist für das Veranlagungsjahr bestätigt oder als `prüfen` markiert.
