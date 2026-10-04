---
name: mt940-dateien-erstellen
description: Erstellt und prüft MT940-/STA-Dateien aus Bankdateien, PDF-Kontoauszügen, Bildern oder Umsatzlisten, insbesondere für DATEV. Erzeugt bei fehlendem Bankmodell eine Rekonstruktion, prüft alle übernommenen Felder und vollständigen Buchungstexte gegen die Quelle und speichert daraus ein neues Referenzmodell. Verwenden für MT940-Aufbereitung, Feldabgleich und DATEV-Probeimporte.
---

# MT940-Dateien erstellen

Ein vorhandenes **bankindividuelles Referenzmodell** verwenden. Fehlt es, den Kontoauszug auslesen, eine MT940-Rekonstruktion erzeugen, vollständig gegen die Originalquelle prüfen und nach erfolgreicher Prüfung ein neues Modell für diese Bank und Quellenvariante speichern. Fehlende Bankreferenzen oder Originalexporte allein sind kein Grund, die Bearbeitung zu sperren.

**Vor jeder Auslieferung die tatsächlich geschriebene Datei erneut einlesen und alle übernommenen Felder je Umsatz mit der Originalquelle vergleichen.** Ein Rundlauf gegen das Erzeugungsmanifest und passende Gesamtsalden reichen nicht aus. Der vollständige Buchungstext ist ein Freigabekriterium.

## Arbeitsmodus

- **Erstellen:** Quelle mit vorhandenem Modell umwandeln oder ein neues Modell durch Erzeugen und Prüfen erarbeiten.
- **Prüfen:** Bestehende Datei gegen Bankmodell und unabhängig geprüfte Quelldaten vergleichen.
- **Erklären:** [technischer-aufbau.md](references/technischer-aufbau.md) lesen.

Keine Quellwerte oder bestätigten Probeimporte erfinden. Technische Ersatzwerte ausdrücklich als abgeleitet dokumentieren; Quellprüfung und erfolgreiche DATEV-Anzeige getrennt ausweisen.

## 1. Bank und Referenzmodell zuerst bestimmen

Vor Extraktion und Formatwahl [bankreferenzmodelle.md](references/bankreferenzmodelle.md) lesen und `profiles/` durchsuchen. Bankidentität anhand der Quelle feststellen, nicht aus einer ähnlichen Bankbezeichnung vermuten. Modell nach `bank_id`, `source_variant`, `profile_version` und erfasster Quellenart auswählen und vollständig lesen.

Das Modell bestimmt Feldzuordnung, vollständige Textdarstellung, Referenzbehandlung und technische Ersatzregeln. Bank und Quellenvariante getrennt halten; bestehende Modelle bei geänderten Regeln versionieren. Banknative Unterfeldbedeutungen nicht aus einem fremden Bankprofil übernehmen.

**Fehlt ein passendes Modell, den Lernablauf ausführen:**

1. Originalquelle vollständig auslesen und den unabhängigen Quellprüfnachweis erstellen.
2. Auf Basis der definierten MT940-Struktur eine Rekonstruktion mit unstrukturiertem, verlustfreiem `:86:`-Text und getrennten Schreib-/Lesefunktionen erzeugen.
3. Die tatsächlich geschriebenen Bytes zurücklesen und jeden übernommenen Wert, besonders sämtliche Buchungstexte, gegen die Originalquelle vergleichen.
4. Bei Abweichungen Ursache und Fundstelle feststellen, Extraktion oder Adapter korrigieren, neu erzeugen und die vollständige Prüfung wiederholen. Nicht bloß denselben fehlerhaften Lauf wiederholen. Bis zum erfolgreichen Abgleich kein bestätigtes Modell speichern.
5. Nach bestandener Prüfung das neue Modell samt Adapter, Quelle/Ziel-Beispielen, Dateihashes und Prüfbeleg unter `profiles/` speichern: `reference_basis.kind: source_reconstruction`, `status: source_verified`.

Ein temporärer Entwurf ist für den Lernlauf zulässig; er ist noch kein wiederverwendbares bestätigtes Modell. `source_verified` belegt die vollständige Quellenübernahme, `verified` zusätzlich einen tatsächlich erfolgreichen DATEV-Probeimport. Bankdokumentation und native Dateien sind hilfreiche weitere Referenzen, keine Voraussetzung für die Rekonstruktion. Die [Vorlage](profiles/unverified-example.json) allein ist kein geprüftes Modell. Details und Aufruf: [bankreferenzmodelle.md](references/bankreferenzmodelle.md).

## 2. Originalquelle sichern und Doppelimporte verhindern

Vorhandene native MT940- oder CAMT-Dateien nutzen. Liegt nur eine PDF, ein Bild oder eine Umsatzliste vor, die Rekonstruktion unmittelbar durchführen; nicht allein wegen eines fehlenden Originalexports unterbrechen. Bei PDFs den PDF-Skill lesen, sämtliche Seiten rendern und visuell prüfen. OCR und Textextraktion dienen als Arbeitshilfe.

Quelldateien unverändert sichern und SHA-256 dokumentieren. Pro Konto eine eigene Datei erzeugen; Zahlkonto und Kreditkartenkonto getrennt halten.

Vor einer korrigierten oder erneut ausgelieferten Datei klären, ob ein früherer Import für dasselbe Konto und denselben Zeitraum aus dem DATEV-Bankbestand gelöscht wurde. Ein anderer Dateiname, eine neue `:20:`-Referenz oder ein neuer Chat bereinigt DATEV nicht. Identischen Fingerprint mit Status `5` sperren. `--allow-duplicate` nur nach bestätigter Löschung und mit `previous_datev_import_removed_confirmed: true` verwenden. Interne Lern-/Korrekturläufe vor der ersten Auslieferung sind keine DATEV-Importe und dürfen ohne Löschbestätigung erneut erzeugt werden. Keine Ausgleichsbuchung zur Verdeckung einer Differenz erzeugen.

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
- `opening_balance_date` gehört nach `:60F:`, `closing_balance_date` nach `:62F:`. Originaldaten übernehmen; bei fehlender Anzeige ausschließlich die dokumentierten Rekonstruktionsregeln verwenden.
- `statement_start`, `statement_end`, Auszugs-/Sequenznummer und Buchungscodes ausdrücklich erfassen. Fehlende technische Werte in `derived_fields` mit Quellwert `null`, Regel, Ergebnis und Begründung dokumentieren; der unabhängige Quellprüfnachweis behält `null`. Sichtbare Originalwerte niemals durch Ersatzwerte überschreiben. Beträge, Salden und Texte dürfen nicht ersetzt werden.
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
- `reconstructed`: vollständig quellgeprüfte Rekonstruktion; neues Modell durch den Lernablauf bestätigen und anschließend wiederverwenden.
- `datev_verified:<profilname>`: genau das ausgewählte Bankmodell mit dokumentiert erfolgreichem, bereinigtem DATEV-Probeimport.

`generic_unstructured` und `unverified` sind veraltete, gesperrte Modi. Für neue Banken ausdrücklich `reconstructed` und den Lernablauf verwenden. Ein unstrukturierter Textadapter erhält den vollständigen Quelltext; `?xx` im Originaltext sind dabei wörtlicher Text. Strukturierte Unterfelder nur mit dokumentierter Bedeutung verwenden.

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

Bei einer Abweichung **Auslieferung und Modellbestätigung sperren**, Fundstelle/Feld benennen, beheben, neu erzeugen und vollständig erneut prüfen. Unleserliche Quellen oder nicht verlustfrei darstellbare Inhalte als konkrete Klärungsfälle ausweisen. Ein fehlender Originalexport allein ist kein Klärungsfall. Technische Ableitungen gegen die dokumentierte Regel prüfen und im Bericht von echten Quellwerten unterscheiden. Eine spätere Änderung an der MT940 macht den Prüfbericht ungültig; der Bericht bindet sich an deren SHA-256.

Exit-Status: `0` = Feldvergleich, Technik und Rechnung bestanden; `2` = Quellnachweis/Feldabgleich/Salden unvollständig oder falsch; `3` = Struktur-/Zeichenfehler; `4` = Bankmodell fehlt, passt nicht oder ist für den Umfang unbestätigt; `5` = möglicher Doppelimport. Bei Fehler steht der Prüfbericht auf `delivery_approved: false`.

## 6. Modell speichern, Übergabe und DATEV-Status

Der erfolgreiche vollständige Quell-/Byteabgleich genügt, um das Rekonstruktionsmodell als `source_verified` zu speichern und die geprüfte Rekonstruktion auszuliefern. Der Lernhelfer speichert kein bestätigtes Modell nach einem fehlgeschlagenen Abgleich. Prüfbelege dauerhaft neben den Arbeitsunterlagen erhalten; das Modell verweist mit Hash darauf. Fehlende externe Bankreferenzen oder ein noch ausstehender DATEV-Probeimport sperren diese quellgeprüfte Auslieferung nicht.

Für einen beauftragten DATEV-Probeimport höchstens einen Buchungstag und mindestens einen langen Buchungstext verwenden. Reale Werte dieser Quelle verwenden; Testzahlen aus `tests/fixtures/` sind keine Bankreferenz. Vor dem Import muss geklärt sein, dass für das Konto und den Testzeitraum keine früher importierten Testumsätze vorhanden sind.

Einen DATEV-Probeimport nur im entsprechend beauftragten Umfang durchführen. Danach Anfangssaldo, Endsaldo, Zahl/Vorzeichen und **alle** übernommenen Felder samt vollständigen Buchungstexten direkt in DATEV prüfen. Sichtbare technische Feldkennzeichen, verschobene Felder oder fehlende Textteile sind Fehler. Prüfergebnis, Datum und anschließend erfolgte Löschung der Testumsätze im Bankmodell dokumentieren. Erst dann `status: verified` und `datev_import_verified: true` ausweisen.

Je Konto `.sta`, Prüf-Sidecar, Manifest und Quellprüfnachweis mitgeben. Kurz nennen: Bankmodell/Version, Konto/Zeitraum, Buchungszahl/-summe, Salden, Quell- und MT940-Hashes, Feldvergleich, DATEV-Status und offene Klärungen. Produktionsdatei nur bei `delivery_approved: true` ausliefern. Eine bestandene Testdatei ausdrücklich als Test ausliefern; sie ist keine produktive Freigabe.

Ohne dokumentierten DATEV-Probeimport formulieren:

> Gegen die Quelle sowie technisch und rechnerisch geprüft. Die konkrete Verarbeitung und Anzeige in DATEV ist noch nicht durch einen Probeimport bestätigt. Technische Ersatzwerte sind im Prüfbericht gekennzeichnet.

„DATEV-kompatibel“, „DATEV-geprüft“ oder „erfolgreich importierbar“ nur mit tatsächlichem Nachweis für dieses Bankmodell behaupten. Bei nativer Originalsyntax die Erhaltung der Quelldaten ausweisen; daraus keinen durchgeführten DATEV-Test ableiten.
