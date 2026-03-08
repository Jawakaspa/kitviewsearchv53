## Intégrations IA potentielles

### 1. **Suggestion de recherche intelligente** (Quick Win)

Quand l'utilisateur commence à taper, l'IA pourrait suggérer des reformulations ou des recherches connexes :

- "bruxisme" → suggère aussi "grincement des dents", "usure dentaire"
- "classe 2 enfant" → suggère "classe II division 1 moins de 12 ans"

**Avantage** : améliore la découvrabilité des patients sans changer l'architecture.

### 2. **Résumé automatique de cohorte** (Valeur métier forte)

Après une recherche retournant N patients, un bouton "📊 Analyser cette cohorte" qui génère :

- Distribution par âge/sexe
- Pathologies les plus fréquentes associées
- Tendances (ex: "67% ont aussi un encombrement")

**Avantage** : transforme l'outil de recherche en outil d'analyse clinique/épidémiologique.

### 3. **Détection d'anomalies ou de cas similaires** (Aide au diagnostic)

À partir d'un patient sélectionné, l'IA trouve les cas les plus similaires dans la base :

- "Montrer des patients avec un profil similaire"
- Utile pour voir comment des cas comparables ont été traités

**Avantage** : capitalise sur l'historique de 25 000 patients comme base de connaissances.

### 4. **Enrichissement automatique des commentaires** (Amélioration continue)

Quand un praticien consulte un patient sans commentaire clinique, l'IA pourrait proposer un commentaire basé sur les pathologies détectées :

- "Ce patient présente une béance antérieure avec bruxisme. Voulez-vous générer un commentaire type ?"

**Avantage** : enrichit progressivement la base de commentaires.

### 5. **Traduction contextuelle médicale** (i18n avancé)

Au lieu de traductions génériques, l'IA pourrait traduire les commentaires cliniques en préservant la terminologie orthodontique exacte dans chaque langue.

---

## Ma recommandation

Je te suggère le **n°2 (Résumé de cohorte)** comme prochaine étape après web9 :

- Fort ROI pour un praticien/chercheur
- Réutilise l'infrastructure `/ia/ask` qu'on vient de créer
- Différenciateur fort par rapport à une simple recherche SQL
