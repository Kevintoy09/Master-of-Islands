"""
API Routes pour le panneau de debug IA
Permet de tester les décisions de l'IA manuellement
"""
from flask import Blueprint, request, jsonify
from app.ai.battle_ai_basic import BattleAIBasic
from app.routes.battle_routes_v2 import load_json_data
from app.config.paths import BATTLES_V2_FILE, BATTLEFIELDS_V2_FILE
import json
import os

ai_debug_bp = Blueprint('ai_debug', __name__)

@ai_debug_bp.route('/api/v2/ai/config', methods=['GET'])
def get_ai_config():
    """Récupère la configuration actuelle de l'IA"""
    try:
        # __file__ = server/app/routes/ai_debug_routes.py
        # On remonte 3 fois pour arriver à server/, puis data/
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(base_dir, 'data', 'ai_config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return jsonify(config), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ai_debug_bp.route('/api/v2/ai/config', methods=['POST'])
def save_ai_config():
    """Sauvegarde la nouvelle configuration IA"""
    try:
        data = request.get_json()
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(base_dir, 'data', 'ai_config.json')
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return jsonify({"success": True, "message": "Configuration sauvegardée"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ai_debug_bp.route('/api/v2/ai/test-unit', methods=['POST'])
def test_unit_ai():
    """
    Teste la décision de l'IA pour une unité spécifique
    Retourne les scores de toutes les cibles et la décision finale
    """
    try:
        data = request.get_json()
        battle_id = data.get('battleId')
        player_id = data.get('playerId')
        unit_id = data.get('unitId')
        custom_weights = data.get('weights', {})
        
        if not all([battle_id, player_id, unit_id]):
            return jsonify({
                'success': False,
                'error': 'Paramètres manquants'
            }), 400
        
        # Charger la bataille
        battles_data = load_json_data(BATTLES_V2_FILE, {})
        battlefields_data = load_json_data(BATTLEFIELDS_V2_FILE, {})
        
        if battle_id not in battles_data:
            return jsonify({
                'success': False,
                'error': f'Bataille {battle_id} non trouvée'
            }), 404
        
        battle_info = battles_data[battle_id]
        battlefield_info = battlefields_data.get(battle_id, {})
        
        # Créer une instance de l'IA avec poids personnalisés
        ai = BattleAIBasic()
        
        # Charger et modifier les poids si fournis
        if custom_weights:
            for key, value in custom_weights.items():
                weight_key = f'priority_{key}'
                if weight_key in ai.config.get('decision_weights', {}):
                    ai.config['decision_weights'][weight_key] = value
        
        # Trouver l'unité dans les teams
        unit_data = None
        team_name = None
        for team_id, units in battle_info.get('teams', {}).items():
            for unit in units:
                if unit.get('unitId') == unit_id:
                    unit_data = unit
                    team_name = 'attacker' if 'attacker' in unit_id else 'defender'
                    break
            if unit_data:
                break
        
        if not unit_data:
            return jsonify({
                'success': False,
                'error': f'Unité {unit_id} non trouvée'
            }), 404
        
        # Analyser toutes les cibles possibles
        all_enemies = ai._get_all_enemies(battle_info, team_name)
        
        if not all_enemies:
            return jsonify({
                'success': False,
                'error': 'Aucun ennemi disponible'
            }), 404
        
        # Calculer les scores pour toutes les cibles
        scores = []
        logs = []
        
        logs.append(f"🎯 Analyse pour {unit_id}")
        logs.append(f"📍 Position: {unit_data.get('position')}")
        logs.append(f"🔢 Nombre: {unit_data.get('unitCount', 1)}")
        logs.append("")
        
        for enemy in all_enemies:
            enemy_id = enemy.get('unitId')
            enemy_pos = enemy.get('position', [0, 0])
            
            # Calculer le score avec la méthode privée
            score_data = ai._calculate_target_score(
                unit_data,
                enemy,
                battle_info,
                battlefield_info,
                100  # Moral par défaut
            )
            
            scores.append({
                'targetId': enemy_id,
                'unitType': ai.combat_calc.get_unit_type_from_id(enemy_id),
                'position': enemy_pos,
                'unitCount': enemy.get('unitCount', 1),
                'hp': score_data.get('hp'),
                'distance': score_data.get('distance'),
                'total': score_data.get('total_score', 0),
                'breakdown': score_data.get('breakdown', '')
            })
        
        # Trier par score décroissant
        scores.sort(key=lambda x: x['total'], reverse=True)
        
        # Décision finale
        best_target = scores[0] if scores else None
        decision = None
        
        if best_target:
            # Déterminer l'action (attaque ou mouvement)
            unit_pos = unit_data.get('position', [0, 0])
            target_pos = best_target['position']
            distance = abs(unit_pos[0] - target_pos[0]) + abs(unit_pos[1] - target_pos[1])
            
            # TODO: Récupérer la vraie portée de l'unité
            unit_range = 1
            
            action = 'attack' if distance <= unit_range else 'move'
            
            decision = {
                'action': action,
                'target': best_target['targetId'],
                'score': best_target['total'],
                'reasoning': f"{'Attaque' if action == 'attack' else 'Mouvement vers'} {best_target['unitType']} (score: {best_target['total']:.1f})"
            }
            
            logs.append(f"✅ Décision: {decision['reasoning']}")
        
        # Logs des scores
        logs.append("\n📊 Top 5 des cibles:")
        for i, score in enumerate(scores[:5], 1):
            logs.append(f"  {i}. {score['unitType']} - {score['total']:.1f}pts ({score['breakdown']})")
        
        return jsonify({
            'success': True,
            'scores': scores,
            'decision': decision,
            'logs': logs,
            'weights_used': ai.config.get('decision_weights', {})
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@ai_debug_bp.route('/api/v2/ai/test-next-unit', methods=['POST'])
def test_next_unit():
    """
    Exécute l'IA pour la prochaine unité non jouée avec logs détaillés
    """
    try:
        data = request.get_json()
        battle_id = data.get('battleId')
        custom_config = data.get('config')
        
        if not battle_id:
            return jsonify({
                'success': False,
                'error': 'battleId manquant'
            }), 400
        
        # Charger la bataille
        battles_data = load_json_data(BATTLES_V2_FILE, {})
        battlefields_data = load_json_data(BATTLEFIELDS_V2_FILE, {})
        
        if battle_id not in battles_data:
            return jsonify({
                'success': False,
                'error': f'Bataille {battle_id} non trouvée'
            }), 404
        
        battle_info = battles_data[battle_id]
        battlefield_info = battlefields_data.get(battle_id, {})
        current_player = battle_info.get('current_player')
        
        # Créer l'instance IA
        ai = BattleAIBasic()
        
        # Appliquer la config personnalisée si fournie
        if custom_config and 'decision_weights' in custom_config:
            ai.config['decision_weights'] = custom_config['decision_weights']
        
        # Récupérer toutes les unités du joueur actuel
        team_name = 'attacker' if current_player == battle_info.get('attacker') else 'defender'
        current_round = battle_info.get('current_round', 1)
        
        # Trouver les unités disponibles (non jouées ce round)
        available_units = ai._get_available_units(battle_info, current_player, current_round)
        
        if not available_units:
            return jsonify({
                'success': False,
                'message': 'Aucune unité disponible (toutes ont déjà joué ce round)'
            }), 200
        
        # Prendre la première unité disponible
        next_unit = available_units[0]
        
        # Analyser les cibles pour cette unité
        all_enemies = ai._get_all_enemies(battle_info, team_name)
        
        if not all_enemies:
            return jsonify({
                'success': False,
                'error': 'Aucun ennemi disponible'
            }), 404
        
        # Calculer les scores
        target_scores = []
        for enemy in all_enemies:
            score_data = ai._calculate_target_score(
                next_unit,
                enemy,
                battle_info,
                battlefield_info,
                100  # Moral par défaut
            )
            
            target_scores.append({
                'unitId': enemy.get('unitId'),
                'unitType': ai.combat_calc.get_unit_type_from_id(enemy.get('unitId')),
                'position': enemy.get('position'),
                'totalScore': score_data.get('total_score', 0),
                'breakdown': {
                    'hero_bonus': score_data.get('hero_bonus', 0),
                    'hp_bonus': score_data.get('hp_bonus', 0),
                    'ranged_bonus': score_data.get('ranged_bonus', 0),
                    'distance_penalty': score_data.get('distance_penalty', 0),
                    'threat_bonus': score_data.get('threat_bonus', 0)
                }
            })
        
        # Trier par score
        target_scores.sort(key=lambda x: x['totalScore'], reverse=True)
        best_target = target_scores[0] if target_scores else None
        
        # Exécuter l'action (attaque ou mouvement)
        action_result = None
        if best_target:
            # TODO: Implémenter l'exécution réelle de l'action
            # Pour l'instant, on retourne juste la décision
            action_result = {
                'action': 'attack',
                'target': best_target['unitId'],
                'damage': 'N/A'  # Sera calculé par le combat
            }
        
        return jsonify({
            'success': True,
            'unit': {
                'unitId': next_unit.get('unitId'),
                'unitType': ai.combat_calc.get_unit_type_from_id(next_unit.get('unitId')),
                'position': next_unit.get('position'),
                'unitCount': next_unit.get('unitCount'),
                'current_hp': next_unit.get('current_hp'),
                'max_hp': next_unit.get('max_hp')
            },
            'decision': {
                'targets': target_scores,
                'best_target': best_target,
                'action': action_result.get('action') if action_result else None,
                'damage': action_result.get('damage') if action_result else None
            }
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@ai_debug_bp.route('/api/v2/battle/list-active', methods=['GET'])

def list_active_battles():
    """Liste toutes les batailles actives"""
    try:
        battles_data = load_json_data(BATTLES_V2_FILE, {})
        
        active_battles = []
        for battle_id, battle in battles_data.items():
            active_battles.append({
                'battleId': battle_id,
                'current_round': battle.get('current_round', 1),
                'current_player': battle.get('current_player', ''),
                'location': battle.get('location', '')
            })
        
        return jsonify(active_battles)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
