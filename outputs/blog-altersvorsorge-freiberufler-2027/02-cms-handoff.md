# CMS-Handoff: Altersvorsorge für Freiberufler ab 2027

Gehört nicht zum Artikeltext. Grundlage für die Veröffentlichung auf burchardt-kollegen.de.

## Meta-Daten (Redaktionsvorschläge, keine Rankinggarantie)

| Feld | Vorschlag |
|---|---|
| Titel (H1 aus dem CMS) | Altersvorsorge für Freiberufler ab 2027: Was das Altersvorsorgedepot wirklich bringt |
| Meta-Title (61 Zeichen) | Altersvorsorge für Freiberufler 2027: Zulage, Steuer, Rechner |
| Meta-Description (153 Zeichen) | Ab 2027 bekommen Ärzte, Anwälte und andere Selbständige erstmals die neue Altersvorsorge-Zulage. Wir rechnen vor, was sie nach Steuern wirklich wert ist. |
| Slug | `altersvorsorge-freiberufler-2027` |
| Kategorie | nach bestehender Blogstruktur (Vorschlag: Heilberufe / Steuertipps) |
| `toc_mode` | `cms` – Inhaltsverzeichnis über Table of Contents Plus (`[toc]`), im Artikel nichts eingefügt |

H1 und Meta-Daten behandeln dasselbe Hauptthema (Altersvorsorge Freiberufler 2027 / Altersvorsorgedepot).

## Beitragsbild

- Motividee: Schreibtisch nach Praxis- oder Kanzleischluss, aufgeschlagene Unterlagen, Taschenrechner, ein Becher Kaffee; keine lesbaren Dokumente, kein Sparschwein, keine Geldscheine.
- Format: 1600 × 900, WebP, Qualität 82.
- Alt-Text (Entwurf für das beschriebene Motiv, nach Bildauswahl anpassen): „Schreibtisch mit Unterlagen und Taschenrechner nach Feierabend in einer Arztpraxis"
- Bildunterschrift: keine nötig.
- `_avia_attachment_copyright` individuell setzen.

## Schaubild (erstellt)

- Dateien: `06-schaubild/schaubild-guenstigerpruefung-altersvorsorge.svg` (Quelle) und `.webp` (1760 × 1072, verlustfrei, 64 Farben, 42 KB).
- In WordPress: Attachment-ID 3352, im Beitrag als `av_image` mit `attachment_size='full'` eingebunden.
- Position: nach dem Absatz mit dem Beispiel des Architekten, also am Ende des Abschnitts „Warum die Zulage für Gutverdiener nur ein Rechenposten ist".
- Inhalt: Gegenüberstellung Zahnärztin (Steuerersparnis 983 EUR gewinnt gegen Zulagen 540 EUR, 42 %) und Architekt (Zulagen 750 EUR gewinnen gegen Steuerersparnis 442 EUR, 71 %). Die Tabelle im Text trägt die Herleitung, das Schaubild den Mechanismus.
- Alt-Text (gesetzt): „Schaubild zur Günstigerprüfung: Bei der Zahnärztin übersteigt die Steuerersparnis von 983 EUR die Zulagen von 540 EUR, beim Architekten liegen die Zulagen mit 750 EUR über der Steuerersparnis von 442 EUR. Der Staat trägt 42 beziehungsweise 71 Prozent der Einzahlung."
- Bildunterschrift (Vorschlag, nicht gesetzt, wie bei den übrigen Schaubildern): „Wer gut verdient und den vollen Beitrag zahlt, bekommt seinen Grenzsteuersatz. Kinder und kleine Beiträge drehen das Ergebnis zugunsten der Zulage."
- `_avia_attachment_copyright`: „Schaubild Günstigerprüfung Altersvorsorge 2027: Burchardt & Kollegen".
- Gerendert mit Gelasio (metrisch gleich zu Georgia), weil Georgia in der Arbeitsumgebung fehlt.

## Rechner

- Shortcode `[bk_avd_rechner]` steht in `05-wordpress/haupttext-2.html` in eigener Zeile direkt nach dem Absatz unter „Ihr eigener Fall im Rechner".
- Installation auf dem Server: siehe `04-rechner/einbau.md` (Sandbox-Datei, kein Quick CSS).

## Interne Links

| Ziel | Status | Position |
|---|---|---|
| [Zusatzbeitrag ins Versorgungswerk](https://www.burchardt-kollegen.de/zahlung-eines-zusatzbeitrags-in-das-versorgungswerk/) | im Artikel gesetzt; auf dem Server bestätigt (Post-ID 2014, veröffentlicht, Permalink identisch) | Abschnitt „Wo das Depot neben Versorgungswerk und Basisrente steht" |
| [Steuerberatung für Heilberufe](https://www.burchardt-kollegen.de/leistungen/heilberufe/steuerberatung/) | optional, nicht gesetzt | höchstens als einziger Leistungslink, etwa im Abschnitt „Alte Riester-Verträge vor dem Neuabschluss prüfen" – nur wenn redaktionell gewollt |

## Externe Links im Artikel

- Altersvorsorgereformgesetz, BGBl. 2026 I Nr. 156: https://www.recht.bund.de/bgbl/1/2026/156/VO.html
- § 22 EStG: https://www.gesetze-im-internet.de/estg/__22.html

Beide Links konnten aus der Arbeitsumgebung nicht abgerufen werden (Netzsperre). Vor Veröffentlichung einmal klicken.

## Stand in WordPress (04.10.2026)

| Punkt | Stand |
|---|---|
| Beitrag | Post-ID 3353, **Entwurf**, Slug `altersvorsorge-freiberufler-2027`, Kategorien Allgemein und Heilberufe |
| Bearbeiten | https://www.burchardt-kollegen.de/wp-admin/post.php?post=3353&action=edit |
| Vorschau | https://www.burchardt-kollegen.de/?p=3353&preview=true |
| Rank Math | Title, Description und Fokus-Keyword „Altersvorsorge Freiberufler 2027" gesetzt; robots index, follow |
| Beitragsbild | **fehlt noch** (Motiv siehe oben) |
| Aufbau | `av_section bk-intro > av_textblock` · `av_hr` · `av_textblock [toc]` · `av_hr` · `av_textblock` · `av_image` (Schaubild) · `av_textblock` (mit Rechner). Keine FAQ, kein Codeblock. Öffnungs-Tags aus Beitrag 3208 übernommen, `av_uid` eindeutig. |
| Pflicht-Meta | gesetzt; `post_content` und `_aviaLayoutBuilderCleanData` identisch; Shortcode-Baum neu erzeugt |

Vor dem Veröffentlichen: Beitragsbild setzen, Vorschau auf Desktop und Smartphone ansehen, Prüfpunkte im Freigabeprotokoll abhaken.

## Strukturierte Daten

Empfehlung `BlogPosting`, sofern Yoast/Rank Math nicht bereits ein Objekt ausgibt. Kein `FAQPage` (keine FAQ).

```json
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Altersvorsorge für Freiberufler ab 2027: Was das Altersvorsorgedepot wirklich bringt",
  "author": { "@type": "Person", "name": "Oliver Burchardt", "url": "[URL der Autorenseite]" },
  "publisher": { "@type": "Organization", "name": "Burchardt & Kollegen", "url": "https://www.burchardt-kollegen.de/" },
  "datePublished": "[Veröffentlichungsdatum]",
  "dateModified": "[nur bei inhaltlicher Änderung]",
  "image": "[URL Beitragsbild]",
  "mainEntityOfPage": "https://www.burchardt-kollegen.de/altersvorsorge-freiberufler-2027/"
}
```

## Wiedervorlage

- Nach Verkündung des Einkommensteuerreformgesetzes 2027: Tarif im Rechner und Beispielzahlen im Artikel aktualisieren, `dateModified` setzen.
- Nach einem Gesetzentwurf zur Rentenversicherungspflicht für Selbständige: Abschnitt „Rentenpflicht" aktualisieren.
