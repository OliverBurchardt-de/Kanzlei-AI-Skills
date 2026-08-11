# Klardaten-Abruf für den Monatsreview

## Verbindliche Reihenfolge

1. `datev://accounting/clients` abrufen und die Mandantennummer zum Client-GUID
   auflösen. Bei mehreren Treffern nicht raten.
2. `datev://accounting/fiscal_years` mit dem Client-GUID abrufen.
3. Das tatsächlich vorhandene Wirtschaftsjahr des Prüfmonats auswählen. Den
   `fiscalYearId` niemals konstruieren.
4. `account_length` des Wirtschaftsjahres übernehmen.
5. `datev://accounting/accounting_sums_and_balances` für Salden und
   Monatsbewegungen abrufen. Auswahl möglichst auf `id`, `account_number`,
   `caption` und `accounting_sums_and_balances_month_values` begrenzen.
6. `datev://accounting/account_postings` für Einzelbuchungen abrufen. Nach
   zulässigen Konto- und Datumsfiltern eingrenzen. Diese Ressource nicht mit
   nicht unterstütztem Paging aufrufen.

## Grundsätze

- Vor dem Bau eines Filters die Ressourcendokumentation über `datev_describe`
  lesen.
- Technische Kontonummern nach `Kontonummernregel.md` umrechnen.
- Monatssummen sind nicht automatisch kumulierte Ultimosalden. Für den
  Monatsendbestand Anfangsbestand und Bewegungen korrekt einbeziehen.
- Buchungstexte und Gegenkonten nur als Indiz werten; fachliche Sollquelle und
  Mandantendatei haben Vorrang.
- Der Review geht von final gebuchter Bank aus. Bankvollständigkeit nicht als
  eigenes Prüfmodul behandeln; bei deutlichen Gegenanzeichen Review abbrechen.
