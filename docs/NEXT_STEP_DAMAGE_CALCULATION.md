# 🎯 PROCHAINE ÉTAPE : CALCUL RÉEL DES DÉGÂTS

*Date : 17 décembre 2024*

## ✅ ÉTAT ACTUEL - CE QUI FONCTIONNE

1. ✅ L'IA se déclenche automatiquement (timer 10s)
2. ✅ Toutes les unités jouent à tour de rôle
3. ✅ Délai de 0.5s entre chaque action (visible)
4. ✅ Timer gelé pendant l'exécution de l'IA
5. ✅ Auto-déploiement au Round 1
6. ✅ Combat à partir du Round 2
7. ✅ Logs clairs et détaillés

**Logs typiques Round 5+ :**
```
🎯 [IA] 2 unités disponibles
🎯 [IA] Traitement unité 1/2: auto_attacker_player_1_militia_0
⚔️ [IA] Attaque de militia_0 sur barbarian_warrior_0
✅ [IA] Attaque réussie
[délai 0.5s]
🎯 [IA] Traitement unité 2/2: auto_attacker_player_1_slinger_1
⚔️ [IA] Attaque de slinger_1 sur barbarian_warrior_0
✅ [IA] Attaque réussie
✅ [IA] 2 actions effectuées pour player_1
```

---

## 🔴 PROBLÈME ACTUEL

**Dans `battle_ai_basic.py` ligne 95 :**
```python
# Calculer les dégâts (1 kill pour simplifier - TODO: vrai calcul)
kills = 1  # ❌ TOUJOURS 1 KILL
```

**Impact :**
- Toutes les unités font les mêmes dégâts
- Pas de différence entre militia (faible) et barbarian_warrior (fort)
- Combat peu réaliste
- Pas d'XP proportionnel aux kills réels

---

## 📊 SYSTÈME DE COMBAT ACTUEL (JOUEUR HUMAIN)

### Comment un joueur humain attaque :

1. **Clique sur une unité alliée** → unité sélectionnée
2. **Clique sur une unité ennemie** → popup de combat s'ouvre
3. **Popup affiche :**
   - Stats attaquant (ATK, DEF, HP, etc.)
   - Stats défenseur
   - Prédiction des dégâts
4. **Joueur clique "Attaquer"**
5. **Client calcule les kills** (TypeScript)
6. **Client envoie à `POST /api/v2/battle/attack`** avec `kills` calculés

### Fichiers impliqués :

**Client (TypeScript) :**
- Popup de combat : `client/src/popups/CombatPopup.tsx` (probable)
- Calcul de dégâts : fonction `calculateCombatResult()` quelque part
- Envoie `POST /api/v2/battle/attack` avec `{ attacker_id, defender_id, kills }`

**Serveur (Python) :**
- Reçoit la requête : `server/app/routes/battle_routes_v2.py`
- Enregistre l'attaque : `BattleTurnManagerV2.record_attack_action()`
- **Ne recalcule PAS les dégâts** (fait confiance au client)

---

## 🎯 SOLUTION : PORTER LE CALCUL EN PYTHON

### Option A : Trouver et réutiliser le calcul client
**Avantage :** Même formule que le joueur humain
**Inconvénient :** Code TypeScript à convertir en Python

### Option B : Créer un calcul serveur-side
**Avantage :** Contrôle total, peut servir pour valider les attaques joueurs
**Inconvénient :** Risque de divergence avec le client

**Recommandation : Option A** (porter la formule existante)

---

## 🔍 ÉTAPE 1 : TROUVER LE CALCUL EXISTANT

### Rechercher dans le client :

```bash
# Fonctions possibles :
- calculateCombatResult()
- calculateDamage()
- simulateCombat()
- getCombatOutcome()
```

### Fichiers probables :
```
client/src/
  ├── services/CombatService.ts
  ├── utils/combatCalculations.ts
  ├── popups/CombatPopup.tsx
  └── hooks/useBattleCombat.ts
```

---

## 🧮 FORMULE ATTENDUE (INSPIRÉE D'IKARIAM)

### Formule typique de combat au tour par tour :

```typescript
function calculateKills(attacker, defender) {
    // 1. ATK de l'attaquant
    const attackPower = attacker.attack * attacker.count;
    
    // 2. DEF du défenseur
    const defensePower = defender.defense;
    
    // 3. Dégâts bruts
    const rawDamage = Math.max(0, attackPower - defensePower);
    
    // 4. Facteur aléatoire (±20%)
    const randomFactor = 0.8 + Math.random() * 0.4;
    
    // 5. Dégâts finaux
    const finalDamage = rawDamage * randomFactor;
    
    // 6. Nombre de kills
    const kills = Math.floor(finalDamage / defender.hp);
    
    // 7. Limiter au nombre d'unités disponibles
    return Math.min(kills, defender.count);
}
```

### Facteurs possibles :
- ✅ Attaque de l'attaquant
- ✅ Défense du défenseur
- ✅ HP du défenseur
- ⚡ Bonus de terrain (colline = +20% DEF)
- ⚡ Bonus de moral (+10% ATK si moral > 80)
- ⚡ Bonus de héros
- ⚡ Flanking (attaque par les côtés)
- ⚡ Type advantage (cavalerie > archers)

---

## 📝 PLAN D'IMPLÉMENTATION

### **Phase 1 : Recherche** ⏱️ 15-30 min
1. Chercher le calcul existant dans le client
2. Analyser la formule utilisée
3. Identifier tous les facteurs (terrain, moral, etc.)

### **Phase 2 : Portage Python** ⏱️ 30-60 min
1. Créer `server/app/ai/combat_calculator.py`
2. Porter la formule en Python
3. Charger les stats depuis `units.json`
4. Tester avec des cas connus

### **Phase 3 : Intégration IA** ⏱️ 15 min
1. Remplacer `kills = 1` par `kills = calculate_kills(attacker, defender)`
2. Importer `combat_calculator.py` dans `battle_ai_basic.py`
3. Tester en conditions réelles

### **Phase 4 : Validation** ⏱️ 30 min
1. Comparer résultats IA vs joueur humain
2. Vérifier que les dégâts sont cohérents
3. Ajuster si nécessaire

---

## 🔬 EXEMPLE DE CODE ATTENDU

### Nouveau fichier : `server/app/ai/combat_calculator.py`

```python
"""
Calculateur de dégâts de combat
Même formule que le client pour cohérence
"""

import math
import random
from typing import Dict, Tuple

class CombatCalculator:
    """Calcule les dégâts d'une attaque"""
    
    def __init__(self):
        self.units_stats = self._load_units_stats()
    
    def _load_units_stats(self) -> Dict:
        """Charge les stats des unités depuis units.json"""
        import json
        import os
        
        units_file = os.path.join('server', 'gamedata', 'units.json')
        with open(units_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def calculate_kills(
        self, 
        attacker_type: str,
        attacker_count: int,
        defender_type: str,
        defender_count: int,
        terrain_bonus: float = 0.0
    ) -> int:
        """
        Calcule le nombre de kills d'une attaque
        
        Args:
            attacker_type: Type d'unité (ex: "militia")
            attacker_count: Nombre d'unités attaquantes
            defender_type: Type d'unité défendante
            defender_count: Nombre d'unités défendantes
            terrain_bonus: Bonus de terrain (ex: 0.2 pour +20% DEF)
        
        Returns:
            Nombre de kills (unités tuées)
        """
        # 1. Récupérer les stats
        attacker_stats = self.units_stats.get(attacker_type, {})
        defender_stats = self.units_stats.get(defender_type, {})
        
        atk = attacker_stats.get('attack', 10)
        def_base = defender_stats.get('defense', 5)
        hp = defender_stats.get('hp', 50)
        
        # 2. Appliquer bonus de terrain
        defense = def_base * (1 + terrain_bonus)
        
        # 3. Puissance d'attaque totale
        attack_power = atk * attacker_count
        
        # 4. Dégâts bruts
        raw_damage = max(0, attack_power - defense)
        
        # 5. Facteur aléatoire (±20%)
        random_factor = 0.8 + random.random() * 0.4
        
        # 6. Dégâts finaux
        final_damage = raw_damage * random_factor
        
        # 7. Nombre de kills
        kills = math.floor(final_damage / hp)
        
        # 8. Limiter au nombre disponible
        return min(kills, defender_count)
    
    def get_unit_type_from_id(self, unit_id: str) -> str:
        """
        Extrait le type d'unité depuis l'ID
        
        Ex: "auto_attacker_player_1_militia_0" → "militia"
        """
        parts = unit_id.split('_')
        
        # Retirer préfixes (auto, attacker/defender, player_X)
        if parts[0] == 'auto':
            parts = parts[1:]  # Retirer 'auto'
        
        if parts[0] in ['attacker', 'defender']:
            parts = parts[1:]  # Retirer 'attacker'/'defender'
        
        if parts[0].startswith('player'):
            parts = parts[1:]  # Retirer 'player_X'
        
        # Retirer le numéro de stack final (_0, _1, etc.)
        if parts[-1].isdigit():
            parts = parts[:-1]
        
        # Rejoindre ce qui reste
        return '_'.join(parts)


# Instance singleton
combat_calculator = CombatCalculator()
```

### Modification dans `battle_ai_basic.py` :

```python
# Ligne 95 - AVANT
kills = 1  # ❌ Fixe

# APRÈS
from app.ai.combat_calculator import combat_calculator

attacker_type = combat_calculator.get_unit_type_from_id(selected_unit['unitId'])
defender_type = combat_calculator.get_unit_type_from_id(target['unitId'])
attacker_count = selected_unit.get('unitCount', 1)
defender_count = target.get('unitCount', 1)

kills = combat_calculator.calculate_kills(
    attacker_type,
    attacker_count,
    defender_type,
    defender_count,
    terrain_bonus=0.0  # TODO: récupérer depuis le terrain
)

print(f"⚔️ [IA] {attacker_type} ({attacker_count}) → {defender_type} ({defender_count}) = {kills} kills")
```

---

## 🎯 RÉSUMÉ DE LA PROCHAINE ÉTAPE

1. **Chercher le calcul client** dans le code TypeScript
2. **Créer `combat_calculator.py`** avec la même formule
3. **Remplacer `kills = 1`** par le vrai calcul
4. **Tester et ajuster**

**Temps estimé :** 1-2 heures

**Question :** Voulez-vous que je commence cette implémentation maintenant ?
