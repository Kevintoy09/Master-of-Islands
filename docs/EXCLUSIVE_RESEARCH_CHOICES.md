# Système de Choix Exclusifs pour les Recherches

## Vue d'ensemble

Ce document décrit le système de **choix exclusifs** implémenté pour les spécialisations de recherche. Certaines recherches appartiennent à un `exclusive_group`, ce qui signifie que **seule l'une d'entre elles peut être débloquée** par joueur.

---

## Architecture

### Fichiers modifiés

| Fichier | Modifications |
|---------|--------------|
| `server/data/research.json` | Remplacement de `scierie_perfectionnee` par `recolte_papyrus` |
| `server/app/business/research_service.py` | Ajout de la validation des groupes exclusifs dans `can_unlock_research()` |

### Flux de validation

```
1. Joueur clique sur "Débloquer" (ResearchPage.tsx)
   ↓
2. Appel API POST /api/research/unlock/<player_id>/<research_id>
   ↓
3. research_service.unlock_research() appelle can_unlock_research()
   ↓
4. Vérification du exclusive_group :
   - Si joueur a déjà une recherche du même groupe → REFUS
   - Sinon → Suite des vérifications (prérequis, coûts)
   ↓
5. Message d'erreur affiché via alert() si échec
```

---

## Groupes Exclusifs Définis

### Niveau 7 : Spécialisations Âge de Pierre (`"specialisation_pierre"`)

| ID | Nom | Effet |
|----|-----|-------|
| `carrieres_avancees` | Carrières Avancées | +25% production pierre |
| `recolte_papyrus` | Récolte de Papyrus | +25% production papyrus |
| `forge_primitive` | Forge Primitive | +25% production fer |

**Coût :** 150 points de recherche + 75 or  
**Prérequis :** `architecte`

### Niveau 5 : Spécialisations Science (`"specialisation_science"`)

| ID | Nom | Effet |
|----|-----|-------|
| `mathematiques` | Mathématiques | (voir research.json) |
| `philosophie` | Philosophie | (voir research.json) |

### Niveau 8 : Alchimie du Fer (`"alchimie_fer"`)

| ID | Nom | Effet |
|----|-----|-------|
| `medecine` | Médecine | (voir research.json) |
| `astronomie_avancee` | Astronomie Avancée | (voir research.json) |

---

## Code Backend : Validation

### `research_service.py` - can_unlock_research()

```python
# Vérifier les groupes exclusifs
exclusive_group = research_data.get("exclusive_group")
if exclusive_group:
    # Charger toutes les recherches pour trouver celles du même groupe
    all_research_data = self.data_manager.load_research()
    all_research_list = all_research_data.get("researches", [])
    
    for other_research in all_research_list:
        other_research_id = other_research.get("id")
        if (other_research.get("exclusive_group") == exclusive_group and 
            other_research_id in unlocked_research and 
            other_research_id != research_id):
            other_name = other_research.get("name", other_research_id)
            return {
                "can_unlock": False,
                "reason": f"Vous avez déjà choisi '{other_name}'. Les spécialisations sont exclusives : vous ne pouvez en choisir qu'une seule."
            }
```

---

## Format JSON : research.json

```json
{
  "id": "recolte_papyrus",
  "level": 7,
  "name": "Récolte de Papyrus",
  "age": "Pierre",
  "description": "Spécialisation : améliore grandement la production de papyrus.",
  "cost": { "research_points": 150, "gold": 75 },
  "prerequisites": ["architecte"],
  "effect": { "resource_bonus": { "papyrus": 25 } },
  "category": "economy",
  "exclusive_group": "specialisation_pierre"
}
```

### Champs clés

- **`exclusive_group`** : Identifiant du groupe (ex: `"specialisation_pierre"`)
- **`effect.resource_bonus`** : Bonus appliqué au niveau **joueur** (toutes les villes)

---

## Bonus au Niveau Joueur

### Stockage

Les bonus sont stockés dans `players.json` :

```json
{
  "id": "player123",
  "username": "John",
  "unlocked_research": ["conservation", "architecte", "recolte_papyrus"],
  "research_effects": {
    "resource_bonuses": {
      "papyrus": 25
    }
  }
}
```

### Application Automatique

Dans `game_logic.py`, la fonction `calculate_total_production_rate()` lit les bonus depuis `player.research_effects.resource_bonuses` :

```python
# Bonus de recherche (niveau joueur)
resource_bonuses = player.get("research_effects", {}).get("resource_bonuses", {})
research_bonus_percent = resource_bonuses.get(resource, 0) / 100.0
total_production *= (1 + research_bonus_percent)
```

**Résultat :** Le bonus s'applique automatiquement à **TOUTES les villes du joueur**, présentes et futures.

---

## Messages d'Erreur

### Message de conflit exclusif

```
Vous avez déjà choisi 'Carrières Avancées'. Les spécialisations sont exclusives : vous ne pouvez en choisir qu'une seule.
```

Ce message apparaît via `alert()` dans `ResearchPage.tsx` ligne 176.

### Autres messages d'erreur

- "Prérequis manquants: architecte"
- "Ressources insuffisantes: research_points: 150 (disponible: 50)"
- "Recherche déjà débloquée"

---

## Tests

### Test automatique (test_exclusive_research.py)

```bash
python test_exclusive_research.py
```

**Résultats attendus :**
```
✅ Débloquer 'carrieres_avancees' (pierre +25%)
❌ Tenter de débloquer 'recolte_papyrus' → Bloqué (même groupe)
❌ Tenter de débloquer 'forge_primitive' → Bloqué (même groupe)
✅ Nouveau joueur peut débloquer 'recolte_papyrus'
```

### Test manuel

1. **Ouvrir le jeu** et se connecter
2. **Accéder au Centre de Recherche**
3. **Débloquer "Carrières Avancées"** (niveau 7)
4. **Tenter de débloquer "Récolte de Papyrus"**
5. **Vérifier** : Message d'erreur apparaît, recherche reste verrouillée

---

## Dépendances

### Recherches de niveau 8+

La recherche `irrigation` (niveau 8) requiert maintenant **l'une des 3 spécialisations** :

```json
"prerequisites": ["carrieres_avancees", "recolte_papyrus", "forge_primitive"]
```

**Implémentation :** Le joueur doit avoir **au moins une** de ces recherches (logique OR).

---

## Ajout de Nouveaux Groupes Exclusifs

### Étapes

1. **Définir le groupe** dans `research.json` :
   ```json
   {
     "id": "nouvelle_recherche_1",
     "exclusive_group": "nouveau_groupe"
   }
   ```

2. **Aucune modification backend requise** : La validation est générique

3. **Tester** avec le script de test modifié

### Exemple : Ajout d'un 4e choix niveau 7

```json
{
  "id": "exploitation_cereales",
  "level": 7,
  "name": "Exploitation Céréalière",
  "exclusive_group": "specialisation_pierre",
  "effect": { "resource_bonus": { "cereal": 25 } }
}
```

Le système bloquera automatiquement l'accès si le joueur a déjà choisi `carrieres_avancees`, `recolte_papyrus` ou `forge_primitive`.

---

## Avantages du Système

### ✅ Choix stratégiques

Les joueurs doivent choisir leur spécialisation avec soin (pas de retour en arrière).

### ✅ Diversité des builds

Encourage des stratégies différentes (pierre, papyrus, fer).

### ✅ Extensible

Facile d'ajouter de nouveaux groupes exclusifs sans modifier le code.

### ✅ Validation serveur

Impossible de contourner via manipulation frontend (sécurité).

---

## Améliorations Futures

### ✅ 1. UI pour les groupes exclusifs (IMPLÉMENTÉ)

Badge visuel ajouté dans `ResearchPage.tsx` :

```tsx
{research.exclusive_group && (
  <div className="exclusive-choice-badge">
    ⚠️ Choix exclusif
  </div>
)}
```

### ✅ 2. Confirmation avant déblocage (IMPLÉMENTÉ)

Popup de confirmation native avec `window.confirm()` :

```tsx
const confirmed = window.confirm(
  `⚠️ ATTENTION : Choix exclusif !\n\n` +
  `Vous êtes sur le point de débloquer "${research.name}".\n\n` +
  `Ce choix est DÉFINITIF et bloquera les autres options : ${otherChoicesNames}\n\n` +
  `Voulez-vous continuer ?`
);
```

### ✅ 3. Affichage des recherches exclues (IMPLÉMENTÉ)

Les autres recherches du même groupe sont automatiquement grisées et affichent :
- Badge "🔒 Bloqué"
- Message : "🔒 Bloqué car vous avez choisi "Carrières Avancées""
- Effet visuel avec `filter: grayscale(70%)` et opacité réduite

### 4. Historique des choix

Stocker dans `players.json` :

```json
"exclusive_choices": {
  "specialisation_pierre": "recolte_papyrus",
  "specialisation_science": "mathematiques"
}
```

---

## Conclusion

Le système de choix exclusifs est **opérationnel, complet et extensible**. Il ajoute une couche stratégique au système de recherche avec une UX claire et intuitive.

### ✅ Résumé des changements

**Backend :**
- ✅ Validation exclusive_group dans `research_service.py`
- ✅ Remplacement `scierie_perfectionnee` → `recolte_papyrus`
- ✅ Bonus appliqués au niveau joueur (toutes les villes)
- ✅ Messages d'erreur clairs et informatifs

**Frontend :**
- ✅ Badge "⚠️ Choix exclusif" sur les recherches
- ✅ Confirmation avant déblocage avec détails des autres options
- ✅ Verrouillage visuel des autres choix après sélection
- ✅ Message "🔒 Bloqué car vous avez choisi X"
- ✅ Effet visuel grayscale + opacité réduite
- ✅ Icône 🔒 en overlay sur les recherches bloquées

**Corrections de données :**
- ✅ Nettoyage des bonus incorrects dans `players.json`
- ✅ Bonus pierre maintenant à 25% (au lieu de 125%)

**Tests :**
- ✅ Validation automatique passante
- ✅ Vérification manuelle des bonus joueurs

**Nettoyage effectué :**
- ✅ Suppression du système `unlocked_buildings` (inutilisé)
- ✅ Suppression des fichiers de test (test_tutorial_api.py, test_reward.py, test_research_system.py)
- ✅ Nettoyage de tous les joueurs dans players.json

**Autres recherches avec bonus joueur :**
- ✅ **Irrigation (niveau 8)** : +30% production céréales sur toutes les villes
  - Prérequis : Une des 3 spécialisations niveau 7
  - Application automatique via game_logic.py

### 🎮 Expérience Utilisateur

1. **Avant le choix** : Badge orange qui pulse pour attirer l'attention
2. **Pendant le choix** : Popup de confirmation avec avertissement clair
3. **Après le choix** : Autres options grisées avec message explicite

Le système est maintenant **production-ready** ! 🚀
