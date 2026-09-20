# Vertrag für getrennte Bankmodelle

Je Bank einen eigenen Ordner `banks/<institut>/` anlegen. Abweichende Kontoarten,
Exportwege und wesentliche Layoutänderungen bekommen eigene Varianten.
Ein allgemeiner MT940-Standard ist nur Formatquelle, kein Bankmodell.

Pflichtbestandteile:

- `model.md`: genaue Bankidentität, Quellvariante, bankeigene Extraktions- und
  Umbruchregeln, Status, Primärquellen und bekannte Grenzen.
- `profile.json`: Modell-ID, Bankbindung, Feldregeln und getrennte technische
  bzw. praktische Abnahme. Kein globales Universalprofil.
- Eine eigene `reference.sta` mit Eingabe und unabhängig festgelegtem Sollinhalt.
  Synthetisch/nativ klar unterscheiden. In öffentlichen Repositories ausschließlich
  frei erfundene Referenzdaten verwenden. Echte Mandantendateien, Einzelumsätze,
  Beträge, Namen, Konten, Referenzen und Originaldatei-Hashes nicht veröffentlichen.
  Private Abnahmen getrennt verwahren; synthetische Dateien nicht als abgenommen melden.
- Eigenen Encoder und unabhängig lesenden Decoder. Der Prüfer darf nicht einfach
  den Encoder aufrufen und dessen Ausgabe als Sollwert verwenden.
- Regressionstests: fehlende Umsätze, leere/abgeschnittene Texte, lange Namen,
  Umlaute, Soll/Haben, abweichende Valuta, Monats- und Seitenwechsel.
  Fehlerhafte alte Beispiele müssen abgelehnt werden.

Bankidentität und Variante vor Verwendung abgleichen. Unbekannte Institute und
gesperrte Versionen ablehnen. Die statische Referenz nicht während des Tests
automatisch erneuern und nicht als Bankoriginal oder DATEV-verifiziert ausgeben.

Die Original-Auszugskette auch in einer Gesamtdatei bewahren: Anfangssaldo plus
Einzelumsätze gleich Endsaldo je Auszug; Schlussdatum/-saldo des Vorgängers gleich
Anfangsdatum/-saldo des Nachfolgers. Erwartete Umsatzanzahl und Monatsverteilung
unabhängig aus allen Quellseiten erheben. Auch fehlende betragsneutrale Paare erkennen.

Unmögliche Daten, widersprüchliche Bankkennungen, Textverlust und Kapazitätsgrenzen
sind konkrete Klärungsfälle. Fehlender DATEV-Probeimport allein begrenzt nicht
die vollständige Dateierstellung. Ungeklärte Quelldaten aber niemals erfinden.

Praxisabnahme je Version: Datei-Hash, Datum, Art und Umfang der Bestätigung,
DATEV-Version soweit bekannt, Monatsanzahl, Salden, Vorzeichen, Gegenpartei sowie
vollständige Zwecke einschließlich Anfang/Ende. Technische Prüfungen, Nutzerbestätigung
und direkte Systembeobachtung getrennt halten. Zeichensatz bank- und importwegspezifisch
anhand belegter Ausgabe prüfen; keine globale Standardkodierung ableiten.
Vorhandene Testbuchungen sind Sache des Anwenders; keine fiktive Löschbestätigung.
