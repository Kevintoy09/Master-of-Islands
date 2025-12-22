"""
=================================================================
CITY_ROUTES.PY - Routes API pour la gestion des villes
=================================================================

RESPONSABILITÉS:
- État des villes (resources, population, bâtiments)
- Gestion de la population
- Réclamation de villes par les joueurs

ROUTES DISPONIBLES:
- GET /api/city/<id>/state         → État complet de la ville
- GET /api/city/<id>/population    → Info population  
- POST /api/city/claim             → Réclamer une ville
- GET /api/city/<id>               → Info ville depuis univers

ROUTES LEGACY (temporaires):
- POST /api/city/<id>/build        → Dans legacy_routes.py
- GET /api/city/<id>/buildings     → Dans legacy_routes.py

AVANT D'AJOUTER UNE ROUTE:
- Utiliser CityService pour la logique métier
- Valider les données avec les décorateurs
- Gérer les erreurs appropriées

DÉPENDANCES:
- CityService pour la logique métier
- DataManager, GameLogic, PopulationManager injectés
=================================================================
"""

from flask import Blueprint, request, jsonify
import os
import json
import time
from ..business.city_service import CityService
from ..business.player_resources_service import PlayerResourcesService
from ..core.decorators import handle_errors, validate_json
from ..core.exceptions import GameValidationError, CityNotFoundError

# Création du Blueprint
city_bp = Blueprint('city', __name__, url_prefix='/api/city')

# Services à injecter lors de l'initialisation
city_service: CityService = None
data_manager = None
game_logic = None
population_manager = None
session_tracker = None

@city_bp.route('/island/<island_id>/cities', methods=['GET'])
@handle_errors
def get_cities_for_island(island_id):
    """
    Retourne la liste des villes d'une île (non enrichies).
    Utilisez le tableau 'cities' de /api/universe pour obtenir owner et buildings.
    """
    BASE_DIR = data_manager.base_dir
    universe_path = os.path.join(BASE_DIR, 'data', 'universe.json')
    try:
        with open(universe_path, 'r', encoding='utf-8') as f:
            universe = json.load(f)
    except Exception as e:
        return jsonify({'error': f'Data not found: {str(e)}'}), 500

    cities = []
    for island in universe.get('islands', []):
        if str(island.get('id')) == str(island_id):
            for element in island.get('elements', []):
                if element.get('type') == 'city':
                    cities.append(element)
    return jsonify(cities)

def init_city_routes(cs: CityService, dm, gl, pm, st = None):
    """Initialise les routes avec les services"""
    global city_service, data_manager, game_logic, population_manager, session_tracker
    city_service = cs
    data_manager = dm
    game_logic = gl
    population_manager = pm
    session_tracker = st

@city_bp.route('/colonize', methods=['POST'])
@handle_errors
@validate_json('player_id', 'city_id')
def colonize_city():
    """
    Colonise une ville libre et l'attribue au joueur.
    Applique automatiquement la logique d'affectation des îles (max 4 joueurs par île).
    Enregistre également la faction du joueur basée sur la ressource de l'île.
    """
    data = request.get_json()
    player_id = data.get('player_id')
    requested_city_id = data.get('city_id')

    try:
        # Charger les données pour analyser la demande
        universe_data = data_manager.load_universe()
        if not universe_data:
            raise GameValidationError("Impossible de charger les données de l'univers")

        # Trouver l'île de la ville demandée
        requested_island = None
        requested_city = None
        for island in universe_data.get('islands', []):
            for element in island.get('elements', []):
                if element.get('type') == 'city' and element.get('id') == requested_city_id:
                    requested_island = island
                    requested_city = element
                    break
            if requested_island:
                break

        if not requested_island or not requested_city:
            raise GameValidationError("Ville introuvable")

        # Obtenir la ressource de base de l'île demandée
        base_resource = requested_island.get('base_resource')
        island_id = requested_island.get('id')

        # Appliquer la logique d'affectation automatique
        from ..business.island_assignment_service import IslandAssignmentService
        island_assignment_service = IslandAssignmentService(data_manager)
        
        # Vérifier si l'île demandée respecte la limite de 4 joueurs
        current_player_count = island_assignment_service.get_island_player_count(island_id)
        
        final_city_id = requested_city_id
        final_island_name = requested_island.get('name')
        assignment_message = None
        
        # Si l'île a déjà 4 joueurs ou plus, rediriger automatiquement
        if current_player_count >= 4:
            # Trouver la prochaine île disponible pour cette ressource
            suggested_island, suggested_city = island_assignment_service.suggest_city_for_player(base_resource)
            
            if suggested_island and suggested_city:
                final_city_id = suggested_city['id']
                final_island_name = suggested_island['name']
                assignment_message = f"Île {requested_island.get('name')} pleine ({current_player_count} joueurs). Redirection automatique vers l'île {final_island_name}."
            else:
                raise GameValidationError(f"Aucune île disponible pour la ressource {base_resource}")

        # Coloniser la ville (originale ou redirigée)
        city = city_service.claim_city(final_city_id, player_id)
        
        # Enregistrer la faction dans les données du joueur (seulement si c'est sa première ville)
        players_data = data_manager.load_players()
        player = next((p for p in players_data.get('players', []) if p.get('id') == player_id), None)
        if player and not player.get('faction'):
            player['faction'] = base_resource  # Stocker l'ID de la faction (ressource)
            data_manager.save_players(players_data)
        
        # Mettre à jour l'activité du joueur
        if session_tracker:
            session_tracker.update_activity(player_id)
        
        # Préparer la réponse
        response = {
            'success': True, 
            'city': city,
            'island_name': final_island_name,
            'faction': base_resource
        }
        
        if assignment_message:
            response['assignment_message'] = assignment_message
            response['redirected'] = True
            response['original_city_id'] = requested_city_id
            response['final_city_id'] = final_city_id
        else:
            response['redirected'] = False
            
        return jsonify(response)

    except GameValidationError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Erreur colonisation: {str(e)}'}), 500

@city_bp.route('/<city_id>', methods=['GET'])
@handle_errors
def get_city(city_id: str):
    """Récupère une ville depuis l'univers"""
    city = city_service.get_city_from_universe(city_id)
    if not city:
        return jsonify({'error': 'City not found'}), 404
    
    return jsonify(city)

@city_bp.route('/<city_id>/state', methods=['GET'])
@handle_errors
def get_city_state(city_id: str):
    """
    Récupère l'état détaillé d'une ville avec mise à jour de production.
    Route principale pour l'état des villes côté client.
    """
    # Charger directement depuis le SaveService en forçant le reload pour consommation temps réel
    from app.services.save_service import get_save_service
    save_service = get_save_service()
    savegame = save_service.get_savegame(force_reload=True)
    
    # Mettre à jour la production de ressources - DÉSACTIVÉ: utilise ManualTickService maintenant
    # game_logic.update_resource_production_in_memory(savegame)
    
    # 🕒 SYSTÈME CENTRALISÉ : Production d'or maintenant gérée automatiquement
    # player_resources_service = PlayerResourcesService(data_manager)
    # for city in savegame.get('cities', []):
    #     owner = city.get('owner')
    #     if owner:
    #         player_resources_service.update_gold_production(owner)  # DÉSACTIVÉ
    
    # Mettre à jour les constructions terminées (en mémoire pour éviter les recharges)
    construction_changes = game_logic.update_construction_statuses_in_memory(savegame)
    
    # Sauvegarder seulement s'il y a eu des changements
    if construction_changes:
        save_service.save_savegame(savegame, force=True, priority="critical")
    
    # Mettre à jour la population de toutes les villes - DÉSACTIVÉ: utilise ManualTickService maintenant
    # population_manager.update_all_cities_population(savegame, elapsed_seconds=None)
    
    # Recalculer la population libre pour toutes les villes
    for city in savegame.get('cities', []):
        city['resources']['population_free'] = game_logic.calculate_actual_free_population(city)
    
    # Les effects sont calculés dynamiquement depuis buildings.json, pas besoin de les ajouter
    
    # Sauvegarder à chaque appel (mode développement pour analyse)
    current_time = int(time.time())
    last_save = getattr(get_city_state, 'last_save', 0)
    
    if current_time - last_save >= 0:  # Sauvegarde à chaque appel (mode développement)
        if save_service.save_savegame(savegame, force=True, priority="normal"):
            get_city_state.last_save = current_time
    
    city = next((c for c in savegame.get('cities', []) if c['id'] == city_id), None)
    if city:
        # Ajouter les limites de stockage
        storage_limits = game_logic.get_city_storage_limits(city)
        city_response = city.copy()
        city_response['storage_limits'] = storage_limits
        return jsonify(city_response)
    else:
        return jsonify({'error': 'City not found'}), 404
    
# Route /build supprimée - utilise celle de legacy_routes.py pour compatibilité
# Route /buildings supprimée - utilise celle de legacy_routes.py pour compatibilité

# Cache simple pour éviter les appels répétitifs
_population_cache = {}
_cache_duration = 1  # Cache de 1 seconde

def get_cached_population(city_id):
    """Retourne la population depuis le cache si disponible"""
    current_time = time.time()
    
    if city_id in _population_cache:
        cached_data, cache_time = _population_cache[city_id]
        if current_time - cache_time < _cache_duration:
            return cached_data
    
    return None

def cache_population(city_id, data):
    """Met en cache les données de population"""
    _population_cache[city_id] = (data, time.time())

@city_bp.route('/<city_id>/population', methods=['GET'])
@handle_errors
def get_city_population(city_id):
    """
    Retourne les informations de population d'une ville.
    Optimisé avec cache pour éviter les appels excessifs.
    """
    from ..transition_utils import load_savegame_transition
    
    # Vérifier le cache d'abord
    cached_data = get_cached_population(city_id)
    if cached_data:
        return jsonify(cached_data)
    
    try:
        savegame = load_savegame_transition()
        if not savegame:
            raise GameValidationError('Impossible de charger les données de jeu')
    except Exception as e:
        raise GameValidationError(f'Erreur de chargement des données: {str(e)}')
    
    # Mettre à jour la population - DÉSACTIVÉ: utilise ManualTickService maintenant
    # population_manager.update_all_cities_population(savegame, elapsed_seconds=None)
    
    city = next((c for c in savegame.get('cities', []) if c['id'] == city_id), None)
    if not city:
        raise CityNotFoundError(f'City {city_id} not found')
    
    # Recalculer la population libre
    city['resources']['population_free'] = game_logic.calculate_actual_free_population(city)
    
    # Sauvegarder à chaque appel (mode développement pour analyse)
    current_time = int(time.time())
    last_save = getattr(get_city_population, 'last_save', 0)
    
    if current_time - last_save >= 0:  # Sauvegarde à chaque appel (mode développement)
        if data_manager.save_savegame(savegame):
            get_city_population.last_save = current_time
    
    # Retourner les informations de population - RECONSTRUCTION MANUELLE
    resources = city.get('resources', {})
    workers_assigned = city.get('workers_assigned', {})
    total_workers = sum(workers_assigned.values())
    
    # Recalculer les satisfaction_factors en temps réel pour avoir les bonus recherche à jour
    from app.managers.population_manager import PopulationManager
    pop_manager = PopulationManager(os.path.join(data_manager.base_dir, 'data'))
    
    # Calculer la chaîne complète: food_capacities → population_food_status → cereal_consumption → satisfaction_factors
    food_capacities = pop_manager.calculate_food_capacities(city)
    population_food_status = pop_manager.calculate_population_food_status(city, food_capacities)
    cereal_consumption = pop_manager.calculate_cereal_consumption(city, population_food_status, dt=1.0)
    satisfaction_factors = pop_manager.calculate_satisfaction_factors(city, cereal_consumption)
    
    # Mettre à jour satisfaction_details avec les factors recalculés
    satisfaction_details = city.get('satisfaction_details', {})
    if satisfaction_factors:
        satisfaction_details['bonus'] = satisfaction_factors.get('bonus', {})
        satisfaction_details['malus'] = satisfaction_factors.get('malus', {})
    
    # Calculer la croissance de base depuis l'Hôtel de Ville (pop_manager déjà instancié ci-dessus)
    base_growth_per_hour = pop_manager.get_population_growth_from_town_hall(city)
    max_capacity = pop_manager.calculate_population_limit(city)
    
    # Si pas de satisfaction_details (ville jamais tickée ou sans bâtiment), utiliser des valeurs par défaut
    if not satisfaction_details:
        satisfaction_details = {
            'base': 50,
            'bonus': {},
            'malus': {},
            'total': 50,
            'growth_rate': 0,
            'real_growth_per_hour': 0,
            'food_capacities': {'townhall': 0, 'windmill': 0, 'total': 0},
            'population_food_status': {'total': resources.get('population_total', 0), 'fed_by_townhall': 0, 'fed_by_windmill': 0, 'starving': resources.get('population_total', 0)},
            'cereal_consumption': {'multiplier': 1, 'max_multiplier': 1, 'total_needed': 0.0, 'base_rate_per_hour': 0.1}
        }
    
    # Construire l'objet info avec toutes les données nécessaires
    population_info = {
        'current_population': resources.get('population_total', 0),
        'max_capacity': max_capacity,
        'population_free': resources.get('population_free', 0),
        'workers_assigned': total_workers,
        'base_growth_per_hour': base_growth_per_hour,  # Croissance de base de l'Hôtel de Ville
        'growth_per_hour': satisfaction_details.get('real_growth_per_hour', 0),  # Directement depuis satisfaction_details
        'growth_per_second': satisfaction_details.get('growth_rate', 0) / 10,  # Croissance réelle par seconde (1 tick = 10 sec)
        'real_growth_per_hour': satisfaction_details.get('real_growth_per_hour', 0),  # Directement depuis satisfaction_details
        'time_multiplier': 1,
        'hygiene_percent': city.get('hygiene_percent', 100),
        'has_plague': city.get('has_plague', False),
        'satisfaction': city.get('satisfaction', 50),
        # Données pour SatisfactionPopup
        'satisfaction_factors': {
            'bonus': satisfaction_details.get('bonus', {}),
            'malus': satisfaction_details.get('malus', {})
        },
        'satisfaction_details': satisfaction_details,
        'food_capacity': satisfaction_details.get('food_capacities', {}).get('total', 0),
        'windmill_food_supply': satisfaction_details.get('food_capacities', {}).get('windmill', 0),
        'cereal_multiplier': satisfaction_details.get('cereal_consumption', {}).get('multiplier', 1.0),
        'cereal_needed': satisfaction_details.get('cereal_consumption', {}).get('total_needed', 0.0)
    }
    
    response_data = {
        'population_total': resources.get('population_total', 0),
        'population_free': resources.get('population_free', 0),
        'max_capacity': max_capacity,
        'workers_assigned': workers_assigned,
        'growth_rate': satisfaction_details.get('real_growth_per_hour', 0),
        'satisfaction': city.get('satisfaction', 50),
        # Garder aussi l'ancien format pour compatibilité
        'population': resources.get('population_total', 0),
        'info': population_info,
        'last_update': city.get('last_population_update', int(time.time()))
    }
    
    # Mettre en cache pour éviter les appels répétitifs
    cache_population(city_id, response_data)
    
    return jsonify(response_data)

@city_bp.route('/<city_id>/cure-plague', methods=['POST'])
@handle_errors
def cure_city_plague(city_id):
    """
    Soigne la peste dans une ville.
    """
    from ..transition_utils import load_savegame_transition, save_savegame_transition
    
    try:
        savegame = load_savegame_transition()
        if not savegame:
            raise GameValidationError('Impossible de charger les données de jeu')
    except Exception as e:
        raise GameValidationError(f'Erreur de chargement des données: {str(e)}')
    
    city = next((c for c in savegame.get('cities', []) if c['id'] == city_id), None)
    if not city:        raise CityNotFoundError(f'City {city_id} not found')
    
    # Vérifier si la ville a la peste
    has_plague = city.get('has_plague', False)
    if not has_plague:
        return jsonify({'success': False, 'message': 'La ville n\'a pas la peste'}), 200
    
    # Vérifier les conditions : hygiène >= 100% et coût en or (2x population)
    population = city['resources'].get('population_total', 0)
    hygiene = city.get('hygiene_percent', 0)
    cost = 2 * population
    
    if hygiene < 100:
        return jsonify({'success': False, 'message': 'Hygiène insuffisante (minimum 100%)'}), 200
    
    # Charger l'or du joueur depuis players.json
    players_data = data_manager.load_players()
    
    player_id = city.get('owner')
    player = next((p for p in players_data.get('players', []) if p['id'] == player_id), None)
    if not player:
        raise GameValidationError(f'Player {player_id} not found')
    
    player_gold = player.get('gold', 0)
    
    if player_gold < cost:
        return jsonify({'success': False, 'message': f'Or insuffisant ({cost} requis, vous avez {player_gold})'}), 200
    
    # Soigner la peste
    from app.managers.population_manager import PopulationManager
    pop_manager = PopulationManager(os.path.join(BASE_DIR, 'data'))
    pop_manager.cure_plague(city)
    
    # Déduire l'or du joueur
    player['gold'] -= cost
    
    # Sauvegarder players.json
    with open(players_path, 'w', encoding='utf-8') as f:
        json.dump(players_data, f, indent=2, ensure_ascii=False)
    
    success = True
    
    # Sauvegarder (forcer la sauvegarde pour les actions critiques)
    save_result = data_manager.save_savegame(savegame, force_save=True)
    
    if success and save_result:        return jsonify({'success': True, 'message': 'Peste soignée avec succès'})
    else:        raise GameValidationError('Erreur lors de la sauvegarde')

@city_bp.route('/<city_id>/build', methods=['POST'])
@handle_errors 
@validate_json('slot_id', 'building')
def build_building(city_id):
    """Construction et développement de bâtiments"""
    from ..transition_utils import load_savegame_transition, save_savegame_transition
    
    BASE_DIR = data_manager.base_dir
    buildings_path = os.path.join(BASE_DIR, 'data', 'buildings.json')
    
    data = request.get_json()
    slot_id = data.get('slot_id')
    building_name = data.get('building')
    building_name = data.get('building')
        
    # Charger savegame via le système de transition
    try:
        savegame = load_savegame_transition()
        if not savegame:
            raise GameValidationError('Impossible de charger les données de jeu')
    except Exception as e:
        raise GameValidationError(f'Erreur de chargement des données: {str(e)}')
        
    # Charger buildings.json
    try:
        with open(buildings_path, 'r', encoding='utf-8') as f:
            buildings_data = json.load(f)
    except Exception as e:
        raise GameValidationError(f'buildings.json introuvable: {str(e)}')
        
    # Trouver la ville
    city = next((c for c in savegame.get('cities', []) if c['id'] == city_id), None)
    if not city:
        raise CityNotFoundError(f'Ville {city_id} introuvable')
        
    # Vérifier que le bâtiment existe dans la base de données
    if building_name not in buildings_data:
        raise GameValidationError('Bâtiment inconnu')
        
    building_info = buildings_data[building_name]
    
    # Initialiser les bâtiments si nécessaire
    if 'buildings' not in city:
        city['buildings'] = []
        
    # Chercher si le bâtiment existe déjà sur ce slot
    existing_building = next((b for b in city['buildings'] if b.get('slot_id') == slot_id), None)
    is_upgrade = existing_building is not None
    
    if is_upgrade:
        # DÉVELOPPEMENT - Améliorer un bâtiment existant
        current_level = existing_building.get('level', 1)
        target_level = current_level + 1
        
        # Vérifier que le bâtiment correspond
        if existing_building.get('name') != building_name:
            raise GameValidationError('Le slot contient un autre bâtiment')
            
        # Vérifier que le bâtiment n'est pas en construction
        if existing_building.get('status') == 'En construction':
            raise GameValidationError('Le bâtiment est en cours de construction')
            
        # Vérifier que le niveau suivant existe
        if target_level > len(building_info.get('levels', [])):
            raise GameValidationError('Niveau maximum déjà atteint')
            
        level_data = building_info.get('levels', [])[target_level - 1]
    else:
        # CONSTRUCTION - Nouveau bâtiment niveau 1
        target_level = 1
        level_data = building_info.get('levels', [{}])[0]
    
    # VALIDATION DES RECHERCHES REQUISES (seulement pour nouveaux bâtiments)
    if not is_upgrade:
        required_research = building_info.get('required_research')
        if required_research:
            # Charger les données des joueurs
            players_path = os.path.join(BASE_DIR, 'gamedata', 'players.json')
            try:
                with open(players_path, 'r', encoding='utf-8') as f:
                    players_data = json.load(f)
            except Exception as e:
                raise GameValidationError(f'players.json introuvable: {str(e)}')
            
            # Trouver le joueur propriétaire de la ville
            player_id = city.get('owner')
            if not player_id:
                raise GameValidationError('Impossible de déterminer le propriétaire de la ville')
            
            player = None
            for p in players_data.get('players', []):
                if p.get('id') == player_id:
                    player = p
                    break
            
            if not player:
                raise GameValidationError('Joueur introuvable')
            
            # Vérifier les recherches débloquées
            unlocked_research = player.get('unlocked_research', [])
            if required_research not in unlocked_research:
                return jsonify({
                    'error': '🔬 Recherche à débloquer !',
                    'type': 'research_required'
                }), 400
    
    # VALIDATION DU NOMBRE MAXIMUM D'INSTANCES (seulement pour nouveaux bâtiments)
    if not is_upgrade:
        max_instances = building_info.get('max_instances', 999)  # Par défaut, pas de limite
        current_instances = len([b for b in city['buildings'] 
                               if b.get('name') == building_name 
                               and b.get('status') != 'En démolition'])
        
        if current_instances >= max_instances:
            return jsonify({
                'error': f'Limite atteinte ! Maximum {max_instances} {building_name}(s) par ville.',
                'type': 'max_instances_reached',
                'current': current_instances,
                'max': max_instances
            }), 400
    
    base_cost = level_data.get('cost', {})
    base_construction_time = level_data.get('construction_time', 30)
    
    # Appliquer les bonus de l'Atelier d'Architecte
    actual_cost = game_logic.apply_architect_bonuses_to_building_cost(base_cost, city)
    actual_construction_time = game_logic.apply_architect_bonuses_to_building_time(base_construction_time, city)
    
    # Vérifier les ressources (avec coût réduit)
    city_resources = city.get('resources', {})
    missing = {}
    for res, val in actual_cost.items():
        if city_resources.get(res, 0) < val:
            missing[res] = val - city_resources.get(res, 0)
    
    if missing:
        return jsonify({
            'error': '💰 Ressources insuffisantes !',
            'type': 'insufficient_resources',
            'required': actual_cost,
            'missing': missing
        }), 400
        
    # Déduire les ressources (avec coût réduit)
    for res, val in actual_cost.items():
        city_resources[res] = city_resources.get(res, 0) - val
    city['resources'] = city_resources
    
    # Lancer le timer de construction/développement (avec temps réduit)
    construction_end = int(time.time()) + actual_construction_time
    
    if is_upgrade:
        # DÉVELOPPEMENT - Mettre à jour le bâtiment existant
        # Sauvegarder le niveau actuel pour maintenir les effets pendant le développement
        current_level = existing_building.get('level', 1)
        existing_building.update({
            'level': target_level,
            'previous_level': current_level,  # Nouveau: sauvegarder le niveau précédent
            'construction_end': construction_end,
            'started_at': int(time.time()),
            'duration': actual_construction_time,
            'status': 'En construction'
        })
        print(f"🔄 Bâtiment en développement: {existing_building}")
        action_message = f'{building_name} niveau {target_level} en développement sur le slot {slot_id}.'
    else:
        # CONSTRUCTION - Ajouter un nouveau bâtiment
        new_building = {
            'slot_id': slot_id,
            'name': building_name,
            'level': target_level,
            'construction_end': construction_end,
            'started_at': int(time.time()),
            'duration': actual_construction_time,
            'status': 'En construction'
        }
        city['buildings'].append(new_building)
        action_message = f'{building_name} niveau {target_level} en construction sur le slot {slot_id}.'
    
    # Sauvegarder via le système de transition
    try:
        success = save_savegame_transition(savegame, force=True)
        if not success:
            raise GameValidationError('Échec de la sauvegarde')
    except Exception as e:
        raise GameValidationError(f'Erreur lors de la sauvegarde: {str(e)}')
    
    # Mettre à jour l'activité du joueur
    owner = city.get('owner')
    if owner and session_tracker:
        session_tracker.update_activity(owner)
        
    return jsonify({
        'success': True, 
        'message': action_message,
        'construction_end': construction_end,
        'actual_cost': actual_cost,
        'actual_construction_time': actual_construction_time,
        'target_level': target_level,
        'is_upgrade': is_upgrade,
        'architect_bonuses': game_logic.calculate_architect_bonuses(city)
    })

@city_bp.route('/<city_id>/destroy', methods=['POST'])
@handle_errors
def destroy_or_downgrade_building(city_id):
    """Détruit ou rétrograde un bâtiment : niveau > 1 → niveau - 1, niveau 1 → suppression"""
    from ..transition_utils import load_savegame_transition, save_savegame_transition
    
    try:
        # Validation JSON manuelle
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données JSON requises'}), 400
            
        slot_id = data.get('slot_id')
        if not slot_id:
            return jsonify({'error': 'Champ slot_id requis'}), 400
            
        # Charger savegame via SaveService
        savegame = load_savegame_transition()
        if not savegame:
            raise GameValidationError('Impossible de charger les données de jeu')
            
    except Exception as e:
        if "JSON" in str(e):
            return jsonify({'error': 'JSON invalide'}), 400
        raise GameValidationError(f'Erreur de chargement: {str(e)}')
        
    # Trouver la ville
    city = next((c for c in savegame.get('cities', []) if c['id'] == city_id), None)
    if not city:
        raise CityNotFoundError(f'Ville {city_id} introuvable')
        
    # Trouver le bâtiment sur ce slot
    buildings = city.get('buildings', [])
    building = next((b for b in buildings if b.get('slot_id') == slot_id), None)
    
    if not building:
        raise GameValidationError('Aucun bâtiment trouvé sur ce slot')
        
    # Vérifier qu'il n'est pas en construction
    if building.get('status') == 'En construction':
        raise GameValidationError('Impossible de détruire un bâtiment en construction')
        
    building_name = building.get('name')
    current_level = building.get('level', 1)
    new_level = None  # Initialiser à None par défaut
    
    # Mémoriser si c'est un entrepôt pour vérifier les limites de stockage après
    is_warehouse = building_name == 'Entrepôt'
    
    if current_level > 1:
        # RÉTROGRADATION : Réduire le niveau de 1
        new_level = current_level - 1
        building['level'] = new_level
        
        # Nettoyer les champs de construction s'ils existent
        building.pop('construction_end', None)
        building.pop('started_at', None)
        building.pop('duration', None)
        building['status'] = 'Construit'
        
        action_message = f'{building_name} rétrogradé du niveau {current_level} au niveau {new_level}'
        action_type = 'downgrade'
        result_building = building
    else:
        # DESTRUCTION : Supprimer complètement le bâtiment
        buildings.remove(building)
        
        # Libérer les ouvriers assignés aux sites de ressources
        workers_assigned = city.get('workers_assigned', {})
        freed_workers = 0
        
        # Calculer les ouvriers à libérer (pour tous les sites)
        for site_type, workers in list(workers_assigned.items()):
            if workers > 0:
                freed_workers += workers
                
        # Recalculer la population libre avec les ouvriers libérés
        city['resources']['population_free'] = game_logic.calculate_actual_free_population(city)
        
        action_message = f'{building_name} niveau {current_level} détruit définitivement'
        if freed_workers > 0:
            action_message += f' ({freed_workers} ouvriers libérés)'
        action_type = 'destroy'
        result_building = None
    
    # Si c'est un entrepôt, vérifier et perdre les ressources excédentaires
    if is_warehouse:
        storage_limits = game_logic.get_city_storage_limits(city)
        resources_lost = {}
        
        for resource, limit in storage_limits.items():
            current = city.get('resources', {}).get(resource, 0)
            if current > limit:
                overflow = current - limit
                city['resources'][resource] = limit
                resources_lost[resource] = overflow
                print(f"⚠️ Entrepôt {'détruit' if action_type == 'destroy' else 'rétrogradé'}: {overflow} {resource} perdu")
        
        if resources_lost:
            total_lost = sum(resources_lost.values())
            action_message += f" - {len(resources_lost)} ressources excédentaires perdues (total: {int(total_lost)})"
        
    # Sauvegarder avec le SaveService (force car c'est une action critique)
    success = save_savegame_transition(savegame, force=True)
    if not success:
        raise GameValidationError('Erreur lors de la sauvegarde')
        
    return jsonify({
        'success': True,
        'message': action_message,
        'action_type': action_type,
        'slot_id': slot_id,
        'building': result_building,
        'new_level': new_level if action_type == 'downgrade' else None
    })

@city_bp.route('/<city_id>/buildings', methods=['GET'])
@handle_errors
def get_buildings_for_slot(city_id):
    """Liste des bâtiments disponibles pour construction avec coûts et bonus architecte"""
    BASE_DIR = data_manager.base_dir
    buildings_path = os.path.join(BASE_DIR, 'data', 'buildings.json')
    savegame_path = os.path.join(BASE_DIR, 'gamedata', 'savegame.json')
    players_path = os.path.join(BASE_DIR, 'gamedata', 'players.json')
    
    # Récupérer le type de slot depuis les paramètres de requête
    slot_type = request.args.get('slot_type', 'general')
    
    try:
        with open(buildings_path, 'r', encoding='utf-8') as f:
            buildings_data = json.load(f)
    except Exception as e:
        raise GameValidationError(f'buildings.json introuvable: {str(e)}')
    
    # ⚡ OPTIMISATION : Charger le savegame pour calculer les bonus architecte
    try:
        with open(savegame_path, 'r', encoding='utf-8') as f:
            savegame = json.load(f)
        city = next((c for c in savegame.get('cities', []) if c['id'] == city_id), None)
    except:
        city = None
    
    # Charger les données du joueur pour vérifier les recherches
    player = None
    if city:
        try:
            with open(players_path, 'r', encoding='utf-8') as f:
                players_data = json.load(f)
            player_id = city.get('owner')
            for p in players_data.get('players', []):
                if p.get('id') == player_id:
                    player = p
                    break
        except:
            pass
        
    # Retourner la liste des bâtiments disponibles filtré par catégorie
    buildings_list = []
    building_costs = {}
    
    for name, b in buildings_data.items():
        building_category = b.get('category', 'general')
        
        # Filtrer selon le type de slot
        if building_category == slot_type:
            level1 = b.get('levels', [{}])[0]
            base_cost = level1.get('cost', {})
            base_time = level1.get('construction_time', 30)
            
            # Vérifier les prérequis de recherche
            required_research = b.get('required_research')
            has_research = True
            if required_research and player:
                unlocked_research = player.get('unlocked_research', [])
                has_research = required_research in unlocked_research
            
            # Vérifier le nombre maximum d'instances
            max_instances = b.get('max_instances', 999)
            current_instances = 0
            is_limit_reached = False
            if city:
                current_instances = len([bldg for bldg in city.get('buildings', []) 
                                       if bldg.get('name') == name 
                                       and bldg.get('status') != 'En démolition'])
                is_limit_reached = current_instances >= max_instances
            
            # Calculer les coûts avec bonus architecte si la ville existe
            if city:
                actual_cost = game_logic.apply_architect_bonuses_to_building_cost(base_cost, city)
                actual_time = game_logic.apply_architect_bonuses_to_building_time(base_time, city)
                
                building_costs[name] = {
                    'base_cost': base_cost,
                    'actual_cost': actual_cost,
                    'base_construction_time': base_time,
                    'actual_construction_time': actual_time,
                    'savings': {res: base_cost.get(res, 0) - actual_cost.get(res, 0) for res in base_cost},
                    'time_saved': base_time - actual_time
                }
            
            buildings_list.append({
                'name': name,
                'description': b.get('description', ''),
                'image': b.get('image', ''),
                'category': building_category,
                'required_research': required_research,
                'has_research': has_research,
                'max_instances': max_instances,
                'current_instances': current_instances,
                'is_limit_reached': is_limit_reached,
                'can_build': has_research and not is_limit_reached,
                'levels': b.get('levels', [])
            })
    
    return jsonify({
        'buildings': buildings_list,
        'building_costs': building_costs  # Inclus directement dans la réponse
    })

@city_bp.route('/<city_id>/building-costs', methods=['GET'])
@handle_errors
def get_building_costs_with_bonuses(city_id):
    """Retourne les coûts et temps de construction avec bonus de l'Atelier d'Architecte"""
    BASE_DIR = data_manager.base_dir
    buildings_path = os.path.join(BASE_DIR, 'data', 'buildings.json')
    savegame_path = os.path.join(BASE_DIR, 'gamedata', 'savegame.json')
    
    # Charger buildings.json
    try:
        with open(buildings_path, 'r', encoding='utf-8') as f:
            buildings_data = json.load(f)
    except Exception as e:
        raise GameValidationError(f'buildings.json introuvable: {str(e)}')
        
    # Charger savegame
    try:
        with open(savegame_path, 'r', encoding='utf-8') as f:
            savegame = json.load(f)
    except Exception as e:
        raise GameValidationError(f'savegame.json introuvable: {str(e)}')
        
    # Trouver la ville
    city = next((c for c in savegame.get('cities', []) if c['id'] == city_id), None)
    if not city:
        raise CityNotFoundError(f'Ville {city_id} introuvable')
        
    # Calculer les bonus de l'Atelier d'Architecte
    architect_bonuses = game_logic.calculate_architect_bonuses(city)
    
    # Calculer les coûts avec bonus pour tous les bâtiments
    building_costs = {}
    for building_name, building_info in buildings_data.items():
        level1 = building_info.get('levels', [{}])[0]
        base_cost = level1.get('cost', {})
        base_time = level1.get('construction_time', 30)
        
        actual_cost = game_logic.apply_architect_bonuses_to_building_cost(base_cost, city)
        actual_time = game_logic.apply_architect_bonuses_to_building_time(base_time, city)
        
        building_costs[building_name] = {
            'base_cost': base_cost,
            'actual_cost': actual_cost,
            'base_construction_time': base_time,
            'actual_construction_time': actual_time,
            'savings': {res: base_cost.get(res, 0) - actual_cost.get(res, 0) for res in base_cost},
            'time_saved': base_time - actual_time
        }
        
    return jsonify({
        'buildings': building_costs,
        'architect_bonuses': architect_bonuses
    })

@city_bp.route('/<city_id>/architect-bonuses', methods=['GET'])
@handle_errors
def get_architect_bonuses(city_id):
    """Retourne les bonus actuels de l'Atelier d'Architecte"""
    BASE_DIR = data_manager.base_dir
    savegame_path = os.path.join(BASE_DIR, 'gamedata', 'savegame.json')
    
    # Charger savegame
    try:
        with open(savegame_path, 'r', encoding='utf-8') as f:
            savegame = json.load(f)
    except Exception as e:
        raise GameValidationError(f'savegame.json introuvable: {str(e)}')
        
    # Trouver la ville
    city = next((c for c in savegame.get('cities', []) if c['id'] == city_id), None)
    if not city:
        raise CityNotFoundError(f'Ville {city_id} introuvable')
        
    # Calculer les bonus de l'Atelier d'Architecte
    bonuses = game_logic.calculate_architect_bonuses(city)
    
    return jsonify(bonuses)

@city_bp.route('/<city_id>/finish-construction', methods=['POST'])
@handle_errors
@validate_json('slot_id')
def finish_construction_instantly(city_id):
    """Termine instantanément la construction d'un bâtiment (nécessite la recherche Plan de Construction)"""
    BASE_DIR = data_manager.base_dir
    savegame_path = os.path.join(BASE_DIR, 'gamedata', 'savegame.json')
    players_path = os.path.join(BASE_DIR, 'gamedata', 'players.json')
    
    data = request.get_json()
    slot_id = data.get('slot_id')
        
    # Charger savegame et players
    try:
        with open(savegame_path, 'r', encoding='utf-8') as f:
            savegame = json.load(f)
        with open(players_path, 'r', encoding='utf-8') as f:
            players_data = json.load(f)
    except Exception as e:
        raise GameValidationError(f'Fichiers de données introuvables: {str(e)}')
        
    # Trouver la ville
    city = next((c for c in savegame.get('cities', []) if c['id'] == city_id), None)
    if not city:
        raise CityNotFoundError(f'Ville {city_id} introuvable')
        
    # Trouver le joueur propriétaire
    player_id = city.get('owner')
    if not player_id:
        raise GameValidationError('Impossible de déterminer le propriétaire de la ville')
        
    player = next((p for p in players_data.get('players', []) if p.get('id') == player_id), None)
    if not player:
        raise GameValidationError('Joueur introuvable')
        
    # Vérifier la recherche Sablier
    unlocked_research = player.get('unlocked_research', [])
    if 'sablier' not in unlocked_research:
        return jsonify({'error': 'Recherche "Sablier" requise'}), 403
    
    # Récupérer le seuil depuis research.json
    research_path = os.path.join(BASE_DIR, 'data', 'research.json')
    instant_finish_threshold = 30  # Valeur par défaut
    try:
        with open(research_path, 'r', encoding='utf-8') as f:
            research_data = json.load(f)
            sablier = next((r for r in research_data.get('researches', []) if r.get('id') == 'sablier'), None)
            if sablier and 'effect' in sablier:
                instant_finish_threshold = sablier['effect'].get('instant_finish_threshold', 30)
    except Exception as e:
        print(f"[WARN] Impossible de charger le seuil depuis research.json: {e}")
        
    # Trouver le bâtiment en construction
    building = next((b for b in city.get('buildings', []) if b.get('slot_id') == slot_id), None)
    if not building:
        raise GameValidationError('Bâtiment introuvable sur ce slot')
        
    # Vérifier qu'il est en construction
    if building.get('status') != 'En construction':
        raise GameValidationError('Le bâtiment n\'est pas en construction')
        
    # Vérifier le seuil dynamique
    now = int(time.time())
    construction_end = building.get('construction_end', 0)
    time_remaining = construction_end - now
    
    if time_remaining > instant_finish_threshold:
        return jsonify({
            'error': f'Il reste {time_remaining} secondes. La finition instantanée n\'est possible que dans les {instant_finish_threshold} dernières secondes.'
        }), 400
        
    # Vérifier si c'est un upgrade ou une construction
    is_upgrade = 'previous_level' in building
    
    # Terminer la construction
    building['status'] = 'Terminé'
    # Supprimer construction_end pour que le timer disparaisse
    if 'construction_end' in building:
        del building['construction_end']
    building.pop('started_at', None)
    building.pop('duration', None)
    building.pop('previous_level', None)
    
    # Mettre à jour la quête de construction
    try:
        from app.services.quest_service import quest_service
        username = player.get('username')
        if username:
            building_name = building.get('name')
            quest_service.update_construction_quest(username, building_name=building_name, is_upgrade=is_upgrade)
    except Exception:
        pass  # Silent fail
    
    # Sauvegarder
    try:
        tmp_path = savegame_path + ".tmp"
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(savegame, f, ensure_ascii=False, indent=2)
        with open(tmp_path, 'r', encoding='utf-8') as f:
            json.load(f)  # Vérification
        os.replace(tmp_path, savegame_path)
    except Exception as e:
        raise GameValidationError(f'Erreur lors de la sauvegarde: {str(e)}')
        
    return jsonify({
        'success': True,
        'message': f'Construction de {building.get("name")} terminée instantanément !',
        'building': building
    })

# Route legacy avec préfixe spécial pour compatibilité frontend
legacy_city_bp = Blueprint('legacy_city', __name__)

@legacy_city_bp.route('/api/city-state/<city_id>', methods=['GET'])
@handle_errors
def get_city_state_legacy(city_id):
    """
    Route legacy /api/city-state/<city_id> - État complet de la ville avec mise à jour
    Route critique pour l'affichage des villes côté client
    """
    # Charger les données une seule fois avec data_manager pour cohérence
    savegame = data_manager.load_savegame()
    if not savegame:
        raise GameValidationError('Savegame not found')
    
    # Mettre à jour la production de ressources - DÉSACTIVÉ: utilise ManualTickService maintenant
    # game_logic.update_resource_production_in_memory(savegame)
    
    # 🕒 SYSTÈME CENTRALISÉ : Production d'or maintenant gérée automatiquement
    # player_resources_service = PlayerResourcesService(data_manager)
    # for city in savegame.get('cities', []):
    #     owner = city.get('owner')
    #     if owner:
    #         player_resources_service.update_gold_production(owner)  # DÉSACTIVÉ
    
    # Mettre à jour les constructions terminées - RÉACTIVÉ pour finalisation automatique
    construction_changes = game_logic.update_construction_statuses_in_memory(savegame)
    
    # CONSOMMATION TEMPS RÉEL : Mettre à jour la population - DÉSACTIVÉ: utilise ManualTickService maintenant
    # population_manager.update_all_cities_population(savegame, elapsed_seconds=None)
    
    # Recalculer la population libre pour toutes les villes
    for city in savegame.get('cities', []):
        city['resources']['population_free'] = game_logic.calculate_actual_free_population(city)
    
    # Les effects sont calculés dynamiquement depuis buildings.json, pas besoin de les ajouter
    
    # Sauvegarder à chaque appel (mode développement pour analyse)
    current_time = int(time.time())
    last_save = getattr(get_city_state_legacy, 'last_save', 0)
    
    if current_time - last_save >= 0:  # Sauvegarde à chaque appel (mode développement)
        if data_manager.save_savegame(savegame):
            get_city_state_legacy.last_save = current_time
    
    city = next((c for c in savegame.get('cities', []) if c['id'] == city_id), None)
    if city:
        # Ajouter les limites de stockage
        storage_limits = game_logic.get_city_storage_limits(city)
        city_response = city.copy()
        city_response['storage_limits'] = storage_limits
        return jsonify(city_response)
    
    raise CityNotFoundError(f'City {city_id} not found')

@city_bp.route('/<city_id>/production/<resource>', methods=['GET'])
@handle_errors
def get_resource_production_details(city_id, resource):
    """Récupère les détails de production d'une ressource spécifique"""
    try:
        # Charger les données de sauvegarde
        savegame_data = data_manager.load_savegame()
        if not savegame_data:
            raise GameValidationError('Impossible de charger les données')
        
        # Trouver la ville
        city = None
        for c in savegame_data.get('cities', []):
            if c.get('id') == city_id:
                city = c
                break
        
        if not city:
            raise CityNotFoundError(city_id)
        
        # Calculer la production passive de base à partir des sites de ressources avec ouvriers
        from app.data.resource_sites_database import RESOURCE_SITE_LEVELS, SITE_TO_RESOURCE
        workers_assigned = city.get('workers_assigned', {})
        base_production = 0.0  # Production de base calculée à partir des ouvriers
        
        for site_type, workers in workers_assigned.items():
            if workers > 0 and site_type in SITE_TO_RESOURCE:
                if SITE_TO_RESOURCE[site_type] == resource:
                    site_data = RESOURCE_SITE_LEVELS.get(resource, {}).get('1', {})
                    base_production_per_worker = site_data.get('base_yield', 1.0)
                    base_production += workers * base_production_per_worker
        
        # Récupérer les bonus depuis la sauvegarde (plus de recalcul en temps réel)
        building_bonus = city.get('resources', {}).get('building_bonus', {}).get(resource, 0)
        
        # Bonus de recherche au niveau JOUEUR (pas ville)
        research_bonus = 0
        player_id = city.get('owner')
        if player_id:
            players_data = data_manager.load_players()
            player = next((p for p in players_data.get('players', []) if p['id'] == player_id), None)
            if player:
                research_effects = player.get('research_effects', {})
                resource_bonuses = research_effects.get('resource_bonuses', {})
                research_bonus = resource_bonuses.get(resource, 0)
        
        # Bonus spécial (pour l'instant 0)
        special_bonus = 0
        
        # Calculer la production totale
        total_production = game_logic.calculate_total_production_rate(city, resource)
        
        # Récupérer les informations des sites de ressources avec ouvriers (déjà calculé plus haut)
        # La production des sites est maintenant incluse dans base_production
        site_production = 0  # Pas besoin de recalculer, déjà dans base_production
        
        # Production totale = production passive de base (avec bonus)
        # Calculer la capacité de stockage réelle
        storage_capacities = calculate_storage_capacities(city)
        storage_capacity = storage_capacities['total'].get(resource, 0)
        
        final_total_production = total_production
        
        return jsonify({
            'baseProduction': base_production,
            'buildingBonus': building_bonus,
            'researchBonus': research_bonus,
            'specialBonus': special_bonus,
            'totalProduction': final_total_production,
            'siteProduction': site_production,
            'passiveProduction': total_production,
            'storageCapacity': storage_capacity
        })
        
    except Exception as e:
        print(f"Erreur get_resource_production_details: {e}")
        raise GameValidationError('Erreur serveur')

@city_bp.route('/<city_id>/assign-workers', methods=['POST'])
@handle_errors
def assign_building_workers(city_id):
    """Assigne des ouvriers à un bâtiment spécifique dans une ville"""
    try:
        data = request.get_json()
        building_type = data.get('building_type')  # ex: 'academy', 'sawmill', etc.
        workers = data.get('workers', 0)
        player_id = data.get('player_id')
        if not building_type:
            raise GameValidationError('building_type requis')
        
        if not player_id:
            raise GameValidationError('player_id requis')
            
        if workers < 0:
            raise GameValidationError('Nombre d\'ouvriers invalide')
        
        # Charger les données de sauvegarde
        savegame_data = data_manager.load_savegame()
        if not savegame_data:
            raise GameValidationError('Impossible de charger les données')
        
        # Trouver la ville
        city = next((c for c in savegame_data.get('cities', []) if c.get('id') == city_id), None)
        if not city:
            raise CityNotFoundError(city_id)
        
        # Vérifier que la ville appartient au joueur
        if city.get('owner') != player_id:
            raise GameValidationError('Accès interdit: cette ville ne vous appartient pas')
        
        # Vérifier que le bâtiment existe dans la ville
        buildings = city.get('buildings', [])
        # Gérer la casse pour l'académie
        building_name_variations = [building_type]
        if building_type.lower() == 'academy':
            building_name_variations = ['academy', 'Academy']
        
        building = next((b for b in buildings if b.get('name') in building_name_variations), None)
        if not building:
            raise GameValidationError(f'Bâtiment {building_type} non trouvé dans cette ville')
        
        # Récupérer la capacité maximale du bâtiment
        buildings_data = data_manager.load_buildings()
        if not buildings_data:
            raise GameValidationError('Configuration bâtiments introuvable')
        
        # Gérer la casse pour la config
        building_config_key = building_type
        if building_type.lower() == 'academy':
            building_config_key = 'Academy'  # Utiliser la casse du JSON
        
        building_config = buildings_data.get(building_config_key, {})
        building_level = building.get('level', 1)
        levels = building_config.get('levels', [])
        
        if building_level > len(levels):
            raise GameValidationError('Niveau de bâtiment invalide')
        
        level_config = levels[building_level - 1] if levels else {}
        effect = level_config.get('effect', {})
        max_workers = effect.get('max_workers', 0)
        
        if workers > max_workers:
            raise GameValidationError(f'Capacité maximale dépassée. Maximum: {max_workers}')
        
        # Vérifier la population libre
        # Normaliser la clé pour l'académie (toujours en minuscule)
        storage_key = building_type.lower() if building_type.lower() == 'academy' else building_type
        
        # Pour l'académie, additionner toutes les variantes existantes
        current_workers = 0
        if building_type.lower() == 'academy':
            for key_variant in ['Academy', 'academy', 'ACADEMY']:
                current_workers += city.get('workers_assigned', {}).get(key_variant, 0)
        else:
            current_workers = city.get('workers_assigned', {}).get(storage_key, 0)
            
        population_free = city.get('resources', {}).get('population_free', 0)
        worker_difference = workers - current_workers
        
        if worker_difference > population_free:
            raise GameValidationError(f'Population libre insuffisante. Disponible: {population_free}')
        
        # Assigner les ouvriers
        if 'workers_assigned' not in city:
            city['workers_assigned'] = {}        # Normaliser la clé pour l'académie (toujours en minuscule)
        storage_key = building_type.lower() if building_type.lower() == 'academy' else building_type        # Pour l'académie, nettoyer les anciennes entrées avec différentes casses
        if building_type.lower() == 'academy':
            # Nettoyer TOUTES les variantes avant d'assigner la nouvelle valeur
            academy_variants = ['Academy', 'academy', 'ACADEMY']
            for key_variant in academy_variants:
                if key_variant in city['workers_assigned']:                    del city['workers_assigned'][key_variant]
        
        # Assigner la nouvelle valeur avec la clé normalisée
        city['workers_assigned'][storage_key] = workers
        
        # Recalculer la population libre
        city['resources']['population_free'] = game_logic.calculate_actual_free_population(city)
        
        # Sauvegarder (forcer la sauvegarde pour les assignations d'ouvriers - action critique)
        if not data_manager.save_savegame(savegame_data, force_save=True):
            raise GameValidationError('Erreur lors de la sauvegarde')
        
        # Mettre à jour l'activité du joueur
        if session_tracker:
            session_tracker.update_activity(player_id)
        
        # 🕒 SYSTÈME CENTRALISÉ : Production de recherche maintenant gérée automatiquement
        current_research_points = 0
        if building_type.lower() == 'academy':
            # game_logic.update_research_points_production()  # DÉSACTIVÉ
            
            # Récupérer les points de recherche actuels du joueur
            players_data = data_manager.load_players()
            if players_data:
                player = next((p for p in players_data.get('players', []) if p['id'] == player_id), None)
                if player:
                    current_research_points = player.get('research_points', 0)
        
        return jsonify({
            'success': True,
            'workers_assigned': workers,
            'building_type': building_type,
            'population_free': city['resources']['population_free'],
            'research_points': current_research_points
        })
        
    except Exception as e:
        print(f"Erreur assign_building_workers: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500

@city_bp.route('/update-buildings-status', methods=['POST'])
def update_buildings_status():
    """Met à jour le statut de tous les bâtiments en construction"""
    try:
        # Importer ici pour éviter les problèmes de dépendances
        from ..business.city_service import CityService
        from ..game_logic import GameLogic
        from ..data_manager import DataManager
        import os
        
        # Créer les services directement
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        data_manager_instance = DataManager(base_dir)
        game_logic_instance = GameLogic(data_manager_instance)
        city_service_instance = CityService(data_manager_instance, game_logic_instance)
        
        result = city_service_instance.update_all_buildings_status()
        
        return jsonify({
            'success': True,
            'message': f"Mise à jour terminée: {result['buildings_completed']} bâtiments terminés sur {result['cities_processed']} villes",
            'result': result
        }), 200
        
    except Exception as e:
        print(f"Erreur update_buildings_status: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500

@city_bp.route('/<city_id>/gold-rate', methods=['POST'])
@handle_errors
def set_gold_rate(city_id):
    """Définit le taux d'impôt d'une ville."""
    try:
        data = request.get_json()
        if not data or 'gold_rate' not in data:
            return jsonify({'error': 'gold_rate requis'}), 400
        
        gold_rate = data['gold_rate']
        if not isinstance(gold_rate, int) or gold_rate not in [1, 2, 3]:
            return jsonify({'error': 'gold_rate doit être 1, 2 ou 3'}), 400
        
        # Charger les données
        savegame_data = data_manager.load_savegame()
        if not savegame_data:
            return jsonify({'error': 'Données non trouvées'}), 404
        
        # Trouver la ville
        city = None
        for c in savegame_data.get('cities', []):
            if c.get('id') == city_id:
                city = c
                break
        
        if not city:
            return jsonify({'error': 'Ville non trouvée'}), 404
        
        # Mettre à jour le taux d'impôt
        city['gold_rate'] = gold_rate
        
        # Sauvegarder (forcer la sauvegarde pour les changements de taux d'impôt - action critique)
        data_manager.save_savegame(savegame_data, force_save=True)
        
        # Mettre à jour l'activité du joueur
        owner = city.get('owner')
        if owner and session_tracker:
            session_tracker.update_activity(owner)
        
        return jsonify({
            'success': True,
            'city_id': city_id,
            'gold_rate': gold_rate
        })
        
    except Exception as e:
        print(f"Erreur set_gold_rate: {e}")
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500

@city_bp.route('/<city_id>/windmill-multiplier', methods=['POST'])
@handle_errors
def set_windmill_multiplier(city_id):
    """Définit le multiplicateur de consommation de céréales du moulin d'une ville."""
    try:
        data = request.get_json()
        if not data or 'multiplier' not in data:
            return jsonify({'error': 'multiplier requis'}), 400
        
        multiplier = data['multiplier']
        if not isinstance(multiplier, (int, float)) or multiplier < 1:
            return jsonify({'error': 'multiplier doit être un nombre >= 1'}), 400
        
        # Charger les données
        savegame_data = data_manager.load_savegame()
        if not savegame_data:            return jsonify({'error': 'Données non trouvées'}), 404
        
        # Trouver la ville
        city = None
        for c in savegame_data.get('cities', []):
            if c.get('id') == city_id:
                city = c
                break
        
        if not city:            return jsonify({'error': 'Ville non trouvée'}), 404
        
        # SIMPLIFIÉ - set windmill multiplier directement
        city['windmill_cereal_multiplier'] = multiplier
        actual_multiplier = multiplier
        
        # Sauvegarder (forcer la sauvegarde pour les changements de multiplicateur - action critique)
        data_manager.save_savegame(savegame_data, force_save=True)
        
        result = {
            'success': True,
            'city_id': city_id,
            'multiplier': actual_multiplier
        }
        return jsonify(result)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500

@city_bp.route('/<city_id>/windmill-multiplier', methods=['GET'])
@handle_errors  
def get_windmill_multiplier(city_id):
    """Récupère le multiplicateur de consommation de céréales du moulin d'une ville."""
    try:
        # Charger les données
        savegame_data = data_manager.load_savegame()
        if not savegame_data:
            return jsonify({'error': 'Données non trouvées'}), 404
        
        # Trouver la ville
        city = None
        for c in savegame_data.get('cities', []):
            if c.get('id') == city_id:
                city = c
                break
        
        if not city:
            return jsonify({'error': 'Ville non trouvée'}), 404
        
        multiplier = city.get('windmill_cereal_multiplier', 1)
        
        return jsonify({
            'city_id': city_id,
            'multiplier': multiplier
        })
        
    except Exception as e:
        print(f"Error in get_windmill_multiplier: {e}")
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500

@city_bp.route('/<city_id>/rename', methods=['POST'])
@handle_errors
def rename_city(city_id):
    """Renomme une ville."""
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'name requis'}), 400
        
        new_name = data['name'].strip()
        if not new_name:
            return jsonify({'error': 'Le nom ne peut pas être vide'}), 400
        
        if len(new_name) > 50:
            return jsonify({'error': 'Le nom ne peut pas dépasser 50 caractères'}), 400
        
        # Charger les données
        savegame_data = data_manager.load_savegame()
        if not savegame_data:
            return jsonify({'error': 'Données non trouvées'}), 404
        
        # Trouver la ville
        city = next((c for c in savegame_data.get('cities', []) if c.get('id') == city_id), None)
        
        if not city:
            return jsonify({'error': 'Ville non trouvée'}), 404
        # Mettre à jour le nom
        old_name = city.get('name', 'Ville sans nom')
        city['name'] = new_name
        
        # Sauvegarder (forcer la sauvegarde pour les changements de nom - action critique)
        if not data_manager.save_savegame(savegame_data, force_save=True):
            return jsonify({'error': 'Erreur lors de la sauvegarde'}), 500
        
        # Mettre à jour l'activité du joueur
        owner = city.get('owner')
        if owner and session_tracker:
            session_tracker.update_activity(owner)
        
        print(f"[RENAME] Ville {city_id} renommée de '{old_name}' vers '{new_name}'")
        
        return jsonify({
            'success': True,
            'city_id': city_id,
            'name': new_name,
            'old_name': old_name
        })
        
    except Exception as e:
        print(f"Erreur rename_city: {e}")
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500

@city_bp.route('/<city_id>/storage', methods=['GET'])
@handle_errors
def get_city_storage(city_id):
    """
    Récupère les données de stockage de la ville (capacités et ressources sécurisées).
    
    Returns:
        JSON avec:
        - total: Capacités totales par ressource
        - secure: Capacités sécurisées par ressource  
        - current: Ressources actuellement stockées
    """
    try:
        # Charger les données
        savegame_data = data_manager.load_savegame()
        if not savegame_data:
            return jsonify({'error': 'Données non trouvées'}), 404
        
        # Trouver la ville
        city = None
        for c in savegame_data.get('cities', []):
            if c.get('id') == city_id:
                city = c
                break
        
        if not city:
            return jsonify({'error': 'Ville non trouvée'}), 404
        
        # Calculer les capacités de stockage en fonction des entrepôts
        storage_capacities = calculate_storage_capacities(city)
        
        # Récupérer les ressources actuelles
        current_resources = city.get('resources', {})
        
        return jsonify({
            'success': True,
            'total_storage': storage_capacities['total'],
            'secure_storage': storage_capacities['secure'],
            'current_resources': {
                'wood': current_resources.get('wood', 0),
                'stone': current_resources.get('stone', 0),
                'iron': current_resources.get('iron', 0),
                'cereal': current_resources.get('cereal', 0),
                'papyrus': current_resources.get('papyrus', 0),
                'meat': current_resources.get('meat', 0),
                'marble': current_resources.get('marble', 0),
                'horse': current_resources.get('horse', 0),
                'glass': current_resources.get('glass', 0),
                'gunpowder': current_resources.get('gunpowder', 0),
                'coal': current_resources.get('coal', 0),
                'cotton': current_resources.get('cotton', 0),
                'spices': current_resources.get('spices', 0)
            }
        })
        
    except Exception as e:
        print(f"Erreur get_city_storage: {e}")
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500

def calculate_storage_capacities(city):
    """
    Calcule les capacités totales et sécurisées en fonction des entrepôts construits.
    Utilise la fonction du jeu pour inclure la capacité de base.
    
    Args:
        city: Dictionnaire de la ville
        
    Returns:
        Dict avec 'total' et 'secure' capacités par ressource
    """
    # Utiliser la fonction du jeu qui inclut la capacité de base
    total_storage = game_logic.get_city_storage_limits(city)
    
    # Calculer les capacités sécurisées séparément (entrepôts uniquement)
    buildings_path = os.path.join(data_manager.data_dir, 'buildings.json')
    with open(buildings_path, 'r', encoding='utf-8') as f:
        buildings_data = json.load(f)
    
    warehouse_data = buildings_data.get('Entrepôt', {})
    levels = warehouse_data.get('levels', [])
    
    # Récupérer les entrepôts de la ville
    city_buildings = city.get('buildings', [])
    warehouses = [b for b in city_buildings if b.get('name') == 'Entrepôt']
    
    # Initialiser les capacités sécurisées
    secure_storage = {}
    resources = ['wood', 'stone', 'iron', 'cereal', 'papyrus', 'meat', 'marble', 
                'horse', 'glass', 'gunpowder', 'coal', 'cotton', 'spices']
    
    for resource in resources:
        secure_storage[resource] = 0
    
    # Calculer les capacités sécurisées en fonction des entrepôts
    for warehouse in warehouses:
        level = warehouse.get('level', 1)
        if 1 <= level <= len(levels):
            level_data = levels[level - 1]  # Index 0-based
            effect = level_data.get('effect', {})
            
            # Ajouter capacités sécurisées
            secure_effect = effect.get('secure_storage', {})
            for resource, capacity in secure_effect.items():
                if resource in secure_storage:
                    secure_storage[resource] += capacity
    
    return {
        'total': total_storage,
        'secure': secure_storage
    }

@city_bp.route('/<city_id>/unblock-growth', methods=['POST'])
@handle_errors
def unblock_growth(city_id):
    """
    Débloque manuellement la croissance de population d'une ville.
    Utilisé quand la ville a récupéré des céréales après un blocage.
    """
    savegame = data_manager.load_savegame()
    city = next((c for c in savegame.get('cities', []) if c['id'] == city_id), None)
    
    if not city:
        raise CityNotFoundError(city_id)
    
    resources = city.get('resources', {})
    current_cereal = resources.get('cereal', 0)
    is_blocked = resources.get('growth_blocked_no_cereal', False)
    
    # Vérifier que la ville a bien des céréales maintenant
    if current_cereal < 1:
        return jsonify({
            'success': False,
            'message': 'Impossible de débloquer : la ville n\'a pas assez de céréales (minimum 1).'
        }), 400
    
    # Débloquer la croissance
    resources['growth_blocked_no_cereal'] = False
    data_manager.save_savegame(savegame, force_save=True)
    
    return jsonify({
        'success': True,
        'message': 'Croissance de population débloquée !',
        'was_blocked': is_blocked,
        'current_cereal': current_cereal
    })
