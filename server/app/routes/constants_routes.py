from flask import Blueprint, jsonify
import math
from app.data_manager import DataManager

constants_bp = Blueprint('constants', __name__)

# Routes temporaires pour que les popups transport fonctionnent
data_manager = DataManager()

@constants_bp.route('/api/transport/constants', methods=['GET'])
def get_transport_constants():
    """Route temporaire pour les constantes de transport"""
    return jsonify({
        'transport_speed': 10.0,  # unités/seconde
        'ship_capacity': 500      # ressources par bateau
    })

@constants_bp.route('/api/transport/distance/<source_city_id>/<destination_city_id>', methods=['GET'])
def get_transport_distance(source_city_id, destination_city_id):
    """Route temporaire pour calculer la distance entre deux villes"""
    try:
        # Charger l'univers pour obtenir les coordonnées
        universe = data_manager.load_universe()
        
        source_coords = None
        dest_coords = None
        
        # Trouver les coordonnées des villes
        for island in universe.get('islands', []):
            for city in island.get('cities', []):
                if city['id'] == source_city_id:
                    source_coords = island['coordinates']
                elif city['id'] == destination_city_id:
                    dest_coords = island['coordinates']
        
        if not source_coords or not dest_coords:
            return jsonify({'error': 'Villes non trouvées'}), 404
        
        # Calculer la distance euclidienne avec coefficient d'échelle
        from app.city_constants import TRANSPORT_CONSTANTS
        dx = abs(source_coords[0] - dest_coords[0])
        dy = abs(source_coords[1] - dest_coords[1])
        raw_distance = math.sqrt(dx*dx + dy*dy)
        distance = raw_distance * TRANSPORT_CONSTANTS['DISTANCE_SCALE_FACTOR']
        
        # Calculer le temps de transport
        transport_speed = 1.5  # Unités de distance par seconde
        transport_time = distance / transport_speed
        
        return jsonify({
            'distance': distance,
            'transport_time': transport_time,
            'transport_speed': transport_speed
        })
        
    except Exception as e:
        print(f"❌ Erreur calcul distance: {e}")
        return jsonify({'error': 'Erreur calcul distance'}), 500

@constants_bp.route('/api/transports/player/<player_id>', methods=['GET'])
def get_player_transports(player_id):
    """Route temporaire pour la liste des transports d'un joueur"""
    # Retourner une liste vide en attendant le nouveau système
    return jsonify([])

@constants_bp.route('/api/transport/create', methods=['POST'])
def create_transport():
    """Route temporaire pour la création de transport"""
    return jsonify({'error': 'Système de transport en cours de développement'}), 501


