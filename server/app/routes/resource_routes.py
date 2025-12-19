"""
=================================================================
RESOURCE_ROUTES.PY - Routes pour la gestion des sites de ressources
=================================================================

RESPONSABILITÉS:
- Informations sur les sites de ressources par île
- Assignation d'ouvriers aux sites
- Donations pour améliorer les sites
- Mise à jour de la production

ROUTES DISPONIBLES:
- GET /api/resources/site/<island_id>/<site_type>/info
- POST /api/resources/site/<island_id>/<site_type>/assign-workers
- POST /api/resources/site/<island_id>/<site_type>/donate
- POST /api/resources/update-production

AVANT D'AJOUTER UNE ROUTE:
- Utiliser les services appropriés (CityService, ResourceSiteService)
- Valider les données d'entrée
- Gérer les erreurs proprement

DÉPENDANCES:
- DataManager pour les données
- GameLogic pour les calculs
- PopulationManager pour la population
- ResourceSiteService pour les sites de ressources
=================================================================
"""

from flask import Blueprint, request, jsonify
from ..core.decorators import handle_errors, validate_json
from ..core.exceptions import GameValidationError, CityNotFoundError
from ..services.resource_site_service import ResourceSiteService

# Initialiser le blueprint
resource_bp = Blueprint('resources', __name__, url_prefix='/api/resources')

# Services à injecter
data_manager = None
game_logic = None
population_manager = None
resource_site_service = None

def init_resource_routes(dm, gl, pm):
    """Initialise les routes avec les services"""
    global data_manager, game_logic, population_manager, resource_site_service
    data_manager = dm
    game_logic = gl
    population_manager = pm
    resource_site_service = ResourceSiteService(data_manager)

@resource_bp.route('/site/<island_id>/<site_type>/info', methods=['GET'])
@handle_errors
def get_resource_site_info(island_id, site_type):
    """Récupère les informations détaillées d'un site de ressources"""
    # Récupérer le player_id depuis les paramètres de requête
    player_id = request.args.get('player_id')
    if not player_id:
        raise GameValidationError('player_id requis en paramètre')
    
    # Convertir island_id en coordonnées [x, y] ou utiliser directement l'ID
    try:
        # Si c'est au format "x,y", convertir en coordonnées
        if isinstance(island_id, str) and ',' in island_id:
            coords = [int(x.strip()) for x in island_id.split(',')]
        else:
            # Sinon, utiliser directement comme ID
            coords = island_id
    except:
        # Si la conversion échoue, utiliser directement comme ID
        coords = island_id
    
    # Utiliser le service de site de ressources
    result = resource_site_service.get_site_info(
        island_coords=coords,
        site_type=site_type,
        player_id=player_id
    )
    
    if result['success']:
        return jsonify(result)
    else:
        raise GameValidationError(result['error'])

@resource_bp.route('/site/<island_id>/<site_type>/assign-workers', methods=['POST'])
@handle_errors
def assign_workers_to_site(island_id, site_type):
    """Assigne des ouvriers à un site de ressources"""
    # Récupérer le player_id depuis les paramètres de requête
    player_id = request.args.get('player_id')
    if not player_id:
        raise GameValidationError('player_id requis en paramètre')
        
    data = request.get_json()
    workers = data.get('workers', 0)
    city_id = data.get('city_id')  # Ville qui fournit les ouvriers
    active_city_id = data.get('active_city_id')  # Ville active dans le headerbar
    
    if not city_id:
        raise GameValidationError('city_id requis')
    if not active_city_id:
        raise GameValidationError('active_city_id requis')
        
    if workers < 0:
        raise GameValidationError('Nombre d\'ouvriers invalide')
    
    # Charger les données de sauvegarde
    savegame_data = data_manager.load_savegame()
    if not savegame_data:
        raise GameValidationError('Impossible de charger les données')

    # Charger l'univers pour récupérer les informations de l'île
    universe_data = data_manager.load_universe()
    if not universe_data:
        raise GameValidationError('Impossible de charger l\'univers')
        
    # Trouver l'île
    island = None
    islands = universe_data.get('islands', [])
    try:
        # Si c'est au format "x,y", convertir en coordonnées
        if isinstance(island_id, str) and ',' in island_id:
            coords = [int(x.strip()) for x in island_id.split(',')]
            for isl in islands:
                if isl.get('coords') == coords:
                    island = isl
                    break
        else:
            # Sinon, chercher par ID
            island_str = str(island_id)
            for isl in islands:
                if str(isl.get('id')) == island_str:
                    island = isl
                    break
    except:
        pass
        
    if not island:
        raise GameValidationError('Île introuvable')
        
    # Trouver la ville active (celle dans le headerbar)
    active_city = next((c for c in savegame_data.get('cities', []) if c.get('id') == active_city_id), None)
    if not active_city:
        raise GameValidationError('Ville active introuvable')
    
    # Vérifier que la ville active appartient au joueur
    if active_city.get('owner') != player_id:
        raise GameValidationError('La ville active ne vous appartient pas.')
    
    # VÉRIFICATION RECHERCHE: Le joueur doit avoir débloqué "acces_ressources" (sauf pour la forêt)
    if site_type != 'forest':
        from app.business.research_service import ResearchService
        research_service = ResearchService(data_manager)
        
        if not research_service.can_assign_workers_to_resource_sites(player_id):
            raise GameValidationError('🔒 Recherche "Accès Ressources de Base" requise pour assigner des ouvriers aux sites de ressources.')
    
    # VALIDATION PRINCIPALE: Vérifier que la ville active est sur la même île que le site
    target_island_id = island.get('id')
    active_city_island_id = active_city.get('island_id')
    if str(active_city_island_id) != str(target_island_id):
        raise GameValidationError('Vous ne pouvez affecter des ouvriers à ce site de production qu\'avec des villes provenant de cette île.')
    
    # Trouver la ville qui fournit les ouvriers
    city = next((c for c in savegame_data.get('cities', []) if c.get('id') == city_id), None)
    if not city:
        raise CityNotFoundError(city_id)
    
    # SÉCURITÉ: Vérifier que la ville qui fournit les ouvriers appartient bien au joueur connecté
    if city.get('owner') != player_id:
        raise GameValidationError(f'Accès interdit: cette ville appartient à {city.get("owner", "un autre joueur")}')
    
    # Calculer les ouvriers actuellement assignés à ce site
    current_workers = city.get('workers_assigned', {}).get(site_type, 0)
    
    # Vérifier la population libre disponible
    population_free = city.get('resources', {}).get('population_free', 0)
    available_population = population_free + current_workers
    
    if workers > available_population:
        raise GameValidationError(f'Population insuffisante. Disponible: {available_population}')
    
    # Charger la configuration des sites de ressources
    config = data_manager.load_resource_sites_config()
    site_to_resource = config.get('site_to_resource', {})
    resource_site_levels = config.get('resource_site_levels', {})
    
    # Convertir le type de site en type de ressource
    resource_type = site_to_resource.get(site_type, site_type)
    site_data = resource_site_levels.get(resource_type, {})
    
    if not site_data:
        raise GameValidationError(f'Type de site inconnu: {site_type}')
    
    # Récupérer le niveau réel du site depuis savegame.json (PAS universe.json)
    resource_sites = savegame_data.get('resource_sites', {})
    site_key = f"{island_id}_{site_type}"
    site_info = resource_sites.get(site_key, {})
    current_level = site_info.get('level', 1)
    
    # CORRECTION : Si le site est en cours d'amélioration, utiliser le niveau de destination
    # pour la validation des ouvriers (comme l'interface l'affiche)
    if 'upgrade_start_time' in site_info and site_info.get('upgrade_start_time'):
        # Le site est en cours d'amélioration, utiliser le niveau suivant
        current_level = current_level + 1
    
    # Récupérer les données du niveau (utiliser str pour la clé)
    level_data = site_data.get(str(current_level), site_data.get('1', {}))
    max_workers = level_data.get('max_workers_per_city', 10)
    
    if workers > max_workers:
        raise GameValidationError(f'Capacité maximale dépassée. Maximum: {max_workers} (niveau {current_level})')
    
    # Mettre à jour l'assignation des ouvriers
    if 'workers_assigned' not in city:
        city['workers_assigned'] = {}
    city['workers_assigned'][site_type] = workers
    
    # Recalculer et mettre à jour la population libre réelle
    city['resources']['population_free'] = game_logic.calculate_actual_free_population(city)
    
    # Sauvegarder les changements (forcer la sauvegarde pour les assignations d'ouvriers - action critique)
    data_manager.save_savegame(savegame_data, force_save=True)
    
    return jsonify({
        'success': True,
        'workers_assigned': workers,
        'population_free': city['resources']['population_free'],
        'message': f'{workers} ouvriers assignés au site {site_type}'
    })

@resource_bp.route('/site/<island_id>/<site_type>/donate', methods=['POST'])
@handle_errors
def donate_to_site(island_id, site_type):
    """Effectue une donation pour améliorer un site de ressources"""
    # Récupérer le player_id depuis les paramètres de requête
    player_id = request.args.get('player_id')
    if not player_id:
        raise GameValidationError('player_id requis en paramètre')
        
    data = request.get_json()
    resource_type = data.get('resource_type')
    amount = data.get('amount', 0)
    city_id = data.get('city_id')  # Ville qui fournit les ressources
    active_city_id = data.get('active_city_id')  # Ville active dans le headerbar
    
    if not city_id:
        raise GameValidationError('city_id requis')
    if not active_city_id:
        raise GameValidationError('active_city_id requis')
    if not resource_type:
        raise GameValidationError('resource_type requis')
    if amount <= 0:
        raise GameValidationError('Montant de don invalide')
    
    # Convertir island_id en coordonnées [x, y] ou utiliser directement l'ID
    try:
        # Si c'est au format "x,y", convertir en coordonnées
        if isinstance(island_id, str) and ',' in island_id:
            coords = [int(x.strip()) for x in island_id.split(',')]
        else:
            # Sinon, utiliser directement comme ID
            coords = island_id
    except:
        # Si la conversion échoue, utiliser directement comme ID
        coords = island_id
    
    # Utiliser le service de site de ressources
    result = resource_site_service.donate_to_site(
        island_coords=coords,
        site_type=site_type,
        city_id=city_id,
        active_city_id=active_city_id,
        player_id=player_id,
        resource_type=resource_type,
        amount=amount
    )
    
    # 🎯 Hook pour les quêtes : tracker les donations
    if result['success']:
        try:
            from app.services.quest_service import quest_service
            from app.data_manager import DataManager
            import os
            
            # Obtenir le répertoire de base
            current_file = os.path.abspath(__file__)
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
            
            # Récupérer le username depuis player_id
            dm = DataManager(base_dir)
            players_data = dm.load_players()
            # players_data est un dict {"players": [...]}
            players_list = players_data.get('players', []) if isinstance(players_data, dict) else []
            player = next((p for p in players_list if p.get('id') == player_id), None)
            
            if player:
                username = player.get('username')
                if username:
                    # Mettre à jour la progression de la quête eco_donate_sites
                    quest_service.update_quest_progress(
                        username=username,
                        quest_id='eco_donate_sites',
                        increment=amount
                    )
                    print(f"[QUEST] Quest updated: {username} donated {amount} {resource_type}")
        except Exception as e:
            # Ne pas bloquer si la mise à jour des quêtes échoue
            print(f"[QUEST ERROR] Failed to update quest progress: {e}")
    
    if result['success']:
        return jsonify(result)
    else:
        raise GameValidationError(result['error'])
