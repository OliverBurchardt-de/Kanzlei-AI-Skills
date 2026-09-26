# Design-System Burchardt & Kollegen (Referenz für Claude)

> Quelle: Gestaltungsrichtlinien-PDF (InDesign, Stand 04/2022) + Logo-SVG.
> Web-Übersetzung der ursprünglich printorientierten Vorgaben. Stand: 2026-07.
> Abweichungen vom Quell-PDF sind unter „Offene Punkte" dokumentiert.

**Geltungsbereich:** Dieses Design-System gilt nur für Projekte, die unter der Marke Burchardt & Kollegen laufen. Neue Websites können bewusst ohne Kanzlei-Branding aufgebaut werden – dann gilt dieses File nicht, und die Gestaltung wird projektweise festgelegt. Zu Projektbeginn klären: Läuft das Projekt unter der Kanzlei-Marke?

## 1. Farb-Tokens

Alle Farben ausschließlich über diese Custom Properties verwenden – nie hartcodiert.

```css
:root {
  /* Hauptfarben laut Gestaltungsrichtlinie */
  --bk-gold: #F7B234;        /* Gelb-Orange: Logo-Akzent, Flächen, NIE für Text auf hellem Grund */
  --bk-gold-tint: #FCE0B0;   /* Abtönung ~35 % der Hauptfarbe: helle Flächen, Verlaufs-Endpunkt */
  --bk-blau: #0080C9;        /* Kräftiges Blau: Flächen, Verläufe */
  --bk-dunkelblau: #3A5791;  /* Dunkelblau: Überschriften, Logo-Text laut Richtlinie */
  /* Zweitfarben */
  --bk-rot: #E94E1B;         /* Hellrot: optische Betonungen, Buttons – nur als Fläche mit weißem Text in großer Schrift, siehe Kontrast-Matrix */
  --bk-anthrazit: #333333;   /* Anthrazit: Standard-Lesetext auf hellem Grund */
  /* Abgeleitete Web-Tokens */
  --bk-weiss: #FFFFFF;       /* Grundfläche */
  --bk-text: var(--bk-anthrazit);      /* semantischer Alias: Fließtext */
  --bk-heading: var(--bk-dunkelblau);  /* semantischer Alias: Überschriften */
}
```

## 2. Kontrast-Matrix (WCAG, berechnet)

| Kombination | Ratio | Zulässig für |
|---|---|---|
| Anthrazit auf Weiß | 12,6:1 | Fließtext ✓ |
| Dunkelblau auf Weiß | 7,1:1 | Fließtext, Überschriften ✓ |
| Anthrazit auf Gold | 6,8:1 | Text auf Gold-Flächen ✓ |
| Weiß auf Dunkelblau | 7,1:1 | Text auf dunkelblauen Flächen ✓ |
| Weiß auf Kräftigem Blau | 4,3:1 | NUR großer Text (≥ 24 px / ≥ 18,7 px bold) und UI-Elemente |
| Dunkelblau auf Gold | 3,9:1 | NUR großer Text und UI-Elemente |
| Weiß auf Hellrot | 3,8:1 | NUR großer Text und UI-Elemente (Buttons: Beschriftung groß/bold halten) |
| **Gold auf Weiß** | **1,9:1** | **VERBOTEN für Text und Icons mit Bedeutung – nur Deko/Flächen** |

Regeln daraus:
- Fließtext: Anthrazit auf Weiß (Default) oder Weiß auf Dunkelblau.
- Buttons in Hellrot: weiße Beschriftung, mindestens 18,7 px bold; sonst Dunkelblau-Button verwenden.
- Gold trägt nie Information allein – es ist Akzent- und Flächenfarbe.

## 3. Typografie

Beide Familien sind Google Fonts → **immer lokal hosten** (woff2 im Projekt, `font-display: swap`, Subsetting latin/latin-ext). Nie von fonts.googleapis.com laden.

```css
:root {
  --font-heading: 'Petrona', Georgia, serif; /* Überschriften und Betonungen; Fallback systemnahe Serife */
  --font-text: 'Aleo', Georgia, serif;       /* Fließtext; Fallback systemnahe Serife */
}
```

- **Petrona** (Überschriften/Betonungen): verfügbare Schnitte laut Richtlinie regular, italic, medium (500), semibold (600), extra bold (800). Web-Default: semibold 600 für h1–h3, medium 500 für h4–h6.
- **Aleo** (Text): light (300), regular (400), bold (700) + kursiv. Web-Default: regular 400, Fließtext ≥ 16 px, Zeilenhöhe 1.5–1.6.
- Performance-Budget aus best-practices.md gilt: maximal 4 geladene Schnitte pro Seite – Standard-Set: Petrona 600, Aleo 400, Aleo 700, Aleo 400 italic. Weitere Schnitte nur bei Bedarf.

## 4. Logo

Das Logo ist kein Pflichtelement – es kommt nur auf Seiten zum Einsatz, die ausdrücklich unter der Kanzlei-Marke auftreten. Wenn es verwendet wird:

- **Hauptlogo:** Wortmarke „Burchardt & Kollegen" in Dunkelblau, „&" als Gold-Verlaufs-Akzent mit Aufwärtsschwung. Einsatz auf weißem/hellem Grund.
- **Varianten:** einfarbig Schwarz (Sonderfälle Druck), Weiß (auf Gold- oder Blau-Flächen).
- Immer als SVG einbinden (`Burchardt-Kollegen-Logo_288x53px.svg`, Seitenverhältnis 288:52,4 ≈ 5,5:1); feste `width`/`height` setzen (CLS).
- Aussagekräftiger Alt-Text: `alt="Burchardt & Kollegen Steuerberatung Wirtschaftsprüfung"` (verlinkt das Logo zur Startseite, beschreibt der Alt-Text das Ziel: `alt="Zur Startseite – Burchardt & Kollegen"`).
- Schutzraum: mindestens Höhe des „B" umlaufend freihalten; Logo nie verzerren, umfärben oder mit Effekten versehen.

## 5. Flächen & Verläufe

Markentypisches Hintergrund-Element: Blau- und Gold-Verläufe mit **Schrägen oben oder unten** (leicht geneigte Kante, kein horizontaler Abschluss).

```css
.bk-flaeche-blau {
  background: linear-gradient(135deg, var(--bk-dunkelblau), var(--bk-blau)); /* Verlauf dunkel → kräftig, diagonal */
  clip-path: polygon(0 0, 100% 3%, 100% 100%, 0 97%);                        /* Schräge oben und unten, ~3 % Neigung */
}
.bk-flaeche-gold {
  background: linear-gradient(135deg, var(--bk-gold), var(--bk-gold-tint));  /* Verlauf Vollton → Abtönung */
  clip-path: polygon(0 3%, 100% 0, 100% 97%, 0 100%);                        /* gegenläufige Schräge zur blauen Fläche */
}
```

- Auf Blau-Verläufen: weißer Text (Größenregel aus Kontrast-Matrix beachten – der Verlauf enthält `--bk-blau`, also für Fließtext ungeeignet; Überschriften ok).
- Auf Gold-Verläufen: Text in Anthrazit oder Dunkelblau (Dunkelblau nur groß).
- Schrägen dezent halten (2–4 % Neigung), Richtung pro Seite konsistent.

## 6. Komponenten-Konventionen

- Präfix `bk-` für alle eigenen Klassen (bestehendes bk-lohn-Framework fortführen).
- Buttons: Primär = Hellrot-Fläche/weiße Bold-Beschriftung; Sekundär = Dunkelblau-Outline. Fokus-Ring sichtbar in Dunkelblau, 2 px, 2 px Offset.
- Links im Fließtext: Dunkelblau + unterstrichen (Farbe allein reicht nicht, siehe best-practices.md §5).

## 7. Offene Punkte / Abweichungen der Quelle

1. **Anthrazit-Widerspruch im PDF:** RGB ist dort mit 100/100/100 (= #646464) angegeben, der Web-Wert mit #333333. Festgelegt: **#333333** gilt für Web (besserer Kontrast, konsistent mit CMYK K80).
2. **Logo-Blau-Abweichung (entschieden):** Das gelieferte SVG verwendet #3E5D9C, die Richtlinie nennt #3A5791. Festgelegt: **Die Richtlinienwerte sind verbindlich für alles CSS**; das SVG bleibt als Original unangetastet. Die minimale Abweichung wird bewusst akzeptiert.
3. **Abtönung 35 %:** Im PDF nur als Farbfeld ohne Wert. #FCE0B0 ist als 35-%-Mischung mit Weiß gesetzt – bei Bedarf durch exakten Wert des Grafikers ersetzen.
4. Die Richtlinie ist printorientiert (2022): Größenskala, Abstände und Button-Detailregeln in diesem File sind Web-Setzungen von Claude, nicht Teil der Original-Richtlinie.
