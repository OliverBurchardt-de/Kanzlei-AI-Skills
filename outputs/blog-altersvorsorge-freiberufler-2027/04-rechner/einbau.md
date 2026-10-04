# Einbau des Förderrechners auf burchardt-kollegen.de

## Stand der Installation (04.10.2026)

| Was | Wo | Prüfung |
|---|---|---|
| Rechner (Shortcode `[bk_avd_rechner]`, CSS und JavaScript) | `wp-content/novamira-sandbox/bk-avd-rechner.php` | SHA1 `5e384966cc0350d5f8c8df9541c7a43087f8a22d`, `php -l` auf dem Server ohne Fehler, Shortcode registriert, Startseite Status 200 |
| Beitrag (Entwurf) | Post-ID 3353, Slug `altersvorsorge-freiberufler-2027` | Vorschau gerendert: CSS im Head, Rechner, Schaubild, Inhaltsverzeichnis, keine Shortcode-Reste |

Novamira lädt PHP-Dateien aus `wp-content/novamira-sandbox/` automatisch. Ein Plugin „Code Snippets" gibt es auf dem Server nicht.

## Dateien im Repo

| Datei | Zweck |
|---|---|
| `bk-avd-rechner.php` | ausgelieferte Datei für den Sandbox-Ordner: Shortcode, Markup, JavaScript, CSS |
| `vorschau.html` | lokale Vorschau zum Ausprobieren (nicht hochladen) |
| `rechenprobe.py`, `rechenprobe.md` | Referenzrechnung und Rechenprobe mit elf Fällen |
| `quelle/` | bearbeitbare Quellen; `python3 quelle/build.py` erzeugt `bk-avd-rechner.php` und `vorschau.html` neu |

Änderungen immer in `quelle/` vornehmen und neu bauen, nie in den erzeugten Dateien.

## Warum kein Quick CSS

Das Kanzlei-CSS liegt im Customizer („Zusätzliches CSS", bk-lohn-Klassen), nicht im Enfold Quick CSS. Das aktive
Novamira-Design untersagt eine neue globale CSS-Schicht. Der Rechner lädt sein CSS deshalb nur auf Seiten, die den
Shortcode enthalten (`wp_add_inline_style` im Head), sonst nirgends.

## Aktualisieren

1. In `quelle/` ändern, `python3 quelle/build.py`, `python3 rechenprobe.py` und den Browsertest laufen lassen.
2. Committen und pushen (das Repo ist öffentlich).
3. Auf dem Server per `download_url()` von `raw.githubusercontent.com/.../<commit>/...` holen, SHA1 gegen die lokale Datei prüfen.
4. Alte Sandbox-Datei vorher als `.txt` mit Datum und Uhrzeit sichern, neue Datei mit `php -l` prüfen und erst dann ersetzen.
5. Ist der Beitrag veröffentlicht: WP-Rocket-Cache für die URL leeren.

## Prüfung im Frontend

- Standardwerte (1.800 EUR, 0 Kinder, 90.000 EUR, einzeln, 25 Jahre, 30 %) müssen zeigen:
  Förderung 983 EUR, 42 %; Nettoaufwand 1.357 EUR; Kapital im mittleren Szenario 97.451; Unterschied +15.655.
- Eingabe 2500 im Feld Eigenbeitrag muss eine Fehlermeldung unter dem Feld zeigen.
- Mobil (360 px): Tabelle passt ohne Scrollen, die Seite scrollt nicht seitlich.

## Technische Hinweise

- Markup und JavaScript werden einzeilig ausgeliefert, damit `wpautop` keine `<p>`- oder `<br>`-Tags in das Skript setzen kann.
- Das Skript trägt `nowprocket`. WP Rocket verzögert JavaScript derzeit ohnehin nicht (`delay_js` aus, Stand 04.10.2026).
- Das Skript wird nur einmal je Seite ausgegeben; jede Instanz bekommt eigene IDs.
- Keine externen Requests, keine Cookies, keine Speicherung. Die Eingaben bleiben im Browser.
- Die Sichtprüfung im Live-Theme (Schriften, Enfold-Formularstile) steht aus: Aus der Arbeitsumgebung ist die Website nicht direkt erreichbar.

## Pflege

Der Einkommensteuertarif steht in `quelle/rechner.js` (Funktion `estGrundtarif`) und in `rechenprobe.py`
(`est_grundtarif_2026`). Nach Verkündung des Tarifs 2027 beide Stellen ändern und wie oben beschrieben aktualisieren.
