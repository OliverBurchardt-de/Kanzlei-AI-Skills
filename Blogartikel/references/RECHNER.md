# Rechner und interaktive Elemente

Ein Rechner lässt den Leser die Rechnung auf seinen eigenen Fall anwenden. Das
ist der stärkste Hebel für Verweildauer, den ein Fachartikel hat — Besucher
probieren mehrere Szenarien durch.

## Wann ein Rechner sinnvoll ist

**Ja**, wenn der Artikel eine Formel enthält, deren Ergebnis stark von wenigen
Eingaben abhängt: Steuersätze, Beträge, Laufzeiten.

**Ja**, wenn die Antwort „kommt darauf an" lautet und der Leser wissen will,
worauf.

**Nein** bei Rechtsfragen ohne Rechengrößen. Ein Rechner, der nur Ja oder Nein
ausgibt, ist ein Formular ohne Nutzen.

**Nein**, wenn die Rechnung mehr als sechs Eingaben braucht. Dann wird aus dem
Werkzeug ein Fragebogen, und der Leser bricht ab.

## Der wichtigste inhaltliche Punkt

**Ein Rechner zeigt beide Seiten.** Wettbewerber bauen Rechner, die nur die
Ersparnis ausweisen. Genau das macht sie unglaubwürdig.

Der Rechner zum Restnutzungsdauer-Artikel hat deshalb zwei Blöcke: „Der Vorteil"
und „Das Risiko", darunter eine Fazitzeile, die beides gegeneinanderstellt. Bei
ungünstigen Annahmen sagt er ausdrücklich, dass die Gestaltung mehr kostet, als
sie einbringt.

Das ist kein Nachteil, sondern der Grund, warum der Rechner Vertrauen schafft.

**Jeder Rechner braucht einen Disclaimer**: vereinfachtes Modell, keine
steuerliche Beratung, Aufzählung dessen, was nicht berücksichtigt ist.

## Technischer Einbau in WordPress mit Enfold

Diese Reihenfolge ist das Ergebnis mehrerer Fehlversuche. Abkürzungen kosten
Zeit.

**1. Markup über einen Shortcode ausliefern, nicht über den Code-Block.**

Enfolds Code-Block entfernt `div`-Container aus dem Beitragsinhalt. Überschriften,
Absätze und Formularfelder überleben, jeder Container nicht — damit bricht jedes
Layout, das auf Grid oder Flex beruht.

Der Shortcode wird über ein Snippet-Plugin registriert, nicht in der
`functions.php` des Themes. Ein fehlerhaftes Snippet lässt sich im Backend
abschalten, ein Fehler in der `functions.php` legt die Seite lahm.

Im Beitrag steht dann nur `[name_des_shortcodes]` in einer eigenen Zeile im
Textblock.

**2. CSS ins Quick CSS, nicht in den Shortcode.**

WordPress entfernt `style`-Tags und Inline-Stilangaben aus dem Beitragsinhalt.
Auch `style="grid-column:1/-1"` als Attribut überlebt nicht.

**3. Keine Selektoren, die einen bestimmten Elternknoten voraussetzen.**

Insbesondere `#top` nicht ungeprüft übernehmen. Es steht in vielen
Enfold-Anleitungen, greift aber nicht in jedem Layout. Sind die eigenen Klassen
mit einem Präfix versehen, braucht es die Absicherung ohnehin nicht.

Wo Enfold eigene Werte setzt — bei `display` auf `div`, bei Überschriften und
Absatzabständen — hilft `!important` an der einzelnen Eigenschaft.

**4. JavaScript wird mit dem Shortcode ausgeliefert.**

Es überlebt die Filter, anders als das CSS. Es läuft dann nur auf Seiten, auf
denen der Shortcode tatsächlich vorkommt.

## Diagnose, wenn nichts greift

**Erst prüfen, dann bauen.** Eine einzelne Testregel klärt in zwanzig Sekunden,
was drei Umbauten nicht klären:

```css
.meine-klasse { outline: 4px solid red; }
```

- **Rahmen erscheint** → Element und CSS sind da. Das Problem liegt bei einem
  einzelnen Selektor oder einer überschreibenden Regel.
- **Kein Rahmen** → entweder fehlt das Element im DOM oder das CSS kommt nicht an.
  Im Entwicklertool nachsehen, welches von beidem.

Wer aus dem gerenderten Bild auf die Ursache schließt, sucht an der falschen
Stelle. Ein Blick ins DOM ist immer der erste Schritt.

## Barrierefreiheit

- jedes Feld mit `<label for="…">`
- Ergebnisbereiche mit `aria-live="polite"`, damit Änderungen vorgelesen werden
- sichtbarer Fokusring über `:focus-visible`
- Kontraste wie im übrigen Design-System
- `prefers-reduced-motion` respektieren

## Ausgabe

Der Skill liefert vier Dateien:

1. das PHP-Snippet mit Markup und JavaScript
2. den CSS-Block zum Anhängen ans Quick CSS
3. eine Rechenprobe mit mindestens drei Fällen, darunter ein Grenzfall
4. Einbauanweisung mit Shortcode-Name und Position im Artikel

**Die Rechenprobe ist Pflicht.** Jede Formel wird unabhängig nachgerechnet, bevor
der Rechner ausgeliefert wird. Beim AfA-Rechner hat sie bestätigt, dass ein realer
Mandatsfall zu einem Minus führt — das war die Kernbotschaft des Artikels und
zugleich der Nachweis, dass die Logik stimmt.
