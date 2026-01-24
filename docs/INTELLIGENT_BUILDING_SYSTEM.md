# Système de Construction Intelligent

## 📋 Vue d'ensemble

Le système de construction IA a été amélioré avec un moteur de décision intelligent basé sur des prévisions et une gestion temporelle.

**Date:** 15 janvier 2026  
**Statut:** ✅ Implémenté

---

## 🎯 Objectif

Remplacer la construction aléatoire (POST-BUILD_ORDER) par un système intelligent qui :
- Analyse les besoins réels de chaque bâtiment
- Calcule le temps d'attente avec transport inter-villes
- Sauvegarde les décisions pour éviter recalculs constants
- S'adapte au gameplay long-terme (semaines/mois)

---

## 🏗️ Architecture

### Transition entre systèmes

```
Ville IA démarre
    ↓
[BUILD_ORDER] (7 bâtiments fixes)
    ├─ Hôtel de Ville 1
    ├─ Academy 1
    ├─ Caserne 1
    ├─ Port 1
    ├─ Windmill 1
    ├─ Thermes 1
    └─ Scierie 1
    ↓
BUILD_ORDER terminé ?
    ↓ OUI
[SYSTÈME INTELLIGENT]
    ↓
Analyse tous les bâtiments
    ↓
Calcul prévisionnel (local + transport)
    ↓
Sauvegarde décision si attente ≤ 24h
    ↓
Recalcul après 360 ticks (1h) ou si constructible
```

---

## 📊 Groupes de Bâtiments

### Groupe 1 : Bâtiments Économiques (Décision Intelligente)

| Bâtiment | Critère d'upgrade | Score |
|----------|-------------------|-------|
| **Hôtel de Ville** | Capacité sites ≥ 75% de capacité HdV | 90 |
| **Entrepôt** | Stockage ≥ 90% plein | 95 |
| **Entrepôt** | Stockage ≥ 80% plein | 85 |
| **Entrepôt** | Stockage ≥ 70% plein | 70 |
| **Entrepôt** | Stockage ≥ 60% plein | 50 |
| **Academy** | Peut être upgradé | 70 |

### Groupe 2 : Bâtiments Annexes (Suivent Référence)

| Bâtiment | Règle de niveau | Score |
|----------|-----------------|-------|
| **Thermes** | Niveau Hôtel de Ville | 65 |
| **Windmill** | Niveau Hôtel de Ville | 65 |
| **Scierie** | Niveau Hôtel de Ville + 3 | 60 |
| **Centre de Ressources** | Niveau Hôtel de Ville + 2 | 60 |
| **Atelier d'Architecte** | Niveau Hôtel de Ville + 2 | 60 |

---

## ⏱️ Système de Prévisionnel

### Calcul du temps d'attente

```python
Pour chaque bâtiment candidat:
    1. Récupérer coût (buildings.json)
    2. Calculer ressources locales (ville actuelle)
    3. Calculer ressources transportables (autres villes IA, 50%)
    4. total_disponible = local + transportable
    5. manque = coût - total_disponible
    
    Si manque ≤ 0:
        → Constructible immédiatement
    Sinon:
        temps_attente_heures = manque / production_horaire
        
        Si production_horaire = 0:
            → Colonisation nécessaire (attente infinie)
```

### Sélection du meilleur bâtiment

```python
candidats_abordables = [c for c in candidats if c.attente < ∞]
tri_par = score / (1 + attente_heures)  # Favorise score élevé + attente courte
meilleur = candidats_abordables[0]
```

---

## 💾 Sauvegarde des Décisions

### Fichier: `ai_strategies_state.json`

```json
{
  "ai_player_7": {
    "building_decisions": {
      "city_123": {
        "building": "Hôtel de Ville",
        "tick": 12450,
        "wait_hours": 3.5,
        "cost": {
          "wood": 1000,
          "stone": 500
        }
      }
    }
  }
}
```

### Logique de sauvegarde/récupération

```
Décision de construction demandée
    ↓
Décision sauvegardée existe ?
    ├─ OUI → Vérifier état
    │   ├─ Tick écoulé ≥ 360 (1h) → Recalculer
    │   ├─ Attente > 24h → Abandonner + recalculer
    │   ├─ Ressources disponibles → Construire
    │   └─ Sinon → Continuer d'attendre
    │
    └─ NON → Calculer nouveau bâtiment
        ├─ Si attente = 0 → Construire
        ├─ Si attente ≤ 24h → Sauvegarder
        └─ Si attente > 24h → Colonisation requise
```

---

## 🔄 Intervalles de Recalcul

| Déclencheur | Intervalle |
|-------------|-----------|
| **Temps écoulé** | 360 ticks = 1 heure (10s/tick) |
| **Attente dépassée** | > 24 heures |
| **Ressources disponibles** | Immédiat |

---

## 📁 Fichiers Modifiés

### 1. `server/app/ai/strategies/building_decision_engine.py` (NOUVEAU)
**Rôle:** Moteur de décision intelligent

**Fonctions principales:**
- `decide_construction_with_forecast()` - Point d'entrée
- `_calculate_best_building_with_forecast()` - Analyse tous les bâtiments
- `_analyze_economic_buildings()` - Groupe 1 (HdV, Entrepôt, Academy)
- `_analyze_support_buildings()` - Groupe 2 (Thermes, Windmill, etc.)
- `_calculate_wait_time_with_transport()` - Calcul prévisionnel
- `_calculate_transportable_resources()` - Ressources inter-villes
- `_save_building_decision()` / `_get_saved_building_decision()` - Persistance

### 2. `server/app/ai/ai_controller.py` (MODIFIÉ)
**Changements:**
- Ajout `import os` (ligne 13)
- `_decide_construction()` : Transition vers système intelligent après BUILD_ORDER (ligne ~363)
- `_decide_construction_intelligent()` : Nouvelle fonction (ligne ~365)

**Code clé:**
```python
# Ligne ~363
if BUILD_ORDER_complete:
    return self._decide_construction_intelligent(ai_player, city)

# Ligne ~365
def _decide_construction_intelligent(self, ai_player: Dict, city: Dict) -> Dict:
    from app.ai.strategies.building_decision_engine import decide_construction_with_forecast
    current_tick = ai_player.get('ai_cycle_counter', 0)
    decision = decide_construction_with_forecast(city, player, ai_player, current_tick)
    # ... conversion en action IA
```

### 3. `server/app/ai/strategies/resource_analyzers.py` (INCHANGÉ)
**Utilisation:**
- `analyze_population_needs()` - Déjà existante, maintenant utilisée par le système intelligent

### 4. `server/app/game_logic.py` (CORRECTIF)
**Changement:** Ajout `import logging` (ligne 34)

---

## 🧪 Tests à Effectuer

### Test 1: Transition BUILD_ORDER → Intelligent
1. Créer nouvelle ville IA
2. Vérifier que BUILD_ORDER est suivi (7 bâtiments)
3. Vérifier passage au système intelligent après

### Test 2: Calcul de prévisionnel
1. Ville IA avec ressources limitées
2. Vérifier calcul temps d'attente
3. Vérifier prise en compte transport inter-villes

### Test 3: Sauvegarde/récupération
1. Décision sauvegardée avec attente 5h
2. Vérifier que IA attend sans recalculer
3. Après 360 ticks (1h), vérifier recalcul

### Test 4: Abandon après 24h
1. Décision avec attente > 24h
2. Vérifier abandon + nouveau calcul

### Test 5: Construction immédiate
1. Ressources disponibles
2. Vérifier construction sans attente

---

## 📈 Améliorations Futures

### Possibilités d'extension

1. **Priorisation dynamique des urgences**
   - Modifier scores en fonction de situations critiques
   - Ex: Stockage à 95% → Score Entrepôt = 100

2. **Optimisation du transport**
   - Calculer coût/temps réel du transport
   - Éviter transport si temps > production locale

3. **Prévision multi-bâtiments**
   - Planifier séquence de 3-5 bâtiments
   - Optimiser l'ordre pour minimiser temps total

4. **Adaptation aux recherches**
   - Prioriser Academy si recherche importante bloquée
   - Ajuster scores selon besoins de recherche

5. **Analyse des cycles de production**
   - Détecter surplus/déficit cycliques
   - Adapter stratégie en conséquence

---

## 🐛 Points de Vigilance

### Problèmes potentiels

1. **Boucle infinie d'attente**
   - Symptôme: Décision sauvegardée jamais construite
   - Cause: Production = 0 mais pas détecté
   - Solution: Recalcul après 360 ticks

2. **Surcharge de transport**
   - Symptôme: Ressources jamais disponibles malgré prévisions
   - Cause: Transport entre villes pas implémenté
   - Solution: Utilise 50% des ressources disponibles (réserve)

3. **Conflits de décisions multi-villes**
   - Symptôme: Plusieurs villes veulent même ressource transportable
   - Cause: Pas de coordination globale
   - Solution: Chaque ville calcule indépendamment (50% réserve)

4. **Tick counter reset**
   - Symptôme: Recalculs intempestifs
   - Cause: `ai_cycle_counter` peut être réinitialisé
   - Solution: Utilise différence de ticks, pas valeur absolue

---

## 📚 Références

- [AI_SYSTEM_CURRENT.md](AI_SYSTEM_CURRENT.md) - Documentation système IA complet
- [CITY_LIFE_IMPROVEMENTS_PLAN.md](../CITY_LIFE_IMPROVEMENTS_PLAN.md) - Plan amélioration globale
- `server/app/ai/strategies/development_strategy.py` - BUILD_ORDER original
- `server/data/buildings.json` - Définitions bâtiments

---

## ✅ Checklist d'implémentation

- [x] Créer `building_decision_engine.py`
- [x] Implémenter analyse Groupe 1 (économique)
- [x] Implémenter analyse Groupe 2 (annexes)
- [x] Implémenter calcul prévisionnel avec transport
- [x] Implémenter sauvegarde/récupération décisions
- [x] Modifier `ai_controller.py` pour transition
- [x] Ajouter imports manquants (`os`, `logging`)
- [x] Documenter système complet
- [ ] Tester transition BUILD_ORDER → Intelligent
- [ ] Tester calculs de prévisionnel
- [ ] Tester sauvegarde/récupération
- [ ] Tester avec plusieurs villes IA
- [ ] Optimiser si ralentissements détectés

---

**Statut final:** Système complet implémenté, prêt pour tests en conditions réelles.
