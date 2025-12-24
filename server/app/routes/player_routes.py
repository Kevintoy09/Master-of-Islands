"""
Routes API pour les factions et statistiques
"""
from flask import Blueprint, jsonify
from ..data_manager import DataManager
import os

def get_base_dir():
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

faction_bp = Blueprint('faction', __name__)
data_manager = DataManager(get_base_dir())


@player_bp.route('/players/', methods=['GET'])
def get_all_players():
    """Retourne la liste de tous les joueurs"""
    try:
        players_data = data_manager.load_players()
        return jsonify(players_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@player_bp.route('/players/faction-stats', methods=['GET'])
def get_faction_stats():
    """
    Retourne les statistiques de répartition des factions.
    Exemple de réponse:
    {
      "stats": [
        {"faction": "stone", "count": 5, "percentage": 25.0},
        {"faction": "iron", "count": 8, "percentage": 40.0},
        {"faction": "cereal", "count": 4, "percentage": 20.0},
        {"faction": "papyrus", "count": 3, "percentage": 15.0}
      ],
      "total_players": 20
    }
    """
    try:
        players_data = data_manager.load_players()
        players = players_data.get('players', [])
        
        # Compter les joueurs par faction
        faction_counts = {
            'stone': 0,
            'iron': 0,
            'cereal': 0,
            'papyrus': 0
        }
        
        total_with_faction = 0
        for player in players:
            faction = player.get('faction')
            if faction and faction in faction_counts:
                faction_counts[faction] += 1
                total_with_faction += 1
        
        # Calculer les pourcentages
        stats = []
        for faction, count in faction_counts.items():
            percentage = (count / total_with_faction * 100) if total_with_faction > 0 else 0
            stats.append({
                'faction': faction,
                'count': count,
                'percentage': round(percentage, 2)
            })
        
        # Trier par nombre de joueurs (décroissant)
        stats.sort(key=lambda x: x['count'], reverse=True)
        
        return jsonify({
            'stats': stats,
            'total_players': total_with_faction,
            'total_all_players': len(players)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
