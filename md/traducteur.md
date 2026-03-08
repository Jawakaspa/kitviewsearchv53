
traducteur.md


Je viens de me rendre compte que la traduction est totalement désordonnée avec des bugs un peu partout et on va donc reprendre le sujet à 0 en créant traducteur.py.

Tout d'abord fini les fallbacks; traducteur utilise exclusivement le glossaire pour toutes les traduction. 
Sauf s'il faut traduire glossaire.csv ou qu'on spécifie --deepl et dans ce cas on traduit avec deepl.
Le principe de la traduction c’est d’avoir systématiquement des fichiers avec les 12 colonnes de langue  fr;en;de;es;it;ja;pt;pl;ro;th;ar;cn à compléter plus un certain nombre d’autres colonnes à ne pas toucher.

Les fichiers doivent au moins avoir une colonne fr. Toutes les autres colonnes de langue seront créées si nécessaire.

Par exemple les fichiers .csv suivants 
- glossaire le glossaire général.
- tests/qpat100.csv Ce fichier n'est pas dans le répertoire refs/ par défaut et il faut donc le spécifier.



en pj glossaire.csv qui contient l'ensemble des termes déjà traduits et comporte les colonnes : fr;en;de;es;it;ja;pt;pl;ro;th;ar;cn 
- 12 colonnes avec comme nom le code de la langue concernée : fr pour français, en pour anglais, etc... Quand on supportera d'autres langues on rajoutera d'autres colonnes.
aucune ligne ne doit jamais être détruite.

Usage :
python traducteur.py ou python traducteur.py -h affiche les présents cas d'usage
python traducteur.py glossaire.csv traduit les cases non traduites de glossaire en utilisant deepl. C'est le seul cas où on utilise deepl car il faut bien créer un fichier de référence. Compatible avec l'option -t ou avec une langue comme de, en etc... en paramètre. Exemples :
python traducteur.py glossaire.csv -t10
python traducteur.py glossaire.csv -t15 en
python traducteur.py glossaire.csv de



python traducteur.py "phrase"  ptfr → traduit la phrase de pt vers fr avec glossaire mot à mot ce qui donnera un résultat hybride mélant mots traduits dans la langue cible et mots non traduits dans la langue d'origine.
python traducteur.py "phrase"   → traduit la phrase de Auto vers fr avec glossaire mot à mot ce qui donnera un résultat hybride mélant mots traduits dans la langue cible et mots non traduits dans la langue d'origine.
python traducteur.py "phrase"  frpt --deepl  → traduit la phrase de fr vers pl avec deepl ce qui donnera un résultat avec tout traduit en pt mais sans glossaire métier orthodontique.
python traducteur.py fichier.csv   → Traduit la colonne fr en créant toutes les colonnes de langue manquantes si nécessaire. Et en remplissant les cases non traduites avec le glossaire. 
python traducteur.py fichier.csv  de --deepl → Traduit la colonne fr vers la colonne de en créant les colonnes de langue manquantes si nécessaire. Et en remplissant les cases non traduites avec deepl. C'est une bonne pratique de faire cette opération après celle de traduction par défaut avec le glossaire pour remplir les cases non trouvées. 
python traducteur.py -t N fichier.csv → Mode test (ne traduit que les N premières lignes. si N non fourni on prend N=5)


Fonctionnement : quand une expression doit être traduite de fr vers une langue xx, on va voir dans le glossaire si elle est référencée en colonne source (fr en général) qui contient des termes en français avec accents et signes diacritiques en minuscules.

Si elle est référencée on va regarder la colonne xx pour voir si la traduction existe et dans le cas contraire on met à jour la colonne en utilisant exclusivement le glossaire ou DeepL si option --deepl ou qu'on traduit le glossaire. 


Par exemple si tailleur est en colonne fr et n'a pas été traduit dans la colonne en on mettra taylor dans la colonne en.

Dans le cas contraire on crée la ligne avec :
- dans la colonne fr l'expression en français tailleur
- et dans la colonne en l'expression traduite taylor