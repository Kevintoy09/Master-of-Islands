# 🔧 Correction des Quêtes Quotidiennes - Système de Snapshot

## 📋 Problème Résolu

Plusieurs quêtes quotidiennes mesuraient des **valeurs absolues** (totaux cumulés) au lieu de **changements quotidiens** (deltas depuis minuit).

### Quêtes Corrigées

| Quête | Avant | Après |
|---|---|---|
| **eco_reach_population** | Population totale (ex: 105) | Croissance depuis minuit (ex: +5) |
| **sci_accumulate_research_points** | Points de recherche totaux | Points gagnés depuis minuit |
| **sci_reach_research_level** | Points de recherche totaux | Points gagnés depuis minuit |
| **mil_win_battles** | Victoires totales | Victoires depuis minuit |
| **mil_kill_units** | Unités tuées totales | Unités tuées depuis minuit |

---

## ✅ Solution Implémentée : Système de Snapshot

### 1️⃣ Structure de Données Étendue

**Fichier** : `server/app/services/quest_service.py`

```json
{
  "daily_quests": {
    "generated_date": "2026-01-04",
    "player_level_snapshot": 1,
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

**Nouvelle clé** : `initial_snapshot` - Capture l'état des statistiques du joueur à minuit (ou génération des quêtes).

### 2️⃣ Fonction de Capture de Snapshot

**Fichier** : `server/app/services/quest_service.py`

```python
def _create_daily_snapshot(self, username: str) -> Dict:
    """
    Crée un snapshot des statistiques du joueur pour calculer les deltas quotidiens
    Retourne: {population_max, research_points, victories, units_killed}
    """
```

**Appelée** :
- Lors de la génération de nouvelles quêtes (`get_or_generate_daily_quests`)
- Lors de la régénération automatique à minuit (`regenerate_daily_quests`)

### 3️⃣ Calcul des Deltas dans tick_service.py

**Fichier** : `server/app/services/tick_service.py`

**Avant (INCORRECT)** :
```python
# ❌ Valeur absolue - Population totale
max_population = 105
quest_service.update_quest_progress(
    username=username,
    quest_id='eco_reach_population',
    set_value=int(max_population)  # 105
)
```

**Après (CORRECT)** :
```python
# ✅ Delta quotidien - Croissance depuis minuit
max_population = 105
initial_population = snapshot.get('population_max', 100)
population_delta = max(0, max_population - initial_population)  # 105 - 100 = 5

quest_service.update_quest_progress(
    username=username,
    quest_id='eco_reach_population',
    set_value=int(population_delta)  # 5 ✅
)
```

**Même logique pour** :
- Points de recherche (`sci_accumulate_research_points`, `sci_reach_research_level`)

### 4️⃣ Synchronisation Auto dans enrich_quest_data()

**Fichier** : `server/app/services/quest_service.py`

Pour les quêtes militaires qui sont mises à jour manuellement (pas à chaque tick), la synchronisation est faite lors de l'enrichissement :

```python
if quest_id == 'mil_win_battles':
    total_victories = self._get_player_stat(username, 'victories')
    initial_victories = snapshot.get('victories', total_victories)
    current_progress = max(0, total_victories - initial_victories)  # Delta quotidien
    quest_progress['progress'] = current_progress
```

---

## 🔄 Flux de Fonctionnement

### À Minuit (Génération des Quêtes)

```
1. Scheduler déclenche la régénération
2. _create_daily_snapshot() capture :
   - population_max = 100
   - research_points = 50
   - victories = 5
   - units_killed = 120
3. Snapshot sauvegardé dans daily_quests.initial_snapshot
4. Quêtes générées avec progress = 0
```

### Pendant la Journée (Chaque Tick)

```
1. Joueur joue, statistiques augmentent :
   - population_max = 105 (+5)
   - research_points = 60 (+10)
2. tick_service.py calcule les deltas :
   - population_delta = 105 - 100 = 5
   - research_delta = 60 - 50 = 10
3. update_quest_progress avec set_value=delta
4. Progression de la quête mise à jour
```

### Affichage au Joueur

```
Avant : "Population : 105/50" ❌ (ne fait aucun sens)
Après : "Croissance : +5/10" ✅ (objectif : +10 de population)
```

---

## 📊 Exemples Concrets

### Exemple 1 : Croissance Démographique

**Joueur "Alice"** :
- À minuit : Population = 95
- Objectif 1★ : +10 de population
- À 14h : Population = 103
- Progression affichée : **+8/10** (encore 2 pour avoir l'étoile)

### Exemple 2 : Accumulation de Points de Recherche

**Joueur "Bob"** :
- À minuit : PR = 200
- Objectif 1★ : +20 PR
- À 16h : PR = 215
- Progression affichée : **+15/20** (encore 5 pour avoir l'étoile)

### Exemple 3 : Victoires au Combat

**Joueur "Charlie"** :
- À minuit : Victoires totales = 50
- Objectif 1★ : +3 victoires aujourd'hui
- Après 2 batailles gagnées : Victoires totales = 52
- Progression affichée : **+2/3** (encore 1 pour avoir l'étoile)

---

## 🛡️ Protection et Sécurité

### Gestion des Cas Limites

```python
# Si pas de snapshot (ancien joueur ou première quête)
initial_population = snapshot.get('population_max', max_population)
```

**Comportement** :
- Si `initial_snapshot` existe → Utilise la valeur sauvegardée
- Si `initial_snapshot` n'existe pas → Suppose que la valeur actuelle est le début (delta = 0)

### Valeurs Négatives Impossibles

```python
population_delta = max(0, max_population - initial_population)
```

**Protection** : Si un joueur perd de la population, le delta ne devient jamais négatif.

---

## 🔄 Compatibilité et Migration

### Joueurs Existants

**Situation** : Les joueurs existants n'ont pas de `initial_snapshot` dans leurs données.

**Solution** :
1. Au prochain tick, `snapshot.get('population_max', current_value)` retourne `current_value`
2. Delta = `current_value - current_value` = 0
3. Quête démarre à 0 (correct)
4. À minuit suivant, un vrai snapshot est créé

**Impact** : Les quêtes actuelles peuvent montrer 0 de progression jusqu'à la prochaine régénération (minuit). C'est normal et ne casse rien.

### Nouvelles Quêtes

**Situation** : À partir de maintenant, toutes les nouvelles quêtes quotidiennes ont un snapshot.

**Garantie** : Deltas mesurés correctement dès la première journée.

---

## 📝 Fichiers Modifiés

| Fichier | Modifications |
|---|---|
| `server/app/services/quest_service.py` | ✅ Ajout `_create_daily_snapshot()` |
|  | ✅ Modification `_initialize_player_quests()` |
|  | ✅ Modification `get_or_generate_daily_quests()` |
|  | ✅ Modification `regenerate_daily_quests()` |
|  | ✅ Modification `enrich_quest_data()` (sync auto) |
| `server/app/services/tick_service.py` | ✅ Calcul des deltas au lieu des valeurs absolues |

---

## 🧪 Tests Recommandés

### Test 1 : Croissance de Population

1. Connecter un joueur
2. Noter la population actuelle (ex: 100)
3. Vérifier que la quête "Croissance Démographique" est à 0/X
4. Construire un bâtiment qui augmente la population
5. Attendre quelques ticks
6. Vérifier que la progression affiche le delta (ex: +3/10)

### Test 2 : Accumulation de Points de Recherche

1. Noter les PR actuels (ex: 50)
2. Vérifier que la quête "Savant" est à 0/X
3. Faire une donation à l'académie pour gagner des PR
4. Attendre le tick suivant
5. Vérifier que la progression affiche le delta (ex: +10/20)

### Test 3 : Victoires au Combat

1. Noter les victoires totales (ex: 10)
2. Vérifier que la quête "Vainqueur" est à 0/X
3. Gagner une bataille
4. Vérifier que la progression affiche +1

### Test 4 : Régénération à Minuit

1. Compléter partiellement une quête (ex: +5/10)
2. Attendre la régénération à minuit (ou forcer avec admin panel)
3. Vérifier qu'un nouveau snapshot est créé
4. Vérifier que les nouvelles quêtes commencent à 0

---

## 🎯 Impact Utilisateur

### Avant (Problématique)

```
Quête : "Croissance Démographique"
Progression : 105/50 ⭐⭐⭐ (Toutes les étoiles !)
Problème : Le joueur a 105 de population totale, pas +105 de croissance
```

### Après (Corrigé)

```
Quête : "Croissance Démographique"
Progression : +5/10 (Objectif : gagner +10 de population aujourd'hui)
Réaliste : Le joueur a effectivement gagné 5 de population depuis minuit
```

### Bénéfices

✅ **Clarté** : Les objectifs sont compréhensibles ("gagner +10" vs "avoir 10")  
✅ **Équité** : Tous les joueurs partent de 0 chaque jour  
✅ **Challenge** : Les quêtes sont des défis quotidiens, pas des stats permanentes  
✅ **Cohérence** : Toutes les quêtes quotidiennes mesurent des actions du jour  

---

## 📌 Notes Importantes

1. **Le snapshot est créé lors de la génération des quêtes**, pas à minuit exacte si le serveur est éteint
2. **Le rattrapage du scheduler** crée un snapshot au démarrage du serveur pour les quêtes manquées
3. **Les quêtes de collecte de ressources** (bois, pierre, etc.) n'utilisent PAS de snapshot car elles incrémentent déjà à chaque tick
4. **Les quêtes manuelles** (commerce, transport, etc.) ne sont pas affectées

---

**Date de correction** : 4 janvier 2026  
**Version** : 2.0 - Système de Snapshot Quotidien  
**Impact** : 5 quêtes sur 19 corrigées  
**Rétrocompatible** : ✅ Oui (graceful degradation)
