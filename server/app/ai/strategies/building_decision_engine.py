"""
Moteur de décision intelligent pour la construction de bâtiments.

Ce fichier contient la logique avancée de décision pour l'IA après le BUILD_ORDER initial.
Analyse les besoins de tous les bâtiments et optimise les choix en fonction :
- Des ressources disponibles (locales + transport inter-villes)
- De la production horaire
- Du temps d'attente estimé
- Des priorités stratégiques

GROUPES DE BÂTIMENTS:

Groupe 1 (Économique - Décision intelligente):
- Hôtel de Ville : Basé sur capacité population vs sites
- Entrepôt : Basé sur taux de remplissage stockage
- Academy : Basé sur gain temps recherche

Groupe 2 (Annexes - Suivent référence):
- Thermes → niveau Hôtel de Ville
- Windmill → niveau Hôtel de Ville
- Scierie → niveau Hôtel de Ville + 2
- Centre de Ressources → niveau Hôtel de Ville + 1
- Atelier d'Architecte → niveau Hôtel de Ville + 1

WORKFLOW:
1. Vérifier décision sauvegardée
2. Si sauvegardée : vérifier si constructible ou abandonner si > 24h
3. Si pas sauvegardée : calculer tous les bâtiments avec prévisionnel
4. Sauvegarder décision ou construire immédiatement
"""

from typing import Dict, List, Optional
import json
import os
import time


# ============================================================
# CONFIGURATION
# ============================================================

RECALCULATION_INTERVAL_TICKS = 360  # Recalculer toutes les heures (1h = 360 ticks à 10s)
MAX_WAIT_HOURS = 24  # Abandonner décision si attente > 24h


# ============================================================
# FONCTION PRINCIPALE
# ============================================================

def decide_construction_with_forecast(city: Dict, player: Dict, ai_player: Dict, current_tick: int) -> Dict:
    """
    Décide du prochain bâtiment à construire avec système de prévisionnel et sauvegarde.
    
    Workflow:
    1. Vérifier si décision déjà sauvegardée
    2. Si oui : vérifier si constructible maintenant ou si trop vieux
    3. Si non : calculer meilleur bâtiment avec temps d'attente
    4. Sauvegarder ou retourner action
    
    Args:
        city: Données de la ville
        player: Données du joueur
        ai_player: Données spécifiques IA
        current_tick: Numéro du tick actuel
    
    Returns:
        {
            'action': 'build'|'upgrade'|'wait',
            'building_name': str,
            'reason': str,
            'wait_hours': float (optionnel)
        }
    """
    player_id = ai_player.get('id')
    city_id = city.get('id')
    
    # 1. Vérifier décision sauvegardée
    saved_decision = _get_saved_building_decision(player_id, city_id)
    
    if saved_decision:
        elapsed_ticks = current_tick - saved_decision.get('tick', 0)
        elapsed_hours = elapsed_ticks * 10 / 3600  # 10s par tick
        
        # Recalcul si > 1 heure
        if elapsed_ticks >= RECALCULATION_INTERVAL_TICKS:
            _clear_saved_decision(player_id, city_id)
            # Continue vers calcul ci-dessous
        
        # Abandonner si > 24h
        elif elapsed_hours > MAX_WAIT_HOURS:
            _clear_saved_decision(player_id, city_id)
            return {
                'action': 'wait',
                'building_name': None,
                'reason': f"Abandon {saved_decision['building']} (attente > 24h)"
            }
        
        # Vérifier si constructible maintenant
        elif _can_build_now(city, saved_decision):
            _clear_saved_decision(player_id, city_id)
            return {
                'action': 'upgrade',
                'building_name': saved_decision['building'],
                'reason': f"Ressources disponibles pour {saved_decision['building']}"
            }
        
        # Continuer d'attendre
        else:
            return {
                'action': 'wait',
                'building_name': saved_decision['building'],
                'reason': f"Attente ressources ({elapsed_hours:.1f}h/{saved_decision['wait_hours']:.1f}h)",
                'wait_hours': saved_decision['wait_hours'] - elapsed_hours
            }
    
    # 2. Pas de décision sauvegardée → CALCULER
    decision = _calculate_best_building_with_forecast(city, player, ai_player)
    
    if not decision or decision['score'] == 0:
        return {
            'action': 'wait',
            'building_name': None,
            'reason': 'Aucun bâtiment prioritaire'
        }
    
    # 3. Constructible immédiatement ?
    if decision['can_build_now']:
        return {
            'action': 'upgrade',
            'building_name': decision['building'],
            'reason': decision['reason']
        }
    
    # 4. Attente raisonnable → sauvegarder
    elif decision['wait_hours'] <= MAX_WAIT_HOURS:
        _save_building_decision(player_id, city_id, decision, current_tick)
        return {
            'action': 'wait',
            'building_name': decision['building'],
            'reason': f"Planifié: {decision['building']} (attente {decision['wait_hours']:.1f}h)",
            'wait_hours': decision['wait_hours']
        }
    
    # 5. Attente trop longue → colonisation nécessaire
    else:
        return {
            'action': 'wait',
            'building_name': None,
            'reason': f"Colonisation requise pour {decision['building']} (attente {decision['wait_hours']:.1f}h > 24h)"
        }


# ============================================================
# ANALYSE DES BÂTIMENTS
# ============================================================

def _analyze_townhall_needs(city: Dict, player_id: str, ai_player: Dict) -> Dict:
    """
    Analyse si l'Hôtel de Ville doit être upgradé.
    Utilise la fonction existante de resource_analyzers.py
    """
    try:
        from .resource_analyzers import analyze_population_needs
        return analyze_population_needs(city, player_id, ai_player)
    except Exception as e:
        print(f"⚠️ Erreur analyse Hôtel de Ville: {e}")
        return {'needs_upgrade': False}


def _calculate_best_building_with_forecast(city: Dict, player: Dict, ai_player: Dict) -> Optional[Dict]:
    """
    Analyse tous les bâtiments et retourne celui avec le meilleur ratio score/temps.
    
    Returns:
        {
            'building': str,
            'score': float,
            'can_build_now': bool,
            'wait_hours': float,
            'cost': dict,
            'reason': str
        }
    """
    candidates = []
    
    # Groupe 1 : Bâtiments économiques
    candidates.extend(_analyze_economic_buildings(city, player, ai_player))
    
    # Groupe 2 : Bâtiments annexes
    candidates.extend(_analyze_support_buildings(city, player))
    
    # Filtrer ceux avec score > 0
    candidates = [c for c in candidates if c['score'] > 0]
    
    if not candidates:
        return None
    
    # Calculer temps d'attente pour chaque candidat
    player_cities = _get_player_cities(player['id'])
    
    for candidate in candidates:
        forecast = _calculate_wait_time_with_transport(
            city, 
            player_cities, 
            candidate['cost']
        )
        
        candidate['can_build_now'] = forecast['can_build_now']
        candidate['wait_hours'] = forecast['wait_hours']
    
    # Filtrer ceux avec wait_hours < infini
    affordable = [c for c in candidates if c['wait_hours'] < float('inf')]
    
    if not affordable:
        return None
    
    # Trier par ratio score / (1 + wait_hours)
    # Plus le score est élevé et le temps court, mieux c'est
    affordable.sort(key=lambda x: x['score'] / (1 + x['wait_hours']), reverse=True)
    
    return affordable[0]


def _analyze_economic_buildings(city: Dict, player: Dict, ai_player: Dict) -> List[Dict]:
    """
    Analyse les bâtiments économiques (Groupe 1).
    
    Returns:
        Liste de candidats avec scores
    """
    candidates = []
    
    # 1. HÔTEL DE VILLE
    townhall_analysis = _analyze_townhall_needs(city, player['id'], ai_player)
    if townhall_analysis.get('needs_upgrade'):
        # VÉRIFIER ÉQUILIBRAGE GROUPE 2 AVANT D'UPGRADER HdV
        townhall_level = _get_building_level(city, 'Hôtel de Ville')
        thermes_level = _get_building_level(city, 'Thermes')
        windmill_level = _get_building_level(city, 'Windmill')
        
        # Bloquer upgrade HdV si Thermes ou Windmill ne suivent pas
        if thermes_level < townhall_level or windmill_level < townhall_level:
            # Ne pas proposer HdV, forcer équilibrage d'abord
            pass
        else:
            candidates.append({
                'building': 'Hôtel de Ville',
                'score': 90,  # Haute priorité
                'cost': _get_building_upgrade_cost(city, 'Hôtel de Ville'),
                'reason': f"Population: sites {townhall_analysis['total_sites_capacity']} >= réserve {townhall_analysis['townhall_reserve_capacity']}"
            })
    
    # 2. ENTREPÔT (nécessite recherche "conservation")
    warehouse_score = _analyze_warehouse_needs(city)
    if warehouse_score > 0:
        # Vérifier si recherche débloquée
        required_research = _get_building_required_research('Entrepôt')
        if _is_research_unlocked(player, required_research):
            candidates.append({
                'building': 'Entrepôt',
                'score': warehouse_score,
                'cost': _get_building_upgrade_cost(city, 'Entrepôt'),
                'reason': f"Stockage critique" if warehouse_score >= 90 else "Stockage élevé"
            })
    
    # 3. ACADEMY
    # Note: analyze_research_production_needs nécessite research_points_needed
    # Pour simplifier, on vérifie juste si Academy existe et peut être upgradée
    academy_score = _analyze_academy_needs(city)
    if academy_score > 0:
        candidates.append({
            'building': 'Academy',
            'score': academy_score,
            'cost': _get_building_upgrade_cost(city, 'Academy'),
            'reason': "Accélération recherche"
        })
    
    return candidates


def _analyze_support_buildings(city: Dict, player: Dict = None) -> List[Dict]:
    """
    Analyse les bâtiments annexes (Groupe 2).
    Règle : Doivent suivre le niveau de l'Hôtel de Ville.
    
    Returns:
        Liste de candidats avec scores
    """
    candidates = []
    
    # Niveau actuel Hôtel de Ville
    townhall_level = _get_building_level(city, 'Hôtel de Ville')
    
    # Règles de niveau - SCORES AUGMENTÉS pour prioriser équilibrage
    support_buildings = [
        ('Thermes', townhall_level, 100, "Suit Hôtel de Ville"),  # 100 = PRIORITÉ ABSOLUE
        ('Windmill', townhall_level, 100, "Suit Hôtel de Ville"),  # 100 = PRIORITÉ ABSOLUE
        ('Scierie', townhall_level + 2, 85, "Production bois"),
        ('Centre de Ressources', townhall_level + 1, 85, "Production ressources"),
        ("Atelier d'Architecte", townhall_level + 1, 85, "Réduction coûts")
    ]
    
    for building_name, target_level, score, reason in support_buildings:
        current_level = _get_building_level(city, building_name)
        
        if current_level < target_level:
            # Vérifier recherche requise
            required_research = _get_building_required_research(building_name)
            if required_research and player:
                if not _is_research_unlocked(player, required_research):
                    continue  # Skip si recherche non débloquée
            
            candidates.append({
                'building': building_name,
                'score': score,
                'cost': _get_building_upgrade_cost(city, building_name),
                'reason': f"{reason} (niv {current_level} → {target_level})"
            })
    
    return candidates


def _analyze_warehouse_needs(city: Dict) -> float:
    """
    Analyse le besoin d'upgrader Entrepôt.
    
    Returns:
        Score 0-100
    """
    from app.game_logic import GameLogic
    from app.data_manager import DataManager
    import os
    
    # Obtenir les capacités réelles depuis GameLogic
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    dm = DataManager(base_dir)
    game_logic = GameLogic(dm)
    
    storage_limits = game_logic.get_city_storage_limits(city)
    resources = city.get('resources', {})
    
    # Calculer taux de remplissage moyen
    storage_resources = ['wood', 'stone', 'iron', 'cereal', 'papyrus']
    total_usage = 0
    count = 0
    
    for res in storage_resources:
        current = resources.get(res, 0)
        capacity = storage_limits.get(res, 3500)  # Défaut 3500
        if capacity > 0:
            usage_percent = (current / capacity * 100)
            total_usage += usage_percent
            count += 1
    
    avg_usage = total_usage / count if count > 0 else 0
    
    # Vérifier si l'Entrepôt existe
    has_warehouse = any(b.get('name') == 'Entrepôt' for b in city.get('buildings', []))
    
    # Si pas d'Entrepôt et qu'on peut le construire → priorité très haute
    if not has_warehouse:
        return 95  # Score très élevé pour construire le premier Entrepôt
    
    # Sinon, basé sur le taux de remplissage
    if avg_usage >= 90:
        return 95  # URGENT
    elif avg_usage >= 80:
        return 85
    elif avg_usage >= 70:
        return 70
    elif avg_usage >= 60:
        return 50
    else:
        return 0


def _analyze_academy_needs(city: Dict) -> float:
    """
    Analyse le besoin d'upgrader Academy.
    Simplifié : retourne un score si Academy existe et peut être upgradée.
    
    Returns:
        Score 0-100
    """
    academy_level = _get_building_level(city, 'Academy')
    
    if academy_level > 0 and academy_level < 30:  # Niveau max = 30
        # Score modéré car pas critique
        return 70
    
    return 0


# ============================================================
# CALCUL DU TEMPS D'ATTENTE AVEC TRANSPORT
# ============================================================

def _calculate_wait_time_with_transport(city: Dict, player_cities: List[Dict], cost: Dict) -> Dict:
    """
    Calcule le temps d'attente en tenant compte :
    - Ressources locales (ville actuelle)
    - Ressources transportables (autres villes du joueur)
    - Production horaire locale
    
    Returns:
        {
            'can_build_now': bool,
            'wait_hours': float
        }
    """
    local_resources = city.get('resources', {})
    
    # Calculer ressources transportables des autres villes
    transportable = _calculate_transportable_resources(player_cities, city['id'])
    
    # Total disponible = local + transport
    total_available = {}
    for res in cost.keys():
        local = local_resources.get(res, 0)
        transport = transportable.get(res, 0)
        total_available[res] = local + transport
    
    # Calculer manques
    shortages = {}
    for res, needed in cost.items():
        shortage = max(0, needed - total_available.get(res, 0))
        if shortage > 0:
            shortages[res] = shortage
    
    # Si pas de manque → constructible maintenant
    if not shortages:
        return {'can_build_now': True, 'wait_hours': 0}
    
    # Calculer temps production pour combler manques
    production_rates = _get_production_rates(city)
    
    max_wait_hours = 0
    for res, amount in shortages.items():
        rate = production_rates.get(res, 0)
        
        if rate > 0:
            hours = amount / rate
            max_wait_hours = max(max_wait_hours, hours)
        else:
            # Pas de production → colonisation nécessaire
            max_wait_hours = float('inf')
            break
    
    return {
        'can_build_now': False,
        'wait_hours': max_wait_hours
    }


def _calculate_transportable_resources(player_cities: List[Dict], exclude_city_id: str) -> Dict:
    """
    Calcule les ressources disponibles dans les autres villes du joueur.
    
    Simplifié : on prend 50% des ressources de chaque ville (l'autre moitié reste en réserve).
    
    Args:
        player_cities: Liste des villes du joueur
        exclude_city_id: ID de la ville actuelle (à exclure)
    
    Returns:
        Dict des ressources transportables par type
    """
    transportable = {
        'wood': 0,
        'stone': 0,
        'iron': 0,
        'cereal': 0,
        'papyrus': 0
    }
    
    for city in player_cities:
        if city.get('id') == exclude_city_id:
            continue
        
        resources = city.get('resources', {})
        
        for res in transportable.keys():
            available = resources.get(res, 0)
            # Prendre 50% des ressources (garder 50% en réserve)
            transportable[res] += available * 0.5
    
    return transportable


def _get_production_rates(city: Dict) -> Dict:
    """
    Retourne les taux de production horaires RÉELS de la ville.
    
    Utilise GameLogic.calculate_total_production_rate() pour obtenir
    la production par seconde incluant tous les bonus (bâtiments, recherches).
    
    Returns:
        Dict {resource: production_per_hour}
    """
    import os
    from app.game_logic import GameLogic
    from app.data_manager import DataManager
    
    # Initialiser GameLogic pour accéder au calcul de production réel
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    dm = DataManager(base_dir)
    game_logic = GameLogic(dm)
    
    # Ressources à calculer
    resources = ['wood', 'stone', 'iron', 'cereal', 'papyrus']
    
    rates = {}
    for res in resources:
        # calculate_total_production_rate retourne production/seconde
        # Multiplier par 3600 pour avoir production/heure
        production_per_second = game_logic.calculate_total_production_rate(city, res)
        rates[res] = production_per_second * 3600
    
    return rates


# ============================================================
# HELPERS - BÂTIMENTS
# ============================================================

def _get_building_level(city: Dict, building_name: str) -> int:
    """Retourne le niveau actuel d'un bâtiment dans la ville."""
    for building in city.get('buildings', []):
        if building.get('name') == building_name:
            return building.get('level', 0)
    return 0


def _is_research_unlocked(player: Dict, research_id: str) -> bool:
    """Vérifie si une recherche est débloquée pour le joueur."""
    if not research_id:
        return True  # Pas de recherche requise
    
    # Essayer les deux clés possibles
    unlocked = player.get('unlocked_research', player.get('research_unlocked', []))
    return research_id in unlocked


def _get_building_required_research(building_name: str) -> str:
    """Retourne la recherche requise pour un bâtiment (ou None)."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        buildings_path = os.path.join(base_dir, 'data', 'buildings.json')
        
        with open(buildings_path, 'r', encoding='utf-8') as f:
            buildings_data = json.load(f)
        
        building_key_map = {
            'Hôtel de Ville': 'Hôtel de Ville',
            'Academy': 'Academy',
            'Entrepôt': 'Entrepôt',
            'Thermes': 'Thermes',
            'Windmill': 'Windmill',
            'Scierie': 'Scierie',
            'Centre de Ressources': 'Centre de Ressources',
            "Atelier d'Architecte": "Atelier d'Architecte"
        }
        
        building_key = building_key_map.get(building_name, building_name)
        building_info = buildings_data.get(building_key, {})
        return building_info.get('required_research')
        
    except Exception as e:
        print(f"⚠️ Erreur lecture recherche requise {building_name}: {e}")
        return None


def _get_building_upgrade_cost(city: Dict, building_name: str) -> Dict:
    """
    Retourne le coût pour upgrader un bâtiment au niveau suivant.
    
    Returns:
        Dict {resource: amount}
    """
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        buildings_path = os.path.join(base_dir, 'data', 'buildings.json')
        
        with open(buildings_path, 'r', encoding='utf-8') as f:
            buildings_data = json.load(f)
        
        current_level = _get_building_level(city, building_name)
        next_level = current_level + 1
        
        # Mapper nom français → nom clé JSON
        building_key_map = {
            'Hôtel de Ville': 'Hôtel de Ville',
            'Academy': 'Academy',
            'Entrepôt': 'Entrepôt',
            'Thermes': 'Thermes',
            'Windmill': 'Windmill',
            'Scierie': 'Scierie',
            'Centre de Ressources': 'Centre de Ressources',
            "Atelier d'Architecte": "Atelier d'Architecte"
        }
        
        building_key = building_key_map.get(building_name, building_name)
        building_info = buildings_data.get(building_key, {})
        levels = building_info.get('levels', [])
        
        for level_data in levels:
            if level_data.get('level') == next_level:
                return level_data.get('cost', {})
        
        return {}
        
    except Exception as e:
        print(f"⚠️ Erreur lecture coût bâtiment {building_name}: {e}")
        return {}


def _get_player_cities(player_id: str) -> List[Dict]:
    """Retourne la liste des villes d'un joueur."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        savegame_path = os.path.join(base_dir, 'gamedata', 'savegame.json')
        
        with open(savegame_path, 'r', encoding='utf-8') as f:
            savegame = json.load(f)
        
        cities = [c for c in savegame.get('cities', []) if c.get('owner_id') == player_id]
        return cities
        
    except Exception as e:
        print(f"⚠️ Erreur lecture villes joueur: {e}")
        return []


# ============================================================
# SAUVEGARDE/RÉCUPÉRATION DÉCISIONS
# ============================================================

def _get_saved_building_decision(player_id: str, city_id: str) -> Optional[Dict]:
    """
    Récupère une décision de construction sauvegardée.
    
    Returns:
        {
            'building': str,
            'tick': int,
            'wait_hours': float,
            'cost': dict
        }
        ou None si pas de décision
    """
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        state_path = os.path.join(base_dir, 'gamedata', 'ai_strategies_state.json')
        
        if not os.path.exists(state_path):
            return None
        
        with open(state_path, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        if player_id not in state:
            return None
        
        cities = state[player_id].get('cities', {})
        if city_id not in cities:
            return None
        
        building_decisions = cities[city_id].get('building_decisions', {})
        return building_decisions if building_decisions else None
        
    except Exception as e:
        print(f"⚠️ Erreur lecture décision sauvegardée: {e}")
        return None


def _save_building_decision(player_id: str, city_id: str, decision: Dict, current_tick: int):
    """Sauvegarde une décision de construction dans ai_strategies_state.json."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        state_path = os.path.join(base_dir, 'gamedata', 'ai_strategies_state.json')
        
        # Charger état existant
        if os.path.exists(state_path):
            with open(state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
        else:
            state = {}
        
        # Initialiser player si nécessaire
        if player_id not in state:
            state[player_id] = {}
        
        if 'cities' not in state[player_id]:
            state[player_id]['cities'] = {}
        
        if city_id not in state[player_id]['cities']:
            state[player_id]['cities'][city_id] = {}
        
        # Sauvegarder décision en format compact
        state[player_id]['cities'][city_id]['building_decisions'] = {
            'building': decision['building'],
            'tick': current_tick,
            'wait_hours': decision['wait_hours'],
            'cost': decision['cost']
        }
        
        # Écrire avec format personnalisé : building_decisions sur 1 ligne
        with open(state_path, 'w', encoding='utf-8') as f:
            json_str = json.dumps(state, indent=2, ensure_ascii=False)
            
            # Compacter building_decisions sur une seule ligne
            import re
            # Pattern pour trouver "building_decisions": { ... } sur plusieurs lignes
            pattern = r'"building_decisions":\s*\{[^}]*"building":[^}]*"tick":[^}]*"wait_hours":[^}]*"cost":\s*\{[^}]*\}\s*\}'
            
            def compact_building_decisions(match):
                # Extraire le contenu et le compacter
                content = match.group(0)
                # Supprimer tous les retours à la ligne et espaces multiples
                compacted = re.sub(r'\s+', ' ', content)
                compacted = re.sub(r'}\s*}', '}}', compacted)
                return compacted
            
            json_str = re.sub(pattern, compact_building_decisions, json_str, flags=re.DOTALL)
            
            f.write(json_str)
        
    except Exception as e:
        print(f"⚠️ Erreur sauvegarde décision: {e}")


def _clear_saved_decision(player_id: str, city_id: str):
    """Supprime une décision sauvegardée."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        state_path = os.path.join(base_dir, 'gamedata', 'ai_strategies_state.json')
        
        if not os.path.exists(state_path):
            return
        
        with open(state_path, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        if player_id in state and 'cities' in state[player_id]:
            if city_id in state[player_id]['cities']:
                if 'building_decisions' in state[player_id]['cities'][city_id]:
                    state[player_id]['cities'][city_id]['building_decisions'] = {}
        
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        
    except Exception as e:
        print(f"⚠️ Erreur suppression décision: {e}")


def _can_build_now(city: Dict, saved_decision: Dict) -> bool:
    """
    Vérifie si les ressources sont maintenant disponibles pour construire.
    
    Args:
        city: Données de la ville
        saved_decision: Décision sauvegardée avec 'cost'
    
    Returns:
        True si constructible maintenant
    """
    resources = city.get('resources', {})
    cost = saved_decision.get('cost', {})
    
    for res, amount in cost.items():
        if resources.get(res, 0) < amount:
            return False
    
    return True
