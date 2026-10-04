# Einbau des Förderrechners auf burchardt-kollegen.de

## Dateien

| Datei | Zweck |
|---|---|
| `bk-avd-rechner-snippet.php` | Registriert den Shortcode `[bk_avd_rechner]`; liefert Markup und JavaScript |
| `bk-avd-rechner-quickcss.css` | CSS-Block zum Anhängen an das Enfold Quick CSS |
| `vorschau.html` | lokale Vorschau zum Ausprobieren (nicht hochladen) |
| `rechenprobe.md` | Rechenprobe mit elf Fällen, darunter Grenzfälle |
| `quelle/` | bearbeitbare Quellen; `python3 quelle/build.py` erzeugt die drei Dateien oben neu |

Änderungen immer in `quelle/` vornehmen und neu bauen, nie in den erzeugten Dateien.

## Reihenfolge

1. **Backup.** Vor jeder Änderung an der Live-Seite Backup bzw. Staging bestätigen.
2. **Snippet.** Plugin „Code Snippets" → Neues Snippet, Typ PHP, Ausführung „Nur im Frontend ausführen".
   Inhalt von `bk-avd-rechner-snippet.php` einfügen. Bemängelt das Plugin das öffnende `<?php`, die erste Zeile weglassen.
   Nicht in die `functions.php` des Themes: Ein fehlerhaftes Snippet lässt sich im Backend abschalten, ein Fehler in der `functions.php` legt die Seite lahm.
3. **CSS.** Inhalt von `bk-avd-rechner-quickcss.css` ans Ende des Enfold Quick CSS anhängen.
   Den `:root`-Block am Anfang nur übernehmen, soweit die Variablen dort noch fehlen.
4. **Beitrag.** Im Layout Architekt in den Haupttext-Textblock in eine eigene Zeile `[bk_avd_rechner]` setzen,
   direkt nach dem Absatz unter „Ihr eigener Fall im Rechner". In `05-wordpress/haupttext.html` steht der Shortcode bereits dort.
5. **WP Rocket.** Wenn „JavaScript-Ausführung verzögern" aktiv ist, `bkAvd` in die Ausschlussliste aufnehmen.
   Sonst bleibt der Ergebnisbereich leer, bis der Besucher scrollt oder klickt.
6. **Cache leeren** und den Beitrag im Frontend prüfen.

## Prüfung nach dem Einbau

- Erscheint der Rechner mit Gold-Linie oben? Wenn nicht: im Entwicklertool prüfen, ob `section.bk-avd` im DOM steht (Snippet aktiv?) und ob die Regeln aus dem Quick CSS ankommen. Schnelltest: `.bk-avd { outline: 4px solid red; }` ins Quick CSS.
- Standardwerte (1.800 EUR, 0 Kinder, 90.000 EUR, einzeln, 25 Jahre, 30 %) müssen zeigen:
  Förderung 983 EUR, 42 %; Nettoaufwand 1.357 EUR; Kapital im mittleren Szenario 97.451; Unterschied +15.655.
- Eingabe 2500 im Feld Eigenbeitrag muss eine rote Fehlermeldung unter dem Feld zeigen.
- Mobil (360 px): Tabelle passt ohne Scrollen, die Seite scrollt nicht seitlich.

## Technische Hinweise

- Markup und JavaScript werden einzeilig ausgeliefert. Ein nachträglich laufendes `wpautop` kann deshalb keine `<p>`- oder `<br>`-Tags in das Skript setzen.
- Das Skript wird nur einmal je Seite ausgegeben, auch wenn der Shortcode mehrfach vorkommt; jede Instanz bekommt eigene IDs.
- Keine externen Requests, keine Cookies, keine Speicherung. Die Eingaben bleiben im Browser.
- `!important` steht nur an Eigenschaften, die Enfold bei Formularfeldern, Überschriften und Tabellen selbst setzt. Die Wirkung im Live-Theme ist nicht geprüft (kein Zugriff aus der Arbeitsumgebung).

## Pflege

Der Einkommensteuertarif steht in `quelle/rechner.js` in der Funktion `estGrundtarif` und in `rechenprobe.py` in `est_grundtarif_2026`.
Nach Verkündung des Tarifs 2027 beide Stellen ändern, `python3 rechenprobe.py` und den Browsertest erneut laufen lassen,
dann `python3 quelle/build.py` und das Snippet ersetzen.
