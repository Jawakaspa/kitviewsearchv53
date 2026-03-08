# Prompt Doc_pipeline V1.0.0 - 08/12/2025 17:39:00

# Doc_pipeline.md

## 

1. ## Voici le pipeline :

tagssaisis.csv (saisie manuelle)
      │
      ▼ (transformation structure)
tagsfr.csv (type;frtags;stdfrtags;fradjs;stdfradjs)
      │
      ▼ fr2tags.py (internationalisation)
tags.csv (type;frtags;stdfrtags;fradjs;stdfradjs;entags;stdentags;enadjs;stdenadjs;...)
      │
      ▼ tags2synta.py (génère les 2 fichiers lookup)
      │
      ├──► syntags.csv (stdtag;canontag;langue)
      │
      └──► synadjs.csv (stdadj;canonadj;langue;canontag)
