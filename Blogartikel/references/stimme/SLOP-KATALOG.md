<!-- ERZEUGTE KOPIE — NICHT HIER BEARBEITEN.

Quelle:  bk-humanizer/references/SLOP-KATALOG.md
Zweck:   Skill bk-blogartikel, Register Fachtext
Pruefsumme der Quelle: a244d928cd1a021d

Diese Datei wird von bk-humanizer/scripts/sync_stimme.py geschrieben. Eine
Aenderung hier geht beim naechsten Lauf verloren und laesst die Fassungen
auseinanderlaufen.

Soll sich eine Regel aendern:
  1. bk-humanizer/references/SLOP-KATALOG.md bearbeiten
  2. python3 bk-humanizer/scripts/sync_stimme.py
  3. python3 bk-humanizer/scripts/sync_stimme.py --check
  4. beides in einem Commit

Danach muessen die betroffenen Skills neu installiert werden, sonst arbeitet
die Installation weiter mit der alten Fassung. Siehe
bk-humanizer/references/PFLEGE.md.
-->

# Slop-Katalog

Die Muster, an denen maschinell erzeugte Sprache erkennbar wird, und was an
ihre Stelle tritt. Der Katalog gilt für beide Register; wo sich Deutsch und
Englisch unterscheiden, steht es dabei.

Zu jedem Muster gehört ein Ersatz. Das ist kein Schmuck, sondern der Kern:
Ein gestrichener Satz ohne Ersatz hinterlässt entweder eine Lücke, die nie
eine war — dann bleibt sie leer —, oder ein Loch im Gedankengang, das
wieder mit Durchschnitt gefüllt wird, wenn niemand sagt, womit sonst.

**Herkunft.** Die Abschnitte 1 bis 18 decken sich weitgehend mit dem
Katalog von *Wikipedia:Signs of AI writing* (WikiProject AI Cleanup), der
aus der Durchsicht tausender Verdachtsfälle entstanden ist. Wo eine
Beobachtung von dort stammt, steht `[Wikipedia]`. Deutschsprachige
Besonderheiten sind mit `[DE]` gekennzeichnet; ihre Belege stehen in
`QUELLEN.md`. Die Abschnitte 19 bis 22 stammen aus dem eigenen Korpus und
finden sich in den externen Quellen so nicht.

**Warnung zu Erkennungswerkzeugen.** Die Wikipedia-Autoren weisen
ausdrücklich darauf hin, dass automatische KI-Detektoren zwar besser als
der Zufall arbeiten, aber nennenswerte Fehlerquoten haben. Für deutsche
Texte sind sie noch deutlich schwächer als für englische. Aus
stilistischen Merkmalen wird deshalb **nie** auf KI-Urheberschaft
geschlossen. Dieser Katalog beschreibt, was einen Text austauschbar macht,
nicht, wer ihn geschrieben hat.

## Inhalt

**Inhaltliche Muster**
1. [Leere Behauptung von Bedeutung](#1-leere-behauptung-von-bedeutung)
2. [Floskeln und Beratungsleerlauf](#2-floskeln-und-beratungsleerlauf)
3. [Werbesprache](#3-werbesprache)
4. [Vage Zuschreibung](#4-vage-zuschreibung)
5. [Der Herausforderungen-und-Ausblick-Abschnitt](#5-der-herausforderungen-und-ausblick-abschnitt)
6. [Autoritätsgestus](#6-autoritätsgestus)
7. [Falsche Ausgewogenheit und Absicherungsstapel](#7-falsche-ausgewogenheit-und-absicherungsstapel)

**Sprachliche Muster**
8. [Kopula-Vermeidung](#8-kopula-vermeidung)
8a. [Legalese](#8a-legalese)
9. [Partizipialschwänze](#9-partizipialschwänze)
10. [Negativparallelen](#10-negativparallelen)
11. [Dreierketten](#11-dreierketten)
12. [Falsche Spannen](#12-falsche-spannen)
13. [Elegante Variation](#13-elegante-variation)
14. [Der Rhythmus der Maschine](#14-der-rhythmus-der-maschine)

**Form und Format**
15. [Gedankenstrich-Inflation](#15-gedankenstrich-inflation)
16. [Fettlisten, Fettung, Emojis](#16-fettlisten-fettung-emojis)
17. [Überschriftenflut und Aufwärmsätze](#17-überschriftenflut-und-aufwärmsätze)
18. [Gliederungsansagen und Chatbot-Rückstände](#18-gliederungsansagen-und-chatbot-rückstände)

**Nur Fiktion**
19. [Gedeutete Redebegleitsätze](#19-gedeutete-redebegleitsätze)
20. [Filterverben](#20-filterverben)
21. [Behauptete Intensität](#21-behauptete-intensität)

**Zum Schluss**
22. [Was kein Slop ist](#22-was-kein-slop-ist)

---

## 1. Leere Behauptung von Bedeutung

`[Wikipedia: undue emphasis on significance]`

Der Text sagt, dass etwas wichtig ist, statt zu zeigen, was es kostet.

**Erkennen (de):** erheblich, maßgeblich, gravierend, von entscheidender
Bedeutung, essenziell, spielt eine zentrale Rolle, nicht zu unterschätzen,
wegweisend, ein wichtiger Baustein, markiert einen Wendepunkt.
**Erkennen (en):** crucial, vital, pivotal, profound, remarkable,
significant, a testament to, underscores the importance of, marking a
pivotal moment, reflects broader, indelible mark, evolving landscape.

**Ersatz: die Zahl.** Eine Größe wirkt stärker als jedes Adjektiv, weil der
Leser sie selbst einordnen kann.

> statt: Die Auswirkungen auf die Abschreibung sind erheblich.
> so: In einem Fall sind die Gebäudekosten von 900.000 EUR auf 400.000 EUR
> reduziert worden. Damit sind 500.000 EUR AfA einfach weg.

> statt: Der Unterschied ist beträchtlich.
> so: Der Unterschied beträgt im Modellfall oben 87.750 EUR. Das ist keine
> Härte des Einzelfalls, sondern die planmäßige Folge einer Vorschrift, die
> an ein einziges Datum anknüpft.

Wo keine Zahl zur Verfügung steht, nenne die Folge: was jemand tun muss,
nicht mehr kann oder verliert.

---

## 2. Floskeln und Beratungsleerlauf

`[DE]`

Die Beratungsfloskel rutscht am leichtesten durch, weil sie fachlich
klingt: „sorgfältig prüfen", „frühzeitig planen", „lassen Sie sich
beraten". Sie sagt nichts, was der Leser nicht schon wusste, und nennt
keine Handlung.

**Ersatz: die Handlung mit Adressat, Zeitpunkt und Prüfschritt.**

> statt: Hier sollte frühzeitig geplant werden.
> so: Wer den Ruhestand in der vermieteten Eigentumswohnung verbringen will
> und gesundheitlich angeschlagen ist, sollte das Mietverhältnis eher zu
> früh als zu spät beenden.

> statt: Prüfen Sie Ihr Gutachten sorgfältig.
> so: Zählen Sie die Seiten, auf denen tatsächlich Ihr Objekt beschrieben
> wird.

Die vollständige Liste steht in `STIMME-FACHTEXT.md`, Abschnitt *Verbotene
Leerformeln*, und wird von `slop_scan.py` mitgemessen.

---

## 3. Werbesprache

`[Wikipedia: promotional language]`

Sprachmodelle halten den neutralen Ton schlecht, besonders bei allem, was
nach Tradition, Region oder Kultur klingt.

**Erkennen (de):** eingebettet in, im Herzen von, beeindruckend,
atemberaubend, renommiert, bietet eine Vielzahl, überzeugt durch,
besticht durch, reichhaltig, lebendig, ein Muss.
**Erkennen (en):** boasts a, vibrant, rich (im übertragenen Sinn),
nestled, in the heart of, breathtaking, renowned, must-visit, stunning,
commitment to, showcasing, exemplifies.

**Ersatz:** eine überprüfbare Tatsache an der Stelle, an der das Adjektiv
stand.

In Kanzleitexten tritt die Werbesprache meist am Schluss auf, als Angebot.
Dazu Abschnitt 18 und die Regel *keine werbliche Schlussfloskel*.

---

## 4. Vage Zuschreibung

`[Wikipedia: vague attributions, weasel words]`

„Experten sind sich einig", „Studien zeigen", „es wird oft empfohlen",
„vielfach wird vertreten", „Branchenkenner berichten". Eine Autorität wird
behauptet und nicht benannt.

**Ersatz: Ross und Reiter, oder die Aussage fällt.**

Wenn die Quelle wirklich diffus ist, sag das und mach es zum Gegenstand:

> Der letzte Schritt ist im Netz als Sieg über die Versuche der
> Finanzverwaltung gesehen worden. Teilweise wurde sogar behauptet, dass
> die Aufhebung bedeuten würde, dass die Finanzämter jetzt jedes Gutachten
> akzeptieren müssten.

Hier ist die Unschärfe ehrlich, weil der Text sie anschließend angreift.

---

## 5. Der Herausforderungen-und-Ausblick-Abschnitt

`[Wikipedia: challenges and future prospects]`

Ein Formelabschnitt gegen Ende, der Probleme nennt, sie sofort
relativiert und mit Zuversicht schließt.

**Erkennen (de):** „Herausforderungen und Ausblick", „Trotz dieser
Herausforderungen", „Fazit und Ausblick", „Die Zukunft bleibt spannend",
„Es bleibt abzuwarten".
**Erkennen (en):** „Despite its … faces several challenges", „Despite
these challenges", „Future Outlook".

**Ersatz:** das konkrete offene Problem mit Datum, Verfahren oder Betrag —
oder den Abschnitt streichen.

> statt: Trotz dieser Herausforderungen bleibt die Gestaltung ein
> sinnvoller Weg.
> so: Ein Risiko bleibt und gehört offen benannt: Wenn die
> Praxisimmobilie einem Ehegatten allein gehört, hängt der Praxisstandort
> an dieser Ehe.

---

## 6. Autoritätsgestus

`[Wikipedia: persuasive authority tropes]`

Der Text kündigt an, jetzt zum Kern vorzudringen, und liefert dann den
gewöhnlichen Punkt mit Zeremonie.

**Erkennen (de):** „Die eigentliche Frage ist", „Im Kern", „In Wahrheit",
„Der entscheidende Punkt ist", „Worauf es wirklich ankommt", „Der
springende Punkt".
**Erkennen (en):** the real question is, at its core, in reality, what
really matters, fundamentally, the deeper issue.

**Prüfung:** Streiche die Ankündigung. Verliert der folgende Satz etwas?
Meist nicht.

**Achtung, hauseigene Variante:** „Die eigentliche Gefahr …" ist in
früheren Texten mehrfach aufgetaucht. Eine Formel wird nicht dadurch
besser, dass sie von diesem Autor stammt. Auch Signatursätze verbrauchen
sich; siehe Abschnitt 22 und die Serienprüfung in `KORPUS.md`.

---

## 7. Falsche Ausgewogenheit und Absicherungsstapel

`[Wikipedia: excessive hedging]` `[DE]`

Jedes Argument bekommt ein Gegenargument gleicher Länge, jede Aussage eine
Einschränkung, am Ende steht „es kommt auf den Einzelfall an". Das Modell
weicht dem Urteil aus, weil der Durchschnitt aller Texte kein Urteil hat.

Im Deutschen ist die Häufung von Modalverben das verlässlichste Zeichen:
„kann", „könnte", „dürfte", „unter Umständen", „möglicherweise",
„gewissermaßen". Ein Satz mit zwei Absicherungen sichert nichts mehr ab.

**Ersatz: das Urteil, mit Begründung und offener Unsicherheit.**

> Ich halte die Entscheidung für richtig und die Vorschrift, die zu ihr
> zwingt, für misslungen.

> Werden das die Finanzämter machen? Ich weiß es nicht, aber die Grundlage
> hat dieses Schreiben gelegt.

Der zweite Satz zeigt, wie Unsicherheit richtig aussieht: benannt,
begrenzt, und mit dem, was trotzdem feststeht. Nicht „es bleibt
abzuwarten".

Gegenargumente werden nicht weggelassen, sondern einzeln beantwortet:

> Ich kenne alle Gegenargumente:
> **„Das ist verfassungswidrig."** Warum sollte es das sein? Die
> Steuerfreiheit des Verkaufs ist aus steuersystematischer Sicht ein
> Fremdkörper.

Im Steuerrecht gilt zusätzlich: Ein echter Vorbehalt gehört hin, wenn die
Rechtslage offen ist. Der Unterschied zwischen Vorbehalt und Weichzeichnen
ist, ob der Text sagt, **woran** es hängt.

---

## 8. Kopula-Vermeidung

`[Wikipedia: copula avoidance]` — im Deutschen besonders wirksam, weil
Nominalstil als seriös gilt.

Statt „ist" und „hat" treten aufwendige Fügungen auf: „stellt … dar",
„fungiert als", „dient als", „verfügt über", „zeichnet sich aus durch",
„bildet … ab", „erweist sich als".
**Englisch:** serves as, stands as, acts as, boasts, features, represents a.

**Ersatz: das einfache Verb.**

> statt: Die Zugewinngemeinschaft stellt den gesetzlichen Güterstand dar
> und verfügt über den Vorteil der Steuerfreiheit des Ausgleichs.
> so: Die Zugewinngemeinschaft ist der gesetzliche Güterstand. Der
> Zugewinnausgleich bleibt nach § 5 ErbStG erbschaftsteuerfrei.

`slop_scan.py` meldet die Häufung ab 2 Stellen je 1000 Wörter.

---

## 8a. Legalese

`[DE]` — kein KI-Muster im engeren Sinn, sondern die hauseigene Gefahr. Ein
Sprachmodell, das auf Steuerliteratur zurückgreift, erzeugt sie zuverlässig
mit, und sie lässt einen Text genauso austauschbar wirken wie jede Floskel.

**Suche:**

- Paragraphenketten;
- ungeklärte Abkürzungen;
- Nominalstil;
- lange Sätze, die Norm, Urteil, Ausnahme und Folge in einen Satz packen;
- Formulierungen, die nur gelehrt klingen.

**Ersatz: die Reihenfolge Klartext, Fachbegriff, Beleg, Folge.** Ausführlich
in `STIMME-FACHTEXT.md`.

Die schärfste Einzelprüfung: **Streiche in einem Absatz die Klammer mit der
Fundstelle. Bleibt er verständlich?** Wenn nicht, trägt die Fundstelle die
Erklärung, und das ist zu wenig.

> statt: Nach § 13 Abs. 1 Nr. 4b ErbStG i. V. m. §§ 9, 11 ErbStG und unter
> Berücksichtigung der Rspr. des BFH (II R 18/20) setzt die Befreiung die
> Selbstnutzung durch den Erblasser im Zeitpunkt der Steuerentstehung voraus,
> sofern keine zwingenden Gründe i. S. d. Vorschrift entgegenstehen.
> so: Der Erblasser muss die Wohnung bis zum Erbfall selbst bewohnt haben
> oder aus zwingenden Gründen daran gehindert gewesen sein. Was als zwingender
> Grund gilt, hat der BFH eng gefasst: objektive Unmöglichkeit oder
> Unzumutbarkeit, nicht bloße Zweckmäßigkeit (BFH vom 01.12.2021 – II R 18/20).

Ein Paragraph ersetzt keine Erklärung.

---

## 9. Partizipialschwänze

`[Wikipedia: superficial -ing analyses]`

Ein Nachsatz, der die Bedeutung des Hauptsatzes behauptet, statt sie
entstehen zu lassen.

**Erkennen (en):** `, highlighting the …`, `, underscoring …`,
`, ensuring that …`, `, reflecting …`, `, fostering …`, `, showcasing …`.
**Erkennen (de):** `, was die Bedeutung … unterstreicht`, `, was zeigt,
dass …`, `, wodurch deutlich wird, dass …`, `, was den Stellenwert …
verdeutlicht`.

**Ersatz: Punkt setzen und die Folge als eigenen Satz sagen — oder
streichen.** In neun von zehn Fällen steht die Bedeutung ohnehin schon im
Hauptsatz.

---

## 10. Negativparallelen

`[Wikipedia: negative parallelisms, tailing negations]`

„Nicht X, sondern Y" / „not only … but also". Die Figur ist nicht falsch;
sie wird nur massenhaft verwendet, um Gewicht vorzutäuschen, wo Y nichts
Neues bringt. Dazu gehört auch der angehängte Kurzsatz: „kein Rätselraten",
„ohne Umwege".

**Prüfung:** Trägt Y eine Information, die ohne den Kontrast zu X verloren
ginge? Überrascht der Kontrast?

> leer: Es geht nicht nur um Steuern, sondern auch um Planung.
> tragfähig: Ein Mietvertrag unter Ehegatten überzeugt das Finanzamt nicht
> durch seinen Text, sondern durch den Kontoauszug.

Die zweite Fassung trägt, weil der Kontrast ein Prüfkriterium benennt, das
der Leser vorher nicht hatte.

---

## 11. Dreierketten

`[Wikipedia: rule of three]` `[DE]` — im Deutschen verstärkt durch den
Hang zu genau drei Tipps, drei Schritten, drei Argumenten.

Drei gleichrangige Glieder, weil drei sich rund anhört, nicht weil es drei
Dinge gibt. Das dritte Glied ist meist eine Variante des zweiten.

**Prüfung:** Streiche das dritte Glied. Fehlt etwas? Wenn nicht, war es
Füllung.

> statt: klar, verständlich und nachvollziehbar
> so: verständlich

Eine Dreierkette, in der jedes Glied eine eigene Information trägt, bleibt
stehen:

> eigenbetrieblich genutzt, fremdbetrieblich vermietet, selbst bewohnt, zu
> Wohnzwecken vermietet — vier Wirtschaftsgüter, vier Rechtsfolgen.

Dasselbe gilt für die Gliederung: Wenn ein Text ohne Not genau drei
Hauptabschnitte hat und jeder genau drei Unterpunkte, ist das eine
Schablone und keine Ordnung.

---

## 12. Falsche Spannen

`[Wikipedia: false ranges]`

„Von X bis Y", wo X und Y auf keiner gemeinsamen Skala liegen. Die Figur
täuscht Vollständigkeit vor, indem sie zwei beliebige Beispiele zu
Endpunkten erklärt.

> statt: Die Bandbreite reicht von der Gründung bis zur Übergabe, von der
> Bewertung bis hin zur Finanzierung.
> so: Der Beitrag behandelt die Bewertung, die Übertragung und die
> Finanzierung des Kaufpreises.

Eine echte Spanne bleibt: „von 20.500 EUR auf 40.000 EUR", „von fünfzig
auf fünfundzwanzig Jahre".

---

## 13. Elegante Variation

`[Wikipedia: elegant variation]`

Sprachmodelle weichen einer Wortwiederholung aus und wechseln zwischen
Synonymen: „die Immobilie" / „das Objekt" / „die Liegenschaft" / „das
Anwesen" im selben Absatz.

In Fachtexten ist das schädlich. Der Leser fragt sich, ob ein anderer
Gegenstand gemeint ist. **Ein Schlüsselbegriff bleibt derselbe**, auch
wenn er dreimal in vier Sätzen steht.

---

## 14. Der Rhythmus der Maschine

`[Wikipedia]` + eigene Messung

Sprachmodelle erzeugen Sätze von auffällig gleicher Länge und Absätze von
auffällig gleicher Größe. Menschen schreiben ungleichmäßig: Ein Gedanke
braucht drei Nebensätze, der nächste passt in vier Wörter.

**Erkennen:** `slop_scan.py` meldet *Satzrhythmus gleichförmig*, *kaum
kurze Sätze* oder *Absätze gleich lang*. Von Hand: mehrere Sätze
hintereinander ohne Neben- oder Relativsatz, alle mit dem Subjekt
beginnend. Im Deutschen zusätzlich: gehäufte Satzanfänge mit
„Dieser/Diese/Dieses".

**Ersatz ist nicht der lange Satz, sondern der Wechsel.**

> statt — vier Sätze, alle vier bis acht Wörter, kein Nebensatz:
> Der Finanzierungszweck steht fest. Der Vertrag ist unterschrieben. Die
> Auszahlung lässt sich verfolgen. Zinsen und Tilgung laufen wie vereinbart.

> so:
> Wenn der Finanzierungszweck feststeht, der Vertrag unterschrieben ist und
> sich die Auszahlung bis zur Immobilie verfolgen lässt, hat ein Prüfer
> wenig Angriffsfläche. Zinsen und Tilgung laufen wie vereinbart.

Der kurze Satz wirkt nur, wenn längere ihn umgeben. Umgekehrt: Wo ein
Ergebnis Gewicht bekommen soll, steht er allein.

> Damit sind 500.000 EUR AfA einfach weg.
> Wirtschaftlich ist das ein Haus. Steuerlich sind es zwei.

---

## 15. Gedankenstrich-Inflation

`[Wikipedia: em dash overuse]`

Der Gedankenstrich ist ein starkes Zeichen und verträgt keine Häufung. Wo
er jeden zweiten Absatz trägt, wird er zur Masche.

**Ersatz:** Doppelpunkt, wenn eine Auflösung folgt. Semikolon, wenn zwei
Gedanken eng zusammengehören. Punkt, wenn der Einschub einen eigenen Satz
verdient. Klammer, wenn es wirklich Nebensache ist.

Der Richtwert unterscheidet sich stark nach Register: Der deutsche
Fachtext liegt bei 0,8 bis 3,0 je 1000 Wörter, der kaskadierende
Erzählton der Belletristik verträgt das Vierfache, weil der Einschub dort
Teil der Satzmelodie ist. Siehe `MESSWERTE.md`.

**Nicht übertragbar:** Die Wikipedia-Liste nennt typografische
Anführungszeichen („curly quotes") als Verdachtsmoment, weil im
englischen Wikitext gerade Anführungszeichen üblich sind. **Im Deutschen
gilt das nicht.** „…" ist die korrekte Form und kein Hinweis auf
irgendetwas.

---

## 16. Fettlisten, Fettung, Emojis

`[Wikipedia: inline-header lists, boldface, emojis]` `[DE]`

Drei Formatmaschen, die zusammen auftreten und in redaktionellen Texten
praktisch nur bei Chatbots vorkommen:

- **Fettlisten** — Aufzählungen im Muster `**Begriff:** Erklärung`. Die
  auffälligste Masche überhaupt.
- **Mechanische Fettung** einzelner Begriffe im Fließtext, ohne dass die
  Fettung eine Hierarchie abbildet.
- **Emojis** in Überschriften oder Aufzählungen.

**Ersatz:** Fließtext. Wenn die Punkte wirklich nebeneinanderstehen, eine
schlichte Aufzählung ohne Fettung. Wenn einer aus dem anderen folgt,
gehören sie in Sätze — und die Beziehung zwischen ihnen ist meist das
eigentliche Argument.

Fettung bleibt an den wenigen Stellen, an denen sie etwas leistet: ein
Ergebnis, eine Warnung, die Antwortzeile einer Modellrechnung.

---

## 17. Überschriftenflut und Aufwärmsätze

`[DE]` `[Wikipedia: fragmented headers]`

Zwei verwandte Muster:

**Überschriftenflut.** Alle zwei bis drei Sätze eine neue
Zwischenüberschrift. Das sieht nach Struktur aus und zerhackt den
Gedankengang. Richtwert: unter 90 Wörter je Abschnitt ist auffällig.

**Aufwärmsatz.** Unter der Überschrift steht ein kurzer Satz, der die
Überschrift noch einmal sagt, bevor der Inhalt beginnt.

> ## Leistung
>
> Geschwindigkeit ist wichtig.
>
> Wenn eine Seite langsam lädt, springen Nutzer ab.

Der mittlere Satz wird gestrichen.

Ebenfalls hierher gehört die **Title Case** in englischen Überschriften
(„Strategic Negotiations And Global Partnerships"). Im Deutschen gibt es
diese Entsprechung nicht; hier ist das Gegenstück die Überschrift, die aus
zwei mit „und" verbundenen Abstrakta besteht („Chancen und
Herausforderungen").

---

## 18. Gliederungsansagen und Chatbot-Rückstände

`[Wikipedia: signposting, collaborative artifacts, knowledge-cutoff
disclaimers, generic positive conclusions]`

**Gliederungsansage.** „Im Folgenden betrachten wir", „In diesem Artikel
erfahren Sie", „Lassen Sie uns einen Blick darauf werfen", „Tauchen wir
ein". Der Text kündigt an, was er gleich tut, statt es zu tun. In
Vorträgen hat das einen Sinn; auf einer Seite, die man sieht, ist es
verschenkter Platz an der wichtigsten Stelle.

> statt: In diesem Artikel erfahren Sie, welche Voraussetzungen die
> Steuerbefreiung für das Familienheim hat.
> so: Ein Ehepaar wohnt zur Miete, während dem Mann seit Jahren eine
> vermietete Eigentumswohnung gehört, die nach seiner Pensionierung der
> gemeinsame Alterssitz werden soll.

Eine Wegweisung ist erlaubt, wenn sie eine Begründung mitbringt:

> Warum beides zusammengehört, steht weiter unten. Zuerst die Mechanik,
> weil sie darüber entscheidet, ob Sie in derselben Lage sind, ohne es zu
> wissen.

Der Unterschied: Diese Ansage sagt, warum die Reihenfolge so ist und was
der Leser davon hat.

**Chatbot-Rückstände.** „Ich hoffe, das hilft", „Gerne!", „Lass mich
wissen, ob …", „Selbstverständlich!". Gesprächstext, der in den Entwurf
gerutscht ist. Ersatzlos streichen.

**Wissensstand-Vorbehalte.** „Nach den mir vorliegenden Informationen",
„Soweit verfügbar", „Konkrete Angaben liegen nicht vor". In einem
Fachtext ist das doppelt schädlich: Es verrät die Herkunft und es steht an
der Stelle, an der eine Recherche hingehört. Entweder die Angabe wird
beschafft, oder die Lücke wird als `[PRÜFEN: …]` markiert.

**Allgemeiner Zuversichtsschluss.** „Die Zukunft bleibt spannend", „ein
Schritt in die richtige Richtung", „Zögern Sie nicht, uns anzusprechen".
Ersatz ist der Schlusssatz mit Preisschild, siehe
`STIMME-FACHTEXT.md`, Zug 14.

---

## 19. Gedeutete Redebegleitsätze

*Nur Fiktion. Aus dem eigenen Korpus; in den externen Listen so nicht
enthalten.*

Das verlässlichste Kennzeichen maschineller Belletristik, und es fällt in
keiner Rhythmusmessung auf.

> „I can't believe it's only four weeks until I leave," she said, her voice
> a mixture of excitement and a faint tremor of unease.

Der Nachsatz benennt das Gefühl, damit der Leser es nicht selbst aus der
Szene ziehen muss — und nimmt ihm genau die Arbeit ab, die das Lesen
lohnt. Dasselbe gilt für `with a thoughtful expression`, `trying to mask
my apprehension`, `said nervously`.

**Ersatz: die Handlung, die das Gefühl erzeugt hat, oder nichts.**

> „And you," Kathy said, reapplying gloss without looking away from the
> mirror, „have had the one in the grey shirt watching you for twenty
> minutes."

Derselbe Bau, aber der Nachsatz zeigt eine Handlung im Raum. Er deutet
nicht.

Oft ist gar kein Begleitsatz nötig:

> „You'll stretch it," Alexa said.
> „Good."

---

## 20. Filterverben

*Nur Fiktion.*

`I felt`, `I noticed`, `I could see`, `I realized`, `I found myself`.

In der Ich-Erzählung ist die Wahrnehmung ohnehin die der Erzählerin. Das
Filterverb schiebt eine Ebene dazwischen.

> statt: I could feel the heat of the room around me.
> so: The room was too warm.

Ausnahme: Wenn der Akt des Bemerkens selbst die Pointe ist.

> It hadn't occurred to me, until just then, that this went both ways.

---

## 21. Behauptete Intensität

*Nur Fiktion.*

Der Text sagt, dass ein Moment überwältigend war, statt ihn so zu bauen,
dass er es ist. Erkennbar an Steigerungswörtern ohne Gegenstand:
`overwhelming`, `intense`, `electric`, `a wave of`, `something shifted`,
`time seemed to slow`.

**Ersatz: ein konkretes Ding, eine Zahl, ein Körperdetail, das nur in
dieser Szene vorkommt.**

> statt: an overwhelming wave of attraction
> so: Cedar, I registered, under the noise and the heat of the room —
> cedar, and something warmer beneath it that was just him.

Und die Gegenprobe: Ein zurückgehaltener Satz trägt oft mehr als ein
ausgeschriebener.

> I won't account for all of it.

---

## 22. Was kein Slop ist

Der häufigste Fehler beim Humanisieren ist Übereifer. Diese Dinge bleiben:

- **Fachbegriffe**, wenn sie für Genauigkeit oder für die Wiedererkennung
  im Bescheid nötig sind. Sie werden beim ersten Auftreten erklärt, nicht
  vermieden.
- **Wiederholung eines Schlüsselbegriffs.** Siehe Abschnitt 13.
- **Einfache, direkte Sätze.** Schlichtheit ist kein Mangel. Ein Satz wird
  nicht verschachtelt, um menschlicher zu wirken.
- **Typografische Anführungszeichen im Deutschen.** Siehe Abschnitt 15.
- **Vertraute Genremuster in der Fiktion.** Wiedererkennbarkeit ist dort
  oft ausdrücklich erwünscht und kein Qualitätsmangel.
- **Ein guter Absatz, der eine Kennzahl reißt.** Die Messung ist ein
  Hinweis, kein Ziel.
- **Echte Vorbehalte**, wo die Rechtslage offen ist. Siehe Abschnitt 7.
- **Sorgfältig gesetzte Gedankenstriche** an wenigen Stellen.

### Und ausdrücklich gegen eine verbreitete Empfehlung

Mehrere Humanizer-Anleitungen, darunter der verbreitete `humanizer`-Skill,
empfehlen, dem Text „Seele" zu geben: Meinungen haben, gemischte Gefühle
zeigen, Abschweifungen zulassen, „etwas Unordnung hereinlassen".

**Für diesen Autor gilt das nur mit einer Einschränkung, und die ist
wichtig.** Eine Meinung ist erwünscht, wenn sie begründet ist. Eine
erfundene Erfahrung, ein erfundenes Gefühl oder eine gespielte
Unsicherheit sind es nicht — bei einem Steuerberater, der unter seinem
Namen über Rechtsfragen publiziert, sind sie ein Haftungsrisiko und ein
Glaubwürdigkeitsschaden. Absichtliche Fehler und gespielte Beiläufigkeit
fallen außerdem schneller auf als jede Floskel.

Die Grenze steht in `SKILL.md`, Abschnitt **Echtheit**. Sie geht jeder
Empfehlung aus einer allgemeinen Anleitung vor.
