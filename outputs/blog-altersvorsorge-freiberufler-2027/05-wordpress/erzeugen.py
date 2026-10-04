"""Erzeugt aus 01-artikel.md die HTML-Teile für die Enfold-Textblöcke.

einstieg.html  -> av_section (custom_class='bk-intro') > av_textblock
haupttext.html -> av_textblock nach dem Inhaltsverzeichnis, mit Shortcode [bk_avd_rechner]
"""
from pathlib import Path
import markdown

HIER = Path(__file__).parent
md = (HIER.parent / "01-artikel.md").read_text(encoding="utf-8")

# Titelblock (H1 und Alternativen) entfällt: Der Titel kommt aus dem CMS.
koerper = md.split("\n---\n", 1)[1].strip()
einstieg, haupt = koerper.split("\n## ", 1)
haupt = "## " + haupt

anker = "jeweils in drei Renditeszenarien."
assert haupt.count(anker) == 1
haupt = haupt.replace(anker, anker + "\n\n[bk_avd_rechner]")

def html(text):
    return markdown.markdown(text, extensions=["tables"], output_format="html5")

(HIER / "einstieg.html").write_text(html(einstieg.strip()) + "\n", encoding="utf-8")
haupt_html = html(haupt).replace("<p>[bk_avd_rechner]</p>", "[bk_avd_rechner]")
(HIER / "haupttext.html").write_text(haupt_html + "\n", encoding="utf-8")
print("einstieg:", len(einstieg.split()), "Wörter | haupttext:", len(haupt.split()), "Wörter")
print("H2:", haupt_html.count("<h2>"), "| Tabellen:", haupt_html.count("<table>"), "| Shortcode:", haupt_html.count("[bk_avd_rechner]"))
