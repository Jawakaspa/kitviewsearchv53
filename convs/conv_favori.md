# Prompt conv_favori V1.0.0 - 07/01/2026 10:33:38

# Synthèse de conversation : favori

**Date de création :** 07/01/2026  
**Dernière mise à jour :** 07/01/2026 14:XX

---

## 📋 Résumé du projet

Ajout d'un système de favoris pour les patients dans Kitview Search, avec affichage d'un cœur cliquable permettant de marquer/démarquer un patient comme favori.

---

## 🕐 Historique des échanges

### 07/01/2026 14:XX - Demande initiale

**Question :** Ajout d'un nouveau tag "favori" (sans adjectif) dans tags.csv. Deux objectifs :
1. Afficher un cœur plein ou vide dans les listes au lieu du mot "favori"
2. Permettre de modifier le statut par simple clic

**Précision importante :** Le favori est un attribut de la fiche du patient, pas un favori personnel de l'utilisateur connecté.

**Fichiers fournis :** `search.py`, `web18.html`

---

### 07/01/2026 14:XX - Questions de clarification

**Questions posées par Claude :**
1. Stockage du favori en base ?
2. Endpoint API existant ou à créer ?
3. Emplacement du cœur dans l'interface ?
4. Comportement au clic (immédiat ou différé) ?
5. Accessibilité (mode condensé et/ou expanded) ?

---

### 07/01/2026 14:XX - Réponses et spécifications

**Réponses de Thierry :**

| Question | Réponse |
|----------|---------|
| Stockage | Tag dans table de jointure `patients_pathologies` + colonne `canontags` de `patients` (les deux endroits) |
| API | Endpoint générique pour toggle de tags (réutilisable) |
| Position cœur | En haut à droite de la carte (Option B) |
| Comportement clic | Mise à jour immédiate en base |
| Accessibilité | Visible et cliquable en mode condensé ET expanded |

---

### 07/01/2026 14:XX - Demande de fichiers complémentaires

**Claude demande :**
- `server.py` pour créer l'endpoint
- Structure de la table de jointure

**Thierry fournit :** `Prompt_cxchargepats.md` (structure de la base)

---

### 07/01/2026 14:XX - Création du prompt

**Décision :** La fonctionnalité est décalée. Création d'un prompt complet (`Prompt_favori.md`) pour implémentation ultérieure.

**Fichier manquant pour l'implémentation :** `server.py`

---

## 📄 Documents générés

| Fichier | Description | Statut |
|---------|-------------|--------|
| `Prompt_favori.md` | Prompt complet pour recréer la fonctionnalité | ✅ Créé |
| `conv_favori.md` | Ce fichier de synthèse | ✅ Créé |

---

## 📎 Fichiers nécessaires pour l'implémentation

| Fichier | Fourni | Nécessaire pour |
|---------|--------|-----------------|
| `web18.html` | ✅ | Modifications frontend |
| `search.py` | ✅ | Vérification retour `patient.id` |
| `Prompt_cxchargepats.md` | ✅ | Structure de la base |
| `Prompt_contexte2312.md` | ✅ | Contexte projet |
| `server.py` | ❌ À fournir | Création endpoint API |

---

## 🎯 Prochaines étapes

1. Fournir `server.py` quand la fonctionnalité sera priorisée
2. Implémenter selon `Prompt_favori.md`
3. Tester le toggle favori
4. Vérifier la recherche par tag "favori"

---

## 💡 Notes techniques

- Le tag "favori" n'a pas d'adjectif associé
- La mise à jour doit se faire à deux endroits en base :
  - Table de jointure `patients_pathologies` (pour la recherche)
  - Colonne `canontags` de la table `patients` (pour l'affichage)
- L'endpoint sera générique pour permettre l'ajout d'autres tags cliquables ultérieurement

---

**Fin de la synthèse**
