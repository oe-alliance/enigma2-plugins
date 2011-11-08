===========================================================
FanControl2 by joergm6                         Help V.2.4
Forum di supporto: IHAD
Ringraziamenti: diddsen, _marv_, DreamKK
                Spaeleus(it), mimi74(fr), Bschaar(nl)
===========================================================

   Funzioni
   --------
Controllo di una ventola a 3 o 4 pin (PWM), in funzione della
media delle due temperature più elevate.
Le regolazioni devono essere applicate gradatamente, dato che
le temperature cambiano lentamente ed è inutile caricare eccessivamente la CPU.

   Caratteristiche di sicurezza
   ----------------------------
Nel caso in cui per 20 minuti non dovesse essere rilevato
nessun valore circa la velocità di rotazione, il sistema 
riterrà difettosa la ventola.
In tal caso verrà visualizzato un messaggio appropriato
sulla TV.
Se la configurazione scelta prevede che ventola venga spenta
quando il decoder si trovi in standby, nel caso in cui la
temperatura dovesse raggiungere il valore massimo, la ventola
verrebbe riattivata, per essere di nuovo spenta quando la
temperatura dovesse abbassarsi più di tre gradi.
La ventola, per i primi 10 minuti, girerà alla velocità 
minima.
la temperatura di intervento può essere innalzata di un
massimo di 9 gradi.
Può essere configurato lo spegnimento automatico del box in
caso di temperatura eccessiva o avaria della ventola.

   Configurazione
   --------------
	Ventola spenta quando in standby
- Sì = quando il box viene posto in standby, la ventola viene
  sempre automaticamente spenta.
- Sì, ma non durante registrazioni o attività HDD = quando il
  box viene posto in standby, la ventola viena automaticamente
  spenta a meno che non ci siano in corso registrazioni o
  attività che coinvolgano il disco fisso.
   Velocità minima
Rappresenta la velocità di rotazione della ventola quando la
temperatura è uguale o inferiore al valore impostato come
"temperatura di riposo".
   Velocità massima
Rappresenta la velocità di rotazione della ventola quando la
temperatura raggiunge il valore impostato come "temperatura
massima".
   Temperatura di riposo
Se questo valore non vene configurato, la velocità di
rotazione della ventola sarà sempre la minima.
   Temperatura massima
Rappresenta la massima temperatura tollerata: se dovesse essere
raggiunta, la velocità di rotazione della ventola verrebbe
impostata al valore "velocità massima". 
   Voltaggio e PWM iniziali
Le modifiche apportate a questi valori saranno applicate
immediatamente, e influenzeranno direttamente tutte le altre regolazioni che dipendono da essi: i parametri mostrati rifletteranno quindi direttamente le modifiche apportate. Non sarà dunque possibile controllare i valori inseriti se non modificandoli nuovamente. Rappresentano i valori utilizzati quando il box viene avviato o attivato dallo standby.
   Ventola a 3 pin
Le ventole a 3 pin con sensore tachimetrico possono essere
controllate solo attraverso la tensione: la configurazione PWM
non ha alcuna influenza.
Configurare il valore voltaggio adeguato a ottenere la velocità
di rotazione che si intende ottimale all'accensione del box.
La velocità sarà successivamente regolata a partire da questi 
valori.
   Ventola a 4 pin
Nelle ventole a 4 pin, per prima cosa utilizzare il parametro
PWM.
Se il range di regolazioni disponibile in tal modo dovesse
rivelarsi insufficiente, è posibile intervenire anche sulla
regolazione del voltaggio.
La regolazione del parametro "voltaggio" è comunque necessaria.
Configurare il parametro al massimo valore previsto (per il
500HD impostare 5-10).
Potrebbe tuttavia rivelarsi sufficiente un valore inferiore, in considerazione del fatto che ad un voltaggio minore
corrispondono velocità massima e minima inferiori.
Configurare quindi il parametro voltaggio ad un valore che
permetta di gestire le successive regolazioni attraverso il
parametro PWM.
E' tuttavia possibile che in alcuni casi anche a PWM = 0 la
velocità di rotazione della ventola risulti eccessiva: in
questi casi agire sul voltaggio riducendolo fino a ottenere
la velocità desiderata (anche il valore 0 è consentito).
Tenere presente che questa regolazione avrà effetto anche sulla
velocità massima raggiungibile.
Configurare un valore PWM adeguato a ottenere la velocità
di rotazione che si intende ottimale all'accensione del box.
La velocità sarà poi regolata a partire da questi valori.
   Parametro tipo ventola disabilitato
Il controllo verrà disabilitato, ma la ventola non verrà
spenta!
Continuerà a funzionare secondo gli ultimi parametri
configurati prima della disabilitazione  del plugin.

   Verifica
   --------
Tramite questa funzione il plugin aiuterà a determinare
la velocità minima ideale da configurare all'avvio del box,
insieme alla massima velocità di rotazione.
Al termine dell'analisi, (OK) indicherà i parametri
correttamente configurati, mentre (!!) indicherà i parametri
che necessitano di ulteriori regolazioni.
Per le ventole a 4 pin vengono presi in considerazione anche i
parametri relativi al range di configurazioni estese proprie
delle funzioni PWM, in aggiunta a quelle relative ai voltaggi. 

   Monitoraggio temperature
   ------------------------
Tramite il pulsante "Info", vengono mostrati i valori delle
singole temperature rilevate.
Premere il pulsante Info per ottenere una lettura della
temperatura HDD

   Configurazioni speciali
   -----------------------
Tramite il tasto "Menu", è possibile configurare una serie
di parametri particolari. Tra le parentesi [ ], il valore
predefinito.
Azione da eseguire in caso di avaria della ventola:
  ["Mostrare info"], "Spegnere il box", "Non fare nulla".
Spegnimento box a temperatura di (C):
  se viene raggiunta la temperatura indicata, il box verrà
  spento automaticamente per evitare danni allo stesso.[65]
Aumento protezione termica di (C):
  Se la ventola in standby è spenta, verrà automaticamente
  riattivata nel caso la temperatura superata la temperatura
  "di riposo".
  Questo parametro aumenta il valore della temperatura
  a cui la ventola viene fatta intervenire (max. 9 gradi).[0]
Rilevare la temperatura del disco anche in standby:
  ["Automaticamente"], "Mai", "No", "Sì".
- sì   = rilevare la temperatura disco anche con HDD in stanby
- no   = rilevare la temperatura disco solo se attivo
- auto = la temperatura disco verrà rilevata all'avvio di FC2,
         per poi disabilitare la rilevazione.
Disabilitare il plugin Fancontrol by DMM:
  ["No"], "Sì".
  Disponibile di default, potrebbe interferire con questo
  plugin, causando accensioni/spegnimenti anomali della
  ventola.
  Si raccomanda di disabilitarlo.
Mostrare Monitor nel menu estensioni:
  Monitor viene inserito nel menu estensioni [Sì]
Numero di log per la WebIf:
  configura il numero di eventi che vengono presi in
  considerazione per l'interfaccia web. Range: 40-999.[040]
Percorso log:
  indica la path relativa al file di log, se abilitato.
  Il file verrà generato solo se risulteranno disponibili
  almeno 10MByte.[/media/hdd/]
Abilitare log dati:
  ["No"], "Sì". Se abilitato,   una volta al minuto, un
  record verrà   aggiunto al file FC2data.csv.
  Questo file può essere aperto direttamente da applicazioni
  come Excel.
  Se il file non esiste e l'opzione viene abilitata, un
  header sarà   generato automaticamente. Lo spazio occupato
  sarà di circa 4 kbyte ogni ora.
Rimuovere autom. dati se più vecchi di (giorni):
  i log dati più vecchi del valore indicat verranno cancellati
  automaticamente.
Abilitare log eventi:
  ["No"], "Sì". Se abilitato,  un record verrà aggiunto al
  file FC2event.txt. Lo spazio occupato sarà di circa 30 
  kbyte ogni ora.

   Interfaccia Web
   ---------------
Raggiungibile all'indirizzo: http://dreamboxip/fancontrol
Mostra informazioni relative ai valori correnti e al contenuto
dell'ultimo file di log eventi. Inoltre viene mostrato un
valore di riferimento per ogni ora relativo a temperatura
e velocità.
"FC2 Chart" mostra diagrammi relativi alle ultime 48 ore.
Per questa funzione il log dati deve essere abilitato .
Devono essere presenti dati per almeno 2,5 ore.
Utilizzando Firefox il digramma potrebbe non essere mostrato
correttamente. in tal caso premere F5 per ottenere un
aggiornamento della pagina.

   Miscellanee
   -----------
Tutte le informazioni rilevanti relative ai valori correnti
inerenti la ventola sono mostrati sotto forma di valore e
barra grafica.
La barra è dimensionata in base alla lettura del parametro
a cui si riferisce.
Fan control è pronto per supportare traduzioni nelle diverse
lingue.
Un pile .POT è incluso nella distribuzione con l'ipk, ed è
dunque diponibile per i traduttori che volessero aggiungere
altre lingue a quelle già presenti.
Le configurazioni sono memorizzate come quelle standard per
enigma2, e come tali aggiunte normalmente a eventuali
backup/ripristini.
