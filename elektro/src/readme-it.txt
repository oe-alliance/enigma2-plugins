====================================================
Elektro Power Save prr Dreambox 
Versione 1 & 2 by gutemine
Versione 3 by Morty <morty@gmx.net>
Profili, HDD, IP, NAS Mod by joergm6
====================================================
Informazioni sulle versioni
====================================================
1.0   Prima versione, come di consueto assolutamente
      non testata - buon divertimento!
1.1   Dopo l'avvio il Dreambox viene posto
      immediatamente in standby.
1.2   Alcuni bugfix e inserita la possibilità
      di configurare lo standby all'avvio.
2.0   Realizzato il kit ipk, aggiunte info prima dello
      standby e prevenuto il deepstandby in presenza
      di timer.
2.1   Bugfix e supporto di immagini con mainloop
      TryQuit (presente in CVS da gennaio 2007).
2.2   Ci sono ancora...
2.3   Aggiornata compatibilità con CVS recenti.
      Probabilmente l'ultima versione by gutemine.
3.0   Riscrittura by Morty, introdotte nuove funzioni.
3.0.2 Persistenza schermata di shutdown configurabile.
3.0.4 Bugfix.
3.0.5 Risolto il problema dello spegnimento nel caso
      il box si avvii troppo rapidamente.
3.1.0 Rimosse dipendenze non necessarie.
      Evitato lo spegnimento su avvio manuale.      
3.2.0 Rilevazione registrazioni corretta.
      Modalità "vacanza" implementata.
3.2.1 Bugfix mancato riconoscimento riavvio da Elektro. 
3.2.2 Aggiunta la traduzione italiana by Spaeleus.     
3.2.3 Risolto il problema con auto-timer.
3.3.0 Aggiunta opzione per scegliere se porre in 
      standby su avvio manuale.
3.3.1 Risolto problema nel caso global session non
      fosse disponibile.
3.3.2 Risolto un problema di arresto sulle versioni
      recenti di enigma2.
3.3.3 Aggiunta una patch per all'installler per
      correggere enigma2. E' ora possibile utilizzare
      Elektro e EPGRefresh contemporaneamente.
3.3.4 Aggiunta la traduzione turca by MytHoLoG.
3.4.0 Nessun arresto su HDD attivo (joergm6).
3.4.1 Fix errore Multi-Language (traduzioni).
3.4.2 Interfaccia avanzata (menu configurazione).
3.4.3 2 Profili; attesa risposta indirizzo IP.
3.4.5 Possibilità di arrestare un NAS/server via Telnet.

1) Prerequisiti
----------------

Dovrebbe funzionare su tutti i sistemi che utilizzano Enigma2, 
ma non è possibilie garantirlo in assoluto.
DM7025, DM800SE  + DM8000: Compatibili.
DM800: Non è in grado di auto avviarsi. Non lo si può
pertanto considerare realmente compatibile.

2) Installazione
---------------

Se è disponibile una connessione diretta a Internet access,
Elektro può essere installato via Plugin-Browser.
O attraverso gli Addon, se l'immagine dispone di Blue Panel.

In alternativa, semplicemente copiare il file elektro*.ipk in
/tmp via FTP (TCP/IP must be working already) o da una penna
USB usando un browser file.

Quindi installarlo da "Installare estensioni locali" (Menu 
Configurazione Gestione software), oppure utilizzando i
seguenti comandi in una sessione telnet:

cd /
ipkg install /tmp/elektro*.ipk

Per assicurarsi che Elektro funzioni correttamente, riavviare
(reboot) il Dreambox. 


3) Uso    
--------------------
Il plugin Elektro Power Save gestisce il passaggio da standby
alla modalità "sleep" (Deep Standby) a orari configurabili.
Ciò avviene solo se il box si trova in modalità Standby e
non ci sono registrazioni in corso o programmate entro i 20
minuti seguenti.

Il Dreambox provvederà a riavviarsi automaticamente per
registrare o al termine del tempo di riposo prefissato.
at the end of the specified sleep time. Di conseguenza non sarà
necessario attendere per il suo avvio.

4) Opzioni
----------
Menu principale -> Estensioni -> Elektro Power Save

 - Mostrare in:
   determina se Elektro debba essere disponibile nel menu Plugin
   o in quello Estensioni (riavvio della GUI necessario).


 - Nome:
   Determina il nome da associare al plugin nel menu (riavvio
   della GUI necessario).

 - Descrizione:
   Determina la descrizione del plugin utilizzata nel menu 
   (riavvio della GUI necessario).

 - Profilo orario attivo
   Verranno utilizzati gli orari inseriti nel profilo selezionato.

 - Utilizzare entrambi i profili alternativamente
   Entrambi i profili saranno usati alernativamente. A ogni
   spegnimento il profilo attivo sarà cambiato. Ciò consente
   due cicli al giorno. Non sovrapporre gli orari.

 - Verificare IP (Ok >> modificare)
   La lista IP verrà verificata. Elektro attenderà sino a che
   gli indirizzi cesseranno di rispondere al ping.

 - Abilitare Elektro Power Save
   Non abilitando l'opzione, il plugin non potrà avviarsi
   automaticamente..
   
 - Standby all'avvio:
   Pone il box in standby dopo l'avvio.  
   
 - Standby su avvio manuale:
   Opzione per porre il box in standby dopo un avvio manuale.
   In caso di avvio manuale, il box non verrà posto in standby
   fino al successivo intervallo di deep standby, anche se
   questa opzione è stata attivata. Inoltre, l'opzione è attiva
   solo se anche la funzione standby all'avvio è stata
   opportunamente configurata.  
   
 - Timeout standby su schermata di avvio:
   Persistenza della richiesta di standby sullo schermo.
   Configurare questo valore in modo da scongiurare il rischio
   di un nuovo deep standby troppo precipitoso quando in
   modalità standby.   
   
 - Forzare spegnimento (anche se non in standby):
   Forza la modalità deep standby, anche quando non in standby.
   Le registrazioni programmate non saranno alterate.   
 
 - Evitare deep standby su attività HDD (es.: FTP):
   Attendere che l'HDD sia posto in modalità sleep.
   Attenzione: una configurazione non congruente potrebbe
   impedire del tutto la messa in deep standby.   
   
 - Non accendere:
   Non riavviare al termine del prossimo intervallo
   di deep standby.
   
 - Modalità vacanza (sperimentale):
   Porre sempre il box in deep standby, se non ci sono
   in corso registrazioni.
   
 - "Il prossimo giorno inizia alle" e altri orari:
   Se è previsto che il box entri in deep standby ad es.
   lunedì notte alla 01:00, va considerato che è
   già martedì. Per ottenere comunque il risulato previsto,
   forzare qui l'ora di inizio del nuovo giorno.   
   
   Si confida che il resto sia autoesplicativo... 


=============================================================
Buon divertimento con il risparmio energetico e la 
protezione degli apprati di Elektro nell'uso del Dreambox!!!!
=============================================================
