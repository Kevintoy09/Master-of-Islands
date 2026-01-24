"""
Routes API pour la gestion des cycles automatiques IA
"""
import os
from flask import Blueprint, jsonify, request
from app.ai.ai_auto_cycle_manager import AIAutoCycleManager

# Créer le blueprint
ai_auto_cycle_bp = Blueprint('ai_auto_cycle', __name__, url_prefix='/api/ai-auto-cycles')

# Initialiser le manager
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
gamedata_dir = os.path.join(base_dir, 'gamedata')
auto_cycle_manager = AIAutoCycleManager(gamedata_dir)


@ai_auto_cycle_bp.route('/status', methods=['GET'])
def get_status():
    """Retourne le statut complet du système"""
    return jsonify(auto_cycle_manager.get_status())


@ai_auto_cycle_bp.route('/toggle', methods=['POST'])
def toggle_system():
    """Active ou désactive le système"""
    data = request.json
    enabled = data.get('enabled', False)
    auto_cycle_manager.toggle_system(enabled)
    return jsonify({"success": True, "enabled": enabled})


@ai_auto_cycle_bp.route('/presets', methods=['GET'])
def get_presets():
    """Retourne tous les presets"""
    return jsonify(auto_cycle_manager.get_presets())


@ai_auto_cycle_bp.route('/presets/<name>', methods=['GET'])
def get_preset(name):
    """Retourne un preset spécifique"""
    preset = auto_cycle_manager.get_preset(name)
    if preset:
        return jsonify(preset)
    return jsonify({"error": "Preset not found"}), 404


@ai_auto_cycle_bp.route('/presets/<name>', methods=['POST'])
def create_preset(name):
    """Crée ou met à jour un preset"""
    data = request.json
    tick_per_cycle = data.get('tick_per_cycle')
    time_slots = data.get('time_slots')
    
    if not tick_per_cycle:
        return jsonify({"error": "tick_per_cycle is required"}), 400
    
    auto_cycle_manager.save_preset(name, tick_per_cycle, time_slots)
    return jsonify({"success": True, "preset": name})


@ai_auto_cycle_bp.route('/presets/<name>', methods=['DELETE'])
def delete_preset(name):
    """Supprime un preset"""
    auto_cycle_manager.delete_preset(name)
    return jsonify({"success": True})


@ai_auto_cycle_bp.route('/presets/generate-defaults', methods=['POST'])
def generate_defaults():
    """Génère les presets par défaut"""
    defaults = {
        "casual": {"tick_per_cycle": 12, "time_slots": None},
        "easy": {"tick_per_cycle": 6, "time_slots": None},
        "medium": {"tick_per_cycle": 3, "time_slots": None},
        "hard": {"tick_per_cycle": 1, "time_slots": None},
        "extreme": {"tick_per_cycle": 0.5, "time_slots": None}
    }
    
    for name, config in defaults.items():
        auto_cycle_manager.save_preset(name, config['tick_per_cycle'], config['time_slots'])
    
    return jsonify({"success": True, "presets": list(defaults.keys())})


@ai_auto_cycle_bp.route('/players/<player_id>', methods=['GET'])
def get_player_config(player_id):
    """Retourne la configuration d'un joueur"""
    config = auto_cycle_manager.get_player_config(player_id)
    if config:
        return jsonify(config)
    return jsonify({"error": "Player config not found"}), 404


@ai_auto_cycle_bp.route('/players/<player_id>', methods=['POST'])
def set_player_preset(player_id):
    """Assigne un preset à un joueur"""
    data = request.json
    preset = data.get('preset')
    
    try:
        auto_cycle_manager.set_player_preset(player_id, preset)
        return jsonify({"success": True, "player_id": player_id, "preset": preset})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@ai_auto_cycle_bp.route('/players/<player_id>', methods=['DELETE'])
def remove_player_config(player_id):
    """Retire la configuration d'un joueur"""
    auto_cycle_manager.set_player_preset(player_id, None)
    return jsonify({"success": True})
