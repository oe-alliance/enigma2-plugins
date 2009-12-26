====================================================
Elektro Power Save for Dreambox 7025 
Version 1 & 2 by gutemine
Version 3 by Morty <morty@gmx.net>
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
3.3.5 Italian translation updated	  
====================================================
The English Documentation follows the German one 
====================================================

1) Voraussetzung
----------------
Power Save sollte auf den meisten Systemen mit Enigma2
funktionieren. Muss aber nicht.
DM7025 + DM8000: Wird unterstützt.
DM800: Kann nicht alleine aufwachen, wird daher nicht
wirklich unterstützt.

2) Installation
---------------

Zuerst kopiert das elektro*.ipk File vom  auf /tmp mit 
ftp (TCP/IP muss natürlich schon funktionieren). 

Wenn Ihr ein Image geflashed habt, das ein Blue 
Pannel hat könnt Ihr damit mit Manual Install das
ipk file installieren.

Wenn nicht, dann installiert elektro mit folgenden 
Kommandos im Telnet:

cd /
ipkg install /tmp/elektro*.ipk

Damit Elektro zuverlässig funktioniert muss die Box 
neu gestartet werden. 


3) Funktionsweise
-----------------

Das Elektro Power Save Plugin sorgt dafür, zu die Box
zu bestimmten Zeiten in den Ruhezustand (Deep Standby)
heruntergefahren wird. Dies passiert nur, wenn sie
sich in Standby befindet und keine Aufnahme läuft
oder in den nächsten 20 Minuten gestartet wird.

Zu Aufnahmen und nach Ende der Ruhezeit wacht die Box
von alleine wieder auf, so dass man nicht ewig warten
muss, bis sie Bereit ist.

4) Optionen
-----------
Hauptmenü -> Erweiterungen -> Elektro Power Save

 - Elektro Power Save aktivieren
   Aktiviert das Plugin
   
 - Nach dem Booten in den Standby
   Geht nach dem Booten in den Standby
   
 - Nach dem manuellen Booten in den Standby
   Soll nach einem manuellen Bootvorgang in den 
   Standby gegangen werden? Die Box geht nach 
   einem manuellen Bootvorgang erst in der nächsten
   den Ruhezeit in den Ruhezustand, selbst wenn
   diese Option aktiviert ist.
   Diese Option wird nur ausgewertet, wenn "Nach 
   dem Booten in den Standby" aktiviert ist.
   
 - In-den-Standby-Bildschirm Anzeigezeit
   Stellt ein wie lange die Stanby-Abfrge angezeigt
   wird. Dieser Wert kann erhöht werden um sicher zu
   stellen, dass sich die Box während der Ruhe-Zeit 
   nicht zu schnell wieder abschaltet.
   
 - Erzwinge Ruhezustand
   Erzwingt den Ruhezustand auch, wenn die Box nicht
   im Standby ist. Auf Aufnahmen hat dies keinen Ein-
   fluss.
   
 - Nicht aufwachen
   Die Box wacht nach dem eine der Ruhe-Zeit nicht von
   alleine auf.
   
 - Urlaubsmodus
   Die Box geht immer schlafen, wenn nicht gerade
   aufgenommen wird.
   
 - Die nächste Tag beginnt um und sostige Zeiten
   Soll die Box Montag Nacht um 1 in den Ruhezustand,
   ist es genau genommen schon Dienstag. Damit dies
   trotzdem möglich ist, muss angegeben werden wann 
   der nächste Tag anfängt.
   Der Rest ist hoffentlich selbsterklärend.
   



====================================================
Viel Spass mit dem Stromsparen und Umweltschützen
mit dem Elektro Plugin auf der Dreambox 7025 !!!!
====================================================


1) Prerequisites
----------------

Should work on most systems using Enigma2, but this 
isn't granted.
DM7025 + DM8000: Supported.
DM800: Can not wake up by itself. It therefore isn't
really supported.

2) Installation
---------------

First copy the elektro*.ipk file from elektro*.zip
to /tmp with ftp (TCP/IP must be working already). 

If you have flashed an image that offer in Blue 
Pannel Manual Addon Install you can use this 
functionality to install the ipk file.

If not, then install Elektro by entering the 
following commands in a Telnet session:

cd /
ipkg install /tmp/elektro*.ipk

To ensure proper operation of Elektro please reboot
the box. 


3) Mode of operation    
--------------------
The Elektro Power Save Plugin puts the box from 
stand by to sleep mode (Deep Standby) at certain 
times. This only happens if the box is in standby
and no recording is running or sheduled in the 
next 20 minutes.

The box automatically wakes up for recordings or
at the end of the sleep time. You therefore don't
have to wait until it is on again.

4) Optiones
-----------
Main menu -> Extensions -> Elektro Power Save

 - Enable Elektro Power Save
   Enables the Plugin.
   
 - Standby on boot
   Puts the box in standby after boot.  
   
 - Standby on manual boot
   Whether to put the box in standby when booted
   manually. On manual boot the box will not go
   to sleep until the next sleep intervall eaven
   when this is turned on.
   This option is only evaluated if Standby on
   boot is turned on.  
   
 - Standby on boot screen timeout
   How long to show the standby on boot screen.
   This value can be encreased to ensure the box
   does not shut down again to quickly during
   sleep times.
   
 - Force sleep 
   Forces sleep, even when not in standby. This
   has influence on sheduled recordings.
   
 - Dont wake up
   Do not wake up at the end of the sleep time.
   
 - Holiday mode
   The box goes to sleep when not recording   
   
 - Next day starts at and other times
   If the box is supposed to go to sleep Monday night
   at 1 it is actually already Thuesday. To make this
   nonetheless possible, it must be known when the
   next day Starts.
   Hopefully the rest is self-explanatory. 


======================================================
Have Fun to let Elektro Save Power and the 
Environment with your Dreambox 7025 !!!!
======================================================
