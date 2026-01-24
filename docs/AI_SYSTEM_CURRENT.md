# 🤖 SYSTÈME D'IA - DOCUMENTATION ACTUELLE

*Dernière mise à jour : 14 janvier 2026*

---

## 📋 VUE D'ENSEMBLE

### Fonctionnement actuel

Le système d'IA est **pleinement fonctionnel** et permet à des joueurs automatisés de développer leurs villes de manière autonome. Les IA suivent un cycle de développement stratégique et exécutent des actions à chaque tick.

**Capacités actuelles** :
- ✅ Construction automatique de bâtiments
- ✅ Assignation intelligente des ouvriers
- ✅ Déblocage automatique de recherches
- ✅ Gestion de multiples villes par IA
- ✅ Stratégies différenciées (development, balanced, aggressive)
- ✅ Système de preset pour fréquence d'exécution
- ✅ Persistance complète (constructions, recherches, workers)

---

## 🏗️ ARCHITECTURE

### Fichiers principaux

```
server/app/ai/
├── ai_controller.py              # Contrôleur principal - exécute toutes les IA
├── ai_strategy_manager.py        # Gestion des stratégies et phases
├── ai_auto_cycle_manager.py      # Système de preset (fréquence exécution)
└── ai_strategies_state.json      # État des stratégies par joueur (cache)
```

### Intégration dans le tick

```python
# Fichier: server/app/services/tick_service.py

def _execute_tick_internal():
    # 1. Calculer production ressources (toutes villes)
    # 2. Calculer or/recherche (tous joueurs)
    
    # 3. SAUVEGARDER production/or AVANT l'IA
    save_savegame(savegame_data)
    save_players(players_data)
    
    # 4. EXÉCUTER IA (charge fichier frais, construit, sauvegarde)
    if auto_cycle_manager.is_enabled():
        auto_cycle_manager.execute_ai_cycles_for_tick(current_tick)
    
    # 5. RECHARGER pour récupérer constructions IA
    savegame_data = load_savegame()
    
    # 6. Vérifier constructions terminées
    update_construction_statuses(savegame_data)
    
    # 7. Sauvegarde finale
    save_savegame(savegame_data)
```

**Points clés** :
- L'IA ne reçoit PAS `savegame_data` en paramètre
- Elle charge elle-même le fichier avec `load_savegame()`
- Elle sauvegarde avec `force_save=True` après chaque action
- Le tick recharge après pour récupérer les modifications

---

## ⚙️ SYSTÈME DE PRESET

### Configuration (`server/auto_tick_settings.json`)

```json
{
  "enabled": true,
  "interval_seconds": 1,
  "ai_auto_cycle": {
    "enabled": true,
    "preset": "hard",
    "custom_interval": 1,
    "time_slots": []
  }
}
```

### Presets disponibles

| Preset | Intervalle | Description |
|--------|-----------|-------------|
| `casual` | 12 ticks | IA joue toutes les 2 minutes (très lent) |
| `easy` | 6 ticks | IA joue toutes les minutes |
| `medium` | 3 ticks | IA joue toutes les 30 secondes |
| `hard` | 1 tick | IA joue à chaque tick (temps réel) |
| `extreme` | 0.5 tick | IA joue 2 fois par tick |
| `perso` | custom | Horaires personnalisés |

**Fichier** : `server/app/ai/ai_auto_cycle_manager.py`

### Fonctionnement

```python
# L'IA n'est exécutée QUE si son cycle est arrivé
# Basé sur le numéro de tick global

if current_tick % interval == 0:
    execute_ai(player)
```

---

## 🎯 STRATÉGIES IA

### Types de stratégies

**1. Development (développement)**
- Focus : construction bâtiments essentiels
- Phases : 0-4 (Hôtel de Ville → Academy → Production)
- Utilisé pour : démarrage rapide

**2. Balanced (équilibré)**
- Focus : équilibre économie/recherche/militaire
- *(Non implémenté)*

**3. Aggressive (militaire)**
- Focus : armée et conquête
- *(Non implémenté)*

### Phases de développement (Development)

```python
PHASES = {
    0: {  # Démarrage
        "buildings": ["Hôtel de Ville"],
        "research": ["acces_ressources"],
        "workers_strategy": "balanced"
    },
    1: {  # Recherche
        "buildings": ["Academy", "Entrepôt"],
        "research": ["maison_chef", "conservation"],
        "workers_strategy": "research_focus"
    },
    2: {  # Production
        "buildings": ["Scierie", "Carrière de pierre"],
        "research": ["abattage_forestier", "extraction_miniere"],
        "workers_strategy": "production_focus"
    },
    # ... phases 3-4
}
```

**Fichier** : `server/app/ai/ai_strategy_manager.py`

---

## 🔨 ACTIONS IA

### 1. Construction de bâtiments

```python
# Fichier: ai_controller.py -> _execute_build_action()

1. Trouver un slot libre (slot_1, slot_2, ..., slot_18)
2. Vérifier prérequis recherche
3. Vérifier ressources disponibles
4. Appeler city_service.build_building()
5. Sauvegarder immédiatement
```

**Service utilisé** : `server/app/business/city_service.py`

### 2. Recherche

```python
# Fichier: ai_controller.py -> _execute_research_action()

1. Vérifier si déjà en cours
2. Vérifier prérequis technologies
3. Vérifier points de recherche disponibles
4. Appeler research_service.start_research()
5. Sauvegarder players.json
```

**Service utilisé** : `server/app/business/research_service.py`

### 3. Assignation workers

```python
# Fichier: ai_controller.py -> _optimize_workers()

Stratégies :
- balanced: Répartition équilibrée
- research_focus: 50% academy
- production_focus: Ressource principale île
- cereal_priority: Anti-famine

Applique :
- workers_assigned[site] = nombre
- Sauvegarde immédiatement
```

---

## 💾 PERSISTENCE

### Fichiers modifiés par l'IA

**1. savegame.json** (constructions, workers)
```json
{
  "cities": [{
    "id": "city_id_1518",
    "owner": "player_7",
    "buildings": [
      {
        "slot_id": "slot_1",
        "name": "Hôtel de Ville",
        "level": 1,
        "status": "Terminé"
      }
    ],
    "workers_assigned": {
      "forest": 10,
      "quarry": 8,
      "academy": 5
    }
  }]
}
```

**2. players.json** (recherches)
```json
{
  "players": [{
    "id": "player_7",
    "username": "IA_Joueur1",
    "research_unlocked": ["acces_ressources", "maison_chef"],
    "research_in_progress": {
      "tech": "conservation",
      "started_at": 1736849234,
      "duration": 120
    }
  }]
}
```

**3. ai_strategies_state.json** (cache stratégie)
```json
{
  "player_7": {
    "strategy": "development",
    "phase": 1,
    "last_update": 1736849234,
    "city_actions": {
      "city_id_1518": [
        {"cycle": 5, "action": "build", "status": "success"}
      ]
    }
  }
}
```

---

## 🔄 CYCLE D'EXÉCUTION

### Tick complet avec IA

```
Tick #42 (intervalle 1 seconde)
│
├─ 1. Traiter 9 villes (production ressources)
│   └─ wood, stone, cereal += workers × production_rate
│
├─ 2. Traiter joueurs (or, recherche)
│   └─ gold += population_free × gold_rate
│
├─ 3. SAUVEGARDER savegame + players
│   └─ force_save=True (bypass throttle)
│
├─ 4. EXÉCUTER IA (si preset match)
│   ├─ AIAutoCycleManager vérifie : tick % interval == 0 ?
│   ├─ Si OUI pour player_7 :
│   │   ├─ Charger savegame frais
│   │   ├─ Analyser stratégie (development, phase 1)
│   │   ├─ Décider action (build Academy)
│   │   ├─ Exécuter (city_service.build_building)
│   │   └─ Sauvegarder (force_save=True)
│   └─ Si NON : skip
│
├─ 5. RECHARGER savegame
│   └─ Récupérer constructions IA
│
├─ 6. Vérifier constructions terminées
│   └─ update_construction_statuses()
│
└─ 7. Sauvegarder final
    └─ Terminé en ~50ms
```

---

## 🐛 DEBUGGING

### Logs IA

```
🔍 [player_7] Strategy: development, Phase: 1
  ✅ 🏗️ Construction: Academy sur slot_2
  
🔍 [player_7] Strategy: development, Phase: 1
  ✅ 🔬 Recherche débloquée: maison_chef
  
🔍 [player_7] Strategy: development, Phase: 2
  ✅ 👷 forest:10, quarry:8, academy:5
```

### Fichier de log

`server/app/ai/ai_strategies_state.json` - Contient l'historique des actions par ville

---

## 📊 PERFORMANCE

### Métriques actuelles

- **Temps exécution IA** : ~5-15ms par IA
- **Nombre IA simultanées** : 1-10 (testé)
- **Temps tick total** : 30-80ms (avec IA)
- **Fréquence sauvegarde** : 2-3 fois par tick (production + IA + final)

### Scalabilité

**Limites actuelles** :
- ✅ 1-100 IA : Performance excellente (<100ms/tick)
- ⚠️ 100-500 IA : Acceptable (100-500ms/tick)
- ❌ 500+ IA : Nécessite optimisations (batch, rotation)

**Solutions futures** (quand nécessaire) :
1. Système de rotation par batch (20 IA/tick)
2. Pré-filtrage (skip IA sans ressources)
3. Sauvegarde groupée (1 seule écriture disque)
4. Cache de stratégie (éviter recalcul)

---

## 🔧 CONFIGURATION IA

### Créer une nouvelle IA

```json
// Dans players.json
{
  "id": "player_8",
  "username": "IA_Conquérant",
  "is_ai": true,
  "faction": "iron",
  "gold": 500,
  "research_points": 0,
  "research_unlocked": []
}
```

### Modifier le preset

```bash
# Dans server/auto_tick_settings.json
"ai_auto_cycle": {
  "enabled": true,
  "preset": "medium",  # Changer ici
  "custom_interval": 3
}
```

### Activer/désactiver l'IA

```python
# Via admin_routes.py
POST /api/admin/ai-auto-cycle/toggle
{
  "enabled": true
}
```

---

## 🚀 ÉVOLUTIONS FUTURES

### Court terme (1-2 semaines)
- [ ] Stratégie colonization (expansion)
- [ ] Gestion du marché (achat/vente)
- [ ] Système de transport entre villes

### Moyen terme (1 mois)
- [ ] Stratégie balanced complète
- [ ] Stratégie aggressive (militaire)
- [ ] Gestion des héros

### Long terme (2-3 mois)
- [ ] Diplomatie (alliances, guerres)
- [ ] IA adaptative (apprend des joueurs)
- [ ] Système de rotation par batch (scalabilité)

---

## 📚 FICHIERS CLÉS

| Fichier | Rôle |
|---------|------|
| `ai_controller.py` | Exécution actions IA |
| `ai_strategy_manager.py` | Logique stratégique |
| `ai_auto_cycle_manager.py` | Gestion preset/fréquence |
| `tick_service.py` | Intégration tick → IA |
| `city_service.py` | Construction bâtiments |
| `research_service.py` | Déblocage technologies |

---

## ❓ FAQ

**Q: Pourquoi l'IA ne passe pas `savegame_data` en paramètre ?**  
R: Pour éviter les conflits. Le tick calcule la production en mémoire, sauvegarde, puis l'IA charge le fichier frais et sauvegarde ses propres modifications.

**Q: Comment l'IA évite-t-elle de construire plusieurs fois le même bâtiment ?**  
R: La stratégie vérifie si le bâtiment existe déjà dans `city.buildings` avant de construire.

**Q: Que se passe-t-il si une construction IA échoue ?**  
R: L'erreur est loggée mais n'arrête pas le système. L'IA réessaiera au prochain cycle.

**Q: L'IA peut-elle dépasser les limites du jeu ?**  
R: Non, elle utilise les mêmes services que les joueurs humains (`city_service`, `research_service`) qui valident toutes les contraintes.

**Q: Comment désactiver complètement l'IA ?**  
R: Mettre `"enabled": false` dans `auto_tick_settings.json` → `ai_auto_cycle`.

---

*Document maintenu à jour avec l'état réel du code.*
