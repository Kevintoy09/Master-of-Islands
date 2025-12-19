# Analyse des Solutions Actuelles

## 1. Affichage des Héros sur le Battlefield

### Mécanisme de Reconnaissance des Héros

Le système actuel reconnait les héros de plusieurs façons :

#### A) Dans le déploiement (`military_api.py` ligne 450-461)
```python
# Détection du type héros
if unit_data.get('type') == 'hero' and 'heroData' in unit_data:
    hero_data = unit_data['heroData']
    unit_info['hero_data'] = {
        'instance_id': hero_data['instance_id'],
        'hero_id': hero_data['hero_id'],
        'name': hero_data['name'],
        'level': hero_data['level'],
        'specialty': hero_data['specialty'],
        'base_stats': hero_data.get('base_stats', {}),
        'base_bonuses': hero_data.get('base_bonuses', {})
    }
    unit_info['is_hero'] = True
```

#### B) Dans les actions de combat (`military_api.py` ligne 472-476)
```python
# Action spécifique pour héros
deploy_action = {
    "timestamp": datetime.now().isoformat(),
    "action_type": "hero_deployed" if unit_data.get('type') == 'hero' else "unit_deployed",
    # ...
}
```

#### C) Enrichissement des données héros (`military_api.py` ligne 289)
```python
# Enrichissement automatique via HeroManager
if unit.get('type') == 'hero':
    hero_manager.enrich_hero_data(unit, heroes_data)
```

### Points Clés pour la Reconnaissance
1. **Champ `type`** : Doit être égal à `'hero'`
2. **Champ `heroData`** : Doit contenir les données détaillées du héros
3. **Champ `is_hero`** : Ajouté automatiquement lors du déploiement
4. **Action spécifique** : `"hero_deployed"` au lieu de `"unit_deployed"`

## 2. Système d'Écriture Compactée

### Mécanisme de Compactage (`military_utils.py` ligne 41-48)

```python
def save_battles_data(data: Dict[str, Any]) -> bool:
    # Sauvegarde normale avec indentation
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    
    # Compactage spécifique des positions avec regex
    import re
    json_str = re.sub(
        r'"(position|from_position|to_position)":\s*\{\s*"q":\s*(-?\d+),\s*"r":\s*(-?\d+)\s*\}',
        r'"\1": {"q": \2, "r": \3}',
        json_str
    )
```

### Transformation

**Avant (format normal):**
```json
"position": {
    "q": 2,
    "r": -5
}
```

**Après (format compact):**
```json
"position": {"q": 2, "r": -5}
```

### Autres Types de Compactage (`battle_routes.py` ligne 204-239)

#### Compactage des Actions de Combat
```python
compact_data = {'unit_id': unit_id}

if action_type == 'move':
    # Suppression des champs redondants
    compact_data['from_position'] = {"q": action_data['from']['q'], "r": action_data['from']['r']}
    compact_data['to_position'] = {"q": action_data['to']['q'], "r": action_data['to']['r']}
elif action_type == 'attack':
    compact_data['target'] = action_data['target']
    compact_data['damage_dealt'] = action_data['damage_dealt']
    compact_data['survivors'] = action_data['survivors']

# Suppression du champ 'type' redondant
if 'type' in compact_data:
    del compact_data['type']
```

## 3. Points Critiques à Vérifier dans la Nouvelle Version

### Pour les Héros
1. ✅ Vérifier que `unit_data.get('type') == 'hero'`
2. ✅ S'assurer que `'heroData'` est présent
3. ✅ Contrôler que `hero_manager.enrich_hero_data()` est appelé
4. ✅ Valider que `'is_hero': True` est ajouté
5. ✅ Confirmer l'action `"hero_deployed"`

### Pour la Compactage
1. ✅ Utiliser `save_battles_data()` avec regex de compactage
2. ✅ Appliquer le compactage des actions dans `battle_routes.py`
3. ✅ Supprimer les champs redondants (`'type'`)
4. ✅ Formater les positions sur une ligne

## 4. Fonctions Utilitaires Actuelles

### Sauvegarde Compacte
- `save_battles_data()` dans `military_utils.py`
- Regex pour positions : `r'"(position|from_position|to_position)":\s*\{\s*"q":\s*(-?\d+),\s*"r":\s*(-?\d+)\s*\}'`

### Gestion des Héros
- `HeroManager.enrich_hero_data()`
- `HeroManager.apply_hero_bonuses_to_units()`
- Vérifications via `unit_data.get('type') == 'hero'`

## 5. Structure des Données Héros

### Format Attendu pour le Déploiement
```json
{
    "unit": {
        "id": "hero_hero_1757538620_c8127d_1757920522142",
        "type": "hero",
        "name": "Nom du Héros",
        "count": 1,
        "team": "attacker",
        "heroData": {
            "instance_id": "hero_1757538620_c8127d",
            "hero_id": "marcus_aurelius",
            "name": "Marcus Aurelius",
            "level": 5,
            "specialty": "cavalry_commander",
            "base_stats": {...},
            "base_bonuses": {...}
        }
    },
    "position": {"q": 2, "r": -5}
}
```

### Format Sauvegardé dans battles.json
```json
{
    "id": "hero_hero_1757538620_c8127d_1757920522142",
    "type": "hero",
    "name": "Marcus Aurelius",
    "count": 1,
    "team": "attacker",
    "position": {"q": 2, "r": -5},
    "status": "deployed",
    "deployed_at": "2025-09-18T...",
    "hero_data": {
        "instance_id": "hero_1757538620_c8127d",
        "hero_id": "marcus_aurelius",
        "name": "Marcus Aurelius",
        "level": 5,
        "specialty": "cavalry_commander",
        "base_stats": {...},
        "base_bonuses": {...}
    },
    "is_hero": true
}
```