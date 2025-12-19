# 📊 PLAN D'ÉQUILIBRAGE - INSPIRATION IKARIAM
*Master of Islands - Phase 1 (Âge Antique - 15 jours)*
*Date: 30 novembre 2025*

---

## 🎯 OBJECTIF

Aligner la vitesse de progression du jeu sur **Ikariam** pour assurer un équilibre testé et éprouvé.

**Configuration de base** :
- ⚡ **Tick** : 1 tick toutes les **10 secondes** (6 ticks/min, 360 ticks/heure, 8640 ticks/jour)
- 🕐 **Phase 1** : ~15 jours de jeu pour progression complète
- 🏗️ **Focus** : Bâtiments niv 1-5, recherches de base, première colonisation

---

## 📋 TODO LIST - 15 ÉTAPES

Suivre dans l'ordre pour un équilibrage progressif et testé :

### **Étape 1 : Analyse de référence** 📊
**Action** : Jouer à Ikariam pendant 2-3 heures, noter les valeurs

**À mesurer** :
- Hôtel de Ville niv 1-5 : coût ressources + temps construction
- Production 1 worker bois/pierre/fer : ressources/heure
- Croissance population : habitants/heure
- Recherches Agriculture, Extraction Minière : coût points + temps
- Colonisation : coût + temps

**Livrable** : Google Sheets avec tableau comparatif

---

### **Étape 2 : Configuration Admin** ⚙️
**Fichier** : Interface http://localhost:5000/admin

**Actions** :
1. Ouvrir l'interface admin
2. Section "⚡ Configuration des Ticks"
3. Activer "Auto-Tick" → ON
4. Cliquer sur bouton "**10s ⭐**" (fréquence recommandée)
5. Vérifier badge affiche "10s"

**Test** : Ouvrir le jeu, observer que les ressources se produisent toutes les 10 secondes

---

### **Étape 3 : Production Ressources** 🏭
**Fichier** : `server/app/game_logic.py`

**Chercher** :
```python
# Ligne ~380-400
def update_resource_production(self, city: Dict, time_multiplier: float = 1.0):
```

**Modifier** :
```python
# AVANT (production par seconde)
production = workers × 1.0 × (1 + bonuses)

# APRÈS (production par tick de 10 secondes)
BASE_YIELD_PER_TICK = 0.5  # Ajouter cette constante
production = workers × BASE_YIELD_PER_TICK × (1 + bonuses)

# Résultat :
# 1 worker = 0.5 res/tick = 3 res/min = 180 res/heure = 4 320 res/jour
# ✅ Aligné avec Ikariam !
```

**Test** : Assigner 10 workers bois, attendre 1 minute, vérifier +30 bois (au lieu de +600)

---

### **Étape 4 : Temps Construction Bâtiments** ⏱️
**Fichier** : `server/data/buildings.json`

**Hôtel de Ville - Valeurs cibles** :
```json
{
  "Hôtel de Ville": {
    "levels": [
      {"level": 1, "construction_time": 120},    // 2 min (était 6 sec)
      {"level": 2, "construction_time": 300},    // 5 min (était 15 sec)
      {"level": 3, "construction_time": 900},    // 15 min (était 16 sec)
      {"level": 4, "construction_time": 2700},   // 45 min (était 20 sec)
      {"level": 5, "construction_time": 7200},   // 2 heures (était 25 sec)
      {"level": 6, "construction_time": 14400},  // 4 heures (était 30 sec)
      {"level": 7, "construction_time": 28800},  // 8 heures (était 36 sec)
      {"level": 8, "construction_time": 57600},  // 16 heures (était 43 sec)
      {"level": 9, "construction_time": 86400},  // 24 heures (était 51 sec)
      {"level": 10, "construction_time": 129600} // 36 heures (était 60 sec)
    ]
  }
}
```

**Ratio multiplicateur** : ×20 (niveau 1-3) → ×100 (niveau 8-10)

**Appliquer à TOUS les bâtiments** :
- Windmill : 2s → 60s, 4s → 240s, etc.
- Academy : 5s → 300s (5 min), 13s → 1080s (18 min), etc.
- Scierie : 5s → 300s, 10s → 600s, etc.
- Entrepôt : 10s → 600s (10 min), 20s → 1800s (30 min), etc.

**Formule générale** :
```
Nouveau temps = Ancien temps × 60 (pour niv 1-3)
Nouveau temps = Ancien temps × 100 (pour niv 4-7)
Nouveau temps = Ancien temps × 120 (pour niv 8-10)
```

---

### **Étape 5 : Croissance Population** 👥
**Fichier** : `server/data/buildings.json`

**Objectif** : Capacité maximale atteinte en **2-4 heures** (au lieu de 66h)

**Formule de calcul** :
```
population_growth = population_capacity / (target_hours × 360 ticks)

Exemple Hôtel de Ville niveau 1 :
- Capacité : 80 habitants
- Objectif : 4 heures
- Calcul : 80 / (4 × 360) = 0.0556 habitants/tick
- En habitants/heure : 0.0556 × 360 = 20 habitants/heure
```

**Hôtel de Ville - Valeurs cibles** :
```json
{
  "levels": [
    {"level": 1, "effect": {
      "population_capacity": 80,
      "population_growth": 20,    // 80 en 4h (était 1.2/h = 66h)
      "food_capacity": 50
    }},
    {"level": 2, "effect": {
      "population_capacity": 120,
      "population_growth": 30,    // 120 en 4h (était 3.3/h)
      "food_capacity": 65
    }},
    {"level": 3, "effect": {
      "population_capacity": 200,
      "population_growth": 50,    // 200 en 4h (était 4.5/h)
      "food_capacity": 80
    }},
    {"level": 4, "effect": {
      "population_capacity": 280,
      "population_growth": 70,    // 280 en 4h (était 6.0/h)
      "food_capacity": 100
    }},
    {"level": 5, "effect": {
      "population_capacity": 520,
      "population_growth": 130,   // 520 en 4h (était 7.8/h)
      "food_capacity": 125
    }},
    {"level": 10, "effect": {
      "population_capacity": 1420,
      "population_growth": 350,   // 1420 en ~4h (était 21.5/h)
      "food_capacity": 325
    }}
  ]
}
```

---

### **Étape 6 : Consommation Céréales** 🌾
**Fichier** : `server/app/city_constants.py`

**Modifier** :
```python
# AVANT
CEREAL_CONSUMPTION_PER_PERSON = 0.1  # par seconde

# APRÈS
CEREAL_CONSUMPTION_PER_PERSON_PER_TICK = 0.01  # par tick de 10 sec

# Résultat :
# 100 habitants = 0.01 × 100 × 360 ticks/heure = 360 céréales/heure
# ✅ Gérable avec production normale !
```

**Alternative** : Si le code utilise `/seconde`, adapter :
```python
# Garder la constante actuelle mais ajuster la fréquence de calcul
# Consommation calculée uniquement lors des ticks (toutes les 10 sec)
cereal_consumed_per_tick = CEREAL_CONSUMPTION_PER_PERSON × 10 × population_starving
```

---

### **Étape 7 : Coûts Recherches** 🔬
**Fichier** : `server/data/research.json`

**Objectif** : Arbre complet de Phase 1 = **~50-80 heures** de production recherche répartis sur 15 jours

**Recherches Phase 1 - Valeurs cibles** :
```json
{
  "researches": [
    // === JOUR 1-3 : Essentielles ===
    {
      "id": "agriculture",
      "cost": { "research_points": 500 },  // 30 min avec Academy niv 1 (était 10)
      "prerequisites": []
    },
    {
      "id": "extraction_miniere",
      "cost": { "research_points": 2000, "gold": 100 },  // 2h (était 50)
      "prerequisites": ["agriculture"]
    },
    {
      "id": "sablier",
      "cost": { "research_points": 500 },  // 30 min (était 50)
      "prerequisites": []
    },
    {
      "id": "ecriture",
      "cost": { "research_points": 1000 },  // 1h (était 100)
      "prerequisites": ["sablier"]
    },
    
    // === JOUR 4-7 : Développement ===
    {
      "id": "architecte",
      "cost": { "research_points": 5000, "gold": 500 },  // 5h (était 300)
      "prerequisites": ["extraction_miniere"]
    },
    {
      "id": "mathematiques",
      "cost": { "research_points": 3000 },  // 3h (était 200)
      "prerequisites": ["ecriture"]
    },
    {
      "id": "marches",
      "cost": { "research_points": 6000, "gold": 750 },  // 6h (était 400)
      "prerequisites": ["architecte"]
    },
    {
      "id": "ingenierie",
      "cost": { "research_points": 5000, "gold": 750 },  // 5h (était 300)
      "prerequisites": ["mathematiques"]
    },
    
    // === JOUR 8-15 : Avancées ===
    {
      "id": "expansion",
      "cost": { "research_points": 10000, "gold": 1000 },  // 10h (était 100)
      "prerequisites": ["architecte"]
    },
    {
      "id": "ressources_avancees",
      "cost": { "research_points": 15000, "gold": 2000 },  // 15h (était 250)
      "prerequisites": ["ingenierie"]
    },
    {
      "id": "maitrise_epees",
      "cost": { "research_points": 8000, "gold": 1000 },  // 8h (était 100)
      "prerequisites": []
    },
    {
      "id": "premiers_heros",
      "cost": { "research_points": 12000, "gold": 2000 },  // 12h (était 200)
      "prerequisites": ["maitrise_epees"]
    }
  ]
}
```

**Multiplicateur global** : ×80 à ×100 pour toutes les recherches

---

### **Étape 8 : Production Academy** 🎓
**Fichier** : `server/data/buildings.json`

**Objectif** : Produire par **tick** au lieu de par seconde

**Valeurs cibles** :
```json
{
  "Academy": {
    "levels": [
      {"level": 1, "effect": {
        "research_points_per_worker": 0.05,  // Par tick (était 1.0/sec)
        // 0.05 × 6 ticks/min = 0.3 pts/min par worker
        // Avec 25 workers : 7.5 pts/min = 450 pts/heure
        // Agriculture (500 pts) = ~67 minutes ✅
        "max_workers": 25
      }},
      
      {"level": 2, "effect": {
        "research_points_per_worker": 0.075,  // (était 1.5/sec)
        // Avec 50 workers : 3.75 pts/min = 1350 pts/heure
        "max_workers": 50
      }},
      
      {"level": 3, "effect": {
        "research_points_per_worker": 0.10,  // (était 2.0/sec)
        // Avec 75 workers : 7.5 pts/min = 2700 pts/heure
        "max_workers": 75
      }},
      
      {"level": 5, "effect": {
        "research_points_per_worker": 0.15,  // (était 3.0/sec)
        // Avec 130 workers : 19.5 pts/min = 5590 pts/heure
        "max_workers": 130
      }},
      
      {"level": 10, "effect": {
        "research_points_per_worker": 0.25,  // (était 5.5/sec)
        // Avec 355 workers : 88.75 pts/min = 31950 pts/heure
        "max_workers": 355
      }}
    ]
  }
}
```

**Formule** : `Nouvelle valeur = Ancienne valeur / 20` (environ)

---

### **Étape 9 : Bonus Production Bâtiments** 📉
**Fichier** : `server/data/buildings.json`

**Objectif** : Réduire progression exponentielle +240% → +100% max

**Scierie - Valeurs cibles** :
```json
{
  "Scierie": {
    "levels": [
      {"level": 1, "effect": {"resource_production_multiplier": {"wood": 5}}},     // +5% (était +10%)
      {"level": 2, "effect": {"resource_production_multiplier": {"wood": 10}}},    // +10% (était +20%)
      {"level": 3, "effect": {"resource_production_multiplier": {"wood": 15}}},    // +15% (était +30%)
      {"level": 4, "effect": {"resource_production_multiplier": {"wood": 25}}},    // +25% (était +45%)
      {"level": 5, "effect": {"resource_production_multiplier": {"wood": 35}}},    // +35% (était +65%)
      {"level": 6, "effect": {"resource_production_multiplier": {"wood": 50}}},    // +50% (était +90%)
      {"level": 7, "effect": {"resource_production_multiplier": {"wood": 65}}},    // +65% (était +120%)
      {"level": 8, "effect": {"resource_production_multiplier": {"wood": 80}}},    // +80% (était +155%)
      {"level": 9, "effect": {"resource_production_multiplier": {"wood": 90}}},    // +90% (était +195%)
      {"level": 10, "effect": {"resource_production_multiplier": {"wood": 100}}}   // +100% MAX (était +240%)
    ]
  }
}
```

**Appliquer la même progression à** :
- Centre de Ressources (pierre, fer, céréales, papyrus)
- Autres bâtiments de production

**Progression suggérée** : +5%, +10%, +15%, +25%, +35%, +50%, +65%, +80%, +90%, +100%

---

### **Étape 10 : Nerf Windmill** 🌾
**Fichier** : `server/data/buildings.json`

**Objectif** : Réduire multiplicateur céréales ×12 → ×4 max

**Valeurs cibles** :
```json
{
  "Windmill": {
    "levels": [
      {"level": 1, "effect": {
        "food_supply": 10,
        "cereal_consumption_multiplier": 1.5  // (était 2)
      }},
      {"level": 2, "effect": {
        "food_supply": 20,
        "cereal_consumption_multiplier": 1.8  // (était 3)
      }},
      {"level": 3, "effect": {
        "food_supply": 40,
        "cereal_consumption_multiplier": 2.0  // (était 4)
      }},
      {"level": 5, "effect": {
        "food_supply": 95,
        "cereal_consumption_multiplier": 2.5  // (était 6)
      }},
      {"level": 8, "effect": {
        "food_supply": 215,
        "cereal_consumption_multiplier": 3.5  // (était 9)
      }},
      {"level": 10, "effect": {
        "food_supply": 320,
        "cereal_consumption_multiplier": 4.0  // (était 12)
      }}
    ]
  }
}
```

**Progression suggérée** : ×1.5, ×1.8, ×2.0, ×2.2, ×2.5, ×2.8, ×3.2, ×3.5, ×3.8, ×4.0

---

### **Étape 11 : Fix Bottleneck Poudre** 💣
**Fichier** : `server/data/resource_sites_database.py`

**Modifier** :
```python
"gunpowder": {
    # AVANT
    1: {"max_workers_per_city": 2, ...},
    2: {"max_workers_per_city": 4, ...},
    10: {"max_workers_per_city": 20, ...}
    
    # APRÈS (aligner sur autres ressources avancées)
    1: {"max_workers_per_city": 6, ...},
    2: {"max_workers_per_city": 10, ...},
    3: {"max_workers_per_city": 14, ...},
    4: {"max_workers_per_city": 18, ...},
    5: {"max_workers_per_city": 22, ...},
    10: {"max_workers_per_city": 40, ...}
}
```

**Objectif** : Harmoniser avec charbon/épices/coton (4→40 workers)

---

### **Étape 12 : Simulation Phase 1** 🧪
**Créer script** : `server/tests/test_phase1_progression.py`

```python
"""
Simulation complète Phase 1 (15 jours)
Objectifs à valider :
- Jour 1-3 : Hôtel de Ville niv 3, 2-3 bâtiments de base
- Jour 5 : Hôtel de Ville niv 5, Academy niv 3, 4-5 recherches
- Jour 7 : Première colonie
- Jour 10 : 2-3 villes actives
- Jour 15 : Prêt pour Phase 2 (bâtiments niv 6-8, 10-12 recherches)
"""

import json
import time
from datetime import datetime, timedelta

def simulate_player_progression(days=15):
    """Simule la progression d'un joueur sur X jours"""
    
    # État initial
    player = {
        "cities": 1,
        "population": 40,
        "resources": {"wood": 1500, "stone": 3000, "iron": 1000, "cereal": 2000},
        "buildings_avg_level": 1,
        "researches_completed": 0
    }
    
    # Paramètres (nouvelles valeurs)
    TICK_INTERVAL = 10  # secondes
    TICKS_PER_DAY = 8640
    PRODUCTION_PER_WORKER_PER_TICK = 0.5
    
    # Simulation jour par jour
    for day in range(1, days + 1):
        # TODO: Implémenter logique simulation
        pass
    
    return player

# Exécuter simulation
result = simulate_player_progression(15)
print(f"Après 15 jours : {result}")
```

**Valider** : Les valeurs correspondent aux objectifs de timeline

---

### **Étape 13 : Tableau Comparatif** 📊
**Créer** : Google Sheets "Master of Islands - Équilibrage Ikariam"

**Colonnes** :
1. Élément (nom bâtiment/recherche/ressource)
2. Ikariam - Valeur
3. MoI - Avant équilibrage
4. MoI - Après équilibrage
5. Écart % (formule)
6. Status (✅ OK / ⚠️ Attention / ❌ À revoir)

**Sections** :
- Bâtiments (13 lignes)
- Ressources (13 lignes)
- Recherches Phase 1 (12 lignes)
- Progression globale (5 lignes)

**Critère validation** : Écart < 20% par rapport à Ikariam

---

### **Étape 14 : Playtest Réel** 🎮
**Durée** : 2-3 heures de jeu continu

**Checklist** :
- [ ] Démarrage : construire 2-3 bâtiments niveau 1 (ressenti temps ?)
- [ ] Production ressources : fluide ou trop lente ?
- [ ] Population : croissance visible et logique ?
- [ ] Recherche Agriculture : temps cohérent (~30 min) ?
- [ ] Construction Hôtel de Ville niv 2-3 : motivant ?
- [ ] Blocages : manque de ressources ? Temps trop long ?
- [ ] Fun : progression satisfaisante ou frustrante ?

**Noter** : Chaque problème rencontré + idées d'amélioration

**Ajuster** : Modifier les valeurs si nécessaire (±20-30%)

---

### **Étape 15 : Documentation** 📝
**Créer** : `docs/CHANGELOG_EQUILIBRAGE.md`

**Contenu** :
```markdown
# 📋 CHANGELOG - ÉQUILIBRAGE PHASE 1

## Vue d'ensemble
- Date : 30 novembre 2025
- Objectif : Aligner progression sur Ikariam
- Tick : 10 secondes
- Phase concernée : Phase 1 (15 jours)

## Changements Détaillés

### 1. Production Ressources
**Fichier** : `server/app/game_logic.py`
- AVANT : 1 res/seconde par worker
- APRÈS : 0.5 res/tick (10 sec) par worker
- IMPACT : 1 worker = 180 res/heure (au lieu de 3600)
- JUSTIFICATION : Alignement Ikariam

### 2. Temps Construction - Hôtel de Ville
**Fichier** : `server/data/buildings.json`

| Niveau | AVANT | APRÈS | Ratio |
|--------|-------|-------|-------|
| 1 | 6s | 120s (2 min) | ×20 |
| 5 | 25s | 7200s (2h) | ×288 |
| 10 | 60s | 129600s (36h) | ×2160 |

[... détailler TOUS les changements ...]

## Tests Effectués
- [ ] Simulation 15 jours : OK
- [ ] Playtest 3h : OK
- [ ] Comparaison Ikariam : Écart < 20%

## Résultat
✅ Phase 1 équilibrée et alignée sur Ikariam
```

---

## 🎯 VALEURS RÉCAPITULATIVES

### **Constantes Système**

| Paramètre | Valeur |
|-----------|--------|
| Tick interval | 10 secondes |
| Ticks par minute | 6 |
| Ticks par heure | 360 |
| Ticks par jour | 8640 |

### **Production**

| Élément | Avant | Après | Ratio |
|---------|-------|-------|-------|
| Ressources par worker | 1/sec = 3600/h | 0.5/tick = 180/h | ÷20 |
| Research pts par worker (Acad niv 1) | 1/sec = 3600/h | 0.05/tick = 18/h | ÷200 |
| Population growth (HdV niv 1) | 1.2/h | 20/h | ×16.7 |
| Céréales consommées (100 hab) | 600/h | 360/h | ÷1.67 |

### **Temps Construction (multiplicateurs)**

| Niveau | Multiplicateur |
|--------|----------------|
| 1-3 | ×60 |
| 4-7 | ×100 |
| 8-10 | ×120 |

### **Bonus Production (max niveau 10)**

| Bâtiment | Avant | Après |
|----------|-------|-------|
| Scierie | +240% | +100% |
| Centre Ressources | +240% | +100% |
| Windmill multiplier | ×12 | ×4 |

### **Coûts Recherches (multiplicateur)**

| Catégorie | Multiplicateur |
|-----------|----------------|
| Essentielles (Agriculture) | ×50 |
| Développement (Architecte) | ×80 |
| Avancées (Expansion) | ×100 |

---

## 📊 TIMELINE ATTENDUE (Phase 1 - 15 jours)

### **Jour 1-2 : Démarrage**
- ✅ Hôtel de Ville niv 2-3
- ✅ Academy niv 1
- ✅ Windmill niv 1
- ✅ Population : 40 → 120
- ✅ Recherches : Agriculture, Plan Construction

### **Jour 3-5 : Développement**
- ✅ Hôtel de Ville niv 4-5
- ✅ Scierie niv 2-3
- ✅ Academy niv 2
- ✅ Population : 200-300
- ✅ Recherches : Extraction Minière, Écriture, Mathématiques

### **Jour 6-8 : Expansion**
- ✅ Première colonie !
- ✅ Multiple bâtiments niv 3-4
- ✅ Population totale : 500-800
- ✅ Recherches : Architecte, Expansion, Ingénierie

### **Jour 9-12 : Consolidation**
- ✅ 2-3 villes actives
- ✅ Bâtiments principaux niv 5-6
- ✅ Population totale : 1000-1500
- ✅ Recherches militaires : Maîtrise Épées, Héros

### **Jour 13-15 : Préparation Phase 2**
- ✅ Commerce inter-villes établi
- ✅ Bâtiments niv 6-8
- ✅ 10-12 recherches complétées
- ✅ Prêt pour ressources avancées (Marbre, Chevaux, etc.)

---

## 🚀 PROCHAINES ÉTAPES

Après équilibrage Phase 1 :
1. **Phase 2 (Âge Classique)** : Ressources intermédiaires, combat avancé
2. **Système de quêtes** : Guider nouveaux joueurs
3. **Événements temporaires** : Maintenir engagement
4. **Alliances et diplomatie** : Interaction sociale
5. **Phase 3 (Nouveau Monde)** : Ressources exotiques, expansion maritime

---

**✅ Suivre ces 15 étapes garantira un équilibrage solide et testé, inspiré d'un jeu à succès !**
