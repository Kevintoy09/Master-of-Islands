# 🔍 Audit du Système de Quêtes Quotidiennes

## ⚠️ Problèmes Identifiés

### 🔴 Problème Majeur : Valeurs Absolues vs Changements Quotidiens

Plusieurs quêtes quotidiennes mesurent des **valeurs absolues** (totaux cumulés) au lieu de **changements quotidiens** (croissance depuis minuit).

---

## 📊 Analyse Quête par Quête

### ✅ Quêtes Correctes (Mesurent l'accumulation quotidienne)

| ID | Titre | Type | Méthode | ✅ Statut |
|---|---|---|---|---|
| `eco_collect_wood` | Bûcheron | Collecte ressource | `update_resource_collection_quests()` | **CORRECT** - Incrémente à chaque tick |
| `eco_collect_stone` | Tailleur de Pierre | Collecte ressource | `update_resource_collection_quests()` | **CORRECT** - Incrémente à chaque tick |
| `eco_collect_marble` | Carrier de Marbre | Collecte ressource | `update_resource_collection_quests()` | **CORRECT** - Incrémente à chaque tick |
| `eco_collect_glass` | Maître Verrier | Collecte ressource | `update_resource_collection_quests()` | **CORRECT** - Incrémente à chaque tick |
| `eco_produce_gold` | Trésorier | Production or | `update_resource_collection_quests()` | **CORRECT** - Accumule la production d'or |
| `eco_build_buildings` | Architecte | Construction | `update_construction_quest()` | **CORRECT** - Compte les constructions terminées |
| `eco_transport_resources` | Transporteur | Transport | Manuel (API transport) | **CORRECT** - Compte les transports effectués |
| `eco_donate_sites` | Philanthrope | Dons | Manuel (API donation) | **CORRECT** - Compte les dons effectués |
| `eco_trade_resources` | Marchand | Commerce | Manuel (API marché) | **CORRECT** - Compte les échanges |
| `mil_recruit_units` | Recruteur | Recrutement | `barracks_api.py` | **CORRECT** - Compte les unités recrutées |
| `mil_attack_barbarians` | Fléau des Sauvages | Attaques | Manuel | **CORRECT** - Compte les attaques |
| `mil_deploy_army` | Stratège | Déploiement | Manuel | **CORRECT** - Compte les déploiements |
| `sci_unlock_research` | Chercheur | Recherche | Manuel | **CORRECT** - Compte les technologies débloquées |
| `sci_upgrade_academy` | Maître de l'Académie | Amélioration | `update_construction_quest()` | **CORRECT** - Compte les améliorations |

### ❌ Quêtes PROBLÉMATIQUES (Utilisent des valeurs absolues)

#### 1. **eco_reach_population** - Croissance Démographique 👥

**Description** : "Augmentez la population de votre ville"

**Comportement actuel** :
```python
# Dans tick_service.py, ligne 395
max_population = 0
for city in cities:
    if city.get('owner') == player_id:
        pop = city.get('resources', {}).get('population_total', 0)
        max_population = max(max_population, pop)

quest_service.update_quest_progress(
    username=username,
    quest_id='eco_reach_population',
    set_value=int(max_population)  # ❌ Valeur ABSOLUE !
)
```

**Problème** :
- Mesure la **population totale** actuelle au lieu de la **croissance depuis minuit**
- Si un joueur a 100 de population à minuit, et 105 à midi, il a fait +5 de croissance
- Mais le code affiche 105/50 (target 1 étoile), ce qui est faux !

**Comportement attendu** :
- À minuit : Population = 100 → Progression = 0
- À midi : Population = 105 → Progression = +5 (croissance depuis minuit)
- Objectif 1★ : +10 de population dans la journée

---

#### 2. **sci_accumulate_research_points** - Savant 📚

**Description** : "Accumulez des points de recherche"

**Comportement actuel** :
```python
# Dans tick_service.py, ligne 402
research_points = int(player.get('research_points', 0))
quest_service.update_quest_progress(
    username=username,
    quest_id='sci_accumulate_research_points',
    set_value=research_points  # ❌ Valeur ABSOLUE !
)
```

**Problème** :
- Mesure le **total de points de recherche** au lieu de l'**accumulation quotidienne**
- Si un joueur a 50 PR à minuit et en gagne 10 dans la journée, il devrait avoir une progression de 10, pas 60

**Comportement attendu** :
- À minuit : PR = 50 → Progression = 0
- Dans la journée : PR = 60 → Progression = +10 (points gagnés depuis minuit)
- Objectif 1★ : Gagner +20 PR dans la journée

---

#### 3. **sci_reach_research_level** - Érudit 📖

**Description** : "Investissez massivement dans la recherche"

**Type dans config** : `reach_research_points_invested`

**Comportement actuel** :
```python
# Dans tick_service.py, ligne 404
for quest_id in ['sci_reach_research_level', 'sci_accumulate_research_points']:
    quest_service.update_quest_progress(
        username=username,
        quest_id=quest_id,
        set_value=research_points  # ❌ Même problème
    )
```

**Problème** : Même problème que `sci_accumulate_research_points`

**Note** : Il y a une confusion entre deux quêtes :
- `sci_accumulate_research_points` (Savant) - Accumuler des PR
- `sci_reach_research_level` (Érudit) - Investir dans la recherche

Les deux utilisent actuellement la même valeur absolue, ce qui est incorrect.

---

### ⚠️ Quêtes à Vérifier (Basées sur des statistiques cumulées)

#### 4. **mil_win_battles** - Vainqueur 🏆

**Description** : "Remportez des victoires au combat"

**Comportement actuel** :
```python
# Dans quest_service.py, ligne 714
if username and quest_id == 'mil_win_battles':
    current_progress = self._get_player_stat(username, 'victories')
    quest_progress['progress'] = current_progress
```

**Problème potentiel** :
- Utilise le **total de victoires** (stat cumulative `victories` dans players.json)
- Pour une quête **quotidienne**, devrait mesurer les victoires **du jour uniquement**

**Question** : Est-ce que l'objectif est :
- Option A : Avoir X victoires au total (stat cumulative) → Mauvais pour quête quotidienne
- Option B : Gagner X victoires aujourd'hui (delta quotidien) → Correct pour quête quotidienne

---

#### 5. **mil_kill_units** - Chasseur d'Ennemis 💀

**Description** : "Éliminez des unités ennemies"

**Comportement actuel** :
```python
# Dans quest_service.py, ligne 716
elif username and quest_id == 'mil_kill_units':
    current_progress = self._get_player_stat(username, 'total_units_killed')
    quest_progress['progress'] = current_progress
```

**Problème potentiel** :
- Utilise le **total d'unités tuées** (stat cumulative `total_units_killed`)
- Pour une quête **quotidienne**, devrait mesurer les unités tuées **du jour uniquement**

---

## 🔧 Solution : Système de Snapshot Quotidien

Pour mesurer correctement les **changements quotidiens**, il faut :

### 1. Sauvegarder un snapshot à minuit (génération des quêtes)

```json
{
  "daily_quests": {
    "generated_date": "2026-01-04",
    "initial_snapshot": {
      "population_max": 100,
      "research_points": 50,
      "victories": 5,
      "units_killed": 120
    },
    "quests": [...]
  }
}
```

### 2. Calculer le delta lors de l'update

```python
# Au lieu de set_value=current_value
current_value = get_current_population()
initial_value = snapshot.get('population_max', 0)
delta = current_value - initial_value

quest_service.update_quest_progress(
    username=username,
    quest_id='eco_reach_population',
    set_value=delta  # ← DELTA quotidien
)
```

---

## 📋 Résumé des Corrections Nécessaires

| Quête | Problème | Solution |
|---|---|---|
| `eco_reach_population` | Utilise population totale | Mesurer la croissance depuis snapshot |
| `sci_accumulate_research_points` | Utilise PR totaux | Mesurer l'accumulation depuis snapshot |
| `sci_reach_research_level` | Utilise PR totaux | Mesurer l'accumulation depuis snapshot |
| `mil_win_battles` | Utilise victoires totales | Mesurer les victoires depuis snapshot |
| `mil_kill_units` | Utilise unités tuées totales | Mesurer les kills depuis snapshot |

---

## 🎯 Impacts

### Quêtes Affectées : 5 sur 19 quêtes quotidiennes
- 3 quêtes économiques/recherche (population, PR)
- 2 quêtes militaires (victoires, kills)

### Changement de Logique
- **Avant** : "Atteindre X population" (objectif absolu)
- **Après** : "Gagner +X population aujourd'hui" (croissance quotidienne)

### Compatibilité
- ⚠️ Nécessite une migration ou un reset des quêtes quotidiennes
- ✅ Les joueurs auront de nouvelles quêtes fraîches à minuit

---

**Date d'analyse** : 4 janvier 2026  
**Analysé par** : GitHub Copilot  
**Priorité** : HAUTE - Impact significatif sur l'expérience des quêtes quotidiennes
