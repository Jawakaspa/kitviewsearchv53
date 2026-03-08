# FORMAT JSON CIBLE UNIFIÉ (Version finale)









{
    "langue": "fr",
    "listcount": "COUNT|LIST",
    "criteres": [
        {
            "type": "count",
            "detecte": "combien",
            "label": "Comptage demandé"
        },
        {
            "type": "tag",
            "detecte": "beance gauche severe",
            "canonique": "béance",
            "label": "Béance",
            "sql": {"colonne": "canontags", "operateur": "=", "valeur": "beance"},
            "adjectifs": [
                {
                    "detecte": "gauche",
                    "canonique": "gauche", 
                    "sql": {"colonne": "canonadjs", "operateur": "=", "valeur": "gauche"}
                },
                {
                    "detecte": "severe",
                    "canonique": "sévère",
                    "sql": {"colonne": "canonadjs", "operateur": "=", "valeur": "severe"}
                }
            ]
        },
        {
            "type": "sexe",
            "detecte": "femme",
            "label": "Féminin",
            "sql": {"colonne": "sexe", "operateur": "=", "valeur": "F"}
        },
        {
            "type": "age",
            "detecte": "moins de 30 ans",
            "label": "Moins de 30 ans",
            "sql": {"colonne": "age", "operateur": "<", "valeur": 30}
        }
    ],
    "residu": "mots non reconnus",
    "question_originale": "Combien de femmes de moins de 30 ans avec béance gauche sévère ?",
    "question_standardisee": "combien de femmes de moins de 30 ans avec beance gauche severe"
}
