# Kanzlei-AI-Skills

Dieses Repo enthält alle Skills in den jeweils gültigen Fassungen, die wir für
die Kanzlei entwickelt haben. **Das Repo ist die maßgebliche Quelle.** Weicht
eine installierte Fassung ab, gilt die hier.

## Bestand

| Ordner | Skill | Zweck |
|---|---|---|
| `abschluss-review/` | `abschluss-review` | Review von Jahresabschlüssen und EÜR |
| `bescheid-review/` | `bescheid-review` | Review von Steuerbescheiden gegen die eigene Berechnung |
| `Blogartikel/` | `bk-blogartikel` | Blogartikel und Fachbeiträge |
| `bk-datev-export/` | `bk-datev-export` | DATEV-EXTF-Stapel und Belegtransfer |
| `bk-gesellschafterbeschluss/` | `bk-gesellschafterbeschluss` | Gesellschafterbeschlüsse |
| `bk-humanizer/` | `bk-humanizer` | Entschwurbeln und Schreibstimme treffen |
| `bk-jahresabschluss-vorbereitung/` | `bk-jahresabschluss-vorbereitung` | Vorbereitung des Jahresabschlusses |
| `bk-monatsbuchhaltung/` | `bk-monatsbuchhaltung` | Belegbuchhaltung aus hochgeladenen Belegen |
| `bk-monatsreview/` | `bk-monatsreview` | Monatsreview mit Arbeitspapier |
| `bk-senior-steuerreview/` | `bk-senior-steuerreview` | Kritischer Zweitblick auf steuerliche Entwürfe |
| `mt940-dateien-erstellen/` | `mt940-dateien-erstellen` | MT940-Dateien erzeugen |
| `Skill für Schaubilder/` | `bk-schaubilder` | Schaubilder im Kanzleidesign |
| `website-entwicklung/` | `website-entwicklung` | Websites und Web-Rechner |

Neue Ordner heißen wie das `name`-Feld des Skills. `Blogartikel/` und
`Skill für Schaubilder/` folgen dieser Regel noch nicht; das ist historisch und
wird beim nächsten Anfassen korrigiert.

## Zusammenhänge zwischen den Skills

`bk-humanizer` führt Schreibstimme und KI-Muster für alle Textarten an einer
Stelle. `bk-blogartikel` verweist darauf und behält nur das Blogspezifische:
Artikeltypen, Evidenzprotokoll, Aufbau, Schaubilder, Rechner, CMS-Handoff,
Veröffentlichungssperren. Dieselben Regeln stehen bewusst nicht zweimal im Repo,
weil eine Nachtragung in nur eine von zwei Dateien zu unterschiedlichen
Ergebnissen führt, ohne dass die Ursache sichtbar wird.

## Kein Mandantenbezug

Skills enthalten keine Mandantendaten, keine Zugangsdaten und keine
Steuernummern, auch nicht in Beispielen. Beispiele arbeiten mit erfundenen
Zahlen und Namen. Das Repo ist öffentlich.
