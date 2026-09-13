# Stammdaten für die Dateierstellung aus DATEV lesen

Festlegung des Nutzers: Beraternummer **413885**. Mandantennummern, Personalnummern und vorhandene individuelle Lohnarten aus dem LuG-Mandanten beziehen. Die wenigen individuellen Lohnarten sind laut Nutzer im Mandanten dokumentiert; ihre Abwesenheit nicht pauschal voraussetzen.

## Klardaten DATEV-Connector

Der verfügbare MCP-Connector beschreibt ein `payroll`-Modul ausdrücklich für **DATEV Lohn und Gehalt**. Die folgenden Verträge wurden am 13.09.2026 mit `datev_describe` geprüft. Ein erfolgreicher Abruf eines konkreten Mandanten wurde dabei noch nicht getestet.

1. Bei Verwendung zuerst `datev_describe(topic="payroll")` bzw. die benötigte Ressourcenbeschreibung lesen. Die aufrufbaren Toolnamen anhand der aktuellen Umgebung ermitteln; der Anbieterpräfix kann variieren.
2. `datev_payroll_list(resourceUri="datev://payroll/clients", referenceDate="YYYY-MM-01")` liefert die LuG-Mandanten zum Abrechnungsmonat. Die Antwort lokal auf `consultant_number = 413885` und den gesuchten Mandanten eingrenzen. Die Payroll-Ressource unterstützt keine Filter-/Paging-Argumente. `Client.id` ist die **Payroll-GUID**, `number` die fachliche Mandantennummer. Keine Accounting- oder Master-Data-GUID als Payroll-GUID einsetzen.
3. `datev_payroll_list(resourceUri="datev://payroll/employees", clientId=<Payroll-GUID>, referenceDate=...)` liefert Mitarbeiter des gewählten Mandanten. `Employee.id` ist die Personalnummer als String mit ggf. führenden Nullen; `surname` und `first_name` stehen direkt dabei. `company_personnel_number` ist davon getrennt. Standardmäßig die DATEV-Personalnummer verwenden; `x` im TXT-Header nur bei ausdrücklich gewählter betrieblicher Nummer und belegter Zuordnung.
4. `datev_payroll_list(resourceUri="datev://payroll/salary_types", clientId=..., referenceDate=...)` liefert den Lohnartenkatalog des Mandanten. Dokumentierte individuelle Zuordnungen haben gegenüber pauschalen Annahmen aus den Standardtabellen Vorrang. Die Ressourcenbeschreibung garantiert IDs und Namen, nicht alle fachlichen Einzelheiten; fehlende Lohnartfunktionen aus der Dokumentation im Mandanten ergänzen.
5. Bei Kalender-/Fehlzeiten `datev_payroll_get(resourceUri="datev://payroll/working_hours", clientId=..., employeeId=..., referenceDate=...)` für individuelle Sollzeiten verwenden; ggf. Mandantenstandard mit `clientId` ohne `employeeId`. Laut Vertrag ist dies ein Einzelobjekt, keine Liste. Mitarbeiterabweichungen, Beschäftigungsbeginn/-ende und Änderungen im Monat berücksichtigen. Der Monatsanfang ist ein Snapshot, kein Nachweis unveränderter Verhältnisse für den ganzen Monat.
6. Nur für die aktuelle Aufgabe benötigte Ergänzungen lesen, etwa Kostenstellen oder ursprüngliche Kalender-/Monatswerte für Korrekturen. Zuordnung mit Connector, Mandant, Ressource, Stichtag und Quellfeld dokumentieren. Keine ungefilterten Bestandsdaten in das portable Skill-Paket kopieren.

Personalnummern nie aus einer Namensähnlichkeit allein ableiten. Bei einer eindeutigen, belegten Zuordnung selbstständig weiterarbeiten. Nur mehrdeutige oder fehlende Treffer nachfragen. Ein leerer oder fehlgeschlagener API-Abruf beweist nicht, dass ein Mitarbeiter oder eine individuelle Lohnart nicht existiert.

## Andere Konnektoren

Ein anderer Konnektor kann denselben Leseweg übernehmen, wenn seine konkreten Werkzeuge **Mandantenmitarbeiter in Lohn und Gehalt** liefern. Der aktuell verfügbare Riecken-mCO-Aufruf `datev_search_employees` beschreibt dagegen **Kanzlei-Mitarbeiter**; dessen Personalnummern nicht für die Lohnabrechnung eines Mandanten verwenden. Mandanten-/DMS-Suche kann bei Riecken für die Zuordnung oder Dokumentation helfen, ersetzt aber keinen nachgewiesenen Payroll-Mitarbeiterabruf.

Wenn der verfügbare Konnektor den erforderlichen Lesezugriff nicht ermöglicht, die genaue fehlende Ressource nennen und vorhandene belegte Exportdaten verwenden. Kein weiteres Plugin und keine API-Anwendung für den zurückgestellten Onlineversand voraussetzen.
