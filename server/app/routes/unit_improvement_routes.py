"""
Routes simples et efficaces pour la gestion des améliorations d'unités
"""
from flask import Blueprint, jsonify, request
from app.battle.unit_improvement_service import UnitImprovementService

unit_improvement_bp = Blueprint('unit_improvements', __name__, url_prefix='/api/unit-improvements')

@unit_improvement_bp.route('/forge-data/<player_id>', methods=['GET'])
def get_forge_data(player_id):
    """Récupère toutes les données nécessaires pour la forge"""
    try:
        service = UnitImprovementService()
        result = service.get_forge_data(player_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@unit_improvement_bp.route('/config', methods=['GET'])
def get_config():
    """Récupère la configuration du système d'améliorations"""
    try:
        service = UnitImprovementService()
        config = service.get_config()
        return jsonify({'success': True, 'config': config})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@unit_improvement_bp.route('/upgrade', methods=['POST'])
def upgrade_unit():
    """Améliore une caractéristique d'unité"""
    try:
        data = request.get_json()
        if not data or not all(k in data for k in ('player_id', 'unit_type', 'improvement_type')):
            return jsonify({'success': False, 'error': 'Données manquantes'}), 400
        
        service = UnitImprovementService()
        result = service.upgrade_unit(
            data['player_id'],
            data['unit_type'],
            data['improvement_type']
        )
        
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@unit_improvement_bp.route('/enhanced-stats/<player_id>/<unit_type>', methods=['GET'])
def get_enhanced_unit_stats(player_id, unit_type):
    """Récupère les stats d'unité avec bonus de forge appliqués"""
    try:
        from app.battle.enhanced_unit_stats_service import EnhancedUnitStatsService
        service = EnhancedUnitStatsService()
        
        enhanced_stats = service.get_unit_stats_with_forge_bonus(unit_type, player_id)
        
        if enhanced_stats:
            return jsonify({
                'success': True,
                'stats': enhanced_stats,
                'player_id': player_id,
                'unit_type': unit_type
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Type d\'unité inconnu: {unit_type}'
            }), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@unit_improvement_bp.route('/downgrade', methods=['POST'])
def downgrade_unit():
    """Réduit une caractéristique d'unité"""
    try:
        data = request.get_json()
        if not data or not all(k in data for k in ('player_id', 'unit_type', 'improvement_type')):
            return jsonify({'success': False, 'error': 'Données manquantes'}), 400
        
        service = UnitImprovementService()
        result = service.downgrade_unit(
            data['player_id'],
            data['unit_type'],
            data['improvement_type']
        )
        
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500