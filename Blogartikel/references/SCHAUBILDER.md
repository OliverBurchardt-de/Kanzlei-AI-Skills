# Schaubilder

Verbindliche Spezifikation. Jedes Schaubild für den Blog folgt diesen Vorgaben,
damit die Reihe über Jahre einheitlich bleibt.

**Diese Datei wird nur gelesen, wenn tatsächlich ein Schaubild erzeugt wird.**

Der Skill kann Schaubilder vollständig produzieren, sofern die Umgebung
Codeausführung mit `cairosvg` und `Pillow` bietet. Das Skript dazu liegt unter
`scripts/svg_nach_webp.py`. Fehlt diese Möglichkeit, liefert der Skill
stattdessen ein Bildbriefing im CMS-Handoff: Datengrundlage, gewünschte
Aussage, Alt-Text-Entwurf und Bildunterschrift. Die Produktion erfolgt dann
getrennt.

---

## Wann ein Schaubild gebaut wird

**Ja**, wenn eine Zahl durch mehrere Stufen wandert und der Sprung sichtbar
werden soll. Beispiel: Jahreswert mal Kapitalisierungsfaktor.

**Ja**, wenn zwei Ergebnisse aus demselben Sachverhalt entstehen und das
Verhältnis die Botschaft trägt. Beispiel: Steuer mit und ohne Nachweis.

**Nein** bei Prüfschritten und Rechtslage. Ein Ablaufdiagramm zu „Ist das
Darlehen anzuerkennen?" wird zur Liste in Kästchen; der Text kann das besser,
weil er Zwischentöne mitliefert.

**Nein als Dekoration.** Ein Bild, das wiederholt, was danebensteht, kostet
Ladezeit und bringt nichts.

**Nie doppelt zur Tabelle.** Zeigen Schaubild und Tabelle dieselben Werte,
entfällt das Schaubild. Zahlen in Grafiken sind für Suchmaschinen unsichtbar und
für Screenreader nur über den Alt-Text erreichbar. Wo beide nebeneinander
bestehen, trägt die Tabelle die Herleitung und das Schaubild die Proportion oder
den Mechanismus — niemals beide dasselbe.

Höchstens zwei Schaubilder pro Artikel.

---

## Farben

Ausschließlich diese Werte. Keine Verläufe, keine Schatten, keine zusätzlichen
Farbtöne.

| Zweck | Wert |
|---|---|
| Struktur, Überschriften, Zahlen | `#3A5791` Dunkelblau |
| Hervorhebung, Akzentkante, Nummernkreis der betonten Stufe | `#F7B234` Gold |
| Fließtext im Bild | `#333333` Anthrazit |
| Sekundärtext, Fußnote, Legende | `#5A6070` Grau |
| Neutrale Kastenfläche | `#F6F8FB` |
| Rahmen neutraler Kästen | `#D8DEE9` |
| Hervorgehobene Kastenfläche | `#FDF3E0` |
| Rahmen hervorgehobener Kästen | `#F7B234`, 2 px |
| Trennlinie in neutralen Kästen | `#C9D2E0` |
| Trennlinie in goldenen Kästen | `#EBC98A` |
| Fläche der Ergebniszeile | `#3A5791` |
| Text auf Dunkelblau | `#FFFFFF`, sekundär `#C3D2E8` |
| Grundfläche | `#FFFFFF` |

**Gold trägt nie Information und steht nie als Text auf Weiß.** Der Kontrast
liegt bei 1,9:1. Gold ist Fläche, Kante oder Text auf dunkelblauem Grund.

**Farbe allein darf nichts bedeuten.** Wird eine Stufe hervorgehoben, bekommt sie
zusätzlich eine dickere Kante und einen erklärenden Hinweis.

---

## Schrift

`font-family="Georgia, 'Times New Roman', serif"` als Attribut am `svg`-Element.

Petrona und Aleo werden **nicht** verwendet. Sie sind auf dem rendernden System
nicht zwingend installiert, und der Fallback wäre unkontrolliert. Georgia ist auf
Windows und macOS vorhanden und passt in der Anmutung zur Marke.

| Element | Größe | Schnitt |
|---|---|---|
| Titel | 21 px | bold |
| Untertitel | 14 px | normal |
| Kastenüberschrift | 15 px | bold |
| Beschreibungstext | 13 px | normal |
| Ergebniszahl im Kasten | 24 px | bold |
| Ergebniszahl in der blauen Zeile | 20 px | bold |
| Fußnote | 11 px | normal |

---

## Aufbau

**Leinwand:** `viewBox="0 0 880 H"`. Breite immer 880, Höhe nach Bedarf.
Weißes Rechteck als erstes Element über die volle Fläche.

**Kopf:** Titel bei `x=36, y=42`. Untertitel mit dem Zahlenbeispiel bei `y=66`.
Darunter der goldene Balken: `x=36 y=80 width=64 height=4 rx=2`.

**Stufenkästen:** Breite 236, Höhe 136, `rx=6`. Abstand 50 zwischen den Kästen.
Aufbau von oben nach unten:

1. Nummernkreis `r=14` mit weißer Ziffer, daneben die Kastenüberschrift
2. zwei Zeilen Beschreibung, Abstand 20
3. dünne Trennlinie
4. Ergebniszahl, 24 px, linksbündig

**Die Zahl steht immer unter der Beschreibung, nie daneben.** Das ist die Regel,
an der die erste Fassung gescheitert ist: Bei rechtsbündigen Zahlen lief der
Beschreibungstext hinein.

**Pfeile:** waagerechte Linie 26 lang, 2 px, plus Dreieck als Spitze.

**Gegenüberstellung zweier Seiten:** zwei Kästen von je 340 bis 384 Breite,
dazwischen 128 Freiraum. Trägt ein Vorgang eine Richtung, etwa einen Zahlungsfluss,
gehört ein beschrifteter Pfeil zwischen die Kästen. Die vorteilhaftere oder
riskantere Seite wird golden hervorgehoben, nie beide.

**Ergebniszeile** (optional): dunkelblaues Rechteck über die volle Breite,
Überschrift weiß, darunter je Spalte Label, Zahl in Gold und Zusatzzeile —
untereinander, nie nebeneinander.

**Fußnote:** unten links, 11 px, nennt Vereinfachungen und ausgelassene Faktoren.

---

## Barrierefreiheit

Verbindlich:

```xml
<svg role="img" aria-labelledby="t d">
  <title id="t">Kurztitel</title>
  <desc id="d">Vollständige Beschreibung mit allen Zahlen</desc>
```

Die `desc` enthält jede Zahl, die im Bild steht. Wer das Bild nicht sieht, muss
dieselbe Information bekommen.

Kontrast mindestens 4,5:1 für Text. Geprüfte Kombinationen: Dunkelblau auf Weiß
7,1:1, Anthrazit auf Weiß 12,6:1, Grau `#5A6070` auf Weiß 6,4:1, Weiß auf
Dunkelblau 7,1:1.

---

## Textbreiten prüfen

**Vor der Ausgabe rechnerisch kontrollieren, ob jeder Text in seinen Kasten
passt.** Georgia belegt etwa 0,52 em je Zeichen im Normalschnitt und 0,56 em im
Fettschnitt.

```
Endposition = x + Zeichenzahl × Schriftgröße × Faktor
```

Mindestens 20 px Luft zur Kastengrenze. Diese Prüfung ist kein optionaler
Zwischenschritt: Die erste Fassung des ersten Schaubilds hatte drei
Überlappungen, die im SVG-Quelltext nicht auffielen.

---

## Ausgabe

**WebP für WordPress**, Breite 1760 px, aus dem SVG gerendert. WordPress blockiert
SVG-Uploads standardmäßig aus Sicherheitsgründen; WebP wird von allen aktuellen
Browsern unterstützt.

**Verlustfrei speichern** (`lossless=True`). Bei Grafiken mit Text und großen
einfarbigen Flächen ist die verlustfreie Datei nicht größer als die
verlustbehaftete, oft sogar kleiner — und die Schrift franst nicht aus. Nur
Fotos werden verlustbehaftet gespeichert, dort mit Qualität 82.

Die Höhe ergibt sich aus dem Seitenverhältnis der viewBox, sie wird nicht
geschätzt. Sonst verzerrt das Bild.

```python
import cairosvg
from PIL import Image

svg = open('name.svg', encoding='utf-8').read()
vb = svg.split('viewBox="')[1].split('"')[0].split()
breite = 1760
hoehe = round(breite * float(vb[3]) / float(vb[2]))

cairosvg.svg2png(url='name.svg', write_to='/tmp/tmp.png',
                 output_width=breite, output_height=hoehe,
                 background_color='white')
Image.open('/tmp/tmp.png').convert('RGB').save(
    'name.webp', 'WEBP', lossless=True, method=6)
```

**SVG als Quelldatei** mitliefern, damit Texte später änderbar bleiben.

**Dateiname** sprechend und mit Bindestrichen, weil WordPress ihn in die URL
übernimmt: `schaubild-zinsvorteil-berechnung.webp`.

**Alt-Text und Bildunterschrift** werden immer mitgeliefert. Der Alt-Text
beschreibt, was zu sehen ist. Die Bildunterschrift wiederholt das nicht, sondern
nennt die Pointe.

---

## Wenn Zahlen sich ändern

Ein Schaubild aktualisiert sich nicht mit dem Text. Wird eine Zahl im Artikel
geändert, muss das Bild neu erzeugt werden. Deshalb die Beschränkung auf zwei
Schaubilder pro Artikel und auf Werte, die stabil sind.
