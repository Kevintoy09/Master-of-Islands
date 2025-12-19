# 🤖 SYSTÈME D'IA - CAHIER DES CHARGES COMPLET

## 📋 TABLE DES MATIÈRES
1. [Vue d'ensemble](#vue-densemble)
2. [Architecture technique](#architecture-technique)
3. [Modules fonctionnels](#modules-fonctionnels)
4. [Configuration](#configuration)
5. [Système de décision](#système-de-décision)
6. [Intégration](#intégration)
7. [Roadmap d'implémentation](#roadmap-dimplémentation)

---

## 🎯 VUE D'ENSEMBLE

### Objectif
Créer un système d'IA modulaire, configurable et extensible qui simule des joueurs réalistes indiscernables des joueurs humains (comme Age of Empire). L'IA doit peupler les serveurs pour éviter qu'ils soient vides (problème d'Ikariam) avec :
- **Comportement autonome** : joue complètement seule sans intervention
- **Simulation de connexion** : plages horaires variables (comme un joueur réel)
- **Adaptabilité** : s'ajuste automatiquement aux changements de constantes du jeu
- **Personnalités multiples** : comportements variés (agressif, économique, équilibré)
- **Niveaux de difficulté** : facile, moyen, difficile
- **Intégration réaliste** : difficile de distinguer une IA d'un joueur humain

### Contexte du jeu (temps réel)
Le jeu se déroule en **temps réel** comme Ikariam avec 3 phases majeures :

#### **Phase 1 : Âge Antique (~15 jours)**
- 4 ressources de base disponibles : **Pierre, Céréales, Papyrus, Fer**
- Choix de l'île de départ (spécialisation stratégique) :
  - **Pierre** → Construction de bâtiments plus rapide
  - **Céréales** → Croissance de population accélérée
  - **Papyrus** → Développement de l'arbre de recherche
  - **Fer** → Production militaire (pillage villages barbares)
- Colonisation possible après 2-3 jours (selon réglages)
- Objectif : équilibrer les 4 ressources de base via colonisation

#### **Phase 2 : Âge Classique (~15 jours après Phase 1)**
- 4 nouvelles ressources débloquées : **Marbre, Chevaux, Vin, Cristal**
  - **Marbre** → Bâtiments avancés
  - **Chevaux** → Cavalerie (unités avancées)
  - **Vin** → Moral de l'armée + croissance
  - **Cristal** → Recherches avancées
- Stratégies plus complexes (île-banque, alliances, commerce intensif)

#### **Phase 3 : Découverte du Nouveau Monde (~30 jours)**
- Nouveau super-continent avec 4 ressources exotiques : **Charbon, Poudre, Épices, Coton**
- Expansion maritime importante
- (En développement)

### Principes fondamentaux
✅ **Pas de triche** : utilise les mêmes règles que les joueurs humains
✅ **Configuration externe** : tous les paramètres dans `ai_config.json`
✅ **Lecture dynamique** : charge buildings.json, units.json, research.json
✅ **Modularité** : chaque fonctionnalité = module activable/désactivable
✅ **Extensibilité** : facile d'ajouter de nouveaux comportements
✅ **Réalisme** : indiscernable d'un joueur humain (connexions, erreurs, stratégies variées)
✅ **Équilibre serveur** : ratio 3-4 IAs pour 10-15 joueurs par île

---

## 🏗️ ARCHITECTURE TECHNIQUE

### Structure de fichiers
```
server/app/ai/
├── __init__.py
├── ai_controller.py          # Contrôleur principal
├── decision_engine.py         # Système de décision
├── personality.py             # Définition des personnalités
├── modules/
│   ├── __init__.py
│   ├── base_module.py        # Classe abstraite
│   ├── city_builder.py       # Construction de bâtiments
│   ├── resource_manager.py   # Gestion ressources/travailleurs
│   ├── economy_manager.py    # Commerce/transport
│   ├── colonizer.py          # Expansion/colonisation
│   ├── military_manager.py   # Armée/attaques
│   ├── hero_manager.py       # Gestion des héros
│   ├── research_manager.py   # Arbre de recherche
│   └── defense_manager.py    # Défense/réactions
├── strategies/
│   ├── __init__.py
│   ├── economic.py           # Stratégie économique
│   ├── military.py           # Stratégie militaire
│   ├── balanced.py           # Stratégie équilibrée
│   └── bank_island.py        # Stratégie île-banque
├── utils/
│   ├── __init__.py
│   ├── data_loader.py        # Lecture buildings/units/research
│   ├── calculator.py         # Calculs (coûts, temps, etc.)
│   ├── activity_simulator.py # Simulation de connexion
│   └── priority_queue.py     # File de priorité pour actions
└── config/
    └── ai_config.json        # Configuration globale
```

### Configuration (`ai_config.json`)
```json
{
  "global": {
    "enabled": true,
    "tick_execution": true,
    "manual_api_enabled": true
  },
  "population_control": {
    "max_ai_per_island": 4,
    "max_human_per_island": 15,
    "ai_spawn_strategy": "progressive",
    "ai_to_human_ratio": 0.3,
    "spawn_delay_days": 1
  },
  "game_phases": {
    "phase_1_antique": {
      "duration_days": 15,
      "available_resources": ["wood", "stone", "iron", "cereal", "papyrus"],
      "ai_colonization_delay_days": 2.5,
      "ai_development_speed_multiplier": 1.0
    },
    "phase_2_classical": {
      "start_day": 15,
      "duration_days": 15,
      "available_resources": ["marble", "horse", "wine", "glass"],
      "ai_development_speed_multiplier": 1.1
    },
    "phase_3_new_world": {
      "start_day": 30,
      "available_resources": ["coal", "gunpowder", "spices", "cotton"],
      "ai_development_speed_multiplier": 1.2
    }
  },
  "activity_simulation": {
    "enabled": true,
    "sessions_per_day": {
      "min": 3,
      "max": 8
    },
    "session_duration_minutes": {
      "min": 15,
      "max": 120
    },
    "night_mode": {
      "enabled": true,
      "start_hour": 23,
      "end_hour": 7,
      "activity_probability": 0.1
    }
  },
  "personalities": {
    "economic": {
      "enabled": true,
      "priorities": {
        "economy": 10,
        "construction": 8,
        "military": 3,
        "expansion": 7,
        "research": 9
      },
      "modules": {
        "city_builder": true,
        "resource_manager": true,
        "economy_manager": true,
        "colonizer": true,
        "military_manager": false,
        "hero_manager": false,
        "research_manager": true,
        "defense_manager": true
      }
    },
    "military": {
      "enabled": true,
      "priorities": {
        "economy": 6,
        "construction": 7,
        "military": 10,
        "expansion": 9,
        "research": 5
      },
      "modules": {
        "city_builder": true,
        "resource_manager": true,
        "economy_manager": true,
        "colonizer": true,
        "military_manager": true,
        "hero_manager": true,
        "research_manager": true,
        "defense_manager": true
      }
    },
    "balanced": {
      "enabled": true,
      "priorities": {
        "economy": 8,
        "construction": 8,
        "military": 7,
        "expansion": 8,
        "research": 8
      },
      "modules": {
        "city_builder": true,
        "resource_manager": true,
        "economy_manager": true,
        "colonizer": true,
        "military_manager": true,
        "hero_manager": true,
        "research_manager": true,
        "defense_manager": true
      }
    }
  },
  "difficulty": {
    "easy": {
      "decision_delay_seconds": {"min": 30, "max": 120},
      "error_probability": 0.15,
      "optimization_level": 0.6,
      "resource_threshold_multiplier": 1.5
    },
    "medium": {
      "decision_delay_seconds": {"min": 10, "max": 60},
      "error_probability": 0.05,
      "optimization_level": 0.85,
      "resource_threshold_multiplier": 1.2
    },
    "hard": {
      "decision_delay_seconds": {"min": 5, "max": 30},
      "error_probability": 0.0,
      "optimization_level": 1.0,
      "resource_threshold_multiplier": 1.0
    }
  },
  "modules_config": {
    "city_builder": {
      "check_interval_ticks": 5,
      "island_specialization": {
        "stone": ["townhall", "warehouse", "wall"],
        "iron": ["barracks", "workshop"],
        "cereal": ["windmill", "warehouse"],
        "papyrus": ["academy", "library"]
      },
      "priority_buildings": ["townhall", "windmill", "warehouse", "academy"]
    },
    "resource_manager": {
      "check_interval_ticks": 3,
      "worker_reallocation_threshold": 0.2,
      "starvation_prevention_buffer": 1000,
      "plague_cure_priority": "immediate"
    },
    "economy_manager": {
      "check_interval_ticks": 10,
      "market_buy_threshold": 0.3,
      "market_sell_threshold": 2.0,
      "transport_trigger_ratio": 0.5,
      "bank_island_strategy": {
        "enabled": true,
        "min_cities_before_activate": 3,
        "resource_concentration_ratio": 0.7
      }
    },
    "colonizer": {
      "check_interval_ticks": 50,
      "min_city_level_before_expand": 5,
      "prioritize_missing_resources": true,
      "max_cities_per_ai": "dynamic",
      "starting_island_strategy": {
        "phase_1": {
          "stone": {"priority": 0.25, "reason": "construction_speed"},
          "cereal": {"priority": 0.25, "reason": "population_growth"},
          "papyrus": {"priority": 0.25, "reason": "research_speed"},
          "iron": {"priority": 0.25, "reason": "military_power"}
        },
        "balanced_distribution": true
      },
      "colonization_strategy": {
        "phase_1_goal": "collect_4_basic_resources",
        "prioritize_high_donation_sites": true,
        "prioritize_populated_islands": true,
        "consider_transport_distance": true,
        "target_resource_diversity": 0.8
      }
    },
    "military_manager": {
      "check_interval_ticks": 20,
      "min_units_before_attack": 10,
      "barbarian_priority": true,
      "army_composition": {
        "infantry": 0.4,
        "ranged": 0.3,
        "cavalry": 0.2,
        "siege": 0.1
      }
    },
    "hero_manager": {
      "check_interval_ticks": 30,
      "auto_deploy": true,
      "upgrade_priority": ["attack", "defense", "health"]
    },
    "research_manager": {
      "check_interval_ticks": 15,
      "prioritize_by_personality": true
    }
  }
}
```

---

## 🧩 MODULES FONCTIONNELS

### 1. **CityBuilderModule**
**Responsabilité** : Construction et amélioration des bâtiments

**Logique de décision** :
1. **Vérifier les besoins critiques** :
   - Famine ? → Windmill priorité absolue
   - Peste ? → Thermes priorité haute
   - Population bloquée ? → Entrepôt/Logements

2. **Spécialisation selon ressource d'île** :
   - Pierre → murs, défenses
   - Fer → caserne, atelier
   - Céréales → moulins, entrepôts
   - Papyrus → académie, bibliothèque

3. **Lecture dynamique depuis `buildings.json`** :
   ```python
   def get_building_data(self, building_type):
       buildings = load_json('buildings.json')
       return buildings.get(building_type)
   
   def calculate_build_cost(self, building_type, level):
       data = self.get_building_data(building_type)
       base_cost = data['levels'][level]['cost']
       return base_cost
   ```

4. **Ordre de construction selon difficulté** :
   - Facile : ordre semi-aléatoire avec priorités basiques
   - Moyen : ordre optimisé avec quelques variations
   - Difficile : ordre optimal strict

**Exemple de priorités** :
```python
PRIORITY_MATRIX = {
    'critical': ['windmill', 'thermes'],  # Survie
    'high': ['townhall', 'warehouse'],     # Développement
    'medium': ['academy', 'barracks'],     # Fonctionnalités
    'low': ['decorations']                 # Bonus
}
```

---

### 2. **ResourceManagerModule**
**Responsabilité** : Gestion des travailleurs et équilibrage des ressources

**Logique de décision** :
1. **Détection des déséquilibres** :
   ```python
   def analyze_resource_balance(self, city):
       production = self.calculate_production(city)
       consumption = self.calculate_consumption(city)
       
       for resource in ['wood', 'stone', 'iron', 'cereal']:
           balance = production[resource] - consumption[resource]
           if balance < -100:  # Pénurie
               self.increase_workers(city, resource)
           elif balance > 500:  # Surplus
               self.decrease_workers(city, resource)
   ```

2. **Prévention de la famine** :
   - Seuil critique : céréales < 1000 → réaffecter immédiatement
   - Buffer de sécurité configurable

3. **Gestion de la peste** :
   - Détection → cure immédiate si or disponible
   - Sinon → vendre ressources au marché pour obtenir or

4. **Optimisation recherche vs production** :
   - Papyrus → plus de chercheurs
   - Autres ressources → plus de producteurs

---

### 3. **EconomyManagerModule**
**Responsabilité** : Commerce et transport entre villes

**Logique de décision** :
1. **Achat au marché** :
   ```python
   def should_buy_resource(self, resource, city):
       if city.resources[resource] < threshold:
           market_price = get_market_price(resource)
           if market_price < acceptable_price:
               return True
       return False
   ```

2. **Vente au marché** :
   - Si surplus > 2x consommation → vendre
   - Prix minimum configurable

3. **Transport inter-villes** :
   - Ville A surplus + Ville B manque → transport
   - Prioriser ville en construction active

4. **Stratégie île-banque** :
   - Activée si ≥ 3 villes
   - Choisir ville la mieux défendue
   - Centraliser 70% des ressources
   - Redistribuer sur demande

---

### 4. **ColonizerModule**
**Responsabilité** : Expansion et colonisation

**Logique de décision** :
1. **Choix de l'île de départ (spawn)** :
   ```python
   def choose_starting_island(self, personality):
       # Distribution équilibrée entre les 4 types
       if personality == "military":
           return random.choice(["iron", "cereal"])  # Armée + population
       elif personality == "economic":
           return random.choice(["stone", "papyrus"])  # Construction + recherche
       else:
           return random.choice(["stone", "cereal", "papyrus", "iron"])
   ```

2. **Conditions de colonisation** :
   - Niveau ambassade suffisant
   - Ville existante développée (niveau ≥ 5)
   - Ressources disponibles pour colonie
   - Délai respecté (2-3 jours selon phase)

3. **Choix de la ressource (Phase 1)** :
   ```python
   def choose_colonization_target(self, ai_player):
       # Objectif : collecter les 4 ressources de base
       owned_resources = self.get_owned_resource_types(ai_player)
       missing_basic = set(["stone", "cereal", "papyrus", "iron"]) - owned_resources
       
       if missing_basic:
           return self.prioritize_by_need(missing_basic)  # Ressource manquante
       else:
           return self.choose_strategic_resource()  # Diversification
   ```

4. **Sélection de l'île** :
   ```python
   def select_best_island(self, resource_type):
       candidates = get_islands_by_resource(resource_type)
       
       # Critères de sélection
       for island in candidates:
           score = 0
           
           # 1. Prioriser îles avec joueurs actifs (sites améliorés)
           score += island.player_count * 10
           
           # 2. Niveau des sites de production (dons cumulés)
           score += island.donation_level * 20
           
           # 3. Distance depuis capitale (transport)
           distance = calculate_distance(ai_player.capital, island)
           score -= distance * 2
           
           # 4. Respecter limite (max 4 IAs par île)
           if island.ai_count >= 4:
               score = 0
           
           island.score = score
       
       return sorted(candidates, key=lambda i: i.score, reverse=True)[0]
   ```

5. **Respecter les limites** :
   - Max 4 joueurs/île (système existant)
   - Max 3-4 IAs par île (nouveau)
   - Équilibrer la distribution des IAs sur les îles

---

### 5. **MilitaryManagerModule**
**Responsabilité** : Production d'unités et attaques

**Logique de décision** :
1. **Production d'unités** :
   - Lecture dynamique depuis `units.json`
   - Composition équilibrée : 40% infanterie, 30% archers, 20% cavalerie, 10% siège

2. **Attaques de villages barbares** :
   ```python
   def select_barbarian_target(self, city):
       villages = get_nearby_barbarian_villages(city)
       # Prioriser : niveau faible, distance courte, récompenses élevées
       return sorted(villages, key=lambda v: v.level - v.distance)[0]
   ```

3. **Attaques de joueurs** :
   - Analyser défense ennemie
   - Attaquer si avantage > 2:1
   - Prioriser villes avec ressources élevées

4. **Pas d'attaque si** :
   - Économie faible
   - Ville en développement
   - Unités insuffisantes

---

### 6. **HeroManagerModule**
**Responsabilité** : Gestion et amélioration des héros

**Logique de décision** :
1. **Déploiement automatique** :
   - Héros envoyés en bataille avec armées
   - Positionnement selon type (tank devant, soutien derrière)

2. **Amélioration prioritaire** :
   - Attaque → Défense → Santé
   - Investir or/ressources selon disponibilité

---

### 7. **ResearchManagerModule**
**Responsabilité** : Arbre de recherche

**Logique de décision** :
1. **Lecture dynamique depuis `research.json`**
2. **Prioriser selon personnalité** :
   - Économique → technologies commerciales
   - Militaire → technologies militaires
   - Équilibré → mix

---

### 8. **DefenseManagerModule**
**Responsabilité** : Réaction aux attaques

**Logique de décision** :
1. **Détection d'attaque entrante**
2. **Contre-mesures** :
   - Déployer défenses
   - Envoyer renforts depuis autres villes
   - Préparer contre-attaque

---

## 🎮 SYSTÈME DE DÉCISION

### Architecture du Decision Engine
```python
class AIDecisionEngine:
    def __init__(self, ai_player, personality, difficulty):
        self.ai_player = ai_player
        self.personality = personality
        self.difficulty = difficulty
        self.modules = self._load_modules()
        self.priority_queue = PriorityQueue()
        self.game_phase = self._detect_game_phase()
    
    def tick(self):
        """Appelé à chaque tick si IA active"""
        if not self.is_active():
            return
        
        # Détecter changement de phase
        current_phase = self._detect_game_phase()
        if current_phase != self.game_phase:
            self._on_phase_change(current_phase)
            self.game_phase = current_phase
        
        # 1. Collecter les actions proposées par chaque module
        for module in self.modules:
            if module.should_execute_this_tick():
                actions = module.propose_actions(self.game_phase)
                for action in actions:
                    priority = self._calculate_priority(action)
                    self.priority_queue.add(action, priority)
        
        # 2. Exécuter l'action la plus prioritaire
        if not self.priority_queue.is_empty():
            action = self.priority_queue.pop()
            self._execute_action(action)
    
    def _calculate_priority(self, action):
        """Calcule la priorité selon personnalité, contexte et phase"""
        base_priority = action.base_priority
        personality_modifier = self.personality.get_modifier(action.category)
        urgency = self._calculate_urgency(action)
        phase_modifier = self._get_phase_modifier(action)
        
        return base_priority * personality_modifier * urgency * phase_modifier
    
    def _detect_game_phase(self):
        """Détecte la phase actuelle du jeu selon le temps écoulé"""
        game_start = load_game_start_date()
        days_elapsed = (datetime.now() - game_start).days
        
        if days_elapsed < 15:
            return "phase_1_antique"
        elif days_elapsed < 30:
            return "phase_2_classical"
        else:
            return "phase_3_new_world"
    
    def _get_phase_modifier(self, action):
        """Ajuste la priorité selon la phase du jeu"""
        if self.game_phase == "phase_1_antique":
            # Phase 1 : focus sur les 4 ressources de base
            if action.resource_type in ["stone", "cereal", "papyrus", "iron"]:
                return 1.5
        
        elif self.game_phase == "phase_2_classical":
            # Phase 2 : nouvelles ressources débloquées
            if action.resource_type in ["marble", "horse", "wine", "glass"]:
                return 2.0
        
        return 1.0
    
    def _on_phase_change(self, new_phase):
        """Réagit au changement de phase"""
        if new_phase == "phase_2_classical":
            # Débloquer nouvelles ressources
            self.modules['colonizer'].unlock_advanced_resources()
            self.modules['military_manager'].unlock_cavalry()
        
        elif new_phase == "phase_3_new_world":
            # Préparer l'expansion maritime
            self.modules['colonizer'].unlock_new_world()
    
    def is_active(self):
        """Vérifie si l'IA est dans sa plage horaire active"""
        return ActivitySimulator.is_online(self.ai_player.id)
```

### Système de priorités
```python
PRIORITY_LEVELS = {
    'critical': 1000,   # Famine, peste
    'urgent': 500,      # Défense, manque ressources
    'high': 100,        # Construction, recherche
    'medium': 50,       # Commerce, optimisation
    'low': 10           # Expansion, exploration
}
```

---

## 🕒 SIMULATION DE CONNEXION

### ActivitySimulator
```python
class ActivitySimulator:
    """Simule les sessions de connexion d'un joueur réel"""
    
    def __init__(self, ai_player_id, config):
        self.ai_player_id = ai_player_id
        self.sessions_per_day = random.randint(
            config['sessions_per_day']['min'],
            config['sessions_per_day']['max']
        )
        self.current_session = None
        self._generate_daily_schedule()
    
    def _generate_daily_schedule(self):
        """Génère les plages horaires de connexion pour la journée"""
        self.schedule = []
        for _ in range(self.sessions_per_day):
            start_hour = self._random_start_time()
            duration = random.randint(
                config['session_duration_minutes']['min'],
                config['session_duration_minutes']['max']
            )
            self.schedule.append({
                'start': start_hour,
                'duration': duration
            })
    
    def is_online(self):
        """Vérifie si l'IA est actuellement "connectée" """
        current_time = datetime.now()
        for session in self.schedule:
            if self._is_in_session(current_time, session):
                return True
        return False
    
    def _is_in_session(self, time, session):
        """Vérifie si le temps actuel est dans la session"""
        # Implémentation avec gestion nuit/jour
        pass
```

---

## 🌍 GESTION DE LA POPULATION IA DANS LE SERVEUR

### Objectifs
- Éviter les serveurs vides (problème d'Ikariam)
- IAs indiscernables des joueurs humains
- Équilibre : 3-4 IAs pour 10-15 joueurs par île
- Spawn progressif pour suivre le rythme des joueurs

### Stratégie de spawn

#### 1. **Spawn initial**
```python
def spawn_initial_ais(server):
    """Spawn des premières IAs au lancement du serveur"""
    # Attendre que 5-10 joueurs humains aient rejoint
    if count_human_players(server) >= 5:
        # Créer 2-3 IAs sur différentes îles
        for i in range(random.randint(2, 3)):
            personality = random.choice(['economic', 'military', 'balanced'])
            difficulty = random.choice(['easy', 'medium'])
            island_type = choose_starting_island(personality)
            
            spawn_ai_player(
                username=generate_ai_name(),
                personality=personality,
                difficulty=difficulty,
                starting_island_type=island_type
            )
```

#### 2. **Spawn progressif**
```python
def check_spawn_ai(server):
    """Vérifié tous les jours (ou tous les X ticks)"""
    for island in server.islands:
        human_count = count_human_players_on_island(island)
        ai_count = count_ai_players_on_island(island)
        
        # Si beaucoup de joueurs mais peu d'IAs
        if human_count >= 8 and ai_count < 3:
            # Spawn une IA sur cette île (délai 1 jour)
            schedule_ai_spawn(island, delay_days=1)
        
        # Limite stricte : max 4 IAs par île
        if ai_count >= 4:
            continue
```

#### 3. **Distribution équilibrée**
```python
def ensure_balanced_distribution():
    """Assure que les 4 types d'îles ont des IAs"""
    resource_types = ['stone', 'cereal', 'papyrus', 'iron']
    
    for resource in resource_types:
        islands = get_islands_by_resource(resource)
        total_ai_count = sum(count_ai_on_island(i) for i in islands)
        
        # Si un type de ressource manque d'IAs
        if total_ai_count < 2:
            best_island = choose_best_island_for_spawn(islands)
            spawn_ai_on_island(best_island, resource)
```

### Vitesse de développement

#### Multiplicateur de vitesse
```python
# ai_config.json
"development_speed": {
    "phase_1": {
        "easy": 0.8,      # 20% plus lent qu'un joueur moyen
        "medium": 1.0,    # Vitesse normale
        "hard": 1.2       # 20% plus rapide
    },
    "phase_2": {
        "easy": 0.9,
        "medium": 1.1,
        "hard": 1.3
    }
}
```

#### Application du multiplicateur
```python
def calculate_construction_time(building, ai_difficulty):
    base_time = building.construction_time
    multiplier = get_speed_multiplier(ai_difficulty, current_phase)
    
    # L'IA ne triche pas : elle construit plus vite en prenant
    # des décisions optimales, pas en réduisant le temps réel
    return base_time  # Temps normal
    
    # La "vitesse" vient de :
    # - Décisions plus rapides (pas d'hésitation)
    # - Optimisation des ressources
    # - Moins d'erreurs stratégiques
```

### Noms et apparence

#### Génération de noms réalistes
```python
AI_NAME_PREFIXES = [
    "Emperor", "Archon", "Consul", "Basileus", "Strategos",
    "Caesar", "Imperator", "Praetor", "Tribune", "Legatus"
]

AI_NAME_SUFFIXES = [
    "Magnus", "Victor", "Maximus", "Augustus", "Invictus",
    "Fortis", "Sapiens", "Audax", "Severus", "Clemens"
]

def generate_ai_name():
    prefix = random.choice(AI_NAME_PREFIXES)
    suffix = random.choice(AI_NAME_SUFFIXES)
    number = random.randint(1, 999)
    
    # Ex: "Consul_Magnus_247", "Emperor_Victor_83"
    return f"{prefix}_{suffix}_{number}"
```

#### Différenciation visuelle (optionnelle)
```python
# Marquer les IAs avec un badge discret (pour admin uniquement)
"player": {
    "id": "ai_001",
    "username": "Consul_Magnus_247",
    "is_ai": true,           # ← Flag caché du frontend
    "display_as_human": true  # ← Apparaît comme humain pour les joueurs
}
```

### Limites et règles

#### Règles strictes
```json
{
  "limits": {
    "max_ai_per_island": 4,
    "max_ai_per_server": 100,
    "min_human_before_spawn": 5,
    "spawn_delay_after_human_days": 1,
    "ai_to_human_ratio_max": 0.4
  },
  "restrictions": {
    "can_attack_humans": true,
    "can_be_attacked": true,
    "can_use_market": true,
    "can_form_alliances": false,  // Phase 1
    "can_send_messages": false    // IAs silencieuses
  }
}
```

#### Monitoring
```python
def get_server_stats():
    return {
        "total_players": 47,
        "human_players": 32,
        "ai_players": 15,
        "ai_ratio": 0.32,
        "islands": [
            {
                "id": 1,
                "resource": "stone",
                "human_count": 8,
                "ai_count": 3,
                "total": 11
            },
            # ...
        ]
    }
```

---

## 🔌 INTÉGRATION

### Endpoints API
```python
# server/app/routes/ai_routes.py

@ai_bp.route('/api/ai/execute', methods=['POST'])
def execute_ai_tick():
    """Déclenche manuellement un tick IA (pour tests)"""
    ai_controller.execute_all_ais()
    return jsonify({'status': 'executed'})

@ai_bp.route('/api/ai/players', methods=['GET'])
def get_ai_players():
    """Liste tous les joueurs IA"""
    return jsonify(ai_controller.get_all_ai_players())

@ai_bp.route('/api/ai/players/<player_id>/config', methods=['GET', 'PUT'])
def manage_ai_config(player_id):
    """Get/Update config d'un joueur IA spécifique"""
    if request.method == 'GET':
        return jsonify(ai_controller.get_config(player_id))
    else:
        config = request.json
        ai_controller.update_config(player_id, config)
        return jsonify({'status': 'updated'})

@ai_bp.route('/api/ai/modules/<module_name>/toggle', methods=['POST'])
def toggle_module(module_name):
    """Active/désactive un module globalement"""
    enabled = request.json.get('enabled')
    ai_controller.toggle_module(module_name, enabled)
    return jsonify({'status': 'toggled', 'module': module_name, 'enabled': enabled})
```

### Intégration avec le système de tick
```python
# server/app/core/tick_manager.py

def process_tick():
    """Fonction principale de tick"""
    # ... traitement normal ...
    
    # Exécution des IAs actives
    if ai_config.get('tick_execution', True):
        ai_controller.execute_all_ais()
    
    # ... suite du traitement ...
```

---

## 🗺️ ROADMAP D'IMPLÉMENTATION

### Phase 1 : Fondations (Semaine 1-2) - PHASE 1 ANTIQUE
✅ Structure de base
- [ ] Créer arborescence `server/app/ai/`
- [ ] Implémenter `AIController` et `DecisionEngine`
- [ ] Créer classe abstraite `BaseModule`
- [ ] Implémenter `ActivitySimulator`
- [ ] Créer `ai_config.json` avec structure complète
- [ ] Implémenter `DataLoader` (lecture buildings/units/research)
- [ ] Implémenter système de phases (Phase 1/2/3)

✅ Modules essentiels (v1 simple)
- [ ] `CityBuilderModule` : construction basique
- [ ] `ResourceManagerModule` : réaffectation travailleurs
- [ ] `EconomyManagerModule` : transport simple
- [ ] `ColonizerModule` : choix île départ + colonisation Phase 1

✅ Système de spawn des IAs
- [ ] Logique de spawn progressif (ratio 3-4 IAs pour 10-15 humains)
- [ ] Distribution équilibrée sur les 4 types d'îles
- [ ] Délai de spawn (1 jour après humains)
- [ ] Limites par île (max 4 IAs)

✅ Tests de base
- [ ] Créer joueur IA test sur chaque type d'île
- [ ] Vérifier lecture config
- [ ] Tester simulation de connexion
- [ ] Valider construction d'un bâtiment
- [ ] Valider colonisation des 4 ressources de base

### Phase 2 : Expansion (Semaine 3-4) - PHASE 2 CLASSIQUE
✅ Modules avancés
- [ ] `MilitaryManagerModule` : attaques barbares + pillage
- [ ] `ResearchManagerModule` : priorisation recherches Phase 1

✅ Personnalités
- [ ] Implémenter personnalité "Économique" (Pierre/Papyrus focus)
- [ ] Implémenter personnalité "Militaire" (Fer/Céréales focus)
- [ ] Implémenter personnalité "Équilibrée"

✅ Amélioration décision
- [ ] Système de priorités complet
- [ ] Gestion des erreurs (difficulté facile)
- [ ] Planification à long terme (économiser pour bâtiment cher)

✅ Support Phase 2 Classique (nouvelles ressources)
- [ ] Détection automatique du passage en Phase 2 (J+15)
- [ ] Déblocage Marbre, Chevaux, Vin, Cristal
- [ ] Colonisation des nouvelles ressources
- [ ] Cavalerie (unités avancées)
- [ ] Sites de production avec dons (priorisation)

### Phase 3 : Combat & Héros (Semaine 5-6)
✅ Militaire avancé
- [ ] `HeroManagerModule` : gestion héros
- [ ] `DefenseManagerModule` : réaction aux attaques
- [ ] Attaques de joueurs humains
- [ ] Composition d'armée adaptative
- [ ] Moral de l'armée (vin)

✅ Stratégies avancées
- [ ] Stratégie "île-banque" (centralisation ressources)
- [ ] Coordination multi-villes
- [ ] Adaptation dynamique selon contexte
- [ ] Alliances entre IAs (optionnel)
- [ ] Priorisation îles avec sites améliorés (dons)
- [ ] Optimisation distance transport

### Phase 4 : Optimisation & Polish (Semaine 7-8)
✅ Performance
- [ ] Optimiser calculs
- [ ] Cache pour données fréquentes
- [ ] Limiter appels API

✅ Configuration
- [ ] Interface admin pour gérer IAs
- [ ] Ajustement dynamique difficulté
- [ ] Monitoring actions IA
- [ ] Dashboard : ratio IAs/Humains par île

✅ Tests & Balance
- [ ] Tests avec plusieurs IAs simultanées
- [ ] Balance des personnalités
- [ ] Ajustement des seuils de décision
- [ ] Validation vitesse développement IA vs Humains
- [ ] Équilibrage spawn progressif

✅ Support Phase 3 Nouveau Monde (Semaine 8+)
- [ ] Détection passage Phase 3 (J+30)
- [ ] Super-continent avec Charbon, Poudre, Épices, Coton
- [ ] Expansion maritime longue distance
- [ ] (À développer selon avancée du jeu)

---

## 📊 MÉTRIQUES & MONITORING

### Données à logger
```python
ai_logs = {
    'player_id': 'ai_001',
    'tick': 12345,
    'online': True,
    'actions': [
        {'type': 'build', 'building': 'townhall', 'level': 3, 'success': True},
        {'type': 'reallocate_workers', 'resource': 'wood', 'count': 10},
        {'type': 'transport', 'from': 'city_1', 'to': 'city_2', 'resources': {...}}
    ],
    'decisions': {
        'total_proposals': 15,
        'executed': 3,
        'rejected': 12
    }
}
```

### Dashboard IA (optionnel)
- Nombre d'IAs actives
- Actions par minute
- Taux de réussite des décisions
- Répartition des personnalités

---

## 📈 STRATÉGIES PAR PHASE DE JEU

### Phase 1 : Âge Antique (Jours 0-15)

#### Objectifs principaux
1. **Développer la ville de départ**
   - Construction : Hôtel de ville, Entrepôt, Moulin à vent
   - Éviter famine et peste
   - Atteindre niveau 5-7

2. **Collecter les 4 ressources de base**
   - Coloniser Pierre, Céréales, Papyrus, Fer
   - Séquence selon personnalité :
     - **Économique** : Pierre → Papyrus → Céréales → Fer
     - **Militaire** : Fer → Céréales → Pierre → Papyrus
     - **Équilibrée** : Selon ressources manquantes

3. **Établir une économie stable**
   - Production > Consommation
   - Transport entre villes
   - Pas encore d'île-banque (trop tôt)

4. **Premiers combats**
   - Attaquer villages barbares niveau 1-2
   - Piller ressources
   - Éviter les joueurs (trop risqué)

#### Stratégie de colonisation Phase 1
```python
def colonize_phase_1(ai_player):
    owned_resources = get_owned_resource_types(ai_player.cities)
    
    # Priorité 1 : Compléter les 4 ressources de base
    basic_resources = ['stone', 'cereal', 'papyrus', 'iron']
    missing = [r for r in basic_resources if r not in owned_resources]
    
    if missing:
        target = choose_by_need(missing, ai_player)
        islands = get_islands_by_resource(target)
        
        # Critères de sélection
        best_island = max(islands, key=lambda i: (
            i.player_count * 10 +        # Préférer îles peuplées
            i.donation_level * 20 -      # Sites améliorés
            calculate_distance(ai_player.capital, i) * 2
        ))
        
        colonize(best_island)
```

---

### Phase 2 : Âge Classique (Jours 15-30)

#### Déblocage automatique
- Nouvelles ressources disponibles : Marbre, Chevaux, Vin, Cristal
- Nouvelles unités : Cavalerie
- Recherches avancées

#### Objectifs principaux
1. **Coloniser les nouvelles ressources**
   - Marbre (construction avancée)
   - Chevaux (cavalerie)
   - Vin (moral + croissance)
   - Cristal (recherche avancée)

2. **Stratégies avancées**
   - **Île-banque** : Centraliser ressources sur 1 île fortifiée
   - **Spécialisation** : Villes thématiques (militaire, recherche, économie)
   - **Commerce intensif** : Acheter/vendre au marché

3. **Montée en puissance militaire**
   - Production de cavalerie
   - Attaques de villages barbares niveau 3-5
   - Premières attaques de joueurs (faibles)

4. **Optimisation sites de production**
   - Faire des dons pour améliorer les sites
   - Prioriser colonisation sur îles avec sites niveau élevé

#### Critères de colonisation Phase 2
```python
def colonize_phase_2(ai_player):
    # Phase 2 : nouvelles ressources + optimisation
    
    # 1. Compléter les nouvelles ressources
    advanced_resources = ['marble', 'horse', 'wine', 'glass']
    owned = get_owned_resource_types(ai_player.cities)
    missing_advanced = [r for r in advanced_resources if r not in owned]
    
    if missing_advanced:
        target = missing_advanced[0]
    else:
        # 2. Diversification : cibler ressources faibles
        target = get_lowest_production_resource(ai_player)
    
    islands = get_islands_by_resource(target)
    
    # Critères affinés
    best_island = max(islands, key=lambda i: (
        i.donation_level * 50 +          # Sites améliorés = PRIORITÉ
        i.player_count * 20 +            # Îles actives
        i.defense_level * 10 -           # Éviter îles trop défendues
        calculate_transport_time(ai_player.capital, i) * 5
    ))
    
    colonize(best_island)
```

#### Stratégie île-banque
```python
def implement_bank_island_strategy(ai_player):
    if len(ai_player.cities) < 3:
        return  # Trop tôt
    
    # Choisir la ville la mieux défendue
    bank_city = max(ai_player.cities, key=lambda c: c.defense_level)
    
    # Centraliser 70% des ressources
    for city in ai_player.cities:
        if city != bank_city:
            for resource in ALL_RESOURCES:
                if city.resources[resource] > 1000:
                    amount = city.resources[resource] * 0.7
                    transport_resources(city, bank_city, resource, amount)
```

---

### Phase 3 : Nouveau Monde (Jour 30+)

#### Déblocage automatique
- Super-continent découvert
- Nouvelles ressources : Charbon, Poudre, Épices, Coton
- Expansion maritime longue distance

#### Objectifs principaux
1. **Explorer le nouveau monde**
   - Coloniser le super-continent
   - Établir routes maritimes

2. **Domination avancée**
   - Guerres de conquête
   - Alliances stratégiques
   - Contrôle de ressources rares

*(À développer selon l'avancée du jeu)*

---

## 🎓 EXEMPLE DE FLUX COMPLET

```
Jour 3, Tick 4320 - IA "Consul_Magnus_247" 
(personnalité: Économique, difficulté: Moyen, île: Papyrus)
│
├─ Phase détectée: Phase 1 Antique (Jour 3/15)
│
├─ ActivitySimulator.is_online() → TRUE (session 14h-16h, durée: 47 min)
│
├─ AIController.tick()
│  │
│  ├─ Ressources actuelles:
│  │  Wood: 450, Stone: 320, Iron: 180, Cereal: 250 ⚠️, Papyrus: 890
│  │
│  ├─ CityBuilderModule.propose_actions()
│  │  └─ Action: Build Windmill level 1 (priority: 900 - famine < 500)
│  │
│  ├─ ResourceManagerModule.propose_actions()
│  │  └─ Action: Reallocate 15 workers to cereal (priority: 850)
│  │
│  ├─ EconomyManagerModule.propose_actions()
│  │  └─ Action: Buy iron from market (priority: 300)
│  │
│  └─ ColonizerModule.propose_actions()
│     ├─ Owned resources: [papyrus]
│     ├─ Missing basic: [stone, cereal, iron]
│     └─ Action: Colonize cereal island (priority: 700 - Phase 1 goal)
│        ├─ Target: Karposia (cereal)
│        ├─ Score: 180 (8 players, donation lvl 2, distance 12)
│        └─ Reason: Missing resource + populated island
│
├─ DecisionEngine._calculate_priority()
│  ├─ Windmill = 900 × 1.2 (economic) × 1.5 (urgency) × 1.0 (phase) = 1620
│  ├─ Reallocate = 850 × 1.1 × 1.3 × 1.0 = 1215
│  ├─ Colonize = 700 × 1.5 (economic loves expansion) × 1.2 × 1.5 (Phase 1) = 1890 🏆
│  └─ Buy iron = 300 × 0.9 × 1.0 × 1.0 = 270
│
├─ Execute: Colonize cereal island (Karposia)
│  ├─ Check embassy level: 2 ✓
│  ├─ Check resources: 3200 wood, 2800 stone ✓
│  ├─ Check delay: 2.8 days since last city ✓
│  ├─ API call: POST /api/colonies/create
│  │  └─ {resource: "cereal", island_id: 3, city_name: "Nova_Magnus"}
│  ├─ Deduct colonization cost
│  ├─ Create new city on Karposia
│  └─ Log action: "AI Consul_Magnus_247 colonized cereal island"
│
├─ Update state:
│  ├─ Cities: 2 (Papyrus capital + Cereal colony)
│  ├─ Progress Phase 1: 2/4 basic resources ✓
│  └─ Next colonization available: Jour 5.8
│
└─ Wait next tick (or until next session)
```

---

## 🔐 SÉCURITÉ & LIMITES

### Pas de triche
- ✅ L'IA utilise les mêmes endpoints API que le frontend
- ✅ Respect des cooldowns et files d'attente
- ✅ Pas d'accès aux données cachées des autres joueurs
- ✅ Construction/recherche prennent le temps normal

### Limites techniques
- Maximum 10 IAs simultanées (configurable)
- Timeout 5s par décision
- Rate limiting sur actions sensibles

---

## 📝 NOTES D'IMPLÉMENTATION

### Points d'attention
1. **Performance** : ne pas ralentir le tick principal
2. **Atomicité** : chaque action doit être transactionnelle
3. **Logs** : tracer toutes les décisions pour debug
4. **Tests** : scénarios de regression pour chaque module

### Évolutions futures
- [ ] Machine Learning pour adapter le comportement
- [ ] Analyse des patterns de joueurs humains
- [ ] Diplomatie entre IAs
- [ ] Événements aléatoires (rébellions, épidémies)

---

## 🚀 COMMANDES DE DÉMARRAGE

### Créer un joueur IA
```python
from app.ai.ai_controller import AIController

ai = AIController.create_ai_player(
    username="AI_Trader",
    personality="economic",
    difficulty="medium"
)
```

### Tester manuellement
```bash
curl -X POST http://localhost:5000/api/ai/execute
```

### Activer/désactiver un module
```bash
curl -X POST http://localhost:5000/api/ai/modules/military_manager/toggle \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

---

## 🎯 POINTS CLÉS DU SYSTÈME IA

### ✅ Ce que l'IA DOIT faire
1. **Se comporter comme un joueur humain**
   - Connexions réalistes (3-8 sessions/jour, 15-120 min)
   - Décisions stratégiques cohérentes
   - Erreurs occasionnelles (difficulté facile/moyen)
   - Indiscernable d'un humain pour les autres joueurs

2. **S'adapter automatiquement**
   - Lecture dynamique de buildings.json, units.json, research.json
   - Pas de valeurs hardcodées
   - Fonctionne même si tu changes les coûts/bonus
   - Détecte les phases automatiquement

3. **Peupler le serveur intelligemment**
   - Spawn progressif (ratio 3-4 IAs pour 10-15 humains)
   - Distribution équilibrée sur les 4 types d'îles
   - Max 4 IAs par île
   - Délai de spawn (1 jour après humains)

4. **Suivre la progression du jeu**
   - Phase 1 : Collecter 4 ressources de base (Pierre, Céréales, Papyrus, Fer)
   - Phase 2 : Débloquer ressources avancées (Marbre, Chevaux, Vin, Cristal)
   - Phase 3 : Explorer le Nouveau Monde (Charbon, Poudre, Épices, Coton)

5. **Optimiser selon le contexte**
   - Prioriser îles avec joueurs actifs (sites améliorés)
   - Considérer la distance de transport
   - Spécialiser les villes selon la ressource d'île
   - Adapter la stratégie selon la personnalité

### ❌ Ce que l'IA NE FAIT PAS
1. **Pas de triche**
   - Utilise les mêmes règles que les joueurs
   - Pas de vision sur les ressources ennemies
   - Temps de construction normaux
   - Pas de téléportation

2. **Pas de règles par élément**
   - Pas de `if building == "townhall"` hardcodé
   - Pas de coûts en dur dans le code
   - Pas de liste d'unités statique
   - Tout vient des fichiers JSON

3. **Pas de communication (Phase 1)**
   - Pas de messages aux joueurs
   - Pas d'alliances (pour l'instant)
   - Joue en solo

### 🏗️ Architecture générique

```
┌─────────────────────────────────────┐
│  DONNÉES (changeables)              │
│  buildings.json, units.json, etc.   │
└──────────────┬──────────────────────┘
               │ Lecture dynamique
┌──────────────▼──────────────────────┐
│  LOGIQUE (stable)                   │
│  - Calculs relatifs                 │
│  - Catégorisation                   │
│  - Priorités génériques             │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  CONFIGURATION (ajustable)          │
│  ai_config.json                     │
│  - Personnalités                    │
│  - Seuils                           │
│  - Phases                           │
└─────────────────────────────────────┘
```

### 🔄 Compatibilité future

#### ✅ Compatible sans modification
- Changement de coûts dans buildings.json
- Ajout d'un nouveau bâtiment avec catégorie existante
- Modification des bonus/malus
- Ajustement de la vitesse de jeu (tick)
- Changement des temps de construction

#### ⚠️ Nécessite ajustement config (5-10 minutes)
- Nouveau bâtiment avec nouvelle catégorie
- Nouvelle unité avec nouveau rôle tactique
- Nouvelle mécanique de jeu majeure
- Nouvelles recherches avec nouvelle branche

#### ❌ Nécessite nouveau module (1-2 jours)
- Système de diplomatie
- Système de quêtes
- Événements aléatoires
- Commerce inter-joueurs complexe

### 📊 Métriques de succès

L'IA est réussie si :
- ✅ Un joueur ne peut pas distinguer une IA d'un humain
- ✅ Le serveur n'est jamais vide (toujours 3-4 IAs minimum)
- ✅ Les IAs se développent à un rythme réaliste (ni trop lent, ni trop rapide)
- ✅ Les IAs adoptent des stratégies variées (économique, militaire, équilibrée)
- ✅ Le système continue de fonctionner après modifications du jeu
- ✅ Les IAs colonisent les 4 ressources de base en Phase 1
- ✅ Les IAs participent au commerce, aux combats, à l'expansion

---

**Fin du cahier des charges**

*Document créé le : 28 novembre 2025*
*Dernière mise à jour : 29 novembre 2025*
*Version : 2.0*
*Auteur : GitHub Copilot*

---

## 📝 CHANGELOG

### Version 2.0 (29 novembre 2025)
- ✅ Ajout du contexte du jeu (temps réel, 3 phases)
- ✅ Système de spawn progressif des IAs (ratio 3-4 pour 10-15)
- ✅ Stratégies par phase (Phase 1/2/3)
- ✅ Gestion de la population IA dans le serveur
- ✅ Critères de colonisation détaillés (sites améliorés, distance, population)
- ✅ Objectif Phase 1 : collecter 4 ressources de base
- ✅ Support Phase 2 : déblocage ressources avancées
- ✅ Stratégie île-banque et optimisation transport
- ✅ Génération de noms réalistes pour IAs
- ✅ Limites strictes (max 4 IAs/île, ratio, spawn delay)

### Version 1.0 (28 novembre 2025)
- Création initiale du cahier des charges
- Architecture modulaire
- Configuration externe
- Système de décision
- 8 modules fonctionnels
