# Anforderungsprofil Einkommensteuer-Skill

Stand: 14. August 2026  
Status: Version 0.1 - technische Grundlage zur fachlichen Erprobung

## 1. Ziel

Aus einem heterogenen Mandantenbestand eine nachvollziehbare Arbeitsgrundlage für die deutsche Einkommensteuererklärung erstellen. Das Ergebnis muss einem fachlichen Bearbeiter zeigen, welcher Betrag aus welchem Grund in welches Formularfeld übernommen werden soll und welche Punkte noch zu prüfen oder nachzufordern sind.

## 2. Vorgesehene Eingaben

- sämtliche für das Veranlagungsjahr bereitgestellten Mandantenunterlagen
- erkennbare Ordner- oder Dateikennzeichnungen für einzelne Vermietungsobjekte
- Einkommensteuererklärung des Vorjahres
- Berechnungslisten und Anlagen des Vorjahres
- sonstige Vorjahresarbeitspapiere, etwa zu Arbeitszimmer, Aufteilungen oder Abzugsfähigkeiten
- weitere Stammdaten oder fachliche Vorgaben, soweit bereitgestellt



## 3. Verbindliche Ausgaben

### Arbeitspapier

Eine zeilenweise Eintragungsmatrix mit mindestens:

- Steuerpflichtiger oder zugeordnete Person
- Veranlagungsjahr
- Mantelbogen, Anlage oder Themenbereich
- amtliche Kennziffer beziehungsweise Feldbezeichnung
- optionales Zielfeld im eingesetzten Steuerprogramm
- vorgeschlagener Betrag
- Rechenweg und Aufteilungslogik
- Quellen-ID und Belegseite
- Vorjahreswert und Abweichung
- Status „bereit“, „prüfen“, „nachfordern“ oder „nicht verarbeitet“
- Bearbeitungshinweis

### Belegpaket

- unveränderte Originale in einem getrennten Quellbereich
- nur bei eindeutiger Zuordnung getrennte Upload-Dateien
- Belegmanifest mit Rückverweis auf Original und Originalseiten
- nachvollziehbare, kollisionsfreie Dateinamen
- technische Integritäts- und Vollständigkeitskontrolle

### Prüf- und Nachforderungsprotokoll

- fehlende Unterlagen oder Angaben
- widersprüchliche oder mehrdeutige Zuordnungen
- fachlich zu prüfende Würdigungen
- verwendete Annahmen einschließlich Auswirkung
- unerklärte Vorjahresabweichungen
- technisch nicht lesbare oder nicht verarbeitete Dateien
- klare nächste Handlung und betroffene Eintragungsposition

## 4. Fachliche Leitplanken

- Das Vorjahr ist Erwartungsgerüst, aber kein Beleg für das aktuelle Jahr.
- Ein fehlender aktueller Beleg führt nicht automatisch zur Übernahme von null oder des Vorjahreswerts.
- Objektkennzeichnungen in Ordnern und Dateinamen sind zu verwenden, aber gegen den Beleginhalt zu plausibilisieren.
- Originale bleiben unverändert; Trennungen sind abgeleitete Arbeits- oder Upload-Dateien.
- Jede Zahl bleibt bis zur Quelle und gegebenenfalls bis zur Einzelrechnung prüfbar.
- Rechts- oder Tatsachenunsicherheit wird sichtbar gemacht und nicht durch eine scheinpräzise Eintragung verdeckt.
- Jahresbezogene Formularstände und amtliche Quellen sind bindend.

## 5. Vorläufiger Umfang

Als erster fachlicher Kern sind private Einkommensteuerfälle natürlicher Personen vorgesehen. Denkbarer Standardumfang: Hauptvordruck sowie Anlagen N, Vorsorgeaufwand, Kind, V, KAP, SO und R.

Bis zur Entscheidung als Sonder- oder Prüffälle behandeln:

- betriebliche Einkünfte und Gewinnermittlungen
- Auslandssachverhalte
- Kryptowährungen und umfangreiche private Veräußerungsgeschäfte
- Land- und Forstwirtschaft
- komplexe Beteiligungen und gesonderte Feststellungen
- sonstige Sachverhalte, die kein stabiles Beleg-zu-Feld-Verfahren erlauben

## 6. Festgelegte Grundentscheidungen

- Eingangsunterlagen sind die vom Mandanten bereitgestellten Unterlagen.
- Der Kernworkflow ist nicht auf ein einzelnes Veranlagungsjahr beschränkt.
- Das Veranlagungsjahr wird je Fall ermittelt; Formulare und Feldzuordnungen werden jahresbezogen geprüft.
- Getrennte Belege werden für DATEV Meine Steuern vorbereitet.
- Das zentrale Arbeitspapier wird als Excel-Arbeitsmappe erstellt.
- Zielsystem für die Dateneingabe ist DATEV Einkommensteuer; die eigentliche Eingabe bleibt eine menschliche Tätigkeit.

Noch offen ist der endgültige Umfang der ersten fachlich unterstützten Anlagen.

## 7. Geplante Paketstruktur

~~~text
ESt_<Jahr>_<Fall-ID>/
|-- 00_Originale/
|-- 01_Arbeitspapier/
|-- 02_Upload-Belege/
|-- 03_Pruefung-und-Nachforderung/
+-- 04_Manifest-und-Validierung/
~~~

Die Struktur ist für die manuelle Bearbeitung in DATEV Einkommensteuer und den manuellen Belegupload in DATEV Meine Steuern vorgesehen.

## 8. Abnahmekriterien der späteren ersten Version

- Jeder aktuelle Eingangsbeleg steht im Inventar.
- Jede vorgeschlagene Eintragung besitzt einen Rechenweg und einen Quellenverweis.
- Jede getrennte Datei ist zum Original und zu den Originalseiten rückverfolgbar.
- Alle nicht eindeutig bearbeitbaren Punkte erscheinen im Prüf- oder Nachforderungsprotokoll.
- Summen, Einzelbelege und Nebenrechnungen sind abgestimmt.
- Vorjahressachverhalte sind als fortgeführt, geändert, weggefallen oder ungeklärt klassifiziert.
- Das Paket kann ohne stille Annahmen von einem fachlichen Bearbeiter geprüft werden.