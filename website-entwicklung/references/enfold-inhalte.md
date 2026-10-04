# Inhalte auf burchardt-kollegen.de (Enfold ALB über den Novamira-Connector)

Diese Referenz regelt das Anlegen und Ändern von Beiträgen und Seiten. Gestaltung,
Quick CSS und Theme-Disziplin stehen in `best-practices.md` Abschnitt 9.

## Zugriffswege

Der Cloud-Container hat **keine** Netzverbindung zur Website. `novamira/create-upload-link`,
curl und wget scheitern am Proxy mit „CONNECT tunnel failed, 403". Dateien gehen
ausschließlich über `novamira/write-file` oder `novamira/execute-php` hinüber.

Der WordPress-Server selbst hat Internetzugang und kann Dateien eigenständig holen
(`download_url()`, `media_sideload_image()`). Bei externen Quellen ist das der kürzere Weg.

## Layout Architekt ist Pflicht

Beiträge und Seiten werden **immer** im Advanced Layout Builder angelegt und bearbeitet,
nie im Standard-Editor — auch nicht für eine einzelne Zeile. Reiner HTML-Inhalt in
`post_content` sieht im Backend unauffällig aus; im Frontend floatet dann das
Inhaltsverzeichnis von Table of Contents Plus in den Fließtext und die erste Überschrift
läuft daneben.

Standardaufbau eines Blogbeitrags:

    av_section (custom_class='bk-intro') > av_textblock   ← Einstieg, zwei bis vier Absätze
    av_hr
    av_textblock mit [toc]
    av_hr
    av_textblock                                          ← Haupttext mit H2 und H3
    av_image (optional, attachment_size='full')
    av_textblock                                          ← Resttext nach dem Schaubild
    av_hr
    av_codeblock                                          ← FAQ als <section class="bk-faq">

Pflicht-Meta:

    _aviaLayoutBuilder_active   = 'active'
    _aviaLayoutBuilderCleanData = identisch zu post_content
    _av_el_mgr_version          = '1.0'
    _avia_sc_parser_state       = 'check_only'
    header_title_bar            = 'hidden_title_bar'

**Enfold rendert aus `_aviaLayoutBuilderCleanData`, nicht aus `post_content`.** Beide
Felder immer gemeinsam schreiben, sonst bleibt die Änderung im Frontend unsichtbar.

Shortcode-Baum danach neu erzeugen:

    $tree = ShortcodeHelper::build_shortcode_tree($content);
    Avia_Builder()->save_shortcode_tree($id, $tree);   // erwartet ein Array, keinen String

## Shortcodes nicht abtippen

Die Attributlisten von `av_section`, `av_textblock`, `av_hr`, `av_image` und `av_codeblock`
sind mehrere hundert Zeichen lang. Zieh die Öffnungs-Tags per Regex aus einem bestehenden
Beitrag und ersetze nur `av_uid`, bei `av_image` zusätzlich `src`, `attachment` und
`alt_attr`. Jede `av_uid` im Beitrag muss eindeutig sein.

Als Referenzbeitrag eignet sich jeder aktuelle Blogbeitrag mit vollständiger Elementkette.

## Codeblock und FAQ

Der `av_codeblock` gibt seinen Inhalt roh aus. Absatz- und Überschriftentags müssen dort
ausgeschrieben stehen (`<h3>`, `<p>`), sonst steht die FAQ als Textwüste in der Seite.
In `av_textblock` ist das egal, dort greift beim Rendern autop.

Wird ein Beitrag doch einmal im Standard-Editor gespeichert, entfernt TinyMCE alle
`<p>`-Tags und wandelt `<br />` in Zeilenumbrüche. Im Textblock folgenlos, im Codeblock
zerstörend. Nach so einem Eingriff den Codeblock prüfen und die Tags wiederherstellen.

Table of Contents Plus erfasst keine Überschriften aus Codeblöcken. Die FAQ taucht deshalb
nie im Inhaltsverzeichnis auf. Das gilt für alle bestehenden Beiträge und ist kein Fehler.

## Renderprüfung

`apply_filters('the_content', …)` allein zeigt den Codeblock **immer** leer, weil Enfold
die Inhalte vorab herauszieht. Ohne die beiden Hilfsmethoden hält man einen funktionierenden
Beitrag für kaputt:

    $sc = new avia_sc_codeblock(Avia_Builder());
    avia_sc_codeblock::$codeblocks = []; avia_sc_codeblock::$codeblock_id = 0;
    $tmp = $sc->code_block_extraction($content);
    avia_sc_codeblock::$codeblock_id = 0;
    $out = $sc->code_block_injection(apply_filters('the_content', $tmp));

Geprüft wird: Zahl der H2 und H3, Tabellen, Bilder, FAQ vorhanden, keine Shortcode-Reste.

## Bilder

Alle Bilder als WebP. Fotos verlustbehaftet mit Qualität 82, Schaubilder verlustfrei nach
Quantisierung auf 64 Farben. Beitragsbilder 1600×900, Schaubilder 1760 px breit.

Der WordPress-Bildeditor reicht bei WebP den Qualitätswert nicht durch — `set_quality(82)`
liefert eine Datei um 1,5 MB. Nach dem Speichern mit Imagick nachkomprimieren
(`setImageFormat('webp')`, `setOption('webp:lossless','false')`,
`setImageCompressionQuality(82)`, `stripImage()`), danach `wp_update_attachment_metadata`
neu erzeugen.

Schaubilder immer lokal rendern (cairosvg) und die fertige WebP übertragen: Der Server
listet rsvg-convert zwar als ImageMagick-Delegate, das Binary fehlt aber, und der interne
MSVG-Renderer liefert unscharfe, zu fette Schrift. Übertragung als Base64 in Blöcken von
etwa 25.000 Zeichen per `novamira/write-file`, serverseitig zusammensetzen, dekodieren und
per SHA1 gegen die lokale Datei prüfen. Bei Abweichung blockweise suchen (sha1 je 1.000 Zeichen).

Im Beitrag mit `attachment_size='full'` einbinden: die 1760-px-Datei ist kleiner als die von
WordPress erzeugte 1030-px-Ableitung und auf Retina schärfer.

Bilder nie unter demselben Dateinamen ersetzen — Browser und Caches liefern weiter die alte
Datei. Ersatzbilder unter neuem Namen hochladen, neues Attachment anlegen, Beitrag umstellen.

Jedes Attachment bekommt `_wp_attachment_image_alt` und einen **individuellen**
`_avia_attachment_copyright`. Enfold rendert den Bildcredit innerhalb des Bildlinks;
identische Credits erzeugen den Seobility-Befund „Identische Linktexte".

SVG-Uploads sind in WordPress gesperrt und bleiben es.

## Sicherung und Nacharbeit

Vor jeder Inhalts- oder Meta-Änderung ein Backup je Post in einem Meta-Feld mit Datum
**und Uhrzeit** ablegen, etwa `_bk_content_backup_20260828_1600`. Reine Datumsschlüssel
kollidieren, wenn am selben Tag zwei Sitzungen dieselbe Seite anfassen.

Nach Änderungen den WP-Rocket-Cache leeren. Frontend-Vergleiche per sha1 sind wegen des
Caches unzuverlässig; belastbar ist der Vergleich in der Datenbank: Backup-Meta nehmen,
dieselbe Transformation darauf anwenden, mit dem Ist-Zustand vergleichen.

Generierte PHP-Dateien gehören in `wp-content/novamira-sandbox/`. Ein mu-plugins-Verzeichnis
existiert auf dem Server nicht.
