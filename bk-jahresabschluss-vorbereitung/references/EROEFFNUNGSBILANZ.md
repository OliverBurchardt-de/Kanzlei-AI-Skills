# Eröffnungsbilanzprüfung nach Handels- und Steuerrecht

## Auftrag und Rechtsrahmen

Prüfe die Übernahme der endgültigen Schlusswerte des Vorjahrs in die Eröffnungswerte des unmittelbar folgenden Wirtschaftsjahrs. Verwende die tatsächlichen DATEV-Jahresgrenzen; 31.12./01.01. gilt nur für Kalenderwirtschaftsjahre. Prüfe keine Ansatz- oder Bewertungsentscheidung und ändere DATEV/DMS nicht.

Handelsrechtliche Grundlage ist die Bilanzidentität nach [§ 252 Abs. 1 Nr. 1 HGB](https://www.gesetze-im-internet.de/hgb/__252.html). Für die steuerliche Prüflinie berücksichtige die eigenständigen steuerlichen Ansätze nach [§ 5 EStG](https://www.gesetze-im-internet.de/estg/__5.html) und Steuerbilanz beziehungsweise steuerliche Überleitung nach [§ 60 Abs. 2 EStDV](https://www.gesetze-im-internet.de/estdv_1955/__60.html). Quellen am 20.09.2026 geprüft; bei historischen Fällen die für das jeweilige Jahr maßgebliche Fassung heranziehen.

## Quellen und Bereichsinventar

1. Für beide Jahre die vollständige Summen- und Saldenliste einschließlich Kontenplan über den Riecken-Connector lesen (`datev_get_account_balances` je `fiscal_year`, nach Bestätigung des Nutzers mit `confirmed_full_list=true`). Sie liefert je Konto EB-Wert, kumulierte Soll-/Habenwerte und Jahressaldo. Der Connector liefert keine Buchungsstapel und keine stapelbezogene Bereichskennung. Das Bereichsinventar aus `datev_get_asset_inventory` je `accounting_reason` (`handelsrecht`, `steuerrecht`), aus DMS-Nachweisen und dem Mandantenprofil aufbauen; fehlende oder weitere Bereiche dokumentieren statt zu raten.
2. Die Buchungen der betroffenen Konten um die Jahresgrenze mit `datev_get_account_postings` lesen: im Vorjahr die Abschlussbuchungen, im Zieljahr die Eröffnungs- und ersten laufenden Buchungen. Je Konto, Gegenkonto, Soll/Haben, Datum, Betrag, Belegfeld und Buchungstext vergleichen. EB-, laufende und nachträgliche Abschlussbuchungen auseinanderhalten; Datum allein beweist keine EB-Buchung.
3. Mandant, Wirtschaftsjahre, Stichtage, Abrufzeit, Buchungsstand (`datev_get_accounting_statistics`), Sperr-/Festschreibestatus, Werkzeuge, Parameter, Limits und Vollständigkeit dokumentieren. Nicht gelieferter Sperrstatus ist `unbekannt`, nicht „gesperrt“ oder „final“.
4. DMS-Nachweise mit Dokumentnummer, Dateiname, Version und Seite/Fundstelle erfassen. Nicht allein nach Titeln „E-Bilanz“/„Steuerbilanz“ urteilen. Körperschaftsteuererklärung und Steuerbescheid ersetzen keine Steuerbilanz.
5. Beide Prüflinien im Ergebnis sichtbar halten, auch wenn keine separaten DATEV-Stapel vorhanden sind. Steuerliche Werte können auch durch eine vollständige Überleitung belegt werden. Nichtanwendbarkeit benötigt einen fachlichen Nachweis; fehlende Daten genügen nicht. Bei EÜR ohne Eröffnungsbilanz ist das Modul begründet nicht anwendbar. Im Erstjahr Gründungs-/Übernahmeunterlagen anfordern, keinen Nullvortrag erfinden.

## Handelsrecht

Vollständige Schluss-SuSa gegen vollständige Eröffnungs-SuSa zunächst kontengleich prüfen, einschließlich aller Bilanz- und Personenkonten auf mindestens einer der beiden Seiten. Unterschriebene HGB-Bilanz und Kontennachweis einbeziehen. Nachträgliche Abschlussbuchungen und Finalität der JA-SuSa belegen.

Ergebnisvortragsdifferenzen nur über eine centgenaue Ergebnisbrücke schließen, deren Betrag durch finale JA-SuSa, festgestellten Abschluss oder konkrete Abschlussbuchung nachgewiesen ist. Ein aus der laufenden SuSa errechneter Jahresüberschuss genügt nicht. Fachliche Ergebnisverwendung nicht neu entscheiden.

## Steuerrecht und Herleitung der Wertschichten

Die Summen- und Saldenliste des Riecken-Connectors ist nicht nach Rechnungslegungsbereich getrennt, und der Connector liefert keine Buchungsstapel mit Bereichskennung. Eine gemeinsame SuSa ist deshalb keine unmittelbar bereichsgetrennte Steuerbilanz. Bereichsgetrennte Werte sind nur über das Anlagenverzeichnis je Bewertungsbereich, eine DMS-Steuerbilanz mit Kontennachweis oder eine vollständige Überleitung belegbar.

Zulässige Nachweiswege je Schluss- und Eröffnungsstichtag:

- Vollständige, bereichsspezifische DATEV-Auswertung/Steuerbilanz mit Kontennachweis.
- Nachvollziehbare Herleitung aus vollständig belegter Grundbuchhaltung und vollständiger steuerlicher Wertschicht. Für beide Jahre Ausgangsquelle, Basisbereich, bereits enthaltene Bereiche, sämtliche Zu-/Abrechnungen, Konten, Vorzeichen und Quellen-IDs festhalten. Keine Schicht doppelt addieren. Unbekannte Basissemantik verhindert einen vollständigen Nachweis. Einen Nachweis von „keine steuerliche Differenz“ ebenfalls ausdrücklich belegen.

Eine identische Teilmenge handels- und steuerrechtlicher Buchungen belegt nur diese Teilmenge. Sie erlaubt weder die Gleichsetzung beider Bilanzen noch eine vollständig hergeleitete steuerliche Schluss- oder Eröffnungsbilanz. Bei Lücken `TEILNACHWEIS`, bei fehlender prüfbarer Grundlage `NICHT_PRUEFBAR`; konkrete fehlende Konten, Stapel, Zeiträume oder Nachweise benennen.

## Konten- und Gruppenabgleich

Soll positiv, Haben negativ; Währungen getrennt führen. Standardtoleranz `0.005 EUR` mit Dezimalarithmetik, keine Wesentlichkeitsgrenze. Bei centgenauen Beträgen ist damit nur `0.00` abgestimmt. Vorher nicht runden oder Vorzeichen entfernen. Bei Fremdwährung den Buchwert in EUR nur mit belegtem Umrechnungskurs vergleichen.

Der kontengleiche Erstvergleich bleibt im Arbeitspapier erhalten. Kontenumstellungen benötigen eine bestätigte Zuordnung. Gruppen sind ausschließlich für folgende Fälle zulässig:

| Gruppentyp | Bedingung |
|---|---|
| `darlehen_gesellschafter` | Belegte Fristigkeits-/Darlehensumgliederung mit gleichem Gruppensaldo. |
| `umsatzsteuer` | Belegte Umgliederung der Umsatzsteuerkonten mit gleichem Gruppensaldo. |
| `ergebnisvortrag` | Belegte finale Ergebnisbrücke; handelsrechtlichen Nachweis nicht ungeprüft steuerlich verwenden. |

Je Gruppe: ID, Prüflinie, Währung, Schlusskonten, Eröffnungskonten, Einzelwerte, Summen, Differenz, Begründung, Quelle und nächster Schritt. Jede Kontenposition darf nur einmal einer Gruppe zugeordnet sein. Keine Gruppierung nur wegen ähnlicher Namen und keine Verrechnung zwischen Prüflinien. Nicht belegte Differenzen bleiben offen. Technische Vortragskonten anhand Live-Kontenplan prüfen, keine universelle 9000er-Regel.

## Status und Startregel

- `ABGESTIMMT`: vollständige, finale Schluss- und vollständige Eröffnungswerte derselben Prüflinie; alle Positionen kontengleich, über zulässige Gruppe oder belegte Ergebnisbrücke innerhalb der Toleranz erklärt.
- `TEILNACHWEIS`: Bereich oder Teilmenge belegt, vollständige Stichtagsherleitung fehlt.
- `FACHLICH_ZU_KLAEREN`: Differenz, Gruppierung oder Ergebnisbrücke ungeklärt.
- `ZU_BEREINIGEN`: eindeutig belegter technischer Vortragsfehler mit konkretem Korrekturauftrag.
- `NICHT_PRUEFBAR`: Pflichtquelle fehlt oder Datenlage erlaubt keinen eindeutigen Vergleich.
- `NICHT_ANWENDBAR`: ausschließlich mit nachgewiesener fachlicher Nichtanwendbarkeit.

Jeder Status benötigt einen konkreten nächsten Schritt. Teilnachweise und ungeklärte Bereiche bleiben Startblocker. Ein erledigter HGB-Abgleich ersetzt die steuerliche Prüflinie nicht. Ohne bekanntes Bereichsinventar müssen beide Prüflinien im Bericht als ungeklärt erscheinen, auch wenn die strukturierten Bereichslisten noch leer sind.

## Eigenständiges Excel-Arbeitspapier

Bei Ausführung der Prüfung `Eroeffnungsbilanzpruefung_<Mandant>_<Vorjahr>_<Zieljahr>.xlsx` erstellen, auch wenn die Gesamt-Review-Sheet-Vorlage fehlt. Bei Erstellung den verfügbaren Spreadsheet-Workflow mit Neuberechnung und visueller Kontrolle verwenden.

1. `Übersicht`: Mandant, Perioden, Quellen, Abruf-/Buchungsstand, Sperrstatus, Toleranz; Zahlen kontengleicher Abgleiche, geprüfter Differenzen, Gruppen und offener Punkte; getrennte Urteile und Vollständigkeit HGB/Steuerrecht.
2. `Abgleich`: jede Bilanz-/Personenkontenposition, Bereich, Währung, Schlusswert, Eröffnungswert, Differenz, Vergleichstyp, Gruppen-ID, Status, Quelle und nächster Schritt. Kontengleiche Ausgangsdifferenz und Gruppenerklärung getrennt zeigen.
3. `Gruppenabgleich`: zugelassene Gruppen mit Einzelkonten, Summen, Ergebnisbrücke, Differenz und Nachweis.
4. `Differenzen`: nur offene oder erklärungsbedürftige Positionen mit konkreter Aufgabe.
5. Bei gemeinsamem OPOS-Auftrag zusätzlich `OPOS-Abgleich` und `OPOS-Fortschreibung` nach der zugehörigen Fachreferenz.

Differenzen, Gruppensummen, Ergebnisbrücken und Zählungen als Formeln. Neu berechnen, Formelfehler prüfen und Blätter visuell auf abgeschnittene Inhalte, Filter, Zahlenformate und Lesbarkeit kontrollieren. Quellen mit Dokumentnummer/Dateiname/Fundstelle oder Riecken-Werkzeug, Wirtschaftsjahr, Parametern und Abrufstand nennen. Keine internen Web-URLs oder temporären Download-Links im ausgegebenen Arbeitspapier; exakte technische URLs bleiben im lokalen Quellenprotokoll.

## Akzeptanzfall aus der bereitgestellten Anweisung

Mandant 12500, 2024/2025 ist ein vorgegebener Testfall, keine neue Live-Prüfung und keine universelle Kontenzuordnung:

- Verlustvortrag `4.608,54` und Jahresüberschuss `75.558,17` ergeben Gewinnvortrag `70.949,63 EUR`. Mit Soll positiv lautet die Brücke `4608.54 + (-75558.17) = -70949.63`. Nur mit finaler Quelle ist die HGB-Brücke abgestimmt.
- Darlehens-/Gesellschafter- und Umsatzsteuerpositionen dürfen bei dokumentierter Zuordnung gruppengleich sein.
- Die vorgegebene Anlagenbuchungs-Teilmenge Juni–Dezember 2024 enthält in den Bereichen Handelsrecht und Steuerrecht jeweils Normalabschreibung Gebäude 4831 gegen 9000 von `2.882,00 EUR`. Dies bleibt steuerlich `TEILNACHWEIS`, selbst bei identischen Beträgen.
- Erst vollständige, belegte Schluss- und Eröffnungswerte dürfen die steuerliche Prüflinie auf `ABGESTIMMT` heben. Kein Schluss „Steuerbilanz fehlt“, nur weil kein passender DMS-Titel gefunden wurde.
