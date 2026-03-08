# Prompt manualhisto V1.0.0 - 23/01/2026 12:53:03

# Historique du projet Manuel Kitview

<!-- PRESENTATION_META
titre_court: "Manuel Kitview - Historique"
sous_titre: "De la conversion PDF ratée au workflow i18n complet"
duree_estimee: "15min"
niveau: "intermédiaire"
audience: "Équipe projet, développeurs, mainteneurs"
fichiers_concernes: "extractfr.py, trad.py, adapt.py, gene.py, translations.csv"
emoji_principal: "📚"
-->

**Version** : 1.0.0  
**Date** : 23 janvier 2026  
**Auteur** : Thierry / Claude

---

<!-- SLIDE
id: "contexte-initial"
titre: "Le point de départ"
template: "2colonnes"
emoji: "🎯"
timing: "2min"
-->

## 1. Contexte initial

<!-- KEY: Kitview est un logiciel de gestion multimédia pour orthodontistes, son manuel PDF de 98 pages devait être converti en aide en ligne HTML. -->

<!-- QUESTION: Pourquoi ne pas simplement distribuer le PDF aux utilisateurs ? -->

### Le besoin

- **Kitview** : logiciel de gestion de photos pour cabinets d'orthodontie
- **Manuel existant** : PDF de 98 pages en français
- **Objectif** : créer une aide en ligne HTML multilingue avec 4 niveaux de difficulté

### Les contraintes

- Manuel accessible depuis l'application (pas de PDF)
- Multilingue : FR natif + EN natif + autres langues via Google Translate
- 4 niveaux : Standard, Débutant, Intermédiaire, Expert
- Maintenance facile par une personne non technique

---

<!-- SLIDE
id: "phase1-echec"
titre: "Phase 1 : La tentative ratée"
template: "timeline"
emoji: "❌"
timing: "3min"
-->

## 2. Phase 1 : Première tentative (21-22 janvier 2026)

<!-- KEY: La conversion directe PDF → HTML en un seul bloc a échoué : trop volumineux, extraction d'images incomplète, mise en page perdue. -->

### Chronologie des échecs

**21 janvier - Tentative 1 : Conversion directe**
- Upload du PDF complet (98 pages)
- Résultat : timeout, fichier trop volumineux
- ❌ Échec total

**21 janvier - Tentative 2 : Découpage en 10 parties**
- PDF découpé en 10 fichiers de ~10 pages
- Extraction des images avec PyMuPDF
- Création progressive du HTML
- ✅ Succès partiel : structure OK, 212 images extraites

**22 janvier - Tentative 3 : Multilinguisme**
- Ajout du sélecteur de langue avec Google Translate
- Création de `kitviewmanuals_en.html` pour l'anglais natif
- ❌ Échec : traduction très incomplète (seuls quelques titres traduits)

### Problèmes identifiés

| Problème | Impact |
|----------|--------|
| Google Translate ne fonctionne pas en local | Tests impossibles sans serveur |
| Traduction par remplacement de chaînes | Très partielle, ratait la majorité du contenu |
| Bouton OK inutile dans le sélecteur | UX dégradée |
| 4 niveaux × 2 langues = 8 fichiers | Maintenance impossible |

---

<!-- SLIDE
id: "phase2-analyse"
titre: "Phase 2 : Analyse et nouvelle stratégie"
template: "schema"
emoji: "🔍"
timing: "2min"
-->

## 3. Phase 2 : Prise de recul (22 janvier 2026, soir)

<!-- KEY: Arrêt complet, analyse des erreurs, définition d'une architecture i18n classique avec extraction → traduction → génération. -->

### Décisions stratégiques

1. **Simplifier d'abord** : se concentrer sur Standard FR + EN uniquement
2. **Workflow i18n classique** : extraction, traduction, génération
3. **APIs professionnelles** : DeepL pour EN, Claude pour D/I/E
4. **Un seul fichier source** : tout dans un CSV à 10 colonnes
5. **Colonnes auto + manuel** : permettre corrections sans perdre l'automatisation

<!-- DIAGRAM
type: "flux"
titre: "Architecture retenue"
-->

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ kitviewmanuals  │     │  translations   │     │   6 fichiers    │
│     .html       │────▶│     .csv        │────▶│     HTML        │
│  (source FR)    │     │  (10 colonnes)  │     │   générés       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │
   extractfr.py            trad.py (DeepL)
                           adapt.py (Claude)
                           gene.py (génération)
```

<!-- /DIAGRAM -->

---

<!-- SLIDE
id: "phase3-implementation"
titre: "Phase 3 : Implémentation"
template: "tableau"
emoji: "🛠️"
timing: "3min"
-->

## 4. Phase 3 : Développement du workflow (23 janvier 2026)

<!-- KEY: 4 scripts Python créés en 2 heures, testés et fonctionnels, avec gestion de cache pour optimiser les coûts API. -->

### Les 4 scripts créés

| Script | API | Fonction | Cache |
|--------|-----|----------|-------|
| `extractfr.py` | - | Extrait 474 textes du HTML source | Non |
| `trad.py` | DeepL | Traduit FR → EN | Oui (JSON) |
| `adapt.py` | Claude | Adapte pour D/I/E | Oui (JSON) |
| `gene.py` | - | Génère les 6 fichiers HTML | Non |

### Structure du CSV

```
id;fr;en;EN;d;D;i;I;e;E
```

- **Minuscules** (en, d, i, e) : remplies automatiquement par les APIs
- **Majuscules** (EN, D, I, E) : corrections manuelles (prioritaires)

### Marqueurs spéciaux pour D/I/E

| Marqueur | Signification |
|----------|---------------|
| `[=]` | Identique au standard (utiliser `fr`) |
| `[X]` | Supprimé pour ce niveau |
| `[?]` ou vide | À générer |

---

<!-- SLIDE
id: "phase3-resultats"
titre: "Résultats obtenus"
template: "stats"
emoji: "📊"
timing: "2min"
-->

## 5. Résultats de la Phase 3

<!-- KEY: 474 textes extraits, traduits en anglais et adaptés pour 3 niveaux, générant 6 fichiers HTML fonctionnels. -->

### Statistiques

| Métrique | Valeur |
|----------|--------|
| Textes extraits | 474 |
| Traductions DeepL | 474 |
| Adaptations Claude | 474 × 3 = 1422 |
| Fichiers HTML générés | 6 |
| Temps de développement | ~3 heures |

### Fichiers générés

1. `kitviewmanuals.html` - Standard FR (source)
2. `kitviewmanuals_en.html` - Standard EN
3. `kitviewmanuald.html` - Débutant FR
4. `kitviewmanuali.html` - Intermédiaire FR
5. `kitviewmanuale.html` - Expert FR
6. `kitviewmanuals_ids.html` - Version technique (debug)

---

<!-- SLIDE
id: "lecons-apprises"
titre: "Leçons apprises"
template: "2colonnes"
emoji: "💡"
timing: "3min"
-->

## 6. Leçons apprises

<!-- KEY: Ne jamais sous-estimer la complexité de l'i18n, toujours séparer extraction/traduction/génération, utiliser des APIs professionnelles. -->

<!-- QUESTION: Quelle erreur de la phase 1 vous semble la plus évitable avec du recul ? -->

### Ce qui n'a PAS fonctionné

- Conversion PDF monolithique (trop gros)
- Traduction par recherche/remplacement simple
- Google Translate en local (CORS)
- Multiplication des fichiers HTML sources

### Ce qui A fonctionné

- Découpage du PDF en parties
- Workflow i18n classique (extract → translate → generate)
- Un seul CSV comme source de vérité
- Cache pour éviter les appels API redondants
- Colonnes auto + manuel (flexibilité)
- APIs professionnelles (DeepL, Claude)

---

<!-- SLIDE
id: "architecture-finale"
titre: "Architecture finale"
template: "schema"
emoji: "🏗️"
timing: "2min"
-->

## 7. Architecture finale

<!-- KEY: Un fichier HTML source, un CSV central à 10 colonnes, 4 scripts Python, 6 fichiers HTML générés. -->

<!-- DIAGRAM
type: "architecture"
titre: "Vue d'ensemble du système"
-->

```
                    SOURCES                         GÉNÉRATION
                    ───────                         ──────────
                         
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   kitviewmanuals.html ──► extractfr.py ──► translations.csv      │
│        (source FR)              │              (474 lignes)      │
│                                 │               10 colonnes      │
│                                 │                                │
│                                 ▼                                │
│                    ┌────────────────────────┐                    │
│                    │                        │                    │
│                    │   trad.py (DeepL)      │──► colonne 'en'    │
│                    │   adapt.py (Claude)    │──► colonnes d,i,e  │
│                    │                        │                    │
│                    └────────────────────────┘                    │
│                                 │                                │
│                                 ▼                                │
│                           gene.py                                │
│                              │                                   │
│              ┌───────────────┼───────────────┐                   │
│              ▼               ▼               ▼                   │
│         kitviewmanuals  kitviewmanuals  kitviewmanuald           │
│            _en.html        .html          .html                  │
│           (EN natif)    (FR vérifié)   (Débutant)                │
│                                                                  │
│              ▼               ▼               ▼                   │
│         kitviewmanuali  kitviewmanuale  kitviewmanuals           │
│            .html          .html          _ids.html               │
│        (Intermédiaire)   (Expert)      (technique)               │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

<!-- /DIAGRAM -->

---

<!-- SLIDE
id: "prochaines-etapes"
titre: "Et maintenant ?"
template: "contenu"
emoji: "🚀"
timing: "2min"
-->

## 8. Prochaines étapes

<!-- KEY: Publication sur GitHub Pages pour avoir une version en ligne fonctionnelle, puis création des versions EN des niveaux D/I/E si demandé. -->

### Court terme

- [ ] Déployer sur GitHub Pages (manuel en ligne)
- [ ] Tester Google Translate sur serveur
- [ ] Réviser les traductions/adaptations dans le CSV
- [ ] Documenter le workflow pour la maintenance

### Moyen terme

- [ ] Créer les versions EN des niveaux D/I/E
- [ ] Intégrer dans Kitview (lien depuis l'application)
- [ ] Ajouter un système de feedback utilisateur

### Long terme

- [ ] Automatiser avec GitHub Actions (CI/CD)
- [ ] Ajouter d'autres langues natives si demandé
- [ ] Créer une version PDF à partir du HTML

---

<!-- NO_SLIDE -->

## Annexe : Fichiers du projet

```
c:\cx\
├── extractfr.py           # Extraction des textes
├── trad.py                # Traduction DeepL
├── adapt.py               # Adaptation Claude
├── gene.py                # Génération HTML
├── kitviewmanuals.html    # Source FR
├── translations.csv       # CSV central (10 colonnes)
├── translations_cache.json        # Cache DeepL
├── translations_cache_claude.json # Cache Claude
└── img/                   # 212 images extraites du PDF
    ├── page05_img01.jpeg
    ├── page06_img01.jpeg
    └── ...
```

<!-- /NO_SLIDE -->

---

**Fin de l'historique**

*Document généré le 23 janvier 2026*
