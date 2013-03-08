===========================================================
FanControl2 by joergm6                          Hilfe V.2.4
Support-Forum: IHAD
Danksagungen: diddsen, _marv_, DreamKK
              Spaeleus(it), mimi74(fr), Bschaar(nl)
===========================================================
 Przeproszam,jezeli engielski przeklad nie jest calkowicie poprawny.
(celowo sa pominiete polskie znaki)
   
   Funkcje
   --------
Kontrola 3pinowego lub 4pinowego wentylator (PWM) zalezna od
sredniej dwoch najwyzszych temparatur.
Regulacja nastepuje w wolnym tepie, gdyz temperatura tez nie
zmienia sie gwaltownie i unikamy w ten sposob 
niepotrzebnego obciazenia procesora CPU.

##############################################################
   Funkcje bezpieczenstwa
   ---------------------
Jesli wentylator nie poda predkosci obrotow w ciagu 20 min. 
bedzie on uwazany za uszkodzony i bedzie sie pojawial odpowiedni
kumunikat na ekranie telewizora.
Jesli w trybie gotowosci bedzie wentylator wylaczony i bedzie 
przekroczona maksymalna temperatura - zostanie wentylator wlaczony. 
Jesli temperatura spadnie o wiecej niz 3°C zostanie on znow 
wylaczony.
Wentylator pracuje w pierwszych 10 minutach na minimalnej
predkosc.
Ochrona przed przegrzaniem moze byc zwiekszona nawet o 9°C.
Mozna tez ustawic czy Box ma sie wylaczyc i przy jakiej
temperaturze bac awarii wentylatora.

##############################################################
   Ustawienia
   -------------
   Wentylator wylaczony w trybie gotowosci
Tak = wentylator jest wylaczony, gdy Box jest w stanie gotowosci
Tak, z wyjatkiem podczas nagrywania na HDD = wentylator wylaczony 
w trybie czuwania, gdy nie nagrywamy i dysk jest w trybie uspienia.

   Predkosc min.
Temperatura jest "temperatura gotowosci" i ponizej jej
ustawienia predkosci obrotow regulacji.

   Predkosc max.
Temperatura jest "temperatura koncowa" i powyzej jej
ustawienia predkosci obrotow regulacji.

   Spokojna Temperatura
Do tej Temperatury nie bedzie regulacji
i bedzie ustawiona predkosc minimalna.

   Temperatura koncowa
Jest to maksymalna temperatura, ktora moze wystapic -gdy bedzie osiagnieta, 
bedzie ustawiona maksymalna predkosc.

   Napiecie poczatkowe i PWM
Przy zmianach tych wartosci bedzie rowniez niezwlocznie
wentylator ustawiony. Moga byc odrazu odczytane wartosci z
predkosci obrotow wentylatora.
Rozporzadzenie jest jednak natychmiastowe, a wiec
wystarczy spojrzec na obroty i wartosci mozna odrazu zmieniac.
Wartosci te sa wylaczone, gdy Box startuje lub
gdy wentylator zostal wylaczony w "trybie gotowosci".
  
   do wentylatorow typu 3pin
Napiecie sterowania wentylatora 3-pin jest ustawione
z sygnalem predkosci. Kontrolowane, tylko napiecia.
Ustawienia dla PWM nie maja kontroli.
Ustaw napiecie na jakas wartosc, ktorej obroty beda odpowiednie,
dla obrotow poczatkowych wentylatora po starcie Boxa.
Od tej predkosci beda juz obroty regulowane.

   do wentylatorow typu 4pin
Do regulacji(PWM) 4-pinowego
wentylatora. Najpierw ustawienia wartosc PWM. Jak nie
wystarcza zakres regulacji, mozna regulowac napieciem. 
Regulacja napiecia jest konieczna.
Ustaw napiecie do wartosci maksymalnej (na DM500HD
5-10). Ale takze nizsza wartosc napiecia jest znaczaca.
Nizsze napiecie oznacza nizsza maksymalna jak i
minimalna predkosc obrotow. Ustaw napiecie tak aby PWM bylo 
optymalne dla maxymalnych jak i minimalnych obrotow.
Istnieja rowniez wentylatory, ktore obracaja sie w PWM = 0 za szybko.
Zmniejszamy napiecie, az do mommentu gdzie
predkosc zostanie osiagnieta (również 0 jest mozliwe). Ale trzeba tez
miec obnizenie maksymalnej predkosci na uwadze.
PWM zapewnia wartosci odpowiadajacej predkosci obrotowej,
dla obrotow poczatkowych wentylatora po starcie Boxa.
Od tej predkosci beda juz obroty regulowane.

   dla Wentylatorow typ Ustawienia Wylaczone
Kontrola jest wylaczona. Wentylator pracuje z 
ustawionymi ostatnimi wartosciami.
Wentylator nie wylacza sie.

################################################################
    Sprawdzic
    ------
Tutaj jest proba, minimalnej predkosci wentylatora
kiedy wentylator przy minimalnym napieciu sie wylaczy.
Okreslona zostaje predkosc minimalna wentylatora.
Podobnie zostaje ustalona predkosc maksymalna
wentylatora. (OK) wartosc nie odpowiada ustawieniom
w (!!) nie pasuja do ustawienia wartosci wentylatora.
Zobacz osiagalne wartosci. Te szczegoly sa dla informacji
i nie ma to wplywu na kontrole mozliwosci.
Dla 4pinowych wentylatorow beda dodatkowe informacje pokazane,
ktore znajduja sie na "rozszerzeniach ustawien".
Zakres sterowania. Oznacza to, ze jest on w PWM-obszarze,
ponadto tez zmiane napiecia.

#################################################################
    Monitorowanie temperatury
    ------------------
Uzycie przycisku "Info" - beda wyswietlone poszczegolne informacje
temperatur Boxa.
Nacisnij przycisk "info" dla jednego odczytu temperatury HDD.

#################################################################
   Specjalne ustawienia
   -------------
Naciskajac przycisk "Menu", mozna poszczegolne wartosci zdefiniowac.
Skarga o awarii wentylatora [Pokaz Info]
  Wiadomosc o awarii wentylatora, czy ma Box sie
  wylaczyc czy nie robic nic
Box wylaczyc przy temperaturze (C) [65]
  Po osiagnieciu okreslonej temperatury, Box wylaczyc
  OFF (Deep Standby).
Przegrzanie zwiekszenie ochrony o (C) [0]
  Jesli wentylator jest wylaczony, w trybie Standby, bedzie 
  maksymalna temperatura osiagnieta - box wylaczyc.
  Ta maksymalna temperature mozna zwiekszyc do 9°C
Temperatura HDD w trybie gotowosci HDD czytac [AUTO]
  Tak = temperatura HDD czytac tez w trybie gotowosci HDD
  Nie = temperatura HDD czytac tylko gdy HDD aktywny
  Auto = przy starcie Boxa FC2 bedzie testowany tylko raz czy HDD
         uruchamia sie, i jesli tak zostanie wylaczone czytanie
  Nigdy = odczyt temperatury HDD deaktywowany - wylaczony
DMM fancontrol wylaczone [Nie]
  Pojawi sie w skorce z temperatura, DMM
  Sterowanie wentylatora aktywne, a takze wlacza wentylator.
  Beda spowodowane niechciane wlacz / wylacz propozycje.
  Zalecene: Wylacz wentylator DMM
Pokaz Monitor rozszerzenia menu [Tak]
  Obserwuj w rozszerzonym menu wyswietlacza (dlugi niebieski przycisk).
Liczba webIF wpisów  [40]
  Ile wydarzen mozna zobaczyc w webIF.
  40-999
Folder wydarzen
  Wybierz "OK", aby wybrac miejsce, w ktorym pliki wydarzen
  powinno byc zapisywane. Dane moga byc zapisywane, jezeli co najmniej
  10 MByte sa jeszcze wolne.
Wlacz rejestrowanie danych
  Kazda minuta jest zapis w FC2data.csv pliku
  zapisana. Mozna to na przyklad wywolywac bezposrednio w programie Excel.
  Jesli ten plik nie istnieje, a jest ta
  opcja wlaczona, plik bedzie generowany do
  okolo 4 kB na godzinę
Automatyczne usuwanie danych starszych niz (dni) [Nie]
  Rejestrowanie danych dane starsze niz tej liczbie
  beda usuniete.
  Wykonac: codziennie o 00:00 i przy starcie Enigmy ( GUI )
Wlacz rejestrowanie zdarzen
  Bedzie kazde zdarzenie w FC2events.txt pliku
  zapisywane.
  ok. 30kByte w kazda godzine
  
 ###############################################################
    Interfejs Web
    -------------
Wejdz na: http://dreamboxip/fancontrol
Wyswietla informacje na temat aktualnych wartosci i ostatnich
protokolach. Co kazda godzine wyswietlane zostana 
wiadomosci o wartosciach temperatury predkosciach wentylatora.
Z "FC2 Log", pliki sa pobierane i rejestrowania mozna ustawic.
"Wykres FC2" pokazuje on-line diagramy w ciagu ostatnich 48 godzin.
Logging musi byc wlaczony, aby bylo to mozliwe. Musza byc przynajmniej 
2.5h te dane dostepne!
W przypadku korzystania z przegladarki Firefox, moze sie zdarzyc, ze diagram
nie bedzie wyswietlany poprawnie. Nastepne i dodatkowe
odswiezania (F5) nie jest konieczne.

##############################################################
    Inne
    ---------
Wszystkie wentylatory wazne biezace odczyty
wyswietlane w postaci wykresu i wartosciach. 
Slupkowy wykres jest wyswietlany na podstawie parametrow.
FanControl2 jest przygotowany na rozne jezyki.
Plik POT dla ipkg - jesli ktos inne jezyki
chce udostępnic.
Ustawienia sa w normalnych Enigma2 ustawieniach
przechowywane i dlatego sa w kopii zapasowej / przywracania wlacznie.

tlumaczenie-kol.MiroMoni

===========================================================
