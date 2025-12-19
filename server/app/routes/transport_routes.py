"""
TRANSPORT_ROUTES.PY - Routes pour le système de transport
========================================================

RESPONSABILITÉS:
- Gestion des constantes de transport
- Calcul des distances entre villes
- Création et gestion des transports
- Annulation des transports
- Liste des transports d'un joueur

ROUTES DISPONIBLES:
- GET /api/transport/constants           → Constantes de transport
- GET /api/transport/distance/<src>/<dst> → Distance entre villes
- GET /api/transports/player/<player_id> → Liste des transports
- POST /api/transport/create             → Créer un transport
- POST /api/transport/<id>/cancel        → Annuler un transport

DÉPENDANCES:
- city_constants.TRANSPORT_CONSTANTS pour les constantes
- DataManager pour accéder aux données
========================================================
"""

from flask import Blueprint, jsonify, request
import math
import os
import time
from app.data_manager import DataManager
from app.city_constants import TRANSPORT_CONSTANTS
from app.business.transport_service import TransportService

# Constantes des statuts de transport
TRANSPORT_STATES = {
    'WAITING': 'waiting',
    'LOADING': 'loading',
    'TRAVELING': 'traveling',
    'RETURNING': 'returning',
    'COMPLETED': 'completed'
}

transport_bp = Blueprint('transport', __name__)

def get_base_dir():
    """Obtient le répertoire de base du projet"""
    current_file = os.path.abspath(__file__)
    # __file__ = .../server/app/routes/transport_routes.py
    # Nous voulons aller jusqu'à .../server/
    return os.path.dirname(os.path.dirname(os.path.dirname(current_file)))

# Services à injecter
data_manager = None
transport_service = None

def init_transport_routes(dm):
    """Initialise les routes avec les services"""
    global data_manager, transport_service
    data_manager = dm
    transport_service = TransportService(dm)

@transport_bp.route('/api/transport/constants', methods=['GET'])
def get_transport_constants():
    """Récupère les constantes de transport depuis city_constants.py"""
    return jsonify({
        'transport_speed': TRANSPORT_CONSTANTS['STANDARD_SPEED'],
        'ship_capacity': TRANSPORT_CONSTANTS['SHIP_CAPACITY']
    })

@transport_bp.route('/api/transport/distance/<source_city_id>/<destination_city_id>', methods=['GET'])
def get_transport_distance(source_city_id, destination_city_id):
    """Calcule la distance entre deux villes"""
    try:
        # Utiliser l'instance globale ou créer une temporaire
        dm = data_manager if data_manager else DataManager(get_base_dir())
        
        # Charger l'univers pour obtenir les coordonnées
        universe = dm.load_universe()
        
        source_coords = None
        dest_coords = None
        source_island_id = None
        dest_island_id = None
        
        # Gestion spéciale pour les villages barbares
        def is_wild_camp(city_id):
            return city_id.startswith('wild_camp_')
        
        def get_island_id_from_barbarian(city_id):
            # wild_camp_2 -> island_id = "2"
            return city_id.replace('wild_camp_', '')
        
        # Trouver les coordonnées des villes
        for island in universe.get('islands', []):
            island_id = island['id']
            
            # Vérifier si la source est un village barbare
            if is_wild_camp(source_city_id):
                barbarian_island_id = get_island_id_from_barbarian(source_city_id)
                if island_id == barbarian_island_id:
                    source_coords = island['coords']
                    source_island_id = island_id
            
            # Vérifier si la destination est un village barbare  
            if is_wild_camp(destination_city_id):
                barbarian_island_id = get_island_id_from_barbarian(destination_city_id)
                if island_id == barbarian_island_id:
                    dest_coords = island['coords']
                    dest_island_id = island_id
            
            # Chercher les villes normales dans les éléments
            for element in island.get('elements', []):
                if element.get('type') == 'city':
                    if element['id'] == source_city_id:
                        source_coords = island['coords']
                        source_island_id = island_id
                    elif element['id'] == destination_city_id:
                        dest_coords = island['coords']
                        dest_island_id = island_id
        
        if not source_coords or not dest_coords:
            return jsonify({'error': 'Villes non trouvées'}), 404
        
        # Vérifier si les deux villes sont sur la même île
        if source_island_id and dest_island_id and source_island_id == dest_island_id:
            # Transport intra-île : temps fixe de 10 secondes
            return jsonify({
                'distance': 10.0,  # Distance symbolique
                'transport_time': 10.0,  # 10 secondes fixes
                'transport_speed': 1.0,  # Vitesse ajustée pour cohérence
                'same_island': True
            })
        
        # Calculer la distance euclidienne pour les transports inter-îles avec coefficient d'échelle
        dx = abs(source_coords[0] - dest_coords[0])
        dy = abs(source_coords[1] - dest_coords[1])
        raw_distance = math.sqrt(dx*dx + dy*dy)
        distance = raw_distance * TRANSPORT_CONSTANTS['DISTANCE_SCALE_FACTOR']
        
        # Calculer le temps de transport
        transport_speed = TRANSPORT_CONSTANTS['STANDARD_SPEED'] / 10
        transport_time = distance / transport_speed
        
        return jsonify({
            'distance': distance,
            'transport_time': transport_time,
            'transport_speed': transport_speed,
            'same_island': False
        })
        
    except Exception as e:
        print(f"❌ Erreur calcul distance: {e}")
        return jsonify({'error': 'Erreur calcul distance'}), 500

@transport_bp.route('/api/transports/player/<player_id>', methods=['GET'])
def get_player_transports(player_id):
    """Récupère la liste des transports d'un joueur"""
    try:
        # Charger les transports actifs
        dm = data_manager if data_manager else DataManager(get_base_dir())
        transports_data = dm.load_transports()
        
        # Filtrer les transports du joueur
        player_transports = [
            transport for transport in transports_data.get('transports', []) 
            if (transport.get('source_player_id') == player_id or 
                transport.get('player_id') == player_id or 
                transport.get('destination_player_id') == player_id)
        ]
        
        return jsonify({'transports': player_transports})
        
    except Exception as e:
        print(f"❌ Erreur récupération transports joueur {player_id}: {e}")
        return jsonify({'error': 'Erreur lors de la récupération des transports'}), 500

@transport_bp.route('/api/transport/create', methods=['POST'])
def create_transport():
    """Crée un nouveau transport"""
    try:
        if not transport_service:
            return jsonify({'error': 'Service de transport non initialisé'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Données JSON manquantes'}), 400
        
        # Extraire les paramètres requis
        required_fields = ['player_id', 'source_city_id', 'destination_city_id', 'resources', 
                          'ships_needed', 'loading_time', 'transport_time']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Champ manquant: {field}'}), 400
        
        # Créer le transport via le service
        result = transport_service.create_transport(
            player_id=data['player_id'],
            source_city_id=data['source_city_id'],
            destination_city_id=data['destination_city_id'],
            resources=data['resources'],
            ships_needed=data['ships_needed'],
            loading_time=data['loading_time'],
            travel_time=data['transport_time']
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'transport_id': result['transport_id'],
                'message': result['message']
            })
        else:
            return jsonify({'error': result['error']}), 400
        
    except Exception as e:
        print(f"❌ Erreur route create_transport: {e}")
        return jsonify({'error': 'Erreur serveur lors de la création du transport'}), 500

def _free_ships_for_player(data_manager, player_id: str, ships_count: int) -> bool:
    """Libère des bateaux pour un joueur donné."""
    try:
        players_data = data_manager.load_players()
        for player in players_data.get('players', []):
            if player['id'] == player_id:
                player['transport_ships_busy'] = max(0, player.get('transport_ships_busy', 0) - ships_count)
                break
        return data_manager.save_players(players_data, force_save=True)
    except Exception as e:
        print(f"❌ Erreur libération bateaux: {e}")
        return False

def _refund_resources_to_city(transport_service, city_id: str, resources: dict) -> bool:
    """Rembourse des ressources à une ville."""
    if not resources or not any(amount > 0 for amount in resources.values()):
        return True
    return transport_service._add_city_resources(city_id, resources)

def _remove_transport_from_list(transports_data: dict, transport_id: str):
    """Supprime un transport de la liste active."""
    transports_data['transports'] = [
        t for t in transports_data['transports'] 
        if t['id'] != transport_id
    ]

@transport_bp.route('/api/transport/<transport_id>/cancel', methods=['POST'])
def cancel_transport(transport_id):
    """Annule un transport existant"""
    try:
        data_manager = DataManager(get_base_dir())
        transport_service = TransportService(data_manager)
        
        # Charger les transports
        transports_data = data_manager.load_transports()
        transport_to_cancel = None
        
        # Trouver le transport à annuler
        for transport in transports_data.get('transports', []):
            if transport['id'] == transport_id:
                transport_to_cancel = transport
                break
        
        if not transport_to_cancel:
            return jsonify({'error': 'Transport non trouvé'}), 404
        
        # Vérifier si le transport peut être annulé
        if transport_to_cancel['status'] in [TRANSPORT_STATES['COMPLETED'], 'archived']:
            return jsonify({'error': 'Transport déjà terminé, impossible d\'annuler'}), 400
        
        # Variables communes
        source_player_id = transport_to_cancel['source_player_id']
        ships_to_free = transport_to_cancel['ships_needed']
        source_city_id = transport_to_cancel['source_city']
        
        # Gestion de l'annulation selon le statut
        if transport_to_cancel['status'] in [TRANSPORT_STATES['LOADING'], TRANSPORT_STATES['WAITING']]:
            # Cas 1: En attente ou chargement - Remboursement immédiat
            _refund_resources_to_city(transport_service, source_city_id, transport_to_cancel['resources'])
            _free_ships_for_player(data_manager, source_player_id, ships_to_free)
            _remove_transport_from_list(transports_data, transport_id)
            
        elif transport_to_cancel['status'] == TRANSPORT_STATES['TRAVELING']:
            # Cas 2: En voyage - Faire demi-tour
            current_time = time.time()
            
            # Calculer le temps de retour = temps déjà parcouru
            time_traveled = transport_to_cancel['travel_time'] - transport_to_cancel['remaining_time']
            return_time = time_traveled  # Le bateau fait demi-tour
            
            # Modifier le transport pour le faire rentrer
            transport_to_cancel['status'] = TRANSPORT_STATES['RETURNING']
            transport_to_cancel['remaining_time'] = return_time
            transport_to_cancel['last_update'] = current_time
            transport_to_cancel['timeline']['return_start'] = current_time
            transport_to_cancel['timeline']['travel_end'] = current_time  # Arrêt du voyage
            
            # Marquer comme annulé pour traitement spécial au retour
            transport_to_cancel['cancelled_return'] = True
            transport_to_cancel['initial_return_time'] = return_time  # Sauvegarder le temps de retour calculé
            transport_to_cancel['resources_to_refund'] = transport_to_cancel['resources'].copy()
            
        elif transport_to_cancel['status'] == TRANSPORT_STATES['RETURNING']:
            # Cas 3: En retour - Accélérer le retour et libérer immédiatement
            resources_to_refund = transport_to_cancel.get('resources_to_refund', transport_to_cancel['resources'])
            _refund_resources_to_city(transport_service, source_city_id, resources_to_refund)
            _free_ships_for_player(data_manager, source_player_id, ships_to_free)
            _remove_transport_from_list(transports_data, transport_id)
            
        else:
            # Statut non géré (completed, etc.)
            return jsonify({'error': f'Transport dans un état non annulable: {transport_to_cancel["status"]}'}), 400
        
        # Sauvegarder les transports mis à jour
        data_manager.save_transports(transports_data, force_save=True)
        
        # Préparer la réponse selon le type d'annulation
        if transport_to_cancel['status'] in [TRANSPORT_STATES['LOADING'], TRANSPORT_STATES['WAITING']]:
            return jsonify({
                'success': True, 
                'message': 'Transport annulé - Ressources et bateaux libérés immédiatement',
                'refunded_resources': transport_to_cancel['resources'],
                'freed_ships': ships_to_free,
                'immediate': True
            })
        elif transport_to_cancel.get('cancelled_return', False):
            return jsonify({
                'success': True,
                'message': f'Transport en demi-tour - Retour dans {transport_to_cancel["remaining_time"]:.1f}s',
                'return_time': transport_to_cancel['remaining_time'],
                'resources_will_be_refunded': transport_to_cancel['resources'],
                'immediate': False
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Transport annulé avec succès',
                'immediate': True
            })
        
    except Exception as e:
        print(f"❌ Erreur annulation transport: {e}")
        return jsonify({'error': 'Erreur lors de l\'annulation'}), 500


