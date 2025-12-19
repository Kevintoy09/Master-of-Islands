"""
Routes API pour l'univers, îles et layouts
"""

from flask import Blueprint, request, jsonify
from ..data_manager import DataManager
from ..core.decorators import handle_errors, validate_json

# Création du Blueprint principal
universe_bp = Blueprint('universe', __name__, url_prefix='/api/universe')

# Création d'un Blueprint pour les routes legacy sans préfixe
legacy_bp = Blueprint('legacy_universe', __name__)

# Le data manager sera injecté lors de l'enregistrement
data_manager: DataManager = None

def init_universe_routes(dm: DataManager):
    """Initialise les routes avec le data manager"""
    global data_manager
    data_manager = dm

@universe_bp.route('', methods=['GET'])
@handle_errors
def get_universe():
    """Récupère les données de l'univers"""
    data = data_manager.load_universe()
    if not data or 'islands' not in data:
        return jsonify({'error': 'universe.json introuvable ou vide'}), 500

    # Charger savegame.json pour enrichir les villes
    savegame = data_manager.load_savegame()
    
    # Vérifier et finaliser les constructions terminées
    from app.game_logic import GameLogic
    game_logic = GameLogic(data_manager)
    construction_changes = game_logic.update_construction_statuses_in_memory(savegame)
    if construction_changes:
        data_manager.save_savegame(savegame)
    
    city_save_map = {city['id']: city for city in savegame.get('cities', [])}

    # Enrichir chaque ville de l'univers avec owner, buildings et workers_assigned
    all_cities = []
    for island in data.get('islands', []):
        for element in island.get('elements', []):
            if element.get('type') == 'city':
                city = element.copy()
                save_data = city_save_map.get(city['id'])
                if save_data:
                    city['owner'] = save_data.get('owner', None)
                    city['buildings'] = save_data.get('buildings', [])
                    city['workers_assigned'] = save_data.get('workers_assigned', {})
                    city['military'] = save_data.get('military', {})
                    # Mettre à jour le nom avec celui de la sauvegarde
                    city['name'] = save_data.get('name', city.get('name'))
                else:
                    city['owner'] = None
                    city['buildings'] = []
                    city['workers_assigned'] = {}
                    city['military'] = {}
                all_cities.append(city)

    data['cities'] = all_cities

    # Ajouter les données des bâtiments
    buildings_data = data_manager.load_buildings()
    if buildings_data:
        data['buildings'] = buildings_data

    return jsonify(data)

@universe_bp.route('/islands', methods=['GET'])
@handle_errors
def get_islands():
    """Récupère la liste des îles"""
    universe = data_manager.load_universe()
    islands = universe.get('islands', [])
    result = [{"id": i["id"], "name": i["name"]} for i in islands]
    return jsonify(result)

@universe_bp.route('/island/<island_id>/cities', methods=['GET'])
@handle_errors
def get_island_cities(island_id: str):
    """
    Récupère les villes d'une île (non enrichies).
    Utilisez le tableau 'cities' de /api/universe pour obtenir owner et buildings.
    """
    universe = data_manager.load_universe()
    islands = universe.get('islands', [])
    island = next((i for i in islands if i['id'] == island_id), None)
    if island:
        cities = [el for el in island.get('elements', []) if el.get('type') == 'city']
        return jsonify(cities)
    return jsonify({'error': 'Island not found'}), 404

@universe_bp.route('/layouts', methods=['GET'])
@handle_errors
def get_city_layouts():
    """Récupère tous les layouts de ville"""
    universe = data_manager.load_universe()
    return jsonify(universe.get('city_layouts', {}))

@universe_bp.route('/layout/<layout_id>', methods=['GET'])
@handle_errors
def get_city_layout(layout_id: str):
    """Récupère un layout de ville spécifique"""
    universe = data_manager.load_universe()
    layout = universe.get('city_layouts', {}).get(layout_id)
    
    if layout:
        return jsonify(layout)
    
    return jsonify({'error': 'City layout not found'}), 404

@universe_bp.route('/select-city', methods=['POST'])
@handle_errors
@validate_json('city_id')
def select_city():
    """Sélectionne une ville dans l'univers"""
    data = request.get_json()
    city_id = data.get('city_id') or data.get('cityId')
    
    universe = data_manager.load_universe()
    
    for island in universe.get('islands', []):
        for el in island.get('elements', []):
            if el.get('type') == 'city' and el.get('id') == city_id:
                return jsonify({'success': True, 'city': el})
    
    return jsonify({'error': 'City not found'}), 404

@universe_bp.route('/savegame', methods=['GET'])
@handle_errors
def get_savegame():
    """Récupère les données de sauvegarde"""
    data = data_manager.load_savegame()
    if not data:
        return jsonify({'error': 'savegame.json introuvable'}), 500
    
    return jsonify(data)

@universe_bp.route('/city/<city_id>', methods=['GET'])
@handle_errors
def get_city(city_id: str):
    """
    Récupère les informations d'une ville spécifique (non enrichie).
    Utilisez le tableau 'cities' de /api/universe pour obtenir owner et buildings.
    """
    universe = data_manager.load_universe()
    for island in universe.get('islands', []):
        for el in island.get('elements', []):
            if el.get('type') == 'city' and el.get('id') == city_id:
                return jsonify(el)
    return jsonify({'error': 'City not found'}), 404

# ===============================================
# ROUTES LEGACY pour compatibilité (sans préfixe /api/universe)
# ===============================================

@legacy_bp.route('/islands', methods=['GET'])
@handle_errors
def legacy_get_islands():
    """Route legacy: récupère la liste des îles"""
    universe = data_manager.load_universe()
    islands = universe.get('islands', [])
    result = [{"id": i["id"], "name": i["name"]} for i in islands]
    return jsonify(result)

@legacy_bp.route('/island/<island_id>/cities', methods=['GET'])
@handle_errors
def legacy_get_island_cities(island_id: str):
    """Route legacy: récupère les villes d'une île"""
    universe = data_manager.load_universe()
    islands = universe.get('islands', [])
    island = next((i for i in islands if i['id'] == island_id), None)
    
    if island:
        cities = [el for el in island.get('elements', []) if el.get('type') == 'city']
        return jsonify(cities)
    
    return jsonify({'error': 'Island not found'}), 404

@legacy_bp.route('/city_layouts', methods=['GET'])
@handle_errors
def legacy_get_city_layouts():
    """Route legacy: récupère tous les layouts de ville"""
    universe = data_manager.load_universe()
    return jsonify(universe.get('city_layouts', {}))

@legacy_bp.route('/city_layout/<layout_id>', methods=['GET'])
@handle_errors
def legacy_get_city_layout(layout_id: str):
    """Route legacy: récupère un layout de ville spécifique"""
    universe = data_manager.load_universe()
    layout = universe.get('city_layouts', {}).get(layout_id)
    
    if layout:
        return jsonify(layout)
    
    return jsonify({'error': 'City layout not found'}), 404

@legacy_bp.route('/select-city', methods=['POST'])
@handle_errors
def legacy_select_city():
    """Route legacy: sélectionne une ville dans l'univers"""
    print('--- Requête reçue sur /select-city ---')
    print('Headers:', dict(request.headers))
    print('Data brute:', request.data)
    
    try:
        data = request.get_json(force=True)
        print('JSON reçu:', data)
    except Exception as e:
        print('Erreur de parsing JSON:', e)
        return jsonify({'error': 'Invalid JSON'}), 400
        
    city_id = data.get('city_id') or data.get('cityId') if data else None
    if not city_id:
        print('city_id manquant ou vide')
        return jsonify({'error': 'city_id is required'}), 400
        
    universe = data_manager.load_universe()
    for island in universe.get('islands', []):
        for el in island.get('elements', []):
            if el.get('type') == 'city' and el.get('id') == city_id:
                print('Ville trouvée:', el)
                return jsonify({'success': True, 'city': el})
                
    print('Ville non trouvée pour city_id:', city_id)
    return jsonify({'error': 'City not found'}), 404

@legacy_bp.route('/city/<city_id>', methods=['GET'])
@handle_errors
def legacy_get_city(city_id: str):
    """Route legacy: récupère les informations d'une ville spécifique"""
    universe = data_manager.load_universe()
    for island in universe.get('islands', []):
        for el in island.get('elements', []):
            if el.get('type') == 'city' and el.get('id') == city_id:
                return jsonify(el)
    
    return jsonify({'error': 'City not found'}), 404
