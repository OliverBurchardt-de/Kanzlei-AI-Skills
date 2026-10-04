# Messwerte

Die Zahlen hinter `slop_scan.py`: woher sie stammen, wie sie zu lesen sind
und was sie nachweislich nicht erkennen.

Erhoben am 26.09.2026 über die Texte in `korpus/`, am 04.10.2026 korrigiert:
Der YAML-Kopf der Korpusdateien wurde bis dahin als Fließtext mitgezählt und
hat Satzlänge, Streuung und Gedankenstrichdichte leicht verschoben. Das
Skript entfernt ihn jetzt vor der Messung; die Tabellen unten zeigen die
bereinigten Werte.

## Die Referenzwerte

### Profil `fachtext`

| Datei | Wörter | Ø Satz | Streuung | ≤8 W | ≥30 W | Striche/1k | Füller/1k |
|---|---:|---:|---:|---:|---:|---:|---:|
| Restnutzungsdauer | 3279 | 14,8 | 9,2 | 27 % | 6 % | 2,74 | 0 |
| Familienheim | 1321 | 19,1 | 9,0 | 14 % | 12 % | 2,27 | 0 |
| Praxis im eigenen Haus | 1277 | 14,5 | 8,9 | 24 % | 4 % | 0 | 0 |

Daraus die Spannen: Satzlänge 13–22, Streuung ab 7,5, kurze Sätze ab
12 %, Gedankenstriche bis 5,0, Füllformeln bis 1,0.

Die Schwellen liegen bewusst knapp **unter** dem schwächsten Kanonwert und
nicht auf ihm. Ein echter Text soll nicht beim ersten Ausreißer anschlagen;
der Abstand zu den Gegenproben ist mit 8,9 gegen 4,3 immer noch groß.

### Profile `fiktion-knapp` und `fiktion-kaskade`

| Datei | Wörter | Ø Satz | Streuung | ≤8 W | ≥30 W | Striche/1k |
|---|---:|---:|---:|---:|---:|---:|
| Bikini, Tonprobe Kap. 9 | 851 | 11,5 | 5,7 | 34 % | 0 % | 0 |
| A Life Between Names, Kap. 35 | 1256 | 22,4 | 17,2 | 25 % | 32 % | 12,74 |

Die beiden Zeilen stehen fast überall im Verhältnis eins zu zwei. Deshalb
gibt es zwei Profile und nicht eines mit weiter Spanne: Ein Mittelwert
über beide würde jeden der beiden Töne für richtig erklären und keinen
schützen.

## Die Gegenproben

Ohne Gegenprobe ist ein Maßstab wertlos. Geprüft wurde an zwei Texten, die
ausschlagen sollen.

**Ein Blogbeitrag mit hoher Floskeldichte** (Profil `fachtext`): Streuung
4,3 statt mindestens 8,0; 4 % kurze Sätze statt mindestens 13 %;
Absatzlängen mit einer Streuung von nur 23 % des Mittels; 4,51
Floskeltreffer je 1000 Wörter. Vier Befunde der Stufe *Hinsehen*.

**Kapitel 1 von *A Life Between Names*** (Profil `fiktion-kaskade`):
Streuung 11,0 statt mindestens 14,0, dazu fünf gedeutete
Redebegleitsätze. Zwei Befunde der Stufe *Hinsehen*.

Die fünf Kanontexte erzeugen gegen ihr jeweils richtiges Profil **null**
Befunde der Stufe *Hinsehen*.

Der synthetische Prüftext mit allen Formatmaschen löst zusätzlich
Kopula-Vermeidung, Chatbot-Rückstände, Emojis, Fettlisten, falsche
Spannen, Autoritätsgestus, Absicherungsstapel, Überschriftenflut und
Aufwärmsätze aus.

## Wie die Werte zu lesen sind

**Die Streuung ist die aussagekräftigste Zahl.** Sie trennt in beiden
Registern am schärfsten, und zwar besser als der Mittelwert. Kapitel 1 und
Kapitel 35 desselben Buches unterscheiden sich im Mittelwert kaum
auffällig, in der Streuung um mehr als die Hälfte.

Das hat einen Grund: Ein Sprachmodell trifft den durchschnittlichen Satz
gut. Was es nicht trifft, ist die Entscheidung, wann ein Satz aus vier
Wörtern besteht und der nächste aus vierzig.

**Zwei Stufen der Befunde.** *Hinsehen* heißt, dass mehrere Kanontexte an
dieser Stelle deutlich anders liegen. *Notiert* heißt, dass etwas
aufgefallen ist, das auch harmlos sein kann.

**Keine Stufe heißt Mangel.** Ein verständlicher Absatz wird nicht
umgebaut, weil eine Zahl ausschlägt. Wer nach Kennzahl umschreibt, erzeugt
genau die Gleichförmigkeit, die hier gesucht wird — nur um einen anderen
Mittelwert herum.

## Was das Skript nicht erkennt

Diese Liste ist wichtiger als die Tabellen darüber, weil sie sagt, wofür
weiterhin ein Mensch gebraucht wird.

**Inhaltliche Leere.** Ein Text kann jede Kennzahl treffen und trotzdem
nichts sagen, was der Leser nicht schon wusste. Das ist Durchgang 2 im
Ablauf, und keine Messung ersetzt ihn.

**Erfundene Erfahrung.** „Wir haben gerade zwei Fälle" misst sich genau
wie ein belegter Satz. Die Echtheitsprüfung ist ausschließlich
menschlich.

**Falsche Fachaussagen.** Das Skript liest keine Fundstellen und rechnet
keine Beispiele nach. Dafür ist das Evidenzprotokoll in `bk-blogartikel`
da.

**Die Serienwirkung.** Ob ein Text der fünfte in Folge mit demselben
Einstieg ist, sieht nur der Vergleich. Siehe `KORPUS.md`,
*Serienprüfung*.

**Ob ein Satz zwingt.** Spannung, Einsatz, Neugier — dafür gibt es keinen
Messwert, und es wird keinen geben. Das ist Durchgang 6.

**Kurze Texte.** Unter etwa 400 Wörtern sind Streuungswerte Zufall. Das
Skript verweigert die Auswertung unter fünf Sätzen, aber zwischen fünf
Sätzen und 400 Wörtern ist es unzuverlässig, ohne das zu melden.

## Was die Werte nicht bedeuten

Sie sagen **nicht**, ob ein Text von einer Maschine stammt.

Die Autoren von *Wikipedia:Signs of AI writing* weisen ausdrücklich darauf
hin, dass selbst spezialisierte Erkennungswerkzeuge wie GPTZero oder
Pangram nennenswerte Fehlerquoten haben, und für deutsche Texte sind sie
noch deutlich schwächer als für englische. Ein paar Regulären Ausdrücken
gelingt es erst recht nicht.

Was das Skript misst, ist etwas anderes und Nützlicheres: **ob ein Text
austauschbar geschrieben ist.** Diese Frage ist unabhängig davon, wer ihn
geschrieben hat, und sie ist die Frage, auf die es ankommt. Ein Mensch
kann austauschbar schreiben, und die drei Kanontexte zeigen, dass ein Text
mit Modellbeteiligung es nicht muss.

Ein Vorwurf der KI-Urheberschaft wird aus diesen Zahlen nicht abgeleitet.
Weder gegenüber Dritten noch gegenüber dem eigenen Entwurf.

## Nach einer Erweiterung des Korpus

Neue Kanontexte verschieben die Spannen. Das Vorgehen steht in
`KORPUS.md`, Abschnitt *Danach messen*. Ändert sich eine Spanne, wird sie
an beiden Stellen nachgeführt: in `REFERENZ` in `scripts/slop_scan.py` und
in den Tabellen oben. Die Kommentare im Skript nennen jeweils die Werte,
aus denen die Spanne stammt, damit die Herkunft nachvollziehbar bleibt.
