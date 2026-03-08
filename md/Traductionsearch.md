Traduction par search

search est le module d'entrée qui doit convertir une demande dans une langue donnée en français

La première chose qu'il doit faire c'est de déterminer la langue si on est en mode auto. La langue utilisée est donc le résultat de cette détermination faite par deepl.

Si une langue a été choisie c'est cette langue qui doit être utilisée.


Ensuite il faut bien se rappeler que le but c'est à partir de la question formulée dans une langue donnée faire le lien avec notre référentiel de tags et d'adjectifs associés.

Tu ne fais pas de traduction classique, tu fais de la résolution sémantique vers un référentiel métier.

C'est pourquoi cette résolution ne va pas utiliser d'outil de traduction mais un référentiel qui s'appelle glossaire.csv et qui a la structure suivante en n'affichant que les colonnes utiles :
type;fr;en;de;es;it;ja;pt;pl;ro;th;ar;cn

type=a pour adjectif, pa pour pattern adjectif, t pour tag, pt pour pattern tag, g pour age, c pour commun, z pour ne pas traduire et o pour object non classé.

les autres colonnes sont des colonnes de langues.

Dans les colonnes il y a des expressions de plusieurs mots ou d'un mot avec différents genres et nombre. Voire des mots directement repris de l'anglais comme over bite considéré comme français dans la colonne fr. Ou encore des fautes d'orthographe.

Rien de grave : tout ce petit monde doit faire de la résolution sémantique vers nos référentiels métier, à savoir tags et adjectifs. Le cas des ages est un peu spécifique car la traduction mot à mot des termes de type g semble suffisante comme résolution.

Pour résoudre pas besoin de coefficients compliqués comme dans une approche traditionnelle. J'ai choisi de traiter dans l'ordre de longueur décroissante pour éviter d'essayer de résoudre béance avant béance latérale par exemple.
Ce qu'il faut donc faire c'est :

- déterminer la langue de la question. C'est celle qui a été choisie par l'utilisateur ou déterminée par deepl. Dans notre exemple ce sera "de" par exemple.
- utiliser ensuite les colonnes fr et de de la manière suivante :
	- trier par longueur de de décroissante et mettre dans un dictionnaire de;fr. Il y aura donc 11 dictionnaires à créer au lancement de server.py s'il y a un serveur ou au lancement de search.py mais uniquement pour la langue détectée si search.py est utilisé en mode cli.

Ensuite on remplace dans la question toutes les expressions détectées dans ce dictionnaire qu'on parcourt dans le sens de la longueur décroissante de la colonne de en gardant la trace des mots qui sont les mots originaux de la question.
A la fin de cette phrase on a une question en petit nègre mêlant des expressions résolues qui sont en français et les mots originaux restant en allemand. C'est cette question qu'on va afficher dans la trace et passer à trouve pour la détermination des tags, angles, adjectifs et âges. 

Une fois que trouve a répondu et qu'on a renvoyé la réponse à la page web ou affichée en cli c'est le moment de traiter les mots originaux restants.
Pour cela on va créer ou mettre à jour un nouveau référentiel appelé chutier.csv. 
Il aura les colonnes suivantes :
langue;mot;nb

Langue contiendra de dans notre exemple. Mot le mot original restant et nb le nombre de fois où ce mot est resté lors des différentes utilisations. 
Si la ligne identifiée par le couple langue;mot n'existe pas on crée la ligne. Dans le cas contraire on incrémente nb

Et une fois qu'on a traité tous les mots on affiche "chutier màj" &  la liste des mots originaux traités séparés par des virgules.

Mets à jour search et server.




- 