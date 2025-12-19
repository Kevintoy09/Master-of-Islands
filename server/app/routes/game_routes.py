"""
=================================================================
GAME_ROUTES.PY - Routes pour les contrôles du jeu
=================================================================

RESPONSABILITÉS:
- Contrôle de la vitesse du temps (time-control)
- Mise à jour manuelle de la production
- État global du jeu
- Paramètres de développement

ROUTES DISPONIBLES:
- GET /api/game/time-control     → Obtenir la vitesse actuelle
- POST /api/game/time-control    → Modifier la vitesse
- POST /api/game/update-production → Forcer la mise à jour

AVANT D'AJOUTER UNE ROUTE:
- Vérifier que c'est bien lié au contrôle global du jeu
- Utiliser les managers appropriés (time_manager, game_logic)
- Documenter les paramètres et effets

DÉPENDANCES:
- GameLogic pour la logique de jeu
- TimeManager pour la gestion du temps
=================================================================
"""

from flask import Blueprint, request, jsonify
from ..core.decorators import handle_errors, validate_json
from ..core.exceptions import GameValidationError
from ..city_constants import DEFAULT_CITY_RESOURCES
from ..business.player_resources_service import PlayerResourcesService

# Initialiser le blueprint principal
game_bp = Blueprint('game', __name__, url_prefix='/api/game')

# Blueprint pour les routes legacy
legacy_game_bp = Blueprint('legacy_game', __name__, url_prefix='/api')

# Services à injecter
game_logic = None
time_manager = None
data_manager = None

def init_game_routes(gl, tm, dm=None):
    """Initialise les routes avec les services"""
    global game_logic, time_manager, data_manager
    game_logic = gl
    time_manager = tm
    data_manager = dm

@game_bp.route('/time-control', methods=['GET'])
@handle_errors
def get_time_control():
    """
    Retourne les informations sur la vitesse du jeu.
    """
    return jsonify({
        'time_multiplier': time_manager.get_time_multiplier(),
        'display_info': time_manager.get_display_info()
    })

@game_bp.route('/time-control', methods=['POST'])
@handle_errors
def set_time_control():
    """
    Modifie la vitesse du jeu.
    Body: {"multiplier": 3600} ou {"preset": "development"|"normal"|"fast"}
    """
    data = request.get_json(force=True)
    
    if 'preset' in data:
        preset = data['preset']
        if preset == 'development':
            time_manager.set_time_multiplier(3600)
        elif preset == 'normal':
            time_manager.set_time_multiplier(1)
        elif preset == 'fast':
            time_manager.set_time_multiplier(60)
        else:
            raise GameValidationError('Preset invalide. Utilisez: development, normal, fast')
    elif 'multiplier' in data:
        multiplier = data['multiplier']
        if not isinstance(multiplier, (int, float)) or multiplier <= 0:
            raise GameValidationError('Le multiplicateur doit être un nombre positif')
        time_manager.set_time_multiplier(multiplier)
    else:
        raise GameValidationError('Spécifiez multiplier ou preset')
    
    return jsonify({
        'success': True,
        'time_multiplier': time_manager.get_time_multiplier(),
        'display_info': time_manager.get_display_info()
    })

@game_bp.route('/update-production', methods=['POST'])
@handle_errors
def trigger_production_update():
    """
    API pour déclencher manuellement la mise à jour de production.
    Utile pour le développement et les tests.
    """
    # 🕒 SYSTÈME CENTRALISÉ : Production maintenant gérée automatiquement
    # game_logic.update_resource_production()  # DÉSACTIVÉ
    # game_logic.update_research_points_production()  # DÉSACTIVÉ
    
    return jsonify({
        'success': True,
        'message': 'Production mise à jour avec succès'
    })

@game_bp.route('/update-research', methods=['POST'])
@handle_errors
def trigger_research_update():
    """
    API pour déclencher manuellement la mise à jour des points de recherche.
    """
    # 🕒 SYSTÈME CENTRALISÉ : Production recherche maintenant gérée automatiquement  
    # game_logic.update_research_points_production()  # DÉSACTIVÉ
    
    return jsonify({
        'success': True,
        'message': 'Points de recherche mis à jour avec succès'
    })

# ===============================================
# ROUTES LEGACY pour compatibilité
# ===============================================

@legacy_game_bp.route('/claim_city', methods=['POST'])
@handle_errors
def legacy_claim_city():
    """Route legacy: réclame une ville pour un joueur"""
    from ..transition_utils import load_savegame_transition, save_savegame_transition
    
    try:
        data = request.get_json(force=True)
        player_id = data.get('player_id')
        city_id = data.get('city_id')
        
        if not player_id or not city_id:
            return jsonify({'error': 'player_id and city_id are required'}), 400

        # Charger les données de sauvegarde via le système de transition
        savegame_data = load_savegame_transition()
        if not savegame_data:
            return jsonify({'error': 'Impossible de charger les données'}), 500
        
        # Trouver la ville dans l'univers
        universe = data_manager.load_universe()
        city_found = None
        for island in universe.get('islands', []):
            for element in island.get('elements', []):
                if element.get('type') == 'city' and element.get('id') == city_id:
                    city_found = element
                    break
            if city_found:
                break
        
        if not city_found:
            return jsonify({'error': 'Ville introuvable dans l\'univers'}), 404
        
        # Vérifier si la ville existe déjà dans le savegame
        existing_city = next((c for c in savegame_data.get('cities', []) if c.get('id') == city_id), None)
        
        if existing_city:
            if existing_city.get('owner'):
                return jsonify({'error': 'Cette ville est déjà réclamée'}), 400
            # Réclamer la ville existante
            existing_city['owner'] = player_id
            city = existing_city
        else:
            # Créer une nouvelle ville dans le savegame
            island_data = None
            island_id = None
            for island in universe.get('islands', []):
                if any(e.get('id') == city_id for e in island.get('elements', [])):
                    island_data = island
                    island_id = island.get('id')
                    break
            
            # Récupérer les informations de l'île
            city_layout = island_data.get('city_layout', 'city_type_1') if island_data else 'city_type_1'
            base_resource = island_data.get('base_resource', 'stone') if island_data else 'stone'
            
            # Créer la ville avec les bâtiments de base (Hôtel de Ville obligatoire)
            initial_buildings = [
                {
                    'name': 'Hôtel de Ville',
                    'level': 1,
                    'status': 'Terminé',
                    'slot_id': 'slot_1'
                }
            ]
            
            # Utiliser les ressources par défaut centralisées
            resources = DEFAULT_CITY_RESOURCES.copy()
            
            city = {
                'id': city_id,
                'name': city_found.get('name', 'Unknown City'),
                'owner': player_id,
                'island_id': island_id,
                'city_layout': city_layout,
                'base_resource': base_resource,
                'controlable': True,
                'buildings': initial_buildings,
                'workers_assigned': {},
                'construction_queue': [],
                'resources': resources,
                'satisfaction': 100,
                'unlocked_buildings': [],
                'gold_rate': 1,
                'windmill_cereal_multiplier': 1,
                'has_plague': False,
                'storage_capacity': {}
            }
            savegame_data['cities'].append(city)
        
        # Sauvegarder via le système de transition
        success = save_savegame_transition(savegame_data, force=True)
        if not success:
            return jsonify({'error': 'Erreur lors de la sauvegarde'}), 500
        
        return jsonify({
            'success': True, 
            'message': 'City claimed successfully',
            'city': city
        })
        
    except Exception as e:
        print(f"Erreur claim_city: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Erreur lors de la réclamation', 'details': str(e)}), 500

@legacy_game_bp.route('/savegame', methods=['GET'])
@handle_errors
def legacy_get_savegame():
    """Route legacy: récupère les données de sauvegarde"""
    try:
        data = data_manager.load_savegame()
        if not data:
            return jsonify({'error': 'savegame.json introuvable'}), 500
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': 'savegame.json introuvable', 'details': str(e)}), 500

@legacy_game_bp.route('/update-production', methods=['POST'])
@handle_errors
def legacy_trigger_production_update():
    """Route legacy: met à jour la production et la recherche"""
    try:
        # 🕒 SYSTÈME CENTRALISÉ : Production maintenant gérée automatiquement
        # game_logic.update_resource_production()  # DÉSACTIVÉ
        # game_logic.update_research_points_production()  # DÉSACTIVÉ
        return jsonify({'success': True, 'message': 'Production updated'})
    except Exception as e:
        return jsonify({'error': 'Production update failed', 'details': str(e)}), 500

@legacy_game_bp.route('/player/<player_id>', methods=['GET'])
@handle_errors
def get_player_info(player_id):
    """Récupère les informations complètes d'un joueur"""
    try:
        from app.business.player_service import PlayerService
        
        player_service = PlayerService(data_manager)
        player_info = player_service.get_player_info(player_id)
        
        return jsonify({
            'player_info': player_info
        })
        
    except Exception as e:
        print(f"Erreur get_player_info: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Joueur non trouvé', 'details': str(e)}), 404

@legacy_game_bp.route('/player/<player_id>/info', methods=['GET'])
@handle_errors
def get_player_info_detailed(player_id):
    """Route spécifique pour les popups - informations détaillées du joueur"""
    try:
        from app.business.player_service import PlayerService
        
        player_service = PlayerService(data_manager)
        player_info = player_service.get_player_info(player_id)
        
        return jsonify({
            'player_info': player_info
        })
        
    except Exception as e:
        print(f"Erreur get_player_info_detailed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Joueur non trouvé', 'details': str(e)}), 404

@legacy_game_bp.route('/player/<player_id>/buy-ship', methods=['POST'])
@handle_errors
def buy_ship(player_id):
    """Achète un bateau pour un joueur"""
    try:
        data = request.get_json() or {}
        city_id = data.get('city_id')
        
        if not city_id:
            return jsonify({'error': 'city_id requis'}), 400
        
        # Charger les données
        players_data = data_manager.load_players()
        savegame_data = data_manager.load_savegame()
        
        if not players_data or not savegame_data:
            return jsonify({'error': 'Données introuvables'}), 404
        
        # Trouver le joueur
        player = next((p for p in players_data.get('players', []) if p['id'] == player_id), None)
        if not player:
            return jsonify({'error': 'Joueur introuvable'}), 404
        
        # Trouver la ville
        city = next((c for c in savegame_data.get('cities', []) if c['id'] == city_id), None)
        if not city:
            return jsonify({'error': 'Ville introuvable'}), 404
        
        # Vérifier que la ville appartient au joueur
        if city.get('owner') != player_id:
            return jsonify({'error': 'Cette ville ne vous appartient pas'}), 403
        
        # Initialiser le service de ressources globales
        player_resources_service = PlayerResourcesService(data_manager)
        
        # Récupérer les ressources globales du joueur (relecture fraîche pour éviter le cache)
        fresh_players_data = data_manager.load_players(use_cache=False)  # Relecture forcée
        fresh_player = next((p for p in fresh_players_data.get('players', []) if p['id'] == player_id), None)
        current_ships = fresh_player.get('transport_ships_total', 0) if fresh_player else 0
        
        global_resources = player_resources_service.get_player_global_resources(player_id)
        current_gold = global_resources.get('gold', 0)
        
        # Calculer le prix du prochain bateau
        ship_price = int(100 * (1.5 ** current_ships))
        
        # Vérifier l'or disponible
        if current_gold < ship_price:
            return jsonify({
                'error': f'Or insuffisant. Requis: {ship_price}, disponible: {int(current_gold)}'
            }), 400
        
        # Effectuer l'achat (ressources globales)
        success_ships = player_resources_service.add_to_player_global_resource(player_id, 'transport_ships_total', 1)
        success_gold = player_resources_service.spend_player_global_resource(player_id, 'gold', ship_price)
        
        if not (success_ships and success_gold):
            return jsonify({'error': 'Erreur lors de la mise à jour des ressources'}), 500

        # Note: Plus de synchronisation vers les villes - les ressources globales restent au niveau joueur
        
        return jsonify({
            'success': True,
            'message': f'Bateau acheté avec succès pour {ship_price} or',
            'player_info': {
                'id': player['id'],
                'transport_ships': current_ships + 1,
                'transport_ships_total': current_ships + 1
            },
            'new_gold': current_gold - ship_price,
            'ship_price': ship_price
        })
        
    except Exception as e:
        print(f"Erreur buy_ship: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Erreur lors de l\'achat du bateau', 'details': str(e)}), 500

@legacy_game_bp.route('/player/<player_id>/cities', methods=['GET'])
@handle_errors
def get_player_cities(player_id):
    """Récupère la liste des villes d'un joueur avec leurs noms"""
    try:
        savegame_data = data_manager.load_savegame()
        if not savegame_data:
            return jsonify({'cities': []}), 200
        
        # Filtrer les villes du joueur
        player_cities = [
            city for city in savegame_data.get('cities', []) 
            if city.get('owner') == player_id
        ]
        
        # Retourner la liste avec id et nom
        cities_info = [
            {
                'id': city['id'],
                'name': city.get('name', f"Ville {city['id']}")
            }
            for city in player_cities
        ]
        
        return jsonify({'cities': cities_info})
        
    except Exception as e:
        print(f"Erreur get_player_cities: {e}")
        return jsonify({'error': 'Erreur lors de la récupération des villes', 'details': str(e)}), 500

@legacy_game_bp.route('/player/<player_id>/resources', methods=['GET'])
@handle_errors
def get_player_resources(player_id):
    """Récupère toutes les ressources globales d'un joueur"""
    try:
        player_resources_service = PlayerResourcesService(data_manager)
        
        # 🕒 SYSTÈME CENTRALISÉ : Production d'or maintenant gérée automatiquement
        # player_resources_service.update_gold_production(player_id)  # DÉSACTIVÉ
        
        # Récupérer les ressources globales
        resources = player_resources_service.get_player_global_resources(player_id)
        
        # Calculer le taux de production d'or actuel
        gold_rate = player_resources_service.calculate_total_gold_production_rate(player_id)
        
        return jsonify({
            'resources': resources,
            'gold_production_rate': gold_rate
        })
        
    except Exception as e:
        print(f"Erreur get_player_resources: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Erreur lors de la récupération des ressources', 'details': str(e)}), 500

@legacy_game_bp.route('/reset_game', methods=['POST'])
@handle_errors
def reset_game():
    """Route pour réinitialiser complètement le jeu"""
    try:
        # Créer un savegame vierge
        empty_savegame = {
            "cities": [],
            "players": {}
        }
        
        # Sauvegarder le nouveau savegame vierge
        if data_manager.save_savegame(empty_savegame):
            # Vider le cache pour forcer le rechargement
            data_manager.clear_cache()
            return jsonify({
                'success': True, 
                'message': 'Jeu réinitialisé avec succès'
            })
        else:
            return jsonify({'error': 'Erreur lors de la sauvegarde du nouveau savegame'}), 500
        
    except Exception as e:
        print(f"Erreur reset_game: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Erreur lors de la réinitialisation', 'details': str(e)}), 500


@game_bp.route('/gold-production', methods=['GET'])
@handle_errors
def get_gold_production():
    """Récupère les détails de production d'or pour le joueur spécifié."""
    try:
        from ..business.player_resources_service import PlayerResourcesService
        
        # Obtenir l'ID du joueur depuis les paramètres de requête
        player_id = request.args.get('player_id')
        if not player_id:
            return jsonify({'error': 'player_id requis en paramètre'}), 400
        
        # Charger les données
        savegame_data = data_manager.load_savegame()
        if not savegame_data:
            return jsonify({'error': 'Données de jeu non trouvées'}), 404
        
        # Utiliser la même logique que le GameLoopManager pour la cohérence
        total_gold_per_second = 0
        cities_gold_info = []
        
        for city in savegame_data.get('cities', []):
            if city.get('owner') == player_id:
                # Population libre de cette ville
                city_free_pop = city.get('resources', {}).get('population_free', 0)
                
                # Utiliser le taux d'or défini par la ville (gold_rate) - MÊME LOGIQUE QUE GAMELOOPMANAGER
                city_gold_rate = city.get('gold_rate', 1)  # 1, 2 ou 3 or/sec par habitant
                
                # Production d'or de cette ville
                city_gold_per_second = city_free_pop * city_gold_rate
                total_gold_per_second += city_gold_per_second
                
                cities_gold_info.append({
                    'city_id': city.get('id'),
                    'city_name': city.get('name'),
                    'population_free': city_free_pop,
                    'tax_rate': city_gold_rate,  # Taux utilisé (1, 2, ou 3)
                    'gold_per_second': city_gold_per_second
                })
        
        return jsonify({
            'total_gold_per_second': total_gold_per_second,
            'cities': cities_gold_info
        })
        
    except Exception as e:
        print(f"Erreur get_gold_production: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Erreur lors de la récupération des données d\'or'}), 500


@legacy_game_bp.route('/players', methods=['GET'])
@handle_errors
def get_players():
    """Récupère la liste de tous les joueurs depuis players.json"""
    try:
        players_data = data_manager.load_players()
        return jsonify(players_data)
    except Exception as e:
        print(f"Erreur get_players: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Erreur lors de la récupération des joueurs', 'players': []}), 500
