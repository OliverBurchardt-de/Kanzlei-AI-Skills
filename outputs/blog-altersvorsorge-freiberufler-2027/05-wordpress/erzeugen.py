"""Erzeugt aus 01-artikel.md die HTML-Teile für die Enfold-Textblöcke.

einstieg.html        -> av_section (custom_class='bk-intro') > av_textblock
haupttext-1.html     -> av_textblock nach dem Inhaltsverzeichnis, bis zum Beispiel des Architekten
                        (danach folgt av_image mit dem Schaubild zur Günstigerprüfung)
haupttext-2.html     -> av_textblock nach dem Schaubild, enthält den Shortcode [bk_avd_rechner]
"""
from pathlib import Path
import markdown

HIER = Path(__file__).parent
md = (HIER.parent / "01-artikel.md").read_text(encoding="utf-8")

# Titelblock (H1 und Alternativen) entfällt: Der Titel kommt aus dem CMS.
koerper = md.split("\n---\n", 1)[1].strip()
einstieg, haupt = koerper.split("\n## ", 1)
haupt = "## " + haupt

trenner = "\n## Im Alter wird alles versteuert"
assert haupt.count(trenner) == 1
teil1, teil2 = haupt.split(trenner, 1)
teil2 = trenner.strip() + teil2

anker = "jeweils in drei Renditeszenarien."
assert teil2.count(anker) == 1
teil2 = teil2.replace(anker, anker + "\n\n[bk_avd_rechner]")


def html(text):
    return markdown.markdown(text, extensions=["tables"], output_format="html5")


for alt in ("haupttext.html",):
    if (HIER / alt).exists():
        (HIER / alt).unlink()

(HIER / "einstieg.html").write_text(html(einstieg.strip()) + "\n", encoding="utf-8")
(HIER / "haupttext-1.html").write_text(html(teil1.strip()) + "\n", encoding="utf-8")
t2 = html(teil2).replace("<p>[bk_avd_rechner]</p>", "[bk_avd_rechner]")
(HIER / "haupttext-2.html").write_text(t2 + "\n", encoding="utf-8")
gesamt = html(teil1) + t2
print("H2:", gesamt.count("<h2>"), "| Tabellen:", gesamt.count("<table>"), "| Shortcode:", gesamt.count("[bk_avd_rechner]"))
