---
name: mt940-dateien-erstellen
description: Erstellt und prüft MT940-/STA-Dateien aus Bankdateien und Kontoauszügen für DATEV mit einem eigenen Referenzmodell je Bank und Auszugsvariante. Verwenden bei Konvertierung, fehlenden Umsätzen und fehlerhaften Buchungstexten.
---

# MT940-Dateien erstellen

## Verbindliche Banktrennung

Keinen bankübergreifenden Konverter oder universelles Bankmodell entwickeln oder verwenden.
Diese Nutzervorgabe gilt verbindlich auch für zukünftige Erweiterungen. Der Skill ist nur der
Einstieg zu getrennten Bankmodellen. Jede Bank erhält eine eigene Referenzdatei,
Quellenbeschreibung, Feldbelegung, Erzeugung und Prüfung. Bankname, BLZ/BIC,
Quellformat und Variante abgleichen. Auch Volksbanken nicht gleichsetzen.

| Bank und Quellvariante | Eigenes Modell | Referenzdatei |
| --- | --- | --- |
| Dortmunder Volksbank eG, BLZ 44160014, BIC GENODEM1DOR, Kontokorrent-EUR-PDF 2025 | [Modell](banks/dortmunder-volksbank/model.md) | `banks/dortmunder-volksbank/reference.sta` (synthetisch) |

Vor Verwendung das gewählte Modell vollständig lesen. Modell-ID:
`dortmunder-volksbank-pdf-2025-v3`. Diese öffentliche Fassung enthält ausschließlich
frei erfundene Testdaten. `reference.sta` ist eine synthetische technische
Testreferenz, kein Bankoriginal und keine DATEV-abgenommene Mandantendatei.
Mandantendaten, echte Kontobewegungen, Quelldokumente und Abnahmenachweise dürfen
nicht in öffentliche Repositories gelangen. Auch Beträge, Datumsfolgen, Referenzen,
Dateinamen und Hashes echter Mandantendateien nicht übernehmen.
v1 und die falsch kodierte v2 sind gesperrt. OEM/CP850 gilt nur für dieses
Bankmodell und den beobachteten Importweg, nicht für andere Banken.
Fehlt ein passendes Modell, zuerst ein eigenes mit eigener Referenzdatei nach
[Modellvertrag](references/technischer-aufbau.md) entwickeln. Kein generisches
Ersatzprofil und kein bloßes Umbenennen eines fremden Bankprofils.

## Quellen und Vollständigkeit

Native Dateien bevorzugen, wenn vorhanden; die genaue Bankvariante prüfen.
Bei PDFs alle Auszüge und Seiten erfassen und Buchungsblöcke visuell kontrollieren.
Automatische Extraktion ist ein Entwurf und setzt niemals selbst Prüfbestätigungen.
Nicht wiederholt nach anderen Dateien fragen, wenn der PDF-Auftrag klar ist.

Buchungstag, Valuta, Auszugszeitraum und Saldendaten getrennt erfassen. Keine
Angaben erfinden. Textumbrüche bankindividuell behandeln: keine künstlichen
Leerzeichen in IBAN, BIC, Referenzen oder getrennten Wörtern. Korrekturen belegen.
Quellanzahl je Monat und Auszug unabhängig zählen. Je Umsatz genau ein
`:61:` und `:86:`; jeden Datensatz feldweise und Salden centgenau vergleichen.
Gebührenanlagen nicht als zusätzliche Umsätze buchen. Widersprüchliche Pflichtdaten
klären, nicht ersetzen oder betroffene Umsätze still weglassen.

## Ausgabeumfang und Status

Sämtliche angeforderten Buchungen erzeugen. Bei gewünschter Gesamtdatei die
Originalauszüge in einer einzigen `.sta` bündeln, mit eigenen Nummern/Salden.
Keinen Jahresauszug erfinden und keine ungefragten Einzeldateien ausgeben.
Ein Tages-Test und eine Testlöschbestätigung sind keine Voraussetzung zur Erstellung.

Dateierstellung ist kein DATEV-Import. Bei erneutem Import Doppelbuchungsrisiko
nennen; ohne Auftrag keine Buchungen löschen/ändern. Korrekturen als Ersatz
kennzeichnen, nicht als zusätzliche Umsätze. Hash und Modellversion protokollieren.

Technische Prüfung, Quellenprüfung und DATEV-Praxisstatus getrennt berichten.
Nutzerbestätigung eines erfolgreichen Imports mit Datei-Hash und Wortlaut festhalten;
unbekannte DATEV-Versionen nicht erfinden. Sie gilt nur für die bestätigte Datei.
Neue Dateien desselben Modells einzeln prüfen und nicht automatisch als
DATEV-importiert oder direkt im Zielsystem kontrolliert melden.
Ein Einzelumsatz-Screenshot belegt weder Salden noch Gesamtvollständigkeit.

## Anwendung

```bash
python3 scripts/build-mt940.py manifest.json Gesamtdatei.sta
python3 scripts/validate-mt940.py manifest.json Gesamtdatei.sta
python3 -m unittest discover -s tests -v
```

Die Einstiegsskripte wählen ausschließlich ausdrücklich registrierte Bankmodelle;
kein universeller Renderer, kein Fallback. Vor jeder Ausgabe den bankeigenen
Referenztest ausführen. Aus technischen Tests keine DATEV-Anzeigegarantie ableiten.
