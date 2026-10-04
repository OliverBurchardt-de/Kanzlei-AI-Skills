# Blogartikel „Altersvorsorge für Freiberufler ab 2027" mit Förderrechner

Erstellt am 04.10.2026 mit dem Skill `bk-blogartikel` aus dem Recherchebriefing vom 03.10.2026.
Status: **redaktionell prüfbar** (keine Veröffentlichungssperre offen, fachliche Freigabe steht aus).

**Nicht veröffentlicht.** Der Novamira-Connector war in der Arbeitssitzung nicht autorisiert. Alles liegt fertig zum Einbau bereit.

| Datei | Inhalt |
|---|---|
| `01-artikel.md` | Block 1: Publikationsinhalt (H1, Alternativtitel, Artikel) |
| `02-cms-handoff.md` | Block 2: Meta-Daten, Slug, Bilder, Links, Aufbau im Layout Architekt, JSON-LD |
| `03-freigabeprotokoll.md` | Block 3: internes Freigabeprotokoll mit Evidenztabelle und Prüfpunkten – nicht veröffentlichen |
| `04-rechner/` | Förderrechner: Shortcode-Snippet, Quick CSS, Vorschau, Rechenprobe, Einbauanleitung |
| `05-wordpress/` | HTML-Teile für die Enfold-Textblöcke (`einstieg.html`, `haupttext.html` mit `[bk_avd_rechner]`) |

## Vor der Veröffentlichung

1. Prüfpunkte 1 bis 4 im Freigabeprotokoll abarbeiten.
2. Snippet und Quick CSS nach `04-rechner/einbau.md` einbauen.
3. Beitrag im Layout Architekt nach `02-cms-handoff.md` anlegen, Beitragsbild setzen.

## Neu erzeugen nach Änderungen

```bash
python3 05-wordpress/erzeugen.py      # HTML-Teile aus 01-artikel.md (benötigt: pip install markdown)
python3 04-rechner/quelle/build.py    # Snippet, Quick CSS und Vorschau aus 04-rechner/quelle/
python3 04-rechner/rechenprobe.py     # Referenzrechnung
```
