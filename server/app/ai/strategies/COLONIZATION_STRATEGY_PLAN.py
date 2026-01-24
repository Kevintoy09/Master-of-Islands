"""
STRATÉGIE DE COLONISATION - ARCHITECTURE SENS DÉCROISSANT

===============================================================================
PRINCIPE GÉNÉRAL
===============================================================================

La colonisation est déclenchée lorsque l'IA manque d'une ressource avancée
(fer, verre, vin, marbre, etc.) qu'elle ne peut pas produire sur son île actuelle.

DÉCLENCHEUR: Manque d'une ressource spécifique non disponible localement.

OBJECTIF: Coloniser une île possédant la ressource manquante.


===============================================================================
PHASES DE LA STRATÉGIE (SENS DÉCROISSANT = DU PLUS HAUT AU PLUS BAS)
===============================================================================

PHASE 1: CHOISIR UNE VILLE SUR UNE ÎLE À COLONISER
──────────────────────────────────────────────────
Objectif: Identifier l'île cible et le slot de ville à coloniser.

Critères de sélection:
  1. Ressource manquante (priorité absolue)
     - Vérifier quelle ressource avancée manque à l'IA
     - Trouver une île qui produit cette ressource
  
  2. Proximité de la ville principale
     - Calculer distance entre ville actuelle et île cible
     - Privilégier îles proches pour réduire temps de transport
  
  3. Disponibilité
     - Vérifier qu'il existe un slot de ville libre sur l'île
     - Vérifier que l'île n'a pas déjà 4 joueurs (limite backend)

Actions nécessaires:
  - Charger universe.json pour lister toutes les îles
  - Filtrer îles par ressource manquante
  - Calculer distances depuis ville actuelle
  - Sélectionner meilleure île (ressource + proximité)
  - Identifier city_id du slot libre

Sortie de phase:
  → target_island_id: ID de l'île cible
  → target_city_id: ID du slot de ville à coloniser
  → target_resource: Ressource de l'île (fer, verre, etc.)


PHASE 2: AVOIR LES RESSOURCES NÉCESSAIRES (AMBASSADE)
──────────────────────────────────────────────────────
Objectif: Accumuler les ressources pour construire l'Ambassade niveau 1.

Prérequis:
  - Recherche "expansion" débloquée (voir PHASE 3)

Coûts Ambassade (lus depuis buildings.json):
  - Niveau 1: {"wood": 800}
  - Construction time: 10800 secondes (3h)
  - Effect: {"max_colonies": 2}

Actions nécessaires:
  - Charger buildings.json → section "Ambassade" → levels[0]
  - Vérifier stock actuel de wood dans city.resources
  - Calculer manque: needed = cost["wood"] - current_stock["wood"]
  - Si manque > 0:
    * Vérifier production_rate de wood
    * Estimer temps d'attente: time = needed / production_rate
    * ATTENDRE (pas d'upgrade, resource_analyzer s'en occupe)
  - Si stock suffisant:
    * Vérifier qu'il y a un slot de construction libre
    * Construire Ambassade via API /api/city/<city_id>/build

Sortie de phase:
  → Ambassade niveau 1 construite
  → max_colonies = 2 disponible


PHASE 3: DÉBLOQUER L'AMBASSADE (RECHERCHES PRÉALABLES)
───────────────────────────────────────────────────────
Objectif: Débloquer les recherches nécessaires pour l'Ambassade.

Arbre de dépendances (lu depuis research.json):
  
  Ambassade (bâtiment)
    ↑ required_research: "expansion"
    │
    └── expansion (recherche niveau 2)
        ├─ cost: {"research_points": 400, "gold": 60}
        ├─ prerequisites: ["astronomie_primitive"]
        └── astronomie_primitive (recherche niveau 1)
            ├─ cost: {"research_points": 100, "gold": 50}
            └─ prerequisites: []

Sous-phase 3.1: Débloquer "astronomie_primitive"
  - Charger research.json → trouver id="astronomie_primitive"
  - Vérifier si déjà débloquée (player.unlocked_research)
  - Si non débloquée:
    * Vérifier stock: research_points >= 100 ET gold >= 50
    * Si manque de research_points:
      → resource_analyzer s'occupe de l'Académie
      → ATTENDRE production naturelle
    * Si stock suffisant:
      → Débloquer via API /api/research/unlock

Sous-phase 3.2: Débloquer "expansion"
  - Vérifier prerequisite "astronomie_primitive" débloquée
  - Charger research.json → trouver id="expansion"
  - Vérifier stock: research_points >= 400 ET gold >= 60
  - Si manque:
    * ATTENDRE production (resource_analyzer gère upgrades)
  - Si stock suffisant:
    * Débloquer via API /api/research/unlock

Coût total:
  - 500 research_points (100 + 400)
  - 110 gold (50 + 60)

Sortie de phase:
  → "expansion" débloquée
  → Ambassade constructible


===============================================================================
FLUX D'EXÉCUTION COMPLET (RÉSUMÉ)
===============================================================================

1. IA détecte manque de ressource (ex: fer)
   ↓
2. PHASE 3: Débloquer recherches
   3.1: Débloquer astronomie_primitive (100 RP + 50 gold)
   3.2: Débloquer expansion (400 RP + 60 gold)
   ↓
3. PHASE 2: Construire Ambassade
   Accumuler 800 wood
   Construire Ambassade niveau 1
   ↓
4. PHASE 1: Choisir île et coloniser
   Sélectionner île avec fer (ressource manquante)
   Calculer proximité
   Sélectionner city_id libre
   Appeler API /api/city/colonize
   ↓
5. SUCCÈS: Nouvelle ville colonisée
   → Stratégie future: Accumuler ressource sur nouvelle ville
   → Transporter vers ville principale


===============================================================================
STRUCTURE DE DONNÉES (ai_strategies_state.json)
===============================================================================

{
  "player_<id>": {
    "current_strategy": "colonization",
    "current_phase": "unlock_research",  // unlock_research | build_embassy | select_island
    "phase_data": {
      "missing_resource": "iron",          // Ressource qui déclenche colonisation
      "target_island_id": null,            // ID île cible (phase 1)
      "target_city_id": null,              // ID city à coloniser (phase 1)
      "target_resource": null,             // Ressource de l'île cible (phase 1)
      "astronomie_primitive": "completed", // completed | in_progress | not_started
      "expansion": "in_progress",          // completed | in_progress | not_started
      "embassy_level": 0,                  // Niveau actuel Ambassade
      "started_at": "2026-01-10T12:00:00"
    }
  }
}


===============================================================================
ANALYSEURS NÉCESSAIRES (À IMPLÉMENTER)
===============================================================================

1. detect_missing_resource(player, city) → str | None
   - Vérifie quelles ressources avancées manquent
   - Retourne nom de ressource (ex: "iron") ou None
   - Logique: vérifier buildings.json upgrades impossibles par manque ressource

2. find_target_island(missing_resource, player, universe_data) → dict
   - Trouve meilleure île pour ressource donnée
   - Critères: ressource + proximité + disponibilité
   - Retourne: {island_id, city_id, resource, distance}

3. check_research_status(player, research_id) → bool
   - Vérifie si recherche débloquée
   - Lit player.unlocked_research

4. check_embassy_requirements(player, city) → dict
   - Lit buildings.json pour coûts Ambassade
   - Compare avec stocks actuels
   - Retourne: {has_resources: bool, missing: dict, can_build: bool}

5. check_research_requirements(player, research_id) → dict
   - Lit research.json pour coûts recherche
   - Vérifie prerequisites
   - Retourne: {has_requirements: bool, missing: dict, can_unlock: bool}


===============================================================================
INTÉGRATION AVEC AUTRES STRATÉGIES
===============================================================================

- La stratégie de colonisation s'exécute EN PARALLÈLE de la stratégie de développement
- resource_analyzer continue de gérer optimisation workers + upgrades Académie
- development_strategy continue BUILD_ORDER sur ville principale
- Pas de conflit: colonisation ne consomme ressources qu'une fois accumulées

Après colonisation:
  → Nouvelle ville = stratégie dédiée (à définir plus tard)
  → Probablement: développement basique + accumulation ressource spécialisée
  → Transport vers ville principale


===============================================================================
NOTES IMPORTANTES
===============================================================================

✅ PAS DE HARDCODING: Tous les coûts/prérequis lus depuis JSON
✅ Sens décroissant: Phase 1 (choisir île) → 2 (ressources) → 3 (recherches)
✅ Logique claire: 1 phase = 1 objectif vérifiable
✅ Robustesse: Gérer cas où recherches déjà débloquées
✅ Modularité: Analyseurs réutilisables pour autres stratégies
"""
