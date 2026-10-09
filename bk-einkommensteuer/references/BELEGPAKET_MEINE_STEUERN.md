# Belegpaket für DATEV Meine Steuern

## Grundsatz

Mandantenunterlagen vollständig inventarisieren und Originaldateien unverändert erhalten. Aus Originalen abgeleitete Uploaddateien nur erstellen, wenn Seitenbereich und Sachverhalt eindeutig bestimmbar sind.

## Trennentscheidung

Automatisch trennen, wenn alle Bedingungen erfüllt sind:

- Anfangs- und Endseite sind eindeutig,
- der Seitenbereich gehört zu genau einem fachlichen Sachverhalt,
- Person und gegebenenfalls Vermietungsobjekt sind eindeutig,
- keine digitale Signatur oder sonstige Integritätsanforderung wird beeinträchtigt,
- das Original bleibt separat erhalten.

Andernfalls einen Prüffall anlegen und keine scheinbar eindeutige Uploaddatei erzeugen.

## Uploadmanifest

Je abgeleiteter Datei mindestens führen:

- Upload-ID
- Upload-Dateiname
- Beleg-ID des Originals
- Originaldateiname
- erste und letzte Originalseite
- Person
- Anlage oder Themenbereich
- Mietobjekt-ID, falls einschlägig
- SHA-256-Prüfsumme der Uploaddatei
- Bearbeitungsstatus

## Dateinamen

Dateinamen kurz, eindeutig und frei von Mandantennamen gestalten. Empfohlenes Schema:

`<Upload-ID>_<Jahr>_<Thema>_<Objekt-ID-oder-ohne-Objekt>.pdf`

Unzulässige Dateisystemzeichen entfernen. Bei Namenskollisionen niemals überschreiben, sondern die Verarbeitung abbrechen und einen Prüffall erzeugen.

## Datenschutz

Keine echten Mandantenunterlagen, getrennten Belege oder personenbezogenen Testdaten im Git-Repository speichern. Reale Fallordner außerhalb des Repositorys führen oder technisch sicher von Git ausschließen. Im Skill nur synthetische Testdaten und leere Vorlagen versionieren.

## Technische Prüfung

- jede Uploaddatei lässt sich erneut öffnen,
- Seitenzahl entspricht dem manifestierten Bereich,
- Prüfsumme stimmt,
- Upload-ID und Dateiname sind eindeutig,
- alle Originalseiten des Uploads sind rückverfolgbar,
- keine Zieldatei überschreibt ein Original.
