# 🎯 SYSTÈME DE QUÊTES - STRUCTURE SIMPLIFIÉE

## 📋 Vue d'ensemble

Le système de quêtes est maintenant basé sur une **séparation claire** entre :
- **`quests_config.json`** : Configuration statique (templates des quêtes)
- **`player_quests.json`** : Progression dynamique des joueurs

---

## 📁 Structure de `player_quests.json`

### Principe
- **Stocke uniquement la PROGRESSION** des joueurs
- Les détails (titres, descriptions, récompenses) sont dans `quests_config.json`
- Le croisement se fait via l'`id` de la quête

### Format pour chaque joueur

```json
{
  "Kevin": {
    "level": 1,
    "quest_points_total": 0,
    "daily_quests": {
      "generated_date": "2025-12-05",
      "quests": [
        {
          "id": "eco_collect_wood",
          "current_progress": 100,
          "target": 500,
          "is_completed": false,
          "is_claimed": false,
          "completed_at": null
        }
      ]
    },
    "weekly_quests": {
      "generated_date": "2025-12-02",
      "quests": []
    },
    "unclaimed_rewards": [
      {
        "quest_id": "eco_transport_resources",
        "star_level": 1,
        "rewards": {"gold": 100, "quest_points": 1},
        "expires_at": "2025-12-06T23:59:59"
      }
    ]
  }
}
```

### Champs expliqués

#### Au niveau du joueur
- **`level`** : Niveau calculé (construction_points + quest_points depuis `players.json`)
- **`quest_points_total`** : Total des quest_points gagnés toutes quêtes confondues

#### Dans `daily_quests.quests[]`
- **`id`** : Identifiant unique (référence vers `quests_config.json`)
- **`current_progress`** : Progression actuelle (ex: 100 bois collectés)
- **`target`** : Objectif à atteindre (ex: 500 bois)
- **`is_completed`** : `true` si `current_progress >= target`
- **`is_claimed`** : `true` si les récompenses ont été réclamées
- **`completed_at`** : Timestamp de complétion (ISO format) ou `null`

#### Dans `unclaimed_rewards[]`
- **`quest_id`** : ID de la quête dont la récompense est disponible
- **`star_level`** : Niveau d'étoile atteint (1, 2 ou 3)
- **`rewards`** : Copie des récompenses pour accès rapide
- **`expires_at`** : Date d'expiration (ISO format) - après cette date, la récompense est perdue

---

## 📁 Structure de `quests_config.json`

### Principe
- **Templates des quêtes** : titres, descriptions, icônes, types
- **Paliers de difficulté** : targets et rewards selon le niveau du joueur
- **Pools de quêtes** : economic, military, research

### Format (extrait)

```json
{
  "daily_quests_pool": {
    "economic": [
      {
        "id": "eco_collect_wood",
        "category": "economic",
        "type": "collect_resource",
        "resource": "wood",
        "title": "Bûcheron",
        "description": "Récoltez du bois dans vos forêts",
        "icon": "🪵"
      }
    ]
  },
  "quest_progression": {
    "eco_collect_wood": [
      {
        "level": 1,
        "targets": [500, 1000, 2000],
        "rewards": [
          {"gold": 100, "quest_points": 1},
          {"gold": 150, "quest_points": 2},
          {"gold": 200, "quest_points": 3}
        ]
      }
    ]
  }
}
```

---

## 🔄 Flux de données

### 1. Chargement des quêtes (Frontend → Backend)

**Frontend** appelle : `GET /api/quests/daily?username=Kevin`

**Backend** (`quest_service.py`) :
1. Charge `player_quests.json` pour récupérer la progression
2. Pour chaque quête, enrichit avec les données de `quests_config.json` :
   - `title`, `description`, `icon` depuis le pool
   - `rewards` calculées selon le niveau

**Retour JSON** :
```json
{
  "username": "Kevin",
  "player_level": 1,
  "quests": [
    {
      "id": "eco_collect_wood",
      "title": "Bûcheron",
      "description": "Récoltez du bois dans vos forêts",
      "type": "economic",
      "target": 500,
      "current_progress": 100,
      "reward_xp": 100,
      "reward_stars": 3,
      "is_completed": false,
      "is_claimed": false
    }
  ]
}
```

### 2. Mise à jour de la progression

**Quand le joueur collecte du bois :**
```python
quest_service.update_quest_progress(
    username="Kevin",
    quest_id="eco_collect_wood",
    increment=50  # +50 bois collectés
)
```

**Backend** :
1. Charge `player_quests.json`
2. Trouve la quête `eco_collect_wood`
3. Incrémente `current_progress` : 100 → 150
4. Vérifie si `current_progress >= target` (150 >= 500 ? Non)
5. Met à jour `is_completed` si nécessaire
6. Sauvegarde dans `player_quests.json`

### 3. Réclamer une récompense

**Frontend** : `POST /api/quests/claim-reward`
```json
{
  "username": "Kevin",
  "quest_id": "eco_collect_wood",
  "star_level": 1
}
```

**Backend** :
1. Vérifie que la quête est complétée (`is_completed = true`)
2. Transfère la récompense vers `unclaimed_rewards[]`
3. Met `is_claimed = true`
4. Ajoute une date d'expiration (24h pour daily, 7j pour weekly)

---

## ✅ Avantages de cette structure

### 1. **Séparation des responsabilités**
- ✅ Config = immuable, facile à modifier sans toucher aux joueurs
- ✅ Progression = état actuel, spécifique à chaque joueur

### 2. **Scalabilité**
- ✅ Ajouter une nouvelle quête = modifier `quests_config.json` uniquement
- ✅ Modifier les récompenses = aucun impact sur les joueurs existants

### 3. **Simplicité**
- ✅ Moins de données redondantes dans `player_quests.json`
- ✅ Fichier plus léger et plus lisible
- ✅ Croisement facile via `id`

### 4. **Flexibilité**
- ✅ `unclaimed_rewards` centralisé pour toutes les quêtes
- ✅ Système d'expiration unifié
- ✅ Facile d'ajouter des weekly/monthly quests

---

## 🔧 Intégration Backend

### Méthode clé : `enrich_quest_data()`

```python
def enrich_quest_data(self, quest_progress: Dict) -> Dict:
    """
    Enrichit les données simplifiées avec les infos de quests_config.json
    
    Input (depuis player_quests.json):
    {
      "id": "eco_collect_wood",
      "current_progress": 100,
      "target": 500,
      "is_completed": false,
      "is_claimed": false,
      "completed_at": null
    }
    
    Output (pour le frontend):
    {
      "id": "eco_collect_wood",
      "title": "Bûcheron",
      "description": "Récoltez du bois",
      "type": "economic",
      "target": 500,
      "current_progress": 100,
      "reward_xp": 100,
      "reward_stars": 3,
      "is_completed": false,
      "is_claimed": false
    }
    """
```

---

## 📊 Exemple complet

### Scénario : Kevin collecte du bois

**État initial** (`player_quests.json`) :
```json
{
  "id": "eco_collect_wood",
  "current_progress": 100,
  "target": 500,
  "is_completed": false
}
```

**Action** : Kevin collecte 450 bois supplémentaires

**Backend** : `update_quest_progress("Kevin", "eco_collect_wood", increment=450)`

**État final** :
```json
{
  "id": "eco_collect_wood",
  "current_progress": 550,
  "target": 500,
  "is_completed": true,
  "is_claimed": false,
  "completed_at": "2025-12-05T18:30:00Z"
}
```

**Frontend affiche** : ✅ Quête complétée ! Barre de progression à 100% (verte)

**Kevin clique sur "Réclamer"** → Récompense ajoutée dans `unclaimed_rewards[]`

---

## 🎁 Système de récompenses non réclamées

### Pourquoi `unclaimed_rewards[]` ?

1. **Centralisation** : Toutes les récompenses en attente au même endroit
2. **Expiration** : Évite l'accumulation infinie de récompenses
3. **Traçabilité** : Historique des quêtes complétées

### Format

```json
"unclaimed_rewards": [
  {
    "quest_id": "eco_collect_wood",
    "star_level": 1,
    "rewards": {
      "gold": 100,
      "quest_points": 1
    },
    "expires_at": "2025-12-06T23:59:59",
    "quest_type": "daily"
  }
]
```

### Gestion de l'expiration

**Backend (cron job quotidien)** :
```python
def clean_expired_rewards():
    for player in player_quests:
        player['unclaimed_rewards'] = [
            r for r in player['unclaimed_rewards']
            if datetime.fromisoformat(r['expires_at']) > datetime.now()
        ]
```

---

## 🚀 Prochaines étapes

### À implémenter
1. ✅ Structure simplifiée de `player_quests.json`
2. ✅ Méthode `enrich_quest_data()` dans le backend
3. ⏳ Système de tracking automatique (hooks sur les actions du joueur)
4. ⏳ Interface frontend pour réclamer les récompenses
5. ⏳ Notifications quand une quête est complétée
6. ⏳ Quêtes hebdomadaires
7. ⏳ Job de nettoyage des récompenses expirées

### Hooks à ajouter

**Exemple : Collecter du bois**
```python
# Dans la fonction de collecte de ressources
def collect_resource(player_id, resource_type, amount):
    # ... logique de collecte existante ...
    
    # Hook pour les quêtes
    if resource_type == "wood":
        quest_service.update_quest_progress(
            username=player_username,
            quest_id="eco_collect_wood",
            increment=amount
        )
```

**Liste des hooks nécessaires :**
- `on_resource_collected` → eco_collect_wood, eco_collect_marble, etc.
- `on_building_built` → eco_build_buildings
- `on_trade_completed` → eco_trade_resources
- `on_transport_sent` → eco_transport_resources
- `on_unit_recruited` → mil_recruit_units
- `on_site_donation` → eco_donate_sites

---

## 📝 Résumé

✅ **Structure simplifiée et scalable**
✅ **Séparation claire Config vs Progression**
✅ **Facilite les mises à jour et l'ajout de quêtes**
✅ **Système de récompenses avec expiration**
✅ **Backend prêt pour l'intégration des hooks**

**Prochaine action** : Implémenter les hooks automatiques pour tracker la progression en temps réel ! 🎯
