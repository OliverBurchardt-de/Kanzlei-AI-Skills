# Zeitwirtschaft: belegtes Format und Exportprofil

Quelle: [Original-PDF](Importschnittstelle.pdf), DATEV, Stand 13.07.2022. Der [Textauszug](Importschnittstelle.txt) enthält Marker `=== PDF-SEITE n ===`. Bei Unklarheiten Originalseite ansehen. Die Seitenzahlen unten beziehen sich auf diese PDF.

## Dateiaufbau (S. 13-19)

DATEV erlaubt variable Spaltenreihenfolgen und Trennzeichen sowie feste Feldlängen. Dieses Paket wählt ein einfaches, festes Profil: `.txt`, Semikolon, CRLF, keine Spaltenüberschrift, keine Feldquotierung, Dezimalkomma ohne Tausendertrennzeichen, 12 Datenfelder. Die mitgelieferte INI bildet dieselbe Reihenfolge ab. Semikolon und Steuerzeichen in Feldinhalten müssen vor Ausgabe geklärt werden; nicht still entfernen.

Erste Zeile: `Beraternummer;Mandantennummer;MM/JJJJ`. Bei betrieblicher Personalnummer kommt `;x` hinzu. Der Header besitzt somit drei bzw. vier Felder, nicht zwölf. Beraternummer: 1000-9999999, maximal 7 Ziffern. Mandantennummer: 1-99999, maximal 5 Ziffern. Die PDF-Muster verwenden keine einheitliche Nullauffüllung. Keine zusätzlichen Zeilen mit `[Allgemein]` in die TXT schreiben; diese gehören zur gesonderten INI.

| Nr. | INI-Feldinhalt | JSON-Feld | Format/Grenze aus S. 15 |
| --- | --- | --- | --- |
| 1 | Personalnummer | personalnummer | DATEV-Nummer 1-99999, höchstens 5 Ziffern; betriebliche Nummer siehe unten |
| 2 | Kalendertag | kalendertag | Gültiger Tag im Headermonat, höchstens 2 Ziffern |
| 3 | Ausfallschlüssel | ausfallschluessel | Bis 2 Zeichen aus dem DATEV-Katalog, einschließlich EÜ |
| 4 | Lohnartennummer | lohnart | 1-5999 oder 8000-9999, höchstens 4 Ziffern |
| 5 | Stundenanzahl | stunden | 0,01-24,00; Kalender |
| 6 | Tagesanzahl | tage | 0,01-1,00; bei Urlaub nur 0,50 oder 1,00 |
| 7 | Wert | wert | -9999999,99 bis 9999999,99; weitere Grenzen je Lohnart |
| 8 | Abweichender Faktor | faktor | -999,99 bis 999,99 |
| 9 | Abweichende Lohnveränderung | lohnveraenderung | 0,01-999,99 |
| 10 | Kostenstellennummer | kostenstelle | Höchstens 8 Zeichen; muss in LuG angelegt sein |
| 11 | Kostenträger | kostentraeger | Höchstens 8 Zeichen |
| 12 | Bemerkung | bemerkung | Höchstens 30 Zeichen |

Betriebliche Personalnummern dürfen laut Mustern (S. 23-24) alphanumerisch sein; die PDF nennt hier keine belastbare Maximallänge. Deshalb nicht die 5-Ziffern-Grenze der DATEV-Personalnummer darauf anwenden, sondern Länge und eindeutige Zuordnung im Zielbestand prüfen. Der Helfer prüft hier nur einen nichtleeren, technisch darstellbaren Wert.

Die INI hat `[Allgemein]` mit `Feldanzahl = 12`, `Feldtrennzeichen = Strichpunkt`, `Satztrennzeichen = Enter/Return`, `Zahlenkomma = ,`, `Datumstrennzeichen = /`; `[Feldinhalt]` führt `Feld1` bis `Feld12`. Keine Konvertierungsregeln voraussetzen: laut S. 18-19 nicht unterstützt. Da das Profil keine festen Feldlängen nutzt, benötigt es keine Sektion `[Feldlaenge]`.

**Korrigierter Musterwiderspruch:** S. 20 setzt `Feldanzahl = 11`, S. 21 nennt jedoch `Feld12 = Bemerkung`. S. 17 verlangt übereinstimmende Feldanzahl. Dieses Profil setzt deshalb 12. Das ist eine nachvollziehbare Korrektur des Beispiels, keine Änderung der Original-PDF.

## Monats- und Kalenderlogik (S. 3-12, 16)

- Monatszeile: Ausfallschlüssel und Kalendertag leer, Wert gefüllt. Stunden-/Tagesfelder gehören zur Kalendererfassung; monatliche Stunden/Tage stehen im Feld Wert. Die Einheit und zulässigen Werte hängen von der Lohnart ab. Beispiel Stundenlohnart: -744,00 bis 744,00 (S. 15).
- Kalenderzeile: Ausfallschlüssel und Kalendertag gefüllt. Stunden/Tage/Lohnart richten sich nach dem Schlüssel. Bei statistischer Zeiterfassung ist eine Lohnart nicht grundsätzlich erforderlich. Das Monatsfeld Wert bleibt im gewählten Profil leer.
- Urlaub: Tage 0,50 oder 1,00, soweit Tagesanzahl angegeben wird. Summen je Mitarbeiter und Kalendertag höchstens 1,00 Tage und 24,00 Stunden (S. 10).
- Unterbrechungstatbestand (S. 8): alle Kalendertage einschließlich arbeitsfreier Tage. An Nicht-Arbeitstagen nur Personalnummer, Tag und Schlüssel; an Arbeitstagen laut Detailregel zusätzlich Sollstunden und Tage 1,00. Keine weiteren Erfassungen für denselben Kalendertag. S. 6 formuliert die Übersicht enger; bei abweichendem Verhalten aktuelle Schlüsseltabelle/Zielversion prüfen.
- Stundenkürzung (S. 8): außer Personalnummer nur Tag, Schlüssel und Stunden. Kann nach S. 9 mit Zeiterfassung ohne Unterbrechung kombiniert werden. Nicht mit beliebigen Lohnarten/Faktoren bestücken.
- Krankheit mit Entgeltfortzahlung (S. 11): durchgängiger Zeitraum. Ganzer Arbeitstag: Stunden und Tage 1,00. Krankheitsbeginn während des Tages: Stunden, Tagesanteil kleiner 1,00 oder leer. Arbeitsfreier Tag: nur Personalnummer, Tag, Schlüssel; Stunden/Tage bleiben leer. AU-Zeitraum und Arbeitsplan sind dafür erforderlich.
- Korrektur bereits abgerechneter Monate (S. 12): Monatswerte als Differenz zum Original; Kalender für betroffene Mitarbeiter für den gesamten Korrekturmonat neu liefern. Der Helfer errechnet keine Differenzen und kann Vollständigkeit ohne Originalbestand nicht belegen.

## Quellen und offene fachliche Prüfungen

Die drei vom Nutzer bereitgestellten Tabellen liegen jetzt als Original-PDF, Text und JSON-Katalog im Paket: [Kataloge und Anwendung](kataloge.md). Der Helfer prüft deren Schlüssel und ausdrücklich angegebene zeitliche/versionsbezogene Grenzen. Die Mandantenkonfiguration wird zusätzlich über [MCP](stammdaten-per-mcp.md) gelesen.

Aktuelle Schlüssel: [DATEV 9222265](https://apps.datev.de/help-center/documents/9222265). Standardlohnarten: [DATEV 9226266](https://apps.datev.de/help-center/documents/9226266). Baulohnarten: [DATEV 9225689](https://apps.datev.de/help-center/documents/9225689). Zielmandant kann eigene Lohnartzuordnungen haben. Die Beispiele liefern keine allgemein gültigen Zuordnungen für andere Mandanten.

Die PDF unterscheidet syntaktisch fehlerhafte Zeilen, die nicht importiert werden, von fachlich fehlerhaften Zeilen, die ggf. trotzdem eingelesen werden (S. 16). Deshalb nach dem tatsächlichen Probeimport das Protokoll und die übernommenen Werte prüfen.

## Codepage und Zeiten

Die PDF spricht von ASCII, definiert aber keine eindeutige Byte-Codepage. Windows-1252 ohne BOM ist die lokale Voreinstellung des Helfers und muss mit dem Zielprofil übereinstimmen; alternativ unterstützt er reines ASCII. Umlaute werden bei Windows-1252 strikt kodiert. Nicht darstellbare Zeichen erzeugen einen Fehler, keine Ersatzzeichen.

Das JSON-Modell erwartet bereits Dezimalstunden. Der Helfer interpretiert `7:30` nicht selbst, weil die Quellsemantik belegt werden muss. Im DATEV-Profil muss die Zeitinterpretation entsprechend auf Industrieminuten/Dezimalstunden stehen (PDF S. 16); kein Trennzeichen für Echtminuten einstellen.
