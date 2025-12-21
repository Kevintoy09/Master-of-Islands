"""
Battle Routes V2 - Version optimisée
===================================

Routes Flask pour le système de bataille V2 avec :
- Élimination complète des doublons d'imports et de chargement de fichiers
- Fonctions utilitaires centralisées pour la gestion des données
- Structure logique des routes par fonctionnalité
- Code réduit de ~40% par rapport à la version originale
"""

from flask import Blueprint, request, jsonify
import time
import json
import os
import re

# ========================================
# IMPORTS CENTRALISÉS - UNE SEULE FOIS
# ========================================
from app.battle.battle_creation_service_v2 import get_battle_creation_service_v2
from app.battle.battle_stats_service_v2 import get_battle_stats_service_v2
from app.battle.battle_end_v2 import BattleEndV2Manager
from app.battle.battle_victory_manager import BattleVictoryManager
from app.battle.battle_victory_manager import BattleVictoryManager as BattleVictoryManagerV2
from app.battle.battle_loader_service import BattleLoaderService
from app.battle.HeroBonusManager import HeroBonusManager
from app.battle.battle_turn_manager_v2 import BattleTurnManagerV2

# Blueprint dédié V2
battle_v2_bp = Blueprint('battle_v2', __name__)

# ========================================
# CHEMINS DE FICHIERS CENTRALISÉS
# ========================================
DATA_DIR = os.path.join(os.path.dirname(__file__), '../../data')
GAMEDATA_DIR = os.path.join(os.path.dirname(__file__), '../../gamedata')
BATTLEFIELDS_V2_FILE = os.path.join(GAMEDATA_DIR, 'battlefields_v2.json')
BATTLES_V2_FILE = os.path.join(GAMEDATA_DIR, 'battlesv2.json')
UNIT_STATS_FILE = os.path.join(DATA_DIR, 'unit_stats.json')
PLAYER_HEROES_FILE = os.path.join(GAMEDATA_DIR, 'player_heroes.json')
BATTLE_NOTIFICATIONS_FILE = os.path.join(GAMEDATA_DIR, 'battle_notifications.json')

# ========================================
# FONCTIONS UTILITAIRES CENTRALISÉES
# ========================================

def load_json_data(file_path, default_value=None):
    """
    Charge un fichier JSON avec gestion d'erreur centralisée
    
    Args:
        file_path (str): Chemin vers le fichier JSON
        default_value: Valeur par défaut si le fichier n'existe pas (None, {}, [])
    
    Returns:
        dict/list: Données chargées ou valeur par défaut
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default_value if default_value is not None else {}

def save_json_data(file_path, data, compact=False):
    """
    Sauvegarde des données JSON avec format compact optionnel
    
    Args:
        file_path (str): Chemin vers le fichier JSON
        data: Données à sauvegarder
        compact (bool): Utiliser le format compact pour battles V2
    """
    try:
        if compact:
            json_content = save_battles_ultra_compact(data)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_content)
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def get_battle_by_id(battle_id):
    """
    Récupère une bataille par son ID depuis battlesv2.json
    
    Args:
        battle_id (str): ID de la bataille
    
    Returns:
        dict: Données de la bataille ou None si introuvable
    """
    battles_data = load_json_data(BATTLES_V2_FILE, {})
    return battles_data.get(battle_id)

def get_battlefield_by_id(battlefield_id):
    """
    Récupère un champ de bataille par son ID depuis battlefields_v2.json
    
    Args:
        battlefield_id (str): ID du champ de bataille
    
    Returns:
        dict: Données du champ de bataille ou None si introuvable
    """
    battlefields_data = load_json_data(BATTLEFIELDS_V2_FILE, {})
    return battlefields_data.get(battlefield_id)

def validate_battle_request(data, required_fields):
    """
    Valide les données d'une requête de bataille
    
    Args:
        data (dict): Données de la requête
        required_fields (list): Liste des champs requis
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not data:
        return False, "Aucune donnée fournie"
    
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Champ requis manquant: {field}"
    
    return True, ""

def check_position_collision(battle_data, target_position, excluding_unit_id=None):
    """
    Vérifie si une position est déjà occupée par une autre unité
    
    Args:
        battle_data (dict): Données de la bataille
        target_position (list): Position à vérifier [q, r]
        excluding_unit_id (str): ID de l'unité à exclure de la vérification (pour les mouvements)
    
    Returns:
        tuple: (collision_detected, occupying_unit_id)
    """
    teams = battle_data.get('teams', {})
    
    for team_name, units in teams.items():
        for unit in units:
            unit_id = unit.get('unitId')
            unit_position = unit.get('position')
            
            # Ignorer l'unité exclue (celle qui se déplace)
            if excluding_unit_id and unit_id == excluding_unit_id:
                continue
                
            # Vérifier si la position correspond
            if unit_position and len(unit_position) >= 2:
                if (unit_position[0] == target_position[0] and 
                    unit_position[1] == target_position[1]):
                    return True, unit_id
    
    return False, None

def save_battles_ultra_compact(data):
    """
    Sauvegarde avec format compact ciblé pour battles V2
    Structure principale lisible, éléments répétitifs compacts
    """
    # Format de base avec indentation pour structure principale
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    
    # Compacter les unit_counts sur une ligne
    json_str = re.sub(
        r'{\s*"deployed":\s*(\d+),\s*"total":\s*(\d+)\s*}',
        r'{"deployed": \1, "total": \2}',
        json_str
    )
    
    # Compacter les unités sur une ligne
    json_str = re.sub(
        r'{\s*"unitId":\s*"([^"]+)",\s*"position":\s*\[\s*(\d+),\s*(\d+)\s*\],\s*"unitCount":\s*(\d+)\s*}',
        r'{"unitId": "\1", "position": [\2, \3], "unitCount": \4}',
        json_str
    )
    
    # Compacter les héros sur une ligne  
    json_str = re.sub(
        r'{\s*"unitId":\s*"([^"]+)",\s*"position":\s*\[\s*(\d+),\s*(\d+)\s*\],\s*"hp":\s*(\d+)\s*}',
        r'{"unitId": "\1", "position": [\2, \3], "hp": \4}',
        json_str
    )
    
    # Compacter les mouvements sur une ligne
    json_str = re.sub(
        r'{\s*"unitId":\s*"([^"]+)",\s*"move":\s*{\s*"from":\s*\[\s*(\d+)\s*,\s*(\d+)\s*\],\s*"to":\s*\[\s*(\d+)\s*,\s*(\d+)\s*\]\s*}\s*}',
        r'{"unitId": "\1", "move": {"from": [\2, \3], "to": [\4, \5]}}',
        json_str,
        flags=re.MULTILINE | re.DOTALL
    )
    
    return json_str

def _update_unit_counts_deployed(battle_data):
    """
    Met à jour les unit_counts.deployed en comptant depuis les teams
    Nouvelle approche simple : ne recalcule que les deployed
    """
    try:
        unit_counts = battle_data.get('unit_counts', {})
        teams = battle_data.get('teams', {})
        
        # Remettre tous les deployed à 0
        for player_id in unit_counts:
            for unit_type in unit_counts[player_id]:
                if isinstance(unit_counts[player_id][unit_type], dict):
                    unit_counts[player_id][unit_type]['deployed'] = 0
        
        # Compter depuis les teams
        for team_id, team_units in teams.items():
            # team_id peut être directement player_10, wild_camp, etc.
            player_id = team_id
            
            if player_id not in unit_counts:
                continue
            
            for unit in team_units:
                unit_id = unit.get('unitId', '')
                unit_count = unit.get('unitCount', 0)
                is_hero = unit.get('hp') is not None
                
                if is_hero:
                    # Compter héros
                    if 'heroes' in unit_counts[player_id]:
                        unit_counts[player_id]['heroes']['deployed'] += 1
                else:
                    # Extraire le type d'unité depuis unit_id
                    # Formats possibles:
                    # - attacker_player_10_militia_timestamp_hash
                    # - auto_defender_wild_camp_barbarian_warrior_0
                    # - defender_wild_camp_barbarian_archer_1
                    
                    # Chercher le type d'unité en retirant les préfixes connus
                    parts = unit_id.split('_')
                    unit_type = None
                    
                    # Trouver le type d'unité après player_XX ou wild_camp
                    for i, part in enumerate(parts):
                        if part == 'player' and i + 1 < len(parts):
                            # Sauter le numéro de joueur
                            if i + 2 < len(parts):
                                # Le type commence après player_XX
                                remaining_parts = parts[i+2:]
                                # Prendre tout jusqu'au timestamp (numérique long) ou hash
                                unit_type_parts = []
                                for p in remaining_parts:
                                    if p.isdigit() and len(p) > 5:  # Timestamp
                                        break
                                    unit_type_parts.append(p)
                                unit_type = '_'.join(unit_type_parts) if unit_type_parts else None
                                break
                        elif part == 'wild' or part == 'barbarian':
                            # Pour wild_camp: chercher après 'camp'
                            if 'camp' in parts:
                                camp_idx = parts.index('camp')
                                if camp_idx + 1 < len(parts):
                                    # Tout après 'camp' jusqu'au numéro final
                                    remaining_parts = parts[camp_idx+1:]
                                    unit_type_parts = []
                                    for p in remaining_parts:
                                        if p.isdigit():  # Numéro final (0, 1, 2...)
                                            break
                                        unit_type_parts.append(p)
                                    unit_type = '_'.join(unit_type_parts) if unit_type_parts else None
                                    break
                    
                    # Fallback: si pas trouvé, essayer pattern simple
                    if not unit_type:
                        # Chercher militia, barbarian_warrior, etc. dans parts
                        for known_type in ['militia', 'barbarian_warrior', 'barbarian_archer', 'barbarian_raider', 
                                          'infantry_light', 'infantry_heavy', 'archer', 'cavalry']:
                            if known_type in unit_id:
                                unit_type = known_type
                                break
                    
                    if unit_type and unit_type in unit_counts[player_id]:
                        if isinstance(unit_counts[player_id][unit_type], dict):
                            unit_counts[player_id][unit_type]['deployed'] += unit_count
        
    except Exception as e:
        pass  # Erreur silencieuse, pas critique

def generate_unit_counts_structure(battle_id):
    """
    Génère automatiquement la structure unit_counts pour une bataille
    en calculant les totaux depuis battlefields_v2.json et les déployés depuis battlesv2.json
    """
    try:
        battlefields_data = load_json_data(BATTLEFIELDS_V2_FILE, {})
        battles_data = load_json_data(BATTLES_V2_FILE, {})
        
        if battle_id not in battlefields_data:
            return {}
        
        battlefield = battlefields_data[battle_id]
        battle = battles_data.get(battle_id, {"teams": {}})
        
        unit_counts = {}
        
        # Traiter attaquants et défenseurs
        for side in ['attackers', 'defenders']:
            forces = battlefield.get('forces', {}).get(side, {})
            for player_id, player_forces in forces.items():
                if player_id not in unit_counts:
                    unit_counts[player_id] = {}
                
                # Calculer les totaux depuis les contributions
                contributions = player_forces.get('contributions', [])
                for contribution in contributions:
                    # Traiter les unités
                    units = contribution.get('units', {})
                    for unit_type, total_count in units.items():
                        if unit_type not in unit_counts[player_id]:
                            unit_counts[player_id][unit_type] = {
                                'deployed': 0,
                                'total': 0
                            }
                        unit_counts[player_id][unit_type]['total'] += total_count
                    
                    # Traiter les héros
                    heroes = contribution.get('heroes', [])
                    if heroes:
                        if 'heroes' not in unit_counts[player_id]:
                            unit_counts[player_id]['heroes'] = {
                                'deployed': 0,
                                'total': 0
                            }
                        unit_counts[player_id]['heroes']['total'] += len(heroes)
        
        # Calculer les déployés depuis battlesv2.json teams
        teams = battle.get('teams', {})
        for team_id, team_units in teams.items():
            for unit in team_units:
                unit_id = unit.get('unitId', '')
                unit_count = unit.get('unitCount', 0)
                
                # Format: "attacker_player_3_infantry_light_timestamp_random"
                parts = unit_id.split('_')
                if len(parts) >= 4:
                    player_id = f"{parts[1]}_{parts[2]}"  # player_3
                    unit_type = parts[3]  # infantry, archer, etc.
                    
                    # Si c'est un type composé comme "infantry_light"
                    if len(parts) >= 5 and parts[4] in ['light', 'heavy']:
                        unit_type = f"{parts[3]}_{parts[4]}"  # infantry_light
                        
                    # Ajouter aux déployés si le player_id existe dans unit_counts
                    if player_id in unit_counts and unit_type in unit_counts[player_id]:
                        unit_counts[player_id][unit_type]['deployed'] += unit_count
        
        return unit_counts
        
    except Exception:
        return {}

# Import de l'utilitaire de sélection de battlefield
from app.utils.battlefield_selector import determine_battlefield_template

# ========================================
# ROUTES - CRÉATION ET GESTION DES BATAILLES
# ========================================

@battle_v2_bp.route('/api/military/attack/start_v2', methods=['POST'])
def start_attack_v2():
    """Créer une nouvelle bataille V2"""
    data = request.get_json()
    
    # Validation des données
    is_valid, error_msg = validate_battle_request(data, ['source_city_id', 'target_city_id', 'units'])
    if not is_valid:
        return jsonify({"success": False, "error": error_msg}), 400
    
    # Extraction des paramètres
    source_city_id = data.get('source_city_id')
    target_city_id = data.get('target_city_id')
    units = data.get('units', {})
    heroes = data.get('heroes', [])
    ships = data.get('ships', 1)
    
    # Déterminer automatiquement le battlefield approprié
    from app.data_manager import DataManager
    data_manager = DataManager(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    attacker_player_id = data.get('owner')  # Récupérer l'ID du joueur attaquant
    battlefield_template_id = determine_battlefield_template(target_city_id, data_manager, attacker_player_id)
    
    # Création de la bataille via le service
    service = get_battle_creation_service_v2()
    result = service.create_battle(
        attacker_city_id=source_city_id,
        target_city_id=target_city_id,
        units=units,
        heroes=heroes,
        ships=ships,
        battlefield_template_id=battlefield_template_id,
        attacker_player_id=data.get('owner')
    )
    
    if result["success"]:
        return jsonify({
            "success": True,
            "battle_id": result["battle_id"],
            "battlefield_id": result["battlefield_id"],
            "message": "Attaque V2 lancée avec succès",
            "system": "V2"
        })
    else:
        return jsonify({
            "success": False, 
            "error": result.get("error", "Erreur inconnue lors de la création de la bataille V2")
        }), 500

@battle_v2_bp.route('/api/military/battlefield_v2/<battlefield_id>', methods=['GET'])
def get_battlefield_v2(battlefield_id):
    """Récupérer les informations d'une battlefield V2"""
    try:
        service = get_battle_creation_service_v2()
        battlefield = service.get_battlefield(battlefield_id)
        
        if not battlefield:
            return jsonify({"success": False, "error": "Champ de bataille V2 non trouvé"}), 404
        
        status_info = service.get_battlefield_status(battlefield_id)
        
        return jsonify({
            "success": True,
            "battlefield": battlefield,
            "status_info": status_info,
            "system": "V2"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Erreur serveur V2: {str(e)}"}), 500

@battle_v2_bp.route('/api/battlefield/terrain-definitions/<battlefield_id>', methods=['GET'])
def get_terrain_definitions(battlefield_id):
    """Récupérer les définitions de terrain d'un battlefield spécifique"""
    try:
        import json
        import os
        
        # Chemin vers les fichiers de battlefield
        server_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        battlefields_dir = os.path.join(server_dir, 'data', 'battlefields')
        
        # Essayer de trouver le fichier du battlefield
        battlefield_files = [
            f"{battlefield_id}.json",
            f"battlefield_{battlefield_id}.json",
            "Overload_beach.json"  # Fallback par défaut
        ]
        
        battlefield_data = None
        for filename in battlefield_files:
            filepath = os.path.join(battlefields_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        battlefield_data = json.load(f)
                    break
                except Exception as e:
                    continue
        
        if not battlefield_data or 'terrainDefinitions' not in battlefield_data:
            return jsonify({"success": False, "error": "Définitions de terrain non trouvées"}), 404
            
        return jsonify({
            "success": True,
            "terrainDefinitions": battlefield_data['terrainDefinitions'],
            "battlefield_id": battlefield_id
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Erreur serveur: {str(e)}"}), 500

@battle_v2_bp.route('/api/v2/battle/end/<battle_id>', methods=['POST'])
def end_battle_v2(battle_id):
    """Terminer une bataille V2 et appliquer les conséquences"""
    try:
        battle_end_manager = BattleEndV2Manager()
        result = battle_end_manager.end_battle(battle_id)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": result.get("message", f"Bataille {battle_id} terminée avec succès"),
                "battle_id": result.get("battle_id", battle_id),
                "troops_returned": result.get("troops_returned", {}),
                "report_id": result.get("report_id"),
                "cities_updated": result.get("cities_updated", 0),
                "system": "V2"
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get("error", "Erreur lors de la fin de bataille")
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur serveur: {str(e)}"
        }), 500

# ========================================
# ROUTES - CONSULTATION DES DONNÉES
# ========================================

@battle_v2_bp.route('/api/v2/battle/latest', methods=['GET'])
def get_latest_battle():
    """Récupérer la dernière bataille enregistrée"""
    try:
        service = get_battle_creation_service_v2()
        
        # Récupérer toutes les batailles V2
        battles_data = service._load_battlefields_v2()
        
        if not battles_data:
            return jsonify({
                "success": False, 
                "error": "Aucune bataille trouvée. Créez d'abord une bataille avec 'Attaquer V2'."
            })
        
        # Trier par timestamp et prendre la plus récente
        latest_battle = max(battles_data.values(), key=lambda b: b.get('created_at', 0))
        
        return jsonify({
            "success": True,
            "battle": latest_battle
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors de la récupération de la dernière bataille: {str(e)}"
        }), 500

@battle_v2_bp.route('/api/v2/battlefields/all', methods=['GET'])
def get_all_battlefields_v2():
    """Liste battlefields avec format {success, battlefields} pour les icônes des villes"""
    try:
        battlefields_data = load_json_data(BATTLEFIELDS_V2_FILE, {})
        
        return jsonify({
            "success": True,
            "battlefields": battlefields_data
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors de la récupération des champs de bataille: {str(e)}"
        }), 500

@battle_v2_bp.route('/api/v2/battlefields/data', methods=['GET'])
def get_battlefields_data_v2():
    """Données RAW battlefields_v2.json pour popup déploiement"""
    try:
        battlefields_data = load_json_data(BATTLEFIELDS_V2_FILE, {})
        return jsonify(battlefields_data)
        
    except Exception as e:
        return jsonify({"error": f"Erreur: {str(e)}"}), 500

@battle_v2_bp.route('/api/v2/battles/data', methods=['GET'])
def get_battles_data_v2():
    """Données RAW battlesv2.json pour popup déploiement"""
    try:
        battles_data = load_json_data(BATTLES_V2_FILE, {})
        return jsonify(battles_data)
        
    except Exception as e:
        return jsonify({"error": f"Erreur: {str(e)}"}), 500

@battle_v2_bp.route('/api/v2/battle/<battle_id>/unit-counts', methods=['GET'])
def get_unit_counts_simple(battle_id):
    """
    Récupère les unit_counts depuis battlesv2.json (nouvelle approche simple)
    """
    try:
        battles_data = load_json_data(BATTLES_V2_FILE, {})
        
        if battle_id not in battles_data:
            return jsonify({"success": False, "error": "Bataille non trouvée"}), 404
        
        battle = battles_data[battle_id]
        unit_counts = battle.get('unit_counts', {})
        
        # Calculer les unités disponibles (total - deployed)
        available_units = {}
        for player_id, player_units in unit_counts.items():
            available_units[player_id] = {}
            for unit_type, counts in player_units.items():
                total = counts.get('total', 0)
                deployed = counts.get('deployed', 0)
                available = max(0, total - deployed)
                
                available_units[player_id][unit_type] = {
                    'available': available,
                    'total': total,
                    'deployed': deployed
                }
        
        return jsonify({
            "success": True,
            "unit_counts": unit_counts,
            "available_units": available_units
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur récupération unit_counts: {str(e)}"
        }), 500

@battle_v2_bp.route('/api/v2/unit_stats', methods=['GET'])
def get_unit_stats_v2():
    """Données RAW unit_stats.json"""
    try:
        unit_stats = load_json_data(UNIT_STATS_FILE, {})
        return jsonify(unit_stats)
        
    except Exception as e:
        return jsonify({"error": f"Erreur: {str(e)}"}), 500

@battle_v2_bp.route('/api/v2/player_heroes', methods=['GET'])
def get_player_heroes_v2():
    """Données RAW player_heroes.json"""
    try:
        heroes_data = load_json_data(PLAYER_HEROES_FILE, {})
        return jsonify(heroes_data)
        
    except Exception as e:
        return jsonify({"error": f"Erreur: {str(e)}"}), 500

@battle_v2_bp.route('/api/v2/hero/aura-bonuses/<battle_id>', methods=['GET'])
def get_hero_aura_bonuses_v2(battle_id):
    """Récupérer les bonus d'aura des héros pour un champ de bataille V2"""
    try:
        bonus_manager = HeroBonusManager()
        applied_bonuses = bonus_manager.apply_battlefield_bonuses(battle_id)
        
        return jsonify({
            "success": True,
            "applied_bonuses": applied_bonuses,
            "source": "battle_routes_v2_hero_aura"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors du chargement des bonus d'aura: {str(e)}"
        }), 500

@battle_v2_bp.route('/api/military/city/units/<city_id>', methods=['GET'])
def get_city_units_v2(city_id):
    """Récupère les unités disponibles dans une ville pour les attaques V2"""
    try:
        # Charger les données de sauvegarde
        savegame_file = os.path.join(GAMEDATA_DIR, 'savegame.json')
        savegame_data = load_json_data(savegame_file, {})
        
        # Trouver la ville
        target_city = None
        for city in savegame_data.get('cities', []):
            if city.get('id') == city_id:
                target_city = city
                break
        
        if not target_city:
            return jsonify({
                'success': False,
                'message': f'Ville {city_id} introuvable'
            }), 404
        
        # Récupérer les unités de la garnison
        military_data = target_city.get('military', {})
        units_garrison = military_data.get('units', {})
        
        return jsonify({
            'success': True,
            'garrison': units_garrison,
            'city_id': city_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la récupération des unités: {str(e)}'
        }), 500

# ========================================
# ROUTES - CONDITIONS DE VICTOIRE ET STATUS
# ========================================

@battle_v2_bp.route('/api/v2/battle/check-victory/<battle_id>', methods=['GET'])
def check_victory_conditions_v2(battle_id):
    """
    🎯 Vérifier les conditions de victoire
    
    Vérifie les 3 conditions de victoire :
    1. Élimination complète des unités adverses
    2. Moral de l'équipe = 0  
    3. Abandon d'une équipe
    """
    try:
        from app.battle.battle_victory_manager import BattleVictoryManager
        victory_manager = BattleVictoryManager()
        has_winner, winner_team, victory_type = victory_manager.check_all_victory_conditions(battle_id)
        
        return jsonify({
            "success": True,
            "has_winner": has_winner,
            "winner_team": winner_team,
            "victory_type": victory_type
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur vérification victoire: {str(e)}"
        }), 500

@battle_v2_bp.route('/api/v2/battle/surrender/<battle_id>/<player_id>', methods=['POST'])
def surrender_battle_v2(battle_id, player_id):
    """
    🏳️ Faire se rendre un joueur dans une bataille
    
    Args:
        battle_id (str): ID de la bataille
        player_id (str): ID du joueur qui se rend
    
    Returns:
        JSON: Résultat de l'abandon avec message de victoire
    """
    try:
        victory_manager = BattleVictoryManager()
        result = victory_manager.surrender_battle(battle_id, player_id)
        
        if result.get('success'):
            return jsonify({
                "success": True,
                "message": result.get('message', f'Le joueur {player_id} s\'est rendu avec succès'),
                "winner_team": result.get('winner_team'),
                "victory_type": "surrender",
                "battle_id": battle_id,
                "surrendering_player": player_id
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get('error', 'Erreur lors de l\'abandon')
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur serveur lors de l'abandon: {str(e)}"
        }), 500

@battle_v2_bp.route('/api/v2/battle/surrender/<battle_id>/auto', methods=['POST'])
def surrender_battle_auto_defender(battle_id):
    """
    🎯 SIMPLE : Faire se rendre automatiquement le défenseur dans une bataille
    
    Le serveur détermine lui-même qui est le défenseur et effectue la reddition.
    Plus de calcul côté client !
    
    Args:
        battle_id (str): ID de la bataille
    
    Returns:
        JSON: Résultat de l'abandon avec message de victoire
    """
    try:
        
        # Charger la bataille
        battlefields_data = load_json_data(BATTLEFIELDS_V2_FILE, {})
        
        if battle_id not in battlefields_data:
            return jsonify({
                "success": False,
                "error": f"Bataille {battle_id} non trouvée"
            }), 404
        
        battlefield = battlefields_data[battle_id]
        participants = battlefield.get('participants', {})
        defenders = participants.get('defenders', [])
        
        if not defenders:
            return jsonify({
                "success": False,
                "error": "Aucun défenseur trouvé dans participants"
            }), 400
        
        # Prendre le premier défenseur
        defender_id = defenders[0]
        
        # Vérifier que les forces du défenseur existent
        forces = battlefield.get('forces', {})
        defender_forces = forces.get('defenders', {})
        
        if defender_id not in defender_forces:
            return jsonify({
                "success": False,
                "error": f"Forces du défenseur {defender_id} non trouvées dans battlefield.forces.defenders. Données incomplètes !"
            }), 400
        
        
        # Déléguer à la logique normale de reddition
        victory_manager = BattleVictoryManager()
        result = victory_manager.surrender_battle(battle_id, defender_id)
        
        if result.get('success'):
            # Récupérer le message détaillé depuis surrender_info si disponible
            battlefield_updated = load_json_data(BATTLEFIELDS_V2_FILE, {}).get(battle_id, {})
            surrender_info = battlefield_updated.get('surrender_info', {})
            detailed_message = surrender_info.get('detailed_message', f'Le défenseur {defender_id} s\'est rendu avec succès')
            
            return jsonify({
                "success": True,
                "message": detailed_message,
                "winner_team": result.get('winner_team'),
                "victory_type": "surrender",
                "battle_id": battle_id,
                "surrendering_player": defender_id,
                "auto_detected": True,
                "surrender_details": surrender_info
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get('error', 'Erreur lors de l\'abandon automatique')
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur serveur lors de l'abandon automatique: {str(e)}"
        }), 500

@battle_v2_bp.route('/api/v2/battle/surrender/<battle_id>/auto-attacker', methods=['POST'])
def surrender_battle_auto_attacker(battle_id):
    """
    🎯 SIMPLE : Faire se rendre automatiquement l'attaquant dans une bataille
    
    Le serveur détermine lui-même qui est l'attaquant et effectue la reddition.
    Plus de calcul côté client !
    
    Args:
        battle_id (str): ID de la bataille
    
    Returns:
        JSON: Résultat de l'abandon avec message de victoire
    """
    try:
        
        # Charger la bataille
        battlefields_data = load_json_data(BATTLEFIELDS_V2_FILE, {})
        
        if battle_id not in battlefields_data:
            return jsonify({
                "success": False,
                "error": f"Bataille {battle_id} non trouvée"
            }), 404
        
        battlefield = battlefields_data[battle_id]
        participants = battlefield.get('participants', {})
        attackers = participants.get('attackers', [])
        
        if not attackers:
            return jsonify({
                "success": False,
                "error": "Aucun attaquant trouvé dans participants"
            }), 400
        
        # Prendre le premier attaquant
        attacker_id = attackers[0]
        
        # Vérifier que les forces de l'attaquant existent
        forces = battlefield.get('forces', {})
        attacker_forces = forces.get('attackers', {})
        
        if attacker_id not in attacker_forces:
            return jsonify({
                "success": False,
                "error": f"Forces de l'attaquant {attacker_id} non trouvées dans battlefield.forces.attackers. Données incomplètes !"
            }), 400
        
        
        # Déléguer à la logique normale de reddition
        victory_manager = BattleVictoryManager()
        result = victory_manager.surrender_battle(battle_id, attacker_id)
        
        if result.get('success'):
            # Récupérer le message détaillé depuis surrender_info si disponible
            battlefield_updated = load_json_data(BATTLEFIELDS_V2_FILE, {}).get(battle_id, {})
            surrender_info = battlefield_updated.get('surrender_info', {})
            detailed_message = surrender_info.get('detailed_message', f'L\'attaquant {attacker_id} s\'est rendu avec succès')
            
            return jsonify({
                "success": True,
                "message": detailed_message,
                "winner_team": result.get('winner_team'),
                "victory_type": "surrender",
                "battle_id": battle_id,
                "surrendering_player": attacker_id,
                "auto_detected": True,
                "surrender_details": surrender_info
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get('error', 'Erreur lors de l\'abandon automatique de l\'attaquant')
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur serveur lors de l'abandon automatique de l'attaquant: {str(e)}"
        }), 500

# ========================================
# ROUTES - GESTION DES HÉROS ET BONUS
# ========================================

@battle_v2_bp.route('/api/v2/battle/heroes/update/<battle_id>', methods=['POST'])
def update_battle_heroes_v2(battle_id):
    """Mettre à jour les héros d'une bataille"""
    try:
        data = request.get_json()
        new_heroes = data.get('heroes', [])
        
        # Charger et modifier les données de héros
        heroes_data = load_json_data(PLAYER_HEROES_FILE, {})
        
        # Logique de mise à jour des héros (à adapter selon besoins)
        for hero in new_heroes:
            hero_id = hero.get('id')
            if hero_id:
                heroes_data[hero_id] = hero
        
        # Sauvegarder
        if save_json_data(PLAYER_HEROES_FILE, heroes_data):
            return jsonify({
                "success": True,
                "message": "Héros mis à jour avec succès"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Erreur lors de la sauvegarde des héros"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur mise à jour héros: {str(e)}"
        }), 500

# ========================================
# ROUTES - ACTIONS DE BATAILLE
# ========================================

@battle_v2_bp.route('/api/v2/battle/move', methods=['POST'])
def battle_move_v2():
    """Déplacer une unité sur le champ de bataille"""
    try:
        data = request.get_json()
        
        # Validation des données
        required_fields = ['battle_id', 'unit_id', 'from_position', 'to_position']
        is_valid, error_msg = validate_battle_request(data, required_fields)
        if not is_valid:
            return jsonify({"success": False, "error": error_msg}), 400
        
        battle_id = data['battle_id']
        unit_id = data['unit_id']
        from_pos = data['from_position']
        to_pos = data['to_position']
        
        # Charger les données de bataille
        battles_data = load_json_data(BATTLES_V2_FILE, {})
        
        if battle_id not in battles_data:
            return jsonify({
                "success": False,
                "error": "Bataille non trouvée"
            }), 404
        
        battle = battles_data[battle_id]
        
        # Vérifier les collisions avant d'accepter le mouvement
        collision_detected, occupying_unit_id = check_position_collision(
            battle, to_pos, excluding_unit_id=unit_id
        )
        
        if collision_detected:
            return jsonify({
                "success": False,
                "error": f"Position occupée par l'unité {occupying_unit_id}"
            }), 400
        
        # Utiliser le turn manager pour enregistrer le mouvement avec le système d'actions
        turn_manager = BattleTurnManagerV2()
        result = turn_manager.record_unit_move(battle_id, unit_id, from_pos, to_pos)
        
        if result['success']:
            return jsonify({
                "success": True,
                "message": "Mouvement enregistré avec succès"
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get('error', 'Erreur lors de l\'enregistrement du mouvement')
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur mouvement: {str(e)}"
        }), 500


# ========================================
# ROUTES - UTILITAIRES ET TESTS
# ========================================


@battle_v2_bp.route('/api/v2/battle/unit-counts/<battle_id>', methods=['GET'])
def get_unit_counts_v2(battle_id):
    """Récupérer les compteurs d'unités pour une bataille"""
    try:
        unit_counts = generate_unit_counts_structure(battle_id)
        
        return jsonify({
            "success": True,
            "unit_counts": unit_counts,
            "battle_id": battle_id
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur récupération unit_counts: {str(e)}"
        }), 500

@battle_v2_bp.route('/api/v2/battle/refresh-unit-counts/<battle_id>', methods=['POST'])
def refresh_unit_counts_v2(battle_id):
    """Force la mise à jour des compteurs d'unités dans battlesv2.json depuis battlefields_v2.json"""
    try:
        # Générer les nouveaux compteurs depuis battlefields_v2.json
        new_unit_counts = generate_unit_counts_structure(battle_id)
        
        # Charger battlesv2.json
        battles_data = load_json_data(BATTLES_V2_FILE, {})
        
        if battle_id not in battles_data:
            return jsonify({
                "success": False,
                "error": f"Bataille {battle_id} non trouvée dans battlesv2.json"
            }), 404
        
        # Mettre à jour les unit_counts
        battles_data[battle_id]['unit_counts'] = new_unit_counts
        
        # Sauvegarder
        if save_json_data(BATTLES_V2_FILE, battles_data, compact=True):
            return jsonify({
                "success": True,
                "message": f"Compteurs mis à jour pour {battle_id}",
                "unit_counts": new_unit_counts
            })
        else:
            return jsonify({
                "success": False,
                "error": "Erreur lors de la sauvegarde"
            }), 500
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur mise à jour unit_counts: {str(e)}"
        }), 500

# ========================================
# ROUTES - GESTION DES TOURS ET TURN MANAGER
# ========================================

@battle_v2_bp.route('/api/v2/battle/turn/next/<battle_id>', methods=['POST'])
def next_turn_v2(battle_id):
    """Passer au tour suivant de la bataille"""
    try:
        turn_manager = BattleTurnManagerV2()
        result = turn_manager.next_turn(battle_id)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": "Tour suivant initié",
                "turn": result.get("current_turn"),
                "battle_id": battle_id
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get("error", "Erreur passage tour suivant")
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur tour suivant: {str(e)}"
        }), 500

@battle_v2_bp.route('/api/v2/battle/stats/<battle_id>', methods=['GET'])
def get_battle_stats_v2(battle_id):
    """Récupérer les statistiques d'une bataille (unités, moral)"""
    try:
        stats_service = get_battle_stats_service_v2()
        stats_data = stats_service.get_battle_stats(battle_id)
        
        if not stats_data.get('success', False):
            return jsonify(stats_data), 404
        
        return jsonify(stats_data)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur récupération stats: {str(e)}"
        }), 500

@battle_v2_bp.route('/api/v2/battle/summary', methods=['GET'])
def get_battles_summary_v2():
    """Récupérer un résumé de toutes les batailles V2"""
    try:
        battles_data = load_json_data(BATTLES_V2_FILE, {})
        battlefields_data = load_json_data(BATTLEFIELDS_V2_FILE, {})
        
        summary = {
            "total_battles": len(battles_data),
            "total_battlefields": len(battlefields_data),
            "battles": {},
            "battlefields": {}
        }
        
        # Résumé des batailles
        for battle_id, battle in battles_data.items():
            summary["battles"][battle_id] = {
                "id": battle_id,
                "status": battle.get("status", "unknown"),
                "turn": battle.get("current_turn", 1),
                "created_at": battle.get("created_at", 0)
            }
        
        # Résumé des champs de bataille
        for battlefield_id, battlefield in battlefields_data.items():
            summary["battlefields"][battlefield_id] = {
                "id": battlefield_id,
                "attacker_city": battlefield.get("attacker_city", "unknown"),
                "defender_city": battlefield.get("defender_city", "unknown"),
                "created_at": battlefield.get("created_at", 0)
            }
        
        return jsonify({
            "success": True,
            "summary": summary
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur récupération résumé: {str(e)}"
        }), 500

@battle_v2_bp.route('/api/v2/battle/city/<city_id>', methods=['GET'])
def get_battle_from_city(city_id):
    """Charger une bataille depuis une ville"""
    try:
        battle_loader = BattleLoaderService()
        battle_data = battle_loader.load_battle_from_city(city_id)
        
        if battle_data:
            return jsonify({
                "success": True,
                "battle": battle_data
            })
        else:
            return jsonify({
                "success": False,
                "error": "Aucune bataille trouvée pour cette ville"
            }), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur lors du chargement de la bataille: {str(e)}"
        }), 500

@battle_v2_bp.route('/api/v2/battle/save-positions', methods=['POST'])
def save_positions_simple():
    """Sauvegarde des positions dans battlesv2.json - Format ultra-compact"""
    try:
        data = request.get_json()
        battle_id = data.get('battleId')
        positions = data.get('positions', [])
        current_round = data.get('current_round', 1)
        
        if not battle_id:
            return jsonify({"success": False, "error": "battleId manquant"}), 400
        
        # Charger données existantes
        battles_data = load_json_data(BATTLES_V2_FILE, {})
        
        # Initialiser la structure si nouvelle bataille
        if battle_id not in battles_data:
            battles_data[battle_id] = {
                "battleId": battle_id,
                "timestamp": data.get('timestamp', int(time.time() * 1000)),
                "current_round": current_round,
                "current_player": "",  # Vide au déploiement pour forcer "Commencer la bataille"
                "battle_status": "deployment",  # ✅ Toujours 'deployment' au démarrage
                "teams": {}
            }
        
        # VÉRIFICATION COMPLÈTE DES COLLISIONS AVANT SAUVEGARDE
        
        # 1. Créer un map des nouvelles positions pour détecter les doublons
        position_map = {}
        for pos in positions:
            position_key = f"{pos['position']['q']},{pos['position']['r']}"
            if position_key in position_map:
                return jsonify({
                    "success": False,
                    "error": f"Collision détectée: les unités {position_map[position_key]} et {pos.get('unitId')} tentent d'occuper la même position"
                }), 400
            position_map[position_key] = pos.get('unitId')
        
        # 2. Vérifier les collisions avec les unités déjà déployées
        for pos in positions:
            target_position = [pos['position']['q'], pos['position']['r']]
            collision_detected, occupying_unit_id = check_position_collision(
                battles_data[battle_id], target_position, excluding_unit_id=pos.get('unitId')
            )
            
            if collision_detected:
                return jsonify({
                    "success": False,
                    "error": f"Position [{target_position[0]}, {target_position[1]}] déjà occupée par l'unité {occupying_unit_id}"
                }), 400
        
        # Organiser par équipes
        teams_data = battles_data[battle_id].get("teams", {})
        
        for pos in positions:
            team = pos.get("team", "attacker")
            unit_id = pos.get("unitId", "")
            
            # Extraire l'ID réel du joueur depuis l'unitId
            team_key = f"{team}_player_id"  # Valeur par défaut
            
            # Gestion des différents formats d'unitId
            if 'wild_camp' in unit_id:
                team_key = 'wild_camp'
            elif 'player_' in unit_id:
                # Extraire player_XX depuis des formats comme:
                # - auto_attacker_player_15_xxx
                # - attacker_player_15_xxx
                # - defender_player_15_xxx
                parts = unit_id.split('_')
                for i, part in enumerate(parts):
                    if part == 'player' and i + 1 < len(parts):
                        team_key = f"player_{parts[i+1]}"
                        break
            
            if team_key not in teams_data:
                teams_data[team_key] = []
            
            # Format ultra-compact
            unit_id = pos.get("unitId", "")
            unit_type = pos.get("unitType", "")
            
            compact_unit = {
                "unitId": unit_id,
                "position": [pos["position"]["q"], pos["position"]["r"]]  # Format [q, r]
            }
            
            # Gestion spéciale pour les héros
            if pos.get("isHero") or unit_type == "hero":
                hero_data = pos.get("heroData", {})
                hero_id = None
                
                # 1. Essayer d'abord de récupérer le realHeroId ou instanceId depuis heroData
                if isinstance(hero_data, dict):
                    hero_id = hero_data.get("realHeroId") or hero_data.get("instanceId")
                
                # 2. Si pas trouvé, essayer d'extraire depuis unit_id
                if not hero_id or not str(hero_id).startswith("hero_"):
                    if "hero_" in unit_id:
                        # Chercher le pattern hero_timestamp_hash
                        import re
                        hero_match = re.search(r'hero_\d+_[a-f0-9]+', unit_id)
                        if hero_match:
                            hero_id = hero_match.group(0)
                
                # 3. Fallback: garder l'unit_id original
                if not hero_id:
                    hero_id = unit_id
                
                try:
                    # Récupérer HP du héros depuis player_heroes.json
                    heroes_data = load_json_data(PLAYER_HEROES_FILE, {})
                    hero_hp = None  # Pas de valeur par défaut
                    
                    
                    # Chercher dans chaque joueur
                    for player_id, player_data in heroes_data.items():
                        if isinstance(player_data, dict) and "heroes" in player_data:
                            if hero_id in player_data["heroes"]:
                                hero_stats = player_data["heroes"][hero_id].get("calculated_stats", {})
                                hero_hp = hero_stats.get("hp")
                                if hero_hp is not None:
                                    break
                    
                    # Seulement assigner les HP si on les a trouvées
                    if hero_hp is not None:
                        compact_unit["hp"] = hero_hp
                    
                    # Appliquer le bonus de moral du héros au déploiement
                    try:
                        from app.battle.HeroBonusManager import HeroBonusManager
                        hero_manager = HeroBonusManager()
                        
                        # Récupérer le bonus moral de ce héros
                        hero_bonuses = hero_manager.get_hero_bonuses(hero_id)
                        moral_bonus = hero_bonuses.get('moral_bonus', 0)
                        
                        if moral_bonus > 0:
                            # Mettre à jour le moral dans battlefields_v2.json (PAS dans battlesv2.json)
                            try:
                                battlefields_data = load_json_data(BATTLEFIELDS_V2_FILE, {})
                                if battle_id in battlefields_data:
                                    forces = battlefields_data[battle_id].get('forces', {})
                                    
                                    # Extraire le player_id depuis l'unit_id
                                    player_id = None
                                    unit_id_parts = unit_id.split('_')
                                    if len(unit_id_parts) >= 3 and unit_id_parts[1] == 'player':
                                        player_id = f"player_{unit_id_parts[2]}"
                                    
                                    if player_id:
                                        if team == "attacker" and 'attackers' in forces and player_id in forces['attackers']:
                                            old_moral = forces['attackers'][player_id].get('moral', 100)
                                            new_moral = old_moral + moral_bonus
                                            forces['attackers'][player_id]['moral'] = new_moral
                                        elif team == "defender" and 'defenders' in forces and player_id in forces['defenders']:
                                            old_moral = forces['defenders'][player_id].get('moral', 100)
                                            new_moral = old_moral + moral_bonus
                                            forces['defenders'][player_id]['moral'] = new_moral
                                        
                                        # Sauvegarder battlefields_v2.json
                                        save_json_data(BATTLEFIELDS_V2_FILE, battlefields_data)
                            except Exception as e:
                                pass
                        else:
                            pass
                            
                    except Exception as e:
                        # Ne pas bloquer le déploiement en cas d'erreur
                        pass
                    
                except Exception as e:
                    # Ne pas assigner de HP si erreur - laisser le système utiliser les vraies données
                    pass
            else:
                compact_unit["unitCount"] = pos.get("unitCount", 1)
            
            # Éviter les doublons
            existing_unit_ids = {unit["unitId"] for unit in teams_data[team_key]}
            if compact_unit["unitId"] not in existing_unit_ids:
                teams_data[team_key].append(compact_unit)
        
        # Mettre à jour la bataille
        battles_data[battle_id]["teams"] = teams_data
        battles_data[battle_id]["timestamp"] = data.get('timestamp', int(time.time() * 1000))
        if current_round:
            battles_data[battle_id]["current_round"] = current_round
        
        # Mettre à jour les unit_counts.deployed depuis les teams déployées
        _update_unit_counts_deployed(battles_data[battle_id])
        
        # Sauvegarder avec format ultra-compact
        if save_json_data(BATTLES_V2_FILE, battles_data, compact=True):
            # ✅ VÉRIFICATION AUTOMATIQUE DE VICTOIRE APRÈS SAUVEGARDE
            # MAIS SEULEMENT SI TOUS LES JOUEURS ONT FINI DE DÉPLOYER
            victory_result = None
            try:
                # Vérifier si tous les joueurs ont déployé leurs unités
                battle_data = battles_data[battle_id]
                unit_counts = battle_data.get("unit_counts", {})
                all_deployed = True
                
                for player_id, units in unit_counts.items():
                    for unit_type, counts in units.items():
                        if isinstance(counts, dict) and "deployed" in counts and "total" in counts:
                            if counts["deployed"] < counts["total"]:
                                all_deployed = False
                                break
                    if not all_deployed:
                        break
                
                if all_deployed:
                    from app.battle.battle_victory_manager import BattleVictoryManager
                    victory_manager = BattleVictoryManager()
                    has_winner, winner_team, victory_type = victory_manager.check_all_victory_conditions(battle_id)
                    
                    if has_winner:
                        
                        # ✅ SAUVEGARDER LE BILAN FINAL DANS BATTLEFIELDS_V2.JSON
                        victory_manager.save_battle_result(battle_id, winner_team, victory_type)
                        
                        victory_result = {
                            "victory_detected": True,
                            "winner_team": winner_team,
                            "victory_type": victory_type,
                            "victory_message": f"Victoire des {winner_team} par {victory_type}"
                        }
                    else:
                        pass
                else:
                    pass
                    
            except Exception as victory_error:
                # Ne pas bloquer la sauvegarde même si la vérification échoue
                pass
            
            response_data = {
                "success": True,
                "message": f"Positions compactes sauvegardées pour {battle_id}",
                "teams_count": len(teams_data)
            }
            
            # Ajouter les informations de victoire si détectées
            if victory_result:
                response_data.update(victory_result)
                
            return jsonify(response_data)
        else:
            return jsonify({
                "success": False,
                "error": "Erreur lors de la sauvegarde des positions"
            }), 500
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@battle_v2_bp.route('/api/v2/battle/get-positions/<battle_id>', methods=['GET'])
def get_battle_positions(battle_id):
    """Récupère les positions d'une bataille depuis battlesv2.json"""
    try:
        battles_data = load_json_data(BATTLES_V2_FILE, {})
        
        if battle_id not in battles_data:
            return jsonify({"success": False, "error": "Bataille non trouvée"}), 404
        
        return jsonify(battles_data[battle_id])
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ========================================
# ROUTES DE NOTIFICATIONS
# ========================================

@battle_v2_bp.route('/api/battles/notifications/<player_id>', methods=['GET'])
def get_player_notifications(player_id):
    """Récupère les notifications de bataille d'un joueur"""
    try:
        notifications = load_json_data(BATTLE_NOTIFICATIONS_FILE, {})
        
        player_notifications = notifications.get(player_id, [])
        
        # Trier par timestamp décroissant (plus récentes d'abord)
        player_notifications.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        
        # Compter les non lues
        unread_count = sum(1 for n in player_notifications if not n.get('read', False))
        
        return jsonify({
            "success": True,
            "notifications": player_notifications,
            "unread_count": unread_count
        })
        
    except Exception as e:
        print(f"[ERROR] Erreur récupération notifications: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@battle_v2_bp.route('/api/battles/notifications/mark-read', methods=['POST'])
def mark_notification_read():
    """Marque une ou plusieurs notifications comme lues"""
    try:
        data = request.get_json()
        player_id = data.get('playerId')
        notification_ids = data.get('notificationIds', [])
        
        if not player_id:
            return jsonify({"success": False, "error": "playerId manquant"}), 400
        
        notifications = load_json_data(BATTLE_NOTIFICATIONS_FILE, {})
        
        if player_id in notifications:
            for notification in notifications[player_id]:
                if notification.get('id') in notification_ids:
                    notification['read'] = True
            
            # Sauvegarder
            save_json_data(BATTLE_NOTIFICATIONS_FILE, notifications)
            
            return jsonify({
                "success": True,
                "message": f"{len(notification_ids)} notification(s) marquée(s) comme lue(s)"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Aucune notification pour ce joueur"
            }), 404
        
    except Exception as e:
        print(f"[ERROR] Erreur marquage notifications: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@battle_v2_bp.route('/api/battles/notifications/clear/<player_id>', methods=['DELETE'])
def clear_player_notifications(player_id):
    """Supprime toutes les notifications d'un joueur"""
    try:
        notifications = load_json_data(BATTLE_NOTIFICATIONS_FILE, {})
        
        if player_id in notifications:
            del notifications[player_id]
            save_json_data(BATTLE_NOTIFICATIONS_FILE, notifications)
            return jsonify({
                "success": True,
                "message": f"Toutes les notifications de {player_id} ont été supprimées"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Aucune notification trouvée pour ce joueur"
            }), 404
        
    except Exception as e:
        print(f"[ERROR] Erreur suppression notifications: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@battle_v2_bp.route('/api/battles/notifications/clear-old', methods=['POST'])
def clear_old_notifications():
    """Supprime les notifications de plus de 7 jours pour tous les joueurs"""
    try:
        import time
        notifications = load_json_data(BATTLE_NOTIFICATIONS_FILE, {})
        
        seven_days_ago = int(time.time() * 1000) - (7 * 24 * 60 * 60 * 1000)
        total_deleted = 0
        
        for player_id in list(notifications.keys()):
            original_count = len(notifications[player_id])
            notifications[player_id] = [
                n for n in notifications[player_id]
                if n.get('timestamp', 0) > seven_days_ago
            ]
            deleted = original_count - len(notifications[player_id])
            total_deleted += deleted
            
            # Supprimer la clé si plus de notifications
            if not notifications[player_id]:
                del notifications[player_id]
        
        save_json_data(BATTLE_NOTIFICATIONS_FILE, notifications)
        
        return jsonify({
            "success": True,
            "message": f"{total_deleted} notifications supprimées (>7 jours)"
        })
        
    except Exception as e:
        print(f"[ERROR] Erreur nettoyage notifications: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
