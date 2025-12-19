from flask import Blueprint, jsonify
from app.transition_utils import load_savegame_transition

# Blueprint simple pour la vérification des villes
city_check_bp = Blueprint('city_check', __name__)

@city_check_bp.route('/api/check-city-ownership/<player_id>/<island_id>', methods=['GET'])
def check_city_ownership(player_id: str, island_id: str):
    """Vérifie si un joueur possède une ville sur une île"""
    try:
        # Charger via transition_utils pour utiliser le bon chemin (gamedata/)
        savegame = load_savegame_transition()
        if not savegame:
            return jsonify({'error': 'Impossible de charger les données', 'has_city': False, 'city_level': 1}), 500
        
        # Chercher une ville du joueur sur l'île
        player_city = None
        for city in savegame.get('cities', []):
            if city.get('owner') == player_id and city.get('island_id') == island_id:
                player_city = city
                break
        
        # Niveau par défaut si pas de ville ou pas de wild_camp_level
        city_level = 1
        if player_city:
            city_level = player_city.get('wild_camp_level', 1)
        
        return jsonify({
            'has_city': player_city is not None,
            'city_level': city_level
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'has_city': False, 'city_level': 1}), 500

