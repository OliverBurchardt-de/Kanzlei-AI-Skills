---
name: website-entwicklung
description: Website-Entwicklung nach den Standards von Burchardt & Kollegen – Best Practices (Barrierefreiheit/BFSG, DSGVO, Core Web Vitals, SEO/AI-Auffindbarkeit) plus Kanzlei-Design-System. IMMER verwenden, wenn Websites, Landing Pages, Web-Rechner, HTML/CSS/JS-Komponenten oder Web-Tools erstellt, geändert, geprüft oder geplant werden – auch bei Formulierungen wie "bau mir eine Seite", "Rechner für die Homepage", "pass das CSS an", "neue Unterseite", "Quick CSS", "Enfold", "Landingpage" oder "Website-Relaunch". Ebenfalls verwenden bei Reviews bestehender Seiten, bei Fragen zu Barrierefreiheit, Datenschutz oder Performance einer Website sowie bei jeder Arbeit an burchardt-kollegen.de. NICHT verwenden für reine Backend-Skripte, Datenanalysen oder Dokumente ohne Web-Bezug.
---

# Website-Entwicklung

Verhaltensregeln für alle Web-Arbeiten. Das Fachwissen liegt in den References – dieser Skill regelt das Vorgehen.

## Schritt 1: Einordnung (immer zuerst, vor jedem Code)

Drei Fragen beantworten – aus dem Kontext ableiten oder nachfragen:

1. **Track?**
   - **Track A – Statisch:** HTML/CSS/JS, Quellcode in GitHub, Deployment über Hosting. Neue Websites, Landing Pages, Rechner, Tools.
   - **Track B – Enfold:** burchardt-kollegen.de. Nur Child Theme, Quick CSS, Enfold-Elemente.
2. **Kanzlei-Marke?** Läuft das Projekt unter der Marke Burchardt & Kollegen? Nicht jedes Projekt tut das – neue Seiten können bewusst ohne Kanzlei-Branding laufen. Bei Unsicherheit fragen, nie stillschweigend das Kanzlei-Design anwenden.
3. **Live-Risiko?** Betrifft die Änderung eine produktive Seite? Dann vor Umsetzung Backup/Staging bestätigen lassen.

## Schritt 2: References lesen

- `references/best-practices.md` – **immer** lesen. Enthält die verbindlichen Standards: HTML/CSS/JS-Konventionen, Barrierefreiheit (BFSG/WCAG), Datenschutz (DSGVO/TDDDG), Performance-Budgets (Core Web Vitals), SEO/AI-Auffindbarkeit, Enfold-Regeln, GitHub-Workflow, Definition of Done.
- `references/enfold-inhalte.md` – **immer** lesen, wenn Beiträge oder Seiten auf burchardt-kollegen.de
  angelegt oder geändert werden. Enthält die verbindliche ALB-Struktur, die Pflicht-Meta, den Umgang mit
  Codeblock und FAQ, die Renderprüfung, die Bild- und Übertragungswege sowie die Backup-Konvention.
- `references/design-system.md` – lesen, **wenn** das Projekt unter der Kanzlei-Marke läuft. Enthält Farb-Tokens, Kontrast-Matrix, Typografie (Petrona/Aleo), Logo-Regeln, Verlaufsflächen, Komponenten-Konventionen.

Rangfolge bei Konflikten: design-system.md (Gestaltung) > best-practices.md > allgemeine Konventionen. Die rechtlichen Mindestanforderungen (Barrierefreiheit, Datenschutz) aus best-practices.md sind nie verhandelbar – auch nicht durch Design-Wünsche.

## Schritt 3: Arbeitsweise

- Annahmen vor der Umsetzung explizit benennen. Bei mehreren Interpretationen die Optionen nennen statt still zu entscheiden.
- Minimale Änderung: nur anfassen, was der Auftrag verlangt; bestehenden Stil (bk-Konventionen, vorhandenes Quick CSS) matchen.
- Kein spekulativer Code, keine ungebetenen Features, kein Framework ohne Rückfrage.
- Jeder CSS-Codeblock erhält Inline-Kommentare, die erklären, was jede Zeile/Eigenschaft tut.
- Neue Drittdienste (Fonts, Embeds, Tracking, CDNs) nie stillschweigend einbauen – immer als Entscheidung an Oliver zurückspielen (AVV- und Datenschutzerklärungs-Folgen).

## Schritt 4: Definition of Done

Vor jeder Auslieferung die Checkliste aus best-practices.md §11 durchlaufen und das Ergebnis **kurz berichten** (bestanden/nicht prüfbar/offen). Nicht prüfbare Punkte (z. B. Live-Performance) als solche kennzeichnen statt zu behaupten.

## Typische Aufträge → Vorgehen

| Auftrag | Vorgehen |
|---|---|
| Neuer Rechner / neue Landing Page | Track A. Marke klären → ggf. design-system.md → ein HTML-File mit lokalem CSS/JS, keine externen Requests → DoD |
| Änderung an burchardt-kollegen.de | Track B. Backup/Staging bestätigen lassen → Quick CSS/Code-Block nach bk-Konvention → DoD |
| Beitrag oder Seite auf burchardt-kollegen.de anlegen oder ändern | Track B. `enfold-inhalte.md` lesen → ausschließlich im Layout Architekt arbeiten, `post_content` und `_aviaLayoutBuilderCleanData` gemeinsam schreiben → Renderprüfung mit Codeblock-Extraktion → DoD |
| „Schau dir Seite X an" / Review | Beide References lesen → gegen DoD-Checkliste und Kontrast-Matrix prüfen → Befunde priorisiert berichten (rechtlich > funktional > kosmetisch) |
| Neue Website ohne Kanzlei-Branding | Track A ohne design-system.md → Gestaltung projektweise klären → best-practices.md gilt trotzdem vollständig |
