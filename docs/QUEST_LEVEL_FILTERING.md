# Distribution des quêtes par niveau de joueur

## ❌ Approche qui NE FONCTIONNE PAS

```json
"eco_collect_marble": [
  {"level": 3, "targets": [20, 30, 40], ...},
  {"level": 4, "targets": [40, 60, 80], ...},
  {"level": 5, "targets": [80, 120, 160], ...}
]
```

**Problème** : Si un joueur est niveau 1 ou 2, le code cherche `level: 1` ou `level: 2` dans la configuration. Ne trouvant rien, **la quête ne sera jamais générée** pour ce joueur, même quand il atteindra le niveau 3.

## ✅ Solutions possibles

### Solution 1 : Garder tous les niveaux mais rendre impossible

```json
"eco_collect_marble": [
  {"level": 1, "targets": [999999, 999999, 999999], "rewards": [...]},
  {"level": 2, "targets": [999999, 999999, 999999], "rewards": [...]},
  {"level": 3, "targets": [20, 30, 40], "rewards": [...]},
  {"level": 4, "targets": [40, 60, 80], "rewards": [...]},
  {"level": 5, "targets": [80, 120, 160], "rewards": [...]}
]
```

**Avantage** : La quête existe toujours dans le pool mais est impossible à compléter pour les bas niveaux.

**Inconvénient** : La quête apparaît quand même dans la liste quotidienne.

### Solution 2 : Ajouter un filtre de niveau minimum dans daily_quests_pool

```json
{
  "id": "eco_collect_marble",
  "category": "economic",
  "type": "collect_resource",
  "resource": "marble",
  "title": "Carrier de Marbre",
  "description": "Collectez du marbre précieux",
  "icon": "🏛️",
  "min_level": 3  // ← NOUVEAU CHAMP
}
```

**Modification requise** : Ajouter la logique de filtrage dans `quest_service.py` lors de la génération des quêtes quotidiennes.

### Solution 3 : Créer des pools de quêtes par tranche de niveau

```json
"daily_quests_pool": {
  "beginner": {  // Niveaux 1-5
    "economic": [...],
    "military": [...],
    "research": [...]
  },
  "intermediate": {  // Niveaux 6-15
    "economic": [...],
    "military": [...],
    "research": [...]
  },
  "advanced": {  // Niveaux 16+
    "economic": [...],
    "military": [...],
    "research": [...]
  }
}
```

**Modification requise** : Refactoriser complètement la génération de quêtes.

## 🎯 Recommandation

**Solution 2** est la plus simple et la plus propre :

1. Ajouter `"min_level"` optionnel dans `daily_quests_pool`
2. Modifier la génération de quêtes pour filtrer selon le niveau
3. Garder les progressions de niveau classiques (1, 2, 3) dans `quest_progression`

### Code à ajouter dans quest_service.py

```python
def _generate_daily_quests(self, player_level: int) -> List[Dict]:
    """Génère des quêtes quotidiennes aléatoires pour un joueur"""
    pool = self.quests_config.get('daily_quests_pool', {})
    
    # Filtrer les quêtes disponibles selon le niveau
    available_quests = []
    for category_quests in pool.values():
        for quest in category_quests:
            min_level = quest.get('min_level', 1)  # Par défaut niveau 1
            if player_level >= min_level:
                available_quests.append(quest)
    
    # Sélectionner 5 quêtes aléatoires parmi les disponibles
    if len(available_quests) >= 5:
        selected = random.sample(available_quests, 5)
    else:
        selected = available_quests
    
    return selected
```

## 📝 Notes importantes

- Le niveau du joueur est recalculé à chaque génération de quêtes
- Les quêtes déjà en cours ne sont pas affectées par le changement de niveau
- Il faut au moins 5 quêtes disponibles pour chaque tranche de niveau
