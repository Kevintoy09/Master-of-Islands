# 📊 Système de Progression du Joueur

## Vue d'ensemble

Le système de progression calcule le **niveau du joueur** basé sur 3 axes :
- **🏗️ Construction** : Points basés sur les niveaux de bâtiments
- **🔬 Recherche** : Total des points de recherche investis
- **⚔️ Militaire** : XP, victoires, unités tuées (déjà existant)

---

## Formules de calcul

### 1. Points de Construction

Pour chaque bâtiment de niveau N :
```
Points = 1 + 2 + 3 + ... + N = N × (N + 1) / 2
```

**Exemples** :
- Bâtiment niveau 1 → **1 point**
- Bâtiment niveau 2 → **3 points** (1+2)
- Bâtiment niveau 3 → **6 points** (1+2+3)
- Bâtiment niveau 5 → **15 points** (1+2+3+4+5)
- Bâtiment niveau 10 → **55 points**

**Total joueur** = Somme des points de tous les bâtiments de toutes ses villes

### 2. Points de Recherche Investis

```
Total = Σ(Coût recherches débloquées) + Points recherche actuels
```

**Exemple** :
```json
{
  "unlocked_research": ["sablier", "conservation", "abattage_forestier"],
  "research_points": 150
}
```

- `sablier` coûte 50 PR
- `conservation` coûte 10 PR
- `abattage_forestier` coûte 25 PR
- Points actuels : 150 PR

**Total** = 50 + 10 + 25 + 150 = **235 points**

### 3. Score Global

```
Score Total = construction_points + research_points_invested + (military_xp / 10)
Niveau Estimé = Score Total / 100
```

---

## Structure des données

### Ajouts dans `players.json`

```json
{
  "id": "player_1",
  "username": "aaa",
  
  // Nouveaux champs
  "construction_points": 45,
  "research_points_invested": 235,
  
  // Existant (militaire)
  "total_xp_gained": 1250,
  "victories": 8,
  "defeats": 2,
  "total_units_killed": 50,
  "total_units_lost": 12
}
```

---

## API Endpoints

### GET `/api/progression/<player_id>`

Récupère les scores de progression du joueur (calcul en temps réel).

**Réponse** :
```json
{
  "success": true,
  "player_id": "player_1",
  "scores": {
    "construction_points": 45,
    "research_points_invested": 235,
    "military_xp": 1250,
    "total_score": 405,
    "estimated_level": 4,
    "victories": 8,
    "defeats": 2,
    "total_units_killed": 50,
    "total_units_lost": 12
  }
}
```

### POST `/api/progression/<player_id>/update`

Recalcule et met à jour les scores dans `players.json`.

**À appeler après** :
- Construction/amélioration d'un bâtiment
- Déverrouillage d'une recherche

**Réponse** :
```json
{
  "success": true,
  "construction_points": 45,
  "research_points_invested": 235
}
```

### POST `/api/progression/update-all`

Recalcule les scores de tous les joueurs (admin/maintenance).

**Réponse** :
```json
{
  "success": true,
  "updated_count": 5,
  "total_players": 5
}
```

---

## Initialisation

### Script d'initialisation

Pour calculer les scores initiaux de tous les joueurs existants :

```bash
cd server
python init_progression_scores.py
```

Le script :
1. Charge tous les joueurs
2. Calcule leurs points de construction
3. Calcule leurs points de recherche
4. Met à jour `players.json`

**Sortie** :
```
🔄 Initialisation des scores de progression...

📊 3 joueur(s) trouvé(s)

⏳ Calcul des scores pour aaa (player_1)...
   🏗️  Points de construction: 45
   🔬 Points de recherche investis: 235
   ✅ Scores mis à jour !

⏳ Calcul des scores pour bbb (player_2)...
   🏗️  Points de construction: 28
   🔬 Points de recherche investis: 150
   ✅ Scores mis à jour !

✨ Initialisation terminée !
```

---

## Intégration automatique (TODO)

### Hooks à ajouter

1. **Après construction de bâtiment** (dans `city_routes.py`) :
```python
from app.services.player_progression_service import PlayerProgressionService

# Après sauvegarde du bâtiment
progression_service = PlayerProgressionService(data_manager)
progression_service.update_player_scores(player_id)
```

2. **Après déverrouillage de recherche** (dans `research_routes.py`) :
```python
from app.services.player_progression_service import PlayerProgressionService

# Après déverrouillage réussi
progression_service = PlayerProgressionService(data_manager)
progression_service.update_player_scores(player_id)
```

---

## Utilisation pour les objectifs

Le système de progression fournit le **niveau du joueur** pour adapter les objectifs :

```python
# Récupérer le niveau du joueur
progression_service = PlayerProgressionService(data_manager)
player_level_data = progression_service.get_player_level(player_id)

estimated_level = player_level_data['estimated_level']  # Ex: 4

# Adapter les objectifs
if estimated_level >= 10:
    # Objectifs avancés
    objective_amount = 5000
elif estimated_level >= 5:
    # Objectifs intermédiaires
    objective_amount = 2000
else:
    # Objectifs débutants
    objective_amount = 500
```

---

## Fichiers créés

- ✅ `server/app/services/player_progression_service.py` - Service de calcul
- ✅ `server/app/routes/progression_routes.py` - API routes
- ✅ `server/init_progression_scores.py` - Script d'initialisation
- ✅ `server/data/players.json` - Champs ajoutés

---

## Prochaines étapes

1. ✅ **Système de progression** → FAIT
2. 🔄 **Intégration automatique** → À ajouter dans city_routes.py et research_routes.py
3. 🎯 **Système d'objectifs** → À implémenter ensuite
   - Fichier `objectives.json` avec templates
   - Routes API pour objectifs
   - Popup UI pour afficher les objectifs
   - Système de récompenses

---

## Tests

### Test manuel via API

```bash
# Récupérer les scores
curl http://localhost:5000/api/progression/player_1

# Mettre à jour les scores
curl -X POST http://localhost:5000/api/progression/player_1/update

# Mettre à jour tous les joueurs
curl -X POST http://localhost:5000/api/progression/update-all
```
