"""
leaderboard_routes.py

ROUTES API POUR LE CLASSEMENT DES JOUEURS

ENDPOINTS:
    GET /api/leaderboard/<category>
        → Récupère le classement des joueurs pour une catégorie
        
CATÉGORIES:
    - general: Score total (construction + recherche + victoires*10)
    - construction: Points de construction
    - research: Points de recherche investis
    - military_xp: XP militaire gagnée
    - military_power: Puissance militaire (sum(quantity × xp_value) / 100)
    - units_killed: Unités ennemies tuées
    - units_lost: Unités perdues
    - victories: Nombre de victoires
    - quests: Points de quêtes accumulés
"""
from flask import Blueprint, jsonify
from app.data_manager import DataManager
from app.services.player_progression_service import PlayerProgressionService
import os

leaderboard_bp = Blueprint('leaderboard', __name__)

def get_base_dir():
    """Obtient le répertoire de base du projet"""
    current_file = os.path.abspath(__file__)
    return os.path.dirname(os.path.dirname(os.path.dirname(current_file)))


@leaderboard_bp.route('/api/leaderboard/<category>', methods=['GET'])
def get_leaderboard(category):
    """
    Récupère le classement des joueurs pour une catégorie donnée.
    
    Catégories disponibles:
    - general: Score total
    - construction: Points de construction
    - research: Points de recherche investis
    - military_xp: XP militaire
    - military_power: Puissance militaire
    - units_killed: Unités tuées
    - units_lost: Unités perdues
    - victories: Victoires
    - quests: Points de quêtes
    """
    try:
        data_manager = DataManager(get_base_dir())
        progression_service = PlayerProgressionService(data_manager)
        
        # Charger tous les joueurs
        players_data = data_manager.load_players()
        players = players_data.get('players', [])
        
        # Construire le classement
        leaderboard = []
        
        for player in players:
            player_id = player.get('id')
            username = player.get('username', 'Inconnu')
            
            # Calculer les scores en temps réel
            construction_points = progression_service.calculate_construction_points(player_id)
            research_points_invested = progression_service.calculate_research_points_invested(player_id)
            military_power = progression_service.calculate_military_power(player_id)
            
            # Récupérer les stats militaires
            military_xp = player.get('total_xp_gained', 0)
            units_killed = player.get('total_units_killed', 0)
            units_lost = player.get('total_units_lost', 0)
            victories = player.get('victories', 0)
            defeats = player.get('defeats', 0)
            
            # Points de quêtes
            quest_points = player.get('quest_points', 0)
            
            # Score général (pondéré)
            general_score = construction_points + research_points_invested + (victories * 10) + quest_points
            
            player_stats = {
                'player_id': player_id,
                'username': username,
                'general_score': general_score,
                'construction_points': construction_points,
                'research_points_invested': research_points_invested,
                'military_xp': military_xp,
                'military_power': military_power,
                'units_killed': units_killed,
                'units_lost': units_lost,
                'victories': victories,
                'defeats': defeats,
                'quest_points': quest_points
            }
            
            leaderboard.append(player_stats)
        
        # Trier selon la catégorie
        sort_key_map = {
            'general': 'general_score',
            'construction': 'construction_points',
            'research': 'research_points_invested',
            'military_xp': 'military_xp',
            'military_power': 'military_power',
            'units_killed': 'units_killed',
            'units_lost': 'units_lost',
            'victories': 'victories',
            'quests': 'quest_points'
        }
        
        sort_key = sort_key_map.get(category, 'general_score')
        leaderboard.sort(key=lambda x: x[sort_key], reverse=True)
        
        # Ajouter le rang
        for rank, player_stats in enumerate(leaderboard, start=1):
            player_stats['rank'] = rank
        
        return jsonify({
            'success': True,
            'category': category,
            'leaderboard': leaderboard
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }), 500
