"""
battle_actions_v2.py

Routes Flask spécifiques pour les actions de bataille V2
- Enregistrement des actions d'attaque dans battlesv2.json
- Séparé du système V1 pour éviter les conflits
- Utilise BattleTurnManagerV2 pour la logique métier
"""

from flask import Blueprint, request, jsonify
from .battle_turn_manager_v2 import BattleTurnManagerV2

# Blueprint dédié pour les actions de bataille V2
battle_actions_v2_bp = Blueprint('battle_actions_v2', __name__)

@battle_actions_v2_bp.route('/api/v2/battle/action', methods=['POST'])
def record_battle_action_v2():
    """
    Enregistre une action de combat V2 dans battlesv2.json
    
    Body attendu pour une attaque:
    {
        "battlefield_id": "bfv2_7axh4h01",
        "unit_id": "infantry_light_attacker_1758783384560_6",
        "round": 1,
        "action": {
            "type": "attack",
            "target": "infantry_light_defender_1758783390704_7",
            "damage_dealt": 86.0,
            "previous_count": 10
        },
        "target_new_state": {
            "count": 8,
            "status": "active"
        }
    }
    """
    try:
        data = request.get_json()
        
        # 🔍 Debug: afficher les données reçues
        print(f"🎯 [ACTION] Données reçues: {data}")
        
        # Validation des données
        battlefield_id = data.get('battlefield_id')
        unit_id = data.get('unit_id')
        action_data = data.get('action', {})
        new_state = data.get('target_new_state', {})
        
        print(f"🔍 battlefield_id={battlefield_id}, unit_id={unit_id}, action_data={action_data}")
        
        if not all([battlefield_id, unit_id, action_data]):
            return jsonify({
                'success': False,
                'error': 'Données manquantes: battlefield_id, unit_id et action requis'
            }), 400
        
        action_type = action_data.get('type')
        
        if action_type == 'attack':
            # Utiliser le BattleTurnManagerV2 pour enregistrer l'attaque
            turn_manager = BattleTurnManagerV2()
            
            # Extraire les données de l'attaque
            target_id = action_data.get('target')
            damage_dealt = action_data.get('damage_dealt', 0)
            previous_count = action_data.get('previous_count', 10)
            target_new_count = new_state.get('count', 0)
            
            # Détecter si la cible est un héros (nouveau format: defender_player_X_hero_hero_xxx)
            is_hero_target = target_id and ('_hero_' in target_id or target_id.startswith('hero_'))


            
            if is_hero_target:

                # Pour les héros : utiliser les dégâts aux HP
                result = turn_manager.record_hero_damage_action(battlefield_id, unit_id, target_id, damage_dealt)
                
                if result.get('success'):
                    response_data = {
                        'success': True,
                        'message': 'Action d\'attaque héros V2 enregistrée avec succès',
                        'battle_id': battlefield_id,
                        'attacker': unit_id,
                        'defender': target_id,
                        'damage_dealt': damage_dealt,
                        'target_type': 'hero',
                        'system': 'V2'
                    }
                    
                    # Ajouter les informations de victoire si présentes
                    if result.get('victory_detected'):
                        response_data.update({
                            'victory_detected': True,
                            'winner_team': result.get('winner_team'),
                            'victory_type': result.get('victory_type'),
                            'victory_message': result.get('victory_message')
                        })
                    
                    return jsonify(response_data), 200
                else:
                    return jsonify(result), 400
            else:
                # Pour les unités normales : utiliser les kills
                kills = max(0, previous_count - target_new_count)
                result = turn_manager.record_attack_action(battlefield_id, unit_id, target_id, kills)
                
                if result.get('success'):
                    response_data = {
                        'success': True,
                        'message': 'Action d\'attaque unité V2 enregistrée avec succès',
                        'battle_id': battlefield_id,
                        'attacker': unit_id,
                        'defender': target_id,
                        'kills': kills,
                        'previous_count': previous_count,
                        'surviving_count': target_new_count,
                        'target_type': 'unit',
                        'system': 'V2'
                    }
                    
                    # Ajouter les informations de victoire si présentes
                    if result.get('victory_detected'):
                        response_data.update({
                            'victory_detected': True,
                            'winner_team': result.get('winner_team'),
                            'victory_type': result.get('victory_type'),
                            'victory_message': result.get('victory_message')
                        })
                    
                    return jsonify(response_data), 200
                else:
                    return jsonify(result), 400
        
        elif action_type == 'move':
            # Pour les mouvements, utiliser la méthode existante
            turn_manager = BattleTurnManagerV2()
            
            from_pos = action_data.get('from', [0, 0])
            to_pos = action_data.get('to', [0, 0])
            
            result = turn_manager.record_unit_move(battlefield_id, unit_id, from_pos, to_pos)
            
            if result.get('success'):
                return jsonify({
                    'success': True,
                    'message': 'Mouvement V2 enregistré avec succès',
                    'battle_id': battlefield_id,
                    'unit_id': unit_id,
                    'from': from_pos,
                    'to': to_pos,
                    'system': 'V2'
                }), 200
            else:
                return jsonify(result), 400
        
        elif action_type == 'attack_wall':
            # 🧱 NOUVEAU : Gestion des attaques de murs
            turn_manager = BattleTurnManagerV2()
            
            # Extraire les données de l'attaque de mur
            wall_group_id = action_data.get('wall_group_id', f"wall_group_{action_data.get('group_index', 0)}")
            damage_dealt = action_data.get('damage_dealt', 0)
            wall_hp_before = action_data.get('wall_hp_before', 0)
            wall_hp_after = action_data.get('wall_hp_after', 0)
            destroyed = action_data.get('destroyed', False)
            
            result = turn_manager.record_wall_attack_action(
                battlefield_id, unit_id, wall_group_id, 
                damage_dealt, wall_hp_before, wall_hp_after, destroyed
            )
            
            if result.get('success'):
                return jsonify({
                    'success': True,
                    'message': 'Attaque de mur V2 enregistrée avec succès',
                    'battle_id': battlefield_id,
                    'attacker': unit_id,
                    'wall_group': wall_group_id,
                    'damage_dealt': damage_dealt,
                    'wall_destroyed': destroyed,
                    'system': 'V2'
                }), 200
            else:
                return jsonify(result), 400
        
        else:
            return jsonify({
                'success': False,
                'error': f'Type d\'action non supporté en V2: {action_type}'
            }), 400
        
    except Exception as e:
        print(f"❌ [V2_ACTIONS] Erreur: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Erreur serveur V2: {str(e)}'
        }), 500

@battle_actions_v2_bp.route('/api/v2/battle/status/<battle_id>', methods=['GET'])
def get_battle_status_v2(battle_id):
    """
    Récupère le statut actuel d'une bataille V2
    """
    try:
        turn_manager = BattleTurnManagerV2()
        result = turn_manager.get_battle_status(battle_id)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        print(f"❌ [V2_ACTIONS] Erreur get_status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
