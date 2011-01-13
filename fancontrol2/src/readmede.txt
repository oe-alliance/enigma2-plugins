===========================================================
FanControl2 by joergm6                          Hilfe V.2.4
Support-Forum: IHAD
Danksagungen: diddsen, _marv_, DreamKK
              Spaeleus(it), mimi74(fr), Bschaar(nl)
===========================================================

   Funktion
   --------
Steuerung eines 3pin Lüfter oder 4pin (PWM) Lüfter abhängig
von dem Durchschnitt der 2 höchsten Temperaturwerte.
Geregelt wird langsam, da sich Temperaturen auch nicht
schnell ändern und keine unnötige CPU-Belastung auftreten
sollte.

   Sicherheitsfunktionen
   ---------------------
Meldet der Lüfter 20min keine Drehzahl wird davon ausgegangen,
daß der Lüfter defekt ist. Regelmäßig wird auf dem TV dann eine
entsprechende Meldung angezeigt.
Wird im Standby-Modus der Lüfter ausgeschaltet, erfolgt bei
überschreiten der eingestellten Maximaltemperatur ein Einschalten
des Lüfters. Fällt die Temperatur um mehr als 3C schaltet
dieser wieder aus. Der Lüfter läuft in den ersten 10min mit
minimaler Drehzahl.
Der Überhitzungsschutz kann um bis zu 9C vergrößert werden.
Es kann eingestellt werden ob die Box herunterfährt, bei
welcher Temperatur und bei Lüfterausfall.

   Einstellungen
   -------------
   Lüfter aus im Standby
Ja = Lüfter wird ausgeschaltet wenn die Box sich im Standby
befindet
Ja, außer bei Aufnahme oder HDD = Lüfter wird im Standby
ausgeschaltet wenn keine Aufnahme läuft und HDD in Sleep-Mode ist.

   min Drehzahl
Bei Temperatur "Ruhe-Temperatur" und darunter wird diese
eingestellte Drehzahl eingeregelt.

   max Drehzahl
Bei Temperatur "Ende-Temperatur" und darüber wird diese
eingestellte Drehzahl eingeregelt.

   Ruhe Temperatur
Bis einschließlich dieser Temperatur wird nicht geregelt
und die min Drehzahl ist eingestellt.

   Ende Temperatur
Das ist die maximale Temperatur die auftreten darf, ist
diese erreicht, wird die maximale Drehzahl eingestellt.

   Anfangs-Spannung und -PWM  
Bei Änderungen an diesen Werten wird sofort auch der
Lüfter darauf eingestellt. Es kann nun direkt das
Ergebnis über die Drehzahl ermittelt werden. Die
Regelung setzt aber trotzdem sofort wieder ein, also
schnell schauen oder Werte laufend verändern.
Diese Werte werden eingestellt, wenn die Box startet bzw.
wenn der Lüfter im Standby ausgeschaltet war.
  
   für Lüftertyp 3pin
Für die Regelung spannungsgesteuerter 3poliger Lüfter
mit Tachosignal. Gesteuert wird nur die Spannung.
Einstellungen bei PWM haben keinen Einfluss.
Stellt die Anfangsspannung auf einen Wert, der der
Drehzahl entspricht, mit dem der Lüfter beim Start der Box
anfänglich laufen soll. Ab dieser Drehzahl wird geregelt. 

   für Lüftertyp 4pin
Für die Regelung pulsweitenmodolierter (PWM) 4poliger
Lüfter. Gesteuert wird zuerst der PWM Wert. Reicht der
Regelbereich nicht mehr aus, wird wenn möglich auch die
Spannung geregelt. Die Spannungseinstellung ist notwendig.
Stellt die Spannung auf den Maximalwert (bei DM500HD auf
5-10). Aber auch ein geringerer Spannungswert ist sinnvoll.
Eine geringere Spannung bedeutet eine geringere maximale
Drehzahl sowie eine geringere minimale Drehzahl. Setzt die
Spannung möglichst so, das der Regelbereich mit PWM ausreicht.
Es gibt Lüfter die auch bei PWM=0 nach zu hoch drehen.
Verringert hier die Spannung bis die gewünschte min
Drehzahl (auch 0 möglich) erreicht wird. Habt aber auch
die sich verringernde max Drehzahl im Auge.
Stellt PWM auf einen Wert, der der Drehzahl entspricht,
mit dem der Lüfter beim Start der Box anfänglich laufen
soll. Ab dieser Drehzahl wird geregelt. 

   für Lüftertyp Steuerung aus
Die Regelung ist deaktiviert. Der Lüfter läuft mit den
letzten Parametern weiter. Der Lüfter wird NICHT
ausgeschaltet!

   Prüfen
   ------
Hier wird versucht, die minimale Drehzahl des Lüfters
für den Anlauf bei stehenden Lüfter und die minimale
Drehzahl bevor der Lüfter abschaltet zu ermitteln.
Ebenso wird die maximale Drehzahl für diese Einstellungen
ermittelt. (OK) bedeutet Wert passt zu den Einstellungen
bei (!!) passen die Einstellungen nicht zu den vom
Lüfter erreichbaren Werten. Diese Angaben dienen der Info
und beeinflussen nicht die Regelung innerhalb des
Möglichen.
Für 4Pin werden zusätzlich Angaben über den erweiterten
Regelbereich angezeigt. Das bedeutet, es wird über den
PWM-Bereich hinaus auch die Spannung verändert. 

   Temperatur-Monitor
   ------------------
Mit der "Info-Taste" können die Einzelwerte der Temperaturen
angezeigt werden.
Drücke die Info-Taste zum einmaligen Auslesen der HDD-Temperatur.

   Spezial-Setup
   -------------
Mit der "Menu-Taste" können spezielle Werte definiert werden.
Aktion bei Lüfterausfall            [zeige Information]
  Meldung bei defekten Lüfter, Box herunterfahren oder nichts
  machen.
Box herunterfahren bei Temperatur (C) [65]
  Bei Erreichen der definierten Temperatur wird die Box
  ausgeschaltet (DeepStandby).
Überhitzungsschutz erhöhen um (C)   [0]
  Ist der Lüfter aus im Standby wird diese bei erreichen der
  maximalen Temperatur eingeschaltet. Diese maximale Temperatur
  kann um bis zu 9C vergrößert werden
HDD-Temperatur im HDD-Standby-Modus lesen [auto]
  Ja = Temperatur der HDD auch im HDD-Standby lesen
  Nein = Temperatur der HDD nur lesen wenn aktiv
  Auto = beim Start von FC2 wird einmal getestet ob die HDD
         anläuft und wenn ja wird das Auslesen deaktiviert
  niemals = kein Auslesen der HDD Temperatur
DMM-FanControl deaktiviert          [Nein]
  Wird in Skins die Temperatur mit angezeigt, ist die DMM-
  Lüftersteuerung auch aktiv und schaltet ebenfalls den Lüfter.
  Es entstehen ungewollte Ein/Ausschaltvorgänge.
  Empfehlung: DMM-Fancontrol deaktivieren  
Zeige Monitor im Erweiterungsmenü   [Ja]
  Monitor im Erweiterungsmenü (Lang-Blau-Taste) anzeigen.
Anzahl der WebIF-Log-Einträge       [40]
  Wieviele Ereignisse sollen im WebIF angesehen werden können.
  40 - 999
Logging Verzeichnis
  Wähle mit "OK" den Ort, wohin die Log-Dateien geschrieben
  werden solle. Daten werden nur geschrieben wenn mindestens
  noch 10MByte frei sind.
Aktiviere Data Logging
  Es wird jede Minute ein Datensatz in die Datei FC2data.csv
  geschreiben. Diese kann z.B. direkt in Excel aufgerufen
  werden. Ist diese Datei nicht vorhanden und wird diese
  Option aktiviert, wird auch eine Kopfzeile erzeugt.
  ca. 4kByte je Stunde
Auto-Löschen Daten älter als (Tage) [Nein]
  Data-Logging-Daten die älter als diese Angabe sind, werden
  gelöscht.
  Ausführung: täglich 00:00 und bei Enigma2-Start
Aktiviere Ereignis Logging
  Es wird jedes FC2-Ereignis in die Datei FC2events.txt
  geschrieben.
  ca. 30kByte je Stunde

   Web-Interface
   -------------
Aufruf: http://dreamboxip/fancontrol
Zeigt Information zu den aktuellen Lüfterwerten und die letzen
Ereignislogs an. Je Stunde wird ein Wert für Temperatur und
Drehzahl angezeigt.
Mit "FC2 Log" können die Logging-Dateien heruntergeladen werden
und das Logging eingestellt werden.
"FC2 Chart" zeigt Online-Diagramme der letzten 48h. Das Data-
Logging muss dazu aktiviert sein. Es müssen für mindestens 2.5h
Daten vorhanden sein!
Bei Nutzung von Firefox kann es vorkommen, daß das Diagramm
nicht ordnungsgemäß angezeigt wird. Dann ist eine zusätzliche 
Seitenaktualisierung (F5) notwendig.

   Sonstiges
   ---------
Alle für den Lüfter wichtigen aktuellen Messwerte werden
als Wert und Balkendiagramm angezeigt. Der Balkenanzeige-
bereich basiert auf die eingestellen Parameter.
FanControl2 ist für verschiedene Sprachen vorbereitet.
POT-Datei ist im ipkg wenn Jemand andere Sprachen zur
Verfügung stellen möchte.
Die Einstellungen werden bei den normalen Enigma2-Settings
abgelegt und sind somit im Backup/Restore enthalten.


===========================================================
