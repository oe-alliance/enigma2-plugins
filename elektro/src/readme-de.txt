====================================================
Elektro Power Save for Dreambox 
Version 1 & 2 by gutemine
Version 3 by Morty <morty@gmx.net>
Profiles, HDD, IP, NAS Mod by joergm6
====================================================
Release infos 
====================================================
1.0   first version, as usually completely 
      untested - have Fun !
1.1   now after boot the Dreambox will go 
      immediately to normal Standby
1.2   some bugfixes on Plugin Text and 
      make standby on boot configurable
2.0   make ipk kit, add info messages before standby 
      and prevent deepstandby if timer is running
2.1   bug fixes and support for new images with TryQuit
      mainloop (which is since mid January 2007 in CVS)
2.2   still alive 
2.3   make compatible with latest CVS changes
      probably last version by gutemine

3.0   Rewritten by Morty, lots of new features
3.0.2 It's now possible to adjust the how long to
      show the shutdown screen
3.0.4 Bugfix
3.0.5 Fixed problem where the box shuts down again
      when it boots up too fast
3.1.0 Removed unneeded dependencies
      Don't shut down if woken up manually
3.2.0 Recording detection should work now
      Holiday mode has been implemented
3.2.1 Fixed Bug not recognizing a wakeup by Elektro 
3.2.2 Added the Italian translation by Spaeleus     
3.2.3 Fixed problem with auto-Timers
3.3.0 Added an option to choose whether to go to 
      standby on manual boot
3.3.1 Fixed problem when the global session was not
      available
3.3.2 Fixed some problems shutting down on latest
	  versions of enigma2.
3.3.3 Added patch to installer to fix enigma2. It 
	  should now be possible to run Elektro and 
	  EPG refresh in parallel.
3.3.4 Added Turkish locale by MytHoLoG	  
3.4.0 no shutdown if HDD not Idle (joergm6)  
3.4.1 Fix: Multi-Language (locale) does not work 
3.4.2 Enhance user interface (configuration menu)
3.4.3 2 Profiles; waiting for responding IP addresses
3.4.5 A NAS/server can be shutdown via Telnet

1) Voraussetzung
----------------
Power Save sollte auf den meisten Systemen mit Enigma2
funktionieren. Muss aber nicht.
DM7025, DM800SE  + DM8000: Wird unterstützt.
DM800: Kann nicht alleine aufwachen, wird daher nicht
wirklich unterstützt.

2) Installation
---------------

Wenn die Dreambox einen Internet-Zugang hat, kann 
Elektro aus dem Plugin-Browser installiert werden. Oder 
mit Addons, wenn das Image ein Blue Panel hat.

Wenn nicht, dann einfach das elektro*.ipk File 
auf /tmp kopieren mit FTP (TCP/IP muss natürlich schon 
funktionieren) oder mit einem Filebrowser vom
USB-Stick.

Anschließend mit "Lokale Erweiterungen installieren"
(Menü Einstellungen Softwareverwaltung). 

Oder mit folgenden Kommandos im Telnet:
cd /
ipkg install /tmp/elektro*.ipk

Damit Elektro zuverlässig funktioniert, muss die Box 
neu gestartet werden. 


3) Funktionsweise
-----------------

Das Elektro Power Save Plugin sorgt dafür, dass die
Dreambox zu bestimmten Zeiten in den Ruhezustand (Deep 
Standby) heruntergefahren wird. Dies passiert nur, wenn 
sie sich im Standby Modus befindet und keine Aufnahme
läuft oder in den nächsten 20 Minuten gestartet wird.

Für Aufnahmen und nach Ende der Ruhezeit wacht die
Dreambox von alleine wieder auf, so dass man nicht ewig 
warten muss, bis sie bereit ist.

4) Optionen
-----------
Hauptmenü -> Erweiterungen -> Elektro Power Save

 - Zeigen in:
   Auswahl, ob Elektro im Plugin Menü oder Erweiterungs- 
   Menü gezeigt werden soll (erfordert GUI Neustart).

 - Name:
   Name, unter dem das Plugin im Menü erscheinen soll 
   (erfordert GUI Neustart).

 - Beschreibung:
   Beschreibung, mit der das Plugin im Menü erscheinen soll  
   (erfordert GUI Neustart).

 - Aktives Zeit Profil
   Die Zeiten dieses angezeigten Profiles werden verwendet.

 - Beide Profile abwechselnd verwenden
   Beide Profile werden abwechselnd eingesetzt. Beim Herunterfahren
   wird des anderen Profil aktiviert. Dieses erlaubt 2 Zeitzyclen
   pro Tag. Die Zeiten dürfen sich nicht überschneiden.

 - Teste IPs (drücke OK zum Editieren)
   Diese Liste von IP Adressen wird überprüft. Elektro wartet
   solange bis keine Adresse mehr auf Ping antwortet.
   
 - Elektro Power Save aktivieren:
   Aktiviert das Plugin
   
 - Nach dem Booten in den Standby:
   Versetzt die Box dem Booten in den Standby Modus.
   
 - Nach dem manuellen Booten in den Standby:
   Soll nach einem manuellen Bootvorgang in den 
   Standby Modus gegangen werden? Die Box geht nach 
   einem manuellen Bootvorgang nicht vor der nächsten
   Deep Standby-Zeit in den Ruhezustand, selbst wenn
   diese Option aktiviert ist.
   Diese Option wird nur wirksam, wenn "Nach 
   dem Booten in den Standby" auch aktiviert ist. 
   
 - Anzeigedauer der Abfrage "In den Standby?":
   Stellt ein, wie lange die Standby-Abfrage angezeigt
   wird. Dieser Wert kann gesetzt werden um sicher zu
   stellen, dass sich die Box während der Standby-Zeit 
   nicht zu schnell wieder abschaltet.
   
 - Erzwinge Ruhezustand:
   Erzwingt den Ruhezustand auch, wenn die Box nicht
   im Standby ist. Auf Aufnahmen hat dies keinen Ein-
   fluss.
   
 - Kein Deep Standby, wenn die HDD aktiv ist:
   Warten bis die Festplatte in den Ruhemodus geht. Je
   nach Konfiguration kann dies den Ruhezustand
   vollständig unterbinden.
   
 - Nicht aufwachen:
   Die Box wacht nach dem Ende der nächsten Ruhezeit 
   nicht automatisch auf.
   
 - Urlaubsmodus:
   Die Box bleibt immer im Deep Standby Modus, sofern 
   nicht gerade aufgenommen wird.
   
 - Der nächste Tag beginnt um und sonstige Zeiten:
   Soll die Box z.B. Montag Nacht um 1 Uhr in den Deep
   Standby gehen, ist es genau genommen schon Dienstag.
   Damit dies trotzdem möglich ist, muss angegeben 
   werden, wann der nächste Tag anfängt.
   Der Rest ist hoffentlich selbsterklärend. 


====================================================
Viel Spass mit dem Stromsparen und beim Schutz der
Umwelt durch das Elektro Plugin auf der Dreambox!!!!
====================================================
