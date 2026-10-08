---
name: nachlasspflege-vermieterkuendigung
description: Use when a Nachlasspfleger needs a standardized landlord termination workflow. Retrieve case data from DATEV DMS and supplied documents, verify current German tenancy law, calculate the earliest defensible termination date, draft the landlord letter independently, and always also generate a Mietaufhebungsvertrag from the bundled authoritative DOCX template. Output both Word files; only the contract carries the watermark "Entwurf".
---

# Nachlasspflege – Kündigung / Vermieterkorrespondenz

## Ziel

Erstelle aus den vorhandenen Unterlagen ein weitgehend versandfertiges Kündigungsschreiben an den Vermieter. Der Anwender soll im Normalfall nur die Unterlagen bzw. den Nachlassfall benennen müssen. Recherchiere die benötigten Tatsachen selbst aus DATEV-DMS und den bereitgestellten Dokumenten.

Der Standardoutput besteht **immer aus zwei Word-Dateien für Sara**:

1. dem neu formulierten Kündigungs-/Vermieterschreiben ohne Wasserzeichen und
2. unmittelbar danach dem ausgefüllten Mietaufhebungsvertrag auf Basis der hinterlegten Kanzleivorlage mit dem Wasserzeichen **„Entwurf“** auf allen Seiten.

Nur wenn der Anwender ausdrücklich verlangt, eines der beiden Dokumente nicht zu erstellen, darf davon abgewichen werden. Das Vermieterschreiben wird **nicht aus dem Padniewski-Schreiben abgeleitet**.

## 1. Daten zuerst aus dem Fall ermitteln

Suche im DATEV-DMS über den Riecken-MCO-Connector nach dem Nachlassfall. Nutze Name des Erblassers, Aktenzeichen, Gericht und Vorgangsmappe. Wenn eine Vorgangsmappe existiert, lies ihre Dokumentlinks aus; eine normale Stichwortsuche kann verlinkte Dokumente übersehen.

Lies die Originalinhalte und verlasse dich nicht nur auf Dokumenttitel. Suche mindestens nach:

- Beschluss über die Bestellung zum Nachlasspfleger,
- Bestellungsurkunde,
- Vermieterschreiben bzw. Informationen über den Vermieter,
- Mietvertrag, soweit vorhanden,
- früherer Korrespondenz zum Mietverhältnis,
- Hinweisen auf Mitmieter, Ehegatten, Lebenspartner, Kinder oder sonstige Mitbewohner,
- Hinweisen auf Schlüssel, Versiegelung, Polizei/Ordnungsamt, Kaution und Bankverbindung des Verstorbenen.

Ermittle und validiere folgende Pflichtdaten:

1. vollständiger Name des Erblassers,
2. zuständiges Amtsgericht/Nachlassgericht,
3. Aktenzeichen,
4. Beschlussdatum,
5. Wirkungskreis der Nachlasspflegschaft; die Beendigung/Abwicklung des Mietverhältnisses muss umfasst sein,
6. Anschrift der Mietwohnung,
7. Vermieter mit vollständiger postalischer Anschrift,
8. Todesdatum,
9. vorhandene Erkenntnisse zu Eintritt/Fortsetzung nach §§ 563, 563a BGB,
10. vorhandener Mietvertrag und seine Laufzeit/Kündigungsregeln,
11. Kenntniszeitpunkte, soweit sie für § 564 BGB erforderlich sind,
12. Informationen zu Kaution, Schlüsseln und Bankverbindungen.

Wenn Pflichtangaben nach DMS-Suche und Auswertung der übergebenen Unterlagen fehlen, **nichts erfinden**. Frage als internen Fallback Tracy über den freigegebenen Outlook-Connector nach genau den fehlenden Angaben, sofern Tracy eindeutig im Verzeichnis identifiziert werden kann. Ist der Empfänger nicht eindeutig auflösbar, frage den Anwender.

## 2. Juristische Prüfung vor Berechnung des Kündigungstermins

Prüfe vor jedem Schreiben die aktuelle Fassung des BGB in der amtlichen Quelle `gesetze-im-internet.de`, insbesondere §§ 563, 563a, 564, 573d und 573c BGB. Nutze statische Skill-Regeln nur als Ausgangspunkt; bei Gesetzesänderungen gilt die aktuelle amtliche Fassung.

Für Wohnraum gilt im Regelfall:

- Zuerst prüfen, ob eine Person nach § 563 BGB in das Mietverhältnis eingetreten ist oder es nach § 563a BGB mit einem überlebenden Mitmieter fortgesetzt wird.
- Nur wenn dies nicht der Fall ist, wird das Mietverhältnis nach § 564 BGB mit dem Erben fortgesetzt. Dann besteht ein Sonderkündigungsrecht innerhalb der gesetzlichen Monatsfrist nach Kenntnis von Tod und fehlendem Eintritt/fehlender Fortsetzung.
- Die „gesetzliche Frist“ richtet sich bei Wohnraum nach § 573d Abs. 2 BGB: Zugang spätestens am dritten Werktag eines Kalendermonats zum Ablauf des übernächsten Monats.
- Wenn die Voraussetzungen oder die Monatsfrist des § 564 BGB nicht sicher belegt sind, verwende die außerordentliche Kündigung **vorsorglich** und kündige **hilfsweise ordentlich zum nächstmöglichen Zeitpunkt**. Bei befristeten oder atypischen Mietverträgen darf der ordentliche Hilfsweg nicht ungeprüft als wirksam unterstellt werden.

### Berechnung

Berechne den konkreten Beendigungstag nur mit belastbaren Daten. Maßgeblich ist der Zugang der Kündigung beim Vermieter, nicht die bloße Erstellung des Briefes. Bei Postversand nahe am dritten Werktag wähle im Zweifel den späteren, sicheren Termin oder formuliere die Datumsangabe ausdrücklich unter einer Zugangsvoraussetzung.

Dokumentiere intern kurz:

- angenommenen/gesicherten Zugangstag,
- dritten Werktag des Monats,
- daraus folgenden Beendigungszeitpunkt,
- ob § 564 BGB sicher, vorsorglich oder nicht nutzbar ist.

## 3. Vermieterschreiben eigenständig neu entwerfen

Das Vermieterschreiben wird **nicht aus dem Padniewski-Schreiben Nr. 87339 kopiert oder stilistisch abgeleitet**. Entwirf es für jeden Fall neu auf Grundlage der Falldaten, der nachstehenden Pflichtinhalte und der fachlichen Regeln aus der NachlassAkademie-Unterlage. Nutze `templates/erstanschreiben.md` als kanzleiinternes Grundmuster.

### A. Bestellung und Legitimation

Das Schreiben beginnt sachlich und nennt Bestellung, Gericht, Aktenzeichen und Beschlussdatum, z. B. sinngemäß:

„Mit Beschluss des Amtsgerichts [Gericht] vom [Beschlussdatum], Az. [Aktenzeichen], bin ich zum Nachlasspfleger für die unbekannten Erben des am [Todesdatum] verstorbenen [Name] bestellt worden. Der Wirkungskreis umfasst die Beendigung und Abwicklung des Mietverhältnisses. Eine Kopie meiner Bestellungsurkunde füge ich bei.“

### B. Eintritt/Fortsetzung klären

Sofern nicht bereits eindeutig geklärt:

„Bitte teilen Sie mir mit, ob Personen gemäß § 563 BGB in das Mietverhältnis eingetreten sind oder das Mietverhältnis gemäß § 563a BGB mit einem weiteren Mieter fortgesetzt wird.“

### C. Kündigung

Standardform bei Wohnraum:

„Vorsorglich kündige ich das Mietverhältnis außerordentlich unter Einhaltung der gesetzlichen Kündigungsfrist zum nächstmöglichen Zeitpunkt; dies ist nach meiner Berechnung der [Datum]. Hilfsweise kündige ich das Mietverhältnis ordentlich zum nächstmöglichen Zeitpunkt.“

Wenn ein fixes Datum rechtlich nicht belastbar berechnet werden kann, kein Datum erfinden. Dann nur „zum nächstmöglichen Zeitpunkt“ verwenden und den Grund intern nennen.

### D. Aufhebungsvertrag anbieten

Immer anbieten, das Mietverhältnis durch Vereinbarung früher zu beenden, damit der Vermieter die Wohnung möglichst schnell zurückerhält und wieder nutzen oder vermieten kann.

### E. Keine Kostenübernahme zusagen

Der wirtschaftliche Vorbehalt ist zwingend und deutlich zu formulieren:

„Derzeit kann ich nicht beurteilen, ob ausreichende liquide Mittel im Nachlass vorhanden sind. Daher kann ich die Übernahme oder Erstattung von Kosten – insbesondere für die Öffnung, Räumung, Entrümpelung, Lagerung oder sonstige Maßnahmen im Zusammenhang mit der Wohnung – nicht zusagen.“

„Soweit derartige Maßnahmen erforderlich sind, müssten Sie diese zunächst im eigenen Namen beauftragen und vorfinanzieren. Etwaige Forderungen können zur Prüfung beim Nachlass angemeldet werden. Eine Anerkennung dem Grunde oder der Höhe nach ist damit nicht verbunden.“

Keine Formulierung verwenden, aus der eine persönliche Kostenhaftung des Nachlasspflegers oder eine sichere Zahlung aus dem Nachlass abgeleitet werden könnte.

### F. Besichtigung / Übergabe

Bitte um Abstimmung eines gemeinsamen Besichtigungs- und Übergabetermins. Wenn Schlüssel fehlen, die Wohnung versiegelt ist oder eine Öffnung erforderlich wird, nur die tatsächlich belegten Tatsachen ergänzen.

### G. Eigenmächtige Räumung verhindern

Wenn eine Räumung/Öffnung konkret im Raum steht, kurz und sachlich aufnehmen, dass bis zur abgestimmten Übergabe von eigenmächtiger Öffnung, Inbesitznahme oder Räumung abzusehen ist. Gesetzlich zulässige Maßnahmen bei Gefahr im Verzug bleiben unberührt.

Lange strafrechtliche Warnungen sind kein Standardbaustein.

### H. Unterlagen, Kaution, Schlüssel und Bankkonto

Bitte standardmäßig um:

- Kopie des Mietvertrages, soweit nicht vorhanden,
- vorhandenes Übergabeprotokoll,
- Information über eine Mietkaution,
- Information über vorhandene Wohnungsschlüssel,
- **Informationen über Bankverbindungen des Verstorbenen**, soweit dem Vermieter solche aus Mietzahlungen, Lastschriften, Kontoauszügen oder sonstiger Korrespondenz bekannt sind.

### I. Anlagen

Zwingend aufführen:

- Kopie der Bestellungsurkunde.

Den Beschluss nur beifügen, wenn dies im Einzelfall sinnvoll oder vom Anwender gewünscht ist.

## 4. Verbindliche Kanzleivorlage für den Mietaufhebungsvertrag

Die vom Anwender bereitgestellte Datei **`templates/Mietaufhebungsvertrag.docx`** ist die verbindliche Kanzleivorlage für den Mietaufhebungsvertrag. Sie stammt aus dem Padniewski-Fall und hat für Aufbau, Klauselreihenfolge, Formulierungsgrundlage und Unterschriftsblock Vorrang vor allen früheren Ersatzmustern oder Seminarvorlagen.

Zusätzlich enthält `templates/mietaufhebungsvertrag.md` eine textgetreue interne Fallback-Fassung derselben Vorlage. Wenn die DOCX-Datei in einem Lauf technisch nicht lesbar oder nicht direkt bearbeitbar ist, verwende diese Fallback-Fassung. Ändere dabei die Vertragsstruktur oder Standardklauseln nicht eigenmächtig; ersetze nur fallbezogene Platzhalter und passe ausdrücklich fallabhängige Regelungen an.

Verwende **nicht** DMS-Dokument Nr. 87339 als Vertragsvorlage; dieses Dokument ist nur ein Begleitschreiben.

Arbeitsweise für jeden Fall:

- Öffne eine Kopie der hinterlegten DOCX-Vorlage und bearbeite diese. Falls die Binärdatei technisch nicht lesbar ist, rekonstruiere das Dokument aus der textgetreuen Fallback-Fassung `templates/mietaufhebungsvertrag.md`.
- Fülle sämtliche Platzhalter aus den tatsächlich festgestellten Falldaten.
- Behalte die fünf Vertragsabschnitte der Vorlage grundsätzlich bei: Wohnung/Beendigungszeitpunkt, Übergabe und Verbleib der Gegenstände, Zählerstände, Zahlungsansprüche/Abgeltung sowie Änderungen/salvatorische Klausel.
- Fallbezogene Optionen wie besondere Gegenstände, Zählerdaten, Kaution, Öffnungs-/Räumungskosten und Beendigungsdatum nur mit belastbaren Angaben ausfüllen. Nicht bekannte Werte nicht erfinden; erforderlichenfalls als klaren offenen Platzhalter markieren.
- Die wirtschaftlichen Vorbehalte müssen erhalten bleiben: keine persönliche Haftung des Nachlasspflegers und keine ungesicherte Zusage, dass Forderungen aus dem Nachlass erfüllt werden können.
- Setze auf **allen Seiten des ausgefüllten Vertrags** das Wasserzeichen **„Entwurf“**. Die hochgeladene DOCX-Quelldatei selbst bleibt unverändert.
- Rendere den fertigen DOCX-Vertrag und kontrolliere alle Seiten visuell.

Die Vorlage ist als Binärdatei Bestandteil des Skills. Wird sie technisch nicht lesbar oder beschädigt, melde das ausdrücklich statt eine andere Vorlage als Ersatz auszugeben.

## 5. NachlassAkademie-Unterlagen als fachliche Grundlage

Die SharePoint-Unterlage **„82781 - Nachlasspfleger - Immobilien im Nachlass - Skript.pdf“**, Abschnitt 5 „Der Erblasser als Mieter“, enthält auf den Skriptseiten 35–44 die fachliche Grundlage. Besonders wichtig:

- S. 35–36: Warnung vor eigenmächtiger Inbesitznahme/Räumung durch den Vermieter und BGH VIII ZR 45/09.
- S. 38: Nachlasspfleger kann das Mietverhältnis bei alleiniger Mieterschaft/Bewohnung kündigen und Wohnung zurückgeben.
- S. 39–42: Besitz- und Eintrittsregeln §§ 563 ff. BGB.
- S. 42: fachliche Orientierung für ein Erstanschreiben mit Nachfrage zu §§ 563/563a, vorsorglicher außerordentlicher Kündigung, hilfsweiser ordentlicher Kündigung und Abfrage von Mietvertrag, Übergabeprotokoll, Kaution und Schlüsseln.
- S. 43–44: fachliche Ergänzung zum Mietaufhebungsvertrag. Für den konkreten Vertrag ist jedoch die eingebettete Kanzleivorlage `templates/Mietaufhebungsvertrag.docx` maßgeblich.

## 6. Word-Dokument erzeugen

### A. Normales Schreiben an den Vermieter

Erstelle ein DOCX mit:

- eigenständig neu formuliertem Inhalt nach `templates/erstanschreiben.md`,
- Kanzleistil bzw. vorhandener allgemeiner Briefvorlage, sofern verfügbar,
- Datum im Format „dd. Monat JJJJ“,
- vollständiger Empfängeranschrift,
- sachgerechtem Betreff,
- sachlichem, knappem Kanzleistil,
- keinen gegenderten Formulierungen,
- Unterschriftszeile „Burchardt – als Nachlasspfleger nach [Name]“ bzw. dem vorhandenen kanzleiüblichen Muster,
- Anlagenvermerk „Kopie der Bestellungsurkunde“,
- **keinem Wasserzeichen**.

Verwende das Padniewski-Schreiben Nr. 87339 weder als Text- noch als Layoutvorlage für dieses Schreiben.

Dateiname:

`Kündigung Mietverhältnis – Nachlass [Name] – [Aktenzeichen].docx`

Vor Bereitstellung das DOCX rendern und visuell prüfen. Insbesondere Seitenumbrüche, Anschriftenfeld, Betreff, Anlagenvermerk und Abwesenheit eines Wasserzeichens kontrollieren.

### B. Mietaufhebungsvertrag

Erstelle **bei jedem Fall unmittelbar nach dem Vermieterschreiben** zusätzlich den Mietaufhebungsvertrag aus `templates/Mietaufhebungsvertrag.docx`, sofern der Anwender ihn nicht ausdrücklich abbestellt. Bearbeite eine Kopie, ersetze die Platzhalter mit den Falldaten und passe nur die tatsächlich fallabhängigen Regelungen an.

Der Vertrag erhält auf allen Seiten ein deutlich sichtbares Wasserzeichen **„Entwurf“**. Vor Ausgabe rendern und vollständig visuell prüfen.

Dateiname:

`Entwurf Mietaufhebungsvertrag – Nachlass [Name] – [Aktenzeichen].docx`

### C. Ausgabereihenfolge

Gib dem Anwender nach erfolgreicher Erstellung **immer beide Dateien in dieser Reihenfolge** aus:

1. `Kündigung Mietverhältnis – Nachlass [Name] – [Aktenzeichen].docx`
2. `Entwurf Mietaufhebungsvertrag – Nachlass [Name] – [Aktenzeichen].docx`

Wenn eine Datei zusätzlich im DMS abgelegt wird, ersetzt die Ablage nicht die Ausgabe im Chat; beide Word-Dateien sind weiterhin bereitzustellen.

## 7. DMS-Ablage für Sara

Wenn der Auftrag die Erstellung für Sara zum Ausdruck/Versand umfasst und der Nachlassfall eindeutig identifiziert ist, lege den fertigen DOCX-Entwurf im DATEV-DMS beim richtigen Nachlassfall ab.

Bearbeitungsstatus bei diesem Zwischenschritt ausdrücklich: **„offen“**.

Nach der Ablage zwingend anhand der Dokument-ID zurücklesen und prüfen:

- richtiger Mandant/Nachlassfall,
- richtiger Ablageort/Register,
- Format DOCX,
- Bearbeitungsstatus „offen“.

Erst nach tatsächlich abgeschlossener Korrespondenz darf die endgültige Fassung als **„erledigt“** behandelt werden. Bei jeder späteren DMS-Ablage den Status ausdrücklich übergeben und anschließend kontrollieren.

## 8. Qualitätskontrolle vor Ausgabe

Vor Fertigstellung prüfe ausdrücklich:

- Name des Erblassers korrekt und überall identisch,
- Gericht und Aktenzeichen aus Beschluss/Bestellungsurkunde,
- Beschlussdatum nicht mit Eingangsdatum oder Ausfertigungsdatum verwechselt,
- Wirkungskreis deckt Mietbeendigung ab,
- Vermieter und Wohnungsanschrift korrekt,
- §§ 563/563a geprüft bzw. im Schreiben abgefragt,
- § 564-Frist geprüft,
- Kündigungstermin nachvollziehbar berechnet,
- Kostenübernahme **nicht** zugesagt,
- Aufhebungsvertrag angeboten,
- Termin zur Besichtigung/Übergabe angeboten,
- Bankverbindung des Verstorbenen abgefragt,
- Bestellungsurkunde als Anlage genannt,
- normales Vermieterschreiben: **kein Wasserzeichen** und **keine Ableitung aus Padniewski Nr. 87339**,
- Mietaufhebungsvertrag: **immer** aus `templates/Mietaufhebungsvertrag.docx` erzeugen (außer ausdrücklich abbestellt); Wasserzeichen **„Entwurf“** auf allen Seiten,
- keine fallfremden Daten verblieben,
- beide Word-Dateien wurden im Chat ausgegeben und verlinkt.

Siehe zusätzlich `references/fachliche-regeln.md`, `templates/erstanschreiben.md`, `templates/mietaufhebungsvertrag.md` und die verbindliche Binärvorlage `templates/Mietaufhebungsvertrag.docx`.
