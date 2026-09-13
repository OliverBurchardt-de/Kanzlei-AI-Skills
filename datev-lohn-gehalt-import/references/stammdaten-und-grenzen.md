# Stammdaten und weitere Importwege

Die mitgelieferte `Importschnittstelle.pdf` beschreibt die Zeitwirtschaftsschnittstelle. Sie definiert keine importierbaren Feldkennungen für Adressen, Bankverbindungen, Ein-/Austritte oder andere Mandanten- und Mitarbeiterstammdaten. Der Zeitwirtschaftshelfer kann solche Daten deshalb nicht rendern.

Bei einer entsprechenden Anfrage trotzdem die Quelle lesen, Daten und offene Zuordnungen aufbereiten. Für die eigentliche Importdatei den passenden Stammdatenleitfaden und die zur eingesetzten LuG-Version gehörende Satzbeschreibung verwenden. Einstieg: [DATEV-Dokument 1080789, Abschnitt Personalwirtschaft / Lohn und Gehalt](https://apps.datev.de/help-center/documents/1080789).

DATEV hat am 10.06.2026 neue Stammdaten-Satzbeschreibungen für LuG 15.8 angekündigt: [DATEV Developer Portal](https://developer.datev.de/en/news/details/shssmh53tmdmu4qsdu6g4hk0). Das belegt die Versionsabhängigkeit, nicht die beim Nutzer installierte Version oder die Verfügbarkeit aller Felder.

Für eine Stammdatenkonvertierung:

1. Zielversion, fachlichen Datenbereich und Zweck (Neuanlage/Änderung) aus Auftrag bzw. Bestand feststellen.
2. Die genaue DATEV-Satzbeschreibung zur Version lesen und als Referenz mit Titel, Stand und Prüfsumme sichern. Kein LODAS-Format und keine FIBU-EXTF-Datei dafür verwenden.
3. Feldkennungen, Satztypen, Pflichtfelder, Schlüssel und gültige Werte direkt daraus ableiten. Unterdrückte, leere und zu löschende Werte anhand der dokumentierten Semantik unterscheiden.
4. Die eigene Quell-Ziel-Zuordnung und Belege erhalten. Nur dokumentierte/importierbare Felder ausgeben. Nicht übernehmbare Daten als offenen Rest berichten.
5. Datei gegen genau diese Beschreibung prüfen und den tatsächlichen DATEV-Probeimport gesondert nachweisen.

**Stand dieses Pakets:** Die aktuelle vollständige Stammdaten-Satzbeschreibung ist nicht enthalten und ihre Felddefinitionen wurden nicht validiert. Die gefundenen direkten DATEV-PDF-Links lieferten bei der Prüfung am 13.09.2026 eine Web-Anwendung bzw. HTTP 404 statt einer PDF. Daher werden keine vermeintlichen Stammdatenfelder aus Suchauszügen erzeugt. Ohne erreichbare Spezifikation die aufbereiteten neutralen Daten und die konkret fehlende Beschreibung liefern; keinen importfertigen Stammdatenstapel behaupten.

Ein Ausgangsdokument kann mehrere Importwege betreffen. In diesem Fall Zeitwirtschaftsdaten mit der vorhandenen Beschreibung bearbeiten und Stammdaten separat anhand ihrer Spezifikation behandeln. Eine komplette Migration aller Daten, Abrechnungsergebnisse oder Dokumente ist durch diese PDF nicht beschrieben.
