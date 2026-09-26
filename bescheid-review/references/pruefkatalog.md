# Prüfkatalog Bescheid-Review

Gliederung:
- Teil A — Formelle Prüfung (jeder Bescheid)
- Teil B — Soll-Ist-Abgleich je Steuerart
- Teil C — Nebenbestimmungen und Erläuterungen (jeder Bescheid)
- Teil D — Zusatzprüfungen bei Änderungsbescheiden
- Teil E — Konsistenzprüfungen bei mehreren Bescheiden

Grundprinzip: Jeder Befund oberhalb der Bagatellgrenze (5,00 EUR) ODER mit
qualitativer Relevanz (Frist, Nebenbestimmung, Abweichung dem Grunde nach) wird
Reviewpunkt. Feststellung und Vermutung strikt trennen und kennzeichnen.

---

## Teil A — Formelle Prüfung (jeder Bescheid)

A1. **Inhaltsadressat**: Name, Rechtsform, ggf. beide Ehegatten bei
    Zusammenveranlagung korrekt? Falscher/unklarer Inhaltsadressat kann den
    Bescheid unwirksam machen (§ 119, § 124 AO) → A-Punkt, Berufsträger einbinden.
A2. **Bekanntgabeadressat**: Zustellung an Kanzlei (Empfangsvollmacht § 122
    Abs. 1 S. 4 AO) oder direkt an Mandant? Direktversand trotz Vollmacht →
    C-Punkt (Prozess: Vollmachtsdatenbank prüfen) und Auswirkung auf tatsächlichen
    Zugang beachten. Bei Personengesellschaften: Empfangsbevollmächtigter § 183 AO.
A3. **Steuernummer/IdNr., VZ, Finanzamt** stimmen mit dem Mandat überein.
A4. **Rechtsbehelfsbelehrung** vorhanden? Fehlt sie oder ist sie unrichtig:
    Jahresfrist § 356 Abs. 2 AO statt Monatsfrist → im Fristenblatt vermerken.
A5. **Einspruchsfrist** gemäß SKILL.md Schritt 2 berechnen (Python, § 122/122a,
    § 355, § 108 AO, Feiertage NRW). Immer Reviewpunkt-fähig, immer ins
    Fristenblatt.
A6. **Fälligkeit und Zahlungsweg** bei Nachzahlungen (Fälligkeit i.d.R. ein
    Monat nach Bekanntgabe): Enthält der Bescheid eine ausdrückliche
    Lastschrift-Aussage ("wird abgebucht")? Wenn ja: Fundstelle notieren,
    Mandanteninfo "Abbuchung am [Datum], Kontodeckung sicherstellen". Wenn
    NEIN: Der Mandant muss selbst überweisen → Mandanteninfo mit Betrag,
    Fälligkeitsdatum, Bankverbindung des FA, Verwendungszweck und Hinweis auf
    Säumniszuschläge (1 % je angefangenem Monat, § 240 AO). Die Überwachung
    des Geldeingangs ist ausschließlich Sache des Mandanten — hierfür wird
    KEIN Kanzlei-Arbeitsschritt angelegt.
A7. **Vorauszahlungen**: (1) **Ableitung aus der Festsetzung** — die (mit-)
    festgesetzten Vorauszahlungen müssen auf dem Ergebnis des Steuerbescheids
    aufbauen; rechnerische Prüfung nach E7. (2) **Angemessenheit** — passt die
    Anpassung (§ 37 EStG, GewSt-Systematik über Messbetrag) zur aktuellen
    Ertragslage des Mandanten? Zu hohe VZ → Herabsetzungsantrag als Empfehlung.
A8. **Stille Abweichung**: Ein leerer oder knapper Erläuterungsteil ist KEIN
    Nachweis erklärungsgemäßer Veranlagung — das FA weicht gelegentlich ab,
    ohne es zu erläutern. Der positionsweise Abgleich (Teil B) wird deshalb
    immer vollständig durchgeführt. Abweichung ohne Begründung gefunden →
    A-/B-Punkt: "Begründung beim FA anfordern (§ 121 AO), Einspruch zur
    Fristwahrung erwägen."
A9. **Anrechnungsteil**: Anzurechnende Beträge (Lohnsteuer, Kapitalertragsteuer,
    SolZ auf Abzugsteuern, geleistete Vorauszahlungen, ggf. § 35 EStG) einzeln
    gegen die **eigene Kanzlei-Berechnung** verproben — diese enthält die
    abgerufenen eDaten (§ 93c AO) bereits und ist das Soll. Separate
    Einzelnachweise (LSt-Bescheinigung etc.) werden NICHT angefordert; sie
    liegen dem Review regelmäßig nicht bei. Zahlendreher und falsch
    übernommene elektronische Daten sind eine der häufigsten Fehlerquellen —
    deshalb ist der Anrechnungsteil Pflichtbestandteil der Abgleichskette
    (Teil B), nie nur die Endsumme. Weicht der Bescheid ab: klären, ob das FA
    andere eDaten hat als die Kanzlei abgerufen hat (dann ggf. Korrektur beim
    Datenübermittler wie Arbeitgeber/Bank anstoßen) oder ein FA-Fehler
    vorliegt.

## Teil B — Soll-Ist-Abgleich je Steuerart

Vergleichslogik immer: Wert lt. eigener Berechnung → Wert lt. Bescheid →
Differenz EUR → Ursache (a) FA-Abweichung lt. Erläuterung / (b) mutmaßlicher
FA-Fehler / (c) mutmaßlich eigener Fehler / (d) Rechtsstand/Programm →
Empfehlung. Mit Python rechnen.

### B1. Einkommensteuer
Abgleichskette: Einkünfte je Einkunftsart (§§ 13–22 EStG, je Ehegatte) →
Gesamtbetrag der Einkünfte (inkl. Altersentlastungsbetrag, Freibetrag § 13
Abs. 3) → Sonderausgaben (inkl. Vorsorgeaufwendungen — Höchstbetragsrechnung
grob plausibilisieren) → außergewöhnliche Belastungen (zumutbare Belastung
nachrechnen) → Kinderfreibeträge/Günstigerprüfung Kindergeld → zu versteuerndes
Einkommen → tarifliche ESt (Splitting?) → Ermäßigungen § 35 EStG (GewSt-
Anrechnung: 4-faches des Messbetrags, Deckelung!), § 35a, § 35c EStG →
festzusetzende ESt → SolZ (Freigrenze!) → KiSt → anzurechnende LSt/KapESt/
Vorauszahlungen → Erstattung/Nachzahlung. Zusätzlich: Progressionsvorbehalt
(§ 32b) übernommen? Kapitaleinkünfte: Abgeltung vs. Günstigerprüfung wie
beantragt umgesetzt?

### B2. Körperschaftsteuer
zvE-Herleitung: Steuerbilanzergebnis → außerbilanzielle Korrekturen (vGA § 8
Abs. 3, nicht abziehbare BA § 10 KStG, § 8b-Positionen inkl. 5 %-Pauschale) →
Verlustabzug § 10d EStG i.V.m. § 8 Abs. 1 KStG (Mindestbesteuerung!) → zvE →
15 % KSt → SolZ. Verlustfeststellung zum 31.12. konsistent (siehe B6)?

### B3. Gewerbesteuer-Messbescheid und GewSt-Bescheid
Gewinn aus Gewerbebetrieb lt. ESt/KSt-Ebene übernommen? Hinzurechnungen § 8
GewStG (insb. Nr. 1: Finanzierungsanteile, 200.000-EUR-Freibetrag, 25 %) und
Kürzungen § 9 GewStG (einfache/erweiterte Grundstückskürzung — bei
Immobilien-Mandanten Kernthema!) nachvollziehen → Gewerbeertrag, Abrundung,
Freibetrag 24.500 EUR (nur Personenunternehmen) → Messbetrag 3,5 %.
GewSt-Bescheid der Gemeinde: Messbetrag × Hebesatz korrekt, Hebesatz der
Gemeinde stimmt (Dortmund derzeit im Bescheid ausgewiesenen Satz gegen
öffentliche Angabe verproben, wenn Zweifel).

### B4. Umsatzsteuer
Steuerpflichtige Umsätze je Steuersatz, steuerfreie Umsätze (§ 4 UStG),
innergemeinschaftliche Erwerbe, § 13b-Umsätze, Vorsteuer, Vorsteuerkorrekturen
§ 15a → verbleibende USt → geleistete Vorauszahlungen → Abschlusszahlung/
Erstattung. Abweichung zur Summe der Voranmeldungen erklärbar (Berichtigungen)?
Sondervorauszahlung angerechnet?

### B5. Gesonderte (und einheitliche) Feststellung
Festgestellte Einkünfte insgesamt und **je Beteiligtem** (Quote, Sonder-BE/-BA,
Ergänzungsbilanzen) gegen die eigene Berechnung. Verteilungsschlüssel korrekt?
Empfangsbevollmächtigter richtig? Hinweis nach § 181 Abs. 5 AO vorhanden?

### B6. Verlustfeststellung § 10d EStG
Verlustrücktrag wie beantragt (Wahlrecht ausgeübt?), verbleibender Verlustvortrag
= Vorjahresfeststellung ± laufendes Jahr. Kette der Feststellungsbescheide
konsistent.

### B7. Zinsbescheid § 233a AO
Zinslauf (Karenzzeit 15 Monate nach Ablauf des VZ, bei überwiegend L+F anders),
Bemessungsgrundlage (auf volle 50 EUR abgerundeter Unterschiedsbetrag), 0,15 %
je vollem Monat (1,8 % p.a., Rechtsstand ab 2019). Bei Änderungsbescheiden:
Teilverzinsung je Teilbetrag nachvollziehen.

### B8. Verspätungszuschlag § 152 AO
Pflichtfall (Abs. 2) oder Ermessensfall (Abs. 1)? Berechnung: 0,25 % der um
Vorauszahlungen/Anrechnungen geminderten festgesetzten Steuer je angefangenem
Monat, mind. 25 EUR/Monat (bei Jahressteuererklärungen). Bei Erstattungsfällen
Ermessen — begründet?

## Teil C — Nebenbestimmungen und Erläuterungen (jeder Bescheid)

C1. **§ 164 AO VdN**: gesetzt / nicht gesetzt / aufgehoben. Bei "aufgehoben":
    B-Punkt "letzte Gelegenheit für eigene Änderungsanträge — Fall final
    durchsehen". Bei gesetzt: C-Punkt Wiedervorlage/Fristenkontrolle
    (Festsetzungsfrist im Blick behalten).
C2. **§ 165 AO Vorläufigkeit**: jeden Punkt einzeln listen. Katalogfälle
    (anhängige Musterverfahren) = C-Punkt (keine Aktion, schützt den Mandanten).
    Einzelfall-Vorläufigkeit (z.B. Einkünfteerzielungsabsicht, Liebhaberei) =
    B-Punkt mit konkreter Beobachtungs-/Nachweisaufgabe und ggf. Frist.
C3. **Nachreichungsaufforderungen**: Welche Unterlage, bis wann, Konsequenz.
    Immer A- oder B-Punkt mit Frist im Fristenblatt.
C4. **Abweichungsbegründungen** des FA: vollständig listen und je Begründung mit
    der betroffenen Abgleichsposition (Teil B) verknüpfen. Prüfen: Ist die
    Begründung rechtlich tragfähig? Lohnt Einspruch (Betrag vs. Aufwand,
    Erfolgsaussicht)?
C5. **Schätzung § 162 AO** (ganz oder teilweise): A-Punkt — Erklärung/Unterlagen
    nachreichen, Einspruch zur Fristwahrung erwägen.
C6. Hinweise auf **Außenprüfung**, Kontrollmaterial, geänderte Rechtsauffassung,
    Aufzeichnungspflichten: als B-/C-Punkt dokumentieren.
C7. **Zahlungsverkehr**: Bankverbindung für Erstattung aktuell? Aufrechnung/
    Umbuchung durch FA erklärt — nachvollziehbar und gewollt? Bei Nachzahlung
    zwingend die Einzugs-Weiche nach A6 anwenden (Lastschrift-Aussage suchen;
    ohne Aussage → Mandant muss überweisen → B-Punkt Mandanteninfo mit
    Zahlungsdaten und Frist). Kein Kanzlei-Punkt "Zahlungseingang überwachen".

## Teil D — Zusatzprüfungen bei Änderungsbescheiden

D1. **Korrekturnorm benannt und einschlägig?** § 164 Abs. 2 (nur solange VdN
    bestand), § 172 Abs. 1 Nr. 2a (Zustimmung/Antrag — liegt unser Antrag vor?),
    § 173 (neue Tatsachen — wirklich neu? grobes Verschulden bei Nr. 2?),
    § 173a (Schreib-/Rechenfehler des Stpfl.), § 175 Abs. 1 Nr. 1
    (Grundlagenbescheid — welcher?), § 175 Abs. 1 Nr. 2 (rückwirkendes Ereignis),
    § 129 (offenbare Unrichtigkeit).
D2. **Änderungsrahmen**: Wurden NUR die von der Korrekturnorm gedeckten Punkte
    geändert, oder hat das FA bei der Gelegenheit weitere Positionen zu Lasten
    verändert? Positionsweiser Vergleich alter Bescheid → neuer Bescheid
    (Delta-Spalte im Abgleichsblatt), sofern der Vorbescheid vorliegt; sonst
    anfordern.
D3. **Teilbestandskraft/§ 351 Abs. 1 AO**: Anfechtung eines Änderungsbescheids
    nur im Umfang der Änderung, außer VdN bestand. Bei Einspruchsempfehlung
    ausweisen.
D4. **Festsetzungsverjährung § 169 ff. AO** grob plausibilisieren (4 Jahre,
    Anlaufhemmung § 170 Abs. 2, Ablaufhemmungen § 171): Durfte überhaupt noch
    geändert werden? Bei Zweifel B-Punkt für den Berufsträger.
D5. **Zinsfolgen** der Änderung (§ 233a Abs. 5): Teilverzinsung korrekt?

## Teil E — Konsistenzprüfungen bei mehreren Bescheiden

E1. Grundlagenbescheid → Folgebescheid: Werte identisch übernommen
    (Messbetrag → GewSt; festgestellte Einkünfte → ESt/KSt-Anteil des
    Beteiligten; Verlustfeststellung → Abzug im Folgejahr)?
E2. **§ 351 Abs. 2 AO-Weiche**: Jede Einspruchsempfehlung dem richtigen Bescheid
    zuordnen und dies im Arbeitspapier ausweisen ("Einspruch gegen
    FESTSTELLUNGSbescheid, nicht ESt-Bescheid").
E3. § 35 EStG-Anrechnung im ESt-Bescheid vs. GewSt-Messbetrag (Faktor 4,
    Begrenzung auf tatsächlich gezahlte GewSt und Ermäßigungshöchstbetrag).
E4. GewSt-Rückstellung im Abschluss vs. tatsächlich festgesetzte GewSt
    (Hinweis-Punkt für die Folgebilanz, Verknüpfung zum Skill abschluss-review).
E5. SolZ/KiSt-Bescheide konsistent zur festgesetzten ESt/KSt (Bemessungsgrundlage
    inkl. Kinderfreibetrags-Sonderrechnung bei KiSt/SolZ).
E6. Ehegatten-/Mehrjahresfälle: mehrere Veranlagungszeiträume hochgeladen →
    Wiederholungsfehler des
    FA oder der eigenen Berechnung über die Jahre erkennen und als einen
    gebündelten Punkt führen.
E7. **Vorauszahlungsbescheid ↔ Steuerbescheid** (Pflicht, sobald ein
    VZ-Bescheid vorliegt oder VZ im Jahresbescheid mitfestgesetzt sind):
    Rechnerisch verproben, dass die Vorauszahlungen auf dem Ergebnis der
    Veranlagung aufbauen (§ 37 Abs. 3 S. 2 EStG; bei KSt über § 31 KStG,
    bei GewSt über § 19 GewStG auf Basis des Messbetrags):
    - **Soll-VZ p.a.** = festzusetzende Steuer lt. Jahresbescheid
      ./. anzurechnende Steuerabzugsbeträge (LSt, KapESt, anrechenbare KSt);
      bei ESt inkl. SolZ-/KiSt-Folge-VZ separat verproben.
    - **Quartalsverteilung**: Soll-VZ / 4, Rundung nach § 37 Abs. 5 EStG
      (Festsetzung nur, wenn mind. 400 EUR p.a. und 100 EUR je Termin;
      Erhöhungsschwellen beachten). Ab welchem Termin greift die Anpassung
      (nur künftige Termine oder nachträgliche VZ § 37 Abs. 4 EStG für den
      laufenden VZ)?
    - **Abweichung** zwischen festgesetzter VZ und Soll-VZ ohne erkennbaren
      Grund (eigener Herabsetzungs-/Anpassungsantrag, dokumentierte
      Ertragslage) → Reviewpunkt: zu hoch = Herabsetzungsantrag empfehlen,
      zu niedrig = Hinweis an Mandant auf spätere Nachzahlung + ggf.
      freiwillige Anpassung erwägen.
    - Fehlt der VZ-Bescheid trotz erwartbarer Anpassung (deutliche
      Mehr-/Mindersteuer): über die Bescheidfamilien-Abfrage (Schritt 0b)
      anfordern bzw. als C-Punkt "Wiedervorlage bei Eingang" führen.
