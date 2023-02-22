Prorgamm zum automatischen Export, alle 24h, von ausgewählten kofigurierbaren Items , aus der Smart HMI Projektdatenbank.


Notwendige Voreinstellungen:

im Ordner json file config.json:

projektname auf Namen der aktuellen Projektierung ändern
projektpfad auf Pfad zu den Projektdatenbanken des aktuellen Projekts ändern (meist reicht hier das ändern des Projektnamens im Pfad)
csv_path auf Pfad zur Ablage der exportierten Daten anpassen.
csv_seperator auf gewünschtes Trennzeichen abändern
csv_decimal auf gewünschtes Dezimal Trennzeichen abändern
export_csv auf "yes" wenn eine Datei erzeugt werden soll, "No" wenn keine Datei erzeugt werden soll
export_json auf "yes" wenn eine Datei erzeugt werden soll, "No" wenn keine Datei erzeugt werden soll 


im Ordner txt

Alias Namen der zu exportierenden Items durch "," getrennt eintragen (beliebig viele) 


Der letzte Zeitstempel der ausführung eines Exports liegt in der Datei lastdate.txt. Um das exportieren neu zu starten (alle Daten bis heute) diese Datei löschen. 