# Prüfprotokoll-Rücklauf

## Statusmodell

Den fachlichen Rücklaufstatus getrennt von der technischen Paketvalidierung führen:

- `Prüfprotokoll-Rücklauf ausstehend`: Noch kein ausgefülltes Prüfprotokoll ausgewertet.
- `Prüfprotokoll-Rücklauf vollständig`: Alle roten Vorgänge besitzen einen gültigen Abschlussstatus, Pflichttexte sind vorhanden und die Integrität ist bestätigt.
- `Prüfprotokoll-Rücklauf unvollständig`: Mindestens ein roter Vorgang ist offen, ein Pflichttext fehlt, ein Status ist unzulässig oder eine Integritätsabweichung besteht.

Den technischen Status des bereits erzeugten DATEV-Pakets durch den Rücklauf niemals verändern.

## Integrität

Ausgangs- und Rücklaufdatei mit `scripts/evaluate_review_return.py` vergleichen. Prüfen:

1. Mandant und Buchungsperiode stimmen überein.
2. Alle Vorgangs-IDs sind exakt einmal und in beiden Dateien vollständig vorhanden.
3. Keine prüfpflichtige Zeile wurde gelöscht oder hinzugefügt.
4. Nur `Bearbeitungsstatus` und `Mitarbeiter-Ergebnis` dürfen in `Belegprüfung` geändert sein.
5. Alle übrigen Blätter und geschützten Inhalte, insbesondere Ampel, Buchungsstapel, Betrag, Kontierung und Belegfeld 1, sind unverändert.

Integritätsabweichungen konkret ausweisen und niemals stillschweigend übernehmen.

## Vollständigkeit

Für jeden roten Vorgang genau einen Abschlussstatus verlangen:

- `unverändert übernommen`
- `geändert`
- `nicht übernommen`

`offen` und ein leeres Feld sind keine Abschlussstatus. Bei `geändert` und `nicht übernommen` ist `Mitarbeiter-Ergebnis` Pflicht. Grüne Vorgänge benötigen keinen Rücklaufeintrag.

## Auswertung

Jedes Ergebnis einer Kategorie zuordnen:

- einmalige Buchungskorrektur,
- dauerhaft wiederverwendbare Mandantenbesonderheit,
- Änderung oder Ergänzung einer Rechnungsabgrenzung,
- Bestätigung oder Änderung von Personenkonten,
- weiterhin offener Klärungsfall.

Folgen:

- Einmalige Korrekturen nur in der Rücklaufauswertung dokumentieren.
- Dauerhafte Besonderheiten als konkreten Vorschlag für das Mandantenprofil ausgeben.
- Abgrenzungsergebnisse mit dem vorhandenen Register abgleichen; bei bereits enthaltenen Fällen keine Dublette vorschlagen.
- Bestätigte Personenkonten als geprüft dokumentieren; nur dauerhaft relevante Informationen für das Mandantenprofil vorschlagen.
- Offene Fälle konkret benennen und den Rücklaufstatus `unvollständig` setzen.

Mandantenprofil und Abgrenzungsregister erst nach ausdrücklicher Freigabe ändern. Keinen DATEV-Buchungsstapel allein aufgrund des Rücklaufs neu erzeugen, wenn die Korrektur bereits in DATEV vorgenommen und im Prüfprotokoll dokumentiert wurde.

## Aufruf

```text
python scripts/evaluate_review_return.py \
  --original <ursprüngliche-prüfungsdatei.xlsx> \
  --returned <ausgefülltes-prüfprotokoll.xlsx> \
  --output-dir <zielordner> \
  --mandantenprofil <mandantenprofil.md> \
  --abgrenzungsregister <abgrenzungsregister.md>
```

Profil und Register mitgeben, wenn sie vorhanden sind. Fehlt das Abgrenzungsregister nach verifiziertem Erstlauf, die Option weglassen. Das Skript erzeugt `Rücklaufauswertung <Mandant> <Periode>.md` und verändert keine Quelldatei.

## Mindestinhalt der Rücklaufauswertung

- Mandant, Periode, Ausgangs- und Rücklaufdatei,
- Integritätsstatus,
- Anzahl Rot und jeweiliger Abschlussstatus,
- geänderte und nicht übernommene Vorgänge,
- fachliche Kategorien,
- Auswirkungen auf Mandantenprofil, Abgrenzungsregister und Personenkonten,
- verbleibende offene Punkte,
- Gesamtstatus `vollständig` oder `unvollständig`.
