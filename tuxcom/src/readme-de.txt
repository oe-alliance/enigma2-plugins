TuxCom:

Historie:
---------
08.04.2007 Version 1.16
 - Ein-Fenster-Anzeige auswählbar (per Info-Taste)
 - Dateigrössen werden in Kurzform (MB/GB) angezeigt (abschaltbar im Hauptmenü)
 - Dateigrösse in Bytes wird in Dateieigenschaften (Taste "1") angezeigt

30.10.2006 Version 1.15
 - Möglichkeit, Skripte in Abhängigkeit von der Dateiendung auszuführen
 - zwei kleine Korrekturen (Dank an murks)

06.03.2006 Version 1.14
- Beim Starten des Plugins wird die Datei /tmp/keyboard.lck angelegt und nach dem Beenden wieder
  gelöscht, dies dient zur Unterstützung des kb2rcd (von robspr1)

22.01.2006 Version 1.13
 - Überschreiben von Verzeichnissen korrigiert
 
27.12.2005 Version 1.12
 - Portugiesische Übersetzung eingebaut (Dank an jlmota)
 - zwei kleine Fehler im Editor behoben
 
22.11.2005 Version 1.11
 - Bessere Tastaturabfrage bei Exit/Enter auf DMM-Tastatur
 - kleinere Fehler im Editor ausgebessert
 - weniger Speicherverbrauch 
 - Datei /tmp/tuxcom.out wird beim Beenden des Plugins gelöscht

01.10.2005 Version 1.10a
 - Zahlentasten auf USB-Tastatur funktionieren wieder

24.09.2005 Version 1.10
 - Verweise auf Dateien in schreibgeschützen Verzeichnissen erstellbar
 - Meldung beim Verzeichnis erstellen, wenn Datei bereits existiert
 
11.09.2005 Version 1.9a
 - Schwedische Übersetzung eingebaut (Dank an yeager)

10.08.2005 Version 1.9
 - Unterstützung für Dbox2-Tastaturen (von robspr1)

15.07.2005 Version 1.8a
 - Italienische Übersetzung eingebaut (Dank an fbrassin)

11.06.2005 Version 1.8
 - direkter Sprung ins Rootverzeichnis möglich (Eintrag '/' selektieren)
 - erweiterte Dateiinformationen im Rechte-Dialog (Taste 1)
 - Druck auf OK bei Dateien, die nicht ausführbar sind, öffnet den Viewer
 - Bei Neuanlegen einer Datei oder eines Verzeichnisses wird diese Datei danach automatisch selektiert.
 - Bugfix: manchmal wurde beim Editieren einer Zeile das \n am Ende entfernt

12.01.2005 Version 1.7
 - kosmetische Fehler bei Farbgebung behoben
 - Bugfix: Absturz bei Eingabe in letzter Zeile im Editor
 - Speichern der aktuellen Einstellungen nicht automatisch beim Beenden (einstellbar im Hauptmenü)
 - Auswahl der Sprache im Hauptmenü (für Neutrino, da dort automatische Auswahl nicht funktioniert)
 - Neue Funktionalität im Editor: mehrere Zeilen markieren/kopieren/verschieben/löschen (analog Midnight-Commander)

10.10.2004 Version 1.6
 - Bugfix: Fehlerhafter Text in Zwischenablage
 - neues Hauptmenü (über Dream-Taste)
 - neue Funktion: Dateien suchen (im Hauptmenü)
 - Editieren von .ftp-Dateien in eigener Maske
 - Bugfix: korrekt selektierte Datei nach Umbenennung
 - Bugfix: unter Umständen Abschneiden des letzten Zeichens bei Texteingabe möglich
 - Textfarbe schwarz bei gelbem Hintergrund
 - Bugfix: Ändern der Dateirechte auch mit Taste rot möglich
 
22.09.2004 Version 1.5a
 - Bugfix: Absturz im Editor / nach Schliessen des Editors
 - Bugfix: Absturz bei Verschieben (Button 6) von einzelnen Dateien

30.08.2004 Version 1.5
 - Passwortschutz eingebaut (über Info->Blau änderbar)
 - Möglichkeit, beim Kopieren/Verschieben die Datei umzubenennen
 - Anzeigefehler in Taskmanager bereinigt
 - Bugfixes in Editor
 - Anzeigefehler in Dateirechten bereinigt
 - Abbruch eines FTP-Downloads möglich (und Wiederaufnahme des unterbrochenen Downloads, wenn der Server das unterstützt)
 - Bugfixes in FTP-Client
 
26.08.2004 Version 1.4b
 - Texteingabe: Möglichkeit, Text zu markieren (Taste grün ) und einzufügen (Taste blau) (sozusagen eine mini-Zwischenablage :-) )
 - Editor: Anzeigen von \r als weisses Kästchen (DOS/Win-Textdatei) (blaue Taste -> Umwandeln in Linux Format)
 - FTP-Client: Entfernen von Whitespace-Zeichen am Ende des Dateinamens beim Download
 - FTP-Client: Verbesserung der Download-Geschwindigkeit

11.08.2004 Version 1.4a
 - Unterstützung für USB-Tastaturen (benötigt wird das Kernel-Modul hid.ko von BoxMan)
 - Lesen von .ftp-Dateien, auch wenn sie über Windows erstellt wurden...
 - Bugfix: Einfügen einer Zeile in eine leere Datei im Editor
 - kleinere Bugfixes im Editor
 - eine Menge Bugfixes in FTP-Client
 - Änderungen an Tastaturabfrage 
 - BugFix: Falsche Anzeige nach drücken von rot (löschen) beim Editieren
 - BugFix: Absturz bei Verlassen des Plugins mit offener FTP-Verbindung

25.07.2004 Version 1.4
 - Taskmanager eingebaut (über Info-Taste aufrufbar)
 - vor-/zurück-scrollen bei Kommandoausführung/Skriptausführung möglich
 - vor-/zurück-scrollen in Dateiansicht nicht mehr auf 100k-Dateien beschränkt
 - aktuell ausgewählte Datei merken bei Verlassen des Plugins
 - Tastaturunterstützung für DMM-Tastatur eingebaut
 - Verzögerung bei gedrückter Taste eingebaut
 - Bugfix: Workaround für Tastendruck-Fehler von Enigma
 - Bei Verweis-erstellen (Taste 0) wird automatisch der ausgewählte Dateiname vorgeschlagen

21.06.2004 Version 1.3
 - FTP-Client eingebaut
 - kleinere Fehler im Editor beseitigt
 - Texteingabe: Sprung zum nächsten Zeichen, wenn eine andere Ziffer gedrückt wird.
 - Texteingabe: letztes Zeichen wird entfernt wenn am Ende der Zeile volume- gedrückt wird.
 - Umschalten zwischen 4:3 und 16:9-Modus über Dream-Taste
 - Dateiansicht : Scrollen wie im Editor möglich (bei Dateien, die maximal 100k gross sind).

05.06.2004 Version 1.2a
 - BugFix: Fehlende Sonderzeichen bei Eingabe ergänzt.
 - Texteingabe im "SMS-Stil" eingebaut
 
29.05.2004 Version 1.2
 - Unterstützung zum Extrahieren aus "tar", "tar.Z", "tar.gz" und "tar.bz2" Archiven
   funktioniert leider im Original-Image 1.07.4 mit vielen Archiven nicht (zu alte BusyBox-Version :( )
 - Anzeige der aktuellen Zeilennummer im Editor
 - Positionierung anhand der TuxTxt-Koordinaten
 - grosse Schrift beim Editieren einer Zeile
 - Scrollen in Zeichen im Editiermodus an Enigma-Standard angepasst (hoch/runter vertauscht)
 - Versionsnummer über Info-Taste abrufbar
 - Sicherheitsabfrage, falls durch kopieren/verschieben bestehende Dateien überschrieben werden.

08.05.2004 Version 1.1a
 - BugFix: Keine angehängten Leerzeichen mehr beim Umbenennen von Dateien

02.05.2004 Version 1.1
 - einige Farbänderungen
 - Deutsche Texte eingebaut
 - Möglichkeit, Tasten gedrückt zu halten (hoch/runter, rechts/links, volume+/-, grüne Taste)
 - 3 Tranzparenzstufen 
 - Dateien markieren, sodass man mehrere Dateien auf einmal kopieren/verschieben oder löschen kann
 - Tranzparanzmodus wird jetzt durch die 'mute'- Taste gewechselt (analog zu TuxTxt) (grüne Taste wird zum Dateien markieren verwendet)

03.04.2004 Version 1.0 : 
   erste Veröffentlichung
   
     

Tasten:
---------------

links/rechts		linkes/rechtes Fenster wählen
hoch/runter 		nächsten/vorherigen Eintrag im aktuellen Fenster wählen
volume -/+		Eine Seite hoch/runter im aktuellen Fenster
ok			gewählte Datei ausführen / Verzeichnis wechseln im aktuellen Fenster / Archiv zum Lesen öffnen
1			Eigenschaften (Rechte) von gewählter Datei anzeigen/ändern
2			gewählte Datei umbenennen
3			gewählte Datei anzeigen
4			gewählte Datei bearbeiten
5			gewählte Datei von aktuellem Fenster ins andere Fenster kopieren
6			gewählte Datei von aktuellem Fenster ins andere Fenster verschieben
7			neues Verzeichnis in aktuellem Fenster erstellen
8			gewählte Datei löschen
9			neue Datei in aktuellem Fenster erstellen
0			symbolischen Verweis zur gewählten Datei im aktuellen Verzeichnis des anderen Fensters erstellen
rot			linux Kommando ausführen
grün			Datei markieren/Markierung aufheben
gelb			Sortierung der Einträge im aktuellen Fenster umkehren
blau			Ansicht aktualisieren
mute			Transparenzmodus wechseln
Menü			Hauptmenü aufrufen
info			Ein-Fenster-Ansicht an/ausschalten

in Mitteilungsfenstern:

links/rechts		Auswahl ändern
ok			Auswahl bestätigen
rot/grün/gelb		Auswahl ändern

in Texteingabe:

links/rechts		Position wechseln
hoch/runter		Zeichen wechseln
ok			bestätigen
volume +		neues Zeichen einfügen
volume -		Zeichen entfernen
rot			Eingabe löschen
grün			in Markierungsmodus wechseln
gelb			Wechseln zwischen Gross und Kleinbuchstaben
blau			Text aus Zwischenablage einfügen
0..9			Zeichenauswahl im "SMS-Stil" ( wie in der Enigma Texteingabe)

in Markierungsmodus:

links/rechts		Position wechseln
ok			markierten Text in Zwischenablage übernehmen
Exit			Markierungsmodus verlassen

in Eigenschaften:

hoch/runter		Auswahl ändern
ok			Recht gewähren/entziehen
rot			Änderungen bestätigen
grün			Änderungen verwerfen


in Editor:

links/rechts		Seite zurück/vor
hoch/runter		Zeile zurück/vor
ok			Zeile bearbeiten
volume +		Sprung zur 1. Zeile
volume -		Sprung zur letzten Zeile
rot			Zeile löschen
grün			Zeile einfügen
blau			Umwandeln einer DOS/Win Textdatei in Linux-Format
3			Starten/Beenden des Markierungsmodus
5			Markierte Zeilen kopieren
6			Markierte Zeilen verschieben
8			Markierte Zeilen löschen

in Viewer:

ok, rechts		nächste Seite
links/rechts		Seite zurück/vor
hoch/runter		Zeile zurück/vor
volume +		Sprung zur 1. Zeile
volume -		Sprung zur letzten Zeile

in Taskmanager:

ok, rechts		nächste Seite
links/rechts		Seite zurück/vor
hoch/runter		Zeile zurück/vor
volume +		Sprung zur 1. Zeile
volume -		Sprung zur letzten Zeile
rot			Prozess beenden 

in Suchergebnis:

links/rechts		Seite zurück/vor
hoch/runter		Zeile zurück/vor
volume +		Sprung zur 1. Zeile
volume -		Sprung zur letzten Zeile
ok			zur Datei springen

in Hauptmenü:

hoch/runter		Menüpunkt wählen
links/rechts		Einstellung ändern
ok			Menüpunkt ausführen

in allen Dialogen: 

Exit			Dialog verlassen



Farben:
------------
Hintergrund: 
schwarz : aktuelles Verzeichnis hat nur Lesezugriff
blau    : aktuelles Verzeichnis hat Lese/Schreibzugriff

Dateiname:
weiss : Eintrag ist Verzeichnis
orange: Eintrag ist Verweis
gelb  : Eintrag ist ausführbar
grau  : Eintrag hat Schreibzugriff
grün  : Eintrag hat Lesezugriff



Tastaturbelegung für USB-Tastaturen:
------------------------------------
exit			Esc
volume+/-	PgUp/PgDn
OK				Enter
rot				F5
grün			F6
gelb			F7
blau			F8
dream			F9
info			F10
mute			F11

Tastaturbelegung für Dbox2-Tastaturen:
--------------------------------------
home			Esc
volume+/-	PgUp/PgDn
OK				Enter
rot				F1
grün			F2
gelb			F3
blau			F4
dbox			F5
?				F6
mute			F7

Um eine Ziffer mit der Dbox2-Tastatur direkt einzugeben, 
ist die entsprechende Zifferntaste in Verbindung mit der Alt-Taste zu drücken. 
Die Sonderzeichen bei den Zifferntasten (²³{[]}\) erhält man über Ziffer und ALTGR-Taste.

Nutzung des Passwortschutzes:
-----------------------------
Wenn man ein Passwort vergeben hat (im Hauptmenü),
dann wird beim Starten des Plugins dieses Passwort abgefragt.
Die Passwortabfrage kann wieder gelöscht werden, indem einfach ein leeres Passwort gesetzt wird.
Wenn man das Passwort vergessen hat, kann man durch Löschen der Datei /etc/tuxbox/tuxcom.conf das Passwort wieder löschen.


