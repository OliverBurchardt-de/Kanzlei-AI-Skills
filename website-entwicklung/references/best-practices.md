# Web-Entwicklung – Best Practices (Referenz für Claude)

> Verbindliche Referenz für alle Website-Arbeiten von Burchardt & Kollegen.
> Zielgruppe: Claude (LLM). Stil: kompakt, imperativ, keine Erklärprosa.
> Stand: 2026-07. Rechtliche Aussagen sind Arbeitsstand, keine Rechtsberatung.

## 0. Geltungsbereich & Rangfolge

Zwei Tracks:

- **Track A – Statische Projekte:** HTML/CSS/JS, Quellcode in GitHub, Deployment über Hosting (z. B. GitHub Pages, Netlify o. Ä.). Gilt für neue Websites, Landing Pages, Rechner, Tools.
- **Track B – WordPress/Enfold:** burchardt-kollegen.de. Änderungen über Child Theme, Quick CSS und Enfold-Elemente. Abschnitt 9 beachten.

Rangfolge bei Konflikten: `design-system.md` (Gestaltung) > dieses File > allgemeine Konventionen. Rechtliche Mindestanforderungen (Abschnitte 5–6) sind nie verhandelbar, auch nicht durch Design-Vorgaben.

## 1. Arbeitsweise

- Annahmen vor der Umsetzung explizit benennen; bei mehreren Interpretationen nachfragen statt still entscheiden.
- Minimale Änderung: nur anfassen, was der Auftrag verlangt. Bestehenden Stil matchen.
- Kein spekulativer Code, keine ungebetene Konfigurierbarkeit.
- Jede Auslieferung endet mit der Definition-of-Done-Prüfung (Abschnitt 11).

## 2. HTML

- Semantische Elemente zuerst: `header`, `nav`, `main` (genau eines), `section`, `article`, `footer`, `button`, `details/summary`. Kein `div`/`span`, wo ein natives Element existiert.
- Erste ARIA-Regel: kein ARIA verwenden, wenn ein natives Element dasselbe leistet.
- Genau ein `h1` pro Seite; Überschriften-Hierarchie ohne Sprünge (h2 → h3, nie h2 → h4).
- `<html lang="de">`; fremdsprachige Passagen mit `lang`-Attribut auszeichnen.
- Links navigieren, Buttons lösen Aktionen aus – nie vertauschen.
- Bilder: immer `width`/`height`-Attribute (verhindert CLS), aussagekräftiger `alt`-Text; dekorative Bilder `alt=""`.
- Formulare: jedes Feld mit `<label>` (Placeholder ersetzt kein Label), Pflichtfelder mit `*` und `aria-required`, `autocomplete`-Attribute (`name`, `email`, `tel`), Fehlermeldungen konkret und direkt am Feld, Erfolgsmeldung visuell und für Screenreader.

## 3. CSS

- Design-Tokens ausschließlich als Custom Properties; einzige Quelle ist `design-system.md`. Keine hartcodierten Farben/Abstände in Komponenten.
- Mobile-first: Basis-Styles für schmale Viewports, `min-width`-Media-Queries nach oben.
- Fluide Typografie mit `clamp()`; Fließtext ≥ 16 px.
- `prefers-reduced-motion` respektieren: Animationen/Transitions dahinter abschalten.
- Fokus-Stile nie entfernen; `:focus-visible` gestalten (sichtbar, ≥ 3:1 Kontrast zum Umfeld).
- Kein `!important` – einzige Ausnahme: gezielte Enfold-Overrides in Quick CSS (Abschnitt 9).

```css
:root {
  --bk-gold: #F7B234;              /* Primärfarbe der Kanzlei (Gold) – nur über Token verwenden */
  --space-m: clamp(1rem, 2vw, 1.5rem); /* fluider Standardabstand: min 16px, skaliert mit Viewport, max 24px */
}
@media (prefers-reduced-motion: reduce) { /* greift, wenn Nutzer im OS reduzierte Bewegung eingestellt hat */
  * { animation: none; transition: none; } /* schaltet alle Animationen und Übergänge ab */
}
```

## 4. JavaScript

- Progressive Enhancement: Kerninhalt und Kernfunktion müssen ohne JS erreichbar sein (Formular-Fallbacks, kein JS-only-Rendering von Inhalten).
- Vanilla JS zuerst; Framework nur bei echtem Bedarf und nach Rückfrage.
- Skripte mit `defer` laden; keine synchronen Third-Party-Skripte im `head`.
- INP-Disziplin: keine Tasks > 50 ms auf dem Main Thread; teure Arbeit stückeln oder nach der Interaktion ausführen; DOM-Reads und -Writes nicht mischen.
- Keine Layout-Verschiebungen durch nachträglich eingefügte Elemente – Platz reservieren.

## 5. Barrierefreiheit (BFSG / WCAG)

**Rechtsrahmen:** BFSG gilt seit 28.06.2025, auch für Bestands-Websites. Betroffen sind verbraucherorientierte Angebote mit Interaktion (Kontaktformular, Terminbuchung, Downloads) – trifft auf die Kanzlei-Website zu. Prüfmaßstab: EN 301 549 → WCAG 2.1 AA als Pflicht, WCAG 2.2 AA als Zielniveau. Durchsetzung läuft (Bußgelder bis 100.000 €, Verbandsklagen). Barrierefreiheitserklärung im Footer vorhalten.

**Umsetzung – immer:**
- Kontrast: Text ≥ 4,5:1; großer Text und UI-Komponenten ≥ 3:1. Gold `#F7B234` auf Weiß besteht das NICHT für Text – nur für Flächen/Deko oder mit dunkler Schrift darauf.
- Vollständige Tastaturbedienbarkeit; logische Fokus-Reihenfolge; Fokus nie verdeckt; Skip-Link zum Hauptinhalt.
- Touch-/Klickziele ≥ 24 × 24 px (WCAG 2.2).
- Information nie nur über Farbe transportieren (Links zusätzlich unterstreichen, Pflichtfelder zusätzlich mit `*`).
- Kein autostartendes Audio/Video; Videos mit Untertiteln.
- Abkürzungen beim ersten Auftreten ausschreiben.
- **Keine Accessibility-Overlays/Widgets** – Barrierefreiheit wird im Code gelöst.

**Testen:** axe/Lighthouse/WAVE als Erstcheck, dann manuell: komplette Seite nur mit Tastatur bedienen, Stichprobe mit Screenreader. Automatisierte Tools finden nur 30–40 % der Probleme.

## 6. Datenschutz (DSGVO / TDDDG)

**Grundprinzip: Zero-Third-Party-Default.** Beim Seitenaufruf darf ohne Einwilligung kein Request an Dritte gehen (§ 25 Abs. 1 TDDDG + Art. 6 DSGVO).

- Fonts immer lokal hosten (woff2 auf eigenem Server). Nie `fonts.googleapis.com`/`fonts.gstatic.com` einbinden – etablierte Abmahnpraxis seit LG München 2022; EuGH-Klärung läuft, Risiko bleibt.
- Keine externen CDNs für CSS/JS-Libraries; Assets ins eigene Repo/Hosting.
- Einbettungen (YouTube, Maps, Jotform, Social) nur per Zwei-Klick-Lösung oder consent-gated: vor Einwilligung Platzhalter, keine Verbindung. YouTube zusätzlich `youtube-nocookie.com`.
- Tracking/Analytics nur nach aktiver Einwilligung über CMP; Ablehnen muss genauso einfach sein wie Akzeptieren; Kategorien einzeln wählbar. Datenschutzfreundliche Alternative (z. B. Matomo, cookielos) bevorzugen.
- Formulare: nur über HTTPS, Datenminimierung (nur nötige Felder), Datenschutzhinweis mit Zweck direkt am Formular.
- Bei jedem neuen Drittdienst: AVV klären und Datenschutzerklärung ergänzen (an Oliver melden, nicht stillschweigend einbauen).

## 7. Performance (Core Web Vitals)

**Ziele (Google, p75):** LCP < 2,5 s · INP < 200 ms · CLS < 0,1.
**Interne Budgets (80 %):** LCP < 2,0 s · INP < 160 ms · CLS < 0,08.

- Bilder: AVIF/WebP mit Fallback, responsive über `srcset`/`sizes`, `loading="lazy"` für alles unterhalb des Folds – NIE für das LCP-Element. LCP-Bild: `fetchpriority="high"` + `<link rel="preload">`.
- Fonts: woff2, subsetted, `font-display: swap`, kritische Schnitte preloaden. Maximal 2 Familien / 4 Schnitte.
- CSS: kritisches CSS klein halten; ungenutztes CSS entfernen.
- JS: `defer`, Third-Party minimieren – jedes externe Skript braucht eine Begründung.
- CLS: Dimensionen für Bilder/Videos/Iframes/Embeds immer reservieren; keine Inhalte über bestehendem Content einschieben.
- Messen: Lighthouse (Lab) als Entwicklungscheck, PageSpeed Insights/CrUX (Field) als Wahrheit; CrUX-Fenster = 28 Tage.

## 8. SEO & AI-Auffindbarkeit

- Pro Seite: einzigartiger `<title>` (≤ 60 Zeichen, Keyword vorn), Meta-Description (≤ 155 Zeichen), sprechende URL, `canonical`.
- `sitemap.xml` und `robots.txt` pflegen. AI-Crawler (GPTBot, ClaudeBot, PerplexityBot) NICHT blockieren – AI-Antworten sind ein Akquisekanal.
- Strukturierte Daten als JSON-LD: `AccountingService`/`LocalBusiness` (NAP exakt konsistent mit Google Business Profile), `FAQPage` für FAQ-Blöcke, `Article` mit Autor bei Fachbeiträgen.
- Answer-first-Struktur: Kernaussage in den ersten Sätzen, klare H2/H3-Gliederung, FAQ-Block mit Fragen als Überschriften – LLMs zitieren extrahierbare, klar strukturierte Abschnitte.
- E-E-A-T: Fachbeiträge mit benanntem Autor und Qualifikation (WP/StB, Fachberater) ausweisen; „Stand: [Datum]" bei Aktualisierungen.
- Keine Keyword-Dichte-Optimierung; Klarheit und Tiefe schlagen Wiederholung.

## 9. Enfold-spezifisch (Track B)

- Änderungen nur über Child Theme oder Quick CSS; nie Parent-Theme-Dateien anfassen.
- Quick CSS: gemeinsame Token-Ebene (`:root`-Custom-Properties) an den Anfang; Komponenten-CSS nach bk-Namenskonvention (`bk-*`); `!important` nur, wo Enfold-Inline-Styles es erzwingen – dann mit Kommentar warum.
- Enfold-Einstellungen: Google Fonts deaktivieren bzw. lokal laden, Performance-Optionen (CSS/JS-Merging) aktiv, ungenutzte Elemente deaktivieren.
- Eigene HTML-Blöcke über Code-Block-Element; JS darin `defer`/am Ende.
- Plugin-Disziplin: jedes neue Plugin ist ein Performance- und Sicherheitsrisiko – vor Installation Alternativen ohne Plugin prüfen.
- Vor Änderungen an Live-Seiten: Staging oder mindestens Backup bestätigen lassen.
- Inhalte (Beiträge, Seiten) werden ausschließlich im Enfold Layout Architekt bearbeitet, nie im Standard-Editor. Vorgehen, Pflicht-Meta und Prüfschritte stehen in `enfold-inhalte.md`.

## 10. GitHub-Workflow (Track A)

- Ein Repo pro Projekt; `README.md` mit Zweck, Deployment-Weg und lokalem Startbefehl.
- Struktur: `/index.html`, `/assets/css`, `/assets/js`, `/assets/img`, `/assets/fonts` – Fonts und Libraries liegen im Repo, nicht auf CDNs (siehe Abschnitt 6).
- Keine Secrets/Keys im Repo; keine Mandanten- oder personenbezogenen Daten, auch nicht in Beispieldaten.
- Commits klein und benannt nach Wirkung („Kontrast Footer-Links auf AA angehoben"), nicht nach Datei.
- Vor Merge/Deploy: Definition of Done (Abschnitt 11) durchlaufen.

## 11. Definition of Done

Vor jeder Auslieferung prüfen und Ergebnis kurz berichten:

1. HTML valide, semantisch, eine h1, Hierarchie ohne Sprünge.
2. Nur Tastatur: alles erreichbar, Fokus sichtbar, Skip-Link funktioniert.
3. Kontraste AA erfüllt (Stichprobe mit Kontrast-Check).
4. Kein Third-Party-Request vor Einwilligung (Netzwerk-Tab bei kaltem Aufruf).
5. Lighthouse: Performance ≥ 90 mobil angestrebt; LCP/CLS-Budgets eingehalten; keine Bilder ohne Dimensionen.
6. Title, Description, JSON-LD vorhanden und valide.
7. Responsive geprüft: 360 px, 768 px, 1280 px.
8. Track B zusätzlich: nur Child Theme/Quick CSS geändert, Backup/Staging bestätigt.
