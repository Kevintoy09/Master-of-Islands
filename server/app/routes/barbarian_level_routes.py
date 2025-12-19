"""
Route pour récupérer le vrai niveau d'un village barbare
"""

from flask import Blueprint, jsonify
from app.data_manager import DataManager
import os

barbarian_level_bp = Blueprint('barbarian_level', __name__)

@barbarian_level_bp.route('/api/barbarian-village-level-v2/<village_id>/<attacker_player_id>', methods=['GET'])
def get_wild_camp_level(village_id, attacker_player_id):
    """
    Récupère le vrai niveau d'un village barbare basé sur son ID et l'attaquant.
    Utilise le niveau original stocké dans la bataille en cours si disponible.
    
    Args:
        village_id: ID du village (format: wild_camp_7)
        attacker_player_id: ID du joueur qui attaque
    
    Returns:
        JSON avec le niveau réel du village (niveau original, pas celui incrémenté)
    """
    try:
        # Charger le data manager
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..')
        data_manager = DataManager(base_dir)
        
        # 1. Chercher d'abord dans les batailles (actives ET terminées) pour le niveau original
        battlefields_data = data_manager.load_battlefields_v2()
        
        for battlefield_id, battlefield in battlefields_data.items():
            if battlefield.get('wild_camp') == village_id or battlefield.get('location') == village_id:
                # Vérifier si l'attaquant fait partie de cette bataille
                attackers = battlefield.get('participants', {}).get('attackers', [])
                is_participant = any([
                    attacker_player_id in attackers,
                    str(attacker_player_id) in attackers,
                    f"player_{attacker_player_id}" in attackers
                ])
                
                if is_participant:
                    original_level = battlefield.get('original_barbarian_level')
                    if original_level is not None:
                        status = battlefield.get('status', 'unknown')
                        return jsonify({
                            'success': True,
                            'level': original_level,
                            'method': f'battle_original_level_{status}',
                            'village_id': village_id,
                            'attacker_player_id': attacker_player_id,
                            'battlefield_id': battlefield_id
                        })
        
        # 2. Si pas de bataille trouvée, charger le savegame traditionnel
        savegame = data_manager.load_savegame()
        
        if not savegame or 'cities' not in savegame:
            return jsonify({
                "success": False,
                "error": "Impossible de charger les données"
            }), 500
        
        # Extraire island_id depuis village_id: wild_camp_7 -> island_id = "7"
        island_id = None
        if village_id.startswith('wild_camp_'):
            village_parts = village_id.split('_')
            if len(village_parts) >= 3:
                island_id = village_parts[2]
        
        # Méthode principale: Chercher la ville DE L'ATTAQUANT sur cette île (même logique que battlefield_selector)
        if island_id and attacker_player_id:
            for city in savegame['cities']:
                if (str(city.get('island_id')) == str(island_id) and 
                    city.get('owner') == attacker_player_id and
                    'wild_camp_level' in city):
                    level = city['wild_camp_level']
                    return jsonify({
                        "success": True,
                        "village_id": village_id,
                        "level": level,
                        "method": "attacker_city_match",
                        "city_id": city.get('id'),
                        "attacker_player_id": attacker_player_id,
                        "island_id": island_id
                    })
        
        # Méthode 2: Si pas trouvé, chercher n'importe quelle ville sur cette île
        if island_id:
            for city in savegame['cities']:
                if (str(city.get('island_id')) == str(island_id) and 
                    'wild_camp_level' in city):
                    return jsonify({
                        "success": True,
                        "village_id": village_id,
                        "level": city['wild_camp_level'],
                        "method": "island_search",
                        "island_id": island_id,
                        "city_id": city.get('id')
                    })
        
        # Fallback: extraire niveau depuis le nom
        if village_id.startswith('wild_camp_'):
            try:
                village_parts = village_id.split('_')
                fallback_level = int(village_parts[2])
                return jsonify({
                    "success": True,
                    "village_id": village_id,
                    "level": fallback_level,
                    "method": "fallback_from_name"
                })
            except (ValueError, IndexError):
                pass
        
        return jsonify({
            "success": False,
            "error": f"Village barbare {village_id} non trouvé"
        }), 404
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur serveur: {str(e)}"
        }), 500

