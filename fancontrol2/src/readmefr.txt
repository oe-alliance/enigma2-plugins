===========================================================
FanControl2 par joergm6
Support forum: IHAD
Remerciements: Spaeleus, mimi74
===========================================================
Mes excuses si la traduction en français n'est pas toujours correcte.

   Fonction
   -----------
Commander un ventilateur 3pin ou 4pin (PWM) dépend de la moyenne
des 2 valeurs de la température les plus élevées.
La régulation est lente, car les températures ne changent pas
rapidement et cela permet de ne pas charger inutilement l'unité
centrale de traitement.

   Préférences
   ----------------
   Vitesse mini
A la température "température statique" et en dessous, cette
vitesse est choisie.

   Vitesse maxi
A la température "température finale" cette vitesse est choisie.

   Température statique
Jusqu'à cette température ce n'est pas régulé, la vitesse mini
est choisie.

   Température finale
C'est la température maximale qui peut se produire, quand ceci
arrive, nous choisirons la vitesse maximum.

   Au commencement, tension et PWM
En changeant ces valeurs le ventilateur est immédiatement
positionné avec ces valeurs. La lecture de la vitesse se fait
directement. Le contrôle est néanmoins de nouveau en activité.
L'examen ou le changement des valeurs sont très rapides.
  
   Pour ventilateur type 3pin
Pour la régulation du voltage du ventilateur 3-pin avec signal
tachymètre. Le voltage uniquement est contrôlé. 
Les paramètres du PWM n'ont aucun contrôle.
Positionne la tension initiale à une valeur du taux de rotation, 
avec le ventilateur au démarrage de la boîte prévu pour se lancer.
C'est régulé depuis cette vitesse de démarrage.

   Pour ventilateur type 4pin
Pour la régulation PWM du ventilateur 4-pin. La valeur PWM
seulement est contrôlée. L'ajustement de tension est exigé.
Placez la tension sur la valeur maximum.
Mais également un niveau à tension inférieure est utile.
Un voltage plus bas signifie une vitesse maxi plus basse de rotation
et une vitesse mini plus basse. Il y a également des ventilateurs
tournant à PWM = 0 qui sont trop haut.
Réduisez la tension ici, jusqu'à ce que la vitesse minimum désirée
(0 y compris est possible) soit réalisée. Ayez également la vitesse
maximum à l'esprit.
PWM fournit une valeur qui correspond à la vitesse d'initialisation
du lancement du ventilateur au démarrage de la boîte.
C'est régulé depuis cette vitesse de démarrage.

   Pour ventilateur type "sans"
La régulation est désactivée. Le ventilateur fonctionne avec les 
derniers paramètres appliqués.

   Vérification
   ---------------
Ceci essaye de déterminer la vitesse minimum du ventilateur pour
le démarrage et le minimum avant que la vitesse de l'hélice 
aille à l'arrêt.
De même, la vitesse maximum pour ces paramètres est déterminée.
(OK) cela signifie que les valeurs moyennes correspondent
au paramètres
(!!) les valeurs ne corespondent pas.

   Divers
   --------
Les plus importantes lectures actuelles apparaissent comme une
valeur ou barre analogique. L'affichage de l'échelle de la
barre est basée sur les paramètres individuellement réglés.
FanControl2 est préparée pour différents langages.
Le fichier POT est un ipkg si quelques autres langages
deviendraient disponibles.


===========================================================

