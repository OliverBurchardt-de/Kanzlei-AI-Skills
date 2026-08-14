# DATEV-Systemgrenzen

## Verbindliche Zielsysteme

- Manuelle Dateneingabe: DATEV Einkommensteuer
- Manueller Belegupload: DATEV Meine Steuern
- Zentrales Arbeitspapier: Excel-Arbeitsmappe

Der Skill bereitet die fachliche Bearbeitung vor. Er liefert Eintragungsvorschläge, Rechenwege, Quellenverweise, getrennte Upload-Belege und offene Punkte. Die tatsächliche Eingabe und der Upload bleiben Aufgaben eines menschlichen Bearbeiters.

## Nicht verfügbare Automatisierung

Im derzeitigen Arbeitsumfeld besteht keine freigegebene Schreib- oder Upload-Schnittstelle für DATEV Einkommensteuer oder DATEV Meine Steuern. Eine vorhandene DATEV-Klardaten-Anbindung darf nur für die von ihr ausdrücklich angebotenen lesenden Bereiche verwendet werden; sie ersetzt weder die Einkommensteueranwendung noch den Belegupload.

Der Skill darf daher insbesondere nicht:

- DATEV Einkommensteuer bedienen oder dort Werte speichern,
- Belege in DATEV Meine Steuern hochladen,
- eine Erklärung freigeben oder übermitteln,
- Bildschirmautomatisierung oder RPA ohne einen gesondert freigegebenen Auftrag einsetzen,
- einen technischen Erfolg in einem DATEV-System behaupten.

## Konsequenz für die Ausgaben

Jede vorgeschlagene Eintragung muss so dokumentiert sein, dass sie manuell in DATEV Einkommensteuer erfasst werden kann. Soweit das programmspezifische Zielfeld für das Veranlagungsjahr nicht verlässlich bestätigt ist, sind amtliches Formular, Feldbezeichnung und Kennziffer anzugeben und der Status auf „prüfen“ zu setzen.

Das Upload-Paket muss für eine manuelle Übergabe an DATEV Meine Steuern vorbereitet sein. Es enthält keine Zugangsdaten und keine Behauptung über einen erfolgten Upload.
