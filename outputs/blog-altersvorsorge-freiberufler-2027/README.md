# Blogartikel „Altersvorsorge für Freiberufler ab 2027" mit Förderrechner

Erstellt am 04.10.2026 mit dem Skill `bk-blogartikel` aus dem Recherchebriefing vom 03.10.2026.
Status: **redaktionell prüfbar** (keine Veröffentlichungssperre offen, fachliche Freigabe steht aus).

**In WordPress als Entwurf angelegt** (Post-ID 3353, nicht veröffentlicht). Der Rechner ist als Sandbox-Datei installiert, das Schaubild liegt in der Mediathek (ID 3352). Es fehlen das Beitragsbild und die fachliche Freigabe.

| Datei | Inhalt |
|---|---|
| `01-artikel.md` | Block 1: Publikationsinhalt (H1, Alternativtitel, Artikel) |
| `02-cms-handoff.md` | Block 2: Meta-Daten, Slug, Bilder, Links, Aufbau im Layout Architekt, JSON-LD |
| `03-freigabeprotokoll.md` | Block 3: internes Freigabeprotokoll mit Evidenztabelle und Prüfpunkten – nicht veröffentlichen |
| `04-rechner/` | Förderrechner: Sandbox-PHP-Datei, Vorschau, Rechenprobe, Einbauanleitung |
| `05-wordpress/` | HTML-Teile für die Enfold-Textblöcke (`einstieg.html`, `haupttext-1.html`, `haupttext-2.html` mit `[bk_avd_rechner]`) |
| `06-schaubild/` | Schaubild zur Günstigerprüfung (SVG-Quelle und WebP) |

## Vor der Veröffentlichung

1. Prüfpunkte 1 bis 4 im Freigabeprotokoll abarbeiten.
2. Beitragsbild setzen und die Vorschau auf Desktop und Smartphone ansehen.
3. Beitrag veröffentlichen.

## Wiedervorlage

Eine wöchentliche Routine prüft, ob das Einkommensteuerreformgesetz 2027 verkündet ist. Danach erstellt sie Artikel,
Rechner und Schaubild mit dem endgültigen Tarif neu und überträgt sie über Novamira in Beitrag 3353.

## Neu erzeugen nach Änderungen

```bash
python3 05-wordpress/erzeugen.py      # HTML-Teile aus 01-artikel.md (benötigt: pip install markdown)
python3 04-rechner/quelle/build.py    # Sandbox-PHP und Vorschau aus 04-rechner/quelle/
python3 04-rechner/rechenprobe.py     # Referenzrechnung
```
