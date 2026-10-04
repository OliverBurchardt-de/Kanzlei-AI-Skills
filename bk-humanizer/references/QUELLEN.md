# Quellen

Woher der Slop-Katalog stammt und was an den einzelnen Quellen belastbar
ist. Abgerufen am 26.09.2026.

## Externe Quellen

### Wikipedia:Signs of AI writing (WikiProject AI Cleanup)

<https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing>

Die mit Abstand beste verfügbare Sammlung. Sie ist seit 2023 aus der
Durchsicht tausender verdächtiger Artikel und Entwürfe entstanden und
belegt jedes Muster mit echten Fundstellen.

**Belastbarkeit: hoch.** Sie beruht auf beobachteten Fällen, nicht auf
Vermutungen, und die Autoren kennzeichnen sie ausdrücklich als
beschreibend, nicht vorschreibend: *„observations, not rules"*.

**Zwei Einschränkungen, die für uns zählen:**

1. Sie ist auf **englische Enzyklopädietexte** zugeschnitten. Ein Teil der
   Merkmale ist nicht übertragbar. Das deutlichste Beispiel sind die
   typografischen Anführungszeichen: Im englischen Wikitext sind gerade
   Anführungszeichen üblich, also gelten `„…"` dort als Verdachtsmoment.
   Im Deutschen sind sie die korrekte Form und sagen nichts aus.
2. Sie zielt auf **Neutralität** als Ideal. Für einen Enzyklopädieartikel
   ist das richtig. Für einen Fachbeitrag mit Meinung ist es das nicht:
   Mehrere dort beanstandete Züge — ein Urteil, eine Prognose, eine
   Wertung — sind bei uns ausdrücklich erwünscht, solange sie begründet
   sind.

Die Seite warnt außerdem davor, sich auf automatische KI-Detektoren wie
GPTZero oder Pangram zu verlassen: Sie schlagen zwar besser als der Zufall
an, haben aber nennenswerte Fehlerquoten. Diese Warnung ist in `SKILL.md`
und in `MESSWERTE.md` übernommen.

Zugriff im September 2026: Der Volltext war aus dieser Umgebung nicht
abrufbar, weil `en.wikipedia.org` von der Netzwerkregel der Umgebung
gesperrt ist. Verwendet wurde daher die vollständige Aufbereitung im
installierten Skill `humanizer` (Version 2.5.1, MIT-Lizenz), der sich
ausdrücklich auf diese Seite stützt und ihre 29 Muster mit Beispielen
wiedergibt, ergänzt um Suchergebnisse zur Seite selbst.

### Deutschsprachige Sammlungen

Für die mit `[DE]` gekennzeichneten Merkmale. Belastbarkeit
**mittel**: Es sind Praxisbeobachtungen aus Redaktion, SEO und Marketing,
keine systematische Auswertung. Sie decken sich aber untereinander und mit
dem, was im hiesigen Korpus messbar ist.

- [ContentConsultants, Udo Raaf: KI-Texte erkennen](https://www.contentconsultants.de/ki-texte-erkennen-warum-man-texte-besser-selbst-schreibt/)
- [eology: Typische Merkmale von ChatGPT-Texten](https://www.eology.de/news/merkmale-von-chatgpt-typischen-texten-beim-ai-roundtable)
- [mindtwo: Typische ChatGPT-Formulierungen](https://marketing.mindtwo.de/blog/typische-chatgpt-phrasen-ki-content-entlarven-und-optimieren)
- [Golem Karrierewelt: KI-Texte erkennen](https://karrierewelt.golem.de/blogs/karriere-ratgeber/ki-texte-erkennen-auf-diese-merkmale-musst-ihr-achten)
- [CHARISMARCOM: Typische KI-Formulierungen vermeiden](https://www.charismarcom.de/post/typische-ki-formulierungen-vermeiden/)

Übereinstimmend genannt und in den Katalog übernommen:

- Wortschatz: essenziell, vielfältig, nahtlos, maßgeschneidert,
  ganzheitlich, „umfassender Leitfaden", „das nächste Level".
- Brückenfloskeln: „Es ist wichtig zu beachten, dass …", „Insgesamt lässt
  sich festhalten …", „Zusammenfassend lässt sich sagen".
- Häufung der Modalverben, vor allem „kann" — relativiert Aussagen und
  nimmt ihnen die Kraft (Katalog Abschnitt 7).
- Hilfsverbstil mit „werden", „können", „haben" statt eines tragenden
  Verbs.
- Gehäufte Satzanfänge mit „Dieser / Diese / Dieses" (Abschnitt 14).
- Dreiergliederung als Reflex: drei Tipps, drei Argumente, drei Schritte
  (Abschnitt 11).
- Fettlisten im Muster `**Begriff:** Erklärung` (Abschnitt 16).
- Überschriftenflut mit zwei bis drei Sätzen je Abschnitt (Abschnitt 17).
- „Tauchen Sie ein in eine Welt …" als Werbeformel (Abschnitte 3 und 18).

Eine Quelle hält fest, dass Erkennungswerkzeuge für **deutsche** Texte
noch deutlich unzuverlässiger sind als für englische. Das stützt die
Entscheidung, in diesem Skill nur messbare Oberflächenmerkmale zu
erheben und daraus keine Urheberschaftsaussage abzuleiten.

### Der installierte Skill `humanizer`

`~/.claude/skills/synced/…/humanizer/` (Version 2.5.1, MIT).

Gute, vollständige Aufbereitung der Wikipedia-Liste mit Vorher/Nachher zu
jedem Muster. Sein Verfahren am Schluss — den eigenen Entwurf noch einmal
mit der Frage *„What makes the below so obviously AI generated?"*
anzugreifen und danach zu überarbeiten — ist wirksam und in `SKILL.md`,
Durchgang 6, sinngemäß übernommen.

**Wo wir bewusst abweichen**, und das ist der wichtigste Punkt dieser
Datei:

Der Skill empfiehlt im Abschnitt *Personality and Soul*, dem Text Seele zu
geben, indem das Modell Meinungen äußert, gemischte Gefühle zeigt,
Abschweifungen einbaut und „etwas Unordnung hereinlässt". Sein eigenes
Beispiel lautet: *„I genuinely don't know how to feel about this one."*

Für einen anonymen Blogpost mag das tragen. Für einen Steuerberater, der
unter seinem Namen über Rechtsfragen schreibt, ist es gefährlich. Ein
Modell, das angewiesen ist, Persönlichkeit zu erzeugen, erfindet
Persönlichkeit — und im Fachtext heißt das: erfundene Mandate, erfundene
Verfahren, erfundene Zahlen. Genau davor steht die Grenze in `SKILL.md`,
Abschnitt **Echtheit**.

Unsere Antwort auf dasselbe Problem ist eine andere: Statt das Modell
Persönlichkeit erfinden zu lassen, beschafft Durchgang 1 echtes Material
beim Autor, und Durchgang 4 setzt Züge ein, die aus seinen eigenen Texten
belegt sind. Das ist aufwendiger und liefert den einzigen Ton, der hält.

### Die Vorlage im Haus

`Blogartikel/references/HUMANIZER-DE.md` — die frühere, auf Blogartikel
zugeschnittene Fassung. Ihre Durchgänge und der Gedanke der
Serienprüfung sind hier aufgegangen. Zum Verhältnis der beiden Dateien
siehe `KORPUS.md`, Abschnitt *Verhältnis zu bk-blogartikel*.

## Eigene Erhebung

Die Zahlen in `MESSWERTE.md` und die Referenzwerte in `slop_scan.py` sind
am 26.09.2026 über die Texte in `korpus/` erhoben worden, dazu eine
Auswertung aller 55 veröffentlichten Blogbeiträge auf burchardt-kollegen.de
über den Novamira-Zugang. Verfahren, Stichprobengröße und die Grenzen der
Aussage stehen in `MESSWERTE.md` und `KORPUS.md`.

Die Abschnitte 19 bis 21 des Katalogs (Belletristik) stammen
ausschließlich aus dieser Erhebung. Die externen Quellen behandeln
Sachtext; für erzählende Prosa nennen sie keine Merkmale.
