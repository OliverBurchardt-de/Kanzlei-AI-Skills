# Durchgearbeitetes Beispiel

Ein Fachtext vor und nach dem Ablauf aus `SKILL.md`. Der Ausgangstext ist
zu Prüfzwecken erzeugt worden und enthält absichtlich die häufigsten
Muster aus dem Slop-Katalog.

Das Beispiel ist nicht als Vorlage gedacht, sondern als Kalibrierung: Es
zeigt, wie weit ein Eingriff geht und wo er aufhört.

## Die Messung

| | vorher | nachher |
|---|---:|---:|
| Wörter | 154 | 421 |
| Satzlänge im Mittel | 11,0 | 13,6 |
| Streuung der Satzlängen | 3,5 | 10,8 |
| Sätze bis 8 Wörter | 21 % | 45 % |
| Sätze ab 30 Wörtern | 0 % | 10 % |
| Füllformeln je 1000 Wörter | 58,4 | 0 |
| Bedeutungsaufblähung je 1000 | 13,0 | 0 |
| Befunde der Stufe *Hinsehen* | 5 | 0 |

Der Text ist dabei **länger** geworden, nicht kürzer. Das ist der
Normalfall und kein Versehen: Die Floskeln sind weg, aber an ihre Stelle
ist Information getreten. Ein Humanizer, der nur kürzt, hat die Aufgabe
zur Hälfte erledigt.

## Was im Einzelnen geschah

| Eingriff | Muster | Katalog |
|---|---|---|
| „In der heutigen Zeit spielt … eine zentrale Rolle" → weg | Floskel plus leere Bedeutung | 1, 2 |
| „stellt ein komplexes Konstrukt dar und verfügt über" → „kann daraus ein einziger Betrieb werden" | Kopula-Vermeidung | 8 |
| „Experten sind sich einig" → weg | vage Zuschreibung | 4 |
| Drei Fettlisten-Punkte → Fließtext mit Erklärung | Fettliste | 16 |
| „Herausforderungen Und Ausblick" → „Die gefährlichste Stelle ist das Ende" | Formelabschnitt, Title Case | 5, 17 |
| „von der Gründung bis hin zur Nachfolge, von der Finanzierung bis zur Beendigung" → weg | falsche Spanne | 12 |
| „könnte möglicherweise … unter Umständen" → „Es fließt kein Euro" | Absicherungsstapel | 7 |
| „Zusammenfassend lässt sich festhalten" → weg | Chatbot-Rückstand | 18 |
| „Zögern Sie nicht, uns zu kontaktieren" → offen benanntes Risiko | Werbeschluss | 3, 18 |
| „Einleitung / Ein wichtiges Thema" → Fall statt Aufwärmsatz | Aufwärmsatz | 17 |

## Welche Züge eingesetzt wurden

Vier, nicht alle. Aus `STIMME-FACHTEXT.md`:

- **Zug 1, Gegensatz in zwei kurzen Sätzen** — „Zivilrechtlich sind das
  zwei getrennte Sachen … Steuerlich kann daraus ein einziger Betrieb
  werden."
- **Zug 4, die Regel auf den Leser drehen** — „Wer eine Immobilie an die
  eigene GmbH vermietet, hat sich damit auf eine Nachfolgeplanung
  festgelegt, ob er das wollte oder nicht."
- **Zug 8, den Preis nennen** — „Der Preis dafür steht nicht im
  Mietvertrag: Er fällt beim Verkauf an und bei der Nachfolge."
- **Zug 9, das offen benannte Risiko** — der Schlussabsatz.

## Was bewusst offen blieb

Der Abschnitt *Was das kostet* trägt einen Marker
`[OLIVER-INPUT: …]` statt eines Zahlenbeispiels.

Das ist der wichtigste Teil dieses Beispiels. Ein erfundenes Mandat hätte
den Abschnitt sofort stark gemacht, und genau deshalb steht es nicht da.
Die Regel aus `SKILL.md`, Abschnitt *Echtheit*, gilt auch dann, wenn der
Text ohne die Erfindung schwächer bleibt. Der Marker wird gemeldet, und
der Autor entscheidet.

Ebenfalls stehen geblieben sind zwei Befunde der Stufe *Notiert*: drei
Dreierketten, deren Glieder je eigene Information tragen, und fünf
Überschriften auf 421 Wörter. Beides ist vertretbar und wird im
Protokoll genannt, nicht stillschweigend geändert.

---

## Vorher

```markdown
# Die Betriebsaufspaltung: Ein Umfassender Überblick

## Einleitung

Ein wichtiges Thema für Unternehmer.

In der heutigen Zeit spielt die Betriebsaufspaltung eine zentrale Rolle in der steuerlichen Gestaltungsberatung. Sie stellt ein komplexes Konstrukt dar und verfügt über weitreichende Konsequenzen. Es ist wichtig zu beachten, dass die Betriebsaufspaltung nicht nur steuerliche, sondern auch haftungsrechtliche Auswirkungen hat. Experten sind sich einig, dass eine frühzeitige Planung unerlässlich ist.

## Voraussetzungen Und Merkmale

Ein Überblick.

Die Betriebsaufspaltung setzt eine sachliche und eine personelle Verflechtung voraus. Die sachliche Verflechtung liegt vor, wenn eine wesentliche Betriebsgrundlage überlassen wird. Die personelle Verflechtung erfordert einen einheitlichen geschäftlichen Betätigungswillen. Beide Voraussetzungen müssen kumulativ vorliegen. Die Rechtsfolgen sind erheblich und sollten sorgfältig geprüft werden.

- **Sachliche Verflechtung:** Die Überlassung einer wesentlichen Betriebsgrundlage stellt das erste Merkmal dar.
- **Personelle Verflechtung:** Der einheitliche Betätigungswille bildet das zweite Merkmal ab.
- **Rechtsfolgen:** Die Umqualifizierung der Einkünfte markiert einen entscheidenden Wendepunkt.

## Herausforderungen Und Ausblick

Die Bandbreite der Gestaltungsmöglichkeiten reicht von der Gründung bis hin zur Nachfolge, von der Finanzierung bis zur Beendigung. Es könnte möglicherweise argumentiert werden, dass unter Umständen auch die Beendigung Risiken birgt. Trotz dieser Herausforderungen bleibt die Betriebsaufspaltung ein bewährtes Instrument.

## Fazit

Zusammenfassend lässt sich festhalten, dass eine maßgeschneiderte und ganzheitliche Beratung von entscheidender Bedeutung ist. Zögern Sie nicht, uns zu kontaktieren.
```

---

## Nachher

```markdown
# Betriebsaufspaltung: Wenn die Immobilie zum Betriebsvermögen wird

Sie vermieten Ihrer eigenen GmbH eine Halle. Zivilrechtlich sind das zwei getrennte Sachen: Ihr Privatvermögen hier, die Gesellschaft dort. Steuerlich kann daraus ein einziger Betrieb werden, ohne dass Sie etwas unterschreiben, ohne Antrag und ohne dass das Finanzamt Sie darauf hinweist.

Das nennt sich Betriebsaufspaltung. Der Preis dafür steht nicht im Mietvertrag: Er fällt beim Verkauf an und bei der Nachfolge, und bis dahin vergehen meist Jahrzehnte.

## Zwei Voraussetzungen, die zusammenkommen müssen

Die **sachliche Verflechtung** liegt vor, wenn Sie der Gesellschaft eine wesentliche Betriebsgrundlage überlassen. Bei einer Immobilie genügt dafür nach der Rechtsprechung, dass die Gesellschaft sie für ihren Betrieb tatsächlich braucht und nicht ohne Weiteres eine gleichwertige anmieten könnte; ein Bürogebäude in durchschnittlicher Lage reicht dafür bereits aus, was in der Beratungspraxis regelmäßig unterschätzt wird.

Die **personelle Verflechtung** verlangt, dass dieselbe Person oder Personengruppe in beiden Unternehmen ihren Willen durchsetzen kann. Bei Alleineigentum und Alleingesellschafterstellung liegt sie offensichtlich vor.

Beide müssen zusammenkommen. Fehlt eine, gibt es keine Betriebsaufspaltung. Genau darin liegt die Gestaltungsmöglichkeit, und genau darin liegt die Gefahr, weil sich beide Voraussetzungen ändern können, ohne dass irgendjemand etwas tut.

## Was das kostet

Aus Vermietungseinkünften werden gewerbliche Einkünfte. Damit fällt Gewerbesteuer an, das Grundstück wird Betriebsvermögen, und die Zehnjahresfrist des § 23 EStG gilt nicht mehr: Der Wertzuwachs ist steuerpflichtig, auch nach zwanzig Jahren.

Die GmbH-Anteile teilen dieses Schicksal. Auch sie werden Betriebsvermögen des Besitzunternehmens, und zwar ebenfalls, ohne dass jemand eine Erklärung dazu abgibt.

`[OLIVER-INPUT: Ein Zahlenbeispiel aus einem eigenen Mandat würde diesen Abschnitt tragen — Anschaffungskosten, Verkaufspreis, Steuerbelastung mit und ohne Verflechtung.]`

## Die gefährlichste Stelle ist das Ende

Eine Betriebsaufspaltung entsteht von allein. Sie endet auch von allein.

Stirbt der beherrschende Gesellschafter, wird die Beteiligung unter mehreren Erben aufgeteilt oder zieht die GmbH schlicht in ein anderes Objekt um, dann entfällt eine der beiden Voraussetzungen, und das Finanzamt behandelt diesen Tag als Betriebsaufgabe. Sämtliche stillen Reserven in Grundstück und Anteilen werden in diesem Moment versteuert. Es fließt kein Euro, aus dem sich die Steuer zahlen ließe.

Wer eine Immobilie an die eigene GmbH vermietet, hat sich damit auf eine Nachfolgeplanung festgelegt, ob er das wollte oder nicht.

## Was zu tun ist

Prüfen Sie zuerst, ob bei Ihnen bereits eine Betriebsaufspaltung besteht. Das ist keine theoretische Frage. Sie entsteht ohne Antrag und ohne Bescheid, und in vielen Fällen taucht sie in keiner Bilanz und in keinem Anlageverzeichnis auf, weshalb die Beteiligten oft erst beim Verkaufsgespräch davon erfahren.

Steht sie fest, gehört der Ausstieg geplant, solange Sie ihn selbst bestimmen können. Nachträglich ist er immer eine Aufgabe zum Teilwert.

Ein Risiko bleibt und gehört offen benannt: Jede Vermeidungsgestaltung schwächt entweder Ihre Kontrolle über das Objekt oder Ihre Kontrolle über die Gesellschaft. Eine Lösung, die beides unangetastet lässt, gibt es nicht.
```
