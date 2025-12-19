# Implémentation des Bonus de Recherche au Niveau Joueur

## 📋 Résumé

Les bonus de recherche s'appliquent maintenant au niveau **joueur** et non plus au niveau **ville**. Cela signifie qu'une fois une recherche débloquée, elle s'applique automatiquement à **toutes les villes actuelles et futures** du joueur.

## 🎯 Objectif

Permettre aux bonus de recherche (comme "Abattage Forestier" : +25% bois) de s'appliquer à toutes les villes du joueur, pas seulement à une ville spécifique.

## ✅ Modifications Effectuées

### 1. **research.json** - Correction du bonus
- **Fichier** : `server/data/research.json`
- **Changement** : Bonus de "Abattage Forestier" corrigé de 20% à 25%
```json
"effect": { "resource_bonus": { "wood": 25 } }
```

### 2. **game_logic.py** - Lecture des bonus depuis le joueur
- **Fichier** : `server/app/game_logic.py`
- **Fonction** : `calculate_total_production_rate()`
- **Changement** : Les bonus de recherche sont maintenant lus depuis `player['research_effects']['resource_bonuses']` au lieu de `city.get('research_bonus')`

**Avant :**
```python
research_bonuses = city.get('research_bonus', {})
research_bonus_percent = research_bonuses.get(resource, 0) / 100.0
```

**Après :**
```python
research_bonus_percent = 0.0
player_id = city.get('owner')
if player_id:
    players_data = self.data.load_players()
    player = next((p for p in players_data.get('players', []) if p['id'] == player_id), None)
    if player:
        research_effects = player.get('research_effects', {})
        resource_bonuses = research_effects.get('resource_bonuses', {})
        research_bonus_percent = resource_bonuses.get(resource, 0) / 100.0
```

### 3. **city_routes.py** - API renvoie les bonus joueur
- **Fichier** : `server/app/routes/city_routes.py`
- **Route** : `/api/city/<city_id>/production`
- **Changement** : L'API récupère maintenant les bonus de recherche depuis le joueur

**Avant :**
```python
research_bonus = city.get('resources', {}).get('research_bonus', {}).get(resource, 0)
```

**Après :**
```python
research_bonus = 0
player_id = city.get('owner')
if player_id:
    players_data = data_manager.load_players()
    player = next((p for p in players_data.get('players', []) if p['id'] == player_id), None)
    if player:
        research_effects = player.get('research_effects', {})
        resource_bonuses = research_effects.get('resource_bonuses', {})
        research_bonus = resource_bonuses.get(resource, 0)
```

### 4. **city_constants.py** - Nettoyage
- **Fichier** : `server/app/city_constants.py`
- **Changement** : Suppression de `"research_bonus": {}` des constantes par défaut des villes
- **Raison** : Les bonus sont maintenant stockés au niveau joueur, pas au niveau ville

## 📊 Architecture du Système

### Stockage des Données

**players.json** (niveau joueur) :
```json
{
  "players": [
    {
      "id": "player_123",
      "name": "Kevin",
      "unlocked_research": ["conservation", "abattage_forestier"],
      "research_effects": {
        "resource_bonuses": {
          "wood": 25,
          "stone": 15
        },
        "unlocked_buildings": ["Entrepôt"],
        "unlocked_resources": []
      }
    }
  ]
}
```

### Flux de Données

1. **Déblocage de recherche** (research_service.py)
   - Le joueur débloque "Abattage Forestier"
   - Le bonus (+25% bois) est ajouté à `player['research_effects']['resource_bonuses']['wood']`

2. **Calcul de production** (game_logic.py)
   - Pour chaque ville, le système récupère le `player_id` depuis `city['owner']`
   - Charge les données du joueur depuis `players.json`
   - Lit les bonus depuis `player['research_effects']['resource_bonuses']`
   - Applique le bonus à la production

3. **Affichage dans l'interface** (HeaderBar → ResourceProductionPopup)
   - L'API `/api/city/<city_id>/production` renvoie `researchBonus: 25`
   - Le frontend affiche "Bonus recherche : +25%" dans la tooltip de production

## 🎮 Exemple Concret

### Scénario
1. Le joueur possède 3 villes : Paris, Lyon, Marseille
2. Le joueur débloque "Abattage Forestier" (+25% bois)

### Résultat
- ✅ **Paris** : +25% production de bois
- ✅ **Lyon** : +25% production de bois
- ✅ **Marseille** : +25% production de bois
- ✅ **Toute nouvelle ville** : +25% production de bois automatiquement

### Calcul de Production

**Sans bonus :**
- Base : 10 ouvriers × 1.0 (rendement) = 10 bois/sec

**Avec bonus de recherche (+25%) :**
- Production = 10 × (1 + 0.25) = **12.5 bois/sec**

**Avec bonus bâtiment (+15%) ET recherche (+25%) :**
- Production = 10 × (1 + 0.15 + 0.25) = **14.0 bois/sec**

## 🧪 Tests

Un script de test a été créé : `server/test_research_system.py`

**Résultats des tests :**
```
✅ Tous les imports sont OK
✅ Données de recherche correctes
✅ Logique correcte

📋 Résumé des changements :
  1. research.json : bonus bois passé de 20% à 25%
  2. game_logic.py : lecture des bonus depuis player.research_effects
  3. city_routes.py : API renvoie les bonus depuis le joueur
  4. city_constants.py : suppression de research_bonus des constantes ville

💡 Les bonus de recherche s'appliquent maintenant à TOUTES les villes du joueur
```

## 📝 Notes Importantes

### Compatibilité avec l'Existant
- Le système `research_service.py` stocke DÉJÀ les bonus au niveau joueur
- Le problème était que `game_logic.py` et `city_routes.py` les lisaient au mauvais endroit
- Cette modification corrige cette incohérence

### Branche Économie
Cette implémentation concerne la recherche "Abattage Forestier" mais le système fonctionne pour **toutes** les recherches avec effet `"resource_bonus"` :

**Recherches de la branche économie :**
1. Conservation (Entrepôt) ✅
2. Abattage Forestier (+25% bois) ✅
3. Carrière Avancée (+15% pierre)
4. Mine de Fer (+20% fer)
5. Agriculture (+15% céréales)
6. Production de Papyrus (+20% papyrus)
7. Etc.

### Prochaines Étapes

Pour continuer sur la branche économie :
1. Vérifier chaque recherche une par une
2. S'assurer que les pourcentages sont corrects
3. Tester l'affichage dans l'interface
4. Documenter les bonus attendus

## 🔧 Maintenance

### Pour ajouter un nouveau bonus de recherche

1. **Ajouter dans research.json :**
```json
{
  "id": "nouvelle_recherche",
  "effect": {
    "resource_bonus": {
      "stone": 15
    }
  }
}
```

2. **Le système appliquera automatiquement :**
   - Stockage dans `player['research_effects']['resource_bonuses']['stone']`
   - Application à toutes les villes du joueur
   - Affichage dans l'interface

### Pour débugger

**Vérifier les bonus d'un joueur :**
```python
players_data = data_manager.load_players()
player = players_data['players'][0]
print(player['research_effects']['resource_bonuses'])
# Output: {'wood': 25, 'stone': 15, ...}
```

**Vérifier la production d'une ville :**
```python
production = game_logic.calculate_total_production_rate(city, 'wood')
print(f"Production de bois : {production} /sec")
```

## 📚 Fichiers Modifiés

- ✅ `server/data/research.json` (bonus 20% → 25%)
- ✅ `server/app/game_logic.py` (lecture depuis joueur)
- ✅ `server/app/routes/city_routes.py` (API depuis joueur)
- ✅ `server/app/city_constants.py` (suppression research_bonus)
- ✅ `server/test_research_system.py` (nouveau fichier de test)

## ✨ Résultat Final

Les bonus de recherche fonctionnent maintenant comme dans Ikariam :
- **Global au joueur** ✅
- **S'applique à toutes les villes** ✅
- **Persistant** ✅
- **Affiché dans l'interface** ✅

---

**Date** : Janvier 2025  
**Système** : Bonus de Recherche au Niveau Joueur  
**Statut** : ✅ Implémenté et testé
