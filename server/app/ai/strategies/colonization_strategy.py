"""
Stratégie de colonisation autonome pour l'IA.

ARCHITECTURE DESCENDANTE:
- Phase 3: Débloquer recherches (expansion ← astronomie_primitive)
- Phase 2: Construire Ambassade (800 wood)
- Phase 1: Sélectionner île + coloniser

Déclenchée par: decide_resource_shortage_solution() retourne 'colonize'
"""

from typing import Dict, Optional
import json
import os
import math


# ============================================================
# PHASE 3: DÉBLOQUER RECHERCHES
# ============================================================

def execute_phase_unlock_research(player_id: str, city: Dict, savegame_data: Dict, phase_data: Dict) -> Optional[Dict]:
    """
    Phase 3: Débloquer les recherches nécessaires (astronomie_primitive → expansion).
    
    Args:
        player_id: ID du joueur IA
        city: Données de la ville principale
        savegame_data: Données complètes du savegame
        phase_data: État de progression de la stratégie
    
    Returns:
        Dict avec action à exécuter, ou None si en attente
    """
    print(f"🔬 [{player_id}] Phase 3: Déblocage recherches")
    
    # Pour player_8 (joueur IA sans entrée dans players.json), 
    # utiliser directement les données de la ville
    # Récupérer le joueur depuis players.json
    players_data = _load_players_data()
    player = next((p for p in players_data.get('players', []) if p.get('id') == player_id), None)
    
    # Si joueur non trouvé dans players.json (cas player_8 IA),
    # créer un objet player fictif avec les données de la ville
    if not player:
        print(f"ℹ️ [{player_id}] Joueur non trouvé dans players.json, utilisation des données ville")
        player = {
            'id': player_id,
            'research_points': city.get('resources', {}).get('research_points', 0),
            'unlocked_research': city.get('unlocked_research', []),
            'gold': city.get('resources', {}).get('gold', 0)
        }
    
    unlocked_research = player.get('unlocked_research', [])
    print(f"📚 [{player_id}] Recherches débloquées: {unlocked_research}")
    
    # Sous-phase 3.1: Débloquer astronomie_primitive
    if 'astronomie_primitive' not in unlocked_research:
        print(f"🎯 [{player_id}] Besoin de débloquer astronomie_primitive")
        return _unlock_astronomie_primitive(player_id, player, city, phase_data)
    
    # Sous-phase 3.2: Débloquer expansion
    if 'expansion' not in unlocked_research:
        print(f"🎯 [{player_id}] Besoin de débloquer expansion")
        return _unlock_expansion(player_id, player, city, phase_data)
    
    # Phase 3 terminée → passer à Phase 2
    print(f"✅ [{player_id}] PHASE 3 terminée: Recherches débloquées")
    return {
        'action': 'change_phase',
        'next_phase': 'build_embassy',
        'reason': 'Recherches expansion + astronomie_primitive débloquées'
    }


def _unlock_astronomie_primitive(player_id: str, player: Dict, city: Dict, phase_data: Dict) -> Optional[Dict]:
    """Sous-phase 3.1: Débloquer astronomie_primitive (100 RP + 50 gold)."""
    # Charger coûts depuis research.json
    research_data = _load_research_data()
    astro_research = next((r for r in research_data.get('researches', []) if r.get('id') == 'astronomie_primitive'), None)
    
    if not astro_research:
        print(f"⚠️ [{player_id}] Recherche astronomie_primitive introuvable dans research.json")
        return None
    
    cost = astro_research.get('cost', {})
    research_points_needed = cost.get('research_points', 100)
    gold_needed = cost.get('gold', 50)
    
    # Vérifier stocks actuels
    current_rp = player.get('research_points', 0)
    current_gold = player.get('gold', 0)
    
    # Calculer manques
    rp_missing = max(0, research_points_needed - current_rp)
    gold_missing = max(0, gold_needed - current_gold)
    
    if rp_missing > 0 or gold_missing > 0:
        # Pas assez de ressources → ATTENDRE
        print(f"⏳ [{player_id}] Phase 3.1: Attente astronomie_primitive")
        print(f"   RP: {current_rp}/{research_points_needed} (manque: {rp_missing})")
        print(f"   Gold: {current_gold}/{gold_needed} (manque: {gold_missing})")
        return None
    
    # Ressources suffisantes → DÉBLOQUER
    print(f"🔬 [{player_id}] Phase 3.1: Déblocage astronomie_primitive")
    return {
        'action': 'unlock_research',
        'research_id': 'astronomie_primitive',
        'city_id': city.get('id'),
        'reason': 'Prérequis pour expansion'
    }


def _unlock_expansion(player_id: str, player: Dict, city: Dict, phase_data: Dict) -> Optional[Dict]:
    """Sous-phase 3.2: Débloquer expansion (400 RP + 60 gold)."""
    # Charger coûts depuis research.json
    research_data = _load_research_data()
    expansion_research = next((r for r in research_data.get('researches', []) if r.get('id') == 'expansion'), None)
    
    if not expansion_research:
        print(f"⚠️ [{player_id}] Recherche expansion introuvable dans research.json")
        return None
    
    cost = expansion_research.get('cost', {})
    research_points_needed = cost.get('research_points', 400)
    gold_needed = cost.get('gold', 60)
    
    # Vérifier stocks actuels
    current_rp = player.get('research_points', 0)
    current_gold = player.get('gold', 0)
    
    # Calculer manques
    rp_missing = max(0, research_points_needed - current_rp)
    gold_missing = max(0, gold_needed - current_gold)
    
    if rp_missing > 0 or gold_missing > 0:
        # Pas assez de ressources → ATTENDRE
        print(f"⏳ [{player_id}] Phase 3.2: Attente expansion")
        print(f"   RP: {current_rp}/{research_points_needed} (manque: {rp_missing})")
        print(f"   Gold: {current_gold}/{gold_needed} (manque: {gold_missing})")
        return None
    
    # Ressources suffisantes → DÉBLOQUER
    print(f"🔬 [{player_id}] Phase 3.2: Déblocage expansion")
    return {
        'action': 'unlock_research',
        'research_id': 'expansion',
        'city_id': city.get('id'),
        'reason': 'Prérequis pour Ambassade'
    }


# ============================================================
# PHASE 2: CONSTRUIRE AMBASSADE
# ============================================================

def execute_phase_build_embassy(player_id: str, city: Dict, savegame_data: Dict, phase_data: Dict) -> Optional[Dict]:
    """
    Phase 2: Construire l'Ambassade niveau 1 (800 wood).
    
    Args:
        player_id: ID du joueur IA
        city: Données de la ville principale
        savegame_data: Données complètes du savegame
        phase_data: État de progression de la stratégie
    
    Returns:
        Dict avec action à exécuter, ou None si en attente
    """
    # Vérifier si Ambassade déjà construite
    buildings = city.get('buildings', [])
    embassy = next((b for b in buildings if b.get('name') == 'Ambassade'), None)
    
    if embassy and embassy.get('level', 0) >= 1:
        # Ambassade déjà niveau 1+ → Phase 2 terminée
        print(f"✅ [{player_id}] PHASE 2 terminée: Ambassade niveau {embassy.get('level')}")
        return {
            'action': 'change_phase',
            'next_phase': 'select_island',
            'reason': 'Ambassade construite'
        }
    
    # Charger coûts depuis buildings.json
    buildings_data = _load_buildings_data()
    embassy_data = buildings_data.get('Ambassade', {})
    level_1 = next((l for l in embassy_data.get('levels', []) if l.get('level') == 1), None)
    
    if not level_1:
        print(f"⚠️ [{player_id}] Ambassade niveau 1 introuvable dans buildings.json")
        return None
    
    cost = level_1.get('cost', {})
    wood_needed = cost.get('wood', 800)
    
    # Vérifier stock actuel
    current_wood = city.get('resources', {}).get('wood', 0)
    wood_missing = max(0, wood_needed - current_wood)
    
    if wood_missing > 0:
        # Pas assez de wood → Optimiser production
        print(f"⏳ [{player_id}] Phase 2: Attente wood pour Ambassade")
        print(f"   Wood: {current_wood:.0f}/{wood_needed} (manque: {wood_missing:.0f})")
        
        # Retourner une action pour optimiser la production de wood
        # L'ai_controller utilisera cela pour orienter les workers/construction
        return {
            'action': 'wait_resource',
            'resource': 'wood',
            'amount_needed': wood_needed,
            'amount_current': current_wood,
            'amount_missing': wood_missing,
            'reason': f'Manquant: wood: {wood_missing:.0f} (besoin: {wood_needed})'
        }
    
    # Vérifier qu'il y a un slot libre
    if not _has_free_building_slot(city):
        print(f"⏳ [{player_id}] Phase 2: Pas de slot libre pour Ambassade")
        return None
    
    # Tout est OK → CONSTRUIRE
    print(f"🏛️ [{player_id}] Phase 2: Construction Ambassade")
    return {
        'action': 'build',
        'building_name': 'Ambassade',
        'city_id': city.get('id'),
        'reason': 'Débloquer colonisation'
    }


# ============================================================
# PHASE 1: SÉLECTIONNER ÎLE ET COLONISER
# ============================================================

def execute_phase_select_island(player_id: str, city: Dict, savegame_data: Dict, phase_data: Dict) -> Optional[Dict]:
    """
    Phase 1: Sélectionner l'île cible et coloniser.
    
    Args:
        player_id: ID du joueur IA
        city: Données de la ville principale
        savegame_data: Données complètes du savegame
        phase_data: État de progression de la stratégie
    
    Returns:
        Dict avec action à exécuter, ou None si impossible
    """
    missing_resource = phase_data.get('missing_resource')
    
    if not missing_resource:
        print(f"⚠️ [{player_id}] Phase 1: Ressource manquante non définie")
        return None
    
    # Trouver île cible (si pas déjà calculée)
    target_island_id = phase_data.get('target_island_id')
    target_city_id = phase_data.get('target_city_id')
    
    if not target_island_id or not target_city_id:
        # Calculer meilleure île
        target_data = _find_best_island(missing_resource, city, savegame_data)
        
        if not target_data:
            print(f"❌ [{player_id}] Phase 1: Aucune île disponible pour {missing_resource}")
            return {
                'action': 'abort_strategy',
                'reason': f'Aucune île avec {missing_resource} disponible'
            }
        
        target_island_id = target_data['island_id']
        target_city_id = target_data['city_id']
        
        print(f"🎯 [{player_id}] Phase 1: Île cible trouvée")
        print(f"   Île: {target_island_id} (ressource: {target_data['resource']})")
        print(f"   Distance: {target_data['distance']:.1f}")
        
        # Sauvegarder cible dans phase_data
        return {
            'action': 'update_phase_data',
            'updates': {
                'target_island_id': target_island_id,
                'target_city_id': target_city_id,
                'target_resource': target_data['resource']
            }
        }
    
    # Cible déjà définie → COLONISER
    print(f"🏰 [{player_id}] Phase 1: Colonisation île {target_island_id}")
    return {
        'action': 'colonize',
        'island_id': target_island_id,
        'city_id': target_city_id,
        'reason': f'Colonisation pour {missing_resource}'
    }


def _find_best_island(resource: str, current_city: Dict, savegame_data: Dict) -> Optional[Dict]:
    """
    Trouve la meilleure île pour coloniser en fonction de la ressource manquante.
    
    Critères:
    1. Île possède la ressource (base_resource ou advanced_resource)
    2. Île a un slot libre
    3. Proximité (distance minimale)
    
    Returns:
        {
            'island_id': str,
            'city_id': str,
            'resource': str,
            'distance': float
        }
    """
    universe_data = _load_universe_data()
    islands = universe_data.get('islands', [])
    
    # Coordonnées ville actuelle
    current_island_id = current_city.get('island_id')
    current_island = next((isl for isl in islands if str(isl.get('id')) == str(current_island_id)), None)
    
    if not current_island:
        return None
    
    current_coords = current_island.get('coords', [0, 0])
    current_x = current_coords[0]
    current_y = current_coords[1]
    
    # Filtrer îles par ressource
    candidate_islands = []
    
    for island in islands:
        base_resource = island.get('base_resource')
        advanced_resource = island.get('advanced_resource')
        
        # Vérifier si île a la ressource
        if base_resource != resource and advanced_resource != resource:
            continue
        
        # Vérifier si île a un slot libre
        free_slot = _get_free_city_slot(island, savegame_data)
        if not free_slot:
            continue
        
        # Calculer distance
        island_coords = island.get('coords', [0, 0])
        island_x = island_coords[0]
        island_y = island_coords[1]
        distance = math.sqrt((island_x - current_x)**2 + (island_y - current_y)**2)
        
        candidate_islands.append({
            'island_id': str(island.get('id')),
            'city_id': free_slot,
            'resource': advanced_resource if advanced_resource == resource else base_resource,
            'distance': distance,
            'x': island_x,
            'y': island_y
        })
    
    # Trier par distance (plus proche d'abord)
    candidate_islands.sort(key=lambda x: x['distance'])
    
    return candidate_islands[0] if candidate_islands else None


def _get_free_city_slot(island: Dict, savegame_data: Dict) -> Optional[str]:
    """
    Trouve un slot de ville libre sur l'île depuis universe.json.
    
    Returns:
        city_id du slot libre, ou None si aucun
    """
    # Charger les villes depuis l'île dans universe.json
    elements = island.get('elements', [])
    city_elements = [e for e in elements if e.get('type') == 'city']
    
    # Vérifier quelles villes sont déjà prises
    cities = savegame_data.get('cities', [])
    occupied_city_ids = {c.get('id') for c in cities}
    
    # Trouver la première ville libre (owner = null et pas dans savegame)
    for city_elem in city_elements:
        city_id = city_elem.get('id')
        owner = city_elem.get('owner')
        
        # Ville libre si owner=null ET pas dans occupied_city_ids
        if owner is None and city_id not in occupied_city_ids:
            return city_id
    
    return None


# ============================================================
# UTILITAIRES
# ============================================================

def _load_research_data() -> Dict:
    """Charge research.json."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        research_path = os.path.join(base_dir, 'data', 'research.json')
        
        with open(research_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Erreur chargement research.json: {e}")
        return {}


def _load_buildings_data() -> Dict:
    """Charge buildings.json."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        buildings_path = os.path.join(base_dir, 'data', 'buildings.json')
        
        with open(buildings_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Erreur chargement buildings.json: {e}")
        return {}


def _load_universe_data() -> Dict:
    """Charge universe.json."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        universe_path = os.path.join(base_dir, 'data', 'universe.json')
        
        with open(universe_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Erreur chargement universe.json: {e}")
        return {}


def _load_players_data() -> Dict:
    """Charge players.json depuis gamedata/ SANS CACHE."""
    try:
        # Utiliser data_manager pour bénéficier du système de gestion
        from app.data_manager import DataManager
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        data_manager = DataManager(base_dir)
        
        # IMPORTANT: use_cache=False pour avoir les données fraîches
        return data_manager.load_players(use_cache=False)
    except Exception as e:
        print(f"⚠️ Erreur chargement players.json: {e}")
        return {}


def _has_free_building_slot(city: Dict) -> bool:
    """Vérifie si la ville a un slot de construction libre."""
    buildings = city.get('buildings', [])
    
    # Compter bâtiments en construction ou terminés
    occupied_slots = len([b for b in buildings if b.get('status') in ['Terminé', 'En construction']])
    
    # Maximum slots (dépend du layout, supposons 20 pour simplifier)
    max_slots = 20
    
    return occupied_slots < max_slots
