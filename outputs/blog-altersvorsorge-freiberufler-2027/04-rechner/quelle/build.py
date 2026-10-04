"""Erzeugt aus markup.html, rechner.js und rechner.css die Auslieferungsdateien.

- ../bk-avd-rechner.php  Datei für wp-content/novamira-sandbox/ auf burchardt-kollegen.de:
                         registriert den Shortcode [bk_avd_rechner] und lädt das CSS
                         nur auf Seiten, die den Rechner enthalten (keine globale CSS-Schicht)
- ../vorschau.html       eigenständige Vorschau zum Testen

Markup und JavaScript werden auf eine Zeile gebracht, damit ein nachträglich
laufendes wpautop keine <p>- oder <br>-Tags hineinsetzen kann. Das CSS wird für
die Auslieferung von Kommentaren befreit; die kommentierte Fassung bleibt rechner.css.
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


def css_minimal(css: str) -> str:
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};:,>])\s*", r"\1", css)
    css = css.replace(";}", "}")
    # Leerzeichen in Media-Queries und vor !important wiederherstellen
    css = css.replace("and(", "and (").replace("!important", " !important").replace("  !important", " !important")
    return css.strip()


markup = markup_einzeilig((HIER / "markup.html").read_text(encoding="utf-8"))
js = js_einzeilig((HIER / "rechner.js").read_text(encoding="utf-8"))
css = (HIER / "rechner.css").read_text(encoding="utf-8")
css_min = css_minimal(css)
markup_vorschau = markup.replace("{{ID}}", "bk-avd-1")

for marke in ("BKAVDHTML", "BKAVDJS", "BKAVDCSS"):
    assert marke not in markup and marke not in js and marke not in css_min

php = f"""<?php
/**
 * Förderrechner Altersvorsorgevertrag 2027 für burchardt-kollegen.de
 *
 * Shortcode:  [bk_avd_rechner]
 * Ablage:     wp-content/novamira-sandbox/bk-avd-rechner.php
 * CSS:        wird nur auf Seiten mit dem Shortcode geladen, keine globale CSS-Schicht.
 * WP Rocket:  das Skript trägt das Attribut nowprocket und wird nicht verzögert.
 * Rechtsstand: 04.10.2026, Einkommensteuertarif 2026.
 * Erzeugt aus outputs/blog-altersvorsorge-freiberufler-2027/04-rechner/quelle/ mit build.py,
 * nicht von Hand ändern.
 */
if ( ! defined( 'ABSPATH' ) ) {{
	return;
}}

if ( ! function_exists( 'bk_avd_rechner_css' ) ) {{
	function bk_avd_rechner_css() {{
		static $geladen = false;
		if ( $geladen ) {{
			return;
		}}
		$geladen = true;
		$css     = <<<'BKAVDCSS'
{css_min}
BKAVDCSS;
		wp_register_style( 'bk-avd-rechner', false, array(), '2026-10-04' );
		wp_enqueue_style( 'bk-avd-rechner' );
		wp_add_inline_style( 'bk-avd-rechner', $css );
	}}

	add_action(
		'wp_enqueue_scripts',
		function () {{
			if ( ! is_singular() ) {{
				return;
			}}
			$post = get_post();
			if ( $post && has_shortcode( $post->post_content, 'bk_avd_rechner' ) ) {{
				bk_avd_rechner_css();
			}}
		}}
	);
}}

if ( ! function_exists( 'bk_avd_rechner_shortcode' ) ) {{
	function bk_avd_rechner_shortcode() {{
		static $instanz = 0;
		$instanz++;
		bk_avd_rechner_css();
		$id     = 'bk-avd-' . $instanz;
		$markup = <<<'BKAVDHTML'
{markup}
BKAVDHTML;
		$markup = str_replace( '{{{{ID}}}}', $id, $markup );
		if ( 1 !== $instanz ) {{
			return $markup;
		}}
		$script = <<<'BKAVDJS'
<script nowprocket>{js}</script>
BKAVDJS;
		return $markup . $script;
	}}
	add_shortcode( 'bk_avd_rechner', 'bk_avd_rechner_shortcode' );
}}
"""
(ZIEL / "bk-avd-rechner.php").write_text(php, encoding="utf-8")
alt = ZIEL / "bk-avd-rechner-snippet.php"
if alt.exists():
    alt.unlink()
alt_css = ZIEL / "bk-avd-rechner-quickcss.css"
if alt_css.exists():
    alt_css.unlink()

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
{css_min}
</style>
</head>
<body>
<main>
<p class="vorschau-hinweis">Lokale Vorschau des Rechners mit dem ausgelieferten CSS. Schrift und Abstände der Website können abweichen.</p>
<h2>Ihr eigener Fall im Rechner</h2>
<p>Der Rechner wendet diese Mechanik auf Ihre Zahlen an. Er zeigt zuerst, wie hoch die Förderung bei Ihnen im Jahr ausfällt und ob die Zulage oder der Steuerabzug gewinnt. Darunter steht, was die Besteuerung im Alter davon wieder kostet und wie der Vertrag gegen ein freies Depot mit demselben Nettoaufwand abschneidet, jeweils in drei Renditeszenarien.</p>
{markup_vorschau}
<script>{js}</script>
</main>
</body>
</html>
"""
(ZIEL / "vorschau.html").write_text(vorschau, encoding="utf-8")
print("geschrieben:", sorted(p.name for p in ZIEL.iterdir() if p.is_file()), "| CSS minimiert:", len(css_min), "Zeichen")
