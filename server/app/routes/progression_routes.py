"""
progression_routes.py

ROUTES API POUR LA PROGRESSION DU JOUEUR

ENDPOINTS:
    GET  /api/progression/<player_id>
         → Récupère les scores de progression du joueur

    POST /api/progression/<player_id>/update
         → Recalcule et met à jour les scores du joueur
    
    POST /api/progression/update-all
         → Recalcule les scores de tous les joueurs (admin)

UTILISATION:
    - Appelé automatiquement après construction/recherche
    - Appelé manuellement pour voir le niveau du joueur
"""
from flask import Blueprint, jsonify
from app.services.player_progression_service import PlayerProgressionService
from app.data_manager import DataManager
import os

progression_bp = Blueprint('progression', __name__)

def get_base_dir():
    """Obtient le répertoire de base du projet"""
    current_file = os.path.abspath(__file__)
    return os.path.dirname(os.path.dirname(os.path.dirname(current_file)))


@progression_bp.route('/api/progression/<player_id>', methods=['GET'])
def get_player_progression(player_id):
    """
    Récupère les scores de progression du joueur.
    Calcule en temps réel sans modifier les données.
    """
    try:
        data_manager = DataManager(get_base_dir())
        progression_service = PlayerProgressionService(data_manager)
        
        scores = progression_service.get_player_level(player_id)
        
        return jsonify({
            'success': True,
            'player_id': player_id,
            'scores': scores
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }), 500


@progression_bp.route('/api/progression/<player_id>/update', methods=['POST'])
def update_player_progression(player_id):
    """
    Recalcule et met à jour les scores du joueur dans players.json.
    À appeler après construction ou recherche.
    """
    try:
        data_manager = DataManager(get_base_dir())
        progression_service = PlayerProgressionService(data_manager)
        
        result = progression_service.update_player_scores(player_id)
        
        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify(result), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }), 500


@progression_bp.route('/api/progression/update-all', methods=['POST'])
def update_all_players_progression():
    """
    Recalcule les scores de tous les joueurs.
    Utile pour initialiser le système ou faire une mise à jour globale.
    """
    try:
        data_manager = DataManager(get_base_dir())
        progression_service = PlayerProgressionService(data_manager)
        
        result = progression_service.update_all_players_scores()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }), 500
