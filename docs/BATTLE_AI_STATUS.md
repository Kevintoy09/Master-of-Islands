# 🤖 IA DE COMBAT - ÉTAT ACTUEL & ROADMAP

*Date : 17 décembre 2024*

---

## ✅ CE QUI FONCTIONNE ACTUELLEMENT

### 1. **IA Basique Opérationnelle**
- ✅ L'IA se déclenche automatiquement quand le timer expire (10s)
- ✅ Fonctionne même si le joueur est déconnecté (serveur-side)
- ✅ Auto-déploiement au Round 1
- ✅ Combat automatique à partir du Round 2

### 2. **Algorithme Actuel**
Fichier : `server/app/ai/battle_ai_basic.py`

**Logique de décision :**
```python
1. Trouver toutes les unités disponibles (qui n'ont pas encore joué ce round)
2. CHOISIR LA PREMIÈRE UNITÉ (⚠️ limitation actuelle)
3. Trouver tous les ennemis
4. Calculer la distance à chaque ennemi (distance hexagonale)
5. Trier par distance (plus proche en premier)
6. DÉCISION :
   - Si ennemi à portée 1 → ATTAQUER
   - Sinon → SE DÉPLACER d'une case vers l'ennemi le plus proche
```

### 3. **Logs Opérationnels**
```
⏰ [BATTLE-TIMER] Timer expiré pour player_1 (Round 2, Status: deployment)
🔍 [BATTLE-TIMER] Joueur player_1 a agi ce round ? False
⚠️ [BATTLE-TIMER] Joueur player_1 n'a PAS agi → Action automatique
🤖 [BATTLE-TIMER] Déclenchement IA pour player_1 dans bfv2_xxx
🤖 [IA] Début tour IA pour player_1 dans bfv2_xxx
🎯 [IA] 2 unités disponibles
🎯 [IA] Unité sélectionnée: auto_attacker_player_1_militia_0
🚶 [IA] Déplacement de auto_attacker_player_1_militia_0 vers [8, 6]
✅ [IA] Déplacement réussi
✅ [BATTLE-TIMER] IA a effectué une action pour player_1
```

---

## 🔴 LIMITATIONS ACTUELLES

### 1. **Une Seule Unité par Tour**
**Problème :** L'IA ne joue qu'une seule unité par tour du joueur
```python
# ❌ Code actuel (ligne 54 de battle_ai_basic.py)
selected_unit = available_units[0]  # Prend seulement la première
```

**Impact :**
- Si le joueur a 5 unités, seulement 1 agit par tour
- Les autres unités restent immobiles
- Stratégie très limitée

**Solution :** Boucler sur toutes les unités disponibles

### 2. **Pas de Priorisation des Cibles**
**Problème :** Attaque toujours l'ennemi le plus proche

**Impact :**
- Ne cible pas les unités faibles pour kill rapide
- Ne protège pas les unités importantes
- Pas de focus fire (concentration de tir)

**Solution attendue :**
- Priorité aux unités blessées (kill facile)
- Priorité aux unités dangereuses (archers, héros)
- Système de menace/valeur

### 3. **Pas de Stratégie de Formation**
**Problème :** Chaque unité agit indépendamment

**Impact :**
- Pas de ligne de front
- Pas de protection des archers
- Unités isolées facilement tuées

### 4. **Pas de Gestion des Capacités Spéciales**
**Problème :** N'utilise pas les capacités (héros, archers longue portée, etc.)

### 5. **Pas de Retraite Tactique**
**Problème :** Continue d'attaquer même avec HP bas

---

## 🎯 SYSTÈME DE DÉCISION - CAHIER DES CHARGES

### Architecture Complète Existante
📄 Voir : `docs/AI_SYSTEM_SPECIFICATION.md` (1456 lignes)

**Modules TypeScript existants (client-side) :**
```
client/src/services/tactical-ai/
├── TacticalAI.ts              # Orchestrateur principal
├── StrategicAnalyzer.ts       # Analyse stratégique
├── TacticalEvaluator.ts       # Évaluation tactique
├── DecisionEngine.ts          # Moteur de décision
├── FormationManager.ts        # Gestion des formations
├── TargetSelector.ts          # Sélection de cibles
├── MovementPlanner.ts         # Planification déplacements
├── ThreatAssessment.ts        # Évaluation menaces
├── SupportCoordinator.ts      # Coordination support
└── types.ts                   # Types TypeScript
```

**⚠️ Ces fichiers existent MAIS sont côté client (TypeScript)**
- Ne fonctionnent PAS quand le joueur est déconnecté
- Doivent être portés en Python côté serveur

---

## 🛠️ ROADMAP - PROCHAINES ÉTAPES

### **Phase 1 : TOUTES LES UNITÉS JOUENT** ⏱️ 30 min
**Objectif :** Chaque unité du joueur agit pendant son tour

**Modifications :**
```python
# Dans battle_ai_basic.py - execute_ai_turn()

# ❌ AVANT
selected_unit = available_units[0]
# ... une seule action

# ✅ APRÈS
for selected_unit in available_units:
    # Décision pour cette unité
    # Attaque ou déplacement
    # Passer à l'unité suivante
```

**Résultat attendu :**
- ✅ Si 5 unités disponibles → 5 actions par tour
- ✅ Stratégie plus efficace
- ✅ Combat plus dynamique

---

### **Phase 2 : PRIORISATION DES CIBLES** ⏱️ 1-2h
**Objectif :** Choisir intelligemment quelle unité attaquer

**Système de score :**
```python
def calculate_target_priority(target, attacker):
    score = 0
    
    # 1. HP bas = cible prioritaire (kill facile)
    if target['hp'] < 30:
        score += 50
    
    # 2. Type d'unité (archers > infanterie)
    if target['type'] in ['archer', 'hero']:
        score += 30
    
    # 3. Distance (plus proche = mieux)
    distance = hex_distance(attacker['pos'], target['pos'])
    score += (10 - distance) * 5
    
    # 4. Menace (attaque-t-il nos alliés ?)
    if target['has_attacked_ally']:
        score += 20
    
    return score
```

**Modifications :**
```python
# Au lieu de :
targets_with_distance.sort(key=lambda x: x['distance'])

# Utiliser :
targets_with_priority = [
    {
        'unit': enemy,
        'priority': calculate_target_priority(enemy, selected_unit)
    }
    for enemy in enemy_units
]
targets_with_priority.sort(key=lambda x: -x['priority'])  # Plus haut score en premier
```

---

### **Phase 3 : FORMATIONS & COORDINATION** ⏱️ 3-5h
**Objectif :** Les unités travaillent ensemble (comme Age of Empires)

**Concepts :**
1. **Ligne de front** : Infanterie lourde en première ligne
2. **Arrière-garde** : Archers protégés derrière
3. **Flancs** : Cavalerie sur les côtés
4. **Focus Fire** : Plusieurs unités sur une même cible

**Exemple de formation :**
```
    A A A         A = Archer (arrière)
  I I I I I       I = Infantry (front)
    C   C         C = Cavalry (flancs)
```

**Algorithme :**
```python
def assign_formation_roles(units):
    roles = {
        'front_line': [],      # Infanterie lourde
        'back_line': [],       # Archers, lanciers
        'flankers': [],        # Cavalerie
        'support': []          # Héros, shamans
    }
    
    for unit in units:
        if unit['defense'] > 50:
            roles['front_line'].append(unit)
        elif unit['range'] > 1:
            roles['back_line'].append(unit)
        elif unit['speed'] > 3:
            roles['flankers'].append(unit)
        else:
            roles['support'].append(unit)
    
    return roles

def move_to_formation(unit, role, battlefield):
    if role == 'front_line':
        # Se déplacer vers la ligne de front (centre)
        target = get_front_line_position()
    elif role == 'back_line':
        # Rester à distance derrière la front line
        target = get_back_line_position()
    # etc.
```

---

### **Phase 4 : PORTAGE TYPESCRIPT → PYTHON** ⏱️ 5-10h
**Objectif :** Porter les modules avancés existants en Python

**Fichiers à porter en priorité :**

1. **TargetSelector.ts → target_selector.py**
   - Sélection intelligente de cibles
   - Système de menaces
   - Priorités dynamiques

2. **FormationManager.ts → formation_manager.py**
   - Gestion des formations
   - Positionnement tactique
   - Cohésion d'unités

3. **ThreatAssessment.ts → threat_assessment.py**
   - Évaluation des menaces
   - Prédiction des attaques ennemies
   - Zones dangereuses

4. **MovementPlanner.ts → movement_planner.py**
   - Pathfinding intelligent
   - Évitement d'obstacles
   - Positionnement optimal

**Méthodologie :**
```
1. Lire le fichier TypeScript
2. Identifier les fonctions clés
3. Récrire en Python avec mêmes algorithmes
4. Tester avec les mêmes cas d'usage
5. Comparer les résultats
```

---

### **Phase 5 : NIVEAUX DE DIFFICULTÉ** ⏱️ 2-3h
**Objectif :** 3 niveaux d'IA configurables

**Paramètres à ajuster :**
```python
AI_DIFFICULTY = {
    'easy': {
        'reaction_time': 3000,      # 3s de délai
        'error_rate': 0.15,         # 15% de mauvaises décisions
        'target_priority': 'random', # Cible aléatoire
        'formation': False,         # Pas de formation
        'focus_fire': False,        # Pas de focus
        'retreat_threshold': 10     # Fuit à 10% HP
    },
    'medium': {
        'reaction_time': 1000,      # 1s de délai
        'error_rate': 0.05,         # 5% d'erreurs
        'target_priority': 'basic', # Cible proche + blessée
        'formation': True,          # Formation basique
        'focus_fire': True,         # Focus sur cibles faibles
        'retreat_threshold': 25     # Fuit à 25% HP
    },
    'hard': {
        'reaction_time': 500,       # 0.5s (très réactif)
        'error_rate': 0.01,         # 1% d'erreurs seulement
        'target_priority': 'advanced', # Système complet
        'formation': True,          # Formations avancées
        'focus_fire': True,         # Focus optimal
        'retreat_threshold': 40,    # Fuit à 40% HP (prudent)
        'micro_management': True    # Micro-gestion (kiting, etc.)
    }
}
```

**Implémentation :**
```python
def make_decision(unit, enemies, difficulty='medium'):
    config = AI_DIFFICULTY[difficulty]
    
    # Introduire des erreurs aléatoires
    if random.random() < config['error_rate']:
        return random_action()
    
    # Appliquer le système de priorité approprié
    if config['target_priority'] == 'random':
        target = random.choice(enemies)
    elif config['target_priority'] == 'basic':
        target = get_closest_or_weakest(enemies, unit)
    else:  # advanced
        target = calculate_best_target(enemies, unit)
    
    return create_action(unit, target)
```

---

## 📊 MÉTRIQUES DE SUCCÈS

### KPIs à mesurer :
- ⏱️ **Temps moyen de combat** (avec/sans IA)
- 💀 **Ratio kills/deaths** de l'IA
- 🎯 **% de victoires** (facile < 30%, moyen ~50%, difficile > 70%)
- 📈 **Courbe d'apprentissage** : IA s'améliore-t-elle ?
- 🤖 **Indiscernabilité** : peut-on distinguer IA vs humain ?

---

## 🔧 FICHIERS MODIFIÉS

### Serveur (Python)
- ✅ `server/app/ai/battle_ai_basic.py` - IA basique créée
- ✅ `server/app/business/battle_timer_service.py` - Intégration IA

### Client (TypeScript)
- ✅ `client/src/hooks/useBattlefieldLogic.ts` - Polling avec recharge unités

### Documentation
- ✅ `docs/AI_SYSTEM_SPECIFICATION.md` - Cahier des charges complet (1456 lignes)
- ✅ `docs/BATTLE_AI_STATUS.md` - Ce document

---

## 💡 PROCHAINE ACTION IMMÉDIATE

### **FIX #1 : Actualisation affichage** ✅ FAIT
Ajout de `loadBattleUnits()` dans le polling (toutes les 2s)

### **TODO #1 : Toutes les unités jouent**
Modifier `battle_ai_basic.py` ligne 54 :
```python
# Remplacer :
selected_unit = available_units[0]

# Par une boucle :
for selected_unit in available_units:
    # ... logique existante
```

**Question :** Commencer par TODO #1 maintenant ?
