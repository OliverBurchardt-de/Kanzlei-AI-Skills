---
name: mt940-dateien-erstellen
description: Erstellt und prüft MT940-/STA-Dateien aus Bankdateien, PDF-Kontoauszügen, Bildern oder Umsatzlisten, insbesondere für DATEV. Verwendet zwingend ein eigenes Referenzmodell je Bank und Exportvariante und prüft vor der Auslieferung sämtliche übernommenen Felder gegen die Originalquelle. Verwenden für MT940-Aufbereitung, Feldabgleich und DATEV-Probeimporte.
---

# MT940-Dateien erstellen

MT940 ausschließlich nach dem passenden **bankindividuellen Referenzmodell** erzeugen. Jede Bank erhält ein eigenes Modell; abweichende Kontoarten, Exportwege oder Layoutversionen erhalten eigene Varianten. Ein allgemeingültiges Modell, ein fremdes Bankprofil oder ein spontan erfundenes Format ist kein Ersatz. Allgemeine MT940-Syntax allein belegt keine bankbezogene Feldzuordnung.

**Vor jeder Auslieferung die tatsächlich geschriebene Datei erneut einlesen und alle übernommenen Felder je Umsatz mit der Originalquelle vergleichen.** Ein Rundlauf gegen das Erzeugungsmanifest und passende Gesamtsalden reichen nicht aus. Der vollständige Buchungstext ist ein Freigabekriterium.

## Arbeitsmodus

- **Erstellen:** Quelle nach ihrem Bankmodell in eine `.sta`-Datei umwandeln.
- **Prüfen:** Bestehende Datei gegen Bankmodell und unabhängig geprüfte Quelldaten vergleichen.
- **Erklären:** [technischer-aufbau.md](references/technischer-aufbau.md) lesen.

Keine Umsätze, Daten, Salden, Referenzen, SWIFT-Codes oder bestätigten Probeimporte erfinden. Technische Prüfung und erfolgreiche DATEV-Anzeige getrennt ausweisen.

## 1. Bank und Referenzmodell zuerst bestimmen

Vor Extraktion und Formatwahl [bankreferenzmodelle.md](references/bankreferenzmodelle.md) lesen und `profiles/` durchsuchen. Bankidentität anhand der Quelle feststellen, nicht aus einer ähnlichen Bankbezeichnung vermuten. Modell nach `bank_id`, `source_variant`, `profile_version` und erfasster Quellenart auswählen und vollständig lesen.

Das Modell bestimmt die Feldzuordnung einschließlich `:61:`, der Bedeutung und Reihenfolge aller `:86:`-Unterfelder, Referenzbehandlung, Zeichen- und Zeilenregeln. Eine Liste erlaubter `?xx`-Kennzeichen allein ist kein Referenzmodell. Modell und zugehörigen Bankadapter anwenden; keine Regeln einer anderen Bank übernehmen und kein bestehendes Modell für den Einzelfall still verändern.

**Fehlt ein passendes Modell, ein neues bankbezogenes Modell in `profiles/` mit Status `draft` anlegen.** Belegte Erkenntnisse und offene Feldzuordnungen dort speichern. Als Referenz eine native Originaldatei dieser Bank, deren Dokumentation oder eine bestätigte bankbezogene Testausgabe verwenden. Fehlt diese Evidenz, den Entwurf trotzdem sichern, die benötigte Bankreferenz benennen und die Erzeugung sperren. Kein leeres Modell durch ein generisches Format auffüllen. Die bereitgestellte [Vorlage](profiles/unverified-example.json) ist kein verwendbares Bankmodell.

Bei einer neuen Variante den Bankadapter mit getrennten Schreib- und Lesefunktionen sowie belegten Quelle/Ziel-Beispielen anlegen. Entwurf und unbestätigte Testdatei klar kennzeichnen. Für DATEV erst nach einem erfolgreichen Probeimport und dokumentierter Löschung der Testumsätze produktiv verwenden. Ohne bankbezogene Grundlage auch keine Testsyntax erfinden.

## 2. Originalquelle sichern und Doppelimporte verhindern

Native MT940- oder CAMT-Dateien bevorzugen; vor einer PDF-Rekonstruktion nach einer solchen Datei fragen, soweit nicht bereits geklärt. Bei PDFs den PDF-Skill lesen, sämtliche Seiten rendern und visuell prüfen. OCR und Textextraktion dienen als Arbeitshilfe.

Quelldateien unverändert sichern und SHA-256 dokumentieren. Pro Konto eine eigene Datei erzeugen; Zahlkonto und Kreditkartenkonto getrennt halten.

Vor einer korrigierten oder erneut erzeugten Datei klären, ob ein früherer Import für dasselbe Konto und denselben Zeitraum aus dem DATEV-Bankbestand gelöscht wurde. Ein anderer Dateiname, eine neue `:20:`-Referenz oder ein neuer Chat bereinigt DATEV nicht. Identischen Fingerprint mit Status `5` sperren. `--allow-duplicate` nur nach bestätigter Löschung und mit `previous_datev_import_removed_confirmed: true` verwenden. Keine Ausgleichsbuchung zur Verdeckung einer Differenz erzeugen.

## 3. Quelle unabhängig erfassen und Manifest aufbauen

Zwei getrennte Nachweise führen:

- `manifest.json`: Eingabe für den Generator mit ausgewähltem Bankmodell und zugeordneten Werten.
- `source-review.json`: unabhängig gegen die Originaldatei geprüfte Quellwerte mit Dateihashes und Fundstelle für jeden Umsatz. **Nicht aus dem Manifest, Generatorbericht oder erzeugten MT940 zurückkopieren.** Bei einer Korrektur die Originalquelle erneut prüfen.

Die Pflichtfelder und das Quellprüfschema stehen in [bankreferenzmodelle.md](references/bankreferenzmodelle.md). Je Konto IBAN, Währung, Auszugs-/Sequenznummer, Auszugsbeginn/-ende und getrennte Anfangs-/Endsalden mit deren Daten erfassen. Je Umsatz in Quellreihenfolge Valuta, Buchungsdatum, Betrag/Vorzeichen, Buchungsart/Code, Referenzen und vollständigen Buchungstext erfassen. Namen, Gegenkonto, EREF, MREF, Gläubiger-ID und andere sichtbare Detailfelder zusätzlich nach den benannten Modellzuordnungen als `source_fields` sichern; keine Information wegen eines allgemeinen Schemas verwerfen.

Für **jeden PDF-/Bildumsatz** zusätzlich speichern:

```json
{
  "source_page": 3,
  "source_description_lines": [
    "Versicherung AG Vertrag VS-1234567890,",
    "Kfz-Versicherung D-AB 123, Referenz REF000000000001"
  ],
  "source_text_verified": true,
  "description": "Versicherung AG Vertrag VS-1234567890, Kfz-Versicherung D-AB 123, Referenz REF000000000001"
}
```

Buchungsblock auf dem Seitenbild abgrenzen und sämtliche Zeilen in sichtbarer Reihenfolge wortgetreu erfassen. Seitenwechsel und Folgezeilen ausdrücklich prüfen. Keine Zeile dem Nachbarumsatz zuordnen. OCR anschließend Zeichen für Zeichen am Bild prüfen. Erst danach `source_text_verified: true` setzen. Bei unklarem Anfang/Ende, unleserlichen Zeichen oder abgeschnittenem Text einen Klärungsfall ausgeben.

Nur belegte Leerzeichennormalisierung und physische Zeilenaufteilung zulassen. Wörter, Namen, Umlaute, Bindestriche, Satzzeichen, Wiederholungen und vollständige Referenzen erhalten. Text weder umstellen, zusammenfassen noch sprachlich verbessern. Modellbedingt verkürzte technische Referenzen zusätzlich vollständig im Nutztext erhalten. Eine nicht verlustfrei darstellbare Information sperrt die Freigabe.

Manifestregeln:

- `bank_id`, `source_variant`, `bank_profile` und `profile_version` sind Pflicht, auch bei nativen Quellen und Testdateien.
- `opening_balance_date` gehört nach `:60F:`, `closing_balance_date` nach `:62F:`. Nicht aus dem Zeitraum oder der ersten Buchung ableiten.
- `statement_start`, `statement_end`, `statement_number`, `sequence_number` und Buchungscodes ausdrücklich erfassen. Legacy-Datumsfelder und globale Standardcodes nicht automatisch übernehmen.
- Beträge als Dezimalstrings mit zwei Stellen speichern; Belastungen negativ, Gutschriften positiv.
- Quellreihenfolge erhalten. Nicht nach Betrag, Beschreibung oder vermutetem Datum neu sortieren.
- Abweichende Valutadaten nur mit `value_date_source_confirmed: true` am Umsatz und dessen Nummer unter `review_report.value_date_exceptions` zulassen.

## 4. Vollständigkeit prüfen und nach dem Modell erzeugen

Centgenau rechnen:

`Anfangssaldo + Summe aller vorzeichenbehafteten Umsätze = Endsaldo`

Buchungszahl, Reihenfolge, Seitenwechsel, Datumsgrenzen, Rücklastschriften, Gutschriften und Gebühren prüfen. Keine Differenz runden oder mit einer künstlichen Buchung schließen.

Zulässige `field86_mode`-Werte:

- `native`: Originalsyntax aus `native_mt940` mit passendem Bankmodell erhalten.
- `bank_profile`: ausgewähltes bankindividuelles Modell anwenden; unbestätigte DATEV-Modelle ausschließlich als Test.
- `datev_verified:<profilname>`: genau das ausgewählte Bankmodell mit dokumentiert erfolgreichem, bereinigtem DATEV-Probeimport.

`generic_unstructured` und `unverified` sind als Ausweichmodi gesperrt. Strukturierte Unterfelder nur entsprechend der belegten Feldbedeutung des ausgewählten Modells verwenden. Der Generator enthält bewusst keinen Standardadapter für unbekannte Banken.

```bash
python scripts/build-mt940.py manifest.json
```

Die erzeugte `.sta` und Sidecar stehen zunächst auf `delivery_approved: false`. Die Erzeugung ist keine Freigabe.

## 5. Pflichtprüfung vor jeder Auslieferung

```bash
python scripts/validate-mt940.py "MT940 <IBAN> <Zeitraum>.sta" manifest.json --source-review source-review.json
```

Der Validator prüft die Originaldateihashes, liest die **geschriebenen Bytes** zurück und vergleicht mit dem getrennten Quellprüfbericht. Sämtliche Umsätze prüfen, keine Stichprobe. Prüfen:

- IBAN, Währung, Auszugs-/Sequenznummer, Saldendaten und Saldenbeträge;
- je Umsatz Zuordnung, Reihenfolge, Valuta, Buchungsdatum, Betrag und Vorzeichen;
- Buchungsart/Code, technische Referenzen und sämtliche benannten Detailfelder gemäß Modell;
- den **vollständigen** zurückgelesenen Buchungstext einschließlich aller ersten/letzten Wörter und Referenzenden;
- keine fehlenden, doppelten, vertauschten oder zusätzlich erfundenen Textteile, keine falschen Feldkennzeichen oder unzulässigen Zeichenänderungen;
- Zeichensatz, CRLF, Zeilen-/Feldgrenzen, Saldenrechnung und Fingerprint.

Quelle → Manifest und Quelle → zurückgelesene MT940 getrennt nachweisen. Im Prüfbericht Quellfundstelle, Quellwert, Manifestwert, tatsächlichen MT940-Wert und Vergleichsergebnis ausweisen. Textanfang/-ende zusätzlich anzeigen; sie ersetzen den Volltextvergleich nicht. Gleich hohe Beträge berechtigen nicht zur Zuordnung eines Textes zu einem anderen Umsatz.

Bei einer Abweichung oder einem fehlenden Nachweis **Auslieferung sperren**, Fundstelle/Feld benennen, beheben und erneut prüfen. Ein technisch stimmiger Rundlauf darf die Quellprüfung nicht ersetzen. Eine spätere Änderung an der MT940 macht den Prüfbericht ungültig; der Bericht bindet sich an deren SHA-256.

Exit-Status: `0` = Feldvergleich, Technik und Rechnung bestanden; `2` = Quellnachweis/Feldabgleich/Salden unvollständig oder falsch; `3` = Struktur-/Zeichenfehler; `4` = Bankmodell fehlt, passt nicht oder ist für den Umfang unbestätigt; `5` = möglicher Doppelimport. Bei Fehler steht der Prüfbericht auf `delivery_approved: false`.

## 6. DATEV-Probeimport und Übergabe

Ein neues DATEV-Modell mit höchstens einem Buchungstag und mindestens einem langen Buchungstext testen. Reale Werte dieser Quelle verwenden; Testzahlen aus `tests/fixtures/` sind keine Bankreferenz. Vor dem Import muss geklärt sein, dass für das Konto und den Testzeitraum keine früher importierten Testumsätze vorhanden sind.

Nach dem Probeimport Anfangssaldo, Endsaldo, Zahl/Vorzeichen und **alle** übernommenen Felder samt vollständigen Buchungstexten direkt in DATEV prüfen. Sichtbare `?xx`-Kennzeichen, verschobene Felder oder fehlende Textteile sind Fehler. Prüfergebnis, Datum und anschließend erfolgte Löschung der Testumsätze im Bankmodell dokumentieren. Erst dann `status: verified` und produktive Verarbeitung zulassen.

Je Konto `.sta`, Prüf-Sidecar, Manifest und Quellprüfnachweis mitgeben. Kurz nennen: Bankmodell/Version, Konto/Zeitraum, Buchungszahl/-summe, Salden, Quell- und MT940-Hashes, Feldvergleich, DATEV-Status und offene Klärungen. Produktionsdatei nur bei `delivery_approved: true` ausliefern. Eine bestandene Testdatei ausdrücklich als Test ausliefern; sie ist keine produktive Freigabe.

Ohne dokumentierten DATEV-Probeimport formulieren:

> Gegen die Quelle sowie technisch und rechnerisch geprüft. Die konkrete Verarbeitung und Anzeige in DATEV ist noch nicht durch einen Probeimport bestätigt. Die Testdatei ist nicht für den vollständigen Produktivimport freigegeben.

„DATEV-kompatibel“, „DATEV-geprüft“ oder „erfolgreich importierbar“ nur mit tatsächlichem Nachweis für dieses Bankmodell behaupten. Bei nativer Originalsyntax die Erhaltung der Quelldaten ausweisen; daraus keinen durchgeführten DATEV-Test ableiten.
