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

## Optionales Schaubild

Nicht erstellt. Lohnt sich, weil die Günstigerprüfung der Kern des Artikels ist und sich als Rechenweg gut zeigen lässt (Skill `bk-schaubilder`).

- Inhalt: Eigenbeitrag 1.800 EUR + Grundzulage 540 EUR = Einzahlung 2.340 EUR; Steuerentlastung 983 EUR = 540 EUR Zulage + 443 EUR Erstattung; Nettoaufwand 1.357 EUR.
- Position: nach der Tabelle im Abschnitt „Warum die Zulage für Gutverdiener nur ein Rechenposten ist".
- Alt-Text-Entwurf: „Rechenweg der Günstigerprüfung: Von 2.340 EUR Einzahlung trägt die Zahnärztin 1.357 EUR selbst, 983 EUR trägt der Staat über Zulage und Steuererstattung."

## Rechner

- Shortcode `[bk_avd_rechner]` steht in `05-wordpress/haupttext.html` bereits an der richtigen Stelle: in eigener Zeile direkt nach dem Absatz unter „Ihr eigener Fall im Rechner".
- Einbau von Snippet und Quick CSS: siehe `04-rechner/einbau.md`.

## Interne Links

| Ziel | Status | Position |
|---|---|---|
| [Zusatzbeitrag ins Versorgungswerk](https://www.burchardt-kollegen.de/zahlung-eines-zusatzbeitrags-in-das-versorgungswerk/) | im Artikel gesetzt; per Websuche am 04.10.2026 im Index gefunden, Seite selbst nicht abgerufen. Vor Veröffentlichung einmal aufrufen. | Abschnitt „Wo das Depot neben Versorgungswerk und Basisrente steht" |
| [Steuerberatung für Heilberufe](https://www.burchardt-kollegen.de/leistungen/heilberufe/steuerberatung/) | optional, nicht gesetzt | höchstens als einziger Leistungslink, etwa im Abschnitt „Alte Riester-Verträge vor dem Neuabschluss prüfen" – nur wenn redaktionell gewollt |

## Externe Links im Artikel

- Altersvorsorgereformgesetz, BGBl. 2026 I Nr. 156: https://www.recht.bund.de/bgbl/1/2026/156/VO.html
- § 22 EStG: https://www.gesetze-im-internet.de/estg/__22.html

Beide Links konnten aus der Arbeitsumgebung nicht abgerufen werden (Netzsperre). Vor Veröffentlichung einmal klicken.

## Aufbau im Layout Architekt (nach `enfold-inhalte.md`)

```
av_section (custom_class='bk-intro') > av_textblock   ← 05-wordpress/einstieg.html
av_hr
av_textblock mit [toc]
av_hr
av_textblock                                          ← 05-wordpress/haupttext.html (enthält [bk_avd_rechner])
```

Keine FAQ, daher kein `av_codeblock`. Öffnungs-Tags aus einem aktuellen Referenzbeitrag übernehmen, nur `av_uid` ersetzen.
Pflicht-Meta setzen (`_aviaLayoutBuilder_active`, `_aviaLayoutBuilderCleanData` identisch zu `post_content`,
`_av_el_mgr_version`, `_avia_sc_parser_state`, `header_title_bar = hidden_title_bar`), Shortcode-Baum neu erzeugen,
Backup-Meta mit Datum und Uhrzeit, danach WP-Rocket-Cache leeren.

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
