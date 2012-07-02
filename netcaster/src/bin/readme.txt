Diese Software ist BETA. Daher können und werden Fehler auftreten, die Enigma2 komplett zu Absturz bringen! Beachte dies bei der Benutzung. Die entstehenden Chrashlogs brauchen nicht zu DMM gesendet werden!

Anleitung
---------
1. Beschreibung
2. Format der Config-Datei
3. bekannte Problem


##########################################
1.Beschreibung
Mit diesem Plugin für Enigma2 ist es dir möglich, Webradios und SHOUTcast.com über E2 zu hören. Derzeit sind nur Streams im MP3-Format abspielbar. Keine wave, ogg, wma , quicktime oder sonstige Dateien. In der Configdatei können die zu hörenden Streams als Favorit gespeichert werden. Diese tauchen dann unter 'LIST' auf. Zum Abspielen eines Stream, diesen in der Liste markieren und 'PLAY' drücken. Zum Stoppen dementsprechend auf 'STOP'. Über die blaue Taste gelangt man in eine Liste der bei NETcast.com gelisteten Musik-Genres. Die in dieser Liste mit OK ausgewählte Liste wird nach vorhanden und abspielbaren Streams durchsucht und anschließend im Browser als Liste angezeigt und sind über den bekannten Weg abspielbar. Jeder dieser Streams kann über das Menü unter der Menü-Taste der Favoritenliste hinzugefügt werden. Über das Menü können Streams in der Favoritenliste auch wieder entfernt werden.

##########################################
2. Format der Config-Datei
Jeder Stream besteht aus einer Sektion [STREAMNAME] und den Options url und description. Dabei kann der STREAMNAME nur einmal vergeben werden.

Beispiel:
[www.dreampowerradio.de]
url = http://dpr.gmc.to:64000/stream
description = die Internet Lokal-Radio Station fuer die Dreamgemeinde

##########################################
3. bekannte Problem
Da dieser Streamsupport sehr rudimentär verwirklich ist, kann es zu E2-Crashes kommen. Zum Einem durch ein Abreißen des Streams, das E2 nicht mitbekommt. Zum Anderen können momentan keine streams in Mono abgespielt werden. Wenn man soeinen abspielt, isses mit E2 bis zum Neustart vorbei. Dadurch kann es auch kommen, das E2 nicht auf Fernbediehungseingaben nicht mehr reagiert. Dann hilft nur einweder ein manueller Eingriff via Telnet oder ein kompletter Neustart!

##########################################
Viel Spaß und gute Unterhaltung mit dem NETcaster!


