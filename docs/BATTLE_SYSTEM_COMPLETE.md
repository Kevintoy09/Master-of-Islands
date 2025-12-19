# Système de Bataille Complet - Documentation Technique

## Table des Matières

1. [Architecture Globale](#architecture-globale)
2. [Structure des Fichiers de Données](#structure-des-fichiers-de-données)
3. [Flux de Bataille](#flux-de-bataille)
4. [Système d'IA](#système-dia)
5. [Composants Client](#composants-client)
6. [API Backend](#api-backend)
7. [Formats de Données](#formats-de-données)
8. [Débogage et Logs](#débogage-et-logs)

---

## 1. Architecture Globale

### Vue d'ensemble

Le système de bataille est divisé en plusieurs couches :

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT (React/TypeScript)                 │
├─────────────────────────────────────────────────────────────┤
│  SimpleBattlefieldV2.tsx (Orchestrateur principal)          │
│  ├── BattlefieldVisualsV2.tsx (Affichage unités)           │
│  ├── BattlefieldTacticsV2.tsx (Déplacement/Combat)         │
│  ├── useBattlefieldLogic.ts (État et logique)              │
│  └── BattleAIService.ts (Actions IA côté client)           │
└─────────────────────────────────────────────────────────────┘
                              ↕ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                  SERVEUR (Python/Flask)                      │
├─────────────────────────────────────────────────────────────┤
│  battle_routes_v2.py (Routes API)                           │
│  ├── BattleServiceV2 (Logique de bataille)                 │
│  ├── BattleAIServiceV2 (IA côté serveur)                   │
│  ├── CombatServiceV2 (Calculs de combat)                   │
│  └── DeploymentServiceV2 (Gestion déploiement)             │
└─────────────────────────────────────────────────────────────┘
                              ↕ JSON Files
┌─────────────────────────────────────────────────────────────┐
│                  DONNÉES (JSON)                              │
├─────────────────────────────────────────────────────────────┤
│  battlefields_v2.json (État de toutes les batailles)        │
│  battlefield_map_X.json (Templates de cartes)               │
│  unit_stats.json (Statistiques des unités)                  │
│  player_heroes.json (Données des héros)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Structure des Fichiers de Données

### 2.1 battlefields_v2.json

**Localisation** : `server/gamedata/battlefields_v2.json`

**Description** : Fichier central contenant l'état de TOUTES les batailles actives.

**Structure** :

```json
{
  "bfv2_abc123": {
    "battleId": "bfv2_abc123",
    "phase": "deployment",
    "currentRound": 1,
    "currentTurnPlayer": "attacker_player_1",
    "attackerTurnOrder": ["attacker_player_1"],
    "defenderTurnOrder": ["defender_player_2"],
    "map": "battlefield_map_2",
    "participants": {
      "attacker_id": "player_1",
      "defender_id": "player_2",
      "attackers": ["attacker_player_1"],
      "defenders": ["defender_player_2"]
    },
    "teams": {
      "attacker_player_1": [
        {
          "unitId": "attacker_player_1_infantry_light_1",
          "unitType": "infantry_light",
          "position": [10, 18],
          "unitCount": 10,
          "hasActed": false,
          "hasMoved": false
        }
      ],
      "defender_player_2": [...]
    },
    "morale": {
      "attacker": 100,
      "defender": 100
    },
    "wall_system": {
      "wall_groups": {
        "group_0": {
          "group_index": 0,
          "hp": 500,
          "max_hp": 500,
          "positions": [[15, 12], [16, 12]]
        }
      }
    },
    "hexMap": [...],
    "battleStartTime": "2025-12-19T10:30:00",
    "lastActionTime": "2025-12-19T10:31:15"
  }
}
```

**Champs Importants** :

- **phase** : `"deployment"`, `"battle"`, ou `"victory"`
- **currentRound** : Numéro du tour actuel (commence à 1)
- **currentTurnPlayer** : ID du joueur dont c'est le tour (ex: `"attacker_player_1"`)
- **teams** : Dictionnaire des unités par équipe
  - Clé = ID de l'équipe (ex: `"attacker_player_1"`)
  - Valeur = Liste des unités de cette équipe
- **hasActed** : Flag sur chaque unité indiquant si elle a agi ce tour
- **hasMoved** : Flag indiquant si l'unité s'est déplacée ce tour

### 2.2 battlefield_map_X.json

**Localisation** : `server/data/battlefields/battlefield_map_2.json`

**Description** : Template de carte de bataille (terrain, zones de déploiement).

**Structure** :

```json
{
  "template": {
    "id": "custom_battlefield_1_v2",
    "name": "Mon Battlefield Personnalisé",
    "size": {"width": 29, "height": 29},
    "deploymentZones": {
      "attacker": {
        "infantry": [[11,18], [10,18], [12,18]],
        "ranged": [[10,19], [9,19]],
        "cavalry": [[8,18], [8,19]],
        "artillery": [[9,20], [10,20]],
        "support": [[10,21]],
        "hero": [[9,21], [8,21]]
      },
      "defender": {
        "infantry": [[21,7], [20,7]],
        ...
      },
      "backgroundImage": "map_2.jpg"
    }
  },
  "terrainDefinitions": {
    "A": {"name": "base-attack", "defenseBonus": 0, ...},
    "P": {"name": "plains", "defenseBonus": 0, ...},
    "H": {"name": "hill", "defenseBonus": 25, ...}
  },
  "hexMap": [
    "PPPPPPPPPPPPPPPPPPPPPPPPPPPP",
    "PPPPPPPPPPPHHHHHPPPPPPPPPPPP",
    ...
  ]
}
```

### 2.3 unit_stats.json

**Localisation** : `server/data/unit_stats.json`

**Description** : Statistiques de toutes les unités du jeu.

**Structure** :

```json
{
  "classical_age": {
    "archer": {
      "name": "Archer",
      "category": "ranged",
      "hp": 35,
      "attack_melee": 5,
      "attack_ranged": 15,
      "defense_melee": 4,
      "defense_ranged": 8,
      "range": 3,
      "movement": 3,
      "special_abilities": [
        {"target_category": "infantry", "attack_ranged": "+20%"}
      ]
    }
  },
  "enemy_units": {
    "barbarian_archer": {...}
  }
}
```

---

## 3. Flux de Bataille

### 3.1 Phases de Bataille

#### Phase 1 : DEPLOYMENT (Déploiement)

**Durée** : 20 secondes par joueur

**Objectif** : Placer les unités sur les zones de déploiement

**Flux** :

```
1. Client charge la bataille (GET /api/v2/battles/{battleId})
2. Client affiche popup de déploiement (UnitDeploymentPopupV2)
3. Joueur sélectionne unités et positions
4. Client envoie déploiement (POST /api/v2/battles/{battleId}/deploy)
5. Serveur valide et enregistre positions
6. Client recharge bataille mise à jour
7. Timer à 0 → Appel auto-déploiement si non fait
```

**Actions IA en Déploiement** :

```python
# server/app/battle/battle_ai_service_v2.py - execute_ai_deployment()

1. Identifier unités non déployées
2. Récupérer zones de déploiement depuis template
3. Pour chaque unité:
   - Trouver zone appropriée selon catégorie (infantry, ranged, etc.)
   - Choisir position aléatoire disponible
   - Déployer unité
4. Sauvegarder état
```

**Code Client (Auto-déploiement)** :

```typescript
// client/src/components/SimpleBattlefieldV2.tsx
const handleAutoDeployment = async () => {
  if (autoDeployTriggeredRef.current) return;
  autoDeployTriggeredRef.current = true;
  
  const response = await fetch(
    `${getApiUrl()}/api/v2/battles/${actualBattleId}/auto-deploy`,
    {method: 'POST'}
  );
  
  if (response.ok) {
    await loadBattleUnits(actualBattleId);
  }
};
```

#### Phase 2 : BATTLE (Combat)

**Durée** : 20 secondes par tour et par joueur

**Objectif** : Déplacer unités et combattre

**Flux d'un Tour** :

```
1. Tour commence pour currentTurnPlayer
2. Timer de 20s démarre
3. Joueur peut:
   - Sélectionner une unité
   - La déplacer (mouvement <= movement)
   - Attaquer une unité ennemie à portée
4. Après action ou timer = 0:
   - endTurn() appelé
   - currentTurnPlayer change
   - hasActed/hasMoved réinitialisés pour nouveau joueur
5. Si round terminé (tous ont joué):
   - currentRound++
   - Tous les flags hasActed/hasMoved = false
```

**Actions IA en Combat** :

```python
# battle_ai_service_v2.py - execute_ai_turn()

1. Récupérer unités IA du joueur actuel
2. Filtrer unités qui n'ont pas agi (hasActed = False)
3. Pour chaque unité disponible:
   a. Chercher cibles ennemies à portée
   b. Si cible trouvée:
      - Calculer distance
      - Si à portée → ATTAQUER
      - Sinon → SE DÉPLACER vers cible
   c. Si pas de cible:
      - Chercher positions stratégiques
      - SE DÉPLACER vers centre/objectif
4. Appeler end_turn() pour passer au joueur suivant
```

**Logique de Combat** :

```python
# combat_service_v2.py - resolve_combat()

1. Récupérer stats attaquant/défenseur depuis unit_stats.json
2. Calculer distance hexagonale
3. Vérifier portée (distance <= range de l'attaquant)
4. Calculer dégâts:
   - Base = attack_ranged (si distance > 1) ou attack_melee
   - Appliquer special_abilities (bonus/malus par catégorie)
   - Appliquer bonus terrain (defenseBonus)
   - Appliquer aura héros si applicable
5. Réduire unitCount ou hp du défenseur
6. Si défenseur détruit (count/hp = 0):
   - Retirer unité
   - Réduire moral de l'équipe perdante
7. Marquer attaquant hasActed = True
8. Sauvegarder bataille
9. Vérifier conditions de victoire
```

#### Phase 3 : VICTORY (Victoire)

**Conditions de Victoire** :

```python
# battle_service_v2.py - check_victory_conditions()

1. DESTRUCTION TOTALE:
   - Une équipe n'a plus d'unités → Victoire de l'autre

2. MORAL À ZÉRO:
   - moral[team] <= 0 → Défaite de cette équipe

3. TIMEOUT (20 rounds):
   - Round > 20 → Victoire de l'équipe avec le plus d'unités
```

**Transition vers Victory** :

```python
battle['phase'] = 'victory'
battle['winner'] = winner_team  # 'attacker' ou 'defender'
battle['endTime'] = current_time
```

---

## 4. Système d'IA

### 4.1 Déclenchement de l'IA

**Côté Client (Timer)** :

```typescript
// SimpleBattlefieldV2.tsx - useEffect du timer

useEffect(() => {
  if (turnTimeRemaining === 0 && !endTurnCalledRef.current) {
    if (actualGamePhase === 'deployment') {
      // Auto-déploiement si non fait
      handleAutoDeployment();
    } else if (actualGamePhase === 'battle') {
      // Fin de tour automatique
      endTurn();
    }
  }
}, [turnTimeRemaining]);
```

**Côté Serveur (end_turn)** :

```python
# battle_service_v2.py - end_turn()

def end_turn(self, battle_id: str, player_id: str):
    # 1. Changer currentTurnPlayer
    battle['currentTurnPlayer'] = next_player
    
    # 2. Réinitialiser flags pour nouveau joueur
    for unit in get_current_player_units():
        unit['hasActed'] = False
        unit['hasMoved'] = False
    
    # 3. Si nouveau round complet
    if all_players_played:
        battle['currentRound'] += 1
        reset_all_flags()
    
    # 4. Si joueur suivant est IA
    if is_ai_controlled(next_player):
        ai_service.execute_ai_turn(battle_id, next_player)
    
    save_battle()
```

### 4.2 Logique IA - Déploiement

**Fichier** : `server/app/battle/battle_ai_service_v2.py`

**Fonction** : `execute_ai_deployment(battle_id, ai_player_team)`

```python
def execute_ai_deployment(self, battle_id, ai_player_team):
    # 1. Charger bataille et template
    battle = load_battle(battle_id)
    template = load_template(battle['map'])
    
    # 2. Déterminer camp (attacker/defender)
    side = 'attacker' if 'attacker' in ai_player_team else 'defender'
    deployment_zones = template['deploymentZones'][side]
    
    # 3. Pour chaque unité non déployée
    for unit in battle['teams'][ai_player_team]:
        if unit['position'] is None:
            # Déterminer catégorie (infantry, ranged, cavalry, etc.)
            unit_type = extract_unit_type(unit['unitId'])
            category = get_unit_category(unit_type)
            
            # Trouver zone de déploiement
            available_positions = deployment_zones.get(category, [])
            
            # Choisir position libre
            for pos in available_positions:
                if is_position_free(pos, battle):
                    unit['position'] = pos
                    break
    
    # 4. Sauvegarder
    save_battle(battle)
```

### 4.3 Logique IA - Combat

**Fonction** : `execute_ai_turn(battle_id, ai_player_team)`

**Algorithme** :

```python
def execute_ai_turn(self, battle_id, ai_player_team):
    # 1. Récupérer unités IA disponibles
    ai_units = [u for u in battle['teams'][ai_player_team] 
                if not u['hasActed']]
    
    # 2. Pour chaque unité
    for unit in ai_units:
        # A. Chercher cible prioritaire
        target = find_best_target(unit, battle)
        
        if target:
            distance = calculate_hex_distance(unit['position'], target['position'])
            unit_range = get_unit_range(unit['unitType'])
            
            # B. Si à portée → ATTAQUER
            if distance <= unit_range:
                combat_service.resolve_combat(
                    battle_id, unit, target
                )
            
            # C. Sinon → SE DÉPLACER vers cible
            else:
                path = find_path(unit['position'], target['position'])
                movement = get_unit_movement(unit['unitType'])
                new_pos = path[min(len(path)-1, movement)]
                
                move_unit(unit, new_pos)
                unit['hasMoved'] = True
        
        # D. Pas de cible → Mouvement stratégique
        else:
            strategic_pos = find_strategic_position(unit, battle)
            move_unit(unit, strategic_pos)
        
        # E. Marquer unité comme ayant agi
        unit['hasActed'] = True
    
    # 3. Fin du tour IA
    self.battle_service.end_turn(battle_id, ai_player_team)
```

**Sélection de Cible** :

```python
def find_best_target(unit, battle):
    enemies = get_enemy_units(unit, battle)
    
    # Priorité 1: Unités à faible HP
    low_hp = [e for e in enemies if e['hp'] < 30 or e['unitCount'] < 3]
    if low_hp:
        return closest(unit, low_hp)
    
    # Priorité 2: Unités à portée
    in_range = [e for e in enemies if distance(unit, e) <= unit_range]
    if in_range:
        return weakest(in_range)
    
    # Priorité 3: Unité la plus proche
    return closest(unit, enemies)
```

---

## 5. Composants Client

### 5.1 SimpleBattlefieldV2.tsx

**Rôle** : Orchestrateur principal de la bataille

**Responsabilités** :

1. Charger et afficher la bataille
2. Gérer le timer de 20s
3. Coordonner les couches (grille, unités, tactiques)
4. Gérer les popups (déploiement, combat, victoire)
5. Appeler l'API pour les actions (déploiement, attaque, fin de tour)

**État Principal** :

```typescript
const {
  battleGrid,           // Grille hexagonale
  battleUnits,          // Liste des unités
  battleData,           // Données complètes de la bataille
  currentRound,         // Numéro du round
  currentTurnPlayer,    // Joueur actuel
  selectedUnit,         // Unité sélectionnée
  attackerStats,        // Stats attaquant (unités, moral)
  defenderStats,        // Stats défenseur
  handleDeployUnit,     // Déployer unité
  handleAttackRequest,  // Demander attaque
  endTurn,              // Terminer tour
  ...
} = useBattlefieldLogic(props);
```

### 5.2 BattlefieldVisualsV2.tsx

**Rôle** : Affichage des unités sur la grille

**Fonctionnalités** :

- Dessiner chaque unité (icône, nombre, HP)
- Afficher cercle de sélection (range ou aura)
- Afficher indicateur d'aura héros (👑)
- Gérer clics sur unités (sélection, attaque)

**Rendu d'une Unité** :

```tsx
<g key={unit.unitId}>
  {/* Cercle de base */}
  <circle cx={x} cy={y} r="20" fill={teamColor} />
  
  {/* Icône unité */}
  <text x={x} y={y-15}>{isHero ? '👑' : icon}</text>
  
  {/* Nombre ou HP */}
  <text x={x} y={y+3}>{unit.unitCount || unit.hp}</text>
  
  {/* Indicateur aura (si dans aura héros) */}
  {isInHeroAura && <text>👑</text>}
  
  {/* Cercle de sélection (range ou aura_radius) */}
  {isSelected && (
    <circle r={isHero ? auraRadius*60 : range*60} 
            stroke="#FFD700" />
  )}
</g>
```

### 5.3 BattlefieldTacticsV2.tsx

**Rôle** : Gestion du déplacement et du combat

**Fonctionnalités** :

- Calculer hexagones accessibles (mouvement)
- Afficher zone de déplacement possible
- Déplacer unité par drag & drop
- Afficher trajectoire d'attaque
- Déclencher combat

**Calcul de Mouvement** :

```typescript
const calculateAccessibleHexes = (unit) => {
  const movement = getUnitMovement(unit.unitType);
  const accessible = new Set();
  
  // BFS pour trouver tous les hexagones à distance <= movement
  const queue = [{pos: unit.position, dist: 0}];
  while (queue.length > 0) {
    const {pos, dist} = queue.shift();
    if (dist > movement) continue;
    
    accessible.add(hexKey(pos));
    
    // Ajouter voisins
    for (neighbor of getNeighbors(pos)) {
      if (!occupied(neighbor) && !visited(neighbor)) {
        queue.push({pos: neighbor, dist: dist+1});
      }
    }
  }
  
  return accessible;
};
```

### 5.4 useBattlefieldLogic.ts

**Rôle** : Hook centralisé pour la logique de bataille

**Fonctions Principales** :

```typescript
// Charger bataille depuis serveur
const loadBattlefieldData = async (battleId) => {
  const response = await fetch(`/api/v2/battles/${battleId}`);
  const data = await response.json();
  setBattleData(data);
  setBattleGrid(convertHexMap(data.hexMap));
  setBattleUnits(extractUnits(data.teams));
};

// Déployer unité
const handleDeployUnit = async (unitType, position, team) => {
  await fetch(`/api/v2/battles/${battleId}/deploy`, {
    method: 'POST',
    body: JSON.stringify({unitType, position, team})
  });
  await loadBattlefieldData(battleId);
};

// Terminer tour
const endTurn = async () => {
  await fetch(`/api/v2/battles/${battleId}/end-turn`, {
    method: 'POST'
  });
  await loadBattlefieldData(battleId);
};
```

---

## 6. API Backend

### 6.1 Routes Principales

**Fichier** : `server/app/battle/battle_routes_v2.py`

#### GET /api/v2/battles/{battleId}

**Description** : Récupérer état complet de la bataille

**Réponse** :

```json
{
  "battleId": "bfv2_abc123",
  "phase": "battle",
  "currentRound": 3,
  "currentTurnPlayer": "attacker_player_1",
  "teams": {...},
  "morale": {"attacker": 85, "defender": 70},
  ...
}
```

#### POST /api/v2/battles/{battleId}/deploy

**Description** : Déployer une unité

**Body** :

```json
{
  "unitType": "archer",
  "position": [10, 18],
  "team": "attacker_player_1"
}
```

**Traitement** :

```python
def deploy_unit():
    # 1. Valider position (dans zone de déploiement)
    # 2. Créer objet unité
    unit = {
        'unitId': f"{team}_{unitType}_{counter}",
        'unitType': unitType,
        'position': position,
        'unitCount': max_stack_size,
        'hasActed': False,
        'hasMoved': False
    }
    # 3. Ajouter à battle['teams'][team]
    # 4. Sauvegarder
```

#### POST /api/v2/battles/{battleId}/attack

**Description** : Attaquer une unité ennemie

**Body** :

```json
{
  "attackerId": "attacker_player_1_archer_1",
  "defenderId": "defender_player_2_infantry_1"
}
```

**Traitement** :

```python
def attack():
    # 1. Récupérer unités
    attacker = find_unit(attackerId)
    defender = find_unit(defenderId)
    
    # 2. Valider attaque (range, hasActed)
    # 3. Calculer dégâts (combat_service.resolve_combat)
    # 4. Appliquer dégâts à defender
    # 5. Marquer attacker.hasActed = True
    # 6. Vérifier victoire
    # 7. Sauvegarder
```

#### POST /api/v2/battles/{battleId}/move

**Description** : Déplacer une unité

**Body** :

```json
{
  "unitId": "attacker_player_1_cavalry_1",
  "newPosition": [12, 19]
}
```

**Traitement** :

```python
def move_unit():
    # 1. Récupérer unité
    # 2. Valider mouvement (distance, hasMoved)
    # 3. Vérifier position libre
    # 4. Mettre à jour unit['position']
    # 5. Marquer unit['hasMoved'] = True
    # 6. Sauvegarder
```

#### POST /api/v2/battles/{battleId}/end-turn

**Description** : Terminer tour du joueur actuel

**Traitement** :

```python
def end_turn():
    # 1. Changer currentTurnPlayer
    # 2. Réinitialiser hasActed/hasMoved pour nouveau joueur
    # 3. Incrémenter round si tour complet
    # 4. Si joueur suivant est IA → execute_ai_turn()
    # 5. Sauvegarder
```

#### POST /api/v2/battles/{battleId}/auto-deploy

**Description** : Déploiement automatique (IA ou timeout)

**Traitement** :

```python
def auto_deploy():
    # 1. Identifier unités non déployées
    # 2. Appeler ai_service.execute_ai_deployment()
    # 3. Passer à phase 'battle' si tous déployés
```

---

## 7. Formats de Données

### 7.1 Structure d'une Unité

```json
{
  "unitId": "attacker_player_1_archer_5",
  "unitType": "archer",
  "position": [10, 18],
  "unitCount": 12,
  "hp": null,
  "hasActed": false,
  "hasMoved": false,
  "isHero": false
}
```

**Champs** :

- `unitId` : Identifiant unique (format: `{team}_{type}_{counter}`)
- `unitType` : Type d'unité (ex: `archer`, `infantry_light`)
- `position` : `[q, r]` coordonnées hexagonales
- `unitCount` : Nombre d'unités dans le stack (pour unités normales)
- `hp` : Points de vie (pour héros uniquement)
- `hasActed` : A fait une action ce tour (attaque)
- `hasMoved` : S'est déplacé ce tour
- `isHero` : Est un héros (optionnel)

### 7.2 Structure d'un Héros

```json
{
  "unitId": "attacker_player_1_hero_hero_1760731775_d086a0",
  "unitType": "hero",
  "position": [9, 21],
  "hp": 150,
  "hasActed": false,
  "hasMoved": false,
  "isHero": true,
  "heroKey": "hero_1760731775_d086a0"
}
```

**Données Héros (player_heroes.json)** :

```json
{
  "player_1": {
    "heroes": {
      "hero_1760731775_d086a0": {
        "name": "Achille",
        "level": 5,
        "calculated_bonuses": {
          "attack_bonus": 15,
          "defense_bonus": 10,
          "aura_radius": 3
        }
      }
    }
  }
}
```

### 7.3 Coordonnées Hexagonales

**Système** : Cube coordinates (q, r, s avec q + r + s = 0)

**Stockage** : `[q, r]` (s implicite = -q - r)

**Conversion Pixel** :

```typescript
const hexToPixel = (q, r, size = 25) => {
  const x = size * (3/2 * q);
  const y = size * (Math.sqrt(3)/2 * q + Math.sqrt(3) * r);
  return {x, y};
};
```

**Distance** :

```python
def hex_distance(pos1, pos2):
    q1, r1 = pos1
    q2, r2 = pos2
    return (abs(q1 - q2) + abs(q1 + r1 - q2 - r2) + abs(r1 - r2)) // 2
```

**Voisins** :

```python
HEX_DIRECTIONS = [
    [1, 0], [1, -1], [0, -1],
    [-1, 0], [-1, 1], [0, 1]
]

def get_neighbors(pos):
    q, r = pos
    return [[q + dq, r + dr] for dq, dr in HEX_DIRECTIONS]
```

---

## 8. Débogage et Logs

### 8.1 Logs Client

**Console Logs** :

```typescript
// useBattlefieldLogic.ts
console.log('🔍 [LOAD-BATTLEFIELD] battleId:', battleId);
console.log('🖼️ [HOOK] backgroundImage:', bgImage);
console.log('✅ [DEPLOYMENT] Unités déployées');
```

**React DevTools** :

- Inspecter état de `useBattlefieldLogic`
- Vérifier props de `SimpleBattlefieldV2`
- Observer re-renders

### 8.2 Logs Serveur

**Fichier** : `server/app/battle/battle_service_v2.py`

```python
logger.info(f"[BATTLE] Phase changed: {old_phase} → {new_phase}")
logger.debug(f"[AI] Executing turn for {ai_player_team}")
logger.error(f"[COMBAT] Attack failed: {error}")
```

**Vérification Fichier** :

```python
# Charger bataille
with open('server/gamedata/battlefields_v2.json', 'r') as f:
    data = json.load(f)
    battle = data.get(battle_id)
    print(json.dumps(battle, indent=2))
```

### 8.3 Points de Debug Critiques

**1. Vérifier Tour Actuel** :

```python
battle = load_battle(battle_id)
print(f"Round: {battle['currentRound']}")
print(f"Current Player: {battle['currentTurnPlayer']}")
print(f"Phase: {battle['phase']}")
```

**2. Vérifier Unités** :

```python
for team, units in battle['teams'].items():
    print(f"\n{team}:")
    for unit in units:
        print(f"  {unit['unitId']}")
        print(f"    Position: {unit['position']}")
        print(f"    hasActed: {unit['hasActed']}")
        print(f"    hasMoved: {unit['hasMoved']}")
```

**3. Vérifier IA** :

```python
is_ai = is_ai_controlled_team(current_player)
print(f"Is AI controlled: {is_ai}")
```

**4. Tracer Déploiement** :

```python
# Avant déploiement
non_deployed = [u for u in units if u['position'] is None]
print(f"Unités non déployées: {len(non_deployed)}")

# Après déploiement
print(f"Toutes déployées: {all(u['position'] for u in units)}")
```

---

## 9. Problèmes Courants et Solutions

### 9.1 Double Déploiement IA

**Symptôme** : L'IA déploie alors que le joueur a déjà déployé manuellement

**Cause** : Timer appelle `auto-deploy` sans vérifier si déploiement déjà fait

**Solution** :

```python
# Vérifier si unités déjà déployées
def auto_deploy(battle_id):
    battle = load_battle(battle_id)
    team = battle['currentTurnPlayer']
    units = battle['teams'][team]
    
    # Si toutes les unités sont déjà déployées, ne rien faire
    if all(u['position'] is not None for u in units):
        return {"message": "Already deployed"}
    
    # Sinon, déployer
    ai_service.execute_ai_deployment(battle_id, team)
```

### 9.2 Unités Fantômes

**Symptôme** : Unités affichées mais absentes de battlefields_v2.json

**Cause** : Cache client non rafraîchi ou corruption JSON

**Solution** :

```bash
# Vider cache React
rm -rf client/node_modules/.cache

# Vérifier JSON
python -m json.tool server/gamedata/battlefields_v2.json
```

### 9.3 Timer ne Se Déclenche Pas

**Symptôme** : Timer reste bloqué à 20s

**Cause** : `useEffect` du timer pas déclenché ou `turnTimeRemaining` non mis à jour

**Solution** :

```typescript
// Vérifier dépendances useEffect
useEffect(() => {
  // Timer logic
}, [turnTimeRemaining, currentTurnPlayer, actualGamePhase]);

// Forcer reset
setTurnTimeRemaining(20);
```

### 9.4 Moral Négatif

**Symptôme** : `morale['attacker']` = -50

**Cause** : Pas de vérification min(0, moral)

**Solution** :

```python
# battle_service_v2.py
battle['morale'][loser_team] = max(0, current_moral - moral_loss)
```

---

## 10. Optimisations et Bonnes Pratiques

### 10.1 Performance

1. **Charger bataille une seule fois** : Utiliser `refreshTrigger` au lieu de recharger constamment
2. **Mémoriser calculs** : `useMemo` pour `battlefieldBounds`, `accessibleHexes`
3. **Lazy loading** : Charger `unit_stats.json` une seule fois au montage

### 10.2 Sécurité

1. **Valider côté serveur** : Ne jamais faire confiance au client
2. **Vérifier propriété** : Le joueur contrôle-t-il cette unité ?
3. **Vérifier tour** : Est-ce le tour de ce joueur ?

```python
def validate_action(player_id, battle):
    if battle['currentTurnPlayer'] != get_player_team(player_id):
        raise Unauthorized("Not your turn")
```

### 10.3 Maintenabilité

1. **Séparer logique métier** : Services vs Routes vs Composants
2. **Types TypeScript** : Interfaces claires pour unités, batailles
3. **Documentation** : Commenter algorithmes complexes (pathfinding, IA)

---

## Conclusion

Ce système de bataille est complexe mais bien structuré :

- **Serveur** : Authorité sur l'état, calculs, IA
- **Client** : Affichage, interactions, UX
- **Données** : Format JSON centralisé dans `battlefields_v2.json`

**Flux Typique** :

```
1. Client charge bataille
2. Joueur fait action (déploie/déplace/attaque)
3. Client envoie requête API
4. Serveur valide et met à jour battlefields_v2.json
5. Si tour IA → Serveur exécute IA automatiquement
6. Client recharge bataille mise à jour
7. Répéter jusqu'à victoire
```

**Fichiers Clés à Surveiller** :

- `server/gamedata/battlefields_v2.json` - État central
- `server/app/battle/battle_service_v2.py` - Logique serveur
- `client/src/hooks/useBattlefieldLogic.ts` - Logique client
- `server/app/battle/battle_ai_service_v2.py` - IA
