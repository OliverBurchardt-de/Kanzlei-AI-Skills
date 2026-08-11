---
name: bk-gesellschafterbeschluss
description: Erstellt unterschriftsreife Gesellschafterbeschlüsse zur Feststellung eines handelsrechtlichen Jahresabschlusses, zur Entlastung der Geschäftsführung und zur Ergebnisverwendung. Verwenden, wenn für einen Mandanten ein Gesellschaftsversammlungsbeschluss beziehungsweise Feststellungs- und Ergebnisverwendungsbeschluss als Word-Dokument erstellt oder geprüft werden soll. Ermittelt Bilanzsumme und Jahresüberschuss, Jahresfehlbetrag oder Nullergebnis ausschließlich aus Kanzlei-ReWe-Daten und darf sie aus vollständigen Kontensalden selbst berechnen. Unterscheidet Vortrag, Voll- oder Teilausschüttung und Ausschüttung aus Gewinnvortrag.
---

# BK Gesellschafterbeschluss

## Ziel

Aus den aktuellen Kanzlei-ReWe-Daten und Mandantenstammdaten einen formal sauberen, unterschriftsreifen Gesellschafterbeschluss als DOCX erstellen. Bilanzsumme und Jahresergebnis bei Bedarf kontrolliert aus den Kontensalden berechnen. Niemals ungeklärte, veraltete oder aus einer unzulässigen Quelle stammende Zahlen übernehmen.

## Pflichtablauf

### 1. Abschlusswerte ausschließlich aus Kanzlei-ReWe ermitteln

1. Mandant und Geschäftsjahr in Kanzlei-ReWe eindeutig auflösen.
2. Ausschließlich das Accounting-Modul von Kanzlei-ReWe verwenden: zuerst `datev://accounting/clients`, danach `datev://accounting/fiscal_years` und anschließend die vollständigen Summen und Salden über `datev://accounting/accounting_sums_and_balances` abrufen.
3. Alle Seiten abrufen. Der Standardwert `top=100` ist keine vollständige Datenmenge. Für die Berechnung mindestens `id`, `account_number`, `caption`, `annual_value_debit`, `annual_value_credit`, `balance`, `balance_debit_credit_identifier` und `opening_balance_sheet` verwenden.
4. Gibt die Schnittstelle Bilanzsumme und Jahresergebnis nicht als fertige Felder zurück, diese Werte selbst aus den Kanzlei-ReWe-Daten berechnen. Dazu [references/rewe-berechnung.md](references/rewe-berechnung.md) vollständig lesen und anwenden.
5. Die ermittelte Ergebnisart festhalten: Jahresüberschuss, Jahresfehlbetrag oder Nullergebnis.
6. Die Quelle intern mit `Kanzlei-ReWe`, Mandantennummer, Geschäftsjahr, Abrufdatum und `berechnet aus Summen und Salden` dokumentieren.

Für Bilanzsumme und Jahresergebnis gilt daneben eine absolute DMS-Sperre:

- Niemals ein Werkzeug oder eine Ressource unter `datev://dms/*` aufrufen.
- Das DMS weder durchsuchen noch öffnen, herunterladen oder auswerten. Insbesondere keine dort gespeicherten Jahresabschlüsse, früheren Gesellschafterbeschlüsse oder sonstigen Dokumente als Quelle oder Gegenprobe verwenden.
- Keine Vorjahreswerte aus einem DMS-Dokument übernehmen. Auch ein Dokument mit passendem Namen kann ein anderes Geschäftsjahr oder einen überholten Bearbeitungsstand enthalten.
- Vom Nutzer genannte oder in einem Dokument sichtbare Beträge sind nur Hinweise und ersetzen die Ermittlung aus den Kanzlei-ReWe-Daten nicht.
- Ist Kanzlei-ReWe nicht erreichbar oder fehlt das Geschäftsjahr, anhalten. Keine Zahlen aus dem DMS oder einer anderen Quelle ersatzweise übernehmen.

### 2. Stammdaten ermitteln

Die Quellensperre aus Schritt 1 betrifft die Abschlusswerte. Firma, Sitz, Gesellschafter und Geschäftsführung über die verfügbare Stammdatenverbindung ermitteln. Bei verfügbarem Klardaten MCP:

1. Mandant über `datev://master-data/clients` mit `number eq <Mandantennummer>` auflösen.
2. Den Rechtsträger über `legal_person_id` und `datev://master-data/addressees` mit `expand=*` lesen.
3. Exakte Firma, Rechtsform, Satzungssitz/Ort und aktuelle Anschrift übernehmen.
4. Über `datev://master-data/relationships` mit `has_addressee_id eq <legal_person_id>` aktuelle Gesellschafter und gesetzliche Vertreter ermitteln.
5. Beteiligungsquote oder Alleingesellschafterstellung nur behaupten, wenn sie zuverlässig belegt ist. Andernfalls neutral von „den Gesellschaftern“ sprechen oder nachfragen.

Ohne vollständige Stammdaten nach exakter Firma, Sitz, Gesellschaftern und Geschäftsführung fragen. Registerdaten nur ergänzen, wenn sie aktuell belegt sind.

### 3. Ergebnisart bestimmen

Den Jahresergebnisbetrag als vorzeichenbehaftete Zahl erfassen:

- positiv: **Jahresüberschuss**;
- negativ: **Jahresfehlbetrag**, im Dokument als positiver Absolutbetrag ausweisen;
- null: **ausgeglichenes Jahresergebnis**.

Die verbindlichen Formulierungen aus [references/beschlusslogik.md](references/beschlusslogik.md) verwenden.

### 4. Ergebnisverwendung zwingend abfragen

Diese Frage niemals überspringen, auch wenn ein Vorjahresbeschluss vorliegt.

Bei Jahresüberschuss fragen:

1. auf neue Rechnung vortragen;
2. vollständig ausschütten;
3. teilweise ausschütten und Rest vortragen.

Bei Jahresfehlbetrag fragen:

1. Jahresfehlbetrag auf neue Rechnung vortragen;
2. zusätzlich Ausschüttung aus vorhandenem Gewinnvortrag beabsichtigt.

Bei Nullergebnis fragen, ob keine Ergebnisverwendung oder eine Ausschüttung aus Gewinnvortrag beschlossen werden soll.

Bei jeder Ausschüttung zusätzlich klären:

- Bruttoausschüttungsbetrag;
- Quelle: laufender Jahresüberschuss oder Gewinnvortrag;
- Fälligkeit/Auszahlungstag;
- Auszahlung oder Verrechnung mit einem Gesellschafterkonto;
- bei Teilausschüttung: Behandlung des Restbetrags.

Eine Ausschüttung aus dem laufenden Ergebnis bei Jahresfehlbetrag sperren. Eine Ausschüttung aus Gewinnvortrag nur nach ausdrücklicher Bestätigung erstellen; verfügbare Rücklagen, Verlustvorträge, Kapitalerhaltung und gesellschaftsvertragliche Vorgaben nicht unterstellen.

Wenn eine interaktive Auswahl verfügbar ist, zuerst eine kurze Auswahlfrage zur Ergebnisverwendung stellen. Detailfragen erst nach Auswahl „Ausschüttung“ stellen.

### 5. Weitere Beschlussparameter klären

- Entlastung der Geschäftsführung standardmäßig vorsehen, aber bei entgegenstehenden Angaben nachfragen.
- Beschlussdatum erfragen oder eine offene Datumszeile verwenden.
- Bei mehreren Geschäftsführern oder Besonderheiten klären, ob die Entlastung gemeinsam oder einzeln erfolgt.
- Abweichende Satzungsregeln, streitige Beschlussfassungen, nicht vollständig bekannte Gesellschafter oder Ausschüttungen trotz Verlusten als Klärungsfall behandeln.

### 6. Dokument erzeugen

Die Eingaben in eine JSON-Datei nach [references/eingabeschema.md](references/eingabeschema.md) übertragen und ausführen:

```bash
"$CODEX_PRIMARY_RUNTIME_PYTHON" scripts/erstelle_beschluss.py \
  --input /absoluter/pfad/eingaben.json \
  --output "/absoluter/pfad/Gesellschafterbeschluss Firma Jahr.docx"
```

Dateinamen ohne Unterstriche bilden. Das Dokument enthält regelmäßig:

1. Feststellung des Jahresabschlusses mit Bilanzsumme und richtiger Ergebnisbezeichnung;
2. Entlastung der Geschäftsführung;
3. beschlossene Ergebnisverwendung;
4. Ort, Datum und Unterschriftszeile.

### 7. Qualitätsprüfung und Übergabe

- Den Documents-Skill für DOCX-Erstellung und Renderprüfung verwenden.
- Das DOCX rendern und jede Seite visuell prüfen.
- Kontrollieren: Firma, Ort, Geschäftsjahr, Bilanzsumme, Ergebnisart, Betrag, Ergebnisverwendung, Nummerierung, Datumszeile und Unterschriftsfeld.
- Nach verbliebenen Platzhaltermarkierungen und alten Vorjahresbeträgen suchen.
- Nur die finale DOCX-Datei ausgeben; PDF nur auf ausdrücklichen Wunsch.
- In der Übergabe `Kanzlei-ReWe`, Mandantennummer, Geschäftsjahr, Abrufdatum und den Rechenstatus `aus Summen und Salden berechnet` als Quelle der Abschlusswerte sowie die Stammdatenquelle und das Konfidenzniveau nennen.

## Stop-Regeln

Keinen finalen Beschluss erstellen bei:

- nicht verfügbarem Kanzlei-ReWe-Zugriff;
- nicht eindeutig aufgelöstem Mandanten oder Geschäftsjahr;
- unvollständiger Seitennavigation der Summen und Salden;
- nicht auflösbarer Kontenzuordnung oder verbleibender Bilanzdifferenz nach der Kontrollrechnung;
- unklarer Abgrenzung zwischen Handels- und Steuerbilanzdaten in Kanzlei-ReWe;
- unbekannter Ergebnisverwendung;
- Ausschüttung ohne Betrag oder Fälligkeit;
- nicht belastbar ermittelter Firma oder Sitz;
- unklarer Ergebnisart.
