# DATEV-Abruf über den Riecken-Connector

Die Anbindung an DATEV erfolgt ausschließlich über den Riecken-DATEV-Connector
(MCP-Server `Riecken`, Werkzeuge mit Präfix `datev_`). Kein anderer
DATEV-Zugang und kein anderer DATEV-MCP-Server wird verwendet, auch wenn er in
der Umgebung verfügbar ist. Der Monatsreview verwendet den Connector
ausschließlich lesend.

## Verbindliche Reihenfolge

1. `datev_search_clients` mit der Mandantennummer aufrufen und die gelieferte
   `id` (UUID) für alle Folgeaufrufe verwenden. Den DATEV-Namen gegen den
   Auftrag bestätigen. Bei keinem oder mehreren Treffern nicht raten.
2. `datev_get_client_dossier` lesen und Kontenrahmen, Sachkontenlänge und
   Beginn des Wirtschaftsjahres festhalten. Fehlt die Sachkontenlänge, ist die
   Kontenprüfung nach `Kontonummernregel.md` `NICHT_PRUEFBAR`.
3. Das Wirtschaftsjahr des Prüfmonats als `fiscal_year` (zum Beispiel `"2026"`)
   in jedem fachlichen Aufruf mitgeben. Nicht auf den Standardwert „laufendes
   Wirtschaftsjahr“ verlassen, wenn der Prüfmonat in einem anderen Jahr liegt.
4. `datev_get_accounting_statistics` für das Wirtschaftsjahr lesen. Daraus
   ergibt sich, bis zu welchem Monat gebucht ist. Fehlen Buchungen im Prüfmonat
   oder endet der Buchungsstand erkennbar vor dem Prüfmonat, die Abbruchregel aus
   `SKILL.md` Abschnitt 4 prüfen.
5. `datev_get_account_balances` für Salden und Monatsbewegungen abrufen. Der
   Monatsreview benötigt die vollständige Summen- und Saldenliste. Deshalb zu
   Beginn des Reviews einmal die Bestätigung des Nutzers für die komplette
   Liste einholen und danach mit `confirmed_full_list=true` abrufen; `limit`
   so hoch setzen, dass alle Konten geliefert werden. Die gelieferte Kontenzahl
   gegen die gemeldete Gesamtzahl prüfen. Wird abgeschnitten, in
   Kontenbereichen (`account_from`/`account_to`) nachladen, bis der Bestand
   vollständig ist. Teilergebnisse nie als Vollbestand behandeln.
6. `datev_get_account_postings` für Einzelbuchungen des benötigten Kontos
   abrufen: `account_number` in normaler Schreibweise, `date_from` und
   `date_to` auf den Prüfzeitraum, `fiscal_year` wie oben. Die Ausgabe ist auf
   `limit` begrenzt (Standard 30, neueste zuerst); die Summen gelten immer über
   alle Treffer. Für Konten, die vollständig bis auf Einzelbuchungsebene zu
   lesen sind (insbesondere 1590), `limit` so setzen, dass die Anzahl der
   gelieferten Buchungen zur gemeldeten Trefferzahl passt.
7. `datev_get_open_items` je Seite (`side=receivable`, `side=payable`) mit
   `status=open` für M3 abrufen. `totals.open_sum` ist der fertige
   OPOS-Saldo; nicht selbst nachrechnen. Für die schnelle Suche einzelner
   Geschäftspartner `business_partner` setzen.

## Grundsätze

- Die aktuelle Werkzeugbeschreibung des Connectors ist maßgeblich. Parameter,
  Feldnamen und Filter nicht erfinden und nicht aus früheren Abrufen ableiten.
- Kontonummern dem Connector in normaler Schreibweise übergeben; die technische
  Auffüllung übernimmt der Server. Die Umrechnung nach `Kontonummernregel.md`
  gilt für den erzeugten DATEV-Vorschlagsstapel und für die Rückrechnung
  technischer Kontonummern aus Antworten.
- Monatssummen sind nicht automatisch kumulierte Ultimosalden. Für den
  Monatsendbestand EB-Wert und Bewegungen korrekt einbeziehen.
- Buchungstexte und Gegenkonten nur als Indiz werten; fachliche Sollquelle und
  Mandantendatei haben Vorrang.
- Jeden Abruf mit Werkzeug, Parametern, Abrufzeitpunkt, gelieferter Anzahl und
  Vollständigkeitsstatus im Arbeitspapier nachweisen.
- Bei Verbindungs- oder Berechtigungsproblemen zuerst `datev_health_check`
  (`accounting`) aufrufen. Bleibt der Abruf unmöglich, die abhängigen
  Prüfpunkte `NICHT_PRUEFBAR` ausweisen; keine Werte aus Erinnerung oder
  früheren Läufen verwenden.
- Niemals schreibende Werkzeuge des Connectors aufrufen, insbesondere nicht
  `datev_add_posting`, `datev_prepare_posting_batch`,
  `datev_prepare_business_partner`, `datev_prepare_document_filing` oder
  `datev_execute_change_plan`. Der Skill importiert oder überträgt keine
  Buchungen in DATEV.
- Der Review geht von final gebuchter Bank aus. Bankvollständigkeit nicht als
  eigenes Prüfmodul behandeln; bei deutlichen Gegenanzeichen Review abbrechen.
