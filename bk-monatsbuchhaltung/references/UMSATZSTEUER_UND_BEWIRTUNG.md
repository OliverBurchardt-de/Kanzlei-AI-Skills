# Umsatzsteuer und Bewirtung

## Umsatzsteuerkonfiguration

`vat_config` ist für jeden Lauf verpflichtend:

- `sales_treatment`: `steuerpflichtig`, `steuerfrei` oder `gemischt`
- `input_tax_deduction`: `voll`, `keiner` oder `anteilig`
- `default_domestic_input_treatment`: `volle_vorsteuer`, `keine_vorsteuer` oder `anteilige_vorsteuer`
- optional `general_cost_input_tax_rate` bei profilierter Quote
- optional `special_rules` für dauerhaft bekannte direkte Zuordnungen

Die Konfiguration steuert die Buchung. Branche oder frühere Läufe dürfen sie nicht ersetzen.

### Kein Vorsteuerabzug

Inländische Eingangsrechnungen werden brutto gebucht; `input_tax_treatment` ist `keine_vorsteuer`, jeder `bu_key` bleibt leer. §13b-/Auslandsfälle werden nicht automatisch als normale Inlandsrechnung behandelt.

### Gemischte Umsätze

1. Direkte Zuordnung zu steuerpflichtigem oder steuerfreiem Tätigkeitsbereich.
2. Nur echte Allgemeinkosten nach profilierter Quote behandeln.
3. Ist weder Zuordnung noch Quote belastbar: `input_tax_treatment: sonderfall`, Ampel Rot und Klärungsfall.

## Bewirtungsnachweise

Vollautomatische Aufteilung nur, wenn alle folgenden Punkte eindeutig erfüllt sind:

- maschineller Rechnungsbeleg mit Gaststättenname/-anschrift, Datum, Leistungen und Betrag;
- bei Rechnungen über der Kleinbetragsgrenze die zusätzlichen Rechnungspflichtangaben;
- gesonderter oder elektronischer Bewirtungsnachweis;
- Teilnehmer;
- konkreter geschäftlicher Anlass;
- erforderliche Unterschrift/elektronische Freigabe.

Bei vollständigem Nachweis:

- Netto-/Bruttoaufteilung nach dem Vorsteuerprofil;
- 70 % auf das konfigurierte abzugsfähige Bewirtungskonto;
- 30 % auf das konfigurierte nicht abzugsfähige Bewirtungskonto;
- Trinkgeld ohne Vorsteuer, ebenfalls 70/30.

Bei fehlendem oder unklarem Nachweis:

- nicht weglassen und nicht als „nicht buchungsrelevant“ behandeln;
- Rot im Klärungsstapel exportieren, sicheren Betrag erhalten; das sichere Datum bleibt in Lauf-JSON und Prüfungsdatei, das DATEV-Belegdatum bleibt im Klärungsstapel leer;
- nur konkret ungesicherte Buchungsfelder mit `open_fields` offen lassen, keine Ersatzkontierung;
- genau einen Klärungsfall mit den fehlenden Nachweisen.
