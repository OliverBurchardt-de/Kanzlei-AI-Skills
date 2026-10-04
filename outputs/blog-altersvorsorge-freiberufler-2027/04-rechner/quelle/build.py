"""Erzeugt aus markup.html, rechner.js und rechner.css die Auslieferungsdateien.

- ../bk-avd-rechner-snippet.php  (Shortcode für das Code-Snippets-Plugin)
- ../bk-avd-rechner-quickcss.css (Block für das Enfold Quick CSS)
- ../vorschau.html               (eigenständige Vorschau zum Testen)

Markup und JavaScript werden auf eine Zeile gebracht, damit ein nachträglich
laufendes wpautop keine <p>- oder <br>-Tags hineinsetzen kann.
"""
import re
from pathlib import Path

HIER = Path(__file__).parent
ZIEL = HIER.parent


def markup_einzeilig(html: str) -> str:
    html = re.sub(r">\s+<", "><", html.strip())
    return re.sub(r"\s+", " ", html)


def js_einzeilig(js: str) -> str:
    zeilen = []
    for zeile in js.splitlines():
        z = zeile.strip()
        if not z or z.startswith("//"):
            continue
        if "//" in z and not re.search(r"['\"].*//.*['\"]", z):
            raise ValueError(f"Kommentar am Zeilenende nicht erlaubt: {z}")
        zeilen.append(z)
    return " ".join(zeilen)


markup = markup_einzeilig((HIER / "markup.html").read_text(encoding="utf-8"))
js = js_einzeilig((HIER / "rechner.js").read_text(encoding="utf-8"))
css = (HIER / "rechner.css").read_text(encoding="utf-8")
markup_vorschau = markup.replace("{{ID}}", "bk-avd-1")

for marke in ("BKAVDHTML", "BKAVDJS"):
    assert marke not in markup and marke not in js

php = f"""<?php
/**
 * Förderrechner Altersvorsorgevertrag 2027 für burchardt-kollegen.de
 *
 * Shortcode: [bk_avd_rechner]
 * Einbau:    Plugin "Code Snippets", Typ PHP, Ausführung "Nur im Frontend".
 *            Die erste Zeile (<?php) beim Einfügen weglassen, falls das Plugin sie bemängelt.
 * CSS:       liegt separat im Enfold Quick CSS (bk-avd-rechner-quickcss.css).
 * Rechtsstand: 04.10.2026. Erzeugt aus 04-rechner/quelle/ mit build.py, nicht von Hand ändern.
 */
if ( ! function_exists( 'bk_avd_rechner_shortcode' ) ) {{
	function bk_avd_rechner_shortcode() {{
		static $instanz = 0;
		$instanz++;
		$id     = 'bk-avd-' . $instanz;
		$markup = <<<'BKAVDHTML'
{markup}
BKAVDHTML;
		$markup = str_replace( '{{{{ID}}}}', $id, $markup );
		if ( 1 !== $instanz ) {{
			return $markup;
		}}
		$script = <<<'BKAVDJS'
<script>{js}</script>
BKAVDJS;
		return $markup . $script;
	}}
	add_shortcode( 'bk_avd_rechner', 'bk_avd_rechner_shortcode' );
}}
"""
(ZIEL / "bk-avd-rechner-snippet.php").write_text(php, encoding="utf-8")
(ZIEL / "bk-avd-rechner-quickcss.css").write_text(css, encoding="utf-8")

vorschau = f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vorschau Förderrechner Altersvorsorge 2027</title>
<meta name="robots" content="noindex">
<style>
body {{ margin: 0; background: #FFFFFF; color: #333333; font-family: Georgia, serif; }}
main {{ max-width: 840px; margin: 0 auto; padding: 24px 16px 64px; }}
h2 {{ color: #3A5791; font-size: 1.75rem; margin: 0 0 0.5em; }}
p {{ margin: 0 0 1em; }}
.vorschau-hinweis {{ font-size: 0.875rem; color: #4D4D4D; border-bottom: 1px solid #C9D3E6; padding-bottom: 12px; margin-bottom: 24px; }}
{css}
</style>
</head>
<body>
<main>
<p class="vorschau-hinweis">Lokale Vorschau des Rechners mit dem CSS aus dem Quick-CSS-Block. Schrift und Abstände der Website können abweichen.</p>
<h2>Ihr eigener Fall im Rechner</h2>
<p>Der Rechner wendet diese Mechanik auf Ihre Zahlen an. Er zeigt zuerst, wie hoch die Förderung bei Ihnen im Jahr ausfällt und ob die Zulage oder der Steuerabzug gewinnt. Darunter steht, was die Besteuerung im Alter davon wieder kostet und wie der Vertrag gegen ein freies Depot mit demselben Nettoaufwand abschneidet, jeweils in drei Renditeszenarien.</p>
{markup_vorschau}
<script>{js}</script>
</main>
</body>
</html>
"""
(ZIEL / "vorschau.html").write_text(vorschau, encoding="utf-8")
print("geschrieben:", [p.name for p in ZIEL.iterdir() if p.is_file()])
