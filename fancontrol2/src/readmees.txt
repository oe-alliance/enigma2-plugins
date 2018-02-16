===========================================================
FanControl2 by joergm6                          Ayuda V.2.7

Agradecimientos: diddsen, _marv_, DreamKK, Lukasz S.
                 Spaeleus(it), mimi74(fr), Bschaar(nl)
===========================================================
Pedimos disculpas en caso de que la traducción del original
no sea del todo correcta.

   Función
   --------
Controlar un ventilador de 3 o 4 pins (PWM) dependiendo 
de la temperatura media de las 2 temperaturas más altas.
La regulación no es instantánea, ya que los cambios de temperatura 
no son bruscos, lo que permite no sobrecargar la CPU.

* PWM: 
  Se puede regular la velocidad de un ventilador conectando al electroimán 
  un voltaje por pulsos en lugar de un voltaje constante.
  Los pulsos de voltaje se convierten en "empujones" al electroimán, y al
  reducir el tiempo que se está aplicando fuerza sobre el electroimán,
  se reduce efectivamente la velocidad del mismo. Estos pulsos de señales
  se conocen como señales PWM ("Pulse Width Modulation").

   Funciones de seguridad
   ----------------------
Si no se recibe ninguna lectura del ventilador durante 20 min, se asume 
que el ventilador es defectuoso. Periódicamente aparecerán mensajes 
en la pantalla de TV avisando de ello.
Si en reposo el ventilador está apagado, éste arrancará cuando se supere
la temperatura máxima. Si la temperatura cae más de 3ºC, el ventilador 
volverá a apagarse. Durante los primeros 10 min, el ventilador funciona
a la mínima velocidad.
La protección de sobrecalentamiento se puede incrementar hasta 9ºC
Puede ser configurada para apagar el receptor, a qué temperatura, y
por fallo del ventilador.

   Preferencias
   ------------
   Apagar ventilador en reposo
si = el ventilador se apagará si el receptor está en reposo
si, excepto en grabaciones o HDD = En reposo, el ventilador se apagará
     si no hay grabaciones y el HDD también está en reposo.

   Velocidad mínima
Esta velocidad se configura en la opción "Temperatura estática".

   Velocidad máxima
Esta velocidad se configura en la opción "Temperatura final".

   Temperatura estática
Hasta que esta temperatura no se ha regulado, se ajusta la velocidad
mínima.

   Temperatura final
Esta es la temperatura máxima admisible. Si se alcanza, se ajustará 
a la velocidad máxima

   Voltaje y PWM iniciales
Cuando estos valores se cambian, el ventilador se ajusta inmediatamente 
con los nuevos valores, de este modo puede leer la velocidad directamente 
y el controlador vuelve a estar activo una vez más.
Estos valores se ajustan cuando el receptor arranca, o si el ventilador
estaba parado en reposo.
  
   Ventiladores de 3 pin
Regulación del voltaje de un ventilador de 3 pin con señal de tacómetro 
(rpm).
Se controla sólo el voltaje. Los ajustes de PWM no surten efecto.
Ajusta el voltaje inicial para un valor de rotación del ventilador
al arrancar el receptor. En este arranque se regula la velocidad.

   Ventiladores de 4 pin
Regulación por PWM de un ventilador de 4 pin. Inicialmente se controla 
el valor PWM. Si este control no fuera suficiente, si es posible, 
también se regulará el voltaje.
La regulación de tensión es necesaria. Ajuste el voltaje a su valor
máximo, aunque una tensión menor también es normal. Un voltaje menor
significa unas velocidades máxima y mínima inferiores. Ajuste el voltaje
tanto como sea posible para que el control por PWM sea suficiente.
También hay ventiladores en los que ajustar PWM = 0 es demasiado alto.
Es necesario reducir el voltaje hasta que se alcance la velocidad mínima 
deseada (incluyendo 0). También hay que tener en cuenta la velocidad 
máxima. PWM proporciona un valor que corresponde a la velocidad inicial
del ventilador en el arranque del receptor. Se regula a partir de aquí

   Ventiladores de 4 pin (PID) -- by Lukasz S.
El voltaje y PWM se controlan automáticamente por un controlador PI,
el cual trata de mantener la velocidad deseada calculada por el algoritmo 
y minimizar las diferencias entre la velocidad deseada y la actual.

En en.wikipedia.org/wiki/PID_controller se ofrece una explicación 
de la teoria de control; En esta implementación sólo se utilizan 
las secciones Proporcional e Integral (pero no la Derivativa).

   Características:
Basado en la banda muerta de entrada(*), se asegura que el controlador 
no  actuará a menos que la velocidad deseada difiera de la actual en más
de un 1% (en más o en menos), para filtrar los picos y fluctuaciones 
en las mediciones de la velocidad real del ventilador.

* Banda muerta de entrada:
  Una 'banda muerta' (también llamada 'zona neutra') es un intérvalo de 
  una señal o banda donde no ocurre ninguna acción (el sistema está 'muerto')
  La banda muerta se utiliza en reguladores de voltaje y otros controladores.

De este modo, el Control de Errores de PID (su %) muestra por qué 
el controlador cree que debe acelerar (o ralentizar) el ventilador.

El ventilador se controla primero por PWM (manteniendo el voltaje en su
ajuste mínimo) variando progresivamente el voltaje sólo si PWM es mayor
que 255; Si posteriormente el PWM calculado baja de 255, el voltaje 
vuelve a ajustarse al mínimo. (en efecto, el voltaje se trata como 
desbordamiento, con un coeficiente distinto para prevenir los cambios 
de tensión demasiado grandes).

   Configuración:

La tensión y PWM iniciales se ajustarán de modo que el ventilador tenga
exactamente la mínima velocidad deseada, y se configurará en la opción
'Velocidad minima (rpm)'. (para prevenir conflictos con el controlador PI
en los ajustes de voltaje y pwm, cambie al modo tradicional de 4 pin, o
utilice la función 'Comprobar')

(En el receptor del autor, el ajuste inicial de Voltaje y PWM al valor cero 
no detenía el ventilador: la velocidad mínima configurando 0 Volt y 0 PWM
era de aprox. 850 rpm.)

'Velocidad máxima (rpm)' debería ajustarse a la máxima velocidad deseada,
admisible por el ventilador, Y QUE SEA ADMISIBLE por los valores disponibles
de voltaje y PWM. Configurar esta opción a un valor incorrecto puede 
dar lugar a un comportamiento errático.

   Problemas conocidos: 
   * cruzando los límites del control PWM - VLT, se puede ver que es inestable
por las diferentes reacciones al controlar el ventilador por voltaje o
sólo por PWM. Entorno de trabajo: ajuste la temperatura estática de modo
que PWM no llegue a 255 en condiciones normales, o que el Voltaje no necesite
caer por debajo del mínimo configurado.
(Procedimiento de ejemplo:arranque FanControl2 cuando el receptor se encuentre
en la que pueda ser considerada una temperatura normal de funcionamiento,
y si el PWM mostrado está cercano a 255, pero en la zona PWM, ajuste la
temperatura estática a uno o dos grados más alta que el ajuste actual; 
si el voltaje ya está siendo controlado y está cerca del ajuste mínimo de volt.
configure la Temperatura Estática un grado o dos MÁS que el ajuste actual
- para asegurar que la salida del controlador está notablemente por debajo
de 255 en PWM, y notablemente por encima del voltaje mínimo).
Desafortunadamente, no hay mucho que se pueda hacer, a menos que se utilice
algún automatismo para afinar esto, ya que puede diferir entre ventiladores,
e incluso entre receptores. Incluso, con el transcurso del tiempo, puede
variar la respuesta del ventilador al controlador, a causa del desgaste.
Esta planeado trabajar en el reconocimiento de situaciones de desgaste.
   
   * Si la temperatura estática se cambia, el controlador se reinicializa, 
empieza desde 0 para prevenir un apagado demasiado largo, y tiene el efecto 
de ajustar al mínimo el voltaje y PWM, ralentizando el ventilador al mínimo.
En este momento esto es una característica, no un problema, aunque probablemente
se hará configurable.
   
   * El control de errores de PID mostrando el error, puede llevar a engaño
cuando se muestren valores negativos; Esto está siendo estudiado para
encontrar un gráfico que pueda mostrar 0 en el centro, y el valor leído,
a ambos lados, en positivo o en negativo.

-- by Lukasz S.

   Control del ventilador deshabilitado
La regulación está deshabilitada. El ventilador gira con los parámetros
mas antiguos y no se apaga.

   Comprobar
   ---------
Intenta determinar la velocidad mínima del ventilador en el arranque y
la mínima antes de que el ventilador se detenga.
De modo parecido, se determina la velocidad máxima para estos ajustes.
(OK) significa que los valores coinciden con los ajustes 
(!!) los valores no coinciden, aunque estos detalles son sólo informativos
y no afectan los reglajes.
4 pin se mostrará añadido a la información del control. Esto significa
que está en la zona de PWM pero que también ha cambiado el voltaje.

   Monitor de temperatura
   ----------------------
Con la tecla 'Info' se pueden mostrar los valores individuales de las
temperaturas.
Pulse la tecla Info para tener una lectura sencilla de la temperatura
del HDD.

   Ajustes Especiales
   ------------------
Con la tecla 'Menú' se pueden definir valores especiales.
Acción en caso de fallo del ventilador           [mostrar info]
  Notificar un ventilador defectuoso, apagar el receptor, o no hacer nada.
Apagar receptor en temperatura (ºC)              [65]
  Una vez se alcance la temperatura especificada, el receptor se apagara
  (reposo profundo)
Aumentar protección de sobrecalentamiento en (ºC) [0]
  Si el ventilador se apaga en reposo, se pondrá en marcha en la máxima
  temperatura. Esta temperatura máxima puede ser aumentada hasta 9ºC
Leer temperatura del HDD en reposo               [auto]  
  si = lee la temperatura del HDD en reposo 
  no = lee la temperatura del HDD sólo cuando éste está activo
  Auto = en el arranque de FC2 una vez comprobado WETHER el HDD, se inicia,
         y de este modo la lectura se deshabilita
  nunca = La temperatura nunca se lee
Deshabilitar el control de ventilador DMM        [No]
  Se muestra en los skins con temperatura, el control de ventilador DMM
  está activo y también conmuta el ventilador. Es causa de inicios/paradas 
  inesperados. Recomendación: Deshabilitar el control DMM
Mostrar monitor en 'Extensiones'                 [Si]
  El monitor se muestra en el menú de extensiones (pulsación en la tecla azul).
Entradas de log en WebIF                         [40] 
  Cuántos eventos se mostrarán en el WebIf.
  40-999
Ruta de Logs
  Configura la carpeta destino donde se guardarán los archivos de log.
  Los datos se escribirán sólo si hay, al menos, 10MB libres.
Habilitar log de datos
  Cada minuto se grabará en el archivo FC2data.csv, que puede ser leido
  directamente en Excel. Si el archivo no existe y se habilita la opción,
  se generará una cabecera. Aumenta unos 4KBytes cada hora.
Autoborrado de datos anteriores a (dias)         [No]
  Los datos de log anteriores a esta definición se borrarán.
  Inicio: diariamente a las 00:00 y en el inicio de Enigma2
Habilitar el log de eventos
  Se escribirán todos los eventos en el archivo FC2events.txt.
  Aumenta unos 30KBytes cada hora.
  
   Web Interface
   -------------
URL: http://ip_del_receptor/fancontrol
Muestra información acerca del estado actual del ventilador y los últimos
eventos. Se muestra un valor de temperatura y velocidad por hora.
Con "FC2 log", los archivos de log se descargan y se puede ajustar el logging
"FC2 Chart" muestra gráficos de las últimas 48 h. Deberá habilitarse
el log de datos para poder acceder a esta función y debe contener, al menos,
2.5 horas de datos.
Si se utiliza Firefox, puede ocurrir que el gráfico no se muestre correctamente.
Será necesario, en este caso, refrescar la página (F5).

   Miscelánea
   ----------
Lo más importante de las lecturas del ventilador aparece como valor
y como gráfico de barras. El rango de barras mostrado está basado en
los parámetros individuales. Fancontrol2 está preparado para diferentes
idiomas, y la plantilla POT se encuentra disponible en el paquete ipkg
para poder ser traducido.
Los ajustes se guardan en los ajustes habituales de Enigma2 y también
se guardan/restauran con las copias de seguridad.


===========================================================

