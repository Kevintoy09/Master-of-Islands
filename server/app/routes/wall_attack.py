"""
Endpoint pour attaquer les groupes de murs
"""

from flask import Blueprint, request, jsonify
import json
import os
from typing import Dict, Any, Optional
from app.battle.battle_creation_service_v2 import BattleCreationServiceV2

wall_attack_bp = Blueprint('wall_attack', __name__)

@wall_attack_bp.route('/api/wall/attack', methods=['POST'])
def attack_wall_group():
    """
    Endpoint pour attaquer un groupe de murs
    
    Request body:
    {
        "battle_id": "bfv2_12345",
        "group_index": 0,
        "damage": 25,
        "attacker_unit_id": "unit_123"
    }
    
    Response:
    {
        "success": true,
        "wall_group": {...},
        "remaining_hp": 95,
        "destroyed": false
    }
    """
    try:
        data = request.get_json()
        battle_id = data.get('battle_id')
        group_index = data.get('group_index')
        damage = data.get('damage', 10)
        attacker_unit_id = data.get('attacker_unit_id')
        
        if not battle_id:
            return jsonify({
                "success": False,
                "error": "battle_id requis"
            }), 400
        
        # Charger les données de battlefield avec décompaction
        try:
            battle_service = BattleCreationServiceV2()
            battlefields_data = battle_service.get_all_battlefields()
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Erreur chargement battlefields: {e}"
            }), 500
        
        # Trouver le battlefield
        battlefield = None
        for bf_id, bf_data in battlefields_data.items():
            if bf_id == battle_id or bf_data.get('id') == battle_id:
                battlefield = bf_data
                battlefield_key = bf_id
                break
        
        if not battlefield:
            return jsonify({
                "success": False,
                "error": f"Battlefield {battle_id} non trouvé"
            }), 404
        
        # Vérifier que le système de murs existe
        wall_system = battlefield.get('wall_system')
        if not wall_system or not wall_system.get('wall_groups'):
            return jsonify({
                "success": False,
                "error": "Aucun système de murs trouvé pour ce battlefield"
            }), 404
        
        # Auto-détecter le groupe si non spécifié
        wall_groups = wall_system['wall_groups']
        
        if group_index is None:
            # Trouver le premier groupe non détruit
            for i, (group_key, group_data) in enumerate(wall_groups.items()):
                if group_data.get('hp', 0) > 0 and not group_data.get('destroyed', False):
                    group_index = i
                    break
            
            if group_index is None:
                return jsonify({
                    "success": False,
                    "error": "Aucun groupe de murs non détruit trouvé"
                }), 404
            

        
        # Trouver le groupe de murs cible
        group_key = f"wall_group_{group_index}"
        
        if group_key not in wall_groups:
            return jsonify({
                "success": False,
                "error": f"Groupe de murs {group_index} non trouvé"
            }), 404
        
        wall_group = wall_groups[group_key]
        current_hp = wall_group.get('hp', 0)
        
        # Appliquer les dégâts
        new_hp = max(0, current_hp - damage)
        wall_group['hp'] = new_hp
        
        is_destroyed = new_hp <= 0
        
        # Si le groupe est détruit, libérer le passage
        if is_destroyed:
            wall_group['destroyed'] = True
            
            # ✅ SIMPLIFICATION: Plus besoin de modifier le hexMap
            # Les positions sont simplement vidées dans wall_groups
            # Le système de pathfinding vérifie wall_groups directement
            if wall_group.get('positions'):
                destroyed_positions = wall_group['positions'].copy()
                wall_group['positions'] = []  # Libérer le passage
                print(f"✅ Groupe de murs détruit: {len(destroyed_positions)} positions libérées")
        
        # Sauvegarder les modifications avec compaction automatique
        try:
            battle_service._save_battlefields_v2(battlefields_data)
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Erreur sauvegarde: {e}"
            }), 500
        
        # Calculer max_hp depuis le niveau du mur
        from app.utils.wall_group_manager import WallGroupManager
        wall_manager = WallGroupManager("data")
        wall_level = wall_group.get('wall_level', 1)
        max_hp = wall_manager.get_max_hp(wall_level)
        
        return jsonify({
            "success": True,
            "wall_group": wall_group,
            "remaining_hp": new_hp,
            "max_hp": max_hp,
            "destroyed": is_destroyed,
            "damage_dealt": damage,
            "attacker_unit_id": attacker_unit_id
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erreur serveur: {str(e)}"
        }), 500