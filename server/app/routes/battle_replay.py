# battle_replay.py
"""
API endpoint pour la gestion des replays de bataille
"""

from flask import Blueprint, jsonify, request
import json
import os
from datetime import datetime

battle_replay_bp = Blueprint('battle_replay', __name__)

def load_json_file(filename):
    """Charge un fichier JSON"""
    filepath = os.path.join('data', filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def save_json_file(filename, data):
    """Sauvegarde un fichier JSON"""
    filepath = os.path.join('data', filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@battle_replay_bp.route('/api/military/battle-replay/<battle_id>', methods=['GET'])
def get_battle_replay(battle_id):
    """
    Récupère les données de replay pour une bataille
    Regarde d'abord dans battle_replays.json, puis dans les fichiers actifs
    """
    try:
        # Essayer d'abord dans battle_replays.json (batailles archivées)
        replays = load_json_file('battle_replays.json')
        
        if battle_id in replays:
            return jsonify(replays[battle_id])
        
        # Si pas trouvé, essayer dans les données actives
        battlefields = load_json_file('battlefields_v2.json')
        battles = load_json_file('battlesv2.json')
        
        if battle_id not in battlefields:
            return jsonify({
                'error': f'Bataille {battle_id} non trouvée',
                'success': False
            }), 404
        
        battlefield = battlefields[battle_id]
        battle_history = battles.get(battle_id, {})
        
        # Construire les données de replay depuis les données actives
        replay_data = build_replay_from_active_data(battlefield, battle_history)
        
        return jsonify(replay_data)
        
    except Exception as e:
        print(f"Erreur lors du chargement du replay {battle_id}: {e}")
        return jsonify({
            'error': f'Erreur serveur: {str(e)}',
            'success': False
        }), 500

def build_replay_from_active_data(battlefield, battle_history):
    """
    Construit les données de replay depuis les données actives
    """
    # Métadonnées
    metadata = {
        'location': battlefield.get('location', 'Unknown'),
        'participants': battlefield.get('participants', {}),
        'result': battlefield.get('status', 'in_progress'),
        'date': battlefield.get('created_at', 0)
    }
    
    # Calculer les stats depuis les données actuelles
    attacker_stats = calculate_stats_from_teams(battle_history, 'player')
    defender_stats = calculate_stats_from_teams(battle_history, 'barbarian')
    
    # Construire le board_state depuis les teams actuelles
    board_state = {
        'units': battle_history.get('teams', {}),
        'current_round': battle_history.get('current_round', 1),
        'current_player': battle_history.get('current_player', 'player_4')
    }
    
    # Créer un seul round avec l'état actuel
    rounds = [{
        'round': battle_history.get('current_round', 1),
        'current_player': battle_history.get('current_player', 'player_4'),
        'turns': [{
            'player': battle_history.get('current_player', 'player_4'),
            'actions': [],
            'board_state': board_state,
            'attacker_stats': attacker_stats,
            'defender_stats': defender_stats
        }]
    }]
    
    return {
        'metadata': metadata,
        'rounds': rounds
    }

def calculate_stats_from_battlefield(battlefield, side):
    """Calcule les stats depuis les données de battlefield"""
    forces = battlefield.get('forces', {}).get(side, {})
    
    total_units = 0
    total_moral = 0
    
    for player_data in forces.values():
        if isinstance(player_data, dict):
            # Compter les unités
            units = player_data.get('units', {})
            for unit_type, count in units.items():
                if isinstance(count, int):
                    total_units += count
            
            # Moral (estimation basique)
            total_moral += player_data.get('moral', 100)
    
    return {
        'units': total_units,
        'moral': total_moral if total_moral > 0 else 100
    }

def calculate_stats_from_teams(battle_history, side_prefix):
    """Calcule les stats depuis les données teams dans battle_history"""
    teams = battle_history.get('teams', {})
    
    total_units = 0
    total_moral = 0  # Calculé à partir des vraies données
    
    # Parcourir toutes les équipes et chercher celles qui commencent par side_prefix
    for team_name, units in teams.items():
        if team_name.startswith(side_prefix):
            if isinstance(units, list):
                for unit in units:
                    if isinstance(unit, dict):
                        # Compter les unités
                        unit_count = unit.get('unitCount', 1)
                        if isinstance(unit_count, int):
                            total_units += unit_count
    
    return {
        'units': total_units,
        'moral': total_moral
    }

@battle_replay_bp.route('/api/military/archive-battle/<battle_id>', methods=['POST'])
def archive_battle(battle_id):
    """
    Archive une bataille terminée dans battle_replays.json
    """
    try:
        battlefields = load_json_file('battlefields_v2.json')
        battles = load_json_file('battlesv2.json')
        
        if battle_id not in battlefields:
            return jsonify({
                'error': f'Bataille {battle_id} non trouvée',
                'success': False
            }), 404
        
        # Construire les données de replay
        battlefield = battlefields[battle_id]
        battle_history = battles.get(battle_id, {})
        replay_data = build_replay_from_active_data(battlefield, battle_history)
        
        # Charger les replays existants
        replays = load_json_file('battle_replays.json')
        
        # Ajouter cette bataille
        replays[battle_id] = replay_data
        
        # Sauvegarder
        save_json_file('battle_replays.json', replays)
        
        return jsonify({
            'message': f'Bataille {battle_id} archivée avec succès',
            'success': True
        })
        
    except Exception as e:
        print(f"Erreur lors de l'archivage {battle_id}: {e}")
        return jsonify({
            'error': f'Erreur serveur: {str(e)}',
            'success': False
        }), 500