"""
BATTLE_TURN_MANAGER_V2.PY - Gestionnaire de Tours de Bataille

RÔLE:
    Gère le déroulement complet d'un tour de combat dans le système de bataille V2.
    Calcule les dégâts, applique les effets, gère les victoires/défaites.

RESPONSABILITÉS:
    1. Exécution d'un tour de combat complet
    2. Calcul des dégâts (unités terrestres, navales, murailles)
    3. Application des effets de héros et bonus
    4. Détection de la fin de bataille (victoire/défaite)
    5. Gestion du moral et des retraites
    6. Mise à jour de l'état de la bataille

ARCHITECTURE DE COMBAT:
    Tour de combat →
        1. Phase d'attaque (attaquant → défenseur)
        2. Calcul des dégâts (compétences, bonus, moral)
        3. Application des pertes
        4. Vérification de fin de bataille
        5. Phase de contre-attaque (défenseur → attaquant)
        6. Mise à jour de l'état

POINTS CLÉS:
    - Séparé du système V1 pour éviter les conflits
    - Gère les combats terrestres ET navals
    - Système de moral influençant les dégâts
    - Gestion des murailles et fortifications
    - Application des bonus de héros

DÉPENDANCES:
    - battle_victory_manager.py : Gestion des victoires
    - battle_stats_service_v2.py : Statistiques de combat
    - HeroBonusManager.py : Calcul des bonus de héros

HISTORIQUE:
    - V2 : Refonte complète du système de combat
    - Ajout du système de moral et retraites
    - Support des combats navals
"""

from flask import Blueprint, request, jsonify
import json
import os
import time
from datetime import datetime
from typing import Dict, Any
from app.config.paths import BATTLEFIELDS_V2_FILE, BATTLES_V2_FILE, GAME_DATA_DIR

# Blueprint spécifique aux tours de bataille V2
battle_turn_bp = Blueprint('battle_turn_v2', __name__)

print("[INIT] Blueprint battle_turn_v2 cree avec route /api/v2/battle/turn-timer/<battle_id>")

# Calculer BASE_DIR de façon plus robuste
# __file__ = .../server/app/battle/battle_turn_manager_v2.py
# Nous voulons aller jusqu'à .../server/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')

class BattleTurnManagerV2:
    """Gestionnaire des tours pour les batailles V2"""
    
    def __init__(self):
        # Utiliser les constantes de chemins
        self.battles_file = BATTLES_V2_FILE
        self.battlefields_file = BATTLEFIELDS_V2_FILE
    
    def save_battles_compact(self, battles_data: dict) -> None:
        """
        Sauvegarde ultra-compacte uniforme - utilise la même logique que battle_routes_v2
        """
        try:
            with open(self.battles_file, 'w', encoding='utf-8') as f:
                # Utiliser le même format compact ciblé que dans battle_routes_v2
                import re
                
                # Format de base avec indentation pour structure principale
                json_str = json.dumps(battles_data, ensure_ascii=False, indent=2)
                
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
                    r'{\s*"unitId":\s*"([^"]+)",\s*"move":\s*{\s*"from":\s*\[\s*(\d+),\s*(\d+)\s*\],\s*"to":\s*\[\s*(\d+),\s*(\d+)\s*\]\s*}\s*}',
                    r'{"unitId": "\1", "move": {"from": [\2, \3], "to": [\4, \5]}}',
                    json_str
                )
                
                # Compacter les attaques avec kills
                json_str = re.sub(
                    r'{\s*"unitId":\s*"([^"]+)",\s*"attack":\s*{\s*"target":\s*"([^"]+)",\s*"kills":\s*(\d+)\s*}\s*}',
                    r'{"unitId": "\1", "attack": {"target": "\2", "kills": \3}}',
                    json_str
                )
                
                # Compacter les attaques avec damage
                json_str = re.sub(
                    r'{\s*"unitId":\s*"([^"]+)",\s*"attack":\s*{\s*"target":\s*"([^"]+)",\s*"damage":\s*(\d+)\s*}\s*}',
                    r'{"unitId": "\1", "attack": {"target": "\2", "damage": \3}}',
                    json_str
                )
                
                f.write(json_str)
            
        except Exception as e:
            # Fallback simple en cas d'erreur
            with open(self.battles_file, 'w', encoding='utf-8') as f:
                json.dump(battles_data, f, ensure_ascii=False, separators=(',', ': '))

    def load_battle_data(self, battle_id: str) -> tuple:
        """
        Charge les données de bataille
        
        Returns:
            tuple: (battles_data, battlefield_info, success, error_message)
        """
        try:
            # Charger battlesv2.json
            if not os.path.exists(self.battles_file):
                return None, None, False, 'Fichier de bataille non trouvé'
                
            with open(self.battles_file, 'r', encoding='utf-8') as f:
                battles_data = json.load(f)
                
            if battle_id not in battles_data:
                return None, None, False, f'Bataille {battle_id} non trouvée'
            
            # Charger battlefields_v2.json
            if not os.path.exists(self.battlefields_file):
                return battles_data, None, False, 'Fichier battlefields non trouvé'
                
            with open(self.battlefields_file, 'r', encoding='utf-8') as f:
                battlefields_data = json.load(f)
            
            # Trouver les infos de la bataille
            battlefield_info = None
            
            # Gérer les deux formats : dict ou liste
            if isinstance(battlefields_data, dict):
                battlefield_info = battlefields_data.get(battle_id)
            elif isinstance(battlefields_data, list):
                for battlefield in battlefields_data:
                    if battlefield.get('battle_id') == battle_id:
                        battlefield_info = battlefield
                        break
            
            return battles_data, battlefield_info, True, None
            
        except Exception as e:
            return None, None, False, f'Erreur lors du chargement: {str(e)}'
    
    def get_participants(self, battle_id: str, battlefield_info: dict) -> tuple:
        """
        Récupère les participants de la bataille
        
        Returns:
            tuple: (attacker_id, defender_id, success, error_message)
        """
        try:
            if battlefield_info is None:
                return None, None, False, 'Informations de bataille non trouvées'
            
            # Essayer différents formats
            attacker_id = None
            defender_id = None
            
            # Format 1: attacker_id, defender_id
            if 'attacker_id' in battlefield_info and 'defender_id' in battlefield_info:
                attacker_id = battlefield_info['attacker_id']
                defender_id = battlefield_info['defender_id']
            
            # Format 2: participants avec attackers/defenders
            elif 'participants' in battlefield_info:
                participants = battlefield_info['participants']
                if 'attackers' in participants and 'defenders' in participants:
                    attackers = participants['attackers']
                    defenders = participants['defenders']
                    
                    if attackers and defenders:
                        attacker_id = attackers[0] if isinstance(attackers, list) else attackers
                        defender_id = defenders[0] if isinstance(defenders, list) else defenders
            
            if not attacker_id or not defender_id:
                return None, None, False, 'Participants non définis correctement'
                
            return attacker_id, defender_id, True, None
            
        except Exception as e:
            return None, None, False, f'Erreur lors de la récupération des participants: {str(e)}'
    
    def _get_unit_owner(self, battle_info: dict, unit_id: str, attacker_id: str, defender_id: str) -> str:
        """Détermine le propriétaire d'une unité depuis l'unit_id ou la structure des équipes"""
        # Extraire le propriétaire depuis l'unit_id
        parts = unit_id.split('_')
        
        # Format: auto_defender_wild_camp_* → wild_camp
        try:
            wild_index = parts.index('wild')
            if wild_index + 1 < len(parts) and parts[wild_index + 1] == 'camp':
                return 'wild_camp'
        except ValueError:
            pass
        
        # Format: attacker_player_X_* ou defender_player_X_* → player_X
        try:
            player_index = parts.index('player')
            if player_index + 1 < len(parts):
                return f"player_{parts[player_index + 1]}"
        except ValueError:
            pass
        
        # Format: barbarian_village_* → barbarian_village
        if len(parts) >= 3 and parts[0] == 'barbarian' and parts[1] == 'village':
            return 'barbarian_village'
        
        # Fallback: chercher dans la structure des équipes
        if 'teams' in battle_info:
            for team_name, unit_list in battle_info['teams'].items():
                if isinstance(unit_list, list):
                    for unit in unit_list:
                        if unit.get('unitId') == unit_id:
                            if team_name.startswith('player_') or team_name == 'barbarian_village' or team_name == 'wild_camp':
                                return team_name
                            elif 'attacker' in team_name:
                                return attacker_id
                            elif 'defender' in team_name:
                                return defender_id
            
            # Structure alternative: teams.attackers.units et teams.defenders.units
            for team_name, team_data in battle_info['teams'].items():
                if isinstance(team_data, dict) and 'units' in team_data and unit_id in team_data['units']:
                    if 'attacker' in team_name:
                        return attacker_id
                    elif 'defender' in team_name:
                        return defender_id
        
        return None
    
    def _unit_has_moved_this_round(self, battle_info: dict, unit_id: str, current_round: int) -> bool:
        """Vérifie si une unité a déjà bougé dans le round actuel"""
        if 'rounds_history' not in battle_info:
            return False
            
        round_key = f"round_{current_round}"
        if round_key not in battle_info['rounds_history']:
            return False
            
        moves = battle_info['rounds_history'][round_key].get('moves', [])
        
        # Vérifier si cette unité a déjà un mouvement enregistré ce round
        for action in moves:
            if action.get('unitId') == unit_id and 'move' in action:
                return True
                
        return False
    
    def _unit_has_attacked_this_round(self, battle_info: dict, unit_id: str, current_round: int) -> bool:
        """Vérifie si une unité a déjà attaqué dans le round actuel"""
        if 'rounds_history' not in battle_info:
            return False
            
        round_key = f"round_{current_round}"
        if round_key not in battle_info['rounds_history']:
            return False
            
        moves = battle_info['rounds_history'][round_key].get('moves', [])
        
        # Vérifier si cette unité a déjà une attaque enregistrée ce round
        for action in moves:
            if action.get('unitId') == unit_id and 'attack' in action:
                return True
                
        return False

    def _unit_has_acted_this_round(self, battle_info: dict, unit_id: str, current_round: int) -> bool:
        """
        Vérifie si une unité a déjà effectué une action dans le round actuel
        LEGACY: Maintenue pour compatibilité - vérifie mouvement OU attaque
        """
        return (self._unit_has_moved_this_round(battle_info, unit_id, current_round) or 
                self._unit_has_attacked_this_round(battle_info, unit_id, current_round))
    
    def _get_terrain_at_position(self, position: list, battle_info: dict) -> str:
        """Récupère le type de terrain à une position donnée"""
        battlefield = battle_info.get('battlefield', {})
        battlefield_map = battlefield.get('battlefield_map', {})
        
        # Convertir la position en string key "q_r"
        pos_key = f"{position[0]}_{position[1]}"
        
        if pos_key in battlefield_map:
            return battlefield_map[pos_key].get('terrain', 'plains')
        
        return 'plains'

    def _check_victory_after_action(self, battle_id: str) -> dict:
        """Vérifie les conditions de victoire et déclenche les actions automatiques"""
        try:
            from app.battle.battle_victory_manager import BattleVictoryManager
            
            victory_manager = BattleVictoryManager()
            has_winner, winner_team, victory_type = victory_manager.check_all_victory_conditions(battle_id)
            
            if has_winner:
                # L'incrémentation du niveau village barbare sera gérée dans victory_manager lors du surrender
                # Pas besoin de la faire ici pour éviter le double appel
                
                # Marquer la bataille comme terminée dans battlesv2.json
                self._mark_battle_as_finished(battle_id, winner_team, victory_type)
                
                # Clic virtuel pour victoires automatiques
                if victory_type in ['moral_breakdown', 'elimination']:
                    if winner_team == 'attackers':
                        surrender_api_result = self._virtual_click_surrender_defender(battle_id)
                    else:
                        surrender_api_result = self._virtual_click_surrender_attacker(battle_id)
                    
                    victory_message = f"Victoire {winner_team} par {victory_type}"
                    
                    return {
                        'victory_detected': True,
                        'winner_team': winner_team,
                        'victory_type': victory_type,
                        'virtual_click': True,
                        'surrender_result': surrender_api_result,
                        'message': victory_message
                    }
                
                return {
                    'victory_detected': True,
                    'winner_team': winner_team,
                    'victory_type': victory_type,
                    'message': f"Victoire {winner_team} par {victory_type}"
                }
            
            return {'victory_detected': False}
            
        except Exception as e:
            return {'victory_detected': False, 'error': str(e)}
    
    def record_unit_move(self, battle_id: str, unit_id: str, from_position: list, to_position: list) -> dict:
        """
        Enregistre un mouvement d'unité et met à jour les positions
        
        Args:
            battle_id (str): ID de la bataille
            unit_id (str): ID de l'unité qui se déplace
            from_position (list): Position d'origine [q, r]
            to_position (list): Position de destination [q, r]
            
        Returns:
            dict: Résultat de l'opération
        """
        try:
            
            # Charger les données
            battles_data, battlefield_info, success, error = self.load_battle_data(battle_id)
            if not success:
                return {'success': False, 'error': error}
            
            # Récupérer les participants pour le contrôle des tours
            attacker_id, defender_id, success, error = self.get_participants(battle_id, battlefield_info)
            if not success:
                return {'success': False, 'error': error}
            
            battle_info = battles_data[battle_id]
            current_round = battle_info.get('current_round', 1)
            current_player = battle_info.get('current_player', "")  # Ne plus utiliser attacker_id par défaut
            
            # 🎯 NOUVEAU: Vérifier que la bataille a commencé (current_player doit être défini)
            if not current_player or current_player == "":
                return {
                    'success': False,
                    'error': 'La bataille n\'a pas encore commencé. Cliquez sur "Commencer la bataille" d\'abord.'
                }
            
            # CORRECTION AUTOMATIQUE : Si current_player n'est pas un vrai nom de joueur
            if current_player not in [attacker_id, defender_id]:
                if current_player == "defender":
                    current_player = defender_id
                elif current_player == "attacker":
                    current_player = attacker_id
                else:
                    # Si on ne reconnaît pas le current_player, le laisser tel quel
                    # plutôt que de le réinitialiser automatiquement
                    pass
                
                # Mettre à jour seulement si on a fait une vraie correction
                if current_player != battle_info.get('current_player'):
                    battles_data[battle_id]['current_player'] = current_player
                    self.save_battles_compact(battles_data)
            
            # CONTRÔLE DES TOURS: Vérifier que l'unité appartient au joueur actuel
            unit_owner = self._get_unit_owner(battle_info, unit_id, attacker_id, defender_id)
            # Vérifier que c'est le bon joueur qui joue
            if unit_owner != current_player:
                return {
                    'success': False, 
                    'error': f"C'est le tour de {current_player}, mais cette unité appartient à {unit_owner}"
                }
            
            # 🎯 NOUVEAU: Vérifier que l'unité n'a pas déjà bougé ce round (mais peut attaquer)
            if self._unit_has_moved_this_round(battle_info, unit_id, current_round):
                return {
                    'success': False,
                    'error': f'L\'unité {unit_id} a déjà effectué un mouvement ce round. Chaque unité ne peut bouger qu\'une fois par round.'
                }
                
            # 🎯 NOUVEAU: Empêcher le mouvement après une attaque
            if self._unit_has_attacked_this_round(battle_info, unit_id, current_round):
                return {
                    'success': False,
                    'error': f'L\'unité {unit_id} a déjà attaqué ce round. Une unité ne peut pas se déplacer après avoir attaqué.'
                }
            
            # 🎯 NOUVEAU: Vérifier que la destination n'est pas une rivière
            destination_terrain = self._get_terrain_at_position(to_position, battle_info)
            if destination_terrain == 'river':
                return {
                    'success': False,
                    'error': 'Les unités ne peuvent pas traverser les rivières.'
                }
            
            # Mettre à jour la position de l'unité dans teams ET récupérer la vraie position actuelle
            actual_from_position = None
            if 'teams' in battle_info:
                unit_found = False
                
                # Structure réelle: teams.attacker_player_id[] et teams.defender_player_id[]
                for team_name, unit_list in battle_info['teams'].items():
                    if isinstance(unit_list, list):
                        for i, unit in enumerate(unit_list):
                            if unit.get('unitId') == unit_id:
                                # Récupérer la VRAIE position actuelle avant de la changer
                                actual_from_position = unit['position'].copy()
                                # Puis mettre à jour vers la nouvelle position
                                unit['position'] = to_position
                                unit_found = True
                                break
                        if unit_found:
                            break
                
                # Si pas trouvé, essayer l'ancienne structure: teams.attackers.units et teams.defenders.units  
                if not unit_found:
                    for team_name, team_data in battle_info['teams'].items():
                        if isinstance(team_data, dict) and 'units' in team_data and unit_id in team_data['units']:
                            unit = team_data['units'][unit_id]
                            # Récupérer la VRAIE position actuelle avant de la changer
                            actual_from_position = [unit['x'], unit['y']]
                            # Puis mettre à jour vers la nouvelle position
                            unit['x'] = to_position[0]
                            unit['y'] = to_position[1]
                            unit_found = True
                            break
                
                if not unit_found:
                    return {'success': False, 'error': f'Unité {unit_id} non trouvée'}
                    
                # Si on n'a pas trouvé la position actuelle, utiliser from_position en fallback
                if actual_from_position is None:
                    actual_from_position = from_position
            
            # Ajouter le mouvement à l'historique avec la VRAIE position de départ
            if 'rounds_history' not in battle_info:
                battle_info['rounds_history'] = {}
            
            # S'assurer que rounds_history est un dictionnaire (pas une liste)
            if not isinstance(battle_info['rounds_history'], dict):
                battle_info['rounds_history'] = {}
            
            round_key = f"round_{current_round}"
            if round_key not in battle_info['rounds_history']:
                battle_info['rounds_history'][round_key] = {"moves": []}
            
            # Ajouter le mouvement - Format compact avec la vraie position from
            move_record = {
                "unitId": unit_id,
                "move": {"from": actual_from_position, "to": to_position}
            }
            
            battle_info['rounds_history'][round_key]["moves"].append(move_record)
            
            # Sauvegarder avec format compact
            self.save_battles_compact(battles_data)
            
            # 🎯 NOUVEAU: Vérifier les conditions de victoire après le mouvement
            victory_check = self._check_victory_after_action(battle_id)
            
            result = {
                'success': True,
                'message': f'Mouvement de {unit_id} enregistré',
                'round': current_round,
                'player': current_player
            }
            
            # Ajouter info de victoire si détectée
            if victory_check.get('victory_detected'):
                result.update({
                    'victory_detected': True,
                    'winner_team': victory_check['winner_team'],
                    'victory_type': victory_check['victory_type'],
                    'victory_message': victory_check['message']
                })
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def record_attack_action(self, battle_id: str, attacker_id: str, defender_id: str, kills: int) -> dict:
        """
        Enregistre une action d'attaque dans l'historique de bataille et met à jour le unitCount
        
        Args:
            battle_id (str): ID de la bataille
            attacker_id (str): ID de l'unité attaquante
            defender_id (str): ID de l'unité défendante
            kills (int): Nombre d'unités tuées
            
        Returns:
            dict: Résultat de l'opération
        """
        try:
            
            # Charger les données
            battles_data, battlefield_info, success, error = self.load_battle_data(battle_id)
            if not success:
                return {'success': False, 'error': error}
            
            # Récupérer les participants pour le contrôle des tours
            attacker_player_id, defender_player_id, success, error = self.get_participants(battle_id, battlefield_info)
            if not success:
                return {'success': False, 'error': error}

            battle_info = battles_data[battle_id]
            current_round = battle_info.get('current_round', 1)
            current_player = battle_info.get('current_player', '')
            
            # 🎯 NOUVEAU: Vérifier que la bataille a commencé
            if not current_player or current_player == "":
                return {
                    'success': False,
                    'error': 'La bataille n\'a pas encore commencé. Cliquez sur "Commencer la bataille" d\'abord.'
                }
            
            # 🎯 NOUVEAU: Vérifier que l'unité attaquante appartient au joueur actuel
            unit_owner = self._get_unit_owner(battle_info, attacker_id, attacker_player_id, defender_player_id)
            if unit_owner != current_player:
                return {
                    'success': False, 
                    'error': f"C'est le tour de {current_player}, mais cette unité appartient à {unit_owner}"
                }
                
            # 🎯 NOUVEAU: Vérifier que l'unité n'a pas déjà attaqué ce round (mais peut avoir bougé)
            if self._unit_has_attacked_this_round(battle_info, attacker_id, current_round):
                return {
                    'success': False,
                    'error': f'L\'unité {attacker_id} a déjà effectué une attaque ce round. Une unité peut se déplacer puis attaquer, mais pas attaquer puis se déplacer.'
                }
                
            # Initialiser rounds_history si nécessaire
            if 'rounds_history' not in battle_info:
                battle_info['rounds_history'] = {}
            
            # S'assurer que rounds_history est un dictionnaire (pas une liste)
            if not isinstance(battle_info['rounds_history'], dict):
                battle_info['rounds_history'] = {}
            
            round_key = f"round_{current_round}"
            if round_key not in battle_info['rounds_history']:
                battle_info['rounds_history'][round_key] = {"moves": []}
            
            # Ajouter l'action d'attaque - Format compact similaire aux mouvements
            attack_record = {
                "unitId": attacker_id,
                "attack": {
                    "target": defender_id,
                    "kills": kills
                }
            }
            
            battle_info['rounds_history'][round_key]["moves"].append(attack_record)
            
            # Mettre à jour le unitCount de l'unité défendante
            self._update_unit_count(battle_info, defender_id, kills)
            
            # Supprimer automatiquement les unités mortes
            self._remove_dead_units(battle_info)
            
            # ✅ NOUVEAU : Mettre à jour les statistiques de battlefield (kills/losses/XP)
            from .battle_stats_service_v2 import get_battle_stats_service_v2
            stats_service = get_battle_stats_service_v2()
            stats_service.update_battle_stats_on_combat(battle_id, attacker_id, defender_id, kills)
            
            # Sauvegarder avec format compact
            self.save_battles_compact(battles_data)
            
            # 🎯 NOUVEAU: Vérifier les conditions de victoire après l'attaque
            victory_check = self._check_victory_after_action(battle_id)
            
            result = {
                'success': True,
                'message': f'Attaque de {attacker_id} contre {defender_id} enregistrée ({kills} tués)',
                'round': current_round
            }
            
            # Ajouter info de victoire si détectée
            if victory_check.get('victory_detected'):
                result.update({
                    'victory_detected': True,
                    'winner_team': victory_check['winner_team'],
                    'victory_type': victory_check['victory_type'],
                    'victory_message': victory_check['message']
                })
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def record_hero_damage_action(self, battle_id: str, attacker_id: str, defender_id: str, damage_dealt: float) -> dict:
        """
        Enregistre une attaque contre un héros avec des dégâts aux HP au lieu de kills
        
        Args:
            battle_id (str): ID de la bataille
            attacker_id (str): ID de l'unité attaquante
            defender_id (str): ID du héros défendant
            damage_dealt (float): Dégâts infligés aux HP du héros
            
        Returns:
            dict: Résultat de l'opération
        """
        try:

            
            # Charger les données
            battles_data, battlefield_info, success, error = self.load_battle_data(battle_id)
            if not success:
                return {'success': False, 'error': error}
            
            # Récupérer les participants pour le contrôle des tours
            attacker_player_id, defender_player_id, success, error = self.get_participants(battle_id, battlefield_info)
            if not success:
                return {'success': False, 'error': error}

            battle_info = battles_data[battle_id]
            current_round = battle_info.get('current_round', 1)
            current_player = battle_info.get('current_player', '')
            
            # 🎯 NOUVEAU: Vérifier que la bataille a commencé
            if not current_player or current_player == "":
                return {
                    'success': False,
                    'error': 'La bataille n\'a pas encore commencé. Cliquez sur "Commencer la bataille" d\'abord.'
                }
            
            # 🎯 NOUVEAU: Vérifier que l'unité attaquante appartient au joueur actuel
            unit_owner = self._get_unit_owner(battle_info, attacker_id, attacker_player_id, defender_player_id)
            if unit_owner != current_player:
                return {
                    'success': False, 
                    'error': f"C'est le tour de {current_player}, mais cette unité appartient à {unit_owner}"
                }
                
            # 🎯 NOUVEAU: Vérifier que l'unité n'a pas déjà attaqué ce round (mais peut avoir bougé)
            if self._unit_has_attacked_this_round(battle_info, attacker_id, current_round):
                return {
                    'success': False,
                    'error': f'L\'unité {attacker_id} a déjà effectué une attaque ce round. Une unité peut se déplacer puis attaquer, mais pas attaquer puis se déplacer.'
                }
                
            # Initialiser rounds_history si nécessaire
            if 'rounds_history' not in battle_info:
                battle_info['rounds_history'] = {}
            
            # S'assurer que rounds_history est un dictionnaire (pas une liste)
            if not isinstance(battle_info['rounds_history'], dict):
                battle_info['rounds_history'] = {}
            
            round_key = f"round_{current_round}"
            if round_key not in battle_info['rounds_history']:
                battle_info['rounds_history'][round_key] = {"moves": []}
            
            # Mettre à jour les HP du héros défendant

            hero_updated = self._update_hero_hp(battle_info, defender_id, damage_dealt)

            if not hero_updated:
                return {'success': False, 'error': f'Héros {defender_id} non trouvé pour mise à jour HP'}
            
            # Supprimer automatiquement les unités mortes (héros avec HP <= 0)
            self._remove_dead_units(battle_info)
            
            # Ajouter l'action d'attaque avec damage au lieu de kills (arrondi sans décimales)
            attack_record = {
                "unitId": attacker_id,
                "attack": {
                    "target": defender_id,
                    "damage": round(damage_dealt)
                }
            }
            
            battle_info['rounds_history'][round_key]["moves"].append(attack_record)
            
            # ✅ NOUVEAU : Mettre à jour les statistiques de battlefield (pour les attaques héros)
            from .battle_stats_service_v2 import get_battle_stats_service_v2
            stats_service = get_battle_stats_service_v2()
            stats_service.update_battle_stats_on_combat(battle_id, attacker_id, defender_id, 0, damage_dealt)
            
            # Sauvegarder avec format compact
            self.save_battles_compact(battles_data)
            
            # 🎯 NOUVEAU: Vérifier les conditions de victoire après l'attaque héros
            victory_check = self._check_victory_after_action(battle_id)
            
            result = {
                'success': True,
                'message': f'Attaque de {attacker_id} contre héros {defender_id} enregistrée ({damage_dealt} dégâts)',
                'round': current_round
            }
            
            # Ajouter info de victoire si détectée
            if victory_check.get('victory_detected'):
                result.update({
                    'victory_detected': True,
                    'winner_team': victory_check['winner_team'],
                    'victory_type': victory_check['victory_type'],
                    'victory_message': victory_check['message']
                })
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def record_wall_attack_action(self, battle_id: str, attacker_id: str, wall_group_id: str, 
                                 damage_dealt: float, wall_hp_before: int, wall_hp_after: int, 
                                 destroyed: bool = False) -> dict:
        """
        🧱 Enregistre une action d'attaque contre un mur dans l'historique de bataille
        
        Args:
            battle_id (str): ID de la bataille
            attacker_id (str): ID de l'unité attaquante  
            wall_group_id (str): ID du groupe de murs attaqué
            damage_dealt (float): Dégâts infligés au mur
            wall_hp_before (int): HP du mur avant attaque
            wall_hp_after (int): HP du mur après attaque
            destroyed (bool): Si le groupe de murs a été détruit
            
        Returns:
            dict: Résultat de l'opération
        """
        try:
            # Charger les données
            battles_data, battlefield_info, success, error = self.load_battle_data(battle_id)
            if not success:
                return {'success': False, 'error': error}
            
            # Récupérer les participants
            attacker_player_id, defender_player_id, success, error = self.get_participants(battle_id, battlefield_info)
            if not success:
                return {'success': False, 'error': error}

            battle_info = battles_data[battle_id]
            current_round = battle_info.get('current_round', 1)
            current_player = battle_info.get('current_player', '')
            
            # Vérifier que la bataille a commencé
            if not current_player or current_player == "":
                return {
                    'success': False,
                    'error': 'La bataille n\'a pas encore commencé.'
                }
            
            # Vérifier que l'unité attaquante appartient au joueur actuel
            unit_owner = self._get_unit_owner(battle_info, attacker_id, attacker_player_id, defender_player_id)
            if unit_owner != current_player:
                return {
                    'success': False,
                    'error': f'Cette unité n\'appartient pas au joueur actuel ({current_player})'
                }
                
            # Vérifier que l'unité n'a pas déjà attaqué ce round
            if self._unit_has_attacked_this_round(battle_info, attacker_id, current_round):
                return {
                    'success': False,
                    'error': f'L\'unité {attacker_id} a déjà effectué une attaque ce round.'
                }
                
            # Initialiser rounds_history si nécessaire
            if 'rounds_history' not in battle_info:
                battle_info['rounds_history'] = {}
            
            if not isinstance(battle_info['rounds_history'], dict):
                battle_info['rounds_history'] = {}
            
            round_key = f"round_{current_round}"
            if round_key not in battle_info['rounds_history']:
                battle_info['rounds_history'][round_key] = {"moves": []}
            
            # Ajouter l'action d'attaque de mur (format compact)
            wall_attack_record = {
                "unitId": attacker_id,
                "attack_wall": {"target": wall_group_id, "dmg": round(damage_dealt, 1), "destroyed": destroyed}
            }
            
            battle_info['rounds_history'][round_key]["moves"].append(wall_attack_record)
            
            # Sauvegarder avec format compact
            self.save_battles_compact(battles_data)
            
            result = {
                'success': True,
                'message': f'Attaque de {attacker_id} contre {wall_group_id} enregistrée ({damage_dealt} dégâts)',
                'round': current_round,
                'wall_destroyed': destroyed
            }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _update_unit_count(self, battle_info: dict, defender_id: str, kills: int):
        """
        Met à jour le nombre d'unités survivantes dans les équipes
        
        Args:
            battle_info (dict): Informations de la bataille
            defender_id (str): ID de l'unité défendante
            kills (int): Nombre d'unités tuées
        """
        try:
            # Chercher l'unité dans les équipes
            teams = battle_info.get('teams', {})
            
            for team_name, team_units in teams.items():
                if isinstance(team_units, list):
                    for unit in team_units:
                        if isinstance(unit, dict) and unit.get('unitId') == defender_id:
                            current_count = unit.get('unitCount', 0)
                            new_count = max(0, current_count - kills)  # Ne peut pas être négatif
                            unit['unitCount'] = new_count
                            return
            

            
        except Exception as e:
            pass

    def _remove_dead_units(self, battle_info: dict):
        """
        Supprime automatiquement les unités mortes (unitCount: 0 ou hp: 0) des équipes
        ET déduit le bonus moral des héros morts
        
        Args:
            battle_info (dict): Informations de la bataille
        """
        try:
            from app.battle.HeroBonusManager import HeroBonusManager
            hero_manager = HeroBonusManager()
            
            teams = battle_info.get('teams', {})
            units_removed = []
            
            for team_name, team_units in teams.items():
                if isinstance(team_units, list):
                    # Filtrer les unités vivantes
                    original_count = len(team_units)
                    alive_units = []
                    
                    for unit in team_units:
                        if isinstance(unit, dict):
                            unit_count = unit.get('unitCount')
                            hp = unit.get('hp')
                            unit_id = unit.get('unitId', 'unknown')
                            
                            # Garder l'unité si elle a encore des soldats ou des HP
                            is_alive = True
                            if unit_count is not None and unit_count <= 0:
                                is_alive = False
                            elif hp is not None and hp <= 0:
                                is_alive = False
                                
                            if is_alive:
                                alive_units.append(unit)
                            else:
                                # Unité morte - vérifier si c'est un héros pour déduire le bonus moral
                                if hp is not None and hp <= 0:  # Héros mort (a des HP)
                                    hero_bonuses = hero_manager.get_hero_bonuses(unit_id)
                                    moral_bonus = hero_bonuses.get('moral_bonus', 0)
                                    
                                    if moral_bonus > 0:
                                        # Mettre à jour le moral dans battlefields_v2.json (PAS dans battlesv2.json)
                                        try:
                                            import json
                                            battlefields_file = os.path.join(BASE_DIR, 'gamedata', 'battlefields_v2.json')
                                            
                                            # Charger battlefields_v2.json
                                            with open(battlefields_file, 'r', encoding='utf-8') as f:
                                                battlefields_data = json.load(f)
                                            
                                            # Récupérer le battle_id depuis battle_info
                                            battle_id = battle_info.get('battleId')
                                            if battle_id and battle_id in battlefields_data:
                                                forces = battlefields_data[battle_id].get('forces', {})
                                                
                                                # Extraire le player_id depuis l'unit_id
                                                player_id = None
                                                unit_id_parts = unit_id.split('_')
                                                if len(unit_id_parts) >= 3 and unit_id_parts[1] == 'player':
                                                    player_id = f"player_{unit_id_parts[2]}"
                                                
                                                if player_id:
                                                    # Déterminer si attaquant ou défenseur
                                                    team_type = "attackers" if team_name.startswith('attacker') else "defenders"
                                                    
                                                    if team_type in forces and player_id in forces[team_type]:
                                                        old_moral = forces[team_type][player_id].get('moral', 100)
                                                        new_moral = max(0, old_moral - moral_bonus)
                                                        forces[team_type][player_id]['moral'] = new_moral
                                                        
                                                        # Sauvegarder battlefields_v2.json
                                                        with open(battlefields_file, 'w', encoding='utf-8') as f:
                                                            json.dump(battlefields_data, f, ensure_ascii=False, indent=2)
                                                        

                                        except Exception as e:
                                            pass
                                
                                units_removed.append({
                                    'unitId': unit_id,
                                    'team': team_name,
                                    'unitCount': unit_count,
                                    'hp': hp
                                })
                    
                    # Remplacer la liste par les unités vivantes
                    teams[team_name] = alive_units
                    removed_count = original_count - len(alive_units)
                    
                if removed_count > 0:
                    # Nettoyage silencieux des unités mortes
                    pass
            
        except Exception as e:
            pass

    def _update_hero_hp(self, battle_info: dict, hero_id: str, damage_dealt: float) -> bool:
        """
        Met à jour les points de vie d'un héros dans les équipes
        
        Args:
            battle_info (dict): Informations de la bataille
            hero_id (str): ID du héros
            damage_dealt (float): Dégâts infligés
            
        Returns:
            bool: True si le héros a été trouvé et mis à jour, False sinon
        """
        try:
            # Chercher le héros dans les équipes
            teams = battle_info.get('teams', {})
            
            for team_name, team_units in teams.items():
                if isinstance(team_units, list):
                    for unit in team_units:
                        if isinstance(unit, dict) and unit.get('unitId') == hero_id:
                            # Vérifier si c'est un héros (a un champ hp)
                            if 'hp' in unit:
                                current_hp = unit.get('hp', 0)
                                new_hp = max(0, current_hp - damage_dealt)  # Ne peut pas être négatif
                
                                unit['hp'] = int(new_hp)  # Convertir en entier pour cohérence
                
                                return True
            

            return False
            
        except Exception as e:
            return False

    def _load_unit_stats(self) -> dict:
        """
        Charge les statistiques d'unités depuis unit_stats.json
        
        Returns:
            dict: Dictionnaire des stats d'unités
        """
        try:
            unit_stats_path = os.path.join(os.path.dirname(self.battles_file), 'unit_stats.json')
            if os.path.exists(unit_stats_path):
                with open(unit_stats_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            return {}

    def _get_unit_xp_value(self, unit_type: str) -> int:
        """
        Récupère la valeur XP d'un type d'unité depuis unit_stats.json
        
        Args:
            unit_type (str): Type d'unité (ex: 'infantry_light', '1_infantry_light', 'archer')
            
        Returns:
            int: Valeur XP de l'unité
        """
        unit_stats = self._load_unit_stats()
        
        # Retirer le préfixe player si présent (ex: "1_infantry_light" → "infantry_light")
        clean_unit_type = unit_type
        if '_' in unit_type and unit_type.split('_')[0].isdigit():
            clean_unit_type = '_'.join(unit_type.split('_')[1:])
        
        # Retirer le préfixe village_ si présent (ex: "village_barbarian_warrior" → "barbarian_warrior")
        if clean_unit_type.startswith('village_'):
            clean_unit_type = clean_unit_type[8:]  # Supprimer "village_"
        
        # Chercher dans toutes les ères
        for era_name, era_units in unit_stats.items():
            if clean_unit_type in era_units:
                return era_units[clean_unit_type].get('xp_value', 0)
        
        # Valeur par défaut pour les unités inconnues
        return 0

    def _extract_unit_type(self, unit_id: str) -> str:
        """
        Extrait le type d'unité depuis l'ID : "infantry_light_attacker_123_0" → "infantry_light"
        
        Args:
            unit_id (str): ID de l'unité
            
        Returns:
            str: Type d'unité
        """
        if not unit_id:
            return 'unknown'
        
        # Cas spécial pour les héros
        if unit_id.startswith('hero_'):
            return 'hero'
        
        # Pour les unités normales, extraire les parties avant _attacker ou _defender
        # Exemples: 
        # "infantry_light_attacker_123_0" → "infantry_light"
        # "archer_defender_456_1" → "archer"
        
        if '_attacker_' in unit_id:
            return unit_id.split('_attacker_')[0]
        elif '_defender_' in unit_id:
            return unit_id.split('_defender_')[0]
        else:
            # Si pas de pattern standard, essayer de deviner
            # "archer_test" → "archer"
            parts = unit_id.split('_')
            if len(parts) >= 2:
                # Vérifier si c'est un type d'unité connu (infantry_light, cavalry_heavy, etc.)
                potential_type = f"{parts[0]}_{parts[1]}"
                unit_stats = self._load_unit_stats()
                for era_units in unit_stats.values():
                    if potential_type in era_units:
                        return potential_type
                # Si pas trouvé, retourner juste la première partie
                return parts[0]
            else:
                return parts[0] if parts else 'unknown'

    def _update_battlefield_stats(self, battle_id: str, attacker_id: str, defender_id: str, kills: int, damage: float = 0):
        """
        Met à jour les statistiques dans battlefields_v2.json
        
        Args:
            battle_id (str): ID de la bataille
            attacker_id (str): ID de l'attaquant
            defender_id (str): ID du défenseur
            kills (int): Nombre d'unités tuées
            damage (float): Dégâts infligés (pour les héros)
        """
        try:
            # Charger battlefields_v2.json
            if not os.path.exists(self.battlefields_file):
                return
            
            with open(self.battlefields_file, 'r', encoding='utf-8') as f:
                battlefields_data = json.load(f)
            
            if battle_id not in battlefields_data:
                return
            
            battlefield = battlefields_data[battle_id]
            forces = battlefield.get('forces', {})
            
            # Déterminer les équipes et les joueurs
            attacker_team = 'attackers' if 'attacker' in attacker_id else 'defenders'
            defender_team = 'defenders' if 'defender' in defender_id else 'attackers'
            
            # Trouver les joueurs correspondants
            attacker_player = None
            defender_player = None
            
            for team_name in ['attackers', 'defenders']:
                for player_id in forces.get(team_name, {}):
                    if attacker_team == team_name and not attacker_player:
                        attacker_player = player_id
                    elif defender_team == team_name and not defender_player:
                        defender_player = player_id
            
            if not attacker_player or not defender_player:

                return
            
            # Extraire les types d'unités
            defender_type = self._extract_unit_type(defender_id)
            
            # Mettre à jour units_lost pour le défenseur
            if kills > 0:
                defender_forces = forces[defender_team][defender_player]
                if 'units_lost' not in defender_forces:
                    defender_forces['units_lost'] = {}
                
                current_lost = defender_forces['units_lost'].get(defender_type, 0)
                defender_forces['units_lost'][defender_type] = current_lost + kills
                

            
            # Mettre à jour units_killed pour l'attaquant  
            if kills > 0:
                attacker_forces = forces[attacker_team][attacker_player]
                if 'units_killed' not in attacker_forces:
                    attacker_forces['units_killed'] = {}
                
                current_killed = attacker_forces['units_killed'].get(defender_type, 0)
                attacker_forces['units_killed'][defender_type] = current_killed + kills
                
                # Calculer et ajouter l'XP
                xp_per_unit = self._get_unit_xp_value(defender_type)
                xp_gained = kills * xp_per_unit
                
                current_xp = attacker_forces.get('xp_gained', 0)
                attacker_forces['xp_gained'] = current_xp + xp_gained
                

            
            # Sauvegarder
            with open(self.battlefields_file, 'w', encoding='utf-8') as f:
                json.dump(battlefields_data, f, indent=2, ensure_ascii=False)
            
        except Exception as e:

            import traceback
            traceback.print_exc()

    def end_turn(self, battle_id: str) -> dict:
        """
        Termine le tour actuel et passe au joueur suivant
        
        Args:
            battle_id (str): ID de la bataille
            
        Returns:
            dict: Résultat de l'opération avec success, current_player, new_round, message
        """
        try:
            
            # Charger les données
            battles_data, battlefield_info, success, error = self.load_battle_data(battle_id)
            if not success:
                return {'success': False, 'error': error}
            
            # Récupérer les participants
            attacker_id, defender_id, success, error = self.get_participants(battle_id, battlefield_info)
            if not success:
                return {'success': False, 'error': error}
                
            battle_info = battles_data[battle_id]
            
            # Déterminer le joueur actuel et le prochain
            current_player = battle_info.get('current_player', attacker_id)
            current_round = battle_info.get('current_round', 1)
            
            # 🎯 NOUVEAU: Récupérer tous les participants depuis battlefield_info
            attackers = battlefield_info.get('participants', {}).get('attackers', [attacker_id])
            defenders = battlefield_info.get('participants', {}).get('defenders', [defender_id])
            
            # Créer la séquence complète: tous les attaquants d'abord, puis tous les défenseurs
            all_players = attackers + defenders
            
            # Trouver l'index du joueur actuel
            try:
                current_index = all_players.index(current_player)
            except ValueError:
                # Si le joueur actuel n'est pas trouvé, commencer par le premier attaquant
                current_index = 0
                current_player = all_players[0]
            
            # Déterminer le prochain joueur
            next_index = (current_index + 1) % len(all_players)
            next_player = all_players[next_index]
            
            # Nouveau round si on revient au premier joueur (premier attaquant)
            if next_index == 0:
                new_round = current_round + 1
                
                # 🚀 Si on passe de Round 1 → Round 2, initialiser la phase combat
                if current_round == 1 and new_round == 2:
                    print(f"[END_TURN] Passage Round 1 → Round 2 : initialisation phase combat")
                    battles_data[battle_id]['battle_status'] = 'battle'  # ✅ CHANGER LE STATUT
                    
                    # 🏆 VÉRIFIER SI VICTOIRE AUTOMATIQUE (défenseur sans unités déployées)
                    teams = battles_data[battle_id].get('teams', {})
                    
                    # Charger battlefields_v2 pour savoir qui est attaquant/défenseur
                    try:
                        battlefields_data = self._load_json('battlefields_v2.json')
                        
                        if battle_id not in battlefields_data:
                            print(f"⚠️ [VICTOIRE-AUTO] Bataille {battle_id} non trouvée dans battlefields_v2")
                        else:
                            participants = battlefields_data[battle_id].get('participants', {})
                            attackers = participants.get('attackers', [])
                            defenders = participants.get('defenders', [])
                            
                            # ⚠️ IGNORER les villages barbares (système de déploiement différent)
                            if 'wild_camp' in defenders:
                                print(f"⏭️ [VICTOIRE-AUTO] Village barbare détecté - skip vérification (combat normal)")
                                # Ne pas détecter de victoire automatique pour les barbares
                            else:
                                # Compter les unités déployées par équipe
                                attacker_units = 0
                                defender_units = 0
                                
                                for player_id, units in teams.items():
                                    if not isinstance(units, list):
                                        continue
                                    
                                    unit_count = len(units)
                                    
                                    if player_id in attackers:
                                        attacker_units += unit_count
                                    elif player_id in defenders:
                                        defender_units += unit_count
                                
                                # Si aucune unité défenseur déployée = victoire automatique attaquants
                                if attacker_units > 0 and defender_units == 0:
                                    print(f"🏆 Victoire automatique - défenseur sans armée")
                                    
                                    from app.battle.battle_victory_manager import BattleVictoryManager
                                    victory_manager = BattleVictoryManager()
                                    victory_manager.save_battle_result(battle_id, 'attackers', 'elimination')
                                    
                                    # Marquer la bataille comme terminée
                                    self._mark_battle_as_finished(battle_id, 'attackers', 'elimination')
                                    
                                    # Retourner avec victoire détectée
                                    return {
                                        'success': True,
                                        'victory_detected': True,
                                        'winner_team': 'attackers',
                                        'victory_type': 'elimination',
                                        'message': 'Victoire automatique - défenseur sans armée'
                                    }
                    except Exception as e:
                        print(f"❌ [VICTOIRE-AUTO] Erreur détection victoire: {e}")
                        import traceback
                        traceback.print_exc()
                
                # Mise à jour du moral pour le nouveau round
                moral_result = self.update_moral_for_new_round(battle_id, new_round)
                if moral_result.get('success'):
                    # Vérifier victoire après mise à jour du moral
                    victory_check = self._check_victory_after_action(battle_id)
                    
                    if victory_check.get('victory_detected'):
                        # Mettre à jour les données avant de retourner
                        battles_data[battle_id]['current_player'] = next_player
                        battles_data[battle_id]['current_round'] = new_round
                        self.save_battles_compact(battles_data)
                        
                        # Retourner le résultat avec les infos de victoire
                        result = {
                            'success': True,
                            'current_player': next_player,
                            'new_round': new_round,
                            'previous_player': current_player,
                            'previous_round': current_round,
                            'message': f'Tour passé à {next_player}, Round {new_round}'
                        }
                        result.update(victory_check)  # Ajouter les infos de victoire
                        return result
            else:
                new_round = current_round
                
            # Mettre à jour seulement les données essentielles
            battles_data[battle_id]['current_player'] = next_player
            battles_data[battle_id]['current_round'] = new_round
            battles_data[battle_id]['turn_started_at'] = int(time.time() * 1000)  # Timestamp en millisecondes
            
            # ⚠️ VÉRIFIER LES VICTOIRES seulement si les deux joueurs ont eu au moins 1 tour
            # Ne pas vérifier au Round 1 avant que les deux joueurs aient joué
            should_check_victory = True
            if new_round == 1:
                # Au Round 1, vérifier la victoire seulement si on est revenu à l'attaquant (les 2 ont joué)
                # Ou si le défenseur vient de jouer
                if next_player == all_players[0]:  # On revient au premier joueur (attaquant)
                    should_check_victory = True
                else:
                    should_check_victory = False  # L'attaquant a joué, mais pas encore le défenseur
            
            if should_check_victory:
                # Vérifier les victoires à chaque fin de tour
                victory_check = self._check_victory_after_action(battle_id)
                
                if victory_check.get('victory_detected'):
                    # Sauvegarder avec format compact
                    self.save_battles_compact(battles_data)
                    
                    # Retourner le résultat avec les infos de victoire
                    result = {
                        'success': True,
                        'current_player': next_player,
                        'new_round': new_round,
                        'previous_player': current_player,
                        'previous_round': current_round,
                        'message': f'Tour passé à {next_player}, Round {new_round}'
                    }
                    result.update(victory_check)  # Ajouter les infos de victoire
                    return result
            
            # Sauvegarder avec format compact
            self.save_battles_compact(battles_data)
            
            return {
                'success': True,
                'current_player': next_player,
                'new_round': new_round,
                'previous_player': current_player,
                'previous_round': current_round,
                'message': f'Tour passé à {next_player}, Round {new_round}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_battle_status(self, battle_id: str) -> dict:
        """
        Récupère l'état actuel d'une bataille
        
        Args:
            battle_id (str): ID de la bataille
            
        Returns:
            dict: État de la bataille avec succès/erreur
        """
        try:

            
            # Charger les données
            battles_data, battlefield_info, success, error = self.load_battle_data(battle_id)
            if not success:
                return {'success': False, 'error': error}
            
            battle_info = battles_data[battle_id]
            
            # Récupérer les participants
            attacker_id, defender_id, success, error = self.get_participants(battle_id, battlefield_info)
            
            result = {
                'success': True,
                'battle_id': battle_id,
                'data': {
                    'current_player': battle_info.get('current_player'),
                    'current_round': battle_info.get('current_round', 1),
                    'battle_status': battle_info.get('battle_status', 'deployment'),
                    'rounds_history': battle_info.get('rounds_history', []),
                    'participants': {
                        'attacker_id': attacker_id if success else None,
                        'defender_id': defender_id if success else None
                    }
                }
            }
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_units_that_acted_this_round(self, battle_id: str) -> dict:
        """
        Récupère la liste des unités qui ont déjà agi dans le round actuel
        
        Args:
            battle_id (str): ID de la bataille
            
        Returns:
            dict: Résultat avec la liste des unitIds qui ont agi
        """
        try:
            # Charger les données
            battles_data, battlefield_info, success, error = self.load_battle_data(battle_id)
            if not success:
                return {'success': False, 'error': error}
            
            battle_info = battles_data[battle_id]
            current_round = battle_info.get('current_round', 1)
            
            units_that_acted = []
            
            # Vérifier rounds_history
            if 'rounds_history' in battle_info:
                round_key = f"round_{current_round}"
                if round_key in battle_info['rounds_history']:
                    moves = battle_info['rounds_history'][round_key].get('moves', [])
                    
                    # Récupérer tous les unitIds qui ont déjà agi
                    for action in moves:
                        unit_id = action.get('unitId')
                        if unit_id and unit_id not in units_that_acted:
                            units_that_acted.append(unit_id)
            
            return {
                'success': True,
                'units_that_acted': units_that_acted,
                'current_round': current_round,
                'total_actions': len(units_that_acted)
            }
            
        except Exception as e:

            return {
                'success': False,
                'error': str(e)
            }
    
    def start_battle(self, battle_id: str) -> dict:
        """
        Démarre une bataille (passe en phase active)
        
        Args:
            battle_id (str): ID de la bataille
            
        Returns:
            dict: Résultat de l'opération
        """
        try:

            
            # Charger les données
            battles_data, battlefield_info, success, error = self.load_battle_data(battle_id)
            if not success:
                return {'success': False, 'error': error}
            
            battle_info = battles_data[battle_id]
            
            # S'assurer que current_round est défini
            if 'current_round' not in battles_data[battle_id]:
                battles_data[battle_id]['current_round'] = 1
            
            # 🚀 Passer au Round 2 SEULEMENT si on était au Round 1 (déploiement → combat)
            if battles_data[battle_id]['current_round'] == 1:
                battles_data[battle_id]['current_round'] = 2
                print(f"[START BATTLE] Passage de Round 1 → Round 2 (déploiement terminé)")
            else:
                print(f"[START BATTLE] Déjà au Round {battles_data[battle_id]['current_round']}")
                
            # 🎯 NOUVEAU: Commencer par l'attaquant seulement si current_player n'est pas déjà défini
            attacker_id, defender_id, success, error = self.get_participants(battle_id, battlefield_info)
            if not success:
                return {'success': False, 'error': error}
            
            # ✅ CORRECTION: Ne forcer l'attaquant que si current_player est vide ou invalide
            current_player = battles_data[battle_id].get('current_player', '')
            if not current_player or current_player not in [attacker_id, defender_id]:
                battles_data[battle_id]['current_player'] = attacker_id
                pass
            else:
                pass
            
            # ⏱️ FORCER la réinitialisation du timer pour Round 2+
            battles_data[battle_id]['turn_started_at'] = int(time.time() * 1000)
            print(f"[START BATTLE] Timer réinitialisé pour Round 2: {battles_data[battle_id]['turn_started_at']}")
            
            # Sauvegarder avec format compact
            self.save_battles_compact(battles_data)
                

            
            return {
                'success': True,
                'message': f'Bataille {battle_id} démarrée',
                'current_player': battles_data[battle_id].get('current_player'),
                'current_round': battles_data[battle_id].get('current_round', 1)
            }
            
        except Exception as e:

            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }

    def update_moral_for_new_round(self, battle_id: str, new_round: int) -> dict:
        """
        Met à jour le moral dans battlefields_v2.json pour un nouveau round
        SIMPLE: -6 par round pour attaquants, -4 pour défenseurs (directement sur le moral stocké)
        
        Args:
            battle_id (str): ID de la bataille
            new_round (int): Nouveau numéro de round
            
        Returns:
            dict: Résultat avec success et détails du moral
        """
        try:
            # Charger battlefields_v2.json
            with open(self.battlefields_file, 'r', encoding='utf-8') as f:
                battlefields_data = json.load(f)
            
            if battle_id not in battlefields_data:
                return {'success': False, 'error': f'Battlefield {battle_id} non trouvé'}
            
            battlefield = battlefields_data[battle_id]
            forces = battlefield.get('forces', {})
            

            
            moral_updates = {}
            
            # Mettre à jour moral des attaquants
            for player_id, player_forces in forces.get('attackers', {}).items():
                if 'moral' in player_forces:
                    original_moral = player_forces['moral']
                    new_moral = max(0, original_moral - 6)  # Simple: -6 par round
                    player_forces['moral'] = new_moral
                    
                    moral_updates[f"{player_id}_attacker"] = {
                        'original': original_moral,
                        'penalty': 6,
                        'new': new_moral
                    }

            
            # Mettre à jour moral des défenseurs  
            for player_id, player_forces in forces.get('defenders', {}).items():
                if 'moral' in player_forces:
                    original_moral = player_forces['moral']
                    new_moral = max(0, original_moral - 4)  # Simple: -4 par round
                    player_forces['moral'] = new_moral
                    
                    moral_updates[f"{player_id}_defender"] = {
                        'original': original_moral,
                        'penalty': 4,
                        'new': new_moral
                    }

            
            # Sauvegarder les changements
            with open(self.battlefields_file, 'w', encoding='utf-8') as f:
                json.dump(battlefields_data, f, indent=2, ensure_ascii=False)
            

            
            return {
                'success': True,
                'round': new_round,
                'moral_updates': moral_updates,
                'message': f'Moral mis à jour pour round {new_round}'
            }
            
        except Exception as e:

            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }

    def _get_team_hero_moral_bonus(self, team_forces: dict, player_id: str) -> int:
        """
        Calcule le bonus moral total des héros d'une équipe
        
        Args:
            team_forces: Données des forces de l'équipe
            player_id: ID du joueur
            
        Returns:
            int: Bonus moral total des héros
        """
        try:
            total_hero_bonus = 0
            
            # Parcourir toutes les contributions pour trouver les héros
            contributions = team_forces.get('contributions', [])
            for contribution in contributions:
                heroes = contribution.get('heroes', [])
                for hero_id in heroes:
                    hero_bonus = self._get_hero_moral_bonus_by_id(hero_id, player_id)
                    total_hero_bonus += hero_bonus

            
            return total_hero_bonus
            
        except Exception as e:

            return 0

    def _get_hero_moral_bonus_by_id(self, hero_id: str, player_id: str) -> int:
        """
        Récupère le bonus moral d'un héros depuis player_heroes.json
        
        Args:
            hero_id: ID de l'instance du héros
            player_id: ID du joueur possédant le héros
            
        Returns:
            int: Bonus moral du héros (0 si non trouvé)
        """
        try:
            player_heroes_path = os.path.join(os.path.dirname(self.battlefields_file), 'player_heroes.json')
            with open(player_heroes_path, 'r', encoding='utf-8') as f:
                heroes_data = json.load(f)
            
            player_heroes = heroes_data.get(player_id, {}).get('heroes', {})
            hero_data = player_heroes.get(hero_id, {})
            
            # Récupérer le bonus moral depuis les bonuses calculés
            calculated_bonuses = hero_data.get('calculated_bonuses', {})
            moral_bonus = calculated_bonuses.get('moral_bonus', 0)
            
            return moral_bonus
            
        except Exception as e:

            return 0

    def _load_json(self, filename: str) -> Dict[str, Any]:
        """Charge un fichier JSON du dossier gamedata"""
        filepath = os.path.join(GAME_DATA_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError as e:
            return {}

    def _save_json(self, filename: str, data: Dict[str, Any]) -> bool:
        """Sauvegarde un fichier JSON dans le dossier gamedata"""
        filepath = os.path.join(GAME_DATA_DIR, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:

            return False

    def _mark_battle_as_finished(self, battle_id: str, winner_team: str, victory_type: str):
        """
        Marque une bataille comme terminée dans battlesv2.json
        """
        try:
            import time
            battles_data = self._load_json('battlesv2.json')
            
            if battle_id in battles_data:
                battles_data[battle_id]['status'] = 'finished'
                battles_data[battle_id]['winner'] = winner_team
                battles_data[battle_id]['victory_type'] = victory_type
                battles_data[battle_id]['finished_at'] = time.time()
                
                # Sauvegarder
                if self._save_json('battlesv2.json', battles_data):
                    pass
                else:
                    pass
            else:
                pass
                
        except Exception as e:
            pass

    def _virtual_click_surrender_defender(self, battle_id: str) -> dict:
        """Simule un clic sur le bouton de reddition du défenseur"""
        try:
            from app.routes.battle_routes_v2 import surrender_battle_auto_defender
            
            result = surrender_battle_auto_defender(battle_id)
            
            # Gérer différents types de retour
            if isinstance(result, tuple) and len(result) == 2:
                response_obj, status_code = result
                if hasattr(response_obj, 'get_json'):
                    api_response = response_obj.get_json()
                else:
                    api_response = {'success': False, 'error': 'Réponse invalide'}
            elif hasattr(result, 'get_json'):
                api_response = result.get_json()
            else:
                api_response = result
            
            return api_response
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur clic virtuel défenseur: {str(e)}'
            }

    def _virtual_click_surrender_attacker(self, battle_id: str) -> dict:
        """Simule un clic sur le bouton de reddition de l'attaquant"""
        try:
            from app.routes.battle_routes_v2 import surrender_battle_auto_attacker
            
            result = surrender_battle_auto_attacker(battle_id)
            
            # Gérer différents types de retour
            if isinstance(result, tuple) and len(result) == 2:
                response_obj, status_code = result
                if hasattr(response_obj, 'get_json'):
                    api_response = response_obj.get_json()
                else:
                    api_response = {'success': False, 'error': 'Réponse invalide'}
            elif hasattr(result, 'get_json'):
                api_response = result.get_json()
            else:
                api_response = result
            
            return api_response
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur clic virtuel attaquant: {str(e)}'
            }

# Instance globale du gestionnaire
_turn_manager = None

def get_turn_manager():
    """Récupère l'instance unique du gestionnaire de tours"""
    global _turn_manager
    if _turn_manager is None:
        _turn_manager = BattleTurnManagerV2()
    return _turn_manager

# ========== ROUTES API ==========

@battle_turn_bp.route('/api/v2/battle/end-turn/<battle_id>', methods=['POST'])
def end_turn_v2(battle_id):
    """
    Termine le tour actuel et passe au joueur suivant
    """
    try:
        turn_manager = get_turn_manager()
        result = turn_manager.end_turn(battle_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@battle_turn_bp.route('/api/v2/battle/start/<battle_id>', methods=['POST'])
def start_battle_v2(battle_id):
    """
    Démarre une bataille (passe de deployment à battle)
    """
    try:
        turn_manager = get_turn_manager()
        result = turn_manager.start_battle(battle_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@battle_turn_bp.route('/api/v2/battle/status/<battle_id>', methods=['GET'])
def get_battle_status_v2(battle_id):
    """
    Récupère l'état actuel d'une bataille
    """
    try:
        turn_manager = get_turn_manager()
        
        # Charger les données
        battles_data, battlefield_info, success, error = turn_manager.load_battle_data(battle_id)
        if not success:
            return jsonify({'success': False, 'error': error}), 404
        
        battle_info = battles_data[battle_id]
        
        # Récupérer les participants
        attacker_id, defender_id, success, error = turn_manager.get_participants(battle_id, battlefield_info)
        
        result = {
            'success': True,
            'battle_id': battle_id,
            'current_player': battle_info.get('current_player'),
            'current_round': battle_info.get('current_round', 1),
            'battle_status': battle_info.get('battle_status', 'deployment'),
            'turn_history': battle_info.get('turn_history', []),
            'timer': battle_info.get('timer', {'paused': False}),
            'participants': {
                'attacker_id': attacker_id if success else None,
                'defender_id': defender_id if success else None
            }
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@battle_turn_bp.route('/api/v2/battle/units-acted/<battle_id>', methods=['GET'])
def get_units_that_acted_v2(battle_id):
    """
    Récupère les unités qui ont déjà agi dans le round actuel
    """
    try:
        turn_manager = get_turn_manager()
        result = turn_manager.get_units_that_acted_this_round(battle_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@battle_turn_bp.route('/api/v2/battle/state/<battle_id>', methods=['GET'])
def get_battle_state_v2(battle_id):
    """
    Récupère l'état complet de la bataille avec l'historique des mouvements
    """
    try:
        turn_manager = get_turn_manager()
        
        # Charger les données depuis battlesv2.json
        battles_data, battlefield_info, success, error = turn_manager.load_battle_data(battle_id)
        if not success:
            return jsonify({'success': False, 'error': error}), 404
        
        battle_data = battles_data[battle_id]
        
        return jsonify({
            'success': True,
            'battleId': battle_id,
            'current_player': battle_data.get('current_player'),
            'current_round': battle_data.get('current_round', 1),
            'battle_status': battle_data.get('battle_status', 'deployment'),
            'teams': battle_data.get('teams', {}),
            'rounds_history': battle_data.get('rounds_history', {}),
            'turn_history': battle_data.get('turn_history', [])
        }), 200
        
    except Exception as e:

        return jsonify({'success': False, 'error': str(e)}), 500

@battle_turn_bp.route('/api/v2/battle/turn-timer/<battle_id>', methods=['GET'])
def get_turn_timer_v2(battle_id):
    """
    Récupère le temps écoulé depuis le début du tour actuel
    Retourne également si le timer de 20 secondes a expiré
    """
    try:
        turn_manager = get_turn_manager()
        
        # Charger les données depuis battlesv2.json
        battles_data, battlefield_info, success, error = turn_manager.load_battle_data(battle_id)
        if not success:
            return jsonify({'success': False, 'error': error}), 404
        
        battle_data = battles_data[battle_id]
        
        # ⚠️ VÉRIFIER SI LA BATAILLE EST TERMINÉE (arrêter le timer)
        is_battle_completed = (
            'surrender_info' in battlefield_info or 
            'completed_at' in battlefield_info or 
            battlefield_info.get('status') == 'completed'
        )
        
        if is_battle_completed:
            return jsonify({
                'success': True,
                'battle_id': battle_id,
                'is_battle_completed': True,
                'battle_ended': True,
                'message': 'Bataille terminée'
            }), 200
        
        # Récupérer le timestamp de début du tour
        turn_started_at = battle_data.get('turn_started_at', 0)
        current_time = int(time.time() * 1000)  # Temps actuel en millisecondes
        
        # Calculer le temps écoulé en secondes
        elapsed_ms = current_time - turn_started_at
        elapsed_seconds = elapsed_ms / 1000.0
        
        # Vérifier si le timer est en pause
        timer_paused = battle_data.get('timer', {}).get('paused', False)
        
        # Timer de 15 secondes
        TURN_DURATION = 15
        remaining_seconds = max(0, TURN_DURATION - elapsed_seconds)
        is_expired = elapsed_seconds >= TURN_DURATION and not timer_paused
        
        result = {
            'success': True,
            'battle_id': battle_id,
            'current_player': battle_data.get('current_player'),
            'current_round': battle_data.get('current_round', 1),
            'turn_started_at': turn_started_at,
            'elapsed_seconds': round(elapsed_seconds, 1),
            'remaining_seconds': round(remaining_seconds, 1) if not timer_paused else 999,
            'is_expired': is_expired,
            'is_paused': timer_paused,
            'timer_paused': timer_paused,
            'turn_duration': TURN_DURATION
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@battle_turn_bp.route('/api/v2/battles/<battle_id>/timer/pause', methods=['POST'])
def toggle_timer_pause(battle_id):
    """
    Met en pause ou réactive le timer d'une bataille
    """
    try:
        data = request.get_json() or {}
        paused = data.get('paused', False)
        
        turn_manager = get_turn_manager()
        
        # Charger les données de la bataille
        battles_data, battlefield_info, success, error = turn_manager.load_battle_data(battle_id)
        if not success:
            return jsonify({'success': False, 'error': error}), 404
        
        # Initialiser timer dans battles_data (battlesv2.json)
        if 'timer' not in battles_data[battle_id]:
            battles_data[battle_id]['timer'] = {}
        
        # Mettre à jour l'état de pause dans battlesv2.json
        battles_data[battle_id]['timer']['paused'] = paused
        
        # Si on réactive, réinitialiser le temps de début du tour
        if not paused:
            battles_data[battle_id]['turn_started_at'] = int(time.time() * 1000)
        
        # Sauvegarder battlesv2.json
        turn_manager.save_battles_compact(battles_data)
        
        return jsonify({
            'success': True,
            'paused': paused,
            'message': f"Timer {'mis en pause' if paused else 'réactivé'}"
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
