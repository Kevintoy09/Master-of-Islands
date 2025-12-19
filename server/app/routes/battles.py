from flask import Blueprint, jsonify, request
import json
import os
from datetime import datetime

battles_bp = Blueprint('battles', __name__)

def load_battlefields():
    """Charger les données des battlefields"""
    battlefields_path = os.path.join(os.path.dirname(__file__), '..', '..', 'gamedata', 'battlefields_v2.json')
    try:
        with open(battlefields_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def load_battles():
    """Charger les données des battles"""
    battles_path = os.path.join(os.path.dirname(__file__), '..', '..', 'gamedata', 'battlesv2.json')
    try:
        with open(battles_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def get_player_cities():
    """Charger les données des joueurs pour obtenir leurs villes"""
    players_path = os.path.join(os.path.dirname(__file__), '..', '..', 'gamedata', 'players.json')
    try:
        with open(players_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

@battles_bp.route('/api/battles/player/<player_id>', methods=['GET'])
def get_player_battles(player_id):
    """Récupérer toutes les batailles impliquant un joueur spécifique"""
    try:
        battlefields = load_battlefields()
        battles = load_battles()
        players = get_player_cities()
        
        player_battles = []
        
        for battlefield_id, battlefield in battlefields.items():
            # Vérifier si le joueur participe à cette bataille
            is_participant = (
                player_id in battlefield.get('participants', {}).get('attackers', []) or
                player_id in battlefield.get('participants', {}).get('defenders', [])
            )
            
            if is_participant:
                # Récupérer les informations détaillées de la bataille
                battle_data = battles.get(battlefield_id, {})
                
                # Déterminer le type de mission
                mission_type = "Attaque"
                if player_id in battlefield.get('participants', {}).get('defenders', []):
                    mission_type = "Défense"
                
                # Calculer les informations des transports et unités
                transport_ships = 0
                total_units = 0
                origin_city = "Inconnue"
                
                player_forces = battlefield.get('forces', {}).get('attackers', {}).get(player_id, {})
                if not player_forces:
                    player_forces = battlefield.get('forces', {}).get('defenders', {}).get(player_id, {})
                
                if player_forces and 'contributions' in player_forces:
                    for contribution in player_forces['contributions']:
                        transport_ships += contribution.get('transport_ships', 0)
                        for unit_type, count in contribution.get('units', {}).items():
                            total_units += count
                        
                        # Obtenir le nom de la ville d'origine
                        from_city_id = contribution.get('from_city', '')
                        if from_city_id and player_id in players:
                            player_data = players[player_id]
                            for city in player_data.get('cities', []):
                                if city.get('id') == from_city_id:
                                    origin_city = city.get('name', from_city_id)
                                    break
                
                # Destination
                destination = battlefield.get('location', 'Inconnue')
                if destination.startswith('wild_camp_'):
                    destination = f"Village Barbare {destination.split('_')[-1]}"
                
                battle_info = {
                    'battleId': battlefield_id,
                    'location': battlefield.get('location', ''),
                    'status': battlefield.get('status', 'unknown'),
                    'created_at': battlefield.get('created_at', 0),
                    'participants': battlefield.get('participants', {}),
                    'forces': battlefield.get('forces', {}),
                    'missionType': mission_type,
                    'origin': origin_city,
                    'destination': destination,
                    'transportShips': transport_ships,
                    'totalUnits': total_units
                }
                
                player_battles.append(battle_info)
        
        # Trier par date de création (plus récent en premier)
        player_battles.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'success': True,
            'battles': player_battles,
            'total': len(player_battles)
        })
        
    except Exception as e:
        print(f"Erreur lors de la récupération des batailles du joueur {player_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'battles': []
        }), 500
